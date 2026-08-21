# The Paint Explainer — measured animation, edit, art, and audio specification

> **Authority:** four user-uploaded reference videos, analyzed 2026-08-21.
> **Use:** implementation with still hand-drawn PNG layers, AE-style property
> tracks (`position`, `scale`, `rotation`, `opacity`) and optional puppet pins.
> **Important correction:** across these four actual files, no sustained
> whole-scene zoom was verified. The dominant system is **locked camera + hard
> cut + local pose/prop/label animation**. This document supersedes earlier
> speculative notes that prescribe routine Ken Burns zooms.

## Evidence package for future chats

A future agent should read these files in this order:

1. [`STYLE_SPEC.md`](STYLE_SPEC.md) — human implementation specification.
2. [`style_rules.json`](style_rules.json) — compact machine-readable rules and
   ten recipe cards.
3. [`metrics/combined.json`](metrics/combined.json) and the four per-video JSON
   files — measured aggregates.
4. [`CUT_LIST.md`](CUT_LIST.md) — all **841** detected edit boundaries.
5. [`cuts/`](cuts/) — machine-readable cut and shot CSVs, including motion class.
6. [`frames/`](frames/) — five annotated evidence grabs per video plus contact
   sheets.
7. [`transcripts/`](transcripts/) — word timestamps and narration text; Vosk
   proper-noun spelling is not authoritative.

## Corpus and protocol

| ID | Video | Uploaded | Runtime | Source copy |
|---|---|---:|---:|---:|
| 15204 | *The Deadliest Sea Animal From Every Single Period* | 2026-08-16 | 13:25.34 | 640×360, 30 fps |
| 15207 | *The Craziest Ways History's Deadliest Warriors Died* | 2026-08-02 | 12:36.97 | 640×360, 30 fps |
| 15215 | *How You'd Die In Every Prehistoric Era* | 2026-07-13 | 14:23.48 | 640×360, 30 fps |
| 15219 | *Criminals Who Accidentally Picked the Worst Possible Victims* | 2026-06-14 | 14:24.60 | 640×360, 30 fps |

**Sound pass:** all 54:50.17 of audio were decoded; 11,719 words received
word-level timestamps; loudness, LRA, transient candidates, pauses and mixed
onset tempo were measured. **Muted/motion pass:** all **98,705** source frames
were decoded. PySceneDetect threshold 18/minimum 6 frames produced 845 shots;
each shot was then sampled for whole-frame registration and residual local
motion. Timing precision is ±1 source frame, or ±0.033 s. Exact thresholds and
hashes are in [`analysis_manifest.json`](analysis_manifest.json).

**Cut terminology:** `hard_cut_full_frame` changes ≥42% of pixels;
`hard_cut_same_palette` changes 18–42%; `localized_swap_or_pop` changes <18%.
The latter is visibly abrupt, but a flattened MP4 cannot prove whether the
artist authored it as an NLE cut or a one-frame layer swap inside one comp.

## Target version and evolution

Use **15204 / 2026-08-16** as the primary current target: persistent chapter
strip, illustrated world plates, 2.50 s median shot, ~204 recognized WPM and
−20.68 LUFS. Use 15207 as the white-history mode, 15215 as the immersive
second-person environment mode, and 15219 as the incident-listicle mode.

| Evolution measure | 15219 Jun 14 | 15215 Jul 13 | 15207 Aug 2 | 15204 Aug 16 | Direction |
|---|---:|---:|---:|---:|---|
| Median shot | 2.733 s | 3.617 s | 2.667 s | **2.500 s** | newest conventional listicles cut faster |
| Mean shot | 3.500 s | 6.257 s | 3.379 s | **3.412 s** | environment video is intentional long-take outlier |
| Recognized WPM | 220.49 | 220.14 | 208.63 | **204.30** | narration slowed ~16 WPM |
| Integrated loudness | −17.73 | −18.07 | −20.60 | **−20.68 LUFS** | newer mix ~2.8 dB quieter |
| Majority-white shots | 38.46% | 7.25% | 48.66% | 16.10% | background follows topic, not date |
| Frozen holds | 44.53% | 37.68% | 47.32% | 52.12% | newest video is most still-first |

The style did **not** evolve linearly from white to painted backgrounds. Topic
controls the mode: warriors return to white at 00:00.00–00:48.23, while the
newest sea video uses gradient ocean worlds from 00:01.27 onward.

---

# PART A — ART & VISUAL STYLE

## A1. Linework

- **Near-black single contour:** quantized frame sampling consistently returns
  `#101010`; visually it reads as black. At 00:08.00 in 15207, the host and
  Sigurd use one clean imperfect outline rather than multi-pass sketching.
- **Measured width:** median black stroke is **2 px at 640-wide** in 15204,
  15207 and 15219: **0.3125% of frame width**. Scale to **~6 px at 1920**.
  Environment-heavy 15215 is thicker: median **4 px at 640** / **~12 px at
  1920** / **0.625% width**, visible on the lava plate at 00:04.00.
