#!/usr/bin/env python3
"""
Normalize a directory of individually-generated frames (Mode 2) and assemble
them into a clean, transparent sprite-sheet grid — locking scale and position so
the character stays planted in place.

Why: even when each frame is an edit of the same base plate, the model renders
the character at slightly different sizes/heights. This pass keys out the chroma
background, trims each frame, normalizes scale using the LEG-STANCE width (the
most pose-invariant landmark — legs don't move while an arm waves), then plants
every frame on a common feet-baseline, horizontally centered on the body. The
result has no bobbing, no size pulsing, and no clipped limbs.

Output: a transparent grid PNG you then feed to spritesheet_to_animation.py with
--keep-bg.

Usage:
  python3 frames_to_sheet.py frames/ --cols 4 --rows 4 \
      --bg-color "#00B140" --out sheet.png
"""
import argparse, math, statistics, subprocess, sys, tempfile, shutil
from pathlib import Path


def sh(*a):
    return subprocess.check_output(["magick", *[str(x) for x in a]]).decode().strip()


def run(*a):
    subprocess.run(["magick", *[str(x) for x in a]], check=True)


def bbox(path):
    """content bounding box (w,h,x,y) of the non-transparent area."""
    out = sh(path, "-format", "%@", "info:")
    wh, x, y = out.split("+")
    w, h = wh.split("x")
    return int(w), int(h), int(x), int(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames_dir")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--bg-color", dest="bg_color", default="#00B140")
    ap.add_argument("--fuzz", type=float, default=18.0)
    ap.add_argument("--stance-band", type=float, default=0.18,
                    help="fraction of height (from the feet up) used as the "
                         "scale-normalization landmark")
    ap.add_argument("--out", default="sheet.png")
    ap.add_argument("--emit-frames", dest="emit_frames", default=None,
                    help="also write the individual normalized transparent frames "
                         "to this directory (for a downstream interpolation pass)")
    args = ap.parse_args()

    frames = sorted(Path(args.frames_dir).glob("frame_*.png"))
    if not frames:
        sys.exit(f"no frame_*.png in {args.frames_dir}")
    n = args.cols * args.rows
    if len(frames) != n:
        print(f"warning: {len(frames)} frames but grid is {args.cols}x{args.rows}={n}",
              file=sys.stderr)

    tmp = Path(tempfile.mkdtemp(prefix="f2s_"))
    try:
        # pass 1: key + trim each frame, measure tight box and leg-stance width
        meta = []
        for i, f in enumerate(frames):
            keyed = tmp / f"k{i:02d}.png"
            # global chroma key + green-spill suppression, then trim to content
            run(f, "-fuzz", f"{args.fuzz}%", "-transparent", args.bg_color,
                "-channel", "G", "-fx", "min(g,(r+b)/2.0)", "+channel",
                "-trim", "+repage", keyed)
            tw, th, _, _ = bbox(keyed)
            band_h = max(1, int(th * args.stance_band))
            band = tmp / f"b{i:02d}.png"
            run(keyed, "-gravity", "South", "-crop", f"{tw}x{band_h}+0+0", "+repage", band)
            bw, bh, bx, by = bbox(band)
            meta.append({"keyed": keyed, "tw": tw, "th": th,
                         "bw": bw, "bcx": bx + bw / 2.0})

        target_bw = statistics.median(m["bw"] for m in meta)
        for m in meta:
            m["scale"] = target_bw / m["bw"]
            m["sw"] = m["tw"] * m["scale"]
            m["sh"] = m["th"] * m["scale"]
            m["bcx_s"] = m["bcx"] * m["scale"]

        # common canvas big enough to hold every scaled frame, centered on body
        pad = int(0.05 * max(m["sh"] for m in meta))
        left = max(m["bcx_s"] for m in meta)
        right = max(m["sw"] - m["bcx_s"] for m in meta)
        half = max(left, right)
        CW = int(2 * half + 2 * pad); CW += CW % 2
        CH = int(max(m["sh"] for m in meta) + 2 * pad); CH += CH % 2
        baseline = CH - pad

        norm = []
        for i, m in enumerate(meta):
            scaled = tmp / f"s{i:02d}.png"
            run(m["keyed"], "-resize", f"{m['scale']*100:.4f}%", scaled)
            x_off = round(CW / 2 - m["bcx_s"])
            y_off = round(baseline - m["sh"])
            out = tmp / f"n{i:02d}.png"
            run("-size", f"{CW}x{CH}", "xc:none", scaled,
                "-geometry", f"+{x_off}+{y_off}", "-compose", "over", "-composite", out)
            norm.append(out)

        # optionally emit the individual normalized (transparent) frames — useful
        # for a downstream interpolation pass before assembling.
        if args.emit_frames:
            edir = Path(args.emit_frames)
            edir.mkdir(parents=True, exist_ok=True)
            for i, p in enumerate(norm):
                shutil.copy(p, edir / f"frame_{i:03d}.png")
            print(f"emitted {len(norm)} normalized frames -> {edir} ({CW}x{CH})")

        # montage into an exact grid (equal cells, no spacing)
        run("montage", *norm, "-tile", f"{args.cols}x{args.rows}",
            "-geometry", "+0+0", "-background", "none", args.out)
        print(f"sheet: {args.out}  ({CW}x{CH} cells, {args.cols}x{args.rows})")
        print(f"  -> convert with: spritesheet_to_animation.py {args.out} "
              f"--keep-bg --cols {args.cols} --rows {args.rows}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
