#!/usr/bin/env python3
"""Full-frame scan and shot atlas for videos uploaded through Reference Studio."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scenedetect import ContentDetector, SceneManager, open_video

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_paint_explainer_corpus import (  # noqa: E402
    describe,
    diff_metrics,
    estimate_transform,
    stroke_widths,
    visual_metrics,
)


def frame_at(cap: cv2.VideoCapture, number: int) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, number))
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"cannot decode frame {number}")
    return frame


def scan_every_frame(path: Path, output: Path, fps: float) -> dict:
    cap = cv2.VideoCapture(str(path))
    rows = []
    previous = None
    frame_number = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320, 180), interpolation=cv2.INTER_AREA)
        if previous is None:
            mean_abs = changed = changed45 = 0.0
        else:
            delta = cv2.absdiff(previous, gray)
            mean_abs = float(delta.mean() / 255.0)
            changed = float(np.mean(delta > 20))
            changed45 = float(np.mean(delta > 45))
        rows.append((frame_number, frame_number / fps, mean_abs, changed, changed45))
        previous = gray
        frame_number += 1
    cap.release()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame", "seconds", "mean_abs", "changed_gt20", "changed_gt45"])
        writer.writerows((n, f"{t:.6f}", f"{m:.7f}", f"{c:.7f}", f"{c45:.7f}") for n, t, m, c, c45 in rows)
    means = [r[2] for r in rows[1:]]
    changed = [r[3] for r in rows[1:]]
    return {
        "frames_scanned": len(rows),
        "frame_difference_mean_abs": describe(means),
        "changed_fraction_gt20": describe(changed),
        "near_frozen_frame_pairs_pct": round(sum(v < 0.0015 for v in means) / max(1, len(means)) * 100, 2),
        "subtle_frame_pairs_pct": round(sum(0.0015 <= v < 0.012 for v in means) / max(1, len(means)) * 100, 2),
        "active_frame_pairs_pct": round(sum(v >= 0.012 for v in means) / max(1, len(means)) * 100, 2),
    }


def detect_scenes(path: Path, threshold: float) -> list[tuple[int, int]]:
    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=3))
    manager.detect_scenes(video=video, show_progress=True)
    scenes = manager.get_scene_list(start_in_scene=True)
    return [(a.get_frames(), b.get_frames()) for a, b in scenes]


def classify_shot(cap: cv2.VideoCapture, start: int, end: int) -> tuple[str, dict]:
    length = max(1, end - start)
    a_num = start + min(max(1, int(length * 0.18)), length - 1)
    b_num = start + min(max(1, int(length * 0.82)), length - 1)
    a = frame_at(cap, a_num)
    b = frame_at(cap, b_num)
    raw = diff_metrics(a, b)
    transform = estimate_transform(a, b)
    camera = transform["valid"] and (
        abs(float(transform["scale_delta_pct"])) >= 0.8
        or abs(float(transform["translation_x_pct"])) >= 1.5
        or abs(float(transform["translation_y_pct"])) >= 1.5
    )
    if camera:
        kind = "camera_move"
    elif raw["mean_abs_rgb"] < 0.003 and raw["changed_fraction_gt20"] < 0.012:
        kind = "frozen_hold"
    elif raw["changed_fraction_gt20"] < 0.08:
        kind = "subtle_local_motion"
    elif raw["changed_fraction_gt20"] < 0.38:
        kind = "active_local_motion"
    else:
        kind = "full_frame_motion_or_internal_cut"
    return kind, {"sample_a_frame": a_num, "sample_b_frame": b_num, "raw": raw, "transform": transform}


def make_atlas(cap: cv2.VideoCapture, shots: list[dict], out_dir: Path, source_width: int, source_height: int) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    font = ImageFont.load_default()
    for shot in shots:
        number = int((shot["start_frame"] + shot["end_frame"] - 1) / 2)
        frame = frame_at(cap, number)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((320, 180))
        card = Image.new("RGB", (320, 211), "white")
        card.paste(image, ((320 - image.width) // 2, 0))
        label = f"{shot['shot']:03d}  {shot['start_seconds']:07.2f}s  {shot['duration_seconds']:05.2f}s  {shot['motion_class']}"
        ImageDraw.Draw(card).text((6, 187), label, font=font, fill=(15, 15, 15))
        cards.append(card)
    outputs = []
    per_page, cols = 20, 4
    for page_start in range(0, len(cards), per_page):
        page_cards = cards[page_start: page_start + per_page]
        rows = (len(page_cards) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 320, rows * 211), (220, 217, 209))
        for index, card in enumerate(page_cards):
            sheet.paste(card, ((index % cols) * 320, (index // cols) * 211))
        path = out_dir / f"shot-atlas-{page_start // per_page + 1:02d}.jpg"
        sheet.save(path, quality=91)
        outputs.append(str(path))
    return outputs


def analyze(path: Path, out_dir: Path, threshold: float) -> dict:
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps
    cap.release()

    full_scan = scan_every_frame(path, out_dir / "every-frame.csv", fps)
    scene_bounds = detect_scenes(path, threshold)
    cap = cv2.VideoCapture(str(path))
    shots = []
    visual_samples = []
    stroke_samples: list[float] = []
    motion_counts = Counter()
    for index, (start, end) in enumerate(scene_bounds, 1):
        duration_seconds = (end - start) / fps
        motion, proof = classify_shot(cap, start, end)
        motion_counts[motion] += 1
        midpoint = max(start, min(end - 1, (start + end) // 2))
        frame = frame_at(cap, midpoint)
        visual = visual_metrics(frame)
        visual_samples.append(visual)
        stroke_samples.extend(stroke_widths(frame))
        shots.append({
            "shot": index,
            "start_frame": start,
            "end_frame": end,
            "start_seconds": round(start / fps, 4),
            "end_seconds": round(end / fps, 4),
            "duration_seconds": round(duration_seconds, 4),
            "motion_class": motion,
            "sample_a_frame": proof["sample_a_frame"],
            "sample_b_frame": proof["sample_b_frame"],
            "changed_fraction": proof["raw"]["changed_fraction_gt20"],
            "mean_abs_rgb": proof["raw"]["mean_abs_rgb"],
            "transform_valid": proof["transform"]["valid"],
            "scale_delta_pct": proof["transform"]["scale_delta_pct"],
            "translation_x_pct": proof["transform"]["translation_x_pct"],
            "translation_y_pct": proof["transform"]["translation_y_pct"],
            "white_fraction": visual["white_fraction"],
            "mean_saturation": visual["mean_saturation"],
            "significant_colors": visual["significant_color_count"],
        })
    atlas = make_atlas(cap, shots, out_dir / "atlases", width, height)
    cap.release()

    with (out_dir / "shots.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(shots[0].keys()))
        writer.writeheader(); writer.writerows(shots)

    durations = [s["duration_seconds"] for s in shots]
    colors = [v["significant_color_count"] for v in visual_samples]
    white = [v["white_fraction"] for v in visual_samples]
    saturation = [v["mean_saturation"] for v in visual_samples]
    palette = Counter()
    for visual in visual_samples:
        for item in visual["top_quantized_colors"]:
            palette[item["hex"]] += item["fraction"]
    summary = {
        "source": str(path),
        "width": width, "height": height, "fps": fps,
        "duration_seconds": round(duration, 3), "frame_count": frame_count,
        "analysis": "Every decoded frame scanned; scene boundaries detected with ContentDetector; every shot midpoint visually sampled.",
        "scene_threshold": threshold,
        "full_frame_scan": full_scan,
        "editing": {
            "shot_count": len(shots),
            "cuts": max(0, len(shots) - 1),
            "shot_duration_seconds": describe(durations),
            "shots_under_1s": sum(d < 1 for d in durations),
            "shots_1_to_3s": sum(1 <= d < 3 for d in durations),
            "shots_3_to_6s": sum(3 <= d <= 6 for d in durations),
            "shots_over_6s": sum(d > 6 for d in durations),
        },
        "motion": {
            "shot_counts": dict(motion_counts),
            "shot_percentages": {k: round(v / len(shots) * 100, 2) for k, v in motion_counts.items()},
        },
        "visual": {
            "white_fraction": describe(white),
            "mean_saturation": describe(saturation),
            "significant_colors": describe(colors),
            "black_stroke_width_px_at_source": describe(stroke_samples),
            "dominant_palette": [{"hex": k, "weight": round(v, 4)} for k, v in palette.most_common(16)],
        },
        "shot_atlases": [str(Path(item).relative_to(out_dir)) for item in atlas],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=18.0)
    args = parser.parse_args()
    combined = []
    for path in args.videos:
        out = args.output / path.stem
        out.mkdir(parents=True, exist_ok=True)
        print(f"Analyzing every frame: {path}", flush=True)
        summary = analyze(path, out, args.threshold)
        combined.append(summary)
        print(f"  {summary['frame_count']} frames, {summary['editing']['shot_count']} shots", flush=True)
    (args.output / "combined.json").write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
