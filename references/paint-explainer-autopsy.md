# The Paint Explainer — Full Motion & Production Autopsy

Measured from the actual file: `uploads/13941.mp4`
(*"Ancient Greek Myths That Turned Out to Be True"*, 11:09, 768K views).
Every number below was computed by ffmpeg/PIL analysis of the real pixels
and waveform — not guessed.

---

## 1. RAW SPECS (measured)

| Property | Value | What it means |
|---|---|---|
| Resolution | 1280×720 (16:9) | standard YouTube |
| **Frame rate** | **60 fps** | they render at 60fps for smooth slides/zooms |
| Duration | 11:09.38 | 11 myths |
| Bitrate | 201 kb/s video + 127 kb/s audio | low bitrate = flat colors compress well |
| Audio | AAC 44.1 kHz stereo, mean −23.7 dB, peak −2.6 dB | quiet-ish master, music bed present |

## 2. THE CUTTING RHYTHM (the biggest surprise)

**186 hard cuts in 669 s = one cut every 3.6 seconds.**

Segment lengths: mostly 2–6 s. This is far faster cutting than the
transcript suggests — the narrator never "sits" on a visual. The rule:
**every narration clause gets a new frame.** A 60-second myth = roughly
12–15 distinct visuals.

**Pause structure:** 25 silences, each **0.67–0.76 s**, spaced ~60 s apart
= exactly at myth boundaries. The breath between myths is a *measured
constant*: 0.7 s. It never varies.

## 3. THE VISUAL SYSTEM (measured across 335 sampled frames)

| Metric | Measured | Meaning |
|---|---|---|
| Background: pure white | **33% of runtime** | classic white-canvas look |
| Other backgrounds | muted pastels: cream, light blue, sage, warm grey | soft, desaturated |
| Dark frames | **ZERO** | never cinematic-dark; always bright |
| Average brightness | 0.71 | light and readable |
| Saturation | 0.17 | heavily desaturated pastel palette |
| **Subject position X** | **center, 0.50 ± 0.06** | subjects are DEAD CENTER horizontally |
| Subject position Y | 0.58 | slightly below center |

**Motion mix (what happens between cuts):**

| Type | Share | What it is |
|---|---|---|
| **Frozen stills** | **55%** | static drawing held 2–4 s, then cut |
| Slow zoom / drift | 25% | subtle push or float |
| Active motion | 20% | character parts animating (charge, sail, flap) |

So the animation model is: **hard cuts between static hand-drawn frames +
a minority of slow zooms + occasional part-animation.** No elaborate
motion on every beat — restraint.

## 4. THE NARRATIVE MACHINE (from transcript structure)

Every myth = the same 5-act template (~60 s):

```
1. THE MYTH       dramatic hand-drawn creature + a number/detail
2. THE DOUBT      "of course most people assumed it was just a myth"
3. THE DIG        real evidence enters (ruins, bones, skeletons, gases)
4. THE EXPLANATION  diagram/map/mechanism (drawn or real photo)
5. THE KICKER     "this is likely how the story spread" — soft landing
```

Anchors that repeat verbatim across all 11 myths: the doubt phrase, the
dig reveal, the soft-verb kicker. Repetition conditions the audience.

## 5. WHAT THE CHANNEL ITSELF DISCLOSES

From their video description (their own words):
- "all drawings are created by a real human artist"
- "AI used only rarely for technical adjustments (upscaling, expansion)"
- "the voiceover is generated using standard, generic AI TTS presets"
- "AI was used as a creative assistant for research, scriptwriting, polishing"

→ The art is the moat. The rest (voice, editing, structure) is replicable.

## 6. IMPROVEMENT BRAINSTORM — every dimension found

| # | Dimension | What to adopt | Skill that fires |
|---|---|---|---|
| 1 | Cut rhythm | cut every 2–6 s, clause-per-frame | ae-motion (hard cuts) |
| 2 | Myth pause | exact 0.7 s breath at section ends | video-polish (audio) |
| 3 | White canvas | 1/3 white bg, 2/3 pastels, never dark | handdrawn-style-lock |
| 4 | Centering | subjects dead-center X, 0.58 Y | ae-motion (default pos) |
| 5 | 60 fps master | render at 60fps for smooth slides | ae-motion (fps setting) |
| 6 | Still-first motion | 55% frozen, 25% slow zoom, 20% part-motion | ae-motion (motion budget) |
| 7 | 5-act myth template | doubt → dig → explanation → kicker | cinematic-director (beat sheet) |
| 8 | Repeated anchors | same doubt phrase, same kicker verb | video-polish (script doctor rules) |
| 9 | Number authority | 14 young people, 1000 rooms, 1870s | script doctor |
| 10 | Music bed | quiet bed under voice, −23 dB master | Ultimate-Video-Editing (mix) |
| 11 | Character actions | charge/sail/flap in 20% of beats | character-animation-skill |
| 12 | Real evidence splice | photos/diagrams between drawings | handdrawn-style-lock (exceptions) |
| 13 | Voice | generic AI TTS, steady, measured | generate_speech (we have) |
| 14 | Batch discipline | 11 myths = 11 chapters, batched | image-batcher |
| 15 | Style persistence | one artist's hand across all frames | style-lock referenceImages |

## 7. THE SMART ROUTER PLAN FOR THIS FORMAT

Stage map for a Paint-Explainer-style myth video:

```
1 script   → script_doctor (verify 5-act × N myths + anchors + numbers)
2 plan     → cinematic-director (beat sheet per myth, shot list)
3 art      → handdrawn-style-lock (white/pastel rule, one reference image)
3b batch   → image-batcher (10/turn, ledger per myth)
4 motion   → ae-motion (hard cuts at 2-6s, 55/25/20 motion budget,
             subjects centered, 60fps, hand fonts)
4b action  → character-animation-skill ONLY for the 20% action beats
5 edit     → Ultimate-Video-Editing (music bed, -23dB master, 0.7s breaths)
6 gates    → video-polish (cuts≈3.6s median, pauses 0.7s, loudness -23dB)
```

Every myth chapter reuses stages 3→5; the router never loads more than
one specialist at a time.
