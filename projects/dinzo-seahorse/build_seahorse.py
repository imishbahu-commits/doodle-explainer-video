#!/usr/bin/env python3
"""Seahorse build — Paint Explainer pro style.

- NO text/captions anywhere.
- Every beat: painted flat-colour background (full frame) + character
  layers cut from white PNGs with defringe (no white halos ever).
- Camera keyframes on EVERY beat (zoom-in/out, drift, punch, wobble) +
  character keyframes (slide-in easeOutExpo, pop easeOutBack, sway bob,
  puppet pin drags for tail/fin) — AE-grade easing, motion blur.
- Beat clip length == padded narration length (voice-synced, hard cuts).

Usage: .venv/bin/python build_seahorse.py <start> <end> [-o out.mp4]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
AE = HERE.parent.parent / "skills" / "ae-motion" / "scripts" / "ae_motion.py"
PY = sys.executable
W, H, FPS = 1376, 768, 30
GAP = 0.25
CX, CY = W / 2, H / 2

# ---------------------------------------------------------------- keyframes
def kf(t, v, e="easeInOut"):
    return {"t": round(float(t), 4), "v": v, "e": e}


def hold(t, v):
    return kf(t, v, "hold")


def slide(dur, x0, x1, y, t0=0.0, entry=0.5, e="easeOutExpo"):
    return [kf(t0, [x0, y], e), kf(t0 + entry, [x1, y])]


def bob(dur, amp=2.0, period=2.0, t0=0.0):
    tr, t, i = [], t0, 0
    while t <= dur + 1e-6:
        tr.append(kf(t, amp if i % 2 else -amp))
        t += period / 2
        i += 1
    tr[-1] = kf(dur, 0.0)
    return tr


def pop(t0, dur=0.45, frm=0.5, to=1.1):
    return [kf(t0, frm, "easeOutBack"), kf(t0 + dur, to),
            kf(max(t0 + dur + 0.6, 1.2), 1.0)]


def punch(t0, dur=0.6, frm=0.78, to=1.12):
    return [kf(t0, frm, "easeInCubic"), kf(t0 + dur, to, "easeOutExpo"),
            kf(t0 + dur + 0.5, max(to - 0.05, 1.0))]


def fade_out(t0, t1):
    return [hold(t0, 1.0), kf(t1, 0.0)]


def step_puppet(dur, amps, step=0.3):
    tr, t, i = [], 0.0, 0
    while t <= dur + 1e-6:
        tr.append(hold(t, list(amps[i % len(amps)])))
        t += step
        i += 1
    return tr


# ------------------------------------------------------------- asset cutting
def key_character(src, out, thr=40, erode=1, feather=0.8, pad=12):
    """White->transparent by distance-to-white + defringe (no white halos)."""
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    dist = np.sqrt(((255.0 - a[:, :, :3]) ** 2).sum(axis=2)) / np.sqrt(3 * 255.0 ** 2)
    # near-white (dist<5%) fully transparent; >15% fully opaque; ramp between
    alpha = np.clip((dist - 0.05) / 0.10, 0.0, 1.0)
    alpha = (alpha * 255).astype(np.uint8)
    im.putalpha(Image.fromarray(alpha, "L"))
    if erode:
        im.putalpha(im.getchannel("A").filter(ImageFilter.MinFilter(3)))
    if feather > 0:
        im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(feather)))
    # trim to content
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        raise SystemExit(f"nothing keyed: {src}")
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    im.crop((x0, y0, x1, y1)).save(out)
    return out


def trim_all():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    cuts = {}
    for src in sorted((HERE / "assets").glob("char_*.png")):
        out = work / (src.stem + "_cut.png")
        key_character(src, out)
        cuts[src.stem] = out
    return cuts


# --------------------------------------------------------------- beat scenes
# bg + cam + char layers. Every beat gets a camera move; chars get keyframes.
SCENES = {
    1: dict(bg="bg_seaweed", cam="zoom-out",
            chars=[dict(src="char_dad", max=780,
                        pos=slide(4.0, -560, CX, CY + 30, 0.0, 0.55),
                        rot=bob(4.0, 2.2, 2.2), puppet=True)]),
    2: dict(bg="bg_reef", cam="drift-l",
            chars=[dict(src="char_dad", max=700, pos=[hold(0, [CX - 190, CY + 60])],
                        rot=bob(4.5, 1.8), puppet=True),
                   dict(src="char_mom", max=560,
                        pos=slide(4.5, 760, CX + 230, CY + 10, 0.35, 0.55),
                        rot=bob(4.5, 2.0, 1.8), puppet=True)]),
    3: dict(bg="bg_reef", cam="zoom-in",
            chars=[dict(src="char_dad", max=760, pos=[hold(0, [CX - 120, CY + 40])],
                        rot=bob(4.5, 1.6), puppet=True),
                   dict(src="char_mom", max=560,
                        pos=[kf(0.0, [CX + 300, CY - 40], "easeInOut"),
                             kf(1.2, [CX + 130, CY + 20], "easeOutExpo")],
                        rot=bob(4.5, 2.0, 1.8), puppet=True)]),
    4: dict(bg="bg_openwater", cam="drift-r",
            chars=[dict(src="char_dad", max=640, pos=[hold(0, [CX - 260, CY + 40])],
                        rot=bob(3.5, 1.5), opacity=fade_out(2.4, 3.3)),
                   dict(src="char_mom", max=520,
                        pos=[kf(0.0, [CX + 200, CY - 10], "easeInOut"),
                             kf(1.4, [CX + 640, CY - 60], "easeInOut"),
                             kf(2.6, [CX + 1100, CY - 30], "linear")],
                        rot=bob(3.5, 2.0, 1.6))]),
    5: dict(bg="bg_seaweed", cam="zoom-in",
            chars=[dict(src="char_dad", max=800, pos=[hold(0, [CX, CY + 40])],
                        rot=bob(5.0, 2.4, 2.4), puppet=True)]),
    6: dict(bg="bg_seaweed", cam="punch",
            chars=[dict(src="char_dad", max=860,
                        pos=[kf(0.0, [CX, CY + 50], "easeInCubic"),
                             kf(0.5, [CX, CY + 20], "easeOutExpo")],
                        rot=[kf(0.0, 0, "hold"), kf(0.35, 3.0, "easeInOut"),
                             kf(0.7, -2.5, "easeInOut"), kf(1.1, 0, "easeInOut")],
                        puppet=True)]),
    7: dict(bg="bg_seaweed", cam="zoom-out",
            chars=[dict(src="char_dad", max=760, pos=[hold(0, [CX - 260, CY + 30])],
                        rot=bob(4.5, 2.0), puppet=True),
                   dict(src="char_cloud", max=640,
                        scale=pop(0.9, 0.5, 0.2, 1.0),
                        pos=[hold(0, [CX + 150, CY + 60])], rot=bob(4.5, 2.5, 1.6))]),
    8: dict(bg="bg_openwater", cam="drift-r",
            chars=[dict(src="char_cloud", max=980,
                        pos=[kf(0.0, [CX - 120, CY], "easeInOut"),
                             kf(1.0, [CX, CY], "easeOutExpo")],
                        scale=pop(0.25, 0.6, 0.5, 1.15), rot=bob(5.0, 2.0, 1.8))]),
    9: dict(bg="bg_openwater", cam="zoom-in",
            chars=[dict(src="char_baby", max=400,
                        scale=pop(0.4, 0.5, 0.3, 1.0),
                        pos=[kf(0.0, [CX, CY + 40], "easeInOut"),
                             kf(2.2, [CX - 40, CY + 10], "easeInOut"),
                             kf(4.0, [CX, CY + 30], "easeInOut")],
                        rot=bob(4.5, 6.0, 1.4))]),
    10: dict(bg="bg_openwater", cam="drift-l",
             chars=[dict(src="char_baby", max=360,
                         pos=[kf(0.0, [CX + 200, CY - 60], "linear"),
                              kf(4.5, [CX - 200, CY + 40], "linear")],
                         rot=bob(4.5, 7.0, 1.2))]),
}

CAM = {
    "zoom-in": lambda d: {"scale": [kf(0, 1.0), kf(d, 1.1)]},
    "zoom-out": lambda d: {"scale": [kf(0, 1.1), kf(d, 1.0)]},
    "drift-l": lambda d: {"pos": [kf(0, [CX + 220, CY], "linear"), kf(d, [CX - 220, CY], "linear")]},
    "drift-r": lambda d: {"pos": [kf(0, [CX - 220, CY], "linear"), kf(d, [CX + 220, CY], "linear")]},
    "punch": lambda d: {"scale": [kf(0, 1.0), kf(0.55, 1.14, "easeInCubic"), kf(1.1, 1.08)]},
    "wobble": lambda d: {"rot": [kf(0, 0, "hold"), kf(0.5, -1.6, "easeInOut"),
                                 kf(1.3, 1.6, "easeInOut"), kf(2.1, -1.2, "easeInOut"),
                                 kf(2.9, 1.2, "easeInOut"), kf(d, 0, "easeInOut")]},
}


def build_scene(idx, d, cuts):
    spec = SCENES[idx]
    scene = {"width": W, "height": H, "fps": FPS, "duration": round(d, 4),
             "motion_blur": 6 if any(c.get("puppet") for c in spec["chars"]) else 4,
             "layers": []}
    # background (full frame, camera keyframes)
    bg = {"type": "image", "src": f"../assets/{spec['bg']}.png", "isolate": False,
          "tracks": {"pos": [hold(0, [CX, CY])], "rot": [hold(0, 0)],
                     "scale": [hold(0, 1.0)]}}
    bg["tracks"].update(CAM[spec["cam"]](d))
    scene["layers"].append(bg)
    # character layers
    for c in spec["chars"]:
        layer = {"type": "image", "src": f"../work/{cuts[c['src']].name}",
                 "isolate": False, "max_dim": c.get("max", 700),
                 "tracks": {"pos": [hold(0, [CX, CY])], "rot": [hold(0, 0)],
                            "scale": [hold(0, 1.0)], "opacity": [hold(0, 1.0)]}}
        for k in ("pos", "rot", "scale", "opacity"):
            if c.get(k):
                layer["tracks"][k] = c[k]
        if c.get("puppet"):
            layer["puppet"] = {"tracks": {
                "drag0": step_puppet(d, [[0, 0], [0, 22], [0, -16], [0, 18], [0, 0]]),
                "drag1": step_puppet(d, [[0, 0], [0, -18], [0, 14], [0, -16], [0, 0]])}}
        scene["layers"].append(layer)
    return scene


# ------------------------------------------------------------------- helpers
def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{p.stderr[-2500:]}")
    return p.stdout


def dur(path):
    p = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise RuntimeError(f"no duration for {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def verify_video(path, min_bytes=50_000):
    if not path.exists() or path.stat().st_size < min_bytes:
        return False
    p = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    return p.returncode == 0 and len(p.stderr.strip()) == 0


def render_clip(scene, clip, attempts=3):
    for i in range(attempts):
        clip.unlink(missing_ok=True)
        run([PY, AE, str(scene), "-o", str(clip)])
        if verify_video(clip):
            return
    raise SystemExit(f"render failed {attempts}x: {clip.name}")


def pad_audio(src, out):
    run([FFMPEG, "-y", "-v", "error", "-i", src,
         "-af", f"apad=pad_dur={GAP},aresample=44100",
         "-ac", "2", "-c:a", "aac", "-b:a", "160k", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=int, nargs="?", default=1)
    ap.add_argument("end", type=int, nargs="?")
    ap.add_argument("-o", "--output", default="dinzo-seahorse-part1.mp4")
    args = ap.parse_args()

    audio = HERE / "audio"
    work, scenes = HERE / "work", HERE / "scenes"
    work.mkdir(exist_ok=True)
    scenes.mkdir(exist_ok=True)

    cuts = trim_all()
    idxs = [i for i in sorted(SCENES) if args.start <= i <= (args.end or 999)]
    clips, padded = [], []
    for i in idxs:
        aud = audio / f"beat{i:02d}.mp3"
        if not aud.exists():
            raise SystemExit(f"missing audio beat {i:02d}")
        pad = work / f"pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        scene = build_scene(i, d, cuts)
        (scenes / f"beat{i:02d}.json").write_text(json.dumps(scene, indent=1))
        clip = work / f"beat{i:02d}_anim.mp4"
        if not verify_video(clip) or clip.stat().st_mtime < aud.stat().st_mtime:
            render_clip(scenes / f"beat{i:02d}.json", clip)
        clips.append(clip)
        padded.append(pad)
        print(f"beat {i:02d}: voice {dur(aud):5.2f}s +gap -> clip {d:5.2f}s", flush=True)

    vlist = work / "clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify_video(video, min_bytes=500_000):
        raise SystemExit("video concat failed verification")

    alist = work / "audio.txt"
    alist.write_text("".join(f"file '{p.as_posix()}'\n" for p in padded))
    narr = work / "narration.m4a"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alist,
         "-c", "copy", narr])
    lev = work / "narration_norm.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", narr,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "160k",
         "-ar", "44100", lev])

    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", lev,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(clips)} beats, "
          f"{dur(out):.0f}s)")


if __name__ == "__main__":
    main()
