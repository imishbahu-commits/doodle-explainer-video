#!/usr/bin/env python3
"""Director cut of the mirror video — applies the cinematic-director skill's
Fincher plan:
  - teal shadow grade, lifted blacks, desaturated mids (shadows readable)
  - red reserved for the threat (red channel boosted)
  - exactly ONE camera move: an ease-in punch on beat 15 (the monster reveal)
  - hard cuts everywhere else, band C stays empty black
Beat boundaries come from the real encoded video (frame-mean segmenting).
"""

import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
W, H, FPS = 720, 1280, 30

# manifest order of beat files (section-by-section)
BEAT_FILES = ["001", "002", "003", "005", "006", "007", "004", "008", "009",
              "010", "011", "012", "013", "014", "015", "016", "017", "018",
              "019"]
PUNCH_BEAT = 14          # 0-based index of 015.png ("IN THE BRAIN")


def cut_times(path):
    p = subprocess.Popen(
        ["ffmpeg", "-i", str(path), "-vf", "scale=32:32:flags=area,format=gray",
         "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frames = []
    while True:
        buf = p.stdout.read(1024)
        if len(buf) < 1024:
            break
        frames.append(buf)
    ref, seg_start, cuts = None, None, []
    for i, f in enumerate(frames):
        t = i / FPS
        if ref is None:
            ref, seg_start = f, t
            continue
        diff = sum(abs(a - b) for a, b in zip(ref, f)) / 1024.0
        if diff > 1.5 and t - seg_start >= 0.4:
            cuts.append(seg_start)
            ref, seg_start = f, t
    cuts.append(seg_start)
    return cuts


def fincher_grade(im):
    a = np.array(im).astype(np.float32)
    luma = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2])[:, :, None]
    # desaturate 40% toward luma
    a = a + (luma - a) * 0.40
    # teal in shadows: shift blues/greens up, reds down, proportional to depth
    shadow = np.clip((128 - luma) / 128.0, 0, 1) * 0.55
    a[:, :, 0] -= 9 * shadow[:, :, 0]
    a[:, :, 1] += 5 * shadow[:, :, 0]
    a[:, :, 2] += 11 * shadow[:, :, 0]
    # lift blacks (shadows stay readable — never dead black)
    a += 7
    # red reserved for the threat: boost strongly-red pixels
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    redmask = (r > g * 1.5) & (r > b * 1.5)
    a[:, :, 0][redmask] = np.clip(r[redmask] * 1.18, 0, 255)
    a[:, :, 1][redmask] = np.clip(g[redmask] * 0.9, 0, 255)
    a[:, :, 2][redmask] = np.clip(b[redmask] * 0.9, 0, 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def compose(art, zoom=1.0):
    """Three-band frame: banner / graded art (band B) / empty black band C."""
    frame = Image.new("RGB", (W, H), (0, 0, 0))
    frame.paste(banner, (0, 0))
    if zoom > 1.0:
        z = zoom
        nw, nh = int(art.width * z), int(art.height * z)
        art = art.resize((nw, nh), Image.LANCZOS)
        x0 = (nw - W) // 2
        y0 = (nh - 420) // 2
        art = art.crop((x0, y0, x0 + W, y0 + 420))
    else:
        scale = max(W / art.width, 420 / art.height)
        art = art.resize((round(art.width * scale), round(art.height * scale)),
                         Image.LANCZOS)
        x0 = (art.width - W) // 2
        y0 = (art.height - 420) // 2
        art = art.crop((x0, y0, x0 + W, y0 + 420))
    frame.paste(art, (0, 420))
    return frame


banner = Image.open(HERE / "assets" / "banner.png").convert("RGB").resize((W, 420), Image.LANCZOS)
arts = [fincher_grade(Image.open(HERE / "assets" / f"{n}.png").convert("RGB"))
        for n in BEAT_FILES]


def main():
    cuts = cut_times(HERE / "final.mp4")
    durs = [round(b - a, 4) for a, b in zip(cuts, cuts[1:])]
    durs.append(round(64.7 - cuts[-1], 4)) if cuts[-1] < 64.7 else durs
    # clamp: last segment ends at audio length
    total = sum(durs[:19])
    print("beats:", len(durs), "total:", round(total, 2))

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         str(HERE / "dc_video.mp4")],
        stdin=subprocess.PIPE)
    for i, dur in enumerate(durs[:19]):
        n = max(1, round(dur * FPS))
        for f in range(n):
            if i == PUNCH_BEAT:
                p = ease_in(f / max(1, n - 1))
                zoom = 1.0 + 0.18 * p
            else:
                zoom = 1.0
            frame = compose(arts[i], zoom)
            proc.stdin.write(frame.tobytes())
        print(f"beat {i + 1:>2} done ({n} frames)")
    proc.stdin.close()
    proc.wait()

    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(HERE / "dc_video.mp4"),
                    "-i", str(HERE / "final.mp4"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
                    "-shortest", str(HERE / "director-cut.mp4")], check=True)
    print("wrote director-cut.mp4")


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x * x * x


if __name__ == "__main__":
    main()
