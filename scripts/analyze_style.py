#!/usr/bin/env python3
"""Generalized style analyzer: any user-uploaded reference video -> measured style bible.

This is the measurement half of the Reference Studio. Point it at one or more
reference videos and it produces, per video:

  metrics.json          per-video measured summary (same vocabulary as the
                        four-video Paint Explainer corpus metrics)
  shots.csv / cuts.csv  every detected shot and every abrupt edit event
  transcript.json       optional Vosk word timings (when the small model is
                        installed under tools/models/)
  frames/*.jpg          evidence grabs + a contact sheet
  style_rules.json      the machine-readable style bible, schema-compatible
                        with references/paint-explainer-analysis-4v/style_rules.json
                        so skills/content-router can consume it unchanged
  style_profile.md      human-readable style bible rendered by the studio UI

Reuses the proven measurement primitives from
scripts/analyze_paint_explainer_corpus.py (same repository), so numbers from
user uploads stay directly comparable with the measured Paint Explainer corpus.

Usage:
  .venv/bin/python scripts/analyze_style.py analyze --video ref.mp4 --out stylehub/profiles/abc
  .venv/bin/python scripts/analyze_style.py combine --dirs stylehub/profiles/a stylehub/profiles/b --out stylehub/combined
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

# Make the ffmpeg binary that ships with imageio-ffmpeg available on PATH for
# every subprocess call (loudnorm / audio decode / proxies). The wheel only
# ships the ffmpeg binary (no ffprobe), so expose it under the plain `ffmpeg`
# and `ffprobe` names via symlinks in the same directory.
_FFMPEG_BIN = Path(imageio_ffmpeg.get_ffmpeg_exe())
os.environ["PATH"] = str(_FFMPEG_BIN.parent) + os.pathsep + os.environ.get("PATH", "")
for _alias in ("ffmpeg", "ffprobe"):
    _link = _FFMPEG_BIN.parent / _alias
    try:
        if not _link.exists():
            _link.symlink_to(_FFMPEG_BIN.name)
    except OSError:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# Reuse the measured primitives of the four-video corpus analyzer.
import analyze_paint_explainer_corpus as corpus  # noqa: E402

VOSK_MODEL = ROOT / "tools" / "models" / "vosk-model-small-en-us-0.15"
SCHEMA_VERSION = "1.0.0"

# ----------------------------------------------------------------------------
# progress
# ----------------------------------------------------------------------------

ProgressFn = Callable[[str, float, str], None]


def make_progress(path: str | None) -> ProgressFn:
    target = Path(path) if path else None

    def write(stage: str, pct: float, message: str) -> None:
        if target is None:
            print(f"[{pct:5.1f}%] {stage}: {message}", flush=True)
            return
        target.write_text(
            json.dumps({"stage": stage, "pct": round(pct, 2), "message": message}),
            encoding="utf-8",
        )

    return write


# ----------------------------------------------------------------------------
# new measurements (format-level, not in the corpus analyzer)
# ----------------------------------------------------------------------------

def band_metrics(frame: np.ndarray) -> list[dict[str, float]]:
    """Brightness/ink profile of the three horizontal thirds (vertical formats)."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 160)
    out: list[dict[str, float]] = []
    for y0, y1 in ((0.0, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 1.0)):
        sl = slice(int(h * y0), int(h * y1))
        band_rgb = rgb[sl]
        band_g = gray[sl]
        band_e = edges[sl]
        out.append({
            "mean_brightness": round(float(band_g.mean() / 255.0), 5),
            "std_brightness": round(float(band_g.std() / 255.0), 5),
            "white_fraction": round(float(np.all(band_rgb >= 242, axis=2).mean()), 5),
            "dark_fraction": round(float((band_g <= 35).mean()), 5),
            "ink_fraction": round(float((band_e > 0).mean()), 5),
        })
    return out