- **Consistency:** one object generally uses one weight; internal anatomy can be
  0.5–0.8× the silhouette stroke. At 10:22.00 in 15207, Blackbeard's face,
  beard and sword remain legible with no hatching cloud.
- **Wobble/roughness:** low-amplitude hand wobble, typically ~1 source pixel
  laterally at 360p; rounded hand-made corners, not vector-perfect geometry.
- **No global paper/film texture:** 00:10.00 in 15204 shows a clean blue world
  plate; 00:08.00 in 15207 shows clean white. Texture is drawn into specific
  smoke, ground, fur, rock or water assets only.

Evidence: [`15204-02.jpg`](frames/15204-02.jpg),
[`15207-02.jpg`](frames/15207-02.jpg),
[`15215-02.jpg`](frames/15215-02.jpg).

## A2. Color

- **Core colors:** off-white transcode `#F0F0F0`, near-black `#101010`.
- **Sea mode, 00:01.27–13:18.97 (15204):** cyan/blue ladder
  `#30D0F0`, `#1090F0`, `#1070D0`, `#105090`, `#103050`; olive seabed
  `#707050`. Median sampled saturation **0.559**.
- **History mode, 00:01.77–12:30.60 (15207):** white dominates; earth/stone
  `#B09070`, `#909070`, `#B0B0B0`, `#707070`. Median saturation **0.125**.
- **Prehistoric survival mode, 00:01.43–14:18.57 (15215):** dark gray/olive
  world plates plus cyan skies and red/orange hazards. Median saturation
  **0.325**; lava example at 00:04.00.
- **Incident mode, 00:01.87–14:19.67 (15219):** cream/tan/gray rooms
  `#F0D0B0`, `#D0B090`, `#909090`, `#505050`. Median saturation **0.156**.
- **Accent hierarchy:** red `~#E31B23` marks danger, death, arrows and warning
  copy; yellow `~#F0D010` marks dates, names and numeric facts. Examples:
  15204 at 00:39.00; 15219 at 04:00.00; 15215 at 00:16.00.
- **Colors per frame:** quantized fills with ≥0.5% area: median 18 in 15204,
  13 in 15207, 22 in 15215, 11 in 15219. Implement with 4–10 intentional
  design fills; gradients/compression inflate the measured bucket count.
- **Gradients exist**, but on environments: ocean depth at 00:10.00 (15204),
  sky/smoke at 00:04.00 (15215), sunset/room plates elsewhere. Character bodies
  remain flat, except a soft gray spherical falloff on the recurring host head.
- **Shadows:** no consistent cast-shadow system. Ground contact is a line or
  dark local patch. Night mood is a full-scene dark overlay at 00:04.00–00:08.47
  in 15219, not physically modeled lighting.

## A3. Backgrounds

There are four implementable background modes:

1. **White void:** 48.66% majority-white shots in 15207 and 38.46% in 15219.
   At 00:08.00 in 15207, a host and Viking float on white with only a small
   ground strip. Camera is locked for the 3.20 s shot beginning 00:07.50.
2. **Simple world plate:** sea gradient + seabed at 00:10.00 in 15204; title
   remains on a separate white strip. Plate and camera remain locked during the
   9.87 s threat reveal at 00:08.20–00:17.50.
3. **Full illustrated environment:** lava 00:04.00, forest 04:10.00 and
   Cretaceous attack 10:27.00–10:32.00 in 15215. Detail is concentrated at
   silhouette edges; central staging area stays readable.
4. **Minimal room/exterior plate:** house at 00:04.00 and door sequence
   00:10.00–00:13.00 in 15219. Two or three depth bands: wall/sky, ground/floor,
   foreground prop.

No sustained independent parallax was verified. The only clean global moves
were eight whole-canvas/chapter slides (**0.95% of 845 shots**), typically
0.70–1.40 s. Treat those as transitions, not ongoing camera motion.

## A4. Character design

- **Recurring host:** head is ~35–50% frame height in close-up; body is a thin
  Y-stick; eyes are outlined dots/ovals; mouth is a pink open oval held as a
  pose. See 15207 at 00:31.30. The narrator is disembodied; the host does not
  flap to each syllable.
- **Generic people:** circle/oval head, 2 px source contour, vertical or oval
  eyes, stick torso/limbs, hands and feet usually omitted. 15219 at 00:10.00
  and 15207 at 00:17.20 show this base.
- **Named people:** hair, beard, helmet, clothing and props are filled modular
  shapes around the same stick skeleton. Sigurd at 00:17.20–00:19.80; Blackbeard
  at 10:22.00.
- **Creatures:** more anatomically detailed closed silhouettes, outlined eyes,
  exaggerated teeth/weapon anatomy, 2–4 internal shade fills. Sea creature
  reveal at 00:08.20–00:17.50 in 15204; Cretaceous eye at 10:32.00 in 15215.
