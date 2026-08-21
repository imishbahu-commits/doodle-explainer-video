# dinzo-mammoth — production status

Topic: **The Mammoth Hunt** (stick-figure hunter vs mammoth, rigged action)

| Stage | State |
|---|---|
| Storyboard | ✅ `STORYBOARD.md` (10 beats, chapters THE HUNT / THE THROW / THE FALL) |
| Assets | ✅ 10 generated (2 bg, 4 mammoth poses, blood, dust, rock, spear) |
| Rig | ✅ `rig_hunt.py` — skeletal stick rig drawn per-frame (run cycle 3Hz, wind-up, throw, follow-through), spear projectile w/ gravity, mammoth fall rotation, blood/dust FX |
| Voice | ✅ 10 clips (voice-00) |
| Video | ✅ `dinzo-mammoth-part1.mp4` (49s, 10 beats, 60fps) |

## GitHub research (user asked)
Spine/DragonBones/UnitySpritesAndBones need editors; PyOpenGL skeleton
needs GPU. Used instead: custom per-frame skeletal rig (PIL) — same
approach as github.com/etc-etc89/Animated-Stick-Figure but frame-rendered
at 60fps, plus repo's handdrawn-code philosophy.

## Rebuild
.venv/bin/python rig_hunt.py 1 10 -o dinzo-mammoth-part1.mp4
