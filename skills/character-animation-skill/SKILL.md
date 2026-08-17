---
name: character-animation
description: >-
  Turn a static character or asset image into a looping animated character,
  delivered as a moving SVG plus animated WebP and GIF. Use this whenever the
  user wants to animate, bring to life, or "make move" a character, mascot,
  logo, creature, sprite, icon, or any asset image — or wants a moving/animated
  SVG, WebP, or GIF made from an image — or mentions generating a sprite sheet
  animation, or names "Nano Banana 2" / Gemini image generation for animation.
  Also use it to convert an EXISTING sprite sheet (a grid of frames) into those
  animated formats. Trigger even when the user just says things like "animate
  this", "make this character move", "turn this into a moving svg/gif", or drops
  in a character asset and asks for an animation — you don't need them to say
  "sprite sheet" explicitly.
---

# Character Animation

Turn one static character image into a looping animation. The pipeline is:

```
character image + motion description
        │  (Nano Banana 2 — gemini-3.1-flash-image, 4K)
        ▼
   4K sprite sheet (grid of frames, white bg)
        │  (slice grid · key out background · assemble)
        ▼
   moving SVG  +  animated WebP  +  animated GIF   (transparent, looping)
```

Scripts (`scripts/`):
- `generate_spritesheet.py` — Mode 1: one Nano Banana 2 call → a whole sprite sheet.
- `generate_posed_frames.py` — Mode 2: one call PER frame, edited from a fixed base
  plate, for coherent motion.
- `frames_to_sheet.py` — Mode 2: normalizes per-frame output (locks scale/position)
  into a clean transparent grid sheet.
- `interpolate_frames.py` — Mode 2: synthesizes motion-compensated in-betweens
  (keyframe-then-interpolate) for extra fluidity.
- `video_to_frames.py` — Path C: extract a time range from an existing video clip
  into per-frame PNGs.
- `remove_bg_ml.py` — ML keyer: shape-based (U²-Net) background removal for subjects
  the color keyers can't separate (white-on-white, photos, video frames).
- `spritesheet_to_animation.py` — shared: any sheet → the three animated files.

There's also a second entry point — **Path C** — that skips generation entirely and
turns an existing **video clip** into the same three looping, transparent files.

A Google Gemini API key is required for generation. Set it once via the
`GEMINI_API_KEY` environment variable, or create
`~/.config/character-animation/key.env` containing `GEMINI_API_KEY=...`
(chmod 600). The generator loads it automatically from either source — the key is
never stored in the skill. Model details and the exact API shape are in
`references/nano-banana-2.md` — read it if anything about the API call is unclear.

## Pick the entry path

- **Path A — animate a static asset (the usual case).** The user gives a single
  character/asset image and describes the motion. Generate frames, then convert.
- **Path B — convert an existing sprite sheet.** The user already has a grid of
  frames (their own, or one made earlier). Skip generation; go straight to convert
  (set `--label-crop` if the sheet prints a caption under each frame).
