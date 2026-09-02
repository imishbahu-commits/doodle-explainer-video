#!/usr/bin/env python3
"""Full-corpus beat analysis for the uploaded reference videos.

For every video in the uploads/ directory this:
  1. Detects hard-cut / scene-change boundaries with ffmpeg (the "beats").
  2. Computes each on-screen image's start, end and duration in seconds and in
     frames (at the video's real fps).
  3. Extracts the representative frame of EVERY beat (the image that sits on
     screen from the cut until the next cut) and saves it as a PNG.
  4. Writes a per-video JSON manifest and a concatenated corpus manifest with
     per-video aggregate timing stats.

Beats are the atomic unit: every distinct hand-drawn illustration that is shown
and then replaced. Duration = how long the image stays on screen.

Usage (from repo root, with the venv):
  python3 tools/analyze_reference_beats.py --dir uploads --out analysis
"""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_upload_server import _ffmpeg_bin  # reuse the bundled ffmpeg lookup

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".ts")
SCENE_THRESHOLD = 0.30


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path: Path) -> dict:
    """Return fps, duration, width, height for a video."""
    ffmpeg = _ffmpeg_bin()
    p = run([ffmpeg, "-hide_banner", "-i", str(path)])
    err = p.stderr
    info = {}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        info["duration"] = h * 3600 + mn * 60 + s
    fps = None
    m = re.search(r"(?P<r>[0-9.]+)\s+fps", err)
    if m:
        fps = float(m.group("r"))
    m = re.search(r"(\d{2,5})x(\d{2,5})", err)
    if m:
        info["width"], info["height"] = int(m.group(1)), int(m.group(2))
    info["fps"] = fps or round(fps or 30.0)
    return info


def detect_cuts(path: Path, threshold: float) -> list[float]:
    """Return sorted list of cut timestamps (seconds) via ffmpeg scene filter."""
    ffmpeg = _ffmpeg_bin()
    vf = f"select='gt(scene,{threshold})',showinfo"
    p = run([ffmpeg, "-hide_banner", "-i", str(path), "-vf", vf, "-an", "-f", "null", "-"])
    times = []
    for line in p.stderr.splitlines():
        mm = re.search(r"pts_time:([0-9.]+)", line)
        if mm:
            times.append(float(mm.group(1)))
    times.sort()
    # De-dupe near-identical timestamps (within 0.05s) that are double-reported.
    dedup = []
    for t in times:
        if not dedup or t - dedup[-1] > 0.05:
            dedup.append(t)
    return dedup


def extract_frame(ffmpeg, path: Path, at: float, out: Path, size=None, quality=3):
    """Extract a single frame at time `at` as a palette-quantised PNG."""
    tmp = out.with_suffix(out.suffix + ".tmp")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{at:.3f}",
           "-i", str(path), "-frames:v", "1"]
    if size:
        cmd += ["-vf", f"scale={size}:-2"]
    cmd += ["-compression_level", str(quality), "-y", str(tmp)]
    run(cmd)
    # Flat doodles have ~200 colours, so a lossless PNG8 palette quantise keeps
    # the files small enough to commit to git (crisp line art, no visual loss).
    try:
        from PIL import Image
        im = Image.open(tmp).convert("RGB")
        im.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE) \
          .save(out, "PNG", optimize=True)
        tmp.unlink(missing_ok=True)
    except Exception:
        tmp.replace(out)
    return out


def analyze_video(path: Path, outdir: Path, threshold: float) -> dict:
    ffmpeg = _ffmpeg_bin()
    info = probe(path)
    duration = info["duration"]
    fps = info["fps"]
    cuts = detect_cuts(path, threshold)

    # Build beat segments: [0, c0), [c0, c1), ..., [last_cut, duration)
    boundaries = [0.0] + cuts + [duration]
    beats = []
    frame_dir = outdir / "frames" / path.stem
    frame_dir.mkdir(parents=True, exist_ok=True)

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1] - 0.001 if i < len(boundaries) - 2 else duration
        beat_dur = max(end - start, 0.0)
        # Representative frame = just after the cut that introduces this image.
        sample_at = start
        if i > 0 and beat_dur > 0.05:
            sample_at = start + 0.06
        frame_name = f"{path.stem}_beat_{i:04d}.png"
        frame_path = frame_dir / frame_name
        extract_frame(ffmpeg, path, sample_at, frame_path, size="480")
        # Repo-relative path: analysis/frames/<video>/<name>.png
        rel = Path("analysis") / "frames" / path.stem / frame_name
        beats.append({
            "index": i,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(beat_dur, 3),
            "duration_frames": round(beat_dur * fps, 1),
            "image": rel.as_posix(),
        })

    manifest = {
        "video": path.name,
        "path": str(path),
        "fps": fps,
        "width": info.get("width"),
        "height": info.get("height"),
        "duration": duration,
        "beat_count": len(beats),
        "avg_beat_duration": round(duration / max(len(beats), 1), 3),
        "beats": beats,
    }
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="uploads")
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--threshold", type=float, default=SCENE_THRESHOLD)
    ap.add_argument("--videos", nargs="*", default=None, help="subset of filenames")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    src = root / args.dir
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [p for p in src.glob("*") if p.suffix.lower() in VIDEO_EXTENSIONS],
        key=lambda p: p.name,
    )
    if args.videos:
        files = [p for p in files if p.name in args.videos]

    if not files:
        print("no videos found under", src)
        return

    corpus = []
    for idx, p in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {p.name} …", flush=True)
        m = analyze_video(p, out, args.threshold)
        base = out / f"{p.stem}.beats.json"
        base.write_text(json.dumps(m, indent=2))
        corpus.append(m)
        print(f"    {m['beat_count']} beats · avg {m['avg_beat_duration']}s"
              f" ({m['duration']:.1f}s, {m['fps']}fps)", flush=True)

    corpus_path = out / "corpus.beats.json"
    corpus_path.write_text(json.dumps(corpus, indent=2))
    total_beats = sum(m["beat_count"] for m in corpus)
    total_dur = sum(m["duration"] for m in corpus)
    print(f"\nCorpus manifest -> {corpus_path}")
    print(f"{len(files)} videos · {total_beats} beats · {total_dur/60:.1f} min total")


if __name__ == "__main__":
    main()
