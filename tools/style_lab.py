#!/usr/bin/env python3
"""Style Lab — Reference Library: upload reference VIDEOS + VOICEOVERS fast,
auto-analyze, and keep a browsable library of every reference + its profile.

- Fast upload: big chunks, parallel, live MB/s.
- Videos  -> auto style analysis (cuts, motion budget, colors) -> style-reports/.
- Audio (voiceovers) -> auto probe (duration, loudness, sample rate) -> report.
- Library survives restarts (reports on disk); agent reads reports to build.
- Voiceover files land in tools/voiceovers/ so builds can use YOUR voice.

Usage: python3 style_lab.py [port]
"""
import json
import mimetypes
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
UPLOADS = HERE / "uploads"          # reference videos
VOICEOVERS = HERE / "voiceovers"    # your narration / audio files
REPORTS = HERE / "style-reports"
THUMBS = UPLOADS / "thumbs"
UPLOADS.mkdir(exist_ok=True)
VOICEOVERS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
THUMBS.mkdir(exist_ok=True)

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FF = "ffmpeg"

SAMPLE_FPS = 6
GW, GH = 480, 270
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".aiff", ".aif", ".wma"}
STATUS = {}   # job_id -> {state, progress, result, error}


# ------------------------------------------------------------------ probe
def probe(path):
    p = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    dur = fps = w = h = sr = ch = codec = None
    for line in p.stderr.splitlines():
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", line)
        if m:
            hh, mm, ss = m.groups()
            dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
        m = re.search(r"(\d{2,5})x(\d{2,5})", line)
        if m and not w:
            w, h = int(m.group(1)), int(m.group(2))
        m = re.search(r"(\d+(?:\.\d+)?) fps", line)
        if m and not fps:
            fps = float(m.group(1))
        m = re.search(r"Audio: ([a-z0-9]+)", line)
        if m and not codec:
            codec = m.group(1)
        m = re.search(r"(\d+) Hz", line)
        if m and not sr:
            sr = int(m.group(1))
        m = re.search(r"(mono|stereo|5\.1|7\.1)", line)
        if m and not ch:
            ch = m.group(1)
    return {"duration": dur, "fps": fps, "w": w, "h": h,
            "codec": codec, "sample_rate": sr, "channels": ch}


def is_audio(path):
    return Path(path).suffix.lower() in AUDIO_EXTS


