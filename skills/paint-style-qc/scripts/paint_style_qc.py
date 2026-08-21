#!/usr/bin/env python3
"""Measured Paint Explainer QC for images, scene JSON, and metrics JSON."""

from __future__ import annotations

import argparse
import colorsys
import json
from pathlib import Path
from typing import Any

from PIL import Image


REPO = Path(__file__).resolve().parents[3]
RULES_PATH = REPO / "references" / "paint-explainer-analysis-4v" / "style_rules.json"
STYLE_RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))


def pixel_values(image: Image.Image) -> list[int]:
    """Pillow 10–13 compatible flattened pixel values without deprecation noise."""
    flattened = getattr(image, "get_flattened_data", None)
    return list(flattened() if flattened else image.getdata())


def result(kind: str, measurements: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "kind": kind,
        "ok": all(check["ok"] for check in checks),
        "measurements": measurements,
        "checks": checks,
    }


def check(name: str, ok: bool, measured: Any, target: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "measured": measured, "target": target}


def image_qc(path: Path, kind: str) -> dict[str, Any]:
    image = Image.open(path).convert("RGBA")
    w, h = image.size
    alpha = image.getchannel("A")
    alpha_values = pixel_values(alpha)
    # Composite transparent pixels over the production white rather than
    # interpreting transparent RGB zeroes as black ink/palette entries.
    composite = Image.new("RGBA", image.size, (255, 255, 255, 255))
    composite.alpha_composite(image)
    rgb = composite.convert("RGB")
    gray = rgb.convert("L")
    gray_values = pixel_values(gray)
    area = max(1, w * h)
    transparent = sum(value <= 8 for value in alpha_values) / area
    ink = sum(value <= 70 for value in gray_values) / area

    quantized = rgb.quantize(colors=32)
    colors = quantized.getcolors(maxcolors=32) or []
    significant = sum(count / area >= 0.005 for count, _ in colors)
    palette = quantized.getpalette() or []
    saturation_weighted = 0.0
    for count, index in colors:
        offset = index * 3
        if offset + 2 >= len(palette):
            continue
        r, g, b = (palette[offset + i] / 255.0 for i in range(3))
        saturation_weighted += colorsys.rgb_to_hsv(r, g, b)[1] * count / area

    corners = [rgb.getpixel((0, 0)), rgb.getpixel((w - 1, 0)), rgb.getpixel((0, h - 1)), rgb.getpixel((w - 1, h - 1))]
    white_corners = sum(min(color) >= 238 for color in corners)
    alpha_corners = sum(alpha.getpixel(point) <= 8 for point in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)))

    title_white = None
    if kind == "frame":
        title_fraction = STYLE_RULES["art"]["persistent_title_strip"]["height_fraction"]
        strip = rgb.crop((0, 0, w, max(1, round(h * title_fraction))))
        strip_gray = pixel_values(strip.convert("L"))
        title_white = sum(value >= 232 for value in strip_gray) / max(1, len(strip_gray))

    measurements = {
        "size": [w, h],
        "transparent_fraction": round(transparent, 5),
        "ink_fraction": round(ink, 5),
        "significant_color_count": significant,
        "mean_palette_saturation": round(saturation_weighted, 5),
        "white_corner_count": white_corners,
        "transparent_corner_count": alpha_corners,
        "title_strip_white_fraction": round(title_white, 5) if title_white is not None else None,
    }
    checks = [
        check("image has visible ink/content", ink >= 0.01, round(ink, 5), ">= 0.01"),
        check("palette remains explainable", significant <= 24, significant, "<= 24 significant quantized colors"),
    ]
    if kind == "subject":
        checks += [
            check("subject border is white or transparent", alpha_corners >= 3 or white_corners >= 3, {"alpha": alpha_corners, "white": white_corners}, ">= 3 matching corners"),
            check("transparent cutout or clean white master", transparent >= 0.02 or white_corners == 4, round(transparent, 5), ">= 0.02 transparent or four white corners"),
        ]
    if kind == "frame":
        checks.append(check("top chapter strip is white", bool(title_white is not None and title_white >= 0.75), title_white, ">= 0.75 white in top 10%"))
    return result(f"image:{kind}", measurements, checks)


def unique_values(track: list[dict[str, Any]]) -> int:
    return len({json.dumps(key.get("v"), sort_keys=True) for key in track})