- **Path C — animate an existing video clip.** The user already has the motion — a
  rendered animation, a screen capture, a generated `*.mp4` — and wants it as a
  looping, transparent web asset (e.g. "use the first 2 seconds, drop the
  background, give me a moving SVG/WebP/GIF"). Skip generation: pull frames from the
  clip, key the background with the **ML keyer** (a real video's subject is rarely
  separable by color), montage, then convert. See
  [Path C](#path-c-convert-a-video-clip-into-a-looping-web-asset).

## Choose a generation mode (Path A) — this matters a lot

Nano Banana 2 has no frame-to-frame memory. How you ask for the frames decides
whether the animation is coherent.

- **Mode 1 — single sheet, one call (`generate_spritesheet.py`).** Fast and cheap,
  but the model draws all frames at once with no continuity: identity, size and
  framing drift cell-to-cell. This is **fine for amorphous/organic subjects** — a
  creature, flame, smoke, blob, slime, splash — where the drift reads as natural,
  living motion (the octopus idle loop works beautifully this way).
- **Mode 2 — per-frame from a base plate (`generate_posed_frames.py` +
  `frames_to_sheet.py`).** One call per frame, each an *edit* of the same locked
  base image, changing only what the pose says. Coherent: consistent identity,
  scale, position, and full-body framing. **Use this for anything rigid or
  articulated** — robots, humans, mascots with arms/legs, vehicles, logos — or any
  motion where the body must stay put (waving, walking, nodding, a blink).

Rule of thumb: **if the subject has a fixed skeleton/silhouette, use Mode 2.** A
single-sheet wave on a robot comes out choppy with jumping size and missing legs;
the same robot in Mode 2 stays planted and waves smoothly.

## Inputs you need before starting

1. **The character image** (a file path). If they reference an asset "from the
   website" or paste an image, that's the character.
2. **The motion** — a short description of the animation the user wants
   (e.g. "walk cycle facing right", "idle breathing", "tentacles waving",
   "flickering torch", "spinning coin"). The user drives the motion; if they
   haven't said what it should do, **ask** — don't invent it.

## Mode 1: single-sheet generation (organic subjects)

Iterate cheaply, then finalize at 4K:

```bash
# fast iteration pass at 2K to dial in the motion
python3 scripts/generate_spritesheet.py CHARACTER.png /tmp/sheet_2k.png \
  --motion "<the user's animation>" --rows 6 --cols 6 --size 2K

# final pass at 4K once the look is right
python3 scripts/generate_spritesheet.py CHARACTER.png OUTDIR/sheet_4k.png \
  --motion "<the user's animation>" --rows 6 --cols 6 --size 4K
```

Defaults: 6×6 = 36 frames (≈682px/frame at 4K), `1:1`, model `gemini-3.1-flash-image`.
Use `--aspect 16:9` etc. for non-square characters. Add `--extra "..."` for extra
art direction. `--dry-run` prints the prompt without calling the API.

**Background color — important for light/white characters.** The default white
background only works when the subject is clearly darker/colored than white. If the
character is white, pale, light-grey, or has large bright areas (a white robot, a
snowman, a pale UI icon), white-on-white can't be separated and the keyer will eat
the subject. In that case generate on a **chroma background** the subject doesn't
contain — green is the safe default — and key that out instead:

```bash
python3 scripts/generate_spritesheet.py CHARACTER.png OUTDIR/sheet.png \
  --motion "<motion>" --size 2K \
  --bg-color "vivid chroma-key green (#00B140)"
# ...then convert with the MATCHING key color:
python3 scripts/spritesheet_to_animation.py OUTDIR/sheet.png \
  --bg-color "#00B140" --rows 6 --cols 6 --out-dir OUTDIR --name CHARNAME
```

Pick a chroma the character lacks: green for most things; if the subject is green,
use magenta `#FF00FF`. Avoid black (dark joints/outlines would vanish).

**Always look at the generated sheet before converting** (open it / view it).
Check four things, because the conversion quality depends on them:
1. The frames form a clean, even grid.
2. The background is flat white (no busy scenery, no heavy shadows).
3. The character is recognizably the same in every frame, at the same scale/position.
4. No text, labels, borders, or grid lines crept in.

If it's off, regenerate — image models vary run-to-run. Levers that help:
sharpen the identity wording, restate "flat pure white background, no text/labels/
borders/grid lines", or **reduce the frame count** (5×5 or 4×4) since identity
holds better with fewer frames in one sheet. See `references/nano-banana-2.md`
for model quirks (it outputs JPEG, paints near-white not pure-white, etc.).

## Mode 2: coherent per-frame generation (rigid/articulated subjects)

Use this when the body must stay consistent. It's ~12–24 fast small calls instead
of one big one; at 1K each frame's character is actually *higher* resolution than a
682px cell in a 4K 6×6 grid.

**Step 1 — build a base plate.** Put the real character on a flat chroma canvas,
full body, centered, bottom-aligned, with headroom for raised limbs (so a waving
arm isn't clipped). Use the character's *actual* image — editing it preserves
identity far better than re-drawing from scratch:

```bash
magick -size 1024x1024 xc:"#00B140" \
  \( CHARACTER.png -resize x820 \) -gravity south -geometry +0+24 \
  -composite base_plate.png
```

**Step 2 — author the pose list.** Write `poses.json`: one entry per frame, in
play order, describing the *incremental* change so the frames form a smooth loop.
You write this from the user's motion — it's the creative core. Keep the body
description out of it (the base plate handles that); only state what moves.

```json
[
  {"pose": "Both arms hang at the sides.", "eyes": "Eyes glowing normally."},
  {"pose": "Right arm half-raised, hand at shoulder height.", "eyes": "Eyes glowing normally."},
  {"pose": "Right arm raised beside the head, hand open, waving, tilted left.", "eyes": "Eyes glowing normally."},
  {"pose": "Right arm raised, hand waving, upright.", "eyes": "Eyes closed in a blink — glow off, thin dark lines."}
]
```
Tips: 12–24 frames is plenty; ramp the motion up and back down so frame N loops
into frame 0; put a blink on a single frame (one frame at 12 fps ≈ a natural
blink); name explicit hand tilts (left/upright/right) to make a wave read clearly.

**Step 3 — generate, normalize, convert:**

```bash
python3 scripts/generate_posed_frames.py base_plate.png poses.json \
  --out-dir frames --size 1K --bg "flat solid green (#00B140)" --workers 4

python3 scripts/frames_to_sheet.py frames --cols 4 --rows 4 \
  --bg-color "#00B140" --out norm_sheet.png      # keys + locks scale/position

python3 scripts/spritesheet_to_animation.py norm_sheet.png --keep-bg \
  --cols 6 --rows 4 --fps 14 --out-dir OUTDIR --name CHARNAME \
  --durations "1.4,1.7,1,0.85,0.8,0.85,1.6,..."   # per-frame hold weights (easing)
```

`--cols`/`--rows` must multiply to your frame count (16 → 4×4, 12 → 4×3, 24 → 6×4).
`frames_to_sheet.py` keys the chroma, then plants every frame on a common
feet-baseline and normalizes scale by the leg-stance width, so the character
doesn't bob or pulse. The converter handles non-square cells automatically.

**Make it fluid, not mechanical — use `--durations`.** Uniform frame timing is the
#1 thing that makes an animation feel robotic (see `references/animation-fluidity.md`
for the cited research). Pass one hold *weight* per frame (a weight of 2 holds twice
as long as 1). Hold the slow moments and run the fast ones quickly:
- **anticipation** frame (the wind-up before the action): ~1.6–1.7
- **apex / extreme** poses (top of a wave, peak of a jump): ~1.5
- a held **closed-eye beat** in a slow blink: ~1.4–1.5
- **settle / rest** frames at the loop seam: ~1.3–1.4
- mid-action in-betweens: ~0.8–0.95

Authoring tips (from the research): **12–24 frames**; ramp the motion up and back
down so frame N loops into frame 0; build a wave as an **overlapping cascade**
(shoulder leads → elbow → hand lags a few frames; reverse on the way down, with a
slight shoulder **overshoot** before settling); move limbs along **arcs**, not
straight lines; add one **anticipation** frame before the action. For a natural
**blink**, don't cut open→closed — step through half-closed frames, close a touch
faster than you open, and hold the closed frame a beat for a slow/expressive blink.

**Still preview the frames** (`frames_to_sheet` output, or a montage of `frames/`)
before finalizing — check the motion ramps smoothly and the blink lands.

### Maximize fluidity with motion interpolation (the choppiness fix)

The model can't reliably draw dozens of near-identical frames, so don't try to get
smoothness from frame count alone — generate a modest set of clean **keyframes**,
then synthesize the in-betweens with `interpolate_frames.py` (ffmpeg `minterpolate`,
motion-compensated). This is the research-backed "keyframe-then-interpolate" path and
is what removes choppiness. It works best on **small, smooth motion** (idle,
breathing, blink, gentle sway) and smears on large/fast motion — so for a big move,
keep more real keyframes; for an idle, a few keyframes interpolated heavily is ideal.

```bash
python3 scripts/frames_to_sheet.py frames --cols 6 --rows 2 \
  --bg-color "#00B140" --emit-frames norm_frames --out /tmp/keys.png   # normalize + emit
python3 scripts/interpolate_frames.py norm_frames interp_frames \
  --factor 4 --chroma "#00B140" --max-width 560     # 12 keyframes -> ~44 fluid frames
# montage the interpolated frames into a grid (drop remainder to fit cols*rows):
magick montage $(ls interp_frames/frame_*.png | head -40) -tile 8x5 -geometry +0+0 \
  -background none interp_sheet.png
python3 scripts/spritesheet_to_animation.py interp_sheet.png --keep-bg \
  --cols 8 --rows 5 --fps 16 --out-dir OUTDIR --name CHARNAME
```

Notes: interpolate at a modest `--max-width` (≤~600) — `minterpolate` silently
truncates its output at large resolutions. Interpolation output ≈ `keyframes ×
factor`; pick a grid whose `cols×rows` ≤ that and use the first that-many frames.

**Splitting motion across two "sheets"** is a good way to build a richer idle: make
one pose set for one motion component (e.g. breathing + blink) and another for a
second (e.g. weight sway), generate each, concatenate the frame folders, then
normalize + interpolate the combined set as one loop.

## Path C: convert a video clip into a looping web asset

Use this when the user already has the **motion** in a video and just wants it as a
transparent, looping asset — no generation, no Gemini key needed. The pipeline:

```
video clip ──(video_to_frames.py)──▶ frames ──(remove_bg_ml.py)──▶ transparent frames
   ──(magick montage)──▶ sheet ──(spritesheet_to_animation.py --keep-bg)──▶ SVG · WebP · GIF
```

**Step 1 — pull the frames you want.** Keep the source frame rate so playback
matches the clip (that's what preserves the original fluidity — don't drop frames):

```bash
python3 scripts/video_to_frames.py CLIP.mp4 frames_raw/ \
  --start 0 --duration 2 --size 800     # first 2s, square 800px
```

It prints the frame count and the grid options (cols×rows) that tile evenly — e.g.
48 frames → `8x6`. (A 24 fps clip × 2 s = 48 frames.)

**Step 2 — key the background with the ML keyer.** A real video's subject usually
shares colors with the background (a white robot on a light-grey set), so the color
keyers in `spritesheet_to_animation.py` would eat it. `remove_bg_ml.py` segments by
**shape**, not color, with U²-Net via onnxruntime (no `rembg` install needed):

```bash
python3 scripts/remove_bg_ml.py frames_raw/ frames_cut/
```

First run downloads + caches the model (~176 MB) to
`~/.config/character-animation/u2net.onnx`. Requires `onnxruntime`, `numpy`,
`Pillow`. Levers if the matte needs work: `--alpha-floor` (raise toward `0.12` to
kill a faint halo a same-color background leaves; lower toward `0.03` if a thin part
like an antenna gets nibbled) and `--alpha-ceil`.

> The ML keyer is **reusable beyond video** — point it at any frames or a single
> image when the subject can't be separated by color (a white/pale subject on a
> light background) and a chroma re-shoot isn't possible. Path A/B can use it too.

**Step 3 — montage into a sheet (positions preserved).** Use a plain `montage`, not
`frames_to_sheet.py`: the latter re-centers and scale-normalizes each frame (right
for a planted character), which would fight motion that *moves through the frame* —
a character flying in, a pan. Plain montage keeps every frame exactly where it sat:

```bash
magick montage frames_cut/f_*.png -tile 8x6 -geometry 800x800+0+0 \
  -background none sheet.png        # tile = cols x rows from step 1
```

**Step 4 — convert at the clip's fps.** The frames are already transparent, so pass
`--keep-bg`:

```bash
python3 scripts/spritesheet_to_animation.py sheet.png --keep-bg \
  --cols 8 --rows 6 --fps 24 --display-cell 480 --out-dir OUTDIR --name CHARNAME
```

Notes:
- **Preview the cutouts** (montage `frames_cut/` over a checkerboard) before
  converting — confirm the subject is fully kept, edges are clean, and the early/late
  frames are noise-free.
- A clip that is an **entrance** (subject flies in, fades in) won't loop seamlessly —
  the loop restarts from the empty/first frame. That's expected when you keep a raw
  time slice; tell the user. For a seamless loop, pick a range whose last frame
  matches its first, or use a ping-pong (forward then reverse) ordering.
- For a clip with *small* motion you want even smoother, run `interpolate_frames.py`
  on `frames_cut/` (chroma `none`) before the montage — see the interpolation section.

## Convert the sheet → SVG / WebP / GIF

```bash
python3 scripts/spritesheet_to_animation.py SHEET.png \
  --rows 6 --cols 6 --fps 12 --out-dir OUTDIR --name CHARNAME
```

Produces in `OUTDIR/`:
- `CHARNAME.svg` — self-contained moving SVG (embedded WebP, SMIL frame stepping).
  Opens and loops in any modern browser; ~1 MB.
- `CHARNAME.webp` — animated WebP with true alpha.
- `CHARNAME.gif` — animated GIF (universal; for chat, thumbnails, docs).
- `CHARNAME-sheet.png` — the cleaned, transparent sprite sheet (handy byproduct).

How it works: it removes the white background across the whole sheet with a
connected-components key (clears the background *and* the white trapped between
limbs, while preserving bright specular highlights on the subject), slices the
grid, and builds a viewport that steps across the cells.

Useful options:
- `--fps` playback speed (default 12). Loop length = frames ÷ fps.
- `--label-crop FRAC` hide a caption band under each frame (Path B sheets that
  print "Frame N" etc.). Measure the band height ÷ cell height; ~`0.1` is typical.
- `--keep-bg` skip background removal (subject already transparent, or you want
  the original background).
- `--display-cell PX` per-frame size of the embedded image (default 400) — bump
  for crisper SVG/WebP at the cost of file size.
- Background tuning if needed: `--flood-fuzz` (white-match tolerance, default 12),
  `--white-key` (tight pure-white cleanup, default 3), `--min-region`
  (white blobs below this fraction of pixels are kept as subject highlights).

## Verify the SVG animates

The terminal can't play SMIL, so confirm with a headless render at two points in
the loop and check the frames differ (this also proves the embedded image decoded
and the background is transparent):

```bash
URL="file://$PWD/OUTDIR/CHARNAME.svg"
for ms in 40 1600; do
  google-chrome-stable --headless=new --no-sandbox --disable-gpu \
    --window-size=400,360 --default-background-color=00000000 \
    --virtual-time-budget=$ms --screenshot="/tmp/v_$ms.png" "$URL" >/dev/null 2>&1
done
# view /tmp/v_40.png and /tmp/v_1600.png — they should be different poses
```

Then show the user the GIF (viewable inline) and report all output paths.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Subject is white/pale and gets eaten by bg removal | generate on a chroma bg (`--bg-color "chroma green (#00B140)"`) and key it (`--bg-color "#00B140"`); if you can't re-shoot on chroma (a photo, a **video**, a fixed asset), use the ML keyer: `remove_bg_ml.py` |
| Subject's color matches the background and no color key works (white robot on white, frames from a photo/video) | `python3 scripts/remove_bg_ml.py IN OUT` — shape-based U²-Net matting, then convert with `--keep-bg` |
| Faint grey halo around an ML cutout | raise `remove_bg_ml.py --alpha-floor` (e.g. `0.12`) |
| ML cutout nibbles a thin part (antenna, whisker, cape tip) | lower `--alpha-floor` (e.g. `0.03`) and/or raise `--alpha-ceil` (e.g. `0.98`) |
| Animating a video looks choppy after keying | you dropped frames — re-extract at the source fps (`video_to_frames.py` without `--fps`) and play back at that fps |
| Green fringe/spill on edges (chroma key) | raise `--flood-fuzz` (e.g. 20–25); green-spill suppression is automatic |
| White halo / fringe around the subject (white bg) | raise `--flood-fuzz` (e.g. 16) |
| Holes punched in bright parts of the subject | lower `--white-key` (e.g. 1–2) or raise `--min-region` |
| White patches left between limbs | lower `--min-region` (e.g. 0.00004) |
| Caption text shows in the animation | set `--label-crop` (e.g. 0.1) |
| Frames look offset/clipped | the sheet's grid is uneven — regenerate, or correct `--rows/--cols` |
| Animation is choppy / body changes size / legs appear then vanish | the subject is rigid — switch to **Mode 2** (per-frame from a base plate). Single-sheet generation can't keep a fixed skeleton coherent |
| Character looks squished or stretched | `--rows`/`--cols` don't match the real grid, or cells are non-square (the converter preserves cell aspect automatically — just pass the right grid) |
| Character morphs between frames | regenerate; reduce frame count (5×5/4×4); strengthen identity wording; or use Mode 2 |
| API returns text but no image | safety/refusal — rephrase the motion; see `references/nano-banana-2.md` |

## Notes

- Use **Nano Banana 2** (`gemini-3.1-flash-image`), never the Pro model
  (`gemini-3-pro-image`) — that's a deliberate choice.
- It's a raster animation inside an SVG container: crisp up to roughly the
  `--display-cell` size, and it softens if scaled much larger (the source frames
  aren't vector art).
- The ML keyer (`remove_bg_ml.py`, Path C) needs `onnxruntime`, `numpy` and
  `Pillow`, and downloads the U²-Net model once to
  `~/.config/character-animation/u2net.onnx` (override via `--model` or
  `$CHARACTER_ANIM_U2NET`). It runs on CPU — fine for a couple hundred frames.
  See the worked example in `examples/superhero-mascot/`.