def analyze_audio(path):
    """Voiceover probe: duration, codec, sample rate, channels, loudness."""
    info = probe(path)
    if not info["duration"]:
        raise ValueError("cannot read duration (bad audio?)")
    # mean volume via volumedetect (fast single pass)
    loud = None
    try:
        p = subprocess.run([FF, "-i", str(path), "-af", "volumedetect",
                            "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r"mean_volume: (-?[\d.]+) dB", p.stderr)
        if m:
            loud = float(m.group(1))
    except Exception:
        pass
    return {
        "file": Path(path).name,
        "kind": "audio",
        "duration": round(info["duration"], 2),
        "codec": info.get("codec") or "?",
        "sample_rate": info.get("sample_rate"),
        "channels": info.get("channels"),
        "loudness_db": loud,
        "detected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ------------------------------------------------------------------ frames
def frames(path, fps=SAMPLE_FPS):
    cmd = [FF, "-v", "error", "-i", str(path), "-vf",
           f"fps={fps},scale={GW}:{GH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    nb = GW * GH * 3
    t = 0.0
    while True:
        buf = p.stdout.read(nb)
        if not buf or len(buf) < nb:
            break
        rgb = np.frombuffer(buf, dtype=np.uint8).reshape(GH, GW, 3)
        yield t, rgb
        t += 1.0 / fps
    p.wait()


def analyze(path):
    """Streaming motion autopsy (low memory, handles long videos)."""
    info = probe(path)
    if not info["duration"]:
        raise ValueError("cannot read duration (bad video?)")

    diffs, gmeans, lmaxes, color_samples = [], [], [], []
    prev = None
    n = 0
    for t, rgb in frames(path):
        g = rgb.mean(axis=2).astype(np.float32)
        if prev is not None:
            d = np.abs(g - prev)
            diffs.append(float(d.mean()))
            bh, bw = GH // 5, GW // 9
            blocks = np.array([[d[y:y + bh, x:x + bw].mean()
                                for x in range(0, GW - bw + 1, bw)]
                               for y in range(0, GH - bh + 1, bh)])
            gmeans.append(float(d.mean()))
            lmaxes.append(float(blocks.max()))
        prev = g
        if n % 12 == 0:
            color_samples.append((t, rgb[10:80, 10:120].reshape(-1, 3).mean(axis=0)))
        n += 1
        if n > 20000:
            break
    if n < 3:
        raise ValueError("too few frames to analyze")

    diffs = np.array(diffs)
    thr = max(6.0, float(np.percentile(diffs, 96)))
    cuts = [0]
    for i, d in enumerate(diffs[1:], 1):
        if d > thr:
            cuts.append(i)
    cuts.append(len(diffs) - 1)

    segs = []
    for c in range(len(cuts) - 1):
        a, b = cuts[c], cuts[c + 1]
        if b - a < 2:
            continue
        n2 = b - a
        frozen = sum(1 for g in gmeans[a:b] if g < 0.6)
        active = sum(1 for i in range(a, b) if lmaxes[i] > 3 * max(gmeans[i], 0.4))
        cam = n2 - frozen - active
        segs.append(dict(start=round(a / SAMPLE_FPS, 2), dur=round((b - a) / SAMPLE_FPS, 2),
                         frozen=round(frozen / n2 * 100), cam=round(max(0, cam) / n2 * 100),
                         active=round(active / n2 * 100)))

    shots = [sg["dur"] for sg in segs]
    srt = sorted(shots)

    def pct(p):
        return round(srt[min(len(srt) - 1, int(len(srt) * p))], 2)

    brights = [float(c[1].mean()) for c in color_samples]
    colors = [[int(v) for v in c[1]] for c in color_samples]

    raw_f = sum(round(sg["frozen"] / 100 * round(sg["dur"] * SAMPLE_FPS)) for sg in segs)
    raw_a = sum(round(sg["active"] / 100 * round(sg["dur"] * SAMPLE_FPS)) for sg in segs)
    tot = sum(round(sg["dur"] * SAMPLE_FPS) for sg in segs)
    raw_c = max(0, tot - raw_f - raw_a)
    motion = {"frozen_pct": round(raw_f / max(tot, 1) * 100),
              "camera_pct": round(raw_c / max(tot, 1) * 100),
              "character_pct": round(raw_a / max(tot, 1) * 100)}
    cam_heavy = sum(1 for sg in segs if sg["cam"] >= 50)
    cam_est = "slow zoom / Ken Burns" if cam_heavy / max(len(segs), 1) > 0.4 else "locked + puppets"

    return {
        "file": Path(path).name,
        "kind": "video",
        "duration": round(info["duration"], 2),
        "fps": info["fps"], "resolution": f"{info['w']}x{info['h']}",
        "shots": len(segs),
        "cut_cadence": {"min": round(min(shots), 2) if shots else 0,
                        "p25": pct(0.25), "median": pct(0.5),
                        "mean": round(sum(shots) / len(shots), 2) if shots else 0,
                        "p75": pct(0.75), "max": round(max(shots), 2) if shots else 0},
        "motion_budget": motion,
        "camera_estimate": cam_est,
        "bg_color": [int(v) for v in np.mean([c for c in colors], axis=0)] if colors else [255, 255, 255],
        "brightness": round(sum(brights) / len(brights)) if brights else 200,
        "palette": [f"rgb({int(c[0])},{int(c[1])},{int(c[2])})" for c in colors[:6]],
        "shot_table": segs[:60],
        "detected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def save_report(job_id, profile):
    rep = REPORTS / f"{job_id}.json"
    rep.write_text(json.dumps(profile, indent=2))
    md = REPORTS / f"{job_id}.md"
    if profile.get("kind") == "audio":
        md.write_text(f"""# Voiceover profile — {profile['file']}

| Metric | Value |
|---|---|
| Duration | {profile['duration']}s |
| Codec | {profile['codec']} |
| Sample rate | {profile.get('sample_rate')} Hz |
| Channels | {profile.get('channels')} |
| Mean loudness | {profile.get('loudness_db')} dB |
| Detected | {profile.get('detected_at')} |
""")
    else:
        c = profile["cut_cadence"]
        m = profile["motion_budget"]
        md.write_text(f"""# Style profile — {profile['file']}

| Metric | Value |
|---|---|
| Duration | {profile['duration']}s · {profile['fps']}fps · {profile['resolution']} |
| Shots | {profile['shots']} |
| Cut cadence | min {c['min']}s · p25 {c['p25']} · median **{c['median']}s** · mean {c['mean']} · p75 {c['p75']} · max {c['max']} |
| Motion budget | {m['frozen_pct']}% frozen / {m['camera_pct']}% camera / {m['character_pct']}% character |
| Camera | {profile['camera_estimate']} |
| Bg color | rgb{tuple(profile['bg_color'])} · brightness {profile['brightness']} |
| Palette | {', '.join(profile['palette'])} |

## Shots
| # | start | dur | frozen% | camera% | character% |
|---|---|---|---|---|---|
""" + "\n".join(
            f"| {i} | {s['start']} | {s['dur']} | {s['frozen']} | {s['cam']} | {s['active']} |"
            for i, s in enumerate(profile["shot_table"], 1)) + "\n")
    return rep


def run_job(job_id, path):
    try:
        STATUS[job_id] = {"state": "analyzing", "progress": 5}
        profile = analyze_audio(path) if is_audio(path) else analyze(path)
        rep = save_report(job_id, profile)
        STATUS[job_id] = {"state": "done", "progress": 100,
                          "result": profile, "report": rep.name}
    except Exception as e:
        STATUS[job_id] = {"state": "error", "error": str(e)}


# ------------------------------------------------------------------ library
def _media_dir(fname):
    return VOICEOVERS if Path(fname).suffix.lower() in AUDIO_EXTS else UPLOADS


def library():
    """All known refs: from reports (survive restarts) + raw files on disk."""
    entries = []
    for rep in sorted(REPORTS.glob("*.json")):
        try:
            data = json.loads(rep.read_text())
        except Exception:
            continue
        fname = data.get("file", "")
        if not fname:
            continue
        kind = data.get("kind", "video")
        fdir = VOICEOVERS if kind == "audio" else UPLOADS
        fpath = fdir / fname
        cc = data.get("cut_cadence") or {}
        mb = data.get("motion_budget") or {}
        entries.append({
            "id": rep.stem, "file": fname, "exists": fpath.exists(),
            "size": fpath.stat().st_size if fpath.exists() else 0,
            "analyzed": True, "kind": kind,
            "duration": data.get("duration"), "fps": data.get("fps"),
            "shots": data.get("shots"),
            "median": cc.get("median"),
            "frozen": mb.get("frozen_pct"),
            "camera": mb.get("camera_pct"),
            "character": mb.get("character_pct"),
            "brightness": data.get("brightness"),
            "palette": data.get("palette", [])[:5],
            "camera_est": data.get("camera_estimate", ""),
            "codec": data.get("codec"), "sample_rate": data.get("sample_rate"),
            "channels": data.get("channels"), "loudness_db": data.get("loudness_db"),
            "report": rep.name,
        })
    seen = {e["file"] for e in entries}
    for folder, kind in ((UPLOADS, "video"), (VOICEOVERS, "audio")):
        for f in sorted(folder.glob("*")):
            if not f.is_file() or f.name in seen or f.suffix.lower() == ".jpg":
                continue
            entries.append({
                "id": f.stem.split("_")[0], "file": f.name, "exists": True,
                "size": f.stat().st_size, "analyzed": False, "kind": kind,
                "duration": None, "shots": None, "median": None,
                "frozen": None, "camera": None, "character": None,
                "palette": [], "camera_est": "", "codec": None,
                "sample_rate": None, "channels": None, "loudness_db": None,
                "report": None,
            })
    entries.sort(key=lambda e: (e["kind"], e["file"]))
    return entries


def thumbnail(fname):
    f = UPLOADS / fname
    if not f.is_file():
        return None
    out = THUMBS / (fname + ".jpg")
    if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
        subprocess.run([FF, "-y", "-v", "error", "-ss", "1", "-i", str(f),
                        "-frames:v", "1", "-vf", "scale=320:180", str(out)],
                       capture_output=True)
    return out if out.exists() else None


# ------------------------------------------------------------------ server
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class Handler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj), "application/json")

    def _serve_file(self, f):
        size = f.stat().st_size
        rng = self.headers.get("Range", "")
        mm = re.match(r"bytes=(\d*)-(\d*)", rng)
        if mm and (mm.group(1) or mm.group(2)):
            start = int(mm.group(1) or 0)
            end = min(int(mm.group(2) or size - 1), size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            length = end - start + 1
        else:
            start, length = 0, size
            self.send_response(200)
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(f, "rb") as fh:
            fh.seek(start)
            left = length
            while left > 0:
                chunk = fh.read(min(65536, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def do_GET(self):
        path = self.path.split("?")[0]
        q = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)

        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
            return
        if path == "/jobs":
            out = {k: {kk: vv for kk, vv in v.items() if kk != "result"}
                   for k, v in STATUS.items()}
            for k, v in STATUS.items():
                if v.get("result"):
                    out[k]["result"] = {kk: vv for kk, vv in v["result"].items()
                                        if kk != "shot_table"}
            self._json(out)
            return
        if path == "/library":
            self._json(library())
            return
        if path == "/thumb":
            t = thumbnail(params.get("file", ""))
            if t:
                self._send(200, t.read_bytes(), "image/jpeg")
            else:
                self._send(404, "no thumb")
            return
        if path.startswith("/report/"):
            f = REPORTS / path.split("/")[-1]
            if f.exists():
                self._send(200, f.read_text(), "application/json")
            else:
                self._send(404, "not found")
            return
        m = re.match(r"/(uploads|voiceovers)/(.+)", path)
        if m:
            base = UPLOADS if m.group(1) == "uploads" else VOICEOVERS
            f = base / m.group(2)
            if f.is_file():
                self._serve_file(f)
                return
            self._send(404, "not found")
            return
        self._send(404, "not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        q = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)

        if path == "/chunk":
            job = params.get("job", "")
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length) if length else b""
            part = UPLOADS / f"{job}.part.{int(params.get('index', 0)):05d}"
            part.write_bytes(data)
            self._json({"job": job, "bytes": len(data)})
            return
        if path == "/complete":
            job = params.get("job", "")
            name = params.get("name", "video.mp4")
            safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
            parts = sorted(UPLOADS.glob(f"{job}.part.*"))
            if not parts:
                self._json({"error": "no chunks for job"}, 400)
                return
            folder = VOICEOVERS if Path(name).suffix.lower() in AUDIO_EXTS else UPLOADS
            dest = folder / f"{job}_{safe}"
            with open(dest, "wb") as out:
                for p in parts:
                    out.write(p.read_bytes())
                    p.unlink()
            self._json({"job": job, "file": dest.name, "uploaded": True,
                        "kind": "audio" if folder is VOICEOVERS else "video"})
            return
        if path == "/analyze":
            job = params.get("job", "")
            fname = params.get("file", "")
            folder = VOICEOVERS if Path(fname).suffix.lower() in AUDIO_EXTS else UPLOADS
            f = folder / fname
            if not f.is_file():
                self._json({"error": "no uploaded file for job"}, 400)
                return
            threading.Thread(target=run_job, args=(job, str(f)), daemon=True).start()
            self._json({"job": job, "analyzing": True})
            return
        self._send(404, "not found")

    def log_message(self, *a):
        pass


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Style Lab — references + voiceovers</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#0b0d12; color:#e9edf4;
         font-family: system-ui,-apple-system,Segoe UI,sans-serif; }
  header { padding:22px 18px 6px; text-align:center; }
  h1 { font-size:22px; margin:0 0 4px; }
  .sub { font-size:13px; color:#8b95a7; margin:0 0 14px; }
  .drop { max-width:760px; margin:0 auto 14px; border:2px dashed #2b3444;
          border-radius:14px; padding:26px 20px; text-align:center;
          cursor:pointer; transition:.2s; background:#10141c; }
  .drop.over { border-color:#f5c63c; background:#161b26; }
  .drop b { font-size:15px; }
  .drop small { color:#8b95a7; display:block; margin-top:6px; }
  #status { text-align:center; color:#f5c63c; font-size:14px; padding:6px 12px 10px; }
  .tabs { display:flex; justify-content:center; gap:8px; margin:0 auto 14px; max-width:760px; }
  .tab { padding:8px 22px; border-radius:999px; border:1px solid #2b3444; background:#10141c;
         color:#cfd6e2; cursor:pointer; font-weight:600; font-size:13px; }
  .tab.on { background:#f5c63c; color:#111; border-color:#f5c63c; }
  h2.sec { font-size:14px; text-transform:uppercase; letter-spacing:.08em;
           color:#8b95a7; margin:20px 18px 10px; text-align:center; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr));
          gap:12px; padding:0 16px 30px; max-width:1200px; margin:0 auto; }
  .card { background:#131722; border:1px solid #232b3a; border-radius:12px;
          overflow:hidden; cursor:pointer; transition:.15s; }
  .card:hover { border-color:#f5c63c; transform:translateY(-2px); }
  .thumbbox { width:100%; aspect-ratio:16/9; background:#000; display:flex;
              align-items:center; justify-content:center; font-size:44px; }
  .card img { width:100%; aspect-ratio:16/9; object-fit:cover; background:#000; display:block; }
  .card .body { padding:10px 12px 12px; }
  .card .name { font-size:12px; color:#cfd6e2; word-break:break-all; }
  .card .meta { font-size:11px; color:#8b95a7; margin-top:4px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:10px;
           font-weight:700; letter-spacing:.04em; margin-bottom:6px; }
  .b-ok { background:#12351f; color:#4ade80; }
  .b-vo { background:#2a1235; color:#e08af5; }
  .b-wait { background:#352a12; color:#f5c63c; }
  .b-old { background:#22242c; color:#8b95a7; }
  .stats { display:flex; gap:8px; margin-top:6px; flex-wrap:wrap; }
  .stat { background:#0f131b; border:1px solid #232b3a; border-radius:8px;
          padding:4px 8px; font-size:11px; }
  .stat b { display:block; font-size:13px; }
  .sw { display:inline-block; width:12px; height:12px; border-radius:3px;
        margin:0 1px; border:1px solid #333; vertical-align:middle; }
  .detail { max-width:1000px; margin:0 auto 30px; padding:0 16px; display:none;
            flex-direction:column; gap:14px; }
  .detail video, .detail audio { width:100%; border-radius:10px; background:#000; }
  .card2 { background:#131722; border:1px solid #232b3a; border-radius:12px; padding:16px; }
  .card2 h3 { margin:0 0 12px; font-size:13px; text-transform:uppercase;
              letter-spacing:.08em; color:#8b95a7; }
  .dgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; }
  .metric { background:#0f131b; border:1px solid #232b3a; border-radius:10px; padding:10px; }
  .metric .k { font-size:10px; color:#8b95a7; text-transform:uppercase; }
  .metric .v { font-size:17px; font-weight:800; margin-top:3px; }
  pre { font-size:11px; white-space:pre-wrap; color:#8b95a7; max-height:200px; overflow:auto; }
  .tip { text-align:center; color:#8b95a7; font-size:12px; max-width:760px; margin:0 auto 20px; }
</style></head><body>
<header><h1>🎬 Style Lab — References + Voiceovers</h1>
<p class="sub">Drop reference videos (style analysis) or your voiceover audio (used in builds)</p></header>

<div class="drop" id="drop">
  <b>Drop files here (multiple allowed — videos AND audio)</b>
  <small>MP4 video → style analysis · MP3/WAV/M4A voiceover → audio profile · fast parallel upload</small>
  <input type="file" id="file" accept="video/*,audio/*" multiple hidden>
</div>
<div id="status"></div>

<div class="tabs">
  <div class="tab on" data-tab="all" onclick="setTab('all')">All</div>
  <div class="tab" data-tab="video" onclick="setTab('video')">🎬 References</div>
  <div class="tab" data-tab="audio" onclick="setTab('audio')">🎙 Voiceovers</div>
</div>

<div class="grid" id="lib"></div>

<div class="detail" id="detail">
  <div class="card2" id="mediaBox"><video id="player" controls playsinline></video></div>
  <div class="card2"><h3>Profile</h3><div class="dgrid" id="metrics"></div></div>
  <div class="card2"><h3>Report</h3><pre id="report"></pre></div>
</div>

<script>
const drop = document.getElementById('drop'), fi = document.getElementById('file');
drop.onclick = () => fi.click();
drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
drop.ondragleave = () => drop.classList.remove('over');
drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over');
  uploadMany([...e.dataTransfer.files]); };
fi.onchange = () => { uploadMany([...fi.files]); fi.value=''; };
let CURRENT_TAB = 'all';

function setTab(t) {
  CURRENT_TAB = t;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('on', x.dataset.tab === t));
  refresh();
}

async function uploadMany(files) {
  if (!files.length) return;
  for (let n = 0; n < files.length; n++) {
    document.getElementById('status').textContent = `Uploading file ${n+1} of ${files.length}: ${files[n].name}`;
    await upload(files[n]);
  }
  refresh();
}

async function upload(file) {
  const st = document.getElementById('status');
  const CHUNK = 8*1024*1024, CONC = 6;
  const total = Math.max(1, Math.ceil(file.size/CHUNK));
  const job = Date.now().toString(36) + Math.random().toString(36).slice(2,8);
  let sent = 0, next = 0; const t0 = performance.now();
  st.textContent = `Uploading ${file.name} (${(file.size/1e6).toFixed(1)} MB, ${CONC} parallel)…`;
  async function send(i) {
    const blob = file.slice(i*CHUNK, Math.min((i+1)*CHUNK, file.size));
    await fetch(`/chunk?job=${job}&index=${i}&total=${total}`, {method:'POST', body: blob});
    sent += blob.size;
    const mbps = sent/1e6/Math.max((performance.now()-t0)/1000, 0.01);
    st.innerHTML = `Uploading… <b>${Math.round(sent/file.size*100)}%</b> — ${(sent/1e6).toFixed(1)}/${(file.size/1e6).toFixed(1)} MB — <b>${mbps.toFixed(1)} MB/s</b>`;
  }
  async function worker() { while (next < total) { const i = next++; try { await send(i); } catch(e) { st.textContent='Upload failed: '+e; return; } } }
  await Promise.all(Array.from({length: Math.min(CONC,total)}, worker));
  const isAudio = /\.(mp3|wav|m4a|aac|ogg|opus|flac|aiff|aif|wma)$/i.test(file.name);
  st.textContent = isAudio ? 'Upload complete ✓ — analyzing audio…' : 'Upload complete ✓ — analyzing…';
  const r = await fetch(`/complete?job=${job}&name=${encodeURIComponent(file.name)}`, {method:'POST'});
  const j = await r.json();
  if (j.error) { st.textContent = 'Error: '+j.error; return; }
  await fetch(`/analyze?job=${job}&file=${encodeURIComponent(j.file)}`, {method:'POST'});
  poll(j.job, j.file);
}

async function poll(job, file) {
  const st = document.getElementById('status');
  for (let i = 0; i < 240; i++) {
    await new Promise(res => setTimeout(res, 1000));
    const jobs = await (await fetch('/jobs')).json();
    const j = jobs[job];
    if (!j) continue;
    if (j.state === 'error') { st.textContent = 'Error: '+j.error; return; }
    if (j.state === 'done') { st.textContent = ''; refresh(); if (file) openDetail(j.result, file, job); return; }
    st.textContent = `Analyzing… ${j.progress || 10}%`;
  }
}

async function refresh() {
  const lib = await (await fetch('/library')).json();
  const grid = document.getElementById('lib');
  const items = lib.filter(e => CURRENT_TAB === 'all' || e.kind === CURRENT_TAB);
  grid.innerHTML = items.map(e => {
    const isVo = e.kind === 'audio';
    const b = e.analyzed
      ? (e.exists ? `<span class="badge ${isVo ? 'b-vo' : 'b-ok'}">${isVo ? 'VOICEOVER' : 'ANALYZED'}</span>`
                  : '<span class="badge b-old">REPORT ONLY</span>')
      : '<span class="badge b-wait">UPLOADED — analyze</span>';
    let stats;
    if (e.analyzed && isVo) {
      stats = `<div class="stats">
        <span class="stat"><b>${e.duration}s</b>length</span>
        <span class="stat"><b>${e.sample_rate||'?'}</b>Hz</span>
        <span class="stat"><b>${e.loudness_db ?? '?'}</b>dB</span>
      </div>
      <div class="meta" style="margin-top:6px">${e.codec||''} · ${e.channels||''}</div>`;
    } else if (e.analyzed) {
      stats = `<div class="stats">
        <span class="stat"><b>${e.median}s</b>median cut</span>
        <span class="stat"><b>${e.frozen}%</b>frozen</span>
        <span class="stat"><b>${e.camera}%</b>camera</span>
        <span class="stat"><b>${e.duration}s</b>length</span>
      </div>
      <div class="meta" style="margin-top:6px">${(e.palette||[]).map(c=>`<span class="sw" style="background:${c}"></span>`).join('')} ${e.camera_est}</div>`;
    } else {
      stats = `<div class="meta">${(e.size/1e6).toFixed(1)} MB — not analyzed yet</div>`;
    }
    const thumb = isVo
      ? '<div class="thumbbox">🎙</div>'
      : `<img src="/thumb?file=${encodeURIComponent(e.file)}" loading="lazy" onerror="this.style.visibility='hidden'">`;
    return `<div class="card" data-id="${e.id}" data-file="${e.file}" data-kind="${e.kind}" data-analyzed="${e.analyzed}" data-report="${e.report||''}">
      ${thumb}<div class="body">${b}<div class="name">${e.file}</div>${stats}</div></div>`;
  }).join('');
  grid.querySelectorAll('.card').forEach(c => c.onclick = () => cardClick(c));
}

async function cardClick(card) {
  const id = card.dataset.id, file = card.dataset.file, report = card.dataset.report;
  if (card.dataset.analyzed === 'true' && report) {
    const data = await (await fetch('/report/' + report)).json();
    openDetail(data, file, id);
  } else {
    document.getElementById('status').textContent = 'Analyzing ' + file + '…';
    await fetch(`/analyze?job=${id}&file=${encodeURIComponent(file)}`, {method:'POST'});
    poll(id, file);
  }
}

function openDetail(p, file, id) {
  const d = document.getElementById('detail');
  d.style.display = 'flex';
  const isVo = p.kind === 'audio';
  const box = document.getElementById('mediaBox');
  const pl = document.getElementById('player');
  const base = isVo ? '/voiceovers/' : '/uploads/';
  if (isVo) {
    const au = document.createElement('audio');
    au.controls = true; au.autoplay = false;
    au.src = base + file;
    box.innerHTML = '';
    box.appendChild(au);
  } else {
    box.innerHTML = '<video id="player" controls playsinline></video>';
    const v = box.querySelector('video');
    v.src = base + file;
  }
  const met = isVo
    ? [['Duration', p.duration+'s'], ['Codec', p.codec||'?'],
       ['Sample rate', (p.sample_rate||'?')+' Hz'], ['Channels', p.channels||'?'],
       ['Mean loudness', (p.loudness_db ?? '?')+' dB']]
    : (() => { const c = p.cut_cadence, m = p.motion_budget;
      return [['Duration', p.duration+'s'], ['FPS', p.fps||'?'], ['Shots', p.shots],
        ['Median cut', c.median+'s'], ['Range', c.min+'–'+c.max+'s'],
        ['Frozen', m.frozen_pct+'%'], ['Camera', m.camera_pct+'%'], ['Character', m.character_pct+'%'],
        ['Brightness', p.brightness], ['Camera style', p.camera_estimate]]; })();
  document.getElementById('metrics').innerHTML = met.map(([k,v]) =>
    `<div class="metric"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
  document.getElementById('report').textContent = JSON.stringify(p, null, 2).slice(0, 5000);
  d.scrollIntoView({behavior:'smooth'});
}

refresh();
</script></body></html>"""


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Style Lab (videos+voiceovers) on http://0.0.0.0:{PORT}", flush=True)
    srv.serve_forever()