- **Faces:** expression is a replacement drawing, not a smooth morph. Eyes,
  brows and mouth change as one head asset or a small set of overlays.

## A5. Props and environment

- Props match the same black-contour/flat-fill grammar: Viking helmet and axe at
  00:17.20–00:19.80 (15207), door/windows at 00:10.00–00:13.00 (15219),
  dinosaur eye at 10:32.00 (15215).
- Reuse is visible inside chapters: the room plate at 00:10.00 and 00:13.00 in
  15219 is unchanged while door markings/people swap. Reuse the plate, not a
  flattened full-frame image, when implementing.
- Typical moving pieces per active shot: **1–3** — body/pose, one arm/prop, one
  label/effect. The flattened video does not justify full-body rigs everywhere.

## A6. Composition

- Measured ink-edge centroid lands at **x≈0.50** in every video: per-video
  medians 0.497–0.504. Y median is **0.538–0.575**, slightly below center.
- Persistent chapter title occupies **top ~10%** of frame; red rectangles in all
  annotated grabs mark the measured band. At 00:10.00 in 15204, world art begins
  directly below it.
- Subject width is typically ~25–65% of frame. Close-up host heads reach ~35–45%
  frame width at 00:31.30 in 15207; hero creatures reach ~45–70% at 00:39.00
  in 15204.
- White scenes preserve roughly 35–70% negative space. Full environments leave
  a lower-center stage or a clear silhouette gap rather than filling every area.
- Layer order: `world → ground → body → arm/prop/effect → label/arrow → title`.

---

# PART B — EDITING & PACING

## B1. Cut cadence

Every detected boundary is listed in [`CUT_LIST.md`](CUT_LIST.md); every shot
with start/end/motion class is in [`cuts/`](cuts/).

| Video | Shots | Events | Min | P25 | Median | Mean | P75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15204 sea | 236 | 235 | 0.467 s | 1.392 s | **2.500 s** | 3.412 s | 3.942 s | 25.900 s |
| 15207 warriors | 224 | 223 | 0.200 s | 1.625 s | **2.667 s** | 3.379 s | 3.858 s | 20.200 s |
| 15215 prehistoric | 138 | 137 | 0.333 s | 1.800 s | **3.617 s** | 6.257 s | 8.458 s | 38.133 s |
| 15219 criminals | 247 | 246 | 0.533 s | 1.600 s | **2.733 s** | 3.500 s | 4.467 s | 16.967 s |
| **Corpus** | **845** | **841** | **0.200 s** | **1.533 s** | **2.767 s** | **3.894 s** | **4.533 s** | **38.133 s** |

Distribution across all shots: **13.61% under 1 s**, **70.30% from 1–6 s**,
**6.51% over 10 s**. Long holds are not automatically static: the 9.87 s
Cambrian reveal at 00:08.20–00:17.50 (15204) updates silhouette/character state
inside one locked plate; 15215 deliberately stages hazards inside longer
illustrated scenes.

## B2. Cut types

- **65.52%** full-frame hard cuts (551/841).
- **29.85%** same-palette hard cuts (251/841).
- **4.64%** localized one-frame swaps/pops (39/841).
- **0 verified dissolves/fades/wipes.** Section changes use hard replacement or
  a rare 0.70–1.40 s whole-canvas slide. See 15219 at 13:21.00–13:26.00 and
  15207 chapter resets at 00:48.23–00:49.60.

## B3. Cut timing versus narration

Across all 841 events, the cut occurs a median **0.050 s before** the nearest
word start: P25 −0.0667 s, P75 −0.0333 s. **94.17%** precede that word;
**95.96%** fall between −0.10 and +0.15 s. This is one-to-two-frame visual
anticipation at 30 fps.

Examples from the complete list:

- 15204: 00:01.267, 0.023 s before “during”; 00:08.067, 0.063 s before “a”.
- 15207: first chapter hard cuts at 00:01.767 and 00:04.167; detailed deltas are
  in `15207-cuts.csv`.
- 15215: noun sync is looser in long scenes; only 91.97% of events fall within
  0.20 s of a word start versus 99.15% in 15204.
- 15219: door/story events at 00:08.467 and 00:13.300 land during the opening
  00:01.87–00:14.30 story build.

**Implementation:** schedule the visual boundary **1–2 frames before** the noun,
number, reveal verb or consequence; do not wait 0.5 s after it.

## B4. Section structure

All four videos use 12 chapters: **48 measured chapters**, 41–115 s, median
**68.5 s**, mean 68.55 s. Each chapter replaces the persistent top title and
world/white plate. No separate full-screen chapter card is required.

Narration boundary breath, measured around 44 usable chapter boundaries:
median **0.615 s**, mean **0.738 s**, P25 0.526 s, P75 1.058 s. Current-target
examples: 00:50.00 boundary into Ordovician has ~1.29 s gap; 04:01.00 into
Carboniferous ~0.60 s; 05:00.00 into Permian ~0.60 s (15204). Full boundary data
are in [`metrics/chapter_timing.json`](metrics/chapter_timing.json).

