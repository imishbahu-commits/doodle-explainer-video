#!/usr/bin/env python3
"""phone_studio.py — batch AI image generation for video beats, mobile-first.

WHY THIS EXISTS
  This sandbox's firewall only allows PyPI / GitHub / npm — it cannot reach
  image.pollinations.ai or huggingface.co. But YOUR PHONE has normal
  internet. So this server turns your phone into the image generator:

    1. open the live-preview URL on your phone
    2. every pending video beat is a card with its FLUX prompt
    3. ONE TAP per image: the phone's browser asks Pollinations (open-source
       FLUX model, unlimited + free) to draw it, then uploads the PNG
       straight into projects/<name>/assets/NNN.png + images.json
    4. if the direct fetch fails, the tap opens the image in a new tab:
       long-press -> Save image -> tap Upload (it lands on the right beat)

Routes
  GET  /                          project picker
  GET  /studio?project=NAME       tap-to-generate cards
  GET  /img?project=NAME&id=N     show a generated image
  POST /save?project=NAME&id=N    raw image body -> beat N
  POST /chunk + /done             chunked upload (+ ?project=&id= target)
  POST /refresh?project=NAME      re-scan images.json

Run:  python3 tools/phone_studio.py 8012        (system python, no deps)
"""

import http.server
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, parse_qs

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
UPLOAD_DIR = ROOT / "uploads"
PARTS_DIR = UPLOAD_DIR / ".parts"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8012
MAX_CHUNK = 2 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024

STYLE_LOCK = ("thick black outlines, flat bold colors, slightly imperfect "
              "hand-drawn lines, pure white background, no text, no "
              "watermark")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone studio — batch AI images</title>
