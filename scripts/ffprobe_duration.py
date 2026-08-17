#!/usr/bin/env python3
"""Minimal ffprobe duration compatibility fallback for the vertical renderer."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

if any(arg in ("-version", "--version") for arg in sys.argv[1:]):
    print("ffprobe duration compatibility shim")
    raise SystemExit(0)
if len(sys.argv) < 2:
    print("usage: ffprobe [options] input", file=sys.stderr)
    raise SystemExit(1)
ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    print("ffmpeg not found", file=sys.stderr)
    raise SystemExit(1)
proc = subprocess.run([ffmpeg, "-i", sys.argv[-1]], capture_output=True, text=True)
match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
if not match:
    print(proc.stderr[-2000:], file=sys.stderr)
    raise SystemExit(1)
hours, minutes, seconds = match.groups()
print(int(hours) * 3600 + int(minutes) * 60 + float(seconds))
