#!/usr/bin/env python3
"""Scene recreation build — 'The Stranger' (reference 15227 opening scene).

Style rules from MASTER_STYLE.md:
- backgrounds NEVER move (zero camera)
- ~70% frozen, ~30% in-place puppet motion only
- hard cuts, voice-synced shot lengths, median ~3s
- muted palette, title cards (black bg + white text)
- 60 fps, loudnorm -16, minimal/no SFX

Usage: .venv/bin/python build_scene.py [-o dinzo-scene.mp4]
"""
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
try:
    import imageio_ffmpeg
    FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
except Exception:
    FFMPEG = Path("ffmpeg")
W, H, FPS = 1376, 768, 60
GAP = 0.25
CX, CY = W / 2, H / 2
GROUND = 640


def font(size, bold=True):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def key_character(src, out, pad=10):
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    dist = np.sqrt(((255.0 - a[:, :, :3]) ** 2).sum(axis=2)) / np.sqrt(3 * 255.0 ** 2)
    alpha = np.clip((dist - 0.05) / 0.10, 0.0, 1.0)
    im.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), "L"))
    im.putalpha(im.getchannel("A").filter(ImageFilter.MinFilter(3)))
    im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(0.7)))
    bbox = im.getchannel("A").getbbox()
    x0, y0, x1, y1 = bbox
    im.crop((max(0, x0 - pad), max(0, y0 - pad),
             min(im.width, x1 + pad), min(im.height, y1 + pad))).save(out)
    return out


def rot(img, deg):
    return img.rotate(deg, resample=Image.BICUBIC, expand=True)


ASSETS = {}


def load():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    for n in ["char_stranger", "char_face", "char_face_shock", "char_elder",
              "char_stranger_walk", "prop_map", "prop_candle", "prop_door"]:
        out = work / f"{n}_cut.png"
        key_character(HERE / "assets" / f"{n}.png", out)
        ASSETS[n] = Image.open(out).convert("RGBA")
    for n in ["bg_dark", "bg_olive"]:
        ASSETS[n] = Image.open(HERE / "assets" / f"{n}.png").convert("RGB").resize((W, H), Image.LANCZOS)


def img(name, h):
    im = ASSETS[name]
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


# per-shot narration text (for title cards)
CARDS = {1: "THE STRANGER", 10: "THE VILLAGE NEVER SPOKE OF HIM AGAIN"}


def draw(beat, t, d):
    if beat in (3, 5, 6, 9):
        frame = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    else:
        bgname = "bg_dark" if beat in (1, 4, 8, 10) else "bg_olive"
        frame = ASSETS[bgname].copy().convert("RGBA")
    dr = ImageDraw.Draw(frame)

    # ---- shot content (in-place motion ONLY) ----
    if beat == 1:
        # black card + title pop
        k = min(1.0, t / 0.25)
        s = 0.92 + 0.08 * (1 - (1 - k) ** 3)
        f = font(int(110 * s))
        txt = "THE STRANGER"
        tw = dr.textlength(txt, font=f)
        dr.text(((W - tw) / 2, CY - 60), txt, font=f, fill=(245, 245, 240, 255))
        dr.text(((W - tw) / 2, CY - 58), txt, font=f, fill=(245, 245, 240, 255))
    elif beat == 2:
        # olive bg, hooded stranger, torch flame wiggle (rotate whole char)
        ch = img("char_stranger", 560)
        bob = math.sin(2 * math.pi * 0.5 * t) * 3
        sway = math.sin(2 * math.pi * 0.9 * t) * 1.4
        ch = rot(ch, sway)
        frame.alpha_composite(ch, (round(CX - ch.width / 2), round(GROUND - ch.height + 10 + bob)))
    elif beat == 3:
        # white bg, face close-up, subtle breathe
        ch = img("char_face", 620)
        pulse = 1.0 + 0.012 * math.sin(2 * math.pi * 0.6 * t)
        ch = ch.resize((round(ch.width * pulse), round(ch.height * pulse)), Image.LANCZOS)
        frame.alpha_composite(ch, (round(CX - ch.width / 2), round(CY + 40 - ch.height / 2)))
    elif beat == 4:
        # dark night, stranger walks SLOWLY (8-20 px/s), stars twinkle
        ch = img("char_stranger_walk", 420)
        k = min(1.0, t / d)
        x = 200 + (1140 - 200) * k
        frame.alpha_composite(ch, (round(x - ch.width / 2), GROUND - ch.height + 8))
        for i in range(5):
            sx = 120 + i * 250
            sy = 90 + (i % 3) * 55
            tw = (0.5 + 0.5 * math.sin(2 * math.pi * (0.7 + i * 0.13) * t))
            r = int(2 + 3 * tw)
            dr.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 230, int(180 + 75 * tw)))
    elif beat == 5:
        # white bg, map wobble
        m = img("prop_map", 420)
        m = rot(m, math.sin(2 * math.pi * 0.5 * t) * 3)
        frame.alpha_composite(m, (round(CX - m.width / 2), round(CY - m.height / 2 + 30)))
    elif beat == 6:
        # white bg, candle flame wiggle
        c = img("prop_candle", 430)
        c = rot(c, math.sin(2 * math.pi * 0.9 * t) * 2)
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * 1.3 * t)
        c = c.resize((round(c.width * pulse), round(c.height * pulse)), Image.LANCZOS)
        frame.alpha_composite(c, (round(CX - c.width / 2), round(GROUND - c.height + 10)))
    elif beat == 7:
        # olive bg, elder + stranger, elder arm raise = body tilt
        e = img("char_elder", 420)
        st = img("char_stranger", 480)
        e = rot(e, math.sin(2 * math.pi * 0.55 * t) * 2.5)
        frame.alpha_composite(e, (round(CX - 330 - e.width / 2), GROUND - e.height + 8))
        frame.alpha_composite(st, (round(CX + 210 - st.width / 2), GROUND - st.height + 8))
    elif beat == 8:
        # dark, door slides in (0.5s easeOutCubic), stranger silhouette steps
        door = img("prop_door", 560)
        k = min(1.0, t / 0.5)
        k = 1 - (1 - k) ** 3
        dx = int(200 + (CX + 260 - 200) * k)
        frame.alpha_composite(door, (round(dx - door.width / 2), GROUND - door.height + 12))
        if t > 0.7:
            ch = img("char_stranger_walk", 330)
            k2 = min(1.0, (t - 0.7) / (d - 0.7))
            x = dx - 80 + (dx + 120 - (dx - 80)) * k2
            frame.alpha_composite(ch, (round(x - ch.width / 2), GROUND - ch.height + 8))
    elif beat == 9:
        # white bg, shocked face with micro-shake then hold
        ch = img("char_face_shock", 660)
        sh = 0.0
        if t < 0.3:
            sh = math.sin(2 * math.pi * 24 * t) * 4 * (1 - t / 0.3)
        frame.alpha_composite(ch, (round(CX - ch.width / 2 + sh), round(CY + 30 - ch.height / 2)))
    elif beat == 10:
        # black sting card + end fade
        f = font(58)
        txt = "THE VILLAGE NEVER"
        tw = dr.textlength(txt, font=f)
        dr.text(((W - tw) / 2, CY - 90), txt, font=f, fill=(245, 245, 240, 255))
        f2 = font(58)
        txt2 = "SPOKE OF HIM AGAIN"
        tw2 = dr.textlength(txt2, font=f2)
        dr.text(((W - tw2) / 2, CY - 20), txt2, font=f2, fill=(245, 245, 240, 255))
        k = min(1.0, max(0.0, (t - (d - 1.0)) / 1.0))
        if k > 0:
            frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    return frame.convert("RGB")


