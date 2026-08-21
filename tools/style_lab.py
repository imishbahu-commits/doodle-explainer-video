#!/usr/bin/env python3
"""Style Lab — upload a reference video, get an instant style profile.

Drop any MP4 (or paste a URL for yt-dlp), the server:
  1. saves it in seconds (local disk)
  2. runs a motion autopsy in a background thread (6fps frame sampling):
     cuts + shot table, motion budget, camera moves, dominant colors,
     brightness, fps/resolution
  3. shows a live STYLE PROFILE + player, and saves the report to
     style-reports/<name>.json so the agent can rebuild to that spec.

Usage: python3 style_lab.py [port]
"""
import io
import json
import math
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
UPLOADS = HERE / "uploads"
REPORTS = HERE / "style-reports"
UPLOADS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

FF = None
try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass
if not FF or not Path(FF).exists():
    for cand in ["ffmpeg", "/usr/bin/ffmpeg", str(Path(sys.prefix) / "bin" / "ffmpeg")]:
        p = subprocess.run(["which", cand], capture_output=True, text=True)
        if p.returncode == 0:
            FF = p.stdout.strip()
            break
if not FF:
    FF = "ffmpeg"

SAMPLE_FPS = 6
GW, GH = 480, 270
STATUS = {}   # job_id -> {state, progress, result, error}


# ------------------------------------------------------------------ utils
def probe(path):
    p = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    dur, fps = None, None
    w = h = None
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
    return {"duration": dur, "fps": fps, "w": w, "h": h}


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
    """Full motion autopsy -> style profile dict. STREAMING (low memory):
    frames are consumed one at a time; only tiny stats are kept, so even
    long videos analyze in seconds without eating memory."""
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
        profile = analyze(path)
        rep = save_report(job_id, profile)
        STATUS[job_id] = {"state": "done", "progress": 100,
                          "result": profile, "report": rep.name}
    except Exception as e:
        STATUS[job_id] = {"state": "error", "error": str(e)}


