# 🧬 STYLE DNA KIT — The Paint Explainer (wipe-proof survival kit)

**Purpose:** if the sandbox wipes `uploads/`, `projects/`, `tools/models/`, or the venv,
everything needed to recreate this channel's style from scratch lives HERE,
committed in git AND pushed to origin so it survives any reset.

**How to use after a wipe (in any new chat):**
1. `git pull` (or clone) → this path exists.
2. Read this file.
3. Read `PROVEN_PROMPTS.md` — the exact image prompts that produced exact-style images.
4. Rebuild the env with the commands in §5.
5. Generate images by pasting a reference crop from `style_locked_crops/` as the
   image-reference + a prompt from `PROVEN_PROMPTS.md`.

---

## 1. THE STYLE IN 3 LINES (what "ditto" means)

1. **Flat 2D doodle on solid white** — giant round head (~45–50% of character height),
   thick black `#101010` outline (~6 px at 1920 = 0.3125% width), tiny dot/oval eyes
   with pupils, thin **black stick limbs**, hands/feet usually omitted, flat fills
   ONLY (no gradients/shadows/textures on characters).
2. **Locked camera + hard cuts** — NO zoom, NO pan, NO parallax, NO dissolve.
   Motion = local layer moves: pose swaps (1 frame), arm/prop rotation
   (0.20–0.45 s, 12–30°), label/prop pops (0.20–0.50 s, scale 0.92→1.00,
   opacity 0→1, ease-out cubic), character slide-in (0.40–0.90 s, 15–35% travel).
3. **Chapters** — persistent white title strip = top **10%** of frame height,
   centered uppercase black hand-lettered text, lasts whole 41–115 s chapter;
   12 chapters/video; no captions/lower-thirds anywhere.

