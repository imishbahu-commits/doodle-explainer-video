#!/usr/bin/env python3
"""Prepare a clean RGBA subject PNG with flat-bg and ML fallback modes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import deque
from pathlib import Path

from PIL import Image


def pixel_values(image: Image.Image) -> list[int]:
    """Pillow 10–13 compatible flattened pixel values."""
    flattened = getattr(image, "get_flattened_data", None)
    return list(flattened() if flattened else image.getdata())


ROOT = Path(__file__).resolve().parents[3]
ML_REMOVER = ROOT / "skills" / "character-animation-skill" / "scripts" / "remove_bg_ml.py"


def has_useful_alpha(image: Image.Image) -> bool:
    if "A" not in image.getbands():
        return False
    alpha = image.getchannel("A")
    lo, hi = alpha.getextrema()
    transparent = sum(1 for value in pixel_values(alpha) if value < 250)
    return lo < 250 and hi > 8 and transparent >= max(8, image.width * image.height // 500)


def border_colors(image: Image.Image) -> list[tuple[int, int, int]]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    step_x = max(1, w // 64)
    step_y = max(1, h // 64)
    colors = []
    for x in range(0, w, step_x):
        colors.extend((px[x, 0], px[x, h - 1]))
    for y in range(0, h, step_y):
        colors.extend((px[0, y], px[w - 1, y]))
    return colors


def border_is_flat(image: Image.Image, tolerance: int) -> bool:
    colors = border_colors(image)
    if not colors:
        return False
    channel_ranges = [max(c[i] for c in colors) - min(c[i] for c in colors) for i in range(3)]
    return max(channel_ranges) <= max(10, tolerance * 2)


def flood_flat_background(image: Image.Image, tolerance: int) -> Image.Image:
    rgba = image.convert("RGBA")
    rgb = rgba.convert("RGB")
    w, h = rgba.size
    src = rgb.load()
    out = rgba.load()
    colors = border_colors(rgba)
    reference = tuple(round(sum(c[i] for c in colors) / len(colors)) for i in range(3))

    def is_bg(x: int, y: int) -> bool:
        color = src[x, y]
        return max(abs(color[i] - reference[i]) for i in range(3)) <= tolerance

    seen = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(x, y):
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(x, y):
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        index = y * w + x
        if seen[index] or not is_bg(x, y):
            continue
        seen[index] = 1
        r, g, b, _ = out[x, y]
        out[x, y] = (r, g, b, 0)
        if x > 0: queue.append((x - 1, y))
        if x + 1 < w: queue.append((x + 1, y))
        if y > 0: queue.append((x, y - 1))
        if y + 1 < h: queue.append((x, y + 1))
    return rgba


def crop_pad(image: Image.Image, pad: int) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit("asset became fully transparent")
    cropped = image.crop(bbox)
    if pad <= 0:
        return cropped
    canvas = Image.new("RGBA", (cropped.width + 2 * pad, cropped.height + 2 * pad), (0, 0, 0, 0))
    canvas.alpha_composite(cropped, (pad, pad))
    return canvas


def run_ml(source: Path, destination: Path) -> Image.Image:
    if not ML_REMOVER.exists():
        raise SystemExit(f"ML remover not found: {ML_REMOVER}")
    subprocess.run([sys.executable, str(ML_REMOVER), str(source), str(destination)], check=True)
    return Image.open(destination).convert("RGBA")


def report(image: Image.Image, mode: str, source_size: tuple[int, int]) -> dict[str, object]:
    alpha = image.getchannel("A")
    values = pixel_values(alpha)
    area = max(1, len(values))
    transparent = sum(value <= 8 for value in values) / area
    opaque = sum(value >= 247 for value in values) / area
    bbox = alpha.getbbox()
    touches = False
    if bbox:
        touches = bbox[0] == 0 or bbox[1] == 0 or bbox[2] == image.width or bbox[3] == image.height
    warnings = []
    if transparent < 0.02:
        warnings.append("less than 2% transparent area")
    if opaque < 0.02:
        warnings.append("less than 2% opaque core")
    if touches:
        warnings.append("subject touches output border; increase --pad")
    return {
        "mode_used": mode,
        "source_size": list(source_size),
        "output_size": list(image.size),
        "alpha_bbox": list(bbox) if bbox else None,
        "transparent_fraction": round(transparent, 5),
        "opaque_fraction": round(opaque, 5),
        "subject_touches_border": touches,
        "warnings": warnings,
        "ok": not warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("auto", "flat", "ml", "alpha"), default="auto")
    parser.add_argument("--tolerance", type=int, default=30)
    parser.add_argument("--pad", type=int, default=8)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise SystemExit(f"input not found: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.input)
    source_size = source.size
    mode = args.mode
    temp_ml = args.output.with_name(args.output.stem + ".ml-temp.png")

    if mode == "auto":
        if has_useful_alpha(source):
            mode = "alpha"
        elif border_is_flat(source, args.tolerance):
            mode = "flat"
        else:
            mode = "ml"

    if mode == "alpha":
        image = source.convert("RGBA")
    elif mode == "flat":
        image = flood_flat_background(source, args.tolerance)
    else:
        image = run_ml(args.input, temp_ml)

    image = crop_pad(image, max(0, args.pad))
    image.save(args.output)
    temp_ml.unlink(missing_ok=True)
    result = report(image, mode, source_size)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
