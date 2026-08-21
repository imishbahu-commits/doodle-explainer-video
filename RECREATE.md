# RECREATE — how a NEW chat rebuilds the videos in this style

> For a fresh chat: install the repo, read this + MASTER_STYLE.md, and
> recreate any of the reference videos' style.

## 1. Install (one command set)

```bash
cd doodle-explainer-video
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt numpy
.venv/bin/pip install -e ./agent-reach        # optional internet tools
FF=$(.venv/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
ln -sf "$FF" .venv/bin/ffmpeg
```

## 2. The style blueprint

Read **`MASTER_STYLE.md`** — it has ALL the measured numbers (median cut
3.0–3.3 s, frozen 65–77%, zero camera, muted palette). That file is the
authority; the per-video raw data lives in `tools/style-reports/*.json`
+ `*.md` + contact sheets in `tools/style-reports/frames/`.

## 3. If the user re-uploads references

```bash
.venv/bin/python tools/style_lab.py 8080
```
Fast chunked upload portal → auto-analyzes → new reports appear in
`tools/style-reports/`. Compare against MASTER_STYLE.md; if a new video
differs, update MASTER_STYLE.md and re-commit.

## 4. Build a new video in the style

```bash
# A) script -> beats (12-16 words each)
.venv/bin/python projects/dinzo-mammoth/make_beats.py   # (copy pattern)

# B) generate assets: subject PNGs on white + flat backgrounds,
#    muted palette (see MASTER_STYLE.md), keyed with defringe

# C) build (pick the closest template):
.venv/bin/python projects/dinzo-mammoth/keyframe_hunt.py 1 10 -o out.mp4
# or seahorse pattern:
.venv/bin/python projects/dinzo-seahorse/build_seahorse.py 1 10 -o out.mp4

# D) verify against the spec:
.venv/bin/python tools/style_lab.py 8080   # upload out.mp4 -> check stats
```

## 5. Rules that never break (from user feedback, hard-won)

- **Backgrounds NEVER move.** Zero camera zoom/pan on any layer. All
  motion = in-place character puppets or quick entrances/pops.
- **No mid-shot fades in/out** (things popping = glitchy). Characters
  enter by sliding in from off-frame or hard cuts only.
- **No on-screen text/captions** unless asked. Title bar (chapter name)
  is the ONLY persistent text, top 12%, fixed overlay.
- **One spoken beat = one shot = one image** (2–6 s each, 12–16 words).
- **60 fps, hard cuts, loudnorm −16**, quiet bed −19 dB, small SFX only.
- Generate **max 10 assets / 10 voice clips per turn**; part-by-part.
- Style-lock: pass the first accepted image as reference on every later
  generation (same hand).

## 6. Known sandbox quirks

- `.venv` gets wiped between turns — reinstall (step 1) when needed.
- YouTube is blocked (only pypi/github reachable) — use uploaded files.
- Never commit tools/uploads/ (big); commit reports + frames + specs.
