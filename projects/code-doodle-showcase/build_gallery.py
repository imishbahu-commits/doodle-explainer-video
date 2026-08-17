#!/usr/bin/env python3
"""build_gallery.py — scan the rendered doodles and emit gallery.json + thumbnails.

Reads every scene/chart spec, pairs it with its rendered PNG/SVG, records what
primitives built it, and writes the manifest the gallery page consumes. Also
writes web-sized thumbnails so the grid loads fast.

    python3 build_gallery.py

Note on paths: renders live in `images/`, not `out/`. Directories named `out`
(along with `build`, `dist`, `node_modules`, ...) are excluded from workspace
snapshots, so anything rendered there disappears between sessions.
"""

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE / "images"
THUMBS = HERE / "thumbs"
THUMB_W = 760

# Human-readable notes per item — what each one is meant to demonstrate.
NOTES = {
    "01-cast": "Three characters — poses, emotions, hair and outfits from the ink character system.",
    "02-mechanism": "A box-and-arrow chain with hachure fills: the mechanism grammar.",
    "03-cat": "A whole creature built only from circles, triangles and lines, plus a thought bubble.",
    "04-compare": "Two-column comparison driven by check and cross marks.",
    "05-giant": "One giant numeral on a flat colour field — the stat beat.",
    "06-background-day": "An empty-middle daytime background: sky, hills, trees, ground.",
    "07-night": "Night palette with stars, moon, paper speckle and a speech bubble.",
    "08-measure": "A scale comparison using a measure arrow.",
    "09-sightings": "Hand-inked bar chart via matplotlib xkcd mode.",
    "10-retellings": "Hand-inked line chart via matplotlib xkcd mode.",
}

RENDERER = {"scene": "rough.js + resvg", "chart": "matplotlib xkcd"}


def collect():
    items = []
    for kind, folder in (("scene", "scenes"), ("chart", "charts")):
        for spec_path in sorted((HERE / folder).glob("*.json")):
            name = spec_path.stem
            png, svg = IMAGES / f"{name}.png", IMAGES / f"{name}.svg"
            if not png.exists():
                continue
            spec = json.loads(spec_path.read_text())

            item = {
                "name": name,
                "kind": kind,
                "renderer": RENDERER[kind],
                "note": NOTES.get(name, ""),
                "spec": f"{folder}/{spec_path.name}",
                "png": f"images/{name}.png",
                "svg": f"images/{name}.svg" if svg.exists() else None,
                "thumb": f"thumbs/{name}.png",
                "pngKB": png.stat().st_size // 1024,
                "svgKB": svg.stat().st_size // 1024 if svg.exists() else None,
                "bg": spec.get("bg", "#FFFFFF"),
                "title": spec.get("title") or "",
                "source": json.dumps(spec, indent=2),
            }

            if kind == "scene":
                counts = Counter(e["type"] for e in spec.get("elements", []))
                item["seed"] = spec.get("seed")
                item["elementCount"] = sum(counts.values())
                item["elements"] = [{"type": t, "n": n} for t, n in counts.most_common()]
            else:
                item["chartKind"] = spec.get("kind", "bar")
                item["elementCount"] = len(spec.get("values", []))
                item["elements"] = [{"type": spec.get("kind", "bar"), "n": 1}]

            items.append(item)
    return items


def thumbs(items):
    try:
        from PIL import Image
    except ImportError:
        print("! Pillow missing — grid will fall back to full-size PNGs")
        for it in items:
            it["thumb"] = it["png"]
        return
    THUMBS.mkdir(parents=True, exist_ok=True)
    for it in items:
        src = HERE / it["png"]
        dst = THUMBS / f"{it['name']}.png"
        im = Image.open(src).convert("RGB")
        h = round(THUMB_W * im.height / im.width)
        im.resize((THUMB_W, h), Image.LANCZOS).save(dst, optimize=True)
        it["thumbKB"] = dst.stat().st_size // 1024


def main():
    items = collect()
    if not items:
        raise SystemExit(
            "no rendered images found in images/ — run render.sh first"
        )
    thumbs(items)
    manifest = {
        "count": len(items),
        "totalPngKB": sum(i["pngKB"] for i in items),
        "items": items,
    }
    (HERE / "gallery.json").write_text(json.dumps(manifest, indent=2))
    print(f"gallery.json — {len(items)} items, {manifest['totalPngKB']} KB of PNG")
    for it in items:
        print(f"  {it['name']:20} {it['kind']:6} {it['pngKB']:4} KB"
              f"  thumb {it.get('thumbKB', '-')} KB")


if __name__ == "__main__":
    main()
