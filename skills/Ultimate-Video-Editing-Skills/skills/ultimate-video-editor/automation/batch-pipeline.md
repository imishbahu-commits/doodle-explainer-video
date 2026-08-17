# Batch Video Processing Pipeline

## Overview
Process hundreds of videos with consistent quality using FFmpeg batch loops, Python automation, and profile-based presets.

## FFmpeg Batch Processing

### Process All Videos in a Folder
```bash
# Apply same grade to all MP4 files
for f in *.mp4; do
  ffmpeg -i "$f" -vf \
    "eq=brightness=0.02:contrast=1.15:saturation=1.2, \
     colorbalance=rs=0.05:gs=0.02:bs=-0.03, \
     unsharp=5:5:0.8" \
    -c:v libx264 -crf 20 -pix_fmt yuv420p \
    "graded_${f}"
done

# Resize all to 1080x1920 vertical
for f in *.mp4; do
  ffmpeg -i "$f" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1:black" \
    -c:v libx264 -crf 20 -pix_fmt yuv420p "vertical_${f}"
done

# Extract thumbnails from all videos
for f in *.mp4; do
  ffmpeg -i "$f" -vf "select=eq(n\,0)" -frames:v 1 "${f%.mp4}_thumb.jpg"
done
```

### PowerShell Batch (Windows)
```powershell
# Process all MP4 files in current directory
Get-ChildItem -Filter "*.mp4" | ForEach-Object {
    $output = "processed_$($_.Name)"
    ffmpeg -i $_.FullName -vf "eq=contrast=1.15:saturation=1.2" `
        -c:v libx264 -crf 20 -pix_fmt yuv420p $output
}
```

## Python Batch Pipeline

### Complete Pipeline Script
```python
#!/usr/bin/env python3
"""
Batch Video Processor
Apply consistent edits to multiple videos.
"""

import subprocess, os, json, sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

PROFILES = {
    "instagram_reel": {
        "scale": "1080:1920",
        "crf": 20,
        "vf": "eq=brightness=0.02:contrast=1.15:saturation=1.25,unsharp=5:5:0.8",
        "audio": "loudnorm=I=-14:TP=-1:LRA=9",
        "max_duration": 90,
    },
    "youtube_short": {
        "scale": "1080:1920",
        "crf": 18,
        "vf": "eq=contrast=1.1:saturation=1.15",
        "audio": "loudnorm=I=-16:TP=-1:LRA=11",
        "max_duration": 60,
    },
    "tiktok": {
        "scale": "1080:1920",
        "crf": 22,
        "vf": "eq=brightness=0.03:contrast=1.2:saturation=1.3,unsharp=5:5:1.0",
        "audio": "loudnorm=I=-14:TP=-1:LRA=7",
        "max_duration": 180,
    },
    "cinematic": {
        "scale": "1920:1080",
        "crf": 16,
        "vf": "eq=contrast=1.2:saturation=0.95,colorbalance=rs=0.04:bs=-0.03,curves=m='0/0.04 0.5/0.52 1/0.96'",
        "audio": "loudnorm=I=-24:TP=-2:LRA=13",
        "max_duration": None,
    },
    "compressed_share": {
        "scale": None,  # keep original
        "crf": 28,
        "vf": "",
        "audio": "loudnorm=I=-16:TP=-1",
        "max_duration": None,
        "maxrate": "2M",
        "bufsize": "4M",
    },
}

def process_video(input_path, output_dir, profile_name):
    profile = PROFILES[profile_name]
    input_path = Path(input_path)
    output_path = Path(output_dir) / f"{input_path.stem}_{profile_name}{input_path.suffix}"
    
    vf_parts = []
    if profile.get("scale"):
        vf_parts.append(f"scale={profile['scale']}:force_original_aspect_ratio=decrease,pad={profile['scale']}:-1:-1:black")
    if profile.get("vf"):
        vf_parts.append(profile["vf"])
    vf_parts.append("format=yuv420p")
    
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    
    if profile.get("max_duration"):
        cmd.extend(["-t", str(profile["max_duration"])])
    
    cmd.extend(["-vf", ",".join(vf_parts)])
    cmd.extend(["-af", profile["audio"]])
    cmd.extend(["-c:v", "libx264", "-crf", str(profile["crf"])])
    
    if profile.get("maxrate"):
        cmd.extend(["-maxrate", profile["maxrate"], "-bufsize", profile["bufsize"]])
    
    cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    cmd.extend(["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    cmd.append(str(output_path))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"input": str(input_path), "output": str(output_path), "success": result.returncode == 0}

def batch_process(input_dir, output_dir, profile_name, workers=2):
    os.makedirs(output_dir, exist_ok=True)
    videos = list(Path(input_dir).glob("*.mp4")) + list(Path(input_dir).glob("*.mov"))
    
    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_video, v, output_dir, profile_name) for v in videos]
        for future in futures:
            results.append(future.result())
    
    success = sum(1 for r in results if r["success"])
    print(f"Processed {success}/{len(results)} videos with profile '{profile_name}'")
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--profile", choices=PROFILES.keys(), default="instagram_reel")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    batch_process(args.input, args.output, args.profile, args.workers)
```

## Watermark Pipeline
```bash
# Add image watermark (bottom-right, 15% opacity)
ffmpeg -i video.mp4 -i logo.png -filter_complex \
  "[1]scale=120:-1,format=rgba,colorchannelmixer=aa=0.15[logo]; \
   [0][logo]overlay=W-w-20:H-h-20" \
  -c:v libx264 -crf 18 output.mp4

# Add text watermark
ffmpeg -i video.mp4 -vf \
  "drawtext=text='@username':fontsize=24:fontcolor=white@0.3:x=w-tw-20:y=h-th-20:font=Arial" \
  output.mp4

# Batch watermark all videos
for f in *.mp4; do
  ffmpeg -i "$f" -i logo.png -filter_complex \
    "[1]scale=100:-1,format=rgba,colorchannelmixer=aa=0.2[wm];[0][wm]overlay=W-w-15:H-h-15" \
    "wm_${f}"
done
```

## Thumbnail Generation Pipeline
```bash
# Best frame (most contrast/sharpness) from each video
ffmpeg -i video.mp4 -vf "select='gt(scene,0.4)',scale=1280:720" -frames:v 1 thumb.jpg

# Multiple thumbnails at intervals
ffmpeg -i video.mp4 -vf "fps=1/5,scale=640:360" thumb_%03d.jpg

# Thumbnail with text overlay
ffmpeg -i video.mp4 -vf \
  "select='eq(n,30)',scale=1280:720, \
   drawtext=text='MY VIDEO':fontsize=72:fontcolor=white:borderw=3:x=(w-tw)/2:y=(h-th)/2" \
  -frames:v 1 thumb_text.jpg
```

## Multi-Format Export Pipeline
```python
def export_all_formats(input_path):
    """Export one video to all social platforms simultaneously"""
    profiles_to_run = ["instagram_reel", "youtube_short", "tiktok", "compressed_share"]
    
    for profile in profiles_to_run:
        process_video(input_path, "exports/", profile)
```

## Performance Tips
- **Parallel workers**: Use 2 workers for HDD, 4 for SSD, match to CPU cores
- **GPU encoding**: Replace `libx264` with `h264_nvenc` (NVIDIA) or `h264_amf` (AMD) for 5-10x speed
- **Two-pass encoding**: Better quality at same bitrate, but 2x slower
- **Copy streams when possible**: `-c copy` is instant when you only need to trim/concat
