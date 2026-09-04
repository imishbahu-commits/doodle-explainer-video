#!/usr/bin/env python3
"""Fast ingest — drop voiceovers + reference videos into the sandbox.

Designed to be fast through the preview proxy:
  • files ≤ 24 MB go in ONE POST (typical voiceover)
  • bigger files split into 4 MB chunks, 8 uploaded in parallel
  • server streams to disk (never holds the whole file in RAM)

  GET  /              upload page (voiceover + reference + extras)
  GET  /api/files     JSON library of what has landed
  POST /put?kind=&name=          raw body, streamed to disk
  POST /chunk?kind=&name=&id=&index=&total=
  POST /done?kind=&name=&id=&total=
  OPTIONS *           CORS

Run:  python3 tools/fast_ingest.py [port]     default 8088
Saves: uploads/inbox/{voiceover,reference,extra}/
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "uploads" / "inbox"
PARTS = ROOT / "uploads" / ".parts"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088

CHUNK_MAX = 8 * 1024 * 1024          # reject a single chunk bigger than this
PUT_MAX = 2 * 1024 * 1024 * 1024     # 2 GB
KINDS = ("video", "voiceover", "reference", "extra")

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dev upload — drop video into the sandbox</title>
<style>
  :root {
    --bg:#0e1017; --panel:#161a24; --panel2:#1d2230; --line:#262d3d;
    --text:#e9ecf3; --muted:#8b93a6; --accent:#ffd23f; --ok:#34d399; --bad:#f87171;
    --vo:#4da3ff; --ref:#ff8a4d;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }
  header { padding:16px 22px; border-bottom:1px solid var(--line); background:var(--panel);
           display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
  header h1 { font-size:17px; margin:0; }
  header .dot { width:9px; height:9px; border-radius:50%; background:var(--ok);
                box-shadow:0 0 10px var(--ok); }
  header .sub { color:var(--muted); font-size:12px; margin-left:auto; }
  main { max-width:980px; margin:0 auto; padding:22px 18px 60px; }
  .lead { color:var(--muted); font-size:14px; line-height:1.6; margin:0 0 18px; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  @media (max-width:720px) { .grid { grid-template-columns:1fr; } }
  .drop { background:var(--panel); border:1.5px dashed var(--line); border-radius:14px;
          padding:22px 18px; min-height:180px; cursor:pointer; transition:border-color .15s, background .15s; }
  .drop:hover, .drop.drag { border-color:var(--accent); background:var(--panel2); }
  .drop.video { border-color:#3d6a4a; min-height:240px; margin-bottom:14px; }
  .drop.vo { border-color:#2a4a70; }
  .drop.ref { border-color:#6a3d22; }
  .drop h2 { margin:0 0 6px; font-size:15px; }
  .drop p { margin:0; color:var(--muted); font-size:13px; line-height:1.5; }
  .drop .hint { margin-top:10px; font-size:12px; color:#6e7687; }
  input[type=file] { display:none; }
  .row { margin-top:16px; background:var(--panel); border:1px solid var(--line);
         border-radius:12px; padding:12px 14px; }
  .row .name { font-size:13px; font-weight:600; }
  .row .meta { font-size:11px; color:var(--muted); margin-top:2px; }
  .bar { height:10px; background:#11141c; border-radius:6px; overflow:hidden; margin-top:8px; }
  .fill { height:100%; width:0; background:var(--ok); }
  .fill.bad { background:var(--bad); }
  .ok { color:var(--ok); } .err { color:var(--bad); }
  .lib { margin-top:22px; }
  .lib h3 { font-size:12px; text-transform:uppercase; letter-spacing:1px; color:var(--muted); }
  .lib ul { list-style:none; padding:0; margin:0; }
  .lib li { font-size:13px; padding:8px 0; border-bottom:1px solid var(--line);
            display:flex; justify-content:space-between; gap:10px; }
  .lib .k { color:var(--vo); font-size:11px; text-transform:uppercase; letter-spacing:.6px; }
  .lib .k.video { color:#34d399; }
  .lib .k.reference { color:var(--ref); }
  code { background:#11141c; padding:1px 6px; border-radius:4px; font-size:12px; }
  .next { margin-top:18px; padding:14px 16px; background:var(--panel2); border-radius:12px;
          font-size:13px; line-height:1.6; color:#cfd6e4; }
</style>
</head>
<body>
<header>
  <span class="dot"></span>
  <h1>Dev upload</h1>
  <span class="sub">video → this sandbox</span>
</header>
<main>
  <p class="lead">Drop a video here. It is written straight into this workspace.
     After ✅, go back to chat and type <code>uploaded</code> — I read it from
     <code>uploads/inbox/video/</code>.</p>
  <label class="drop video" id="drop-video">
    <h2>🎬 Video</h2>
    <p>mp4 / mov / webm / mkv. Click or drag. Keep the tab open until it hits 100%.</p>
    <p class="hint">Big files: 8 MB × 8 parallel chunks. Small files: one shot.</p>
    <input type="file" id="file-video" accept="video/*,.mp4,.mov,.webm,.mkv,.m4v" multiple>
  </label>
  <div class="grid">
    <label class="drop vo" id="drop-voiceover">
      <h2>🎙️ Voiceover</h2>
      <p>Optional. mp3 / wav / m4a / aac / ogg / flac.</p>
      <p class="hint">Lands in <code>uploads/inbox/voiceover/</code></p>
      <input type="file" id="file-voiceover" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac" multiple>
    </label>
    <label class="drop ref" id="drop-reference">
      <h2>🖼 Extra / reference</h2>
      <p>Optional. Images, zip, another clip.</p>
      <p class="hint">Lands in <code>uploads/inbox/reference/</code></p>
      <input type="file" id="file-reference" accept="video/*,image/*,.mp4,.mov,.webm,.mkv,.png,.jpg,.jpeg,.webp,.zip" multiple>
    </label>
  </div>
  <div id="jobs"></div>
  <div class="next">When the bar is green: type <b>uploaded</b> in chat.
    I grab files from <code>uploads/inbox/video/</code>.</div>
  <div class="lib">
    <h3>Already in the sandbox</h3>
    <ul id="lib"><li class="hint">loading…</li></ul>
  </div>
</main>
<script>
const CHUNK = 8 * 1024 * 1024;
const PARALLEL = 8;
const SINGLE = 32 * 1024 * 1024;

function $(id){ return document.getElementById(id); }
function fmt(n){ return n < 1048576 ? (n/1024).toFixed(1)+' KB' : (n/1048576).toFixed(2)+' MB'; }
function uid(){ return Math.random().toString(36).slice(2,10) + Date.now().toString(36); }

function bindDrop(kind) {
  const box = $('drop-'+kind);
  const input = $('file-'+kind);
  box.addEventListener('dragover', e => { e.preventDefault(); box.classList.add('drag'); });
  box.addEventListener('dragleave', () => box.classList.remove('drag'));
  box.addEventListener('drop', e => {
    e.preventDefault(); box.classList.remove('drag');
    if (e.dataTransfer.files.length) [...e.dataTransfer.files].forEach(f => enqueue(f, kind));
  });
  input.addEventListener('change', () => {
    [...input.files].forEach(f => enqueue(f, kind));
    input.value = '';
  });
}
bindDrop('video');
bindDrop('voiceover');
bindDrop('reference');

function enqueue(file, kind) {
  const id = uid();
  const jobs = $('jobs');
  const row = document.createElement('div');
  row.className = 'row';
  row.id = 'job-'+id;
  row.innerHTML = '<div class="name">'+esc(kind)+' · '+esc(file.name)+'</div>'
    + '<div class="meta" id="meta-'+id+'">'+fmt(file.size)+' — starting</div>'
    + '<div class="bar"><div class="fill" id="fill-'+id+'"></div></div>';
  jobs.prepend(row);
  upload(file, kind, id).catch(err => {
    $('meta-'+id).innerHTML = '<span class="err">❌ '+esc(err.message)+'</span>';
    $('fill-'+id).classList.add('bad');
  });
}
function esc(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function upload(file, kind, id) {
  const t0 = performance.now();
  const set = (pct, msg) => {
    const fill = $('fill-'+id); const meta = $('meta-'+id);
    if (fill) fill.style.width = Math.max(0, Math.min(100, pct)) + '%';
    if (meta) meta.textContent = msg;
  };
  const q = 'kind='+encodeURIComponent(kind)+'&name='+encodeURIComponent(file.name)+'&id='+id;
  if (file.size <= SINGLE) {
    set(5, 'one-shot upload…');
    const r = await fetch('/put?'+q, { method:'POST', body:file, headers:{'Content-Type':'application/octet-stream'} });
    const j = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(j.error || ('HTTP '+r.status));
    const sec = (performance.now()-t0)/1000;
    const mbps = (file.size/1048576) / Math.max(sec, 0.001);
    set(100, '✅ '+j.path+'  ·  '+sec.toFixed(1)+'s  ·  '+mbps.toFixed(1)+' MB/s');
    $('fill-'+id).style.width = '100%';
    refreshLib();
    return;
  }
  const total = Math.ceil(file.size / CHUNK);
  let done = 0;
  const worker = async (index) => {
    const blob = file.slice(index*CHUNK, (index+1)*CHUNK);
    const url = '/chunk?'+q+'&index='+index+'&total='+total;
    for (let attempt=0; attempt<3; attempt++) {
      const r = await fetch(url, { method:'POST', body:blob, headers:{'Content-Type':'application/octet-stream'} });
      if (r.ok) { done++; 
        const sec = (performance.now()-t0)/1000;
        const mbps = ((done*CHUNK)/1048576) / Math.max(sec, 0.001);
        set(done/total*90, 'chunk '+(done)+'/'+total+'  ·  '+mbps.toFixed(1)+' MB/s');
        return;
      }
      if (attempt === 2) throw new Error('chunk '+index+' HTTP '+r.status);
      await new Promise(res => setTimeout(res, 250*(attempt+1)));
    }
  };
  const queue = Array.from({length: total}, (_, i) => i);
  const runners = Array.from({length: Math.min(PARALLEL, total)}, async () => {
    while (queue.length) await worker(queue.shift());
  });
  await Promise.all(runners);
  set(95, 'assembling…');
  const d = await fetch('/done?'+q+'&total='+total, { method:'POST' });
  const j = await d.json().catch(()=>({}));
  if (!d.ok) throw new Error(j.error || ('assemble HTTP '+d.status));
  const sec = (performance.now()-t0)/1000;
  const mbps = (file.size/1048576) / Math.max(sec, 0.001);
  set(100, '✅ '+j.path+'  ·  '+sec.toFixed(1)+'s  ·  '+mbps.toFixed(1)+' MB/s');
  refreshLib();
}

async function refreshLib() {
  try {
    const r = await fetch('/api/files');
    const j = await r.json();
    const ul = $('lib');
    if (!j.files || !j.files.length) { ul.innerHTML = '<li class="hint">Nothing yet.</li>'; return; }
    ul.innerHTML = j.files.map(f =>
      '<li><span><span class="k '+esc(f.kind)+'">'+esc(f.kind)+'</span> '+esc(f.name)+'</span>'
      + '<span class="meta">'+fmt(f.size)+'</span></li>'
    ).join('');
  } catch (e) { $('lib').innerHTML = '<li class="err">'+esc(e.message)+'</li>'; }
}
refreshLib();
setInterval(refreshLib, 4000);
</script>
</body>
</html>
"""


