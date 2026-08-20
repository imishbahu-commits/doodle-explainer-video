#!/usr/bin/env python3
"""Assemble the Dinzo-style anglerfish video, part by part.

Dinzo format: 16:9 landscape, full-frame hand-drawn doodle, hard cuts,
one image per narration beat, no music, no captions, 30 fps.

Each beat = assets/beatNN.png + audio/beatNN.mp3. Labels are drawn by the
image generator (this script only fits/crops and sharpens).

Usage:
  python3 build.py part 1        # render projects/dinzo-anglerfish/parts/part01.mp4
  python3 build.py final         # concat all rendered parts -> final.mp4
  python3 build.py all           # render every part, then final
"""

import json
import os
import re
import shutil
import subprocess
import sys

from mutagen.mp3 import MP3
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
AUDIO = os.path.join(ROOT, "audio")
PARTS = os.path.join(ROOT, "parts")
WORK = os.path.join(ROOT, "build_work")
BEATS = json.load(open(os.path.join(ROOT, "beats.json")))

FFMPEG = shutil.which("ffmpeg") or "/home/user/.local/bin/ffmpeg"
W, H, FPS = 1920, 1080, 30
TAIL = 0.25  # breath after each beat


def audio_duration(path):
    return MP3(path).info.length


def img_for(bid):
    return os.path.join(ASSETS, f"beat{bid:02d}.png")


def aud_for(bid):
    return os.path.join(AUDIO, f"beat{bid:02d}.mp3")


def beats_of(part):
    return [b for b in BEATS if b["part"] == part]


def fit_cover(img, w=W, h=H):
    """Scale + centre-crop to exactly w x h (16:9)."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(round(iw * scale)), int(round(ih * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def prepare_frame(b):
    """1920x1080 frame for a beat (fit + light sharpen)."""
    out = os.path.join(WORK, f"frame{b['id']:03d}.png")
    img = Image.open(img_for(b["id"])).convert("RGB")
    img = fit_cover(img)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))
    img.save(out, "PNG")
    return out


def build_part(n):
    beats = beats_of(n)
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(PARTS, exist_ok=True)
    clips = []
    for b in beats:
        bid = b["id"]
        if not os.path.isfile(img_for(bid)):
            print(f"  skip beat {bid}: missing beat{bid:02d}.png")
            continue
        if not os.path.isfile(aud_for(bid)):
            print(f"  skip beat {bid}: missing beat{bid:02d}.mp3")
            continue
        frame = prepare_frame(b)
        dur = audio_duration(aud_for(bid)) + TAIL
        clip = os.path.join(WORK, f"clip{bid:03d}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", frame,
            "-i", aud_for(bid),
            "-t", f"{dur:.3f}",
            "-af", "apad",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-movflags", "+faststart",
            "-shortest",
            clip,
        ]
        run(cmd)
        clips.append(clip)
    if not clips:
        print(f"part {n}: nothing to render")
        return
    listfile = os.path.join(WORK, f"part{n:02d}.txt")
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    out = os.path.join(PARTS, f"part{n:02d}.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"part {n}: {len(clips)} beats -> {out}")


def build_final():
    parts = sorted(p for p in os.listdir(PARTS) if p.startswith("part") and p.endswith(".mp4"))
    if not parts:
        print("no parts yet")
        return
    listfile = os.path.join(WORK, "final.txt")
    with open(listfile, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.join(PARTS, p)}'\n")
    out = os.path.join(ROOT, "final.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    d = subprocess.run([FFMPEG, "-i", out, "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"time=(\d+:\d+:\d+\.\d+)", d)
    print(f"final: {out}  ({m.group(1) if m else '?'})")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg failed:", " ".join(cmd[:6]), "...")
        print(r.stderr[-2000:])
        sys.exit(1)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "part":
        build_part(int(sys.argv[2]))
    elif mode == "final":
        build_final()
    else:
        for n in sorted({b["part"] for b in BEATS}):
            build_part(n)
        build_final()
