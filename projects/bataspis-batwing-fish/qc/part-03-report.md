# Part 3 QC Report

**Status: PASS**

## Synchronization

- Source-audio span: `01:26.970–02:17.490`
- Global frame span: `2609–4124` (`4125` exclusive)
- Decoded output: exactly **1,516 frames** at **30 fps**
- Container/frame duration: **50.53 s**
- Part 3 starts on the frame immediately following Part 2; no frame gap or overlap.
- All ten visual changes use the contracted global beat frames.
- Narration comes directly from the uploaded continuous master; no time-stretching.

## Video and audio

- Video: H.264 High, 1376×768, progressive yuv420p, 30 fps.
- Audio: AAC-LC, 44.1 kHz, stereo, approximately 193 kb/s.
- Fixed gain: −2.36 dB.
- Measured Part 3 integrated loudness: −20.5 LUFS; true peak: −6.7 dBFS.
- Full output decode passed.
- FFmpeg found no black segment lasting 0.15 seconds or longer.

## Visual and scientific QC

- Ten generated assets used: exactly at the 10-asset cap.
- All ten labeled preflight frames passed `paint_style_qc.py` with zero failures.
- Midpoint frames from all ten encoded beats were extracted and visually inspected.
- Text remains inside safe margins and the chapter strip is consistent.
- B028–B029 explicitly distinguish the preserved headshield and counterpart from the uncertain reconstructed body.
- Bat, boomerang, and aircraft forms are presented as shape comparisons, not ancestry or literal flight.

## Review artifacts

- `part-03-assets.jpg` — ten source illustrations.
- `part-03-preflight-sheet.jpg` — final labeled plates.
- `part-03-output-sheet.jpg` — decoded midpoint samples.
- `part-03-blackdetect.log` — decode and black-frame scan.
- `part-03-ebur128.log` — loudness measurement.
- `part-03-poster.png` — representative final frame.
