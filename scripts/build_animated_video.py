#!/usr/bin/env python3
"""Render a layered 16:9 animated-history manifest with Pillow and ffmpeg.

The renderer intentionally uses simple staged motion—slide, pop, bob, shake,
wipe, camera pan and slow zoom—suited to original hand-drawn Paint-style art.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def font(size: int, path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in [path, *FONT_CANDIDATES]:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def color(value, default="#000000"):
    return ImageColor.getcolor(value or default, "RGBA")


def contain(image: Image.Image, width: int, height: int) -> Image.Image:
    image = image.convert("RGBA")
    ratio = min(width / image.width, height / image.height)
    return image.resize((max(1, round(image.width * ratio)), max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    image = image.convert("RGBA")
    ratio = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def alpha_scale(image: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 0.999:
        return image
    image = image.copy()
    image.putalpha(image.getchannel("A").point(lambda p: round(p * max(0, opacity))))
    return image


def active_progress(layer: dict, scene_time: float, scene_duration: float) -> tuple[bool, float, float]:
    start = float(layer.get("start", 0))
    end = float(layer.get("end", scene_duration))
    if scene_time < start or scene_time > end or end <= start:
        return False, 0, 0
    local = (scene_time - start) / (end - start)
    entrance = min(1.0, (scene_time - start) / max(0.001, float(layer.get("enter_duration", 0.35))))
    exit_at = end - float(layer.get("exit_duration", 0.25))
    exit_progress = 0 if scene_time <= exit_at else (scene_time - exit_at) / max(0.001, end - exit_at)
    return True, ease(local), min(ease(entrance), 1 - ease(exit_progress))


def draw_text_layer(layer: dict, canvas_size: tuple[int, int]) -> Image.Image:
    width = int(layer.get("width", canvas_size[0] * 0.8))
    size = int(layer.get("font_size", 64))
    padding = int(layer.get("padding", 22))
    face = font(size, layer.get("font"))
    chars = max(8, int(width / max(1, size * 0.58)))
    lines = textwrap.wrap(str(layer.get("text", "")), width=chars) or [""]
    probe = Image.new("RGBA", (width, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    boxes = [draw.textbbox((0, 0), line, font=face, stroke_width=int(layer.get("stroke_width", 2))) for line in lines]
    line_height = max((b[3] - b[1] for b in boxes), default=size) + int(size * 0.18)
    height = line_height * len(lines) + padding * 2
    image = Image.new("RGBA", (width, height), color(layer.get("box_color"), "#00000000"))
    draw = ImageDraw.Draw(image)
    y = padding
    align = layer.get("align", "center")
    for line, box in zip(lines, boxes):
        text_width = box[2] - box[0]
        x = padding if align == "left" else width - padding - text_width if align == "right" else (width - text_width) / 2
        draw.text(
            (x, y), line, font=face, fill=color(layer.get("color"), "#111111"),
            stroke_width=int(layer.get("stroke_width", 2)),
            stroke_fill=color(layer.get("stroke_color"), "#f2eadb"),
        )
        y += line_height
    return image


def draw_shape_layer(layer: dict) -> Image.Image:
    kind = layer.get("type")
    if kind == "arrow":
        x1, y1 = layer.get("from", [0, 0])
        x2, y2 = layer.get("to", [300, 0])
        pad = int(layer.get("stroke", 12) * 3)
        width, height = abs(x2 - x1) + pad * 2, abs(y2 - y1) + pad * 2
        image = Image.new("RGBA", (max(1, width), max(1, height)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        a = (pad + max(0, x1 - x2), pad + max(0, y1 - y2))
        b = (pad + max(0, x2 - x1), pad + max(0, y2 - y1))
        stroke = int(layer.get("stroke", 12))
        fill = color(layer.get("color"), "#d92727")
        draw.line([a, b], fill=fill, width=stroke)
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        head = int(layer.get("head", stroke * 2.5))
        points = [b]
        for delta in (2.55, -2.55):
            points.append((b[0] + head * math.cos(angle + delta), b[1] + head * math.sin(angle + delta)))
        draw.polygon(points, fill=fill)
        return image
    width, height = map(int, layer.get("size", [300, 180]))
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    fill = color(layer.get("color"), "#f7c948")
    outline = color(layer.get("outline"), "#111111")
    stroke = int(layer.get("stroke", 6))
    if kind == "ellipse":
        draw.ellipse((stroke, stroke, width - stroke, height - stroke), fill=fill, outline=outline, width=stroke)
    else:
        draw.rounded_rectangle((stroke, stroke, width - stroke, height - stroke), radius=int(layer.get("radius", 12)), fill=fill, outline=outline, width=stroke)
    return image


def layer_image(layer: dict, base: Path, cache: dict[str, Image.Image], canvas_size: tuple[int, int]) -> Image.Image:
    kind = layer.get("type", "image")
    if kind == "text":
        return draw_text_layer(layer, canvas_size)
    if kind in ("arrow", "rectangle", "ellipse"):
        return draw_shape_layer(layer)
    source = str(layer["image"])
    path = Path(source).expanduser()
    if not path.is_absolute():
        path = base / path
    key = str(path.resolve())
    if key not in cache:
        cache[key] = Image.open(path).convert("RGBA")
    original = cache[key]
    target_width = int(layer.get("width", original.width))
    target_height = int(layer.get("height", original.height * target_width / original.width))
    return contain(original, target_width, target_height)


def render_layer(canvas: Image.Image, layer: dict, source: Image.Image, scene_time: float, duration: float, frame_number: int) -> None:
    active, progress, visibility = active_progress(layer, scene_time, duration)
    if not active:
        return
    x = lerp(float(layer.get("x", canvas.width / 2)), float(layer.get("to_x", layer.get("x", canvas.width / 2))), progress)
    y = lerp(float(layer.get("y", canvas.height / 2)), float(layer.get("to_y", layer.get("y", canvas.height / 2))), progress)
    scale = lerp(float(layer.get("scale", 1)), float(layer.get("to_scale", layer.get("scale", 1))), progress)
    animation = layer.get("animation", "none")
    if animation == "bob":
        y += math.sin(scene_time * float(layer.get("speed", 3.5))) * float(layer.get("amount", 8))
    elif animation == "shake":
        random.seed(frame_number * 7919 + int(layer.get("seed", 0)))
        amount = float(layer.get("amount", 5))
        x += random.uniform(-amount, amount)
        y += random.uniform(-amount, amount)
    entrance = layer.get("enter", "fade")
    if visibility < 1:
        if entrance == "slide_left":
            x -= (1 - visibility) * float(layer.get("slide_distance", 160))
        elif entrance == "slide_right":
            x += (1 - visibility) * float(layer.get("slide_distance", 160))
        elif entrance == "pop":
            scale *= 0.55 + 0.45 * visibility
    rendered = source
    if scale != 1:
        rendered = source.resize((max(1, round(source.width * scale)), max(1, round(source.height * scale))), Image.Resampling.LANCZOS)
    opacity = float(layer.get("opacity", 1)) * visibility
    rendered = alpha_scale(rendered, opacity)
    if layer.get("reveal") == "wipe":
        shown = max(1, round(rendered.width * progress))
        rendered = rendered.crop((0, 0, shown, rendered.height))
    anchor = layer.get("anchor", "center")
    left = round(x if anchor == "topleft" else x - rendered.width / 2)
    top = round(y if anchor == "topleft" else y - rendered.height / 2)
    canvas.alpha_composite(rendered, (left, top))


def camera(frame: Image.Image, motion: str, progress: float) -> Image.Image:
    width, height = frame.size
    if motion in ("none", "hold", None):
        return frame
    zoom = 1.0
    cx, cy = width / 2, height / 2
    if motion == "slow_zoom_in":
        zoom = lerp(1.0, 1.08, progress)
    elif motion == "slow_zoom_out":
        zoom = lerp(1.08, 1.0, progress)
    elif motion == "pan_left":
        zoom, cx = 1.08, lerp(width * 0.54, width * 0.46, progress)
    elif motion == "pan_right":
        zoom, cx = 1.08, lerp(width * 0.46, width * 0.54, progress)
    crop_w, crop_h = width / zoom, height / zoom
    box = (round(cx - crop_w / 2), round(cy - crop_h / 2), round(cx + crop_w / 2), round(cy + crop_h / 2))
    return frame.crop(box).resize((width, height), Image.Resampling.LANCZOS)


def background(scene: dict, manifest: dict, base: Path, cache: dict[str, Image.Image], size: tuple[int, int]) -> Image.Image:
    source = scene.get("background_image")
    if source:
        path = Path(source).expanduser()
        if not path.is_absolute():
            path = base / path
        key = str(path.resolve())
        if key not in cache:
            cache[key] = Image.open(path).convert("RGBA")
        return cover(cache[key], *size)
    return Image.new("RGBA", size, color(scene.get("background") or manifest.get("background"), "#f2eadb"))


def run(command: list[str]) -> None:
    proc = subprocess.run(command)
    if proc.returncode:
        raise SystemExit(proc.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest")
    ap.add_argument("--draft", action="store_true", help="render at 1280x720 regardless of final size")
    ap.add_argument("--output")
    args = ap.parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    width = 1280 if args.draft else int(manifest.get("width", 1920))
    height = 720 if args.draft else int(manifest.get("height", 1080))
    fps = int(manifest.get("fps", 24))
    scenes = manifest.get("scenes", [])
    if not scenes:
        raise SystemExit("manifest has no scenes")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH; run bash scripts/setup.sh")
    output = Path(args.output or manifest.get("output", "animated.mp4")).expanduser()
    if not output.is_absolute():
        output = base / output
    output.parent.mkdir(parents=True, exist_ok=True)
    cache: dict[str, Image.Image] = {}
    total_frames = sum(max(1, round(float(scene["duration"]) * fps)) for scene in scenes)
    with tempfile.TemporaryDirectory(prefix="animated-history-") as tmp:
        video_only = Path(tmp) / "video.mp4"
        command = [
            ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(manifest.get("crf", 18)),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_only),
        ]
        proc = subprocess.Popen(command, stdin=subprocess.PIPE)
        assert proc.stdin is not None
        rendered_count = 0
        try:
            for scene_index, scene in enumerate(scenes, 1):
                duration = float(scene["duration"])
                count = max(1, round(duration * fps))
                bg = background(scene, manifest, base, cache, (width, height))
                sources = [(layer, layer_image(layer, base, cache, (width, height))) for layer in scene.get("layers", [])]
                if scene.get("text"):
                    title_layer = {
                        "type": "text", "text": scene["text"], "x": width / 2, "y": height / 2,
                        "width": width * 0.82, "font_size": scene.get("font_size", round(height * 0.075)),
                        "color": scene.get("text_color", "#111111"), "enter": "pop",
                    }
                    sources.append((title_layer, layer_image(title_layer, base, cache, (width, height))))
                print(f"scene {scene_index}/{len(scenes)}: {duration:.2f}s, {len(sources)} layers")
                for index in range(count):
                    t = index / fps
                    progress = index / max(1, count - 1)
                    frame = bg.copy()
                    for layer, source in sources:
                        render_layer(frame, layer, source, t, duration, rendered_count)
                    frame = camera(frame, scene.get("motion", "hold"), ease(progress)).convert("RGB")
                    proc.stdin.write(frame.tobytes())
                    rendered_count += 1
            proc.stdin.close()
            code = proc.wait()
            if code:
                raise SystemExit(code)
        except BrokenPipeError:
            proc.wait()
            raise SystemExit("ffmpeg stopped while receiving frames")
        audio = manifest.get("audio")
        if audio:
            audio_path = Path(audio).expanduser()
            if not audio_path.is_absolute():
                audio_path = base / audio_path
            run([
                ffmpeg, "-y", "-v", "error", "-i", str(video_only), "-i", str(audio_path),
                "-filter:a", "loudnorm=I=-16:TP=-1.5:LRA=11,apad", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output),
            ])
        else:
            shutil.copy2(video_only, output)
    print(f"wrote {output} ({total_frames} frames, {total_frames / fps:.1f}s)")


if __name__ == "__main__":
    main()
