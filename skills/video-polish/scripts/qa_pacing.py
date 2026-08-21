#!/usr/bin/env python3
"""Measure flattened visual-change cadence against the Paint Explainer corpus.

This detector is deliberately called a visual-change detector: local animation
in a flattened render can look like an edit. Use the scene manifest and manual
spot checks to distinguish hard cuts, source swaps, and in-shot motion.
"""

import argparse
import json
import re
import shutil
import statistics
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RULES_PATH = REPO / "references" / "paint-explainer-analysis-4v" / "style_rules.json"
EDITING_RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))["editing"]
THRESHOLD = 1.5
MIN_EVENT_GAP = float(EDITING_RULES["shot_duration_seconds"]["min"])


def ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def ffprobe():
    return shutil.which("ffprobe") or "ffprobe"


def probe(path):
    process = subprocess.run(
        [ffprobe(), "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=avg_frame_rate:format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if process.returncode == 0:
        try:
            data = json.loads(process.stdout)
            if isinstance(data, dict):
                duration = float(data["format"]["duration"])
                numerator, denominator = data["streams"][0]["avg_frame_rate"].split("/")
                fps = float(numerator) / max(float(denominator), 1.0)
                return duration, fps
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    # Some repository environments expose a duration-only ffprobe shim.
    # Parse both duration and fps from ffmpeg in that case.
    process = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", process.stderr)
    fps_match = re.search(r"(?:,|\s)(\d+(?:\.\d+)?)\s+fps(?:,|\s)", process.stderr)
    if not match:
        raise SystemExit("could not read video duration/frame rate")
    hours, minutes, seconds = match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    fps = float(fps_match.group(1)) if fps_match else 30.0
    return duration, fps


def frame_means(path, fps):
    # Keep RGB so equal-luminance palette cuts (for example red to dark green)
    # are not lost by grayscale conversion.
    frame_bytes = 16 * 16 * 3
    process = subprocess.Popen(
        [ffmpeg(), "-i", str(path), "-vf", "scale=16:16:flags=area,format=rgb24",
         "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    index = 0
    while True:
        buffer = process.stdout.read(frame_bytes)
        if len(buffer) < frame_bytes:
            break
        yield index / fps, buffer
        index += 1
    process.stdout.close()
    process.wait()


def visual_event_times(path, fps):
    reference = None
    segment_start = None
    starts = []
    for timestamp, buffer in frame_means(path, fps):
        if reference is None:
            reference, segment_start = buffer, timestamp
            continue
        difference = sum(abs(a - b) for a, b in zip(reference, buffer)) / len(buffer)
        if difference > THRESHOLD and timestamp - segment_start >= MIN_EVENT_GAP:
            starts.append(segment_start)
            reference, segment_start = buffer, timestamp
    if reference is not None:
        starts.append(segment_start)
    return starts


def manifest_counts(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if "sections" in manifest:
        beats = [beat for section in manifest["sections"] for beat in section.get("beats", [])]
        events = [event for section in manifest["sections"] for event in section.get("visual_events", [])]
    else:
        beats = manifest.get("beats", [])
        events = manifest.get("visual_events", [])
    if not events and beats:
        events = [beat for beat in beats if beat.get("event_type") not in (None, "hold")]
    return {"beat_count": len(beats), "explicit_visual_event_count": len(events)}


def percentage(predicate, values):
    return round(100 * sum(predicate(value) for value in values) / max(1, len(values)), 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--manifest", help="report beat and explicit visual-event counts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    duration, fps = probe(args.video)
    starts = visual_event_times(args.video, fps)
    holds = [round(end - start, 4) for start, end in zip(starts, starts[1:])]
    if starts:
        holds.append(round(duration - starts[-1], 4))

    median = statistics.median(holds) if holds else 0.0
    mean = statistics.mean(holds) if holds else 0.0
    shortest = min(holds) if holds else 0.0
    longest = max(holds) if holds else 0.0
    distribution = {
        "under_1s": percentage(lambda value: value < 1.0, holds),
        "between_1_and_6s": percentage(lambda value: 1.0 <= value <= 6.0, holds),
        "over_10s": percentage(lambda value: value > 10.0, holds),
    }
    extreme_short = [
        {"segment": index + 1, "duration": hold}
        for index, hold in enumerate(holds) if hold < 0.2
    ]
    corpus_max = float(EDITING_RULES["shot_duration_seconds"]["max"])
    extreme_long = [
        {"segment": index + 1, "duration": hold}
        for index, hold in enumerate(holds) if hold > corpus_max + 0.1
    ]
    median_ok = 2.3 <= median <= 3.1

    report = {
        "file": args.video,
        "duration_seconds": round(duration, 3),
        "fps": round(fps, 4),
        "editing": {
            "detected_visual_change_segments": len(holds),
            "visual_change_times_seconds": [round(value, 4) for value in starts],
            "shot_duration_seconds": {
                "median": round(median, 4),
                "mean": round(mean, 4),
                "min": round(shortest, 4),
                "max": round(longest, 4),
            },
            "distribution_pct": distribution,
        },
        "targets": {
            "median_shot_seconds": [2.3, 3.1],
            "corpus_distribution_pct": EDITING_RULES["distribution_pct"],
        },
        "extreme_short_segments": extreme_short,
        "extreme_long_segments": extreme_long,
        "detector_note": (
            "Flattened abrupt visual changes are not guaranteed semantic cuts; "
            "spot-check local animation and compare the authored event manifest."
        ),
        "ok": median_ok and not extreme_short and not extreme_long,
    }
    if args.manifest:
        report["manifest"] = manifest_counts(args.manifest)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"PACING CHECK — {args.video} ({duration:.1f}s @ {fps:.3f} fps)")
    print(f"  detected visual-change segments: {len(holds)}")
    print(
        f"  durations: median {median:.2f}s | mean {mean:.2f}s | "
        f"range {shortest:.2f}–{longest:.2f}s"
    )
    print("  target median: 2.3–3.1s (newest reference 2.50s)")
    print(
        "  distribution: "
        f"<1s {distribution['under_1s']:.2f}% | "
        f"1–6s {distribution['between_1_and_6s']:.2f}% | "
        f">10s {distribution['over_10s']:.2f}%"
    )
    print("  " + ("PASS" if report["ok"] else "REVIEW"))
    print("  note: flattened local motion can trigger this detector; spot-check events")
    if args.manifest:
        counts = report["manifest"]
        print(
            f"  manifest: {counts['beat_count']} beats, "
            f"{counts['explicit_visual_event_count']} explicit visual events"
        )
        print("  beat count is not expected to equal cut/event count")


if __name__ == "__main__":
    main()
