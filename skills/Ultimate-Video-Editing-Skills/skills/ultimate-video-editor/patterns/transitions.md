# Transition Recipes — Complete FFmpeg Reference

## Rule: Less is More
90% of transitions should be hard cuts. Fancy transitions are seasoning, not the meal.

## FFmpeg xfade Transitions

All use the format:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0][1]xfade=transition=TYPE:duration=DUR:offset=OFFSET[v]; \
   [0:a][1:a]acrossfade=d=DUR[a]" \
  -map "[v]" -map "[a]" output.mp4
```
Where OFFSET = duration_of_first_clip - DUR.

### Soft Transitions
```bash
# Cross dissolve (most versatile)
xfade=transition=fade:duration=0.5:offset=4

# Fade to black (chapter end)
xfade=transition=fadeblack:duration=1.0:offset=4

# Fade to white (flashback, heavenly)
xfade=transition=fadewhite:duration=0.5:offset=4

# Smooth left (reading direction)
xfade=transition=smoothleft:duration=0.5:offset=4

# Smooth up (vertical content)
xfade=transition=smoothup:duration=0.5:offset=4
```

### Geometric Transitions
```bash
# Circle crop (zoom, focus)
xfade=transition=circlecrop:duration=0.3:offset=4

# Circle open (iris reveal)
xfade=transition=circleopen:duration=0.5:offset=4

# Circle close (spotlight exit)
xfade=transition=circleclose:duration=0.5:offset=4

# Diamond (stylized)
xfade=transition=diamond:duration=0.4:offset=4

# Radial wipe
xfade=transition=radial:duration=0.6:offset=4
```

### Directional Wipes
```bash
# Wipe left (classic)
xfade=transition=wipeleft:duration=0.5:offset=4

# Wipe right
xfade=transition=wiperight:duration=0.5:offset=4

# Wipe up
xfade=transition=wipeup:duration=0.5:offset=4

# Wipe down
xfade=transition=wipedown:duration=0.5:offset=4

# Slide left (push)
xfade=transition=slideleft:duration=0.4:offset=4

# Slide right
xfade=transition=slideright:duration=0.4:offset=4
```

### Effect Transitions
```bash
# Pixelize (digital/glitch feel)
xfade=transition=pixelize:duration=0.3:offset=4

# Distance (blur transition)
xfade=transition=distance:duration=0.5:offset=4

# Dissolve (organic/film)
xfade=transition=dissolve:duration=0.6:offset=4

# Horizontal/vertical bars
xfade=transition=horzopen:duration=0.4:offset=4
xfade=transition=vertopen:duration=0.4:offset=4
xfade=transition=horzclose:duration=0.4:offset=4
xfade=transition=vertclose:duration=0.4:offset=4
```

## Custom Transition Effects (Without xfade)

### Zoom Transition (Social Media Style)
```bash
# Zoom out clip A → zoom in clip B
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0]trim=0:4,setpts=PTS-STARTPTS,zoompan=z='if(gt(on,90),min(zoom+0.02,2),1)':d=120:s=1920x1080[a]; \
   [1]trim=0:4,setpts=PTS-STARTPTS,zoompan=z='max(2-on*0.02,1)':d=120:s=1920x1080[b]; \
   [a][b]concat=n=2:v=1:a=0" output.mp4
```

### Whip Pan (Blur Transition)
```bash
# Motion blur at cut point
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0]trim=0:3.8,setpts=PTS-STARTPTS[a1]; \
   [0]trim=3.8:4,setpts=PTS-STARTPTS,boxblur=30:1[a2]; \
   [1]trim=0:0.2,setpts=PTS-STARTPTS,boxblur=30:1[b1]; \
   [1]trim=0.2,setpts=PTS-STARTPTS[b2]; \
   [a1][a2][b1][b2]concat=n=4:v=1:a=0" output.mp4
```

### Flash Transition
```bash
# Brief white flash at cut point
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0][1]xfade=transition=fadewhite:duration=0.15:offset=4" output.mp4
```

## When to Use Each Transition
| Transition | Duration | Energy | Best For |
|-----------|----------|--------|----------|
| Hard cut | 0ms | Neutral | Default — 90% of cuts |
| Dissolve | 300-800ms | Soft | Time passage, memories |
| Fade black | 500-1500ms | Low | Chapter end, finality |
| Fade white | 200-500ms | High | Flashback, energy burst |
| Wipe | 400-800ms | Medium | Geographic, playful |
| Circle | 300-600ms | Medium | Focus, spotlight |
| Slide | 300-500ms | Medium | Corporate, organized |
| Pixelize | 200-400ms | High | Tech, gaming, glitch |
| Zoom | 200-500ms | High | Social media, travel |
| Whip | 150-300ms | Very high | Comedy, action, location |
