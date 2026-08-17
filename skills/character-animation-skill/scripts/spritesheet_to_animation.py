#!/usr/bin/env python3
"""
Convert a sprite sheet (a grid of animation frames) into a looping, transparent
animation in three formats:
  - <name>.svg   self-contained animated SVG (embedded WebP, SMIL frame stepping)
  - <name>.webp  animated WebP (true alpha)
  - <name>.gif   animated GIF (universal)
plus <name>-sheet.png, the cleaned transparent sprite sheet.

The frames are read left-to-right, top-to-bottom. By default the white
background is removed to transparency using a connected-components key that
keeps the subject (and its bright specular highlights) while clearing the
background AND the white trapped between limbs.

Requires ImageMagick 7 (`magick`).

Usage:
  python3 spritesheet_to_animation.py SHEET.png --rows 6 --cols 6 \
      --out-dir . --name octopus --fps 12

Key options:
  --rows / --cols      grid layout (default 6x6)
  --fps                playback frames per second (default 12)
  --label-crop FRAC    fraction of each cell's HEIGHT to hide at the bottom,
                       for sheets that print a caption under each frame
                       (e.g. 0.09). Default 0 (clean generated sheets).
  --display-cell PX    per-frame size of the embedded image (default 400).
                       Controls SVG/WebP file size vs. crispness.
  --keep-bg            do NOT remove the background (leave it as-is).
  --flood-fuzz N       white-match tolerance for the bg mask (default 12).
  --white-key N        tight pure-white key for trapped slivers (default 3).
  --min-region FRAC    white blobs smaller than FRAC*pixels are treated as
                       subject highlights and kept (default 0.00009).
  --webp-quality N     embedded/animated webp quality (default 82).
  --gif-max PX         longest side of the GIF preview (default 480).
"""
import argparse, base64, shutil, subprocess, sys, tempfile
from pathlib import Path


def run(cmd):
    subprocess.run(cmd, check=True)


def magick(*args):
    run(["magick", *[str(a) for a in args]])


def identify_wh(path):
    out = subprocess.check_output(["magick", "identify", "-format", "%w %h", str(path)])
    w, h = out.decode().split()
    return int(w), int(h)


def bounds(total, n):
    """Evenly distributed integer cut points 0..total into n cells."""
    return [round(i * total / n) for i in range(n + 1)]


def _is_white(color):
    return color.strip().lower() in ("white", "#fff", "#ffffff", "rgb(255,255,255)")


def remove_background(src, dst, flood_fuzz, white_key, min_region, bg_color="white"):
    if not _is_white(bg_color):
        # Chroma background (e.g. green for a white/light subject): the bg color
        # is absent from the subject, so a single global color key cleanly clears
        # the background AND any gaps between limbs, while the subject's own
        # whites/highlights survive. Then suppress green spill on the edges.
        magick(
            src,
            "-fuzz", f"{flood_fuzz}%", "-transparent", bg_color,
            "-channel", "G", "-fx", "min(g,(r+b)/2.0)", "+channel",
            dst,
        )
        return
    w, h = identify_wh(src)
    area = max(200, round(w * h * min_region))
    # White background: the subject may itself contain white, so we can't key by
    # color alone. Build a mask of LARGE white regions (background + gaps between
    # limbs), keep small white blobs (specular highlights), invert to alpha, then
    # a tight pure-white key cleans up leftover slivers.
    magick(
        src,
        "(", "+clone",
        "-fuzz", f"{flood_fuzz}%", "-fill", "white", "-opaque", "white",
        "-fill", "black", "+opaque", "white",
        "-define", f"connected-components:area-threshold={area}",
        "-define", "connected-components:mean-color=true",
        "-connected-components", "8",
        "-threshold", "50%", "-negate", ")",
        "-alpha", "off", "-compose", "CopyOpacity", "-composite",
        "-fuzz", f"{white_key}%", "-transparent", "white",
        dst,
    )


def build_svg(webp_path, cols, rows, cell_w, cell_h, vp_w, vp_h, fps, out_svg,
              durations=None):
    b64 = base64.b64encode(Path(webp_path).read_bytes()).decode()
    sheet = cell_w * cols
    sheet_h = cell_h * rows
    n = cols * rows
    vals = ";".join(f"{-(k % cols) * cell_w} {-(k // cols) * cell_h}" for k in range(n))
    # Variable per-frame timing (durations in seconds) is what stops a loop from
    # feeling mechanical — hold anticipation/apex/settle frames longer, run the
    # mid-action frames faster. Implemented via SMIL keyTimes.
    if durations:
        total = sum(durations)
        cum, kts = 0.0, []
        for d in durations:
            kts.append(f"{cum / total:.6g}")
            cum += d
        keytimes = f'\n        keyTimes="{";".join(kts)}"'
        dur = round(total, 4)
    else:
        dur = round(n / fps, 4)
        keytimes = ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{vp_w}" height="{vp_h}" viewBox="0 0 {vp_w} {vp_h}" role="img" aria-label="Animated character">
  <title>Animated character ({n}-frame loop)</title>
  <defs><clipPath id="vp"><rect x="0" y="0" width="{vp_w}" height="{vp_h}"/></clipPath></defs>
  <g clip-path="url(#vp)">
    <image width="{sheet}" height="{sheet_h}" image-rendering="auto"
           href="data:image/webp;base64,{b64}">
      <animateTransform attributeName="transform" type="translate"
        calcMode="discrete" repeatCount="indefinite" dur="{dur}s"{keytimes}
        values="{vals}"/>
    </image>
  </g>
