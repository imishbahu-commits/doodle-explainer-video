---
name: paint-style-qc
description: Enforce the measured Paint Explainer profile on prepared images, ae-motion scene manifests, HyperFrames compositions, and final-video analysis reports. Checks title strip, near-black ink, palette restraint, clean alpha, locked camera, moving-layer count, motion blur, shot cadence, motion budget, word anticipation, WPM, and LUFS. Trigger after art preparation, after scene authoring, and after final assembly.
---

# Paint style QC

Authority:

- `references/paint-explainer-analysis-4v/STYLE_SPEC.md`
- `references/paint-explainer-analysis-4v/style_rules.json`

Run this in addition to `video-polish`, not instead of it.

## Gate A — image

```bash
python3 skills/paint-style-qc/scripts/paint_style_qc.py image subject.png \
  --kind subject --json qc/subject.json
```

Kinds:

- `subject`: clean alpha or flat white border, near-black ink, restrained fills.
- `background`: full plate permitted; no requirement for transparency.
- `frame`: checks the persistent ~10% white chapter-title strip.

## Gate B — ae-motion scene

```bash
python3 skills/paint-style-qc/scripts/paint_style_qc.py scene scene.json \
  --json qc/scene.json
```

Checks:

- camera track absent/locked;
- `motion_blur <= 1`;
- no more than three moving image/text layers without explicit override;
- source frame rate 30 by default;
- hold/step keys allowed and encouraged;
- no hidden global zoom/pan layer.

For HyperFrames, also run:

```bash
npx hyperframes lint
npx hyperframes check
npx hyperframes keyframes . --json
npx hyperframes snapshot
```

Then inspect the keyframe map: no camera journey, generic dissolve, captions,
ambient breathing, or infinite loop.

## Gate C — measured final report

Generate a metrics JSON with the corpus analyzer or equivalent, then:

```bash
python3 skills/paint-style-qc/scripts/paint_style_qc.py metrics \
  qc/final-metrics.json --json qc/final-style.json
```

Primary targets:

- median shot 2.3–3.1 s (current target 2.50–2.80);
- 35–60% frozen shots;
- no verified whole-scene zooms;
- visual events lead nearest words by roughly 0.033–0.067 s;
- 204–209 WPM for current mode;
- −20.7 to −20.6 LUFS, true peak ≤−2.3 dBTP, LRA 1.8–3.8 LU.

## Repair order

1. camera/motion violations;
2. noun timing and cut cadence;
3. title strip/composition;
4. line/palette/alpha;
5. voice and loudness.

Rerender and rerun every failed gate. Do not waive a failure by adding more
motion or effects.
