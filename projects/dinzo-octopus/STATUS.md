# dinzo-octopus — production status

Topic: **Why It Sucks to Be Born as an Octopus** (Dinzo format, 16:9)

| Stage | State |
|---|---|
| 1 Script | ✅ `script.md` (10 beats, ~2:33 narration) |
| 1b Beats | ✅ `beats.json` (10 beats) |
| 2 Images | ✅ 10 / 10 (`assets/beat01–10.png`, 1376×768, style-locked hand-drawn) |
| 3 Voiceover | ✅ 10 / 10 (`audio/beat01–10.mp3`, voice-00 masculine deadpan) |
| 4 Animation | ✅ AE-grade keyframes per beat via `skills/ae-motion` (slide-in, punch-in, crawl, pop_boing, wobble, drift, ghost, puppet tentacle drags, motion blur) |
| 5 Assembly | ✅ `dinzo-octopus.mp4` (2:34, 1376×768 @ 30fps, loudnorm −16 LUFS) |
| 6 Studio | ✅ `studio.py` live preview (beat gallery + player) |

## Rebuild commands
```bash
.venv/bin/python make_beats.py        # beats.json <- script.md
.venv/bin/python build_video.py -o dinzo-octopus.mp4   # resumable render+assemble
.venv/bin/python studio.py "Dinzo Octopus" 8080        # live preview
```

## Why octopus (topic research)
- Channel covered reptiles (crocodile) + insects (mosquito) — octopus opens a
  new animal class (cephalopod) with the niche's strongest emotional hook:
  the mother starves to death before you hatch, you're an orphan genius with
  3 broken hearts, and you live ~1 year. No Dinzo episode on octopus/shark;
  the emotional "mother dies" angle is unique to octopus.
- Facts sourced: ScienceAlert (optic gland / senescence), Discover Wildlife
  (4.5-yr brooding record, Graneledone boreopacifica), Weird & Wild (GPO
  guarding 50–70k eggs, no eating), NatGeo anatomy (3 hearts, 9 brains,
  chromatophores).
