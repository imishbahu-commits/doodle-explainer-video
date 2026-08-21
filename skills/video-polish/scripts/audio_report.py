#!/usr/bin/env python3
"""Measure Paint Explainer mix loudness, silence, and chapter breaths.

Current target: -20.7 to -20.6 LUFS, true peak <= -2.3 dBTP, LRA 1.8-3.8 LU,
and intentional chapter breaths around 0.6-0.8 seconds.
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
AUDIO_RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))["audio"]
LUFS_MIN, LUFS_MAX = AUDIO_RULES["target_newest_integrated_lufs_range"]
TRUE_PEAK_MAX = AUDIO_RULES["target_newest_true_peak_dbtp_max"]
LRA_MIN, LRA_MAX = AUDIO_RULES["lra_lu_range"]
BREATH_MIN, BREATH_MAX = AUDIO_RULES["chapter_pause_seconds_target"]


def ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration_of(path):
    p = run([ffmpeg(), "-i", str(path)])
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not match:
        raise SystemExit(f"could not read duration of {path}\n{p.stderr[-800:]}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def silences(path, noise="-35dB", duration=0.35):
    p = run([ffmpeg(), "-i", str(path), "-af",
             f"silencedetect=noise={noise}:d={duration}", "-f", "null", "-"])
    output = []
    start = None
    for line in p.stderr.splitlines():
        match = re.search(r"silence_start:\s*([\d.]+)", line)
        if match:
            start = float(match.group(1))
        match = re.search(
            r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", line
        )
        if match and start is not None:
            output.append({
                "start": start,
                "end": float(match.group(1)),
                "duration": float(match.group(2)),
            })
            start = None
    return output


def r128_loudness(path):
    """Run loudnorm in measurement mode and return input EBU R128 values."""
    p = run([
        ffmpeg(), "-hide_banner", "-nostats", "-i", str(path),
        "-af", (
            f"loudnorm=I={(LUFS_MIN + LUFS_MAX) / 2}:TP={TRUE_PEAK_MAX}:"
            f"LRA={(LRA_MIN + LRA_MAX) / 2}:print_format=json"
        ),
        "-f", "null", "-",
    ])
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", p.stderr, flags=re.DOTALL)
    if not blocks:
        raise SystemExit(f"could not parse EBU R128 measurement\n{p.stderr[-1200:]}")
    measured = json.loads(blocks[-1])

    def number(key):
        value = measured.get(key)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return {
        "integrated_lufs": number("input_i"),
        "true_peak_dbfs": number("input_tp"),
        "lra_lu": number("input_lra"),
        "threshold_lufs": number("input_thresh"),
    }


def sample_peak(path):
    p = run([ffmpeg(), "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*([-\d.]+) dB", p.stderr)
    peak = re.search(r"max_volume:\s*([-\d.]+) dB", p.stderr)
    return (
        float(mean.group(1)) if mean else None,
        float(peak.group(1)) if peak else None,
    )


def tighten(path, out, keep=1.0, threshold="-40dB"):
    """Keep at most `keep` seconds of each detected silence.

    This is opt-in because it can remove intentional chapter breaths and alter
    narration-to-picture alignment.
    """
    p = run([
        ffmpeg(), "-y", "-v", "error", "-i", str(path),
        "-af", f"silenceremove=stop_periods=-1:stop_duration={keep}:stop_threshold={threshold}",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(out),
    ])
    if p.returncode != 0:
        raise SystemExit(p.stderr[-1500:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--tighten", metavar="OUT",
        help="opt-in: remove silence beyond 1 s; always remeasure and resync",
    )
    args = parser.parse_args()

    path = Path(args.input)
    duration = duration_of(path)
    silence_rows = silences(path)
    loudness = r128_loudness(path)
    mean_dbfs, sample_peak_dbfs = sample_peak(path)

    silence_total = sum(row["duration"] for row in silence_rows)
    review = [row for row in silence_rows if row["duration"] > 1.0]
    durations = [row["duration"] for row in silence_rows]
    median_pause = statistics.median(durations) if durations else 0.0
    chapter_like = [row for row in silence_rows if BREATH_MIN <= row["duration"] <= BREATH_MAX]

    checks = {
        "integrated_loudness": (
            loudness["integrated_lufs"] is not None
            and LUFS_MIN <= loudness["integrated_lufs"] <= LUFS_MAX
        ),
        "true_peak": (
            loudness["true_peak_dbfs"] is not None
            and loudness["true_peak_dbfs"] <= TRUE_PEAK_MAX
        ),
        "lra": (
            loudness["lra_lu"] is not None
            and LRA_MIN <= loudness["lra_lu"] <= LRA_MAX
        ),
    }
    report = {
        "file": str(path),
        "duration": round(duration, 2),
        "audio": loudness,
        "sample_mean_dbfs": mean_dbfs,
        "sample_peak_dbfs": sample_peak_dbfs,
        "silence_count": len(silence_rows),
        "total_silence_seconds": round(silence_total, 2),
        "silence_pct": round(100 * silence_total / max(duration, 1e-9), 1),
        "median_silence_seconds": round(median_pause, 2),
        "chapter_breath_candidate_count": len(chapter_like),
        "silences_over_1s_for_review": [
            {"start": round(row["start"], 2), "duration": round(row["duration"], 2)}
            for row in review
        ],
        "targets": {
            "integrated_lufs": [LUFS_MIN, LUFS_MAX],
            "true_peak_dbfs_max": TRUE_PEAK_MAX,
            "lra_lu": [LRA_MIN, LRA_MAX],
            "chapter_breath_seconds": [BREATH_MIN, BREATH_MAX],
        },
        "checks": checks,
        "ok": all(checks.values()),
    }

    if args.tighten:
        tighten(path, Path(args.tighten))
        tightened_duration = duration_of(args.tighten)
        report["tightened"] = {
            "file": args.tighten,
            "duration": round(tightened_duration, 2),
            "saved": round(duration - tightened_duration, 2),
            "warning": "remeasure and resync narration-word visual events",
        }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"AUDIO REPORT — {path} ({duration:.1f}s)")
    print(
        f"  EBU R128: {loudness['integrated_lufs']} LUFS | "
        f"{loudness['true_peak_dbfs']} dBTP | LRA {loudness['lra_lu']} LU"
    )
    print(f"  target:   {LUFS_MIN} to {LUFS_MAX} LUFS | ≤{TRUE_PEAK_MAX} dBTP | LRA {LRA_MIN}–{LRA_MAX} LU")
    print(
        f"  pauses:   {len(silence_rows)} gaps, median {median_pause:.2f}s; "
        f"{len(chapter_like)} in {BREATH_MIN}–{BREATH_MAX}s chapter-breath range"
    )
    if review:
        print(f"  review:   {len(review)} silence(s) over 1s (not automatically removed)")
    print("  " + ("PASS" if report["ok"] else "FAIL") + " — " + json.dumps(checks))
    if args.tighten:
        print(f"  tightened: {args.tighten}; remeasure and resync before muxing")


if __name__ == "__main__":
    main()