## B5. Complexity versus shot length

- Simple labels/stings occupy 0.20–0.90 s; examples include clustered warrior
  edits at 01:58.23–01:59.93 in 15207.
- Hero explanations hold 4–10 s while elements are introduced on a fixed plate:
  00:08.20–00:17.50 (15204), 00:12.00–00:16.00 (15215).
- Immersive danger sequences run longer: 15215 median 3.617 s and 27 shots over
  10 s. This is format-driven, not an error.
- Emotional/death moments do not receive cinematic dissolves; they receive a
  pose/dead-state hold, desaturation/darkening, then hard cut. Example:
  13:39.37–13:51.57 in 15215.

---

# PART C — CAMERA LANGUAGE

## C1. Move types present

**Verified normal-shot camera language: locked.** No sustained whole-frame zoom
in/out, pan-follow, tilt, orbit, handheld wobble or whip pan survived the
strict whole-frame registration test across 845 shots.

The measured motion budget is:

| Motion class | Shots | Share |
|---|---:|---:|
| Frozen hold | 391 | **46.27%** |
| Character/graphic animation | 345 | **40.83%** |
| Subtle local motion | 99 | **11.72%** |
| Whole-canvas chapter slide | 8 | **0.95%** |
| Short graphic sting | 2 | **0.24%** |
| Verified sustained whole-scene zoom | 0 | **0.00%** |

At 09:51.20–09:54.80 in 15204, the whale shifts and a “60 feet” label appears,
but seabed/title remain fixed; this is **not** a camera zoom. At
00:08.20–00:17.50 the Cambrian silhouette becomes a detailed creature while the
ocean plate stays fixed.

## C2–C3. Zoom values and speed

No defensible start/end whole-scene scale pair was found. Therefore the coded
default is `camera.scale = 1.0` throughout each shot. Do **not** invent a
1.00→1.10 documentary push as a signature move.

If a non-reference production needs a readability adjustment, make it a new
hard-cut composition. Only use a zoom after intentional creative approval; it
is not measured channel grammar in this four-video corpus.

## C4. Motion budget interpretation

- **46.27% frozen:** all properties held.
- **52.55% local/graphic:** body/prop/label states change while camera stays
  fixed (40.83% active + 11.72% subtle).
- **0.95% virtual global translation:** chapter/canvas slide, not character
  tracking.
- **0% verified camera-only and 0% verified camera-follow shots.**

## C5. Punch-ins

No repeatable whole-scene punch-in was verified. Apparent punches are usually:

1. a hard cut to a closer drawing, e.g. host at 00:31.30 in 15207; or
2. a local asset scaling/pose replacement, e.g. eye close-up at 10:32.00 in
   15215.

Implement emphasis as a one-frame composition cut or a local 0.20–0.40 s prop
pop, not a camera zoom.

## C6. Character tracking

No camera-follow behavior was verified. Characters move inside fixed plates;
the plate does not chase them. The door sequence at 00:10.00–00:13.00 in 15219
and Sigurd reveal at 00:17.20–00:19.80 in 15207 demonstrate this.

---

# PART D — CHARACTER ANIMATION & RIGGING

## D1. Idle motion

There is no mandatory breathing/bob loop. Frozen holds are **46.27%** of shots;
regular blink or sinusoidal body breathing was not verified. A still host at
00:31.30 in 15207 holds the open mouth rather than continuously animating.

**Code default:** no idle keys. If a creature must feel alive, use one local
2–4% position/rotation adjustment over 1–3 s only when supported by the beat;
do not apply it globally.

## D2. Entrances

Observed entrance methods:

1. **Hard cut/cut-on** — default, zero duration. 95.37% of events are full or
   same-palette hard cuts.
2. **Whole-layer slide** — ~0.40–0.90 s, no verified overshoot. Sigurd/foil
   character change at 00:17.20–00:19.80; room participants at
   00:10.00–00:13.00 in 15219.
3. **Local reveal/pop** — ~0.20–0.50 s opacity/scale or one-frame source swap.
   Red/yellow label updates at 00:39.00 in 15204 and 00:16.00 in 15215.
4. **Rare whole-canvas chapter slide** — ~0.70–1.40 s, 0.95% of shots.

Estimated easing from flattened 30 fps: ease-out cubic for slides; step for
pose swaps; no bounce unless a specific joke demands it. Motion blur is not
visible; keep edges crisp.

## D3. Exits

Exits are overwhelmingly hard cuts. Do not fade a character away. For a death,
swap to dead pose/desaturated plate, hold 0.3–1.5 s, then hard cut; examples at
00:40.57–00:50.60 in 15204 and 13:39.37–13:51.57 in 15215.

## D4. Part animation and rig choice

Typical active shot uses **1–3 independently changing elements**:

- body/head pose swap;
- one arm, weapon, jaw or prop layer;
- one text/arrow/effect overlay.

Use separate rotation layers for rigid pieces; use **2–4 puppet pins** only for
soft tails, tentacles, limbs or body bend. The footage more strongly supports
pose swaps than elaborate mesh deformation. Evidence: creature state change
00:08.20–00:17.50 (15204), dinosaur attack/eye replacement
10:27.00–10:32.00 (15215), door/people changes 00:10.00–00:13.00 (15219).

## D5. Walk/gait

No reusable multi-step walk cycle was verified. Locomotion is represented by a
whole-figure slide, a horse/vehicle asset, or a new pose/composition. If code
must emulate it, use two source PNG poses over 0.6–0.9 s with ≤2% vertical
bounce; do not build a Disney walk cycle as the default.

## D6. Faces

- No narration lip sync. Host mouth is a held open/closed expression; see
  00:31.30 in 15207.
- No periodic blink interval can be measured. Leave eyes held unless the beat
  explicitly calls for a reaction.
- Expression change is a one-frame PNG/overlay swap: neutral → pain/fear/dead.
  Cretaceous reaction at 10:27.00–10:32.00 in 15215.
- Brows/eyes/mouth can be one replaceable face group. Do not morph every
  phoneme.

## D7. Actions

Implement an action with 2–4 authored states:

1. anticipation/neutral hold, ~0.10–0.25 s;
2. action layer rotation/translation, ~0.20–0.45 s, fast ease-out;
3. optional contact pose, one frame to 0.15 s;
4. result pose/label hold until cut.

Rigid actions use separate layers: sword/arm at 10:22.00 in 15207, door/marking
at 00:10.00–00:13.00 in 15219. Creature attacks use source swaps plus local
translation: 10:27.00–10:32.00 in 15215. Squash/stretch is not a defining
feature; cap any local scale deformation at ~4%.

## D8. Secondary motion

Secondary motion is sparse, not ambient everywhere. Apply it only to a tail,
fin, beard, loose arm or smoke/effect involved in the sentence. Typical budget:
one secondary element in an active shot, zero in frozen shots. No broad
multi-layer parallax was verified.

## D9. Effects

- **Red warning text/arrows:** 00:39.00 in 15204; 00:16.00 in 15215.
- **Smoke/fire/meteor overlays:** lava sequence 00:04.00–00:16.00 in 15215.
- **Dark overlay/night state:** 00:04.00–00:08.47 in 15219.
- **Desaturation/death state:** 00:40.57–00:50.60 in 15204.
- **Speech bubbles/labels:** appear as local one-frame or 0.2–0.5 s updates;
  there is no persistent caption system.

Prefer one-shot state changes over looping particle systems. Bubbles, smoke or
fire can loop locally when the environment requires them, but effects do not
move the camera.

---

# PART E — TEXT & GRAPHICS

- **Chapter title:** always present in a white strip ~10% frame height,
  centered uppercase black hand lettering. It lasts the entire 41–115 s
  chapter. Examples: CAMBRIAN at 00:10.00 (15204), SIGURD THE MIGHTY at
  00:08.00 (15207), PRECAMBRIAN at 00:04.00 (15215), THE AMBULANCE ATTACK at
  00:04.00 (15219).
- **Font approximation:** use a hand-lettered uppercase display such as
  `Comic Sans MS Bold`, `Patrick Hand`, or a traced custom alphabet—not a clean
  geometric corporate sans. Production title size: ~42–58 px at 1080,
  adjusted to fill ≤75% width.
- **Fact labels:** red or yellow hand lettering, commonly ~3–5% frame height;
  black or white outline for contrast. 00:39.00 in 15204 and 04:00.00 in 15219.
- **Speech bubbles:** sparse, character-specific gag/action aid; not narration
  captions. 00:12.00–00:16.00 in 15215 shows labels rather than a lower-third.
- **Captions:** none. No karaoke, lower-third, or persistent subtitles were
  observed in 54:50.
- **Animation:** title generally cuts on with the plate. Labels use one-frame
  swap or estimated 0.20–0.50 s scale/opacity ease-out. No typewriter effect was
  verified.

---

# PART F — SOUND DESIGN

## F1. Music

The mixed onset estimator returns 117.19, 133.93, 125.00 and 125.00 BPM; use
**~117–134 BPM** only as a mixed-track range because narration/SFX contaminate
the estimator. The audible-system implementation is a continuous, low,
electronic/ambient bed; no per-chapter theme reset is supported by the flat
loudness profile.

Measured masters:

| Video | Integrated | True peak | LRA | Recognized WPM |
|---|---:|---:|---:|---:|
| 15204 | −20.68 LUFS | −2.31 dBTP | 1.8 LU | 204.30 |
| 15207 | −20.60 LUFS | −2.77 dBTP | 2.0 LU | 208.63 |
| 15215 | −18.07 LUFS | −0.17 dBTP | 3.8 LU | 220.14 |
| 15219 | −17.73 LUFS | −0.02 dBTP | 3.3 LU | 220.49 |