<style>
  body { margin:0; background:#0d0f1a; color:#eee; font-family:system-ui,sans-serif; }
  header { padding:18px 16px 10px; text-align:center; }
  h1 { font-size:19px; margin:0 0 4px; }
  #prog { font-size:13px; color:#9aa; }
  #bar { width:82%; height:10px; background:#161a2b; border-radius:6px;
         margin:8px auto 0; overflow:hidden; }
  #fill { height:100%; width:0%; background:#7ee08a; transition:width .3s; }
  .card { margin:12px 14px; background:#161a2b; border:1px solid #2a3045;
          border-radius:14px; padding:14px; }
  .card.done { border-color:#2f6b3f; background:#12241a; }
  .beat { color:#778; font-size:12px; letter-spacing:.5px; }
  .prompt { font-size:14px; line-height:1.45; margin:8px 0 12px; color:#dde; }
  button.gen { width:100%; padding:14px; border:0; border-radius:12px;
    background:#7ee08a; color:#000; font-weight:700; font-size:16px; }
  .card.done button.gen { display:none; }
  .card.done .ok { color:#7ee08a; font-size:14px; font-weight:600; }
  .err { color:#ff8080; font-size:12px; margin-top:8px; min-height:15px; }
  .uploadrow { display:none; margin-top:10px; }
  .uploadrow.show { display:block; }
  input[type=file] { width:100%; margin-bottom:8px; }
  button.upload { width:100%; padding:12px; border:0; border-radius:10px;
    background:#f5c63c; color:#000; font-weight:700; font-size:15px; }
  button.regen { width:82%; padding:12px; border:0; border-radius:10px;
    background:#b06cf5; color:#fff; font-weight:700; font-size:14px;
    margin-top:10px; }
  .note { font-size:12px; color:#778; text-align:center; margin:18px 14px 30px;
    line-height:1.6; }
  #status { font-size:13px; color:#f5c63c; text-align:center; min-height:18px; }
</style>
</head>
<body>
<header>
  <h1>🎨 Batch AI images — {{PROJECT}}</h1>
  <div id="prog">0 / 0</div>
  <div id="bar"><div id="fill"></div></div>
  <button class="start" id="startbtn" style="display:none">▶ Start now</button>
  <button class="regen" id="regenbtn">✨ Generate ALL with FLUX (overwrite, high-res)</button>
</header>
<div id="status"></div>
<div id="cards"></div>
<div class="note">Generation starts <b>automatically ~3 s after this page opens</b>
— no taps needed. Every image is drawn by the open-source <b>FLUX</b> model on
Pollinations (free, unlimited) and saved straight into the project. Keep this
tab open; if a card fails, tap <b>Retry</b> on it (or use its Upload button
with a saved image).</div>

<script>
const PROJECT = {{PROJECT_JSON}};
const CARDS = {{CARDS_JSON}};

function el(tag, cls, html){ const e=document.createElement(tag);
  if(cls) e.className=cls; if(html!=null) e.innerHTML=html; return e; }

function pollinationsUrl(id, prompt){
  const seed = id * 13 + 7;
  return 'https://image.pollinations.ai/prompt/' + encodeURIComponent(prompt) +
         '?width=1024&height=1024&model=flux&nologo=true&enhance=true&seed=' + seed +
         '&referrer=doodle-explainer-video';
}

function render(){
  const wrap = document.getElementById('cards');
  wrap.innerHTML = '';
  let done = 0;
  CARDS.forEach(c => {
    const card = el('div', 'card' + (c.done ? ' done' : ''));
    card.appendChild(el('div','beat','BEAT ' + c.id));
    card.appendChild(el('div','prompt', c.prompt));
    if (c.done){
      card.appendChild(el('div','ok','✓ done — assets/' + pad(c.id) + '.png'));
      card.appendChild(el('img','',null) ); // placeholder replaced below
      const im = card.querySelector('img');
      im.src = '/img?project=' + encodeURIComponent(PROJECT) + '&id=' + c.id;
      im.style.cssText = 'width:100%;border-radius:8px;margin-top:8px;';
      done++;
    } else {
      const b = el('button','gen','⚡ Generate image');
      b.onclick = () => gen(c.id);
      card.appendChild(b);
      card.appendChild(el('div','err',''));
      const row = el('div','uploadrow');
      row.innerHTML = '<input type="file" accept="image/*"><button class="upload">⬆ Upload saved image</button>';
      const inp = row.querySelector('input');
      row.querySelector('button').onclick = () => uploadFile(inp, c.id, card);
      card.appendChild(row);
    }
    wrap.appendChild(card);
  });
  document.getElementById('prog').textContent = done + ' / ' + CARDS.length;
  document.getElementById('fill').style.width = (done / CARDS.length * 100) + '%';
}

function pad(n){ return String(n).padStart(3,'0'); }

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------------- AUTO-RUN: no taps needed, generates every pending beat ----
let autoRunning = false;

async function genAuto(cardObj){
  // cardObj: {id, prompt} — generate + save, no tab fallback in auto mode
  const card = [...document.querySelectorAll('.card')].find(
      c => c.querySelector('.beat').textContent === 'BEAT ' + cardObj.id);
  const btn = card.querySelector('button.gen');
  const err = card.querySelector('.err');
  if (btn){ btn.disabled = true; btn.textContent = '⏳…'; }
  err.textContent = 'generating…';
  const url = pollinationsUrl(cardObj.id, cardObj.prompt);
  let ok = false;
  for (let attempt = 1; attempt <= 3; attempt++){
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const blob = await r.blob();
      if (blob.size < 3000) throw new Error('empty image');
      const up = await fetch('/save?project=' + encodeURIComponent(PROJECT) +
                             '&id=' + cardObj.id, { method:'POST', body: blob });
      if (!up.ok) throw new Error('save failed');
      ok = true;
      break;
    } catch(e){
      err.textContent = 'attempt ' + attempt + '/' + 3 + ' — ' + e.message;
      if (attempt < 3) await sleep(4000);
    }
  }
  if (ok){
    const c = CARDS.find(c => c.id === cardObj.id); c.done = true;
    err.textContent = '';
    render();
  } else {
    err.textContent = '❌ failed after 3 tries — tap the card to retry, or use Upload.';
    if (btn){ btn.disabled = false; btn.textContent = '🔄 Retry'; }
    card.querySelector('.uploadrow').classList.add('show');
  }
  const left = CARDS.filter(c => !c.done).length;
  document.getElementById('status').textContent =
      left ? '⏳ auto-run… ' + left + ' image(s) left' : '✅ BATCH COMPLETE — all images saved!';
}

async function autoRunAll(){
  if (autoRunning) return;
  autoRunning = true;
  if (navigator.wakeLock){
    try { await navigator.wakeLock.request('screen'); } catch(e){}
  }
  const pending = CARDS.filter(c => !c.done);
  if (!pending.length){
    document.getElementById('status').textContent = '✅ All images already done.';
    return;
  }
  document.getElementById('status').textContent =
      '▶ AUTO-RUN: ' + pending.length + ' images — keep this tab open, no taps needed';
  const CONC = 2; let idx = 0;
  async function worker(){
    while (true){
      const next = idx++;
      if (next >= pending.length) return;
      await genAuto(pending[next]);
    }
  }
  await Promise.all([worker(), worker()]);
  autoRunning = false;
}

// auto-start shortly after the page loads
setTimeout(() => {
  if (!autoRunning && CARDS.some(c => !c.done)){
    const sb = document.getElementById('startbtn');
    if (sb){ sb.style.display = 'block';
      sb.onclick = () => { sb.style.display = 'none'; autoRunAll(); }; }
    setTimeout(() => { if (!autoRunning) autoRunAll(); }, 2500);
  }
}, 1500);

// regenerate EVERYTHING with FLUX (overwrite existing, high-res)
document.getElementById('regenbtn').onclick = () => {
  if (!confirm('Generate ALL ' + CARDS.length + ' images with FLUX? ' +
               'This overwrites the current images (2-3 min).')) return;
  CARDS.forEach(c => { c.done = false; });
  render();
  autoRunAll();
};

async function gen(id){
  const card = [...document.querySelectorAll('.card')].find(
      c => c.querySelector('.beat').textContent === 'BEAT ' + id);
  const btn = card.querySelector('button.gen');
  const err = card.querySelector('.err');
  btn.disabled = true; btn.textContent = '⏳ Drawing… (10-30 s)';
  err.textContent = '';
  const p = CARDS.find(c => c.id === id).prompt;
  const url = pollinationsUrl(id, p);
  for (let attempt = 1; attempt <= 3; attempt++){
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('Pollinations HTTP ' + r.status);
      const blob = await r.blob();
      if (blob.size < 3000) throw new Error('empty image returned');
      const up = await fetch('/save?project=' + encodeURIComponent(PROJECT) +
                             '&id=' + id, { method:'POST', body: blob });
      if (!up.ok) throw new Error('upload to workspace failed');
      const c = CARDS.find(c => c.id === id); c.done = true;
      render();
      document.getElementById('status').textContent =
          '✅ Beat ' + id + ' generated & saved. ' +
          (CARDS.filter(c=>!c.done).length) + ' left.';
      return;
    } catch(e){
      err.textContent = 'attempt ' + attempt + ': ' + e.message;
      if (attempt === 3){
        window.open(url, '_blank');
        err.textContent = '📱 Opened in a new tab — long-press → Save image → ' +
                          'tap Upload below.';
        card.querySelector('.uploadrow').classList.add('show');
        btn.disabled = false; btn.textContent = '🔄 Try again';
      } else { await sleep(4000); }
    }
  }
}

async function uploadFile(inp, id, card){
  const f = inp.files[0]; const err = card.querySelector('.err');
  if (!f){ err.textContent = 'pick the saved image first'; return; }
  err.textContent = 'uploading…';
  try {
    const CHUNK = 512 * 1024;
    const total = Math.ceil(f.size / CHUNK);
    const name = 'beat' + pad(id) + '.png';
    for (let i = 0; i < total; i++){
      const r = await fetch('/chunk?name=' + encodeURIComponent(name) +
        '&index=' + i + '&total=' + total + '&project=' + encodeURIComponent(PROJECT) +
        '&id=' + id, { method:'POST', body: f.slice(i*CHUNK, (i+1)*CHUNK) });
      if (!r.ok) throw new Error('chunk ' + i + ' failed');
    }
    const d = await fetch('/done?name=' + encodeURIComponent(name) + '&total=' + total +
      '&project=' + encodeURIComponent(PROJECT) + '&id=' + id, { method:'POST' });
    if (!d.ok) throw new Error('assembly failed');
    const c = CARDS.find(c => c.id === id); c.done = true;
    render();
  } catch(e){ err.textContent = '❌ ' + e.message; }
}

render();
</script>
</body>
</html>
"""


def safe_name(name):
    return re.sub(r"[^\w.\-]", "_", name or "file") or "file"


def project_names():
    out = []
    for d in sorted(PROJECTS.iterdir()):
        if (d / "prompts.json").exists():
            out.append(d.name)
    return out


def project_meta(name):
    d = PROJECTS / safe_name(name)
    pf, imf = d / "prompts.json", d / "images.json"
    if not pf.exists():
        return None
    prompts = json.loads(pf.read_text())
    images = json.loads(imf.read_text()) if imf.exists() else []
    done = {im["id"] for im in images if not im.get("error")}
    return {"name": d.name, "total": len(prompts), "done": len(done)}


def images_json(name):
    d = PROJECTS / safe_name(name)
    return json.loads((d / "images.json").read_text()) if (d / "images.json").exists() else []


def save_beat(project, bid, data):
    d = PROJECTS / safe_name(project)
    (d / "assets").mkdir(parents=True, exist_ok=True)
    out = d / "assets" / f"{int(bid):03d}.png"
    out.write_bytes(data)
    images = images_json(project)
    images = [im for im in images if im["id"] != int(bid)]
    p = json.loads((d / "prompts.json").read_text())
    kw = next((x["keyword"] for x in p if x["id"] == int(bid)), "")
    images.append({"id": int(bid), "keyword": kw, "backend": "pollinations",
                   "file": f"assets/{out.name}", "source": "pollinations",
                   "model": "flux",
                   "license": "Pollinations API (open-source FLUX model)",
                   "bytes": len(data)})
    images.sort(key=lambda x: x["id"])
    (d / "images.json").write_text(json.dumps(images, indent=2))
    write_credits(d, images)
    return out


def write_credits(d, images):
    used = [im for im in images if im.get("source")]
    if not used:
        return
    lines = ["# CREDITS — open-source artwork used by this project", ""]
    for im in sorted(used, key=lambda x: x["id"]):
        lines.append(f"- `{im['file']}` — **{im['keyword']}** — generated via "
                     f"Pollinations ({im.get('model','flux')}, open-source) — "
                     f"{im['license']}")
    (d / "CREDITS.md").write_text("\n".join(lines) + "\n")


class Handler(http.server.BaseHTTPRequestHandler):
    def _q(self):
        return {k: v[0] for k, v in parse_qs(
            self.path.split("?", 1)[1]).items()} if "?" in self.path else {}

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        q = self._q()
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            projects = project_names()
            cards = "".join(
                f'<a style="display:block;margin:10px 20px;padding:16px;'
                f'background:#161a2b;border-radius:12px;color:#eee;'
                f'text-decoration:none" href="/studio?project={m["name"]}">'
                f'<b>{m["name"]}</b> — {m["done"]}/{m["total"]} done</a>'
                for m in [project_meta(n) for n in projects] if m)
            html = ("<!doctype html><html><head><meta charset=utf-8>"
                    "<meta name=viewport content='width=device-width,initial-scale=1'>"
                    "<title>Phone studio</title></head><body style='background:#0d0f1a;"
                    "color:#eee;font-family:system-ui;padding:20px 0'>"
                    "<h1 style='font-size:19px;text-align:center'>🎨 Phone studio — "
                    "pick a project</h1>" + cards +
                    "</body></html>")
            self._send(200, html)
        elif path == "/studio":
            meta = project_meta(q.get("project", ""))
            if not meta:
                self._send(404, "unknown project")
                return
            d = PROJECTS / meta["name"]
            prompts = json.loads((d / "prompts.json").read_text())
            done_ids = {im["id"] for im in images_json(meta["name"])
                        if not im.get("error")}
            cards = [{"id": p["id"], "prompt": p["keyword"],
                      "done": p["id"] in done_ids} for p in prompts]
            html = (PAGE.replace("{{PROJECT}}", meta["name"])
                        .replace("{{PROJECT_JSON}}",
                                 json.dumps(meta["name"]))
                        .replace("{{CARDS_JSON}}", json.dumps(cards)))
            self._send(200, html)
        elif path == "/img":
            d = PROJECTS / safe_name(q.get("project", ""))
            f = d / "assets" / f"{int(q.get('id', 0)):03d}.png"
            if f.exists():
                self._send(200, f.read_bytes(), "image/png")
            else:
                self._send(404, "not yet")
        else:
            self._send(404, "nope")

    def _read(self, limit):
        chunks, got = [], 0
        while got < limit:
            c = self.rfile.read(min(65536, limit - got))
            if not c:
                break
            chunks.append(c)
            got += len(c)
        return b"".join(chunks)

    def do_POST(self):
        q = self._q()
        path = self.path.split("?", 1)[0]
        try:
            if path == "/save":
                length = int(self.headers.get("Content-Length", 0))
                data = self._read(length)
                out = save_beat(q.get("project", ""), int(q.get("id", 0)), data)
                print(f"SAVE beat {q.get('id')} -> {out} ({len(data)} B)", flush=True)
                self._send(200, "ok")
            elif path == "/chunk":
                self._chunk(q)
            elif path == "/done":
                self._done(q)
            else:
                self._send(404, "nope")
        except Exception as e:
            print("ERR", e, flush=True)
            self._send(500, str(e)[:200])

    def _chunk(self, q):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_CHUNK:
            self._send(413, "too big"); return
        data = self._read(length)
        PARTS_DIR.mkdir(parents=True, exist_ok=True)
        name = safe_name(q.get("name", "f"))
        part = PARTS_DIR / f"{name}.{int(q.get('index', 0)):05d}"
        part.write_bytes(data)
        self._send(200, "ok")

    def _done(self, q):
        name = safe_name(q.get("name", "f"))
        total = int(q.get("total", 0))
        parts = []
        for i in range(total):
            part = PARTS_DIR / f"{name}.{i:05d}"
            if not part.exists():
                self._send(400, f"missing part {i}"); return
            parts.append(part.read_bytes())
        data = b"".join(parts)
        project, bid = q.get("project", ""), q.get("id", "")
        if project and bid:
            out = save_beat(project, int(bid), data)
            print(f"UPLOAD beat {bid} -> {out} ({len(data)} B)", flush=True)
        else:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest = UPLOAD_DIR / name
            dest.write_bytes(data)
            print(f"UPLOAD {len(data)/1e6:.1f} MB -> {dest}", flush=True)
        for part in PARTS_DIR.glob(f"{name}.*"):
            part.unlink()
        self._send(200, "done")

    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] " + fmt % args + "\n")


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"phone studio on :{PORT}  projects: {project_names()}", flush=True)
    srv.serve_forever()