# ------------------------------------------------------------------ server
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
JOBS = {}


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

    def do_GET(self):
        path = self.path.split("?")[0]
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
        if path.startswith("/report/"):
            name = path.split("/")[-1]
            f = REPORTS / name
            if f.exists():
                self._send(200, f.read_text(), "application/json")
            else:
                self._send(404, "not found")
            return
        # static uploads
        m = re.match(r"/uploads/(.+)", path)
        if m:
            f = UPLOADS / m.group(1)
            if f.is_file():
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
                return
            self._send(404, "not found")
            return
        self._send(404, "not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        # ---- chunked upload: POST /chunk?job=X&index=N&total=T (raw bytes)
        if path == "/chunk":
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
            job = params.get("job", "")
            idx = int(params.get("index", 0))
            total = int(params.get("total", 1))
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length) if length else b""
            # per-index part file -> parallel-safe (concatenated on /complete)
            part = UPLOADS / f"{job}.part.{idx:05d}"
            part.write_bytes(data)
            self._json({"job": job, "index": idx, "total": total, "bytes": len(data)})
            return
        # ---- finish chunked: POST /complete?job=X&name=FILE.mp4
        if path == "/complete":
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
            job = params.get("job", "")
            name = params.get("name", "video.mp4")
            safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
            parts = sorted(UPLOADS.glob(f"{job}.part.*"))
            if not parts:
                self._json({"error": "no chunks for job"}, 400)
                return
            dest = UPLOADS / f"{job}_{safe}"
            with open(dest, "wb") as out:
                for p in parts:
                    out.write(p.read_bytes())
                    p.unlink()
            self._json({"job": job, "file": dest.name, "uploaded": True})
            return
        # ---- analyze an uploaded file: POST /analyze?job=X&file=NAME
        if path == "/analyze":
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
            job = params.get("job", "")
            f = UPLOADS / params.get("file", "")
            if not f.is_file():
                self._json({"error": "no uploaded file for job"}, 400)
                return
            threading.Thread(target=run_job, args=(job, str(f)), daemon=True).start()
            self._json({"job": job, "analyzing": True})
            return
        # ---- simple single-shot upload
        if path != "/upload":
            self._send(404, "not found")
            return
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._send(400, "multipart required")
            return
        # minimal multipart parse
        boundary = ctype.split("boundary=")[1].encode()
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        parts = body.split(b"--" + boundary)
        fname = None
        data = b""
        for part in parts:
            if b"filename=" in part.split(b"\r\n\r\n", 1)[0]:
                m = re.search(rb'filename="([^"]+)"', part)
                if m:
                    fname = m.group(1).decode("utf-8", "replace")
                    data = part.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]
        if not fname or not data:
            self._send(400, "no file")
            return
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", fname)
        job_id = f"{int(time.time()*1000)}"
        dest = UPLOADS / f"{job_id}_{safe}"
        dest.write_bytes(data)
        threading.Thread(target=run_job, args=(job_id, str(dest)), daemon=True).start()
        self._json({"job": job_id, "file": dest.name, "size": len(data)})

    def log_message(self, *a):
        pass


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Style Lab — reference video style analyzer</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#0b0d12; color:#e9edf4;
         font-family: system-ui,-apple-system,Segoe UI,sans-serif; }
  header { padding:22px 18px 8px; text-align:center; }
  h1 { font-size:20px; margin:0 0 4px; }
  .sub { font-size:13px; color:#8b95a7; margin:0 0 18px; }
  .drop { max-width:760px; margin:0 auto 18px; border:2px dashed #2b3444;
          border-radius:14px; padding:34px 20px; text-align:center;
          cursor:pointer; transition:.2s; background:#10141c; }
  .drop.over { border-color:#f5c63c; background:#161b26; }
  .drop b { font-size:16px; }
  .drop small { color:#8b95a7; display:block; margin-top:8px; }
  .urlbar { max-width:760px; margin:0 auto 20px; display:flex; gap:8px; }
  .urlbar input { flex:1; padding:10px 14px; border-radius:10px; border:1px solid #2b3444;
                  background:#10141c; color:#e9edf4; font-size:13px; }
  .urlbar button { padding:10px 18px; border-radius:10px; border:0;
                   background:#f5c63c; color:#111; font-weight:700; cursor:pointer; }
  .wrap { max-width:1000px; margin:0 auto; padding:0 16px 40px; display:flex;
          flex-direction:column; gap:18px; }
  .card { background:#131722; border:1px solid #232b3a; border-radius:12px; padding:16px; }
  .card h2 { margin:0 0 12px; font-size:14px; text-transform:uppercase;
             letter-spacing:.08em; color:#8b95a7; }
  video { width:100%; border-radius:10px; background:#000; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }
  .metric { background:#0f131b; border:1px solid #232b3a; border-radius:10px; padding:12px; }
  .metric .k { font-size:11px; color:#8b95a7; text-transform:uppercase; }
  .metric .v { font-size:20px; font-weight:800; margin-top:4px; }
  .metric .v small { font-size:12px; color:#8b95a7; font-weight:500; }
  table { width:100%; border-collapse:collapse; font-size:12px; }
  th, td { padding:6px 8px; text-align:right; border-bottom:1px solid #1c2230; }
  th:first-child, td:first-child { text-align:left; }
  .swatch { display:inline-block; width:14px; height:14px; border-radius:4px;
            margin-right:6px; vertical-align:middle; border:1px solid #333; }
  #status { text-align:center; color:#f5c63c; font-size:14px; padding:8px; }
  .badge { display:inline-block; padding:2px 10px; border-radius:999px;
           background:#1a202b; color:#cfd6e2; font-size:12px; margin:2px; }
</style></head><body>
<header><h1>🎬 Style Lab</h1>
<p class="sub">Drop a reference video → instant style profile → the agent builds your video to match</p></header>
<div class="drop" id="drop">
  <b>Drop a video here</b>
  <small>MP4 · any length · analyzed in seconds (cuts, zooms, motion budget, colors)</small>
  <input type="file" id="file" accept="video/*" hidden>
</div>
<div class="urlbar">
  <input id="url" placeholder="…or paste a video URL (yt-dlp)">
  <button onclick="fetchUrl()">Grab URL</button>
</div>
<div id="status"></div>
<div class="wrap" id="main" style="display:none">
  <div class="card"><video id="player" controls playsinline></video></div>
  <div class="card"><h2>Style profile</h2><div class="grid" id="metrics"></div></div>
  <div class="card"><h2>Shot table</h2><div style="overflow:auto"><table id="shots"></table></div></div>
  <div class="card"><h2>Analysis report</h2><pre id="report" style="font-size:12px;white-space:pre-wrap;color:#8b95a7;max-height:220px;overflow:auto"></pre></div>
</div>
<script>
const drop = document.getElementById('drop'), fi = document.getElementById('file');
drop.onclick = () => fi.click();
drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
drop.ondragleave = () => drop.classList.remove('over');
drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over');
  uploadMany([...e.dataTransfer.files]); };
fi.onchange = () => { uploadMany([...fi.files]); fi.value = ''; };

// queue: uploads EVERY dropped file one after another (fixes multi-drop)
let qBusy = false;
async function uploadMany(files) {
  if (!files.length) return;
  const st = document.getElementById('status');
  for (let n = 0; n < files.length; n++) {
    st.textContent = `Uploading file ${n+1} of ${files.length}: ${files[n].name}`;
    await upload(files[n], files.length, n + 1);
  }
}

async function upload(file, totalFiles = 1, fileNum = 1) {
  const st = document.getElementById('status');
  const CHUNK = 4 * 1024 * 1024;            // 4 MB chunks
  const CONC = 4;                           // 4 parallel uploads
  const total = Math.max(1, Math.ceil(file.size / CHUNK));
  const job = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  let sent = 0, next = 0;
  const t0 = performance.now();
  st.textContent = `Uploading ${file.name} (${(file.size/1e6).toFixed(1)} MB in ${total} chunks, ${CONC} parallel)…`;
  async function send(i) {
    const blob = file.slice(i * CHUNK, Math.min((i + 1) * CHUNK, file.size));
    await fetch(`/chunk?job=${job}&index=${i}&total=${total}`, {method: 'POST', body: blob});
    sent += blob.size;
    const el = (performance.now() - t0) / 1000;
    const mbps = sent / 1e6 / Math.max(el, 0.01);
    const pct = Math.round(sent / file.size * 100);
    st.innerHTML = `Uploading… <b>${pct}%</b> — ${(sent/1e6).toFixed(1)}/${(file.size/1e6).toFixed(1)} MB — <b>${mbps.toFixed(1)} MB/s</b> (${CONC} parallel)`;
  }
  async function worker() {
    while (next < total) {
      const i = next++;
      try { await send(i); } catch (e) { st.textContent = 'Upload failed at chunk ' + i + ': ' + e; return; }
    }
  }
  await Promise.all(Array.from({length: Math.min(CONC, total)}, worker));
  st.textContent = 'Upload complete ✓ — starting analysis…';
  const r = await fetch(`/complete?job=${job}&name=${encodeURIComponent(file.name)}`, {method: 'POST'});
  const j = await r.json();
  if (j.error) { st.textContent = 'Error: ' + j.error; return; }
  await fetch(`/analyze?job=${job}&file=${encodeURIComponent(j.file)}`, {method: 'POST'});
  poll(j.job, j.file);
}

async function fetchUrl() {
  const url = document.getElementById('url').value.trim();
  if (!url) return;
  const st = document.getElementById('status');
  st.textContent = 'Trying to grab URL… (note: YouTube is blocked in this sandbox)';
  const r = await fetch('/upload?url=' + encodeURIComponent(url), {method:'POST'});
  const j = await r.json();
  if (j.error) { st.textContent = j.error; return; }
  st.textContent = 'Downloaded. Analyzing…';
  poll(j.job, j.file);
}

async function poll(job, file) {
  const st = document.getElementById('status');
  for (let i = 0; i < 120; i++) {
    await new Promise(res => setTimeout(res, 1000));
    const r = await fetch('/jobs');
    const jobs = await r.json();
    const j = jobs[job];
    if (!j) continue;
    if (j.state === 'error') { st.textContent = 'Error: ' + j.error; return; }
    if (j.state === 'done') {
      st.textContent = '';
      show(j.result, file, job);
      return;
    }
    st.textContent = `Analyzing… ${j.progress || 10}%`;
  }
  st.textContent = 'Timed out';
}

function show(p, file, job) {
  document.getElementById('main').style.display = 'flex';
  const pl = document.getElementById('player');
  pl.src = '/uploads/' + file;
  const c = p.cut_cadence, m = p.motion_budget;
  const met = [
    ['Shots', p.shots], ['Median cut', c.median + 's'],
    ['Mean cut', c.mean + 's'], ['Range', c.min + '–' + c.max + 's'],
    ['Duration', p.duration + 's'], ['FPS', p.fps || '?'],
    ['Frozen', m.frozen_pct + '%'], ['Camera', m.camera_pct + '%'],
    ['Character', m.character_pct + '%'],
    ['Brightness', p.brightness],
    ['Camera style', p.camera_estimate],
  ];
  document.getElementById('metrics').innerHTML = met.map(([k,v]) =>
    `<div class="metric"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
  document.getElementById('metrics').insertAdjacentHTML('beforeend',
    `<div class="metric"><div class="k">Palette</div><div class="v" style="font-size:14px">` +
    p.palette.map(c => `<span class="swatch" style="background:${c}"></span>`).join('') + `</div></div>`);
  const rows = p.shot_table.map((s,i) =>
    `<tr><td>${i+1}</td><td>${s.start}s</td><td>${s.dur}s</td>
     <td>${s.frozen}%</td><td>${s.cam}%</td><td>${s.active}%</td></tr>`).join('');
  document.getElementById('shots').innerHTML =
    `<tr><th>#</th><th>start</th><th>dur</th><th>frozen</th><th>camera</th><th>char</th></tr>` + rows;
  document.getElementById('report').textContent =
    JSON.stringify(p, null, 2).slice(0, 4000);
  document.title = 'Style Lab — ' + p.file;
}
</script></body></html>"""


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Style Lab on http://0.0.0.0:{PORT}  (uploads -> {UPLOADS}, reports -> {REPORTS})", flush=True)
    srv.serve_forever()