**Current target:** mix to ~−20.6 to −20.7 LUFS, true peak ≤−2.3 dBTP, bed
roughly 18–22 dB below voice. The newer mix is ~2.8 dB quieter and flatter than
the June/July pair.

## F2. Sound effects

SFX are not mix-dominant: LRA remains only 1.8–3.8 LU over full runtimes. The
analysis stores the 20 strongest transient candidates per video in each metrics
JSON—for example 15204 includes 02:22.752, 05:01.728 and 12:10.592—but the flat
mix cannot reliably distinguish a quiet whoosh from TTS plosives without stems.

Implementation rule: if used, place a short 0.15–0.30 s pop/impact on the same
frame as a local reveal or action; keep it below narration and do not add a
whoosh to every hard cut. This restrained rule matches the measured low LRA;
exact per-effect inventory remains an acknowledged gap.

## F3. Voice

- Corpus median recognized delivery: **214.39 WPM**.
- Current target: **204–209 WPM**, measured across 00:00–13:25 (15204) and
  00:00–12:36 (15207).
- Older delivery: **220–221 WPM**, 15215/15219.
- Tone: steady explanatory TTS; sentence flow is continuous, with designed
  chapter breaths rather than dramatic actor pauses.
- Chapter breath target: **0.60–0.80 s**; measured corpus median 0.615 s and mean
  0.738 s. Some current-target boundaries extend to 1.11–1.29 s.

---

# PART G — STORYTELLING & STRUCTURE

## G1. First 15 seconds

All four begin with a **1.27–1.87 s contents mosaic**, then immediate story—not
a logo animation:

- 15204 00:00.00–00:01.267 pyramid → “during the Cambrian period…”; by
  00:08.067 a predator reveal begins.
- 15207 00:00.00–00:01.767 warrior mosaic → Sigurd biography/death setup;
  characters change at 00:07.50 and 00:10.70.
- 15215 00:00.00–00:01.433 era mosaic → second-person “as soon as you land…”;
  lava plate by 00:01.433 and hazard states through 00:15.70.
- 15219 00:00.00–00:01.867 incident mosaic → a dated ambulance-call story;
  night plate by 00:03.267 and door threat by 00:08.467.

Hook formula: **show the menu briefly → enter one concrete dangerous scene →
name a measurable/specifically dated threat inside 15 s.**

## G2. Narration–visual sync

The image generally anticipates its nearest spoken keyword by ~0.05 s. Picture
shows the exact noun or consequence: creature at 00:08.20–00:17.50 (15204),
Sigurd/foe at 00:17.20–00:19.80 (15207), “NO OXYGEN” by 00:16.00 (15215),
door state by 00:13.00 (15219). Use exact noun matching, not metaphorical B-roll.

## G3. Recurring motifs and gags

- giant recurring host head on white or over world plates: 00:31.30 (15207);
- red danger/fatality text and arrows: 00:39.00 (15204);
- silhouette → reveal → scale/fact label: 00:08.20–00:17.50 and
  09:51.20–09:54.80 (15204);
- ordinary stick person against a specific threat, then reaction/dead state:
  00:04.00–00:16.00 and 10:27.00–10:32.00 (15215);
- opening mosaic returns as chapter/menu visual language, not as an end card.

## G4. Chapter introduction

A new title and plate arrive at the chapter timestamp, usually with a hard cut;
chapter title persists. The narrator says the period/person/case after a
0.60–0.80 s breath. Chapter durations are listed in the manifest; every
boundary and word gap is in `chapter_timing.json`.

---

# PART H — QUANTIFIED DELIVERABLE

## H1. Final rule table

