#!/usr/bin/env python3
"""Reproducible frame/audio analysis for the four uploaded Paint Explainer videos.

Inputs are declared in references/paint-explainer-analysis-4v/analysis_manifest.json.
Outputs:
  metrics/<id>.json        per-video measured summary
  metrics/combined.json    corpus aggregates
  cuts/<id>-cuts.csv       every detected abrupt edit event
  cuts/<id>-shots.csv      every measured shot and motion classification

The script scans every decoded source frame for scene boundaries using
PySceneDetect, then samples within each shot for camera/character motion. The
source copies are 640x360/30 fps transcodes, so inferred layer transforms and
stroke widths are estimates rather than access to original AE keyframes.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import librosa
import numpy as np
from scenedetect import ContentDetector, SceneManager, open_video
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "references" / "paint-explainer-analysis-4v"
MANIFEST = ANALYSIS / "analysis_manifest.json"
TRANSCRIPTS = ANALYSIS / "transcripts"
METRICS = ANALYSIS / "metrics"
CUTS = ANALYSIS / "cuts"


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes = int(seconds // 60)
    return f"{minutes:02d}:{seconds - minutes * 60:06.3f}"


def percentile(values: list[float], q: float) -> float | None:
    return round(float(np.percentile(values, q)), 4) if values else None


def describe(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p25": None, "median": None, "mean": None, "p75": None, "p90": None, "max": None}
    return {
        "min": round(min(values), 4),
        "p25": percentile(values, 25),
        "median": round(statistics.median(values), 4),
        "mean": round(statistics.mean(values), 4),
        "p75": percentile(values, 75),
        "p90": percentile(values, 90),
        "max": round(max(values), 4),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def get_frame(cap: cv2.VideoCapture, frame_number: int) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number))
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"cannot decode frame {frame_number}")
    return frame


def small_gray(frame: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)


def diff_metrics(before: np.ndarray, after: np.ndarray) -> dict[str, float]:
    a = cv2.resize(before, (320, 180), interpolation=cv2.INTER_AREA)
    b = cv2.resize(after, (320, 180), interpolation=cv2.INTER_AREA)
    diff = cv2.absdiff(a, b)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    mean_abs = float(np.mean(diff) / 255.0)
    changed = float(np.mean(gray > 20))
    large_changed = float(np.mean(gray > 45))
    return {
        "mean_abs_rgb": round(mean_abs, 6),
        "changed_fraction_gt20": round(changed, 6),
        "changed_fraction_gt45": round(large_changed, 6),
    }


def estimate_transform(before: np.ndarray, after: np.ndarray) -> dict[str, float | bool]:
    """Estimate a robust whole-frame similarity transform with ORB+RANSAC."""
    a = small_gray(before)
    b = small_gray(after)
    orb = cv2.ORB_create(nfeatures=1800, fastThreshold=7)
    k1, d1 = orb.detectAndCompute(a, None)
    k2, d2 = orb.detectAndCompute(b, None)
    empty = {
        "valid": False, "scale": 1.0, "scale_delta_pct": 0.0,
        "rotation_deg": 0.0, "translation_x_pct": 0.0,
        "translation_y_pct": 0.0, "inlier_ratio": 0.0,
        "residual_mean_abs": 1.0, "residual_changed_fraction": 1.0,
    }
    if d1 is None or d2 is None or len(k1) < 12 or len(k2) < 12:
        return empty
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(d1, d2, k=2)
    good = [m for m, n in matches if m.distance < 0.76 * n.distance]
    if len(good) < 10:
        return empty
    src = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    matrix, inliers = cv2.estimateAffinePartial2D(
        src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5,
        maxIters=2500, confidence=0.995, refineIters=10,
    )
    if matrix is None or inliers is None:
        return empty
    inlier_ratio = float(inliers.mean())
    aa, bb = float(matrix[0, 0]), float(matrix[0, 1])
    scale = math.sqrt(aa * aa + bb * bb)
    rotation = math.degrees(math.atan2(bb, aa))
    tx_pct = float(matrix[0, 2] / a.shape[1] * 100.0)
    ty_pct = float(matrix[1, 2] / a.shape[0] * 100.0)
    warped = cv2.warpAffine(a, matrix, (a.shape[1], a.shape[0]))
    residual = cv2.absdiff(warped, b)
    plausible = (
        inlier_ratio >= 0.35
        and 0.65 <= scale <= 1.50
        and abs(rotation) <= 15.0
        and abs(tx_pct) <= 40.0
        and abs(ty_pct) <= 40.0
    )
    return {
        "valid": bool(plausible),
        "scale": round(scale, 6),
        "scale_delta_pct": round((scale - 1.0) * 100.0, 4),
        "rotation_deg": round(rotation, 4),
        "translation_x_pct": round(tx_pct, 4),
        "translation_y_pct": round(ty_pct, 4),
        "inlier_ratio": round(inlier_ratio, 5),
        "residual_mean_abs": round(float(np.mean(residual) / 255.0), 6),
        "residual_changed_fraction": round(float(np.mean(residual > 20)), 6),
    }


def visual_metrics(frame: np.ndarray) -> dict[str, Any]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    value = hsv[:, :, 2].astype(np.float32) / 255.0
    saturation = hsv[:, :, 1].astype(np.float32) / 255.0
    white = np.all(rgb >= 242, axis=2)
    black = np.all(rgb <= 35, axis=2)
    dark = np.mean(rgb, axis=2) <= 64

    # Quantize to 8 levels/channel. Count only fills occupying >=0.5% frame.
    q = (rgb // 32).astype(np.int32)
    packed = q[:, :, 0] * 64 + q[:, :, 1] * 8 + q[:, :, 2]
    counts = np.bincount(packed.ravel(), minlength=512)
    significant = int(np.sum(counts >= rgb.shape[0] * rgb.shape[1] * 0.005))
    top_indices = counts.argsort()[-8:][::-1]
    top_colors = []
    for idx in top_indices:
        r, rem = divmod(int(idx), 64)
        g, b = divmod(rem, 8)
        top_colors.append({
            "hex": f"#{r * 32 + 16:02X}{g * 32 + 16:02X}{b * 32 + 16:02X}",
            "fraction": round(float(counts[idx] / counts.sum()), 5),
        })

    # Ink/edge centroid excludes persistent top chapter-title band.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 160)
    edges[: int(frame.shape[0] * 0.11), :] = 0
    yy, xx = np.nonzero(edges)
    if len(xx):
        centroid = [round(float(np.mean(xx) / frame.shape[1]), 4), round(float(np.mean(yy) / frame.shape[0]), 4)]
    else:
        centroid = [0.5, 0.5]

    return {
        "mean_brightness": round(float(value.mean()), 5),
        "mean_saturation": round(float(saturation.mean()), 5),
        "white_fraction": round(float(white.mean()), 5),
        "black_fraction": round(float(black.mean()), 5),
        "dark_fraction": round(float(dark.mean()), 5),
        "significant_color_count": significant,
        "top_quantized_colors": top_colors,
        "ink_edge_centroid_normalized": centroid,
    }


def stroke_widths(frame: np.ndarray) -> list[float]:
    """Estimate black stroke widths in bright/white-canvas frames."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    bright_fraction = float(np.mean(np.mean(rgb, axis=2) > 225))
    if bright_fraction < 0.50:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    dark = gray < 62
    # Remove title strip and tiny compression flecks.
    dark[: int(frame.shape[0] * 0.11), :] = False
    n, labels, stats, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8), 8)
    clean = np.zeros_like(dark)
    for label in range(1, n):
        if stats[label, cv2.CC_STAT_AREA] >= 8:
            clean[labels == label] = True
    if not clean.any():
        return []
    dist = cv2.distanceTransform(clean.astype(np.uint8), cv2.DIST_L2, 5)
    skeleton = skeletonize(clean)
    widths = (2.0 * dist[skeleton]).tolist()
    # Broad fills are not linework. Keep likely line-width samples at source res.
    return [float(w) for w in widths if 0.8 <= w <= 8.0]


