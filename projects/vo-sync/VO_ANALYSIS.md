# Uploaded voiceover — pacing + beat map

File: `uploads/inbox/voiceover/20260904-075751_my_vouceover__160357619.mp3`  
Encoder: AudioLab · 44100 Hz mono · 128 kb/s

## Numbers

| | |
|---|---|
| Duration | **11:43.03** (703.03 s) |
| Speech | 620.9 s |
| Silence | 82.1 s (11.7%) |
| Pauses detected | 252 (noise −28 dB, min 0.15 s) |
| Pause mean | **0.33 s** (breath, not chapter gaps) |
| Pauses ≥ 0.5 s | 31 |
| Pauses ≥ 0.7 s | 15 (true sentence/section breaths) |
| Longest pause | 1.38 s |

## Speed

You said **~200 wpm**. At that rate:

- ~**2343 words** in 11:43
- 12–13 words per beat → **3.6 s** hold
- Beat map: **182 cuts**, mean **3.60 s**, median **3.39 s**, min 2.29, max 5.20
- Words per beat ≈ **12.9**

That matches the Paint Explainer cut rhythm (2–6 s, ~3.6 s median). The VO is **fast and tight** — most pauses are 0.2–0.4 s breaths, not long holds. Images must cut on those breaths, never stretch.

Beat list: `projects/vo-sync/vo_beats.json`

Sync rule: image N on screen from `start` to `end` of beat N. 182 images for the full VO.

## Style lock (from your reference clips)

Stick figures: thin black-line body, **large irregular lumpy white head** (not a clean oval), messy hair tufts, big black oval eyes, simple brows, open mouth + teeth. Flat color backgrounds, thick outlines.

Samples: `projects/vo-sync/samples/sample01–05.png`

Next: approve the face, then we generate beat 1–10 against this VO.
