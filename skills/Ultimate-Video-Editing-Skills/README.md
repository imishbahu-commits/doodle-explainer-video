# Ultimate Video Editing Skills

**Turn any AI code editor into a 50+ year veteran video editor.** One install. God-level editing, color grading, animation, motion design, sound design, and compositing — all from natural language.

Works with **Claude Code**, **Codex**, **Gemini**, **Cursor**, **Windsurf**, **GitHub Copilot**, and 40+ AI coding agents.

---

## What This Does

When you install this skill package and invoke `/Ultimate-Video-Editing-Skills`, your AI assistant transforms into a professional video editor with mastery over:

- **Narrative Editing** — Three-act structure, pacing, all cut types (J-cut, L-cut, match cut, smash cut, cross-cut)
- **Color Grading** — Cinema-grade color science, LUT-equivalent FFmpeg filters, mood-driven grading, scene matching
- **Motion Design** — Disney's 12 principles, 4 personality archetypes, spring physics, choreography
- **Sound Design** — Audio hierarchy, music ducking, beat-synced editing, noise removal, normalization
- **Animation** — Kinetic typography, lower thirds, title cards, overlays, transitions via GSAP/CSS/Lottie/Three.js
- **Subtitles** — Classic, modern, social (TikTok-style), cinematic, karaoke — with burn-in recipes
- **Speed Ramping** — Smooth slow-mo, hyperlapses, frame interpolation
- **Compositing** — PIP, overlays, green screen, split screen, picture-in-picture
- **AI-Native Workflows** — Transcription-first editing, multi-modal analysis, automated vlog cutting
- **Pro Effects** — Glow/bloom, chromatic aberration, velocity edits, white flash transitions, zoom crops
- **Auto Captions** — Whisper-based word-level transcription with karaoke/pop-up/highlight styles
- **Beat-Synced Editing** — Librosa/Aubio beat detection → auto-cut video segments to music rhythm
- **Batch Processing** — Process hundreds of videos with consistent quality, multi-platform export
- **Sound Design** — SFX layering, foley, whoosh/impact generation, audio ducking, platform-specific mixing
- **Viral Social Media** — 2026 hook formulas, pacing rules, trending formats, engagement triggers
- **Platform Specs** — Every export setting for Instagram, TikTok, YouTube, Twitter, LinkedIn, WhatsApp
- **Text & Typography** — Animated drawtext, lower thirds, timers, kinetic text, image overlays
- **Programmatic Video** — Remotion (React) + MoviePy (Python) guides for automated video creation
- **Export** — Platform-optimized presets for YouTube, TikTok, Reels, LinkedIn, Twitter, Cinema

---

## Quick Install

### Claude Code / Cursor / Windsurf / Copilot
```bash
# Clone into your project
git clone https://github.com/Rajbharti06/Ultimate-Video-Editing-Skills.git .claude/skills/ultimate-video-editor

# Or copy just the skill files
cp -r Ultimate-Video-Editing-Skills/skills/ultimate-video-editor/ .claude/skills/ultimate-video-editor/
cp Ultimate-Video-Editing-Skills/commands/Ultimate-Video-Editing-Skills.md .claude/commands/Ultimate-Video-Editing-Skills.md
```

### Manual Install (Any Agent)
1. Clone this repo
2. Copy `skills/ultimate-video-editor/` into your project's `.claude/skills/` (or equivalent skill directory)
3. Copy `commands/Ultimate-Video-Editing-Skills.md` into `.claude/commands/`
4. Start your AI agent and type `/Ultimate-Video-Editing-Skills`

### Prerequisites
| Tool | Required | Install |
|------|----------|---------|
| FFmpeg | Yes | `brew install ffmpeg` / `winget install ffmpeg` / `apt install ffmpeg` |
| Python 3.9+ | Recommended | For automation scripts (beat-sync, captions, batch processing) |
| Node.js 18+ | Optional | For Remotion/HyperFrames programmatic video |
| faster-whisper | Optional | `pip install faster-whisper` — auto captions with word-level timestamps |
| librosa | Optional | `pip install librosa` — beat detection for music-synced editing |
| moviepy | Optional | `pip install moviepy` — Python video editing automation |

