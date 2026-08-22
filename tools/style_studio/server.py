#!/usr/bin/env python3
"""Reference Studio — upload reference videos, measure their style, reuse it.

Serves the studio UI and runs `scripts/analyze_style.py` as background jobs:

  POST /api/upload            upload one or more reference videos
  GET  /api/studio            list videos, jobs, merged profile, current style
  GET  /api/videos/{id}/*     per-video summary, shots, artifacts, playback
  POST /api/videos/{id}/promote   make this profile the current production style
  POST /api/combine           merge all analyzed profiles into one style bible
  DELETE /api/videos/{id}     remove an upload and its analysis

Durable artifacts live under stylehub/ (uploads/, profiles/, combined/,
current.json, studio.json). The merged/current style_rules.json is
schema-compatible with references/paint-explainer-analysis-4v/style_rules.json,
so skills/content-router consumes it unchanged.

Run:  .venv/bin/python tools/style_studio/server.py --host 0.0.0.0 --port 8765
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import imageio_ffmpeg
import uvicorn
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
STYLEHUB = ROOT / "stylehub"
UPLOADS = STYLEHUB / "uploads"
PROFILES = STYLEHUB / "profiles"
COMBINED = STYLEHUB / "combined"
CURRENT = STYLEHUB / "current.json"
STUDIO_STATE = STYLEHUB / "studio.json"
PY = str(ROOT / ".venv" / "bin" / "python")
ANALYZER = str(ROOT / "scripts" / "analyze_style.py")
STATIC_DIR = Path(__file__).resolve().parent / "static"

ALLOWED_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi", ".mpeg", ".mpg"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB per file
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Codec preference for picking the "real" video stream when a container holds
# several (e.g. an attached cover image before the actual video).
VIDEO_CODEC_PRIORITY = [
    "h264", "hevc", "vp9", "av1", "hvc1", "avc1", "vp8",
    "mpeg4", "mpeg2video", "msmpeg4v3", "theora", "mjpeg", "png", "gif",
]
MIN_DURATION_SECONDS = 0.5

app = FastAPI(title="Reference Studio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------------------------------------------------------
# state
# ----------------------------------------------------------------------------

_state_lock = threading.Lock()
_jobs: queue.Queue[dict[str, Any]] = queue.Queue()
_videos: dict[str, dict[str, Any]] = {}
_worker_started = False


def _persist() -> None:
    with _state_lock:
        payload = {
            "videos": _videos,
            "combined": _combined_info(),
            "current": _current_info(),
        }
        STYLEHUB.mkdir(parents=True, exist_ok=True)
        STUDIO_STATE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load() -> None:
    global _videos
    if STUDIO_STATE.exists():
        try:
            data = json.loads(STUDIO_STATE.read_text(encoding="utf-8"))
            _videos = data.get("videos", {})
            for vid in _videos.values():
                if vid.get("status") in {"queued", "analyzing"}:
                    vid["status"] = "interrupted"
                    vid["error"] = "Studio restarted while the job was running; re-queue it."
        except (json.JSONDecodeError, OSError):
            _videos = {}
    for prof in sorted(PROFILES.glob("*")) if PROFILES.exists() else []:
        if not prof.is_dir():
            continue
        vid = prof.name
        if vid not in _videos and (prof / "metrics.json").exists():
            metrics = json.loads((prof / "metrics.json").read_text(encoding="utf-8"))
            _videos[vid] = {
                "id": vid,
                "original_name": metrics["identity"]["file"],
                "label": metrics["identity"].get("label") or metrics["identity"]["file"],
                "source_path": metrics["identity"]["path"],
                "profile_dir": str(prof),
                "status": "done",
                "progress": {"stage": "done", "pct": 100, "message": "Analysis complete"},
                "created_at": prof.stat().st_mtime,
            }


def _combined_info() -> dict[str, Any] | None:
    combined_json = COMBINED / "combined.json"
    if not combined_json.exists():
        return None
    data = json.loads(combined_json.read_text(encoding="utf-8"))
    data["_updated_at"] = combined_json.stat().st_mtime
    return data


def _current_info() -> dict[str, Any] | None:
    if not CURRENT.exists():
        return None
    data = json.loads(CURRENT.read_text(encoding="utf-8"))
    data["_updated_at"] = CURRENT.stat().st_mtime
    return data


# ----------------------------------------------------------------------------
# background worker
# ----------------------------------------------------------------------------

def _run_analyze(vid: str, label: str) -> None:
    with _state_lock:
        video = _videos[vid]
        video["status"] = "analyzing"
        video["error"] = None
        _persist_unlocked()
    profile = Path(video["profile_dir"])
    progress_file = profile / "progress.json"
    proc = subprocess.run(
        [PY, ANALYZER, "analyze",
         "--video", video["source_path"],
         "--out", str(profile),
         "--label", label,
         "--progress", str(progress_file),
         "--analyzed-at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())],
        capture_output=True, text=True,
    )
    with _state_lock:
        if proc.returncode == 0:
            video["status"] = "done"
            video["progress"] = {"stage": "done", "pct": 100, "message": "Analysis complete"}
        else:
            tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-6:])
            video["status"] = "failed"
            video["error"] = tail
            video["progress"] = {"stage": "failed", "pct": 100, "message": tail[:240]}
        _persist_unlocked()


def _run_combine() -> None:
    done = [Path(v["profile_dir"]) for v in _videos.values() if v.get("status") == "done"]
    if len(done) < 2:
        return
    progress_file = COMBINED / "progress.json"
    proc = subprocess.run(
        [PY, ANALYZER, "combine",
         "--dirs", *[str(d) for d in done],
         "--out", str(COMBINED),
         "--label", f"{len(done)}-video merged profile",
         "--progress", str(progress_file)],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        (COMBINED / "progress.json").write_text(
            json.dumps({"stage": "done", "pct": 100, "message": "Merged profile ready"}),
            encoding="utf-8")
    else:
        (COMBINED / "progress.json").write_text(
            json.dumps({"stage": "failed", "pct": 100,
                        "message": (proc.stderr or proc.stdout)[-240:]}), encoding="utf-8")
    _persist()


def _worker() -> None:
    while True:
        job = _jobs.get()
        try:
            if job["kind"] == "analyze":
                _run_analyze(job["id"], job["label"])
                _run_combine()
            elif job["kind"] == "combine":
                _run_combine()
        except Exception as exc:  # noqa: BLE001 — keep the worker alive
            with _state_lock:
                video = _videos.get(job.get("id", ""))
                if video:
                    video["status"] = "failed"
                    video["error"] = str(exc)
                _persist_unlocked()
        finally:
            _jobs.task_done()


def _ensure_worker() -> None:
    global _worker_started
    if not _worker_started:
        _worker_started = True
        threading.Thread(target=_worker, daemon=True, name="studio-worker").start()


def _persist_unlocked() -> None:
    payload = {
        "videos": _videos,
        "combined": _combined_info(),
        "current": _current_info(),
    }
    STYLEHUB.mkdir(parents=True, exist_ok=True)
    STUDIO_STATE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ----------------------------------------------------------------------------
# api
# ----------------------------------------------------------------------------

@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/studio")
async def studio() -> JSONResponse:
    with _state_lock:
        videos = sorted(_videos.values(), key=lambda v: v.get("created_at", 0), reverse=True)
        cards = [_card(v) for v in videos]
    return JSONResponse({
        "videos": cards,
        "combined": _combined_info(),
        "current": _current_info(),
        "queue_depth": _jobs.qsize(),
        "models": {
            "transcription": "vosk-model-small-en-us-0.15"
            if (ROOT / "tools" / "models" / "vosk-model-small-en-us-0.15" / "am").exists()
            else "missing (transcription skipped)",
        },
    })


def _card(video: dict[str, Any]) -> dict[str, Any]:
    profile = Path(video["profile_dir"])
    progress = dict(video.get("progress") or {})
    if video.get("status") == "analyzing" and (profile / "progress.json").exists():
        try:
            progress = json.loads((profile / "progress.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    card: dict[str, Any] = {
        "id": video["id"],
        "original_name": video.get("original_name", ""),
        "label": video.get("label", video.get("original_name", "")),
        "status": video.get("status", "unknown"),
        "error": video.get("error"),
        "progress": progress,
        "created_at": video.get("created_at"),
        "artifacts": [p.name for p in sorted(profile.iterdir())
                      if p.is_file() and p.name != "progress.json"] if profile.exists() else [],
        "has_frames": [p.name for p in sorted((profile / "frames").iterdir())]
        if (profile / "frames").exists() else [],
    }
    metrics = profile / "metrics.json"
    if metrics.exists():
        card["metrics"] = _digest(metrics)
    return card


def _digest(metrics_path: Path) -> dict[str, Any]:
    try:
        m = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    spec = m.get("source_specs", {})
    editing = m.get("editing", {})
    motion = m.get("motion", {})
    visual = m.get("visual", {})
    audio = m.get("audio") or {}
    fmt = m.get("format", {})
    return {
        "duration_seconds": spec.get("duration_seconds"),
        "width": spec.get("width"),
        "height": spec.get("height"),
        "fps": spec.get("fps"),
        "orientation": fmt.get("orientation"),
        "three_band": (m.get("format") or {}).get("banner_staticness_0_1") is not None,
        "banner_staticness": fmt.get("banner_staticness_0_1"),
        "shot_count": editing.get("detected_shot_count"),
        "cut_count": editing.get("detected_edit_event_count"),
        "median_shot": (editing.get("shot_duration_seconds") or {}).get("median"),
        "mean_shot": (editing.get("shot_duration_seconds") or {}).get("mean"),
        "motion_pct": motion.get("shot_percentages", {}),
        "transition_counts": editing.get("transition_counts", {}),
        "cut_word_offset_median": (editing.get("cut_minus_word_start_seconds") or {}).get("median"),
        "cuts_before_word_pct": editing.get("cuts_before_word_start_pct"),
        "majority_white_pct": visual.get("frames_majority_white_pct"),
        "ink_centroid": [
            (visual.get("ink_centroid_x_normalized") or {}).get("median"),
            (visual.get("ink_centroid_y_normalized") or {}).get("median"),
        ],
        "stroke_1920_median": (visual.get("estimated_black_stroke_width_px_at_1920") or {}).get("median"),
        "palette": visual.get("dominant_quantized_palette", [])[:8],
        "wpm": audio.get("recognized_wpm_full_runtime"),
        "lufs": audio.get("integrated_lufs"),
        "true_peak": audio.get("true_peak_dbfs"),
        "lra": audio.get("lra_lu"),
        "tempo": audio.get("estimated_tempo_bpm"),
        "transcript_available": (m.get("transcript") or {}).get("available", False),
        "word_count": (m.get("transcript") or {}).get("word_count", 0),
        "chapters": m.get("chapters", []),
        "title_strip_detected": (
            (m.get("format") or {}).get("title_strip_top_band") or {}).get("white_fraction", 0) >= 0.5,
    }


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> JSONResponse:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for file in files:
        original = file.filename or "video"
        vid = uuid.uuid4().hex[:10]
        stamp = time.strftime("%Y%m%d-%H%M%S")
        ext = Path(original).suffix.lower()[:8]
        if not re.fullmatch(r"[A-Za-z0-9.]+", ext):
            ext = ".mp4"
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(original).stem)[:60] or "video"
        stored = UPLOADS / f"{stamp}-{vid}-{safe_stem}{ext}"
        size = 0
        with stored.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    out.close()
                    stored.unlink(missing_ok=True)
                    rejected.append({"name": original, "reason": "file larger than 2 GB"})
                    break
                out.write(chunk)
        if size == 0 or size > MAX_UPLOAD_BYTES:
            if stored.exists() and size == 0:
                stored.unlink(missing_ok=True)
                rejected.append({"name": original, "reason": "empty file"})
            continue
        probe, probe_reason = _probe(stored)
        if probe is None:
            stored.unlink(missing_ok=True)
            rejected.append({"name": original, "reason": probe_reason or "not a readable video file"})
            continue
        profile = PROFILES / vid
        profile.mkdir(parents=True, exist_ok=True)
        with _state_lock:
            _videos[vid] = {
                "id": vid,
                "original_name": original,
                "label": Path(original).stem[:80],
                "source_path": str(stored),
                "profile_dir": str(profile),
                "status": "queued",
                "progress": {"stage": "queued", "pct": 0, "message": "Waiting for analysis"},
                "created_at": time.time(),
                "probe": probe,
            }
            _persist_unlocked()
        _jobs.put({"kind": "analyze", "id": vid, "label": Path(original).stem[:80]})
        accepted.append({"id": vid, "name": original})
    _ensure_worker()
    return JSONResponse({"accepted": accepted, "rejected": rejected})


def _probe(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Probe a file with the imageio ffmpeg binary (no ffprobe is shipped).

    Tolerant of the many stream-line shapes real files produce: pixel-format
    fields can contain commas (``yuv420p(tv, bt709)``), some containers list
    only ``tbr``/``tbn`` with no ``fps``, and some put an attached cover
    stream before the actual video. Returns (probe_dict, None) on success or
    (None, human_reason) on failure.
    """
    proc = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path)],
        text=True, capture_output=True,
    )
    # `ffmpeg -i file` always exits 1 (no output file given); parse stderr.
    stderr = proc.stderr
    if "Stream #" not in stderr:
        if re.search(r"moov atom not found|Premature end of file|End of file", stderr):
            return None, ("file looks truncated or incomplete — the upload may not have "
                          "finished; retry the upload")
        tail = " ".join(line.strip() for line in stderr.strip().splitlines()[-2:] if line.strip())
        if "Invalid data" in stderr or not tail:
            return None, "not a readable media file — is this actually a video?"
        return None, f"not a readable media file ({tail[:160]})"

    duration: float | None = None
    match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", stderr)
    if match:
        duration = (int(match.group(1)) * 3600 + int(match.group(2)) * 60
                    + float(match.group(3)))

    streams: list[dict[str, Any]] = []
    for line in stderr.splitlines():
        sm = re.match(r"\s*Stream #\d+:(\d+)[^\n]*: Video:\s*([A-Za-z0-9]+)", line)
        if not sm:
            continue
        codec = sm.group(2).lower()
        res = re.search(r"(\d{2,5})x(\d{2,5})", line)
        if not res:
            continue
        fps = None
        fm = re.search(r"([\d.]+)\s*(?:fps|tbr|tbn)", line)
        if fm:
            fps = round(float(fm.group(1)), 4)
        priority = (VIDEO_CODEC_PRIORITY.index(codec)
                    if codec in VIDEO_CODEC_PRIORITY else 99)
        if "attached pic" in line:
            priority += 100
        streams.append({
            "index": int(sm.group(1)),
            "codec": codec,
            "width": int(res.group(1)),
            "height": int(res.group(2)),
            "fps": fps,
            "priority": priority,
        })
    if not streams:
        return None, "no video stream found — is this an audio or image file?"

    if re.search(r"Input #\d+,\s*(?:image2|image2pipe|jpeg_pipe|png_pipe|webp_pipe|bmp_pipe|tiff_pipe)\b",
                 stderr):
        return None, "that is an image or a sub-second clip, not a video"

    best = min(streams, key=lambda s: (-s["width"] * s["height"], s["priority"]))
    same_size = [s for s in streams
                 if s["width"] == best["width"] and s["height"] == best["height"] and s["fps"]]
    if same_size:
        best = min(same_size, key=lambda s: s["priority"])
    if duration is not None and duration < MIN_DURATION_SECONDS:
        return None, "that is an image or a sub-second clip, not a video"

    return {
        "duration_seconds": round(duration, 2) if duration is not None else None,
        "width": best["width"],
        "height": best["height"],
        "fps": best["fps"] or 30.0,
        "fps_estimated": best["fps"] is None,
        "codec": best["codec"],
        "has_audio": bool(re.search(r"Stream #\S+: Audio:", stderr)),
        "stream_index": best["index"],
        "first_video_index": streams[0]["index"],
    }, None


