#!/usr/bin/env python3
"""ae_motion.py — After-Effects-grade keyframe engine for still PNGs.

Implements AE's keyframe semantics in pure Python+PIL:
  - per-property tracks: pos / scale / rot / opacity / text-scale / pin drags
  - cubic-bezier easing (AE's own curve presets), incl. easeOutBack overshoot
  - "hold" keyframes (no interpolation, like AE)
  - puppet pins (rigid MLS warp) whose drags are keyframed — part-motion
    INSIDE a PNG (fins, tails, limbs)
  - motion blur by temporal sub-frame accumulation (true AE-style blur)
  - a script-aware move chooser: --plan reads a narration beat and picks
    the right move (see SKILL.md decision tree)

Frames pipe straight to ffmpeg — no moviepy. Usage:
  python3 ae_motion.py scene.json -o out.mp4
  python3 ae_motion.py --plan "Forty eight percent saw a monster."
  python3 ae_motion.py --isolate subject.png
"""

import argparse
import json
import math
import subprocess
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------- AE easings
# exact After Effects / CSS cubic-bezier presets: y(t) solved from x(t)
EASINGS = {
    "linear":     (0.0, 0.0, 1.0, 1.0),
    "easeInOut":  (0.42, 0.0, 0.58, 1.0),
    "easeIn":     (0.42, 0.0, 1.0, 1.0),
    "easeOut":    (0.0, 0.0, 0.58, 1.0),
    "easeInCubic":(0.55, 0.055, 0.675, 0.19),
    "easeOutCubic":(0.215, 0.61, 0.355, 1.0),
    "easeInOutCubic":(0.645, 0.045, 0.355, 1.0),
    "easeOutExpo":(0.16, 1.0, 0.3, 1.0),
    "easeOutBack":(0.175, 0.885, 0.32, 1.275),
    "easeInBack": (0.6, -0.28, 0.735, 0.045),
}


def bezier_y(x, cx1, cy1, cx2, cy2):
    """Solve t for x(t)=x (Newton) and return y(t) — cubic-bezier easing."""
    x = max(0.0, min(1.0, x))
    t = x
    for _ in range(8):
        a = 1 - t
        xt = 3 * a * a * t * cx1 + 3 * a * t * t * cx2 + t * t * t
        dxt = (3 * a * a * cx1 + 6 * a * t * (cx2 - cx1) + 3 * t * t * (1 - cx2))
        if abs(dxt) < 1e-9:
            break
        t -= (xt - x) / dxt
        t = max(0.0, min(1.0, t))
    a = 1 - t
    return 3 * a * a * t * cy1 + 3 * a * t * t * cy2 + t * t * t


def sample_track(track, t):
    """Sample an AE-style track at time t. key = {t, v, e}."""
    if t <= track[0]["t"]:
        return track[0]["v"]
    if t >= track[-1]["t"]:
        return track[-1]["v"]
    for i in range(len(track) - 1):
        k0, k1 = track[i], track[i + 1]
        if k0["t"] <= t <= k1["t"]:
            if k1.get("e") == "hold":
                return k0["v"]
            u = (t - k0["t"]) / max(1e-6, k1["t"] - k0["t"])
            e = EASINGS.get(k1.get("e", "easeInOut"), EASINGS["easeInOut"])
            y = bezier_y(u, *e)
            if isinstance(k0["v"], (list, tuple)):
                return tuple(k0["v"][j] + (k1["v"][j] - k0["v"][j]) * y
                             for j in range(len(k0["v"])))
            return k0["v"] + (k1["v"] - k0["v"]) * y
    return track[-1]["v"]