---

## Usage

Just tell your AI what you want:

```
"Edit this video — remove filler words, add subtitles, color grade it warm cinematic"

"Make a TikTok-style edit with beat-synced cuts and animated captions"

"Color grade this like a Wes Anderson film — pastel warm, centered compositions"

"Add a professional lower third intro, speed ramp the action sequence, and export for YouTube"

"Create a product launch video with kinetic typography and motion graphics"
```

The skill handles routing — it knows when to use FFmpeg filters vs. Remotion compositions vs. HyperFrames HTML-to-video vs. raw Python processing.

---

## What's Inside

```
skills/
  ultimate-video-editor/
    SKILL.md                          # Master skill — READ FIRST (12 parts, 600+ lines)
    references/
      advanced-techniques.md          # AI editing (AnimateAnything, I2VEdit), pro heuristics
      motion-design.md                # Disney's 12 principles, timing tables, choreography
      easing-reference.md             # Complete cubic-bezier + spring parameter lookup
      pitfalls.md                     # 30+ hard-won editing pitfalls to avoid
    director/
      narrative-structure.md          # Three-act structure, pacing, shot rhythm
      choreography.md                 # Multi-element coordination, stagger patterns
      emotion-mapping.md              # Emotion → motion/color/timing translation
    patterns/
      entrance-exit.md                # 20+ entrance/exit animation recipes
      transitions.md                  # Every transition type with FFmpeg commands
      state-feedback.md               # Success, error, loading, hover patterns
    ffmpeg-recipes/
      color-grading.md                # 30+ color grade recipes (cinematic, moody, vintage, etc.)
      audio-processing.md             # Noise removal, ducking, normalization, mixing
      compositing.md                  # PIP, overlays, split screen, green screen
      speed-manipulation.md           # Slow-mo, speed ramps, hyperlapse, time remapping
      export-presets.md               # Platform-optimized export commands
      subtitles.md                    # Every subtitle style with burn-in commands
      pro-effects.md                  # ★ Glow/bloom, velocity edits, flash transitions, zoom, RGB split
      text-overlays.md                # ★ Animated drawtext, kinetic typography, lower thirds, timers
    color-science/
      color-grading-master.md         # Film-grade color science, scopes, color theory
      lut-equivalent-filters.md       # Recreate popular LUTs in pure FFmpeg
      scene-matching.md               # Match color across shots, auto white balance
    automation/                       # ★ NEW — Python-powered automation
      beat-sync.md                    # ★ Librosa/Aubio beat detection → auto-cut to music
      auto-captions.md                # ★ Whisper word-level transcription + animated caption styles
      batch-pipeline.md               # ★ Batch process hundreds of videos with profiles
    sound-design/                     # ★ NEW — Professional audio
      sfx-guide.md                    # ★ SFX layering, foley, whoosh/impact, free SFX sources
      audio-mixing.md                 # ★ Platform loudness standards, voice chains, EQ reference
    social-media/                     # ★ NEW — Viral content strategy
      viral-editing.md                # ★ 2026 hooks, pacing, trending formats, engagement triggers
      platform-specs.md               # ★ Every platform's specs + FFmpeg export presets
    programmatic/                     # ★ NEW — Code-based video
      remotion-guide.md               # ★ React video generation, components, rendering
      moviepy-guide.md                # ★ Python video automation, batch processing, composition
    ai-tools/                         # ★ NEW — AI workflow
      ai-workflow.md                  # ★ AI editing pipeline, scene detection, multi-platform export
commands/
  Ultimate-Video-Editing-Skills.md    # The slash command entry point
```

---

## Standing on the Shoulders of Giants

This skill package synthesizes knowledge from these incredible open-source projects. **Full credit and gratitude to every contributor:**

