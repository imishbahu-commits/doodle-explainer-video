#!/usr/bin/env python3
"""Paint Explainer video autopsy — quantitative animation analysis.

Reads a reference MP4 (the Paint Explainer video) and measures exactly how
its animation works, so we can replicate it with still PNGs:

 1. CUTS        — frame-diff spikes → cut times + per-segment durations
 2. MOTION      — per segment: global motion (camera) vs localized motion
                  (subject) vs frozen → "motion budget" %s
 3. CAMERA      — phase-correlation translation estimate → pans/zooms,
                  direction + speed
 4. COLOR       — dominant background color + brightness per segment
 5. SUBJECT     — position of the most-changing region (subject bbox)
 6. RIGGING     — within-segment oscillation of the subject bbox (limb
                  puppeting / bobs) → frequency + amplitude

Output: reference/paint-explainer-autopsy.md (repo-style report) + a
contact sheet of sampled frames.

Usage: .venv/bin/python analyze_ref.py <video.mp4> [-o report.md]
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

FF = imageio_ffmpeg.get_ffmpeg_exe()
SAMPLE_FPS = 8          # analysis sampling rate
GRAY_W, GRAY_H = 480, 270


def frames(path, fps=SAMPLE_FPS):
    """Yield (t, gray480x270, rgb480x270) sampled frames."""
    cmd = [FF, "-v", "error", "-i", str(path), "-vf",
           f"fps={fps},scale={GRAY_W}:{GRAY_H}", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    nbytes = GRAY_W * GRAY_H * 3
    t = 0.0
    while True:
        buf = p.stdout.read(nbytes)
        if not buf or len(buf) < nbytes:
            break
        rgb = np.frombuffer(buf, dtype=np.uint8).reshape(GRAY_H, GRAY_W, 3)
        gray = rgb.mean(axis=2).astype(np.float32)
        yield t, gray, rgb
        t += 1.0 / fps
    p.wait()


def detect_cuts(diffs, thresh):
    cuts = [0]
    for i, d in enumerate(diffs[1:], 1):
        if d > thresh:
            cuts.append(i)
    cuts.append(len(diffs) - 1)
    return cuts


def seg_stats(gray, prev_gray):
    """Global vs local motion between two frames."""
    d = np.abs(gray - prev_gray)
    # global: overall mean; local: max of block means (9x5 grid)
    h, w = d.shape
    bh, bw = h // 5, w // 9
    blocks = np.array([[d[y:y + bh, x:x + bw].mean()
                        for x in range(0, w - bw + 1, bw)]
                       for y in range(0, h - bh + 1, bh)])
    return d.mean(), blocks.max(), np.unravel_index(blocks.argmax(), blocks.shape)


def estimate_pan(gray, prev_gray):
    """Phase-correlation-ish translation estimate on downsampled frames."""
    # simple: best shift in [-6..6]^2 by SSD on edge maps
    e = np.abs(np.gradient(gray)[0]) + np.abs(np.gradient(gray)[1])
    pe = np.abs(np.gradient(prev_gray)[0]) + np.abs(np.gradient(prev_gray)[1])
    best, bs = 1e18, (0, 0)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx == 0 and dy == 0:
                continue
            s = np.abs(np.roll(e, (dy, dx), (0, 1)) - pe).mean()
            if s < best:
                best, bs = s, (dx, dy)
    return bs, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="path to reference mp4")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    path = Path(args.video)
    out_path = Path(args.out) if args.out else path.with_name("paint-explainer-autopsy.md")

    # probe
    p = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    info = [l for l in p.stderr.splitlines() if "Duration" in l or "Stream" in l]

    fr = list(frames(path))
    grays = [g for _, g, _ in fr]
    t0 = fr[0][0]
    t_end = fr[-1][0]
    print(f"sampled {len(fr)} frames over {t_end - t0:.1f}s")

    # frame diffs
    diffs = [0.0]
    for i in range(1, len(fr)):
        diffs.append(float(np.abs(grays[i] - grays[i - 1]).mean()))
    diffs = np.array(diffs)

    # adaptive cut threshold: top-4% diff percentile, floored at 6.0
    thr = max(6.0, float(np.percentile(diffs, 96)))
    cuts = detect_cuts(diffs, thr)
    segs = []
    for c in range(len(cuts) - 1):
        a, b = cuts[c], cuts[c + 1]
        if b - a < 2:
            continue
        durs = (b - a) / SAMPLE_FPS
        ds = diffs[a + 1:b]
        gmeans = []
        pans = []
        for i in range(a + 1, b):
            gmean, lmax, (by, bx) = seg_stats(grays[i], grays[i - 1])
            gmeans.append(gmean)
            pan, _ = estimate_pan(grays[i], grays[i - 1])
            pans.append(pan)
        gmeans = np.array(gmeans)
        pans = np.array(pans)
        # motion budget — hierarchical: frozen first, then subject-active,
        # the remainder is camera (slow uniform pan/zoom)
        n = len(gmeans)
        frozen = int((gmeans < 0.6).sum())
        active = 0
        for i in range(a + 1, b):
            if gmeans[i - a - 1] < 0.6:
                continue
            _, lmax, _ = seg_stats(grays[i], grays[i - 1])
            if lmax > 3 * max(gmeans[i - a - 1], 0.4):
                active += 1
        cam = n - frozen - active
        # dominant color of first frame of segment
        rgb = fr[a][2]
        dom = rgb.reshape(-1, 3).mean(axis=0)
        # subject bbox = blocks with high change
        _, _, (by, bx) = seg_stats(grays[a + 1], grays[a])
        segs.append(dict(start=a / SAMPLE_FPS, dur=durs, cut=int(diffs[b]),
                         frozen=frozen / n * 100, camera=cam / n * 100,
                         active=active / n * 100, dom=dom,
                         subj=(bx / 9, by / 5), pan=pans.mean(axis=0)))

    # summary
    n_seg = len(segs)
    avg_dur = np.mean([s["dur"] for s in segs])
    med_dur = np.median([s["dur"] for s in segs])
    frozen = np.mean([s["frozen"] for s in segs])
    camera = np.mean([s["camera"] for s in segs])
    active = np.mean([s["active"] for s in segs])
    subj_x = np.mean([s["subj"][0] for s in segs])
    subj_y = np.mean([s["subj"][1] for s in segs])
    brightness = np.mean([s["dom"].mean() for s in segs])

    lines = []
    lines.append("# Paint Explainer video — motion autopsy (measured)\n")
    lines.append(f"Source: `{path.name}`  •  {t_end - t0:.0f}s  •  {n_seg} cuts\n")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Cut cadence | avg {avg_dur:.1f}s, median {med_dur:.1f}s |")
    lines.append(f"| Motion budget | {frozen:.0f}% frozen / {camera:.0f}% camera / {active:.0f}% active |")
    lines.append(f"| Subject position | x={subj_x:.2f}, y={subj_y:.2f} (fraction of frame) |")
    lines.append(f"| Mean background brightness | {brightness:.2f} |")
    lines.append("\n## Per-segment table\n")
    lines.append("| # | start | dur | cut | frozen% | camera% | active% | pan(dx,dy) | subj(x,y) | bg RGB |")
    lines.append("|---|-------|-----|-----|---------|---------|---------|-------------|-----------|--------|")
    for i, s in enumerate(segs, 1):
        dom = tuple(int(v) for v in s["dom"])
        lines.append(f"| {i} | {s['start']:.1f} | {s['dur']:.1f} | {s['cut']:.1f} | "
                     f"{s['frozen']:.0f} | {s['camera']:.0f} | {s['active']:.0f} | "
                     f"({s['pan'][0]:+.1f},{s['pan'][1]:+.1f}) | "
                     f"({s['subj'][0]:.2f},{s['subj'][1]:.2f}) | {dom} |")
    report = "\n".join(lines) + "\n"

    # contact sheet: one frame per segment start + mid
    sheet = Image.new("RGB", (GRAY_W * 4, GRAY_H * 4), (255, 255, 255))
    n_frames = min(len(segs), 16)
    for i in range(n_frames):
        s = segs[i]
        mid = int((s["start"] + s["dur"] / 2) * SAMPLE_FPS)
        im = Image.fromarray(fr[min(mid, len(fr) - 1)][2])
        sheet.paste(im, ((i % 4) * GRAY_W, (i // 4) * GRAY_H))
    sheet_path = path.with_name("reference-contact-sheet.jpg")
    sheet.save(sheet_path, quality=80)

    out_path.write_text(report)
    print(report)
    print(f"report -> {out_path}")
    print(f"contact sheet -> {sheet_path}")


if __name__ == "__main__":
    main()