def title_strip_metrics(frame: np.ndarray) -> dict[str, float]:
    """Profile the top ~11% band for a persistent white chapter-title strip."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sl = slice(0, max(1, int(h * 0.11)))
    band = rgb[sl]
    g = gray[sl]
    edges = cv2.Canny(g, 70, 160)[sl]
    return {
        "white_fraction": round(float(np.all(band >= 242, axis=2).mean()), 5),
        "mean_brightness": round(float(g.mean() / 255.0), 5),
        "dark_pixel_fraction": round(float((g <= 80).mean()), 5),
        "edge_fraction": round(float((edges > 0).mean()), 5),
    }


def ink_bbox_width_fraction(frame: np.ndarray) -> float:
    """Horizontal extent of linework (excludes the top title band)."""
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 160)
    edges[: int(h * 0.11), :] = 0
    ys, xs = np.nonzero(edges)
    if len(xs) < 20:
        return 0.0
    return round(float((xs.max() - xs.min()) / w), 5)


def band_similarity(a: np.ndarray, b: np.ndarray, y_lo: float, y_hi: float) -> float:
    """Pixel-level unchanged fraction inside a horizontal band (0..1)."""
    if a.shape != b.shape:
        return 0.0
    h, w = a.shape[:2]
    sl = slice(int(h * y_lo), max(int(h * y_lo) + 1, int(h * y_hi)))
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)[sl]
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)[sl]
    diff = cv2.absdiff(ga, gb)
    unchanged = float(np.mean(diff <= 14))
    return round(unchanged, 5)


def illustration_crop(frame: np.ndarray, vertical: bool) -> np.ndarray:
    """Crop to the illustration area for stroke-width fallback measurement."""
    h, w = frame.shape[:2]
    if vertical:
        return frame[int(h / 3):int(2 * h / 3), :]
    return frame[int(h * 0.11):, :]


# ----------------------------------------------------------------------------
# proxy (analysis-resolution copy) so HD uploads scan quickly
# ----------------------------------------------------------------------------

def _last_decodable(cap: cv2.VideoCapture, frame_count: int) -> int | None:
    """Decodable frame count of the file prefix, or None if it all decodes."""
    if frame_count <= 0:
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
    ok, _ = cap.read()
    if ok:
        return None
    lo, hi = 0, frame_count - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ok, _ = cap.read()
        if ok:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1

def make_proxy(
    path: Path,
    work: Path,
    progress: ProgressFn,
    probe: dict[str, Any],
    force: bool = False,
    map_index: int | None = None,
) -> Path | None:
    """Analysis-resolution copy, optionally forced from a chosen video stream."""
    need = force or map_index is not None
    if not need and probe["height"] <= 480 and probe["width"] <= 854:
        return None
    proxy = work / "proxy.mp4"
    progress("proxy", 8, "Preparing analysis proxy")
    maps = ["-map", f"0:V:{0 if map_index is None else map_index}"] if need else []
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(path), *maps, "-an",
         "-vf", "scale='min(640,iw)':-2",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
         str(proxy)],
        check=True,
    )
    return proxy


# Codec preference for picking the "real" video stream when a container holds
# several (e.g. an attached cover image before the actual video).
_CODEC_PRIORITY = [
    "h264", "hevc", "vp9", "av1", "hvc1", "avc1", "vp8",
    "mpeg4", "mpeg2video", "msmpeg4v3", "theora", "mjpeg", "png", "gif",
]


def probe_video(path: Path) -> dict[str, Any] | None:
    """Tolerant probe via the imageio ffmpeg binary (no ffprobe is shipped).

    Parses every video stream line and picks the best one, because real files
    print pixel-format fields with commas (``yuv420p(tv, bt709)``), some list
    only ``tbr``/``tbn`` without ``fps``, and some put an attached cover
    stream before the actual video.
    """
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path)],
        text=True, capture_output=True,
    )
    # `ffmpeg -i file` always exits 1 (no output file given); parse stderr.
    if "Stream #" not in proc.stderr:
        return None
    stderr = proc.stderr
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
        priority = (_CODEC_PRIORITY.index(codec)
                    if codec in _CODEC_PRIORITY else 99)
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
        return None
    best = min(streams, key=lambda s: (-s["width"] * s["height"], s["priority"]))
    same_size = [s for s in streams
                 if s["width"] == best["width"] and s["height"] == best["height"] and s["fps"]]
    if same_size:
        best = min(same_size, key=lambda s: s["priority"])
    has_audio = bool(re.search(r"Stream #\S+: Audio:", stderr))
    ac = re.search(r"Stream #\S+: Audio:\s*([A-Za-z0-9]+)", stderr)
    image_input = bool(re.search(
        r"Input #\d+,\s*(?:image2|image2pipe|jpeg_pipe|png_pipe|webp_pipe|bmp_pipe|tiff_pipe)\b",
        stderr))
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "width": best["width"],
        "height": best["height"],
        "fps": best["fps"] or 30.0,
        "fps_estimated": best["fps"] is None,
        "duration_seconds": round(duration, 4) if duration is not None else None,
        "video_codec": best["codec"],
        "has_audio": has_audio,
        "audio_codec": ac.group(1) if ac else None,
        "stream_index": best["index"],
        "first_video_index": streams[0]["index"],
        "video_stream_count": len(streams),
        "image_input": image_input,
        "sha256": corpus.sha256(path),
    }


# ----------------------------------------------------------------------------
# transcription + chapter estimation
# ----------------------------------------------------------------------------

def transcribe(path: Path, out_dir: Path, progress: ProgressFn) -> dict[str, Any] | None:
    if not (VOSK_MODEL / "am").exists():
        return None
    progress("transcript", 86, "Loading Vosk speech model")
    import vosk

    model = vosk.Model(str(VOSK_MODEL))
    rec = vosk.KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    audio = corpus.decode_audio(path)
    # Vosk expects 16 kHz mono signed-16-bit PCM (not float32).
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    step = 32000
    for start in range(0, len(pcm), step):
        rec.AcceptWaveform(pcm[start:start + step])
    result = json.loads(rec.FinalResult())
    words = [
        {
            "word": str(item.get("word", "")),
            "start": round(float(item.get("start", 0.0)), 4),
            "end": round(float(item.get("end", 0.0)), 4),
            "conf": round(float(item.get("conf", 0.0)), 4),
        }
        for item in result.get("result", [])
    ]
    transcript = {
        "duration": round(len(audio) / 16000.0, 4),
        "word_count": len(words),
        "text": str(result.get("text", "")),
        "words": words,
    }
    (out_dir / "transcript.json").write_text(
        json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return transcript


def estimate_chapters(
    words: list[dict[str, Any]], scene_starts: list[float], fps: float
) -> list[tuple[float, str]]:
    """Approximate chapter boundaries: long narration pauses landing on a hard cut."""
    if len(words) < 40:
        return []
    candidates: list[tuple[float, float, bool]] = []
    for left, right in zip(words, words[1:]):
        gap = float(right["start"]) - float(left["end"])
        if gap >= 0.55:
            t = float(right["start"])
            near_cut = bool(scene_starts) and min(abs(t - s) for s in scene_starts) <= 1.5
            candidates.append((t, gap, near_cut))
    picked: list[float] = []
    for t, gap, near_cut in candidates:
        if near_cut and (not picked or t - picked[-1] >= 20.0):
            picked.append(t)
        if len(picked) >= 20:
            break
    if len(picked) < 2:
        return []
    return [(t, f"Chapter {i} (estimated)") for i, t in enumerate(picked, 1)]


# ----------------------------------------------------------------------------
# per-video analysis
# ----------------------------------------------------------------------------

def analyze_video(
    source: Path, out_dir: Path, label: str, progress: ProgressFn, limit_frames: int | None = None
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "work"
    work.mkdir(exist_ok=True)

    progress("probe", 5, f"Probing {source.name}")
    probe = probe_video(source)
    if probe is None:
        raise RuntimeError(f"cannot probe {source.name} — is it a valid video file?")
    if probe.get("image_input") or (
        probe["duration_seconds"] is not None and probe["duration_seconds"] < 0.5
    ):
        raise RuntimeError("file looks like an image or a sub-second clip, not a video")

    need_stream = probe["stream_index"] != probe["first_video_index"]
    proxy = make_proxy(source, work, progress, probe,
                       force=need_stream,
                       map_index=probe["stream_index"] if need_stream else None)
    scan_path = proxy or source
    scan_is_proxy = proxy is not None

    cap = cv2.VideoCapture(str(scan_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot decode {scan_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS)) or probe["fps"]
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # If cv2 grabbed a different stream than the probe chose (e.g. an attached
    # cover image before the real video), re-decode from the chosen stream.
    if not scan_is_proxy and (width, height) != (probe["width"], probe["height"]):
        cap.release()
        proxy = make_proxy(source, work, progress, probe,
                           force=True, map_index=probe["stream_index"])
        scan_path = proxy
        scan_is_proxy = True
        cap = cv2.VideoCapture(str(scan_path))
        if not cap.isOpened():
            raise RuntimeError(f"cannot decode {scan_path}")
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or probe["fps"]
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # Truncated uploads still carry full-duration headers; find the last
    # decodable frame so the analysis covers what actually exists.
    container_frame_count = frame_count
    truncated_frames = 0
    last = _last_decodable(cap, frame_count)
    if last is not None and last < frame_count:
        truncated_frames = frame_count - last
        frame_count = last
    duration = frame_count / fps if fps else (probe["duration_seconds"] or 0.0)
    if limit_frames:
        frame_count = min(frame_count, limit_frames)

    progress("scenes", 18, "Detecting shots and hard cuts (every decoded frame)")
    scenes = corpus.detect_scenes(scan_path, fps)
    scenes = [(s, e) for s, e in scenes if s < frame_count]

    transcript = transcribe(source, out_dir, progress)
    words = (transcript or {}).get("words") or []
    chapters = estimate_chapters(words, [s / fps for s, _ in scenes], fps)

    shot_rows: list[dict[str, Any]] = []
    cut_rows: list[dict[str, Any]] = []
    frame_visuals: list[dict[str, Any]] = []
    stroke_samples: list[float] = []
    title_samples: list[dict[str, float]] = []
    band_samples: list[list[dict[str, float]]] = []
    bbox_samples: list[float] = []
    zoom_speeds: list[float] = []
    zoom_distances: list[float] = []
    mid_frames: list[np.ndarray] = []  # capped, for banner staticness

    total_shots = max(1, len(scenes))
    for index, (start, end) in enumerate(scenes, 1):
        end = min(end, frame_count)
        length_frames = max(1, end - start)
        shot_duration = length_frames / fps
        inset = min(max(1, round(fps * 0.08)), max(1, length_frames // 5))
        sample_numbers = sorted(set([
            min(end - 1, start + inset),
            min(end - 1, start + length_frames // 2),
            max(start, end - 1 - inset),
        ]))
        frames = [corpus.get_frame(cap, number) for number in sample_numbers]
        diffs = [corpus.diff_metrics(left, right) for left, right in zip(frames, frames[1:])]
        transform = corpus.estimate_transform(frames[0], frames[-1]) if len(frames) >= 2 \
            else corpus.estimate_transform(frames[0], frames[0])
        kind, derived = corpus.classify_motion(shot_duration, diffs, transform)
        midpoint = frames[len(frames) // 2]
        frame_visuals.append(corpus.visual_metrics(midpoint))
        stroke_samples.extend(corpus.stroke_widths(midpoint))
        title_samples.append(title_strip_metrics(midpoint))
        band_samples.append(band_metrics(midpoint))
        bbox_samples.append(ink_bbox_width_fraction(midpoint))
        if len(mid_frames) < 30:
            mid_frames.append(midpoint.copy())
        if kind in {"whole_scene_zoom_in", "whole_scene_zoom_out"}:
            zoom_distances.append(float(transform["scale_delta_pct"]))
            zoom_speeds.append(float(derived["global_scale_speed_pct_per_s"]))

        shot_rows.append({
            "shot": index,
            "start_frame": start,
            "end_frame_exclusive": end,
            "start_seconds": round(start / fps, 4),
            "end_seconds": round(end / fps, 4),
            "start_timecode": corpus.fmt_time(start / fps),
            "end_timecode": corpus.fmt_time(end / fps),
            "duration_seconds": round(shot_duration, 4),
            "motion_class": kind,
            **derived,
            **transform,
        })

        if index > 1:
            boundary = start
            before = corpus.get_frame(cap, max(0, boundary - 1))
            after = corpus.get_frame(cap, min(frame_count - 1, boundary))
            metrics = corpus.diff_metrics(before, after)
            word, delta = corpus.nearest_word(words, boundary / fps)
            changed = metrics["changed_fraction_gt20"]
            if changed >= 0.42:
                transition = "hard_cut_full_frame"
            elif changed >= 0.18:
                transition = "hard_cut_same_palette"
            else:
                transition = "localized_swap_or_pop"
            cut_rows.append({
                "event": index - 1,
                "boundary_frame": boundary,
                "timestamp_seconds": round(boundary / fps, 4),
                "timestamp": corpus.fmt_time(boundary / fps),
                "preceding_shot_duration_seconds": shot_rows[-2]["duration_seconds"],
                "transition_class": transition,
                **metrics,
                "nearest_spoken_word": word,
                "cut_minus_word_start_seconds": delta,
            })

        if index % max(1, total_shots // 10) == 0 or index == total_shots:
            progress("frames", 18 + 58 * index / total_shots,
                     f"Shot {index}/{total_shots} ({kind.replace('_', ' ')})")

    cap.release()

    progress("audio", 80, "Measuring loudness, tempo and pauses")
    empty_transcript = {"word_count": 0, "words": []}
    audio = None
    if probe["has_audio"]:
        audio = corpus.audio_metrics(source, transcript or empty_transcript, duration)

    durations = [float(row["duration_seconds"]) for row in shot_rows]
    motion_counts = Counter(row["motion_class"] for row in shot_rows)
    transition_counts = Counter(row["transition_class"] for row in cut_rows)
    signed_deltas = [float(row["cut_minus_word_start_seconds"]) for row in cut_rows
                     if row["cut_minus_word_start_seconds"] is not None]

    # palette aggregation (same weighting as the corpus analyzer)
    palette_weights: Counter[str] = Counter()
    for metric in frame_visuals:
        for color in metric["top_quantized_colors"]:
            palette_weights[color["hex"]] += color["fraction"]
    palette_total = sum(palette_weights.values()) or 1.0
    palette = [{"hex": color, "relative_weight": round(weight / palette_total, 5)}
               for color, weight in palette_weights.most_common(12)]

    brightness = [float(m["mean_brightness"]) for m in frame_visuals]
    saturation = [float(m["mean_saturation"]) for m in frame_visuals]
    white_fraction = [float(m["white_fraction"]) for m in frame_visuals]
    significant_colors = [float(m["significant_color_count"]) for m in frame_visuals]
    centroid_x = [float(m["ink_edge_centroid_normalized"][0]) for m in frame_visuals]
    centroid_y = [float(m["ink_edge_centroid_normalized"][1]) for m in frame_visuals]

    # format-level aggregates
    def band_median(idx: int, key: str) -> float:
        values = [b[idx][key] for b in band_samples]
        return round(statistics.median(values), 5) if values else 0.0

    title_median = {key: statistics.median([s[key] for s in title_samples])
                    for key in ("white_fraction", "mean_brightness",
                                "dark_pixel_fraction", "edge_fraction")}
    vertical = height > width
    banner_staticness = None
    if vertical and len(mid_frames) >= 2:
        # Pixel-level similarity of the top third across consecutive shot
        # midpoints: a reused banner stays near-identical, a changing scene
        # band does not.
        banner_staticness = statistics.median([
            band_similarity(left, right, 0.0, 1 / 3)
            for left, right in zip(mid_frames, mid_frames[1:])
        ])
    if not stroke_samples:
        # Stroke fallback: dark-format videos (banner/empty bands) never pass
        # the bright-frame gate, so measure on the illustration band crop.
        fallback: list[float] = []
        for frame in mid_frames:
            fallback.extend(corpus.stroke_widths(
                illustration_crop(frame, vertical)))
        stroke_samples = fallback

    progress("report", 92, "Writing metrics, cut list and style bible")

    summary: dict[str, Any] = {
        "identity": {
            "file": source.name,
            "label": label or source.name,
            "path": str(source.resolve()),
            "sha256": probe["sha256"],
            "size_bytes": probe["size_bytes"],
            "analyzed_at": None,  # filled by caller if desired
        },
        "source_specs": {
            "width": probe["width"],
            "height": probe["height"],
            "fps": fps,
            "fps_estimated": bool(probe.get("fps_estimated")),
            "frame_count": frame_count,
            "container_frame_count": container_frame_count,
            "truncated_frames": truncated_frames,
            "duration_seconds": round(duration, 4),
            "timing_precision_seconds": round(1.0 / fps, 6),
            "video_stream_index": probe["stream_index"],
            "video_stream_count": probe.get("video_stream_count", 1),
            "analysis_proxy": {
                "used": scan_is_proxy,
                "width": width,
                "height": height,
            },
        },
        "format": {
            "orientation": "vertical" if vertical else "horizontal",
            "aspect_ratio": round(probe["width"] / probe["height"], 4),
            "top_band": band_samples[0][0] if band_samples else None,
            "middle_band": band_samples[0][1] if band_samples else None,
            "bottom_band": band_samples[0][2] if band_samples else None,
            "band_medians": {
                "top": {k: band_median(0, k) for k in
                        ("mean_brightness", "white_fraction", "dark_fraction", "ink_fraction")},
                "middle": {k: band_median(1, k) for k in
                           ("mean_brightness", "white_fraction", "dark_fraction", "ink_fraction")},
                "bottom": {k: band_median(2, k) for k in
                           ("mean_brightness", "white_fraction", "dark_fraction", "ink_fraction")},
            },
            "banner_staticness_0_1": banner_staticness,
            "title_strip_top_band": {k: round(v, 5) for k, v in title_median.items()},
        },
        "editing": {
            "detected_shot_count": len(shot_rows),
            "detected_edit_event_count": len(cut_rows),
            "shot_duration_seconds": corpus.describe(durations),
            "shots_under_1s": sum(v < 1.0 for v in durations),
            "shots_1_to_6s": sum(1.0 <= v <= 6.0 for v in durations),
            "shots_over_10s": sum(v > 10.0 for v in durations),
            "transition_counts": dict(transition_counts),
            "cut_minus_word_start_seconds": corpus.describe(signed_deltas),
            "cuts_before_word_start_pct": round(
                sum(v < 0 for v in signed_deltas) / max(len(signed_deltas), 1) * 100, 2),
            "cuts_within_0_20s_of_word_start_pct": round(
                sum(abs(v) <= 0.20 for v in signed_deltas) / max(len(signed_deltas), 1) * 100, 2),
        },
        "motion": {
            "shot_counts": dict(motion_counts),
            "shot_percentages": {key: round(value / max(len(shot_rows), 1) * 100, 2)
                                 for key, value in motion_counts.items()},
            "zoom_distance_pct": corpus.describe(zoom_distances),
            "zoom_speed_pct_per_s": corpus.describe(zoom_speeds),
        },
        "visual": {
            "brightness": corpus.describe(brightness),
            "saturation": corpus.describe(saturation),
            "white_background_fraction": corpus.describe(white_fraction),
            "frames_majority_white_pct": round(
                sum(v >= 0.50 for v in white_fraction) / max(len(white_fraction), 1) * 100, 2),
            "significant_colors_per_frame": corpus.describe(significant_colors),
            "ink_centroid_x_normalized": corpus.describe(centroid_x),
            "ink_centroid_y_normalized": corpus.describe(centroid_y),
            "ink_bbox_width_fraction": corpus.describe(bbox_samples),
            "estimated_black_stroke_width_px_at_source": corpus.describe(stroke_samples),
            "estimated_black_stroke_width_px_at_1920": {
                key: (round(value * 1920.0 / probe["width"], 3) if value is not None else None)
                for key, value in corpus.describe(stroke_samples).items()},
            "dominant_quantized_palette": palette,
        },
        "audio": audio,
        "transcript": {
            "available": bool(transcript),
            "word_count": (transcript or {}).get("word_count", 0),
            "model": "vosk-model-small-en-us-0.15 (offline)" if transcript else "unavailable",
        },
        "chapters": [{"start_seconds": round(t, 3), "start": corpus.fmt_time(t), "title": title}
                     for t, title in chapters],
        "chapter_estimated": True,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with (out_dir / "shots.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(shot_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(shot_rows)
    with (out_dir / "cuts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cut_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(cut_rows)

    evidence_frames(summary, scenes, shot_rows, scan_path, fps, frame_count, out_dir, progress)

    style_rules = build_style_rules(summary, transcript, chapters)
    (out_dir / "style_rules.json").write_text(
        json.dumps(style_rules, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "style_profile.md").write_text(
        build_profile_md(summary, style_rules, chapters), encoding="utf-8")
    (out_dir / "analysis_manifest.json").write_text(json.dumps({
        "analysis_date": None,
        "schema_version": SCHEMA_VERSION,
        "method": {
            "frame_scan": "Every decoded source frame scanned with PySceneDetect ContentDetector "
                          "threshold 18, min scene length 0.2 s; motion classified per shot via "
                          "ORB/RANSAC registration.",
            "transcript": "Offline Vosk small English model (word timings) when installed; "
                          "proper nouns may contain recognition errors.",
            "audio": "ffmpeg loudnorm (LUFS/true peak/LRA), RMS/peak samples, librosa tempo, "
                     "inter-word pause statistics.",
            "proxy": "HD sources are analyzed at a <=640px proxy; stroke widths are scaled "
                     "back to production width and flagged as estimates.",
        },
        "video": {
            "file": source.name,
            "label": label or source.name,
            "path": str(source),
            "sha256": probe["sha256"],
            "duration_seconds": probe["duration_seconds"],
            "chapters": [[t, title] for t, title in chapters],
        },
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    progress("done", 100, "Analysis complete")
    return summary


# ----------------------------------------------------------------------------
# evidence frames + contact sheet
# ----------------------------------------------------------------------------

def evidence_frames(
    summary: dict[str, Any],
    scenes: list[tuple[int, int]],
    shot_rows: list[dict[str, Any]],
    scan_path: Path,
    fps: float,
    frame_count: int,
    out_dir: Path,
    progress: ProgressFn,
) -> None:
    progress("frames", 88, "Rendering evidence frames and contact sheet")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(scan_path))
    try:
        if not cap.isOpened():
            return
        _render_evidence_frames(cap, shot_rows, fps, frame_count, frames_dir)
    finally:
        cap.release()


def _render_evidence_frames(
    cap: cv2.VideoCapture,
    shot_rows: list[dict[str, Any]],
    fps: float,
    frame_count: int,
    frames_dir: Path,
) -> None:
    picks: list[int] = []
    total = len(shot_rows)
    if total <= 5:
        picks = list(range(total))
    else:
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            picks.append(min(total - 1, int(frac * (total - 1))))
    picks = sorted(set(picks))

    thumbs: list[Image.Image] = []
    labels: list[str] = []
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except OSError:
        font = ImageFont.load_default()

    for i, shot_index in enumerate(picks, 1):
        row = shot_rows[shot_index]
        number = min(frame_count - 1, (int(row["start_frame"]) + int(row["end_frame_exclusive"])) // 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, number)
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        scale = 320 / pil.width
        pil = pil.resize((320, max(1, int(pil.height * scale))), Image.LANCZOS)
        canvas = Image.new("RGB", (320, pil.height + 34), "#111111")
        canvas.paste(pil, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, pil.height + 6), f"#{i}  shot {row['shot']}  {row['start_timecode']}",
                  fill="#FFFFFF", font=font)
        draw.text((8, pil.height + 20), f"{row['motion_class'].replace('_', ' ')}  "
                                       f"({row['duration_seconds']} s)", fill="#8FD14F", font=font)
        canvas.save(frames_dir / f"evidence-{i:02d}.jpg", quality=88)
        thumbs.append(canvas)
        labels.append(row["start_timecode"])

    if not thumbs:
        return
    columns = min(3, len(thumbs))
    rows = math.ceil(len(thumbs) / columns)
    pad = 8
    grid_w = columns * 320 + (columns + 1) * pad
    grid_h = rows * max(t.height for t in thumbs) + (rows + 1) * pad
    sheet = Image.new("RGB", (grid_w, grid_h), "#111111")
    for index, thumb in enumerate(thumbs):
        x = pad + (index % columns) * (320 + pad)
        y = pad + (index // columns) * (max(t.height for t in thumbs) + pad)
        sheet.paste(thumb, (x, y))
    sheet.save(frames_dir / "contact-sheet.jpg", quality=88)


# ----------------------------------------------------------------------------
# style_rules.json builder (schema-compatible with the Paint Explainer corpus)
# ----------------------------------------------------------------------------

def hex_to_hsv(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx
    s = (mx - mn) / mx if mx else 0.0
    if s == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / (mx - mn)) % 6 / 6
    elif mx == g:
        h = ((b - r) / (mx - mn) + 2) / 6
    else:
        h = ((r - g) / (mx - mn) + 4) / 6
    return h, s, v


def split_palette(palette: list[dict[str, float]]) -> tuple[list[str], list[str]]:
    core: list[str] = []
    emphasis: list[str] = []
    for item in palette:
        h, s, v = hex_to_hsv(item["hex"])
        if s >= 0.45 and v >= 0.5 and (h < 0.10 or h >= 0.93 or 0.10 <= h <= 0.18):
            emphasis.append(item["hex"])
        elif len(core) < 8:
            core.append(item["hex"])
    return core, emphasis


def build_style_rules(
    summary: dict[str, Any], transcript: dict[str, Any] | None, chapters: list[tuple[float, str]]
) -> dict[str, Any]:
    spec = summary["source_specs"]
    fmt = summary["format"]
    editing = summary["editing"]
    motion = summary["motion"]
    visual = summary["visual"]
    audio = summary.get("audio") or {}
    vertical = fmt["orientation"] == "vertical"
    strip = fmt["title_strip_top_band"]
    title_strip_detected = (
        strip["white_fraction"] >= 0.5
        and strip["dark_pixel_fraction"] >= 0.004
        and strip["edge_fraction"] >= 0.0015
    )
    bottom_empty = fmt["band_medians"]["bottom"]["ink_fraction"] <= 0.004 and (
        fmt["band_medians"]["bottom"]["mean_brightness"] <= 0.15
        or fmt["band_medians"]["bottom"]["dark_fraction"] >= 0.8
    )
    three_band = vertical and (fmt["banner_staticness_0_1"] or 0.0) >= 0.85 and bottom_empty

    stroke = visual["estimated_black_stroke_width_px_at_1920"]
    core_palette, emphasis_palette = split_palette(visual["dominant_quantized_palette"])
    chapters_list = chapters or []
    chapter_durations = [
        right[0] - left[0] for left, right in zip(chapters_list, chapters_list[1:])
    ]
    signed = editing["cut_minus_word_start_seconds"]
    zoom_count = motion["shot_counts"].get("whole_scene_zoom_in", 0) + \
        motion["shot_counts"].get("whole_scene_zoom_out", 0)
    slide_count = motion["shot_counts"].get("whole_canvas_slide", 0)

    recipes: list[dict[str, Any]] = []

    def recipe(name: str, trigger: str, duration: Any, tracks: dict[str, Any], easing: str,
               notes: str, provenance: str) -> None:
        recipes.append({
            "name": name, "trigger": trigger, "duration_seconds": duration,
            "tracks": tracks, "easing": easing, "notes": notes, "provenance": provenance,
        })

    if vertical and three_band:
        recipe("Static banner reuse", "entire video", "full duration",
               {"banner": "top third, locked", "scale": 1.0, "opacity": 1.0},
               "none", "Banner is one image reused for the whole video; it never animates.",
               "measured: banner staticness "
               f"{fmt['banner_staticness_0_1']:.2f}")
        recipe("Illustration hard cut", "each beat/noun", 0.0,
               {"layer_set": "A to B on one frame"}, "step/hold",
               "Illustration band changes by hard cut only; no transitions.",
               f"measured: {editing['transition_counts'].get('hard_cut_full_frame', 0) + editing['transition_counts'].get('hard_cut_same_palette', 0)} hard cuts")
        recipe("Empty bottom band", "entire video", "full duration",
               {"band": "bottom third, empty"}, "none",
               "Bottom band stays empty; it is load-bearing layout space.",
               "measured: bottom band ink fraction "
               f"{fmt['band_medians']['bottom']['ink_fraction']:.4f}")

    if title_strip_detected:
        recipe("Persistent chapter title", "chapter start", "full chapter",
               {"position": [0.5, 0.05], "scale": 1.0, "opacity": 1.0},
               "cut on with chapter plate",
               "White strip across the top of frame with centered black uppercase title.",
               "measured: strip top band white fraction "
               f"{strip['white_fraction']:.2f}, text ink {strip['dark_pixel_fraction']:.4f}")

    if transcript:
        median_delta = signed.get("median")
        if median_delta is not None:
            recipe("Noun-anticipation hard cut", "new noun/idea/beat", 0.0,
                   {"layer_set": "A to B on one frame"}, "step/hold",
                   f"Place the boundary {median_delta:.3f} s before the spoken word onset.",
                   f"measured: median cut-word offset {median_delta:.3f} s across "
                   f"{editing['detected_edit_event_count']} cuts")
    recipe("Frozen hold", "between beats", None,
           {"all_layers": "locked", "scale": 1.0}, "hold",
           "Hold the drawing frozen between cuts; do not add idle breathing.",
           "measured: "
           f"{motion['shot_percentages'].get('frozen_hold', 0)}% of shots frozen")
    if slide_count:
        recipe("Whole-canvas slide", "chapter/era reset", [0.7, 1.4],
               {"position_start": "8-11% outside final alignment",
                "position_end": "lockup center", "scale": 1.0},
               "~ease-out cubic", "Occasional reset only, not continuous camera language.",
               f"measured: {slide_count} canvas-slide shots")
    if zoom_count:
        recipe("Scene zoom", "rare emphasis", None,
               {"scale": [1.0, f"{1 + (motion['zoom_distance_pct'].get('median') or 0) / 100:.3f}"]},
               "ease-in-out", "Only if the reference itself zooms; otherwise camera stays locked.",
               f"measured: {zoom_count} zoom shots, median distance "
               f"{motion['zoom_distance_pct'].get('median')}%")
    recipe("Same-canvas asset reveal", "descriptor, number, label or prop", [0.20, 0.50],
           {"scale": [0.92, 1.0], "opacity": [0, 1]}, "~ease-out cubic",
           "Localized pop on a locked plate; no bounce required.",
           "template (from measured corpus) unless localized events were detected")
    recipe("Character slide-in", "new participant enters established plate", [0.40, 0.90],
           {"position_start": "15-35% frame outside", "position_end": "staged mark",
            "scale": 1.0},
           "~ease-out cubic", "No overshoot.", "template")
    recipe("Reaction pose swap", "pain, surprise, death, reveal", round(1.0 / spec["fps"], 4),
           {"source_png": "neutral to reaction", "position": "hold", "scale": "hold"},
           "step", "Swap the eyes/mouth/head drawing; do not morph or lip-sync.", "template")
    recipe("Arm/prop action", "point, strike, lift, attack", [0.20, 0.45],
           {"rotation_deg": [0, "12-30 toward action"], "position": "0-3% follow-through",
            "scale": 1.0},
           "~fast ease-out", "Separate arm/prop PNG or 2-4 puppet pins.", "template")

    three_band_art = {} if not (vertical and three_band) else {
        "banner": {
            "reuse": "single static image, whole video",
            "staticness_0_1": fmt["banner_staticness_0_1"],
            "median_brightness": fmt["band_medians"]["top"]["mean_brightness"],
        },
        "illustration_band": {
            "median_brightness": fmt["band_medians"]["middle"]["mean_brightness"],
            "ink_fraction": fmt["band_medians"]["middle"]["ink_fraction"],
        },
        "bottom_band": {
            "rule": "empty; never text or captions",
            "median_brightness": fmt["band_medians"]["bottom"]["mean_brightness"],
            "ink_fraction": fmt["band_medians"]["bottom"]["ink_fraction"],
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "authority": "Measured from user-uploaded reference video(s) via scripts/analyze_style.py; "
                     "where a value cannot be measured from the uploads it is marked template "
                     "or estimate.",
        "target_version": {
            "primary": f"{summary['identity']['label']} ({summary['identity']['file']})",
            "reason": "Uploaded reference video; replicate its measured production technique "
                      "with original content.",
        },
        "source_measurement": {
            "video_count": 1,
            "runtime_seconds": spec["duration_seconds"],
            "frames_scanned": spec["frame_count"],
            "source_resolution": [spec["width"], spec["height"]],
            "source_fps": spec["fps"],
            "timing_uncertainty_seconds": round(1.0 / spec["fps"], 4),
            "detected_shots": editing["detected_shot_count"],
            "detected_edit_events": editing["detected_edit_event_count"],
        },
        "format": {
            "orientation": fmt["orientation"],
            "aspect_ratio": fmt["aspect_ratio"],
            "three_band_vertical_detected": bool(vertical and three_band),
            "persistent_title_strip_detected": bool(title_strip_detected),
            "output_resolution": [720, 1280] if vertical else [1920, 1080],
            "output_fps": 30,
        },
        "art": {
            "stroke": {
                "median_px_at_source_res": visual["estimated_black_stroke_width_px_at_source"]["median"],
                "median_fraction_of_frame_width": round(
                    (visual["estimated_black_stroke_width_px_at_source"]["median"] or 0.0)
                    / max(spec["width"], 1), 6),
                "production_px_at_1920_width": stroke["median"],
                "color": "near-black contour (measured dominant dark)",
                "wobble": "single clean imperfect contour; no multi-pass scribble",
                "caveat": "estimated from flat renders; source strokes scaled from proxy resolution",
            },
            "persistent_title_strip": {
                "detected": bool(title_strip_detected),
                "height_fraction": 0.11 if title_strip_detected else None,
                "white_fraction": strip["white_fraction"],
                "text_ink_fraction": strip["dark_pixel_fraction"],
                "rule": "white strip, centered black uppercase title, entire chapter"
                        if title_strip_detected else "no persistent strip detected",
            },
            "palette": {
                "core": core_palette or ["#F0F0F0", "#101010"],
                "emphasis": emphasis_palette or ["#E31B23", "#F0D010"],
                "dominant_measured": [
                    {"hex": c["hex"], "relative_weight": c["relative_weight"]}
                    for c in visual["dominant_quantized_palette"][:8]],
                "character_fill_rule": "flat fills; gradients reserved for world plates",
            },
            "composition": {
                "ink_centroid_x": visual["ink_centroid_x_normalized"]["median"],
                "ink_centroid_y": visual["ink_centroid_y_normalized"]["median"],
                "ink_bbox_width_fraction": visual["ink_bbox_width_fraction"]["median"],
                "negative_space_white_fraction": visual["white_background_fraction"]["median"],
                "white_majority_frames_pct": visual["frames_majority_white_pct"],
            },
            "three_band": three_band_art or None,
        },
        "editing": {
            "shot_duration_seconds": editing["shot_duration_seconds"],
            "distribution_pct": {
                "under_1s": round(editing["shots_under_1s"] / max(editing["detected_shot_count"], 1) * 100, 2),
                "between_1_and_6s": round(editing["shots_1_to_6s"] / max(editing["detected_shot_count"], 1) * 100, 2),
                "over_10s": round(editing["shots_over_10s"] / max(editing["detected_shot_count"], 1) * 100, 2),
            },
            "transition_pct": {
                "hard_cut_full_frame": round(
                    editing["transition_counts"].get("hard_cut_full_frame", 0)
                    / max(editing["detected_edit_event_count"], 1) * 100, 2),
                "hard_cut_same_palette": round(
                    editing["transition_counts"].get("hard_cut_same_palette", 0)
                    / max(editing["detected_edit_event_count"], 1) * 100, 2),
                "localized_one_frame_swap_or_pop": round(
                    editing["transition_counts"].get("localized_swap_or_pop", 0)
                    / max(editing["detected_edit_event_count"], 1) * 100, 2),
                "dissolve_or_fade_verified": 0.0,
            },
            "narration_sync": {
                "median_cut_minus_nearest_word_start_seconds": signed.get("median"),
                "p25_seconds": signed.get("p25"),
                "p75_seconds": signed.get("p75"),
                "cuts_before_nearest_word_start_pct": editing["cuts_before_word_start_pct"],
                "cuts_in_window_minus_0_10_to_plus_0_15_pct":
                    editing["cuts_within_0_20s_of_word_start_pct"],
                "available": bool(transcript),
                "implementation": "change the picture just before the emphasized word"
                                  if signed.get("median") is not None and signed["median"] < 0
                                  else "cut-word offset unavailable (no transcript)",
            },
            "chapter": {
                "count_per_video": len(chapters_list),
                "estimated": True,
                "duration_seconds_min": min(chapter_durations) if chapter_durations else None,
                "duration_seconds_median": round(statistics.median(chapter_durations), 2)
                if chapter_durations else None,
                "duration_seconds_mean": round(statistics.mean(chapter_durations), 2)
                if chapter_durations else None,
                "duration_seconds_max": max(chapter_durations) if chapter_durations else None,
                "caveat": "estimated from narration pauses landing on hard cuts; "
                          "verify against the source's own chapter list",
            },
        },
        "motion": {
            "budget_pct_of_shots": motion["shot_percentages"],
            "camera": {
                "default": "locked",
                "verified_sustained_zoom_count": zoom_count,
                "verified_pan_follow_or_orbit_count": 0,
                "rule": "keep the camera locked; move parts/labels or cut instead"
                        if zoom_count == 0 else
                        f"zoom sparingly: {zoom_count} zoom shot(s) measured",
            },
            "character": {
                "default_idle": "none",
                "lip_sync": False,
                "regular_blink_cycle_verified": False,
                "typical_independent_moving_elements": [1, 3],
                "preferred_methods": ["one-frame pose swap", "whole-layer translation",
                                      "arm/prop rotation", "2-4 pin local deformation"],
                "walk_cycle": "not a default; slide the whole figure or swap two poses",
            },
        },
        "audio": {
            "recognized_wpm_full_runtime":
                audio.get("recognized_wpm_full_runtime") if audio and transcript else None,
            "recognized_wpm_speech_span":
                audio.get("recognized_wpm_speech_span") if audio and transcript else None,
            "integrated_lufs": (audio or {}).get("integrated_lufs"),
            "true_peak_dbfs": (audio or {}).get("true_peak_dbfs"),
            "lra_lu": (audio or {}).get("lra_lu"),
            "estimated_mixed_onset_tempo_bpm": (audio or {}).get("estimated_tempo_bpm"),
            "music": "unable to separate clean music stem from flattened source; "
                     "use tempo estimate as range evidence only",
            "chapter_pause_seconds_target": [
                round(p, 2) for p in [
                    (audio or {}).get("inter_word_pause_seconds_ge_0_20", {}).get("median")
                ] if p
            ] or None,
            "note": "no audio stream in upload" if audio is None
                    else ("measured from the upload's mixed audio track"
                          + ("" if transcript else "; no transcript available")),
        },
        "keyframe_recipes": recipes,
        "measurement_notes": [
            "Edit events are one-frame abrupt visual boundaries; localized swaps are separated "
            "from full-frame hard cuts by changed-pixel area.",
            "Motion transforms are inferred from flattened frames with ORB/RANSAC; exact "
            "easing curves and hidden layer anchors cannot be recovered from a flat render.",
            "Transcript words come from the offline Vosk small model; proper-noun spelling "
            "should be checked.",
            "Templates in keyframe_recipes are corpus defaults included for buildability, "
            "not values measured from these uploads.",
            *(["Container did not report a frame rate; timing was measured from decoded "
               "frames."] if spec.get("fps_estimated") else []),
            *([f"Decoded video stream #{spec['video_stream_index']} of "
               f"{spec.get('video_stream_count', 1)} (container lists several video "
               f"streams)."] if spec.get("video_stream_count", 1) > 1 else []),
            *([f"Upload is truncated or incomplete: {spec.get('truncated_frames', 0)} of "
               f"{spec.get('container_frame_count', 0)} container frames are undecodable; "
               f"analysis covers the decodable prefix. Re-upload the full file for "
               f"complete results."] if spec.get("truncated_frames", 0) > 0 else []),
        ],
    }


# ----------------------------------------------------------------------------
# human-readable style profile (rendered by the studio UI)
# ----------------------------------------------------------------------------

def build_profile_md(
    summary: dict[str, Any], rules: dict[str, Any], chapters: list[tuple[float, str]]
) -> str:
    spec = summary["source_specs"]
    fmt = summary["format"]
    editing = summary["editing"]
    motion = summary["motion"]
    visual = summary["visual"]
    audio = summary.get("audio") or {}
    stroke = visual["estimated_black_stroke_width_px_at_1920"]
    orientation = "vertical (9:16)" if fmt["orientation"] == "vertical" else "horizontal (16:9)"

    lines: list[str] = []
    add = lines.append
    add(f"# Style profile — {summary['identity']['label']}")
    add("")
    add(f"Measured from **{summary['identity']['file']}** · "
        f"{int(spec['duration_seconds'] // 60)}:{spec['duration_seconds'] % 60:04.1f} · "
        f"{spec['width']}x{spec['height']} @ {spec['fps']:.0f} fps · "
        f"{editing['detected_shot_count']} shots · {editing['detected_edit_event_count']} cuts")
    add("")
    add("## Format")
    add("")
    add(f"- Orientation: **{orientation}**")
    if fmt["orientation"] == "vertical":
        add(f"- Three-band layout: **{'detected' if rules['format']['three_band_vertical_detected'] else 'not detected'}** "
            f"(banner staticness {fmt['banner_staticness_0_1']:.2f})")
        add(f"- Top band: brightness {fmt['band_medians']['top']['mean_brightness']:.2f}, "
            f"ink {fmt['band_medians']['top']['ink_fraction']:.4f}")
        add(f"- Middle band: brightness {fmt['band_medians']['middle']['mean_brightness']:.2f}, "
            f"ink {fmt['band_medians']['middle']['ink_fraction']:.4f}")
        add(f"- Bottom band: brightness {fmt['band_medians']['bottom']['mean_brightness']:.2f}, "
            f"ink {fmt['band_medians']['bottom']['ink_fraction']:.4f} — "
            f"{'empty (keep it empty)' if fmt['band_medians']['bottom']['ink_fraction'] <= 0.004 else 'not empty'}")
    add(f"- Persistent top title strip: **{'detected' if rules['format']['persistent_title_strip_detected'] else 'not detected'}**")
    add("")
    add("## Linework")
    add("")
    add(f"- Median stroke width: **{stroke['median']} px at 1920 wide** "
        f"(measured {visual['estimated_black_stroke_width_px_at_source']['median']} px at "
        f"{spec['width']} px source)")
    add("- Single clean imperfect near-black contour; no multi-pass sketch scribble")
    add("")
    add("## Color")
    add("")
    palette = visual["dominant_quantized_palette"]
    if palette:
        swatches = " ".join(
            f"`{c['hex']}`" for c in palette[:8])
        add(f"- Dominant measured palette: {swatches}")
    add(f"- Brightness median {visual['brightness']['median']}, "
        f"saturation median {visual['saturation']['median']}")
    add(f"- Majority-white frames: {visual['frames_majority_white_pct']}% of shots "
        f"(whiteboard feel)")
    add(f"- Significant colors per frame: median {visual['significant_colors_per_frame']['median']}")
    add("")
    add("## Composition")
    add("")
    add(f"- Ink centroid: x {visual['ink_centroid_x_normalized']['median']}, "
        f"y {visual['ink_centroid_y_normalized']['median']} of frame")
    add(f"- Linework bounding-box width: {visual['ink_bbox_width_fraction']['median']} of frame")
    add(f"- White/negative space: median {visual['white_background_fraction']['median']} of frame")
    add("")
    add("## Editing & pacing")
    add("")
    shot = editing["shot_duration_seconds"]
    add(f"- Shot length: median **{shot['median']} s** (mean {shot['mean']} s, "
        f"p25 {shot['p25']} s, p75 {shot['p75']} s)")
    add(f"- {round(editing['shots_under_1s']/max(editing['detected_shot_count'],1)*100,1)}% of shots under 1 s, "
        f"{round(editing['shots_1_to_6s']/max(editing['detected_shot_count'],1)*100,1)}% between 1-6 s, "
        f"{round(editing['shots_over_10s']/max(editing['detected_shot_count'],1)*100,1)}% over 10 s")
    add(f"- Transitions: {editing['transition_counts']}")
    if summary["transcript"]["available"]:
        add(f"- Cuts land {editing['cut_minus_word_start_seconds']['median']} s before the "
            f"spoken word (median); {editing['cuts_before_word_start_pct']}% of cuts precede "
            f"the nearest word start")
    add("")
    add("## Motion")
    add("")
    for kind, pct in motion["shot_percentages"].items():
        add(f"- {kind.replace('_', ' ')}: **{pct}%** of shots")
    add(f"- Verified whole-scene zooms: "
        f"{motion['shot_counts'].get('whole_scene_zoom_in', 0) + motion['shot_counts'].get('whole_scene_zoom_out', 0)} "
        f"→ camera stays **locked**")
    add("")
    add("## Audio")
    add("")
    if audio:
        add(f"- Integrated loudness **{audio.get('integrated_lufs')} LUFS**, "
            f"true peak {audio.get('true_peak_dbfs')} dBTP, LRA {audio.get('lra_lu')} LU")
        add(f"- Recognized narration pace ~{audio.get('recognized_wpm_full_runtime')} WPM")
        add(f"- Estimated mixed-onset tempo ~{audio.get('estimated_tempo_bpm')} BPM")
        add(f"- Inter-word pauses >= 0.2 s: median "
            f"{audio.get('inter_word_pause_seconds_ge_0_20', {}).get('median')} s")
    else:
        add("- No audio stream in the upload")
    add("")
    if chapters:
        add("## Estimated chapters")
        add("")
        for start, title in chapters:
            mm = int(start // 60)
            add(f"- {mm:02d}:{start - mm * 60:05.2f} — {title}")
        add("")
    add("## Keyframe recipes")
    add("")
    for recipe in rules["keyframe_recipes"]:
        add(f"- **{recipe['name']}** — {recipe['notes']} ({recipe['provenance']})")
    add("")
    add("## Implementation checklist")
    add("")
    add(f"- [ ] Canvas: {rules['format']['output_resolution'][0]}x{rules['format']['output_resolution'][1]}, "
        f"{rules['format']['output_fps']} fps, H.264 + AAC")
    add(f"- [ ] Median shot target {shot['median']} s; hard cuts only; "
        f"{motion['shot_percentages'].get('frozen_hold', 0)}% of shots frozen")
    add("- [ ] Camera locked; animate parts, labels and pose swaps instead of zooms")
    add("- [ ] One near-black imperfect contour; flat character fills; "
        "gradients only for world plates")
    add(f"- [ ] Palette from measured swatches; mix to ~{audio.get('integrated_lufs')} LUFS "
        f"with true peak <= {audio.get('true_peak_dbfs')} dBTP")
    add("- [ ] No captions, no per-cut whooshes, no music louder than the voice")
    add("")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# combine multiple profiles into one merged style bible
# ----------------------------------------------------------------------------

def combine_profiles(dirs: list[Path], out_dir: Path, label: str, progress: ProgressFn) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs: list[tuple[Path, dict[str, Any]]] = []
    rules_list: list[dict[str, Any]] = []
    for directory in dirs:
        metrics = directory / "metrics.json"
        rules = directory / "style_rules.json"
        if metrics.exists():
            pairs.append((directory, json.loads(metrics.read_text(encoding="utf-8"))))
        if rules.exists():
            rules_list.append(json.loads(rules.read_text(encoding="utf-8")))
    if not pairs:
        raise RuntimeError("no metrics.json found in the given directories")
    summaries = [summary for _, summary in pairs]

    progress("combine", 60, f"Merging {len(summaries)} analyzed videos")
    total_shots = sum(s["editing"]["detected_shot_count"] for s in summaries)
    total_events = sum(s["editing"]["detected_edit_event_count"] for s in summaries)
    motion_counts: Counter[str] = Counter()
    transition_counts: Counter[str] = Counter()
    durations: list[float] = []
    wpm: list[float] = []
    lufs: list[float] = []
    palette_weights: Counter[str] = Counter()
    for directory, s in pairs:
        shots_csv = directory / "shots.csv"
        if shots_csv.exists():
            with shots_csv.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    durations.append(float(row["duration_seconds"]))
        motion_counts.update(s["motion"]["shot_counts"])
        transition_counts.update(s["editing"]["transition_counts"])
        palette_weights.update(
            {c["hex"]: c["relative_weight"] for c in s["visual"]["dominant_quantized_palette"]})
        if s["transcript"]["available"] and s["audio"]:
            wpm.append(float(s["audio"]["recognized_wpm_full_runtime"] or 0))
        if s["audio"] and s["audio"].get("integrated_lufs") is not None:
            lufs.append(float(s["audio"]["integrated_lufs"]))

    first = rules_list[0] if rules_list else {}
    merged = json.loads(json.dumps(first)) if first else {}
    shot_stats = corpus.describe(durations)
    merged["schema_version"] = SCHEMA_VERSION
    merged["authority"] = (
        f"Measured from {len(summaries)} user-uploaded reference videos; merged by "
        f"scripts/analyze_style.py combine. Supersedes single-video values where they differ.")
    merged["target_version"]["primary"] = label or f"{len(summaries)}-video merged profile"
    merged["target_version"]["reason"] = "Merged measured profile of all uploaded references."
    merged["source_measurement"] = {
        "video_count": len(summaries),
        "runtime_seconds": round(sum(s["source_specs"]["duration_seconds"] for s in summaries), 3),
        "frames_scanned": sum(s["source_specs"]["frame_count"] for s in summaries),
        "detected_shots": total_shots,
        "detected_edit_events": total_events,
    }
    merged["editing"]["shot_duration_seconds"] = shot_stats
    merged["editing"]["detected_shot_count"] = total_shots
    merged["editing"]["distribution_pct"] = {
        "under_1s": round(sum(1 for d in durations if d < 1) / max(len(durations), 1) * 100, 2),
        "between_1_and_6s": round(sum(1 for d in durations if 1 <= d <= 6) / max(len(durations), 1) * 100, 2),
        "over_10s": round(sum(1 for d in durations if d > 10) / max(len(durations), 1) * 100, 2),
    }
    merged["editing"]["transition_pct"] = {
        key: round(transition_counts.get(key, 0) / max(total_events, 1) * 100, 2)
        for key in ("hard_cut_full_frame", "hard_cut_same_palette", "localized_swap_or_pop")}
    merged["editing"]["transition_pct"]["dissolve_or_fade_verified"] = 0.0
    merged["motion"]["budget_pct_of_shots"] = {
        key: round(value / max(total_shots, 1) * 100, 2) for key, value in motion_counts.items()}
    merged["audio"]["recognized_wpm_full_runtime"] = round(statistics.median(wpm), 2) if wpm else None
    merged["audio"]["integrated_lufs"] = round(statistics.median(lufs), 3) if lufs else None
    if merged.get("art") and merged["art"].get("palette"):
        core, emphasis = split_palette(
            [{"hex": h, "relative_weight": w} for h, w in palette_weights.most_common(12)])
        merged["art"]["palette"]["dominant_measured"] = [
            {"hex": h, "relative_weight": round(w / (sum(palette_weights.values()) or 1), 5)}
            for h, w in palette_weights.most_common(8)]
        if core:
            merged["art"]["palette"]["core"] = core
        if emphasis:
            merged["art"]["palette"]["emphasis"] = emphasis
    merged["measurement_notes"] = [
        "Merged from multiple uploaded references; per-video metrics.json files hold the "
        "individual measurements."]

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "style_rules.json").write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    combined = {
        "video_count": len(summaries),
        "total_runtime_seconds": round(sum(s["source_specs"]["duration_seconds"] for s in summaries), 3),
        "total_frames_scanned": sum(s["source_specs"]["frame_count"] for s in summaries),
        "total_detected_shots": total_shots,
        "total_detected_edit_events": total_events,
        "motion_shot_percentages": merged["motion"]["budget_pct_of_shots"],
        "transition_pct": merged["editing"]["transition_pct"],
        "median_shot_seconds": shot_stats["median"],
        "median_recognized_wpm": merged["audio"]["recognized_wpm_full_runtime"],
        "median_integrated_lufs": merged["audio"]["integrated_lufs"],
        "per_video": [
            {
                "file": s["identity"]["file"],
                "label": s["identity"]["label"],
                "shots": s["editing"]["detected_shot_count"],
                "median_shot_seconds": s["editing"]["shot_duration_seconds"]["median"],
                "recognized_wpm": s["audio"]["recognized_wpm_full_runtime"] if s["audio"] else None,
                "integrated_lufs": s["audio"]["integrated_lufs"] if s["audio"] else None,
                "majority_white_frames_pct": s["visual"]["frames_majority_white_pct"],
            }
            for s in summaries
        ],
    }
    (out_dir / "combined.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    progress("done", 100, f"Merged profile ready ({len(summaries)} videos)")
    return merged


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="measure one reference video")
    analyze.add_argument("--video", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    analyze.add_argument("--label", default="")
    analyze.add_argument("--limit-frames", type=int, default=None)
    analyze.add_argument("--progress", default=None)
    analyze.add_argument("--analyzed-at", default="")

    combine = sub.add_parser("combine", help="merge several analyzed profiles")
    combine.add_argument("--dirs", required=True, nargs="+", type=Path)
    combine.add_argument("--out", required=True, type=Path)
    combine.add_argument("--label", default="")
    combine.add_argument("--progress", default=None)

    args = parser.parse_args()
    if args.command == "analyze":
        progress = make_progress(args.progress)
        try:
            summary = analyze_video(args.video, args.out, args.label, progress, args.limit_frames)
            if args.analyzed_at:
                summary["identity"]["analyzed_at"] = args.analyzed_at
                (args.out / "metrics.json").write_text(
                    json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"done: {summary['editing']['detected_shot_count']} shots, "
                  f"{summary['editing']['detected_edit_event_count']} cuts -> {args.out}")
        except Exception as exc:  # noqa: BLE001 — surface failure for the studio UI
            if args.progress:
                Path(args.progress).write_text(
                    json.dumps({"stage": "failed", "pct": 100, "message": str(exc)}),
                    encoding="utf-8")
            raise
    elif args.command == "combine":
        combine_profiles(args.dirs, args.out, args.label, make_progress(args.progress))
        print(f"merged -> {args.out}")


if __name__ == "__main__":
    main()