### Core Sources

| Project | Author | What We Learned | License |
|---------|--------|----------------|---------|
| [video-use](https://github.com/browser-use/video-use) | Browser Use | Transcript-first editing, filler removal, audio-primary cuts, subtitle burning, overlay system | MIT |
| [hyperframes](https://github.com/heygen-com/hyperframes) | HeyGen | HTML-to-MP4 rendering, 35 animation rules, 15 blueprints, GSAP/Lottie/Three.js adapters, cinematic captions | Apache 2.0 |
| [motion-design-skill](https://github.com/LottieFiles/motion-design-skill) | LottieFiles | Disney's 12 principles for UI, motion personality archetypes, timing/easing tables, choreography, emotion mapping | MIT |
| [motion-skills](https://github.com/iart-ai/motion-skills) | iart.ai | 50 motion graphics workflows across 14 packs, deliver-and-verify loop methodology | MIT |
| [claude-code-video-toolkit](https://github.com/Kapildevv/-claude-code-video-toolkit) | Kapildevv | Remotion skill integration, FFmpeg recipes, cloud GPU tools, voice generation | MIT |
| [claude-code](https://github.com/KirttiVushan/claude-code) | KirttiVushan | Agent performance optimization, subagent patterns, TDD workflows | MIT |
| [Claude-Code-Video-Toolkit](https://github.com/wilwaldon/Claude-Code-Video-Toolkit) | wilwaldon | Video tool curation, Manim/Remotion/FFmpeg/YouTube workflow documentation | — |
| [ai-video-editing-skill](https://github.com/znyupup/ai-video-editing-skill) | nyx (znyupup) | Automated vlog editing workflow, 24 pitfalls, three-act narrative prompts, Whisper/FunASR integration | — |
| [Monet](https://github.com/Monet-AI-Editor/Monet) | Monet AI Editor | Electron editor with CLI/MCP control, Remotion compositions, brand extraction, timeline manipulation | — |

### Research References

| Paper | Authors | Contribution |
|-------|---------|-------------|
| [AnimateAnything](https://animationai.github.io/AnimateAnything/) | Alibaba Group | Image-to-video via text prompts, motion area masks, motion strength control |
| [I2VEdit](https://i2vedit.github.io/) | SIGGRAPH ASIA 2024 | Single-frame edit propagation through video, style transfer, subject replacement |

### Animation & Motion Libraries Referenced

| Library | Use In This Skill |
|---------|------------------|
| [GSAP](https://gsap.com/) | Timeline animations, easing, stagger, ScrollTrigger |
| [Lottie](https://lottiefiles.com/) | Vector animations, micro-interactions |
| [Three.js](https://threejs.org/) | 3D graphics, WebGL rendering |
| [Anime.js](https://animejs.com/) | Lightweight animation engine |
| [Remotion](https://www.remotion.dev/) | React-based programmatic video |
| [Manim](https://www.manim.community/) | Mathematical animations (3Blue1Brown style) |
| [MoviePy](https://zulko.github.io/moviepy/) | Python video editing |
| [FFmpeg](https://ffmpeg.org/) | Universal video processing backbone |

---

## Philosophy

> **"The best edit is one the viewer never notices."**

This skill doesn't teach AI to follow templates. It teaches AI to *think like an editor* — to understand why a J-cut builds anticipation, why color temperature shifts emotion, why the 6-second rule keeps attention, why silence after noise is powerful.

Every technique has a *why*. Every recipe has context for *when* to use it and *when not to*. The AI learns judgment, not just commands.

---

## Contributing

Found a technique missing? Have a better FFmpeg recipe? Know a pro editing heuristic that should be here?

1. Fork this repo
2. Add your knowledge to the appropriate file
3. Include the *why* — not just the *what*
4. PR with before/after examples if possible

---

## License

MIT License — use freely, credit appreciated.

**Created by [Raj Bharti](https://github.com/Rajbharti06)** — synthesizing the collective wisdom of the open-source video editing community.
