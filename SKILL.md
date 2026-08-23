---
name: doodle-explainer-video
description: Produce original faceless hand-drawn explainers using the measured four-video Paint Explainer profile: illustrated world plates, persistent chapter titles, locked camera, noun-anticipated hard cuts, sparse local PNG motion, controlled narration/mix, deterministic QC, and YouTube packaging.
---

# Doodle Explainer Video — measured Paint Explainer production

## Authority and target

Always begin with:

- `skills/paint-explainer-recreation/SKILL.md` — master production profile;
- `references/paint-explainer-analysis-4v/style_rules.json` — authoritative
  machine rules;
- `references/paint-explainer-analysis-4v/STYLE_SPEC.md` — human evidence and
  implementation specification;
- `skills/content-router/SKILL.md` — stage routing.

The rules were measured from four user-supplied videos: 98,705 frames,
3,290.167 s, 845 shots, and 841 abrupt edit events. When any generic skill
default conflicts, `style_rules.json` wins.

Primary target: the newest supplied sea-world version (2026-08-16), with its
slower voice, quieter mix, illustrated environments, and persistent title
strip. White-history, immersive-environment, and incident-listicle are named
secondary modes in the machine rules.

## Non-negotiable profile

| Dimension | Rule |
|---|---|
| Frame timing | 30 fps source timing, ±0.0333 s measured uncertainty |
| Edit cadence | 2.7667 s corpus median; production envelope 2.3–3.1 s |
| Word sync | picture change median ~0.050 s before nearest word; implement 1–2 frames early |
| Transitions | 65.52% full-frame hard cut, 29.85% same-palette hard cut, 4.64% local one-frame swap/pop, 0% verified dissolve/fade |
| Motion | ~46.27% frozen; ~40.83% active local; ~11.72% subtle local |
| Camera | locked; zero verified sustained zoom/pan-follow/orbit |
| Active parts | normally 1–3; pose swap, local translation, arm/prop rotation, or 2–4 pins |
| Idle | none by default; no routine blink, lip-sync, breathing, or walk cycle |
| Ink | near-black `#101010`; ~2 px at 640 width / ~6 px at 1920; clean imperfect contour |
| Composition | subject typically ~25–65% width; ink center x≈0.50, y≈0.54–0.58 |
| Chapter title | centered black uppercase hand lettering on white top ~10%; persists for full chapter |
| Voice | current mode 204–209 recognized WPM |
| Mix | −20.7 to −20.6 LUFS; true peak ≤−2.3 dBTP; LRA 1.8–3.8 LU |
| Music/SFX | low continuous electronic/ambient bed; sparse semantic SFX, no whoosh-per-cut |
| Captions | none unless explicitly requested |

## Approved production stack

| Responsibility | Skill |
|---|---|
| Orchestration | `content-router` |
| Research/script/beats | `youtube-script` |
| Visual-state and asset ledger | `image-queue` |
| Art language | `handdrawn-style-lock` |
| Deterministic diagrams/marks | `handdrawn-code` |
| PNG layers and MLS puppet motion | `ae-motion` |
| Exceptional repeated character actions | `character-animation-skill` |
| Opt-in expressive acting/camera direction | `expressive-doodle-acting` |
| Script/audio/cadence checks | `video-polish` |
| Publishing metadata | `youtube-seo` |
| Clean alpha/cutouts | `transparent-asset-prep` |
| Repository-specific enforcement | `paint-style-qc` |
| Master profile | `paint-explainer-recreation` |
| Browser composition/runtime | `hyperframes-core` |
| Keyframe diagnostics | `hyperframes-keyframes` |
| Seekable animation adapters | `hyperframes-animation` |
| Preview/lint/render CLI | `hyperframes-cli` |

The four HyperFrames skills are a pinned Apache-2.0 subset. Provenance is in
`skills/hyperframes-upstream/UPSTREAM.md`. Do not import its generic
faceless/creative presets into this profile.

## Workflow

1. **Select mode and write.** Use `youtube-script`; retain word-level timing.
   Run `video-polish` script QC.
2. **Plan semantic visual states.** Use `image-queue`, but do not force one
   image per beat. Record holds, reuse, hard cuts, source swaps, local actions,
   title continuity, and anticipated event times.
3. **Make art.** Lock the mode palette and contour with
   `handdrawn-style-lock`; use `handdrawn-code` for diagrams. Approve first
   subject and world-plate masters as references.
4. **Prepare assets.** Use `transparent-asset-prep` only when clean alpha is
   missing. Keep original sources. Run image QC.
5. **Choose one renderer per composition.** Use `ae-motion` for transparent
   PNG/MLS work, or the selected HyperFrames subset for deterministic browser
   layout and diagnostics. Keep the camera locked and blur off.
6. **Use character rigging sparingly.** Fire `character-animation-skill` only
   for a genuinely repeated action; simpler pose swaps/part rotation win. When
   the user explicitly selects expressive character storytelling rather than a
   corpus-faithful recreation, route acting, deformation, secondary motion, and
   motivated camera decisions through `expressive-doodle-acting`; keep that
   opt-in profile separate from the measured locked-camera default.
7. **Assemble to narration.** Put hard changes 1–2 source frames before the
   emphasized word; preserve chapter breath and title strip. Add the measured
   low bed and only semantic SFX.
8. **Gate the result.** Run `paint-style-qc` and `video-polish`; manually spot
   check events because flattened local animation can resemble a scene cut.
9. **Package.** Use `youtube-seo` only after the master passes.

## Minimum artifacts

```text
projects/SLUG/
  script.md
  beats.json
  audio/word-timings.json
  assets/source/
  assets/cutouts/
  scenes/
  manifest.json
  qc/
  final.mp4
  metadata.md
```

The master profile defines the fuller artifact contract. Keep source masters,
scene manifests, event timing, and machine reports; do not commit render caches
or unneeded frame sequences.

## Stop conditions

Do not approve a final when any of these remains:

- generic zoom/pan/parallax, dissolve, or idle loop;
- more than three local moving elements without a measured exception;
- chapter title absent or drifting;
- cuts timed after the noun when anticipation was intended;
- off-style outline/palette, alpha fringe, AI text, or anatomy error;
- narration/mix outside current measured targets;
- captions added without request;
- generic skill presets have replaced repository authority.

## Legacy vertical mode

The old static three-band 9:16 builder remains in `scripts/build_video.py` for
explicit legacy requests only. Its geometry/audio defaults are not Paint
Explainer defaults and must not leak into the measured 16:9 workflow.

Never copy another creator's drawings, script, voice, or branding. Reproduce
measured production technique with original content and assets.
