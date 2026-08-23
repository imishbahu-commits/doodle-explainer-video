# GitHub research and adoption decision

Reviewed 2026-08-23. Links are references, not vendored dependencies.

## Strong projects examined

- [yemount/pose-animator](https://github.com/yemount/pose-animator) — excellent
  browser proof of skeletal deformation for authored SVG characters (Apache-2.0),
  but it is driven by PoseNet/FaceMesh and is not an acting-direction system.
- [Stretchy Studio](https://github.com/stretchy-studio/stretchy) — promising open
  2D rigging/editor workflow. It solves manipulation, not shot acting decisions,
  timing against narration, or this repository's art/QC contract.
- [mounika-v/Rigging-sketches-for-2D-character-animation](https://github.com/mounika-v/Rigging-sketches-for-2D-character-animation)
  — research prototype for sketch auto-rig initialization; old/heavy and not a
  production acting planner.
- [LingDong-/linedraw](https://github.com/LingDong-/linedraw) — useful contour and
  plotter-style vector extraction with optional sketch noise. It does not retain
  controlled flat fills or enforce character identity.
- [visioncortex/vtracer](https://github.com/visioncortex/vtracer) — strong modern
  raster-to-vector tracing, palette snapping and curve simplification. Recommended
  as an optional downstream SVG route, but not required by the core skill.
- [MarkMoHR/virtual_sketching](https://github.com/MarkMoHR/virtual_sketching) —
  high-quality SIGGRAPH vector line-art research, but model/runtime weight and its
  photograph-to-line focus make it unsuitable as the default production gate.
- [josephrocca/image-to-line-art-js](https://github.com/josephrocca/image-to-line-art-js)
  — accessible ONNX port of Informative Drawings. Good for photo line extraction,
  not enough for flat-color doodle reconstruction.
- [honzajavorek/cartoonist](https://github.com/honzajavorek/cartoonist) — valuable
  for cleaning photographs of actual drawings; not for generated layered assets.

## Decision

No reviewed repository combines all required responsibilities:

1. performance intent and readable posing;
2. narration-synchronized acting beats;
3. identity-locked character construction;
4. face/body deformation and secondary overlap;
5. motivated camera grammar;
6. generated-asset simplification and deterministic re-inking;
7. handoff to this repository's `ae-motion`, HyperFrames and QC stack.

Therefore this repository owns the direction/planning layer and a lightweight,
deterministic Pillow re-inking tool. Existing rendering engines remain responsible
for pixels and keyframes. External projects can be evaluated later behind explicit
adapters; none are copied here.
