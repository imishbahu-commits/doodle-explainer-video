---
name: style-analyzer
description: Turns user-uploaded reference videos into a measured, machine-readable style bible (style_rules.json + style_profile.md) that the Paint Explainer production pipeline consumes. Backs the Reference Studio UI and the analyze/combine CLI.
---

# Style analyzer — measure any reference video, then rebuild it

## What it does

A user uploads one or more reference videos (any resolution, any aspect
ratio). This skill measures the production technique and emits a style bible
in the **same schema** as `references/paint-explainer-analysis-4v/style_rules.json`,
so `content-router` and the whole measured stack can consume it unchanged.

Measurement covers, per video:

- **Editing** — every abrupt edit boundary, shot-length distribution
  (min/p25/median/mean/p75/p90/max), cut-type split (full-frame hard cut,
  same-palette hard cut, localized swap/pop), and — when a transcript is
  available — the signed cut-to-word offset (median, share of cuts that
  precede the spoken word).
- **Motion** — per-shot class: frozen hold, character/graphic animation,
  subtle local motion, whole-canvas slide, short graphic sting, verified
  whole-scene zoom in/out (via ORB/RANSAC registration with a residual gate,
  so moving characters are not mistaken for camera moves).
- **Art** — dominant quantized palette (core vs emphasis), median black-stroke
  width at source resolution scaled to 1920, ink centroid, ink bbox width,
  majority-white frame share, per-frame significant color count.
- **Format** — orientation, three-band vertical layout detection (banner
  staticness, middle-band ink, empty bottom band), persistent top title-strip
  detection.
- **Audio** — integrated LUFS, true peak, LRA, RMS/peak, mixed-onset tempo
  estimate, inter-word pause statistics, and recognized WPM when the offline
  Vosk small model is installed.
- **Structure** — estimated chapter boundaries (narration pauses landing on
  hard cuts), evidence frames + contact sheet.

## Entry points

### 1. Reference Studio (browser)

```
.venv/bin/python tools/style_studio/server.py --host 0.0.0.0 --port 8765
```

Opens the upload UI. Users drop videos; the server runs the analyzer in the
background and shows progress, metrics, palette, motion budget, shot
histogram, evidence frames, transcript and the rendered style bible.
**Promote** marks one profile (or the merged profile) as the current style:
it writes `stylehub/current.json`.

### 2. CLI (headless)

```bash
# one video
.venv/bin/python scripts/analyze_style.py analyze \
  --video path/to/ref.mp4 --out stylehub/profiles/<id> --label "My reference"

# merge several analyzed profiles into one style bible
.venv/bin/python scripts/analyze_style.py combine \
  --dirs stylehub/profiles/a stylehub/profiles/b --out stylehub/combined
```

Outputs per profile: `metrics.json`, `shots.csv`, `cuts.csv`,
`transcript.json` (optional), `frames/contact-sheet.jpg` + evidence frames,
`analysis_manifest.json`, `style_rules.json`, `style_profile.md`.

## How the analyzed style drives production

Resolution order for any new build:

1. `stylehub/current.json` — if present, its `style_rules` is the
   authoritative profile (user promoted it in the studio).
2. `stylehub/combined/style_rules.json` — merged uploads, if any.
3. `references/paint-explainer-analysis-4v/style_rules.json` — the built-in
   measured default.

Then run the normal stack with those numbers substituted:

- **content-router stage 0** reads the active profile and fixes the invariants
  for the build: median shot target, frozen-hold share, cut-to-word offset,
  palette, stroke width at production resolution, title-strip/banner rules,
  loudness/WPM targets.
- The user's uploads **override** the corpus defaults where values differ
  (e.g. a vertical three-band upload reactivates the legacy three-band
  builder; a horizontal whiteboard upload keeps the Paint Explainer workflow).
- Anything the uploads cannot measure (exact easing curves, hidden layer
  anchors, clean music stem, original AE keyframes) stays marked
  `template`/`estimate` in the emitted rules — keep the corpus recipe cards
  for those gaps.

## Rules that must not regress

- Never claim a value is measured when it is estimated. The emitted
  `measurement_notes` and per-recipe `provenance` fields say which is which.
- Do not equate detected shots with required cuts: holds and reuse are
  intentional in this style.
- A three-band vertical upload means: static banner reused for the whole
  video, illustration band hard-cuts per beat, bottom band stays empty.
- Transcription is offline (Vosk small). Proper nouns will be misheard —
  check them against the user's chapter list before using timings.
- Uploaded videos stay under `stylehub/uploads/` (gitignored). Never commit
  them; store sha256 + analysis artifacts only.
- Respect the user's rights: analysis of a user-supplied reference for the
  purpose of reproducing production technique is fine; never copy their
  drawings, scripts, voice, or branding into generated content.
