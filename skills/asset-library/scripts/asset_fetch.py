#!/usr/bin/env python3
"""asset_fetch.py — query and fetch individual assets from GitHub-mirrored
open asset libraries WITHOUT cloning the repos or committing the assets.

Uses the GitHub API (gh CLI) so only the single file you ask for travels.
Downloads land in the local cache (~/.asset-library/cache, gitignored);
only a tiny USED-ASSETS manifest is ever committed.

Usage:
    python3 asset_fetch.py search KEYWORD           # find images across libraries
    python3 asset_fetch.py get SRC PATH [--out D]   # fetch one asset
    python3 asset_fetch.py get SRC PATH --rasterize # SVG -> PNG (needs cairosvg)
    python3 asset_fetch.py license SRC              # license + credit line
    python3 asset_fetch.py used                     # show the used-assets manifest
"""

import argparse
import base64
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBS = json.loads((HERE.parent / "libraries.json").read_text())
CACHE = Path.home() / ".asset-library" / "cache"
MANIFEST = Path.home() / ".asset-library" / "used-assets.json"

IMG_EXT = (".png", ".svg", ".jpg", ".jpeg", ".webp")


def gh(args, **kw):
    return subprocess.run(["gh", "api", *args], capture_output=True,
                          text=True, **kw)


def tree(src):
    """Cached recursive tree listing for a library (never re-fetched).
    Always returns a parsed dict."""
    tcache = Path.home() / ".asset-library" / "trees" / f"{src}.json"
    if tcache.exists():
        return json.loads(tcache.read_text())
    repo = LIBS[src]["repo"]
    p = gh([f"repos/{repo}/git/trees/HEAD?recursive=1"])
    if p.returncode != 0:
        sys.exit(f"tree fetch failed: {p.stderr[:300]}")
    data = json.loads(p.stdout)
    tcache.parent.mkdir(parents=True, exist_ok=True)
    tcache.write_text(json.dumps(data))
    return data


def search(keyword):
    kw = keyword.lower()
    hits = []
    for src in LIBS:
        try:
            entries = tree(src).get("tree", [])
        except Exception:
            continue
        lib_hits = 0
        for e in entries:
            path = e.get("path", "")
            name = path.split("/")[-1].lower()
            if kw in name and path.lower().endswith(IMG_EXT):
                hits.append((src, path))
                lib_hits += 1
                if lib_hits >= 15:      # cap per library so one pack
                    break               # doesn't flood the results
            if len(hits) >= 60:
                break
    if not hits:
        print(f"nothing found for '{keyword}'")
        return
    for src, path in hits:
        lic = LIBS[src]["license"]
        fmt = LIBS[src]["fmt"]
        hint = " (svg: add --rasterize)" if "svg" in fmt else ""
        print(f"{src:16s} | {lic:28s} | {fmt:8s} | {path}{hint}")


def get_asset(src, path, out_dir, rasterize):
    if src not in LIBS:
        sys.exit(f"unknown library '{src}' — see libraries.json")
    repo = LIBS[src]["repo"]
    quoted = urllib.parse.quote(path, safe="/() ")
    p = gh([f"repos/{repo}/contents/{quoted}"])
    if p.returncode != 0:
        sys.exit(f"fetch failed: {p.stderr[:300]}")
    meta = json.loads(p.stdout)
    if "content" not in meta:
        sys.exit(f"'{path}' is not a file (is it a directory?)")
    data = base64.b64decode(meta["content"])
    dest = Path(out_dir or ".") / Path(path).name
    dest.write_bytes(data)
    print(f"fetched {len(data)} bytes -> {dest}  [{LIBS[src]['license']}]")

    if rasterize:
        if not str(dest).lower().endswith(".svg"):
            sys.exit("--rasterize only applies to SVG files")
        png = dest.with_suffix(".png")
        rasterize_svg(dest, png)
        print(f"rasterized -> {png}")
        dest = png

    record = {"src": src, "path": path, "license": LIBS[src]["license"],
              "file": str(dest)}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    used = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
    used.append(record)
    MANIFEST.write_text(json.dumps(used, indent=2))


def rasterize_svg(svg_path, png_path):
    """SVG -> PNG. Prefers cairosvg (pip), falls back to the bundled Node
    resvg-js script (self-installs into ~/.asset-library, never the repo)."""
    try:
        import cairosvg  # noqa
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         background_color="white")
        return
    except Exception:
        pass
    script = HERE / "svg2png.mjs"
    p = subprocess.run(["node", str(script), str(svg_path), str(png_path)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("rasterize failed: " + (p.stderr or "")[-400:])
    print(p.stderr.strip())


def show_license(src):
    if src not in LIBS:
        sys.exit(f"unknown library '{src}'")
    print(f"{src}: {LIBS[src]['license']}")
    print(f"repo: github.com/{LIBS[src]['repo']}")
    print(f"format: {LIBS[src]['fmt']}")
    if LIBS[src].get("credit"):
        print(f"CREDIT REQUIRED: {LIBS[src]['credit']}")
    print(f"note: {LIBS[src].get('note', '')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("keyword")
    p = sub.add_parser("get"); p.add_argument("src"); p.add_argument("path")
    p.add_argument("--out"); p.add_argument("--rasterize", action="store_true")
    p = sub.add_parser("license"); p.add_argument("src")
    sub.add_parser("used")
    args = ap.parse_args()
    if args.cmd == "search":
        search(args.keyword)
    elif args.cmd == "get":
        get_asset(args.src, args.path, args.out, args.rasterize)
    elif args.cmd == "license":
        show_license(args.src)
    elif args.cmd == "used":
        used = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
        for u in used:
            print(f"{u['src']:16s} | {u['path']}  [{u['license']}]")


if __name__ == "__main__":
    main()
