# Four-video Paint Explainer analysis corpus

This directory is the **current measured authority** for recreating The Paint
Explainer animation/edit style. It was produced from four user-uploaded videos
(54:50 total; 98,705 decoded frames) on 2026-08-21.

Start with:

1. [`STYLE_SPEC.md`](STYLE_SPEC.md) — complete human-readable specification.
2. [`style_rules.json`](style_rules.json) — compact rules for agents/code.
3. [`CUT_LIST.md`](CUT_LIST.md) — every detected edit boundary.

Supporting data:

- `analysis_manifest.json` — source identity, hashes/method, chapter timestamps.
- `metrics/*.json` — visual, motion, edit, audio and chapter aggregates.
- `cuts/*-cuts.csv` — all abrupt edit events with timestamp and word-sync delta.
- `cuts/*-shots.csv` — every shot with duration and motion class.
- `transcripts/*.json` — Vosk word timings; proper nouns may be misspelled.
- `frames/*.jpg` — five annotated evidence grabs/video plus contact sheets.

## Rebuild

Install the analysis dependencies and provide the Vosk small English model at
`tools/models/vosk-model-small-en-us-0.15`. The source videos remain local in
`uploads/` and are excluded from normal Git history.

```bash
python3 -m venv .analysis-venv
.analysis-venv/bin/pip install -r requirements-analysis.txt
.analysis-venv/bin/python scripts/analyze_paint_explainer_corpus.py
.analysis-venv/bin/python scripts/build_paint_explainer_evidence.py
.analysis-venv/bin/python scripts/build_paint_explainer_cut_list.py
```

## Critical measured correction

Across these four files, **no sustained whole-scene zoom was verified**. Camera
is locked; motion is hard cuts plus local pose/prop/label animation. This
supersedes older speculative instructions that prescribe default Ken Burns
zooms. See `STYLE_SPEC.md`, Parts B–D, before implementing motion.
