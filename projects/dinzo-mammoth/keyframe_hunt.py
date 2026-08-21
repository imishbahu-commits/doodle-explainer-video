#!/usr/bin/env python3
"""Mammoth Hunt — keyframe build (Paint Explainer style, small mammoth).

PNG assets + keyframe motion (like the reference sheet): hunter = 5 pose
PNGs swapped on keyframes (run cycle ~8 swaps/s while sliding, wind-up,
follow-through), spear = projectile with gravity (rotation follows
velocity), blood = scale-pop, mammoth = SMALL (fits the wide shot),
swap hurt -> shake -> rotate-to-ground fall -> down. Static bg + title bar.

Usage: .venv/bin/python keyframe_hunt.py [start] [end] [-o out.mp4]
"""
import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
try:
    FFMPEG = Path(sys.prefix) / "bin" / "ffmpeg"
    if not FFMPEG.exists():
        import imageio_ffmpeg
        FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
except Exception:
    import imageio_ffmpeg
    FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
W, H, FPS = 1376, 768, 60
GAP = 0.25
CX, CY = W / 2, H / 2
GROUND = 640
BAR_H = int(H * 0.12)
CH = {1: "THE HUNT", 4: "THE THROW", 8: "THE FALL"}


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
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    im.crop((x0, y0, x1, y1)).save(out)
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
    for n in ["char_mammoth_s", "char_mammoth_hurt_s", "char_mammoth_fall_s",
              "char_mammoth_down_s", "char_hunter_run1", "char_hunter_run2",
              "char_hunter_run3", "char_hunter_windup", "char_hunter_follow",
              "fx_blood2", "fx_dust", "prop_rock", "prop_spear"]:
        out = work / f"{n}_cut.png"
        key_character(HERE / "assets" / f"{n}.png", out)
        ASSETS[n] = Image.open(out).convert("RGBA")
    for n in ["bg_savanna", "bg_dusk"]:
        ASSETS[n] = Image.open(HERE / "assets" / f"{n}.png").convert("RGB").resize((W, H), Image.LANCZOS)


# scene geometry ---------------------------------------------------------
MAM_X = 1040          # mammoth feet-center x
MAM_W = 430           # mammoth display width (SMALL — ~31% of frame)
HIT = (880, 400)      # spear hit point on mammoth side


