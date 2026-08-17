# FFmpeg Text Overlays & Kinetic Typography

## Basic Text Overlay
```bash
# Static centered text
ffmpeg -i video.mp4 -vf \
  "drawtext=text='Hello World':fontsize=48:fontcolor=white:borderw=3:bordercolor=black:x=(w-tw)/2:y=(h-th)/2" \
  output.mp4

# Text with custom font
ffmpeg -i video.mp4 -vf \
  "drawtext=fontfile='C\\:/Windows/Fonts/impact.ttf':text='IMPACT':fontsize=64:fontcolor=white:borderw=4:x=(w-tw)/2:y=h*0.2" \
  output.mp4
```

## Animated Text

### Fade In/Out
```bash
# Fade in text (0-1s), hold (1-4s), fade out (4-5s)
ffmpeg -i video.mp4 -vf \
  "drawtext=text='Fade Text':fontsize=48:fontcolor=white@%{eif\\:if(lt(t,1),t,if(lt(t,4),1,5-t)):d}:x=(w-tw)/2:y=(h-th)/2" \
  output.mp4

# Simpler alpha control
-vf "drawtext=text='Hello':fontsize=48:fontcolor=white:alpha='if(lt(t,1),t,if(lt(t,4),1,max(0,5-t)))':x=(w-tw)/2:y=(h-th)/2"
```

### Slide In from Left
```bash
-vf "drawtext=text='SLIDE IN':fontsize=48:fontcolor=white:borderw=3: \
     x='if(lt(t,0.5),-tw+tw*(t/0.5),(w-tw)/2)':y=(h-th)/2: \
     enable='between(t,0,5)'"
```

### Slide Up from Bottom
```bash
-vf "drawtext=text='SLIDE UP':fontsize=48:fontcolor=white:borderw=3: \
     x=(w-tw)/2:y='if(lt(t,0.5),h-th*(t/0.5),h*0.7)': \
     enable='between(t,0,5)'"
```

### Typewriter Effect
```bash
# Reveal characters one by one
-vf "drawtext=text='%{eif\\:if(lt(t,3),t*5,15)\\:d} chars':fontsize=48:fontcolor=white:x=(w-tw)/2:y=(h-th)/2"

# Better typewriter using text length
-vf "drawtext=textfile=text.txt:fontsize=48:fontcolor=white:x=(w-tw)/2:y=(h-th)/2: \
     text='%{eif\\:clip(t*10,0,15)\\:d}'"
```

### Bounce Effect
```bash
-vf "drawtext=text='BOUNCE':fontsize=56:fontcolor=yellow:borderw=3:bordercolor=black: \
     x=(w-tw)/2:y='(h-th)/2+30*sin(t*8)*exp(-t*2)'"
```

### Scale Pulse (Pop-In)
```bash
# Use zoompan on text layer for scale animation
ffmpeg -f lavfi -i "color=c=black@0:s=1080x1920:d=3,format=rgba" -vf \
  "drawtext=text='POP':fontsize='48+20*sin(t*6)*exp(-t*3)':fontcolor=white:borderw=3:x=(w-tw)/2:y=(h-th)/2" \
  text_layer.mov
```

## Multi-Line Text / Lower Thirds

### Lower Third (Name + Title)
```bash
ffmpeg -i video.mp4 -vf \
  "drawbox=x=0:y=ih*0.78:w=iw*0.5:h=ih*0.12:color=black@0.7:t=fill, \
   drawtext=text='John Doe':fontsize=36:fontcolor=white:x=30:y=h*0.79:font=Arial:Bold, \
   drawtext=text='CEO, Company':fontsize=24:fontcolor=white@0.8:x=30:y=h*0.79+40:font=Arial" \
  output.mp4
```

### Centered Title Card
```bash
ffmpeg -i video.mp4 -vf \
  "drawbox=x=iw*0.1:y=ih*0.4:w=iw*0.8:h=ih*0.2:color=black@0.6:t=fill, \
   drawtext=text='CHAPTER ONE':fontsize=28:fontcolor=white@0.7:x=(w-tw)/2:y=h*0.42:font=Helvetica, \
   drawtext=text='The Beginning':fontsize=52:fontcolor=white:x=(w-tw)/2:y=h*0.42+40:font=Georgia" \
  output.mp4
```

## Timer & Countdown

### Elapsed Timer
```bash
-vf "drawtext=text='%{pts\\:hms}':fontsize=24:fontcolor=white:x=w-tw-20:y=20:font=Courier"
```

### Countdown Timer
```bash
# 30-second countdown
-vf "drawtext=text='%{eif\\:30-t\\:d}':fontsize=72:fontcolor=red:borderw=3:x=(w-tw)/2:y=h*0.15:font=Impact:enable='lte(t,30)'"
```

## Text with Background Shapes

### Pill-Shaped Tag
```bash
ffmpeg -i video.mp4 -vf \
  "drawbox=x=(iw-400)/2:y=ih*0.85:w=400:h=60:color=red@0.9:t=fill, \
   drawtext=text='SUBSCRIBE':fontsize=32:fontcolor=white:x=(w-tw)/2:y=h*0.85+14:font=Impact" \
  output.mp4
```

### Full-Width Banner
```bash
-vf "drawbox=x=0:y=ih*0.9:w=iw:h=ih*0.1:color=black@0.8:t=fill, \
     drawtext=text='@username | Follow for more':fontsize=28:fontcolor=white:x=(w-tw)/2:y=h*0.92:font=Arial"
```

## Image Overlay (Logo/Watermark)

```bash
# Logo in corner (with transparency)
ffmpeg -i video.mp4 -i logo.png -filter_complex \
  "[1]scale=120:-1,format=rgba,colorchannelmixer=aa=0.3[logo]; \
   [0][logo]overlay=W-w-20:20" output.mp4

# Animated logo (slide in, hold, fade out)
ffmpeg -i video.mp4 -i logo.png -filter_complex \
  "[1]scale=150:-1,format=rgba[logo]; \
   [0][logo]overlay='if(lt(t,0.5),W,W-w-20)':'20':enable='between(t,0,5)'" output.mp4
```

## Pro Tips
1. **Escape special chars**: Use `\\:` for colons, `\\\\` for backslashes in drawtext
2. **Time-based enable**: `enable='between(t,2,5)'` shows text only between 2-5 seconds
3. **Font fallback**: Always specify a system font path on Windows; Linux/Mac can use font names
4. **Readability**: Minimum 3px border/outline for text on video. White text + black outline reads on any background
5. **Performance**: drawtext is CPU-intensive. For many text layers, render once to an intermediate file
6. **Safe zones**: Keep text within 90% of frame. Instagram/TikTok UI covers top 10% and bottom 15%
