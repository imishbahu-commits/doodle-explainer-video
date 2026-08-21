---
name: ae-motion
description: Measured Paint Explainer keyframe renderer for transparent hand-drawn PNG layers. Implements per-property position, scale, rotation, opacity, hold/source-swap, and MLS puppet-pin tracks. Defaults to locked camera, crisp holds, noun-anticipated cuts, no blur, and only 1–3 moving local elements.
---

# AE Motion — measured PNG and puppet renderer

`scripts/ae_motion.py` renders layers directly with Pillow and uses OpenCV for
rigid MLS puppet deformation. It supports AE-like independent tracks and cubic
Bezier easing without requiring After Effects.

Authority: `references/paint-explainer-analysis-4v/style_rules.json`.

## Measured defaults

- `fps: 30` (source timing baseline);
- `motion_blur: 1` (off/crisp);
- no camera/global transform track;
- still holds and hard step/source swaps are first-class;
- only 1–3 local elements move in an active shot;
- visual event normally lands ~0.033–0.067 s before word onset;
- no idle breathe, automatic blink, lip-sync, perpetual loop, bounce,
  parallax, or routine entrance;
- no whole-scene pan/zoom/orbit/shake.

## Scene JSON

```json
{
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "duration": 3.0,
  "background": "assets/worlds/sea.png",
  "motion_blur": 1,
  "layers": [
    {
      "type": "image",
      "name": "fish-body",
      "src": "assets/cutouts/fish.png",
      "tracks": {
        "pos": [
          {"t": 0.0, "v": [960, 610], "e": "hold"},
          {"t": 3.0, "v": [960, 610], "e": "hold"}
        ]
      }
    },
    {
      "type": "image",
      "name": "fish-fin",
      "src": "assets/cutouts/fin.png",
      "tracks": {
        "rot": [
          {"t": 0.0, "v": 0, "e": "hold"},
          {"t": 0.35, "v": 22, "e": "easeInOut"},
          {"t": 0.55, "v": 22, "e": "hold"}
        ]
      }
    }
  ]
}
```

`e: "hold"` means no interpolation from the previous key. Position values are
layer-anchor coordinates; the default anchor is center.

## Puppet pins

A layer may define:

```json
{
  "puppet": {
    "pins": [[120, 80], [200, 90], [280, 100]],
    "drag": [2],
    "tracks": {
      "drag0": [
        {"t": 0.0, "v": [0, 0], "e": "hold"},
        {"t": 0.4, "v": [0, 30], "e": "easeInOut"},
        {"t": 0.8, "v": [0, 30], "e": "hold"}
      ]
    }
  }
}
```

Use 2–4 semantic pins on a tail, fin, jaw, arm, or flexible prop. Do not
whole-body-puppet a still merely to keep it moving.

## Move planner

```bash
python3 skills/ae-motion/scripts/ae_motion.py --plan "Forty eight percent survived."
```

The planner is intentionally conservative:

| Narration function | Recommendation |
|---|---|
| new noun, place, statistic, or state | hard cut/source swap 1–2 frames early |
| semantic body action | one named local part motion, then hold |
| negation | semantic source swap or one local X |
| list progression | hard cut/source swap; do not auto-stagger |
| default | preserve the hold; no invented motion |

The engine retains additional easing/move capabilities for explicit exceptions,
but their existence does not make them style defaults.

## Fonts and title strip

The shipped OFL fonts are `hand` (Caveat), `hand-note` (Patrick Hand), and
`hand-bold` (Kalam). Use centered uppercase hand lettering for the chapter
title on a white strip occupying ~10% of frame height. Keep it fixed for the
full chapter. Labels are sparse semantic elements, not subtitles.

## Render and gate

```bash
python3 skills/ae-motion/scripts/ae_motion.py scene.json -o out.mp4
python3 skills/paint-style-qc/scripts/paint_style_qc.py scene scene.json \
  --json qc/scene.json
```

Verify rendered event frames against aligned word onsets and manually inspect
alpha edges at 100%/200% scale.

## Renderer boundary

Choose this renderer for transparent-PNG compositing and MLS puppet work.
Choose the vendored HyperFrames core/keyframes/animation/CLI subset for
browser-authored HTML/CSS composition, diagnostics, preview, and snapshots.
Neither renderer may import generic creative presets over the measured profile.
