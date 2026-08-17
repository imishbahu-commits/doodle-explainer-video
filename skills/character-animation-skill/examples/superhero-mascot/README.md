# Use case: video clip → looping web asset (Path C)

A **video** of a white-and-purple superhero mascot flying in, turned into a
transparent, looping website asset using the **first 2 seconds** only.

| Input video (`source.mp4`) | Output (`hero-mascot.gif`) |
|:---:|:---:|
| <img src="source-still.png" width="300" alt="A still from the source video: a white and purple superhero robot mascot on a light-grey background"> | <img src="hero-mascot.gif" width="300" alt="The same mascot as a looping animation with the background removed"> |
| 1440×1440, 24 fps, light-grey background | 48 frames @ 24 fps, true-alpha transparent |

This is the case the color keyers **can't** handle: the mascot's body is white and
the background is near-white, so a white/chroma key would eat the subject. Path C
keys by **shape** with the ML keyer (`remove_bg_ml.py`, U²-Net) instead, and keeps
the source 24 fps so the original flight motion stays fluid.

> The clip is an *entrance* (the mascot rises into frame), so the loop is not
> seamless — it restarts from the near-empty first frame. That's the literal first
> two seconds; pick a self-matching range or a ping-pong order for a seamless loop.

## Reproduce it

```bash
# 1. first 2 seconds -> 48 frames at the source 24 fps, square 800px
python3 ../../scripts/video_to_frames.py source.mp4 frames_raw/ \
  --start 0 --duration 2 --size 800

# 2. shape-based background removal (downloads the U²-Net model once)
python3 ../../scripts/remove_bg_ml.py frames_raw/ frames_cut/

# 3. montage into an 8x6 sheet (plain montage = keep each frame's position)
magick montage frames_cut/f_*.png -tile 8x6 -geometry 800x800+0+0 \
  -background none sheet.png

# 4. assemble the three looping files at the clip's fps (frames already transparent)
python3 ../../scripts/spritesheet_to_animation.py sheet.png --keep-bg \
  --cols 8 --rows 6 --fps 24 --display-cell 480 --name hero-mascot --out-dir .
```

Outputs: `hero-mascot.svg`, `hero-mascot.webp` (both true-alpha) and
`hero-mascot.gif` (shown above).
