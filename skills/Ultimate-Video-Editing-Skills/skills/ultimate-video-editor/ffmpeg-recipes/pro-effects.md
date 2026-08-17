# Pro Effects — CapCut/Canva-Level Techniques in FFmpeg

*These recipes replicate effects that tools like CapCut, Canva, Kling charge for.*

## Glow / Bloom Effect (Dreamy Instagram Look)

The signature "dreamy" look from CapCut and Instagram filters. Split video, blur one copy heavily, blend back with screen mode.

```bash
# Soft glow (subtle, professional)
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[original][forglow]; \
   [forglow]gblur=sigma=25:steps=4[glowlayer]; \
   [original][glowlayer]blend=all_mode=screen:all_opacity=0.15, \
   format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4

# Strong bloom (music video, dreamy)
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[original][forglow]; \
   [forglow]gblur=sigma=40:steps=6[glowlayer]; \
   [original][glowlayer]blend=all_mode=screen:all_opacity=0.25, \
   format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4

# Warm halation (film-like light bleed from highlights)
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[original][forglow]; \
   [forglow]eq=brightness=0.1,gblur=sigma=35:steps=4[glowlayer]; \
   [original][glowlayer]blend=all_mode=softlight:all_opacity=0.3, \
   format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4
```

### Glow Intensity Guide
| sigma | opacity | Result |
|-------|---------|--------|
| 15-20 | 0.10-0.15 | Subtle skin smoothing glow |
| 25-35 | 0.15-0.20 | Instagram story/reel look |
| 40-50 | 0.20-0.30 | Music video / dreamy |
| 60+ | 0.25-0.35 | Heavy vintage / ethereal |

### Blend Mode Guide
| Mode | Effect |
|------|--------|
| screen | Brightens, best for glow/bloom |
| softlight | Subtle, natural glow |
| overlay | High contrast glow |
| lighten | Only affects dark areas |
| addition | Very bright, use low opacity |

## White Flash Transitions (CapCut "Flash" Effect)

```bash
# Create a white flash frame (0.13s = 4 frames at 30fps)
ffmpeg -f lavfi -i "color=c=white:s=1080x1920:r=30:d=0.133" \
  -c:v libx264 -crf 16 -pix_fmt yuv420p flash.mp4

# Insert flash between clips via concat
# concat_list.txt:
# file 'clip1.mp4'
# file 'flash.mp4'
# file 'clip2.mp4'
ffmpeg -f concat -safe 0 -i concat_list.txt -c:v libx264 -crf 18 output.mp4

# xfade fadewhite (smoother, between 2 clips)
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0][1]xfade=transition=fadewhite:duration=0.15:offset=OFFSET" output.mp4
```

### Flash Duration Guide
| Frames | Duration @30fps | Feel |
|--------|----------------|------|
| 2 | 0.067s | Subliminal flash |
| 3-4 | 0.1-0.13s | Quick punch (best for beat sync) |
| 5-6 | 0.17-0.2s | Noticeable flash |
| 8-10 | 0.27-0.33s | Dramatic flash (scene change) |

## Velocity Edit (CapCut Speed Ramp)

The key to viral velocity edits: dramatic speed changes synced to music beats, with zoom crops at slow-mo moments.

```bash
# Step 1: Segment the video at beat points
ffmpeg -i input.mp4 -ss 0 -to 2 -c copy seg1.mp4
ffmpeg -i input.mp4 -ss 2 -to 5 -c copy seg2.mp4
# ... etc

# Step 2: Apply speed + zoom to each segment
# Normal speed (no change)
ffmpeg -i seg1.mp4 -vf "format=yuv420p" -c:v libx264 normal.mp4

# Slow-mo 0.5x with zoom crop (dramatic reveal)
ffmpeg -i seg2.mp4 -vf \
  "setpts=2.0*PTS, \
   crop=iw*0.85:ih*0.85:iw*0.075:ih*0.075, \
   scale=1080:1920:flags=lanczos, \
   format=yuv420p" \
  -an -c:v libx264 slowmo.mp4

# Speed up 1.5x (energy burst between reveals)
ffmpeg -i seg3.mp4 -vf "setpts=0.67*PTS,format=yuv420p" \
  -an -c:v libx264 fast.mp4

# Step 3: Insert flash frames between segments and concat
```

### Speed Ramp Patterns for Viral Reels
| Pattern | Speeds | Best For |
|---------|--------|----------|
| Reveal | Normal → 0.5x slow → Normal | Product unboxing, food |
| Hype | Normal → 1.5x fast → 0.4x slow | Dance, action, sports |
| Dramatic | 0.6x slow → Flash → Normal | Transitions, storytelling |
| Pulse | 1.3x → 0.7x → 1.3x → 0.7x | Beat-synced montage |

## Dynamic Zoom (CapCut Keyframe Zoom)

```bash
# Slow zoom in over entire clip (Ken Burns)
-vf "zoompan=z='min(zoom+0.001,1.3)':d=1:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

# Slow zoom out
-vf "zoompan=z='if(lte(zoom,1.0),1.3,max(1.001,zoom-0.001))':d=1:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

# Zoom to corner (top-right focus)
-vf "zoompan=z='min(zoom+0.001,1.4)':d=1:s=1080x1920:x='iw-iw/zoom':y='0'"

# Crop-based zoom (simpler, works on video)
# 90% crop = ~1.11x zoom, centered
-vf "crop=iw*0.9:ih*0.9:iw*0.05:ih*0.05,scale=1080:1920:flags=lanczos"

# 85% crop = ~1.18x zoom
-vf "crop=iw*0.85:ih*0.85:iw*0.075:ih*0.075,scale=1080:1920:flags=lanczos"
```

## Chromatic Aberration (RGB Split)

```bash
# Subtle RGB shift (cinematic lens effect)
-vf "rgbashift=rh=3:bv=3:gh=-2"

# Strong RGB split (glitch/retro)
-vf "rgbashift=rh=10:bv=10:gh=-8"

# Combined with glow for retro look
ffmpeg -i input.mp4 -filter_complex \
  "[0]rgbashift=rh=5:bv=5:gh=-3[shifted]; \
   [shifted]split[a][b]; \
   [b]gblur=sigma=30:steps=4[glow]; \
   [a][glow]blend=all_mode=screen:all_opacity=0.2,format=yuv420p[v]" \
  -map "[v]" output.mp4
```

## Complete Pro Edit Pipeline

The order to apply effects for maximum quality:

```
1. Scale/upscale (lanczos)
2. Color grade (eq + colorbalance + curves)
3. Sharpen (unsharp)
4. Glow/bloom (split + gblur + blend=screen)
5. Vignette
6. Film grain (noise)
7. Speed manipulation (setpts) — do this on segments
8. Flash transitions (concat with flash frames)
9. Audio enhancement (loudnorm + eq + afftdn)
10. Export (yuv420p, movflags +faststart)
```
