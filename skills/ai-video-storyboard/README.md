# AI Video Storyboard Generator

> A skill for Claude Code, Cursor, Windsurf, and other AI coding assistants that turns vague video ideas into complete multi-shot storyboards — with ready-to-copy prompts, visual consistency guidance, and post-production checklists.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-8B5CF6)](https://claude.com/claude-code)
[![Cursor](https://img.shields.io/badge/Cursor-compatible-000000)](https://cursor.com)

---

## The Problem

AI video generators produce **5–15 second clips**. But real videos people actually ship are longer:

- 30-second TikTok Reels
- 60-second Instagram Ads
- 90-second product explainers
- 2-minute YouTube Shorts

If you just generate 6 clips independently and stitch them together, the result looks like **6 disconnected pieces made by 6 different people**. No consistent color, no consistent lighting, no narrative arc.

This skill fixes that.

## What It Does

Give it a brief like "a 30-second TikTok for my coffee shop opening" and it produces:

1. **A shared visual theme** — color palette, lighting style, lens character, film look, motion language — that every shot must respect
2. **A complete shot list** — 6–18 shots with purpose, composition, camera move, lighting, subject, and action
3. **Ready-to-copy prompts** — cinematic, concrete, 40–80 words each, tuned for modern AI video models
4. **Audio direction** — what the synchronized audio should sound like per shot
5. **Post-production checklist** — LUT suggestions, transition specs, BGM direction, export settings
6. **"Why this works" rationale** — the storytelling logic behind the shot order

See [`examples/tiktok-reel-30s-coffee.md`](examples/tiktok-reel-30s-coffee.md) for a complete worked example.

## Quick Example

**You:** "Help me make a 30s TikTok for my specialty coffee shop opening next week. Warm and analog vibe, final CTA is 'Opening Saturday'."

**The skill outputs:**

```markdown
# 30s TikTok Reel — Coffee Shop Opening
6 shots × 5s, 9:16 vertical

## Visual Theme
- Palette: espresso brown, cream, muted amber, sage green
- Lighting: warm golden backlight with motivated window light
- Lens: shallow DOF, 35mm full-frame
- Film: subtle 16mm grain, warm 3200K

## Shot 1 (0-5s) — Hook: The Pour
Prompt to copy:
> Extreme close-up overhead shot of hot water pouring from a brass
> gooseneck kettle into a white ceramic V60 dripper filled with dark
> coffee grounds, the grounds blooming and rising in slow motion,
> warm golden backlight with visible steam curling upward, shallow
> depth of field, 35mm full-frame look, subtle 16mm film grain,
> cinematic 1080p, synchronized audio, 5 seconds, 9:16 vertical

[... 5 more shots with matching visual language ...]

## Post-Production Checklist
- Stitch in CapCut with Portra 400 LUT
- 0.3s dissolve transitions
- Acoustic guitar BGM at 85 BPM
- Export 1080×1920 30fps
```

## Installation

### Claude Code

1. Clone this repo or copy `SKILL.md` into your Claude Code skills directory:

   ```bash
   # User-level (all projects)
   cp SKILL.md ~/.claude/skills/ai-video-storyboard/SKILL.md
   cp -r examples references ~/.claude/skills/ai-video-storyboard/
   ```

2. Invoke in any Claude Code session:

   ```
   Use the ai-video-storyboard skill to plan a 30s TikTok for my coffee shop opening
   ```

### Cursor

1. Copy the contents of `SKILL.md` (without frontmatter) into your project's `.cursorrules` file
2. Ask Cursor to "plan an AI video storyboard for [your brief]"

### Windsurf

1. Copy `SKILL.md` content into your `.windsurfrules` file
2. Invoke the same way

### ChatGPT / Claude.ai

Paste the contents of `SKILL.md` as system instructions for a custom GPT or project.

## What Makes It Different

Most AI video helpers give you **one prompt at a time**. This skill gives you **a coordinated production plan**:

| Feature | Typical prompt helpers | AI Video Storyboard |
|---|---|---|
| Output | A single prompt | A shot list of 6–18 prompts |
| Visual consistency | Not considered | Enforced via a shared theme layer |
| Narrative structure | None | Explicit arc (hook/build/payoff/CTA) |
| Per-shot details | Prompt only | Prompt + composition + camera + lighting + audio |
| Post-production | Not covered | LUT, transitions, BGM, export specs |
| Platform awareness | Generic | Platform-specific cadence (TikTok, Reels, Shorts, Ads) |

## Use Cases

- 📱 **TikTok / Reels / Shorts creators** making multi-shot content
- 📢 **Marketing teams** producing short-form ads at scale
- 🛍️ **E-commerce brands** shooting product showcase videos
- 🎨 **Creative agencies** pitching concept videos to clients
- 🎮 **Indie game devs** making trailers and store videos
- 🎓 **Educators** creating explainer content
- 🎬 **Freelancers** delivering multi-shot video projects

## Examples Library

- [`tiktok-reel-30s-coffee.md`](examples/tiktok-reel-30s-coffee.md) — Specialty coffee shop opening Reel

*More examples coming soon: 15s Instagram Ad, 60s product explainer, 90s brand story, 2-minute YouTube Short.*

## Contributing

Contributions welcome. Especially:

- Additional examples for new platforms / genres
- New references (genre templates, lighting patterns, camera moves)
- Translation of the skill into other languages
- Format ports (Continue.dev, Cline, Windsurf, OpenAI Custom GPT)

Open an issue or PR.

## License

MIT — use freely, commercial or personal.
