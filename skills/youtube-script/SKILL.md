---
name: youtube-script
description: Write deep, interesting explainer scripts for ANY topic (or pick a topic when the user has none), in the measured Paint Explainer style: one spoken beat = one image, cuts every 2-6 s, myth/misconception/mystery/how-it-works/comparison/timeline/big-question formats, but-therefore seams, misconception-first research, and a ready handoff to image planning and YouTube SEO. Use for every new video at script stage (content-router stage 1).
---

# YouTube Script — any niche, deeper and more interesting

This skill produces the script every other stage feeds on. It works for any
topic the user gives, and picks a strong topic itself when none is given.

**The bar:** viewers must feel the next beat is worth staying for. That comes
from three things only — (1) a format with real tension, (2) but-therefore
seams instead of "and then", (3) concrete facts (numbers, names, dates, the
actual find, the actual paper) — never vague filler.

## 1. Intake (ask once, all questions in one message)

If any of these are missing, ask in ONE batch, never one by one:

1. Topic or niche (if none: use `references/topic-picker.md` and propose 3
   picks with a one-line pitch each, let the user tap one)
2. Format (offer the best match from `references/formats.md`; default to the
   match, allow override)
3. Length: ~1 min / ~3 min / ~8+ min
4. Audience age & language
5. Voiceover: will the user record it, or should the agent narrate?
   (If the user will record: script is written to be READ ALOUD — short
   sentences, no tongue twisters, pauses marked.)

## 2. Research — depth is mandatory, filler is banned

1. Gather facts with web search + page reading. Minimum 3 independent
   sources. Myths: find the earliest written source, the excavation/paper
   that matters, names and dates. Science: find the actual study, its year,
   authors, and the size of the effect.
2. Write a `research.md` in the project folder: one fact per line, each with
   its source link. Every claim in the script must trace to a line here.
3. Kill filler: any sentence that works in a different video gets cut.
4. Find the ONE curiosity gap per minute: the question the viewer asks just
   before the next beat answers it.

## 3. Draft the script

1. Pick the format (references/formats.md) and its act timings for the target
   length.
2. Write the hook using the hook table (contrarian / mystery / stakes /
   outcome / scale).
3. Fill the acts beat by beat. Rules:
   - **One spoken beat = one image.** Each beat is one sentence (max two short
     clauses), 2–6 s spoken (median ~3.6 s). Never let a beat run long to
     save images; a long beat is split into two beats, each with its own image.
   - **Seams:** every section boundary is "but" or "therefore" — written
     literally into the spoken text ("But then, in 1876…", "Therefore the
     real answer…").
   - **Misconception-first:** when the format allows, open with what the
     audience thinks is true, then break it.
   - **Palette cleanser** every ~60 s (visual gag, "let that sink in", or a
     0.7 s silence).
   - **Anti-subjective rule:** the `visual` field of every beat describes
     what is ON SCREEN (subject, action, camera move), never the emotion.
     Write "the cyclops' eye widens, head tilts back" — never "epic reveal".
     Forbidden in visuals: cinematic, moody, painterly, film grain, dark
     palettes, shadows, gradients, photorealism.
4. The final beat is the kicker: restate the hook's answer in one sentence +
   open one new curiosity gap (this is what earns the next video's click).

## 4. Beat schema (what every beat must contain)

```json
{
  "id": 7,
  "spoken": "But in 1876, Schliemann's diggers found something that should not exist.",
  "visual": "Hand-drawn doodle of a digger's trowel lifting a gold mask from dark soil outline, on a PURE WHITE background",
  "subject": "gold-mask",
  "transition": "cut",
  "duration": 3.8,
  "source_hint": "ai"
}
```

- `subject`: the recurring thing on screen (character / object / diagram).
  Repeated subjects across beats = rig + pose reuse = fewer new images.
- `transition`: `cut` | `revealing` (new subject enters) | `disappearing`
  (subject leaves) | `switching` (focus jumps A→B). Written explicitly so the
  image plan and motion stage never have to guess.
- `duration`: estimate; final durations come from the voiceover (step 6).

## 5. Turn beats into a plan

```bash
python3 scripts/script_planner.py plan PROJECT "topic" --duration 180 --format myth
```

This writes `projects/PROJECT/beats.json` with the beat math (beat count from
duration / 3.6 s) and a skeleton `script.md`. Fill the skeleton with the
draft, then hand `beats.json` to the image-queue skill (stage 2).

## 6. Fit to the voiceover (never stretch, never duplicate)

The script is approved, THEN the voiceover is recorded (or generated). The
voiceover is the boss:

- One voiceover segment = one beat. If the voiceover has more segments than
  beats → **new beats are inserted, each needing its own image** (the image
  queue grows; the rule "1 beat = 1 image" is never bent).
- If it has fewer → beats merge, images in hand cover more beats.
- Re-fit durations:

```bash
python3 scripts/script_planner.py fit PROJECT --segments vo_segments.txt
```

Each segment stays inside 2–6 s. A 60 s voiceover ≈ 17 beats; 3 min ≈ 50;
8 min ≈ 133. Long videos are solved by BEAT MATH, not by stretching images.

## 7. Hand off

- Stage 2 (images): `beats.json` → image-queue skill — it classifies every
  beat as doodle / asset / pose-reuse / ai, so only genuinely new subjects
  cost an AI generation (10 per turn, ledger resumable).
- SEO: when the script is approved, load `youtube-seo` → `youtube-seo-optimize`
  and `youtube-seo-keywords`: title variants (Browse vs Search), entity-rich
  description, tags, chapters, the 15-second hook line, thumbnail concept.

## 8. Self-check before the script leaves this skill

- [ ] Hook + tension complete by second 30
- [ ] Every seam is "but" or "therefore"
- [ ] Every beat ≤ 6 s spoken, one image each, `visual` describes the screen
- [ ] Palette cleanser roughly every 60 s
- [ ] All claims trace to `research.md`
- [ ] Kicker answers the hook and opens a new gap
- [ ] `beats.json` exists and counts match the duration math
