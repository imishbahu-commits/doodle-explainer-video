# FFmpeg Export Presets

## YouTube

```bash
# YouTube 1080p (H.264, web-ready)
ffmpeg -i input.mp4 -c:v libx264 -preset slow -crf 18 \
  -c:a aac -b:a 192k -movflags +faststart output.mp4

# YouTube 4K (H.265 for smaller file)
ffmpeg -i input.mp4 -c:v libx265 -preset slow -crf 20 \
  -c:a aac -b:a 256k -movflags +faststart -tag:v hvc1 output.mp4

# YouTube Shorts (vertical 1080x1920)
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -crf 20 -c:a aac -b:a 128k -movflags +faststart output.mp4
```

## Instagram / TikTok / Reels

```bash
# Vertical (9:16, 1080x1920)
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 128k \
  -t 60 -movflags +faststart output.mp4

# Square (1:1, 1080x1080)
ffmpeg -i input.mp4 -vf "crop=min(iw\,ih):min(iw\,ih),scale=1080:1080" \
  -c:v libx264 -crf 20 -c:a aac -b:a 128k -movflags +faststart output.mp4

# Landscape for Instagram feed (4:5, 1080x1350)
ffmpeg -i input.mp4 -vf "scale=1080:1350:force_original_aspect_ratio=decrease,pad=1080:1350:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -crf 20 -c:a aac -b:a 128k -movflags +faststart output.mp4
```

## Twitter/X

```bash
# Twitter optimized (720p, small file)
ffmpeg -i input.mp4 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k \
  -movflags +faststart output.mp4
```

## LinkedIn

```bash
# LinkedIn (1080p, professional)
ffmpeg -i input.mp4 -c:v libx264 -preset slow -crf 20 \
  -c:a aac -b:a 192k -movflags +faststart output.mp4
```

## High Quality / Archive

```bash
# Master quality (archival)
ffmpeg -i input.mp4 -c:v libx264 -preset veryslow -crf 15 \
  -c:a aac -b:a 320k -movflags +faststart output.mp4

# ProRes 422 (for editing in Premiere/DaVinci)
ffmpeg -i input.mp4 -c:v prores_ks -profile:v 2 -c:a pcm_s16le output.mov

# Lossless (huge file — for intermediate processing only)
ffmpeg -i input.mp4 -c:v libx264 -preset ultrafast -crf 0 -c:a copy output.mkv
```

## Utility Exports

```bash
# GIF (optimized with palette)
ffmpeg -i input.mp4 -vf "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif

# Thumbnail at specific time
ffmpeg -i input.mp4 -ss 00:00:05 -vframes 1 -q:v 2 thumbnail.jpg

# Extract audio only (MP3)
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3

# Extract audio only (WAV)
ffmpeg -i input.mp4 -vn -c:a pcm_s16le output.wav

# Strip audio from video
ffmpeg -i input.mp4 -an -c:v copy output_silent.mp4

# Trim without re-encoding
ffmpeg -i input.mp4 -ss 00:00:10 -to 00:00:30 -c copy trimmed.mp4
```

## Always Remember
- `-movflags +faststart` — critical for web playback (moves moov atom to front)
- `-preset slow` or `veryslow` — better compression, smaller file at same quality
- CRF scale: 0=lossless, 18=visually lossless, 23=default, 28=low quality
- Lower CRF = higher quality = larger file
