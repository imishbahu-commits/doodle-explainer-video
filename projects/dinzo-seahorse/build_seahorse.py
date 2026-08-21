#!/usr/bin/env python3
"""Seahorse build — Paint Explainer 2026 spec engine.

Implements references/paint-explainer-style-spec-2026.md:
- 60 fps, NO motion blur (crisp stills)
- chapter title bar: white strip top 12% + ALL-CAPS rounded sans title
  (0.92->1.00 scale in 0.20 s at chapter start), world clipped below
- camera budget: ~50% locked+puppet, ~35% slow zoom (easeInOut,
  ~2.6 %/s, net 1.09x), ~12% punch-in (0.35-0.55 s, 1.12-1.22x,
  easeOutCubic), ~3% static
- puppets: sine-wave swim idle 0.6 Hz, amp 6-10% body height,
  travel 8-20 px/s; cut-on entrances; slide 0.40-0.55 s easeOutCubic;
  scale-pop easeOutBack 8-12% overshoot for props
- audio: narration loudnorm -16, ambient bed -19 dB, SFX (whoosh/pop/
  thud) -14 dB, whoosh same frame as punch key
- hard cuts, voice-synced clip lengths

Usage: .venv/bin/python build_seahorse.py <start> <end> [-o out.mp4]
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
AE = HERE.parent.parent / "skills" / "ae-motion" / "scripts" / "ae_motion.py"
PY = sys.executable
W, H, FPS = 1376, 768, 60
GAP = 0.25
CX, CY = W / 2, H / 2
BAR_H = int(H * 0.12)            # chapter title strip height (spec: top 10-12%)
SR = 44100

# ------------------------------------------------------------ keyframes
def kf(t, v, e="easeInOut"):
    return {"t": round(float(t), 4), "v": v, "e": e}


def hold(t, v):
    return kf(t, v, "hold")


def slow_zoom(dur, net=1.09, direction=1, t0=0.0):
    """Spec: ease-in-out, ~2.6 %/s, net 1.09x."""
    if direction > 0:
        return [kf(t0, 1.0), kf(t0 + dur, net, "easeInOut")]
    return [kf(t0, net), kf(t0 + dur, 1.0, "easeInOut")]


def punch(dur=0.45, to=1.18, t0=0.0):
    """Spec: punch-in 0.35-0.55 s, 1.00->1.12-1.22, ease-out, no overshoot."""
    return [kf(t0, 1.0), kf(t0 + dur, to, "easeOutCubic"), kf(t0 + dur + 0.4, max(to - 0.03, 1.0))]


def slide_in(dur, x0, x1, y, t0=0.0, e="easeOutCubic"):
    """Spec: slide 0.40-0.55 s ease-out-cubic."""
    return [kf(t0, [x0, y], e), kf(t0 + min(dur, 0.55), [x1, y])]


def pop(t0=0.0, dur=0.35, frm=0.6, to=1.08):
    """Spec: scale-pop 0.28-0.40 s ease-out-back, 8-12% overshoot."""
    return [kf(t0, frm, "easeOutBack"), kf(t0 + dur, to),
            kf(t0 + dur + 0.35, 1.0)]


def sine_wave(dur, amp, freq=0.6, t0=0.0, step=0.15):
    """Stepped sine (puppet pin drags) — swim idle. amp = px."""
    tr, t = [], t0
    while t <= dur + 1e-6:
        tr.append(hold(t, [0.0, round(amp * math.sin(2 * math.pi * freq * t), 2)]))
        t += step
    tr[-1] = hold(dur, [0.0, 0.0])
    return tr


def travel(dur, dx, t0=0.0):
    """Layer translates at constant px/s (spec: 8-20 px/s)."""
    return [kf(t0, [0, 0], "linear"), kf(t0 + dur, [dx, 0], "linear")]


def sine_rot(dur, amp_deg, freq=0.6, t0=0.0, step=0.15):
    """Scalar stepped sine for rotation (bob/sway). amp in degrees."""
    tr, t = [], t0
    while t <= dur + 1e-6:
        tr.append(hold(t, round(amp_deg * math.sin(2 * math.pi * freq * t), 2)))
        t += step
    tr[-1] = hold(dur, 0.0)
    return tr


def jolt(t0, amp=6.0, dur=0.5):
    """Anticipation + snap (spec D7 bite staging): -amp then +amp, settle."""
    return [hold(t0, 0.0), kf(t0 + 0.12, -amp, "easeInOut"),
            kf(t0 + 0.24, amp * 0.8, "easeOutCubic"),
            kf(t0 + 0.24 + 0.25, 0.0, "easeOutCubic")]


# ------------------------------------------------------------- assets
def key_character(src, out, pad=12):
    """White->transparent by distance-to-white + defringe (no halos)."""
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    dist = np.sqrt(((255.0 - a[:, :, :3]) ** 2).sum(axis=2)) / np.sqrt(3 * 255.0 ** 2)
    alpha = np.clip((dist - 0.05) / 0.10, 0.0, 1.0)
    im.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), "L"))
    im.putalpha(im.getchannel("A").filter(ImageFilter.MinFilter(3)))
    im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(0.8)))
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        raise SystemExit(f"nothing keyed: {src}")
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    im.crop((x0, y0, x1, y1)).save(out)
    return out


def bg_with_strip(src, out):
    """Spec B: white chapter strip on top 12%, world clipped below."""
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, BAR_H], fill=(255, 255, 255))
    d.rectangle([0, BAR_H - 3, W, BAR_H], fill=(0, 0, 0))
    im.save(out)
    return out


def prep_assets():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    cuts, bgs = {}, {}
    for src in sorted((HERE / "assets").glob("char_*.png")):
        out = work / (src.stem + "_cut.png")
        key_character(src, out)
        cuts[src.stem] = out
    for src in sorted((HERE / "assets").glob("bg_*.png")):
        out = work / (src.stem + "_bar.png")
        bg_with_strip(src, out)
        bgs[src.stem] = out
    return cuts, bgs


# ------------------------------------------------------------- scenes
# chapter structure (spec: title bar persists for the whole chapter)
CHAPTERS = {1: "THE POUCH", 6: "THE BIRTH"}

def chapter_for(i):
    c = "THE POUCH"
    for k in sorted(CHAPTERS):
        if i >= k:
            c = CHAPTERS[k]
    return c

# per-beat: bg, camera (lock|zoom-in|zoom-out|punch), chars [dict]
# camera budget: lock x5, zoom x3, punch x2  (50/30/20)
SCENES = {
    1: dict(bg="bg_seaweed", cam="zoom-in",
            chars=[dict(src="char_dad", max=760, pos=[hold(0, [CX, CY + 60])],
                        puppet="swim", bob=0.0)]),
    2: dict(bg="bg_reef", cam="lock",
            chars=[dict(src="char_dad", max=660, pos=[hold(0, [CX - 220, CY + 80])], puppet="swim"),
                   dict(src="char_mom", max=520, pos=[hold(0, [CX + 230, CY + 20])], puppet="swim")]),
    3: dict(bg="bg_reef", cam="zoom-in",
            chars=[dict(src="char_dad", max=660, pos=[hold(0, [CX - 160, CY + 70])], puppet="swim"),
                   dict(src="char_mom", max=520,
                        pos=[kf(0.0, [CX + 340, CY], "easeInOut"),
                             kf(0.55, [CX + 40, CY + 40], "easeOutCubic")], puppet="swim")]),
    4: dict(bg="bg_openwater", cam="lock",
            chars=[dict(src="char_dad", max=600, pos=[hold(0, [CX - 280, CY + 60])], puppet="swim"),
                   dict(src="char_mom", max=480,
                        pos=[kf(0.0, [CX + 180, CY - 20], "linear"),
                             kf(4.2, [CX + 900, CY - 40], "linear")], puppet="swim")]),
    5: dict(bg="bg_seaweed", cam="zoom-in",
            chars=[dict(src="char_dad", max=860, pos=[hold(0, [CX, CY + 70])], puppet="swim")]),
    6: dict(bg="bg_seaweed", cam="punch",
            chars=[dict(src="char_dad", max=880,
                        pos=[hold(0, [CX, CY + 60])],
                        rot=jolt(0.1, 5.0, 0.5), puppet="swim")]),
    7: dict(bg="bg_seaweed", cam="lock",
            chars=[dict(src="char_dad", max=700, pos=[hold(0, [CX - 240, CY + 60])],
                        rot=[hold(0, 0.0), kf(0.35, -4.0, "easeInOut"), kf(0.9, 3.5, "easeInOut"),
                             kf(1.5, -3.0, "easeInOut"), kf(2.1, 0.0, "easeInOut")], puppet="swim"),
                   dict(src="char_cloud", max=720,
                        pos=[kf(0.0, [CX + 60, CY + 10], "easeInOut"),
                             kf(0.75, [CX + 60, CY + 10], "easeOutBack")],
                        scale=pop(0.7, 0.35, 0.5, 1.08), puppet="swim")]),
    8: dict(bg="bg_openwater", cam="zoom-out",
            chars=[dict(src="char_cloud", max=940,
                        pos=[kf(0.0, [CX - 20, CY], "linear"),
                             kf(5.5, [CX - 120, CY + 10], "linear")], puppet="swim")]),
    9: dict(bg="bg_openwater", cam="punch",
            chars=[dict(src="char_baby", max=340,
                        pos=[hold(0, [CX, CY + 40])],
                        rot=sine_rot(5.0, 3.0, 0.35), puppet="swim")]),
    10: dict(bg="bg_openwater", cam="lock",
             chars=[dict(src="char_baby", max=330,
                         pos=[kf(0.0, [CX + 200, CY - 40], "linear"),
                              kf(4.8, [CX - 180, CY + 30], "linear")],
                         rot=sine_rot(4.8, 3.0, 0.35), puppet="swim")]),
}

CAM = {
    "lock": lambda d: {},
    "zoom-in": lambda d: {"scale": slow_zoom(d, 1.09, 1)},
    "zoom-out": lambda d: {"scale": slow_zoom(d, 1.09, -1)},
    "punch": lambda d: {"scale": punch(0.45, 1.18)},
}


def build_scene(idx, d, cuts, bgs):
    spec = SCENES[idx]
    chapter = chapter_for(idx)
    scene = {"width": W, "height": H, "fps": FPS, "duration": round(d, 4),
             "layers": []}
    # background with title strip (world clipped below bar)
    bg = {"type": "image", "src": f"../work/{bgs[spec['bg']].name}", "isolate": False,
          "tracks": {"pos": [hold(0, [CX, CY])], "rot": [hold(0, 0)],
                     "scale": [hold(0, 1.0)]}}
    bg["tracks"].update(CAM[spec["cam"]](d))
    scene["layers"].append(bg)
    # chapter title (sans, ALL CAPS, strip center; pop at chapter start)
    first = idx == min(i for i in SCENES if chapter_for(i) == chapter)
    title = {"type": "text", "text": chapter, "size": 54, "font": "sans",
             "fill": [0, 0, 0],
             "tracks": {"pos": [hold(0, [CX, BAR_H / 2])],
                        "scale": [kf(0.0, 0.92, "easeOutCubic"), kf(0.2, 1.0, "easeOutCubic")],
                        "opacity": [hold(0, 1.0)]}}
    scene["layers"].append(title)
    # characters
    for c in spec["chars"]:
        layer = {"type": "image", "src": f"../work/{cuts[c['src']].name}",
                 "isolate": False, "max_dim": c.get("max", 700),
                 "tracks": {"pos": [hold(0, [CX, CY])], "rot": [hold(0, 0)],
                            "scale": [hold(0, 1.0)], "opacity": [hold(0, 1.0)]}}
        for k in ("pos", "rot", "scale", "opacity"):
            if c.get(k):
                layer["tracks"][k] = c[k]
        if c.get("puppet") == "swim":
            hpx = 300 * (c.get("max", 700) / 700)   # ~body height proxy
            amp = hpx * 0.08                          # spec: 6-10% of body length
            layer["puppet"] = {"tracks": {
                "drag0": sine_wave(d, amp, 0.6),
                "drag1": sine_wave(d, amp * 0.6, 0.6, 0.075)}}
        scene["layers"].append(layer)
    return scene


# ------------------------------------------------------------ audio (SFX)
def whoosh(dur=0.25):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = np.random.randn(n)
    smooth = np.convolve(noise, np.ones(12) / 12, mode="same")
    bp = noise - smooth                      # crude bandpass
    env = np.exp(-t * 14) * np.minimum(t / 0.03, 1.0)
    sweep = np.sin(2 * np.pi * (250 * t + 450 * t * t / dur)) * 0.35
    x = (bp * 0.8 + sweep) * env
    return x / max(np.abs(x).max(), 1e-9) * 0.5


def pop_sfx(dur=0.08):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 750 * t) * np.exp(-t * 45)
    return x / max(np.abs(x).max(), 1e-9) * 0.5


def thud(dur=0.18):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 22)
    return x / max(np.abs(x).max(), 1e-9) * 0.55


# SFX timeline: beat -> [(t_abs, kind)]  (whoosh same frame as punch key)
SFX = {6: [(0.05, "whoosh"), (0.45, "thud")],
       7: [(0.72, "pop")],
       9: [(0.10, "whoosh")]}


def build_sfx(total):
    x = np.zeros(int(SR * (total + 0.5)))
    for beat, items in SFX.items():
        start = sum(dur(Path(AUDIO / f"beat{i:02d}.mp3")) + GAP
                    for i in range(1, beat))
        for t0, kind in items:
            fx = {"whoosh": whoosh, "pop": pop_sfx, "thud": thud}[kind]()
            i0 = int(SR * (start + t0))
            x[i0:i0 + len(fx)] += fx[:max(0, len(x) - i0)]
    return x / max(np.abs(x).max(), 1e-9) * 0.8


def build_bed(total):
    """Ambient pad: ~90-110 BPM feel, detuned sines + soft noise, flat LRA."""
    n = int(SR * total)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, f in enumerate([110.0, 164.81, 220.0, 277.18]):
        trem = 0.55 + 0.25 * np.sin(2 * np.pi * (0.10 + i * 0.013) * t + i)
        x += np.sin(2 * np.pi * f * t) * trem
    noise = np.cumsum(np.random.randn(n)) / np.sqrt(n) * 0.06
    k = np.ones(400) / 400
    noise = np.convolve(noise, k, mode="same")
    x += noise
    fade = np.ones(n)
    fi = int(SR * 1.5)
    fade[:fi] = np.linspace(0, 1, fi)
    fo = int(SR * 2.5)
    fade[-fo:] *= np.linspace(1, 0, fo)
    x *= fade
    return x / max(np.abs(x).max(), 1e-9) * 0.5


# ------------------------------------------------------------------- glue
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


def wav_from_np(x, path):
    x16 = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x16.tobytes())


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

    cuts, bgs = prep_assets()
    idxs = [i for i in sorted(SCENES) if args.start <= i <= (args.end or 999)]
    clips, padded, vdurs = [], [], []
    total_video = 0.0
    for i in idxs:
        aud = audio / f"beat{i:02d}.mp3"
        if not aud.exists():
            raise SystemExit(f"missing audio beat {i:02d}")
        pad = work / f"pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        scene = build_scene(i, d, cuts, bgs)
        (scenes / f"beat{i:02d}.json").write_text(json.dumps(scene, indent=1))
        clip = work / f"beat{i:02d}_anim.mp4"
        scene_file = scenes / f"beat{i:02d}.json"
        stale = (not verify_video(clip)
                 or clip.stat().st_mtime < aud.stat().st_mtime
                 or clip.stat().st_mtime < scene_file.stat().st_mtime)
        if stale:
            render_clip(scene_file, clip)
        clips.append(clip)
        padded.append(pad)
        vdurs.append(d)
        total_video += d
        print(f"beat {i:02d}: voice {dur(aud):5.2f}s +gap -> clip {d:5.2f}s", flush=True)

    # --- video concat (re-encode)
    vlist = work / "clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify_video(video, min_bytes=500_000):
        raise SystemExit("video concat failed verification")

    # --- narration (loudnorm -16), bed (-19 dB), sfx (-14 dB), mix
    alist = work / "audio.txt"
    alist.write_text("".join(f"file '{p.as_posix()}'\n" for p in padded))
    narr = work / "narration.m4a"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alist,
         "-c", "copy", narr])
    lev = work / "narration_norm.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", narr,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "160k",
         "-ar", "44100", lev])

    bed = build_bed(total_video + 0.3)
    sfx = build_sfx(total_video)
    wav_from_np(bed, work / "bed.wav")
    wav_from_np(sfx, work / "sfx.wav")
    mix = work / "mix.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", lev, "-i", work / "bed.wav",
         "-i", work / "sfx.wav", "-filter_complex",
         "[1:a]volume=0.11[bed];[2:a]volume=0.20[sfx];"
         "[0:a][bed][sfx]amix=inputs=3:duration=first:normalize=0,"
         "alimiter=limit=0.89[mix]",
         "-map", "[mix]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", mix])

    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", mix,
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(clips)} beats, "
          f"{dur(out):.0f}s)")


if __name__ == "__main__":
    main()
