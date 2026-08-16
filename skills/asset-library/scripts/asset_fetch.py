#!/usr/bin/env python3
"""asset_fetch.py — query and fetch individual assets from GitHub-mirrored
open asset libraries WITHOUT cloning the repos or committing the assets.

Uses the GitHub API (gh CLI) so only the single file you ask for travels.
Downloads land in the local cache (~/.asset-library/cache, gitignored);
only a tiny USED-ASSETS manifest is ever committed.

Usage:
    python3 asset_fetch.py search KEYWORD          # find PNGs across libraries
    python3 asset_fetch.py get SRC PATH [--out D]  # fetch one asset
    python3 asset_fetch.py license SRC             # show a library's license
    python3 asset_fetch.py used                    # show the used-assets manifest
"""

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBS = json.loads((HERE.parent / "libraries.json").read_text())
CACHE = Path.home() / ".asset-library" / "cache"
MANIFEST = Path.home() / ".asset-library" / "used-assets.json"


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
        for e in entries:
            path = e.get("path", "")
            name = path.split("/")[-1].lower()
            if kw in name and path.lower().endswith((".png", ".svg", ".jpg", ".webp")):
                hits.append((src, path))
                if len(hits) >= 40:
                    break
    if not hits:
        print(f"nothing found for '{keyword}'")
        return
    for src, path in hits:
        lic = LIBS[src]["license"]
        print(f"{src:14s} | {lic:22s} | {path}")


def get_asset(src, path, out_dir):
    if src not in LIBS:
        sys.exit(f"unknown library '{src}' — see libraries.json")
    repo = LIBS[src]["repo"]
    p = gh(["repos/{}/contents/{}".format(repo, path)])
    if p.returncode != 0:
        sys.exit(f"fetch failed: {p.stderr[:300]}")
    meta = json.loads(p.stdout)
    if "content" not in meta:
        sys.exit(f"'{path}' is not a file (is it a directory?)")
    data = base64.b64decode(meta["content"])
    dest = Path(out_dir or ".") / Path(path).name
    dest.write_bytes(data)
    print(f"fetched {len(data)} bytes -> {dest}  [{LIBS[src]['license']}]")
    record = {"src": src, "path": path, "license": LIBS[src]["license"],
              "file": str(dest)}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    used = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
    used.append(record)
    MANIFEST.write_text(json.dumps(used, indent=2))


def show_license(src):
    if src not in LIBS:
        sys.exit(f"unknown library '{src}'")
    print(f"{src}: {LIBS[src]['license']}")
    print(f"repo: github.com/{LIBS[src]['repo']}")
    print(f"note: {LIBS[src].get('note', '')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("keyword")
    p = sub.add_parser("get"); p.add_argument("src"); p.add_argument("path")
    p.add_argument("--out")
    p = sub.add_parser("license"); p.add_argument("src")
    sub.add_parser("used")
    args = ap.parse_args()
    if args.cmd == "search":
        search(args.keyword)
    elif args.cmd == "get":
        get_asset(args.src, args.path, args.out)
    elif args.cmd == "license":
        show_license(args.src)
    elif args.cmd == "used":
        used = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
        for u in used:
            print(f"{u['src']:14s} | {u['path']}  [{u['license']}]")


if __name__ == "__main__":
    main()
