#!/usr/bin/env python3
"""Studio showreel — a demo of what code-only animation can do.

Techniques shown, one per scene:
  1. kinetic typography (type-on + draw-on underline)
  2. easing curves (linear vs overshoot — the anti-robotic difference)
  3. anticipation + squash & stretch (the cartoon jump)
  4. blink & expression cycles
  5. audio-driven lip sync (mouth follows the real narration waveform)
  6. walk cycle + multiplane parallax
  7. camera punch-in
  8. impact: anticipation slam, screen shake, dust particles, pop text
  9. outro

Every frame is drawn programmatically (PIL) with per-frame boiling-line
jitter so nothing reads as machined. Encoded with ffmpeg.
"""

import math
import random
import struct
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 24
INK = (28, 28, 34)
PAPER = (255, 253, 242)
SKY = (208, 231, 246)
NAVY = (28, 34, 66)
ACCENT = (235, 64, 52)
GOLD = (250, 196, 60)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HERE = Path(__file__).resolve().parent
NARRATION = HERE / "audio" / "narration.mp3"

_font_cache = {}


def F(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]


def text(dr, s, x, y, size=44, fill=INK, anchor="mm"):
    dr.text((x, y), s, font=F(size), fill=fill, anchor=anchor)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_in_cubic(x):
    x = max(0.0, min(1.0, x))
    return x * x * x


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    v = x - 1
    return 1 + c3 * v * v * v + c1 * v * v


def jit(seed, amp=1.6):
    r = random.Random(seed * 1000003 + 7)
    return (r.random() - 0.5) * 2 * amp


def draw_character(dr, x, y, frame, sx=1.0, sy=1.0, mouth="closed",
                   blink=0.0, arm_a=(-0.5, 0.5), leg_a=(0.25, -0.25),
                   scale=1.0, jitter=1.6):
    s = scale
    jx = lambda seed: jit(seed, jitter)
    body_w, body_h = 52 * s * sx, 62 * s * sy
    by = y - 100 * s * sy
    dr.ellipse([x - body_w + jx(frame), by - body_h + jx(frame + 3),
                x + body_w + jx(frame + 5), by + body_h + jx(frame + 7)],
               fill=(96, 165, 235), outline=INK, width=4)
    hr = 44 * s * min(sx, sy)
    hy = y - 175 * s * sy
    dr.ellipse([x - hr + jx(frame + 9), hy - hr + jx(frame + 11),
                x + hr + jx(frame + 13), hy + hr + jx(frame + 15)],
               fill=(246, 215, 192), outline=INK, width=4)
    ey = hy - 6 * s
    ex = 16 * s
    if blink > 0.5:
        dr.line([(x - ex - 7, ey), (x - ex + 7, ey)], fill=INK, width=4)
        dr.line([(x + ex - 7, ey), (x + ex + 7, ey)], fill=INK, width=4)
    else:
        dr.ellipse([x - ex - 5, ey - 5, x - ex + 5, ey + 5], fill=INK)
        dr.ellipse([x + ex - 5, ey - 5, x + ex + 5, ey + 5], fill=INK)
    my = hy + 18 * s
    if mouth == "open":
        dr.ellipse([x - 10, my - 6, x + 10, my + 14], fill=(122, 46, 46),
                   outline=INK, width=3)
    elif mouth == "mid":
        dr.ellipse([x - 7, my - 2, x + 7, my + 8], fill=INK)
    elif mouth == "happy":
        dr.arc([x - 13, my - 14, x + 13, my + 8], 20, 160, fill=INK, width=4)
    else:
        dr.line([x - 8, my, x + 8, my], fill=INK, width=4)
    sh = y - 140 * s * sy
    for side, ang in enumerate(arm_a):
        hx = x + (-30 if side == 0 else 30) * s
        ex2 = hx + math.sin(ang) * 58 * s
        ey2 = sh + math.cos(ang) * 58 * s * sy
        dr.line([(hx + jx(frame + 20 + side), sh),
                 (ex2 + jx(frame + 23 + side), ey2)], fill=INK, width=6)
        dr.ellipse([ex2 - 7, ey2 - 7, ex2 + 7, ey2 + 7], fill=(246, 215, 192),
                   outline=INK, width=3)
    hip_y = y - 55 * s * sy
    for side, ang in enumerate(leg_a):
        hx2 = x + (-16 if side == 0 else 16) * s
        fx = hx2 + math.sin(ang) * 30 * s
        fy = hip_y + math.cos(ang) * 55 * s * sy
        dr.line([(hx2, hip_y), (fx, fy)], fill=INK, width=6)
    dr.line([x - 26, y, x + 26, y], fill=INK, width=6)