| # | Rule | Measured/implementation value |
|---:|---|---|
| 1 | Canvas | 16:9; measured 640×360; author at 1920×1080 |
| 2 | Timing evidence | 30 fps source; ±0.033 s; keyframe times are frame-independent |
| 3 | Median shot | **2.767 s corpus**; current target **2.500 s** |
| 4 | Mean shot | 3.894 s corpus |
| 5 | Shot distribution | 13.61% <1 s; 70.30% 1–6 s; 6.51% >10 s |
| 6 | Full-frame hard cuts | 551/841 = **65.52%** |
| 7 | Same-palette hard cuts | 251/841 = **29.85%** |
| 8 | Localized swap/pop | 39/841 = **4.64%** |
| 9 | Dissolves/fades/wipes | **0 verified** |
| 10 | Cut lead | median **−0.050 s** before nearest word start |
| 11 | Cut-word window | 95.96% between −0.10 and +0.15 s |
| 12 | Frozen motion budget | **46.27%** of shots |
| 13 | Active local/graphic | **40.83%** |
| 14 | Subtle local motion | **11.72%** |
| 15 | Whole-canvas slide | **0.95%**, ~0.70–1.40 s |
| 16 | Sustained camera zoom | **0 verified**; camera scale 1.0 default |
| 17 | Pan/follow/orbit/handheld | **0 verified** |
| 18 | Typical moving pieces | **1–3** per active shot |
| 19 | Default idle | none; do not auto-bob/breathe |
| 20 | Lip sync | none |
| 21 | Expression change | one-frame source/face-group swap |
| 22 | Character slide | ~0.40–0.90 s, ~15–35% frame travel, estimated ease-out cubic |
| 23 | Local label/prop pop | ~0.20–0.50 s, scale ~0.92→1.00 or one-frame swap |
| 24 | Arm/prop action | ~0.20–0.45 s, 12–30° rotation, fast ease-out |
| 25 | Chapter count | **12/video** in all four |
| 26 | Chapter duration | 41–115 s; median **68.5 s** |
| 27 | Chapter breath | median **0.615 s**, mean 0.738 s |
| 28 | Title strip | top **~10%** frame, white, title persists whole chapter |
| 29 | Stroke width | median **2 px/640 = 0.3125% width = ~6 px/1920** |
| 30 | Environment-heavy stroke | median **4 px/640 = ~12 px/1920** |
| 31 | Ink centroid | x≈0.50; y≈0.54–0.58 |
| 32 | Majority-white shots | 29.82% weighted corpus; mode range 7.25–48.66% |
| 33 | Accent colors | red danger `~#E31B23`; yellow fact `~#F0D010` |
| 34 | Current narration | **204–209 WPM** |
| 35 | Current loudness | **−20.6 to −20.7 LUFS**, ≤−2.3 dBTP |
| 36 | LRA | 1.8–3.8 LU; flat, controlled mix |
| 37 | Mixed onset tempo | ~117–134 BPM; exact music-stem BPM unavailable |
| 38 | Captions/lower thirds | none |
| 39 | Motion blur | none visible; crisp PNG edges |
| 40 | Parallax | none verified as recurring grammar |

## H2. Keyframe recipe cards

### 1. Cold-open chapter mosaic

- **Use:** first frame of a list/era/case video.
- **Evidence/duration:** 15204 00:00.000–00:01.267; 15207 to 00:01.767;
  15215 to 00:01.433; 15219 to 00:01.867.
- **Tracks:** `pos=(50%,50%)`, `scale=1.00`, `rot=0`, `opacity=1`.
- **Ease:** none; hold, then hard cut.
- **Audio:** narration starts immediately; no logo pause.

### 2. Noun-anticipation hard cut

- **Use:** new creature/person/place/fact/consequence.
- **Duration:** one frame.
- **Tracks:** step entire layer set A→B; no interpolation.
- **Timing:** key at spoken-word start −0.050 s; acceptable −0.10…+0.15 s.
- **Evidence:** 841-event measured median; first 15204 boundaries at
  00:01.267, 00:06.133 and 00:08.067.

### 3. Persistent chapter title lock

- **Use:** every chapter.
- **Duration:** full 41–115 s chapter.
- **Tracks:** strip `posY=5%`, `height=10%`, `opacity=1`; text centered;
  no camera parent.
- **Ease:** cut on with plate.
- **Evidence:** 15204 00:10.00; 15207 00:08.00; 15215 00:04.00;
  15219 00:04.00.

### 4. Same-canvas asset reveal

- **Use:** number, warning, arrow, label, prop.
- **Duration:** ~0.20–0.50 s.
- **Tracks:** `scale 0.92→1.00`, `opacity 0→1`, position held; or one-frame
  source swap when punchier.
- **Ease:** estimated ease-out cubic; no mandatory overshoot.
- **Evidence:** 15215 00:12.00–00:16.00; 15204 09:51.20–09:54.80.

### 5. Whole-canvas chapter slide

- **Use:** rare chapter reset only; 0.95% shot frequency.
- **Duration:** ~0.70–1.40 s.
- **Tracks:** start translated 8–11% beyond final alignment; end centered;
  scale 1.0; rotation 0.
- **Ease:** estimated ease-out cubic.
- **Notes:** transition, not camera language; do not repeat within every scene.

### 6. Character slide-in

- **Use:** new participant on an established plate.
- **Duration:** ~0.40–0.90 s.
- **Tracks:** `pos` travels 15–35% frame; `scale=1`; `rot=0`; opacity held.
- **Ease:** estimated ease-out cubic, no overshoot.
- **Evidence:** 15207 00:17.20–00:19.80; 15219 00:10.00–00:13.00.

### 7. Reaction pose swap

- **Use:** pain, surprise, death, joke.
- **Duration:** one frame / 0.033 s at source.
- **Tracks:** swap `neutral.png`→`reaction.png`; all transforms held.
- **Ease:** step.
- **Evidence:** 15215 10:27.00–10:32.00; host pose at 15207 00:31.30.

### 8. Arm/weapon/prop action

