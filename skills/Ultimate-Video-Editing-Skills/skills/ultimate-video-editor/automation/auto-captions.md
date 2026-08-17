# Auto Captions — Whisper-Based Transcription + Animated Subtitles

## Overview
Generate word-level timestamps from audio using OpenAI Whisper, then burn them as animated captions — the exact technique CapCut, Descript, and Captions app charge for.

## Whisper Transcription

### Basic SRT Generation
```bash
# Install
pip install openai-whisper

# Generate SRT subtitle file
whisper video.mp4 --model medium --output_format srt --output_dir .

# Word-level timestamps (JSON with per-word timing)
whisper video.mp4 --model medium --word_timestamps True --output_format json

# Faster with faster-whisper (GPU accelerated)
pip install faster-whisper
```

### Faster-Whisper (5-10x Faster)
```python
from faster_whisper import WhisperModel

model = WhisperModel("medium", device="cuda", compute_type="float16")
# Use "cpu" and "int8" if no GPU

segments, info = model.transcribe("video.mp4", word_timestamps=True)

for segment in segments:
    for word in segment.words:
        print(f"[{word.start:.2f} → {word.end:.2f}] {word.word}")
```

### Generate Word-Level SRT
```python
from faster_whisper import WhisperModel

def generate_word_srt(audio_path, output_path="words.srt", max_words=3):
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    
    srt_entries = []
    group = []
    group_start = 0
    idx = 1
    
    for segment in segments:
        for word in segment.words:
            if not group:
                group_start = word.start
            group.append(word)
            
            if len(group) >= max_words:
                start = format_time(group_start)
                end = format_time(group[-1].end)
                text = " ".join(w.word.strip() for w in group)
                srt_entries.append(f"{idx}\n{start} --> {end}\n{text}\n")
                idx += 1
                group = []
    
    if group:
        start = format_time(group_start)
        end = format_time(group[-1].end)
        text = " ".join(w.word.strip() for w in group)
        srt_entries.append(f"{idx}\n{start} --> {end}\n{text}\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
```

## Animated Caption Styles

### Style 1: CapCut Pop-Up (Word-by-Word, Centered)
```bash
# Burn word-level SRT with bold impact font
ffmpeg -i video.mp4 -vf \
  "subtitles=words.srt:force_style='FontName=Impact,FontSize=42,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=10,MarginV=0'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4
```

### Style 2: Karaoke Highlight (Current Word Colored)
```python
def generate_karaoke_ass(audio_path, output_path="karaoke.ass"):
    """Generate ASS with karaoke-style word highlighting"""
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,48,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,10,10,10,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    events = []
    for segment in segments:
        words = list(segment.words)
        if not words:
            continue
        
        line_start = format_ass_time(words[0].start)
        line_end = format_ass_time(words[-1].end)
        
        # Build karaoke line: current word is yellow, others white
        for i, word in enumerate(words):
            dur = int((word.end - word.start) * 100)
            text_parts = []
            for j, w in enumerate(words):
                if j == i:
                    text_parts.append(f"{{\\c&H00FFFF&}}{w.word.strip()}")
                else:
                    text_parts.append(f"{{\\c&HFFFFFF&}}{w.word.strip()}")
            
            w_start = format_ass_time(word.start)
            w_end = format_ass_time(word.end)
            events.append(
                f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,"
                + " ".join(text_parts)
            )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
```

### Style 3: Background Box (Modern Clean)
```bash
ffmpeg -i video.mp4 -vf \
  "subtitles=words.srt:force_style='FontName=Helvetica Neue,FontSize=36,PrimaryColour=&H00FFFFFF,BackColour=&HCC000000,BorderStyle=4,Outline=0,Shadow=0,Alignment=2,MarginV=120'" \
  -c:v libx264 -crf 18 output.mp4
```

### Style 4: Outline Glow (Trending 2026)
```bash
ffmpeg -i video.mp4 -vf \
  "subtitles=words.srt:force_style='FontName=Montserrat,FontSize=40,PrimaryColour=&H00FFFFFF,OutlineColour=&H6600AAFF,Outline=4,Shadow=0,Bold=1,Alignment=10'" \
  output.mp4
```

## Caption Style Presets

| Style | Font | Size | Colors | Best For |
|-------|------|------|--------|----------|
| CapCut Pop | Impact | 42 | White + black outline | Reels, TikTok |
| Clean Modern | Helvetica | 36 | White + dark bg box | YouTube, LinkedIn |
| Karaoke | Impact | 48 | White + yellow highlight | Music, lyrics |
| Minimal | SF Pro | 28 | Light gray + thin outline | Aesthetic, vlog |
| Bold Statement | Bebas Neue | 56 | White + thick outline | Hook text, quotes |

## Pro Tips
1. **3 words max per caption group** — research shows 2-3 words per flash is optimal for comprehension at scroll speed
2. **Center-screen placement** — Alignment=10 (middle-center) performs 23% better than bottom for Reels
3. **Larger font for hooks** — first 3 seconds use 20% larger font, then normalize
4. **Contrast is king** — always use outline OR background, never naked text
5. **Match brand colors** — use consistent highlight color for word emphasis

## ElevenLabs Alternative (API-Based)
```bash
# Transcribe via ElevenLabs API (requires ELEVENLABS_API_KEY)
curl -X POST "https://api.elevenlabs.io/v1/audio-isolation" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -F "audio=@video.mp4"
```

## Requirements
```
pip install openai-whisper faster-whisper
# OR for GPU acceleration:
pip install faster-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
