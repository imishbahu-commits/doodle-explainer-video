---
name: expressive-doodle-acting
description: Direct elite-level acting for original hand-drawn explainer characters: identity-locked model sheets, silhouette-first poses, face/body deformation, overlap and follow-through, narration-aligned acting beats, motivated camera accents, renderer selection, and deterministic re-inking of generated assets. Use when characters must perform, react, emote, gesture, deform, or move cinematically rather than remain in the measured locked-camera Paint Explainer profile.
---

# Expressive Doodle Acting

This skill owns **performance direction**. It does not replace the renderer. It
turns story intent into drawable poses, timed acting beats, rig/layer requirements,
secondary motion and a justified camera plan, then hands those decisions to
`ae-motion`, HyperFrames, or exceptional frame-by-frame animation.

Read `references/acting-grammar.md` and `references/asset-workflow.md` before a new
character pipeline. Research/adoption decisions are in `references/github-research.md`.

## Profile boundary

This is a separate opt-in mode. The measured Paint Explainer profile remains
locked-camera and sparse-motion unless the user explicitly requests expressive
acting. Never silently mix this profile into corpus-faithful recreation.

Even in expressive mode:

- story clarity beats motion quantity;
- original design beats creator imitation;
- holds remain animation;
- camera accents performance but does not manufacture it;
- character identity is stricter than smoothness;
- a strong replacement drawing beats a badly warped neutral pose.

## Required inputs

Before animation, obtain or author:

1. approved narration and word timings;
2. shot story function and emotional turn;
3. character bible validated against `schemas/character-bible.schema.json`;
4. accepted model-sheet masters and semantic RGBA layers;
5. target renderer and shot duration.

If no character bible exists, stop and build it. Do not generate unrelated poses
one prompt at a time.

## Character bible gate

Record at minimum:

- head/body ratio and stable skull mass;
- three silhouette words and one deliberate asymmetry;
- hairline and outer hair silhouette;
- eyes, nose and mouth construction rules;
- costume anchors and flat palette;
- front, profile and three-quarter views;
- six facial expressions including transitional shapes;
- eight silhouette-distinct body poses;
- hand/prop vocabulary;
- layer order, pivots and deformable parts;
- five or more identity locks that no generation/edit may change.

A recurring character needs a model sheet, not merely a prompt.

## Shot-direction procedure

### 1. State the turn

Write one sentence:

> The character begins thinking/feeling **A**, perceives **B**, and ends in **C**.

If the shot has no turn, use a held explanatory pose or remove the character.

### 2. Stage the eyeline and silhouette

Choose subject placement, look direction, negative space and prop location. Draw
the starting and ending silhouettes as filled shapes. Both must read at 10–15% size.
Fix staging before facial detail.

### 3. Choose golden poses

Usually author 2–4 intentional drawings:

- starting thought;
- anticipation/breakdown if needed;
- emotional/action extreme;
- final settled thought.

Mark which states are transforms of one drawing and which require replacement art.
Do not ask a mesh to invent anatomy or perspective.

### 4. Build the acting beat

Use the hierarchy:

`thought → eyes → head → torso → limb chain → hand/prop → hair/clothing`

Author times against emphasized words. Give the extreme and final thought readable
holds. Use anticipation, overshoot and settle only when the action/material calls
for them. Never auto-return to neutral.

### 5. Select the smallest renderer

| Need | Method |
|---|---|
| face, hand or silhouette changes materially | pose/source swap |
| rigid head/limb/prop movement | layered transform keys in `ae-motion` |
| local bend in hair, jaw, sleeve, tail | 2–4 MLS puppet pins in `ae-motion` |
| camera/reframe/mask/path with browser diagnostics | HyperFrames subset |
| complex run, fall, fight or physical comedy | authored frame sequence / `character-animation-skill` |
| close-up hero acting | hybrid replacement drawings + local keys |

AI sprite generation is an exception. Inspect every frame for identity drift; fewer
strong authored poses are preferred to many inconsistent in-betweens.

### 6. Motivate the camera

Every non-locked camera entry must contain a written story motivation.

| Move | Valid use | Starting envelope |
|---|---|---|
| punch-in | realization, threat, decisive detail | +8–18%, 6–16 frames |
| pull-back | isolation, consequence, reveal scale | −8–20%, 20–45 frames |
| pan/reframe | reveal offscreen cause or preserve geography | shortest readable path |
| impact bump | collision or comic shock | 2–4 frames, settle immediately |
| character follow | movement would otherwise leave staging | follow once, then lock |

