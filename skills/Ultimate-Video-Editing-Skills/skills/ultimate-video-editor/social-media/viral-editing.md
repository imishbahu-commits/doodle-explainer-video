# Viral Editing Playbook — 2026 Reels/TikTok/Shorts

## The Hook Formula (First 3 Seconds)

### Rule: You have 1.5 seconds before the scroll. 3 seconds to lock them in.

### Hook Patterns That Work
| Pattern | Example | Why It Works |
|---------|---------|--------------|
| Payoff first | Show the result, then show how | Curiosity gap |
| Pattern interrupt | Start with unexpected visual/sound | Breaks autopilot scrolling |
| Bold text hook | "Nobody talks about this..." | Triggers FOMO |
| Direct address | "Wait, you need to see this" | Personal connection |
| Number hook | "3 things that changed my..." | Specific, scannable |
| Controversy | "This is why [common thing] is wrong" | Triggers engagement |

### FFmpeg Hook Techniques
```bash
# Zoom burst on first frame (attention grab)
ffmpeg -i video.mp4 -vf \
  "zoompan=z='if(lt(t,0.5),1.3-0.6*t,1.0)':d=1:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)', \
   format=yuv420p" output.mp4

# Flash frame at start
ffmpeg -f lavfi -i "color=c=white:s=1080x1920:r=30:d=0.1" -i video.mp4 \
  -filter_complex "[0][1]concat=n=2:v=1:a=0" output.mp4

# Bold hook text overlay (first 3 seconds)
ffmpeg -i video.mp4 -vf \
  "drawtext=text='YOU NEED TO SEE THIS':fontsize=64:fontcolor=white:borderw=4:bordercolor=black: \
   x=(w-tw)/2:y=(h-th)/2:enable='lt(t,3)', \
   format=yuv420p" output.mp4
```

## Pacing Rules

### Cut Frequency by Content Type
| Content | Cut Every | Total Cuts/Min |
|---------|-----------|---------------|
| Hook (0-3s) | 0.5-1.0s | Pattern breaks |
| Talking head | 3-5s | 12-20 |
| B-roll montage | 1-2s | 30-60 |
| Tutorial/demo | 4-8s | 8-15 |
| Storytelling | 3-6s | 10-20 |
| Music/dance | On beat | Beat-dependent |

### The Energy Curve
```
High ████                    ████
          ██              ████
            ██          ██
              ████████ ██
Low
    Hook  Setup  Build  Payoff  CTA
    0-3s  3-8s   8-20s  20-25s  25-30s
```

## Trending Formats (2026)

### 1. YAP Format (Raw Selfie Talk)
- Direct to camera, no script
- Minimal editing — just cuts for dead air
- Bold subtitle hook text
- **Editing**: Jump cuts every 2-3s, captions, minimal grade

### 2. Split Comparison
- Before/after or two POVs side by side
- **FFmpeg**: `[0][1]hstack` or `[0][1]vstack`

### 3. POV Storytelling
- "POV: you're a..." opening
- Immersive camera angle
- **Editing**: Color grade per mood, sound design heavy

### 4. Alarm Clock / Delayed Payoff
- Build tension for 40-50 seconds
- Payoff in final 5 seconds
- **Editing**: Slow build, velocity ramp at climax

### 5. Rate/React
- Flash rating overlay on celebrity/product
- Quick-cut highlight reel
- Bass-heavy audio sync

## Caption Strategy

### On-Screen Text Rules
- 85% of viewers watch without sound — captions are mandatory
- Maximum 2-3 words per flash for word-by-word style
- Hook text is 20-30% larger than body text
- Use contrasting colors: white text + black outline minimum

### Caption Placement
| Platform | Best Position | Alignment |
|----------|---------------|-----------|
| Reels | Center-screen | Middle |
| TikTok | Upper third | Top-center |
| Shorts | Center-screen | Middle |
| Stories | Lower third | Bottom |

## Engagement Triggers (Editing Choices That Boost Comments)

1. **Open loops**: Start a story but cut before the conclusion → "wait what happened??"
2. **Easter eggs**: Hide small details that reward re-watches → "omg I just noticed..."
3. **Controversial take**: State an opinion in text → triggers agree/disagree comments
4. **Question hooks**: End with a question → direct CTA for comments
5. **Intentional "mistake"**: Slight imperfection → people comment to "correct" you

## Retention Optimization

### Watch-Through Patterns
| Technique | Retention Boost | How |
|-----------|----------------|-----|
| Pattern interrupt every 3-5s | +15-20% | Quick cuts, zoom, SFX |
| On-screen countdown | +25% | "Wait for #1..." |
| Progress bar/indicator | +10-15% | Shows video length remaining |
| Audio ducking at key moments | +8-12% | Brief silence = attention |
| Speed ramp at peaks | +12-18% | Slow-mo dramatic moments |

## Content-Specific Edit Recipes

### Unboxing/Haul (Best for Products)
```
0-2s: Hero shot of everything (payoff first)
2-5s: "I got all this from [brand]"
5-15s: Individual item reveals (velocity edit: normal → slow at each reveal)
15-25s: Best item slow-mo with glow effect
25-30s: Everything together again, CTA
Audio: Upbeat lo-fi, whoosh on each reveal, impact on slow-mo
```

### Tutorial/How-To
```
0-3s: Show the finished result
3-8s: "Here's how to do it in 30 seconds"
8-25s: Step-by-step (numbered text overlays, zoom on details)
25-30s: Before/after comparison, CTA
Audio: Clean voice, subtle background music at -18dB
```

### Lifestyle/Vlog
```
0-2s: Most aesthetic shot from the day
2-5s: Quick montage of highlights (1s each, beat-synced)
5-25s: Story flow with J-cuts and L-cuts
25-30s: Sunset/wind-down moment, fade out
Audio: Trending audio or lo-fi, natural ambient layered in
```
