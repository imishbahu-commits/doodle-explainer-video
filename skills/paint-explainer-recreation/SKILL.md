---
name: paint-explainer-recreation
description: Master production skill for recreating the measured Paint Explainer grammar with original scripts and artwork. Routes the existing script, image, keyframe, puppet, editing, QC, and SEO skills; optionally uses the vendored HyperFrames core/keyframe/animation/CLI skills. Enforces locked camera, noun-anticipated hard cuts, sparse local PNG motion, persistent chapter titles, measured pacing, and measured audio targets from the four-video corpus.
---

# Paint Explainer recreation — measured master skill

This is the authority for Paint Explainer-style production. It does not copy
reference drawings or scripts; it reproduces the measured visual/edit grammar
with original material.

## Read first

1. `references/paint-explainer-analysis-4v/STYLE_SPEC.md`
2. `references/paint-explainer-analysis-4v/style_rules.json`
3. `references/paint-explainer-analysis-4v/metrics/combined.json`

If another skill conflicts with these files, the measured corpus wins.

## Non-negotiable profile

- Camera locked: no default zoom, pan, follow, orbit, shake, or parallax.
- Visual event lands about **0.050 s before** its spoken keyword.
- Shot target: **2.50–2.80 s median**; 70.30% of shots in 1–6 s.
- Motion budget: **46.27% frozen / 40.83% active local / 11.72% subtle
  local / ≤1% whole-canvas slides**.
- Active shot changes only **1–3 local elements**.
- Hard cut or one-frame pose/source swap is the default transition.
- No routine lip sync, idle breathing, blinking, motion blur, captions,
  dissolves, or Ken Burns movement.
- Persistent white chapter strip: top ~10% of frame.
- Current voice target: **204–209 WPM**.
- Current master target: **−20.7 to −20.6 LUFS**, ≤−2.3 dBTP, LRA 1.8–3.8 LU.

## Required skill stack (the approved 1–9)

| Stage | Skill | Job |
|---|---|---|
| 0 | `content-router` | choose the current production stage only |
| 1 | `youtube-script` | original 12-chapter narration + spoken beats |
| 2 | `image-queue` | assign every beat a visual state and asset source |
| 3 | `handdrawn-style-lock` | lock line, palette, character, and world-plate grammar |
| 3a | `handdrawn-code` | diagrams, maps, arrows, labels, simple props |
| 4 | `ae-motion` | PNG tracks and MLS puppet pins |
| 4a | `character-animation-skill` | only a genuinely repeated character action |
| 5 | `video-polish` | script, timing, pacing, and audio gates |
| 6 | `youtube-seo` | packaging after the final video passes QC |

Supporting approved skills:

- `transparent-asset-prep` — produce clean transparent subject/part PNGs only
  when a generated asset is not already transparent.
- `paint-style-qc` — measured image, scene-manifest, and final-video gates.
- `hyperframes-core`, `hyperframes-keyframes`, `hyperframes-animation`,
  `hyperframes-cli` — optional deterministic browser renderer/validator.

## Renderer decision

### Use `ae-motion` by default when

- the scene is PNG layers;
- a tail, fin, jaw, arm, or soft body needs 2–4 MLS pins;
- no browser stack is needed;
- the scene is a locked plate with local layer tracks.

### Use HyperFrames when

- an agent-authored HTML composition benefits from live browser preview;
- keyframe diagnostics, lint/check/snapshot, or reusable HTML components matter;
- SVG, GSAP, Lottie, or a custom Canvas/Pixi mesh is required;
- rendering must be called through a deterministic CLI/API.

HyperFrames generic animation recipes do **not** override this profile. Select
only hold/step, local translation, local rotation, opacity, and restrained
scale keys. Never select generic camera journeys, dissolves, captions, grain,
ambient breathing, or spring-heavy presets for this style.

## Production contract

Each project writes these artifacts:

```text
projects/<slug>/
├── script.md
├── beats.json                 # words + timing + visual state per beat
├── style.json                 # palette, title, stroke, character IDs
├── assets/
│   ├── worlds/                # reusable fixed plates
│   ├── characters/            # transparent masters + pose/source swaps
│   ├── props/
│   └── labels/
├── scenes/                    # ae-motion JSON or HyperFrames compositions
├── audio/
├── qc/
│   ├── image-report.json
│   ├── scene-report.json
│   └── final-report.json
└── final.mp4
```

## Workflow

1. **Script:** write 12 chapters and spoken clauses. Align the final narration;
   every visual event is scheduled at keyword start minus 0.050 s.
2. **Visual-state plan:** one beat means one visual state, not necessarily one
   new full-frame image. A world plate and established character may be reused;
   change the pose, prop, label, or effect required by the clause.
3. **Art lock:** choose white void, simple plate, or illustrated environment by
   topic. Characters retain flat fills; gradients stay on world plates.
4. **Asset prep:** run `transparent-asset-prep` only when an image is not
   already alpha-clean. Keep source masters immutable.
5. **Motion:** default to hold or hard source swap. Animate only the semantic
   local element. Keep whole-scene camera scale at 1.0.
6. **Assembly:** preserve the 0.60–0.80 s chapter breaths and restrained ambient
   bed. Do not use automatic silence deletion on the final timeline.
7. **QC:** run `paint-style-qc` and `video-polish`; repair failures, rerender,
   and rerun both gates.
8. **Package:** trigger `youtube-seo` only after QC passes.

## Stop conditions

Stop rather than improvising when:

- a chapter has no approved narration;
- a generated character lacks a stable master design;
- more than three elements animate without narrative need;
- a generic skill proposes a camera zoom, caption, dissolve, or idle loop;
- audio or cut metrics miss the measured target;
- the result uses copied reference art rather than original assets.
