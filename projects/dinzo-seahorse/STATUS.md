# dinzo-seahorse — production status

Topic: **Why It Sucks to Be Born as a Seahorse** (Paint Explainer pro style)

| Stage | State |
|---|---|
| 1 Script | ✅ `script.md` (28 beats, 8–16 words each) |
| 1b Beats | ✅ `beats.json` (28 beats) |
| 2 Art | ✅ 4 painted backgrounds (seaweed/reef/open water/dusk — no white) + 4 character PNGs keyed with defringe (dad/mom/baby/cloud) |
| 3 Voiceover | 🔄 9 / 28 (voice-00; beat 10 blocked by moderation cap → next turn) |
| 4 Animation | ✅ AE-grade per-beat keyframes: camera move on EVERY beat (zoom/drift/punch), character slide-ins (easeOutExpo), pops (easeOutBack), sway bobs, puppet pin drags, motion blur |
| 5 Assembly | 🔄 part 1 = beats 1–9 building (ends on "Now comes the hard part" hook) |
| 6 Studio | ⬜ start after part 1 |

## Rules of this production (from user feedback + Paint Explainer study)
- NO text/captions — picture tells the story.
- NO white backgrounds — every scene is a painted flat-colour illustration.
- One spoken beat = 12–16 words = one shot; hard cuts; voice-synced lengths.
- Camera motion on every beat so nothing is ever a frozen still.

## Rebuild commands
```bash
.venv/bin/python make_beats.py                # beats.json <- script.md
.venv/bin/python build_seahorse.py 1 9 -o dinzo-seahorse-part1.mp4
.venv/bin/python studio.py "Seahorse Part 1" 8080
```

## Facts (sourced)
Britannica (<1 in 200 survive; 100–2,000 eggs; 2–4 week pouch gestation),
HowStuffWorks (male pregnancy, placenta-like lining, labor contractions),
oceanbites (5–2,500 babies, 0.5% survival, abandoned at birth),
DoofyDoodles field notes (morning dance, 5–10 s egg handoff).
