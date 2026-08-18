# Skinny Fat Ape — THE HOOK

Paint Explainer–style hook (~27s spoken) about skinny-fat / body recomp.

## Reproduce

```bash
# repo setup
bash scripts/setup.sh
source .venv/bin/activate
pip install numpy

# keyframe the 10 beats
python projects/skinny-fat-ape/make_hook.py

# meme captions + comedy SFX mix
python projects/skinny-fat-ape/comedy_mix.py
```

Outputs: `final.mp4` then `final_meme.mp4` (gitignored).

## Tools used

| Step | File |
|---|---|
| Script / beats | `script.md`, `beats.json`, `shot-plan.md` |
| AE-style motion | `make_hook.py` + `scenes/*.json` |
| Meme timing score | `MEME_TIMING.md` |
| Post-draw captions/X | `../../tools/meme_draw.py` |
| Mask + draw one ape | `draw_one_meme.py` |
| Code-drawn ape (no image model) | `scenes/one-ape-handdrawn.json` → `doodle.mjs` |
| Comedy SFX mix | `comedy_mix.py` |
| Kokoro-82M helper | `../../tools/kokoro_tts.py` |

Hand-drawn still (rough.js): `assets/one-ape-handdrawn.png` / `.svg`.