def caption(dr, s, t, y=660, size=38, fill=(90, 95, 110)):
    text(dr, s, W / 2, y, size=size, fill=fill)


def scene_bg(bg=PAPER):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def scene_title(frame, t, dur):
    im, dr = scene_bg(NAVY)
    frac = min(1.0, t / 0.6)
    y = 330
    dr.line([W / 2 - 300 * frac, y, W / 2 + 300 * frac, y], fill=GOLD, width=6)
    s = "MOTION LAB — STUDIO SHOWREEL"
    n = int(len(s) * min(1.0, t / 1.6)) + 1 if t < 1.6 else len(s)
    shown = s[:n]
    tw = dr.textlength(shown, font=F(64))
    x0 = W / 2 - tw / 2
    for i, ch in enumerate(shown):
        cx = x0 + dr.textlength(shown[:i + 1], font=F(64)) - dr.textlength(ch, font=F(64)) / 2
        pop = 1.0
        if i == n - 1 and t < 1.6:
            pop = 1.0 + 0.35 * max(0.0, 1 - (t * 1.6 - i) / 0.25)
        dr.text((cx, 250), ch, font=F(64), fill=(255, 255, 255), anchor="mm")
    if t > 1.2:
        text(dr, "every frame below is animated from code",
             W / 2, 420, size=30, fill=(190, 196, 220))
    return im


def scene_easing(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "TIMING & EASING — the difference between robotic and alive", t)
    y_lin, y_ease = 220, 420
    x_lin = 100 + (W - 300) * (t / dur)
    x_ease = 100 + (W - 300) * ease_out_back(min(1.0, t / dur))
    for (x, y, lab, col) in [(x_lin, y_lin, "LINEAR — robotic", (170, 175, 190)),
                             (x_ease, y_ease, "EASED — alive", (96, 165, 235))]:
        dr.ellipse([x - 34, y - 34, x + 34, y + 34], fill=col, outline=INK, width=4)
        dr.ellipse([x - 14, y - 12, x - 6, y - 4], fill=INK)
        dr.ellipse([x + 6, y - 12, x + 14, y - 4], fill=INK)
        text(dr, lab, 60, y, size=30, fill=col, anchor="lm")
    dr.line([W - 200, 120, W - 200, 560], fill=INK, width=4)
    return im


def scene_jump(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "ANTICIPATION + SQUASH & STRETCH", t)
    gx, ground = 420, 560
    if t < 0.45:
        p = t / 0.45
        sx, sy = 1.0 + 0.25 * p, 1.0 - 0.3 * p
        y = ground
    elif t < 0.6:
        p = (t - 0.45) / 0.15
        sx, sy = 1.0 - 0.35 * p, 1.0 + 0.4 * p
        y = ground - 40 * p
    elif t < 1.25:
        p = (t - 0.6) / 0.65
        y = ground - 190 * (1 - 4 * (p - 0.5) ** 2)
        sx, sy = 0.85, 1.1
    elif t < 1.42:
        p = (t - 1.25) / 0.17
        y = ground
        sx, sy = 1.0 + 0.45 * p, 1.0 - 0.35 * p
    else:
        p = (t - 1.42) / 0.8
        k = math.exp(-4 * p) * math.cos(9 * p)
        sx, sy = 1.0 + 0.12 * k, 1.0 - 0.12 * k
        y = ground
    hgt = (ground - y) / 190.0
    sh = max(0.25, 1.0 - hgt * 0.7)
    dr.ellipse([gx - 60 * sh, ground + 26, gx + 60 * sh, ground + 40],
               fill=(200, 200, 205))
    mouth = "open" if 0.45 < t < 1.25 else "happy" if t > 1.25 else "closed"
    draw_character(dr, gx, y, frame, sx=sx, sy=sy, mouth=mouth,
                   arm_a=(-1.6, 1.6) if 0.45 < t < 1.25 else (-0.5, 0.5),
                   leg_a=(0.3, -0.3))
    dr.line([0, ground + 40, W, ground + 40], fill=INK, width=5)
    return im


