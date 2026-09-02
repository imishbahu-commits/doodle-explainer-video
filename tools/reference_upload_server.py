#!/usr/bin/env python3
"""Reference-video upload server (superfast, parallel, chunked).

Purpose
-------
A tiny, dependency-light dev server that lets the user hand a reference video
into the workspace from their browser. The browser can reach hosts the sandbox
firewall blocks, so the page is served here and the user picks/drops the file
in the live preview.

The uploader is optimised for speed:
  * the file is split into chunks and up to ``WORKERS`` chunks are POSTed in
    parallel (this is the single biggest win — it saturates several
    connections at once instead of one long sequential stream);
  * each chunk is written straight to disk as a part file;
  * ``/done`` streams the parts together (no full-file load in memory);
  * live Mbps + ETA are shown so the user can see the transfer is fast.

After assembly the video is probed (ffmpeg) for duration / resolution / fps so
the downstream doodle-explainer analysis has the specs immediately.

The upload control is a native ``<label for="file">`` so the file picker opens
without any JavaScript — that reliable even inside a sandboxed preview iframe.

Endpoints
---------
GET  /            -> upload page
GET  /files       -> JSON list of uploaded files
POST /part?name=&index=&total=   -> save one chunk (raw body) to uploads/.parts/
POST /done?name=&total=          -> assemble parts into uploads/<name>, probe, return JSON

Tuning (all optional):
  --port      int      bind port          (default 8013)
  --dir PATH           upload directory   (default <repo>/uploads)
  --chunk MB   int     chunk size (MB)     (default 8)
  --workers N  int     parallel streams   (default 8)
  --max-mb N   int     max file (MB)      (default 2048)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO_ROOT / "uploads"

PORT = 8013
UPLOAD_DIR = Path(DEFAULT_DIR)
PARTS_DIR = UPLOAD_DIR / ".parts"
CHUNK_MB = 4
WORKERS = 8
MAX_TOTAL = 2048 * 1024 * 1024  # 2 GiB

# 4 MiB is a proven-safe size under common reverse-proxy request limits and
# stays comfortably portable. 8 workers x 4 MiB = 32 MiB in flight, still very
# fast. Tune with --chunk and --workers.
CHUNK = CHUNK_MB * 1024 * 1024


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w.\-]", "_", name or "reference.mp4")
    return name if name else "reference.mp4"


# --------------------------------------------------------------------------
# Optional metadata probe (best effort — never blocks the upload).
# --------------------------------------------------------------------------
def _ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe_video(path: Path) -> dict:
    """Return {duration, width, height, fps, video_codec, audio} or {}."""
    ffmpeg = _ffmpeg_bin()
    if not ffmpeg:
        return {}
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(path)],
            capture_output=True, text=True, timeout=60,
        )
    except Exception:
        return {}
    err = proc.stderr
    out: dict = {}

    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        out["duration"] = h * 3600 + mn * 60 + s

    m = re.search(
        r"Stream #\d+:\d+.*?Video:\s*([^\s,]+).*?(\d{2,5})x(\d{2,5}).*?([\d.]+)\s*fps",
        err,
    )
    if m:
        out["video_codec"] = m.group(1)
        out["width"] = int(m.group(2))
        out["height"] = int(m.group(3))
        out["fps"] = float(m.group(4))

    m = re.search(r"Stream #\d+:\d+.*?Audio:\s*([^\s,]+)", err)
    if m:
        out["audio_codec"] = m.group(1)

    return out


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GB"


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload Reference Video — Doodle Explainer</title>
<style>
  :root {
    --bg:#0b0e16; --card:#151a26; --card2:#1b2130; --line:#2a3040;
    --txt:#ecf0f7; --sub:#9aa4b8; --accent:#f5c63c; --accent2:#7ee08a;
    --danger:#ff8080; --blue:#4da3ff;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--txt);
         font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         min-height:100vh; display:flex; align-items:center; justify-content:center;
         padding:18px 12px; }
  .wrap { width:100%; max-width:640px; }
  header { text-align:center; margin-bottom:14px; }
  h1 { font-size:21px; margin:0 0 6px; }
  .sub { color:var(--sub); font-size:13px; margin:0; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:16px;
          padding:20px; margin-bottom:16px; }
  .card h2 { font-size:13px; color:var(--sub); letter-spacing:.04em;
             text-transform:uppercase; margin:0 0 10px; }

  /* The upload area is a native <label> so clicking it always opens the picker. */
  label.drop { display:block; border:2px dashed #3b4356; border-radius:12px;
               padding:28px 16px; text-align:center; cursor:pointer; transition:.18s; }
  label.drop.drag { border-color:var(--blue); background:#17222f; }
  label.drop .ic { font-size:34px; }
  label.drop .big { font-size:17px; font-weight:700; margin:8px 0 4px; }
  label.drop .hint { color:var(--sub); font-size:13px; }
  label.drop .hint b { color:var(--accent2); }
  input[type=file] { display:none; }

  .file { display:none; align-items:center; gap:12px; background:var(--card2);
          border:1px solid var(--line); border-radius:10px; padding:12px 14px; margin-top:14px; }
  .file .ic { font-size:22px; }
  .file .meta { flex:1; min-width:0; }
  .file .nm { font-weight:600; font-size:14px; word-break:break-all; }
  .file .sz { color:var(--sub); font-size:12px; margin-top:2px; }
  .file .rm { background:none; border:0; color:var(--sub); font-size:16px; cursor:pointer; }

  button { border:0; border-radius:11px; font-weight:700; font-size:15px;
           cursor:pointer; padding:15px 18px; transition:.15s; }
  .btn-up { width:100%; margin-top:16px; background:var(--accent); color:#000; }
  .btn-up:hover { filter:brightness(1.06); }
  .btn-up:disabled { background:#3a3f4c; color:#7a8190; cursor:not-allowed; }

  #bar { display:none; margin-top:16px; }
  .track { height:14px; background:#0d1220; border-radius:8px; overflow:hidden; border:1px solid var(--line); }
  #fill { height:100%; width:0%; background:linear-gradient(90deg,var(--accent),var(--accent2));
          transition:width .18s; }
  #stats { display:flex; justify-content:space-between; margin-top:8px; color:var(--sub);
           font-size:12.5px; }
  #status { margin-top:12px; font-size:13px; min-height:20px; white-space:pre-wrap; }
  .ok { color:var(--accent2); } .err { color:var(--danger); }

  #result { display:none; margin-top:16px; background:#0f1522; border:1px solid #2b3b4a;
            border-radius:12px; padding:16px; }
  #result h3 { font-size:15px; margin:0 0 10px; color:var(--accent2); }
  .kv { display:grid; grid-template-columns:auto 1fr; gap:5px 14px; font-size:13px;
        color:var(--sub); }
  .kv b { color:var(--txt); font-weight:600; }
  .path { display:flex; gap:8px; align-items:center; background:#0a0f1a; border:1px solid var(--line);
          border-radius:8px; padding:9px 12px; margin:12px 0; }
  .path code { flex:1; font-family:ui-monospace,Menlo,Consolas,monospace; font-size:12.5px;
               color:#cfe0ff; word-break:break-all; }
  .copy { background:var(--blue); color:#04121f; border-radius:8px; padding:8px 12px; font-size:13px; }
  .btn-again { background:transparent; color:var(--sub); border:1px solid var(--line); width:100%; }

  #files { display:flex; flex-direction:column; gap:8px; }
  .fitem { display:flex; align-items:center; gap:10px; background:var(--card2);
           border:1px solid var(--line); border-radius:9px; padding:9px 12px; }
  .fitem .ic { font-size:18px; }
  .fitem .m { flex:1; min-width:0; }
  .fitem .n { font-size:13px; font-weight:600; word-break:break-all; }
  .fitem .s { font-size:11px; color:var(--sub); }
  .empty { color:var(--sub); font-size:13px; text-align:center; padding:8px; }
  .note { color:var(--sub); font-size:12px; margin-top:2px; text-align:center;
          line-height:1.7; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🎬 Upload your reference video</h1>
    <p class="sub">Send it into the doodle-explainer workspace — superfast.</p>
  </header>

  <div class="card">
    <h2>1 · Pick a video</h2>
    <label for="file" id="drop" class="drop">
      <div class="ic">🎞️</div>
      <div class="big">Tap here to choose a video</div>
      <div class="hint">…or drag &amp; drop the file anywhere on this box.</div>
    </label>
    <input type="file" id="file" accept="video/*,.mp4,.mov,.mkv,.webm,.avi,.m4v,.ts">

    <div class="file" id="fileCard">
      <div class="ic">🎬</div>
      <div class="meta">
        <div class="nm" id="fname"></div>
        <div class="sz" id="fsize"></div>
      </div>
      <button class="rm" id="fclear" title="Remove">✕</button>
    </div>

    <button class="btn-up" id="upload" disabled>⬆ Upload now</button>

    <div id="bar">
      <div class="track"><div id="fill"></div></div>
      <div id="stats">
        <span id="pct">0%</span>
        <span id="speed">—</span>
        <span id="eta">—</span>
      </div>
    </div>

    <div id="status"></div>

    <div id="result">
      <h3>✅ Reference video saved</h3>
      <div class="kv" id="meta"></div>
      <div class="path">
        <code id="pth"></code>
        <button class="copy" id="copy">Copy</button>
      </div>
      <button class="btn-again" id="again">⬆ Upload another</button>
    </div>
  </div>

  <div class="card">
    <h2>Already in the workspace</h2>
    <div id="files"><div class="empty">Loading…</div></div>
  </div>

  <p class="note">Transfer uses __WORKERS__ parallel streams of __CHUNK_MB__ MB.
  Tune with <code>?workers=N&amp;chunk=N</code> in the URL.</p>
</div>

<script>
// __CHUNK_MB__ is an integer number of megabytes. Chunk size is MB * 1 MiB.
const DEFAULTS = { CHUNK_MB: __CHUNK_MB__, WORKERS: __WORKERS__, MAX: __MAXTOTAL__ };
const q = new URLSearchParams(location.search);
const CHUNK_MB = parseInt(q.get('chunk')) || DEFAULTS.CHUNK_MB;
const CHUNK    = CHUNK_MB * 1024 * 1024;
const WORKERS  = parseInt(q.get('workers')) || DEFAULTS.WORKERS;
const MAX      = DEFAULTS.MAX;

const drop = document.getElementById('drop');
const file = document.getElementById('file');
const fileCard = document.getElementById('fileCard');
const fname = document.getElementById('fname');
const fsize = document.getElementById('fsize');
const fclear = document.getElementById('fclear');
const uploadBtn = document.getElementById('upload');
const bar = document.getElementById('bar');
const fill = document.getElementById('fill');
const pct = document.getElementById('pct');
const speed = document.getElementById('speed');
const eta = document.getElementById('eta');
const status = document.getElementById('status');
const result = document.getElementById('result');
const meta = document.getElementById('meta');
const pth = document.getElementById('pth');
const copyBtn = document.getElementById('copy');
const againBtn = document.getElementById('again');
const filesBox = document.getElementById('files');

let current = null;

function fmtSize(n) {
  if (n < 1024) return n + ' B';
  if (n < 1048576) return (n/1024).toFixed(1) + ' KB';
  if (n < 1073741824) return (n/1048576).toFixed(1) + ' MB';
  return (n/1073741824).toFixed(2) + ' GB';
}
function setStatus(m, cls) { status.className = cls || ''; status.textContent = m; }

function showFile(f) {
  current = f;
  fname.textContent = f.name;
  fsize.textContent = fmtSize(f.size) + ' · ' + Math.max(1, Math.round(f.size / CHUNK)) + ' pieces';
  fileCard.style.display = 'flex';
  uploadBtn.disabled = false;
}

// Native picker — <label for="file"> handles the click, no JS required.
file.addEventListener('change', () => { if (file.files.length) showFile(file.files[0]); });
drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag'); });
drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
drop.addEventListener('drop', e => {
  e.preventDefault(); drop.classList.remove('drag');
  if (e.dataTransfer.files.length) { file.files = e.dataTransfer.files; showFile(e.dataTransfer.files[0]); }
});
fclear.addEventListener('click', () => {
  current = null; file.value = ''; fileCard.style.display = 'none'; uploadBtn.disabled = true;
});

function setProgress(uploaded, fsizeBytes, startedMs) {
  const elapsed = Math.max((performance.now() - startedMs) / 1000, 0.05);
  const p = Math.min(uploaded / fsizeBytes, 1);
  const mbps = (uploaded * 8) / 1e6 / elapsed;
  const remaining = Math.max(fsizeBytes - uploaded, 0);
  const sec = mbps > 0 ? Math.ceil(remaining * 8 / 1e6 / mbps) : 0;
  fill.style.width = (p * 100).toFixed(1) + '%';
  pct.textContent = (p * 100).toFixed(0) + '%';
  speed.textContent = mbps.toFixed(1) + ' Mbps';
  eta.textContent = sec > 0 ? '~' + sec + 's left' : 'finalizing…';
}

async function doUpload() {
  if (!current) return;
  const f = current;
  if (f.size > MAX) { setStatus('⚠ File too big (' + fmtSize(f.size) + '). Max is ' + fmtSize(MAX) + '.', 'err'); return; }
  if (f.size === 0) { setStatus('⚠ That file is empty.', 'err'); return; }

  bar.style.display = 'block';
  result.style.display = 'none';
  fill.style.width = '0%';
  uploadBtn.disabled = true;
  setStatus('Starting ' + WORKERS + ' parallel streams…');

  const name = encodeURIComponent(f.name);
  const total = Math.ceil(f.size / CHUNK);
  const started = performance.now();
  let next = 0, completed = 0, uploaded = 0;

  async function worker() {
    while (true) {
      const i = next++;
      if (i >= total) return;
      const s = i * CHUNK;
      const slice = f.slice(s, Math.min(s + CHUNK, f.size));
      let r = null;
      for (let attempt = 0; attempt < 2; attempt++) {
        try {
          r = await fetch('/part?name=' + name + '&index=' + i + '&total=' + total,
                          { method: 'POST', body: slice });
          break;
        } catch (e) { if (attempt === 1) throw e; }
      }
      if (!r.ok) throw new Error('piece ' + i + ' rejected (HTTP ' + r.status + ')');
      completed += 1; uploaded += slice.size;
      setProgress(uploaded, f.size, started);
    }
  }

  try {
    await Promise.all(Array.from({ length: Math.min(WORKERS, total) }, worker));
    if (completed !== total) throw new Error('not all pieces completed');
    setProgress(uploaded, f.size, started);
    setStatus('Assembling file & probing…');
    const d = await fetch('/done?name=' + name + '&total=' + total, { method: 'POST' });
    const res = await d.json().catch(() => ({}));
    if (!d.ok) throw new Error(res.error || ('assembly failed (HTTP ' + d.status + ')'));
    const elapsed = Math.max((performance.now() - started) / 1000, .05);
    pct.textContent = '100%';
    speed.textContent = (uploaded * 8 / 1e6 / elapsed).toFixed(1) + ' Mbps';
    eta.textContent = 'done';
    renderResult(res);
    setStatus('', 'ok');
    bar.style.display = 'none';
    loadFiles();
  } catch (e) {
    setStatus('❌ ' + e.message, 'err');
  } finally {
    uploadBtn.disabled = false;
  }
}

function fmtDur(s) {
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = (s%60).toFixed(1);
  return (h ? h + ':' : '') + String(m).padStart(2,'0') + ':' + String(sec).padStart(4,'0');
}
function renderResult(res) {
  result.style.display = 'block';
  pth.textContent = res.path || res.name;
  const rows = [['File', res.name], ['Size', fmtSize(res.size)], ['Saved at', res.path]];
  if (res.meta) {
    const m = res.meta;
    if (m.duration != null) rows.push(['Duration', fmtDur(m.duration)]);
    if (m.width && m.height) rows.push(['Resolution', m.width + ' × ' + m.height]);
    if (m.fps) rows.push(['Frame rate', (+m.fps).toFixed(2) + ' fps']);
    if (m.video_codec) rows.push(['Video codec', m.video_codec]);
    if (m.audio_codec) rows.push(['Audio codec', m.audio_codec]);
  }
  meta.innerHTML = rows.map(r => '<div>' + r[0] + '</div><div><b>' +
    (r[1] == null ? '—' : String(r[1]).replace(/</g,'&lt;')) + '</b></div>').join('');
}
async function loadFiles() {
  try {
    const r = await fetch('/files');
    const d = await r.json();
    const list = d.files || [];
    if (!list.length) {
      filesBox.innerHTML = '<div class="empty">Nothing here yet — upload one above ⬆</div>';
      return;
    }
    filesBox.innerHTML = list.map(f =>
      '<div class="fitem"><div class="ic">🎞️</div><div class="m">' +
      '<div class="n">' + String(f.name).replace(/</g,'&lt;') + '</div>' +
      '<div class="s">' + fmtSize(f.size) + ' · just now</div></div></div>').join('');
  } catch (e) {
    filesBox.innerHTML = '<div class="empty">Could not load.</div>';
  }
}
loadFiles();

uploadBtn.addEventListener('click', doUpload);
copyBtn.addEventListener('click', () => {
  const t = pth.textContent;
  const ok = () => { copyBtn.textContent = 'Copied ✓'; setTimeout(() => copyBtn.textContent = 'Copy', 1500); };
  (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(ok, () => {
    const a = document.createElement('textarea'); a.value = t;
    document.body.appendChild(a); a.select(); document.execCommand('copy'); a.remove(); ok();
  });
});
againBtn.addEventListener('click', () => {
  result.style.display = 'none'; bar.style.display = 'none';
  current = null; file.value = ''; fileCard.style.display = 'none'; uploadBtn.disabled = true;
  setStatus('');
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "RefUpload/1.0"

    def _send(self, code, body, ctype="application/json", headers=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj))

    def _params(self):
        q = urlparse(self.path).query
        out = {}
        for pair in q.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                out[k] = unquote(v)
        return out

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            html = (
                PAGE_TEMPLATE.replace("__WORKERS__", str(WORKERS))
                .replace("__CHUNK_MB__", str(CHUNK_MB))
                .replace("__MAXTOTAL__", str(MAX_TOTAL))
            )
            self._send(200, html, "text/html; charset=utf-8")
        elif path == "/files":
            if not UPLOAD_DIR.exists():
                self._json(200, {"files": []})
                return
            files = []
            for p in sorted(UPLOAD_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                if p.is_file() and not p.name.startswith("."):
                    files.append({
                        "name": p.name,
                        "size": p.stat().st_size,
                        "path": str(p),
                        "mtime": p.stat().st_mtime,
                    })
            self._json(200, {"files": files})
        else:
            self._json(404, {"error": "not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/part":
                self._part()
            elif path == "/done":
                self._done()
            else:
                self._json(404, {"error": "not found"})
        except Exception as e:
            try:
                self._json(500, {"error": f"server error: {e}"})
            except Exception:
                pass

    def _part(self):
        p = self._params()
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > CHUNK:
            self._json(413, {"error": "bad piece size"})
            return
        data = self.rfile.read(length)
        if len(data) != length:
            self._json(400, {"error": f"truncated piece: got {len(data)} of {length}"})
            return
        PARTS_DIR.mkdir(parents=True, exist_ok=True)
        part = PARTS_DIR / f"{safe_name(p.get('name', ''))}.{int(p.get('index', 0)):05d}"
        part.write_bytes(data)
        self._json(200, {"ok": True, "index": int(p.get("index", 0))})

    def _done(self):
        p = self._params()
        name = safe_name(p.get("name", ""))
        total = int(p.get("total", 0))
        if total <= 0:
            self._json(400, {"error": "invalid part count"})
            return

        part_paths = []
        total_bytes = 0
        for i in range(total):
            part = PARTS_DIR / f"{name}.{i:05d}"
            if not part.exists():
                self._json(400, {"error": f"missing part {i}"})
                return
            total_bytes += part.stat().st_size
            if total_bytes > MAX_TOTAL:
                self._json(413, {"error": "assembled file exceeds max size"})
                return
            part_paths.append(part)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        dest = UPLOAD_DIR / name
        assembling = dest.with_name(dest.name + ".assembling")
        with assembling.open("wb") as target:
            for part in part_paths:
                with part.open("rb") as src:
                    shutil.copyfileobj(src, target, length=1024 * 1024)
        assembling.replace(dest)

        for part in part_paths:
            try:
                part.unlink()
            except OSError:
                pass

        probe = probe_video(dest)
        print(f"UPLOADED {total_bytes / 1e6:.1f} MB -> {dest}", flush=True)
        self._json(200, {
            "ok": True,
            "name": dest.name,
            "size": total_bytes,
            "path": str(dest),
            "meta": probe,
        })

    def log_message(self, fmt, *args):
        sys.stderr.write("[upload] " + fmt % args + "\n")


def main():
    global PORT, UPLOAD_DIR, PARTS_DIR, CHUNK_MB, CHUNK, WORKERS, MAX_TOTAL
    args = sys.argv[1:]
    opts = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            opts[args[i].lstrip("-")] = args[i + 1]
            i += 2
        else:
            i += 1

    PORT = int(opts.get("port", os.environ.get("UPLOAD_PORT", "8013")))
    UPLOAD_DIR = Path(opts.get("dir", os.environ.get("UPLOAD_DIR", DEFAULT_DIR)))
    PARTS_DIR = UPLOAD_DIR / ".parts"
    CHUNK_MB = int(opts.get("chunk", os.environ.get("UPLOAD_CHUNK_MB", "8")))
    CHUNK = CHUNK_MB * 1024 * 1024
    WORKERS = int(opts.get("workers", os.environ.get("UPLOAD_WORKERS", "8")))
    MAX_TOTAL = int(opts.get("max-mb", os.environ.get("UPLOAD_MAX_MB", "2048"))) * 1024 * 1024

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"Reference uploader on http://0.0.0.0:{PORT} -> {UPLOAD_DIR} "
        f"(chunk {CHUNK_MB}MB x {WORKERS} workers)", flush=True
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
