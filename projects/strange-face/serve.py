#!/usr/bin/env python3
"""Serve the project folder with a tiny HTML5 player for final.mp4.

Supports HTTP Range requests so the browser can seek inside the video.
Run: python3 serve.py [port]
"""
import http.server
import os
import re
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = os.path.dirname(os.path.abspath(__file__))

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Why isn't your reflection you? — doodle explainer</title>
<style>
  body { margin: 0; background: #000; color: #fff;
         font-family: system-ui, sans-serif; display: flex;
         flex-direction: column; align-items: center; min-height: 100vh; }
  h1 { font-size: 18px; font-weight: 600; margin: 14px 10px 4px; text-align: center; }
  p  { font-size: 13px; color: #999; margin: 0 10px 14px; text-align: center; }
  video { width: min(100vw, 400px); max-height: 78vh; background: #000; }
  a.dl { display: inline-block; margin: 14px 0 20px; padding: 10px 18px;
         background: #FCEB00; color: #000; text-decoration: none;
         font-weight: 700; border-radius: 8px; }
</style>
</head>
<body>
  <h1>Why isn't your reflection you?</h1>
  <p>64 s &bull; three-band doodle explainer &bull; 720x1280</p>
  <video src="why-isnt-your-reflection-you.mp4" controls playsinline preload="auto" poster="contact_sheet.png"></video>
  <a class="dl" href="why-isnt-your-reflection-you.mp4" download="why-isnt-your-reflection-you.mp4">&#11015; Download the video</a>
</body>
</html>
"""

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(INDEX.encode())))
            self.end_headers()
            self.wfile.write(INDEX.encode())
            return
        # Range support for smooth seeking in the <video> tag
        m = RANGE_RE.match(self.headers.get("Range", ""))
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().do_GET()
        size = os.path.getsize(path)
        if m and (m.group(1) or m.group(2)):
            start = int(m.group(1) or 0)
            end = int(m.group(2) or size - 1)
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            length = end - start + 1
        else:
            start, length = 0, size
            self.send_response(200)
        ctype = self.guess_type(path)
        if isinstance(ctype, tuple):
            ctype = ctype[0]
        self.send_header("Content-Type", ctype or "application/octet-stream")
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


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving {ROOT} on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
