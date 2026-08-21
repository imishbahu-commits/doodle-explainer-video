# CLAUDE.md — READ THIS FIRST (auto-loaded in every new chat)

## ⚠️ THE SECOND RULE THAT KEEPS GETTING BROKEN

**NEVER stretch or reuse images to fill time. 1 beat = 1 image. Always.**

Wrong (forbidden): generating 10 images and then holding each one for 6+
seconds to "cover" a 60s video, reusing images, or extending beats to
match a short image list.

Right: count the beats first, then generate exactly that many images.

### The beat math (from the measured reference: one cut every 2-6s)

| Video length | Beats (images) needed | AI generations needed | Turns (10/turn) |
|---|---|---|---|
| 60 s | **~17** | ~6-9 (the rest come free) | 1 |
| 3 min | ~50 | ~14-22 | 2-3 |
| 8 min | ~133 | ~40-60 | 4-6 |

### The smart supply chain (skills/image-queue — the standard path)

Every beat gets ONE image, but beats are classified by the CHEAPEST source
that can draw them, in this order:

1. `doodle` — `skills/handdrawn-code` draws diagrams, maps, arrows, labels
   from code. FREE, unlimited, local.
2. `asset` — `skills/asset-library` fetches single files from 23 cloud
   libraries (Kenney CC0, game-icons sketchy icons, 4 emoji sets, humaaans
   people, 0x72 + Pixel Adventure pixel backgrounds, openclipart…).
   FREE, unlimited, never committed.
3. `pose` — a character that was already generated is re-posed from its
   rig + pose library (ae-motion). FREE, unlimited, local.
4. `ai` — ONLY genuinely new subjects (a character's first appearance, a
   unique artifact, a new location). This is the ONLY thing that consumes
   the 10-images-per-turn cap.

So a 3-minute video costs ~15 AI generations instead of 50. Use
`skills/image-queue/scripts/queue.py` for the ledger.

### The batch loop (exactly this, for the ai beats only)

1. Classify beats (`queue.py classify`), then generate the ai beats,
   **min(10, pending) per turn**, in parallel.
2. Pass the first accepted image as the reference image on every call.
3. Save each image to `projects/<slug>/assets/`, mark it (`queue.py mark`),
   and commit — a crash must never cause regeneration.
4. If ai beats remain, **STOP** and tell the user exactly:
   `"X of Y images done — type 'go' for the next batch."`
5. Never skip the stop, never stretch, never reuse. The user's single
   word starts the next turn, and the cap resets every turn.

### Voiceover is the boss — never stretch images to cover it

Record (or generate) the voiceover, then fit the beats to it
(`script_planner.py fit`). One voiceover segment = one beat = one image.
A longer voiceover means MORE beats, each with its OWN image — an image
is never held longer and never reused to fill time.

### Unlimited paths (when the batch loop is too slow)

- `skills/handdrawn-code` — generates hand-drawn doodles FROM CODE:
  zero cap, zero cost, runs instantly (doodle.mjs + ink-elements.mjs).
  Use it for any beat, especially simple diagrams/stick scenes.
- `skills/asset-library` — 5,000+ CC0 Kenney PNGs, fetched one at a
  time. Use for props/backgrounds instead of generating.
- The user's own free generators (Perchance, Bing Creator, Leonardo,
  or their Qwen key via `tools/qwen_media.py`) — ask the user if they
  want to generate the bulk themselves and upload.

**Every image in every video MUST look HAND-DRAWN — MS-Paint style.
Never "cinematic", never "moody painterly", never dark, never photoreal.
If the images look cinematic, the video is WRONG and must be redone.**

The style reference: The Paint Explainer channel. Hand-drawn doodle
characters on PURE WHITE backgrounds, thick black outlines, flat colors.

## Copy these prompts VERBATIM (change ONLY the {SUBJECT} part)

### For a character / creature / object (subject PNG):

```
Hand-drawn doodle illustration of {SUBJECT}, on a PURE WHITE background.
MS-Paint-like style: thick black outlines, flat bold colors, slightly
imperfect hand-drawn lines, simple and {MOOD: funny-scary | grumpy | cute}.
No text, no background scenery, no shadows, no gradients.
```

### For a background (separate image):