def safe_name(name: str) -> str:
    name = unquote(name or "")
    name = os.path.basename(name.replace("\\", "/"))
    name = re.sub(r"[^\w.\-]+", "_", name).strip("._") or "file.bin"
    return name[:180]


def kind_of(raw: str) -> str:
    k = (raw or "extra").strip().lower()
    return k if k in KINDS else "extra"


def dest_path(kind: str, name: str) -> Path:
    folder = INBOX / kind
    folder.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    base, ext = os.path.splitext(name)
    candidate = folder / f"{stamp}_{name}"
    n = 1
    while candidate.exists():
        candidate = folder / f"{stamp}_{base}_{n}{ext}"
        n += 1
    return candidate


def stream_copy(rfile, dest: Path, length: int, limit: int) -> int:
    if length <= 0 or length > limit:
        raise ValueError("bad size")
    dest.parent.mkdir(parents=True, exist_ok=True)
    got = 0
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with open(tmp, "wb") as f:
        remaining = length
        while remaining > 0:
            block = rfile.read(min(1024 * 1024, remaining))
            if not block:
                break
            f.write(block)
            got += len(block)
            remaining -= len(block)
    if got != length:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"truncated: got {got} of {length}")
    tmp.replace(dest)
    return got


def list_files():
    out = []
    if not INBOX.exists():
        return out
    for kind in KINDS:
        folder = INBOX / kind
        if not folder.is_dir():
            continue
        for p in sorted(folder.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file() and not p.name.endswith(".partial"):
                st = p.stat()
                out.append({
                    "kind": kind,
                    "name": p.name,
                    "path": str(p.relative_to(ROOT)),
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                })
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def _qs(self):
        q = parse_qs(urlparse(self.path).query)
        return {k: (v[0] if v else "") for k, v in q.items()}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
            return
        if path == "/api/files":
            self._json(200, {"files": list_files(), "inbox": str(INBOX)})
            return
        if path == "/health":
            self._json(200, {"ok": True, "inbox": str(INBOX)})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/put":
                self._put()
            elif path == "/chunk":
                self._chunk()
            elif path == "/done":
                self._done()
            else:
                self._json(404, {"error": "not found"})
        except ValueError as e:
            self._json(400, {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _put(self):
        q = self._qs()
        length = int(self.headers.get("Content-Length") or 0)
        kind = kind_of(q.get("kind", "extra"))
        name = safe_name(q.get("name", "upload.bin"))
        dest = dest_path(kind, name)
        n = stream_copy(self.rfile, dest, length, PUT_MAX)
        print(f"PUT {kind} {n/1e6:.2f} MB -> {dest}", flush=True)
        self._json(200, {"ok": True, "path": str(dest.relative_to(ROOT)), "size": n, "kind": kind})

    def _chunk(self):
        q = self._qs()
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > CHUNK_MAX:
            self._json(413, {"error": "bad chunk size"})
            return
        name = safe_name(q.get("name", "file.bin"))
        uid = re.sub(r"[^\w\-]", "", q.get("id", "") or uuid.uuid4().hex)[:24]
        index = int(q.get("index", "0"))
        PARTS.mkdir(parents=True, exist_ok=True)
        part = PARTS / f"{uid}.{name}.{index:05d}"
        n = stream_copy(self.rfile, part, length, CHUNK_MAX)
        self._json(200, {"ok": True, "index": index, "bytes": n})

    def _done(self):
        q = self._qs()
        kind = kind_of(q.get("kind", "extra"))
        name = safe_name(q.get("name", "file.bin"))
        uid = re.sub(r"[^\w\-]", "", q.get("id", ""))[:24]
        total = int(q.get("total", "0"))
        if total <= 0 or not uid:
            raise ValueError("bad assemble params")
        dest = dest_path(kind, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".partial")
        size = 0
        with open(tmp, "wb") as out:
            for i in range(total):
                part = PARTS / f"{uid}.{name}.{i:05d}"
                if not part.is_file():
                    tmp.unlink(missing_ok=True)
                    raise ValueError(f"missing chunk {i}")
                with open(part, "rb") as inp:
                    shutil.copyfileobj(inp, out, 1024 * 1024)
                size += part.stat().st_size
                part.unlink()
        tmp.replace(dest)
        print(f"DONE {kind} {size/1e6:.2f} MB -> {dest}", flush=True)
        self._json(200, {"ok": True, "path": str(dest.relative_to(ROOT)), "size": size, "kind": kind})

    def log_message(self, fmt, *args):
        sys.stderr.write("[ingest %s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


if __name__ == "__main__":
    INBOX.mkdir(parents=True, exist_ok=True)
    for k in KINDS:
        (INBOX / k).mkdir(exist_ok=True)
    print(f"Dev upload on http://0.0.0.0:{PORT}  -> {INBOX}", flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
