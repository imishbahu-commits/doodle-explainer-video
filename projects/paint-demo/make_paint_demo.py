#!/usr/bin/env python3
"""Paint Explainer style demo — the decoded motion grammar on hand-drawn PNGs.

Grammar (from references/paint-explainer-style.md):
  1. slide-in subject with overshoot settle + idle bob
  2. pop-in labels (scale overshoot)
  3. punch-in zoom into the subject
  4. quick hard swap to the next subject (slide-push)
  5. parallax between background layer and subject layer
All stills, all keyframed in code, hard cuts, narration-paced.
"""

import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageSequenceClip

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
WORK = HERE / "work"
WORK.mkdir(exist_ok=True)

W, H, FPS = 1280, 720, 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}


def F(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(FONT, size)
    return _fc[size]


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_in_cubic(x):
    x = max(0.0, min(1.0, x))
    return x * x * x


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    v = x - 1
    return 1 + c3 * v * v * v + c1 * v * v


def isolate(path):
    """Magic-wand isolation from the pure-white background."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    h, w = a.shape[:2]
    corner = a[2, 2, :3].astype(int)
    bg = (abs(a[:, :, 0].astype(int) - corner[0]) < 30) & \
         (abs(a[:, :, 1].astype(int) - corner[1]) < 30) & \
         (abs(a[:, :, 2].astype(int) - corner[2]) < 30)
    from collections import deque
    vis = np.zeros((h, w), bool)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
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
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def pop_label(dr, text, cx, cy, size, t, t0=0.0):
    """Label that pops in with scale overshoot at t0."""
    p = (t - t0) / 0.4
    if p <= 0:
        return
    if p >= 1:
        p = 1.0
    s = 0.6 + 0.4 * ease_out_back(p)
    a = int(255 * min(1.0, p / 0.6))
    im = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((cx, 100), text, font=F(size), fill=(28, 28, 34, a), anchor="mm")
    im = im.resize((int(W * s), int(200 * s)), Image.LANCZOS)
    dr._image.alpha_composite(im, (int(cx - W * s / 2), int(cy - 100 * s)))
    return dr


def scene1_title(t, dur):
    im = Image.new("RGBA", (W, H), (252, 250, 244, 255))
    dr = ImageDraw.Draw(im)
    p = (t) / 0.7
    s = 0.7 + 0.3 * ease_out_back(min(1.0, p))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 280), "THE DEEP", font=F(96), fill=(28, 28, 34, 255), anchor="mm")
    sub = Image.new("RGBA", (W, 80), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sub)
    ds.text((W / 2, 40), "hand-drawn stills + keyframe motion", font=F(36),
            fill=(90, 95, 110, 255), anchor="mm")
    a = min(1.0, t / 0.5)
    sub.putalpha(sub.getchannel("A").point(lambda v: int(v * a)))
    im.alpha_composite(sub, (0, 380))
    return im.convert("RGB")


def scene_angler(t, dur, subj, bgimg):
    """Slide-in from left with overshoot, idle bob, label pop, punch-in."""
    im = bgimg.copy().convert("RGBA")
    # subject position: slide from off-left with back-ease, then bob
    if t < 0.7:
        x = -300 + (W / 2 - 60 + 300) * ease_out_back(t / 0.7)
    else:
        x = W / 2 - 60
    x += 4 * math.sin(t * 2.0)
    y = H / 2 - 40 + 5 * math.sin(t * 1.6 + 1)
    im.alpha_composite(subj, (int(x - subj.width / 2), int(y - subj.height / 2)))
    dr = ImageDraw.Draw(im)
    pop_label(dr, "ANGLERFISH", W / 2, 620, 52, t, t0=1.0)
    # punch-in zoom from 1.6s
    if t > 1.6:
        p = ease_in_cubic(min(1.0, (t - 1.6) / (dur - 1.6)))
        z = 1.0 + 0.16 * p
        fx, fy = W / 2 - 60, H / 2 - 40
        cw, ch = W / z, H / z
        box = (max(0, int(fx - cw / 2)), max(0, int(fy - ch / 2)),
               min(W, int(fx + cw / 2)), min(H, int(fy + ch / 2)))
        im = im.crop(box).resize((W, H), Image.LANCZOS)
    return im.convert("RGB")


def scene_goblin(t, dur, subj, bgimg):
    """Quick swap: goblin shark slides in from right, label pops, then zoom."""
    im = bgimg.copy().convert("RGBA")
    if t < 0.6:
        x = W + 300 - (W + 300 - (W / 2 + 60)) * ease_out_back(t / 0.6)
    else:
        x = W / 2 + 60
    x += 4 * math.sin(t * 2.2 + 0.5)
    y = H / 2 - 30 + 5 * math.sin(t * 1.4 + 2)
    im.alpha_composite(subj, (int(x - subj.width / 2), int(y - subj.height / 2)))
    dr = ImageDraw.Draw(im)
    pop_label(dr, "GOBLIN SHARK", W / 2, 620, 52, t, t0=0.8)
    if t > 1.4:
        p = ease_in_cubic(min(1.0, (t - 1.4) / (dur - 1.4)))
        z = 1.0 + 0.16 * p
        fx, fy = W / 2 + 60, H / 2 - 30
        cw, ch = W / z, H / z
        box = (max(0, int(fx - cw / 2)), max(0, int(fy - ch / 2)),
               min(W, int(fx + cw / 2)), min(H, int(fy + ch / 2)))
        im = im.crop(box).resize((W, H), Image.LANCZOS)
    return im.convert("RGB")


def scene_parallax(t, dur, subj, bgimg):
    """Parallax pan: background pans left, subject drifts right (depth)."""
    # background pans left
    bg_w = int(W * 1.25)
    bg = bgimg.resize((bg_w, H), Image.LANCZOS)
    off = int((bg_w - W) * (t / dur))
    frame = bg.crop((off, 0, off + W, H)).convert("RGBA")
    # subject drifts right + bob (opposite = parallax depth)
    x = W / 2 + 40 + 90 * (t / dur) + 4 * math.sin(t * 2.0)
    y = H / 2 - 40 + 5 * math.sin(t * 1.6)
    frame.alpha_composite(subj, (int(x - subj.width / 2), int(y - subj.height / 2)))
    dr = ImageDraw.Draw(frame)
    pop_label(dr, "DEPTH — LAYERS MOVE APART", W / 2, 640, 42, t, t0=0.4)
    return frame.convert("RGB")


def scene_outro(t, dur):
    im = Image.new("RGBA", (W, H), (24, 28, 48, 255))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 320), "STILLS + KEYFRAMES = THE STYLE", font=F(54),
           fill=(255, 244, 214, 255), anchor="mm")
    d.text((W / 2, 400), "slide-in · bob · pop labels · punch-in · swap · parallax",
           font=F(32), fill=(190, 196, 220, 255), anchor="mm")
    if t > dur - 0.8:
        im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)),
                         (t - (dur - 0.8)) / 0.8)
    return im.convert("RGB")


def main():
    angler = isolate(ASSETS / "anglerfish.png")
    goblin = isolate(ASSETS / "goblinshark.png")
    bgimg = Image.open(ASSETS / "background.png").convert("RGBA").resize((W, H), Image.LANCZOS)
    angler.thumbnail((420, 420), Image.LANCZOS)
    goblin.thumbnail((420, 420), Image.LANCZOS)
    print("subjects:", angler.size, goblin.size)

    scenes = [
        (2.0, scene1_title),
        (3.4, lambda t, d: scene_angler(t, d, angler, bgimg)),
        (3.0, lambda t, d: scene_goblin(t, d, goblin, bgimg)),
        (3.0, lambda t, d: scene_parallax(t, d, angler, bgimg)),
        (2.0, scene_outro),
    ]
    seq = []
    for dur, fn in scenes:
        for i in range(int(dur * FPS)):
            t = i / FPS
            p = WORK / f"f_{len(seq):04d}.png"
            fn(t, dur).save(p)
            seq.append(str(p))
        print(f"scene done ({dur}s)")

    clip = ImageSequenceClip(seq, fps=FPS)
    out = HERE / "paint-style-demo.mp4"
    clip.write_videofile(str(out), fps=FPS, codec="libx264", preset="medium",
                         audio=False, logger=None)
    print(f"wrote {out} ({len(seq) / FPS:.1f}s)")


if __name__ == "__main__":
    main()
