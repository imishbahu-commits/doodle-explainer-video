#!/usr/bin/env python3
"""Dinzo studio — live preview for a video project.

Serves the project folder with a 16:9 player for the assembled parts plus a
gallery of the hand-drawn beat images. Supports HTTP Range requests.

Usage: python3 studio.py [title] [port]
"""
import http.server
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

TITLE = sys.argv[1] if len(sys.argv) > 1 else "Dinzo Studio"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
ROOT = Path(__file__).resolve().parent
RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def render_page():
    mp4s = sorted(ROOT.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    imgs = sorted(ROOT.glob("assets/beat*.png"))

    part_buttons = ""
    for i, p in enumerate(mp4s):
        cls = "on" if i == 0 else ""
        part_buttons += (
            f'<button class="part {cls}" data-src="/{p.name}">'
            f'{p.name.replace(".mp4", "")}</button>\n'
        )

    gallery = ""
    for p in imgs:
        gallery += (f'<figure><img src="/assets/{p.name}" alt="{p.stem}" '
                    f'loading="lazy"><figcaption>{p.stem}</figcaption></figure>\n')

    primary = f"/{mp4s[0].name}" if mp4s else ""
    dur = ""
    if mp4s:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", str(mp4s[0])],
                capture_output=True, text=True).stdout.strip()
            dur = f"&bull; {float(out):.0f} s" if out else ""
        except Exception:
            pass

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#0b0d12; color:#e9edf4;
         font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
  header { padding: 22px 18px 8px; text-align:center; }
  h1 { font-size: 20px; margin: 0 0 4px; font-weight: 700; }
  .sub { font-size: 13px; color:#8b95a7; margin: 0; }
  .stage { display:flex; flex-direction:column; align-items:center; padding: 10px 12px 4px; }
  video { width: min(100vw, 900px); aspect-ratio: 16/9; background:#000;
          border-radius: 10px; box-shadow: 0 6px 40px rgba(0,0,0,.55); }
  .parts { display:flex; flex-wrap:wrap; gap:8px; justify-content:center;
           padding: 14px 12px 4px; }
  .part { background:#1a202b; color:#cfd6e2; border:1px solid #2b3444;
          border-radius: 999px; padding: 8px 16px; font-size: 13px;
          cursor:pointer; font-weight:600; }
  .part.on { background:#f5c63c; color:#111; border-color:#f5c63c; }
  .part:hover { border-color:#4a5568; }
  .meta { text-align:center; font-size: 13px; color:#8b95a7; padding: 2px 0 12px; }
  h2 { font-size: 14px; text-transform: uppercase; letter-spacing:.08em;
       color:#8b95a7; margin: 22px 16px 10px; text-align:center; }
  .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
          gap: 10px; padding: 0 16px 40px; max-width: 1100px; margin: 0 auto; }
  figure { margin:0; background:#131722; border:1px solid #232b3a;
           border-radius:8px; overflow:hidden; }
  figure img { width:100%; display:block; }
  figcaption { font-size:11px; color:#8b95a7; padding:6px 8px; text-align:center; }
</style>
</head>
<body>
  <header>
    <h1>__TITLE__</h1>
    <p class="sub">Dinzo-style explainer &bull; 16:9 &bull; hand-drawn</p>
  </header>
  <div class="stage">
    <video id="player" src="__PRIMARY__" controls autoplay playsinline
           preload="auto"></video>
  </div>
  <div class="parts">__PARTS__</div>
  <div class="meta">__DUR__</div>
  <h2>Beat gallery</h2>
  <div class="grid">__GALLERY__</div>
<script>
  const player = document.getElementById('player');
  document.querySelectorAll('.part').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.part').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      player.src = btn.dataset.src;
      player.load();
      player.play().catch(() => {});
    });
  });
</script>
</body>
</html>""".replace("__TITLE__", TITLE).replace("__PRIMARY__", primary).replace(
        "__PARTS__", part_buttons).replace("__DUR__", dur).replace("__GALLERY__", gallery)


class Handler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = render_page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        path = ROOT / self.path.lstrip("/").split("?")[0]
        if not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        m = RANGE_RE.match(self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            start = int(m.group(1) or 0)
            end = min(int(m.group(2) or size - 1), size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            length = end - start + 1
        else:
            start, length = 0, size
            self.send_response(200)
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] " + fmt % args + "\n")


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"{TITLE} on http://0.0.0.0:{PORT}", flush=True)
    srv.serve_forever()
