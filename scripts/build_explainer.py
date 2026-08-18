#!/usr/bin/env python3
"""build_explainer.py — assemble a YouTube-ready 16:9 explainer video.

Paint-Explainer grammar (measured autopsy in references/):
- 1280x720 @ 30fps, H.264 + AAC, faststart
- hard cuts between beats, slow zoom (Ken Burns) on ~half the beats
- hand-lettered labels (Caveat font) baked in per beat (Pillow — no
  drawtext dependency; the static ffmpeg build lacks libfreetype)
- 0.35s tails + 0.35s gaps = measured 0.7s breath between segments
- audio loudness normalised to -23 LUFS (measured -23.7 on the reference)

Usage: .venv/bin/python3 scripts/build_explainer.py projects/shark-video
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

FONT = str(ROOT / "skills" / "handdrawn-code" / "fonts" / "caveat-700.ttf")
W, H, FPS = 1280, 720, 30
YELLOW, RED = "#FCEB00", "#FF0000"


def run(args, **kw):
    p = subprocess.run([FF, "-y", *args], capture_output=True, text=True, **kw)
    if p.returncode != 0:
        sys.exit("ffmpeg failed:\n" + (p.stderr or "")[-1500:])
    return p


def duration(path):
    p = run(["-i", str(path), "-f", "null", "-"])
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        sys.exit(f"no duration for {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def text_size(draw, txt, font):
    b = draw.textbbox((0, 0), txt, font=font)
    return b[2] - b[0], b[3] - b[1]


def draw_labeled(src, out, text, kind="beat"):
    im = Image.open(src).convert("RGB")
    # fit to 16:9 1280x720 via centre crop
    if im.size[0] / im.size[1] > 16 / 9:
        nh = W * im.size[1] // im.size[0]
        im = im.resize((W, nh), Image.LANCZOS)
        y0 = int((nh - H) * 0.42)
        im = im.crop((0, y0, W, y0 + H))
    else:
        nw = H * im.size[0] // im.size[1]
        im = im.resize((nw, H), Image.LANCZOS)
        x0 = (nw - W) // 2
        im = im.crop((x0, 0, x0 + W, H))
    d = ImageDraw.Draw(im)

    if kind == "title":
        f1 = ImageFont.truetype(FONT, 74)
        for y, t, col in ((H // 2 - 130, "THE BIGGEST FISH IN THE SEA", YELLOW),
                          (H // 2 - 30, "IS NOT WHAT YOU THINK", RED)):
            tw, th = text_size(d, t, f1)
            d.text(((W - tw) / 2, y), t, font=f1, fill=col,
                   stroke_width=6, stroke_fill="black")
    elif kind == "end":
        f1 = ImageFont.truetype(FONT, 58)
        t = "SUBSCRIBE FOR MORE OCEAN STORIES"
        tw, th = text_size(d, t, f1)
        d.text(((W - tw) / 2, H - 170), t, font=f1, fill=YELLOW,
               stroke_width=6, stroke_fill="black")
    else:
        fs = 52 if len(text) <= 14 else (42 if len(text) <= 24 else 34)
        f1 = ImageFont.truetype(FONT, fs)
        tw, th = text_size(d, text, f1)
        d.text(((W - tw) / 2, H - 140), text, font=f1, fill="white",
               stroke_width=5, stroke_fill="black")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return im.size


def zoompan_filter(dur, variant):
    frames = int(round(dur * FPS))
    if variant == "in":
        z = f"min(1.0+0.0012*on,1.14)"
    elif variant == "out":
        z = f"max(1.14-0.0012*on,1.0)"
    else:
        z = f"min(1.08,1.0+0.0008*on)"
    x = f"(iw-iw/zoom)/2+{28 if variant=='pan' else 0}*sin(on/48)"
    return f"zoompan=z='{z}':x='{x}':y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS}"


def build_segment(img, out, dur, variant, fade=True):
    vf = (f"scale=1600:900,{zoompan_filter(dur, variant)}")
    if fade:
        vf += f",fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.55:.2f}:d=0.55"
    run(["-i", str(img), "-frames:v", str(int(round(dur * FPS))),
         "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-crf", "20",
         "-preset", "medium", "-pix_fmt", "yuv420p", "-an", str(out)])


def silence(path, dur):
    run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}",
         "-c:a", "pcm_s16le", "-y", str(path)])


def main():
    proj = ROOT / sys.argv[1] if len(sys.argv) > 1 else ROOT / "projects" / "shark-video"
    beats = json.loads((proj / "beats.json").read_text())
    work = proj / "build"
    lab = work / "lab"
    (work / "segs").mkdir(parents=True, exist_ok=True)
    (work / "aud").mkdir(parents=True, exist_ok=True)

    segs, auds, timeline = [], [], 0.0

    # ---- labelled stills (Pillow) ----
    draw_labeled(proj / "assets" / "title-card.png", lab / "title.png", "", "title")
    draw_labeled(proj / "assets" / "end-card.png", lab / "end.png", "", "end")
    for b in beats["beats"]:
        draw_labeled(proj / b["image"], lab / f"{b['id']:03d}.png", b["label"])
    print("labelled stills done", flush=True)

    # ---- title card ----
    td = beats["title_card"]
    tseg = work / "segs" / "000-title.mp4"
    build_segment(lab / "title.png", tseg, td, "in")
    segs.append(tseg)
    s = work / "aud" / "000-title.wav"
    silence(s, td)
    auds.append(s)
    timeline += td
    print(f"title {td:.1f}s ok", flush=True)

    # ---- beats ----
    variants = ["in", "out", "pan", "in", "out", "pan", "in", "out", "in", "out"]
    for i, b in enumerate(beats["beats"]):
        clip = proj / "audio" / f"{b['id']:02d}.mp3"
        d = duration(clip)
        seg_dur = d + 0.35
        gap = beats["breath_pause"] - 0.35
        out = work / "segs" / f"{b['id']:03d}.mp4"
        build_segment(lab / f"{b['id']:03d}.png", out, seg_dur, variants[i])
        segs.append(out)
        g = work / "aud" / f"gap{i}.wav"
        silence(g, gap)
        auds.append(g)
        auds.append(clip)
        timeline += gap + d
        print(f"beat {b['id']} clip={d:.2f}s seg={seg_dur:.2f}s label={b['label']}", flush=True)

    # ---- end card ----
    ed = beats["end_card"]
    eseg = work / "segs" / "999-end.mp4"
    build_segment(lab / "end.png", eseg, ed, "out")
    segs.append(eseg)
    s = work / "aud" / "999-end.wav"
    silence(s, ed)
    auds.append(s)
    timeline += ed
    print(f"end {ed:.1f}s ok — total {timeline:.1f}s", flush=True)

    # ---- concat video ----
    vlist = work / "vlist.txt"
    vlist.write_text("\n".join(f"file '{s}'" for s in segs))
    vcat = work / "video-only.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(vlist), "-c", "copy", str(vcat)])

    # ---- concat audio ----
    alist = work / "alist.txt"
    wavs = []
    for i, a in enumerate(auds):
        if a.suffix == ".mp3":
            w = work / "aud" / f"c{i:03d}.wav"
            run(["-i", str(a), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(w)])
            wavs.append(w)
        else:
            wavs.append(a)
    alist.write_text("\n".join(f"file '{w}'" for w in wavs))
    acat = work / "audio-raw.wav"
    run(["-f", "concat", "-safe", "0", "-i", str(alist), "-c:a", "pcm_s16le", str(acat)])
    anorm = work / "audio-norm.wav"
    run(["-i", str(acat), "-af", "loudnorm=I=-23:TP=-2.5:LRA=11", "-ar", "44100",
         "-ac", "2", "-c:a", "pcm_s16le", str(anorm)])

    # ---- final mux ----
    final = proj / "final.mp4"
    run(["-i", str(vcat), "-i", str(anorm), "-c:v", "copy", "-c:a", "aac",
         "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart",
         "-shortest", str(final)])
    print(f"FINAL: {final}  ({timeline:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

