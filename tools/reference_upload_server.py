#!/usr/bin/env python3
"""Fast reference-video intake studio for the doodle explainer agent.

The browser uploads in parallel 4 MiB chunks. Completed videos are stored under
uploads/references/<project-id>/ together with creative notes, technical metadata,
eight representative frames, a contact sheet, and READY_FOR_ANALYSIS.md.

No cloud storage or third-party service is used.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
UPLOAD_ROOT = ROOT / "uploads" / "references"
PARTS_ROOT = UPLOAD_ROOT / ".parts"
LATEST = UPLOAD_ROOT / "latest.json"
CLI_PORT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else "8013"
PORT = int(os.environ.get("REFERENCE_UPLOAD_PORT", CLI_PORT))
MAX_CHUNK = 4 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_FILES = 5
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
FFMPEG = shutil.which("ffmpeg") or str(Path.home() / ".local" / "bin" / "ffmpeg")


def safe_filename(value: str) -> str:
    value = Path(unquote(value or "reference.mp4")).name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-") or "reference"
    return stem[:120]


def safe_project_id(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "", value or "")
    return value[:80] or uuid.uuid4().hex[:16]


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def parse_media_info(path: Path) -> dict:
    command = [FFMPEG, "-hide_banner", "-i", str(path), "-f", "null", "-"]
    proc = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=90)
    text = proc.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    video_match = re.search(r"Video:.*?(\d{2,5})x(\d{2,5}).*?(\d+(?:\.\d+)?)\s*fps", text)
    audio_match = re.search(r"Audio:\s*([^,]+),\s*(\d+)\s*Hz,\s*([^,]+)", text)
    duration = None
    if duration_match:
        duration = int(duration_match.group(1)) * 3600 + int(duration_match.group(2)) * 60 + float(duration_match.group(3))
    return {
        "duration_seconds": round(duration, 3) if duration is not None else None,
        "width": int(video_match.group(1)) if video_match else None,
        "height": int(video_match.group(2)) if video_match else None,
        "fps": float(video_match.group(3)) if video_match else None,
        "video_codec": (re.search(r"Video:\s*([^,]+)", text) or [None, None])[1],
        "audio_codec": audio_match.group(1).strip() if audio_match else None,
        "audio_sample_rate": int(audio_match.group(2)) if audio_match else None,
        "audio_layout": audio_match.group(3).strip() if audio_match else None,
    }


def extract_reference_frames(video: Path, output_dir: Path, duration: float | None, count: int = 8) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not duration or duration <= 0:
        times = [0.0]
    else:
        # Avoid title cards and end cards while retaining the opening hook.
        start = min(0.5, duration * 0.03)
        end = max(start, duration * 0.94)
        times = [start + (end - start) * i / max(1, count - 1) for i in range(count)]
    names: list[str] = []
    for index, at in enumerate(times, 1):
        name = f"frame-{index:02d}.jpg"
        target = output_dir / name
        command = [
            FFMPEG, "-y", "-ss", f"{at:.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", str(target),
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=True)
        names.append(name)
    return names


def make_contact_sheet(frames_dir: Path, names: list[str], output: Path) -> None:
    from PIL import Image, ImageDraw

    cards = []
    for index, name in enumerate(names, 1):
        image = Image.open(frames_dir / name).convert("RGB")
        image.thumbnail((480, 270))
        card = Image.new("RGB", (480, 300), "white")
        card.paste(image, ((480 - image.width) // 2, 0))
        ImageDraw.Draw(card).text((12, 276), f"REFERENCE {index:02d}", fill=(25, 25, 25))
        cards.append(card)
    cols = 4
    rows = (len(cards) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 300), (235, 232, 224))
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % cols) * 480, (index // cols) * 300))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


def write_handoff(project_dir: Path, manifest: dict) -> None:
    focus = ", ".join(manifest.get("focus", [])) or "Not specified"
    files = "\n".join(f"- `{item['relative_path']}`" for item in manifest.get("files", []))
    text = f"""# Reference upload ready for analysis

Project ID: `{manifest['project_id']}`
Uploaded: {manifest['created_at']}
Reference/channel: {manifest.get('reference_name') or 'Not supplied'}
Focus: {focus}

## Creator notes

{manifest.get('notes') or 'No additional notes supplied.'}

## Source videos

{files}

## Agent analysis order

1. Inspect `manifest.json` and every `frames/contact-sheet.jpg`.
2. Sample full-resolution frames around visual changes when needed.
3. Measure shot cadence, composition, character construction, contour, palette,
   acting poses, camera behavior, transitions, narration and sound separately.
