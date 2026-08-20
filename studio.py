#!/usr/bin/env python3
"""Studio — watch every video built in this workspace from one page.

A tiny zero-dependency web app that scans projects/ for finished .mp4 files,
lists them as a library, and plays them in an HTML5 player with seeking.
Alongside each video it shows the project's script, beat plan and artwork.

Run:  python3 studio.py [port]     (default 8090)
"""

import json
import mimetypes
import os
import re
import socketserver
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.join(ROOT, "projects")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def rel_project_path(rel):
    """Resolve a URL path against projects/ and reject escapes."""
    base = os.path.realpath(PROJECTS)
    target = os.path.realpath(os.path.join(base, rel.lstrip("/")))
    if target != base and not target.startswith(base + os.sep):
        return None
    return target


def library():
    """Walk projects/ and index videos, images and scripts per project."""
    out = []
    if not os.path.isdir(PROJECTS):
        return out
    for name in sorted(os.listdir(PROJECTS)):
        pdir = os.path.join(PROJECTS, name)
        if not os.path.isdir(pdir) or name.startswith("."):
            continue
        videos, images = [], []
        for dirpath, dirnames, filenames in os.walk(pdir):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in ("build_work",)]
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, PROJECTS)
                if fn.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                    videos.append({
                        "rel": rel,
                        "name": fn,
                        "size": os.path.getsize(full),
                        "mtime": os.path.getmtime(full),
                    })
                elif fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                    images.append({"rel": rel, "name": fn})
        videos.sort(key=lambda v: -v["mtime"])
        out.append({
            "name": name,
            "videos": videos,
            "images": images,
            "has_script": os.path.isfile(os.path.join(pdir, "script.md")),
            "has_beats": os.path.isfile(os.path.join(pdir, "beats.json")),
        })
    return out


