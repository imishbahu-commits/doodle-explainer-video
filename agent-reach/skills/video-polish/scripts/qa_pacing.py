#!/usr/bin/env python3
"""qa_pacing.py — verify a finished video's cut cadence against the measured
format spec (references/format-spec.md).

Method: decode every frame, area-average it to 32x32 grayscale (which
cancels the encoder's ±1-2 rounding noise between duplicate stills), then
run-length segment against the current segment's reference frame. A hard
illustration cut jumps the mean pixel difference by orders of magnitude, so
threshold 1.5 separates cuts from noise cleanly. Zero new dependencies —
ffmpeg + Python stdlib only.

Reference cadence:
    median hold   2-3 s
    mean hold     3.4-4.1 s
    longest hold  ~14 s (allowed); anything > 8 s is worth a look

Usage:
    python3 qa_pacing.py final.mp4
    python3 qa_pacing.py final.mp4 --manifest manifest.json   # compare expected beats
    python3 qa_pacing.py final.mp4 --json
"""

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

THRESHOLD = 1.5        # mean |diff| per pixel (0-255) that counts as a cut
MIN_HOLD = 0.4         # seconds between distinct cuts (drops GOP-boundary noise)


def ffmpeg():
    import shutil
    return shutil.which("ffmpeg") or "ffmpeg"


def duration_of(path):
    p = subprocess.run([ffmpeg(), "-i", str(path)],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise SystemExit("could not read duration")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def frame_means(path):
    """Yield (timestamp, 32x32-gray bytes) for every decoded frame."""
    p = subprocess.Popen(
        [ffmpeg(), "-i", str(path),
         "-vf", "scale=32:32:flags=area,format=gray",
         "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    i = 0
    while True:
        buf = p.stdout.read(1024)
        if len(buf) < 1024:
            break
        yield i / 30.0, buf  # assumes 30 fps output like the pipeline renders
        i += 1
    p.stdout.close()
    p.wait()


def cut_times(path):
    ref = None
    seg_start = None
    cuts = []
    for t, buf in frame_means(path):
        if ref is None:
            ref, seg_start = buf, t
            continue
        diff = sum(abs(a - b) for a, b in zip(ref, buf)) / 1024.0
        if diff > THRESHOLD and t - seg_start >= MIN_HOLD:
            cuts.append(seg_start)
            ref, seg_start = buf, t
    if ref is not None:
        cuts.append(seg_start)   # the final segment's start has no later cut
    return cuts


def expected_beats(manifest_path):
    m = json.loads(Path(manifest_path).read_text())
    if "sections" in m:
        return sum(len(s["beats"]) for s in m["sections"])
    if "beats" in m:
        return len(m["beats"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--manifest", help="compare cuts against expected beats")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    dur = duration_of(args.video)
    cuts = cut_times(args.video)
    holds = [round(b - a, 2) for a, b in zip(cuts, cuts[1:])]
    if cuts:
        holds.append(round(dur - cuts[-1], 2))

    n = len(holds)
    median = statistics.median(holds) if holds else 0.0
    mean = statistics.mean(holds) if holds else 0.0
    lo, hi = (max(holds), min(holds)) if holds else (0.0, 0.0)
    fast = [(i + 1, h) for i, h in enumerate(holds) if h < 1.5]
    slack = [(i + 1, h) for i, h in enumerate(holds) if h > 8.0]

    rep = {
        "duration": round(dur, 2), "cuts": n,
        "cut_times": cuts,
        "median_hold": round(median, 2), "mean_hold": round(mean, 2),
        "shortest_hold": hi, "longest_hold": lo,
        "too_fast": fast, "too_slow": slack,
    }

    if args.json:
        print(json.dumps(rep, indent=2))
        return

    print(f"PACING CHECK — {args.video}  ({dur:.1f}s)")
    print(f"  illustration cuts:  {n}")
    print(f"  hold times:         median {median:.2f}s | mean {mean:.2f}s | "
          f"range {hi:.2f}-{lo:.2f}s")
    print(f"  format target:      median 2-3s | mean 3.4-4.1s | longest ~14s")
    if fast:
        print(f"  ⚠ {len(fast)} cut(s) held under 1.5s — reads as flashing:")
        for i, h in fast[:8]:
            print(f"      beat {i:>3}: {h:.2f}s")
    if slack:
        print(f"  ⚠ {len(slack)} cut(s) held over 8s — cutting goes slack:")
        for i, h in slack[:8]:
            print(f"      beat {i:>3}: {h:.2f}s")
    if not fast and not slack:
        print("  ✓ cadence matches the format")

    if args.manifest:
        exp = expected_beats(args.manifest)
        if exp is not None:
            tag = "match ✓" if exp == n else f"MISMATCH — expected {exp}"
            print(f"  manifest beats:     {exp}  ({tag})")
            if exp != n:
                print("      a mismatch usually means images were reused in the")
                print("      manifest or the video was built from a different one.")


if __name__ == "__main__":
    main()
