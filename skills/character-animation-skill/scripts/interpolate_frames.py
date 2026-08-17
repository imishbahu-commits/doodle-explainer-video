#!/usr/bin/env python3
"""
Motion-interpolate a folder of frames into a smoother, longer sequence using
ffmpeg's `minterpolate` (motion-compensated in-betweening). This is the reliable
way to add fluidity: generate a handful of consistent keyframes, then synthesize
the smooth in-betweens here instead of asking the image model for dozens of
near-identical frames it can't render consistently.

Best for SMALL, smooth motion (idle, breathing, blink, gentle sway). It will smear
on large/fast motion — keep the per-keyframe change modest.

ffmpeg can't motion-estimate an alpha channel, so transparent input frames are
composited onto a chroma color, interpolated, then keyed back to transparency.
The sequence is treated as a seamless loop (the first frame is appended so the
last→first transition is interpolated too).

Usage:
  python3 interpolate_frames.py IN_DIR OUT_DIR --factor 4 --chroma "#00B140"
"""
import argparse, math, shutil, subprocess, sys, tempfile
from pathlib import Path


def magick(*a):
    subprocess.run(["magick", *[str(x) for x in a]], check=True)


def wh(path):
    out = subprocess.check_output(["magick", "identify", "-format", "%w %h", str(path)])
    w, h = out.decode().split()
    return int(w), int(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--factor", type=int, default=4, help="frame multiplier (>=2)")
    ap.add_argument("--chroma", default="#00B140")
    ap.add_argument("--fuzz", type=float, default=18.0)
    ap.add_argument("--base-fps", type=int, default=12,
                    help="nominal input fps; output fps = base-fps * factor")
    ap.add_argument("--max-width", type=int, default=600,
                    help="downscale to this width before interpolating — ffmpeg's "
                         "minterpolate silently truncates output at large sizes, so "
                         "keep this modest (the display size is usually smaller anyway)")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ERROR: ffmpeg is required.")
    frames = sorted(Path(args.in_dir).glob("*.png"))
    if len(frames) < 4:
        sys.exit("ERROR: need at least 4 input frames for motion interpolation.")
    W, H = wh(frames[0])
    if W > args.max_width:
        H = round(H * args.max_width / W)
        W = args.max_width
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="interp_"))
    try:
        # 1. composite each frame onto chroma (at working size); append first frame
        #    to close the loop
        seq = frames + [frames[0]]
        for i, f in enumerate(seq):
            magick("-size", f"{W}x{H}", f"xc:{args.chroma}",
                   "(", f, "-resize", f"{W}x{H}", ")",
                   "-gravity", "center", "-compose", "over", "-composite",
                   tmp / f"g{i:04d}.png")
        # 2. motion-compensated interpolation
        out_fps = args.base_fps * args.factor
        # NOTE: keep the minterpolate options minimal — me_mode=bidir / vsbmc=1
        # error out on large frames (only a handful survive). mci + obmc is robust.
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(args.base_fps), "-i", str(tmp / "g%04d.png"),
            "-vf", f"minterpolate=fps={out_fps}:mi_mode=mci:mc_mode=obmc",
            "-loglevel", "error", str(tmp / "m%04d.png"),
        ], check=True)
        interp = sorted(tmp.glob("m*.png"))
        # drop the final frame(s) that duplicate the appended wrap (keeps the loop
        # seamless without a repeated frame)
        if len(interp) > args.factor:
            interp = interp[:-1]
        # 3. key the chroma back out (+ green-spill suppression), write final frames
        for i, m in enumerate(interp):
            magick(m, "-fuzz", f"{args.fuzz}%", "-transparent", args.chroma,
                   "-channel", "G", "-fx", "min(g,(r+b)/2.0)", "+channel",
                   out_dir / f"frame_{i:04d}.png")
        print(f"interpolated {len(frames)} -> {len(interp)} frames -> {out_dir}")
        print(f"  factor x{args.factor}, {W}x{H} per frame")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
