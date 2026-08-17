# Sandbox adaptation notes (this repo's environment)

The eight skills in this folder are copied verbatim from
[deeployCO/youtube-seo-skills](https://github.com/deeployCO/youtube-seo-skills)
(MIT License — see `LICENSE`). This file only explains how they run HERE.

## What works in this sandbox

| Piece | Works? | Notes |
|---|---|---|
| `youtube-seo-optimize` (titles, description, tags, chapters, 15s hook) | ✅ fully | Works from the local script + topic. No internet needed. |
| `youtube-seo-keywords` (intent, clusters, opportunity) | ✅ fully | Knowledge work, no internet needed. |
| `youtube-seo-thumbnail` + `scripts/analyze_thumbnail.py` | ✅ fully | Works on local thumbnail files. |
| `scripts/audio_loudness.py` | ✅ fully | Works on local mp4. |
| `youtube-seo-video` / `-audit` / `-channel` / `-competitor` | ⚠️ partly | `fetch_video.py` / `fetch_channel.py` need the YouTube Data API or yt-dlp — **blocked** in this sandbox. Instead: use the agent's web page reader on the YouTube watch/channel URL (title, description, transcript) and feed that text into the skill. |
| Keyword search volume / live SERPs | ⚠️ limited | No search API here. The skill's entity + intent logic still applies to whatever text the user or the page reader provides. |

## House rule

Use the knowledge inside these skills even when live YouTube data is unavailable —
titles, descriptions, tags, chapters and hook scripts are generated from the
script we wrote, which is the highest-value part of this suite.
