#!/usr/bin/env python3
"""Comedy pass: generate SFX + burn meme captions + mix to the hook.

Uses Ultimate-Video-Editing sfx-guide recipes (lavfi, not copyrighted
meme audio) timed to the Rule-of-3 / stamp / splat grammar in MEME_TIMING.md.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SFX = HERE / "sfx"
FONT = HERE.parents[1] / "skills" / "ae-motion" / "fonts" / "kalam-700.ttf"
SRC = HERE / "final.mp4"
OUT = HERE / "final_meme.mp4"


def run(cmd):
    subprocess.run(cmd, check=True)


def make_sfx():
    SFX.mkdir(exist_ok=True)

    def lavfi(name, src, extra=None):
        out = SFX / name
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src]
        if extra:
            cmd += ["-af", extra]
        cmd += [str(out)]
        run(cmd)

    # whoosh in
    lavfi("whoosh.wav", "anoisesrc=d=0.28:c=pink:a=0.35:r=44100",
          "afade=t=in:st=0:d=0.08,afade=t=out:st=0.16:d=0.12,highpass=f=400,lowpass=f=7000,volume=2.2")
    # bonk / rejection stamp
    lavfi("bonk.wav",
          "aevalsrc='0.9*sin(2*PI*90*t)*exp(-18*t)+0.45*sin(2*PI*180*t)*exp(-22*t)':s=44100:d=0.35")
    # record-scratch-ish (noise + pitch drop) for the box twist
    lavfi("scratch.wav", "anoisesrc=d=0.22:c=white:a=0.25:r=44100",
          "asetrate=44100*0.55,aresample=44100,highpass=f=800,afade=t=out:st=0.12:d=0.1,volume=1.6")
    # ding / same-picture reveal
    lavfi("ding.wav",
          "aevalsrc='0.55*sin(2*PI*880*t)*exp(-6*t)+0.35*sin(2*PI*1320*t)*exp(-8*t)':s=44100:d=0.55")
    # pop / 4th wall
    lavfi("pop.wav",
          "aevalsrc='0.7*sin(2*PI*520*t)*exp(-30*t)':s=44100:d=0.18")
    # splat (banana melt)
    lavfi("splat.wav", "anoisesrc=d=0.3:c=brown:a=0.5:r=44100",
          "alimiter=limit=0.6,afade=t=out:st=0.12:d=0.18,volume=2.4")
    # boing
    lavfi("boing.wav",
          "aevalsrc='0.55*sin(2*PI*(420-180*t)*t)*exp(-5*t)':s=44100:d=0.45")
    # stamp / transformation
    lavfi("stamp.wav",
          "aevalsrc='0.8*sin(2*PI*60*t)*exp(-10*t)+0.3*sin(2*PI*240*t)*exp(-16*t)':s=44100:d=0.4")
    # shutter
    lavfi("shutter.wav",
          "aevalsrc='0.5*sin(2*PI*2000*t)*exp(-40*t)+0.35*sin(2*PI*900*t)*exp(-25*t)':s=44100:d=0.16")
    # wah (descending)
    lavfi("wah.wav",
          "aevalsrc='0.45*sin(2*PI*(360-220*t)*t)*exp(-3*t)':s=44100:d=0.55")
    # boom victory
    lavfi("boom.wav",
          "aevalsrc='0.7*sin(2*PI*45*t)*exp(-4*t)+0.35*sin(2*PI*90*t)*exp(-6*t)':s=44100:d=0.7")
    print("sfx ready")


# (file, delay_ms, volume)
CUES = [
    ("whoosh.wav", 40, 0.55),
    ("bonk.wav", 1180, 0.85),
    ("whoosh.wav", 2400, 0.55),
    ("bonk.wav", 3620, 0.85),
    ("scratch.wav", 4800, 0.70),
    ("ding.wav", 8200, 0.55),
    ("pop.wav", 10700, 0.70),
    ("splat.wav", 13100, 0.75),
    ("boing.wav", 13400, 0.45),
    ("stamp.wav", 16400, 0.80),
    ("shutter.wav", 19100, 0.55),
    ("wah.wav", 22100, 0.50),
    ("boom.wav", 24600, 0.85),
]


CAPS = [
    ("SETUP 1 OF 3", 0.00, 2.35),
    ("SETUP 2 OF 3", 2.40, 4.75),
    ("PLOT TWIST", 4.80, 8.05),
    ("THEY ARE THE SAME PICTURE", 8.10, 10.65),
    ("POV  APE CLOCKED YOU", 10.70, 13.05),
    ("THE BANANA ARC", 13.10, 16.35),
    ("GLOW-UP UNLOCKED", 16.40, 18.85),
    ("ZOOM IN ON THE CRIME", 18.90, 21.95),
    ("NO WAIST GANG", 22.00, 24.45),
    ("WE APPROVE THIS MESSAGE", 24.50, 26.80),
]


def caption_png(text: str, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1280, 92
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype(str(FONT), 44)
    except Exception:
        fnt = ImageFont.load_default()
    # bar
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 150))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((W / 2 + dx, H / 2 + dy), text, font=fnt, fill=(0, 0, 0, 255), anchor="mm")
    d.text((W / 2, H / 2), text, font=fnt, fill=(255, 255, 255, 255), anchor="mm")
    path.parent.mkdir(exist_ok=True)
    im.save(path)


def mix():
    cap_dir = HERE / "build" / "caps"
    cap_dir.mkdir(parents=True, exist_ok=True)
    cap_files = []
    for i, (text, _a, _b) in enumerate(CAPS):
        p = cap_dir / f"c{i:02d}.png"
        caption_png(text, p)
        cap_files.append(p)

    inputs = ["-i", str(SRC)]
    for name, _ms, _vol in CUES:
        inputs += ["-i", str(SFX / name)]
    sfx_n = len(CUES)
    for p in cap_files:
        inputs += ["-i", str(p)]

    filters = []
    last = "0:v"
    for i, (_t, a, b) in enumerate(CAPS):
        idx = 1 + sfx_n + i
        nxt = f"v{i}"
        filters.append(
            f"[{last}][{idx}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]"
        )
        last = nxt

    mix_in = ["[0:a]"]
    for i, (_name, ms, vol) in enumerate(CUES, start=1):
        filters.append(f"[{i}:a]adelay={ms}|{ms},volume={vol}[s{i}]")
        mix_in.append(f"[s{i}]")
    filters.append(
        f"{''.join(mix_in)}amix=inputs={1+sfx_n}:normalize=0:duration=first,"
        f"alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    )
    filters.append(f"[{last}]null[v]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k",
           "-t", "26.81", "-movflags", "+faststart",
           str(OUT)]
    run(cmd)
    hook = HERE / "skinny-fat-ape-hook.mp4"
    hook.write_bytes(OUT.read_bytes())
    print(f"wrote {OUT} and {hook}")


if __name__ == "__main__":
    make_sfx()
    mix()
