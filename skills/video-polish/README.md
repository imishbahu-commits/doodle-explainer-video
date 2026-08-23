# video-polish

Measured quality gates for the Paint Explainer pipeline.

| Gate | Tool | Checks |
|---|---|---|
| Script | `script_doctor.py` | structure, sources, rhythm, word budget |
| Voice/final mix | `audio_report.py` | EBU R128 integrated loudness, true peak, LRA, pauses |
| Assembly | `qa_pacing.py` | flattened visual-change cadence and manifest event counts |
| Style | `paint-style-qc` | repository-specific art, camera, motion, timing, and audio rules |

```bash
python3 skills/video-polish/scripts/script_doctor.py projects/example/script.md
python3 skills/video-polish/scripts/audio_report.py projects/example/final.mp4 --json
python3 skills/video-polish/scripts/qa_pacing.py projects/example/final.mp4 \
  --manifest projects/example/manifest.json --json
```

Current authority is
`references/paint-explainer-analysis-4v/style_rules.json`; it supersedes older
generic format notes. The tools report first and do not restyle media. Captions
remain out unless requested; the measured low ambient/electronic music bed is
allowed and should remain subordinate.