def read_text(rel):
    path = rel_project_path(rel)
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Studio — Doodle Explainer</title>
<style>
  :root {
    --bg:#0e1017; --panel:#161a24; --panel2:#1d2230; --line:#262d3d;
    --text:#e9ecf3; --muted:#8b93a6; --accent:#ffd23f; --accent2:#4da3ff;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font-family:system-ui, -apple-system, "Segoe UI", sans-serif; }
  header { display:flex; align-items:center; gap:12px; padding:14px 20px;
           border-bottom:1px solid var(--line); background:var(--panel); }
  header h1 { font-size:17px; margin:0; font-weight:700; letter-spacing:.3px; }
  header .dot { width:9px; height:9px; border-radius:50%; background:#34d399;
                box-shadow:0 0 10px #34d399; }
  header .sub { color:var(--muted); font-size:12px; margin-left:auto; }
  .wrap { display:grid; grid-template-columns: 300px 1fr; gap:0; height:calc(100vh - 61px); }
  .side { border-right:1px solid var(--line); overflow-y:auto; background:var(--panel); }
  .side h2 { font-size:11px; text-transform:uppercase; letter-spacing:1.2px;
             color:var(--muted); padding:16px 18px 8px; margin:0; }
  .proj { border-bottom:1px solid var(--line); }
  .proj > .pname { padding:10px 18px; font-size:13px; font-weight:700; color:#cfd6e4; }
  .vid { display:block; width:100%; text-align:left; background:none; border:0;
         color:var(--muted); padding:7px 18px 7px 30px; cursor:pointer; font-size:13px; }
  .vid:hover { color:var(--text); background:var(--panel2); }
  .vid.active { color:var(--accent); background:var(--panel2); border-left:3px solid var(--accent); }
  .vid .sz { float:right; font-size:11px; opacity:.7; }
  .empty { color:var(--muted); padding:20px; font-size:13px; line-height:1.6; }
  .main { overflow-y:auto; padding:20px 24px; }
  .stage { background:var(--panel); border:1px solid var(--line); border-radius:14px;
           padding:18px; margin-bottom:18px; }
  .stage h3 { margin:0 0 6px; font-size:16px; }
  .stage .meta { color:var(--muted); font-size:12px; margin-bottom:14px; }
  video { width:100%; max-height:62vh; background:#000; border-radius:8px; display:block; }
  .tabs { display:flex; gap:8px; margin:16px 0 10px; flex-wrap:wrap; }
  .tabs button { background:var(--panel2); color:var(--muted); border:1px solid var(--line);
                 border-radius:8px; padding:8px 14px; cursor:pointer; font-size:13px; }
  .tabs button.active { color:#000; background:var(--accent); border-color:var(--accent); font-weight:700; }
  .pane { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; }
  .pane h4 { margin:0 0 10px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }
  .script { white-space:pre-wrap; font-size:14px; line-height:1.7; color:#d6dbe6; }
  .script b, .script strong { color:var(--accent); }
  pre { white-space:pre-wrap; word-break:break-word; font-size:12px; line-height:1.6;
        color:#cbd2de; font-family:ui-monospace, Menlo, monospace; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }
  .grid figure { margin:0; background:var(--panel2); border:1px solid var(--line);
                 border-radius:8px; overflow:hidden; }
  .grid img { width:100%; aspect-ratio:16/9; object-fit:cover; display:block; background:#fff; }
  .grid figcaption { font-size:11px; color:var(--muted); padding:6px 8px; }
  .hint { color:var(--muted); font-size:12px; line-height:1.6; padding:0 2px; }
  a { color:var(--accent2); }
</style>
</head>
<body>
<header>
  <span class="dot"></span>
  <h1>Doodle Explainer — Studio</h1>
  <span class="sub" id="sub">loading library…</span>
</header>
<div class="wrap">
  <aside class="side" id="side"></aside>
  <main class="main" id="main">
    <div class="stage" style="text-align:center;padding:60px 20px;">
      <p class="hint">Pick a video on the left to watch it here.<br>
      Finished renders appear automatically — no refresh needed.</p>
    </div>
  </main>
</div>
<script>
let state = { library:[], current:null, tab:'script' };

async function loadLibrary() {
  const r = await fetch('/api/library');
  state.library = await r.json();
  renderSide();
}
function renderSide() {
  const side = document.getElementById('side');
  const n = state.library.reduce((a,p)=>a+p.videos.length,0);
  document.getElementById('sub').textContent = n + ' video' + (n===1?'':'s') + ' in workspace';
  side.innerHTML = '';
  if (!state.library.length) {
    side.innerHTML = '<div class="empty">No videos yet. Build one and it will show up here.</div>';
    return;
  }
  for (const p of state.library) {
    if (!p.videos.length) continue;
    const box = document.createElement('div');
    box.className = 'proj';
    const h = document.createElement('div');
    h.className = 'pname';
    h.textContent = p.name;
    box.appendChild(h);
    for (const v of p.videos) {
      const b = document.createElement('button');
      b.className = 'vid' + (state.current === v.rel ? ' active':'');
      b.innerHTML = '<span class="sz">' + (v.size/1048576).toFixed(1) + ' MB</span>' + escapeHtml(v.name);
      b.onclick = () => openVideo(p.name, v);
      box.appendChild(b);
    }
    side.appendChild(box);
  }
}
function escapeHtml(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

async function openVideo(project, v) {
  state.current = v.rel;
  renderSide();
  const main = document.getElementById('main');
  main.innerHTML =
    '<div class="stage">' +
      '<h3>' + escapeHtml(v.name) + '</h3>' +
      '<div class="meta">project: ' + escapeHtml(project) + ' · ' +
        (v.size/1048576).toFixed(1) + ' MB</div>' +
      '<video controls playsinline preload="metadata" src="/f/' + encodeURIComponent(v.rel) + '"></video>' +
      '<div class="tabs">' +
        '<button class="active" data-t="script" onclick="switchTab(this,\'script\')">Script</button>' +
        '<button data-t="beats" onclick="switchTab(this,\'beats\')">Beats</button>' +
        '<button data-t="art" onclick="switchTab(this,\'art\')">Artwork</button>' +
      '</div>' +
      '<div class="pane" id="pane"><h4>Loading…</h4></div>' +
    '</div>';
  const p = state.library.find(x => x.name === project) || {images:[]};
  state._project = project;
  state._images = p.images;
  loadPane('script');
}
function switchTab(btn, t) {
  document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadPane(t);
}
async function loadPane(t) {
  const pane = document.getElementById('pane');
  const proj = state._project;
  if (t === 'script') {
    const r = await fetch('/api/project/' + encodeURIComponent(proj) + '/script');
    if (r.ok) {
      const txt = await r.text();
      pane.innerHTML = '<h4>Script</h4><div class="script">' + mdToHtml(txt) + '</div>';
    } else {
      pane.innerHTML = '<h4>Script</h4><p class="hint">No script.md in this project.</p>';
    }
  } else if (t === 'beats') {
    const r = await fetch('/api/project/' + encodeURIComponent(proj) + '/beats');
    if (r.ok) {
      const j = await r.json();
      pane.innerHTML = '<h4>Beat plan (beats.json)</h4><pre>' + escapeHtml(JSON.stringify(j, null, 2)) + '</pre>';
    } else {
      pane.innerHTML = '<h4>Beats</h4><p class="hint">No beats.json in this project.</p>';
    }
  } else if (t === 'art') {
    const imgs = state._images || [];
    if (!imgs.length) {
      pane.innerHTML = '<h4>Artwork</h4><p class="hint">No images in this project.</p>';
      return;
    }
    let html = '<h4>Artwork (' + imgs.length + ')</h4><div class="grid">';
    for (const im of imgs) {
      html += '<figure><img loading="lazy" src="/f/' + encodeURIComponent(im.rel) + '" alt="' + escapeHtml(im.name) + '">' +
              '<figcaption>' + escapeHtml(im.name) + '</figcaption></figure>';
    }
    pane.innerHTML = html + '</div>';
  }
}
function mdToHtml(md) {
  let out = escapeHtml(md);
  out = out.replace(/^## (.*)$/gm, '<b>$1</b>');
  out = out.replace(/\n/g, '<br>');
  return out;
}
loadLibrary();
setInterval(loadLibrary, 5000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype, extra=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, indent=2), "application/json")

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, INDEX, "text/html; charset=utf-8")
            return
        if path == "/api/library":
            self._json(200, library())
            return
        m = re.match(r"^/api/project/([^/]+)/(script|beats)$", path)
        if m:
            proj, kind = urllib.parse.unquote(m.group(1)), m.group(2)
            if kind == "script":
                txt = read_text(os.path.join(proj, "script.md"))
                if txt is None:
                    self._json(404, {"error": "no script.md"})
                else:
                    self._send(200, txt, "text/markdown; charset=utf-8")
            else:
                txt = read_text(os.path.join(proj, "beats.json"))
                if txt is None:
                    self._json(404, {"error": "no beats.json"})
                else:
                    self._json(200, json.loads(txt))
            return
        if path.startswith("/f/"):
            rel = urllib.parse.unquote(path[len("/f/"):])
            self._serve_file(rel)
            return
        self._json(404, {"error": "not found"})

    def _serve_file(self, rel):
        target = rel_project_path(rel)
        if not target or not os.path.isfile(target):
            self._json(404, {"error": "file not found"})
            return
        size = os.path.getsize(target)
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        rng = self.headers.get("Range", "")
        m = RANGE_RE.match(rng)
        if m and (m.group(1) or m.group(2)):
            start = int(m.group(1) or 0)
            end = int(m.group(2) or size - 1)
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            with open(target, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(target, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] %s - %s\n" % (time.strftime("%H:%M:%S"), fmt % args))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"Studio on http://0.0.0.0:{PORT}  (projects dir: {PROJECTS})", flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
