#!/usr/bin/env python3
"""Fetch full YouTube video metadata for SEO analysis.

Tries the YouTube Data API v3 first (requires YOUTUBE_API_KEY env var),
then falls back to yt-dlp. Emits a unified JSON blob on stdout.

Usage:
    python fetch_video.py <video-url-or-id>
    python fetch_video.py <video-url-or-id> --transcript   # also dump transcript
    python fetch_video.py <video-url-or-id> --thumbnail out.jpg
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def extract_video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    parsed = urllib.parse.urlparse(url_or_id)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    if parsed.hostname and "youtube.com" in parsed.hostname:
        qs = urllib.parse.parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        m = re.match(r"/(shorts|embed|live)/([A-Za-z0-9_-]{11})", parsed.path)
        if m:
            return m.group(2)
    raise SystemExit(f"Could not extract video id from: {url_or_id}")


def fetch_via_api(video_id: str, api_key: str) -> dict[str, Any] | None:
    parts = "snippet,statistics,contentDetails,topicDetails,status,player,liveStreamingDetails"
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part={parts}&id={video_id}&key={api_key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:400]
        print(f"[fetch_video] API HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[fetch_video] API call failed: {e}", file=sys.stderr)
        return None
    items = data.get("items", [])
    if not items:
        return None
    item = items[0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    topics = item.get("topicDetails", {})
    return {
        "source": "youtube_data_api_v3",
        "video_id": video_id,
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "channel_id": snippet.get("channelId"),
        "channel_title": snippet.get("channelTitle"),
        "published_at": snippet.get("publishedAt"),
        "tags": snippet.get("tags", []),
        "category_id": snippet.get("categoryId"),
        "default_audio_language": snippet.get("defaultAudioLanguage"),
        "default_language": snippet.get("defaultLanguage"),
        "thumbnails": snippet.get("thumbnails", {}),
        "duration_iso": content.get("duration"),
        "dimension": content.get("dimension"),
        "definition": content.get("definition"),
        "caption": content.get("caption") == "true",
        "licensed_content": content.get("licensedContent"),
        "view_count": int(stats.get("viewCount", 0) or 0),
        "like_count": int(stats.get("likeCount", 0) or 0),
        "comment_count": int(stats.get("commentCount", 0) or 0),
        "topic_categories": topics.get("topicCategories", []),
        "made_for_kids": item.get("status", {}).get("madeForKids"),
        "privacy_status": item.get("status", {}).get("privacyStatus"),
        "upload_status": item.get("status", {}).get("uploadStatus"),
        "license": item.get("status", {}).get("license"),
    }


def fetch_via_ytdlp(video_id: str) -> dict[str, Any] | None:
    # Retry with two player clients: the default web client can get
    # bot-challenged; the android/ios clients often succeed instead.
    attempts = [
        ["yt-dlp", "-j", "--no-warnings", "--skip-download",
         f"https://www.youtube.com/watch?v={video_id}"],
        ["yt-dlp", "-j", "--no-warnings", "--skip-download",
         "--extractor-args", "youtube:player_client=android",
         f"https://www.youtube.com/watch?v={video_id}"],
        ["yt-dlp", "-j", "--no-warnings", "--skip-download",
         "--extractor-args", "youtube:player_client=ios",
         f"https://www.youtube.com/watch?v={video_id}"],
    ]
    last_err = ""
    for cmd in attempts:
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, check=True,
            )
            break
        except FileNotFoundError:
            print("[fetch_video] yt-dlp not installed", file=sys.stderr)
            return None
        except subprocess.CalledProcessError as e:
            last_err = e.stderr
            continue
    else:
        print(f"[fetch_video] yt-dlp failed after retries: {last_err}",
              file=sys.stderr)
        return None
    try:
        raw = json.loads(out.stdout)
    except json.JSONDecodeError as e:
        print(f"[fetch_video] yt-dlp returned invalid JSON: {e}",
              file=sys.stderr)
        return None
    return {
        "source": "yt_dlp",
        "video_id": video_id,
        "title": raw.get("title"),
        "description": raw.get("description"),
        "channel_id": raw.get("channel_id"),
        "channel_title": raw.get("channel") or raw.get("uploader"),
        "published_at": raw.get("upload_date"),
        "tags": raw.get("tags", []) or [],
        "categories": raw.get("categories", []),
        "thumbnails": raw.get("thumbnails", []),
        "duration_sec": raw.get("duration"),
        "view_count": raw.get("view_count"),
        "like_count": raw.get("like_count"),
        "comment_count": raw.get("comment_count"),
        "chapters": raw.get("chapters", []),
        "language": raw.get("language"),
        "automatic_captions_langs": list((raw.get("automatic_captions") or {}).keys()),
        "subtitles_langs": list((raw.get("subtitles") or {}).keys()),
        "availability": raw.get("availability"),
        "live_status": raw.get("live_status"),
    }


def fetch_transcript(video_id: str) -> str | None:
    """Use yt-dlp to dump the best available transcript as plain text."""
    with subprocess.Popen(
        [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang",
            "en.*",
            "--sub-format",
            "vtt",
            "-o",
            f"/tmp/yt_{video_id}.%(ext)s",
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as p:
        p.wait(timeout=90)
    for path in Path("/tmp").glob(f"yt_{video_id}*.vtt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = [
            ln for ln in text.splitlines()
            if ln and not ln.startswith(("WEBVTT", "NOTE", "Kind:", "Language:"))
            and "-->" not in ln
            and not ln.strip().isdigit()
        ]
        return "\n".join(lines)
    return None


def download_thumbnail(video_id: str, out_path: str) -> bool:
    for name in ("maxresdefault", "sddefault", "hqdefault"):
        url = f"https://i.ytimg.com/vi/{video_id}/{name}.jpg"
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                Path(out_path).write_bytes(r.read())
                return True
        except Exception:
            continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--transcript", action="store_true")
    parser.add_argument("--thumbnail", metavar="PATH")
    args = parser.parse_args()

    vid = extract_video_id(args.video)
    api_key = os.environ.get("YOUTUBE_API_KEY")
    data = fetch_via_api(vid, api_key) if api_key else None
    if data is None:
        data = fetch_via_ytdlp(vid)
    if data is None:
        print(json.dumps({"error": "Could not fetch metadata", "video_id": vid}))
        return 1

    if args.transcript:
        data["transcript"] = fetch_transcript(vid)

    if args.thumbnail:
        data["thumbnail_saved"] = download_thumbnail(vid, args.thumbnail)

    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
