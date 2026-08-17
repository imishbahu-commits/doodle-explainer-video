#!/usr/bin/env python3
"""audio_report.py — measure narration like the reference format does.

Reports silence (dead air), loudness, and duration using ffmpeg's built-in
silencedetect + volumedetect — the same analysers professionals use. No new
installs beyond ffmpeg (the repo already ships one).

Reference targets (from references/format-spec.md):
    mean level   -17.5 dBFS
    peak          0.0 dBFS
    natural pauses 0.4-0.8s at section boundaries; dead air > 1.0s is slack

Usage:
    python3 audio_report.py video_or_audio.mp4
    python3 audio_report.py final.mp4 --json
    python3 audio_report.py final.mp4 --tighten out.m4a   # remove dead air >1s
"""

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p


def ffmpeg():
    import shutil
    return shutil.which("ffmpeg") or "ffmpeg"


def duration_of(path):
    p = run([ffmpeg(), "-i", str(path)])
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise SystemExit(f"could not read duration of {path}\n{p.stderr[-800:]}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def silences(path, noise="-35dB", d=0.35):
    p = run([ffmpeg(), "-i", str(path), "-af",
             f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"])
    out = []
    start = None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start:\s*([\d.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", line)
        if m and start is not None:
            out.append({"start": start, "end": float(m.group(1)),
                        "duration": float(m.group(2))})
            start = None
    return out


def loudness(path):
    p = run([ffmpeg(), "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*([-\d.]+) dB", p.stderr)
    peak = re.search(r"max_volume:\s*([-\d.]+) dB", p.stderr)
    return (float(mean.group(1)) if mean else None,
            float(peak.group(1)) if peak else None)


def tighten(path, out, keep=1.0, threshold="-40dB"):
    """silenceremove: keep at most `keep` seconds of each silence, removing
    only dead air beyond it. Section breaths and natural pauses survive."""
    p = run([ffmpeg(), "-y", "-v", "error", "-i", str(path),
             "-af", f"silenceremove=stop_periods=-1:stop_duration={keep}:stop_threshold={threshold}",
             "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out])
    if p.returncode != 0:
        raise SystemExit(p.stderr[-1500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tighten", metavar="OUT", help="write a tightened copy (dead air > 1s removed)")
    args = ap.parse_args()

    path = Path(args.input)
    dur = duration_of(path)
    sil = silences(path)
    mean, peak = loudness(path)

    total_sil = sum(s["duration"] for s in sil)
    dead = [s for s in sil if s["duration"] > 1.0]
    longest = max((s["duration"] for s in sil), default=0.0)
    durs = [s["duration"] for s in sil]
    median = statistics.median(durs) if durs else 0.0

    rep = {
        "file": str(path), "duration": round(dur, 2),
        "silence_count": len(sil), "total_silence": round(total_sil, 2),
        "silence_pct": round(100 * total_sil / dur, 1),
        "median_silence": round(median, 2), "longest_silence": round(longest, 2),
        "dead_air": [{"start": round(s["start"], 2), "duration": round(s["duration"], 2)}
                     for s in dead],
        "mean_db": mean, "peak_db": peak,
    }

    if args.tighten:
        tighten(path, args.tighten)
        new = duration_of(args.tighten)
        rep["tightened"] = {"file": args.tighten, "duration": round(new, 2),
                            "saved": round(dur - new, 2)}

    if args.json:
        print(json.dumps(rep, indent=2))
        return

    print(f"AUDIO REPORT — {path}  ({dur:.1f}s)")
    print(f"  loudness:       mean {mean} dB, peak {peak} dB  "
          f"(reference: -17.5 dB mean, 0.0 peak)")
    print(f"  silences:       {len(sil)} gaps, {total_sil:.1f}s total "
          f"({100*total_sil/dur:.1f}% of runtime)")
    print(f"  median pause:   {median:.2f}s  (format: 0.4-0.8s at section ends)")
    print(f"  longest pause:  {longest:.2f}s")
    if dead:
        print(f"  dead air >1s:   {len(dead)} gap(s) — slack:")
        for s in dead:
            print(f"                  at {s['start']:6.1f}s for {s['duration']:.1f}s")
    else:
        print("  dead air >1s:   none — pacing is tight")
    if mean is not None and mean < -22:
        print("  ⚠ narration is quiet vs reference — build script normalises by default;")
        print("    re-render without --no-normalize, or run loudnorm again.")
    if mean is not None and mean > -12:
        print("  ⚠ narration is hotter than the reference. Check peak clipping.")
    if args.tighten:
        print(f"  tightened copy: {args.tighten}  {new:.1f}s "
              f"(saved {dur - new:.1f}s of dead air)")


if __name__ == "__main__":
    main()
