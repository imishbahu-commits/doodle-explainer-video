# The Paint Explainer — animation style profile

> **LEGACY HIGH-LEVEL PROFILE:** current measured rules are in
> `paint-explainer-analysis-4v/STYLE_SPEC.md` and `style_rules.json`; those
> values win whenever this profile conflicts.

> High-level technique analysis of a public channel, for building original
> work. Never copy their drawings, scripts, narration, or branding — extract
> only the grammar. (Their own disclosures confirm the recipe: human-drawn
> art, AI TTS, editing-software motion.)

## What the channel is

1M+ subscriber explainer channel, 10–15 min videos, list-catalog formats:
"Every X in Each Y", "How You'd Die In Every X", "The 5 Times The World
Ended". Fast AI-narrated lists with dark humor over **hand-drawn doodles**.
They publicly state: *"all drawings are created by a real human artist, with
AI used only rarely for technical adjustments"* and the voiceover is a
generic AI TTS preset.

## The visual system

- **Hand-drawn subject PNGs with transparent backgrounds** — one clear
  subject per beat (a creature, an icon, a character), thick outlines,
  flat bold colors, slightly imperfect lines.
- **Hand-drawn backgrounds** — clean, simple (white, flat color washes,
  sketched scenery), never photoreal. Background and subject are drawn to
  feel like the same hand.
- **Labels** are hand-lettered or plain-bold text placed in the frame, never
  part of the drawing.
- Honest naivety: the drawing reads as *explainer sketch*, not fine art.
  That is the brand.

## The motion grammar (the important part)

Their "animation" is editing-software keyframing on still PNGs — no
frame-by-frame drawing, no rigs. Community analysis and observation agree
the whole motion vocabulary is:

1. **Slide-in characters** — the subject PNG slides in from off-frame
   (left/right/up) with a slight overshoot settle. 0.3–0.5s.
2. **Pop icons** — labels, arrows, numbers pop in with a scale overshoot
   (start 60%, land 100% with a bounce). One pop per narration beat.
3. **Zoom into diagrams** — the camera slowly pushes toward the subject
   (5–15% over the shot), or a fast punch-in for emphasis. The classic
   "zoom into the picture" move.
4. **Quick visual swaps** — beat N shows creature A; beat N+1 hard-cuts to
   creature B. The swap IS the pacing; matches the narration word-for-word.
5. **Slide-push transitions** — scenes enter with a simple push or reveal,
   no fancy transitions (fades/dissolves are rare).
6. **Parallax layering** — subject layer and background layer move at
   different speeds during pans/zooms, so the flat drawing gains depth.
7. **Subtle idle motion** — a held subject gently bobs/floats (3–6px,
   1–2s cycle) so the frame never feels dead between cuts.

Timing rules:
- One visual change per narration clause. The image changes exactly when
  the narrator moves to the next item.
- Holds are short in list videos: 2–6s per item, hard cuts between items.
- Sound: narration + light music bed (they do use music; volume low under
  voice). No SFX per item.

## Why this style is perfect for a 10-image-per-turn budget

Every image earns its place through REUSE:
- one subject PNG → slide-in, zoom, pop-label, and swap all reuse it
- one background → parallax across many beats
- mirrored/re-tinted variants of the same PNG → "new" shots for free

So a 10-image batch can cover far more than 10 beats — the motion grammar
multiplies each asset.

## Implementation in this repo

The keyframe machinery already exists (eased keyframes + hard cuts +
parallax + punch-in, proven in the puppet/studio demos). The style profile
adds three habits:

1. Generate subjects on flat/transparent-friendly backgrounds so the
   magic-wand isolation in code can cleanly separate subject from background.
2. Draw backgrounds separately (or generate them), never baked into the
   subject image.
3. Animate per clause: slide → hold-with-bob → pop label → hard cut.