4. Write an original style specification; do not copy scripts, branding, exact
   characters, or protected drawings.
5. Ask for confirmation before generating a production video.
"""
    (project_dir / "READY_FOR_ANALYSIS.md").write_text(text, encoding="utf-8")


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reference Studio · Doodle Explainer</title>
<style>
:root{--ink:#171713;--paper:#f5f0e5;--card:#fffdf7;--orange:#ff6b35;--teal:#1d9b8a;--muted:#6f6b61;--line:#d8d0c0}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,sans-serif}
body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:radial-gradient(#8c8577 .55px,transparent .55px);background-size:7px 7px}
.wrap{position:relative;max-width:1060px;margin:auto;padding:38px 20px 70px}.top{display:flex;gap:18px;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.eyebrow{font:700 12px/1 ui-monospace,monospace;letter-spacing:.15em;color:var(--orange);text-transform:uppercase}.top h1{font-size:clamp(34px,6vw,66px);letter-spacing:-.055em;line-height:.92;margin:12px 0}.top p{max-width:620px;color:var(--muted);font-size:16px;line-height:1.55;margin:0}
.badge{white-space:nowrap;border:2px solid var(--ink);border-radius:999px;padding:9px 13px;background:#fff;box-shadow:3px 3px 0 var(--ink);font-size:12px;font-weight:800}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.panel{background:var(--card);border:2px solid var(--ink);border-radius:22px;padding:22px;box-shadow:6px 6px 0 var(--ink)}
.step{display:flex;align-items:center;gap:10px;margin-bottom:15px}.num{display:grid;place-items:center;width:31px;height:31px;border-radius:50%;background:var(--ink);color:white;font-weight:900}.step h2{font-size:18px;margin:0}
label{display:block;font-weight:750;font-size:13px;margin:14px 0 7px}input[type=text],textarea{width:100%;border:1.5px solid var(--line);background:white;border-radius:12px;padding:12px 13px;color:var(--ink);font:inherit;outline:none}input:focus,textarea:focus{border-color:var(--teal);box-shadow:0 0 0 3px #1d9b8a22}textarea{min-height:105px;resize:vertical}
.drop{position:relative;border:2px dashed #aaa08e;border-radius:17px;padding:28px 16px;text-align:center;background:#faf7ef;transition:.2s;cursor:pointer}.drop.drag{border-color:var(--orange);background:#fff1e9;transform:translateY(-2px)}.drop input{position:absolute;inset:0;opacity:0;cursor:pointer}.drop .icon{font-size:36px}.drop strong{display:block;font-size:17px;margin:6px}.drop small{color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip input{display:none}.chip span{display:block;border:1.5px solid var(--line);border-radius:999px;padding:8px 11px;background:white;font-size:12px;font-weight:700;cursor:pointer}.chip input:checked+span{background:var(--teal);border-color:var(--ink);color:white;box-shadow:2px 2px 0 var(--ink)}
.files{display:grid;gap:8px;margin-top:14px}.file{border:1px solid var(--line);border-radius:11px;padding:10px 12px;background:white;display:flex;justify-content:space-between;gap:12px;font-size:12px}.file b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.file span{color:var(--muted);white-space:nowrap}
button{width:100%;border:2px solid var(--ink);border-radius:13px;background:var(--orange);padding:14px;color:white;font:850 15px/1 inherit;margin-top:16px;box-shadow:4px 4px 0 var(--ink);cursor:pointer}button:hover{transform:translate(-1px,-1px);box-shadow:5px 5px 0 var(--ink)}button:disabled{opacity:.5;cursor:not-allowed;transform:none}
.progress{display:none;margin-top:17px}.track{height:12px;border:1.5px solid var(--ink);border-radius:999px;overflow:hidden;background:white}.fill{width:0;height:100%;background:var(--teal);transition:width .15s}.status{font:12px/1.5 ui-monospace,monospace;margin-top:8px;color:var(--muted);white-space:pre-wrap}.done{display:none;border:2px solid var(--teal);background:#e8fff9;border-radius:15px;padding:15px;margin-top:17px}.done strong{color:#087466}.recent{margin-top:20px}.recent h3{font-size:13px;text-transform:uppercase;letter-spacing:.1em}.upload-card{border-top:1px solid var(--line);padding:10px 0;font-size:12px}.upload-card a{color:var(--teal);font-weight:800}.privacy{font-size:12px;color:var(--muted);line-height:1.5;margin-top:15px}.scribble{font-family:cursive;color:var(--orange);transform:rotate(-2deg);font-size:18px;margin-top:12px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.top{display:block}.badge{display:inline-block;margin-top:18px}.panel{box-shadow:4px 4px 0 var(--ink)}.wrap{padding-top:24px}}
</style></head><body><main class="wrap">
<header class="top"><div><div class="eyebrow">Doodle Explainer · Reference Intake</div><h1>Show me the<br>visual language.</h1><p>Upload the YouTube reference videos you are allowed to use. I will receive the original files plus representative frames, so I can study the image style, characters, acting, camera, pacing and line work.</p></div><div class="badge">LOCAL + PRIVATE</div></header>
<div class="grid"><section class="panel"><div class="step"><div class="num">1</div><h2>Add reference videos</h2></div>
<div class="drop" id="drop"><input id="files" type="file" accept="video/mp4,video/quicktime,video/webm,video/x-matroska,.mp4,.mov,.mkv,.webm,.m4v" multiple><div class="icon">↥</div><strong>Drop videos here or tap to browse</strong><small>Up to 5 files · 1 GB each · uploads in 6 parallel streams</small></div><div class="files" id="fileList"></div>
<div class="privacy">Files go directly into this project workspace—never to a public host. Only upload videos you own or have permission to analyze.</div></section>
<section class="panel"><div class="step"><div class="num">2</div><h2>Tell me what to learn</h2></div>
<label>Channel or reference name</label><input id="name" type="text" placeholder="e.g. My favorite hand-drawn history channel">
<label>Analysis focus</label><div class="chips" id="focus">
<label class="chip"><input type="checkbox" value="character design" checked><span>Characters</span></label><label class="chip"><input type="checkbox" value="line and color style" checked><span>Line + color</span></label><label class="chip"><input type="checkbox" value="acting and expressions" checked><span>Acting</span></label><label class="chip"><input type="checkbox" value="camera movement"><span>Camera</span></label><label class="chip"><input type="checkbox" value="storytelling and pacing"><span>Storytelling</span></label><label class="chip"><input type="checkbox" value="background design"><span>Backgrounds</span></label><label class="chip"><input type="checkbox" value="editing and transitions"><span>Editing</span></label><label class="chip"><input type="checkbox" value="sound and narration"><span>Sound</span></label></div>
<label>Notes for the agent</label><textarea id="notes" placeholder="What do you love? Which moments, characters, poses, or images should I study? Add timestamps if useful."></textarea>
<div class="scribble">Your notes make the analysis much sharper ↗</div><button id="upload">Upload references</button><div class="progress" id="progress"><div class="track"><div class="fill" id="fill"></div></div><div class="status" id="status"></div></div><div class="done" id="done"><strong>✓ References received and prepared.</strong><div id="doneText"></div></div></section></div>
<section class="panel recent"><div class="step"><div class="num">3</div><h2>Recent reference packs</h2></div><div id="recent">Loading…</div></section>
</main><script>
const $=id=>document.getElementById(id), CHUNK=4*1024*1024, WORKERS=6, MAX=1024*1024*1024;let selected=[];
function size(n){const u=['B','KB','MB','GB'];let i=0;while(n>=1024&&i<3){n/=1024;i++}return n.toFixed(i?1:0)+' '+u[i]}
function renderFiles(){ $('fileList').innerHTML=selected.map(f=>`<div class="file"><b>${escapeHtml(f.name)}</b><span>${size(f.size)}</span></div>`).join('') }
function escapeHtml(s){return s.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
$('files').onchange=e=>{selected=[...e.target.files].slice(0,5);renderFiles()};const drop=$('drop');
['dragenter','dragover'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.add('drag')}));['dragleave','drop'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.remove('drag')}));drop.addEventListener('drop',e=>{selected=[...e.dataTransfer.files].filter(f=>f.type.startsWith('video/')||/\.(mp4|mov|mkv|webm|m4v)$/i.test(f.name)).slice(0,5);renderFiles()});
async function uploadOne(file,project,index,onBytes){const total=Math.ceil(file.size/CHUNK);let next=0;async function worker(){while(true){const i=next++;if(i>=total)return;const start=i*CHUNK,blob=file.slice(start,Math.min(start+CHUNK,file.size));const r=await fetch(`/api/chunk?project=${project}&file=${index}&name=${encodeURIComponent(file.name)}&index=${i}&total=${total}`,{method:'POST',body:blob});if(!r.ok)throw Error(await r.text()||`Chunk ${i} failed`);onBytes(blob.size)}}await Promise.all(Array.from({length:Math.min(WORKERS,total)},worker));return total}
$('upload').onclick=async()=>{if(!selected.length)return alert('Choose at least one video.');if(selected.some(f=>f.size>MAX))return alert('A file is over 1 GB.');const project=crypto.randomUUID().replaceAll('-',''),totalBytes=selected.reduce((a,f)=>a+f.size,0),started=performance.now();let sent=0;$('upload').disabled=true;$('progress').style.display='block';$('done').style.display='none';
try{const totals=[];for(let i=0;i<selected.length;i++){const onBytes=n=>{sent+=n;const pct=Math.round(sent/totalBytes*100),sec=Math.max((performance.now()-started)/1000,.1),mbps=sent*8/sec/1e6,eta=Math.ceil((totalBytes-sent)*8/Math.max(mbps,0.01)/1e6);$('fill').style.width=pct+'%';$('status').textContent=`Uploading ${i+1}/${selected.length} · ${pct}% · ${mbps.toFixed(1)} Mbps · ~${eta}s left`};totals.push(await uploadOne(selected[i],project,i,onBytes))}$('status').textContent='Assembling videos and extracting reference frames…';const focus=[...document.querySelectorAll('#focus input:checked')].map(x=>x.value);const r=await fetch('/api/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:project,files:selected.map((f,i)=>({name:f.name,total:totals[i]})),reference_name:$('name').value.trim(),notes:$('notes').value.trim(),focus})});const data=await r.json();if(!r.ok)throw Error(data.error||'Preparation failed');$('fill').style.width='100%';$('status').textContent='Ready for agent analysis.';$('done').style.display='block';$('doneText').innerHTML=`<br>Pack: <b>${escapeHtml(data.project_id)}</b><br>${data.files.length} video(s) · ${data.frame_count} representative frames<br><br>Return to chat and say <b>“analyze my latest references”</b>.`;loadRecent()}catch(e){$('status').textContent='ERROR: '+e.message}finally{$('upload').disabled=false}}
async function loadRecent(){try{const r=await fetch('/api/recent'),j=await r.json();$('recent').innerHTML=j.items.length?j.items.map(x=>`<div class="upload-card"><b>${escapeHtml(x.reference_name||'Untitled reference')}</b> · ${x.files} video(s)<br><span>${new Date(x.created_at).toLocaleString()}</span> · <a href="${x.contact_sheet}" target="_blank">view contact sheet</a></div>`).join(''):'No reference packs yet.'}catch(e){$('recent').textContent='Could not load recent packs.'}}loadRecent();
</script></body></html>'''


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "ReferenceStudio/1.0"

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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_bytes(200, PAGE.encode(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/recent":
            self.recent()
            return
        if parsed.path.startswith("/files/"):
            self.serve_file(parsed.path.removeprefix("/files/"))
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/chunk":
                self.chunk()
            elif parsed.path == "/api/complete":
                self.complete()
            else:
                self.send_json(404, {"error": "not found"})
        except Exception as exc:
            print(f"ERROR {type(exc).__name__}: {exc}", flush=True)
            self.send_json(500, {"error": str(exc)})

    def read_body(self, limit: int) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > limit:
            raise ValueError("invalid request size")
        data = self.rfile.read(length)
        if len(data) != length:
            raise ValueError("truncated request")
        return data

    def chunk(self) -> None:
        p = self.params()
        project = safe_project_id(p.get("project", ""))
        file_index = int(p.get("file", "-1"))
        index = int(p.get("index", "-1"))
        total = int(p.get("total", "0"))
        name = safe_filename(p.get("name", ""))
        if file_index < 0 or file_index >= MAX_FILES or index < 0 or total <= 0 or index >= total:
            raise ValueError("invalid chunk coordinates")
        if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError("unsupported video extension")
        data = self.read_body(MAX_CHUNK)
        folder = PARTS_ROOT / project / f"{file_index:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{index:06d}.part").write_bytes(data)
        atomic_json(folder / "upload.json", {"name": name, "total": total})
        self.send_json(200, {"ok": True, "bytes": len(data)})

    def complete(self) -> None:
        payload = json.loads(self.read_body(512 * 1024))
        project = safe_project_id(payload.get("project_id", ""))
        files = payload.get("files") or []
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
            raise ValueError("invalid file list")
        timestamp = datetime.now(timezone.utc)
        pack_id = timestamp.strftime("%Y%m%d-%H%M%S-") + project[:8]
        project_dir = UPLOAD_ROOT / pack_id
        videos_dir = project_dir / "videos"
        frames_root = project_dir / "frames"
        videos_dir.mkdir(parents=True, exist_ok=False)
        manifest_files = []
        frame_count = 0
        for file_index, requested in enumerate(files):
            part_dir = PARTS_ROOT / project / f"{file_index:02d}"
            upload_meta = json.loads((part_dir / "upload.json").read_text())
            name = safe_filename(requested.get("name", upload_meta["name"]))
            total = int(requested.get("total", upload_meta["total"]))
            if total != int(upload_meta["total"]):
                raise ValueError("part count mismatch")
            destination = videos_dir / name
            digest = hashlib.sha256()
            total_bytes = 0
            assembling = destination.with_suffix(destination.suffix + ".assembling")
            with assembling.open("wb") as target:
                for chunk_index in range(total):
                    part = part_dir / f"{chunk_index:06d}.part"
                    if not part.exists():
                        raise ValueError(f"missing chunk {chunk_index} for {name}")
                    data = part.read_bytes()
                    total_bytes += len(data)
                    if total_bytes > MAX_TOTAL:
                        raise ValueError(f"{name} exceeds 1 GB")
                    digest.update(data)
                    target.write(data)
            assembling.replace(destination)
            info = parse_media_info(destination)
            if not info.get("width"):
                raise ValueError(f"{name} does not contain a readable video stream")
            frame_dir = frames_root / f"video-{file_index + 1:02d}"
            frame_names = extract_reference_frames(destination, frame_dir, info.get("duration_seconds"))
            make_contact_sheet(frame_dir, frame_names, frame_dir / "contact-sheet.jpg")
            frame_count += len(frame_names)
            manifest_files.append({
                "name": name,
                "relative_path": str(destination.relative_to(project_dir)),
                "bytes": total_bytes,
                "sha256": digest.hexdigest(),
                "media": info,
                "frames": [str((frame_dir / item).relative_to(project_dir)) for item in frame_names],
                "contact_sheet": str((frame_dir / "contact-sheet.jpg").relative_to(project_dir)),
            })
        manifest = {
            "project_id": pack_id,
            "created_at": timestamp.isoformat(),
            "reference_name": str(payload.get("reference_name", ""))[:300],
            "notes": str(payload.get("notes", ""))[:10000],
            "focus": [str(item)[:100] for item in (payload.get("focus") or [])][:20],
            "files": manifest_files,
            "status": "ready_for_analysis",
        }
        atomic_json(project_dir / "manifest.json", manifest)
        write_handoff(project_dir, manifest)
        atomic_json(LATEST, {"project_id": pack_id, "path": str(project_dir.relative_to(ROOT)), "created_at": manifest["created_at"]})
        shutil.rmtree(PARTS_ROOT / project, ignore_errors=True)
        print(f"REFERENCE_READY {pack_id} -> {project_dir}", flush=True)
        self.send_json(200, {"ok": True, "project_id": pack_id, "files": manifest_files, "frame_count": frame_count})

    def recent(self) -> None:
        items = []
        if UPLOAD_ROOT.exists():
            for manifest_path in sorted(UPLOAD_ROOT.glob("*/manifest.json"), reverse=True)[:8]:
                try:
                    data = json.loads(manifest_path.read_text())
                    first = data["files"][0]
                    items.append({
                        "project_id": data["project_id"],
                        "reference_name": data.get("reference_name"),
                        "created_at": data["created_at"],
                        "files": len(data["files"]),
                        "contact_sheet": "/files/" + data["project_id"] + "/" + first["contact_sheet"],
                    })
                except Exception:
                    continue
        self.send_json(200, {"items": items})

    def serve_file(self, relative: str) -> None:
        candidate = (UPLOAD_ROOT / relative).resolve()
        root = UPLOAD_ROOT.resolve()
        if root not in candidate.parents or not candidate.is_file():
            self.send_json(404, {"error": "file not found"})
            return
        allowed = {".jpg", ".jpeg", ".png", ".json", ".md"}
        if candidate.suffix.lower() not in allowed:
            self.send_json(403, {"error": "preview not allowed"})
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_bytes(200, candidate.read_bytes(), content_type)

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[reference-studio] " + fmt % args + "\n")


if __name__ == "__main__":
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Reference Studio listening on http://0.0.0.0:{PORT}", flush=True)
    print(f"Uploads: {UPLOAD_ROOT}", flush=True)
    server.serve_forever()
