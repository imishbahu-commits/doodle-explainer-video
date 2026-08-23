# Part 2 QC Report

**Status: PASS**

## Synchronization

- Global frame span: `1251–2608` (`2609` exclusive)
- Preview audio trim: `00:41.700–01:26.967` from the continuous master
- Aligned beat span: `00:41.715–01:26.970`
- Decoded output: exactly **1,358 frames** at **30 fps**
- Container duration: **45.27 s**
- Scene cuts occur on contracted global frames 1391, 1528, 1658, 1799, 1960, 2094, 2228, 2344, and 2453.
- Audio was taken directly from the continuous master at the global frame boundary; no time-stretching was applied.

## Video and audio

- Video: H.264 High, 1376×768, progressive yuv420p, 30 fps.
- Audio: AAC-LC, 44.1 kHz, stereo, approximately 194 kb/s.
- Fixed gain: −2.36 dB.
- Measured Part 2 integrated loudness: **−20.7 LUFS**; true peak: **−6.9 dBFS**.
- Full output decode passed.
- FFmpeg black-frame scan found no black segment of 0.15 seconds or longer.

## Visual QC

- Ten generated assets used, exactly at the 10-asset cap.
- All ten final preflight frames passed `paint_style_qc.py` with zero failures.
- Chapter strip, restrained palette, dark hand-drawn linework, and label readability passed.
- Decoded start frames for all ten beats and the final frame were visually inspected.
- Era guardrails passed: no whales, marine reptiles, or pelicans are shown as Early Devonian residents; crossed-out modern animals are comparisons.
- General galeaspid anatomy is separated from direct preservation claims about Bataspis.

## Review artifacts

- `part-02-assets.jpg` — ten generated source plates.
- `part-02-preflight-sheet.jpg` — all ten final labeled plates.
- `part-02-output-sheet.jpg` — decoded beat-start samples and final frame.
- `part-02-blackdetect.log` — decode and black-frame scan.
- `part-02-ebur128.log` — loudness measurement.
- `part-02-poster.png` — representative final frame.
