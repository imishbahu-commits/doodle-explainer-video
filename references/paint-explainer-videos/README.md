# Authorized Paint Explainer video references

This directory contains the **10 newest public videos** from
[The Paint Explainer](https://www.youtube.com/@ThePaintExplainer/videos), as
captured on **2026-08-21**. The repository owner confirmed that they are
authorized to redistribute these copies.

## Storage

The downloaded 360p reference copies are tracked with **Git LFS**, not as normal
Git blobs. After cloning, install Git LFS and fetch the media:

```bash
git lfs install
git lfs pull --include="references/paint-explainer-videos/*"
```

`catalog.json` is the frozen source list. `index.json` is generated after a
successful download and records each local filename, dimensions, duration,
size, and SHA-256 digest.

## Rebuild

Agent Reach provides `yt-dlp`. With Agent Reach or `yt-dlp` available on PATH:

```bash
python3 scripts/download_paint_explainer_videos.py
```

The downloader is intentionally fixed to the ten entries in `catalog.json`, so
a later channel upload cannot silently change this reference set. The default
format is a progressive MP4 no larger than 360p. Only download or redistribute
media when you have the necessary rights.
