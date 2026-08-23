#!/usr/bin/env python3
"""Local gallery and chunked upload studio for reviewing generated videos."""
from __future__ import annotations

import hashlib
import http.server
import json
import mimetypes
import os
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT / "projects"
UPLOAD_ROOT = ROOT / "uploads" / "preview-studio"
VIDEOS_ROOT = UPLOAD_ROOT / "videos"
PARTS_ROOT = UPLOAD_ROOT / ".parts"
CLI_PORT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else "8014"
PORT = int(os.environ.get("VIDEO_PREVIEW_PORT", CLI_PORT))
MAX_CHUNK = 4 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_FILES = 10
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".mkv"}


def safe_filename(value: str) -> str:
    name = Path(unquote(value or "preview.mp4")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-") or "preview.mp4"
    return cleaned[:140]


def safe_upload_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", value or "")
    return cleaned[:80] or uuid.uuid4().hex


def video_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]


def display_title(path: Path) -> str:
    stem = re.sub(r"[-_]+", " ", path.stem).strip()
    return stem[:1].upper() + stem[1:]


def inventory() -> tuple[list[dict], dict[str, Path]]:
    """Return generated/project videos and uploaded review videos."""
    candidates: list[tuple[str, Path]] = []
    for source, base in (("Project", PROJECTS_ROOT), ("Uploaded", VIDEOS_ROOT)):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                candidates.append((source, path))
    candidates.sort(key=lambda pair: pair[1].stat().st_mtime, reverse=True)
    result: list[dict] = []
    lookup: dict[str, Path] = {}
    for source, path in candidates:
        ident = video_id(path)
        lookup[ident] = path
        relative = path.relative_to(ROOT) if ROOT in path.resolve().parents else Path(path.name)
        stat = path.stat()
        result.append({
            "id": ident,
            "title": display_title(path),
            "source": source,
            "path": str(relative),
            "bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "url": f"/media/{ident}",
        })
    return result, lookup


def parse_range(value: str | None, size: int) -> tuple[int, int] | None:
    if not value or not value.startswith("bytes=") or "," in value:
        return None
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value.strip())
    if not match:
        return None
    first, last = match.groups()
    if not first and not last:
        return None
    if not first:
        length = min(int(last), size)
        return size - length, size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError("range not satisfiable")
    return start, end


PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Preview Room · Doodle Explainer</title><style>
:root{--ink:#191814;--paper:#efe8d7;--card:#fffaf0;--lime:#c7f36b;--orange:#ff7043;--blue:#3f75ff;--muted:#746e61;--line:#cec2ad}*{box-sizing:border-box}
body{margin:0;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:var(--paper)}body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.2;background-image:radial-gradient(#746e61 .65px,transparent .65px);background-size:8px 8px}
main{position:relative;max-width:1240px;margin:auto;padding:28px 20px 80px}.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;border-bottom:3px solid var(--ink);padding:18px 0 25px}.kicker{font:800 12px ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:#b33c1b}.hero h1{font-size:clamp(40px,7vw,82px);line-height:.85;letter-spacing:-.065em;margin:10px 0 13px}.hero p{max-width:630px;color:var(--muted);line-height:1.55;margin:0}.live{background:var(--lime);border:2px solid var(--ink);box-shadow:4px 4px var(--ink);padding:9px 13px;border-radius:999px;font-weight:900;white-space:nowrap}.toolbar{display:grid;grid-template-columns:1fr auto;gap:14px;margin:26px 0}.search{border:2px solid var(--ink);background:#fff;border-radius:14px;padding:13px 15px;font:inherit;min-width:0}.uploadButton{border:2px solid var(--ink);border-radius:14px;background:var(--orange);box-shadow:4px 4px var(--ink);color:#fff;padding:12px 18px;font-weight:900;cursor:pointer}.uploadButton:hover{transform:translate(-1px,-1px);box-shadow:5px 5px var(--ink)}
.drop{display:none;margin:0 0 25px;border:2px dashed var(--ink);border-radius:18px;padding:24px;background:#fff7e7;text-align:center}.drop.show{display:block}.drop.drag{background:#f1ffce;border-style:solid}.drop input{display:block;margin:14px auto}.drop small{color:var(--muted)}.progress{height:10px;border:1px solid var(--ink);background:white;border-radius:20px;overflow:hidden;margin-top:13px}.fill{height:100%;width:0;background:var(--blue)}.status{font:12px ui-monospace,monospace;margin-top:8px;color:var(--muted)}
.count{font:800 12px ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;margin:0 0 13px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.card{background:var(--card);border:2px solid var(--ink);border-radius:18px;overflow:hidden;box-shadow:5px 5px var(--ink)}.screen{background:#111;aspect-ratio:16/9;display:grid;place-items:center}.screen video{display:block;width:100%;height:100%;object-fit:contain}.meta{padding:14px 15px 16px}.meta h2{font-size:17px;margin:0 0 7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.row{display:flex;gap:8px;align-items:center;color:var(--muted);font-size:12px}.tag{background:var(--lime);color:var(--ink);border:1px solid var(--ink);border-radius:999px;padding:3px 7px;font-weight:800}.path{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.empty{grid-column:1/-1;border:2px dashed var(--line);border-radius:18px;padding:50px;text-align:center;color:var(--muted)}
@media(max-width:760px){main{padding:17px 13px 60px}.hero{display:block}.live{display:inline-block;margin-top:18px}.toolbar{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.card{box-shadow:3px 3px var(--ink)}}
</style></head><body><main><header class="hero"><div><div class="kicker">Doodle Explainer · Review Studio</div><h1>Preview<br>Room.</h1><p>Watch every generated project video in one place. Upload additional cuts from your phone or computer and compare them without downloading files.</p></div><div class="live">● LOCAL PREVIEWS</div></header>
<div class="toolbar"><input class="search" id="search" placeholder="Search videos or project paths…"><button class="uploadButton" id="toggle">＋ Add videos</button></div>
<section class="drop" id="drop"><b>Drop preview videos here</b><input id="files" type="file" multiple accept="video/*,.mp4,.mov,.webm,.mkv,.m4v"><small>Up to 10 videos · 1 GB each · MP4 works best in browsers</small><div class="progress"><div class="fill" id="fill"></div></div><div class="status" id="status">Ready.</div></section>
<div class="count" id="count">Loading videos…</div><section class="grid" id="grid"></section></main><script>
const $=x=>document.getElementById(x),CHUNK=4*1024*1024,WORKERS=6;let videos=[];const esc=s=>s.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));const size=n=>n>1e9?(n/1e9).toFixed(1)+' GB':n>1e6?(n/1e6).toFixed(1)+' MB':Math.ceil(n/1e3)+' KB';
function render(){const q=$('search').value.toLowerCase(),shown=videos.filter(v=>(v.title+' '+v.path).toLowerCase().includes(q));$('count').textContent=`${shown.length} VIDEO${shown.length===1?'':'S'} READY TO REVIEW`;$('grid').innerHTML=shown.length?shown.map(v=>`<article class="card"><div class="screen"><video controls preload="metadata" playsinline src="${v.url}"></video></div><div class="meta"><h2 title="${esc(v.title)}">${esc(v.title)}</h2><div class="row"><span class="tag">${esc(v.source)}</span><span>${size(v.bytes)}</span><span class="path" title="${esc(v.path)}">${esc(v.path)}</span></div></div></article>`).join(''):'<div class="empty">No matching videos.</div>'}
async function load(){const r=await fetch('/api/videos');const j=await r.json();videos=j.items;render()}$('search').oninput=render;$('toggle').onclick=()=>$('drop').classList.toggle('show');
const drop=$('drop');['dragenter','dragover'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.add('drag')}));['dragleave','drop'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.remove('drag')}));drop.addEventListener('drop',e=>upload([...e.dataTransfer.files]));$('files').onchange=e=>upload([...e.target.files]);
async function one(file,upload,fileNo,onBytes){const total=Math.ceil(file.size/CHUNK);let next=0;async function worker(){while(true){const index=next++;if(index>=total)return;const blob=file.slice(index*CHUNK,Math.min((index+1)*CHUNK,file.size));const r=await fetch(`/api/chunk?upload=${upload}&file=${fileNo}&name=${encodeURIComponent(file.name)}&index=${index}&total=${total}`,{method:'POST',body:blob});if(!r.ok)throw Error(await r.text());onBytes(blob.size)}}await Promise.all(Array.from({length:Math.min(total,WORKERS)},worker));return total}
async function upload(files){files=files.filter(f=>f.type.startsWith('video/')||/\.(mp4|mov|webm|mkv|m4v)$/i.test(f.name)).slice(0,10);if(!files.length)return;if(files.some(f=>f.size>1024**3))return alert('One video is larger than 1 GB.');drop.classList.add('show');const id=crypto.randomUUID().replaceAll('-',''),all=files.reduce((a,f)=>a+f.size,0);let sent=0;$('status').textContent='Uploading…';try{const totals=[];for(let i=0;i<files.length;i++)totals.push(await one(files[i],id,i,n=>{sent+=n;$('fill').style.width=(sent/all*100)+'%';$('status').textContent=`Uploading ${i+1}/${files.length} · ${Math.round(sent/all*100)}%`}));const r=await fetch('/api/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({upload_id:id,files:files.map((f,i)=>({name:f.name,total:totals[i]}))})});const j=await r.json();if(!r.ok)throw Error(j.error||'Upload failed');$('status').textContent=`Added ${j.files.length} video(s).`;$('fill').style.width='100%';await load()}catch(e){$('status').textContent='ERROR: '+e.message}}
load();</script></body></html>'''


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "VideoPreviewStudio/1.0"

    def send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, status: int, data: object) -> None:
        self.send_bytes(status, json.dumps(data).encode(), "application/json")

    def params(self) -> dict[str, str]:
        values = parse_qs(urlparse(self.path).query)
        return {key: value[0] for key, value in values.items() if value}

    def read_body(self, limit: int) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > limit:
            raise ValueError("invalid request size")
        data = self.rfile.read(length)
        if len(data) != length:
            raise ValueError("truncated request")
        return data

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_bytes(200, PAGE.encode(), "text/html; charset=utf-8")
        elif parsed.path == "/api/videos":
            items, _ = inventory()
            self.send_json(200, {"items": items})
        elif parsed.path.startswith("/media/"):
            self.serve_video(parsed.path.removeprefix("/media/"))
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/chunk":
                self.receive_chunk()
            elif parsed.path == "/api/complete":
                self.complete_upload()
            else:
                self.send_json(404, {"error": "not found"})
        except Exception as exc:
            print(f"ERROR {type(exc).__name__}: {exc}", flush=True)
            self.send_json(500, {"error": str(exc)})

    def receive_chunk(self) -> None:
        p = self.params()
        upload = safe_upload_id(p.get("upload", ""))
        file_no = int(p.get("file", "-1"))
        index, total = int(p.get("index", "-1")), int(p.get("total", "0"))
        name = safe_filename(p.get("name", ""))
        if file_no not in range(MAX_FILES) or index < 0 or total <= 0 or index >= total:
            raise ValueError("invalid chunk coordinates")
        if Path(name).suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError("unsupported video extension")
        data = self.read_body(MAX_CHUNK)
        folder = PARTS_ROOT / upload / f"{file_no:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{index:06d}.part").write_bytes(data)
        (folder / "meta.json").write_text(json.dumps({"name": name, "total": total}))
        self.send_json(200, {"ok": True})

    def complete_upload(self) -> None:
        payload = json.loads(self.read_body(256 * 1024))
        upload = safe_upload_id(payload.get("upload_id", ""))
        files = payload.get("files") or []
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
            raise ValueError("invalid file list")
        VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
        completed = []
        for file_no, requested in enumerate(files):
            folder = PARTS_ROOT / upload / f"{file_no:02d}"
            meta = json.loads((folder / "meta.json").read_text())
            total = int(requested.get("total", meta["total"]))
            if total != int(meta["total"]):
                raise ValueError("part count mismatch")
            name = safe_filename(requested.get("name", meta["name"]))
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            destination = VIDEOS_ROOT / f"{stamp}-{file_no + 1:02d}-{name}"
            total_bytes = 0
            with destination.open("wb") as target:
                for index in range(total):
                    part = folder / f"{index:06d}.part"
                    if not part.exists():
                        raise ValueError(f"missing chunk {index}")
                    data = part.read_bytes()
                    total_bytes += len(data)
                    if total_bytes > MAX_TOTAL:
                        raise ValueError("video exceeds 1 GB")
                    target.write(data)
            completed.append({"name": destination.name, "bytes": total_bytes})
        shutil.rmtree(PARTS_ROOT / upload, ignore_errors=True)
        self.send_json(200, {"ok": True, "files": completed})

    def serve_video(self, ident: str) -> None:
        _, lookup = inventory()
        path = lookup.get(ident)
        if not path or not path.is_file():
            self.send_json(404, {"error": "video not found"})
            return
        size = path.stat().st_size
        try:
            selected = parse_range(self.headers.get("Range"), size)
        except ValueError:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        start, end = selected or (0, size - 1)
        length = end - start + 1
        self.send_response(206 if selected else 200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "video/mp4")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        if selected:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining:
                data = handle.read(min(1024 * 1024, remaining))
                if not data:
                    break
                self.wfile.write(data)
                remaining -= len(data)

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[preview-studio] " + fmt % args + "\n")


if __name__ == "__main__":
    VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Preview Studio listening on http://0.0.0.0:{PORT}", flush=True)
    print(f"Project gallery: {PROJECTS_ROOT}", flush=True)
    print(f"Uploaded previews: {VIDEOS_ROOT}", flush=True)
    server.serve_forever()
