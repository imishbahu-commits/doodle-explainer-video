#!/usr/bin/env python3
"""finalize_photo_beats.py — turn license-clean, full-resolution photographs
(searched from Wikimedia Commons / Pexels / public-domain archives) into the
project's 10 beat images.

Fully server-side: center-crop to square, resize to 1280x1280 (LANCZOS),
subtle cinematic grade (contrast/saturation/vignette), light sharpening for
smaller sources. Updates images.json + CREDITS.md with source + licence.

Usage:
    .venv/bin/python3 scripts/finalize_photo_beats.py shark-video
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "image-search"
SIZE = 1280

# beat -> (source file, licence, source_url, credit line)
MAP = {
    1: ("great-white-shark-wikimedia-commons-1.jpg",
        "Wikimedia Commons (CC BY-SA — see source page)",
        "https://commons.wikimedia.org/wiki/File:Great_white_shark_close_up.JPG",
        "Great white shark close up — Wikimedia Commons contributor"),
    2: ("open-water-swimmer-person-floating-ocean-1.jpg",
        "Pexels License (free to use, no attribution required)",
        "https://www.pexels.com/search/person%20floating%20in%20water/",
        "Photo by Pexels contributor — Pexels License"),
    3: ("whale-underwater-ocean-wikimedia-commons-1.jpg",
        "Public domain (Wikimedia Commons)",
        "https://commons.wikimedia.org/",
        "Whale shark underwater — public domain, Wikimedia Commons"),
    4: ("whale-shark-illustration-wikimedia-commo-2.jpg",
        "Wikimedia Commons (see source page)",
        "https://commons.wikimedia.org/wiki/Category:Rhincodon_typus",
        "Whale shark — Wikimedia Commons contributor"),
    5: ("shark-fin-ocean-surface-pexels-photo-1.jpg",
        "Pexels License (free to use, no attribution required)",
        "https://www.pexels.com/search/shark%20fin/",
        "Photo by Pexels contributor — Pexels License"),
    6: ("sonar-machine-screen-wikimedia-commons-1.jpg",
        "Public domain (Wikimedia Commons — side-scan sonar)",
        "https://en.wikipedia.org/wiki/Side-scan_sonar",
        "Side-scan sonar image — public domain, Wikimedia Commons"),
    7: ("scuba-diver-deep-blue-water-pexels-photo-3.jpg",
        "Pexels License (free to use, no attribution required)",
        "https://www.pexels.com/search/scuba%20diver/",
        "Photo by Pexels contributor — Pexels License"),
    8: ("shark-teeth-isolated-white-background-wi-1.png",
        "Vecteezy Free License (attribution: vecteezy.com)",
        "https://www.vecteezy.com/free-png/shark-teeth",
        "Great white shark open mouth — Vecteezy (free license)"),
    9: ("fishing-boat-sunset-ocean-wikimedia-comm-1.jpg",
        "Wikimedia Commons (CC BY-SA — Featured picture)",
        "https://commons.wikimedia.org/wiki/Commons:Featured_pictures/Objects/Vehicles/Water_transport",
        "Pirogue on the Mekong at sunset — Wikimedia Commons featured picture"),
    10: ("dramatic-ocean-wave-photo-wikimedia-comm-1.jpg",
        "Public domain (Wikimedia Commons via Rawpixel)",
        "https://commons.wikimedia.org/",
        "Ocean waves aerial — public domain, Wikimedia Commons"),
}


def square_crop(im):
    w, h = im.size
    s = min(w, h)
    x = (w - s) // 2
    y = int((h - s) * 0.42)  # bias slightly above center
    y = max(0, min(h - s, y))
    return im.crop((x, y, x + s, y + s))


def grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.07)
    # vignette
    m = Image.new("L", (64, 64), 0)
    d = ImageDraw.Draw(m)
    cx = cy = 31.5
    for i in range(64):
        t = i / 63
        v = int(255 * max(0.0, min(1.0, (t - 0.35) / 0.65)))
        r = 32 * t
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    m = m.resize(im.size)
    black = Image.new("RGB", im.size, (0, 0, 0))
    im = Image.composite(im, black, m.point(lambda p: int(p * 0.88)))
    return im


def scene_jaws(im):
    """Beat 8: transparent shark PNG over a deep-sea gradient."""
    c = Image.new("RGB", (SIZE, SIZE))
    px = c.load()
    for y in range(SIZE):
        t = y / SIZE
        r = int(28 + (4 - 28) * t)
        g = int(6 + (2 - 6) * t)
        b = int(10 + (4 - 10) * t)
        for x in range(SIZE):
            px[x, y] = (r, g, b)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    im.thumbnail((SIZE * 0.86, SIZE * 0.86), Image.LANCZOS)
    c = c.convert("RGBA")
    x = (SIZE - im.size[0]) // 2
    y = (SIZE - im.size[1]) // 2
    c.alpha_composite(im, (x, y))
    return grade(c.convert("RGB"))


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: finalize_photo_beats.py PROJECT [beat_id ...]")
    project = sys.argv[1]
    want = [int(a) for a in sys.argv[2:]] or None
    d = ROOT / "projects" / project
    assets = d / "assets"
    imgs_path = d / "images.json"
    images = json.loads(imgs_path.read_text()) if imgs_path.exists() else []
    by_id = {im["id"]: im for im in images}
    prompts = json.loads((d / "prompts.json").read_text())
    kw = {p["id"]: p["keyword"] for p in prompts}

    for bid, (fname, lic, url, credit) in MAP.items():
        if want and bid not in want:
            continue
        src = SRC / fname
        if not src.exists():
            print(f"skip beat {bid}: missing {fname}")
            continue
        im = Image.open(src).convert("RGB")
        if bid == 8:
            im = Image.open(src)  # keep alpha for scene_jaws
            out_im = scene_jaws(im)
        else:
            out_im = grade(square_crop(im).resize((SIZE, SIZE), Image.LANCZOS))
            if im.size[0] < 900:
                out_im = out_im.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3))
        out = assets / f"{bid:03d}.png"
        out_im.save(out)
        entry = by_id.get(bid, {"id": bid})
        entry.update({
            "backend": "photo",
            "file": f"assets/{out.name}",
            "keyword": kw.get(bid, ""),
            "license": lic,
            "source_url": url,
            "credit": credit,
            "bytes": out.stat().st_size,
        })
        by_id[bid] = entry
        print(f"beat {bid}: {src.name} ({Image.open(src).size}) -> {out}")

    imgs_path.write_text(json.dumps(sorted(by_id.values(), key=lambda x: x["id"]), indent=2))

    # CREDITS
    lines = ["# CREDITS — sources used by this project", ""]
    for im in sorted(by_id.values(), key=lambda x: x["id"]):
        if im.get("credit"):
            lines.append(f"- Beat {im['id']}: `{im['file']}` — {im['credit']}")
            lines.append(f"  License: {im['license']} — {im['source_url']}")
    (d / "CREDITS.md").write_text("\n".join(lines) + "\n")
    print("done; ledger + CREDITS.md updated")


if __name__ == "__main__":
    main()
