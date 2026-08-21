#!/usr/bin/env python3
"""THE STRIKE — tiger-hunt scene recreation (ref 15227 style, enhanced keys).

Locked camera, frozen bg, in-place + short keyframe motion only.
NEW: gravity spear arc + rotation follows velocity, freeze-frame impact,
blood squash-stretch pop, mammoth rear-anticipation then rotate-fall with
ease-in, dust pop on landing, hunter 3-pose walk-up.

Usage: .venv/bin/python strike_scene.py [-o dinzo-strike.mp4]
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
HIT = (960, 470)          # spear hit point on mammoth
MAM_X = 1080              # mammoth feet-center x
MAM_W = 380               # small mammoth width

# narration for the 7 shots
VOICE = [
    "He pulls his arm back. The whole hunt comes down to this.",
    "He throws. The spear leaves his hand like a bird.",
    "It hits the mammoth's side.",
    "Blood blooms against the fur.",
    "The mammoth roars. It staggers. Then it tips.",
    "And crashes into the dust.",
    "The hunter walks closer. His dinner is huge.",
]


def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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
    im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
             min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))).save(out)
    return out


def rot(img, deg):
    return img.rotate(deg, resample=Image.BICUBIC, expand=True)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in(t):
    return t ** 2.2


ASSETS = {}


def load():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    for n in ["char_hunter_run1", "char_hunter_run2", "char_hunter_run3",
              "char_hunter_windup", "char_hunter_follow",
              "char_mammoth_s", "char_mammoth_hurt_s", "char_mammoth_fall_s",
              "char_mammoth_down_s", "fx_blood2", "fx_dust", "prop_spear"]:
        out = work / f"{n}_cut.png"
        key_character(HERE / "assets" / f"{n}.png", out)
        ASSETS[n] = Image.open(out).convert("RGBA")
    for n in ["bg_savanna", "bg_dusk"]:
        ASSETS[n] = Image.open(HERE / "assets" / f"{n}.png").convert("RGB").resize((W, H), Image.LANCZOS)


def hunter(name, h=130):
    im = ASSETS[name]
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def mammoth(name, w=MAM_W):
    im = ASSETS[name]
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def draw(beat, t, d):
    bg = "bg_dusk" if beat == 7 else "bg_savanna"
    frame = ASSETS[bg].copy().convert("RGBA")
    dr = ImageDraw.Draw(frame)

    if beat == 1:
        # wind-up: hunter at center, anticipation dip then hold
        im = hunter("char_hunter_windup", 150)
        dip = 1.0 - 0.06 * ease_out(min(1.0, t / 0.6))
        im = im.resize((round(im.width * dip), round(im.height * dip)), Image.LANCZOS)
        frame.alpha_composite(im, (round(680 - im.width / 2), round(GROUND - im.height + 8)))

    elif beat == 2:
        # throw: follow-through + spear gravity arc
        im = hunter("char_hunter_follow", 150)
        frame.alpha_composite(im, (round(680 - im.width / 2), GROUND - im.height + 8))
        ft = t - 0.25
        if ft >= 0:
            vx, vy, g = -540, -300, 1000
            px = 660 + vx * ft
            py = 520 + vy * ft + 0.5 * g * ft * ft
            ang = math.degrees(math.atan2(vy + g * ft, vx))
            sp = rot(ASSETS["prop_spear"], -ang + 180)
            frame.alpha_composite(sp, (round(px - sp.width / 2), round(py - sp.height / 2)))

    elif beat == 3:
        # freeze-frame impact: spear stuck, 0.15s hold, then blood starts
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
        m = mammoth("char_mammoth_hurt_s")
        frame.alpha_composite(m, (round(MAM_X - m.width / 2), GROUND - m.height + 8))
        bt = min(1.0, max(0.0, (t - 0.15) / 0.2))
        if bt > 0:
            bw = int(100 + 90 * ease_out(bt))
            b = ASSETS["fx_blood2"].resize((bw, round(ASSETS["fx_blood2"].height * bw / ASSETS["fx_blood2"].width)), Image.LANCZOS)
            frame.alpha_composite(b, (round(HIT[0] - b.width / 2 + 20), round(HIT[1] - b.height / 2 + 10)))

    elif beat == 4:
        # blood squash-stretch pop + mammoth hurt shake
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
        # shake: 6Hz damped
        sh = math.sin(2 * math.pi * 6 * t) * 5 * math.exp(-2 * t)
        m = mammoth("char_mammoth_hurt_s")
        frame.alpha_composite(m, (round(MAM_X - m.width / 2 + sh), GROUND - m.height + 8))
        # blood pop with overshoot: scale 0.6 -> 1.25 -> 1.0
        bt = min(1.0, max(0.0, (t - 0.1) / 0.35))
        s = 0.6 + 0.65 * ease_out(bt) if bt < 0.8 else 1.25 - 0.25 * ease_out((bt - 0.8) / 0.2)
        bw = int(220 * s)
        b = ASSETS["fx_blood2"].resize((bw, round(ASSETS["fx_blood2"].height * bw / ASSETS["fx_blood2"].width)), Image.LANCZOS)
        frame.alpha_composite(b, (round(HIT[0] - b.width / 2 + 20), round(HIT[1] - b.height / 2 + 10)))

    elif beat == 5:
        # rear anticipation then rotate-fall
        k = min(1.0, max(0.0, (t - 0.6) / 1.1))
        if k < 0.05:
            m = mammoth("char_mammoth_s")
            rear = 6 * min(1.0, t / 0.5)
            m = rot(m, -rear)
            frame.alpha_composite(m, (round(MAM_X - m.width / 2), GROUND - m.height + 8))
        else:
            k2 = ease_in(k)
            base = mammoth("char_mammoth_fall_s" if k2 < 0.8 else "char_mammoth_down_s")
            if k2 >= 1.0:
                frame.alpha_composite(base, (round(MAM_X - base.width / 2), round(GROUND - base.height + 22)))
            else:
                r = rot(base, -80 * k2)
                frame.alpha_composite(r, (round(MAM_X - r.width / 2 + 40 * k2), round(GROUND - r.height + 10)))

    elif beat == 6:
        # landed: down pose + dust pop + tiny shake
        m = mammoth("char_mammoth_down_s")
        frame.alpha_composite(m, (round(MAM_X - m.width / 2), round(GROUND - m.height + 22)))
        dt = min(1.0, max(0.0, (t - 0.2) / 0.5))
        if dt > 0:
            dw = int(220 * (0.4 + 0.8 * ease_out(dt)))
            dimg = ASSETS["fx_dust"].resize((dw, round(ASSETS["fx_dust"].height * dw / ASSETS["fx_dust"].width)), Image.LANCZOS)
            dimg.putalpha(dimg.getchannel("A").point(lambda p: int(p * (1 - 0.5 * dt))))
            frame.alpha_composite(dimg, (round(MAM_X - dimg.width / 2), round(GROUND - 30)))
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))

    elif beat == 7:
        # hunter 3-pose walk-up + mammoth down + dusk fade
        m = mammoth("char_mammoth_down_s")
        frame.alpha_composite(m, (round(MAM_X - m.width / 2), round(GROUND - m.height + 22)))
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
        k = min(1.0, t / d)
        x = 780 + (640 - 780) * ease_out(k)
        im = hunter(["char_hunter_run1", "char_hunter_run2", "char_hunter_run3"][int(t * 5) % 3], 140)
        frame.alpha_composite(im, (round(x - im.width / 2), GROUND - im.height + 8))
        kf = min(1.0, max(0.0, (t - (d - 1.0)) / 1.0))
        if kf > 0:
            frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * kf))), (0, 0))

    # title bar (fixed, top 12%)
    dr.rectangle([0, 0, W, int(H * 0.12)], fill=(255, 255, 255, 255))
    dr.rectangle([0, int(H * 0.12) - 3, W, int(H * 0.12)], fill=(0, 0, 0, 255))
    f = font(50)
    txt = "THE STRIKE"
    tw = dr.textlength(txt, font=f)
    dr.text(((W - tw) / 2, int(H * 0.12) / 2 - 28), txt, font=f, fill=(0, 0, 0, 255))
    return frame.convert("RGB")


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
    ap.add_argument("-o", "--output", default="dinzo-strike.mp4")
    args = ap.parse_args()
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    load()

    # generate 7 voice clips from VOICE (TTS via saved clips pattern not used here —
    # we reuse beat04-10 audio from the mammoth kit where possible, else skip)
    clips, padded = [], []
    for i in range(1, 8):
        # map strike shots to existing mammoth audio (beats 4..10)
        src_idx = 3 + i
        aud = HERE / "audio" / f"beat{src_idx:02d}.mp3"
        if not aud.exists():
            raise SystemExit(f"missing audio beat{src_idx:02d}")
        pad = work / f"strike_pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        clip = work / f"strike_{i:02d}.mp4"
        if not verify(clip) or clip.stat().st_mtime < aud.stat().st_mtime:
            render(i, d, clip)
        clips.append(clip)
        padded.append(pad)
        print(f"strike {i:02d}: {d:5.2f}s", flush=True)

    vlist = work / "strike_clips.txt"
    vlist.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    video = work / "strike_video.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist,
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-movflags", "+faststart", video])
    if not verify(video, 300_000):
        raise SystemExit("video concat failed verification")

    alist = work / "strike_audio.txt"
    alist.write_text("".join(f"file '{p.as_posix()}'\n" for p in padded))
    narr = work / "strike_narration.m4a"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alist,
         "-c", "copy", narr])
    lev = work / "strike_norm.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", narr,
         "-af", "loudnorm=I=-16:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "160k",
         "-ar", "44100", lev])

    total = sum(dur(p) for p in padded)
    sr = 44100
    starts, cum = {}, 0.0
    for i in range(1, 8):
        starts[i] = cum
        cum += dur(work / f"strike_pad{i:02d}.m4a")

    def whoosh(dr=0.25):
        n = int(sr * dr); t = np.arange(n) / sr
        noise = np.random.randn(n)
        smooth = np.convolve(noise, np.ones(12) / 12, mode="same")
        env = np.exp(-t * 14) * np.minimum(t / 0.03, 1.0)
        return (noise - smooth) * env / 2

    def thud(dr=0.2, amp=0.6):
        n = int(sr * dr); t = np.arange(n) / sr
        return np.sin(2 * np.pi * 80 * t) * np.exp(-t * 22) * amp

    sfx = np.zeros(int(sr * (total + 0.5)))
    plan = {2: [(0.3, whoosh, 1.0)], 3: [(0.2, thud, 0.5)],
            5: [(1.8, thud, 0.4)], 6: [(0.3, thud, 0.8)]}
    for b, items in plan.items():
        for t0, fn, amp in items:
            x = fn() * amp
            i0 = int(sr * (starts[b] + t0))
            sfx[i0:i0 + len(x)] += x[:max(0, len(sfx) - i0)]
    with wave.open(str(work / "strike_sfx.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
    mix = work / "strike_mix.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", lev, "-i", work / "strike_sfx.wav",
         "-filter_complex",
         "[1:a]volume=0.18[sfx];[0:a][sfx]amix=inputs=2:duration=first:normalize=0,"
         "alimiter=limit=0.89[mix]",
         "-map", "[mix]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", mix])

    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", mix,
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(clips)} beats, {dur(out):.0f}s)")


if __name__ == "__main__":
    main()
