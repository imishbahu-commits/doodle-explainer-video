# MAKE_VIDEO.md — the 10-line recipe (read this, then just copy)

> One page. No documents to search. Follow top to bottom.

## 1. Style lock — COPY THESE PROMPTS VERBATIM

**Every subject image:**
```
Hand-drawn doodle illustration of {SUBJECT}, on a PURE WHITE background.
MS-Paint-like style: thick black outlines, flat bold colors, slightly
imperfect hand-drawn lines, simple and {MOOD: funny-scary | grumpy | cute}.
No text, no background scenery, no shadows, no gradients.
```

**Every background image:**
```
Simple hand-drawn doodle {SETTING} background, MS-Paint-like style:
flat {PALETTE} colors, thick black outlines, wavy hand-drawn lines,
completely EMPTY in the middle. No text.
```

❌ Forbidden words: `cinematic` `moody` `painterly` `film grain` `dark palette`
✅ Rule: generate image 1 → accept it → pass it as the reference image
   for EVERY later generation.

## 2. Script — the 5 acts (repeat per chapter)

THE MYTH → THE DOUBT ("most people assumed it was just a story") →
THE DIG (real evidence) → THE EXPLANATION (diagram) → THE KICKER
("this is likely how the story spread").

## 3. Generate — max 10 images per turn

```bash
python3 skills/image-batcher/scripts/batch_images.py init my-video --prompts prompts.txt
# then: generate 10 in parallel → mark 1..10 → commit → "send 'go'" for next 10
```

## 4. Motion — keyframes, not stills

```bash
python3 skills/ae-motion/scripts/ae_motion.py scene.json -o out.mp4
python3 skills/ae-motion/scripts/ae_motion.py --plan "the beat text"
```

Rules: cuts every 2–6 s · subjects centered · 60 fps · slide-ins with
easeOutExpo · label pops with easeOutBack · punch-in on the reveal ·
puppet-pin any body part that acts (tail, wings, limbs) · hand fonts.

## 5. Character does something? / missing a prop?

```bash
# walk / wave / blink: skills/character-animation-skill
# missing prop: fetch one CC0 file (never clone, never commit assets)
python3 skills/asset-library/scripts/asset_fetch.py search dragon
python3 skills/asset-library/scripts/asset_fetch.py get kenney "<path>" --out assets
```

## 6. Audio + assembly

Voiceover → music bed −26 dB under voice → 0.7 s pause between chapters →
final loudness −23 dB → hard cuts, no transitions, no captions.

## 7. Verify

```bash
python3 skills/video-polish/scripts/script_doctor.py script.md
python3 skills/video-polish/scripts/audio_report.py final.mp4
python3 skills/video-polish/scripts/qa_pacing.py final.mp4
```

## Full worked example (copy it)

`references/worked-example.md` — a complete Minotaur chapter: 10 exact
prompts + per-beat motion.

## If in doubt

Read `CLAUDE.md` (style rules) and `references/paint-explainer-autopsy.md`
(the measured numbers). The reference style is The Paint Explainer —
hand-drawn, bright, fast cuts. NOT cinematic, NOT dark, NOT static stills.