def mammoth_img(name, w=MAM_W):
    im = ASSETS[name]
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def hunter_img(name, h=120):
    im = ASSETS[name]
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def draw(beat, t, d):
    frame = ASSETS["bg_savanna" if beat < 10 else "bg_dusk"].copy().convert("RGBA")
    dr = ImageDraw.Draw(frame)

    # rock (left)
    rw = 220
    rock = ASSETS["prop_rock"].resize((rw, round(ASSETS["prop_rock"].height * rw / ASSETS["prop_rock"].width)), Image.LANCZOS)
    rock_x, rock_top = 120, GROUND - rock.height + 20

    # ---- mammoth (small) ----
    if beat == 1:
        im = mammoth_img("char_mammoth_s")
        bob = math.sin(2 * math.pi * 0.5 * t) * 3
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 8 + bob)))
    elif beat == 2:
        im = mammoth_img("char_mammoth_s")
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), GROUND - im.height + 8))
    elif beat in (3, 4):
        im = mammoth_img("char_mammoth_s")
        bob = math.sin(2 * math.pi * 0.5 * t) * 2
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 8 + bob)))
    elif beat == 5:
        im = mammoth_img("char_mammoth_s")
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), GROUND - im.height + 8))
    elif beat == 6:
        im = mammoth_img("char_mammoth_hurt_s")
        sh = math.sin(2 * math.pi * 8 * t) * 4 * math.exp(-2.5 * t)
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 8 + sh)))
    elif beat == 7:
        im = mammoth_img("char_mammoth_hurt_s")
        sh = math.sin(2 * math.pi * 6 * t) * 3
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 8 + sh)))
    elif beat == 8:
        k = min(1.0, max(0.0, (t - 0.5) / 1.1))
        k = ease_in(k)
        if k >= 1.0:
            im = mammoth_img("char_mammoth_down_s")
            frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 22)))
        else:
            base = mammoth_img("char_mammoth_hurt_s" if k < 0.75 else "char_mammoth_fall_s")
            r = rot(base, -80 * k)
            # pivot near feet; place so feet stay ~ground
            frame.alpha_composite(r, (round(MAM_X - r.width / 2 + 40 * k), round(GROUND - r.height + 10)))
        if t > 1.6:
            dt = min(1.0, (t - 1.6) / 0.5)
            dw = int(260 * (0.4 + 0.8 * dt))
            dimg = ASSETS["fx_dust"].resize((dw, round(ASSETS["fx_dust"].height * dw / ASSETS["fx_dust"].width)), Image.LANCZOS)
            dimg.putalpha(dimg.getchannel("A").point(lambda p: int(p * (1 - 0.4 * dt))))
            frame.alpha_composite(dimg, (round(MAM_X - dimg.width / 2), round(GROUND - 30)))
    else:  # 9, 10
        im = mammoth_img("char_mammoth_down_s")
        frame.alpha_composite(im, (round(MAM_X - im.width / 2), round(GROUND - im.height + 22)))
        if beat in (9, 10):
            sp = rot(ASSETS["prop_spear"], -115)
            frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
            if beat == 10:
                b = ASSETS["fx_blood2"].resize((150, round(ASSETS["fx_blood2"].height * 150 / ASSETS["fx_blood2"].width)), Image.LANCZOS)
                frame.alpha_composite(b, (round(HIT[0] - 60), round(HIT[1] - 40)))

    # ---- hunter ----
    if beat == 2:
        # peek from behind left rock: paste hunter, then rock over it
        im = hunter_img("char_hunter_windup")
        frame.alpha_composite(im, (250, GROUND - im.height + 10))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 3:
        # run across with 3-pose swap (keyframed cycle)
        k = min(1.0, t / d)
        x = 300 + (760 - 300) * ease_out(k)
        poses = ["char_hunter_run1", "char_hunter_run2", "char_hunter_run3"]
        im = hunter_img(poses[int(t * 8) % 3])
        bob = abs(math.sin(2 * math.pi * 4 * t)) * 6
        frame.alpha_composite(im, (round(x - im.width / 2), round(GROUND - im.height + 6 - bob)))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 4:
        im = hunter_img("char_hunter_windup")
        dip = 1 - 0.05 * min(1.0, t / d)          # anticipation scale-down
        w2 = round(im.width * dip)
        im = im.resize((w2, round(im.height * dip)), Image.LANCZOS)
        frame.alpha_composite(im, (round(700 - im.width / 2), round(GROUND - im.height + 8)))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 5:
        rel = min(1.0, t / 0.4)
        if rel < 1:
            im = hunter_img("char_hunter_windup")
            frame.alpha_composite(im, (round(700 - im.width / 2), GROUND - im.height + 8))
        else:
            im = hunter_img("char_hunter_follow")
            frame.alpha_composite(im, (round(700 - im.width / 2), GROUND - im.height + 8))
            # spear projectile with gravity
            ft = t - 0.4
            vx, vy, g = -540, -300, 1000
            px = 680 + vx * ft
            py = 500 + vy * ft + 0.5 * g * ft * ft
            ang = math.degrees(math.atan2(vy + g * ft, vx))
            sp = rot(ASSETS["prop_spear"], -ang + 180)
            frame.alpha_composite(sp, (round(px - sp.width / 2), round(py - sp.height / 2)))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 6:
        im = hunter_img("char_hunter_follow")
        frame.alpha_composite(im, (round(700 - im.width / 2), GROUND - im.height + 8))
        # stuck spear + blood pop
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
        bt = min(1.0, max(0.0, (t - 0.15) / 0.25))
        bw = int(120 + 110 * ease_out(bt))
        b = ASSETS["fx_blood2"].resize((bw, round(ASSETS["fx_blood2"].height * bw / ASSETS["fx_blood2"].width)), Image.LANCZOS)
        frame.alpha_composite(b, (round(HIT[0] - b.width / 2 + 30), round(HIT[1] - b.height / 2 + 20)))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 7:
        im = hunter_img("char_hunter_follow")
        frame.alpha_composite(im, (round(700 - im.width / 2), GROUND - im.height + 8))
        sp = rot(ASSETS["prop_spear"], -115)
        frame.alpha_composite(sp, (round(HIT[0] - sp.width / 2), round(HIT[1] - sp.height / 2)))
        b = ASSETS["fx_blood2"].resize((160, round(ASSETS["fx_blood2"].height * 160 / ASSETS["fx_blood2"].width)), Image.LANCZOS)
        frame.alpha_composite(b, (round(HIT[0] - 40), round(HIT[1] - 20)))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 8:
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 9:
        k = min(1.0, t / d)
        x = 700 + (560 - 700) * ease_out(k)
        im = hunter_img(["char_hunter_run1", "char_hunter_run2", "char_hunter_run3"][int(t * 4) % 3])
        frame.alpha_composite(im, (round(x - im.width / 2), GROUND - im.height + 8))
        frame.alpha_composite(rock, (rock_x, rock_top))
    elif beat == 10:
        im = hunter_img("char_hunter_follow")
        frame.alpha_composite(im, (round(620 - im.width / 2), GROUND - im.height + 8))
        frame.alpha_composite(rock, (rock_x, rock_top))

    # title bar
    dr.rectangle([0, 0, W, BAR_H], fill=(255, 255, 255, 255))
    dr.rectangle([0, BAR_H - 3, W, BAR_H], fill=(0, 0, 0, 255))
    title = CH.get(beat, "THE HUNT")
    f = font(52)
    tw = dr.textlength(title, font=f)
    dr.text(((W - tw) / 2, BAR_H / 2 - 30), title, font=f, fill=(0, 0, 0, 255))

    if beat == 10:
        k = min(1.0, max(0.0, (t - (d - 1.2)) / 1.2))
        if k > 0:
            frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * k))), (0, 0))
    return frame.convert("RGB")