def scene_qc(path: Path) -> dict[str, Any]:
    scene = json.loads(path.read_text(encoding="utf-8"))
    layers = scene.get("layers") or []
    moving_layers = 0
    moving_properties = 0
    hold_keys = 0
    interpolated_keys = 0
    suspicious_global = []
    for index, layer in enumerate(layers):
        layer_moves = False
        tracks = layer.get("tracks") or {}
        for property_name, track in tracks.items():
            if isinstance(track, list) and unique_values(track) > 1:
                layer_moves = True
                moving_properties += 1
            for key in track if isinstance(track, list) else []:
                if key.get("e") == "hold":
                    hold_keys += 1
                else:
                    interpolated_keys += 1
        if layer_moves:
            moving_layers += 1
        name = str(layer.get("name") or layer.get("id") or "").lower()
        if any(token in name for token in ("camera", "global-zoom", "global_pan", "global-pan")) and layer_moves:
            suspicious_global.append(index)

    camera = scene.get("camera")
    camera_locked = not camera
    if isinstance(camera, dict):
        tracks = camera.get("tracks") or {}
        camera_locked = not any(isinstance(track, list) and unique_values(track) > 1 for track in tracks.values())

    expected_fps = int(STYLE_RULES["source_measurement"]["source_fps"])
    max_moving = int(STYLE_RULES["motion"]["character"]["typical_independent_moving_elements"][1])
    fps = int(scene.get("fps", expected_fps))
    blur = int(scene.get("motion_blur", 1))
    measurements = {
        "fps": fps,
        "motion_blur_samples": blur,
        "layer_count": len(layers),
        "moving_layer_count": moving_layers,
        "moving_property_count": moving_properties,
        "hold_key_count": hold_keys,
        "interpolated_key_count": interpolated_keys,
        "camera_locked": camera_locked,
        "suspicious_global_layer_indices": suspicious_global,
    }
    checks = [
        check("source timing fps", fps == expected_fps, fps, str(expected_fps)),
        check("motion blur is off/crisp", blur <= 1, blur, "<= 1"),
        check("camera is locked", camera_locked, camera_locked, "true"),
        check("no animated global camera layer", not suspicious_global, suspicious_global, "none"),
        check("active layer budget", moving_layers <= max_moving, moving_layers, f"<= {max_moving} moving layers per shot"),
    ]
    return result("scene", measurements, checks)


def pick(data: dict[str, Any], *path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def metrics_qc(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    audio_rules = STYLE_RULES["audio"]
    wpm_min, wpm_max = audio_rules["target_newest_wpm_range"]
    lufs_min, lufs_max = audio_rules["target_newest_integrated_lufs_range"]
    lra_min, lra_max = audio_rules["lra_lu_range"]
    true_peak_max = audio_rules["target_newest_true_peak_dbtp_max"]
    median_shot = pick(data, "editing", "shot_duration_seconds", "median")
    frozen = pick(data, "motion", "shot_percentages", "frozen_hold")
    zoom_in = pick(data, "motion", "shot_counts", "whole_scene_zoom_in", default=0) or 0
    zoom_out = pick(data, "motion", "shot_counts", "whole_scene_zoom_out", default=0) or 0
    cut_lead = pick(data, "editing", "cut_minus_word_start_signed_seconds", "median")
    if cut_lead is None:
        # The corpus per-video format stores absolute stats plus detailed CSV;
        # custom production reports should prefer the signed field.
        cut_lead = pick(data, "editing", "median_cut_minus_word_start_seconds")
    wpm = pick(data, "audio", "recognized_wpm_full_runtime")
    lufs = pick(data, "audio", "integrated_lufs")
    peak = pick(data, "audio", "true_peak_dbfs")
    lra = pick(data, "audio", "lra_lu")

    measurements = {
        "median_shot_seconds": median_shot,
        "frozen_shots_pct": frozen,
        "whole_scene_zoom_count": int(zoom_in) + int(zoom_out),
        "median_cut_minus_word_start_seconds": cut_lead,
        "recognized_wpm": wpm,
        "integrated_lufs": lufs,
        "true_peak_dbfs": peak,
        "lra_lu": lra,
    }
    checks = [
        check("median shot cadence", median_shot is not None and 2.3 <= float(median_shot) <= 3.1, median_shot, "2.3–3.1 s"),
        check("frozen motion budget", frozen is not None and 35 <= float(frozen) <= 60, frozen, "35–60%"),
        check("no whole-scene zooms", int(zoom_in) + int(zoom_out) == 0, int(zoom_in) + int(zoom_out), "0"),
        check("current narration pace", wpm is not None and wpm_min <= float(wpm) <= wpm_max, wpm, f"{wpm_min}–{wpm_max} WPM"),
        check("current integrated loudness", lufs is not None and lufs_min <= float(lufs) <= lufs_max, lufs, f"{lufs_min} to {lufs_max} LUFS"),
        check("true peak headroom", peak is not None and float(peak) <= true_peak_max, peak, f"<= {true_peak_max} dBTP"),
        check("controlled loudness range", lra is not None and lra_min <= float(lra) <= lra_max, lra, f"{lra_min}–{lra_max} LU"),
    ]
    if cut_lead is not None:
        checks.append(check("noun anticipation", -0.10 <= float(cut_lead) <= 0.0, cut_lead, "−0.10 to 0.00 s"))
    return result("metrics", measurements, checks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    image = sub.add_parser("image")
    image.add_argument("path", type=Path)
    image.add_argument("--kind", choices=("subject", "background", "frame"), default="subject")
    image.add_argument("--json", type=Path)
    scene = sub.add_parser("scene")
    scene.add_argument("path", type=Path)
    scene.add_argument("--json", type=Path)
    metrics = sub.add_parser("metrics")
    metrics.add_argument("path", type=Path)
    metrics.add_argument("--json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "image":
        output = image_qc(args.path, args.kind)
    elif args.command == "scene":
        output = scene_qc(args.path)
    else:
        output = metrics_qc(args.path)
    text = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text, end="")
    if not output["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
