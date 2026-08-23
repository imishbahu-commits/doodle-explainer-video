# Part 2 QC Report

**Status: PASS**

## Synchronization

- Source-audio span: `00:41.715–01:26.970`
- Global frame span: `1251–2608` (`2609` exclusive)
- Decoded output: exactly **1,358 frames** at **30 fps**
- Container/frame duration: **45.27 s**
- Part 2 begins on the frame immediately following Part 1; no frame gap or overlap.
- All ten cuts use the contracted global beat frames.
- Narration is trimmed from the uploaded continuous master; no time-stretching was applied.

## Video and audio

- Video: H.264 High, 1376×768, progressive yuv420p, 30 fps.
- Audio: AAC-LC, 44.1 kHz, stereo, approximately 193 kb/s.
- Fixed gain: −2.36 dB.
- Measured Part 2 integrated loudness: −20.7 LUFS; true peak: −6.9 dBFS.
- Full output decode passed.
- FFmpeg black-frame scan found no black segment of 0.15 seconds or longer.

## Visual QC

- Ten generated assets used: exactly at, but not above, the 10-asset cap.
- Every labeled preflight frame passed `paint_style_qc.py` with zero failures.
- Midpoint frames from all ten encoded beats were extracted and visually inspected.
- Text remains inside safe margins and the chapter strip stays consistent.
- Era, anatomy, and reconstruction visuals remain within the approved scientific guardrails.

## Review artifacts

- `part-02-assets.jpg` — ten source illustrations.
- `part-02-preflight-sheet.jpg` — final labeled plates.
- `part-02-output-sheet.jpg` — decoded midpoint samples.
- `part-02-blackdetect.log` — decode and black-frame scan.
- `part-02-ebur128.log` — loudness measurement.
- `part-02-poster.png` — representative final frame.
