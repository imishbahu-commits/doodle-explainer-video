# ✅ PROVEN PROMPTS — exact reference-style image generation

These prompts produced **visually verified** ditto-style images of the channel
(2026-09-02 run, projects/dumbest-wars + revenge-first-part).

**Golden rule:** ALWAYS pass an image reference from `style_locked_crops/`
(primary: `ref_blackbeard_char.png`). Never generate from text alone.

---

## 1. BASE TEMPLATE (fill SCENE)

```
Recreate this EXACT drawing style from the reference image: flat 2D doodle
cartoon on solid white background, one small character centered, giant
oversized cartoon head with thick black outline and flat pale beige face,
tiny simple dot eyes, thin black stick-figure legs, flat colors only, no
shading or gradients, no engraving, no photo. SCENE: <ONE king/queen/creature
+ ONE simple prop or ONE other figure on one flat ground strip>. A flat
tan-brown ground strip runs along the bottom with a wavy black outline. Thin
black title bar strip across the very top of the image, empty, no text.
```

**Comedy-friendly scene add-ons that still pass:** angry brows + frown (deadpan),
tug-of-war between two figures, smug animal looking back, stick man covered in
goo with only eyes visible, tiny cannon, crossed arms + raised eyebrow.

---

## 2. 7 FAILURE SIGNATURES (check BEFORE using an image)

| # | Signature | Fix |
|---|---|---|
| 1 | Eyes small/oval with white glint | regenerate; add `tiny simple DOT eyes, NO white highlights` |
| 2 | Thick/shaped body instead of sticks | regenerate; add `thin black stick-figure legs, stick arms` |
| 3 | Gradients / shadows / hatching / engraving / photo | regenerate; add `flat colors only, no shading or gradients` |
| 4 | Any text/letters in image | regenerate; keep `empty, no text` AND avoid labels |
| 5 | Hands/feet drawn when reference omits them | regenerate; add `hands and feet usually omitted` |
| 6 | Busy/detailed background | regenerate; add `simple background, 35-70% empty white space` |
| 7 | Multiple figures overwhelm | split into separate beats; ONE subject + ONE prop |

---

## 3. WHAT *NOT* TO PROMPT (moderation + drift traps)

- ❌ blood, gore, corpses, impalement, weapons striking people (blocked)
- ❌ "engraving", "ink", "vintage illustration", "history book", "painting"
  (produces the WRONG style — the channel is flat doodle, NOT engraving)
- ❌ "3D", "realistic", "texture", "watercolor", "pencil shading"
- ❌ "cinematic camera", "zoom", "depth of field" (style is locked camera)
- ✅ safe euphemisms: `black crown lying on ground`, `empty goblet`, `red X`,
  `hourglass`, `grim reaper with skull shaped head`, `long sticks` instead of
  guns, `brown sticky wave`, `cannon aimed at shop`

---

## 4. VOICE-OVER REUSE

`tools/kokoro_tts.py` is committed; the ONNX model + `voices.npz` are re-fetched
from npm (`expo-kokoro`) per STYLE_DNA_KIT.md §5. Voice `am_michael` (warm
male narrator); alternates `am_onyx` (deeper), `am_adam`, `am_fenrir`,
`am_puck`, `am_liam`, `bm_george` (British). Command:
```bash
python tools/kokoro_tts.py "text" -o out.wav -v am_michael -s 1.05
```
