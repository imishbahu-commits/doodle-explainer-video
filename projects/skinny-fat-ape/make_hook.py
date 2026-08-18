#!/usr/bin/env python3
"""Build the Skinny Fat Ape hook with ae-motion + ffmpeg assembly.

Follows skills/ae-motion (keyframes, puppet pins, hand fonts) and
skills/Ultimate-Video-Editing-Skills (hard cuts, 30ms fades, loudnorm).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AE = ROOT / "skills" / "ae-motion" / "scripts" / "ae_motion.py"
ASSETS = HERE / "assets"
SCENES = HERE / "scenes"
BUILD = HERE / "build"
W, H, FPS = 1280, 720, 60
CX, CY = 640, 418  # dead-center x, slightly low y

sys.path.insert(0, str(AE.parent))
from ae_motion import render_scene  # noqa: E402


def make_x(path: Path) -> None:
    im = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # thick hand-ish red X
    for o in range(-18, 19, 2):
        d.line([(70 + o, 80), (450 + o, 440)], fill=(220, 28, 28, 255), width=22)
        d.line([(450 + o, 80), (70 + o, 440)], fill=(220, 28, 28, 255), width=22)
    # white outline via a second pass under? already thick enough
    im.save(path)


def kf(t, v, e="easeInOut"):
    return {"t": t, "v": v, "e": e}


def image_layer(src, tracks, max_dim=540, puppet=None, isolate=True):
    layer = {
        "type": "image",
        "src": src,
        "isolate": isolate,
        "max_dim": max_dim,
        "tracks": tracks,
    }
    if puppet:
        layer["puppet"] = puppet
    return layer


def text_layer(text, size, pos, appear, font="hand", color=None):
    tracks = {
        "pos": [kf(0, list(pos), "hold")],
        "scale": [kf(appear, 0.55, "hold"), kf(appear + 0.32, 1.0, "easeOutBack")],
        "opacity": [kf(0, 0.0, "hold"), kf(appear, 0.0, "hold"), kf(appear + 0.05, 1.0, "easeOut")],
    }
    spec = {"type": "text", "text": text, "size": size, "font": font, "tracks": tracks}
    return spec


def bob_pos(t0, t1, xy, amp=8, period=1.7):
    """Idle vertical bob as a few sine-ish keyframes."""
    x, y = xy
    keys = [kf(t0, [x, y], "easeInOut")]
    t = t0 + period / 2
    up = True
    while t < t1 - 0.05:
        keys.append(kf(t, [x, y - amp if up else y + amp], "easeInOut"))
        up = not up
        t += period / 2
    keys.append(kf(t1, [x, y], "easeInOut"))
    return keys


def write_scenes():
    SCENES.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    make_x(ASSETS / "x-stamp.png")
    rel = lambda p: str(Path("..") / "assets" / p)  # scenes/ -> assets/

    scenes = []

    # 1 skinny — question zoom-out, then NO + X
    d = 2.40
    scenes.append({
        "name": "01-thin",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-paper.png"),
        "motion_blur": 4,
        "layers": [
            image_layer(rel("01-skinny-ape.png"), {
                "pos": bob_pos(0.0, d, [CX, CY], 6),
                "scale": [kf(0, 1.10, "hold"), kf(d, 1.00, "easeInOut")],
            }, max_dim=500),
            text_layer("THIN?", 86, (CX, 88), 0.08, "hand-bold"),
            image_layer(rel("x-stamp.png"), {
                "pos": [kf(0, [CX, CY - 20], "hold")],
                "scale": [kf(1.15, 1.7, "hold"), kf(1.40, 1.0, "easeOutBack")],
                "opacity": [kf(0, 0, "hold"), kf(1.15, 0, "hold"), kf(1.18, 1, "easeOut")],
                "rot": [kf(1.15, -18, "hold"), kf(1.40, -8, "easeOutBack")],
            }, max_dim=380, isolate=False),
            text_layer("NO", 80, (1080, 120), 1.20, "hand-bold"),
        ],
    })

    # 2 fat — slide from right + X
    d = 2.40
    scenes.append({
        "name": "02-fat",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 5,
        "layers": [
            image_layer(rel("02-fat-ape.png"), {
                "pos": [kf(0, [1480, CY], "easeOutExpo"), kf(0.48, [CX, CY], "easeInOut")]
                       + bob_pos(0.48, d, [CX, CY], 5)[1:],
                "rot": [kf(0, 6, "hold"), kf(0.48, 0, "easeOutExpo")],
            }, max_dim=560),
            text_layer("FAT?", 86, (CX, 88), 0.20, "hand-bold"),
            image_layer(rel("x-stamp.png"), {
                "pos": [kf(0, [CX, CY - 10], "hold")],
                "scale": [kf(1.20, 1.7, "hold"), kf(1.44, 1.0, "easeOutBack")],
                "opacity": [kf(0, 0, "hold"), kf(1.20, 0, "hold"), kf(1.23, 1, "easeOut")],
            }, max_dim=380, isolate=False),
            text_layer("NO", 80, (1080, 120), 1.22, "hand-bold"),
        ],
    })

    # 3 box — slide-in + label
    d = 3.30
    scenes.append({
        "name": "03-box",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 5,
        "layers": [
            image_layer(rel("03-box-ape.png"), {
                "pos": [kf(0, [-360, CY], "easeOutExpo"), kf(0.55, [CX, CY], "easeInOut")]
                       + bob_pos(0.55, d, [CX, CY], 7)[1:],
                "rot": [kf(0, -5, "hold"), kf(0.55, 0, "easeOutExpo")],
            }, max_dim=560),
            text_layer("A BOX", 78, (CX, 84), 0.70, "hand-bold"),
            text_layer("NO SHAPE", 52, (1088, 130), 1.35, "hand"),
        ],
    })

    # 4 skinny-fat — punch-in
    d = 2.60
    scenes.append({
        "name": "04-skinny-fat",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-paper.png"),
        "motion_blur": 3,
        "layers": [
            image_layer(rel("04-skinny-fat-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY + 8], 5),
                "scale": [kf(0, 1.00, "hold"), kf(d, 1.16, "easeInCubic")],
            }, max_dim=540),
            text_layer("SKINNY FAT", 78, (CX, 90), 0.18, "hand-bold"),
        ],
    })

    # 5 hero ape slide
    d = 2.40
    scenes.append({
        "name": "05-hero",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 5,
        "layers": [
            image_layer(rel("00-style-lock-ape.png"), {
                "pos": [kf(0, [-340, CY], "easeOutExpo"), kf(0.50, [CX, CY], "easeInOut")]
                       + bob_pos(0.50, d, [CX, CY], 6)[1:],
            }, max_dim=540),
            text_layer("APE SHOWS YOU", 70, (CX, 88), 0.55, "hand-bold"),
        ],
    })

    # 6 banana — squash/stretch wobble (puppet-style body jiggle, no MLS)
    d = 3.30
    scenes.append({
        "name": "06-banana",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-paper.png"),
        "motion_blur": 3,
        "layers": [
            image_layer(rel("05-banana-body-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY + 6], 10, 1.2),
                "rot": [kf(0, -4, "easeInOut"), kf(0.8, 5, "easeInOut"),
                        kf(1.6, -4, "easeInOut"), kf(2.4, 4, "easeInOut"),
                        kf(d, -1, "easeInOut")],
                "scale": [kf(0, 1.0, "easeInOut"), kf(0.6, 1.08, "easeInOut"),
                          kf(1.2, 0.96, "easeInOut"), kf(1.8, 1.07, "easeInOut"),
                          kf(2.5, 0.98, "easeInOut"), kf(d, 1.02, "easeInOut")],
            }, max_dim=520),
            text_layer("OVERRIPE", 74, (CX, 84), 0.20, "hand-bold"),
        ],
    })

    # 7 jacked masterpiece — stamp + punch
    d = 2.50
    scenes.append({
        "name": "07-primal",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 4,
        "layers": [
            image_layer(rel("08-jacked-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY], 5),
                "scale": [kf(0, 1.55, "hold"), kf(0.38, 1.00, "easeOutBack"),
                          kf(d, 1.12, "easeInCubic")],
            }, max_dim=580),
            text_layer("PRIMAL", 88, (CX, 86), 0.40, "hand-bold"),
        ],
    })

    # 8 shredded + X
    d = 3.10
    scenes.append({
        "name": "08-shredded",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-paper.png"),
        "motion_blur": 3,
        "layers": [
            image_layer(rel("06-shredded-skinny-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY + 6], 5),
                "scale": [kf(0, 1.04, "hold"), kf(d, 0.98, "easeInOut")],
            }, max_dim=480),
            text_layer("ABS?", 80, (CX, 84), 0.10, "hand-bold"),
            image_layer(rel("x-stamp.png"), {
                "pos": [kf(0, [CX, CY - 20], "hold")],
                "scale": [kf(0.85, 1.7, "hold"), kf(1.10, 1.0, "easeOutBack")],
                "opacity": [kf(0, 0, "hold"), kf(0.85, 0, "hold"), kf(0.88, 1, "easeOut")],
            }, max_dim=360, isolate=False),
            text_layer("NO MORE", 58, (1080, 128), 1.05, "hand-bold"),
        ],
    })

    # 9 no waist + X
    d = 2.50
    scenes.append({
        "name": "09-nowaist",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 3,
        "layers": [
            image_layer(rel("07-no-waist-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY], 5),
            }, max_dim=560),
            text_layer("NO WAIST", 76, (CX, 90), 0.12, "hand-bold"),
            image_layer(rel("x-stamp.png"), {
                "pos": [kf(0, [CX, CY], "hold")],
                "scale": [kf(0.70, 1.7, "hold"), kf(0.95, 1.0, "easeOutBack")],
                "opacity": [kf(0, 0, "hold"), kf(0.70, 0, "hold"), kf(0.73, 1, "easeOut")],
            }, max_dim=400, isolate=False),
        ],
    })

    # 10 kicker — body recomp
    d = 2.31
    scenes.append({
        "name": "10-recomp",
        "width": W, "height": H, "fps": FPS, "duration": d,
        "background": rel("bg-cream.png"),
        "motion_blur": 4,
        "layers": [
            image_layer(rel("08-jacked-ape.png"), {
                "pos": bob_pos(0, d, [CX, CY + 12], 6, 1.3),
                "scale": [kf(0, 0.62, "hold"), kf(0.36, 1.04, "easeOutBack"),
                          kf(d, 1.10, "easeInOut")],
            }, max_dim=600),
            text_layer("BODY RECOMP", 80, (CX, 86), 0.28, "hand-bold"),
        ],
    })

    paths = []
    for sc in scenes:
        p = SCENES / f"{sc['name']}.json"
        p.write_text(json.dumps(sc, indent=2))
        paths.append(p)
        print(f"wrote {p.name}  {sc['duration']:.2f}s")
    return paths


def render_all(paths):
    BUILD.mkdir(exist_ok=True)
    clips = []
    for p in paths:
        out = BUILD / f"{p.stem}.mp4"
        force = True  # new metaphor art — rebuild every beat
        if out.exists() and out.stat().st_size > 1000 and not force:
            print(f"skip {out.name} (already rendered)")
        else:
            print(f"render {p.name} → {out.name}")
            scene = json.loads(p.read_text())
            render_scene(scene, out, base_dir=p.parent)
        clips.append(out)
    return clips


def assemble(clips):
    lst = BUILD / "concat.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    video = BUILD / "picture.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(video)],
        check=True,
    )
    audio = HERE / "audio" / "hook.mp3"
    final = HERE / "final.mp4"
    # Pad picture to VO length, 30ms fades, broadcast loudness
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-i", str(video), "-i", str(audio),
         "-filter_complex",
         "[0:v]tpad=stop_mode=clone:stop_duration=2[v];"
         "[1:a]afade=t=in:st=0:d=0.03,afade=t=out:st=26.78:d=0.03,"
         "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k",
         "-t", "26.81", "-movflags", "+faststart",
         str(final)],
        check=True,
    )
    print(f"wrote {final}")
    return final


def main():
    paths = write_scenes()
    clips = render_all(paths)
    assemble(clips)


if __name__ == "__main__":
    main()
