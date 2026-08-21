# MASTER STYLE SPEC — the 5 reference videos (deep analysis)

> Synthesized from the 5 user reference videos (style-reports/*.json + *.md
> + frames/). THIS IS THE AUTHORITY for recreating their exact style.
> Every rule below is measured, not guessed.

## The 5 references (all analyzed automatically by tools/style_lab.py)

| ID | File | Duration | fps | Res | Shots | Median cut | Frozen | Character |
|----|------|----------|-----|-----|-------|-----------|--------|-----------|
| 15223 | mt2y1cnbtb50hv_15223.mp4 | 8:03 | 30 | 640x360 | 116 | 3.33s | 77% | 23% |
| 15227 | mt2y6iljtmfnqd_15227.mp4 | 17:48 | 24 | 640x360 | 247 | 3.00s | 64% | 36% |
| 15231 | mt2yh0ycuclldu_15231.mp4 | 33:39 | 24 | 640x360 | 458 | 3.33s | 70% | 30% |
| 15235 | mt2yfginjiqavc_15235.mp4 | 15:24 | 24 | 640x360 | 222 | 3.00s | 66% | 34% |
| 15239 | mt2yg8bw0j6dzx_15239.mp4 | 9:32 | 24 | 640x360 | 138 | 3.33s | 67% | 33% |

Avg colors (background mood): 15223 rgb(176,173,170) · 15227 rgb(129,149,124)
· 15231 rgb(184,181,179) · 15235 rgb(132,135,113) · 15239 rgb(163,167,132)
→ muted, desaturated, warm-grey / sage / olive. Brightness 131–151 (medium).

## THE STYLE RULES (exact numbers to recreate)

### 1. Pacing / editing
- **Median shot length: 3.0–3.3 s.** Mean 4.2–4.3 s (right-skewed: some
  12–25 s holds). Min 0.33 s (quick stings). p25 ≈ 2.0 s, p75 ≈ 5.3–5.7 s.
- **Hard cuts only.** No dissolves, no wipes, no fade transitions
  (fade-to-black only at very end of a video).
- **Cut on the noun** — the picture changes when the spoken word lands.

### 2. Motion budget (the "restraint" look)
- **~65–77% of screen time = frozen frames** (nothing moves at all).
- **~23–36% = character motion only** (small puppet moves: limbs, tails,
  mouths, blinks — the subject animates IN PLACE).
- **~0% camera motion.** No zooms, no pans, no handheld. The camera is
  dead still. (This is THE defining trait — the opposite of Ken Burns.)

### 3. Composition & art
- 640×360 effective canvas (ours: 1376×768, upscale).
- Subjects centered or slightly low-center; large and simple; thick black
  outlines; flat fills; muted earthy palette (warm grey / sage / olive /
  cream); brightness medium (130–155/255); white or light backgrounds
  with occasional darker scenes.
- Simple backgrounds — often a flat colour or minimal scene; never busy.
- Characters: simplified humanoid/animal figures, dot or dash eyes, no
  lip-sync (mouth = held expression).

### 4. Sound
- Steady measured narration (TTS), no loud music, no big SFX moments.
  Loudness consistent ~−16 LUFS target.

## HOW TO RECREATE (implementation mapping for this repo)

1. **Script** → 12–16 words per beat, one beat = one shot (2.5–4 s spoken).
   Cut list = beats. Every chapter (~60–90 s) = ~20–25 shots.
2. **Art** → generate subject PNGs on white + painted flat-colour
   backgrounds (muted palette above), keyed with defringe.
3. **Motion** → THE DEFAULT IS FROZEN. Add ONLY in-place puppet pins
   (0.4–0.8 Hz sine drags on tail/limb/mouth) to ~30% of shots.
   ZERO camera moves. Hard cuts.
4. **Build** → use projects/dinzo-mammoth/keyframe_hunt.py or
   projects/dinzo-seahorse/build_seahorse.py pattern: per-beat scene
   JSON → ae-motion render at 60 fps → concat → loudnorm −16 + quiet bed.
5. **Verify** → tools/style_lab.py re-analyze output: target median
   3.0–3.3 s, frozen ≥ 60%, camera ≈ 0%.

Contact sheets per video: tools/style-reports/frames/<id>_contact.jpg
