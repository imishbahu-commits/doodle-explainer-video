#!/usr/bin/env python3
"""Measure YouTube video audio loudness for retention diagnosis.

Downloads the audio stream via yt-dlp and runs FFmpeg loudnorm in
analysis mode to report integrated LUFS, true peak, and loudness range.
YouTube normalizes to -14 LUFS; videos measurably under -16 LUFS feel
quiet on playback and correlate with lower retention.

Usage:
    python audio_loudness.py <video-url-or-id>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    args = parser.parse_args()

    audio_path = Path(f"/tmp/yt_loud_{abs(hash(args.video))}.m4a")

    dl = subprocess.run(
        [
            "yt-dlp",
            "-x",
            "--audio-format", "m4a",
            "-o", str(audio_path),
            "--no-warnings",
            args.video,
        ],
        capture_output=True, text=True,
    )
    if dl.returncode != 0 or not audio_path.exists():
        print(json.dumps({"error": "yt-dlp audio download failed", "stderr": dl.stderr}))
        return 1

    ff = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(audio_path),
            "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )
    # loudnorm prints JSON to stderr
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", ff.stderr, re.DOTALL)
    if not m:
        print(json.dumps({"error": "Could not parse loudnorm output", "stderr": ff.stderr[-2000:]}))
        return 1
    loud = json.loads(m.group(0))

    input_i = float(loud.get("input_i", "0"))
    input_tp = float(loud.get("input_tp", "0"))
    input_lra = float(loud.get("input_lra", "0"))

    verdict = []
    if input_i < -16:
        verdict.append(f"QUIET — integrated loudness {input_i:.1f} LUFS is below -16; viewers will hunt for volume")
    elif input_i > -12:
        verdict.append(f"LOUD — integrated loudness {input_i:.1f} LUFS will be normalized down by YouTube (-14 target)")
    else:
        verdict.append(f"OK — integrated loudness {input_i:.1f} LUFS is within YouTube normalization band")

    if input_tp > -1:
        verdict.append(f"CLIPPING risk — true peak {input_tp:.2f} dBTP exceeds -1")
    if input_lra > 15:
        verdict.append(f"HIGH dynamic range ({input_lra:.1f} LU) — viewers will volume-hunt")
    elif input_lra < 4:
        verdict.append(f"OVER-COMPRESSED ({input_lra:.1f} LU) — audio feels lifeless")

    audio_path.unlink(missing_ok=True)

    json.dump(
        {
            "integrated_lufs": input_i,
            "true_peak_dbtp": input_tp,
            "loudness_range_lu": input_lra,
            "verdict": verdict,
            "raw": loud,
        },
        sys.stdout,
        indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
