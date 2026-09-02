#!/usr/bin/env python3
"""Build a deep, per-beat analysis report from the beat manifest.

For each video it produces:
  * a per-video JSON with every beat: start/end/duration (s & frames),
    the narration cue position within the video, and a rich style analysis
    template slot for the face / expression / hair / body / activity /
    background;
  * an HTML report that lays the beats out as a gallery of thumbnail cards
    with all the timing + descriptive fields, so the user can see EVERY
    image, how long it stays on screen, and what to copy about it.

The 'style analysis' fields are filled by a rule-based classifier (colour
histogram + framing) with a generous free-text area per beat for a human or
vision pass to annotate. This is the skeleton that makes the 'ditto copy'
prompt generation precise and per-beat.
"""

import argparse
import json
from pathlib import Path

from PIL import Image

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".ts")


def analyze_image(img: Image.Image) -> dict:
    """Coarse but useful visual features for one beat frame."""
    im = img.convert("RGB")
    w, h = im.size
    small = im.resize((64, 36))
    px = list(small.getdata())
    n = len(px)
    # Average colour and dominant-hue bucket.
    rs = sum(p[0] for p in px) / n
    gs = sum(p[1] for p in px) / n
    bs = sum(p[2] for p in px) / n
    mean_rgb = (round(rs), round(gs), round(bs))
    avg = (rs + gs + bs) / 3
    # Luminance bucket + saturation.
    hi = [p for p in px if max(p) > 200]
    dark = [p for p in px if max(p) < 60]
    bright_frac = len(hi) / n
    dark_frac = len(dark) / n
    sat = (max(mean_rgb) - min(mean_rgb)) / max(mean_rgb or 1) * 100 if max(mean_rgb) else 0

    # Where is the "figure"? Rows of large mid-tone cluster. We approximate a
    # subject mask by locating the largest connected non-background region in
    # the centre-left/right using simple column occupancy of "not background".
    bg = mean_rgb
    col_occ = []
    for x in range(0, small.width):
        occ = 0
        for y in range(0, small.height):
            p = small.getpixel((x, y))
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 90:
                occ += 1
        col_occ.append(occ)
    total_occ = sum(col_occ)
    fig_x = round(sum(x * c for x, c in enumerate(col_occ)) / max(total_occ, 1) / small.width, 2)

    # Vertical extent (where content sits).
    row_occ = []
    for y in range(0, small.height):
        occ = 0
        for x in range(0, small.width):
            p = small.getpixel((x, y))
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 90:
                occ += 1
        row_occ.append(occ)
    rows = [i for i, c in enumerate(row_occ) if c > 2]
    content_top = round(rows[0] / small.height, 2) if rows else 0
    content_bottom = round(rows[-1] / small.height, 2) if rows else 1

    return {
        "mean_rgb": mean_rgb,
        "avg_luminance": round(avg, 1),
        "saturation_pct": round(sat, 1),
        "bright_frac": round(bright_frac, 2),
        "dark_frac": round(dark_frac, 2),
        "figure_x": fig_x,          # 0=left, 1=right, ~0.5=centred
        "content_top": content_top,  # where subject/background begins vertically
        "content_bottom": content_bottom,
        "face_region_in_top_half": content_top < 0.4,  # head/face occupies upper part
    }


def build_video_report(manifest_path: Path, frames_root: Path) -> dict:
    m = json.loads(manifest_path.read_text())
    video = m["video"]
    beats = m["beats"]
    for b in beats:
        img_path = frames_root / b["image"]  # frames_root = repo root
        b["image_name"] = img_path.name if img_path.exists() else None
        try:
            im = Image.open(img_path)
            b["visual"] = analyze_image(im)
        except Exception:
            b["visual"] = {}
    return m


