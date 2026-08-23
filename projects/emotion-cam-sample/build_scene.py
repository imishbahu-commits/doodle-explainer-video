#!/usr/bin/env python3
"""Build the emotions sample scene: 4 shots, one emotion per shot,
keyframed camera move per shot (channel grammar), baked into a single
ae-motion scene, then rendered to mp4.

  shot 1  neutral   push_in       (the measured channel signature, +3.4%)
  shot 2  shocked   crash_zoom_in (punch)
  shot 3  sad       slow_drift    (ambient downbeat)
  shot 4  angry     pull_out      (back away)

Usage: .venv/bin/python projects/emotion-cam-sample/build_scene.py [--no-render]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skills" / "camera-router" / "scripts"))
sys.path.insert(0, str(REPO / "skills" / "ae-motion" / "scripts"))

import camera_moves as cm  # noqa: E402
import ae_motion  # noqa: E402
from PIL import Image  # noqa: E402

W, H, FPS = 1280, 720, 30
ASSETS = HERE / "assets"
CUT = ASSETS / "cut"

# (emotion, move, duration, caption)
SHOTS = [
    ("neutral", "push_in", 2.2, "content"),
    ("shocked", "crash_zoom_in", 1.3, "shocked!"),
    ("sad", "slow_drift", 2.2, "sad"),
    ("angry", "pull_out", 2.2, "furious"),
]
DUR = sum(s[2] for s in SHOTS)

BG_DEPTH = 0.8
CHAR_DEPTH = 1.0
CHAR_H = 520          # character height on canvas
CHAR_POS = (W / 2, 378)   # face lands ~38% down the frame
CAP_POS = (W / 2, H * 0.958)  # caption strip on the grass, below the figure


def cutout(emotion: str) -> Path:
    """Magic-wand cut the character card once; cache the result."""
    CUT.mkdir(exist_ok=True)
    out = CUT / f"peasant_{emotion}.png"
    if not out.exists():
        ae_motion.isolate(str(ASSETS / f"peasant_{emotion}.png")).save(out)
    return out


def baked_camera(move: str, t0: float, t1: float, layers: list) -> dict:
    """Per-shot camera: bake the move into absolute layer tracks, offset by t0.
    Camera resets at each cut (discontinuity hidden by the shot cut)."""
    dur = t1 - t0
    tracks = cm.make_tracks(move, dur=dur, W=W, H=H)
    baked = cm.bake(tracks, layers, W, H, dur)
    out = {}
    for lid, props in baked.items():
        out[lid] = {
            prop: [{**k, "t": round(k["t"] + t0, 3)} for k in ks]
            for prop, ks in props.items()
        }
    return out


def min_zoom_over_shots() -> float:
    """Smallest camera zoom across all shots (to margin the backdrop)."""
    zmin = 1.0
    for emo, move, d, _ in SHOTS:
        tr = cm.make_tracks(move, dur=d, W=W, H=H)
        for k in tr.get("zoom", []):
            zmin = min(zmin, float(k["v"]))
    return zmin


def cover_bg() -> Path:
    """Size the backdrop to cover the frame at EVERY point of the camera
    travel (pan/tilt offsets + min zoom + 2% safety) — no white edges."""
    p = ASSETS / "background_cover.png"
    d = BG_DEPTH
    mx_dx = mx_dy = 0.0
    mn_scale = 1.0
    for _emo, move, dur, _cap in SHOTS:
        tr = cm.make_tracks(move, dur=dur, W=W, H=H)
        for k in tr.get("pan", []):
            mx_dx = max(mx_dx, abs(k["v"]) / 100.0 * W * d)
        for k in tr.get("tilt", []):
            mx_dy = max(mx_dy, abs(k["v"]) / 100.0 * H * d)
        for k in tr.get("zoom", []):
            mn_scale = min(mn_scale, float(k["v"]) ** d)
    need_w = (W + 2 * mx_dx) / mn_scale
    need_h = (H + 2 * mx_dy) / mn_scale
    im = Image.open(ASSETS / "background.png").convert("RGB")
    s = max(need_w / im.width, need_h / im.height) * 1.02
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im.save(p)
    return p


def hold_keys(segs, val_on=1.0):
    """Hard-cut opacity: [{t, v, e:'hold'}...] stepping on/off at shot edges."""
    keys = [{"t": 0.0, "v": 0.0, "e": "hold"}]
    for t0, t1 in segs:
        keys += [{"t": t0, "v": val_on, "e": "hold"},
                 {"t": t1, "v": 0.0, "e": "hold"}]
    return keys


def main() -> int:
    # ---- pre-scale backdrop to cover (margin for the smallest zoom) ----
    zmin = min_zoom_over_shots()
    bg_path = cover_bg()
    bg_w, bg_h = Image.open(bg_path).size

    # ---- layer list (meta only, for the camera bake) ----
    layers_meta = [{"id": "bg", "depth": BG_DEPTH, "base_pos": [W / 2, H / 2]}]
    for i, (emo, _m, _d, _c) in enumerate(SHOTS):
        layers_meta.append({"id": f"char_{i}", "depth": CHAR_DEPTH,
                            "base_pos": list(CHAR_POS)})
        layers_meta.append({"id": f"cap_{i}", "depth": CHAR_DEPTH,
                            "base_pos": list(CAP_POS)})

    # ---- bake camera per shot and stitch ----
    cam = {lid: {"pos": [], "scale": [], "rot": []} for lid in
           {l["id"] for l in layers_meta}}
    t0 = 0.0
    for emo, move, d, _cap in SHOTS:
        t1 = t0 + d
        baked = baked_camera(move, t0, t1, layers_meta)
        for lid, props in baked.items():
            for prop in ("pos", "scale", "rot"):
                cam[lid][prop].extend(props[prop])
        t0 = t1
    for lid, props in cam.items():
        for prop in props:
            props[prop].sort(key=lambda k: k["t"])

    # ---- assemble scene ----
    scene = {"width": W, "height": H, "fps": FPS, "duration": round(DUR, 3),
             "motion_blur": 2,
             "layers": [
                 {"type": "image", "src": str(bg_path),
                  "isolate": False,
                  "tracks": cam["bg"]},
             ]}
    t0 = 0.0
    for i, (emo, _move, d, cap_text) in enumerate(SHOTS):
        t1 = t0 + d
        seg = [(t0, t1)]
        scene["layers"].append(
            {"type": "image", "src": str(cutout(emo)), "isolate": False,
             "max_dim": CHAR_H,   # integer: thumbnail fits a square box
             "tracks": {**cam[f"char_{i}"],
                        "opacity": hold_keys(seg)}})
        scene["layers"].append(
            {"type": "text", "text": cap_text, "size": 40,
             "fill": (20, 20, 24), "font": "hand",
             "tracks": {**cam[f"cap_{i}"],
                        "opacity": hold_keys(seg)}})
        t0 = t1

    scene_path = HERE / "scene_emotions.json"
    scene_path.write_text(json.dumps(scene, indent=1))
    print(f"scene: {scene_path}  ({DUR:.1f} s, {len(scene['layers'])} layers, "
          f"zoom floor {zmin:.3f}, backdrop {bg_w}x{bg_h})")

    if "--no-render" in sys.argv:
        return 0
    out = HERE / "sample_emotions.mp4"
    ae_motion.render_scene(scene, str(out), base_dir=str(HERE))
    print(f"video: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
