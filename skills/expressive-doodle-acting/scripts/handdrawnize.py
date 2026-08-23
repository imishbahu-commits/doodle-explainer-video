#!/usr/bin/env python3
"""Deterministically re-ink generated art into clean hand-drawn doodle assets.

This is deliberately not a photo-to-sketch novelty filter. It simplifies color
regions, derives semantic-looking region contours, gives the contour controlled
low-frequency irregularity, and composites one near-black variable-width ink
pass over flat fills. Pillow is the only dependency.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

INK = (16, 16, 16)


def odd(value: int) -> int:
    value = max(1, int(value))
    return value if value % 2 else value + 1


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise argparse.ArgumentTypeError("color must be a 6-digit hex value")
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid hex color") from exc


def flatten_rgb(image: Image.Image, colors: int, smooth: int) -> Image.Image:
    rgb = image.convert("RGB")
    if smooth:
        rgb = rgb.filter(ImageFilter.MedianFilter(odd(smooth)))
    # Quantize only RGB; handling alpha separately prevents matte halos.
    pal = rgb.quantize(colors=max(2, colors), method=Image.Quantize.MEDIANCUT)
    return pal.convert("RGB")


def channel_range(channel: Image.Image, radius: int = 1) -> Image.Image:
    size = odd(radius * 2 + 1)
    return ImageChops.difference(
        channel.filter(ImageFilter.MaxFilter(size)),
        channel.filter(ImageFilter.MinFilter(size)),
    )


def region_edges(flat: Image.Image, alpha: Image.Image, sensitivity: int) -> Image.Image:
    ranges = [channel_range(ch, 1) for ch in flat.split()]
    ranges.append(channel_range(alpha, 1))
    edge = ranges[0]
    for item in ranges[1:]:
        edge = ImageChops.lighter(edge, item)
    threshold = max(1, min(254, sensitivity))
    return edge.point(lambda p: 255 if p >= threshold else 0, mode="L")


def mesh_warp(image: Image.Image, amount: float, grid: int, rng: random.Random) -> Image.Image:
    if amount <= 0:
        return image.copy()
    w, h = image.size
    cell = max(24, int(grid))
    xs = list(range(0, w, cell)) + ([w] if w % cell else [])
    ys = list(range(0, h, cell)) + ([h] if h % cell else [])
    if xs[-1] != w:
        xs.append(w)
    if ys[-1] != h:
        ys.append(h)

    points: dict[tuple[int, int], tuple[float, float]] = {}
    for y in ys:
        for x in xs:
            # Keep the canvas boundary stable so assets remain registration-safe.
            dx = 0.0 if x in (0, w) else rng.uniform(-amount, amount)
            dy = 0.0 if y in (0, h) else rng.uniform(-amount, amount)
            points[(x, y)] = (x + dx, y + dy)

    mesh = []
    for yi in range(len(ys) - 1):
        for xi in range(len(xs) - 1):
            x0, x1 = xs[xi], xs[xi + 1]
            y0, y1 = ys[yi], ys[yi + 1]
            quad = (
                *points[(x0, y0)],
                *points[(x0, y1)],
                *points[(x1, y1)],
                *points[(x1, y0)],
            )
            mesh.append(((x0, y0, x1, y1), quad))
    return image.transform(image.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)


def low_frequency_texture(size: tuple[int, int], rng: random.Random, minimum: int = 220) -> Image.Image:
    w, h = size
    sw, sh = max(2, math.ceil(w / 64)), max(2, math.ceil(h / 64))
    values = bytes(rng.randint(minimum, 255) for _ in range(sw * sh))
    small = Image.frombytes("L", (sw, sh), values)
    return small.resize((w, h), Image.Resampling.BICUBIC)


def make_ink_mask(
    edge: Image.Image,
    width: int,
    wobble: float,
    seed: int,
    opacity: int,
) -> Image.Image:
    rng = random.Random(seed)
    warped = mesh_warp(edge, wobble, max(48, width * 18), rng)
    # A single contour pass with mild variable thickness—not duplicated scribble.
    ink = warped.filter(ImageFilter.MaxFilter(odd(width))) if width > 1 else warped
    ink = ink.filter(ImageFilter.GaussianBlur(max(0.15, width * 0.10)))
    ink = ink.point(lambda p: 255 if p > 72 else int(p * 2.2), mode="L")
    texture = low_frequency_texture(ink.size, rng)
    ink = ImageChops.multiply(ink, texture)
    if opacity < 255:
        ink = ink.point(lambda p: p * opacity // 255)
    return ink


def composite_ink(flat: Image.Image, source_alpha: Image.Image, ink_mask: Image.Image, ink: tuple[int, int, int]) -> Image.Image:
    rgba = flat.convert("RGBA")
    rgba.putalpha(source_alpha)
    ink_layer = Image.new("RGBA", rgba.size, (*ink, 0))
    ink_layer.putalpha(ink_mask)
    out = Image.alpha_composite(rgba, ink_layer)
    # Include the outside half of silhouette ink without introducing a white matte.
    out.putalpha(ImageChops.lighter(source_alpha, ink_mask))
    return out


def metrics(flat: Image.Image, alpha: Image.Image, ink_mask: Image.Image, colors_requested: int) -> dict:
    hist = ink_mask.histogram()
    pixels = ink_mask.width * ink_mask.height
    ink_pixels = sum(hist[32:])
    values: Iterable[int] = (
        alpha.get_flattened_data() if hasattr(alpha, "get_flattened_data") else alpha.getdata()
    )
    opaque = sum(1 for v in values if v > 16)
    palette = flat.quantize(colors=256).getcolors(256) or []
    return {
        "width": flat.width,
        "height": flat.height,
        "requested_fill_colors": colors_requested,
        "observed_quantized_colors": len(palette),
        "ink_coverage": round(ink_pixels / max(1, pixels), 5),
        "subject_coverage": round(opaque / max(1, pixels), 5),
        "mean_ink_alpha": round(ImageStat.Stat(ink_mask).mean[0], 3),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--line-art", type=Path, help="optional transparent ink-only PNG")
    parser.add_argument("--report", type=Path, help="optional JSON processing/QC report")
    parser.add_argument("--colors", type=int, default=10, help="flat fill palette size (default: 10)")
    parser.add_argument("--smooth", type=int, default=3, help="median smoothing kernel (default: 3)")
    parser.add_argument("--sensitivity", type=int, default=28, help="region-edge threshold, 1..254")
    parser.add_argument("--line-width", type=int, default=4, help="production ink width in pixels")
    parser.add_argument("--wobble", type=float, default=1.35, help="maximum low-frequency contour displacement")
    parser.add_argument("--ink", type=parse_hex, default=INK, help="ink color, default #101010")
    parser.add_argument("--ink-opacity", type=int, default=246)
    parser.add_argument("--seed", type=int, default=17, help="deterministic imperfection seed")
    parser.add_argument("--background", choices=("transparent", "white"), default="transparent")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = Image.open(args.input).convert("RGBA")
    alpha = source.getchannel("A")
    flat = flatten_rgb(source, args.colors, args.smooth)
    edge = region_edges(flat, alpha, args.sensitivity)
    mask = make_ink_mask(edge, args.line_width, args.wobble, args.seed, max(0, min(255, args.ink_opacity)))
    out = composite_ink(flat, alpha, mask, args.ink)
    if args.background == "white":
        paper = Image.new("RGBA", out.size, "white")
        out = Image.alpha_composite(paper, out).convert("RGB")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)

    if args.line_art:
        args.line_art.parent.mkdir(parents=True, exist_ok=True)
        line = Image.new("RGBA", source.size, (*args.ink, 0))
        line.putalpha(mask)
        line.save(args.line_art)

    report = {
        "input": str(args.input),
        "output": str(args.output),
        "seed": args.seed,
        "parameters": {
            "colors": args.colors,
            "smooth": args.smooth,
            "sensitivity": args.sensitivity,
            "line_width": args.line_width,
            "wobble": args.wobble,
            "ink": "#%02x%02x%02x" % args.ink,
            "ink_opacity": args.ink_opacity,
            "background": args.background,
        },
        "metrics": metrics(flat, alpha, mask, args.colors),
        "warnings": [],
    }
    coverage = report["metrics"]["ink_coverage"]
    if coverage < 0.008:
        report["warnings"].append("very low ink coverage; lower --sensitivity")
    if coverage > 0.28:
        report["warnings"].append("very high ink coverage; raise --sensitivity or lower --line-width")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
