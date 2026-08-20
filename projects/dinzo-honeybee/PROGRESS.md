# PROGRESS — "Why It Sucks to Be Born as a Male Honeybee" (Dinzo style)

## Resume summary (read this first)

- **Topic:** Male honeybee (drone) life cycle
- **Voice:** `voice-02` — deadpan masculine narrator (the "Dinzo" style).
  If a NEW session ever needs to re-audition a voice, use this audition text
  and pick a deadpan male:
  "You are born inside an egg buried in a muddy mound on the edge of a
  mangrove swamp in Northern Australia. The nest is a stinking pile of
  rotting leaves and mud your mother kicked together a few months ago.
  She's long gone now. She doesn't care about you. She cares about the
  next meal."
- **Style anchor image:** `assets/beat01.png` — pass it as the reference
  image (`images` arg) on EVERY new image generation to lock the style.
- **Format:** 16:9 landscape 1920x1080, hard cuts, one image per beat,
  no music, no captions. Labels are drawn BY THE IMAGE GENERATOR.

## Progress: parts 1–4 COMPLETE, part 5 = 8/10

| Part | Beats | Status |
|---|---|---|
| 1 | 1–10 | complete (10/10) |
| 2 | 11–20 | complete (10/10) |
| 3 | 21–30 | complete (10/10) |
| 4 | 31–40 | complete (10/10) |
| 5 | 41–50 | 8/10 — missing beat 49 audio + beat 50 audio+image |
| 6 | 51–60 | not started |
| 7 | 61–70 | not started |
| 8 | 71–80 | not started |
| 9 | 81–90 | not started |
| 10 | 91–100 | not started |
| 11 | 101–110 | not started |
| 12 | 111–114 | not started |

Total: 114 beats (48 audio + 49 images done so far).

## How to build / assemble

```bash
cd /home/user/doodle-explainer-video
export PATH="$HOME/.local/bin:$PATH"

# re-render one part (images + audio already in assets/ and audio/)
.venv/bin/python projects/dinzo-honeybee/build.py part 5

# render every part that has all its media, then stitch final.mp4
.venv/bin/python projects/dinzo-honeybee/build.py all
# or just stitch whatever parts exist:
.venv/bin/python projects/dinzo-honeybee/build.py final
```

Each beat = `assets/beatNN.png` + `audio/beatNN.mp3`. `build.py` fits the
image to 1920x1080, sharpens, and shows it for exactly the audio length
(+0.25s breath), hard cut to the next beat. Output parts → `parts/partNN.mp4`,
final → `final.mp4`.

## What's committed to git (safe on GitHub)

- `script.md`, `beats.json` (full 114 beats), `research.md`, `build.py`
- `assets/*.png` (all images — the style lock anchor is beat01.png)
- `audio/*.mp3` (voice clips — the expensive part, now committed too)
- NOT committed (regenerable): `build_work/`, `parts/`, `final.mp4`

## To resume producing (the per-turn loop)

1. Check the missing beats table above.
2. Generate the missing media (≤10 voice clips + ≤10 images per turn,
   images referencing `assets/beat01.png`).
3. `build.py part N` for each affected part, `git commit` + `git push`.
4. Continue one part per turn. When all 12 parts exist, run
   `build.py final` to stitch the ~9-minute video.

## Watch progress

The Studio (`python3 studio.py 8090`) lists `dinzo-honeybee → partNN.mp4`.