# -------------------------------------------------------------- puppet warp
def isolate(path):
    """Magic-wand: flood-fill the flat background from the borders."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    h, w = a.shape[:2]
    corner = a[2, 2, :3].astype(int)
    bg = (abs(a[:, :, 0].astype(int) - corner[0]) < 30) & \
         (abs(a[:, :, 1].astype(int) - corner[1]) < 30) & \
         (abs(a[:, :, 2].astype(int) - corner[2]) < 30)
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


def mls_rigid(img, pins, drags, chunk=30000):
    """Rigid MLS warp (Schaefer 2006, analytic rotation) — Photopea's
    puppet-warp math. pins: (n,2), drags: (n,2) deltas."""
    a = np.array(img).astype(float)
    h, w = a.shape[:2]
    p = np.asarray(pins, float)
    q = p + np.asarray(drags, float)
    out = np.zeros_like(a)
    ys, xs = np.mgrid[0:h, 0:w]
    pts = np.stack([xs.ravel(), ys.ravel()], -1)
    total = len(pts)
    for s in range(0, total, chunk):
        e = min(s + chunk, total)
        x = pts[s:e]
        d = x[:, None, :] - p[None, :, :]
        dist2 = np.sum(d * d, axis=-1) + 1e-10
        wgt = 1.0 / dist2
        wsum = wgt.sum(1)
        pstar = (wgt[:, :, None] * p[None]).sum(1) / wsum[:, None]
        qstar = (wgt[:, :, None] * q[None]).sum(1) / wsum[:, None]
        phat = p[None] - pstar[:, None, :]
        qhat = q[None] - qstar[:, None, :]
        H = np.einsum("nk,nki,nkj->nij", wgt, phat, qhat)
        h1 = H[:, 0, 0] + H[:, 1, 1]
        h2 = H[:, 1, 0] - H[:, 0, 1]
        mu = np.sqrt(h1 * h1 + h2 * h2) + 1e-12
        R = np.stack([np.stack([h1, h2], -1),
                      np.stack([-h2, h1], -1)], -1) / mu[..., None, None]
        xnew = np.einsum("nij,nj->ni", R, x - pstar) + qstar
        gx = np.clip(np.round(xnew[:, 0]).astype(int), 0, w - 1)
        gy = np.clip(np.round(xnew[:, 1]).astype(int), 0, h - 1)
        out[ys.ravel()[s:e], xs.ravel()[s:e]] = a[gy, gx]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def auto_rig(img):
    """Spine pins + extreme-point drag pins (tail/wings/feet tips)."""
    a = np.array(img)
    m = a[:, :, 3] > 40
    ys, xs = np.where(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cx = (x0 + x1) / 2
    spine = [(cx, y0 + (y1 - y0) * f) for f in (0.15, 0.45, 0.75)]
    # extremes of the middle band = left/right tips
    mid = m[y0 + (y1 - y0) // 3: y0 + 2 * (y1 - y0) // 3, :]
    l = int(np.where(mid.any(axis=0))[0].min())
    r = int(np.where(mid.any(axis=0))[0].max())
    drags = [len(spine), len(spine) + 1]
    pins = spine + [(l, y0 + (y1 - y0) * 0.45), (r, y0 + (y1 - y0) * 0.45)]
    return pins, drags


# ------------------------------------------------------------------ render
HERE = Path(__file__).resolve().parent
FONT_DIR = HERE.parent / "fonts"

# hand-drawn fonts (OFL-licensed, shipped with the skill) + fallback
FONT_MAP = {
    "hand": FONT_DIR / "caveat-700.ttf",        # loose marker hand
    "hand-note": FONT_DIR / "patrick-hand.ttf", # neat pencil note
    "hand-bold": FONT_DIR / "kalam-700.ttf",    # heavy marker
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}


def draw_text(text, size, fill=(28, 28, 34), w=1280, font_name="hand"):
    path = FONT_MAP.get(font_name, FONT_MAP["sans"])
    try:
        fnt = ImageFont.truetype(str(path), size)
    except Exception:
        fnt = ImageFont.load_default()
    tmp = Image.new("RGBA", (w, size * 3), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((w / 2, size * 1.5), text, font=fnt,
                             fill=fill + (255,), anchor="mm")
    return tmp.crop(tmp.getbbox())


def render_scene(scene, out_path, base_dir=None):
    W = scene.get("width", 1280)
    H = scene.get("height", 720)
    fps = scene.get("fps", 30)
    dur = scene["duration"]
    n_frames = max(1, round(dur * fps))
    blur = max(1, scene.get("motion_blur", 1))
    base_dir = Path(base_dir or ".")

    bg_src = scene.get("background")
    if bg_src:
        p = Path(bg_src)
        if not p.is_absolute():
            p = base_dir / p
        bg = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
    else:
        c = scene.get("bg_color", (255, 255, 255, 255))
        bg = Image.new("RGBA", (W, H), tuple(c))

    layers = []
    for spec in scene.get("layers", []):
        if spec["type"] == "text":
            base = draw_text(spec.get("text", ""), spec.get("size", 48),
                             fill=tuple(spec.get("fill", (28, 28, 34))),
                             font_name=spec.get("font", "hand"))
        elif spec["type"] == "image":
            src = Path(spec["src"])
            if not src.is_absolute():
                src = base_dir / src
            base = (isolate(src) if spec.get("isolate", True)
                    else Image.open(src).convert("RGBA"))
            md = spec.get("max_dim")
            if md:
                base.thumbnail((md, md), Image.LANCZOS)
        else:
            continue
        # puppet rig (part-motion inside the PNG)
        rig = None
        if spec.get("puppet"):
            pins, drag_idx = auto_rig(base)
            rig = (pins, drag_idx)
        layers.append((spec, base, rig))

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
        stdin=subprocess.PIPE)

    warp_cache = {}   # rounded drag tuple -> warped image (one warp per pose)

    def warp_cached(base, pins, drags):
        key = tuple((round(d[0]), round(d[1])) for d in drags)
        if key not in warp_cache:
            warp_cache[key] = mls_rigid(base, pins, drags)
        return warp_cache[key]

    def draw_at(t):
        frame = bg.copy()
        for spec, base, rig in layers:
            # puppet: drags are keyframed tracks named drag0, drag1, ...
            img = base
            if rig and "puppet" in spec:
                pins, drag_idx = rig
                drags = [[0.0, 0.0] for _ in pins]
                for i, di in enumerate(drag_idx):
                    tr = spec["puppet"].get("tracks", {}).get(f"drag{i}")
                    if tr:
                        drags[di] = list(sample_track(tr, t))
                img = warp_cached(base, pins, drags)
            tr = spec.get("tracks", {})
            pos = sample_track(tr["pos"], t) if "pos" in tr else (W / 2, H / 2)
            rot = sample_track(tr["rot"], t) if "rot" in tr else 0.0
            scale = sample_track(tr["scale"], t) if "scale" in tr else 1.0
            opa = sample_track(tr["opacity"], t) if "opacity" in tr else 1.0
            if rot:
                img = img.rotate(rot, expand=True, resample=Image.BICUBIC)
            if scale != 1.0:
                img = img.resize((max(1, round(img.width * scale)),
                                  max(1, round(img.height * scale))),
                                 Image.LANCZOS)
            if opa < 1.0:
                img = img.copy()
                img.putalpha(img.getchannel("A").point(
                    lambda p: int(p * max(0.0, min(1.0, opa)))))
            frame.alpha_composite(
                img, (round(pos[0] - img.width / 2),
                      round(pos[1] - img.height / 2)))
        return frame.convert("RGB")

    for i in range(n_frames):
        # motion blur: accumulate sub-frame samples
        acc = None
        for s in range(blur):
            t = (i + (s + 0.5) / blur) / fps
            f = draw_at(min(t, dur - 1e-4))
            f = np.asarray(f, dtype=np.float32)
            acc = f if acc is None else acc + f
        frame = (acc / blur).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    return out_path


# -------------------------------------------------------------- move planner
def plan_move(text):
    """Conservative measured-profile suggestion; never invent camera motion."""
    t = text.lower()
    if any(w in t for w in ["eats", "bites", "waves", "swims", "crawls", "runs", "attacks", "grabs", "opens"]):
        return {"move": "local-part-action", "why": "the subject acts — animate only the named tail/fin/limb/prop for one beat",
                "shape": [{"t": 0, "v": [0, 0], "e": "hold"},
                          {"t": 0.4, "v": [0, 34], "e": "easeInOut"},
                          {"t": 0.8, "v": [0, 34], "e": "hold"}]}
    if any(w in t for w in ["not ", "never", "no ", "wrong", "false", "mistake"]):
        return {"move": "source-swap-or-local-x", "why": "negation — use a semantic cut/swap or draw one local X",
                "shape": [{"t": 0, "v": 0, "e": "hold"}, {"t": 0.067, "v": 1, "e": "hold"}]}
    if any(w in t for w in [" percent", "%", " thousand", " million", " in 19", " in 18", " in 20", " in two"]):
        return {"move": "cut-to-labeled-plate", "why": "stat/date — cut to a legible static plate 1–2 frames before the term",
                "shape": [{"t": -0.067, "v": 1, "e": "hold"}]}
    if any(w in t for w in ["first", "second", "third", "next", "also", "another", "then"]):
        return {"move": "hard-cut-or-source-swap", "why": "new list/state — do not auto-stagger; follow noun timing",
                "shape": [{"t": -0.067, "v": 1, "e": "hold"}]}
    return {"move": "hold-or-hard-cut", "why": "default — keep the camera and idle elements still; cut 1–2 frames before the noun when a visual change is necessary",
            "shape": [{"t": -0.067, "v": 1, "e": "hold"}]}


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?", help="scene JSON")
    ap.add_argument("-o", "--out", default="out.mp4")
    ap.add_argument("--plan", help="narration beat → recommended move")
    ap.add_argument("--isolate", help="PNG → magic-wand cut (prints bbox)")
    args = ap.parse_args()

    if args.plan:
        print(json.dumps(plan_move(args.plan), indent=2))
        return
    if args.isolate:
        im = isolate(args.isolate)
        print(f"cut: {im.size} bbox ok")
        im.save("cut.png")
        return
    if not args.scene:
        ap.print_help()
        return
    scene = json.loads(Path(args.scene).read_text())
    out = render_scene(scene, args.out, base_dir=Path(args.scene).resolve().parent)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
