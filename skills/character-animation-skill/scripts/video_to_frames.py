#!/usr/bin/env python3
"""Extract a time range from a video into a folder of PNG frames (Path C).

Turns an existing motion clip — a rendered animation, a screen recording, a
generated video (e.g. an `hf_*.mp4`) — into the per-frame input the rest of the
skill expects. Pull a range, optionally resample the frame rate and rescale,
then key the background with `remove_bg_ml.py` (the subject in a real video is
rarely separable by color), montage, and finish with
`spritesheet_to_animation.py --keep-bg`.

Frames keep their true position in the clip (no re-centering), so motion that
moves through the frame — a character flying in, a camera pan — is preserved.

Usage:
  # first 2 seconds, at the source fps, scaled to 800px square
  python3 video_to_frames.py clip.mp4 frames_raw/ --start 0 --duration 2 --size 800
  # a slice from 1.5s to 3.0s, resampled to 24 fps
  python3 video_to_frames.py clip.mp4 frames_raw/ --start 1.5 --end 3.0 --fps 24

Prints the extracted frame count and suggests grid layouts (cols x rows) for the
montage step.
"""
import argparse, shutil, subprocess, sys
from pathlib import Path


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-show_entries", "format=duration", "-of", "default=nw=1", str(path),
    ]).decode()
    info = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k] = v
    return info


def grid_suggestions(n):
    out = []
    for cols in range(4, 13):
        if n % cols == 0:
            out.append(f"{cols}x{n // cols}")
    return out or [f"(montage {n} frames into any cols×rows >= {n})"]


def main():
    ap = argparse.ArgumentParser(description="Video -> folder of PNG frames.")
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--start", type=float, default=0.0, help="start time (seconds)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--duration", type=float, default=None, help="length (seconds)")
    g.add_argument("--end", type=float, default=None, help="end time (seconds)")
    ap.add_argument("--fps", type=float, default=None,
                    help="resample to this fps (default: keep source fps)")
    ap.add_argument("--size", type=int, default=None,
                    help="scale to SIZE x SIZE (square). Omit to keep source size")
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ERROR: ffmpeg/ffprobe are required.")
    video = Path(args.video)
    if not video.exists():
        sys.exit(f"ERROR: video not found: {video}")

    info = probe(video)
    rfr = info.get("r_frame_rate", "0/1")
    num, den = (rfr.split("/") + ["1"])[:2]
    src_fps = float(num) / float(den) if float(den) else 0.0
    sys.stderr.write(f"source: {info.get('width')}x{info.get('height')} "
                     f"@ {src_fps:.3f} fps, {info.get('duration','?')}s\n")

    out_dir = Path(args.out_dir)
    if out_dir.exists():
        for p in out_dir.glob("f_*.png"):
            p.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    vf = []
    if args.fps:
        vf.append(f"fps={args.fps}")
    if args.size:
        vf.append(f"scale={args.size}:{args.size}")

    cmd = ["ffmpeg", "-y", "-ss", str(args.start), "-i", str(video)]
    if args.end is not None:
        cmd += ["-to", str(max(0.0, args.end - args.start))]
    elif args.duration is not None:
        cmd += ["-t", str(args.duration)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-fps_mode", "passthrough", "-start_number", "0",
            str(out_dir / "f_%03d.png")]
    subprocess.run(cmd, check=True)

    frames = sorted(out_dir.glob("f_*.png"))
    n = len(frames)
    eff_fps = args.fps or src_fps
    print(f"extracted {n} frames -> {out_dir}")
    if eff_fps:
        print(f"playback at {eff_fps:.3g} fps reproduces the clip's original speed "
              f"(loop = {n/eff_fps:.2f}s)")
    print(f"grid options for montage: {', '.join(grid_suggestions(n))}")


if __name__ == "__main__":
    main()