Cut instead of moving when the new composition is the point. Avoid perpetual zoom,
floating parallax, random shake and simultaneous camera/character accents that fight.

### 7. Write and validate the shot contract

Create a JSON shot using `schemas/acting-shot.schema.json`. It must name:

- story function and line of action;
- characters, rigs, screen sides and eye lines;
- timed poses, expressions, lead/overlap parts and holds;
- accent word when synchronized to narration;
- camera move and motivation;
- render method.

See `examples/reaction-shot.json`.

### 8. Render proof, not polish

First render only the start, anticipation, extreme and settle. Review as:

- four-frame contact sheet;
- black silhouettes;
- full-speed motion;
- muted clip (acting must still read);
- audio-only timing check;
- 10–15% thumbnail view.

Only then add breakdowns, overlap, line cleanup and final camera interpolation.

## Generated-art acquisition and re-inking

Image generators should produce controlled **construction candidates**, not final
ink. Ask for one view, flat background, clean regions, invariant identity details,
full unclipped body and no lighting/texture/text. Generate a model sheet first and
use accepted masters as edit references.

Reject malformed anatomy and identity drift before processing. The repository can
then remove generator softness and faux texture with its deterministic re-inker:

```bash
python3 skills/expressive-doodle-acting/scripts/handdrawnize.py \
  input.png output.png --line-art output-ink.png \
  --colors 10 --line-width 4 --wobble 1.35 --seed 17 \
  --report qc/output-handdrawn.json
```

This yields flat fills, a single near-black imperfect contour, transparent output,
optional ink-only art and QC metrics. Keep one seed/parameter family per character.
Run `transparent-asset-prep` first when source alpha is bad and run
`paint-style-qc` afterward when the target shares the repository paint language.

A filter cannot turn wrong design into great drawing. Hero poses, close-ups, hands
and thumbnails should receive a manual redraw over the approved construction when
quality matters most. Never claim digitally filtered art was physically drawn.

## Facial acting system

Build expressions as coordinated sets, not isolated mouths:

- eye aperture/direction;
- brow height, angle and asymmetry;
- cheek compression;
- jaw translation/rotation;
- mouth shape;
- head squash/stretch;
- neck/head angle;
- hair silhouette response.

Use a replacement face/head when perspective or construction changes. For dialogue,
animate thought accents and mouth groups sparingly; phoneme-perfect lip-sync is not
a substitute for acting.

## Body mechanics

- Establish support foot/seat and center of mass.
- Lead gestures from clavicle/shoulder, then elbow, then wrist/hand.
- Move limbs on arcs unless an external constraint demands a straight path.
- Use asymmetry; mirrored limbs flatten personality.
- Compress before explosive expansion.
- Let heavy characters accelerate and settle longer than light characters.
- Keep hands readable and uncluttered at the final delivery pose.
- Preserve screen direction unless a deliberate crossing is staged.

## Hair, clothing and props

Root is constrained; middle follows; tip overlaps and settles last. Use separate
layers or 2–4 semantic puppet pins. Secondary action must not peak on the same frame
as every primary part. Stop it after the thought lands—never add endless idle sway.

Props must have weight and contact: establish grip, pivot, drag/lead relationship,
and a reaction in the body. A floating prop is an acting failure.

## Quality gates

Reject a shot when any is true:

- emotional turn is unclear with audio muted;
- silhouette or eyeline fails at thumbnail size;
- adjacent poses differ only in mouth/eyebrows;
- all parts start/stop together;
- feet slide or body lacks support;
- deformation changes identity or invents anatomy;
- hair/cloth moves before its driver without cause;
- generated frames change skull, costume, proportions or line language;
- camera move has no written story motivation;
- camera and actor compete for the same accent;
- action returns automatically to neutral;
- excessive smoothing erases drawn pose contrast;
- re-ink has double contours, noisy interior edges or alpha fringe.

## Deliverables

```text
projects/SLUG/
  characters/NAME/character-bible.json
  characters/NAME/model-sheet.png
  characters/NAME/expressions/
  characters/NAME/hands/
  characters/NAME/rig.json
  assets/source/
  assets/reinked/
  scenes/SHOT/acting-shot.json
  scenes/SHOT/blocking-proof.mp4
  scenes/SHOT/final.mp4
  qc/*-handdrawn.json
  qc/*-acting-review.md
```

Preserve source generations, accepted masters, re-ink settings and shot contracts.
Do not keep large disposable frame caches in Git.
