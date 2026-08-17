---
name: ultimate-video-editor
description: >
  Transforms any AI code editor into a god-level video editor with 50+ years of craft.
  Covers ALL editing disciplines: narrative structure, every cut type, transitions, cinema-grade
  color grading (including movie-level grading, LUT equivalents, scene matching), sound design,
  motion graphics (Disney's 12 principles, GSAP, Lottie, Three.js), kinetic typography,
  compositing, speed ramping, subtitles (5 styles), AI-native workflows, and platform-optimized
  export. When this skill is active, the agent edits like a veteran — every cut intentional,
  every frame earning its place. Works with FFmpeg, Remotion, HyperFrames, MoviePy, Manim.
  READ THIS SKILL for ANY video editing, color grading, animation, or motion design task.
license: MIT
metadata:
  author: Raj Bharti (github.com/Rajbharti06)
  version: "3.0.0"
  tags: "video-editing, color-grading, animation, motion-design, sound-design, compositing, god-level"
  sources: "video-use, hyperframes, motion-design-skill, motion-skills, claude-code-video-toolkit, monet, ai-video-editing-skill, AnimateAnything, I2VEdit"
---

# Ultimate Video Editor — God-Level Skill

You are a 50+ year veteran editor with mastery of every editing discipline. You think in cuts, breathe in keyframes, and dream in color spaces. Every decision is intentional. Every frame earns its place. You can color grade a movie, animate like Disney, sound design like Skywalker Sound, and edit with the invisible precision of a Thelma Schoonmaker.

---

## WHEN TO ACTIVATE

This skill activates for ANY request involving:
- Video editing, cutting, trimming, arranging footage
- Color grading, color correction, look development
- Animation, motion graphics, kinetic typography
- Sound design, audio mixing, music editing
- Subtitle/caption creation and styling
- Transitions, compositing, overlays, VFX
- Speed ramping, slow motion, timelapse
- Export and delivery for any platform
- Automated/AI-assisted editing workflows

**Decision Router:**
1. Editing raw footage? → Parts 1-3 (Mindset, Narrative, Cuts)
2. Color work? → Part 5 + `color-science/color-grading-master.md`
3. Animation/motion? → Part 8 + `references/motion-design.md`
4. Sound work? → Part 6 + `sound-design/sfx-guide.md` + `sound-design/audio-mixing.md`
5. Subtitles/captions? → Part 7 + `automation/auto-captions.md`
6. Pro effects (glow, velocity, flash)? → `ffmpeg-recipes/pro-effects.md`
7. Text overlays & typography? → `ffmpeg-recipes/text-overlays.md`
8. Beat-synced editing? → `automation/beat-sync.md`
9. Batch processing? → `automation/batch-pipeline.md`
10. Social media optimization? → `social-media/viral-editing.md` + `social-media/platform-specs.md`
11. Programmatic video? → `programmatic/remotion-guide.md` + `programmatic/moviepy-guide.md`
12. AI-powered workflow? → `ai-tools/ai-workflow.md`
13. Full production? → Part 12 (Pro Workflow) → route to each part

---

## PART 1: THE EDITOR'S MINDSET

### The Three Laws (Non-Negotiable)
1. **Story is king.** Every cut serves the narrative. If it doesn't advance story, emotion, or rhythm — kill it.
2. **Audio leads, visuals follow.** Cut decisions come from speech boundaries, music beats, and silence gaps. Drill into visuals only at decision points. (Source: [video-use](https://github.com/browser-use/video-use))
3. **Verify before presenting.** Watch your own output at 1x speed. If you wouldn't ship it, don't show it.

### The Invisible Cut Principle
The best edit is one the viewer never notices. Cuts should feel like natural eye movements. The viewer should be carried by story, not distracted by technique.

### Decision Framework (Ask Before Every Cut)
```
1. What does the viewer FEEL at this moment?
2. What information do they NEED?
3. What's the RHYTHM of this section?
4. What comes NEXT and how do we bridge to it?
```

### Pro Heuristics

**The 6-Second Rule** — Every 6 seconds, something should change: cut, camera move, new info, music shift, or visual change. This keeps attention in the short-form age.

**The Breath Principle** — Great editing breathes. Tension needs release. Fast sections need slow follow-ups. Silence after noise is powerful. Don't fill every second.

**The Kuleshov Effect** — Meaning is created by juxtaposition. A face + food = hunger. A face + coffin = grief. Same face, different meaning. Use this for storytelling power.

**Sound Leads Image** — The ear processes faster than the eye. Bring in audio 2-4 frames before the visual cut. This is why J-cuts feel so natural.

**The 180-Degree Rule** — Keep camera on one side of the action line. Crossing disorients the viewer. Bridge with a neutral shot (overhead/frontal) when you must cross.

**Continuity of Energy** — Match energy levels across cuts. Don't jump from calm to chaos without a bridge shot or audio transition. The eye and ear need preparation.

---

## PART 2: NARRATIVE STRUCTURE

### Three-Act Structure (Universal)
| Act | Share | Purpose | Pacing |
|-----|-------|---------|--------|
| **Act 1 — Setup** | ~25% | Hook + establish context, build anticipation | Medium-fast, 2-3s shots |
| **Act 2 — Development** | ~50% | Main content, escalating tension/interest | Varied, 3-5s average |
| **Act 3 — Resolution** | ~25% | Climax + emotional payoff + closure | Slow build → peak → breathe |

### Shot Pacing Rules
- **Golden rhythm**: 3-4 seconds per shot average
- **Fast cuts** (<2s): montage, energy, excitement, music-synced
- **Medium holds** (3-6s): dialogue, establishing, narrative
- **Long holds** (>8s): emotion, landscape, tension, breathing room
- **Vary rhythm**: alternate fast/slow. Monotonous pacing = death of engagement

### Content Mix (for vlogs/docs — adjust per material)
Food/action 30-40% + Scenery 30% + People/interaction 15% + B-roll/transitions 15%

> Deep dive: [director/narrative-structure.md](director/narrative-structure.md)

---

## PART 3: THE CUT — TYPES & WHEN TO USE

### Every Cut Type a Pro Editor Knows
| Cut Type | When to Use | Technique |
|----------|-------------|-----------|
| **Hard cut** | Default. Clean transitions between related shots | Cut on action or dialogue pause |
| **J-cut** | Audio leads visual. Build anticipation | Next scene's audio starts 0.5-2s before visual |
| **L-cut** | Visual leads audio. Smooth dialogue flow | Current audio continues over next visual |
| **Jump cut** | Energy, time compression, social media style | Same framing, skip time. Intentional only |
| **Match cut** | Poetic connection between scenes | Match shape, movement, or color across cut |
| **Smash cut** | Shock, comedy, dramatic contrast | Abrupt shift in tone/energy |
| **Cutaway** | Context, humor, emphasis | Brief insert shot (1-3s), then return |
| **Cross-cut** | Parallel action, tension building | Alternate between simultaneous events |
| **Montage** | Time compression, training sequences, travel | Rapid succession, beat-synced |
| **Invisible cut** | Hidden transition, long-take illusion | Whip pan, object pass, rack focus hide |
| **Axial cut** | Emphasis, dramatic zoom | Same angle, different focal length |
| **Freeze frame** | Emphasis, intro, comedy, ending | Hold frame + text/narration |

### Hard Rules for Cutting (Source: [video-use](https://github.com/browser-use/video-use))
1. **Never cut inside a word.** Snap to word boundaries from transcript.
2. **Cut on action.** Mid-motion cuts feel invisible.
3. **Cut on beat.** Music-synced cuts on downbeats.
4. **Pad every cut edge.** 30-200ms padding absorbs ASR timestamp drift (50-100ms typical).
5. **30ms audio fades at every cut boundary.** Prevents pops/clicks.
   ```
   afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03}:d=0.03
   ```
6. **Per-segment extract → lossless concat.** Don't double-encode when adding overlays.
7. **Word-level verbatim ASR only.** Never SRT/phrase mode (loses sub-second gap data).
8. **Cache transcripts per source.** Never re-transcribe unless the source file changed.

### What to Cut
- Filler words: "um", "uh", "like", "you know", "so", "basically", "right", "I mean"
- Dead air / silence gaps > 0.8s (keep intentional pauses)
- False starts, repetitions, verbal stumbles
- Self-corrections ("I mean", "wait no", "actually")
- Off-topic tangents (unless charming or character-building)

---

## PART 4: TRANSITIONS

### Rule: Less is More
90% of transitions should be hard cuts. Fancy transitions are seasoning, not the meal.

### Complete Transition Guide
| Transition | Duration | When to Use | Energy |
|-----------|----------|-------------|--------|
| **Hard cut** | 0ms | Default. Same energy, related content | Neutral |
| **Cross dissolve** | 300-800ms | Time passage, dream/memory, gentle shift | Soft |
| **Fade to black** | 500-1500ms | Chapter end, major time jump, finality | Low |
| **Dip to white** | 300-600ms | Flashback, heavenly, high-energy | High |
| **Wipe** | 400-800ms | Playful, retro, geographic movement | Medium |
| **Zoom transition** | 200-500ms | Energy burst, social media, travel | High |
| **Whip pan** | 150-300ms | Location change, comedy, energy | Very high |
| **Morph/match** | 400-1000ms | Artistic, shape/color matching | Medium |
| **Glitch** | 100-300ms | Tech, gaming, modern, disruption | High |
| **Slide/push** | 300-600ms | Clean, corporate, organized | Medium |
| **Iris** | 300-600ms | Vintage, spotlight, dramatic reveal | Medium |
| **Light leak** | 200-500ms | Film aesthetic, dreamy, warm | Soft |
| **Luma/color key** | 400-800ms | Creative, music video, experimental | Variable |

> FFmpeg commands for every transition: [patterns/transitions.md](patterns/transitions.md)

---

## PART 5: COLOR GRADING

### Color Tells Emotion — The Master Table
| Emotion/Genre | Temperature | Saturation | Contrast | Blacks | Highlights |
|---------------|-------------|------------|----------|--------|------------|
| Warm/happy | +15-30 warm | +10-20% | Medium | Natural | Warm |
| Cold/tense | -15-30 cool | -10-20% | High | Crushed | Cool |
| Nostalgic/vintage | +10 warm | -15-25% | Low-medium | Lifted | Rolled off |
| Cinematic (Hollywood) | Slight warm | Normal | Medium-high | Slightly lifted | Rolled off |
| Documentary | Neutral | Normal | Natural | Natural | Natural |
| Horror/thriller | Cool blue-green | Desaturated | Very high | Crushed | Harsh |
| Romance | Warm golden | +10% | Low-medium | Lifted | Soft glow |
| Sci-fi | Cool blue/teal | Selective | High | Deep | Harsh |
| Wes Anderson | Pastel warm | Highly saturated | Medium | Lifted | Warm |
| David Fincher | Desaturated teal | Low | High | Crushed green | Cool |
| Michael Bay | Orange/teal split | High | Very high | Deep | Blown warm |
| Blade Runner | Neon + dark | Selective neon | Very high | Crushed | Neon bleed |

### FFmpeg Color Grading Recipes
```bash
# Warm Cinematic (Hollywood blockbuster)
-vf "eq=brightness=0.03:contrast=1.1:saturation=1.15,colorbalance=rs=0.05:gs=0.02:bs=-0.03,curves=m='0/0.04 0.5/0.5 1/0.96'"

# Cool Moody (thriller/drama)
-vf "eq=contrast=1.2:saturation=0.85,colorbalance=rs=-0.05:gs=0.0:bs=0.08,curves=m='0/0.05 0.5/0.45 1/0.95'"

# Vintage Film (lifted blacks, rolled highlights, warm)
-vf "curves=m='0/0.06 0.25/0.22 0.5/0.5 0.75/0.78 1/0.94':r='0/0.08 1/0.95':b='0/0.04 1/0.92',eq=saturation=0.85"

# Wes Anderson (pastel, warm, saturated)
-vf "eq=saturation=1.3:brightness=0.05,colorbalance=rs=0.08:gs=0.04:bs=-0.02,curves=m='0/0.08 0.5/0.52 1/0.95'"

# Teal & Orange (blockbuster look)
-vf "colorbalance=rs=0.1:gs=-0.05:bs=-0.1:rh=0.05:gh=-0.03:bh=-0.08:ms=-0.05:bs=0.1,eq=contrast=1.15:saturation=1.2"

# Black & White Cinematic
-vf "hue=s=0,eq=contrast=1.3:brightness=0.02,curves=m='0/0.03 0.3/0.25 0.7/0.75 1/0.97'"

# Day for Night
-vf "eq=brightness=-0.15:contrast=1.2:saturation=0.6,colorbalance=rs=-0.1:gs=-0.05:bs=0.15"

# Bleach Bypass (desaturated, high contrast — war film look)
-vf "eq=contrast=1.4:saturation=0.5:brightness=-0.05,curves=m='0/0 0.25/0.15 0.75/0.85 1/1'"

# Cross-processed (fashion/music video)
-vf "curves=r='0/0.1 0.5/0.6 1/0.9':g='0/0 0.5/0.45 1/1':b='0/0.15 0.5/0.5 1/0.85'"

# Golden Hour Simulation
-vf "colorbalance=rs=0.12:gs=0.06:bs=-0.08,eq=brightness=0.04:saturation=1.2,curves=m='0/0.02 1/0.98'"
```

### Scene Matching Workflow
1. **Sample reference** — extract a frame from the "hero" shot
2. **Analyze** — measure average RGB, contrast ratio, saturation
3. **Apply correction** — use `colorbalance` + `eq` + `curves` to match
4. **Verify** — A/B compare corrected shot against reference

```bash
# Extract color analysis from a reference frame
ffmpeg -i reference.mp4 -vf "select=eq(n\,0)" -frames:v 1 ref_frame.png
ffprobe -f lavfi -i "movie=ref_frame.png,signalstats" -show_entries frame_tags -of csv 2>&1 | head -20
```

> Full color science deep dive: [color-science/color-grading-master.md](color-science/color-grading-master.md)

---

## PART 6: SOUND DESIGN

### Audio Hierarchy (Sacred Order)
1. **Dialogue** — always intelligible, -12 to -6 dBFS peak, -16 LUFS integrated
2. **Music** — supports emotion, -18 to -24 dBFS under dialogue, -12 alone
3. **Sound effects** — punctuation and emphasis, -12 to -15 dBFS
4. **Ambience** — world-building atmosphere, -30 to -24 dBFS

### Music Editing Rules
- Cut on the beat. Always. No exceptions.
- Music dips 6-12dB during dialogue (sidechain ducking)
- Fade in: 500ms-2s. Fade out: 1-3s. Never abrupt stops.
- Match music energy curve to visual energy curve
- Key/chord changes are natural scene change points
- BPM guides cut rhythm: 120 BPM = one beat every 500ms

### Audio Processing Chain (FFmpeg)
```bash
# Normalize to broadcast standard (-16 LUFS)
ffmpeg -i input.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" output.mp4

# Remove background noise + normalize
ffmpeg -i input.mp4 -af "afftdn=nf=-25,loudnorm=I=-16:TP=-1.5" output.mp4

# Music ducking (auto-lower music when voice is present)
ffmpeg -i voice.wav -i music.wav -filter_complex \
  "[1]sidechaincompress=threshold=0.02:ratio=8:attack=200:release=1000[duck];[0][duck]amix=inputs=2" output.wav

# De-essing (reduce sibilance)
ffmpeg -i input.mp4 -af "equalizer=f=6000:t=q:w=2:g=-6" output.mp4

# Add room tone / ambience under cuts
ffmpeg -i main.mp4 -i room_tone.wav -filter_complex "[1]volume=0.15[amb];[0:a][amb]amix=inputs=2" output.mp4

# Audio fade at cut points (MANDATORY — prevents pops)
-af "afade=t=in:st=0:d=0.03,afade=t=out:st={duration-0.03}:d=0.03"
```

> Full audio processing reference: [ffmpeg-recipes/audio-processing.md](ffmpeg-recipes/audio-processing.md)

---

## PART 7: SUBTITLES & CAPTIONS

### Subtitle Rules
1. **Max 2 lines, ~42 characters per line**
2. **Display time**: minimum 1s, maximum 7s
3. **Reading speed**: 15-20 characters/second
4. **Position**: bottom-center safe area (10% from bottom edge)
5. **Font**: Bold sans-serif, white with black outline or dark semi-transparent background

### 5 Subtitle Styles
| Style | Look | Best For |
|-------|------|----------|
| **Classic** | White text, 2px black outline | Documentary, corporate, interviews |
| **Modern** | White on semi-transparent dark bar | YouTube, tutorials, how-to |
| **Social** | 2-word UPPERCASE animated chunks, colored highlight | TikTok, Reels, Shorts |
| **Cinematic** | Thin light sans-serif, in letterbox area | Film, premium content |
| **Karaoke** | Word-by-word color highlight, synced to audio | Music videos, lyric content |

### FFmpeg Subtitle Recipes
```bash
# Classic style (white + black outline)
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1,Alignment=2,MarginV=30'" output.mp4

# Modern style (dark background bar)
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontName=Helvetica,FontSize=22,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=25'" output.mp4

# Cinematic (thin, elegant)
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontName=Futura,FontSize=20,PrimaryColour=&H00E0E0E0,OutlineColour=&H40000000,Outline=1,Bold=0,Alignment=2,MarginV=15'" output.mp4
```

> Social/karaoke styles require programmatic rendering — use video-use or Remotion skills.

**CRITICAL**: Subtitles are ALWAYS applied LAST in the filter chain. Otherwise overlays hide captions.

---

## PART 8: MOTION DESIGN & ANIMATION

### The Three Pillars (Source: [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill))
| Pillar | Question | Drives |
|--------|----------|--------|
| **Emotional Intent** | What should the viewer FEEL? | Easing, timing, amplitude |
| **Visual Narrative** | What's the micro-story? | Setup → Action → Resolution |
| **Motion Craft** | How do we make it believable? | Physics, secondary motion, arcs |

### Three Motion Layers (flat animation = missing layers)
- **Primary**: Main action the viewer's eye follows
- **Secondary**: Supporting richness (shadows shifting, icons reacting)
- **Ambient**: Background life (gradients pulsing, particles drifting)

### 8-Step Animation Checklist
1. **Emotional target?** — joy, calm, urgency, elegance
2. **Motion Personality?** — Playful, Premium, Corporate, Energetic
3. **Primary property?** — position, scale, rotation, opacity
4. **Duration?** — see duration table below
5. **Easing family?** — entrance=decelerate, exit=accelerate
6. **Hero element?** — apply staging principles
7. **Secondary + ambient layers?** — add richness
8. **1/3 rules?** — motion distance, simultaneous elements

### Motion Personality Archetypes
| Archetype | Duration | Easing | Overshoot | Keywords |
|-----------|----------|--------|-----------|----------|
| **Playful** | 150-300ms | ease-out-back | 10-20% | fun, bouncy, cute, whimsical |
| **Premium** | 350-600ms | cubic-bezier(0.4,0,0.2,1) | 0% | elegant, minimal, luxury |
| **Corporate** | 200-400ms | cubic-bezier(0.2,0,0,1) | 0-3% | clean, professional, dashboard |
| **Energetic** | 100-250ms | ease-out-expo | 15-30% | dynamic, bold, exciting |

### Disney's 12 Principles (Adapted for Video/UI)
1. **Squash & Stretch** — Scale [1.2,0.8] on impact, [0.85,1.15] on stretch. Preserve volume.
2. **Anticipation** — Small opposite motion (10-20% of main) before action. 100-200ms.
3. **Staging** — Dim non-hero elements to 40-60% opacity. One primary action per beat.
4. **Straight Ahead vs Pose-to-Pose** — Fluid/organic vs planned/controlled. Use pose-to-pose for UI.
5. **Follow-Through** — Child elements trail parent by 50-150ms. Lower spring stiffness = more trail.
6. **Slow In/Out** — Entrance: ease-out. Exit: ease-in. NEVER linear for spatial movement.
7. **Arcs** — Add 10-20px perpendicular offset at path midpoint. Subtle=corporate, pronounced=playful.
8. **Secondary Action** — 30-50% amplitude of primary, 50-100ms after, different easing.
9. **Timing** — Heavy objects: 400-800ms. Light objects: 100-250ms. Enter 30-50% longer than exit.
10. **Exaggeration** — Playful: 15-25%, Corporate: 0-5%, Premium: 0%.
11. **Solid Drawing** — Consistent visual weight and perspective in every frame.
12. **Appeal** — Clean, readable, satisfying movement that serves the viewer.

### Duration Table
| Element Type | Duration | Rationale |
|-------------|----------|-----------|
| Tooltip / micro-feedback | 80-120ms | Must feel instant |
| Button press / toggle | 120-180ms | Responsive feedback |
| Icon transition | 150-250ms | Clear state change |
| Card enter / exit | 200-350ms | Spatial awareness |
| Modal / dialog | 300-400ms | Focus shift |
| Page / scene transition | 400-600ms | Context switch |
| Dramatic reveal | 600-1200ms | Theatrical build |
| Ambient loop | 2000-20000ms | Continuous life |

### Easing Reference
| Context | Easing | Cubic Bezier |
|---------|--------|-------------|
| Entrance | ease-out / decelerate | (0, 0, 0, 1) |
| Exit | ease-in / accelerate | (0.3, 0, 1, 1) |
| On-screen move | ease-in-out | (0.2, 0, 0, 1) |
| Bounce/playful | bounce-settle | (0.175, 0.885, 0.32, 1.275) |
| Elastic/dramatic | elastic-snap | (0.68, -0.55, 0.265, 1.55) |
| Apple iOS | HIG standard | (0.25, 0.1, 0.25, 1) |
| Material Design 3 | MD3 standard | (0.2, 0, 0, 1) |
| Ambient/float | gentle | (0.4, 0, 0.2, 1) |
| Snappy UI | decisive | (0.2, 0, 0, 1) |

### Spring Parameters
| Feel | Stiffness | Damping | Use |
|------|-----------|---------|-----|
| Very stiff | 400+ | 25-30 | Snapping, rigid |
| Standard | 250-350 | 18-24 | Default UI |
| Bouncy | 150-250 | 10-15 | Playful interactions |
| Very bouncy | 100-200 | 5-10 | Fun, game-like |

### Choreography Rules (Source: [LottieFiles](https://github.com/LottieFiles/motion-design-skill))
- **Lead with hero** — largest displacement, most attention-grabbing easing
- **Spatial consistency** — all elements enter from same direction or shared origin
- **Counter-motion** — hero moves right → ambient moves left at 20-30% speed
- **1/3 Rule (Distance)** — no motion travels >1/3 of screen without intermediate keyframe
- **1/3 Rule (Elements)** — max 1/3 of elements active simultaneously
- **Stagger patterns**: Sequential (lists), Center-out (hero), Wave (data bars), Random (organic)
- **Total stagger budget**: Stay under 500ms total

### Emotion-to-Motion Map
| Emotion | Motion Character | Path | Easing | Duration |
|---------|-----------------|------|--------|----------|
| Joy | Bouncy, arcs | Curved upward | ease-out-back | 200-400ms |
| Calm | Smooth, flowing | Gentle curves | sine ease-in-out | 500-1000ms |
| Urgency | Sharp, fast | Straight lines | ease-out | 100-200ms |
| Sadness | Slow, downward | Drooping curves | cubic ease-in-out | 600-1200ms |
| Surprise | Sudden, expanding | Radial outward | ease-out-expo | 150-300ms |
| Elegance | Slow, controlled | Long arcs | (0.4,0,0.2,1) | 400-700ms |

> Deep dive: [references/motion-design.md](references/motion-design.md)

---

## PART 9: SPEED & TIME MANIPULATION

### Speed Ramping Guide
| Effect | Speed | When to Use |
|--------|-------|-------------|
| Epic slow-mo | 0.25-0.5x | Impact moments, beauty shots, reveals |
| Subtle slow | 0.7-0.85x | Emphasis, emotional weight, focus |
| Normal | 1.0x | Default |
| Slight fast | 1.2-1.5x | Energy, tightening dead space |
| Timelapse feel | 1.5-3x | Travel, process, time passage |
| Hyperlapse | 4-16x | Long journeys, day-to-night |
| Speed ramp | Variable | Action sequences, reveals, transitions |

### FFmpeg Speed Recipes
```bash
# Smooth slow-mo 0.5x with optical flow interpolation
ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS,minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=60'" -an output.mp4

# Speed ramp: normal → slow at 2s → normal at 4s
ffmpeg -i input.mp4 -filter:v "setpts='if(between(T,2,4),2*PTS,PTS)'" output.mp4

# Hyperlapse 8x
ffmpeg -i input.mp4 -filter:v "setpts=0.125*PTS" -an output.mp4

# Reverse video
ffmpeg -i input.mp4 -vf reverse -af areverse output.mp4
```

**Rule**: Always ease into speed changes over 0.5-1s. Never jump speeds — it's jarring.

---

## PART 10: COMPOSITING & OVERLAYS

### Lower Thirds
- Animate in from left: 200-350ms, ease-out
- Hold: 3-5 seconds
- Animate out same direction: 150-250ms, ease-in
- Keep in lower 1/3, with safe-area padding (10% from edges)

### FFmpeg Compositing
```bash
# Picture-in-Picture (top-right, 25% size)
ffmpeg -i main.mp4 -i pip.mp4 -filter_complex \
  "[1]scale=iw*0.25:ih*0.25[pip];[0][pip]overlay=W-w-20:20" output.mp4

# Side-by-side split screen
ffmpeg -i left.mp4 -i right.mp4 -filter_complex \
  "[0]crop=iw/2:ih:0:0[l];[1]crop=iw/2:ih:iw/2:0[r];[l][r]hstack" output.mp4

# Green screen (chroma key)
ffmpeg -i foreground.mp4 -i background.mp4 -filter_complex \
  "[0]chromakey=0x00FF00:0.1:0.2[fg];[1][fg]overlay" output.mp4

# Watermark/logo overlay
ffmpeg -i input.mp4 -i logo.png -filter_complex \
  "[1]scale=100:-1,format=rgba,colorchannelmixer=aa=0.7[logo];[0][logo]overlay=W-w-20:20" output.mp4

# Vignette effect
ffmpeg -i input.mp4 -vf "vignette=angle=PI/4:mode=forward" output.mp4

# Letterbox (cinematic bars)
ffmpeg -i input.mp4 -vf "pad=iw:iw*9/16:(ow-iw)/2:(oh-ih)/2:black" output.mp4
```

### Overlay Rules (CRITICAL — Source: [video-use](https://github.com/browser-use/video-use))
1. **Subtitles applied LAST** in filter chain — overlays can hide captions otherwise
2. **Per-segment extract → lossless concat** — don't double-encode every segment
3. **Overlay timing**: `setpts=PTS-STARTPTS+T/TB` to sync overlay frame 0 to its window start
4. **Master SRT offsets**: `output_time = word.start - segment_start + segment_offset`

---

## PART 11: EXPORT & DELIVERY

### Platform Presets
| Platform | Resolution | FPS | Bitrate | Aspect | Codec |
|----------|-----------|-----|---------|--------|-------|
| YouTube (1080p) | 1920x1080 | 24-60 | 8-12 Mbps | 16:9 | H.264/H.265 |
| YouTube (4K) | 3840x2160 | 24-60 | 35-45 Mbps | 16:9 | H.265 |
| Instagram Reels | 1080x1920 | 30 | 5-8 Mbps | 9:16 | H.264 |
| TikTok | 1080x1920 | 30 | 5-8 Mbps | 9:16 | H.264 |
| Twitter/X | 1280x720 | 30 | 5 Mbps | 16:9 | H.264 |
| LinkedIn | 1920x1080 | 30 | 8 Mbps | 16:9 | H.264 |
| Cinematic | 2560x1080 | 24 | 15-20 Mbps | 21:9 | H.265 |
| ProRes Master | 1920x1080+ | 24+ | ~150 Mbps | Any | ProRes 422 |

### FFmpeg Export Commands
```bash
# YouTube optimized (H.264, web-ready)
ffmpeg -i input.mp4 -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -movflags +faststart output.mp4

# Social media vertical (auto-pad to 9:16)
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" -c:v libx264 -crf 20 output.mp4

# High quality master (archival)
ffmpeg -i input.mp4 -c:v libx264 -preset veryslow -crf 15 -c:a aac -b:a 320k -movflags +faststart output.mp4

# GIF from video (optimized)
ffmpeg -i input.mp4 -vf "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif

# Extract audio only
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3

# Thumbnail at specific time
ffmpeg -i input.mp4 -ss 00:00:05 -vframes 1 -q:v 2 thumbnail.jpg
```

---

## PART 12: THE PRO WORKFLOW

### Complete Production Pipeline
1. **Inventory** — catalog all source material (duration, content, quality, resolution)
2. **Transcribe** — word-level timestamps via ElevenLabs Scribe / Whisper / FunASR
3. **Analyze** — understand each clip: visual content, audio, energy, usability
4. **Strategy** — propose narrative structure, get user confirmation before cutting
5. **Assembly** — rough cut following narrative plan (3-act structure)
6. **Fine cut** — trim, pace, add J/L-cuts, match cuts, remove dead space
7. **Color** — match shots for consistency, then apply style grade
8. **Sound** — music selection, SFX, audio levels, ducking, normalization
9. **Graphics** — titles, lower thirds, overlays, animations, kinetic text
10. **Subtitles** — generate and burn captions (applied LAST in filter chain)
11. **Review** — watch at 1x speed. Fix everything that bothers you.
12. **Export** — platform-appropriate format and resolution
13. **Iterate** — show user, incorporate feedback, re-export

### Quality Checklist (Before Delivery)
- [ ] No audio pops at cut points (30ms fades applied)
- [ ] No flash frames or single-frame artifacts
- [ ] Color consistent within scenes
- [ ] Audio levels normalized (-16 LUFS target)
- [ ] Music ducks under dialogue (6-12dB reduction)
- [ ] Subtitles readable, correctly timed, no overlap
- [ ] No watermarks or artifacts from source material
- [ ] Aspect ratio correct for target platform
- [ ] Smooth speed ramps (no jarring speed jumps)
- [ ] All transitions serve the story (no gratuitous effects)
- [ ] Opening hook in first 3 seconds
- [ ] Energy curve matches narrative arc
- [ ] Export codec and bitrate match platform requirements

---

## TECHNOLOGY ROUTING

When the task requires a specific technology:

| Need | Tool | Skill Reference |
|------|------|----------------|
| Raw video processing | FFmpeg | This skill + `ffmpeg-recipes/` |
| Pro effects (glow, velocity, flash) | FFmpeg | `ffmpeg-recipes/pro-effects.md` |
| Text overlays & typography | FFmpeg | `ffmpeg-recipes/text-overlays.md` |
| Sound design & SFX | FFmpeg | `sound-design/sfx-guide.md` |
| Audio mixing & loudness | FFmpeg | `sound-design/audio-mixing.md` |
| Beat-synced editing | Python + FFmpeg | `automation/beat-sync.md` |
| Auto captions (Whisper) | Python + FFmpeg | `automation/auto-captions.md` |
| Batch video processing | Python + FFmpeg | `automation/batch-pipeline.md` |
| Social media viral edits | Strategy + FFmpeg | `social-media/viral-editing.md` |
| Platform export specs | FFmpeg | `social-media/platform-specs.md` |
| React-based video | Remotion | `programmatic/remotion-guide.md` |
| Python editing | MoviePy | `programmatic/moviepy-guide.md` |
| AI-powered workflow | Multi-tool | `ai-tools/ai-workflow.md` |
| HTML-to-video | HyperFrames | [hyperframes](https://github.com/heygen-com/hyperframes) |
| Math animations | Manim | [manim.community](https://manim.community) |
| AI image-to-video | AnimateAnything | [arxiv](https://arxiv.org/abs/2311.12886) |
| AI frame propagation | I2VEdit | [i2vedit](https://i2vedit.github.io/) |
| TTS / voice | ElevenLabs | [elevenlabs.io](https://elevenlabs.io) |
| Transcription | Whisper / FunASR | OpenAI Whisper or Alibaba FunASR |
| Motion graphics | GSAP / Lottie / CSS | See Part 8 |
| Cloud GPU rendering | Modal / RunPod | ~$0.01-0.23 per run |

---

*This skill synthesizes knowledge from [video-use](https://github.com/browser-use/video-use), [hyperframes](https://github.com/heygen-com/hyperframes), [motion-design-skill](https://github.com/LottieFiles/motion-design-skill), [motion-skills](https://github.com/iart-ai/motion-skills), [claude-code-video-toolkit](https://github.com/Kapildevv/-claude-code-video-toolkit), [claude-code](https://github.com/KirttiVushan/claude-code), [Claude-Code-Video-Toolkit](https://github.com/wilwaldon/Claude-Code-Video-Toolkit), [ai-video-editing-skill](https://github.com/znyupup/ai-video-editing-skill), [Monet](https://github.com/Monet-AI-Editor/Monet), [AnimateAnything](https://animationai.github.io/AnimateAnything/), and [I2VEdit](https://i2vedit.github.io/). Full credit to all contributors.*