# ---------------------------------------------------------------- video
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
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=int, nargs="?", default=1)
    ap.add_argument("end", type=int, nargs="?")
    ap.add_argument("-o", "--output", default="dinzo-mammoth-part2.mp4")
    args = ap.parse_args()
    audio = HERE / "audio"
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    load()
    idxs = list(range(args.start, (args.end or 10) + 1))
    clips, padded = [], []
    for i in idxs:
        aud = audio / f"beat{i:02d}.mp3"
        if not aud.exists():
            raise SystemExit(f"missing audio beat {i:02d}")
        pad = work / f"pad{i:02d}.m4a"
        if not pad.exists() or pad.stat().st_mtime < aud.stat().st_mtime:
            pad_audio(aud, pad)
        d = dur(pad)
        clip = work / f"beat{i:02d}_kf.mp4"
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
    if not verify(video, 500_000):
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
    import wave
    sr = 44100

    def whoosh(dr=0.25):
        n = int(sr * dr); t = np.arange(n) / sr
        noise = np.random.randn(n)
        smooth = np.convolve(noise, np.ones(12) / 12, mode="same")
        env = np.exp(-t * 14) * np.minimum(t / 0.03, 1.0)
        x = (noise - smooth) * env
        return x / max(np.abs(x).max(), 1e-9) * 0.5

    def pop(dr=0.08):
        n = int(sr * dr); t = np.arange(n) / sr
        return np.sin(2 * np.pi * 750 * t) * np.exp(-t * 45) * 0.5

    def thud(dr=0.18, amp=0.55):
        n = int(sr * dr); t = np.arange(n) / sr
        return np.sin(2 * np.pi * 85 * t) * np.exp(-t * 22) * amp

    starts, cum = {}, 0.0
    for i in idxs:
        starts[i] = cum
        cum += dur(work / f"pad{i:02d}.m4a")
    sfx = np.zeros(int(sr * (total + 0.5)))
    plan = {3: [(0.5, thud, 0.12), (1.3, thud, 0.12), (2.1, thud, 0.12)],
            5: [(0.45, whoosh, 1.0)],
            6: [(0.5, thud, 0.5), (0.2, pop, 0.7)],
            8: [(1.7, thud, 0.7)]}
    for b, items in plan.items():
        for t0, fn, amp in items:
            x = fn() * amp
            i0 = int(sr * (starts[b] + t0))
            sfx[i0:i0 + len(x)] += x[:max(0, len(sfx) - i0)]
    sfx = np.clip(sfx, -1, 1)
    with wave.open(str(work / "sfx.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((sfx * 32767).astype(np.int16).tobytes())

    mix = work / "mix.m4a"
    run([FFMPEG, "-y", "-v", "error", "-i", lev, "-i", work / "sfx.wav",
         "-filter_complex",
         "[1:a]volume=0.20[sfx];[0:a][sfx]amix=inputs=2:duration=first:normalize=0,"
         "alimiter=limit=0.89[mix]",
         "-map", "[mix]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", mix])

    out = HERE / args.output
    run([FFMPEG, "-y", "-v", "error", "-i", video, "-i", mix,
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(clips)} beats, {dur(out):.0f}s)")


if __name__ == "__main__":
    main()
