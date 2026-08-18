#!/usr/bin/env python3
"""Post-generation drawing pass — turn a subject PNG into a meme panel.

Does NOT regenerate the character. Draws captions, arrows, circles, X's
on top of an already-accepted doodle so the joke can change without a
new image model call.

  .venv/bin/python tools/meme_draw.py IN.png OUT.png --top "THIN?" --stamp no
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "skills" / "ae-motion" / "fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = {
        "bold": FONTS / "kalam-700.ttf",
        "hand": FONTS / "caveat-700.ttf",
        "note": FONTS / "patrick-hand.ttf",
    }.get(name, FONTS / "kalam-700.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, start: int, face: str):
    size = start
    while size > 18:
        f = font(face, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(face, 18)


def draw_caption(im: Image.Image, text: str, y: int, face="bold", fill=(20, 20, 24)):
    d = ImageDraw.Draw(im)
    f = fit_text(d, text, int(im.width * 0.86), 92, face)
    x = im.width / 2
    # thick hand outline
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
        d.text((x + dx, y + dy), text, font=f, fill=(255, 255, 255), anchor="mm")
    d.text((x, y), text, font=f, fill=fill, anchor="mm")


def draw_x(im: Image.Image):
    d = ImageDraw.Draw(im)
    m = min(im.size)
    pad = int(m * 0.18)
    w = max(18, m // 28)
    d.line([(pad, pad), (im.width - pad, im.height - pad)], fill=(220, 28, 28), width=w)
    d.line([(im.width - pad, pad), (pad, im.height - pad)], fill=(220, 28, 28), width=w)


def draw_circle(im: Image.Image):
    d = ImageDraw.Draw(im)
    m = min(im.size)
    pad = int(m * 0.12)
    d.ellipse([pad, pad, im.width - pad, im.height - pad], outline=(220, 28, 28), width=max(10, m // 40))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--top")
    ap.add_argument("--bottom")
    ap.add_argument("--stamp", choices=["no", "x", "circle"])
    args = ap.parse_args()

    im = Image.open(args.src).convert("RGBA")
    if args.top:
        draw_caption(im, args.top.upper(), int(im.height * 0.08))
    if args.bottom:
        draw_caption(im, args.bottom.upper(), int(im.height * 0.92), face="hand")
    if args.stamp in ("no", "x"):
        draw_x(im)
    if args.stamp == "circle":
        draw_circle(im)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out)
    print(f"drew {args.out}")


if __name__ == "__main__":
    main()