</svg>
'''
    Path(out_svg).write_text(svg)
    return len(svg)


def main():
    ap = argparse.ArgumentParser(description="Sprite sheet -> animated SVG/WebP/GIF.")
    ap.add_argument("sheet")
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--name", default="animation")
    ap.add_argument("--fps", type=float, default=12.0)
    ap.add_argument("--label-crop", type=float, default=0.0,
                    help="fraction of cell height to hide at the bottom (captions)")
    ap.add_argument("--display-cell", type=int, default=400)
    ap.add_argument("--keep-bg", action="store_true")
    ap.add_argument("--bg-color", dest="bg_color", default="white",
                    help="background color to key out. 'white' (default) uses the "
                         "connected-components keyer; any other color (e.g. '#00B140') "
                         "uses a chroma key + green-spill suppression — use this when "
                         "the sheet was generated on a chroma background.")
    ap.add_argument("--flood-fuzz", type=float, default=12.0)
    ap.add_argument("--white-key", type=float, default=3.0)
    ap.add_argument("--min-region", type=float, default=0.00009)
    ap.add_argument("--webp-quality", type=int, default=82)
    ap.add_argument("--gif-max", type=int, default=480)
    ap.add_argument("--durations", default=None,
                    help="comma-separated per-frame hold WEIGHTS (length = frame "
                         "count), e.g. '1.6,1,0.9,...'. A weight of 2 holds twice as "
                         "long as 1. This is how you get natural easing (slow-in/out, "
                         "held apex) instead of mechanical uniform timing. Each "
                         "frame's time = weight / --fps seconds.")
    args = ap.parse_args()

    if not shutil.which("magick"):
        sys.exit("ERROR: ImageMagick 7 (`magick`) is required.")
    sheet = Path(args.sheet)
    if not sheet.exists():
        sys.exit(f"ERROR: sheet not found: {sheet}")
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    cols, rows = args.cols, args.rows
    n = cols * rows

    durations = None  # per-frame seconds
    if args.durations:
        weights = [float(x) for x in args.durations.split(",")]
        if len(weights) != n:
            sys.exit(f"ERROR: --durations has {len(weights)} weights but the grid "
                     f"is {cols}x{rows}={n} frames.")
        durations = [w / args.fps for w in weights]

    tmp = Path(tempfile.mkdtemp(prefix="spritegen_"))
    try:
        # 1. clean background (whole sheet at once)
        clean = tmp / "clean.png"
        if args.keep_bg:
            magick(sheet, clean)
        else:
            remove_background(sheet, clean, args.flood_fuzz, args.white_key,
                              args.min_region, args.bg_color)
        # keep a copy of the cleaned sheet for the user
        shutil.copy(clean, outdir / f"{args.name}-sheet.png")

        W, H = identify_wh(clean)
        xs, ys = bounds(W, cols), bounds(H, rows)
        cell_h_native = H / rows
        band_px = round(cell_h_native * args.label_crop)

        # 2. extract per-frame viewport crops (full-res, transparent)
        frames = []
        for k in range(n):
            c, r = k % cols, k // cols
            x0, x1 = xs[c], xs[c + 1]
            y0 = ys[r]
            cw = x1 - x0
            ch = (ys[r + 1] - y0) - band_px
            fp = tmp / f"f{k:02d}.png"
            magick(clean, "-crop", f"{cw}x{ch}+{x0}+{y0}", "+repage", fp)
            frames.append(fp)

        # 3. embedded sheet for the SVG: resize so each cell == display-cell,
        #    preserving the source cell aspect ratio (cells need not be square),
        #    then re-tile so the SVG window math is exact integers.
        cell_w = args.display_cell
        cell_h = max(1, round(cell_w * (H / rows) / (W / cols)))
        disp_sheet = tmp / "disp_sheet.webp"
        magick(clean, "-resize", f"{cell_w*cols}x{cell_h*rows}!",
               "-quality", str(args.webp_quality),
               "-define", "webp:alpha-quality=92", disp_sheet)
        vp_w = cell_w
        vp_h = round(cell_h * (1 - args.label_crop))

        out_svg = outdir / f"{args.name}.svg"
        svg_bytes = build_svg(disp_sheet, cols, rows, cell_w, cell_h, vp_w, vp_h,
                              args.fps, out_svg, durations)

        # 4. animated webp (true alpha) and gif from the full-res frames.
        #    Per-frame delays (centiseconds) carry the same easing as the SVG.
        if durations:
            delays = [max(2, round(d * 100)) for d in durations]
        else:
            delays = [max(2, round(100 / args.fps))] * n
        timed = []
        for d, f in zip(delays, frames):
            timed += ["-delay", str(d), f]

        out_webp = outdir / f"{args.name}.webp"
        magick("-dispose", "previous", "-loop", "0",
               *timed, "-quality", str(args.webp_quality), out_webp)

        out_gif = outdir / f"{args.name}.gif"
        magick("-dispose", "previous", "-loop", "0",
               *timed, "-resize", f"{args.gif_max}x{args.gif_max}>",
               "-layers", "OptimizeTransparency", out_gif)

        def kb(p):
            return f"{Path(p).stat().st_size/1024:.0f} KB"
        print(f"frames:      {n} ({cols}x{rows}) @ {args.fps} fps, "
              f"viewport {vp_w}x{vp_h}px")
        print(f"SVG:         {out_svg}  ({svg_bytes/1024:.0f} KB)")
        print(f"WebP:        {out_webp}  ({kb(out_webp)})")
        print(f"GIF:         {out_gif}  ({kb(out_gif)})")
        print(f"clean sheet: {outdir / (args.name + '-sheet.png')}  "
              f"({kb(outdir / (args.name + '-sheet.png'))})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
