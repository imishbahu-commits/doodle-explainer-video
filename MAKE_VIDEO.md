# MAKE_VIDEO.md — measured Paint Explainer quick recipe

For full detail read `SKILL.md`, `skills/paint-explainer-recreation/SKILL.md`,
and `references/paint-explainer-analysis-4v/style_rules.json`.

## 1. Script and align

Use `youtube-script`, research every claim, write at the current 204–209 WPM
target, and retain final word-level timing. Mark ~0.6–0.8 s chapter breaths.

```bash
python3 skills/youtube-script/scripts/script_planner.py plan PROJECT "topic" \
  --duration 180 --format myth
python3 skills/video-polish/scripts/script_doctor.py projects/PROJECT/script.md
```

## 2. Plan visual states

Use `image-queue`. A spoken beat may hold or reuse the prior visual. Record only
semantic events: hard cut, source swap, or local action. Schedule justified
changes ~0.033–0.067 s before their keyword.

```bash
python3 skills/image-queue/scripts/queue.py classify PROJECT
python3 skills/image-queue/scripts/queue.py ai-prompts PROJECT
```

Generate only genuinely new masters, up to 10 pending AI assets in a turn. Do
not regenerate subjects/plates merely to avoid intentional reuse.

## 3. Lock and prepare art

Use the measured mode palette in `handdrawn-style-lock`: near-black `#101010`
single-pass contour, ~6 px at 1920, flat character fills, and gradients only on
world plates. Preserve a white top title strip ~10% of frame height.

```bash
python3 skills/transparent-asset-prep/scripts/prepare_asset.py in.png out.png \
  --mode auto --report qc/alpha.json
python3 skills/paint-style-qc/scripts/paint_style_qc.py image out.png \
  --kind subject --json qc/image.json
```

## 4. Render one composition

Use `ae-motion` for transparent PNG/MLS work:

```bash
python3 skills/paint-style-qc/scripts/paint_style_qc.py scene scene.json
python3 skills/ae-motion/scripts/ae_motion.py scene.json -o shot.mp4
```

Defaults: 30 fps timing, locked camera, `motion_blur: 1`, holds/cuts/source
swaps, and 0–3 moving local elements. No routine idle, blink, lip-sync, bounce,
parallax, zoom, pan, dissolve, or fade.

Use the selected HyperFrames core/keyframes/animation/CLI subset instead when a
deterministic browser composition and its diagnostics are more useful. Never
load generic creative/faceless presets.

## 5. Character action exception

Use `character-animation-skill` only for a genuinely repeated semantic action
that cannot be expressed by a pose swap, whole-layer translation, arm/prop
rotation, or 2–4-pin local deformation.

## 6. Assemble and mix

Hard-cut/source-swap on anticipated word timing. Preserve the persistent title
strip and chapter breaths. Use the measured low electronic/ambient bed and
sparse semantic SFX. Do not add captions unless requested.

Current master: **−20.7 to −20.6 LUFS, true peak ≤−2.3 dBTP, LRA 1.8–3.8 LU**.

## 7. Gate

```bash
python3 skills/video-polish/scripts/audio_report.py final.mp4 --json
python3 skills/video-polish/scripts/qa_pacing.py final.mp4 \
  --manifest manifest.json --json
python3 skills/paint-style-qc/scripts/paint_style_qc.py metrics \
  qc/final-metrics.json --json qc/final-style.json
```

Target median shot envelope: 2.3–3.1 s. Flattened local motion can resemble an
edit, so compare machine detection with the authored event manifest and spot
check frames.

## 8. Package

After all gates pass, use `youtube-seo` for title, description, chapters, tags,
and thumbnail brief. Its generic loudness/caption suggestions do not override
the measured production profile.
