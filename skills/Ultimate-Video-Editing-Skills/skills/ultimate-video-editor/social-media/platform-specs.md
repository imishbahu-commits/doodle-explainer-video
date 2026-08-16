# Platform Specs — Every Export Setting for Every Platform (2026)

## Quick Reference

| Platform | Resolution | Aspect | Duration | Max Size | FPS | Codec |
|----------|-----------|--------|----------|----------|-----|-------|
| Instagram Reels | 1080x1920 | 9:16 | 3-90s | 250MB | 30 | H.264 |
| Instagram Feed | 1080x1350 | 4:5 | 3-60s | 250MB | 30 | H.264 |
| Instagram Stories | 1080x1920 | 9:16 | 1-60s | 250MB | 30 | H.264 |
| TikTok | 1080x1920 | 9:16 | 1-10min | 287MB | 30 | H.264 |
| YouTube Shorts | 1080x1920 | 9:16 | ≤60s | 256MB | 30/60 | H.264 |
| YouTube | 3840x2160 | 16:9 | ≤12h | 256GB | 24-60 | H.264/VP9 |
| Twitter/X | 1920x1080 | 16:9/1:1 | ≤140s | 512MB | 30-60 | H.264 |
| LinkedIn | 1920x1080 | 16:9/1:1 | 3s-10min | 5GB | 30 | H.264 |
| Facebook Reels | 1080x1920 | 9:16 | 3-90s | 250MB | 30 | H.264 |
| Pinterest | 1000x1500 | 2:3 | 4-15min | 2GB | 25 | H.264 |
| Snapchat | 1080x1920 | 9:16 | ≤60s | 32MB | 30 | H.264 |
| WhatsApp Status | 1080x1920 | 9:16 | ≤30s | 16MB | 30 | H.264 |

## FFmpeg Export Presets

### Instagram Reels (Optimal)
```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -maxrate 12M -bufsize 24M \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -pix_fmt yuv420p -movflags +faststart \
  -t 90 reel.mp4
```

### TikTok (Optimal)
```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 20 -maxrate 10M -bufsize 20M \
  -c:a aac -b:a 192k -ar 44100 \
  -pix_fmt yuv420p -movflags +faststart tiktok.mp4
```

### YouTube Shorts (Optimal)
```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -maxrate 15M -bufsize 30M \
  -c:a aac -b:a 256k -ar 48000 \
  -pix_fmt yuv420p -movflags +faststart \
  -t 60 short.mp4
```

### YouTube Full (1080p High Quality)
```bash
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 16 -maxrate 20M -bufsize 40M \
  -c:a aac -b:a 320k -ar 48000 -ac 2 \
  -pix_fmt yuv420p -movflags +faststart youtube.mp4
```

### YouTube Full (4K)
```bash
ffmpeg -i input.mp4 -vf "scale=3840:2160:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset slow -crf 15 -maxrate 50M -bufsize 100M \
  -c:a aac -b:a 320k -ar 48000 \
  -pix_fmt yuv420p -movflags +faststart youtube_4k.mp4
```

### Twitter/X (Under 512MB, Fast Load)
```bash
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset medium -crf 23 -maxrate 5M -bufsize 10M \
  -c:a aac -b:a 128k -ar 44100 \
  -pix_fmt yuv420p -movflags +faststart \
  -t 140 twitter.mp4
```

### WhatsApp Status (Strict 16MB Limit)
```bash
ffmpeg -i input.mp4 -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 28 -maxrate 800k -bufsize 1600k \
  -c:a aac -b:a 64k -ar 44100 \
  -pix_fmt yuv420p -movflags +faststart \
  -t 30 -fs 15M whatsapp.mp4
```

### LinkedIn (Professional Quality)
```bash
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,format=yuv420p" \
  -c:v libx264 -preset slow -crf 20 -maxrate 8M -bufsize 16M \
  -c:a aac -b:a 192k -ar 44100 \
  -pix_fmt yuv420p -movflags +faststart linkedin.mp4
```

## Aspect Ratio Conversion

### Horizontal to Vertical (16:9 → 9:16)
```bash
# Center crop (loses sides)
ffmpeg -i horizontal.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos" vertical.mp4

# Blur-behind (keeps full frame with blurred background)
ffmpeg -i horizontal.mp4 -filter_complex \
  "[0]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg]; \
   [0]scale=1080:-2:force_original_aspect_ratio=decrease[fg]; \
   [bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
  -map "[v]" -map 0:a vertical.mp4
```

### Vertical to Horizontal (9:16 → 16:9)
```bash
# Blur-behind
ffmpeg -i vertical.mp4 -filter_complex \
  "[0]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=20[bg]; \
   [0]scale=-2:1080:force_original_aspect_ratio=decrease[fg]; \
   [bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
  -map "[v]" -map 0:a horizontal.mp4
```

### Square (1:1) for Instagram Feed
```bash
ffmpeg -i input.mp4 -vf "crop=min(iw\,ih):min(iw\,ih),scale=1080:1080:flags=lanczos" square.mp4
```

## Quality vs File Size Guide

| CRF | Quality | ~Size (1min 1080p) | Use Case |
|-----|---------|-------------------|----------|
| 15-17 | Excellent | 80-120 MB | Master/archive |
| 18-20 | Very good | 40-80 MB | YouTube, high quality |
| 21-23 | Good | 20-40 MB | General social media |
| 24-26 | Acceptable | 10-20 MB | Twitter, fast sharing |
| 27-30 | Compressed | 5-10 MB | WhatsApp, low bandwidth |
| 31+ | Low | <5 MB | Thumbnails, previews |

## Critical Export Settings
1. **Always use `-pix_fmt yuv420p`** — without it, many players can't decode
2. **Always use `-movflags +faststart`** — enables streaming before full download
3. **Audio: AAC at 44100 or 48000 Hz** — MP3 not accepted by some platforms
4. **H.264 (libx264)** — universal compatibility; H.265 not supported everywhere yet
5. **`-preset slow`** for final exports — better compression, same quality
