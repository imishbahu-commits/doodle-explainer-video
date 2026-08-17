#!/usr/bin/env python3
"""Phone studio: Flux image generator (Pollinations tap-link) + chunked
video upload into the workspace.

GET  /            -> page: prompt box -> open Flux image in new tab
GET  /upload      -> chunked file upload (512 KB pieces, progress bar)
POST /chunk?name=&index=&total=   -> append one chunk (raw body)
POST /done?name=&total=           -> reassemble into uploads/<name>
"""

import http.server
import re
import sys
from pathlib import Path
from urllib.parse import unquote

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8012
UPLOAD_DIR = Path("/home/user/doodle-explainer-video/uploads")
PARTS_DIR = UPLOAD_DIR / ".parts"
MAX_CHUNK = 2 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024


def safe_name(name):
    name = re.sub(r"[^\w.\-]", "_", name or "video.mp4")
    return name if name else "video.mp4"


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone studio — Flux + upload</title>
<style>
  body { margin:0; background:#0d0f1a; color:#eee; font-family: system-ui, sans-serif;
         padding: 24px 16px; text-align:center; }
  h1 { font-size: 18px; margin: 6px 0 2px; }
  p  { font-size: 13px; color:#9aa; margin: 0 auto 16px; max-width: 440px; }
  textarea, input[type=file] { display:block; margin: 10px auto; color:#9aa;
    font-size:14px; }
  textarea { width:100%; max-width:420px; height:70px; background:#161a2b;
    color:#eee; border:1px solid #2a3045; border-radius:10px; padding:10px;
    box-sizing:border-box; }
  button { width: 100%; max-width: 360px; padding: 16px; border: 0;
    border-radius: 12px; background:#f5c63c; color:#000; font-weight:700;
    font-size:17px; margin-top: 8px; }
  button.flux { background:#7ee08a; }
  button.upload { background:#f5c63c; }
  hr { border-color:#2a3045; margin:20px 0; max-width:440px; }
  #bar { width:100%; max-width:360px; height:18px; background:#161a2b;
    border-radius:9px; margin:18px auto; overflow:hidden; display:none; }
  #fill { height:100%; width:0%; background:#7ee08a; transition:width .2s; }
  #status { font-size:13px; color:#f5c63c; margin-top:12px; min-height:18px;
    white-space:pre-wrap; }
  .tip { font-size:12px; color:#778; margin-top:22px; line-height:1.7;
    text-align:left; max-width:440px; margin-left:auto; margin-right:auto; }
  .err { color:#ff8080; }
</style>
</head>
<body>
  <h1>🎨 Flux images + 📤 upload — your phone studio</h1>

  <p><b>1 · Generate an image (unlimited, free):</b> type a prompt, tap the
  green button. The image opens in a new tab on Pollinations — long-press it
  and choose "Save image".</p>
  <textarea id="fluxprompt" placeholder="Hand-drawn doodle of a cyclops, MS-Paint style, thick black outlines, flat colors, white background, no text..."></textarea>
  <button class="flux" onclick="openFlux()">🎨 Generate with Flux</button>
  <div class="tip" style="margin-top:6px">Style lock — add to any prompt:
  <i>"MS-Paint-like style: thick black outlines, flat bold colors, slightly
  imperfect hand-drawn lines, no text, no shadows, no gradients"</i></div>

  <hr>

  <p><b>2 · Send files to the agent:</b> pick the image/video from your
  phone, tap Upload, watch the green bar fill.</p>
  <input type="file" id="file" accept="video/*,image/*,.mp4,.mov,.mkv,.webm,.png,.jpg,.jpeg">
  <button class="upload" onclick="upload()">⬆ Upload</button>
  <div id="bar"><div id="fill"></div></div>
  <div id="status"></div>
  <div class="tip">When it shows ✅, go back to the chat and type
  <b>uploaded</b>. Files are cut into tiny 512 KB pieces, so big videos are
  fine.</div>

<script>
function openFlux() {
  const p = document.getElementById('fluxprompt').value.trim();
  if (!p) { document.getElementById('status').textContent = '⚠ Type a prompt first.'; return; }
  const url = 'https://image.pollinations.ai/prompt/' + encodeURIComponent(p) +
              '?width=1152&height=648&model=flux&nologo=true';
  window.open(url, '_blank');
}

async function upload() {
  const f = document.getElementById('file').files[0];
  const status = document.getElementById('status');
  const bar = document.getElementById('bar');
  const fill = document.getElementById('fill');
  if (!f) { status.textContent = '⚠ Pick a file first.'; return; }
  const CHUNK = 512 * 1024;
  const total = Math.ceil(f.size / CHUNK);
  if (f.size > 400 * 1024 * 1024) {
    status.textContent = '⚠ File too big — compress it first.';
    return;
  }
  bar.style.display = 'block';
  fill.style.width = '0%';
  status.textContent = 'Uploading… 0/' + total + ' pieces';
  const name = encodeURIComponent(f.name);
  try {
    for (let i = 0; i < total; i++) {
      const chunk = f.slice(i * CHUNK, (i + 1) * CHUNK);
      const r = await fetch('/chunk?name=' + name + '&index=' + i + '&total=' + total,
                            { method: 'POST', body: chunk });
      if (!r.ok) throw new Error('piece ' + i + ' rejected: HTTP ' + r.status);
      fill.style.width = Math.round((i + 1) / total * 100) + '%';
      status.textContent = 'Uploading… ' + (i + 1) + '/' + total + ' pieces';
    }
    const d = await fetch('/done?name=' + name + '&total=' + total, { method: 'POST' });
    if (!d.ok) throw new Error('assembly failed: HTTP ' + d.status);
    status.innerHTML = '<span style="color:#7ee08a">✅ Uploaded! Go back to the chat and type <b>uploaded</b></span>';
  } catch (e) {
    status.innerHTML = '<span class="err">❌ ' + e.message + '</span>';
  }
}
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def _params(self):
        q = self.path.split("?", 1)[1] if "?" in self.path else ""
        out = {}
        for pair in q.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                out[k] = unquote(v)
        return out

    def _read(self, limit):
        chunks = []
        got = 0
        while got < limit:
            c = self.rfile.read(min(65536, limit - got))
            if not c:
                break
            chunks.append(c)
            got += len(c)
        return b"".join(chunks)

    def do_POST(self):
        try:
            if self.path.startswith("/chunk"):
                self._chunk()
            elif self.path.startswith("/done"):
                self._done()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            except Exception:
                pass

    def _chunk(self):
        p = self._params()
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_CHUNK:
            self.send_response(413)
            self.end_headers()
            return
        data = self._read(length)
        if len(data) != length:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"truncated: got {len(data)} of {length}".encode())
            return
        PARTS_DIR.mkdir(parents=True, exist_ok=True)
        part = PARTS_DIR / f"{safe_name(p.get('name',''))}.{int(p.get('index',0)):05d}"
        part.write_bytes(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def _done(self):
        p = self._params()
        name = safe_name(p.get("name", ""))
        total = int(p.get("total", 0))
        parts = []
        for i in range(total):
            part = PARTS_DIR / f"{name}.{i:05d}"
            if not part.exists():
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"missing part {i}".encode())
                return
            parts.append(part.read_bytes())
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        dest = UPLOAD_DIR / name
        dest.write_bytes(b"".join(parts))
        for part in PARTS_DIR.glob(f"{name}.*"):
            part.unlink()
        print(f"UPLOADED {len(b''.join(parts)) / 1e6:.1f} MB -> {dest}", flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"done")

    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] " + fmt % args + "\n")


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"phone studio on :{PORT}", flush=True)
    srv.serve_forever()