def chapter_at(chapters: list[list[Any]], seconds: float) -> str:
    starts = [float(c[0]) for c in chapters]
    index = max(0, bisect.bisect_right(starts, seconds) - 1)
    return str(chapters[index][1])


def nearest_word(words: list[dict[str, Any]], seconds: float) -> tuple[str, float | None]:
    if not words:
        return "", None
    starts = [float(word["start"]) for word in words]
    i = bisect.bisect_left(starts, seconds)
    choices = [j for j in (i - 1, i) if 0 <= j < len(words)]
    j = min(choices, key=lambda item: abs(starts[item] - seconds))
    return str(words[j]["word"]), round(seconds - starts[j], 4)


def detect_scenes(path: Path, fps: float) -> list[tuple[int, int]]:
    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=18.0, min_scene_len=max(1, round(fps * 0.2))))
    manager.detect_scenes(video=video, show_progress=False)
    scenes = manager.get_scene_list(start_in_scene=True)
    return [(start.get_frames(), end.get_frames()) for start, end in scenes]


def parse_loudnorm(path: Path) -> dict[str, float | None]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
         "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        text=True, capture_output=True,
    )
    matches = re.findall(r"\{[\s\S]*?\}", proc.stderr)
    if not matches:
        return {"integrated_lufs": None, "true_peak_dbfs": None, "lra_lu": None, "threshold_lufs": None}
    data = json.loads(matches[-1])
    def number(key: str) -> float | None:
        try:
            return round(float(data[key]), 3)
        except (KeyError, TypeError, ValueError):
            return None
    return {
        "integrated_lufs": number("input_i"),
        "true_peak_dbfs": number("input_tp"),
        "lra_lu": number("input_lra"),
        "threshold_lufs": number("input_thresh"),
    }


