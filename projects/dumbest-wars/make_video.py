#!/usr/bin/env python3
"""Assemble Dumbest Wars Part 1: 10 beats, one image per beat, each image held
for exactly its own narration clip (+ breath), hard cuts. Locked camera."""

import argparse
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 30
GAP = 0.22


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
    ap.add_argument("-o", "--output", default="dumbest_wars_part1.mp4")
    args = ap.parse_args()
    assets, audio, work = HERE / "assets", HERE / "audio", HERE / "work"
    work.mkdir(exist_ok=True)
    beats = sorted(int(p.stem[4:]) for p in assets.glob("beat*.png") if (audio / f"beat{p.stem[4:]}.mp3").exists())
    if not beats:
        raise SystemExit("no beat images with matching audio")

    parts, vlist = [], []
    for i, b in enumerate(beats, 1):
        img, aud = assets / f"beat{b:02d}.png", audio / f"beat{b:02d}.mp3"
        pad = work / f"pad{i:03d}.m4a"
        run(["ffmpeg", "-y", "-v", "error", "-i", aud,
             "-af", f"apad=pad_dur={GAP},aresample=44100", "-ac", "2",
             "-c:a", "aac", "-b:a", "160k", pad])
        d = dur(pad)
        parts.append(pad)
        vlist.append(f"file '{img.as_posix()}'")
        vlist.append(f"duration {d:.4f}")
        print(f"beat {b:>2}: image {d:5.2f}s")
    vlist.append(f"file '{(assets / f'beat{beats[-1]:02d}.png').as_posix()}'")

    (work / "video.txt").write_text("\n".join(vlist) + "\n", encoding="utf-8")
    (work / "audio.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    audioall = work / "narration.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i",
         work / "audio.txt", "-c", "copy", audioall])
    norm = work / "narration_norm.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-i", audioall,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", norm])
    out = HERE / args.output
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", work / "video.txt",
         "-i", norm,
         "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size/1e6:.1f} MB, {len(beats)} beats, ~{sum(dur(p) for p in parts):.0f}s)")


if __name__ == "__main__":
    main()