def big_face(dr, cx, cy, r, expression, blink, frame):
    jx = lambda seed: jit(seed, 1.4)
    dr.ellipse([cx - r + jx(frame), cy - r + jx(frame + 1),
                cx + r + jx(frame + 2), cy + r + jx(frame + 3)],
               fill=(246, 215, 192), outline=INK, width=5)
    ey = cy - r * 0.25
    ex = r * 0.45
    if blink > 0.5:
        dr.line([(cx - ex - 12, ey), (cx - ex + 12, ey)], fill=INK, width=5)
        dr.line([(cx + ex - 12, ey), (cx + ex + 12, ey)], fill=INK, width=5)
    elif expression == "happy":
        dr.arc([cx - ex - 12, ey - 14, cx - ex + 12, ey + 10], 200, 340, fill=INK, width=5)
        dr.arc([cx + ex - 12, ey - 14, cx + ex + 12, ey + 10], 200, 340, fill=INK, width=5)
    elif expression == "surprised":
        dr.ellipse([cx - ex - 9, ey - 11, cx - ex + 9, ey + 11], fill=INK)
        dr.ellipse([cx + ex - 9, ey - 11, cx + ex + 9, ey + 11], fill=INK)
    else:
        dr.ellipse([cx - ex - 8, ey - 8, cx - ex + 8, ey + 8], fill=INK)
        dr.ellipse([cx + ex - 8, ey - 8, cx + ex + 8, ey + 8], fill=INK)
    by = cy - r * 0.45
    if expression == "surprised":
        dr.line([(cx - ex - 10, by), (cx - ex + 2, by - 10)], fill=INK, width=5)
        dr.line([(cx + ex - 2, by - 10), (cx + ex + 10, by)], fill=INK, width=5)
        dr.ellipse([cx - 9, cy + r * 0.3, cx + 9, cy + r * 0.52], fill=INK)
    elif expression == "happy":
        dr.arc([cx - r * 0.55, cy + r * 0.15, cx + r * 0.55, cy + r * 0.75],
               20, 160, fill=INK, width=6)
        dr.ellipse([cx - r * 0.72, cy + r * 0.3, cx - r * 0.52, cy + r * 0.42],
                   fill=(240, 150, 150))
        dr.ellipse([cx + r * 0.52, cy + r * 0.3, cx + r * 0.72, cy + r * 0.42],
                   fill=(240, 150, 150))
    else:
        dr.line([cx - r * 0.25, cy + r * 0.45, cx + r * 0.25, cy + r * 0.45],
                fill=INK, width=5)


def blink_value(t, offset=0.0):
    p = (t * 0.85 + offset) % 3.1
    return 1.0 if p < 0.13 else 0.0


def scene_expressions(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "BLINK + EXPRESSION CYCLES", t)
    for i, expr in enumerate(["neutral", "happy", "surprised"]):
        cx = 240 + i * 400
        big_face(dr, cx, 330, 120, expr, blink_value(t, i * 0.9), frame + i * 50)
        text(dr, expr.upper(), cx, 560, size=34, fill=(90, 95, 110))
    return im


def load_rms():
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(NARRATION), "-f", "f32le",
         "-ac", "1", "-ar", str(FPS), "-"], capture_output=True)
    raw = p.stdout
    return [abs(struct.unpack("<f", raw[i:i + 4])[0]) for i in range(0, len(raw) - 3, 4)]


RMS = load_rms()


def scene_lipsync(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "LIP SYNC — the mouth follows the real narration waveform", t)
    i = min(len(RMS) - 1, max(0, frame))
    o = min(1.0, RMS[i] * 9)
    mouth = "open" if o > 0.35 else "mid" if o > 0.08 else "closed"
    draw_character(dr, 400, 560, frame, mouth=mouth,
                   arm_a=(-0.2, 0.35), sy=1.0)
    for k in range(14):
        v = min(1.0, RMS[min(len(RMS) - 1, max(0, frame + k - 7))] * 9)
        bx = 820 + k * 30
        bh = 20 + 130 * v
        dr.rounded_rectangle([bx, 400 - bh / 2, bx + 18, 400 + bh / 2],
                             radius=6, fill=ACCENT if v > 0.3 else (190, 196, 210))
    text(dr, "narration", 1020, 420, size=30, fill=(90, 95, 110))
    return im