```
Simple hand-drawn doodle {SETTING} background, MS-Paint-like style:
flat {PALETTE} colors, thick black outlines, wavy hand-drawn lines,
completely EMPTY in the middle (no characters, no subject). No text.
```

### NEVER use prompts like "cinematic documentary illustration", "moody
painterly", "film grain", "deep navy palette". Those produce the WRONG
style. If you find yourself writing those words, stop and use the
templates above instead.

## The style lock (non-negotiable)

1. Generate the FIRST image with the template above.
2. **Pass that first image as the reference image on EVERY later
   generation** (referenceImages / reference_image / style reference —
   whichever the generator supports).
3. Every image must match that first image's line weight and look.
   Regenerate anything that looks different.

## The video pipeline (numbered — follow in order)

1. **Script** — `skills/youtube-script`: ANY topic (or propose 3 topics
   when the user has none), pick a format (myth / misconception / mystery /
   how-it-works / comparison / timeline / big-question — see
   `skills/youtube-script/references/formats.md`), research facts, write
   hooks + but-therefore seams, one spoken beat = one image.
   `script_planner.py plan` writes the beat math + skeleton.
2. **Images** — `skills/image-queue`: classify beats (doodle / asset /
   pose / ai), fill the free beats locally, generate ai beats 10 per turn
   with the templates above and the style lock. Character + minimalist
   background are TWO images (background EMPTY in the middle).
3. **Motion** — `skills/ae-motion/scripts/ae_motion.py`:
   slide-ins, pops, punch-ins, rig-posed limbs. Cuts every 2-6 s,
   subjects centered, 60 fps, hand fonts for text.
4. **Character actions** — a character walking/waving/blinking uses
   `skills/character-animation-skill`. Missing props: `skills/asset-library`
   (23 cloud libraries — Kenney CC0, game-icons, 4 emoji sets, humaaans,
   open-peeps, openclipart, 0x72 + Pixel Adventure backgrounds — fetch one
   file at a time, never commit).
5. **Audio** — voiceover + quiet music bed (−23 dB), 0.7 s pauses between
   chapters. No captions unless asked. Fit beats to the voiceover with
   `script_planner.py fit` (longer voiceover = more beats, more images —
   never stretch).
6. **Verify** — `skills/video-polish` checks the numbers.
7. **Package for YouTube** — `skills/youtube-seo`: title variants (Browse
   vs Search), description, tags, chapters, the 15-second hook line, and
   the thumbnail concept — generated from the finished script.

## Files to read as needed

> **Current measured authority (read first for Paint Explainer builds):**
> `references/paint-explainer-analysis-4v/STYLE_SPEC.md` plus
> `references/paint-explainer-analysis-4v/style_rules.json`. This four-video,
> 98,705-frame corpus supersedes older single-video/speculative motion numbers.
> Critical correction: camera is locked; no sustained whole-scene zoom was
> verified. Use hard cuts plus local pose/prop/label animation.

| Question | File |
|---|---|
| Current complete style specification | `references/paint-explainer-analysis-4v/STYLE_SPEC.md` |
| Machine-readable current rules | `references/paint-explainer-analysis-4v/style_rules.json` |
| Every measured cut/shot | `references/paint-explainer-analysis-4v/CUT_LIST.md` + `cuts/` |
| Legacy single-video format numbers | `references/paint-explainer-autopsy.md` |
| Legacy motion grammar | `references/paint-explainer-style.md` |
| Which skill fires when | `skills/content-router/SKILL.md` |
| Script formats for any niche | `skills/youtube-script/references/formats.md` |
| Image supply chain | `skills/image-queue/SKILL.md` |
| YouTube SEO playbook | `skills/youtube-seo/README.md` |
| Keyframe engine docs | `skills/ae-motion/SKILL.md` |
| Style prompt templates | `skills/handdrawn-style-lock/SKILL.md` |

## What NOT to do

- Do NOT produce static stills synced to voiceover with no motion.
- Do NOT use cinematic/painterly image prompts.
- Do NOT skip the style lock (reference image on every call).
- Do NOT generate more than 10 AI images per turn (queue them with
  `skills/image-queue`, stop for the user's "go").
- Do NOT stretch or reuse images to cover a longer voiceover — add beats.
- Do NOT add captions, transitions, or loud music.