def decode_audio(path: Path, sample_rate: int = 16000) -> np.ndarray:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-vn", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "-"],
        check=True, capture_output=True,
    )
    return np.frombuffer(proc.stdout, dtype=np.float32)


def audio_metrics(path: Path, transcript: dict[str, Any], duration: float) -> dict[str, Any]:
    sr = 16000
    audio = decode_audio(path, sr)
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    rms = float(np.sqrt(np.mean(audio * audio))) if len(audio) else 0.0
    peak_db = 20 * math.log10(max(peak, 1e-9))
    rms_db = 20 * math.log10(max(rms, 1e-9))
    hop = 512
    onset = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop)
    tempo_value = float(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) else 0.0
    onset_times = librosa.frames_to_time(np.argsort(onset)[-30:][::-1], sr=sr, hop_length=hop)

    words = transcript.get("words") or []
    gaps = []
    for left, right in zip(words, words[1:]):
        gap = float(right["start"]) - float(left["end"])
        if gap >= 0.20:
            gaps.append(gap)
    detected_speech_span = float(words[-1]["end"] - words[0]["start"]) if len(words) >= 2 else duration
    word_count = int(transcript.get("word_count") or len(words))
    return {
        **parse_loudnorm(path),
        "sample_peak_dbfs": round(peak_db, 3),
        "sample_rms_dbfs": round(rms_db, 3),
        "estimated_tempo_bpm": round(tempo_value, 2),
        "tempo_caveat": "Onset estimate includes narration and SFX; use as music-bed range evidence, not a clean stem BPM.",
        "strongest_transient_times_seconds": [round(float(value), 3) for value in sorted(onset_times[:20])],
        "recognized_word_count": word_count,
        "recognized_wpm_full_runtime": round(word_count / duration * 60.0, 2),
        "recognized_wpm_speech_span": round(word_count / max(detected_speech_span, 1.0) * 60.0, 2),
        "inter_word_pause_seconds_ge_0_20": describe(gaps),
        "pause_count_ge_0_20": len(gaps),
        "pause_count_ge_0_50": sum(value >= 0.50 for value in gaps),
        "pause_count_ge_0_70": sum(value >= 0.70 for value in gaps),
    }