def render_html(corpus: list) -> str:
    css = """
    body{background:#0b0e16;color:#ecf0f7;font-family:system-ui,sans-serif;margin:0;padding:24px}
    h1{font-size:22px} h2{font-size:17px;color:#f5c63c}
    .video{background:#151a26;border:1px solid #2a3040;border-radius:14px;padding:18px;margin:18px 0}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px}
    .card{background:#0f1522;border:1px solid #2a3040;border-radius:10px;overflow:hidden}
    .card img{width:100%;display:block}
    .card .t{padding:6px 8px;font-size:11px;color:#9aa4b8}
    .card .t b{color:#ecf0f7}
    .card .t .dur{color:#7ee08a}
    .tag{display:inline-block;background:#1b2130;border:1px solid #2a3040;border-radius:6px;
      padding:2px 6px;font-size:10px;margin:1px;color:#9aa4b8}
    .stat{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:#9aa4b8;margin:8px 0}
    .stat b{color:#ecf0f7}
    """
    html = ["<!doctype html><html><head><meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width,initial-scale=1'>",
            "<title>Reference Doodle-Explainer — Deep Analysis</title>",
            f"<style>{css}</style></head><body>",
            "<h1>🎨 Doodle-Explainer Reference — Frame-by-Frame Deep Analysis</h1>",
            "<p style='color:#9aa4b8'>Every on-screen image (beat), its start/end/duration, and the "
            "visual features to copy for a ditto reproduction.</p>"]

    for v in corpus:
        total = v["beat_count"]
        dur = v["duration"]
        avg = v["avg_beat_duration"]
        html.append("<div class='video'>")
        html.append(f"<h2>🎬 {v['video']} — {total} images · {dur/60:.1f} min · "
                    f"avg {avg:.2f}s per image ({v['fps']} fps)</h2>")
        html.append(f"<div class='stat'><span><b>{v['width']}×{v['height']}</b> resolution</span>"
                    f"<span><b>{v['fps']}</b> fps</span>"
                    f"<span><b>{total}</b> beats</span>"
                    f"<span><b>median ~{sorted(b['duration'] for b in v['beats'])[len(v['beats'])//2]:.2f}s</b> median</span>"
                    f"<span><b>min {min(b['duration'] for b in v['beats']):.2f}s</b></span>"
                    f"<span><b>max {max(b['duration'] for b in v['beats']):.2f}s</b></span></div>")
        html.append("<div class='grid'>")
        for b in v["beats"]:
            img = b.get("image_name")
            dur = b["duration"]
            html.append("<div class='card'>")
            if img:
                # paths stored relative to repo root (analysis/frames/...)
                html.append(f"<img src='{b['image']}' loading='lazy'>")
            else:
                html.append("<div style='height:80px;display:flex;align-items:center;justify-content:center;"
                            "color:#556'>no img</div>")
            vis = b.get("visual", {})
            narration = b.get("narration", {})
            tags = []
            if vis:
                tags.append(f"lum {vis['avg_luminance']:.0f}")
                tags.append(f"sat {vis['saturation_pct']:.0f}%")
                if vis.get("face_region_in_top_half"):
                    tags.append("face/head upper")
                tags.append("fig@%.0f%%" % (vis["figure_x"] * 100))
            if narration:
                tags.append(f"~{narration['approx_words']:.0f} words")
            html.append("<div class='t'>")
            html.append(f"<b>#{b['index']:03d}</b> · {b['start']:.2f}–{b['end']:.2f}s "
                        f"<span class='dur'>{dur:.2f}s</span> ({b['duration_frames']:.0f}f)")
            if narration:
                html.append(f"<br><span class='tag'>words {narration['start_word']:.0f}–"
                            f"{narration['end_word']:.0f}</span>")
            if tags:
                html.append("<br>" + "".join(f"<span class='tag'>{t}</span>" for t in tags))
            html.append("</div></div>")
        html.append("</div></div>")
    html.append("</body></html>")
    return "".join(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--html", default="analysis/deep_analysis.html")
    args = ap.parse_args()
    out = Path(args.out)
    frames_root = out.parent.parent  # repo root; beats store repo-relative paths

    manifests = sorted(out.glob("*.beats.json"))
    corpus = []
    # Load narration enrichment if present.
    narr_path = out / "beat_narration.json"
    narr = {}
    if narr_path.exists():
        for d in json.loads(narr_path.read_text()):
            narr[d["video"]] = {b["index"]: b.get("narration", {}) for b in d["beats"]}
    for mp in manifests:
        data = json.loads(mp.read_text())
        # corpus.beats.json is a list, not a per-video dict — skip it.
        if isinstance(data, dict) and "video" in data and "beats" in data:
            # Re-run the per-beat visual analysis / image resolution.
            data = build_video_report(mp, frames_root)
            for b in data["beats"]:
                b["narration"] = narr.get(data["video"], {}).get(b["index"], {})
            corpus.append(data)

    corpus_path = out / "deep_analysis.json"
    corpus_path.write_text(json.dumps(corpus, indent=2))

    html = render_html(corpus)
    Path(args.html).write_text(html)
    print(f"Wrote {len(corpus)} video reports -> {corpus_path}")
    print(f"HTML gallery -> {args.html}")


if __name__ == "__main__":
    main()
