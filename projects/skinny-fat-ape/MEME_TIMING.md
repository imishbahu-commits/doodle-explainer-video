# Meme grammar applied to this hook

Technique only — original ape drawings, no stolen templates.

## What the research said (and we used)

| Mechanic | Source | How it lands here |
|---|---|---|
| Rule of 3 — two setups, third betrays | stand-up / visual comedy | Thin? No. Fat? No. **BOX.** |
| Joke readable in the first 1–2s | short-form meme video | Caption + subject on frame 1 of each beat |
| Audio syncs the punch | viral meme edits | Bonk on every NO, splat on banana, hit on RECOMP |
| Comparison template | Drake / reject-approve grammar | Two NOs then approve the jacked ape |
| Reaction zoom | punch-in on the reveal | Skinny-fat + abs magnifier |
| Image-macro captions | top/bottom Impact style | Hand-lettered, never baked into the PNG |
| Less is more SFX | sfx-guide.md | 9 hits, not a circus |

## Beat → meme job → SFX

| t | Narration | Meme job | SFX |
|---|---|---|---|
| 0.00 | Is monkey thin? | Setup 1 | whoosh in |
| 1.18 | No. | Rejection stamp | bonk |
| 2.40 | Is monkey fat? | Setup 2 | whoosh |
| 3.62 | No. | Rejection stamp | bonk |
| 4.80 | looks like a box | **Rule-of-3 twist** | record-scratch |
| 8.10 | classic skinny fat | "same picture" reveal | ding |
| 10.70 | Ape shows you | 4th-wall point | pop |
| 13.10 | overripe banana | exaggeration gag | splat + boing |
| 16.40 | primal masterpiece | transformation | stamp |
| 18.90 | crackhead abs | zoom-reaction | shutter |
| 22.00 | no waist | sad beat | wah |
| 24.50 | body recomp | victory approve | boom |

## After-generate drawing step

`tools/meme_draw.py` is the post-pass: take a white-bg subject PNG and stamp
captions / arrows / circles without regenerating the character.
