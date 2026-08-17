#!/usr/bin/env python3
"""compose_scenes.py — turn flat open-licensed assets into finished,
high-quality illustration panels, fully server-side (no AI API, no phone).

Each beat gets a designed scene: deep-ocean gradient backdrop, layered
silhouettes, light rays, bubbles, waves, vignette — with the beat's subject
composited large and consistent. Output is 1280x1280 PNG per beat.

Usage:
    .venv/bin/python3 scripts/compose_scenes.py shark-video

Scenes are declared per beat id in SCENES below; subjects come from
projects/<name>/assets/NNN.png (already fetched open assets). Ledger and
CREDITS.md are updated (backend=compose, license inherited).
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1280

# ---------------------------------------------------------------- palette

NAVY = (10, 24, 48)
DEEP = (8, 42, 92)
MID = (14, 76, 130)
TEAL = (32, 140, 180)
CYAN = (90, 200, 230)
AMBER = (255, 176, 84)
SAND = (255, 224, 168)
INK = (6, 14, 30)
SIL = (200, 225, 240)

SCENES = {
    3: "abyss_silhouette",
    4: "scale_compare",
    5: "fin_surface",
    6: "sonar_boat",
    7: "diver_light",
    8: "jaws_closeup",
    9: "sunset_boat",
    10: "big_wave",
}


# ---------------------------------------------------------------- helpers

def gradient(size, stops):
    """Vertical gradient. stops = [(pos0..1, (r,g,b)), ...]. Fast via small
    mask resized up. size may be an int (square)."""
    if isinstance(size, int):
        size = (size, size)
    w, h = size
    small = Image.new("RGB", (1, len(stops) * 8), (0, 0, 0))
    px = small.load()
    n = small.height
    for y in range(n):
        t = y / (n - 1)
        # find segment
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = (t - p0) / (p1 - p0)
                px[0, y] = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
    return small.resize((w, h))


def radial_mask(size, inner=0.0, outer=1.0):
    """Radial mask (L), black center -> white edges."""
    w, h = size
    m = Image.new("L", (64, 64), 0)
    d = ImageDraw.Draw(m)
    cx = cy = 31.5
    r = 32
    for i in range(64):
        t = i / 63
        v = int(255 * max(0.0, min(1.0, (t - inner) / (outer - inner))))
        d.ellipse([cx - r * t, cy - r * t, cx + r * t, cy + r * t], fill=v)
    return m.resize((w, h))


def load_subject(path, max_w=760, max_h=760):
    """Load asset, ensure transparency, scale to fit box."""
    im = Image.open(path).convert("RGBA")
    # flatten any white background to transparent
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and r > 235 and g > 235 and b > 235:
                px[x, y] = (r, g, b, 0)
    im.thumbnail((max_w, max_h), Image.LANCZOS)
    return im


def paste_centered(canvas, subject, cx=None, cy=None, scale=1.0, shadow=True):
    """Paste subject with optional drop shadow; cx,cy = center (fraction)."""
    w, h = canvas.size
    cx = cx if cx is not None else 0.5
    cy = cy if cy is not None else 0.5
    sw, sh = subject.size
    sw, sh = int(sw * scale), int(sh * scale)
    if sw != subject.size[0]:
        subject = subject.resize((sw, sh), Image.LANCZOS)
    x = int(w * cx - sw / 2)
    y = int(h * cy - sh / 2)
    if shadow:
        sh_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sh_img.paste((0, 0, 0, 160), (x + 14, y + 22), subject)
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(sh_img)
    canvas.alpha_composite(subject, (x, y))


def bubbles(canvas, n=26, y0=0.05, y1=0.95, x0=0.04, x1=0.96, max_r=26):
    d = ImageDraw.Draw(canvas)
    import random
    rnd = random.Random(7)
    for _ in range(n):
        x = int(canvas.size[0] * rnd.uniform(x0, x1))
        y = int(canvas.size[1] * rnd.uniform(y0, y1))
        r = rnd.randint(2, max_r)
        a = rnd.randint(18, 60)
        d.ellipse([x - r, y - r, x + r, y + r],
                  outline=(CYAN[0], CYAN[1], CYAN[2], a), width=2)


def light_rays(canvas, color=(255, 255, 255), alpha=14, n=5, y_end=0.75):
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    import random
    rnd = random.Random(11)
    for _ in range(n):
        x0 = rnd.uniform(0.1, 0.9) * w
        width = rnd.uniform(0.05, 0.14) * w
        ye = h * y_end
        d.polygon([(x0, 0), (x0 + width, 0),
                   (x0 + width * 2.2, ye), (x0 - width * 1.2, ye)],
                  fill=color + (alpha,))


def vignette(canvas, strength=110):
    m = radial_mask(canvas.size, 0.35, 1.0)
    black = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    black.paste((0, 0, 0, strength), (0, 0), m)
    canvas.alpha_composite(black)


def stick_person(canvas, cx, cy, s=1.0, color=SIL, alpha=200):
    """Tiny swimmer/diver stick figure."""
    d = ImageDraw.Draw(canvas)
    L = 46 * s
    x, y = cx, cy
    d.ellipse([x - 12 * s, y - 26 * s, x + 12 * s, y - 4 * s],
              outline=color + (alpha,), width=5)
    d.line([(x, y - 4 * s), (x, y + 18 * s)], fill=color + (alpha,), width=5)
    d.line([(x, y + 2 * s), (x - 20 * s, y - 14 * s)],
           fill=color + (alpha,), width=5)  # arm out
    d.line([(x, y + 2 * s), (x + 20 * s, y - 16 * s)],
           fill=color + (alpha,), width=5)
    d.line([(x, y + 18 * s), (x - 10 * s, y + 40 * s)],
           fill=color + (alpha,), width=5)  # legs
    d.line([(x, y + 18 * s), (x + 10 * s, y + 40 * s)],
           fill=color + (alpha,), width=5)


def wave_band(canvas, y_frac=0.30, color=(24, 96, 150), alpha=70, amp=26, period=180):
    """Translucent rolling wave band across the frame."""
    w, h = canvas.size
    y0 = int(h * y_frac)
    d = ImageDraw.Draw(canvas)
    pts = []
    x = 0
    while x <= w + period:
        pts.append((x, y0 + amp * (0.5 + 0.5 * __import__("math").sin(x / period * 6.283))))
        x += 12
    d.line(pts, fill=color + (alpha,), width=10)


def sonar_rings(canvas, cx=0.5, cy=0.62, r0=0.10, r1=0.42, color=(120, 230, 255), alpha=90):
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    cx, cy = w * cx, h * cy
    r = r0 * w
    while r < r1 * w:
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  outline=color + (alpha,), width=4)
        r += 0.075 * w


def stars(canvas, n=40, y_max=0.35, color=(200, 225, 245), alpha=120):
    d = ImageDraw.Draw(canvas)
    import random
    rnd = random.Random(3)
    w, h = canvas.size
    for _ in range(n):
        x = rnd.uniform(0, w)
        y = rnd.uniform(0, h * y_max)
        r = rnd.uniform(0.6, 1.8)
        a = rnd.randint(30, alpha)
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))


# ------------------------------------------------------------- scenes

def scene_abyss_silhouette(subj):
    c = gradient(SIZE, [(0.0, NAVY), (0.5, DEEP), (1.0, (3, 10, 24))]).convert("RGBA")
    light_rays(c, alpha=10, y_end=0.55)
    stars(c)
    # whale silhouette, deep
    paste_centered(c, subj, cx=0.5, cy=0.72, scale=1.0, shadow=False)
    # tint the whale dark for silhouette feel
    ov = Image.new("RGBA", c.size, (2, 10, 26, 150))
    c.alpha_composite(ov)
    paste_centered(c, subj, cx=0.5, cy=0.72, scale=1.0, shadow=False)
    # tiny swimmer up top
    stick_person(c, int(SIZE * 0.5), int(SIZE * 0.14), s=0.9)
    bubbles(c, n=18)
    vignette(c)
    return c


def scene_scale_compare(subj):
    c = gradient(SIZE, [(0.0, (16, 52, 96)), (0.6, (10, 34, 72)), (1.0, (4, 14, 34))]).convert("RGBA")
    light_rays(c, alpha=16, y_end=0.7)
    bubbles(c, n=14, max_r=18)
    paste_centered(c, subj, cx=0.48, cy=0.62, scale=1.15)
    stick_person(c, int(SIZE * 0.80), int(SIZE * 0.30), s=1.0, color=AMBER, alpha=230)
    d = ImageDraw.Draw(c)
    d.line([(SIZE * 0.80, SIZE * 0.34), (SIZE * 0.80, SIZE * 0.52)],
           fill=AMBER + (160,), width=3)
    d.line([(SIZE * 0.70, SIZE * 0.52), (SIZE * 0.90, SIZE * 0.52)],
           fill=AMBER + (160,), width=3)
    vignette(c)
    return c


def scene_fin_surface(subj):
    c = gradient(SIZE, [(0.0, (168, 220, 245)), (0.28, (120, 190, 230)),
                        (0.31, (70, 150, 200)), (1.0, (14, 60, 110))]).convert("RGBA")
    # sky sparkle
    stars(c, n=24, y_max=0.26, color=(255, 255, 255), alpha=90)
    # fin breaking surface
    paste_centered(c, subj, cx=0.5, cy=0.32, scale=1.15)
    wave_band(c, y_frac=0.30, amp=30, alpha=120, color=(90, 180, 225))
    wave_band(c, y_frac=0.34, amp=18, alpha=70, color=(50, 130, 190))
    # splash droplets
    d = ImageDraw.Draw(c)
    import random
    rnd = random.Random(5)
    for _ in range(26):
        x = SIZE * rnd.uniform(0.3, 0.7)
        y = SIZE * (0.28 + rnd.uniform(0, 0.03))
        r = rnd.uniform(2, 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 235, 255, 200))
    bubbles(c, n=20, y0=0.4, y1=0.95, max_r=16)
    vignette(c, 90)
    return c


def scene_sonar_boat(subj):
    c = gradient(SIZE, [(0.0, (4, 12, 30)), (0.5, (6, 26, 58)), (1.0, (2, 8, 22))]).convert("RGBA")
    sonar_rings(c, cx=0.5, cy=0.60, r0=0.08, r1=0.46)
    paste_centered(c, subj, cx=0.5, cy=0.60, scale=0.9)
    bubbles(c, n=10, y0=0.7, y1=0.95, max_r=10)
    # boat silhouette near top of the water column
    stick_person(c, int(SIZE * 0.5), int(SIZE * 0.08), s=0.7, color=CYAN, alpha=120)
    d = ImageDraw.Draw(c)
    d.line([(SIZE * 0.30, SIZE * 0.16), (SIZE * 0.70, SIZE * 0.16)],
           fill=CYAN + (90,), width=4)
    d.line([(SIZE * 0.34, SIZE * 0.16), (SIZE * 0.38, SIZE * 0.10),
            (SIZE * 0.46, SIZE * 0.10), (SIZE * 0.50, SIZE * 0.16)],
           fill=CYAN + (90,), width=3)
    vignette(c)
    return c


def scene_diver_light(subj):
    c = gradient(SIZE, [(0.0, (3, 8, 20)), (0.6, (5, 18, 42)), (1.0, (1, 4, 12))]).convert("RGBA")
    # flashlight cone
    d = ImageDraw.Draw(c)
    d.polygon([(SIZE * 0.5, SIZE * 0.34), (SIZE * 0.20, SIZE * 0.95),
               (SIZE * 0.80, SIZE * 0.95)],
              fill=(255, 236, 160, 26))
    d.polygon([(SIZE * 0.5, SIZE * 0.34), (SIZE * 0.32, SIZE * 0.95),
               (SIZE * 0.68, SIZE * 0.95)],
              fill=(255, 240, 180, 22))
    paste_centered(c, subj, cx=0.5, cy=0.36, scale=0.95)
    bubbles(c, n=24, max_r=22)
    stars(c, n=30, y_max=1.0, color=(160, 200, 240), alpha=70)
    vignette(c, 130)
    return c


def scene_jaws_closeup(subj):
    c = gradient(SIZE, [(0.0, (28, 6, 10)), (0.5, (12, 4, 8)), (1.0, (4, 2, 4))]).convert("RGBA")
    paste_centered(c, subj, cx=0.5, cy=0.52, scale=1.5)
    bubbles(c, n=12, max_r=14)
    vignette(c, 120)
    return c


def scene_sunset_boat(subj):
    c = gradient(SIZE, [(0.0, (255, 170, 90)), (0.28, (255, 205, 130)),
                        (0.32, (236, 130, 60)), (0.55, (96, 60, 110)),
                        (1.0, (16, 26, 58))]).convert("RGBA")
    d = ImageDraw.Draw(c)
    # sun
    d.ellipse([SIZE * 0.40, SIZE * 0.12, SIZE * 0.60, SIZE * 0.32],
              fill=(255, 240, 200, 220))
    # shimmer path
    for i in range(14):
        y = SIZE * (0.34 + i * 0.04)
        xw = SIZE * (0.10 + i * 0.006)
        d.line([(SIZE * 0.5 - xw, y), (SIZE * 0.5 + xw, y)],
               fill=(255, 230, 180, 110), width=3)
    paste_centered(c, subj, cx=0.5, cy=0.52, scale=1.0)
    wave_band(c, y_frac=0.55, amp=16, alpha=90, color=(200, 120, 90))
    wave_band(c, y_frac=0.60, amp=10, alpha=60, color=(160, 90, 100))
    # seagulls
    for gx in (0.22, 0.72, 0.85):
        gx = SIZE * gx
        gy = SIZE * 0.22
        d.arc([gx - 14, gy - 8, gx, gy + 8], 180, 360, fill=(40, 30, 40, 180), width=3)
        d.arc([gx, gy - 8, gx + 14, gy + 8], 180, 360, fill=(40, 30, 40, 180), width=3)
    vignette(c, 70)
    return c


def scene_big_wave(subj):
    c = gradient(SIZE, [(0.0, (90, 180, 215)), (0.35, (30, 110, 160)),
                        (0.7, (10, 60, 110)), (1.0, (4, 24, 52))]).convert("RGBA")
    paste_centered(c, subj, cx=0.38, cy=0.42, scale=1.35)
    # spray
    d = ImageDraw.Draw(c)
    import random
    rnd = random.Random(9)
    for _ in range(40):
        x = SIZE * rnd.uniform(0.15, 0.7)
        y = SIZE * rnd.uniform(0.10, 0.45)
        r = rnd.uniform(2, 9)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 240, 255, rnd.randint(40, 160)))
    # tiny boat bottom right
    stick_person(c, int(SIZE * 0.80), int(SIZE * 0.72), s=0.8, color=(10, 30, 60), alpha=220)
    d.polygon([(SIZE * 0.72, SIZE * 0.80), (SIZE * 0.88, SIZE * 0.80),
               (SIZE * 0.85, SIZE * 0.86), (SIZE * 0.75, SIZE * 0.86)],
              fill=(30, 50, 80, 230))
    d.line([(SIZE * 0.80, SIZE * 0.80), (SIZE * 0.80, SIZE * 0.74),
            (SIZE * 0.77, SIZE * 0.77)],
           fill=(30, 50, 80, 230), width=5)
    wave_band(c, y_frac=0.85, amp=14, alpha=80, color=(60, 140, 190))
    bubbles(c, n=16, y0=0.5, y1=0.95, max_r=14)
    vignette(c, 100)
    return c


SCENE_FNS = {
    "abyss_silhouette": scene_abyss_silhouette,
    "scale_compare": scene_scale_compare,
    "fin_surface": scene_fin_surface,
    "sonar_boat": scene_sonar_boat,
    "diver_light": scene_diver_light,
    "jaws_closeup": scene_jaws_closeup,
    "sunset_boat": scene_sunset_boat,
    "big_wave": scene_big_wave,
}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: compose_scenes.py PROJECT [beat_id ...]")
    project = sys.argv[1]
    want = [int(a) for a in sys.argv[2:]] or None
    d = ROOT / "projects" / project
    assets = d / "assets"
    imgs_path = d / "images.json"
    images = json.loads(imgs_path.read_text()) if imgs_path.exists() else []
    by_id = {im["id"]: im for im in images}
    done = []
    for bid, kind in SCENES.items():
        if want and bid not in want:
            continue
        subj_path = assets / f"{bid:03d}.png"
        if not subj_path.exists():
            print(f"skip {bid}: no subject asset")
            continue
        fn = SCENE_FNS[kind]
        subject = load_subject(subj_path)
        scene = fn(subject)
        out = assets / f"{bid:03d}.png"
        scene.convert("RGB").save(out)
        entry = by_id.get(bid, {"id": bid})
        entry["backend"] = "compose"
        entry["scene"] = kind
        entry["file"] = f"assets/{out.name}"
        by_id[bid] = entry
        done.append(bid)
        print(f"composed beat {bid} ({kind}) -> {out} {scene.size}")
    imgs_path.write_text(json.dumps(sorted(by_id.values(), key=lambda x: x["id"]), indent=2))
    print(f"done {len(done)} scenes; ledger updated")


if __name__ == "__main__":
    main()
