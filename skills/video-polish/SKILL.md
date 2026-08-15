---
name: video-polish
description: Quality-check and tighten narration videos before publishing — grade a script like an editor (hook, paradox, promise, re-hook, closing question, sources, rhythm), measure audio loudness and dead air against the measured format spec, and verify the illustration cut cadence of a finished video. Use after writing a script, after recording narration, and after assembling a video in the doodle-explainer-video or animated pipelines.
---

# Video polish — the quality pass

Three zero-dependency tools (ffmpeg + Python only; the repo already ships
both). Run them at three gates: after the script, after the voiceover, after
assembly. Each prints a report; none modify files unless asked.

## Gate 1 — after writing the script: `scripts/script_doctor.py`

```bash
python3 scripts/script_doctor.py projects/<slug>/script.md
# or reconstruct the script straight from a build manifest:
python3 scripts/script_doctor.py --manifest projects/<slug>/manifest.json
```

Grades the script against the nine-move arc in
`references/script-formula.md`:

- cold open in second person (~15s)
- the impossible fact in the first third
- an explicit retention promise
- a mid-video re-hook
- a closing question aimed at the viewer
- real named sources (names, institutions, dates)
- sentence rhythm: avg/max length, fragments
- numbers spelled out for TTS
- word budget vs target length

Fails print an exact fix. Never generate media below 8/10; restructure
below 6/10. `--json` gives a machine-readable scorecard.

## Gate 2 — after the voiceover: `scripts/audio_report.py`

```bash
python3 scripts/audio_report.py projects/<slug>/audio/section.mp3
python3 scripts/audio_report.py final.mp4 --tighten final_tight.m4a
```

Measures with ffmpeg's silencedetect + volumedetect against the reference
(references/format-spec.md): mean −17.5 dBFS, peak ~0 dBFS, pauses 0.4–0.8s
at section boundaries. Flags every gap over 1.0s as dead air. `--tighten`
writes a copy with dead air removed (it keeps ≤1s of each pause, so
natural breaths survive) — then re-measure before muxing.

## Gate 3 — after assembly: `scripts/qa_pacing.py`

```bash
python3 scripts/qa_pacing.py projects/<slug>/final.mp4 \
  --manifest projects/<slug>/manifest.json
```

Recovers the exact cut list with ffmpeg's scene-change detector (every
illustration cut in a stills-based video is a hard cut), then checks the
hold-time cadence against the format: median 2–3s, mean 3.4–4.1s, longest
~14s. Flags holds under 1.5s (reads as flashing) and over 8s (slack
cutting). With `--manifest` it also verifies the cut count equals the beat
count — a mismatch means images were reused or the wrong manifest was built.

## Rules

- These are checks, not restyles. Report first; change only what a report
  flags.
- The format's restraints are load-bearing: no music, no sound effects,
  no captions (unless the user asks), hard cuts only. Polishing must not
  smuggle them back in.
- Always re-run the check after a fix and show the before/after.
