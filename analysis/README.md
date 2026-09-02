# Reference-video frame analysis (committed for durability)

This folder holds the **extracted frames** and **quantified timing** from the 14
reference videos the user uploaded. It is committed to git so it survives any
workspace wipe. The raw source videos stay in `uploads/` (gitignored — they are
large and re-uploadable).

## Why the frames are small PNGs
The source videos are flat MS-Paint doodles (~100–256 colours per frame). Every
frame is palette-quantised losslessly to PNG8, which keeps the 2,830 images at
~65 MB total — small enough to commit and push to GitHub without losing any
line-art crispness.

## Contents

| Path | What it is |
|---|---|
| `frames/<video>/<video>_beat_NNNN.png` | Every on-screen image (beat) of every video, one PNG per beat. **2,830 images.** |
| `reference_frames/` | Full-resolution 640×360 reference frames used to build the style lock. |
| `style_locked/` | The character reference(s) you pass to `generate_image` as the `images` style-lock. |
| `matches/` | Verified ditto-copy recreations (facing the real reference frames). |
| `reports/` | All the quantified analysis: beat timing CSV/JSON, narration sync, per-video manifests, and the `deep_analysis.html` gallery. |

## Key reports
- `reports/deep_analysis.html` — **interactive gallery**: every beat's thumbnail + its on-screen duration + visual tags + word range. Open in a browser.
- `reports/beat_timing.csv` — all **2,830** beats: video, start/end/duration (s & frames), image path.
- `reports/beat_narration.csv` — per-beat estimated word range at ~210 wpm.
- `reports/STYLE_SPEC.md` — the measured style spec (deformed non-oval face, thin stick body, expressions, backgrounds).
- `reports/DEFORMED_FACE_SPEC.md` — the corrected "destroyed/deformed face" rules + verified prompt.
- `reports/PROVEN_PROMPT.md` — the verified single-prompt recipe + failure signatures.

## How to regenerate (if the videos are re-uploaded)
```bash
# 1. detect beats + extract every frame (writes analysis/frames/ + manifests)
python3 tools/analyze_reference_beats.py --dir uploads --out analysis
# 2. build the gallery + per-beat visual features
python3 tools/build_deep_report.py --out analysis
# 3. estimated beat→narration word ranges
python3 tools/analyze_voiceover_sync.py --out analysis
```