def scene_walk(frame, t, dur):
    im, dr = scene_bg(SKY)
    ph = t * 5.2
    for layer, speed, color, r in [
        (0.25, 1100, (255, 255, 255), 90),
        (0.55, 1900, (170, 208, 160), 260)]:
        off = (speed * t) % 1900
        for cx in [-1900 + off, off]:
            dr.ellipse([cx - r, 430 - r * 0.6, cx + r, 430 + r * 0.6],
                       fill=color, outline=INK, width=3)
    for k in range(4):
        cx = (k * 380 + t * 28) % (W + 300) - 150
        cy = 110 + 40 * math.sin(k * 2.1)
        dr.ellipse([cx - 70, cy, cx + 70, cy + 46], fill=(255, 255, 255),
                   outline=INK, width=3)
        dr.ellipse([cx - 30, cy - 24, cx + 46, cy + 30], fill=(255, 255, 255),
                   outline=INK, width=3)
    gy = 560
    dr.line([0, gy + 44, W, gy + 44], fill=INK, width=5)
    off = (t * 220) % 60
    for x in range(-60, W + 60, 60):
        dr.line([x + off, gy + 44, x + off + 26, gy + 44], fill=INK, width=5)
    leg_a = (math.sin(ph) * 0.7, math.sin(ph + math.pi) * 0.7)
    arm_a = (-math.sin(ph) * 0.7, math.sin(ph) * 0.7)
    bob = abs(math.cos(ph)) * 7
    draw_character(dr, 500, 560 - bob, frame, mouth="happy",
                   arm_a=arm_a, leg_a=leg_a, blink=blink_value(t, 1.3))
    caption(dr, "WALK CYCLE + MULTIPLANE PARALLAX", t, y=668)
    return im


def scene_punchin(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "CAMERA PUNCH-IN", t, y=640)
    draw_character(dr, 500, 560, frame,
                   mouth="open" if t >= dur / 2 else "closed", blink=0.0)
    text(dr, "did you see that?", 500, 240, size=40, fill=(90, 95, 110))
    z = 1.0 + 1.15 * ease_in_cubic(min(1.0, t / dur))
    fx, fy = 500, 380
    cw, ch = W / z, H / z
    box = (fx - cw / 2, fy - ch / 2, fx + cw / 2, fy + ch / 2)
    box = (max(0, int(box[0])), max(0, int(box[1])),
           min(W, int(box[2])), min(H, int(box[3])))
    return im.crop(box).resize((W, H), Image.LANCZOS)


def scene_impact(frame, t, dur):
    im, dr = scene_bg()
    caption(dr, "IMPACT — anticipation, slam, screen shake, dust, pop", t)
    gx, gy = 420, 540
    if t < 0.5:
        p = ease(t / 0.5)
        ang = -2.4 * p
        sy_sq = 1.0
        shake = 0
        dust = False
        bang = 0
    elif t < 0.68:
        p = (t - 0.5) / 0.18
        ang = -2.4 + (2.4 - 0.0) * ease_in_cubic(p)
        sy_sq = 1.0 - 0.25 * p
        shake = 0
        dust = p > 0.85
        bang = p > 0.85
    else:
        p = min(1.0, (t - 0.68) / 0.35)
        ang = 0.0
        sy_sq = 1.0 - 0.25 * (1 - p)
        shake = max(0.0, 1 - (t - 0.68) / 0.3)
        dust = True
        bang = p < 0.35
    draw_character(dr, gx, gy, frame, sx=1.0, sy=sy_sq,
                   mouth="open" if bang else "closed",
                   arm_a=(ang, -0.5), leg_a=(0.3, -0.3))
    hx = gx - 30 + math.sin(ang) * 58
    hy = gy - 140 + math.cos(ang) * 58
    stamp_ang = 0.0 if t > 0.68 else ang * 0.3
    sw, sh = 150, 90
    cx0, cy0 = hx + 110, hy + 40
    corners = []
    for (dx, dy) in [(-sw / 2, -sh / 2), (sw / 2, -sh / 2), (sw / 2, sh / 2), (-sw / 2, sh / 2)]:
        c, s = math.cos(stamp_ang), math.sin(stamp_ang)
        corners.append((cx0 + dx * c - dy * s, cy0 + dx * s + dy * c))
    dr.polygon(corners, fill=ACCENT, outline=INK)
    text(dr, "BANG!", (corners[0][0] + corners[2][0]) / 2,
         (corners[0][1] + corners[2][1]) / 2, size=38, fill=(255, 255, 255))
    if dust:
        ix, iy = cx0, cy0 + sh / 2
        for k in range(9):
            a = (t - 0.66) * 5
            ang = k / 9 * math.tau + 0.4
            d = min(1.0, a / 0.55)
            px = ix + math.cos(ang) * 150 * d
            py = iy + math.sin(ang) * 90 * d - 60 * d * d
            r = 8 * (1 - d * 0.4)
            dr.ellipse([px - r, py - r, px + r, py + r], fill=(170, 170, 180))
    if bang:
        pop = 1.0 + 0.5 * max(0.0, 1 - (t - 0.68) / 0.12)
        text(dr, "!", cx0, cy0 - 150, size=int(90 * pop), fill=ACCENT)
    if shake > 0:
        r = random.Random(frame)
        dx = round((r.random() - 0.5) * 2 * 7 * shake)
        dy = round((r.random() - 0.5) * 2 * 7 * shake)
        canvas = Image.new("RGB", (W, H), PAPER)
        canvas.paste(im, (dx, dy))
        im = canvas
    return im


