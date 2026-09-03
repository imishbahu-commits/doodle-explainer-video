# BATCH-3 STYLE — 9 new references (16060–16092) + voiceover analysis

## Reference videos (all ~90–96% FROZEN — face-expression story style)
| id | dur | bright | sat | bg tint |
|----|-----|--------|-----|---------|
| 16060 | 644s | 192 | 47 | sage (196,199,180) |
| 16064 | 557s | 164 | 45 | grey-warm (169,162,160) |
| 16068 | 707s | 180 | 63 | grey-green (182,182,173) |
| 16072 | 724s | 186 | 55 | sage (186,192,180) |
| 16076 | 511s | 205 | 31 | pale green (200,209,205) |
| 16080 | 638s | 161 | 92 | warm brown (173,159,149) |
| 16084 | 598s | 156 | 53 | teal-grey (148,160,158) |
| 16088 | 627s | 189 | 60 | sage (191,196,178) |
| 16092 | 648s | 179 | 60 | warm grey (185,179,170) |

Median cut 2.8–3.8 s. Bright warm/muted backgrounds (no pure white void):
sage-green, warm grey, soft teal. Faces are the focus; body chest-up;
expression changes (brows/eyes/mouth/teeth) carry the story.

## Face micro-grammar (for image generation)
- ONE recurring character identity; expression per beat via NEW image.
- Eyebrows: thick, expressive (high=shock, slanted=anger, inner-up=sad).
- Eyes: dot pupils + small white highlight; arcs when laughing/happy.
- Mouth: teeth rows visible when open; dark cavity; tongue rare.
- Hair: simple messy cap; body: plain t-shirt chest-up; bg: flat warm
  muted single color; thick black ink; flat fills; no shadows/gradients.

## Voiceover (my_20vouceover mp3, 703s)
Beat-marked by energy envelope -> 222 beats, median 2.96 s, mean 3.17 s,
range 2.0–6.3 s  (see voiceover-beats.json). => ~222 images needed for a
full sync; 10 per turn => ~23 turns, or work section-by-section.

## Sample images created (projects/dinzo-samples/assets/)
char_base (neutral) + happy, angry, shock, sad, laugh, thinking, scared —
one consistent identity, 8 expressions.
