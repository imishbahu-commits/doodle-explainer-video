# video-polish

The quality pass for the doodle-explainer-video pipeline: three checkpoints
that catch problems at the cheapest moment to fix them.

| When | Tool | What it checks | Downloads |
|---|---|---|---|
| After the script | `script_doctor.py` | hook, paradox, promise, re-hook, closing question, sources, rhythm, spoken numbers | nothing |
| After the voiceover | `audio_report.py` | loudness vs reference, dead air, pause rhythm (+ optional `--tighten`) | nothing |
| After assembly | `qa_pacing.py` | illustration cut cadence vs the measured format, beat-count mismatch | nothing |

Everything runs on ffmpeg + Python, both already installed by the repo's
setup. No new packages, no internet, no APIs.

## Quick start

```bash
python3 scripts/script_doctor.py projects/strange-face/script.md
python3 scripts/audio_report.py projects/strange-face/final.mp4
python3 scripts/qa_pacing.py projects/strange-face/final.mp4 \
  --manifest projects/strange-face/manifest.json
```

Each prints a PASS/FAIL report with exact fixes; every check accepts
`--json` for machine-readable output. See `SKILL.md` for the agent-facing
rules, and `references/format-spec.md` for the numbers everything is
measured against.

## What it deliberately does NOT do

- No caption generator, no thumbnail builder — kept out to stay lean.
- No restyling — it reports, and you decide the fix.