@app.post("/api/combine")
async def combine_now() -> JSONResponse:
    done = [v for v in _videos.values() if v.get("status") == "done"]
    if len(done) < 2:
        raise HTTPException(400, "need at least two analyzed videos to merge")
    _jobs.put({"kind": "combine", "id": ""})
    _ensure_worker()
    return JSONResponse({"queued": True})


@app.post("/api/videos/{vid}/promote")
async def promote(vid: str) -> JSONResponse:
    with _state_lock:
        video = _videos.get(vid)
        if not video or video.get("status") != "done":
            raise HTTPException(404, "video not found or not analyzed")
        profile = Path(video["profile_dir"])
        rules = profile / "style_rules.json"
        if not rules.exists():
            raise HTTPException(404, "style_rules.json missing")
        CURRENT.parent.mkdir(parents=True, exist_ok=True)
        CURRENT.write_text(json.dumps({
            "adopted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_video": video["label"],
            "video_id": vid,
            "profile_dir": str(profile),
            "style_rules": str(rules),
            "note": "skills/style-analyzer + skills/content-router treat this as the "
                    "authoritative style profile for the next build; "
                    "references/paint-explainer-analysis-4v/style_rules.json remains the "
                    "built-in default when no upload profile is promoted.",
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _persist_unlocked()
    return JSONResponse({"ok": True, "current": _current_info()})


@app.post("/api/promote-combined")
async def promote_combined() -> JSONResponse:
    rules = COMBINED / "style_rules.json"
    if not rules.exists():
        raise HTTPException(404, "no merged style bible yet — analyze at least two videos first")
    CURRENT.parent.mkdir(parents=True, exist_ok=True)
    CURRENT.write_text(json.dumps({
        "adopted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_video": "merged profile (all analyzed references)",
        "video_id": "combined",
        "profile_dir": str(COMBINED),
        "style_rules": str(rules),
        "note": "skills/style-analyzer + skills/content-router treat this as the "
                "authoritative style profile for the next build.",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _persist()
    return JSONResponse({"ok": True, "current": _current_info()})


@app.get("/api/combined/file/{name}")
async def combined_file(name: str) -> Response:
    if name not in {"style_rules.json", "combined.json", "progress.json"}:
        raise HTTPException(404, "unknown artifact")
    path = COMBINED / name
    if not path.exists():
        raise HTTPException(404, "artifact not found")
    return Response(path.read_text(encoding="utf-8"),
                    media_type="application/json; charset=utf-8")


@app.get("/api/videos/{vid}/shots")
async def shots(vid: str) -> JSONResponse:
    profile = _profile_or_404(vid)
    rows: list[dict[str, Any]] = []
    shots_csv = profile / "shots.csv"
    if shots_csv.exists():
        with shots_csv.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append({
                    "shot": int(row["shot"]),
                    "start": row["start_timecode"],
                    "duration": float(row["duration_seconds"]),
                    "motion": row["motion_class"],
                })
    return JSONResponse({"shots": rows})


@app.get("/api/videos/{vid}/file/{name}")
async def artifact(vid: str, name: str) -> Response:
    allowed = {
        "metrics.json", "style_rules.json", "style_profile.md", "shots.csv",
        "cuts.csv", "transcript.json", "analysis_manifest.json",
    }
    if name not in allowed:
        raise HTTPException(404, "unknown artifact")
    profile = _profile_or_404(vid)
    path = profile / name
    if not path.exists():
        raise HTTPException(404, "artifact not found")
    media = "application/json" if name.endswith(".json") else (
        "text/markdown" if name.endswith(".md") else "text/csv")
    return Response(path.read_text(encoding="utf-8"), media_type=media + "; charset=utf-8")


@app.get("/api/videos/{vid}/frames/{name}")
async def frame_file(vid: str, name: str) -> FileResponse:
    profile = _profile_or_404(vid)
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.(jpg|png|jpeg)", name):
        raise HTTPException(404, "unknown frame")
    path = profile / "frames" / name
    if not path.exists():
        raise HTTPException(404, "frame not found")
    return FileResponse(path)


@app.get("/api/videos/{vid}/source")
async def source(vid: str, request: Request) -> Response:
    with _state_lock:
        video = _videos.get(vid)
        if not video:
            raise HTTPException(404, "video not found")
        path = Path(video["source_path"])
    if not path.exists():
        raise HTTPException(404, "source file missing")
    media = mimetypes.guess_type(path.name)[0] or "video/mp4"
    size = path.stat().st_size
    range_header = request.headers.get("range")
    if range_header:
        match = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if match:
            start = int(match.group(1)) if match.group(1) else 0
            end = int(match.group(2)) if match.group(2) else size - 1
            end = min(end, size - 1)
            start = max(0, min(start, end))

            def stream():
                with path.open("rb") as handle:
                    handle.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        block = handle.read(min(1024 * 1024, remaining))
                        if not block:
                            break
                        remaining -= len(block)
                        yield block

            return StreamingResponse(
                stream(), status_code=206, media_type=media,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(end - start + 1),
                })
    return FileResponse(path, media_type=media)


@app.delete("/api/videos/{vid}")
async def delete(vid: str) -> JSONResponse:
    with _state_lock:
        video = _videos.pop(vid, None)
        if video is None:
            raise HTTPException(404, "video not found")
        _persist_unlocked()
    shutil.rmtree(Path(video["profile_dir"]), ignore_errors=True)
    source = Path(video["source_path"])
    if source.exists() and UPLOADS in source.parents:
        source.unlink(missing_ok=True)
    if _current_info() and _current_info().get("video_id") == vid:
        CURRENT.unlink(missing_ok=True)
    return JSONResponse({"ok": True})


@app.get("/api/health")
async def health() -> PlainTextResponse:
    return PlainTextResponse("ok")


def _profile_or_404(vid: str) -> Path:
    with _state_lock:
        video = _videos.get(vid)
    if not video:
        raise HTTPException(404, "video not found")
    return Path(video["profile_dir"])


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    for directory in (STYLEHUB, UPLOADS, PROFILES, COMBINED):
        directory.mkdir(parents=True, exist_ok=True)
    _load()
    _ensure_worker()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
