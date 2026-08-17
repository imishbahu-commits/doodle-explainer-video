#!/usr/bin/env python3
"""Fetch YouTube channel metadata, recent uploads, and top videos.

Prefers YouTube Data API v3 (requires YOUTUBE_API_KEY). Falls back to
yt-dlp flat playlist extraction.

Usage:
    python fetch_channel.py <channel-url | @handle | channel-id>
    python fetch_channel.py <...> --recent 25 --top 25
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
from typing import Any


API_BASE = "https://www.googleapis.com/youtube/v3"


def resolve_channel_id(target: str, api_key: str | None) -> str | None:
    # Direct channel ID
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", target):
        return target
    # Extract from URL
    parsed = urllib.parse.urlparse(target)
    if parsed.hostname and "youtube.com" in parsed.hostname:
        m = re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", parsed.path)
        if m:
            return m.group(1)
        m = re.search(r"/(?:@|c/|user/)([^/]+)", parsed.path)
        if m and api_key:
            return resolve_handle(m.group(1), api_key)
    if target.startswith("@") and api_key:
        return resolve_handle(target.lstrip("@"), api_key)
    # yt-dlp fallback
    try:
        out = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", "--playlist-items", "0", target],
            capture_output=True, text=True, timeout=60, check=True,
        )
        data = json.loads(out.stdout)
        return data.get("channel_id") or data.get("uploader_id")
    except Exception:
        return None


def resolve_handle(handle: str, api_key: str) -> str | None:
    url = f"{API_BASE}/channels?part=id&forHandle=@{handle}&key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            items = json.loads(r.read()).get("items", [])
            if items:
                return items[0]["id"]
    except Exception:
        return None
    return None


def channel_details(channel_id: str, api_key: str) -> dict[str, Any] | None:
    parts = "snippet,statistics,topicDetails,brandingSettings,status,contentDetails"
    url = f"{API_BASE}/channels?part={parts}&id={channel_id}&key={api_key}"
    with urllib.request.urlopen(url, timeout=30) as r:
        items = json.loads(r.read()).get("items", [])
    if not items:
        return None
    c = items[0]
    snip = c.get("snippet", {})
    stats = c.get("statistics", {})
    branding = c.get("brandingSettings", {}).get("channel", {})
    uploads_pid = c.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    return {
        "channel_id": channel_id,
        "title": snip.get("title"),
        "handle": snip.get("customUrl"),
        "description": snip.get("description"),
        "country": snip.get("country"),
        "published_at": snip.get("publishedAt"),
        "thumbnails": snip.get("thumbnails", {}),
        "keywords": branding.get("keywords"),
        "unsubscribed_trailer": branding.get("unsubscribedTrailer"),
        "topic_categories": c.get("topicDetails", {}).get("topicCategories", []),
        "sub_count": int(stats.get("subscriberCount", 0) or 0),
        "view_count": int(stats.get("viewCount", 0) or 0),
        "video_count": int(stats.get("videoCount", 0) or 0),
        "hidden_subs": stats.get("hiddenSubscriberCount"),
        "uploads_playlist_id": uploads_pid,
        "made_for_kids": c.get("status", {}).get("madeForKids"),
    }


def playlist_items(playlist_id: str, api_key: str, max_items: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    token = ""
    while len(results) < max_items:
        url = (
            f"{API_BASE}/playlistItems?part=snippet,contentDetails"
            f"&playlistId={playlist_id}&maxResults=50&key={api_key}"
        )
        if token:
            url += f"&pageToken={token}"
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        for it in data.get("items", []):
            snip = it.get("snippet", {})
            results.append({
                "video_id": it.get("contentDetails", {}).get("videoId"),
                "title": snip.get("title"),
                "published_at": snip.get("publishedAt"),
                "description": snip.get("description"),
                "position": snip.get("position"),
            })
            if len(results) >= max_items:
                break
        token = data.get("nextPageToken", "")
        if not token:
            break
    return results


def video_stats_batch(video_ids: list[str], api_key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        url = (
            f"{API_BASE}/videos?part=snippet,statistics,contentDetails"
            f"&id={','.join(batch)}&key={api_key}"
        )
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        for it in data.get("items", []):
            snip = it.get("snippet", {})
            stats = it.get("statistics", {})
            content = it.get("contentDetails", {})
            out[it["id"]] = {
                "title": snip.get("title"),
                "tags": snip.get("tags", []),
                "view_count": int(stats.get("viewCount", 0) or 0),
                "like_count": int(stats.get("likeCount", 0) or 0),
                "comment_count": int(stats.get("commentCount", 0) or 0),
                "duration_iso": content.get("duration"),
                "thumbnails": snip.get("thumbnails", {}),
                "published_at": snip.get("publishedAt"),
            }
    return out


def top_videos(channel_id: str, api_key: str, max_items: int) -> list[str]:
    url = (
        f"{API_BASE}/search?part=snippet&channelId={channel_id}"
        f"&order=viewCount&type=video&maxResults={min(max_items,50)}&key={api_key}"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        return [
            it["id"]["videoId"]
            for it in json.loads(r.read()).get("items", [])
            if it.get("id", {}).get("videoId")
        ]


def fetch_via_ytdlp_fallback(target: str, recent: int) -> dict[str, Any] | None:
    """Key-less fallback via yt-dlp flat playlist extraction.

    Returns a minimal channel blob — no tags / topicDetails / per-video
    stats (yt-dlp --flat-playlist doesn't fetch them), but enough for a
    metadata-only audit.
    """
    try:
        out = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J",
             "--playlist-items", f"1-{max(recent, 1)}", target],
            capture_output=True, text=True, timeout=120, check=True,
        )
    except FileNotFoundError:
        print("[fetch_channel] yt-dlp not installed", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"[fetch_channel] yt-dlp fallback failed: {e.stderr[:400]}",
              file=sys.stderr)
        return None
    try:
        raw = json.loads(out.stdout)
    except json.JSONDecodeError as e:
        print(f"[fetch_channel] yt-dlp returned invalid JSON: {e}",
              file=sys.stderr)
        return None
    entries = raw.get("entries", []) or []
    return {
        "channel": {
            "channel_id": raw.get("channel_id") or raw.get("uploader_id"),
            "title": raw.get("channel") or raw.get("uploader") or raw.get("title"),
            "handle": raw.get("uploader_id"),
            "description": raw.get("description"),
            "source": "yt_dlp_flat",
        },
        "recent": [
            {
                "video_id": e.get("id"),
                "title": e.get("title"),
                "duration_sec": e.get("duration"),
                "view_count": e.get("view_count"),
            }
            for e in entries if e.get("id")
        ],
        "top": [],
        "degraded": "yt-dlp fallback: tags, topicDetails, per-video like/comment counts unavailable",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--recent", type=int, default=25)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        # Key-less path: yt-dlp flat playlist
        data = fetch_via_ytdlp_fallback(args.target, args.recent)
        if data is None:
            print(json.dumps({"error": "YOUTUBE_API_KEY not set and yt-dlp fallback failed"}))
            return 1
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0

    try:
        cid = resolve_channel_id(args.target, api_key)
        if not cid:
            raise RuntimeError("Could not resolve channel id")

        details = channel_details(cid, api_key)
        if not details:
            raise RuntimeError(f"Channel not found: {cid}")

        recent_items = playlist_items(details["uploads_playlist_id"], api_key, args.recent)
        recent_ids = [r["video_id"] for r in recent_items if r["video_id"]]
        recent_stats = video_stats_batch(recent_ids, api_key)
        for r in recent_items:
            r.update(recent_stats.get(r["video_id"], {}))

        top_ids = top_videos(cid, api_key, args.top)
        top_stats = video_stats_batch(top_ids, api_key)
        top_list = [{"video_id": vid, **top_stats[vid]} for vid in top_ids if vid in top_stats]
    except Exception as e:
        # API path broke (quota / network / 403) — degrade to yt-dlp.
        print(f"[fetch_channel] API path failed, falling back to yt-dlp: {e}",
              file=sys.stderr)
        data = fetch_via_ytdlp_fallback(args.target, args.recent)
        if data is None:
            print(json.dumps({"error": f"API and yt-dlp both failed: {e}"}))
            return 1
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0

    json.dump(
        {"channel": details, "recent": recent_items, "top": top_list},
        sys.stdout,
        indent=2,
        ensure_ascii=False,
    )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
