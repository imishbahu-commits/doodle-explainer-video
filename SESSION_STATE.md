# SESSION STATE — read me FIRST in any new chat (saves 30+ min)

> A new chat that reads THIS file + the specs it points to can continue
> work immediately WITHOUT re-watching videos or re-installing blind.

## Latest state (commit 88e054e)
Project: **"Why It Sucks to Be Born as a [animal]" channel** → now pivoting to
**face-expression story style** (batch-3 refs).

## What exists where
| Thing | Location |
|---|---|
| 9 batch-3 reference videos (SAFE in git) | tools/ref-videos/ (16060–16092) |
| Reference style analyses (all batches) | tools/style-reports/*.json/.md |
| Batch-3 palette + keyframes | tools/style-reports/batch3-frames/ |
| Batch-3 style micro-grammar | tools/style-reports/BATCH3_STYLE.md |
| Voiceover (703s) + beat marks (222 beats, med 2.96s) | tools/voiceovers/ + tools/style-reports/voiceover-beats.json |
| Face expression sample images (8) | projects/dinzo-samples/assets/char_*.png |
| Upload+analysis studio (videos + voiceovers) | tools/style_lab.py (python3 tools/style_lab.py 8080) |
| Master style specs | MASTER_STYLE.md · references/style-spec-batch2.md |
| Recovery script | quickstart.sh (rebuild .venv: bash quickstart.sh) |

## If sandbox wiped
1. `bash quickstart.sh` (rebuilds venv ~15s)
2. `git reset --hard origin/arena/01a02220-doodle-explainer-video` (restore files)
3. Start servers with the process tool: `python3 tools/style_lab.py 8080`
4. Everything is in git — videos, voice, analysis, images, scripts.

## Next job (user request)
Use the 703s voiceover + 222 beat marks + batch-3 face style:
generate ~10 expression images per turn keyed to beat timings, then build
the video section-by-section (10 beats/turn), frozen camera, face swaps.
