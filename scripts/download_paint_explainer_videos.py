#!/usr/bin/env python3
"""Download the frozen, authorized Paint Explainer reference set.

The ten source URLs live in references/paint-explainer-videos/catalog.json.
Media is limited to a progressive MP4 at 360p or lower and belongs in Git LFS.
Only run this script when redistribution is authorized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "references" / "paint-explainer-videos"
MEDIA_EXTENSIONS = {".mp4", ".webm", ".mkv"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_yt_dlp(explicit: str | None) -> str:
    candidates = [
        explicit,
        shutil.which("yt-dlp"),
        str(Path.home() / ".agent-reach-venv" / "bin" / "yt-dlp"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit(
        "yt-dlp was not found. Install Agent Reach first or pass --yt-dlp PATH."
    )


def load_catalog(path: Path) -> dict[str, Any]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    videos = catalog.get("videos")
    if not isinstance(videos, list) or len(videos) != 10:
        raise SystemExit(f"{path} must contain exactly 10 videos")
    ids = [video.get("id") for video in videos]
    if any(not isinstance(video_id, str) for video_id in ids) or len(set(ids)) != 10:
        raise SystemExit(f"{path} contains missing or duplicate video IDs")
    return catalog


def download(yt_dlp: str, output: Path, catalog: dict[str, Any]) -> None:
    urls_file = output / ".download-urls.txt"
    urls_file.write_text(
        "".join(f"{video['url']}\n" for video in catalog["videos"]),
        encoding="utf-8",
    )
    command = [
        yt_dlp,
        "--batch-file",
        str(urls_file),
        "--no-playlist",
        "--format",
        "best[height<=360][ext=mp4]/best[height<=360]/worst",
        "--paths",
        str(output),
        "--output",
        "%(autonumber)02d-%(upload_date)s-%(id)s.%(ext)s",
        "--autonumber-start",
        "1",
        "--restrict-filenames",
        "--trim-filenames",
        "120",
        "--write-info-json",
        "--no-write-playlist-metafiles",
        "--no-overwrites",
        "--continue",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "--retry-sleep",
        "http:exp=1:20",
        "--sleep-requests",
        "1",
        "--sleep-interval",
        "2",
        "--max-sleep-interval",
        "5",
        "--js-runtimes",
        "node",
        "--remote-components",
        "ejs:github",
    ]
    try:
        subprocess.run(command, check=True)
    finally:
        urls_file.unlink(missing_ok=True)


def media_for_id(output: Path, video_id: str) -> Path:
    matches = sorted(
        path
        for path in output.iterdir()
        if path.is_file()
        and path.suffix.lower() in MEDIA_EXTENSIONS
        and video_id in path.name
    )
    if len(matches) != 1:
        raise SystemExit(
            f"expected one downloaded media file for {video_id}, found {len(matches)}"
        )
    return matches[0]


def info_for_id(output: Path, video_id: str) -> dict[str, Any]:
    matches = sorted(output.glob(f"*{video_id}*.info.json"))
    if len(matches) != 1:
        raise SystemExit(f"expected one info JSON for {video_id}, found {len(matches)}")
    return json.loads(matches[0].read_text(encoding="utf-8"))


def build_index(output: Path, catalog: dict[str, Any]) -> None:
    indexed: list[dict[str, Any]] = []
    for source in catalog["videos"]:
        video_id = source["id"]
        media = media_for_id(output, video_id)
        info = info_for_id(output, video_id)
        indexed.append(
            {
                **source,
                "file": media.name,
                "size_bytes": media.stat().st_size,
                "sha256": sha256(media),
                "duration_seconds": info.get("duration"),
                "width": info.get("width"),
                "height": info.get("height"),
                "format_id": info.get("format_id"),
                "video_codec": info.get("vcodec"),
                "audio_codec": info.get("acodec"),
            }
        )

    index = {
        "generated_from": "catalog.json",
        "quality_limit": "360p",
        "video_count": len(indexed),
        "total_size_bytes": sum(video["size_bytes"] for video in indexed),
        "videos": indexed,
    }
    (output / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for info_json in output.glob("*.info.json"):
        info_json.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"destination directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--yt-dlp", help="path to the yt-dlp executable")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    catalog_path = output / "catalog.json"
    if not catalog_path.is_file():
        raise SystemExit(f"catalog not found: {catalog_path}")
    catalog = load_catalog(catalog_path)
    yt_dlp = find_yt_dlp(args.yt_dlp)
    print(f"Downloading {len(catalog['videos'])} authorized references with {yt_dlp}")
    download(yt_dlp, output, catalog)
    build_index(output, catalog)
    print(f"Wrote {output / 'index.json'}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
