#!/usr/bin/env python3
"""Serve the hook video with an HTML5 player + forced MP4 download."""
import http.server
import os
import re
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = os.path.dirname(os.path.abspath(__file__))
VIDEO_NAME = "skinny-fat-ape-hook.mp4"
VIDEO_PATH = os.path.join(ROOT, VIDEO_NAME)

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skinny Fat Ape — download MP4</title>
<style>
  html, body { margin: 0; background: #111; color: #fff;
    font-family: system-ui, sans-serif; min-height: 100%; }
  body { display: flex; flex-direction: column; align-items: center;
    padding: 16px 12px 32px; box-sizing: border-box; }
  h1 { font-size: 20px; margin: 8px 0 4px; text-align: center; }
  p  { font-size: 14px; color: #bbb; margin: 0 0 16px; text-align: center; }
  video { width: min(96vw, 960px); background: #000; border-radius: 8px; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-top: 18px; }
  button.dl, a.dl { display: inline-block; padding: 14px 22px; background: #FCEB00;
    color: #111; text-decoration: none; font-weight: 800; border-radius: 10px;
    font-size: 16px; border: 0; cursor: pointer; }
  a.sec { display: inline-block; padding: 14px 22px; background: #2a2a2a;
    color: #fff; text-decoration: none; font-weight: 600; border-radius: 10px;
    font-size: 16px; border: 1px solid #444; }
  #status { min-height: 1.2em; margin-top: 12px; color: #FCEB00; font-size: 14px; }
</style>
</head>
<body>
  <h1>Skinny Fat Ape — THE HOOK</h1>
  <p>26.8s · 1280×720 · H.264 MP4 · 4.6 MB</p>
  <video src="/play.mp4" controls playsinline preload="metadata" poster="poster.jpg"></video>
  <div class="row">
    <button class="dl" id="save" type="button">Download MP4</button>
    <a class="sec" href="/download.mp4" target="_blank" rel="noopener">Save via new tab</a>
  </div>
  <p id="status"></p>
  <script>
  const status = document.getElementById('status');
  document.getElementById('save').addEventListener('click', async () => {
    status.textContent = 'Preparing download…';
    try {
      const res = await fetch('/download.mp4', { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'skinny-fat-ape-hook.mp4';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4000);
      status.textContent = 'If nothing saved, tap “Save via new tab”.';
    } catch (err) {
      status.textContent = 'Direct save blocked — opening file…';
      window.location.href = '/download.mp4';
    }
  });
  </script>
</body>
</html>
"""

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def send_file(handler, path, ctype, disposition):
    size = os.path.getsize(path)
    rng = RANGE_RE.match(handler.headers.get("Range", "") or "")
    if rng and (rng.group(1) or rng.group(2)) and disposition.startswith("inline"):
        start = int(rng.group(1) or 0)
        end = int(rng.group(2) or size - 1)
        end = min(end, size - 1)
        handler.send_response(206)
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        length = end - start + 1
    else:
        start, length = 0, size
        handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(length))
    handler.send_header("Content-Disposition", disposition)
    handler.end_headers()
    with open(path, "rb") as f:
        f.seek(start)
        remaining = length
        while remaining > 0:
            chunk = f.read(min(65536, remaining))
            if not chunk:
                break
            handler.wfile.write(chunk)
            remaining -= len(chunk)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route in ("/", "/index.html"):
            body = INDEX.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route in ("/download", "/download.mp4", "/download/skinny-fat-ape-hook.mp4"):
            send_file(
                self,
                VIDEO_PATH,
                "application/octet-stream",
                'attachment; filename="skinny-fat-ape-hook.mp4"',
            )
            return
        if route in ("/play.mp4", "/skinny-fat-ape-hook.mp4", "/final.mp4"):
            send_file(
                self,
                VIDEO_PATH,
                "video/mp4",
                'inline; filename="skinny-fat-ape-hook.mp4"',
            )
            return
        return super().do_GET()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    if not os.path.isfile(VIDEO_PATH):
        sys.exit(f"missing {VIDEO_PATH}")
    with Server(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving {ROOT} on http://0.0.0.0:{PORT}", flush=True)
        httpd.serve_forever()
