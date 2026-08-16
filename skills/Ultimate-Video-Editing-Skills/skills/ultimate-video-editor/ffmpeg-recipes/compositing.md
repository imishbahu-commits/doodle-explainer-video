# FFmpeg Compositing Recipes

## Picture-in-Picture

```bash
# PIP top-right corner (25% size)
ffmpeg -i main.mp4 -i pip.mp4 -filter_complex \
  "[1]scale=iw*0.25:ih*0.25[pip];[0][pip]overlay=W-w-20:20" output.mp4

# PIP bottom-left with border
ffmpeg -i main.mp4 -i pip.mp4 -filter_complex \
  "[1]scale=iw*0.25:ih*0.25,pad=iw+4:ih+4:2:2:white[pip]; \
   [0][pip]overlay=20:H-h-20" output.mp4

# PIP with rounded corners (approximate)
ffmpeg -i main.mp4 -i pip.mp4 -filter_complex \
  "[1]scale=320:180,format=rgba,geq='a=if(gt(min(min(X,W-X),min(Y,H-Y)),10),255,0)'[pip]; \
   [0][pip]overlay=W-w-20:20" output.mp4
```

## Split Screen

```bash
# Side-by-side (50/50)
ffmpeg -i left.mp4 -i right.mp4 -filter_complex \
  "[0]crop=iw/2:ih:0:0[l];[1]crop=iw/2:ih:iw/2:0[r];[l][r]hstack" output.mp4

# Top-bottom (50/50)
ffmpeg -i top.mp4 -i bottom.mp4 -filter_complex \
  "[0]crop=iw:ih/2:0:0[t];[1]crop=iw:ih/2:0:ih/2[b];[t][b]vstack" output.mp4

# 4-way grid
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 -filter_complex \
  "[0]scale=960:540[a];[1]scale=960:540[b];[2]scale=960:540[c];[3]scale=960:540[d]; \
   [a][b]hstack[top];[c][d]hstack[bot];[top][bot]vstack" output.mp4
```

## Green Screen (Chroma Key)

```bash
# Basic green screen removal
ffmpeg -i foreground.mp4 -i background.mp4 -filter_complex \
  "[0]chromakey=0x00FF00:0.1:0.2[fg];[1][fg]overlay" output.mp4

# Blue screen removal
ffmpeg -i foreground.mp4 -i background.mp4 -filter_complex \
  "[0]chromakey=0x0000FF:0.1:0.2[fg];[1][fg]overlay" output.mp4

# Fine-tuned chroma key (adjust similarity and blend)
ffmpeg -i fg.mp4 -i bg.mp4 -filter_complex \
  "[0]chromakey=0x00FF00:similarity=0.15:blend=0.05[fg];[1][fg]overlay" output.mp4
```

## Watermark / Logo Overlay

```bash
# Logo overlay (top-right, semi-transparent)
ffmpeg -i input.mp4 -i logo.png -filter_complex \
  "[1]scale=100:-1,format=rgba,colorchannelmixer=aa=0.7[logo]; \
   [0][logo]overlay=W-w-20:20" output.mp4

# Logo overlay (bottom-right)
ffmpeg -i input.mp4 -i logo.png -filter_complex \
  "[1]scale=80:-1,format=rgba,colorchannelmixer=aa=0.5[logo]; \
   [0][logo]overlay=W-w-15:H-h-15" output.mp4

# Centered watermark (large, very transparent)
ffmpeg -i input.mp4 -i watermark.png -filter_complex \
  "[1]scale=iw*0.5:-1,format=rgba,colorchannelmixer=aa=0.15[wm]; \
   [0][wm]overlay=(W-w)/2:(H-h)/2" output.mp4
```

## Text Overlays

```bash
# Title card text (centered, large)
ffmpeg -i input.mp4 -vf \
  "drawtext=text='Title Here':fontsize=72:fontcolor=white:borderw=3:bordercolor=black: \
   x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,4)'" output.mp4

# Lower third name
ffmpeg -i input.mp4 -vf \
  "drawtext=text='John Smith':fontsize=36:fontcolor=white:borderw=2:bordercolor=black: \
   x=50:y=h-100:enable='between(t,2,7)'" output.mp4

# Timestamp/timecode
ffmpeg -i input.mp4 -vf \
  "drawtext=text='%{pts\:hms}':fontsize=24:fontcolor=white:borderw=1:bordercolor=black:x=10:y=10" output.mp4
```

## Effects

```bash
# Vignette (darken edges)
-vf "vignette=angle=PI/4:mode=forward"

# Letterbox (cinematic 2.35:1 bars)
-vf "pad=iw:iw/2.35:(ow-iw)/2:(oh-ih)/2:black"

# 16:9 letterbox on 4:3
-vf "pad=ih*16/9:ih:(ow-iw)/2:0:black"

# Mirror/flip
-vf "hflip"  # horizontal
-vf "vflip"  # vertical

# Rotate 90 degrees
-vf "transpose=1"  # clockwise
-vf "transpose=2"  # counter-clockwise

# Ken Burns (slow zoom)
-vf "zoompan=z='min(zoom+0.001,1.3)':d=250:s=1920x1080"

# Film grain
-vf "noise=alls=15:allf=t+u"

# Blur (gaussian)
-vf "gblur=sigma=5"
```
