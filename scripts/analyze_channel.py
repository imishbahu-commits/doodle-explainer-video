#!/usr/bin/env python3
"""Snapshot a public YouTube channel for format research using yt-dlp.

This records metadata only—never downloads or republishes another creator's
videos. Use the resulting corpus to identify high-level patterns and then make
original work.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url", help="channel URL, preferably ending in /videos")
    ap.add_argument("--output", default="channel-snapshot.json")
    args = ap.parse_args()
    proc = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--dump-single-json", args.url],
        text=True, capture_output=True,
    )
    if proc.returncode:
        raise SystemExit(proc.stderr[-3000:])
    source = json.loads(proc.stdout)
    videos = []
    for item in source.get("entries") or []:
        videos.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "url": item.get("url") or item.get("webpage_url"),
            "duration": item.get("duration"),
            "view_count": item.get("view_count"),
            "upload_date": item.get("upload_date"),
        })
    durations = [v["duration"] for v in videos if isinstance(v.get("duration"), (int, float))]
    views = [v["view_count"] for v in videos if isinstance(v.get("view_count"), (int, float))]
    snapshot = {
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "channel": source.get("channel") or source.get("uploader") or source.get("title"),
        "channel_url": args.url,
        "video_count": len(videos),
        "median_duration_seconds": statistics.median(durations) if durations else None,
        "median_views": statistics.median(views) if views else None,
        "videos": videos,
        "research_note": "Metadata research only. Create original scripts, art, voice, thumbnails, and branding.",
    }
    output = Path(args.output)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {output}: {len(videos)} videos")


if __name__ == "__main__":
    main()
