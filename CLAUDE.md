# CLAUDE.md — READ THIS FIRST (auto-loaded in every new chat)

## ⚠️ THE SECOND RULE THAT KEEPS GETTING BROKEN

**NEVER stretch or reuse images to fill time. 1 beat = 1 image. Always.**

Wrong (forbidden): generating 10 images and then holding each one for 6+
seconds to "cover" a 60s video, reusing images, or extending beats to
match a short image list.

Right: count the beats first, then generate exactly that many images.

### The beat math (from the measured reference: one cut every 2-6s)

| Video length | Beats (images) needed | Turns (10/turn) |
|---|---|---|
| 60 s | **~17-20** | 2 |
| 3 min | ~50-60 | 5-6 |
| 8 min | ~130-160 | 13-16 |

### The batch loop (exactly this)

1. Write ALL image prompts first (one per beat) into the
   `skills/image-batcher` ledger.
2. Generate **min(10, pending)** in parallel this turn.
3. Mark them done, commit.
4. If images remain, **STOP** and tell the user exactly:
   `"X images left — type 'go' and I generate the next 10."`
5. Never skip the stop, never stretch, never reuse. The user's single
   word starts the next turn, and the cap resets every turn.

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

1. **Script** — write the 5-act story (myth → doubt → dig → explanation →
   kicker). Read `references/paint-explainer-autopsy.md` for the numbers.
2. **Images** — one subject PNG per narration clause via the templates
   above (max 10 generations per turn, use `skills/image-batcher` ledger).
3. **Motion** — `skills/ae-motion/scripts/ae_motion.py`:
   slide-ins, pops, punch-ins, puppet-rigged limbs. Cuts every 2-6 s,
   subjects centered, 60 fps, hand fonts for text.
4. **Character actions** — a character walking/waving/blinking uses
   `skills/character-animation-skill`. Missing props: `skills/asset-library`
   (5,000+ CC0 Kenney assets, fetch one file at a time).
5. **Audio** — voiceover + quiet music bed (−23 dB), 0.7 s pauses between
   chapters. No captions unless asked.
6. **Verify** — `skills/video-polish` checks the numbers.

## Files to read as needed

| Question | File |
|---|---|
| Exact format numbers | `references/paint-explainer-autopsy.md` |
| Motion grammar (moves) | `references/paint-explainer-style.md` |
| Which skill fires when | `skills/content-router/SKILL.md` |
| Keyframe engine docs | `skills/ae-motion/SKILL.md` |
| Style prompt templates | `skills/handdrawn-style-lock/SKILL.md` |

## What NOT to do

- Do NOT produce static stills synced to voiceover with no motion.
- Do NOT use cinematic/painterly image prompts.
- Do NOT skip the style lock (reference image on every call).
- Do NOT generate more than 10 images per turn (use the batcher).
- Do NOT add captions, transitions, or loud music.
