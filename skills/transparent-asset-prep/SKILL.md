---
name: transparent-asset-prep
description: Prepare clean transparent PNG subjects and optional character-part cutouts for Paint Explainer scenes. Uses fast border flood-fill for pure/flat backgrounds, falls back to the existing U2Net ML remover only when color separation fails, checks halos/cropping, and documents when SAM2/manual part separation is justified. Trigger only when a source asset lacks a clean alpha channel.
---

# Transparent asset preparation

Run this only when an asset is not already a clean transparent PNG. Preserve the
original under `assets/source/`; write prepared output under `assets/cutouts/`.

## Decision order

1. Existing alpha channel is clean → copy/crop only.
2. Pure white or flat corner-connected background → border flood-fill.
3. Subject/background colors overlap → existing U2Net fallback:
   `skills/character-animation-skill/scripts/remove_bg_ml.py`.
4. One flattened character must become separate head/arm/prop/tail parts → use
   SAM2/manual masks only for those named parts. Do not split every asset.

## Command

```bash
python3 skills/transparent-asset-prep/scripts/prepare_asset.py \
  input.png output.png --mode auto --pad 8 --report output.json
```

Modes:

- `auto` — preserve good alpha, otherwise flat flood-fill, otherwise ML.
- `flat` — force corner-connected background flood-fill.
- `ml` — force the existing U2Net tool.
- `alpha` — preserve alpha and crop/pad only.

## Acceptance gate

- output format RGBA PNG;
- at least 2% transparent pixels unless intentionally full-frame;
- subject does not touch output border after padding;
- opaque core remains present;
- no white/color fringe wider than ~1–2 output pixels;
- bounding box is not suspiciously tiny or the whole source frame.

Use `paint-style-qc image --kind subject` after preparation.

## Part separation

The measured style normally animates only 1–3 elements. Prefer authoring
separate source PNGs. If forced to split a flattened character, request only the
semantic parts needed by the shot, e.g.:

```text
body.png (fixed)
arm_sword.png (rotation child)
head_reaction.png (source swap)
tail.png (2–4 puppet pins)
```

SAM2 is optional and not vendored. A manual mask is preferable to an uncertain
automatic cut on a production master.
