#!/usr/bin/env python3
"""Extract and annotate five evidentiary frame grabs per analyzed video."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "references" / "paint-explainer-analysis-4v"
OUT = ANALYSIS / "frames"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

EVIDENCE = {
    "15204": [
        (0.50, None, "Cold-open contents pyramid: white canvas; multiple chapter thumbnails; hard cut at 00:01.267."),
        (10.00, None, "Chapter world: title strip is ~10% of frame height; ocean gradient is baked behind flat inked subject."),
        (8.20, 17.50, "Within one 9.87 s Cambrian shot: silhouette/reveal staging changes while the background and camera remain locked."),
        (39.00, None, "Emphasis graphic: thick red arrow/label over the same chapter lockup; no lower-third or caption track."),
        (591.20, 594.80, "In-shot label/pose update: the 60-feet callout appears and the whale shifts locally; seafloor/title stay locked."),
    ],
    "15207": [
        (0.50, None, "Cold-open story mosaic on white; each card previews one warrior; opening shot ends at 00:01.767."),
        (8.00, None, "Default history tableau: top chapter title, grounded stick figure, flat earth strip, >45% negative space."),
        (17.20, 19.80, "Same-canvas character reveal: hair/face/pose swaps and labels animate; horizon and camera stay fixed."),
        (31.30, None, "Host close-up: oversized head, minimal eyes/open mouth, stick body, and large white negative space; no lip sync."),
        (622.00, None, "Blackbeard chapter: reusable white-canvas character asset; separate sword/arm layers support rotation or swaps."),
    ],
    "15215": [
        (0.50, None, "Cold-open era mosaic; first hard cut at 00:01.433."),
        (4.00, None, "Environment-heavy variant: painted lava bands and smoky sky; stick human centered below title strip."),
        (12.00, 16.00, "Threat build inside one setting: hand/face/text elements appear in steps; background is not panned."),
        (250.00, None, "Survival POV uses a full illustrated environment; text callout remains red while character fills stay flat."),
        (627.00, 632.00, "Creature attack is staged by pose swaps/translation and reaction-face replacement; no lip sync."),
    ],
    "15219": [
        (0.50, None, "Cold-open incident mosaic; 12 cases previewed before the first story."),
        (4.00, None, "Night setup: simplified depth layers, dark overlay, two lit windows; title remains black on white."),
        (10.00, 13.00, "Door sequence: woman/door/intruder states swap on a fixed room plate; action is cut/pose driven."),
        (240.00, None, "Action tableau: three anti-terror figures use modular weapons/arms over a minimal ground strip."),
        (801.00, 806.00, "Final chapter setup: protagonist/prop plate to storefront tableau; scene changes by hard replacement."),
    ],
}


def frame_at(path: Path, seconds: float) -> Image.Image:
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000.0)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"cannot decode {path} at {seconds}")
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


def timestamp(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def guide_frame(image: Image.Image, label: str) -> Image.Image:
    image = image.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    # Quantified guides: thirds and the persistent ~10% title band.
    for x in (w / 3, 2 * w / 3):
        draw.line((x, 0, x, h), fill=(230, 35, 35, 115), width=1)
    for y in (h / 3, 2 * h / 3):
        draw.line((0, y, w, y), fill=(230, 35, 35, 80), width=1)
    title_h = round(h * 0.10)
    draw.rectangle((0, 0, w - 1, title_h), outline=(255, 30, 30, 210), width=2)
    draw.rectangle((5, h - 26, 150, h - 5), fill=(255, 255, 255, 220))
    draw.text((10, h - 24), label, fill=(190, 0, 0, 255), font=font(FONT_BOLD, 14))
    return image


def annotated(title: str, time_a: float, time_b: float | None, note: str, video: Path) -> Image.Image:
    left = guide_frame(frame_at(video, time_a), timestamp(time_a))
    if time_b is None:
        visual = left.resize((960, 540), Image.Resampling.LANCZOS)
    else:
        right = guide_frame(frame_at(video, time_b), timestamp(time_b))
        arrow = Image.new("RGB", (80, 360), "white")
        ad = ImageDraw.Draw(arrow)
        ad.line((10, 180, 65, 180), fill="#E31B23", width=8)
        ad.polygon([(65, 180), (45, 165), (45, 195)], fill="#E31B23")
        pair = Image.new("RGB", (1360, 360), "white")
        pair.paste(left, (0, 0)); pair.paste(arrow, (640, 0)); pair.paste(right, (720, 0))
        visual = pair.resize((1020, 270), Image.Resampling.LANCZOS)
    panel_h = 170
    canvas = Image.new("RGB", (visual.width, visual.height + panel_h), "white")
    canvas.paste(visual, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, visual.height, visual.width, visual.height + 4), fill="#E31B23")
    draw.text((18, visual.height + 14), title, fill="black", font=font(FONT_BOLD, 22))
    time_text = timestamp(time_a) if time_b is None else f"{timestamp(time_a)} → {timestamp(time_b)} ({time_b-time_a:.2f} s)"
    draw.text((18, visual.height + 46), f"Evidence timestamp: {time_text}", fill="#B00000", font=font(FONT_BOLD, 16))
    wrapped = textwrap.wrap(note, width=105)
    y = visual.height + 76
    for line in wrapped[:4]:
        draw.text((18, y), line, fill="#202020", font=font(FONT_REGULAR, 16))
        y += 23
    return canvas


def main() -> None:
    manifest = json.loads((ANALYSIS / "analysis_manifest.json").read_text(encoding="utf-8"))
    by_id = {str(item["file_id"]): item for item in manifest["videos"]}
    OUT.mkdir(parents=True, exist_ok=True)
    for file_id, entries in EVIDENCE.items():
        item = by_id[file_id]
        video = ROOT / item["path"]
        made = []
        for index, (time_a, time_b, note) in enumerate(entries, 1):
            image = annotated(item["title"], time_a, time_b, note, video)
            path = OUT / f"{file_id}-{index:02d}.jpg"
            image.save(path, quality=91, optimize=True)
            made.append(image)
        # A compact per-video overview for quick review.
        thumbs = []
        for image in made:
            thumb = image.copy(); thumb.thumbnail((650, 430), Image.Resampling.LANCZOS); thumbs.append(thumb)
        width = max(image.width for image in thumbs)
        height = sum(image.height for image in thumbs) + 12 * (len(thumbs) - 1)
        sheet = Image.new("RGB", (width, height), "#D8D8D8")
        y = 0
        for image in thumbs:
            sheet.paste(image, ((width - image.width) // 2, y)); y += image.height + 12
        sheet.save(OUT / f"{file_id}-contact-sheet.jpg", quality=88, optimize=True)
        print(f"{file_id}: wrote {len(made)} annotated frames + contact sheet")


if __name__ == "__main__":
    main()
