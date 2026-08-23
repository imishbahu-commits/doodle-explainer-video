# Part 1 QC Report

**Status: PASS**

## Synchronization

- Audio span: `00:00.000–00:41.715`
- Global frame span: `0–1250` (`1251` exclusive)
- Decoded output: exactly **1,251 frames** at **30 fps**
- Container duration: **41.70 s** (frame duration is 41.700 s; timing contract ends at source timestamp 41.715 s)
- Scene cuts occur on the globally contracted frames: 140, 256, 386, 532, 661, 806, 954, and 1109.
- Narration is trimmed from the continuous master and starts at zero; no time-stretching was applied.

## Video and audio

- Video: H.264 High, 1376×768, progressive yuv420p, 30 fps.
- Audio: AAC-LC, 44.1 kHz, stereo, approximately 193 kb/s.
- Fixed gain: −2.36 dB.
- Measured Part 1 integrated loudness: −19.9 LUFS; true peak: −6.6 dBFS. (The fixed gain is based on the full 7:15.70 master; short-part loudness naturally differs.)
- Full output decode passed.
- FFmpeg black-frame scan found no black segment of 0.15 seconds or longer.

## Visual QC

- Nine generated assets used, below the 10-asset cap.
- All nine preflight frames passed custom checks for restrained palette, dominant white chapter strip, and visible dark linework.
- Significant-color counts ranged from 10–16 at a 0.5% area threshold.
- Chapter-strip white occupancy was 88.1% in every tested frame.
- Transition before/after frames were extracted and visually inspected; every cut is clean.
- Scientific guardrails present: B008 is explicitly marked `RECONSTRUCTION`; visuals do not portray literal flight.

## Review artifacts

- `part-01-preflight-sheet.jpg` — all nine labeled plates.
- `part-01-output-sheet.jpg` — decoded transition samples.
- `part-01-blackdetect.log` — decode and black-frame scan.
- `part-01-ebur128.log` — loudness measurement.
- `part-01-poster.png` — representative final frame.
