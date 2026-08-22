# CLAUDE.md — Paint Explainer repository instructions

## Read first

For any current Paint Explainer build, read in this order:

1. `SKILL.md`
2. `skills/style-analyzer/SKILL.md` — if the user uploaded reference videos
3. `skills/paint-explainer-recreation/SKILL.md`
4. The active style profile (first one that exists):
   - `stylehub/current.json` → its `style_rules` (promoted in Reference Studio)
   - `stylehub/combined/style_rules.json` (merged uploads)
   - `references/paint-explainer-analysis-4v/style_rules.json` (built-in default)
5. `skills/content-router/SKILL.md`

`style_rules.json` is authoritative. The built-in default comes from four
user-supplied videos, 98,705 scanned frames, 3,290.167 s, 845 shots, and 841
abrupt edit events. A promoted upload profile supersedes it when the user has
chosen one. It supersedes older single-video, vertical-format, or speculative
notes whenever values conflict.

## Rules that must not regress

- A spoken beat is **not** a mandatory new image/cut. Record intentional holds
  and reused visual states in `beats.json`.
- Justify a visual change with a noun, idea, relationship, or action. Put a
  cut/source swap ~1–2 source frames (0.033–0.067 s) before its word onset.
- Camera is locked. No routine zoom, pan, follow, orbit, parallax, or shake.
- Motion is sparse: ~35–60% frozen shots and normally only 1–3 moving local
  elements in an active shot.
- Default to hard cuts, holds, and one-frame pose/source swaps. Do not add
  dissolve/fade, generic entrances, idle breathing, blink cycles, lip-sync,
  motion blur, or perpetual loops.
- Preserve the centered black uppercase chapter title on a white top strip
  occupying ~10% of frame height for the entire chapter.
- Use a single clean imperfect near-black `#101010` contour, ~6 px at
  1920-wide production. Use measured mode palettes and flat character fills;
  reserve gradients for sky/water/world plates.
- Current voice target: 204–209 recognized WPM.
- Current mix: −20.7 to −20.6 LUFS, true peak ≤−2.3 dBTP, LRA 1.8–3.8 LU.
- A low continuous electronic/ambient bed is measured and allowed. Keep it
  subordinate; use only sparse semantic SFX and never a whoosh per cut.
- Do not add captions/subtitles unless requested.

## Approved stack

| Stage | Skill |
|---|---|
| profile/orchestration | `paint-explainer-recreation`, `content-router` |
| script | `youtube-script` |
| state/asset ledger | `image-queue` |
| generated/deterministic art | `handdrawn-style-lock`, `handdrawn-code` |
| clean subject alpha | `transparent-asset-prep` |
| PNG/MLS renderer | `ae-motion` |
| exceptional repeated action | `character-animation-skill` |
| browser renderer/diagnostics | `hyperframes-core`, `hyperframes-keyframes`, `hyperframes-animation`, `hyperframes-cli` |
| measured gates | `paint-style-qc`, `video-polish` |
| publishing metadata | `youtube-seo` |

HyperFrames is a pinned Apache-2.0 subset. Do not import its generic
creative/faceless skills or use camera/transition blueprints that conflict with
this repository profile.

## Workflow

1. Resume from durable artifacts in `projects/SLUG/`.
2. Research and approve narration; retain final word timings.
3. Plan visual states separately from spoken beats: hold, reuse, hard cut,
   source swap, or local action.
4. Approve one subject and one world-plate style reference for the selected
   mode. Use `handdrawn-code` for deterministic diagrams where useful.
5. Prepare clean RGBA subjects only when needed. Keep source masters immutable.
6. Choose one renderer per composition: `ae-motion` for PNG/MLS work or the
   selected HyperFrames subset for deterministic HTML/CSS work.
7. Use character sprite generation only when a repeated semantic action cannot
   be represented with a pose swap, part rotation, or 2–4 pins.
8. Assemble at word-aligned event times, preserve chapter breaths/titles, and
   mix to measured targets.
9. Run `paint-style-qc` after asset prep and scene authoring, then run it with
   `video-polish` after assembly. Repair and rerun.
10. Run `youtube-seo` only after the final passes.

## Generation ledger

The image-generation cap applies only to genuinely new `ai` masters. Generate
up to 10 pending AI assets per turn, pass accepted references when supported,
record each path in `beats.json`, and retain the ledger. `hold`, `pose`, `asset`,
and `doodle` rows do not consume generation calls. Never generate
near-duplicates merely to avoid deliberate reuse.

## Renderer defaults

For `ae-motion`: `fps: 30`, `motion_blur: 1`, no camera track, and no more than
three moving layers per shot. Its `--plan` output is conservative.

For HyperFrames: use the core contract and seek-safe runtime, then lint/check,
inspect keyframes, and snapshot. Repository-specific QC remains mandatory.

## Durable artifacts

Retain scripts, research, word timing, source masters, cutouts, state/event
ledger, scene manifests/compositions, audio, QC reports, final master, and
metadata. Do not commit render caches, node_modules, frame sequences, or
unneeded generated intermediates.

## Legacy boundary

`scripts/build_video.py`, old three-band vertical docs, old single-video
references, and copied Agent Reach examples remain legacy material. Use them
only when the user explicitly requests that legacy format. Their one-image-per-
beat, 60 fps, no-music, and loudness defaults are not current Paint Explainer
rules.

Never copy another creator's drawings, scripts, voice, or branding. Reproduce
measured production technique with original content and assets.
