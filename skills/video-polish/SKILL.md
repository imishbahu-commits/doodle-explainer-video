---
name: video-polish
description: Quality-check Paint Explainer scripts, narration/mix, and finished edits. Measures structure, EBU R128 loudness, chapter breaths, and cut cadence, then hands repository-specific style enforcement to paint-style-qc. Use after writing, after voice/mix, and after final assembly.
---

# Video polish — measured quality gates

Authority: `references/paint-explainer-analysis-4v/style_rules.json` overrides
older `references/format-spec.md` targets where they conflict.

## Gate 1 — script

```bash
python3 skills/video-polish/scripts/script_doctor.py projects/SLUG/script.md
```

Review hook, promise, re-hook, sources, rhythm, TTS numbers, and word budget.
For the current target, plan **204–209 recognized WPM**, 12 chapters per
reference-length video, ~68.5 s median chapter, and a ~0.6–0.8 s breath at a
chapter boundary. Narrative formulas are aids, not license to add generic
captions or visual effects.

## Gate 2 — voice and final mix

```bash
python3 skills/video-polish/scripts/audio_report.py projects/SLUG/final.mp4 --json
```

Current master targets:

- integrated loudness: **−20.7 to −20.6 LUFS**;
- true peak: **≤−2.3 dBTP**;
- LRA: **1.8–3.8 LU**;
- chapter breath: **~0.6–0.8 s**.

The measured format includes a continuous low electronic/ambient bed under the
narration. Keep it subordinate. Use sparse semantic SFX only; do not add a
whoosh to every cut.

`--tighten` is diagnostic and potentially destructive. Never run it blindly on
a final mix: it may remove intentional chapter breaths or alter alignment.
Re-measure and resync after any use.

## Gate 3 — final edit cadence

```bash
python3 skills/video-polish/scripts/qa_pacing.py projects/SLUG/final.mp4 \
  --manifest projects/SLUG/manifest.json --json
```

Target envelope:

- median shot: 2.3–3.1 s (corpus 2.7667 s; newest target 2.50 s);
- mean shot: ~3.4–4.1 s;
- ~13.61% may be under 1 s and ~6.51% may exceed 10 s;
- verified transitions: 65.52% full-frame hard cut, 29.85% same-palette hard
  cut, 4.64% localized one-frame swap/pop, 0% verified dissolve/fade;
- visual event median: ~0.050 s before nearest word onset.

A beat is not necessarily a cut. Manifest comparison reports both beat count
and explicit visual-event count where available; intentional holds/reuse are
valid.

## Gate 4 — repository-specific style

Run `paint-style-qc` on images, ae-motion scenes, and final metrics. Also inspect:

- persistent white ~10%-height chapter title strip;
- locked camera, no generic Ken Burns moves;
- 35–60% frozen shots;
- 0–3 moving local elements;
- no regular blink, lip-sync, idle breathe, captions, dissolve, or global zoom
  unless explicitly required and reference-supported.

## Rules

- These are checks, not restyles. Report first and change only supported faults.
- Music is measured and allowed; generic transition sounds/effects are not.
- No captions/subtitles unless the user asks.
- Re-run all affected gates after every fix and retain machine-readable reports.
