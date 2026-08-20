#!/usr/bin/env python3
"""Assemble the Dinzo 16:9 video from per-beat images + per-beat narration.

One beat = one image = one audio clip. Each image is held for exactly its
audio clip's duration (+ a small breath), hard cuts between beats. Dinzo
"Why It Sucks to Be Born as..." format: full-frame landscape doodles, deadpan
narration, no music, no captions.

Usage:
    python3 make_video.py [start] [end] [-o out.mp4]
"""
import argparse
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, FPS = 1376, 768, 30   # matches the crocodile assets
GAP = 0.25                  # breath appended after each beat


def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{p.stderr[-2000:]}")
    return p.stdout


def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", path]).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=int, nargs="?", default=1)
    ap.add_argument("end", type=int, nargs="?")
    ap.add_argument("-o", "--output", default="part1.mp4")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--gap", type=float, default=GAP)
    args = ap.parse_args()

    assets = HERE / "assets"
    audio = HERE / "audio"
    beats = sorted(int(p.stem[4:]) for p in assets.glob("beat*.png"))
    end = args.end or max(beats)
    beats = [b for b in beats
             if args.start <= b <= end and (audio / f"beat{b:02d}.mp3").exists()]
    if not beats:
        raise SystemExit("no beat images with matching audio found")

    work = HERE / "work"
    work.mkdir(exist_ok=True)
    parts, vlist = [], []
    for i, b in enumerate(beats, 1):
        img = assets / f"beat{b:02d}.png"
        aud = audio / f"beat{b:02d}.mp3"
        padded = work / f"pad_{i:03d}.m4a"
        run(["ffmpeg", "-y", "-v", "error", "-i", aud,
             "-af", f"apad=pad_dur={args.gap},aresample=44100",
             "-ac", "2", "-c:a", "aac", "-b:a", "160k", padded])
        parts.append(padded)
        d = dur(padded)
        vlist.append(f"file '{img.as_posix()}'")
        vlist.append(f"duration {d:.4f}")
        print(f"beat {b:>3}: image {d:5.2f}s")

    vlist.append(f"file '{(assets / f'beat{beats[-1]:02d}.png').as_posix()}'")

    listing = work / "audio.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    narration = work / "narration.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c", "copy", narration])
    levelled = work / "narration_norm.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-i", narration,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", levelled])

    vfile = work / "video.txt"
    vfile.write_text("\n".join(vlist) + "\n", encoding="utf-8")
    out = HERE / args.output
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vfile,
         "-i", levelled,
         "-vf", f"scale={W}:{H},fps={args.fps},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, "
          f"{len(beats)} beats, ~{sum(dur(p) for p in parts):.0f}s)")


if __name__ == "__main__":
    main()
