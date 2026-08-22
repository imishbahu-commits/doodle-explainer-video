# Reference Studio — upload reference videos, get their style, build like them

The repo now has a **Reference Studio section**: you upload reference videos,
the studio measures the production technique frame-by-frame, and the existing
video pipeline rebuilds that style for new videos.

## 1. Upload & analyze (browser)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-analysis.txt \
                      -r tools/style_studio/requirements.txt
.venv/bin/python tools/style_studio/server.py --host 0.0.0.0 --port 8765
```

Open the studio UI, drop one or more reference videos (mp4/mov/webm/mkv), and
watch the live analysis. Per video it measures:

| What | How |
|---|---|
| Shots & cuts | PySceneDetect on every decoded frame; cut-type split |
| Cut ↔ narration sync | signed cut-to-word offset via offline Vosk word timings |
| Motion budget | per-shot class: frozen / character / subtle-local / slide / sting / zoom (ORB+RANSAC with residual gate) |
| Format | orientation, three-band layout (pixel-level banner staticness, empty bottom band), persistent title strip |
| Art | dominant palette (core vs emphasis), stroke width scaled to 1920, ink centroid/bbox, white-frame share |
| Audio | LUFS / true peak / LRA, tempo estimate, WPM, inter-word pauses |
| Structure | estimated chapters (pauses landing on hard cuts), evidence frames + contact sheet |

Same-format headless CLI:

```bash
.venv/bin/python scripts/analyze_style.py analyze --video ref.mp4 --out stylehub/profiles/<id>
.venv/bin/python scripts/analyze_style.py combine --dirs <profiles...> --out stylehub/combined
```

## 2. Choose the style

- **Use as current style** (per video) writes `stylehub/current.json`.
- With two or more analyzed videos, **merge** them into one style bible and
  promote that instead.

## 3. Build

The production pipeline (skills `style-analyzer` → `content-router` →
renderers → `paint-style-qc`/`video-polish`) reads the promoted
`style_rules.json` — the same schema as the built-in
`references/paint-explainer-analysis-4v/style_rules.json` — and substitutes the
upload's measured numbers (median shot length, frozen-hold share, cut offset,
palette, stroke width, loudness/WPM targets, banner/title-strip rules).

Resolution order for any build:

1. `stylehub/current.json` (promoted profile)
2. `stylehub/combined/style_rules.json` (merged uploads)
3. `references/paint-explainer-analysis-4v/style_rules.json` (built-in default)

Values the uploads cannot measure (easing curves, layer anchors, clean music
stem) stay marked `template`/`estimate` and fall back to the corpus recipe
cards.

## Storage & rights

Uploads and analysis artifacts live under `stylehub/` (gitignored). Analysis
of a user-supplied reference for technique replication is fine; never copy
their drawings, scripts, voice, or branding.
