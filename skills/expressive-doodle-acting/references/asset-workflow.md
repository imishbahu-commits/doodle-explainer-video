# Generated asset → authored doodle workflow

An image model is a concept and variation engine, not the final inker.

## Acquisition contract

Generate characters on a flat removable background with:

- one character and one view per image;
- full body, unclipped hands/feet and generous motion headroom;
- simple flat regions, near-black contour, no texture or lighting;
- explicit invariant list (head shape, hair silhouette, costume anchors, ratios);
- no embedded text, hatching, shadows, cinematic light or faux paper;
- a model sheet/contact sheet first, never isolated production frames first.

Reject anatomy and identity errors before post-processing. Re-inking cannot repair
wrong hands, changing clothes, a different skull or inconsistent perspective.

## Identity-lock order

1. Approve one neutral three-quarter master.
2. Create front/profile/back views as edits of that master.
3. Build expression and hand libraries as edits, changing only named parts.
4. Split accepted art into semantic RGBA layers.
5. Re-ink every layer with the same seed family, line width, ink and palette.
6. Register pivots and test neutral pose before authoring acting.

## Deterministic re-ink

```bash
python3 skills/expressive-doodle-acting/scripts/handdrawnize.py \
  generated.png assets/cutouts/hero.png \
  --line-art assets/ink/hero.png \
  --colors 10 --line-width 5 --wobble 1.35 --seed 17 \
  --report qc/hero-handdrawn.json
```

The tool:

1. median-simplifies generator noise;
2. quantizes fills into readable color regions;
3. extracts RGB and alpha-region contours;
4. applies low-frequency registration-safe contour irregularity;
5. produces one near-black variable-width ink pass;
6. preserves transparency and emits an ink-only layer plus QC metrics.

Tune by intent:

- too much interior noise → lower `--colors`, raise `--sensitivity`;
- missing meaningful boundaries → lower `--sensitivity`;
- sterile contour → increase `--wobble` slightly (normally ≤2 px at 1080p);
- doubled/muddy contour → lower `--line-width`; never add more passes;
- pale halo → prepare alpha first with `transparent-asset-prep`.

## Optional vector route

When true editable curves are needed, process the simplified PNG with VTracer and
then manually inspect/simplify paths. Vector tracing is not automatically more
hand-drawn: perfect curves look synthetic, while too many nodes preserve generator
noise. The approved raster re-ink remains the visual reference.

## Human pass

For hero close-ups and thumbnails, the highest-quality route remains a real manual
redraw over the approved construction:

- lower generated concept to 15–25% opacity;
- redraw silhouette and expression with one pressure-sensitive pass;
- correct tangencies, hand shapes and line weight;
- flat-fill beneath the ink;
- compare against the character bible at thumbnail and 200% size.

The automated tool handles production volume; manual redraw handles identity-critical
hero frames. Do not claim a filtered image was physically hand-drawn.
