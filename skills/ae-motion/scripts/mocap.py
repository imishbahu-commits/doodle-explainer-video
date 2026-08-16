#!/usr/bin/env python3
"""mocap.py — apply recorded human motion (BVH mocap) to a hand-drawn PNG.

Motion data: MIT-licensed BVH clips from Meta's Animated Drawings project
(facebookresearch/AnimatedDrawings, examples/bvh/fair1/). Parse the BVH,
forward-kinematics the skeleton, project it to 2D, retarget the joints onto
the character's bounding box, then deform the drawing with the ARAP engine
(arap.py) so the hand-drawn character performs the recorded move.

Usage:
    python3 mocap.py scene.json -o out.mp4

scene.json:
{
  "width": 1280, "height": 720, "fps": 60,
  "background": "background.png",
  "character": {
    "image": "character.png",          # isolated PNG (white bg or alpha)
    "x": 640, "y": 560, "height": 520, # where it stands, how tall
    "joints": { ... }                  # optional manual joints (fractions)
  },
  "motion": { "bvh": "motions/dab.bvh", "start": 0.5, "duration": 3.0 }
}
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from arap import deform_image

HERE = Path(__file__).resolve().parent
MOTIONS = HERE.parent / "motions"

# ---------------------------------------------------------------- BVH parse
def parse_bvh(path):
    """Returns (joints, channels_per_joint, frames). joints = list of
    (name, offset_xyz, parent_idx); frames = (n_frames, n_channels)."""
    text = Path(path).read_text()
    lines = [ln.strip() for ln in text.splitlines()]

    joints = []          # (name, offset, parent)
    stack = [-1]
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("ROOT") or ln.startswith("JOINT"):
            name = ln.split()[1]
            parent = stack[-1]
            stack.append(len(joints))
            joints.append([name, np.zeros(3), parent])
        elif ln.startswith("OFFSET"):
            parts = ln.split()
            joints[stack[-1]][1] = np.array(
                [float(parts[1]), float(parts[2]), float(parts[3])])
        elif ln == "{":
            pass
        elif ln == "}":
            if len(stack) > 1:
                stack.pop()
        elif ln.startswith("End Site"):
            # skip the whole End Site block: "End Site" "{" "OFFSET.." "}"
            j = i + 1
            while j < len(lines) and lines[j] != "}":
                j += 1
            i = j  # the loop's trailing i += 1 then moves past the "}"
        elif ln.startswith("MOTION"):
            break
        i += 1

    # motion section
    frame_time = 1.0 / 30.0
    frames = []
    j = i
    while j < len(lines):
        if lines[j].startswith("Frame Time:"):
            frame_time = float(lines[j].split(":")[1].strip())
        elif lines[j].startswith("Frames:"):
            pass
        elif lines[j] and lines[j][0] in "-0123456789.":
            try:
                frames.append([float(v) for v in lines[j].split()])
            except ValueError:
                pass
        j += 1
    return joints, frame_time, np.array(frames)


def joint_index(joints, name):
    for idx, (n, _, _) in enumerate(joints):
        if n == name:
            return idx
    return None


def fk(joints, frame):
    """Forward kinematics: world position + parent-relative rotation per
    joint for one frame. Returns list of (position 3D, rotation 3x3)."""
    n = len(joints)
    pos = [np.zeros(3) for _ in range(n)]
    rot = [np.eye(3) for _ in range(n)]
    # channels are 3 rotations per joint (root adds 3 positions first)
    c = 0
    for i in range(n):
        name, offset, parent = joints[i]
        if parent < 0:  # root: position + rotation
            root_pos = frame[c:c + 3].astype(float)
            c += 3
        ang = np.radians(frame[c:c + 3].astype(float))
        c += 3
        rx = np.array([[1, 0, 0], [0, math.cos(ang[0]), -math.sin(ang[0])],
                       [0, math.sin(ang[0]), math.cos(ang[0])]])
        ry = np.array([[math.cos(ang[1]), 0, math.sin(ang[1])], [0, 1, 0],
                       [-math.sin(ang[1]), 0, math.cos(ang[1])]])
        rz = np.array([[math.cos(ang[2]), -math.sin(ang[2]), 0],
                       [math.sin(ang[2]), math.cos(ang[2]), 0], [0, 0, 1]])
        r_local = rz @ ry @ rx
        if parent < 0:
            rot[i] = r_local
            pos[i] = root_pos
        else:
            rot[i] = rot[parent] @ r_local
            pos[i] = pos[parent] + rot[parent] @ offset
    return pos


# ------------------------------------------------------------- retargeting
def project_2d(joints, frame, screen_w, screen_h, char_cx, char_cy, char_h):
    """FK one frame and map skeleton joints to 2D character space.
    The fair1 clips are captured facing the camera: BVH x = left-right,
    BVH y = up, BVH z = depth (toward camera). Project: screen_x = x,
    screen_y = -y (flip to image coords). Normalise to char_h and center
    on (char_cx, char_cy). Returns dict name -> (x, y) for key joints."""
    pos = fk(joints, frame)
    names = [j[0] for j in joints]
    pts = {n: p for n, p in zip(names, pos)}
    hip = pts.get("Hips", np.zeros(3))
    # gather all joint positions for scaling
    all_pos = np.array(pos)
    span_x = all_pos[:, 0].max() - all_pos[:, 0].min()
    span_y = all_pos[:, 1].max() - all_pos[:, 1].min()
    scale = char_h / max(1e-3, max(span_x, span_y, 1.0))

    def to_2d(p):
        x = (p[0] - hip[0]) * scale + char_cx
        y = char_cy - (p[1] - hip[1]) * scale
        return (float(x), float(y))

    return {n: to_2d(p) for n, p in pts.items()}


# -------------------------------------------------------- auto joint place
def auto_joints(alpha):
    """Estimate joint positions on the drawing from ink distribution.
    Returns dict name -> (x, y) in image pixels (fractions of bbox)."""
    ys, xs = np.where(alpha > 40)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    fx = lambda fx: x0 + fx * w
    fy = lambda fy: y0 + fy * h
    return {
        "Head": (fx(0.50), fy(0.10)),
        "Neck": (fx(0.50), fy(0.24)),
        "Spine3": (fx(0.50), fy(0.30)),
        "LeftShoulder": (fx(0.28), fy(0.32)),
        "RightShoulder": (fx(0.72), fy(0.32)),
        "LeftArm": (fx(0.18), fy(0.46)),
        "RightArm": (fx(0.82), fy(0.46)),
        "LeftHand": (fx(0.12), fy(0.60)),
        "RightHand": (fx(0.88), fy(0.60)),
        "Hips": (fx(0.50), fy(0.50)),
        "LeftLeg": (fx(0.38), fy(0.74)),
        "RightLeg": (fx(0.62), fy(0.74)),
        "LeftFoot": (fx(0.34), fy(0.96)),
        "RightFoot": (fx(0.66), fy(0.96)),
    }


BVH_TO_JOINT = {  # which BVH joints drive which drawing joints
    "Head": "Head", "Neck": "Neck", "Spine3": "Spine3",
    "LeftShoulder": "LeftShoulder", "RightShoulder": "RightShoulder",
    "LeftArm": "LeftArm", "RightArm": "RightArm",
    "LeftForeArm": "LeftHand", "RightForeArm": "RightHand",
    "LeftHand": "LeftHand", "RightHand": "RightHand",
    "Hips": "Hips", "LeftUpLeg": "LeftLeg", "RightUpLeg": "RightLeg",
    "LeftLeg": "LeftFoot", "RightLeg": "RightFoot",
    "LeftFoot": "LeftFoot", "RightFoot": "RightFoot",
}


# ----------------------------------------------------------------- render
def render(scene, out_path):
    W = scene.get("width", 1280)
    H = scene.get("height", 720)
    fps = scene.get("fps", 60)

    bg_src = scene.get("background")
    if bg_src:
        p = Path(bg_src)
        if not p.is_absolute():
            p = Path(out_path).parent / p
        bg = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (W, H), (250, 250, 245))

    char = scene["character"]
    img = Image.open(char["image"]).convert("RGBA")
    # magic-wand isolation: make near-white pixels transparent
    rgb = np.array(img)[:, :, :3]
    near_white = (rgb.min(axis=2) > 235)
    a = np.array(img)[:, :, 3]
    a[near_white] = 0
    img.putalpha(Image.fromarray(a))
    alpha = a
    # crop the character's ink bounding box (+ margin) so the mesh covers
    # only the character — fast ARAP, and the white box stays small
    ys, xs = np.where(alpha > 40)
    m = 14
    x0 = max(0, int(xs.min()) - m); x1 = min(img.width, int(xs.max()) + m)
    y0 = max(0, int(ys.min()) - m); y1 = min(img.height, int(ys.max()) + m)
    img_c = img.crop((x0, y0, x1, y1))
    # keep the mesh small and fast: cap the crop at 640 px on the long side
    max_dim = max(img_c.size)
    scale = 1.0
    if max_dim > 640:
        scale = 640.0 / max_dim
        img_c = img_c.resize((max(1, int(img_c.width * scale)),
                              max(1, int(img_c.height * scale))), Image.LANCZOS)
    arr = np.array(img_c)  # RGBA, warps with alpha
    char_w, char_h_crop = img_c.size

    joints = auto_joints(np.array(img_c)[:, :, 3])

    bvh_joints, frame_time, frames = parse_bvh(scene["motion"]["bvh"])
    start = scene["motion"].get("start", 0.0)
    duration = scene["motion"].get("duration", 3.0)
    start_frame = max(0, int(start / frame_time))
    n_frames = int(duration * fps)

    # joint pins are now in CROP coordinates; character stands centered at
    # char_cx / char_cy with height char_h scaled to the crop
    src_pins = {k: (int(v[0]), int(v[1])) for k, v in joints.items()}
    char_cx = char.get("x", W / 2)
    char_cy = char.get("y", H - 90)
    char_h = char.get("height", 560)

    # fixed anchors = bbox corners of the drawing (keep it planted)
    fixed = [(4, 4), (char_w - 4, 4), (4, char_h_crop - 4),
             (char_w - 4, char_h_crop - 4)]

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
        stdin=subprocess.PIPE)

    for i in range(n_frames):
        t = i / fps
        frame_idx = min(len(frames) - 1, start_frame + int(t / frame_time))
        posed = project_2d(bvh_joints, frames[frame_idx], W, H,
                           char_cx, char_cy, char_h)
        # map BVH joints onto the drawing's joint pins
        pins, targets = [], []
        for bvh_name, draw_name in BVH_TO_JOINT.items():
            if bvh_name in posed and draw_name in src_pins:
                pins.append(src_pins[draw_name])
                targets.append((posed[bvh_name][0] - char_cx + char_w / 2,
                                posed[bvh_name][1] - char_cy + char_h_crop / 2))
        for c in fixed:
            pins.append(c)
            targets.append(c)
        warped = deform_image(arr, pins, targets, delta=24, bg=(255, 255, 255, 0))
        warped_img = Image.fromarray(warped, "RGBA")
        if scale != 1.0:
            warped_img = warped_img.resize((int(warped_img.width / scale),
                                            int(warped_img.height / scale)),
                                           Image.LANCZOS)
        frame = bg.copy()
        frame.paste(warped_img,
                    (int(char_cx - warped_img.width / 2),
                     int(char_cy - warped_img.height / 2)),
                    warped_img)
        proc.stdin.write(np.array(frame).tobytes())
    proc.stdin.close()
    proc.wait()
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("-o", "--out", default="mocap.mp4")
    args = ap.parse_args()
    scene = json.loads(Path(args.scene).read_text())
    # resolve relative paths against the scene file
    base = Path(args.scene).resolve().parent
    if "background" in scene:
        scene["background"] = str(base / scene["background"])
    scene["character"]["image"] = str(base / scene["character"]["image"])
    if "bvh" in scene.get("motion", {}):
        scene["motion"]["bvh"] = str(base / scene["motion"]["bvh"])
    out = render(scene, args.out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