def classify_motion(duration: float, diffs: list[dict[str, float]], transform: dict[str, Any]) -> tuple[str, dict[str, float]]:
    raw_diff = statistics.mean([item["mean_abs_rgb"] for item in diffs]) if diffs else 0.0
    raw_changed = statistics.mean([item["changed_fraction_gt20"] for item in diffs]) if diffs else 0.0
    scale_delta = float(transform.get("scale_delta_pct") or 0.0)
    translation = math.hypot(float(transform.get("translation_x_pct") or 0.0), float(transform.get("translation_y_pct") or 0.0))
    valid = bool(transform.get("valid"))
    residual = float(transform.get("residual_changed_fraction") or 0.0)

    # A real camera transform moves almost all surviving linework together and
    # leaves a low registration residual. Without this gate ORB can lock onto a
    # moving character and falsely report a 100% "camera zoom". The verified
    # corpus mostly uses locked cameras; clean translations are chapter/canvas
    # slides rather than pans following a character.
    clean_global_transform = valid and residual <= 0.12
    whole_scene_zoom = clean_global_transform and abs(scale_delta) >= 1.0
    whole_canvas_slide = clean_global_transform and not whole_scene_zoom and translation >= 0.9
    character = raw_changed >= 0.055 or (valid and residual >= 0.06)
    frozen = raw_diff < 0.0075 and raw_changed < 0.025
    if frozen:
        kind = "frozen_hold"
    elif whole_scene_zoom:
        kind = "whole_scene_zoom_in" if scale_delta > 0 else "whole_scene_zoom_out"
    elif whole_canvas_slide:
        kind = "whole_canvas_slide"
    elif character:
        kind = "character_or_graphic_animation"
    elif duration < 0.9:
        kind = "short_graphic_sting"
    else:
        kind = "subtle_local_motion"
    derived = {
        "sampled_mean_abs_rgb": round(raw_diff, 6),
        "sampled_changed_fraction": round(raw_changed, 6),
        "global_translation_total_pct": round(translation, 4),
        "global_scale_speed_pct_per_s": round(scale_delta / max(duration, 0.033), 4),
    }
    return kind, derived


