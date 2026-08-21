---
name: content-router
description: Orchestrates the approved Paint Explainer production stack. Starts with the measured paint-explainer-recreation profile, routes script, visual-state planning, art, alpha prep, one of two deterministic renderers, QC, and SEO, and prevents generic creative presets from overriding style_rules.json.
---

# Content router — measured profile first

For Paint Explainer work, first load:

1. `skills/paint-explainer-recreation/SKILL.md`;
2. `references/paint-explainer-analysis-4v/style_rules.json`;
3. only the specialist needed for the current stage.

The machine rules are authoritative. Skills are capabilities, not permission to
apply their generic defaults.

## Approved stage map

| Stage | Trigger/state | Skill(s) | Required handoff |
|---|---|---|---|
| 0 Profile | any Paint Explainer request | `paint-explainer-recreation` | target mode + constraints |
| 1 Script | no approved narration/word times | `youtube-script`, then `video-polish` script gate | `script.md`, `beats.json`, word timings |
| 2 Visual states | narration exists, scenes do not | `image-queue` | visual-state/event ledger; holds/reuse explicit |
| 3 Art | missing subjects/plates/diagrams | `handdrawn-style-lock`; `handdrawn-code` for deterministic diagrams | accepted source masters |
| 3a Alpha | source subject lacks clean alpha | `transparent-asset-prep` | RGBA cutout + QC report |
| 4 Render selection | authored visual events exist | `ae-motion` **or** HyperFrames subset | scene/composition + deterministic render |
| 4b Repeated action exception | a recurring character action truly needs a sprite/rig | `character-animation-skill` | minimal sprite/parts; no routine idle/lip-sync |
| 5 Assembly | rendered shots + final mix | deterministic ffmpeg/editing tools | final master + event manifest |
| 6 QC | after art, scene authoring, or assembly | `paint-style-qc` plus `video-polish` | machine reports + repaired render |
| 7 Package | final is approved | `youtube-seo` | title, description, chapters, tags, thumbnail brief |
| 8 Done | all gates pass | none | delivery artifacts |

## Renderer decision

### Choose `ae-motion` when

- the scene is mostly transparent PNG layers;
- a named arm/prop/tail needs 2–4-pin MLS deformation;
- direct Pillow/OpenCV composition is simplest.

Defaults: 30 fps timing source, locked camera, `motion_blur: 1`, hard cuts and
hold/source-swap keys, 0–3 moving local elements.

### Choose the vendored HyperFrames subset when

- deterministic HTML/CSS layout is useful;
- keyframe diagnostics, browser preview, snapshotting, or CLI rendering help;
- the composition benefits from its seekable adapters.

Load only:

- `hyperframes-core`;
- `hyperframes-keyframes`;
- `hyperframes-animation`;
- `hyperframes-cli`.

Do not import generic HyperFrames creative/faceless presets. Its CLI/lint rules
supplement rather than replace `paint-style-qc`.

## Invariants passed to every stage

- camera locked; no routine zoom, pan, orbit, or parallax;
- hard noun/idea cuts/source swaps, normally ~0.033–0.067 s before word onset;
- persistent white chapter-title strip, ~10% of frame height;
- median shot target 2.3–3.1 s; ~35–60% frozen;
- no dissolve/fade by default;
- no regular idle, blink, lip-sync, or full walk rig;
- one clean imperfect near-black contour; mode-specific restrained palette;
- current narration 204–209 WPM;
- final mix −20.7 to −20.6 LUFS, true peak ≤−2.3 dBTP, LRA 1.8–3.8 LU;
- low ambient/electronic bed allowed; sparse semantic SFX only;
- no captions/subtitles unless requested.

## Routing rules

1. **Resume from artifacts.** Inspect `projects/SLUG/` before creating work.
2. **Do not equate beats with images/cuts.** Holds and reuse are intentional.
3. **Missing prerequisites stop the stage.** Do not animate unapproved art or
   time pictures to unaligned narration.
4. **Use the smallest renderer/capability set.** Character rigging and ML alpha
   removal are exceptions, not routine stages.
5. **Run QC incrementally.** Image gate after prep, scene gate before render,
   final metrics/audio gates after assembly.
6. **Repair measured violations, not taste.** Do not polish by adding motion,
   captions, transitions, or effects.
7. **Commit durable project artifacts.** Source masters, manifests, scenes, and
   reports are the cross-chat memory; generated caches are not.

## Example

A new sea-animal chapter routes as:

`paint-explainer-recreation` → `youtube-script` + word alignment →
`image-queue` state/event ledger → `handdrawn-style-lock` / `handdrawn-code` →
`transparent-asset-prep` only where alpha is missing → `ae-motion` for a local
fin action **or** HyperFrames for deterministic plate layout →
`paint-style-qc` + `video-polish` → `youtube-seo`.
