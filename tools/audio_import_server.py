#!/usr/bin/env python3
"""Audio import server.

The sandbox firewall blocks vocaroo/dropbox, so this tiny server gives the
user a page in their browser (which CAN reach those hosts) to hand the audio
file into the workspace. The page first tries to fetch the Dropbox URL
directly from the browser (CORS permitting); if that fails, the user picks
the file manually and it is uploaded here.

Endpoints:
  GET  /            -> upload page
  POST /upload      -> raw file body, header X-Filename, saved to SAVE_DIR
"""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.environ.get("AUDIO_SAVE_DIR", os.path.join(ROOT, "..", "projects", "dinzo-batch", "work"))
PORT = int(os.environ.get("AUDIO_PORT", "8787"))
DROPBOX_URL = os.environ.get(
    "DROPBOX_URL",
    "https://www.dropbox.com/scl/fi/mal2ocfgavh89zs3kfb1b/ElevenLabs_2026-08-19T17_21_09_Mark-Casual-Relaxed-and-Light_pvc_sp100_s50_sb75_se0_b_m2.mp3?rlkey=2n9sfamq553edgkzrx9gbruiw&st=1e5n5r4i&dl=1",
)

os.makedirs(SAVE_DIR, exist_ok=True)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Audio Import — Doodle Explainer</title>
<style>
  body { font-family: system-ui, sans-serif; background:#0f1115; color:#e8e8e8;
         display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; padding:20px; }
  .card { background:#1a1e26; border:1px solid #2a2f3a; border-radius:14px;
          padding:28px; max-width:560px; width:100%; }
  h1 { font-size:20px; margin-top:0; }
  p  { font-size:14px; line-height:1.55; color:#b8bfc9; }
  .section { border:1px solid #2a2f3a; border-radius:10px; padding:16px; margin:14px 0; }
  .section h2 { font-size:15px; margin:0 0 10px; }
  #drop { border:2px dashed #3a4150; border-radius:10px; padding:26px 16px; margin:10px 0 14px;
          cursor:pointer; text-align:center; transition:border-color .2s, background .2s; }
  #drop.drag { border-color:#4da3ff; background:#1d2a3d; }
  /* Real native file input, visually hidden but directly clickable via label */
  #file { position:absolute; width:1px; height:1px; opacity:0; overflow:hidden; }
  .btn { background:#2b6cff; color:#fff; border:0; border-radius:8px; padding:10px 18px;
         font-size:14px; cursor:pointer; }
  .btn:hover { background:#3f7bff; }
  .btn.gray { background:#333a47; }
  .btn.gray:hover { background:#414a5a; }
  textarea { width:100%; box-sizing:border-box; min-height:110px; background:#11141b;
             color:#e8e8e8; border:1px solid #2a2f3a; border-radius:8px; padding:10px;
             font-size:13px; font-family:inherit; }
  .muted { color:#8b93a3; font-size:12px; }
  #status { margin-top:12px; font-size:14px; min-height:20px; white-space:pre-wrap; }
  .ok { color:#4ade80; } .err { color:#f87171; }
  a { color:#6ea8ff; }
  code { background:#11141b; padding:1px 5px; border-radius:4px; font-size:12px; }
</style>
</head>
<body>
<div class="card">
  <h1>🎙️ Audio Import</h1>
  <p>The sandbox can't reach Dropbox, but your browser can. Use one of the
     three options below — whichever is easiest.</p>

  <div class="section">
    <h2>Option 1 — Auto-fetch from your Dropbox link</h2>
    <button class="btn" id="autofetch">Fetch from Dropbox link</button>
    <span id="autofetch_status" class="muted"></span>
  </div>

  <div class="section">
    <h2>Option 2 — Upload the MP3 file</h2>
    <div id="drop">
      <label for="file" style="cursor:pointer; display:block;">
        <div style="font-size:15px; margin-bottom:6px;">⬇️ <b>Click here to choose the MP3</b></div>
        <div class="muted">…or drag &amp; drop the file anywhere in this box</div>
      </label>
      <input type="file" id="file" name="file" accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac">
    </div>
    <p class="muted">If clicking the box does nothing in this preview, download the MP3
       from Dropbox and drag it onto this box — that usually still works.</p>
  </div>

  <div class="section">
    <h2>Option 3 — Paste the script text instead</h2>
    <p class="muted">You generated this audio with ElevenLabs, so you have the exact
       script. Pasting it gives perfect word accuracy — no transcription needed.</p>
    <textarea id="script" placeholder="Paste your script here…"></textarea>
    <div style="margin-top:10px;">
      <button class="btn" id="submit-script">Send script</button>
    </div>
  </div>

  <div id="status" class="muted">Waiting…</div>
</div>
<script>
const DROPBOX = __DROPBOX_JSON__;
const status = document.getElementById('status');
function setStatus(msg, cls) { status.className = cls || ''; status.textContent = msg; }

async function uploadBytes(blob, filename) {
  setStatus('Uploading…');
  const res = await fetch('/upload', {
    method: 'POST',
    headers: { 'X-Filename': encodeURIComponent(filename) },
    body: blob
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}

function handleFile(file) {
  const ext = (file.name.split('.').pop() || 'mp3').toLowerCase();
  uploadBytes(file, 'voiceover.' + ext).then(d => {
    setStatus('✅ Saved: ' + d.path + ' (' + (d.size/1024).toFixed(1) + ' KB)', 'ok');
  }).catch(e => setStatus('❌ Upload failed: ' + e.message, 'err'));
}

document.getElementById('autofetch').addEventListener('click', () => {
  const st = document.getElementById('autofetch_status');
  st.textContent = '…trying';
  fetch(DROPBOX, { mode: 'cors' }).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.blob();
  }).then(blob => {
    if (blob.size < 10000) throw new Error('too small (' + blob.size + ' B)');
    st.textContent = 'got ' + (blob.size/1024).toFixed(0) + ' KB — uploading…';
    return uploadBytes(blob, 'voiceover.mp3');
  }).then(d => {
    st.textContent = '';
    setStatus('✅ Auto-fetched from Dropbox: ' + d.path + ' (' + (d.size/1024).toFixed(1) + ' KB)', 'ok');
  }).catch(e => {
    st.textContent = '';
    setStatus('⚠️ Dropbox blocked direct fetch (' + e.message + '). Use option 2 (download + drag in) or option 3 (paste script).', 'err');
  });
});

// Native file input — clicking the label opens the picker without JS
const fileInput = document.getElementById('file');
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

// Drag & drop
const drop = document.getElementById('drop');
drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag'); });
drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
drop.addEventListener('drop', e => {
  e.preventDefault(); drop.classList.remove('drag');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

// Paste script
document.getElementById('submit-script').addEventListener('click', async () => {
  const text = document.getElementById('script').value.trim();
  if (!text) { setStatus('⚠️ Script is empty', 'err'); return; }
  setStatus('Sending script…');
  try {
    const res = await fetch('/script', {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      body: text
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(d.error || ('HTTP ' + res.status));
    setStatus('✅ Script saved: ' + d.path + ' (' + d.chars + ' chars)', 'ok');
  } catch (e) {
    setStatus('❌ Failed: ' + e.message, 'err');
  }
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = PAGE.replace("__DROPBOX_JSON__", json.dumps(DROPBOX_URL))
            self._send(200, html, "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Filename, Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/script":
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0 or length > 5 * 1024 * 1024:
                self._send(413, json.dumps({"error": "bad size"}))
                return
            text = self.rfile.read(length).decode("utf-8", errors="replace")
            path = os.path.join(SAVE_DIR, "script.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._send(200, json.dumps({"ok": True, "path": os.path.relpath(path, os.path.join(ROOT, "..")), "chars": len(text)}))
            return
        if self.path != "/upload":
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > 200 * 1024 * 1024:
            self._send(413, json.dumps({"error": "bad size"}))
            return
        body = self.rfile.read(length)
        fname = self.headers.get("X-Filename", "")
        try:
            fname = fname.encode("latin1").decode("utf-8") if fname else "voiceover.bin"
        except Exception:
            fname = "voiceover.bin"
        safe = "".join(c for c in fname if c.isalnum() or c in "._-") or "voiceover.bin"
        path = os.path.join(SAVE_DIR, safe)
        with open(path, "wb") as f:
            f.write(body)
        self._send(200, json.dumps({"ok": True, "path": os.path.relpath(path, os.path.join(ROOT, "..")), "size": len(body)}))

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))


if __name__ == "__main__":
    print(f"Audio import server on http://0.0.0.0:{PORT} -> {SAVE_DIR}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
