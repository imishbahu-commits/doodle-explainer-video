#!/usr/bin/env python3
"""Watch-only server for videos we create in this workspace.

Scans:
  projects/vo-sync/parts/
  uploads/inbox/created/
  projects/*/parts/  (skip gitignored scratch if empty)

GET  /              player
GET  /api/library   JSON list
GET  /v/<rel>       video (HTTP Range)

Run: python3 tools/video_preview.py [port]    default 8092
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")

SCAN = [
    ROOT / "projects" / "vo-sync" / "parts",
    ROOT / "uploads" / "inbox" / "created",
    ROOT / "uploads" / "inbox" / "video",
]

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Created videos — watch</title>
<style>
  :root {
    --bg:#0e1017; --panel:#161a24; --panel2:#1d2230; --line:#262d3d;
    --text:#e9ecf3; --muted:#8b93a6; --accent:#ffd23f; --ok:#34d399;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }
  header { padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel);
           display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
  header h1 { font-size:17px; margin:0; }
  .dot { width:9px; height:9px; border-radius:50%; background:var(--ok);
         box-shadow:0 0 10px var(--ok); }
  .sub { margin-left:auto; color:var(--muted); font-size:12px; }
  .wrap { display:grid; grid-template-columns: 300px 1fr; height:calc(100vh - 53px); }
  @media (max-width:800px) { .wrap { grid-template-columns:1fr; height:auto; } }
  .side { overflow-y:auto; border-right:1px solid var(--line); background:var(--panel); }
  .side h2 { font-size:11px; text-transform:uppercase; letter-spacing:1.2px;
             color:var(--muted); padding:14px 16px 6px; margin:0; }
  .vid { display:block; width:100%; text-align:left; background:none; border:0;
         color:var(--muted); padding:10px 16px; cursor:pointer; font-size:13px; }
  .vid:hover { color:var(--text); background:var(--panel2); }
  .vid.active { color:var(--accent); background:var(--panel2); border-left:3px solid var(--accent); }
  .vid .sz { float:right; font-size:11px; opacity:.7; }
  .main { padding:20px 24px; overflow-y:auto; }
  .stage { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; }
  .stage h3 { margin:0 0 6px; }
  .meta { color:var(--muted); font-size:12px; margin-bottom:12px; }
  video { width:100%; max-height:70vh; background:#000; border-radius:8px; display:block; }
  .empty { color:var(--muted); padding:24px; font-size:13px; line-height:1.6; }
</style>
</head>
<body>
<header>
  <span class="dot"></span>
  <h1>Created videos</h1>
  <span class="sub" id="sub">loading…</span>
</header>
<div class="wrap">
  <aside class="side" id="side"></aside>
  <main class="main" id="main">
    <div class="stage empty">Pick a video on the left. New cuts in
      <code>projects/vo-sync/parts/</code> show up here automatically.</div>
  </main>
</div>
<script>
let lib=[], current=null;
async function load() {
  const r = await fetch('/api/library');
  lib = await r.json();
  document.getElementById('sub').textContent = lib.length + ' video' + (lib.length===1?'':'s');
  const side = document.getElementById('side');
  if (!lib.length) { side.innerHTML = '<div class="empty">No created videos yet.</div>'; return; }
  let html = '<h2>Workspace</h2>';
  for (const v of lib) {
    const act = current===v.rel ? ' active':'';
    html += '<button class="vid'+act+'" onclick=\'openV('+JSON.stringify(v).replace(/'/g,"&#39;")+')\'>'
      + '<span class="sz">'+(v.size/1048576).toFixed(1)+' MB</span>'+esc(v.name)+'</button>';
  }
  side.innerHTML = html;
}
function esc(s){return String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));}
function openV(v) {
  current = v.rel;
  load();
  document.getElementById('main').innerHTML =
    '<div class="stage"><h3>'+esc(v.name)+'</h3>'
    + '<div class="meta">'+esc(v.rel)+' · '+(v.size/1048576).toFixed(1)+' MB</div>'
    + '<video controls playsinline autoplay preload="metadata" src="/v/'+encodeURIComponent(v.rel)+'"></video></div>';
}
load();
setInterval(load, 4000);
</script>
</body>
</html>
"""


def library():
    out = []
    seen = set()
    folders = list(SCAN)
    for p in (ROOT / "projects").glob("*/parts"):
        folders.append(p)
    for folder in folders:
        if not folder.is_dir():
            continue
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".mp4", ".webm", ".mov", ".mkv"):
                continue
            rel = str(f.relative_to(ROOT))
            if rel in seen:
                continue
            seen.add(rel)
            st = f.stat()
            out.append({"name": f.name, "rel": rel, "size": st.st_size, "mtime": st.st_mtime})
    out.sort(key=lambda x: -x["mtime"])
    return out


def safe(rel: str) -> Path | None:
    target = (ROOT / rel).resolve()
    if not str(target).startswith(str(ROOT.resolve()) + os.sep):
        return None
    if not target.is_file():
        return None
    return target


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
            return
        if path == "/api/library":
            self._send(200, json.dumps(library()), "application/json")
            return
        if path.startswith("/v/"):
            self._file(unquote(path[len("/v/"):]))
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def _file(self, rel):
        target = safe(rel)
        if not target:
            self._send(404, b'{"error":"missing"}', "application/json")
            return
        size = target.stat().st_size
        ctype = mimetypes.guess_type(str(target))[0] or "video/mp4"
        rng = self.headers.get("Range", "")
        m = RANGE_RE.match(rng or "")
        if m and (m.group(1) or m.group(2)):
            start = int(m.group(1) or 0)
            end = int(m.group(2) or size - 1)
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with open(target, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(65536, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open(target, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def log_message(self, fmt, *args):
        sys.stderr.write("[videos %s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"Video preview on http://0.0.0.0:{PORT}", flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
