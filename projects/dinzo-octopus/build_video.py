#!/usr/bin/env python3
"""Dinzo octopus — keyframed animated build.

Each beat: image (or subject-over-flat-color) + hand-font label + the AE-style
keyframe choreography from skills/ae-motion (slide-in, punch-in, bob, wobble,
puppet pins, motion blur). Every beat clip is rendered to EXACTLY its padded
narration length, so voice and picture are frame-synced.

Resumable: existing clips in work/ are reused (skip re-render).

Usage: .venv/bin/python build_video.py [-o dinzo-octopus.mp4]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
AE = HERE.parent.parent / "skills" / "ae-motion" / "scripts" / "ae_motion.py"
PY = sys.executable
W, H, FPS = 1376, 768, 30
GAP = 0.35            # breath of silence appended after each beat
STEP = 0.18           # puppet hold-step (crude doodle keyframing)

# palette — Dinzo flat colors
CREAM = (255, 224, 172, 255)
SKY = (95, 188, 228, 255)
OCEAN = (63, 129, 178, 255)
WHITE = (255, 255, 255, 255)
DEEP = (36, 72, 110, 255)

# per-beat choreography: [move, bg color, subject-on-white?, label, label2]
BEATS = {
    1:  dict(move="slow-zoom-in",  bg=OCEAN, subject=False, label="100,000 EGGS",
             label2="WHY IT SUCKS TO BE BORN AS AN OCTOPUS"),
    2:  dict(move="slow-zoom-out", bg=OCEAN, subject=False, label="SHE NEVER EATS"),
    3:  dict(move="drift",         bg=SKY,   subject=False, label="DRIFTING LUNCH"),
    4:  dict(move="crawl",         bg=CREAM, subject=True,  label="3 HEARTS. 0 CARDIO."),
    5:  dict(move="punch-in",      bg=SKY,   subject=True,  label="9 BRAINS"),
    6:  dict(move="wobble",        bg=WHITE, subject=False, label="MOOD RING"),
    7:  dict(move="punch-in",      bg=DEEP,  subject=False, label="HIDE"),
    8:  dict(move="pop_boing",     bg=OCEAN, subject=True,  label="ESCAPE ARTIST"),
    9:  dict(move="ghost",         bg=DEEP,  subject=False, label="EXPIRATION DATE"),
    10: dict(move="ending",        bg=OCEAN, subject=False, label="1 IN 100,000"),
}

EASE = "easeInOut"
CX, CY = W / 2, H / 2


def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{p.stderr[-2500:]}")
    return p.stdout


def dur(path):
    """Duration via ffmpeg stderr (no ffprobe needed)."""
    p = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise RuntimeError(f"no duration for {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def pad_audio(src, out):
    run([FFMPEG, "-y", "-v", "error", "-i", src,
         "-af", f"apad=pad_dur={GAP},aresample=44100",
         "-ac", "2", "-c:a", "aac", "-b:a", "160k", out])


def verify_video(path, min_bytes=100_000):
    """Full decode check — catches corrupt-but-probable files."""
    if not path.exists() or path.stat().st_size < min_bytes:
        return False
    p = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    return p.returncode == 0 and len(p.stderr.strip()) == 0


def render_clip(scene, clip, attempts=3):
    """Render with verification + retry (ae_motion can write corrupt files silently)."""
    for i in range(attempts):
        clip.unlink(missing_ok=True)
        run([PY, AE, str(scene), "-o", str(clip)])
        if verify_video(clip):
            return
    raise SystemExit(f"render failed {attempts}x: {clip.name}")


def kf(t, v, e=EASE):
    return {"t": round(t, 4), "v": v, "e": e}


def step_track(dur, amps, step=STEP):
    """Hold-keyframed puppet drags: stepped crude-doodle motion (cheap, cache-friendly)."""
    tr, t, i = [], 0.0, 0
    while t <= dur + 1e-6:
        a = amps[i % len(amps)]
        tr.append(kf(t, list(a), "hold"))
        t += step
        i += 1
    return tr


def build_scene(idx, img, audio_dur):
    """Return scene.json for one beat — AE-grade keyframes per move."""
    spec = BEATS[idx]
    d = audio_dur
    scene = {"width": W, "height": H, "fps": FPS, "duration": round(d, 4),
             "motion_blur": 6 if spec["subject"] else 2,
             "bg_color": list(spec["bg"])}
    layers = []

    if spec["subject"]:
        # character PNG on white -> magic-wand cut, puppet-rigged, keyframed
        img_layer = {"type": "image", "src": f"../assets/{img.name}",
                     "isolate": True, "max_dim": 950, "puppet": {"tracks": {}}}
        tr = {"pos": [], "scale": [], "rot": []}
        m = spec["move"]
        if m == "crawl":
            tr["pos"] = [kf(0.0, [-420, CY + 140], "easeOutExpo"),
                         kf(0.55, [CX - 60, CY + 140]), kf(d, [CX + 320, CY + 140], "linear")]
            tr["scale"] = [kf(0.0, 0.9), kf(d, 1.0)]
            for i in range(2):  # tentacle wiggle, stepped
                img_layer["puppet"]["tracks"][f"drag{i}"] = step_track(
                    d, [[0, 0], [0, 26], [0, -18], [0, 20], [0, -14], [0, 0]])
        elif m == "punch-in":
            tr["pos"] = [kf(0.0, [CX, CY + 60], "easeInCubic"), kf(0.9, [CX, CY], "easeOutExpo")]
            tr["scale"] = [kf(0.0, 0.72, "easeInCubic"), kf(0.9, 1.12, "easeOutExpo"), kf(d, 1.06)]
            for i in range(2):
                img_layer["puppet"]["tracks"][f"drag{i}"] = step_track(
                    d, [[0, 0], [0, 22], [0, -16], [0, 18], [0, 0]])
        elif m == "pop_boing":
            tr["pos"] = [kf(0.0, [CX, CY], "hold")]
            tr["scale"] = [kf(0.0, 0.55, "easeOutBack"), kf(0.7, 1.1, "easeOutBack"),
                           kf(1.2, 0.97), kf(d, 1.0)]
            tr["rot"] = [kf(0.0, 0, "hold"), kf(0.5, -3, "easeInOut"), kf(1.0, 3, "easeInOut"),
                         kf(1.5, 0, "easeInOut")]
            for i in range(2):
                img_layer["puppet"]["tracks"][f"drag{i}"] = step_track(
                    d, [[0, 0], [0, 30], [0, -20], [0, 24], [0, 0]])
        if not tr["pos"]:
            tr["pos"] = [kf(0.0, [CX, CY], "hold")]
        if not tr["rot"]:
            tr["rot"] = [kf(0.0, 0, "hold")]
        if not tr["scale"]:
            tr["scale"] = [kf(0.0, 1.0, "hold")]
        img_layer["tracks"] = tr
        layers.append(img_layer)
    else:
        # full-frame scene — keyframed camera (pos/scale/rot)
        cam = {"type": "image", "src": f"../assets/{img.name}",
               "isolate": False, "tracks": {"pos": [], "scale": [], "rot": []}}
        m = spec["move"]
        if m == "slow-zoom-in":
            cam["tracks"]["scale"] = [kf(0.0, 1.0), kf(d, 1.13)]
        elif m == "slow-zoom-out":
            cam["tracks"]["scale"] = [kf(0.0, 1.14), kf(d, 1.0)]
        elif m == "drift":
            cam["tracks"]["pos"] = [kf(0.0, [CX + 260, CY], "linear"), kf(d, [CX - 260, CY], "linear")]
            cam["tracks"]["scale"] = [kf(0.0, 1.1), kf(d, 1.1)]
            cam["tracks"]["rot"] = [kf(0.0, 0, "hold"), kf(1.0, -1.2, "easeInOut"),
                                    kf(3.0, 1.2, "easeInOut"), kf(d, 0, "easeInOut")]
        elif m == "wobble":
            cam["tracks"]["rot"] = [kf(0.0, 0, "hold"), kf(0.5, -2.4, "easeInOut"),
                                    kf(1.2, 2.4, "easeInOut"), kf(1.9, -2.0, "easeInOut"),
                                    kf(2.6, 2.0, "easeInOut"), kf(d, 0, "easeInOut")]
            cam["tracks"]["scale"] = [kf(0.0, 1.0), kf(d, 1.07)]
        elif m == "punch-in":
            cam["tracks"]["scale"] = [kf(0.0, 1.0), kf(0.8, 1.22, "easeInCubic"), kf(1.4, 1.16)]
            cam["tracks"]["rot"] = [kf(0.0, 0, "hold"), kf(0.35, 1.1, "easeInOut"),
                                    kf(0.7, -1.1, "easeInOut"), kf(1.1, 0, "easeInOut")]
        elif m == "ghost":
            cam["tracks"]["scale"] = [kf(0.0, 1.1), kf(d, 1.0)]
            cam["tracks"]["opacity"] = [kf(0.0, 1.0), kf(d - 1.2, 1.0), kf(d, 0.62)]
        elif m == "ending":
            cam["tracks"]["scale"] = [kf(0.0, 1.0), kf(d, 1.08)]
            cam["tracks"]["opacity"] = [kf(0.0, 1.0), kf(d - 0.7, 1.0), kf(d, 0.0)]
        if not cam["tracks"]["pos"]:
            cam["tracks"]["pos"] = [kf(0.0, [CX, CY], "hold")]
        if not cam["tracks"]["rot"]:
            cam["tracks"]["rot"] = [kf(0.0, 0, "hold")]
        if not cam["tracks"]["scale"]:
            cam["tracks"]["scale"] = [kf(0.0, 1.0, "hold")]
        layers.append(cam)

    # hand-lettered label — pops in with easeOutBack (AE text layer)
    lsize = 58 if idx == 1 else 50
    label = {"type": "text", "text": spec["label"], "size": lsize, "font": "hand-bold",
             "tracks": {"pos": [kf(0.0, [CX, H - 92], "hold")],
                        "scale": [kf(0.55, 0.6, "hold"), kf(0.95, 1.0, "easeOutBack")],
                        "opacity": [kf(0.0, 0, "hold"), kf(0.55, 0, "hold"), kf(0.62, 1)]}}
    layers.append(label)

    if spec.get("label2"):
        title = {"type": "text", "text": spec["label2"], "size": 40, "font": "hand",
                 "tracks": {"pos": [kf(0.0, [CX, 96], "hold")],
                            "scale": [kf(0.9, 0.7, "hold"), kf(1.4, 1.0, "easeOutBack")],
                            "opacity": [kf(0.0, 0, "hold"), kf(0.9, 0, "hold"), kf(1.0, 1)]}}
        layers.append(title)

    scene["layers"] = layers
    return scene


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="dinzo-octopus.mp4")
    args = ap.parse_args()

    assets, audio = HERE / "assets", HERE / "audio"
    work, scenes = HERE / "work", HERE / "scenes"
    work.mkdir(exist_ok=True)
    scenes.mkdir(exist_ok=True)

    idxs = sorted(BEATS)
    # 1) pad audio + 2) render keyframed beat clips (resumable)
    clips, padded = [], []
    for i in idxs:
        img = assets / f"beat{i:02d}.png"
        aud = audio / f"beat{i:02d}.mp3"
        if not (img.exists() and aud.exists()):
            raise SystemExit(f"missing beat {i:02d} asset or audio")
        pad = work / f"pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        scene = build_scene(i, img, d)
        (scenes / f"beat{i:02d}.json").write_text(json.dumps(scene, indent=1))
        clip = work / f"beat{i:02d}_anim.mp4"
        if not verify_video(clip) or clip.stat().st_mtime < aud.stat().st_mtime:
            render_clip(scenes / f"beat{i:02d}.json", clip)
        clips.append(clip)
        padded.append(pad)
        print(f"beat {i:02d}: voice {dur(aud):5.2f}s +gap -> clip {d:5.2f}s", flush=True)

    # 3) concat animated clips (re-encode — robust; stream-copy concat is
    #    unreliable with these mp4 clips and TS remux segfaults this ffmpeg)
    vlist = work / "clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify_video(video, min_bytes=1_000_000):
        raise SystemExit("video concat failed verification")

    # 4) concat narration + loudness-normalise
    alist = work / "audio.txt"
    alist.write_text("".join(f"file '{p.as_posix()}'\n" for p in padded))
    narr = work / "narration.m4a"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alist,
         "-c", "copy", narr])
    lev = work / "narration_norm.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", narr,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "160k",
         "-ar", "44100", lev])

    # 5) mux
    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", lev,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, "
          f"{len(clips)} beats, {dur(out):.0f}s)")


if __name__ == "__main__":
    main()
