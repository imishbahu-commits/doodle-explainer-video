---
name: youtube-script
description: Research and write original Paint Explainer narration for any topic, with sourced facts, but-therefore causality, 204–209 WPM current pacing, clause/beat timing, and a clean handoff to semantic visual-state planning. Spoken beats do not require unique images or cuts; style_rules.json controls editorial cadence.
---

# YouTube Script — sourced narration and timed semantic beats

This skill writes narration. `image-queue` decides whether each beat produces a
visual event, reuses a state, or holds. Never force a new image merely because a
sentence exists.

Authority: `references/paint-explainer-analysis-4v/style_rules.json`.

## Intake

Ask missing decisions together: topic/niche, best-matching format, target
runtime, audience/language, and whether the user or agent narrates. Supported
formats in `references/formats.md` include myth, misconception, mystery,
how-it-works, comparison, timeline, and big-question.

## Research

1. Use at least three independent credible sources.
2. Write `projects/SLUG/research.md`, one claim with its source per entry.
3. For history/myth, find earliest sources and consequential names/dates. For
   science, identify the actual study, year, authors, and effect/sample.
4. Remove any sentence that could be pasted into an unrelated script.
5. Design roughly one earned curiosity gap per minute.

## Draft

- Use concrete nouns, numbers, names, mechanisms, and consequences.
- Prefer but-therefore causality over an “and then” list.
- Open with the misconception/impossible fact where the format supports it.
- Write for speech: short readable clauses, deliberate chapter breaths.
- Current target is 204–209 recognized WPM.
- The reference-length structure uses 12 chapters with ~68.5 s median duration
  and ~0.6–0.8 s boundary breath; adapt chapter count to requested runtime.
- End by answering the hook and opening one relevant next question.

A spoken beat is a clause/sentence timing unit. Split it when clarity or word
alignment needs a boundary, **not** to manufacture image count. A beat may map
to `hold`, `hard_cut`, `source_swap`, or `local_motion` later.

## Beat schema

```json
{
  "id": 7,
  "spoken": "But in 1876, the diggers lifted a gold mask from the soil.",
  "duration": 3.1,
  "word_start": 42.267,
  "keywords": ["1876", "gold mask"],
  "visual": "Gold-mask excavation state; preserve chapter title.",
  "subject": "gold-mask",
  "event_type": "hard_cut",
  "event_time": 42.200,
  "visual_state_id": "dig-mask-01",
  "source_hint": "ai"
}
```

During drafting, timing/event fields may be null. After alignment:

- use final word timings, not character-count timing;
- schedule a justified picture change ~0.033–0.067 s before its keyword;
- use `event_type: hold` if the state should not change;
- do not write camera moves, emotion adjectives, cinematic lighting, or generic
  transitions into `visual`;
- preserve the chapter title across every state in that chapter.

## Plan skeleton

```bash
python3 skills/youtube-script/scripts/script_planner.py plan PROJECT "topic" \
  --duration 180 --format myth
```

The planner uses the measured ~2.7667 s editorial median only as a rough
initial row budget. It is not a mandate for a cut or new asset at each row.

## Fit the final voiceover

```bash
python3 skills/youtube-script/scripts/script_planner.py fit PROJECT \
  --segments vo_segments.txt
```

The voiceover is authoritative. Fitting updates/creates spoken timing rows; new
rows default to `hold` until semantic visual planning. It must not automatically
request another generated image. Preserve intentional chapter breaths and
recompute aligned word/event times after any audio edit.

## Handoff

- `beats.json` → `image-queue` for hold/reuse/source/event classification;
- approved narration + word timing → selected renderer;
- final approved master → `youtube-seo` for publishing metadata.

## Self-check

- [ ] claims trace to `research.md`;
- [ ] hook establishes a concrete gap/stake early;
- [ ] causal seams and chapter progression are clear;
- [ ] wording reads naturally at 204–209 WPM;
- [ ] beats are speech units, not forced image slots;
- [ ] visuals specify semantic on-screen state, never generic camera/effects;
- [ ] chapter breaths/titles are marked;
- [ ] final event timing waits for word alignment.
