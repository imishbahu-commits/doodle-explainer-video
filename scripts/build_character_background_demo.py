#!/usr/bin/env python3
"""Build a small cutout-motion demo from a white-background character master."""
from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

RESAMPLE = Image.Resampling.LANCZOS


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize and center-crop an image to exactly ``size``."""
    width, height = size
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), RESAMPLE)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def white_background_cutout(path: Path) -> Image.Image:
    """Remove only near-white pixels connected to the canvas edge.

    Enclosed white details such as eye whites remain opaque. This is safer than a
    global chroma key for illustrated characters.
    """
    rgb = np.asarray(Image.open(path).convert("RGB"))
    bright = rgb.min(axis=2) >= 226
    neutral = (rgb.max(axis=2) - rgb.min(axis=2)) <= 34
    candidate = bright & neutral

    seed = np.zeros(candidate.shape, dtype=bool)
    seed[0, :] = candidate[0, :]
    seed[-1, :] = candidate[-1, :]
    seed[:, 0] = candidate[:, 0]
    seed[:, -1] = candidate[:, -1]
    exterior = ndimage.binary_propagation(seed, mask=candidate)
    foreground = ~exterior

    # Keep the largest connected foreground object and softly antialias its edge.
    labels, count = ndimage.label(foreground)
    if count == 0:
        raise RuntimeError("No foreground character found")
    sizes = ndimage.sum(foreground, labels, range(1, count + 1))
    main = labels == (int(np.argmax(sizes)) + 1)
    main = ndimage.binary_fill_holes(main)
    ys, xs = np.nonzero(main)
    pad = 12
    x0, x1 = max(0, xs.min() - pad), min(rgb.shape[1], xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(rgb.shape[0], ys.max() + pad + 1)

    alpha = Image.fromarray((main * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.65))
    rgba = Image.fromarray(rgb, "RGB").convert("RGBA")
    rgba.putalpha(alpha)
    return rgba.crop((x0, y0, x1, y1))


def add_long_robe(character: Image.Image, phase: float = 0.0) -> Image.Image:
    """Cover the legs with a simple robe whose hem can sway during translation."""
    actor = character.copy()
    width, height = actor.size
    overlay = Image.new("RGBA", actor.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    sway = math.sin(phase) * width * 0.018
    lift = math.cos(phase) * height * 0.006
    top_y = height * 0.685
    hem_y = height * 0.975
    points = [
        (width * 0.285, top_y),
        (width * 0.695, top_y),
        (width * 0.755 + sway, hem_y - lift),
        (width * 0.49 + sway * 0.25, hem_y + lift),
        (width * 0.225 + sway, hem_y - lift),
    ]
    ink = (48, 29, 23, 255)
    cloth = (139, 128, 76, 255)
    draw.polygon(points, fill=cloth)
    draw.line(points + [points[0]], fill=ink, width=max(3, round(width * 0.012)), joint="curve")
    # The top line reads as the existing belt; restrained folds keep the body crude.
    draw.line((width * 0.29, top_y + 2, width * 0.69, top_y + 2), fill=(88, 70, 39, 255), width=3)
    for fraction in (0.38, 0.50, 0.62):
        x = width * fraction + sway * (fraction - 0.5)
        draw.line((x, top_y + height * 0.04, x + sway * 0.2, hem_y - height * 0.045),
                  fill=(103, 91, 54, 150), width=2)
    # A few fixed marks preserve the lightly handmade texture without visual noise.
    for x_fraction, y_fraction in ((.34, .77), (.57, .81), (.67, .9), (.43, .93)):
        x, y = width * x_fraction + sway * .2, height * y_fraction
        draw.line((x, y, x + width * .018, y - height * .006), fill=(112, 99, 58, 125), width=2)
    actor.alpha_composite(overlay)
    return actor


def ease(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def build(character_path: Path, background_path: Path, output_path: Path,
          poster_path: Path, seconds: float, fps: int, long_robe: bool = False,
          robe_master_path: Path | None = None) -> None:
    width, height = 1280, 720
    background = cover(Image.open(background_path).convert("RGB"), (width, height))
    character = white_background_cutout(character_path)
    if long_robe and robe_master_path:
        robe_master_path.parent.mkdir(parents=True, exist_ok=True)
        add_long_robe(character).save(robe_master_path)
    total = max(2, round(seconds * fps))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None

    for frame_number in range(total):
        t = frame_number / (total - 1)
        travel = ease(t)
        phase = 2 * math.pi * 4 * t
        source_actor = add_long_robe(character, phase) if long_robe else character
        # Approximately 35–39% of frame height: small enough to belong in the plate.
        target_height = round(260 + 22 * travel)
        scale = target_height / source_actor.height
        actor = source_actor.resize((round(source_actor.width * scale), target_height), RESAMPLE)
        bob = round(3.5 * math.sin(phase))
        angle = 1.2 * math.sin(phase + math.pi / 2)
        actor = actor.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

        x = round(-actor.width * 0.15 + travel * (width - actor.width * 0.75))
        ground_y = 655
        y = ground_y - actor.height + bob
        frame = background.copy()
        frame.paste(actor, (x, y), actor)
        if frame_number == total // 2:
            frame.save(poster_path, quality=95)
        process.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())

    process.stdin.close()
    code = process.wait()
    if code:
        raise RuntimeError(f"ffmpeg exited with status {code}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("character", type=Path)
    parser.add_argument("background", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--poster", type=Path, default=Path("poster.jpg"))
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--long-robe", action="store_true", help="cover legs with an animated robe")
    parser.add_argument("--robe-master", type=Path, help="optionally save the transparent robed puppet")
    args = parser.parse_args()
    build(args.character, args.background, args.output, args.poster, args.seconds, args.fps,
          long_robe=args.long_robe, robe_master_path=args.robe_master)


if __name__ == "__main__":
    main()
