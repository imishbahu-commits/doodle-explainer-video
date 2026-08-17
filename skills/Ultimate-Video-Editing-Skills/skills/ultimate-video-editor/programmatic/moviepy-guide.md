# MoviePy — Python Video Editing Automation

## What is MoviePy?
Python library for video editing: cut, concat, resize, add text, overlays, effects — all in code. Perfect for automating repetitive edits.

## Install
```bash
pip install moviepy
```

## Core Operations

### Read, Trim, Write
```python
from moviepy import VideoFileClip

clip = VideoFileClip("input.mp4")
trimmed = clip.subclipped(2, 10)  # seconds 2-10
trimmed.write_videofile("output.mp4", codec="libx264", audio_codec="aac")
```

### Resize & Crop
```python
# Resize to 1080p vertical
clip = VideoFileClip("input.mp4")
resized = clip.resized(width=1080)

# Center crop to 9:16
w, h = resized.size
target_h = int(w * 16 / 9)
cropped = resized.cropped(y_center=h/2, height=target_h)
cropped.write_videofile("vertical.mp4")
```

### Concatenate Clips
```python
from moviepy import VideoFileClip, concatenate_videoclips

clips = [VideoFileClip(f"clip{i}.mp4") for i in range(1, 5)]
final = concatenate_videoclips(clips, method="compose")
final.write_videofile("combined.mp4")
```

### Speed Change
```python
clip = VideoFileClip("input.mp4")
slow = clip.with_speed_scaled(0.5)   # half speed
fast = clip.with_speed_scaled(2.0)   # double speed
```

## Text Overlays

### Basic Text
```python
from moviepy import TextClip, CompositeVideoClip, VideoFileClip

video = VideoFileClip("input.mp4")

text = TextClip(
    text="Hello World",
    font_size=64,
    color="white",
    stroke_color="black",
    stroke_width=3,
    font="Impact",
    size=video.size,
    method="caption",
)
text = text.with_duration(5).with_start(2)

final = CompositeVideoClip([video, text])
final.write_videofile("with_text.mp4")
```

### Animated Text (Fade In)
```python
text = TextClip(text="Fade In", font_size=48, color="white")
text = (text
    .with_duration(5)
    .with_start(1)
    .with_position("center")
    .with_effects([vfx.CrossFadeIn(1.0)])
)
```

## Image Overlays (Watermark/Logo)

```python
from moviepy import ImageClip, CompositeVideoClip

video = VideoFileClip("input.mp4")
logo = (ImageClip("logo.png")
    .with_duration(video.duration)
    .resized(width=100)
    .with_opacity(0.3)
    .with_position(("right", "top"))
)

final = CompositeVideoClip([video, logo])
final.write_videofile("watermarked.mp4")
```

## Audio Operations

```python
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

video = VideoFileClip("input.mp4")

# Replace audio
music = AudioFileClip("music.mp3").subclipped(0, video.duration)
video = video.with_audio(music.with_volume_scaled(0.3))

# Mix original audio + music
original_audio = video.audio
music = AudioFileClip("music.mp3").with_volume_scaled(0.2)
mixed = CompositeAudioClip([original_audio, music])
video = video.with_audio(mixed)

video.write_videofile("with_music.mp4")
```

## Batch Processing

```python
import os
from moviepy import VideoFileClip

def process_video(input_path, output_dir, grade_func):
    clip = VideoFileClip(input_path)
    processed = grade_func(clip)
    output_path = os.path.join(output_dir, f"edited_{os.path.basename(input_path)}")
    processed.write_videofile(output_path, codec="libx264", audio_codec="aac")
    clip.close()

def warm_grade(clip):
    """Apply warm cinematic look"""
    return clip.with_effects([
        vfx.ColorX(factor=1.2),       # boost saturation
        vfx.LumContrast(contrast=0.1), # slight contrast
    ])

# Process all videos in folder
input_dir = "raw_footage/"
output_dir = "edited/"
os.makedirs(output_dir, exist_ok=True)

for f in os.listdir(input_dir):
    if f.endswith((".mp4", ".mov")):
        process_video(os.path.join(input_dir, f), output_dir, warm_grade)
```

## Complete Edit Pipeline Script

```python
#!/usr/bin/env python3
"""
One-command video editor: trim, grade, add text, music, watermark, export.
Usage: python edit.py input.mp4 --trim 2 15 --text "My Video" --music bg.mp3
"""

from moviepy import *
import argparse

def full_edit(args):
    clip = VideoFileClip(args.input)
    
    # Trim
    if args.trim:
        clip = clip.subclipped(args.trim[0], args.trim[1])
    
    # Resize to vertical 1080p
    if args.vertical:
        clip = clip.resized(width=1080)
        w, h = clip.size
        if h < 1920:
            clip = clip.resized(height=1920)
    
    # Text overlay
    layers = [clip]
    if args.text:
        text = (TextClip(text=args.text, font_size=56, color="white",
                         stroke_color="black", stroke_width=3, font="Impact")
                .with_duration(min(3, clip.duration))
                .with_position("center"))
        layers.append(text)
    
    # Watermark
    if args.watermark:
        logo = (ImageClip(args.watermark)
                .resized(width=80)
                .with_opacity(0.25)
                .with_duration(clip.duration)
                .with_position(("right", "bottom")))
        layers.append(logo)
    
    final = CompositeVideoClip(layers)
    
    # Music
    if args.music:
        music = (AudioFileClip(args.music)
                 .subclipped(0, clip.duration)
                 .with_volume_scaled(0.2))
        if clip.audio:
            final = final.with_audio(CompositeAudioClip([clip.audio, music]))
        else:
            final = final.with_audio(music)
    
    final.write_videofile(args.output, codec="libx264", audio_codec="aac",
                          fps=30, preset="medium")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="edited_output.mp4")
    parser.add_argument("--trim", nargs=2, type=float)
    parser.add_argument("--text")
    parser.add_argument("--music")
    parser.add_argument("--watermark")
    parser.add_argument("--vertical", action="store_true")
    full_edit(parser.parse_args())
```

## When to Use MoviePy vs FFmpeg

| Task | MoviePy | FFmpeg |
|------|---------|--------|
| Complex compositions | Easier (Python) | Harder (filter_complex) |
| Text with custom fonts | Easier (PIL/ImageMagick) | Harder (drawtext) |
| Batch with logic | Easier (Python loops) | OK (shell loops) |
| Speed/performance | Slower | Much faster |
| Color grading | Limited | Extensive filters |
| Filter chains | Limited | Industry standard |
| Audio processing | Basic | Comprehensive |

**Rule of thumb**: Use MoviePy for composition-heavy edits (text, logos, multiple layers). Use FFmpeg for everything else (grading, audio, speed, export).