# ------------------------------------------------------------------ video
def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{p.stderr[-2000:]}")
    return p.stdout


def dur(path):
    p = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def verify(path, min_b=50_000):
    if not path.exists() or path.stat().st_size < min_b:
        return False
    p = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    return p.returncode == 0 and len(p.stderr.strip()) == 0


def pad_audio(src, out):
    run([FFMPEG, "-y", "-v", "error", "-i", src,
         "-af", f"apad=pad_dur={GAP},aresample=44100",
         "-ac", "2", "-c:a", "aac", "-b:a", "160k", out])


def render(idx, d, out):
    n = max(1, round(d * FPS))
    proc = subprocess.Popen(
        [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(draw(idx, i / FPS, d).tobytes())
    proc.stdin.close()
    proc.wait()
    if not verify(out):
        raise SystemExit(f"render failed beat {idx:02d}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="dinzo-scene.mp4")
    args = ap.parse_args()
    audio = HERE / "audio"
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    load()
    idxs = list(range(1, 11))
    clips, padded = [], []
    for i in idxs:
        aud = audio / f"beat{i:02d}.mp3"
        if not aud.exists():
            raise SystemExit(f"missing audio beat {i:02d}")
        pad = work / f"pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        clip = work / f"beat{i:02d}_sc.mp4"
        if not verify(clip) or clip.stat().st_mtime < aud.stat().st_mtime:
            render(i, d, clip)
        clips.append(clip)
        padded.append(pad)
        print(f"beat {i:02d}: voice {dur(aud):5.2f}s -> clip {d:5.2f}s", flush=True)

    vlist = work / "clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify(video, 300_000):
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

    total = sum(dur(p) for p in padded)
    # soft door thud only (minimal SFX per reference mix)
    sr = 44100
    n = int(sr * 0.2)
    t = np.arange(n) / sr
    thud = np.sin(2 * np.pi * 80 * t) * np.exp(-t * 24) * 0.4
    starts, cum = {}, 0.0
    for i in idxs:
        starts[i] = cum
        cum += dur(work / f"pad{i:02d}.m4a")
    sfx = np.zeros(int(sr * (total + 0.5)))
    i0 = int(sr * (starts[8] + 0.45))
    sfx[i0:i0 + n] += thud[: max(0, len(sfx) - i0)]
    with wave.open(str(work / "sfx.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
    mix = work / "mix.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", lev, "-i", work / "sfx.wav",
         "-filter_complex",
         "[1:a]volume=0.16[sfx];[0:a][sfx]amix=inputs=2:duration=first:normalize=0,"
         "alimiter=limit=0.89[mix]",
         "-map", "[mix]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", mix])

    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", mix,
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(clips)} beats, {dur(out):.0f}s)")


if __name__ == "__main__":
    main()