- **Use:** point, strike, lift, attack.
- **Duration:** 0.20–0.45 s action + optional 0.10–0.20 s contact hold.
- **Tracks:** child rotation 0→12–30°; local position 0–3% follow-through;
  body remains fixed.
- **Ease:** fast ease-out; no elastic bounce.
- **Rig:** separate child PNG or 2–4 pins.
- **Evidence:** Blackbeard asset 10:22.00 (15207); modular incident actions
  throughout 04:00–04:47 in 15219.

### 9. Threat build on locked plate

- **Use:** narration escalates multiple hazards in one setting.
- **Duration:** 4–10 s.
- **Tracks:** camera held at 1.0; sequence 2–4 character/prop source swaps;
  labels pop separately.
- **Ease:** step for poses, short ease-out for moving props.
- **Evidence:** 15204 00:08.20–00:17.50; 15215 00:12.00–00:16.00.

### 10. Death/desaturation state

- **Use:** fatal result/chapter kicker.
- **Duration:** 0.30–0.80 s state change, then hold to cut.
- **Tracks:** saturation 1→0; brightness 1→0.65; alive→dead PNG; camera 1.0.
- **Ease:** linear or ease-out; no camera shake.
- **Evidence:** 15204 00:40.57–00:50.60; 15215 13:39.37–13:51.57.

## H3. DO / DON'T

### DO

1. Cut 1–2 frames before the noun (−0.050 s median evidence).
2. Keep the camera locked; animate only the necessary local layer.
3. Allocate ~46% frozen shots and ~41% clearly active local shots.
4. Keep most shots 1–6 s; aim ~2.5–2.8 s median.
5. Draw one near-black contour at ~0.31% frame width.
6. Keep chapter title in the top 10% for the full chapter.
7. Center the ink mass near x=0.50, y=0.54–0.58.
8. Use red only for danger/emphasis and yellow for facts/dates.
9. Reuse world plates while swapping 1–3 modular foreground pieces.
10. Leave 0.60–0.80 s breathing room at chapter boundaries.

### DON'T

1. Do not add default Ken Burns zooms; zero were verified.
2. Do not fade/dissolve between beats; use hard cuts.
3. Do not lip-sync disembodied narration.
4. Do not apply idle bob/blink loops to every character.
5. Do not animate 6–10 independent parts when 1–3 communicate the beat.
6. Do not use cinematic shadows, film grain or 3D lighting on characters.
7. Do not use gradients inside character bodies as the default.
8. Do not add karaoke captions or lower-thirds.
9. Do not follow moving characters with the camera.
10. Do not bounce/overshoot every entrance; reserve exaggeration for a real gag.

## H4. Five qualities that make it feel professional/expensive

1. **Frame-accurate noun anticipation.** 841 boundaries lead the nearest word by
   0.050 s median; the viewer sees meaning as it is spoken, not after it.
2. **Motion restraint.** 46.27% frozen, zero verified sustained camera zooms;
   movement has a narrative job instead of being decoration.
3. **Persistent design system.** Top 10% title strip and near-black 0.31%-width
   contour survive every topic, from 00:10.00 sea to 00:04.00 night incident.
4. **Modular illustration staging.** Fixed plates plus 1–3 changing pieces make
   00:08.20–00:17.50 and 00:10.00–00:13.00 feel authored, not slideshow-random.
5. **Industrial chapter rhythm and controlled audio.** 12 chapters/video,
   68.5 s median, 0.615 s breath, current −20.6 LUFS master.

## H5. What still cannot be measured

1. **Exact easing curves:** flattened 30 fps frames reveal trajectory, not AE
   Bézier handles. Project files or 60/120 fps originals are needed.
2. **Original delivery frame rate:** supplied derivatives are 30 fps; YouTube
   may have down-converted a higher-frame-rate master.
3. **Exact layer/pin topology:** source PNGs and AE project are needed to know
   whether a change is mesh warp, child rotation or replacement drawing.
4. **Localized pop versus NLE cut:** 39 abrupt events change <18% of pixels; the
   flattened output cannot expose comp boundaries.
5. **Clean music BPM/genre and exact SFX count:** no stems. Mixed onset tempo is
   117–134 BPM, but narration plosives contaminate it.
6. **Font identity:** the rendered title resembles hand lettering; source font
   files or artist alphabet are needed for exact glyph matching.
7. **Stroke width before 360p resampling:** values are measured after transcode;
   1920 values are proportional estimates.
8. **Off-screen reuse across unsupplied videos:** four videos establish strong
   rules but cannot prove every channel exception.

# Ranked top three things to replicate first

1. **Hard-cut noun sync:** new picture 1–2 frames before the word; median shot
   2.5–2.8 s.
2. **Locked-camera modular PNG staging:** ~46% frozen, active shots change only
   1–3 character/prop/label layers—no routine camera zoom.
3. **Brand lockup:** top 10% persistent chapter title, centered composition,
   near-black ~0.31%-width outline, white/topic-colored flat worlds, red/yellow
   emphasis only.
