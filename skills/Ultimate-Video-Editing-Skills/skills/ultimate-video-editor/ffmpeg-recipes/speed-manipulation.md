# FFmpeg Speed Manipulation Recipes

## Basic Speed Changes

```bash
# 2x speed (both video + audio)
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" output.mp4

# 0.5x slow motion (drop audio)
ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" -an output.mp4

# 0.5x slow motion (keep audio pitched down)
ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" -filter:a "atempo=0.5" output.mp4

# 4x speed (chain atempo for >2x)
ffmpeg -i input.mp4 -filter:v "setpts=0.25*PTS" -filter:a "atempo=2.0,atempo=2.0" output.mp4

# 0.25x ultra slow motion
ffmpeg -i input.mp4 -filter:v "setpts=4.0*PTS" -an output.mp4
```

## Smooth Slow Motion (Frame Interpolation)

```bash
# Optical flow slow-mo (0.5x, 60fps output)
ffmpeg -i input.mp4 -filter:v \
  "setpts=2.0*PTS,minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=60'" \
  -an output.mp4

# Smooth 0.25x slow-mo
ffmpeg -i input.mp4 -filter:v \
  "setpts=4.0*PTS,minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=60'" \
  -an output.mp4

# Simple frame blending slow-mo (faster but lower quality)
ffmpeg -i input.mp4 -filter:v \
  "setpts=2.0*PTS,minterpolate='mi_mode=blend:fps=60'" \
  -an output.mp4
```

## Timelapse & Hyperlapse

```bash
# 8x hyperlapse
ffmpeg -i input.mp4 -filter:v "setpts=0.125*PTS" -an output.mp4

# 16x hyperlapse
ffmpeg -i input.mp4 -filter:v "setpts=0.0625*PTS" -an output.mp4

# Timelapse from image sequence
ffmpeg -framerate 30 -i frame_%04d.jpg -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4

# Extract frames for timelapse (1 frame per second)
ffmpeg -i input.mp4 -vf "fps=1" frame_%04d.png
```

## Reverse

```bash
# Reverse entire video
ffmpeg -i input.mp4 -vf reverse -af areverse output.mp4

# Reverse video only (no audio)
ffmpeg -i input.mp4 -vf reverse -an output.mp4

# Boomerang (forward + reverse)
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0" output.mp4
```

## Speed Ramps

```bash
# Normal → slow (at 2s) → normal (at 4s) — conceptual
# Note: ffmpeg setpts doesn't easily do smooth ramps.
# For smooth speed ramps, use Remotion or programmatic approach.

# Step speed change (abrupt — use as starting point)
ffmpeg -i input.mp4 -filter:v "setpts='if(between(T,2,4),2*PTS,PTS)'" output.mp4

# For smooth ramps, segment the video and process each part:
# 1. Extract normal section
ffmpeg -i input.mp4 -ss 0 -to 2 -c copy part1.mp4
# 2. Extract and slow the action section
ffmpeg -i input.mp4 -ss 2 -to 4 -filter:v "setpts=2.0*PTS" -an part2_slow.mp4
# 3. Extract remaining normal section
ffmpeg -i input.mp4 -ss 4 -c copy part3.mp4
# 4. Add transition frames between speeds (frame interpolation)
# 5. Concat all parts
```

## Frame Rate Conversion

```bash
# Convert to 24fps (cinematic)
ffmpeg -i input.mp4 -filter:v "fps=24" -c:a copy output.mp4

# Convert to 30fps
ffmpeg -i input.mp4 -filter:v "fps=30" -c:a copy output.mp4

# Convert to 60fps (smooth interpolation)
ffmpeg -i input.mp4 -filter:v "minterpolate='fps=60'" output.mp4
```
