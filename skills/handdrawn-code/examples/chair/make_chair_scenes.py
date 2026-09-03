#!/usr/bin/env python3
"""Build the three 'sawing your own chair' scene JSONs for doodle.mjs.

A classic stick-figure explainer bit, made entirely from code:
  1. chair-1-sitting  — nervous figure, sweating, on a high-back chair (grey room)
  2. chair-2-sawing   — smug figure saws the chair's back post (dim room, hanging bulb)
  3. chair-3-broken   — smug figure surveys the broken, stuffed-out chair (teal room)

Everything is plain scene-JSON primitives (shape/line/circle/stick) — no
image model. Re-render with:
    node scripts/doodle.mjs examples/chair/chair-N-*.json --out out/chair-N
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
INK = "#16161a"
W, H = 1376, 768
WOOD = "#5C3B20"
WOOD_DARK = "#4A3018"
WOOD_LIGHT = "#7A5230"
MAROON = "#482826"
MAROON_DARK = "#3E211F"
MAROON_LIGHT = "#5D3A34"
DESK_TOP = "#4A3028"
DESK_PANEL = "#573A2C"
STUFF = "#E9DCC3"
HAIR = "#6B4A2E"

# ------------------------------------------------------------------ helpers
def rect(x0, y0, x1, y1):
    return [[round(x0), round(y0)], [round(x1), round(y0)],
            [round(x1), round(y1)], [round(x0), round(y1)]]

def shape(pts, fill=None, roughness=0.9, stroke_width=5, fill_style="solid"):
    e = {"type": "shape", "points": [[round(a), round(b)] for a, b in pts],
         "fillStyle": fill_style, "roughness": roughness, "strokeWidth": stroke_width}
    if fill:
        e["fill"] = fill
    return e

def line(x1, y1, x2, y2):
    return {"type": "line", "x1": round(x1), "y1": round(y1),
            "x2": round(x2), "y2": round(y2)}

def circle(x, y, r, fill, roughness=0.6):
    return {"type": "circle", "x": round(x), "y": round(y), "r": round(r),
            "fill": fill, "fillStyle": "solid", "roughness": roughness}

def polyline(pts):
    return [line(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]

def sweat(x, y, s=1.0, color="#C6E9F2"):
    """Teardrop sweat mark, pointed end up."""
    pts = [(0, -16), (6, -7), (8, 1), (4, 8), (0, 11), (-4, 8), (-8, 1), (-6, -7)]
    return shape([(x + a * s, y + b * s) for a, b in pts], fill=color,
                 roughness=1.2, stroke_width=2.5)

def hair_crown(cx, cy, s, color=HAIR):
    """Spiky hair crown sitting on a stick head (local head radius 46*s)."""
    bases = [150, 120, 90, 60, 30]
    tips = [135, 105, 75, 45]
    pts = [(-44, -14)]
    for i, b in enumerate(bases):
        pts.append((46 * math.cos(math.radians(b)), -46 * math.sin(math.radians(b))))
        if i < len(tips):
            t = tips[i]
            pts.append((64 * math.cos(math.radians(t)), -64 * math.sin(math.radians(t))))
    pts.append((44, -14))
    return shape([(cx + a * s, cy + b * s) for a, b in pts], fill=color,
                 roughness=1.0, stroke_width=4)

def flyaways(cx, cy, s):
    """A few nervous hairs above the crown."""
    out = []
    for dx, dy1, dy2, bend in [(-40, -170, -200, -6), (0, -176, -208, 0), (40, -172, -202, 6)]:
        out.append(line(cx + dx * s, cy + dy1 * s, cx + (dx + bend) * s, cy + dy2 * s))
    return out

def stuffing(cx, cy, spread, seed, base_r=17):
    """Lumpy stuffing mound: overlapping blobs (visible lump outlines)."""
    rnd = random.Random(seed)
    el = []
    n = max(3, int(spread / 26))
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        x = cx - spread / 2 + t * spread
        arc = math.sin(t * math.pi) * base_r * 0.55   # middle lumps sit higher
        el.append(circle(x, cy - arc + rnd.uniform(-3, 3),
                         base_r * rnd.uniform(0.8, 1.15), STUFF, roughness=0.8))
    for i in range(max(2, n // 2)):
        t = (i + 0.5) / max(2, n // 2)
        x = cx - spread / 2 + t * spread
        el.append(circle(x + rnd.uniform(-6, 6),
                         cy - base_r * 1.35 + rnd.uniform(-4, 4),
                         base_r * rnd.uniform(0.45, 0.6), STUFF, roughness=0.8))
    return el

def saw_blade(x1, y1, x2, y2, thick=34, teeth=9, depth=10, fill="#C9CDD3"):
    """Hand-saw: flat top edge, zigzag teeth along the bottom, from handle to tip."""
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    n1x, n1y = -uy, ux
    if n1y > 0:  # want n1 pointing "up" (negative y)
        n1x, n1y = uy, -ux
    h = thick / 2
    a_top = (x1 + n1x * h, y1 + n1y * h)
    b_top = (x2 + n1x * h, y2 + n1y * h)
    b_bot = (x2 - n1x * h, y2 - n1y * h)
    a_bot = (x1 - n1x * h, y1 - n1y * h)
    vx, vy = a_bot[0] - b_bot[0], a_bot[1] - b_bot[1]
    pts = [a_top, b_top, b_bot]
    for i in range(1, 2 * teeth + 1):
        px = b_bot[0] + vx * i / (2 * teeth + 1)
        py = b_bot[1] + vy * i / (2 * teeth + 1)
        if i % 2:
            px += -n1x * depth
            py += -n1y * depth
        pts.append((px, py))
    pts.append(a_bot)
    return shape(pts, fill=fill, roughness=0.8, stroke_width=4)

def floor(bg_floor, y=700):
    return [shape(rect(0, y, W, H), fill=bg_floor, roughness=0.6, stroke_width=3),
            line(0, y, W, y)]

# stick geometry (scale s, param y): feet=y+63s, hip=y-55s, neck=y-159s,
# head centre=(x, y-205s) r=46s; sit knees at (x±48s, y-25s); hold hands
# (flipped) at (x-88s, neck+95s) and (x-78s, neck+86s).
def head_centre(x, y, s):
    return (x, y - 205 * s, 46 * s)

# ---------------------------------------------------------------- scene 1
def scene1():
    s, x, y = 2.2, 560, 679          # butt on seat (558), feet near floor (704)
    hx, hy, hr = head_centre(x, y, s)
    el = []
    el += floor("#C8C5BA", 704)
    # desk, right edge
    el.append(shape(rect(1180, 412, W, 448), fill=DESK_TOP))
    el.append(shape(rect(1240, 448, W, 704), fill=DESK_PANEL))
    # high-back chair, dark maroon
    el.append(shape([[505, 558], [539, 558], [527, 320], [493, 320]], fill=MAROON))
    el.append(shape(rect(450, 558, 670, 584), fill=MAROON))
    el.append(shape([[478, 584], [492, 584], [488, 698], [474, 698]], fill=MAROON_LIGHT, stroke_width=4))
    el.append(shape([[628, 584], [642, 584], [646, 698], [632, 698]], fill=MAROON_LIGHT, stroke_width=4))
    el.append(shape(rect(472, 648, 648, 660), fill=MAROON_DARK, stroke_width=4))
    el.append(shape([[450, 584], [468, 584], [461, 704], [443, 704]], fill=MAROON_DARK))
    el.append(shape([[652, 584], [670, 584], [677, 704], [659, 704]], fill=MAROON_DARK))
    # figure + face
    el.append(circle(hx, hy, hr - 1.5, "#FFFFFF", roughness=0.8))   # white head
    el.append({"type": "stick", "x": x, "y": y, "scale": s, "pose": "sit"})
    el.append(line(454, 624, 426, 704))          # shins (sit pose has no shins)
    el.append(line(666, 624, 694, 704))
    el.append(line(426, 704, 402, 708))          # feet
    el.append(line(694, 704, 718, 708))
    el += flyaways(hx, hy, s)
    el.append(hair_crown(hx, hy, s))
    el.append(circle(hx - 42, hy + 8, 17, INK, roughness=0.4))
    el.append(circle(hx + 42, hy + 8, 17, INK, roughness=0.4))
    el.append(line(hx - 66, hy - 50, hx - 24, hy - 70))   # worried brows
    el.append(line(hx + 24, hy - 70, hx + 66, hy - 50))
    mouth = [(hx - 42, hy + 72), (hx - 27, hy + 83), (hx - 12, hy + 72),
             (hx + 3, hy + 83), (hx + 18, hy + 72), (hx + 33, hy + 83), (hx + 45, hy + 76)]
    el += polyline(mouth)
    el.append(sweat(hx - 92, hy - 14, 1.2))
    el.append(sweat(hx - 52, hy - 80, 0.95))
    el.append(sweat(hx + 94, hy - 32, 1.2))
    el.append(sweat(hx + 88, hy + 58, 0.9))
    el.append(sweat(hx + 44, hy - 88, 0.85))
    return {"width": W, "height": H, "bg": "#B2B2AE", "seed": 11,
            "roughness": 1.2, "ink": 1.5, "elements": el}

# ---------------------------------------------------------------- scene 2
def scene2():
    s, x, y = 2.1, 940, 568          # feet on floor (700)
    hx, hy, hr = head_centre(x, y, s)
    el = []
    el.append(shape(rect(790, 0, W, 700), fill="#2C343B", roughness=0.5, stroke_width=3))
    el.append(line(790, 0, 790, 700))
    el += floor("#3A4046", 700)
    # hanging bulb
    el.append(line(470, 0, 470, 138))
    el.append(shape(rect(456, 138, 484, 156), fill="#697077", stroke_width=4))
    el.append(circle(470, 194, 40, "#F5D86A", roughness=0.7))
    el.append(line(456, 198, 463, 184)); el.append(line(463, 184, 471, 198))
    el.append(line(471, 198, 478, 184))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        el.append(line(470 + 50 * math.cos(a), 194 + 50 * math.sin(a),
                       470 + 68 * math.cos(a), 194 + 68 * math.sin(a)))
    # simple wooden chair
    el.append(shape(rect(600, 428, 624, 584), fill=WOOD))
    el.append(shape(rect(584, 584, 764, 610), fill=WOOD))
    el.append(shape(rect(628, 610, 642, 696), fill=WOOD_LIGHT, stroke_width=4))
    el.append(shape(rect(724, 610, 738, 696), fill=WOOD_LIGHT, stroke_width=4))
    el.append(shape(rect(606, 652, 748, 664), fill=WOOD, stroke_width=4))
    el.append(shape(rect(592, 610, 610, 700), fill=WOOD_DARK))
    el.append(shape(rect(742, 610, 760, 700), fill=WOOD_DARK))
    # figure: flipped, holding the saw (hands at ~755,434 / ~776,415)
    el.append(circle(hx, hy, hr - 1.5, "#FFFFFF", roughness=0.8))
    el.append({"type": "stick", "x": x, "y": y, "scale": s, "pose": "hold", "flip": True})
    el.append(hair_crown(hx, hy, s))
    el.append(circle(hx - 45, hy + 8, 15, INK, roughness=0.4))
    el.append(circle(hx + 45, hy + 8, 15, INK, roughness=0.4))
    el.append(line(hx - 70, hy - 52, hx - 28, hy - 66))   # determined brows
    el.append(line(hx + 28, hy - 66, hx + 70, hy - 52))
    el.append(line(hx - 76, hy + 34, hx - 8, hy + 50))    # wide gap-tooth smirk
    el.append(line(hx + 10, hy + 48, hx + 78, hy + 38))   # (corners up, centre down)
    el.append(line(hx - 4, hy + 42, hx + 6, hy + 40))     # tooth in the gap
    # hand saw: blade tip bites into the back post (600-624, 428-584)
    el.append(saw_blade(753, 436, 560, 502))
    el.append(shape([[742, 398], [792, 404], [786, 452], [738, 446]],
                    fill="#8A5A28", roughness=0.8, stroke_width=4))
    return {"width": W, "height": H, "bg": "#49545E", "seed": 22,
            "roughness": 1.2, "ink": 1.5, "elements": el}

# ---------------------------------------------------------------- scene 3
def scene3():
    s, x, y = 2.1, 430, 568
    hx, hy, hr = head_centre(x, y, s)
    el = []
    el.append(shape(rect(0, 0, 577, 646), fill="#6FB2B6", roughness=0.5, stroke_width=3))
    el.append(line(577, 0, 577, 646))
    el += floor("#B5A293", 646)
    # desk, right edge
    el.append(shape(rect(1238, 392, W, 428), fill=DESK_TOP))
    el.append(shape(rect(1298, 428, W, 646), fill=DESK_PANEL))
    # broken chair: split back with crack, stuffed out
    el.append(shape([[884, 352], [934, 344], [940, 560], [900, 566]], fill=WOOD))
    el.append(shape([[950, 340], [998, 348], [992, 560], [952, 562]], fill=WOOD))
    el += polyline([(936, 352), (946, 400), (938, 450), (948, 500), (940, 556)])
    el += stuffing(968, 430, 52, seed=7, base_r=12)        # tuft on the slat
    el.append(shape([[878, 560], [1010, 566], [1014, 594], [882, 590]], fill=WOOD_DARK))
    el.append(shape(rect(894, 590, 910, 646), fill=WOOD_DARK, stroke_width=4))
    el.append(shape(rect(984, 594, 1000, 646), fill=WOOD_DARK, stroke_width=4))
    el.append(shape(rect(918, 592, 932, 642), fill=WOOD_LIGHT, stroke_width=4))
    el.append(shape(rect(954, 594, 968, 642), fill=WOOD_LIGHT, stroke_width=4))
    el += stuffing(944, 546, 150, seed=5, base_r=19)       # pile on the seat
    # figure, same scale as scene 2 — surveying the damage
    el.append(circle(hx, hy, hr - 1.5, "#FFFFFF", roughness=0.8))
    el.append({"type": "stick", "x": x, "y": y, "scale": s, "pose": "stand"})
    el.append(hair_crown(hx, hy, s))
    el.append(circle(hx - 45, hy + 8, 15, INK, roughness=0.4))
    el.append(circle(hx + 45, hy + 8, 15, INK, roughness=0.4))
    el.append(line(hx - 74, hy - 52, hx - 26, hy - 64))
    el.append(line(hx + 26, hy - 64, hx + 74, hy - 52))
    el.append(line(hx - 76, hy + 34, hx - 8, hy + 50))    # same smug smirk
    el.append(line(hx + 10, hy + 48, hx + 78, hy + 38))
    el.append(line(hx - 4, hy + 42, hx + 6, hy + 40))
    return {"width": W, "height": H, "bg": "#7CC4C7", "seed": 33,
            "roughness": 1.2, "ink": 1.5, "elements": el}

# ------------------------------------------------------------------- main
def main():
    scenes = {
        "chair-1-sitting.json": scene1(),
        "chair-2-sawing.json": scene2(),
        "chair-3-broken.json": scene3(),
    }
    for name, scene in scenes.items():
        out = HERE / name
        out.write_text(json.dumps(scene, indent=1), encoding="utf-8")
        print(f"wrote {out}")

if __name__ == "__main__":
    main()
