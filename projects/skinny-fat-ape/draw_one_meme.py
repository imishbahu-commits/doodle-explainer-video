#!/usr/bin/env python3
"""One generated PNG → mask the ape → draw the meme.

1. Magic-wand isolate (same as ae_motion) → transparent ape + alpha mask
2. Draw a doodle background + captions + stamps around the masked ape
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "skills" / "ae-motion" / "fonts"
RAW = HERE / "assets" / "one-ape-raw.png"
MASK = HERE / "assets" / "one-ape-mask.png"
CUT = HERE / "assets" / "one-ape-cut.png"
OUT = HERE / "assets" / "one-ape-meme.png"
W, H = 1280, 720


def load_font(name: str, size: int):
    path = {
        "bold": FONTS / "kalam-700.ttf",
        "hand": FONTS / "caveat-700.ttf",
        "note": FONTS / "patrick-hand.ttf",
    }[name]
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def isolate(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    h, w = a.shape[:2]
    corner = a[2, 2, :3].astype(int)
    bg = (
        (np.abs(a[:, :, 0].astype(int) - corner[0]) < 28)
        & (np.abs(a[:, :, 1].astype(int) - corner[1]) < 28)
        & (np.abs(a[:, :, 2].astype(int) - corner[2]) < 28)
    )
    vis = np.zeros((h, w), bool)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not vis[y, x]:
                vis[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x] and not vis[y, x]:
                vis[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and bg[ny, nx] and not vis[ny, nx]:
                vis[ny, nx] = True
                q.append((ny, nx))
    a[vis, 3] = 0
    out = Image.fromarray(a)
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


def stroke_text(d, xy, text, font, fill, outline=(255, 255, 255), width=3, anchor="mm"):
    x, y = xy
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                d.text((x + dx, y + dy), text, font=font, fill=outline, anchor=anchor)
    d.text((x, y), text, font=font, fill=fill, anchor=anchor)


def doodle_bg() -> Image.Image:
    im = Image.new("RGB", (W, H), (255, 244, 210))
    d = ImageDraw.Draw(im)
    # cream patches
    d.ellipse([-80, -60, 360, 220], fill=(255, 232, 176))
    d.ellipse([980, 480, 1360, 800], fill=(255, 226, 160))
    d.ellipse([900, -40, 1320, 180], fill=(255, 236, 190))
    # wavy notebook lines
    for y in range(90, H, 78):
        pts = [(x, y + int(6 * np.sin(x / 70.0))) for x in range(0, W + 8, 8)]
        d.line(pts, fill=(40, 40, 44), width=3)
    # margin
    d.line([(110, 0), (110, H)], fill=(220, 70, 70), width=4)
    # corner bananas (tiny doodles)
    for cx, cy in ((70, 70), (1210, 80), (70, 650), (1210, 650)):
        d.ellipse([cx - 22, cy - 10, cx + 22, cy + 18], outline=(30, 30, 30), width=3, fill=(250, 210, 40))
        d.ellipse([cx - 6, cy - 18, cx + 6, cy - 4], outline=(30, 30, 30), width=3)
    # dumbbells
    for cx, cy in ((180, 80), (1100, 640)):
        d.ellipse([cx - 28, cy - 14, cx - 10, cy + 14], fill=(50, 50, 54), outline=(20, 20, 20), width=3)
        d.ellipse([cx + 10, cy - 14, cx + 28, cy + 14], fill=(50, 50, 54), outline=(20, 20, 20), width=3)
        d.line([(cx - 10, cy), (cx + 10, cy)], fill=(20, 20, 20), width=6)
    d.rectangle([8, 8, W - 9, H - 9], outline=(28, 28, 32), width=6)
    return im.convert("RGBA")


def main():
    ape = isolate(RAW)
    ape.save(CUT)
    # save the alpha as a readable mask
    alpha = ape.getchannel("A")
    Image.merge("RGB", (alpha, alpha, alpha)).save(MASK)

    canvas = doodle_bg()
    # place ape slightly low, centered
    ape = ape.copy()
    ape.thumbnail((620, 560), Image.LANCZOS)
    x = (W - ape.width) // 2
    y = H - ape.height - 70
    canvas.alpha_composite(ape, (x, y))

    d = ImageDraw.Draw(canvas)
    # red circle around the soft middle (the "crime")
    cx, cy = W // 2, y + int(ape.height * 0.52)
    d.ellipse([cx - 170, cy - 110, cx + 170, cy + 130], outline=(220, 28, 28), width=8)

    # hand arrow pointing at belly
    d.line([(cx + 200, cy - 40), (cx + 175, cy + 10)], fill=(220, 28, 28), width=7)
    d.polygon([(cx + 168, cy + 4), (cx + 198, cy + 22), (cx + 186, cy - 8)], fill=(220, 28, 28))

    top = load_font("bold", 72)
    bot = load_font("bold", 52)
    note = load_font("note", 36)
    stroke_text(d, (W / 2, 58), "IS MONKEY THIN?", top, (24, 24, 28))
    stroke_text(d, (W / 2, H - 38), "NAH. THAT'S A BOX WITH NO SHAPE.", bot, (24, 24, 28))
    stroke_text(d, (cx + 250, cy - 70), "THE CRIME", note, (220, 28, 28), outline=(255, 255, 255), width=2)

    canvas.convert("RGB").save(OUT, quality=95)
    print(f"mask  {MASK}")
    print(f"cut   {CUT}")
    print(f"meme  {OUT}")


if __name__ == "__main__":
    main()
