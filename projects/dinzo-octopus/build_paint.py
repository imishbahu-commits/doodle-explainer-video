#!/usr/bin/env python3
"""Paint Explainer build — separated subject PNGs + backgrounds, manual keyframes.

Workflow (per beat):
  subject PNG on pure white  -> trimmed to tight RGBA cut (white = transparent)
  background PNG (empty middle) -> full-frame layer
  ae-motion scene JSON: bg camera tracks + subject keyframes (pos/scale/rot/
  opacity) + optional puppet pin drags + hand-font labels, all hand-written
  keyframes per beat. Each beat clip is rendered to EXACTLY its padded
  narration length (voice-synced). Hard cuts between beats.

Resumable: verified clips in work/ are reused.

Usage: .venv/bin/python build_paint.py <start> <end> [-o out.mp4]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
AE = HERE.parent.parent / "skills" / "ae-motion" / "scripts" / "ae_motion.py"
PY = sys.executable
W, H, FPS = 1376, 768, 30
GAP = 0.25            # breath after each beat
CX, CY = W / 2, H / 2

LIGHT = (250, 250, 245)   # label fill on dark backgrounds (alpha appended by draw_text)
DARK = (28, 28, 34)       # label fill on light backgrounds

# ---------------------------------------------------------------- keyframes
def kf(t, v, e="easeInOut"):
    return {"t": round(float(t), 4), "v": v, "e": e}


def hold(t, v):
    return kf(t, v, "hold")


def zoom(dur, a, b, e="easeInOut", t0=0.0):
    return [kf(t0, a), kf(t0 + dur, b, e)]


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
    return [kf(t0, frm, "easeOutBack"), kf(t0 + dur, to), kf(max(t0 + dur + 0.6, 1.2), 1.0)]


def punch(t0, dur=0.6, frm=0.78, to=1.12):
    return [kf(t0, frm, "easeInCubic"), kf(t0 + dur, to, "easeOutExpo"),
            kf(t0 + dur + 0.5, max(to - 0.05, 1.0))]


def fade_out(t0, t1):
    return [hold(t0, 1.0), kf(t1, 0.0)]


def appear(t0):
    return [hold(t0, 0.0), kf(t0 + 0.07, 1.0)]


def step_puppet(dur, amps, step=0.3):
    """Hold-stepped pin drags — crude-doodle keyframing (fast + cache friendly)."""
    tr, t, i = [], 0.0, 0
    while t <= dur + 1e-6:
        tr.append(hold(t, list(amps[i % len(amps)])))
        t += step
        i += 1
    return tr


# ------------------------------------------------------------- layer helpers
def subject_cut(src, out, pad=14):
    """Trim white background -> tight RGBA cut (white pixels transparent)."""
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    alpha = 255 - np.clip(a[:, :, :3].max(axis=2) - 235, 0, 255).astype(np.uint8)
    if alpha.max() == 0:
        raise SystemExit(f"nothing to cut: {src}")
    ys, xs = np.where(alpha > 0)
    x0, x1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(im.height, ys.max() + pad + 1)
    im.putalpha(Image.fromarray(alpha, "L"))
    im.crop((x0, y0, x1, y1)).save(out)
    return out


def trim_all():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    cuts = {}
    for src in sorted((HERE / "assets").glob("sub_*.png")):
        out = work / (src.stem + "_cut.png")
        subject_cut(src, out)
        cuts[src.stem] = out
    return cuts


# --------------------------------------------------------------- beat scenes
# every beat: bg (background png), cam (camera move), subs (subject layers),
# labels (hand-font text pops). Keyframes are hand-written per beat.
SCENES = {
    1: dict(bg="bg_den.png", cam="zoom-in",
            subs=[dict(src="sub_eggs", max=720,
                       pos=slide(4.0, -520, CX, CY + 60, 0.0, 0.5),
                       rot=bob(4.0, 2.0))],
            labels=[("THE EGG", 0.95, 58, LIGHT), ("GRAIN OF RICE", 1.5, 42, LIGHT)]),
    2: dict(bg="bg_den.png", cam="hold",
            subs=[dict(src="sub_eggs", max=720,
                       scale=punch(0.25, 0.5, 0.72, 1.1))],
            labels=[("NOT A NEST", 0.5, 56, LIGHT), ("NOT A POUCH", 1.15, 56, LIGHT)]),
    3: dict(bg="bg_den.png", cam="zoom-out",
            subs=[dict(src="sub_eggs", max=720, pos=[hold(0, [CX, CY + 50])],
                       rot=bob(5.0, 1.6))],
            labels=[("TINY PEARL", 0.9, 56, LIGHT), ("DARK DEN", 1.5, 42, LIGHT)]),
    4: dict(bg="bg_den.png", cam="hold",
            subs=[dict(src="sub_eggs", max=680, pos=[hold(0, [CX, CY + 40])],
                       scale=pop(0.7, 0.5, 0.6, 1.0), rot=bob(4.0, 1.5)),
                  dict(src="sub_eggs", max=520, pos=slide(4.0, -700, CX - 420, CY + 130, 0.25, 0.5),
                       rot=bob(4.0, 2.0)),
                  dict(src="sub_eggs", max=520, pos=slide(4.0, 760, CX + 420, CY + 160, 0.5, 0.5),
                       rot=bob(4.0, 2.0))],
            labels=[("100,000", 1.1, 84, LIGHT), ("SIBLINGS", 1.65, 42, LIGHT)]),
    5: dict(bg="bg_den.png", cam="hold",
            subs=[dict(src="sub_mother", max=860,
                       pos=slide(5.0, -520, CX, CY + 40, 0.0, 0.55),
                       rot=bob(5.0, 1.5), puppet=True)],
            labels=[("MAMA", 1.3, 58, LIGHT)]),
    6: dict(bg="bg_den.png", cam="zoom-in",
            subs=[dict(src="sub_mother", max=860, pos=[hold(0, [CX, CY + 40])],
                       rot=bob(5.5, 1.2), puppet=True)],
            labels=[("NO FOOD", 1.0, 72, LIGHT)]),
    7: dict(bg="bg_den.png", cam="zoom-in",
            subs=[dict(src="sub_mother_weak", max=860,
                       pos=slide(5.0, 600, CX, CY + 50, 0.0, 0.6),
                       rot=bob(5.0, 1.0), puppet=True)],
            labels=[("WEAKER", 1.2, 60, LIGHT)]),
    8: dict(bg="bg_den.png", cam="hold",
            subs=[dict(src="sub_mother_weak", max=860, pos=[hold(0, [CX, CY + 50])],
                       opacity=fade_out(3.4, 5.2))],
            labels=[("SHE DIES", 0.9, 72, LIGHT), ("NEVER MEET HER", 2.6, 44, LIGHT)]),
    9: dict(bg="bg_den.png", cam="hold",
            subs=[dict(src="sub_baby", max=640,
                       scale=pop(0.45, 0.5, 0.4, 1.12),
                       rot=bob(3.5, 3.0))],
            labels=[("ORPHAN", 1.15, 60, LIGHT)]),
    10: dict(bg="bg_den.png", cam="zoom-out",
             subs=[dict(src="sub_baby", max=640,
                        pos=slide(4.5, CX, CX + 260, CY + 120, 0.0, 0.6),
                        scale=pop(0.2, 0.5, 0.3, 0.85), rot=bob(4.5, 2.5))],
             labels=[("TINY GHOST", 1.2, 56, LIGHT), ("HATCHING", 1.8, 40, LIGHT)]),
}

CAM_MOVES = {
    "hold": None,
    "zoom-in": lambda d: {"scale": zoom(d, 1.0, 1.09)},
    "zoom-out": lambda d: {"scale": zoom(d, 1.09, 1.0)},
}


def build_scene(idx, d, cuts):
    spec = SCENES[idx]
    scene = {"width": W, "height": H, "fps": FPS, "duration": round(d, 4),
             "motion_blur": 6 if any(s.get("puppet") for s in spec["subs"]) else 4,
             "layers": []}
    # background full-frame layer
    bg = {"type": "image", "src": f"../assets/{spec['bg']}", "isolate": False,
          "tracks": {"pos": [hold(0, [CX, CY])], "rot": [hold(0, 0)], "scale": [hold(0, 1)]}}
    cam = CAM_MOVES[spec["cam"]]
    if cam:
        bg["tracks"].update(cam(d))
    scene["layers"].append(bg)
    # subject layers (tight cuts, transparent)
    for s in spec["subs"]:
        layer = {"type": "image", "src": f"../work/{cuts[s['src']].name}",
                 "isolate": False, "max_dim": s.get("max", 800),
                 "tracks": {"pos": [hold(0, [CX, CY])],
                            "scale": [hold(0, 1.0)], "rot": [hold(0, 0)],
                            "opacity": [hold(0, 1.0)]}}
        for k in ("pos", "scale", "rot", "opacity"):
            if s.get(k):
                layer["tracks"][k] = s[k]
        if s.get("puppet"):
            layer["puppet"] = {"tracks": {
                "drag0": step_puppet(d, [[0, 0], [0, 24], [0, -18], [0, 20], [0, 0]]),
                "drag1": step_puppet(d, [[0, 0], [0, -20], [0, 16], [0, -18], [0, 0]])}}
        scene["layers"].append(layer)
    # hand-font labels (pop in, then sit)
    for text, t0, size, fill in spec["labels"]:
        scene["layers"].append({
            "type": "text", "text": text, "size": size, "font": "hand-bold",
            "fill": list(fill),
            "tracks": {"pos": [hold(0, [CX, H - 96])],
                       "scale": [hold(t0, 0.6), kf(t0 + 0.35, 1.0, "easeOutBack")],
                       "opacity": appear(t0)}})
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
    ap.add_argument("-o", "--output", default="dinzo-octopus-part1.mp4")
    args = ap.parse_args()

    assets, audio = HERE / "assets", HERE / "audio"
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

    # concat video (re-encode — stream-copy concat is unreliable here)
    vlist = work / "clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify_video(video, min_bytes=500_000):
        raise SystemExit("video concat failed verification")

    # concat narration + loudness-normalise
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
