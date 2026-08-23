---
name: handdrawn-style-lock
description: Locks the measured Paint Explainer art language across generated and local assets: near-black single-pass imperfect contours, flat character fills, restrained mode-specific palettes, simple illustrated world plates, and a persistent white chapter-title strip. Use for every subject, prop, diagram, and background; style_rules.json overrides generic prompt defaults.
---

# Hand-drawn style lock

Authority: `references/paint-explainer-analysis-4v/style_rules.json`.

## Measured visual grammar

- Ink: near-black `#101010`, rounded/hand-rounded joins.
- Typical stroke: ~2 px at 640-wide source, ~6 px at 1920 production.
  Environment-heavy variants may reach ~12 px at 1920.
- Contour: one clean imperfect pass, never multi-pass sketch scribble.
- Character/prop fill: flat color. Gradients are reserved for sky/water/world
  plates and occasional soft gray host-head modeling.
- Subject width is typically ~25–65% of frame.
- Ink centroid is usually around x=50%, y=54–58%.
- White-mode negative space is typically ~35–70%.
- Every chapter carries a white ~10%-height top strip with centered black
  uppercase hand-lettered display text for the entire chapter.

## Subject master prompt

Use white only as a removable acquisition background; final subjects should be
clean RGBA PNGs.

```text
Hand-drawn doodle illustration of {SUBJECT}, isolated on pure white.
Paint Explainer language: single clean slightly imperfect near-black contour,
rounded joins, flat restrained colors from {MODE_PALETTE}, simple readable
silhouette, {SPECIFIC_DETAILS}. No scenery, cast shadow, texture, gradient,
photorealism, 3D rendering, cinematic lighting, or embedded text.
```

Rules:

1. Prefer one independently animatable subject/prop per master.
2. Preserve design and line weight from the accepted reference image.
3. Add titles/labels as deterministic editor layers when practical.
4. Pass masters through `transparent-asset-prep`, then `paint-style-qc image`.
5. Mood may change the expression; it may not change the rendering language.

## World-plate prompt

The measured newest mode is **not pure white everywhere**. It uses fully
illustrated environmental plates under the persistent white title strip.

```text
Simple hand-drawn {SETTING} world plate in Paint Explainer language,
near-black clean imperfect contours, restrained {MODE_PALETTE}, simple readable
depth bands, clear staging space for {SUBJECTS}. No embedded labels, cast
shadows, photographic texture, 3D rendering, lens effects, or cinematic light.
Leave the top 10% clear for a white chapter-title strip.
```

Backgrounds and subjects must share contour weight and palette family. A
subtle plate gradient is allowed only for sky/water/world depth; do not put
gradients on ordinary character fills.

## Mode palettes

Use the machine rules exactly; do not reduce every scene to generic primaries.

| Mode | Production palette |
|---|---|
| Core | `#F0F0F0`, `#101010` |
| Newest sea world | `#30D0F0`, `#1090F0`, `#1070D0`, `#105090`, `#103050`, `#707050` |
| White history | `#B09070`, `#909070`, `#B0B0B0`, `#707070` |
| Incident listicle | `#F0D0B0`, `#D0B090`, `#909090`, `#505050` |
| Emphasis only | red `#E31B23`, yellow `#F0D010` |

Keep any one object simple; a world plate may use the full mode family.

## Consistency lock

1. Approve one subject and one world plate for the selected mode.
2. Supply those references to every later generation where supported.
3. Record palette, production stroke width, title treatment, and recurring
   character proportions in the project ledger.
4. Reject drift immediately; never average incompatible generations together.

## Automatic gates

```bash
python3 skills/transparent-asset-prep/scripts/prepare_asset.py in.png out.png \
  --mode auto --report qc/out-alpha.json
python3 skills/paint-style-qc/scripts/paint_style_qc.py image out.png \
  --kind subject --json qc/out-style.json
```

Also inspect at 100% and 200% scale for a fringe wider than ~1–2 output pixels,
line doubling, tiny accidental marks, malformed text, and inconsistent anatomy.
