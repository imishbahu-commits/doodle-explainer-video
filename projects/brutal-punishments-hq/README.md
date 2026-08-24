# Brutal Punishments — HQ hand-drawn asset set

High-quality, AI-rendered hand-drawn plates that **replace the cheap
code-driven doodles** in `../brutal-punishments-sample/assets/`. The narration
script, beat texts and per-beat TTS clips are unchanged and reused from the
sample project.

## Contents

| File | Beat |
|---|---|
| `assets/banner.png` | clickbait banner band (hand-lettered title) |
| `assets/beat1_court.png` | Hook — Florence court, 1343 |
| `assets/beat2_rack.png` | The rack |
| `assets/beat3_iron_maiden.png` | Iron maiden |
| `assets/beat4_wheel.png` | The wheel, France |
| `assets/beat5_crowd.png` | Why it worked — the crowd |
| `assets/beat6_cell.png` | The quiet fix — 1800s cell |

## Art language

Elevated Paint Explainer per `skills/handdrawn-style-lock/SKILL.md`:
single-pass slightly imperfect near-black ink contours, rounded joins, flat
restrained gouache fills (browns `#B09070`/`#909070`, grays `#B0B0B0`/`#707070`,
shadow `#505050`, red `#E31B23` / yellow `#F0D010` accents only), subtle paper
grain, and a clean cream strip (`#F5ECD4`, ~10% frame height, 2px ink rule)
reserved for the chapter-title layer. Cartoon-safe: no gore, no blood.

All plates are 1920×1080 production resolution.

## Render

```bash
python3 scripts/build_video.py projects/brutal-punishments-hq/manifest.json --captions
```

The manifest reuses the sample project's `audio/beatN.mp3` clips; output lands
at `brutal_tortures_hq.mp4` (git-ignored like all mp4 scratch output).