def scene_outro(frame, t, dur):
    im, dr = scene_bg(NAVY)
    text(dr, "EVERY FRAME ABOVE WAS GENERATED FROM CODE",
         W / 2, 230, size=46, fill=(255, 255, 255))
    if t > 0.5:
        text(dr, "easing · squash & stretch · blink · lip sync · walk cycle · "
                 "parallax · punch-in · impact", W / 2, 330, size=30,
             fill=(190, 196, 220))
        text(dr, "zero hand-drawn frames. zero robotic feel.",
             W / 2, 420, size=36, fill=GOLD)
    dr.ellipse([W / 2 - 30, 520, W / 2 + 30, 580], fill=ACCENT)
    dr.ellipse([W / 2 - 12, 538, W / 2 - 4, 546], fill=(255, 255, 255))
    dr.ellipse([W / 2 + 4, 538, W / 2 + 12, 546], fill=(255, 255, 255))
    dr.arc([W / 2 - 12, 552, W / 2 + 12, 566], 20, 160, fill=(255, 255, 255), width=3)
    return im


SCENES = [
    ("title", scene_title, 2.6),
    ("easing", scene_easing, 3.2),
    ("jump", scene_jump, 2.6),
    ("expressions", scene_expressions, 3.2),
    ("lipsync", scene_lipsync, len(RMS) / FPS + 0.6),
    ("walk", scene_walk, 3.2),
    ("punchin", scene_punchin, 1.8),
    ("impact", scene_impact, 2.2),
    ("outro", scene_outro, 2.6),
]


def main():
    out = HERE / "studio-showreel.mp4"
    video_only = HERE / "video_only.mp4"
    ffmpeg = "ffmpeg"
    total_frames = sum(max(1, round(d * FPS)) for _, _, d in SCENES)
    print(f"rendering {len(SCENES)} scenes, {total_frames} frames")
    proc = subprocess.Popen(
        [ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_only)],
        stdin=subprocess.PIPE)
    frame_no = 0
    for name, fn, dur in SCENES:
        n = max(1, round(dur * FPS))
        for i in range(n):
            t = i / FPS
            im = fn(frame_no, t, dur)
            proc.stdin.write(im.tobytes())
            frame_no += 1
        print(f"  scene {name}: {dur:.1f}s done")
    proc.stdin.close()
    proc.wait()
    start_s = sum(d for _, _, d in SCENES[:4])
    start_ms = int(start_s * 1000)
    tail_s = sum(d for _, _, d in SCENES[5:]) + 0.2
    mix = HERE / "audio_track.m4a"
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(NARRATION),
                    "-af", f"adelay={start_ms}|{start_ms},apad=pad_dur={tail_s}",
                    "-ar", "44100", "-ac", "2", str(mix)], check=True)
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(video_only),
                    "-i", str(mix), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", str(out)], check=True)
    print(f"wrote {out} ({frame_no / FPS:.1f}s)")


if __name__ == "__main__":
    main()
