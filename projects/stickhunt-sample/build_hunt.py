#!/usr/bin/env python3
"""Build the stickfigure-hunts-mammoth scene: a 6-shot sequence in an ancient
landscape, each shot a DIFFERENT keyframed camera move (channel-style hard
cuts, per-shot camera reset, 2.5D depth parallax).

  shot 1  stand        push_in        (slow establish, channel signature)
  shot 2  stand        slow_drift     (ready, ambient)
  shot 3  lunge        truck_right    (follow the charge)
  shot 4  throw        crash_zoom_in  (punch on the throw)
  shot 5  throw        handheld_shake (impact on the mammoth)
  shot 6  celebrate    crane_up       (victory, rise)

Usage: .venv/bin/python projects/stickhunt-sample/build_hunt.py [--no-render]
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
BG_DEPTH = 0.8
CHAR_DEPTH = 1.0

HUNTER_X, HUNTER_FOOT = 300, 620   # left third, feet on the ground line
MAM_X, MAM_FOOT = 950, 620         # right side
HUNTER_H = 200                      # displayed hunter height
MAM_H = 400                         # displayed mammoth height

# (move, duration, hunter_pose)
SHOTS = [
    ("push_in",        2.2, "stand"),
    ("slow_drift",     1.6, "stand"),
    ("truck_right",    1.4, "lunge"),
    ("crash_zoom_in",  1.2, "throw"),
    ("handheld_shake", 1.6, "throw"),
    ("crane_up",       2.0, "celebrate"),
]
DUR = sum(s[1] for s in SHOTS)


def travel_margin():
    """Worst-case bg-layer travel across all shots (pan/tilt px + min zoom)."""
    d = BG_DEPTH
    mx_dx = mx_dy = 0.0
    mn_zoom = 1.0
    for move, dur, _p in SHOTS:
        tr = cm.make_tracks(move, dur=dur, W=W, H=H)
        for k in tr.get("pan", []):
            mx_dx = max(mx_dx, abs(k["v"]) / 100.0 * W * d)
        for k in tr.get("tilt", []):
            mx_dy = max(mx_dy, abs(k["v"]) / 100.0 * H * d)
        for k in tr.get("zoom", []):
            mn_zoom = min(mn_zoom, float(k["v"]) ** d)
    return mx_dx, mx_dy, mn_zoom


def cover_bg() -> Path:
    """Size the backdrop so it covers the frame at EVERY point of the camera
    travel (pan/tilt offsets + min zoom + 2% safety) — no white edges ever."""
    p = ASSETS / "ancient_background_cover.png"
    mx_dx, mx_dy, mn_scale = travel_margin()
    need_w = (W + 2 * mx_dx) / mn_scale
    need_h = (H + 2 * mx_dy) / mn_scale
    im = Image.open(ASSETS / "ancient_background.png").convert("RGB")
    s = max(need_w / im.width, need_h / im.height) * 1.02
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im.save(p)
    return p


def max_dim_for(path: Path, target_h: int) -> int:
    """Square-box max_dim that makes the cutout's displayed height = target_h."""
    w, h = Image.open(path).size
    return round(target_h * max(w, h) / h)


def foot_center(cut_path: Path, target_h: int, cx: int, foot_y: int):
    """Center x keeps cx; center y puts the cutout's bottom on the ground line."""
    w, h = Image.open(cut_path).size
    disp_h = target_h
    disp_w = round(disp_h * w / h)
    return [round(cx), round(foot_y - disp_h / 2)]


def baked_camera(move, t0, t1, layers):
    dur = t1 - t0
    tracks = cm.make_tracks(move, dur=dur, W=W, H=H)
    baked = cm.bake(tracks, layers, W, H, dur)
    return {lid: {prop: [{**k, "t": round(k["t"] + t0, 3)} for k in ks]
                  for prop, ks in props.items()}
            for lid, props in baked.items()}


def hold_keys(segs, val_on=1.0):
    keys = [{"t": 0.0, "v": 0.0, "e": "hold"}]
    for t0, t1 in segs:
        keys += [{"t": t0, "v": val_on, "e": "hold"},
                 {"t": t1, "v": 0.0, "e": "hold"}]
    return keys


def main() -> int:
    bg_path = cover_bg()

    poses = {p: ASSETS / f"cut_hunter_{p}2.png" for p in
             ("stand", "lunge", "throw", "celebrate")}
    mam = ASSETS / "cut_mammoth.png"

    # layer meta for the camera bake
    layers_meta = [{"id": "bg", "depth": BG_DEPTH, "base_pos": [W / 2, H / 2]}]
    layers_meta.append({"id": "mam", "depth": CHAR_DEPTH,
                        "base_pos": foot_center(mam, MAM_H, MAM_X, MAM_FOOT)})
    for p in poses:
        layers_meta.append({"id": f"hu_{p}", "depth": CHAR_DEPTH,
                            "base_pos": foot_center(poses[p], HUNTER_H,
                                                    HUNTER_X, HUNTER_FOOT)})

    cam = {l["id"]: {"pos": [], "scale": [], "rot": []} for l in layers_meta}
    t0 = 0.0
    for _m, d, _p in SHOTS:
        t1 = t0 + d
        for lid, props in baked_camera(_m, t0, t1, layers_meta).items():
            for prop in ("pos", "scale", "rot"):
                cam[lid][prop].extend(props[prop])
        t0 = t1
    for lid, props in cam.items():
        for prop in props:
            props[prop].sort(key=lambda k: k["t"])

    scene = {"width": W, "height": H, "fps": FPS, "duration": round(DUR, 3),
             "motion_blur": 2,
             "layers": [
                 {"type": "image", "src": str(bg_path), "isolate": False,
                  "tracks": cam["bg"]},
                 {"type": "image", "src": str(mam), "isolate": False,
                  "max_dim": max_dim_for(mam, MAM_H),
                  "tracks": {**cam["mam"],
                              "opacity": [{"t": 0, "v": 1, "e": "hold"}]}},
             ]}
    t0 = 0.0
    for _m, d, p in SHOTS:
        t1 = t0 + d
        scene["layers"].append(
            {"type": "image", "src": str(poses[p]), "isolate": False,
             "max_dim": max_dim_for(poses[p], HUNTER_H),
             "tracks": {**cam[f"hu_{p}"],
                        "opacity": hold_keys([(t0, t1)])}})
        t0 = t1

    scene_path = HERE / "scene_hunt.json"
    scene_path.write_text(json.dumps(scene, indent=1))
    print(f"scene: {scene_path}  ({DUR:.1f} s, {len(scene['layers'])} layers)")

    if "--no-render" in sys.argv:
        return 0
    out = HERE / "stickfigure_hunts_mammoth.mp4"
    ae_motion.render_scene(scene, str(out), base_dir=str(HERE))
    print(f"video: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
