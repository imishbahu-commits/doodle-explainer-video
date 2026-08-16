# FFmpeg Audio Processing Recipes

## Normalization

```bash
# Broadcast standard (-16 LUFS) — use for YouTube, podcasts
ffmpeg -i input.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" output.mp4

# Streaming standard (-14 LUFS) — Spotify, Apple Music
ffmpeg -i input.mp4 -af "loudnorm=I=-14:TP=-1:LRA=7" output.mp4

# Cinema standard (-24 LUFS)
ffmpeg -i input.mp4 -af "loudnorm=I=-24:TP=-2:LRA=15" output.mp4

# Two-pass normalization (more accurate)
ffmpeg -i input.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | grep -A20 "output"
# Then use the measured values in pass 2
```

## Noise Removal

```bash
# Light noise removal
ffmpeg -i input.mp4 -af "afftdn=nf=-20" output.mp4

# Medium noise removal + normalization
ffmpeg -i input.mp4 -af "afftdn=nf=-25,loudnorm=I=-16:TP=-1.5" output.mp4

# Aggressive noise removal
ffmpeg -i input.mp4 -af "afftdn=nf=-30:nt=w:om=o" output.mp4

# High-pass filter (remove low rumble)
ffmpeg -i input.mp4 -af "highpass=f=80" output.mp4

# Low-pass filter (remove high-freq hiss)
ffmpeg -i input.mp4 -af "lowpass=f=12000" output.mp4

# Combined cleanup chain
ffmpeg -i input.mp4 -af "highpass=f=80,afftdn=nf=-25,lowpass=f=14000,loudnorm=I=-16:TP=-1.5" output.mp4
```

## Music Ducking

```bash
# Auto-duck music under voice (sidechain compression)
ffmpeg -i voice.wav -i music.wav -filter_complex \
  "[1]sidechaincompress=threshold=0.02:ratio=8:attack=200:release=1000[duck]; \
   [0][duck]amix=inputs=2:duration=first" output.wav

# Manual music volume reduction (set music to -18dB under voice)
ffmpeg -i voice.wav -i music.wav -filter_complex \
  "[1]volume=0.15[music];[0][music]amix=inputs=2:duration=first" output.wav
```

## Fades

```bash
# Audio fade in (first 2 seconds)
-af "afade=t=in:st=0:d=2"

# Audio fade out (last 3 seconds)
-af "afade=t=out:st={total_duration-3}:d=3"

# Cut-point micro-fades (MANDATORY — prevents pops)
-af "afade=t=in:st=0:d=0.03,afade=t=out:st={duration-0.03}:d=0.03"

# Crossfade between two audio clips
ffmpeg -i a.wav -i b.wav -filter_complex "acrossfade=d=1:c1=tri:c2=tri" output.wav
```

## EQ & Enhancement

```bash
# Voice clarity boost (presence + air)
-af "equalizer=f=3000:t=q:w=1:g=3,equalizer=f=8000:t=q:w=2:g=2"

# De-essing (reduce sibilance)
-af "equalizer=f=6000:t=q:w=2:g=-6"

# Warmth boost (voice richness)
-af "equalizer=f=200:t=q:w=1:g=3,equalizer=f=3000:t=q:w=1:g=2"

# Bass boost (music/SFX)
-af "equalizer=f=80:t=q:w=1:g=6"

# Telephone/radio effect
-af "highpass=f=300,lowpass=f=3400,volume=0.8"
```

## Speed & Pitch

```bash
# Speed up audio 1.5x (pitch preserved)
-af "atempo=1.5"

# Speed up audio 3x (chain atempo — max 2.0 per instance)
-af "atempo=2.0,atempo=1.5"

# Slow down audio 0.5x (pitch preserved)
-af "atempo=0.5"
```

## Mixing

```bash
# Mix voice + music + SFX
ffmpeg -i voice.wav -i music.wav -i sfx.wav -filter_complex \
  "[0]volume=1.0[v]; \
   [1]volume=0.2[m]; \
   [2]volume=0.5[s]; \
   [v][m][s]amix=inputs=3:duration=first" output.wav

# Add room tone/ambience under edits
ffmpeg -i main.mp4 -i room_tone.wav -filter_complex \
  "[1]volume=0.15[amb];[0:a][amb]amix=inputs=2:duration=first" output.mp4

# Extract audio from video
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3
ffmpeg -i input.mp4 -vn -c:a pcm_s16le output.wav
```
