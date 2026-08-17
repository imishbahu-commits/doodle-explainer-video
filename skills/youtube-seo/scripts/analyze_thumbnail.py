#!/usr/bin/env python3
"""Analyze a YouTube thumbnail image.

Reports: dimensions, file size, dominant colors (histogram), contrast
score, face count (OpenCV Haar cascade if available), text-region
estimate, and mobile-size previews saved to /tmp.

Optionally, compute cosine similarity between the target thumbnail and
a folder of competitor SERP thumbnails using CLIP (ViT-B/32) if the
`clip` / `open_clip_torch` package is available.

Usage:
    python analyze_thumbnail.py thumbnail.jpg
    python analyze_thumbnail.py thumbnail.jpg --serp-dir ./serp_grid
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def analyze(path: Path) -> dict:
    try:
        import cv2  # type: ignore
        import numpy as np
    except ImportError:
        return {"error": "opencv-python + numpy required. pip install opencv-python numpy"}

    img = cv2.imread(str(path))
    if img is None:
        return {"error": f"Could not read image: {path}"}
    h, w = img.shape[:2]
    result: dict = {
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "width": w,
        "height": h,
        "aspect_ratio": round(w / h, 3) if h else None,
        "meets_1280x720": w >= 1280 and h >= 720,
        "under_2mb": path.stat().st_size < 2 * 1024 * 1024,
    }

    # Dominant colors via k-means
    pixels = img.reshape(-1, 3).astype("float32")
    try:
        k = 3
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten())
        order = counts.argsort()[::-1]
        result["dominant_colors_bgr"] = [
            {"bgr": centers[i].astype(int).tolist(), "share": round(float(counts[i]) / len(labels), 3)}
            for i in order
        ]
        result["dominant_colors_hex"] = [
            "#{:02X}{:02X}{:02X}".format(int(c["bgr"][2]), int(c["bgr"][1]), int(c["bgr"][0]))
            for c in result["dominant_colors_bgr"]
        ]
    except Exception as e:
        result["dominant_colors_error"] = str(e)

    # Contrast = stddev of luminance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result["contrast_stddev"] = round(float(gray.std()), 2)
    result["mean_luminance"] = round(float(gray.mean()), 2)

    # Face detection
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        result["face_count"] = len(faces)
        if len(faces):
            total_face_area = sum(fw * fh for (_, _, fw, fh) in faces)
            result["face_area_pct"] = round(total_face_area / (w * h) * 100, 2)
    except Exception as e:
        result["face_detection_error"] = str(e)

    # Mobile previews
    previews_dir = Path("/tmp/thumb_previews")
    previews_dir.mkdir(exist_ok=True)
    preview_paths = {}
    for size_name, sw, sh in (("120x68", 120, 68), ("246x138", 246, 138), ("480x270", 480, 270)):
        small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA)
        p = previews_dir / f"{path.stem}_{size_name}.jpg"
        cv2.imwrite(str(p), small)
        preview_paths[size_name] = str(p)
    result["preview_paths"] = preview_paths

    # Text region estimate via MSER (rough proxy)
    try:
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        result["text_region_estimate"] = len(regions)
    except Exception:
        pass

    return result


def clip_similarity(target: Path, serp_dir: Path) -> dict:
    try:
        import torch  # type: ignore
        from PIL import Image  # type: ignore
        try:
            import open_clip  # type: ignore
            model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
            model.eval()
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
        except ImportError:
            import clip  # type: ignore
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-B/32", device=device)
    except ImportError:
        return {"error": "CLIP not installed. pip install open_clip_torch pillow torch"}

    def embed(p: Path):
        img = preprocess(Image.open(p).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            feat = model.encode_image(img)
        feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat

    target_feat = embed(target)
    sims = []
    for comp in sorted(serp_dir.glob("*.jp*g")) + sorted(serp_dir.glob("*.png")):
        if comp.resolve() == target.resolve():
            continue
        f = embed(comp)
        sim = float((target_feat @ f.T).item())
        sims.append({"file": comp.name, "cosine": round(sim, 4)})
    sims.sort(key=lambda x: x["cosine"], reverse=True)
    if not sims:
        return {"error": "No SERP thumbnails found"}
    avg = sum(s["cosine"] for s in sims) / len(sims)
    return {
        "serp_count": len(sims),
        "avg_cosine": round(avg, 4),
        "max_cosine": sims[0]["cosine"],
        "most_similar": sims[:3],
        "verdict": (
            "strong pattern-break" if avg < 0.55
            else "typical" if avg < 0.70
            else "too similar to competitors"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("thumbnail")
    parser.add_argument("--serp-dir", help="Folder of SERP thumbnails for CLIP comparison")
    args = parser.parse_args()

    path = Path(args.thumbnail)
    if not path.exists():
        print(json.dumps({"error": f"File not found: {path}"}))
        return 1

    result = analyze(path)
    if args.serp_dir:
        result["serp_similarity"] = clip_similarity(path, Path(args.serp_dir))

    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
