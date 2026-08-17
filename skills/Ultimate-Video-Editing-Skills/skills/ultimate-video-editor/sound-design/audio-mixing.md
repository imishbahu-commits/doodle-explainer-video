# Audio Mixing for Video — Platform-Specific Standards

## Loudness Standards

| Platform | Target LUFS | True Peak | LRA | Notes |
|----------|-------------|-----------|-----|-------|
| Instagram/Reels | -14 LUFS | -1 dBTP | 7-9 | Loud and punchy |
| TikTok | -14 LUFS | -1 dBTP | 7-9 | Same as Instagram |
| YouTube | -14 LUFS | -1 dBTP | 9-13 | YouTube normalizes anyway |
| YouTube Shorts | -14 LUFS | -1 dBTP | 7-9 | Treated like Reels |
| Spotify/Podcasts | -14 LUFS | -1 dBTP | 9-13 | Comfortable listening |
| Broadcast TV | -24 LUFS | -2 dBTP | 11-15 | EBU R128 standard |
| Cinema | -24 LUFS | -2 dBTP | 13-18 | Maximum dynamic range |

### FFmpeg Loudness Normalization
```bash
# Social media (Instagram, TikTok, YouTube)
-af "loudnorm=I=-14:TP=-1:LRA=9"

# Broadcast/cinema
-af "loudnorm=I=-24:TP=-2:LRA=13"

# Two-pass (most accurate)
# Pass 1: Analyze
ffmpeg -i input.mp4 -af "loudnorm=I=-14:TP=-1:print_format=json" -f null -
# Read the output values, then:
# Pass 2: Apply
ffmpeg -i input.mp4 -af \
  "loudnorm=I=-14:TP=-1:measured_I=MEASURED_I:measured_TP=MEASURED_TP:measured_LRA=MEASURED_LRA:measured_thresh=MEASURED_THRESH:linear=true" \
  output.mp4
```

## Voice Enhancement Chain

### Clear Dialogue (Podcast/Vlog)
```bash
-af "highpass=f=80, \
     afftdn=nf=-20, \
     equalizer=f=200:t=q:w=1:g=-2, \
     equalizer=f=3000:t=q:w=1:g=3, \
     equalizer=f=8000:t=q:w=2:g=2, \
     acompressor=threshold=-20dB:ratio=3:attack=5:release=50, \
     loudnorm=I=-16:TP=-1"
```

### Warm Voice (Storytelling/Narration)
```bash
-af "highpass=f=60, \
     afftdn=nf=-18, \
     equalizer=f=200:t=q:w=1:g=2, \
     equalizer=f=2500:t=q:w=1.5:g=2, \
     equalizer=f=6000:t=q:w=2:g=1, \
     acompressor=threshold=-18dB:ratio=2.5:attack=10:release=100, \
     loudnorm=I=-16:TP=-1"
```

### Punchy Voice (Reels/TikTok Energy)
```bash
-af "highpass=f=100, \
     afftdn=nf=-15, \
     equalizer=f=250:t=q:w=1:g=-3, \
     equalizer=f=3500:t=q:w=1:g=4, \
     equalizer=f=10000:t=q:w=2:g=3, \
     acompressor=threshold=-15dB:ratio=4:attack=3:release=30, \
     loudnorm=I=-14:TP=-1"
```

## Music + Voice Mixing

### Volume Balance Rules
| Element | Relative Level | Notes |
|---------|---------------|-------|
| Voice/Dialogue | 0 dB (reference) | Always dominant |
| Background music | -18 to -12 dB below voice | Audible but not competing |
| SFX | -6 to -3 dB below voice | Punchy but brief |
| Ambient | -24 to -18 dB below voice | Barely noticeable |

### Mix Music Under Voice
```bash
# Simple: lower music volume
ffmpeg -i voice.mp4 -i music.mp3 -filter_complex \
  "[1:a]volume=0.15[music]; \
   [0:a][music]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" output.mp4

# Advanced: sidechain compression (auto-duck)
ffmpeg -i voice.mp4 -i music.mp3 -filter_complex \
  "[0:a]asplit=2[voice][sc]; \
   [1:a][sc]sidechaincompress=threshold=0.03:ratio=6:attack=50:release=300:level_sc=0.5[ducked]; \
   [voice][ducked]amix=inputs=2:weights=1 0.25[a]" \
  -map 0:v -map "[a]" output.mp4
```

## Noise Reduction

### FFmpeg Noise Removal
```bash
# Light denoise (preserves quality)
-af "afftdn=nf=-20"

# Aggressive denoise (may affect voice quality)
-af "afftdn=nf=-12:nt=w"

# Highpass + denoise (removes rumble + hiss)
-af "highpass=f=80,afftdn=nf=-18"

# Full cleanup chain
-af "highpass=f=80,lowpass=f=12000,afftdn=nf=-18,volume=1.5"
```

## Fade Patterns

```bash
# Simple in/out
-af "afade=t=in:st=0:d=0.5,afade=t=out:st=DURATION:d=1"

# Crossfade between two audio tracks
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0:a][1:a]acrossfade=d=1:c1=tri:c2=tri[a]" \
  -map "[a]" output.mp3

# Music fade out under voice (manual timing)
ffmpeg -i video.mp4 -i music.mp3 -filter_complex \
  "[1:a]afade=t=in:st=0:d=2,afade=t=out:st=25:d=3,volume=0.2[m]; \
   [0:a][m]amix=inputs=2[a]" \
  -map 0:v -map "[a]" output.mp4
```

## EQ Frequency Reference

| Frequency | Name | Boost Effect | Cut Effect |
|-----------|------|-------------|------------|
| 60-80 Hz | Sub-bass | Rumble, weight | Remove mic rumble |
| 100-250 Hz | Bass | Warmth, body | Reduce muddiness |
| 250-500 Hz | Low-mid | Fullness | Reduce boominess |
| 500-2000 Hz | Mid | Presence, clarity | Reduce honk/nasal |
| 2000-4000 Hz | Upper-mid | Intelligibility | Reduce harshness |
| 4000-8000 Hz | Presence | Brightness, air | Reduce sibilance |
| 8000-16000 Hz | Air | Sparkle, detail | Reduce hiss |
