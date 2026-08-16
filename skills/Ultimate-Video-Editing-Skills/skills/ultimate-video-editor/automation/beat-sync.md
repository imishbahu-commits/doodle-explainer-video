# Beat-Synced Editing — Auto-Cut Video to Music

## Overview
Automatically detect beats/onsets in audio and cut video segments to match the rhythm. This is the #1 technique behind viral reels and TikToks.

## Beat Detection with Python

### Using Librosa (Most Accurate for Offline)
```python
import librosa
import json

# Load audio
y, sr = librosa.load("audio.mp3", sr=22050)

# Detect beats
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

print(f"Tempo: {tempo:.1f} BPM")
print(f"Beats: {len(beat_times)}")

# Export timestamps
with open("beats.json", "w") as f:
    json.dump({"tempo": float(tempo), "beats": beat_times.tolist()}, f, indent=2)
```

### Using Aubio (Lightweight, Fast)
```python
import aubio

# Beat detection
win_s = 1024
hop_s = 512
samplerate = 44100

src = aubio.source("audio.mp3", samplerate, hop_s)
tempo = aubio.tempo("default", win_s, hop_s, samplerate)

beats = []
total_frames = 0
while True:
    samples, read = src()
    is_beat = tempo(samples)
    if is_beat:
        beats.append(total_frames / float(samplerate))
    total_frames += read
    if read < hop_s:
        break

print(f"Found {len(beats)} beats")
```

### Onset Detection (Percussive Hits, Not Just Beats)
```python
import librosa

y, sr = librosa.load("audio.mp3")

# Detect onsets (more granular than beats)
onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)

# Detect strong onsets only (filter by strength)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
strong_onsets = onset_times[onset_env[onset_frames] > onset_env.mean() * 1.5]
```

## FFmpeg Auto-Cut Pipeline

### Step 1: Extract Audio
```bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 22050 audio.wav
```

### Step 2: Generate Beat Timestamps (Python)
```python
import librosa, json

y, sr = librosa.load("audio.wav", sr=22050)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# Generate FFmpeg trim commands
for i in range(len(beat_times) - 1):
    start = beat_times[i]
    end = beat_times[i + 1]
    print(f'ffmpeg -i video.mp4 -ss {start:.3f} -to {end:.3f} -c copy seg_{i:03d}.mp4')

# Generate concat list
with open("concat.txt", "w") as f:
    for i in range(len(beat_times) - 1):
        f.write(f"file 'seg_{i:03d}.mp4'\n")
```

### Step 3: Concat All Segments
```bash
ffmpeg -f concat -safe 0 -i concat.txt -c copy beat_synced.mp4
```

## Complete Beat-Sync Script

```python
#!/usr/bin/env python3
"""
Beat-Sync Video Editor
Cuts footage to match beats in a music track.
Usage: python beat_sync.py --video footage.mp4 --music track.mp3 --output synced.mp4
"""

import subprocess, json, os, argparse
import librosa

def detect_beats(audio_path, sensitivity=1.0):
    y, sr = librosa.load(audio_path, sr=22050)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    if sensitivity != 1.0:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        threshold = onset_env.mean() * (2.0 - sensitivity)
        strong = onset_env[beat_frames] > threshold
        beat_times = beat_times[strong]
    
    return float(tempo), beat_times.tolist()

def get_duration(video_path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "json", video_path],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def beat_sync_edit(video_path, music_path, output_path, style="cut"):
    tempo, beats = detect_beats(music_path)
    video_duration = get_duration(video_path)
    
    segments = []
    video_pos = 0
    
    for i in range(len(beats) - 1):
        beat_dur = beats[i + 1] - beats[i]
        
        if video_pos + beat_dur > video_duration:
            video_pos = 0  # loop footage
        
        seg_file = f"_seg_{i:04d}.mp4"
        
        if style == "cut":
            cmd = f'ffmpeg -y -i "{video_path}" -ss {video_pos:.3f} -t {beat_dur:.3f} -c copy "{seg_file}"'
        elif style == "velocity":
            speed = 1.5 if i % 2 == 0 else 0.6
            cmd = (f'ffmpeg -y -i "{video_path}" -ss {video_pos:.3f} -t {beat_dur * speed:.3f} '
                   f'-vf "setpts={1/speed}*PTS,format=yuv420p" -an -c:v libx264 "{seg_file}"')
        
        subprocess.run(cmd, shell=True, capture_output=True)
        segments.append(seg_file)
        video_pos += beat_dur
    
    # Concat
    with open("_concat.txt", "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")
    
    subprocess.run(
        f'ffmpeg -y -f concat -safe 0 -i _concat.txt -i "{music_path}" '
        f'-map 0:v -map 1:a -c:v copy -c:a aac -shortest '
        f'-movflags +faststart "{output_path}"',
        shell=True
    )
    
    # Cleanup
    for seg in segments:
        os.remove(seg)
    os.remove("_concat.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--music", required=True)
    parser.add_argument("--output", default="beat_synced.mp4")
    parser.add_argument("--style", choices=["cut", "velocity"], default="cut")
    args = parser.parse_args()
    beat_sync_edit(args.video, args.music, args.output, args.style)
```

## Beat-Sync Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| Every beat | Cut on every beat | Fast montages, 120+ BPM |
| Every 2nd beat | Cut on downbeats | Medium-paced edits |
| Every 4th beat | Cut on bar boundaries | Cinematic, slow reveals |
| Onset-sync | Cut on percussive hits | Drum-heavy music |
| Mixed | Slow → every beat at drop | Build-and-release edits |

## Requirements
```
pip install librosa aubio numpy
```
