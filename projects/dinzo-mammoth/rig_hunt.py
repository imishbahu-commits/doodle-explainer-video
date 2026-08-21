#!/usr/bin/env python3
"""Mammoth Hunt — custom skeletal rig engine (60 fps, per-frame drawn).

The hunter is NOT a PNG with keyframes: it is a skeletal stick rig drawn
every frame (hip/knee/ankle/shoulder/elbow joints) with a real run cycle
(contact -> down -> pass -> up), wind-up, throw and follow-through —
like a human animator, not a slideshow.

The spear is a projectile with gravity (rotation follows velocity), the
mammoth is a keyed PNG that idles, shakes on impact, rotates to the
ground around its feet, and lands in a "down" pose. Blood + dust are
keyed FX with scale-pops. Backgrounds are pixel-static; title bar
overlay on top.

Usage: .venv/bin/python rig_hunt.py [start] [end] [-o out.mp4]
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
FFMPEG = Path(sys.prefix) / "bin" / "ffmpeg"
if not FFMPEG.exists():
    import imageio_ffmpeg
    FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
W, H, FPS = 1376, 768, 60
GAP = 0.25
CX, CY = W / 2, H / 2
GROUND = 648            # ground line
BAR_H = int(H * 0.12)   # title strip

# ------------------------------------------------------------------ fonts
def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ------------------------------------------------------------------ keying
def key_character(src, out, pad=12):
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    dist = np.sqrt(((255.0 - a[:, :, :3]) ** 2).sum(axis=2)) / np.sqrt(3 * 255.0 ** 2)
    alpha = np.clip((dist - 0.05) / 0.10, 0.0, 1.0)
    im.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), "L"))
    im.putalpha(im.getchannel("A").filter(ImageFilter.MinFilter(3)))
    im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(0.8)))
    bbox = im.getchannel("A").getbbox()
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    im.crop((x0, y0, x1, y1)).save(out)
    return out


def rotate_around(img, deg, pivot, target):
    """Rotate img by deg around pivot (in img coords), place pivot at target."""
    ang = math.radians(deg)
    c, s = math.cos(ang), math.sin(ang)
    r = Image.new("RGBA", img.size, (0, 0, 0, 0))
    # paste rotated into padded canvas
    rot = img.rotate(deg, resample=Image.BICUBIC, expand=True)
    # new pivot position inside rot: rotate offset (px, py) from top-left
    px, py = pivot
    ox, oy = px, py
    nx = ox * c - oy * s
    ny = ox * s + oy * c
    r.paste(rot, (0, 0))
    del r
    x0 = target[0] - nx
    y0 = target[1] - ny
    return rot, (round(x0), round(y0))


# ------------------------------------------------------------------ rig
class Hunter:
    """Skeletal stick-figure drawn per frame. dir=-1 faces left."""

    def __init__(self, s=1.0):
        self.s = s
        self.dir = -1
        self.torso = 52 * s
        self.thigh = 34 * s
        self.shin = 32 * s
        self.arm_u = 26 * s
        self.arm_l = 24 * s
        self.head_r = 11 * s

    def seg(self, d, p, ang, ln):
        return (p[0] + self.dir * math.sin(ang) * ln, p[1] + math.cos(ang) * ln)

    def draw(self, d, mode, t, x, gy, spear_img=None, spear_ang=0.0, held=True,
             line=5, color=(20, 20, 24, 255)):
        s = self.s
        bob = 0.0
        lean = 0.10
        leg_ang1 = leg_ang2 = 0.15
        knee1 = knee2 = 0.25
        arm_ang1 = arm_ang2 = 0.3
        elb1 = elb2 = 0.4

        if mode == "run":
            f = 3.0
            ph = 2 * math.pi * f * t
            swing = 0.75
            leg_ang1 = lean + swing * math.sin(ph)
            leg_ang2 = lean + swing * math.sin(ph + math.pi)
            knee1 = 0.15 + max(0.0, -math.cos(ph)) * 1.25
            knee2 = 0.15 + max(0.0, -math.cos(ph + math.pi)) * 1.25
            arm_ang1 = lean - 0.85 * swing * math.sin(ph + math.pi)
            arm_ang2 = lean - 0.85 * swing * math.sin(ph)
            elb1 = 0.55 + 0.3 * max(0.0, math.cos(ph))
            elb2 = 0.55 + 0.3 * max(0.0, math.cos(ph + math.pi))
            lean = 0.30
            bob = -abs(math.sin(ph)) * 7 * s
        elif mode == "walk":
            f = 2.2
            ph = 2 * math.pi * f * t
            swing = 0.5
            leg_ang1 = lean + swing * math.sin(ph)
            leg_ang2 = lean + swing * math.sin(ph + math.pi)
            knee1 = 0.2 + max(0.0, -math.cos(ph)) * 0.7
            knee2 = 0.2 + max(0.0, -math.cos(ph + math.pi)) * 0.7
            arm_ang1 = lean - 0.6 * swing * math.sin(ph + math.pi)
            arm_ang2 = lean - 0.6 * swing * math.sin(ph)
            bob = -abs(math.sin(ph)) * 5 * s
        elif mode == "windup":
            # arm pulls back (anticipation), body leans back slightly
            k = min(1.0, t / 0.55)
            k = 1 - (1 - k) ** 3
            arm_ang2 = lean + 0.35 - 2.9 * k
            elb2 = 0.35 + 0.9 * k
            lean = 0.16 - 0.10 * k
            leg_ang1 = leg_ang2 = 0.18
        elif mode == "throw":
            k = min(1.0, t / 0.28)
            k = k ** 2
            arm_ang2 = -2.55 + 4.4 * k
            elb2 = 1.25 - 1.0 * k
            lean = 0.06 + 0.22 * k
            leg_ang1 = leg_ang2 = 0.22
        elif mode == "follow":
            arm_ang2 = 1.35
            elb2 = 0.3
            lean = 0.28
        elif mode == "peek":
            arm_ang2 = -0.4
            elb2 = 1.2
        else:  # stand
            pass

        hip = (x, gy - self.thigh * 0.94 + bob)
        sh = self.seg(d, hip, lean, self.torso)
        # far leg
        k1 = self.seg(d, hip, leg_ang1, self.thigh)
        f1 = self.seg(d, k1, leg_ang1 + knee1, self.shin)
        # near leg
        k2 = self.seg(d, hip, leg_ang2, self.thigh)
        f2 = self.seg(d, k2, leg_ang2 + knee2, self.shin)
        # far arm
        e1 = self.seg(d, sh, arm_ang1, self.arm_u)
        h1 = self.seg(d, e1, arm_ang1 + elb1, self.arm_l)
        # near arm (spear arm)
        e2 = self.seg(d, sh, arm_ang2, self.arm_u)
        h2 = self.seg(d, e2, arm_ang2 + elb2, self.arm_l)
        head = (sh[0] + self.dir * math.sin(lean) * 10 * s, sh[1] - 13 * s)

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        L = max(3, int(line * s))
        dr.line([k1, f1], fill=color, width=L)
        dr.line([k2, f2], fill=color, width=L)
        dr.line([hip, sh], fill=color, width=L)
        dr.line([sh, e1, h1], fill=color, width=L)
        dr.line([sh, e2, h2], fill=color, width=L)
        dr.ellipse([head[0] - self.head_r, head[1] - self.head_r,
                    head[0] + self.head_r, head[1] + self.head_r],
                   fill=(245, 225, 200, 255), outline=color, width=max(2, int(3 * s)))
        if mode == "peek":
            # only head + one arm + spear tip visible above rock
            return img, head
        if spear_img is not None and held:
            hand = h2
            sp = spear_img.copy()
            a = math.degrees(arm_ang2) * -0.6 - 20
            sp = sp.rotate(a, resample=Image.BICUBIC, expand=True)
            img.alpha_composite(sp, (round(hand[0] - sp.width / 2),
                                    round(hand[1] - sp.height / 2)))
        return img, head


# ------------------------------------------------------------------ assets
ASSETS = {}


def load_assets():
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    for name in ["char_mammoth", "char_mammoth_hurt", "char_mammoth_fall",
                 "char_mammoth_down", "fx_blood", "fx_dust", "prop_rock",
                 "prop_spear"]:
        out = work / f"{name}_cut.png"
        key_character(HERE / "assets" / f"{name}.png", out)
        ASSETS[name] = Image.open(out).convert("RGBA")
    for name in ["bg_savanna", "bg_dusk"]:
        ASSETS[name] = Image.open(HERE / "assets" / f"{name}.png").convert("RGB").resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ beats
CHAPTERS = {1: "THE HUNT", 4: "THE THROW", 8: "THE FALL"}

def chapter_for(i):
    c = "THE HUNT"
    for k in sorted(CHAPTERS):
        if i >= k:
            c = CHAPTERS[k]
    return c


# mammoth feet position + scale per beat
def draw_mammoth(beat, t, d):
    """Return (layer_img, pos) or None."""
    base = ASSETS["char_mammoth"]
    mx, mscale = 430, 1.0
    if beat >= 8:
        mx = 470
    if beat >= 9:
        base = ASSETS["char_mammoth_down"]
        w = base.width * mscale
        return base.resize((round(w), round(base.height * mscale)), Image.LANCZOS), (round(mx), round(GROUND - base.height * mscale + 30))
    if beat in (6, 7):
        base = ASSETS["char_mammoth_hurt"] if beat == 7 or t > d * 0.5 else base
    if beat == 8:
        # fall: rotate around feet with ease-in
        k = min(1.0, max(0.0, (t - 0.4) / 1.1))
        k = k ** 2.2
        base = ASSETS["char_mammoth_hurt"] if k < 0.85 else ASSETS["char_mammoth_fall"]
        if k >= 1.0:
            base = ASSETS["char_mammoth_down"]
            w = base.width * mscale
            return base.resize((round(w), round(base.height * mscale)), Image.LANCZOS), (round(mx), round(GROUND - base.height * mscale + 30))
        img = base.resize((round(base.width * mscale), round(base.height * mscale)), Image.LANCZOS)
        pivot = (img.width * 0.82, img.height - 14)
        rot, pos = rotate_around(img, -78 * k, pivot, (mx + 40, GROUND - 6))
        return rot, pos
    # idle / hurt
    img = base.resize((round(base.width * mscale), round(base.height * mscale)), Image.LANCZOS)
    bob = math.sin(2 * math.pi * 0.5 * t) * 3 if beat < 6 else 0
    if beat == 7:
        bob = math.sin(2 * math.pi * 8 * t) * 5 * math.exp(-2.5 * t)
    if beat == 6:
        bob = math.sin(2 * math.pi * 7 * t) * 3 * math.exp(-3 * t)
    rot = math.sin(2 * math.pi * 0.5 * t) * 0.6 if beat < 6 else 0
    img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    return img, (round(mx - img.width / 2 + 60), round(GROUND - img.height + 8 + bob))


def draw_scene(beat, t, d, hunter, spear, rock):
    """Compose one frame."""
    bg = ASSETS["bg_savanna"] if beat < 10 else ASSETS["bg_dusk"]
    frame = bg.copy().convert("RGBA")

    # rock (right side)
    rw = 260
    rock_img = rock.resize((rw, round(rock.height * rw / rock.width)), Image.LANCZOS)
    frame.alpha_composite(rock_img, (1160, GROUND - rock_img.height + 26))

    # mammoth
    m = draw_mammoth(beat, t, d)
    if m:
        frame.alpha_composite(m[0], m[1])

    hunter_img = None
    if beat == 2:
        hh = Hunter(0.9)
        img, head = hh.draw(None, "peek", t, 1030, GROUND, spear_img=spear if t < 4 else None, held=True)
        # clip to rock: only show above rock top
        rock_top = GROUND - rock_img.height + 26
        clip = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        clip.paste(img, (0, 0), img)
        frame.alpha_composite(clip, (0, 0))
        frame.paste(rock_img, (1160, GROUND - rock_img.height + 26), rock_img)  # rock in front
    elif beat == 3:
        hh = Hunter(1.0)
        x = 1180 - (1180 - 600) * min(1.0, t / d)
        img, _ = hh.draw(None, "run", t, x, GROUND)
        frame.alpha_composite(img, (0, 0))
    elif beat == 4:
        hh = Hunter(1.0)
        img, _ = hh.draw(None, "windup", t, 640, GROUND, spear_img=spear, held=True)
        frame.alpha_composite(img, (0, 0))
    elif beat == 5:
        hh = Hunter(1.0)
        rel = min(1.0, t / 0.35)
        img, _ = hh.draw(None, "throw" if rel < 1 else "follow", t, 640, GROUND, spear_img=None, held=False)
        frame.alpha_composite(img, (0, 0))
        # spear projectile
        if rel >= 1:
            ft = t - 0.35
            vx, vy, g = -520, -330, 980
            px = 560 + vx * ft
            py = 500 + vy * ft + 0.5 * g * ft * ft
            ang = math.degrees(math.atan2(vy + g * ft, vx))
            sp = spear.rotate(-ang + 180, resample=Image.BICUBIC, expand=True)
            frame.alpha_composite(sp, (round(px - sp.width / 2), round(py - sp.height / 2)))
    elif beat == 6:
        hh = Hunter(1.0)
        img, _ = hh.draw(None, "follow", t, 640, GROUND)
        frame.alpha_composite(img, (0, 0))
        # stuck spear + blood
        sp = spear.rotate(-115, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(sp, (round(470 - sp.width / 2), round(430 - sp.height / 2)))
        bt = min(1.0, max(0.0, (t - 0.15) / 0.25))
        k = 1 - (1 - bt) ** 3
        bw = int(170 * (0.5 + 0.7 * k))
        bimg = ASSETS["fx_blood"].resize((bw, round(ASSETS["fx_blood"].height * bw / ASSETS["fx_blood"].width)), Image.LANCZOS)
        frame.alpha_composite(bimg, (round(470 - bimg.width / 2), round(420 - bimg.height / 2)))
    elif beat == 7:
        hh = Hunter(1.0)
        img, _ = hh.draw(None, "follow", t, 640, GROUND)
        frame.alpha_composite(img, (0, 0))
        sp = spear.rotate(-115, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(sp, (round(470 - sp.width / 2), round(430 - sp.height / 2)))
        bimg = ASSETS["fx_blood"].resize((200, round(ASSETS["fx_blood"].height * 200 / ASSETS["fx_blood"].width)), Image.LANCZOS)
        frame.alpha_composite(bimg, (round(470 - bimg.width / 2), round(420 - bimg.height / 2)))
    elif beat == 8:
        # dust at fall
        if t > 1.4:
            dt = min(1.0, (t - 1.4) / 0.6)
            dw = int(300 * (0.4 + 0.9 * dt))
            dimg = ASSETS["fx_dust"].resize((dw, round(ASSETS["fx_dust"].height * dw / ASSETS["fx_dust"].width)), Image.LANCZOS)
            dimg.putalpha(dimg.getchannel("A").point(lambda p: int(p * (1 - 0.45 * dt))))
            frame.alpha_composite(dimg, (round(470 - dimg.width / 2), round(GROUND - 40)))
    elif beat == 9:
        hh = Hunter(1.0)
        x = 900 - (900 - 620) * min(1.0, t / d)
        img, _ = hh.draw(None, "walk", t, x, GROUND)
        frame.alpha_composite(img, (0, 0))
        sp = spear.rotate(-115, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(sp, (round(470 - sp.width / 2), round(430 - sp.height / 2)))
    elif beat == 10:
        hh = Hunter(1.0)
        img, _ = hh.draw(None, "stand", t, 700, GROUND)
        frame.alpha_composite(img, (0, 0))
        sp = spear.rotate(-115, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(sp, (round(470 - sp.width / 2), round(430 - sp.height / 2)))

    # title bar overlay
    dr = ImageDraw.Draw(frame)
    dr.rectangle([0, 0, W, BAR_H], fill=(255, 255, 255, 255))
    dr.rectangle([0, BAR_H - 3, W, BAR_H], fill=(0, 0, 0, 255))
    title = chapter_for(beat)
    f = font(52)
    tw = dr.textlength(title, font=f)
    dr.text(((W - tw) / 2, BAR_H / 2 - 30), title, font=f, fill=(0, 0, 0, 255))

    if beat == 10:
        # fade out at the end
        k = min(1.0, max(0.0, (t - (d - 1.0)) / 1.0))
        if k > 0:
            black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * k)))
            frame.alpha_composite(black, (0, 0))
    return frame.convert("RGB")


# ------------------------------------------------------------------ video
def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{p.stderr[-2500:]}")
    return p.stdout


def dur(path):
    p = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def verify_video(path, min_bytes=50_000):
    if not path.exists() or path.stat().st_size < min_bytes:
        return False
    p = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    return p.returncode == 0 and len(p.stderr.strip()) == 0


def pad_audio(src, out):
    run([FFMPEG, "-y", "-v", "error", "-i", src,
         "-af", f"apad=pad_dur={GAP},aresample=44100",
         "-ac", "2", "-c:a", "aac", "-b:a", "160k", out])


def render_beat(idx, d, out, hunter, spear, rock):
    n = max(1, round(d * FPS))
    proc = subprocess.Popen(
        [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        frame = draw_scene(idx, t, d, hunter, spear, rock)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if not verify_video(out):
        raise SystemExit(f"render failed beat {idx:02d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=int, nargs="?", default=1)
    ap.add_argument("end", type=int, nargs="?")
    ap.add_argument("-o", "--output", default="dinzo-mammoth-part1.mp4")
    args = ap.parse_args()

    audio = HERE / "audio"
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    load_assets()
    hunter = Hunter(1.0)
    spear = ASSETS["prop_spear"]
    rock = ASSETS["prop_rock"]

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
        clip = work / f"beat{i:02d}_rig.mp4"
        if not verify_video(clip) or clip.stat().st_mtime < aud.stat().st_mtime:
            render_beat(i, d, clip, hunter, spear, rock)
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

    total = sum(dur(p) for p in padded)
    import wave
    sr = 44100

    def whoosh(dr=0.25):
        n = int(sr * dr); t = np.arange(n) / sr
        noise = np.random.randn(n)
        smooth = np.convolve(noise, np.ones(12) / 12, mode="same")
        env = np.exp(-t * 14) * np.minimum(t / 0.03, 1.0)
        sweep = np.sin(2 * np.pi * (250 * t + 450 * t * t / dr)) * 0.35
        x = (noise - smooth + sweep) * env
        return x / max(np.abs(x).max(), 1e-9) * 0.5

    def pop(dr=0.08):
        n = int(sr * dr); t = np.arange(n) / sr
        return np.sin(2 * np.pi * 750 * t) * np.exp(-t * 45) * 0.5

    def thud(dr=0.18, amp=0.55):
        n = int(sr * dr); t = np.arange(n) / sr
        return np.sin(2 * np.pi * 85 * t) * np.exp(-t * 22) * amp

    starts = {}
    acc = 0.0
    for i in idxs:
        starts[i] = acc
        acc += dur(padded[len(starts) - 1]) if len(starts) > 1 else 0
    # fix: cumulative offsets
    cum = 0.0
    for i in idxs:
        starts[i] = cum
        cum += dur(pad_audio and (work / f"pad{i:02d}.m4a"))

    sfx = np.zeros(int(sr * (total + 0.5)))
    plan = {3: [(0.4, thud, 0.18), (1.1, thud, 0.18), (1.8, thud, 0.18), (2.5, thud, 0.18)],
            5: [(0.4, whoosh, 1.0)],
            6: [(0.5, thud, 0.5)],
            7: [(0.3, thud, 0.22)],
            8: [(1.5, thud, 0.7), (1.5, whoosh, 0.6)]}
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