Full measured spec (44 rules, 10 recipe cards, DO/DON'T): `../STYLE_SPEC_IMPLEMENTABLE.md`
(regenerate from `frames/`+`metrics/` if missing — corpus is committed).

---

## 2. REFERENCE FILES THAT MUST NOT BE LOST

| Path | What it is | Evidence for |
|---|---|---|
| `style_locked_crops/ref_blackbeard_char.png` | **PRIMARY crop — character template** (big head, tricorn, beard, stick limbs) | A4 character design |
| `style_locked_crops/ref_sigurd_stick_scene.png` | Stick warrior scene on locked plate | D2/D4 same-canvas reveal |
| `style_locked_crops/ref_willie_door_scene.png` | Room plate + pose swap + red X + yellow label | A5 plate reuse, E1 labels |
| `style_locked_crops/ref_creature_reveal_scene.png` | Creature reveal + lime "All teeth" label | C5 local reveal, D9 |
| `style_locked_crops/ref_contents_pyramid.png` | Cold-open contents mosaic | G1 hook form |
| `../frames/*.jpg` (24) | 5 annotated grabs + contact sheets/video | full corpus |
| `../metrics/*.json` | visual/motion/audio/metrics per video | every number |
| `../cuts/*.csv` | every shot + every edit boundary (841 events) | B1/B3 |
| `../transcripts/*.json` | word-level narration timestamps | narration sync |
| `../CUT_LIST.md`, `../style_rules.json`, `../STYLE_SPEC.md` | full analysis reads | reference |

---

## 3. MEASURED STYLE RULES (compact)

| # | Rule | Value |
|---|---|---|
| 1 | Canvas | 16:9, author 1920×1080 (sources 640×360 / 30 fps) |
| 2 | Stroke | `#101010`, median 2 px@640 = **0.3125% width ≈ 6 px@1920** (env-heavy 12 px) |
| 3 | Wobble | ~1 px lateral @360p; single clean imperfect contour; no sketch scribble |
| 4 | Palette | paper `#F0F0F0`, ink `#101010`; accents red `#E31B23`, yellow `#F0D010`, lime `#C1FF08` |
| 5 | Characters | flat fills, NO gradients/shadows; big head + stick limbs; hands/feet often omitted |
| 6 | Eyes | small oval with black pupil (host) or plain dots; **no white glints** |
| 7 | Mouth | simple line/curve or pink open oval held as pose; **no lip sync** |
| 8 | Median shot | **2.767 s** corpus / **2.50 s** target |
| 9 | Cut classes | 65.52% full-frame hard cut · 29.85% same-palette · 4.64% local swap · **0% dissolve/fade/wipe** |
| 10 | Cut vs word | median **−0.050 s** BEFORE spoken noun; 95.96% in [−0.10,+0.15] s |
| 11 | Motion budget | **46.27% frozen** · 40.83% local · 11.72% subtle · 0.95% slide · **0% camera zoom/pan** |
| 12 | Moving parts/shot | **1–3** (pose, one prop/arm, one label) |
| 13 | Idle | **NONE** (no auto-bob/breathe/blink) |
| 14 | Slide-in | 0.40–0.90 s, 15–35% travel, ease-out cubic, no overshoot |
| 15 | Pop-in | 0.20–0.50 s, scale 0.92→1.00, opacity 0→1, ease-out cubic |
| 16 | Arm/prop | 0.20–0.45 s, 12–30° rotation, 0–3% follow-through |
| 17 | Chapters | 12/video, 41–115 s (median 68.5 s), breath 0.615–0.80 s |
| 18 | Title strip | top ~10% height, white, uppercase black hand lettering (~42–58 px@1080, ≤75% width), persists whole chapter |
| 19 | Labels | red/yellow, ~3–5% frame height, black/white outline, pop or 1-frame swap |
| 20 | Captions | **NONE** — no karaoke, no lower-thirds |
| 21 | Voice | **204–209 WPM target** (corpus median 214.4), steady explanatory TTS |
| 22 | Audio | **−20.6…−20.7 LUFS**, ≤−2.3 dBTP, LRA 1.8–3.8 LU, ambient bed ~18–22 dB under voice, ~117–134 BPM |
| 23 | SFX | restrained: 0.15–0.30 s pop/impact on same frame as reveals; no whoosh every cut |
| 24 | Hook | 1.27–1.87 s contents mosaic → concrete scene → measurable/dated threat in 15 s |
| 25 | Sync | picture shows the EXACT noun ~0.05 s before it is spoken |

---

## 4. PROVEN STYLE-LOCK METHOD

**Do NOT generate from text alone.** Text-only prompts drift (small eyes, thick
limbs, engraving style, gradients). The method that produced exact ditto:

```
STEP 1 — Copy a reference crop into the generator as IMAGE REFERENCE:
   references/paint-explainer-analysis-4v/SURVIVAL_KIT/style_locked_crops/ref_blackbeard_char.png

STEP 2 — Prompt template (fill the SCENE part):
   "Recreate this EXACT drawing style from the reference image: flat 2D doodle
   cartoon on solid white background, one small character centered, giant
   oversized cartoon head with thick black outline and flat pale beige face,
   tiny simple dot eyes, thin black stick-figure legs, flat colors only, no
   shading or gradients, no engraving, no photo. SCENE: <simple scene, one subject + one prop>.
   A flat tan-brown ground strip runs along the bottom with a wavy black outline.
   Thin black title bar strip across the very top of the image, empty, no text."
```

**STEP 3 — Check these 7 failure signatures; regenerate if ANY appear:**
1. small/oval eyes or white glints
2. thick body or shaped limbs instead of thin sticks
3. gradients, shading, hatching, "engraving/photo" look
4. text/letters in the image
5. full hands/feet when reference omits them
6. busy background (rule: ~35–70% negative space)
7. multiple figures overwhelm composition — one subject + one prop

**STEP 4 — Post-process to normalize:** posterize to ≤4 fills; force `#F0F0F0`/`#101010`;
crop borders; resize to 1280×720 stage (25–65% subject width).

---

## 5. ENVIRONMENT REBUILD (after wipe — fully offline, no HuggingFace)

```bash
python3 -m venv /home/user/.venv
/home/user/.venv/bin/pip install -q --upgrade pip
/home/user/.venv/bin/pip install -q kokoro-onnx onnxruntime espeakng-loader phonemizer numpy soundfile pillow imageio-ffmpeg

# TTS model (weights NOT in git; npm allowed):
mkdir -p /tmp/kok && cd /tmp/kok && npm pack expo-kokoro && tar -xzf expo-kokoro-*.tgz
mkdir -p <project>/assets/models
cp /tmp/kok/package/build/kokoro-quantized.onnx <project>/assets/models/
python - <<'PY'
import numpy as np, glob, os
out={}
for f in sorted(glob.glob('/tmp/kok/package/build/voices/*.bin')):
    out[os.path.basename(f)[:-4]] = np.fromfile(f, dtype=np.float32)
np.savez('<project>/assets/models/voices.npz', **out)
print('voices:', len(out))
PY

# ffmpeg + ffprobe:
FF=$(/home/user/.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
sudo cp "$FF" /usr/local/bin/ffmpeg && sudo chmod +x /usr/local/bin/ffmpeg
cd /tmp && npm pack ffprobe-static && mkdir -p fps && tar -xzf ffprobe-static-*.tgz -C fps
sudo cp /tmp/fps/package/bin/linux/x64/ffprobe /usr/local/bin/ffprobe && sudo chmod +x /usr/local/bin/ffprobe
```

**Access rules (verified):** github.com ✅ (git clone), pypi.org ✅, npm ✅,
git LFS/release-assets ❌, huggingface.co ❌, k2-fsa.github.io ❌, apt ❌.

---

## 6. COPY-PASTE PROMPT FOR A NEW CHAT

```
This workspace keeps a committed Style DNA Kit at
references/paint-explainer-analysis-4v/SURVIVAL_KIT/.
1. Read STYLE_DNA_KIT.md and PROVEN_PROMPTS.md before generating anything.
2. Rebuild env using section 5 commands (kokoro-onnx + npm expo-kokoro +
   imageio-ffmpeg for ffmpeg; never HuggingFace).
3. When asked for channel-style images, ALWAYS paste a crop from
   style_locked_crops/ as image reference and use the PROVEN_PROMPTS.md template.
4. Check the 7 failure signatures in section 4; regenerate if any appear.
5. Do not add camera zooms, pans, dissolves, captions, or idle animation —
   measured style is locked camera + hard cuts + local layer moves.
6. Push all new work to the session branch so it survives resets.
```
