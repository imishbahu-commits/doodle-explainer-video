---
name: handdrawn-style-lock
description: Locks the "human hand-drawn explainer" art style (The Paint Explainer / Dinzo style — MS-Paint-like doodles, thick outlines, flat colors) so every image in a project matches the same hand. Use when generating beat illustrations, characters, or background PNGs for explainer videos, and whenever style consistency across many images matters.
---

# Hand-drawn style lock

The style that reads as *drawn by a human with a marker*, not rendered
by an AI. Two separate jobs, one hand:

## 1. Beat subjects (PNG on pure white)

Prompt template — copy exactly, change only the subject:

```
Hand-drawn doodle illustration of {SUBJECT}, on a PURE WHITE background.
MS-Paint-like style: thick black outlines, flat bold colors, slightly
imperfect hand-drawn lines, simple and {MOOD}. {SPECIFIC DETAILS}.
No text, no background scenery, no shadows, no gradients.
```

Rules that lock the hand:

- **Pure white background, always.** Flat white lets the isolation script
  cut the subject cleanly (magic wand = border flood-fill), and the same
  white reads as "scanned marker drawing".
- **Thick uniform outlines** on everything; **flat fills**; slightly
  *imperfect* lines (ask for it explicitly — perfect bezier lines read as
  vector, not hand).
- **One subject per image.** Two subjects = two PNGs.
- **Mood words only**: "funny-scary", "grumpy", "cute", "menacing",
  "childlike". Never "cinematic", "detailed", "photorealistic".
- **Labels never in the image.** Text is added as a separate layer at
  edit time (models mangle lettering; the editor layer is also what the
  motion skill animates).

## 2. Backgrounds (separate image, same hand)

```
Simple hand-drawn doodle {SETTING} background, MS-Paint-like style:
flat {PALETTE} colors, thick black outlines, wavy hand-drawn lines,
completely EMPTY in the middle (no characters, no subject).
No text.
```

- Background and subjects must look like the same marker. Use the same
  outline thickness and the same palette family.
- Keep the middle empty — the subject PNG gets composited there.
- One flat color wash per background, plus simple doodle props (bubbles,
  grass, rocks, stars).

## 3. The consistency lock (the part that matters over 100 images)

1. Generate the FIRST subject. Verify it by eye (or the ink/background
   checks below).
2. **Pass that first PNG as the style reference on every later call**
   (referenceImages / reference image parameter — whichever the generator
   supports). This is the actual lock: the generator copies line weight
   and character design from it.
3. Regenerate anything that breaks the rules; never let one off-style
   image through — one drift frame undoes the whole hand.

## 4. Automatic checks (scripts)

Isolation (magic wand): `skills/ae-motion/scripts/ae_motion.py --isolate subject.png`
prints the cut's bounding box. A good cut has no white halo — check the
corners of the cut are transparent.

Style QC: white background present (corner pixel ≈ 255,255,255), thick
outline (ink > 2% of pixels), flat fills (few unique colors). Regenerate
if any fails.

## Palette

| Mood | Palette |
|---|---|
| Neutral diagrams | white bg, black ink, one accent |
| Playful | white bg, primary colors (red/yellow/blue) |
| Menacing | white bg, black ink, one red accent |
| Nature | white bg, greens/browns/blue |

Keep palettes small: 2–4 colors + black ink. That restraint IS the style.