def analyze_video(item: dict[str, Any]) -> dict[str, Any]:
    file_id = str(item["file_id"])
    path = ROOT / item["path"]
    transcript = json.loads((TRANSCRIPTS / f"{file_id}.json").read_text(encoding="utf-8"))
    words = transcript.get("words") or []
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps
    scenes = detect_scenes(path, fps)

    shot_rows: list[dict[str, Any]] = []
    cut_rows: list[dict[str, Any]] = []
    frame_visuals: list[dict[str, Any]] = []
    stroke_samples: list[float] = []
    all_zoom_speeds: list[float] = []
    all_zoom_distances: list[float] = []

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
        frames = [get_frame(cap, number) for number in sample_numbers]
        diffs = [diff_metrics(left, right) for left, right in zip(frames, frames[1:])]
        transform = estimate_transform(frames[0], frames[-1]) if len(frames) >= 2 else estimate_transform(frames[0], frames[0])
        kind, derived = classify_motion(shot_duration, diffs, transform)
        midpoint_metrics = visual_metrics(frames[len(frames) // 2])
        frame_visuals.append(midpoint_metrics)
        stroke_samples.extend(stroke_widths(frames[len(frames) // 2]))
        if kind in {"whole_scene_zoom_in", "whole_scene_zoom_out"}:
            all_zoom_distances.append(float(transform["scale_delta_pct"]))
            all_zoom_speeds.append(float(derived["global_scale_speed_pct_per_s"]))
        shot_rows.append({
            "shot": index,
            "start_frame": start,
            "end_frame_exclusive": end,
            "start_seconds": round(start / fps, 4),
            "end_seconds": round(end / fps, 4),
            "start_timecode": fmt_time(start / fps),
            "end_timecode": fmt_time(end / fps),
            "duration_seconds": round(shot_duration, 4),
            "chapter": chapter_at(item["chapters"], start / fps),
            "motion_class": kind,
            **derived,
            **transform,
        })

        if index > 1:
            boundary = start
            before = get_frame(cap, max(0, boundary - 1))
            after = get_frame(cap, min(frame_count - 1, boundary))
            metrics = diff_metrics(before, after)
            word, delta = nearest_word(words, boundary / fps)
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
                "timestamp": fmt_time(boundary / fps),
                "preceding_shot_duration_seconds": shot_rows[-2]["duration_seconds"],
                "chapter": chapter_at(item["chapters"], boundary / fps),
                "transition_class": transition,
                **metrics,
                "nearest_spoken_word": word,
                "cut_minus_word_start_seconds": delta,
            })

    cap.release()
    durations = [float(row["duration_seconds"]) for row in shot_rows]
    motion_counts = Counter(row["motion_class"] for row in shot_rows)
    transition_counts = Counter(row["transition_class"] for row in cut_rows)
    cut_word_deltas = [abs(float(row["cut_minus_word_start_seconds"])) for row in cut_rows if row["cut_minus_word_start_seconds"] is not None]

    # Aggregate palettes from frame-level top colors, weighted by listed fraction.
    palette_weights: Counter[str] = Counter()
    for frame_metric in frame_visuals:
        for color in frame_metric["top_quantized_colors"]:
            palette_weights[color["hex"]] += color["fraction"]
    palette_total = sum(palette_weights.values()) or 1.0
    palette = [{"hex": color, "relative_weight": round(weight / palette_total, 5)} for color, weight in palette_weights.most_common(12)]

    brightness = [float(metric["mean_brightness"]) for metric in frame_visuals]
    saturation = [float(metric["mean_saturation"]) for metric in frame_visuals]
    white_fraction = [float(metric["white_fraction"]) for metric in frame_visuals]
    significant_colors = [float(metric["significant_color_count"]) for metric in frame_visuals]
    centroid_x = [float(metric["ink_edge_centroid_normalized"][0]) for metric in frame_visuals]
    centroid_y = [float(metric["ink_edge_centroid_normalized"][1]) for metric in frame_visuals]

    audio = audio_metrics(path, transcript, duration)
    summary = {
        "identity": {
            "file_id": file_id,
            "file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "youtube_id": item["youtube_id"],
            "title": item["title"],
            "upload_date": item["upload_date"],
        },
        "source_specs": {
            "width": width, "height": height, "fps": fps,
            "frame_count": frame_count, "duration_seconds": round(duration, 4),
            "timing_precision_seconds": round(1.0 / fps, 6),
        },
        "editing": {
            "detected_shot_count": len(shot_rows),
            "detected_edit_event_count": len(cut_rows),
            "shot_duration_seconds": describe(durations),
            "shots_under_1s": sum(value < 1.0 for value in durations),
            "shots_1_to_6s": sum(1.0 <= value <= 6.0 for value in durations),
            "shots_over_10s": sum(value > 10.0 for value in durations),
            "transition_counts": dict(transition_counts),
            "cut_to_nearest_word_abs_seconds": describe(cut_word_deltas),
            "cuts_within_0_20s_of_word_start_pct": round(sum(value <= 0.20 for value in cut_word_deltas) / max(len(cut_word_deltas), 1) * 100, 2),
            "cuts_within_0_35s_of_word_start_pct": round(sum(value <= 0.35 for value in cut_word_deltas) / max(len(cut_word_deltas), 1) * 100, 2),
        },
        "motion": {
            "shot_counts": dict(motion_counts),
            "shot_percentages": {key: round(value / len(shot_rows) * 100, 2) for key, value in motion_counts.items()},
            "zoom_distance_pct": describe(all_zoom_distances),
            "zoom_speed_pct_per_s": describe(all_zoom_speeds),
        },
        "visual": {
            "brightness": describe(brightness),
            "saturation": describe(saturation),
            "white_background_fraction": describe(white_fraction),
            "frames_majority_white_pct": round(sum(value >= 0.50 for value in white_fraction) / max(len(white_fraction), 1) * 100, 2),
            "significant_colors_per_frame": describe(significant_colors),
            "ink_centroid_x_normalized": describe(centroid_x),
            "ink_centroid_y_normalized": describe(centroid_y),
            "estimated_black_stroke_width_px_at_360p": describe(stroke_samples),
            "estimated_black_stroke_width_px_at_1080p": {key: (round(value * 3, 3) if value is not None else None) for key, value in describe(stroke_samples).items()},
            "dominant_quantized_palette": palette,
        },
        "audio": audio,
        "chapters": [{"start_seconds": start, "start": fmt_time(start), "title": title} for start, title in item["chapters"]],
        "measurement_notes": [
            "Edit events are one-frame abrupt visual boundaries at 30 fps. Localized swaps/pops are separated from full-frame hard cuts by changed-pixel area.",
            "Motion transforms are inferred from flattened frames using ORB/RANSAC; exact AE curves and hidden layer anchors cannot be recovered.",
            "Vosk transcript is used for timing/WPM; proper-noun spelling should be checked against the chapter list.",
        ],
    }

    CUTS.mkdir(parents=True, exist_ok=True)
    METRICS.mkdir(parents=True, exist_ok=True)
    with (CUTS / f"{file_id}-shots.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(shot_rows[0].keys()), lineterminator="\n")
        writer.writeheader(); writer.writerows(shot_rows)
    with (CUTS / f"{file_id}-cuts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cut_rows[0].keys()), lineterminator="\n")
        writer.writeheader(); writer.writerows(cut_rows)
    (METRICS / f"{file_id}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{file_id}: {len(shot_rows)} shots, {len(cut_rows)} edit events")
    return summary


def combine(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    total_shots = sum(item["editing"]["detected_shot_count"] for item in summaries)
    total_events = sum(item["editing"]["detected_edit_event_count"] for item in summaries)
    motion = Counter()
    transitions = Counter()
    weighted_brightness = []
    weighted_saturation = []
    for item in summaries:
        motion.update(item["motion"]["shot_counts"])
        transitions.update(item["editing"]["transition_counts"])
        weighted_brightness.extend([item["visual"]["brightness"]["median"]] * item["editing"]["detected_shot_count"])
        weighted_saturation.extend([item["visual"]["saturation"]["median"]] * item["editing"]["detected_shot_count"])
    combined = {
        "video_count": len(summaries),
        "total_runtime_seconds": round(sum(item["source_specs"]["duration_seconds"] for item in summaries), 3),
        "total_frames_scanned": sum(item["source_specs"]["frame_count"] for item in summaries),
        "total_detected_shots": total_shots,
        "total_detected_edit_events": total_events,
        "motion_shot_counts": dict(motion),
        "motion_shot_percentages": {key: round(value / total_shots * 100, 2) for key, value in motion.items()},
        "transition_counts": dict(transitions),
        "corpus_brightness_median_of_shot_weighted_video_medians": round(statistics.median(weighted_brightness), 4),
        "corpus_saturation_median_of_shot_weighted_video_medians": round(statistics.median(weighted_saturation), 4),
        "per_video": [
            {
                "file_id": item["identity"]["file_id"],
                "title": item["identity"]["title"],
                "upload_date": item["identity"]["upload_date"],
                "shots": item["editing"]["detected_shot_count"],
                "median_shot_seconds": item["editing"]["shot_duration_seconds"]["median"],
                "mean_shot_seconds": item["editing"]["shot_duration_seconds"]["mean"],
                "recognized_wpm": item["audio"]["recognized_wpm_full_runtime"],
                "integrated_lufs": item["audio"]["integrated_lufs"],
                "majority_white_frames_pct": item["visual"]["frames_majority_white_pct"],
            }
            for item in summaries
        ],
    }
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", help="analyze only a file_id; may be repeated")
    parser.add_argument("--combine-only", action="store_true", help="combine existing per-video metrics without rescanning")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.combine_only:
        summaries = [json.loads((METRICS / f"{item['file_id']}.json").read_text(encoding="utf-8")) for item in manifest["videos"]]
        combined = combine(summaries)
        (METRICS / "combined.json").write_text(json.dumps(combined, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"combined: {combined['total_frames_scanned']} frames, {combined['total_detected_shots']} shots")
        return
    selected = [item for item in manifest["videos"] if not args.only or str(item["file_id"]) in args.only]
    summaries = [analyze_video(item) for item in selected]
    if not args.only:
        combined = combine(summaries)
        METRICS.mkdir(parents=True, exist_ok=True)
        (METRICS / "combined.json").write_text(json.dumps(combined, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"combined: {combined['total_frames_scanned']} frames, {combined['total_detected_shots']} shots")


if __name__ == "__main__":
    main()
