# THE PAINT EXPLAINER — Complete Implementable Animation Style Specification

**Audience:** a developer recreating this channel's exact style with still hand-drawn PNG layers animated by code-driven property tracks (position, scale, rotation, opacity) plus optional puppet-pin deformation — the same keyframe model After Effects uses.
**Author:** senior animation director / motion designer / editor, working from a frame-by-frame measurement package.

---

## 0. SOURCE MATERIAL & METHOD

| Video | Title | Runtime | Source copy |
|---|---:|---|---|
| 15204 | The Deadliest Sea Animal From Every Single Period | 13:25.34 | 640×360, 30 fps |
| 15207 | The Craziest Ways History's Deadliest Warriors Died | 12:36.97 | 640×360, 30 fps |
| 15215 | How You'd Die In Every Prehistoric Era | 14:23.48 | 640×360, 30 fps |
| 15219 | Criminals Who Accidentally Picked the Worst Possible Victims | 14:24.60 | 640×360, 30 fps |

**Total: 4 videos, 54:50.17, 98,705 decoded frames, 11,719 word timestamps, 845 shots, 841 edit events, 24 annotated grabs.**

Method: every source frame decoded at 30 fps; PySceneDetect threshold-18/min-6-frame; per-shot optical registration + residual motion; Vosk word timings; full-audio loudness/LRA/onset analysis. Timing uncertainty ±1 frame = ±0.033 s. Full evidence committed: `metrics/`, `cuts/`, `transcripts/`, `frames/`, `CUT_LIST.md`, `style_rules.json`, `STYLE_SPEC.md`.

> **HEADLINE CORRECTION vs. the brief's assumptions:** across 54:50 there is **zero verified whole-scene zoom, zero pan/follow/orbit/handheld, zero dissolve/fade/wipe.** Motion language = **locked camera + hard cut + local pose/prop/label animation.** The "punch-in" feeling is a *local asset scale pop* on a locked plate.

**Target version:** 15204 (2026-08-16, newest) — marked **TARGET**.

### 0.1 STYLE EVOLUTION (older → newer)

| Measure | 15219 (Jun) | 15215 (Jul) | 15207 (Aug) | **15204 (TARGET)** |
|---|---:|---:|---:|---:|
| Median shot | 2.733 s | 3.617 s | 2.667 s | **2.500 s** |
| Mean shot | 3.500 s | 6.257 s | 3.379 s | **3.412 s** |
| Recognized WPM | 220.49 | 220.14 | 208.63 | **204.30** |
| Integrated LUFS | −17.73 | −18.07 | −20.60 | **−20.68** |
| Majority-white shots | 38.46% | 7.25% | 48.66% | 16.10% |
| Stroke median @640 | 2 px | 4 px | 2 px | 2 px |

Topic (not date) controls art mode: warriors = white history; prehistoric = painted environment; sea = gradient ocean worlds; criminals = incident listicle. **Timing/audio language evolved; art grammar did not.**

---

# PART A — ART & VISUAL STYLE

## A1. Linework
- **Color:** near-black `#101010` (quantized; reads black) — all videos.
- **Width:** median **2 px @640 = 0.3125% of frame width ≈ 6 px @1920**. Environment-heavy (15215): median 4 px @640 → **~12 px @1920**.
- **Joins:** rounded/hand-rounded. **Wobble:** low-amplitude, **~1 px lateral @360p (±0.33% width)**; single clean imperfect contour; **no multi-pass sketch scribble, no hatching clouds.**
- **Consistency:** uniform; characters & props share the same contour grammar (15207 00:17.20–00:19.80; 15219 00:10.00–00:13.00).

## A2. Color

| Property | 15204 (TARGET) | 15207 | 15215 | 15219 |
|---|---:|---:|---:|---:|
| Median brightness | 0.635 | 0.780 | 0.641 | 0.775 |
| Median saturation | 0.559 | 0.125 | 0.325 | 0.156 |
| Colors/frame (median) | 18 | 13 | 22 | 11 |
| Majority-white shots | 16.1% | 48.66% | 7.25% | 38.46% |

- **Core:** `#F0F0F0` paper + `#101010` ink. **Sea world:** `#30D0F0 #1090F0 #1070D0 #105090 #103050 #707050`. **History:** whites/grays `#B0B0B0 #909090 #D0D0D0` + earth `#909070 #B09070`. **Incident:** warm neutrals `#F0D0B0 #D0B090 #909090 #505050`.
- **Emphasis (ALL):** red `#E31B23`, yellow `#F0D010`, occasional lime `#C1FF08` (e.g. "All teeth" label, "Fair fight" variants).
- **Gradients/shadows/textures — CONFIRMED:** characters & props are **FLAT fills, no gradients, no drop shadows**. Gradients reserved ONLY for world plates (ocean depth, sky/lava) and rare soft gray modeling on the host's head. **No texture anywhere.** Contrast high (ink-on-paper ΔL ≈ 0.95); emphasis colors stay <3% frame area.

## A3. Backgrounds
- **White history mode** (15207): solid `#F0F0F0`, flat earth strip at bottom, character centered.
- **Immersive environment** (15215): painted plates (lava/sea/sky) with flat silhouettes on gradient backgrounds.
- **Ocean world** (15204): gradient blue depth plates, olive seabed band.
- **Incident room plate** (15219 00:04–00:13): flat beige room (door, 2 windows) **reused unchanged across 3+ shots**.
- **Depth layers:** 5 (`world → ground → body → arm/prop/effect → label/arrow → title`) — **stacked plates, NO parallax** (no independent background movement verified).
- **Detail level:** low-to-mid; 3–8 distinct fills; deliberate negative space.

## A4. Character design
- **Recurring host head:** ~35–50% frame height close-up (15207 00:31.30); circle/oval, 2 px contour, **outlined dot/oval eyes**, pink open oval mouth held as pose. Narrator disembodied — no lip flap.
- **Generic people** (15219 00:10.00; 15207 00:17.20): circle/oval head **~2.5–3× torso width**, vertical/oval eyes, **stick torso + thin stick limbs**, **hands/feet usually omitted**.
- **Named people** (Sigurd 00:17.20–00:19.80; Blackbeard 10:22.00): hair/beard/helmet/clothing/props = **filled modular shapes** around the same stick skeleton (Blackbeard = black tricorn + red band + beard mass + stick legs).
- **Creatures** (15204 00:08.20–00:17.50; 15215 10:27–10:32): closed silhouettes, outlined eyes, exaggerated teeth/weapon anatomy, 2–4 internal fills.
- **Faces:** expression = **replacement drawing, NOT morph** (neutral → pain/fear/dead as one head asset/overlay set).
- **Shading:** none on characters (flat fill); occasional soft gray on host head only.

## A5. Props & environment
- Same black-contour/flat-fill grammar: Viking helmet+axe, door+windows, giant eye.
- **Reuse is structural:** 15219 room plate unchanged while red X + person swap on it. **Implement plates as reusable layers, never flattened full-frame images.**
- **Typical moving pieces per active shot: 1–3.**

## A6. Composition
| Rule | Value |
|---|---|
| Ink centroid X (all 4) | median 0.497–0.504 ≈ **0.50** |
| Ink centroid Y | median **0.538–0.575** (slightly below center) |
| Subject width | **25–65%** frame; heads 35–45%; hero creatures 45–70% (15204 00:39) |
| Negative space (white scenes) | **35–70%** |
| Title strip | top **10%** height, white, persistent (§E1) |
| Layer order | `world → ground → body → arm/prop/effect → label/arrow → title` |

---

# PART B — EDITING & PACING

## B1. Cut cadence
| Video | Shots | Min | P25 | **Median** | Mean | P75 | P90 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15204 (TARGET) | 236 | 0.467 s | 1.392 s | **2.500 s** | 3.412 s | 3.942 s | 6.367 s | 25.900 s |
| 15207 | 224 | 0.200 s | 1.625 s | 2.667 s | 3.379 s | 3.858 s | — | 20.200 s |
| 15215 | 138 | 0.333 s | 1.800 s | 3.617 s | 6.257 s | 8.458 s | — | 38.133 s |
| 15219 | 247 | 0.533 s | 1.600 s | 2.733 s | 3.500 s | 4.467 s | — | 16.967 s |
| **CORPUS** | **845** | 0.200 s | 1.533 s | **2.767 s** | **3.894 s** | 4.533 s | 8.300 s | 38.133 s |

- **Distribution:** 13.61% <1 s · **70.30% 1–6 s** · 6.51% >10 s. Mostly short beats + a tail of long threat-build shots (4–10 s) + rare 13–38 s set-pieces.

## B2. Cut types — hard cuts only
| Type | Count | % |
|---|---:|---:|
| Hard cut full-frame (≥42% change) | 551 | **65.52%** |
| Hard cut same-palette (18–42%) | 251 | 29.85% |
| Localized one-frame swap/pop (<18%) | 39 | 4.64% |
| **Dissolve/fade/wipe** | **0** | **0.00%** |

## B3. Cut timing vs narration (the money stat)
- **Median cut − word start = −0.050 s** → boundaries placed **1–2 frames BEFORE the emphasized word** (anticipation).
- **94.17% of cuts before nearest word start.** **95.96% in [−0.10, +0.15] s.**
- Examples: 00:01.267 → "during" (−0.023); 00:08.067 → "a" (−0.063); 00:39.233 → "until" (−0.067); 00:40.567 → "ocean" (−0.203, deliberate early outlier).
- **Implementation:** compute each spoken keyword timestamp → key the picture at `word_start − 0.050 s`.

## B4. Section structure
- **12 chapters/video, 41–115 s, median 68.5 s.** Boundary = narrator breath **median 0.615 s / mean 0.738 s** (target 0.6–0.8 s) + **hard cut** to new plate + **persistent title strip**. No black frames, no separate title cards, no music change. Full gap table: `metrics/chapter_timing.json`.

## B5. Long shots for complex/emotional content — yes
| Shot type | Duration | Evidence | Motion |
|---|---|---:|---|---|
| Cold-open mosaic | 1.27–1.87 s | 4 videos 00:00 | hold, then cut |
| Threat build | **4.0–10.0 s** | 15204 00:08.20–00:17.50; 15215 00:12–00:16 | step reveals + label pops |
| Death/desaturation kicker | **10.0 s** | 15204 00:40.57–00:50.60 | state change, hold, cut |
| Hazard escalation | 12.0 s | 15215 00:04–00:16 | multi-hazard on locked plate |
| Long-take outlier | 25.9–38.1 s | 15215 | single plate, layered reveals |

Rule: **jokes/stings = 0.5–2 s shots; builds/emotional = 6–12 s locked-plate reveals.**

---

# PART C — CAMERA LANGUAGE

## C1. Move types present (845 shots)
| Camera class | Count | % |
|---|---:|---:|
| Static/locked (incl. frozen) | 391 | 46.27% |
| Locked plate + local animation | 345 | 40.83% |
| Subtle local motion | 99 | 11.72% |
| Whole-canvas chapter slide | 8 | 0.95% |
| Short graphic sting | 2 | 0.24% |
| Slow zoom / punch-in zoom / pan / tilt / drift / orbit / parallax / handheld / whip | **0** | **0.00%** |

## C2/C3. Zoom parameters — do not exist as camera moves
- Verified zoom distance 0; zoom speed 0; camera `scale = 1.0` default in every shot.
- **What feels like a zoom** = **local asset scale pop**: silhouette → creature → "60 feet" label (15204 09:51.20–09:54.80), creature reveal (00:08.20–00:17.50), giant eye (15215 10:32.00). **Implement on the layer, never the camera.**

## C4. Motion budget
- **46.27% frozen · 40.83% local animation · 11.72% subtle local · 0.95% canvas slide · 0.24% sting · 0% camera-only.**

## C5. "Punch-ins" (local reveal/pop — the real equivalent)
- **~0.20–0.50 s; scale 0.92→1.00; opacity 0→1; position held; ~ease-out cubic; no overshoot; or 1-frame swap.** When: numbers, warnings, arrows, descriptors, new props, "All teeth"-style labels (15204 00:39.00; 15215 00:16.00; 15204 09:51.20–09:54.80).

## C6. Tracking/following — none
- No verified camera follow. When characters "move", **plate stays fixed and elements swap/slide on it** (Sigurd 15207 00:17.20–00:19.80; door 15219 00:10–00:13).

---

# PART D — CHARACTER ANIMATION & RIGGING

## D1. Idle motion — the biggest "don't"
- **No mandatory breathing/bob/sway loop.** Frozen = 46.27%; no regular blink interval; no sinusoidal breathing verified.
- **Default = no idle keys.** If a creature must feel alive: one local **2–4% position/rotation adjustment over 1–3 s**, only when the beat supports it. Never global.

## D2. Entrances (by measured frequency)
1. **Hard cut-on** — default (95.37% of events).
2. **Whole-layer slide** — ~0.40–0.90 s, travel 15–35% frame, **estimated ease-out cubic, no overshoot** (Sigurd 15207 00:17.20–00:19.80; 15219 00:10).
3. **Local reveal/pop** — ~0.20–0.50 s opacity/scale (labels, red X 15219 00:13).
4. **Rare whole-canvas slide** — ~0.70–1.40 s, 8–11% off-center start (0.95%).
- **Motion blur: none visible. Keep PNG edges crisp.**

## D3. Exits — hard cuts only
- No fade-out. Death = swap to dead pose + desaturated plate, hold **0.3–1.5 s**, hard cut (15204 00:40.57–00:50.60; 15215 13:39.37–13:51.57).

## D4. Part animation / rig choice
- **1–3 independently changing elements per active shot:** body/head pose swap, one arm/weapon/jaw/prop layer, one label/arrow/effect.
- **Rigid pieces = separate rotation layer.** **2–4 puppet pins ONLY for soft parts** (tails, tentacles, limbs, body bend). Pose swaps dominate over mesh deformation.

## D5. Walk/gait
- **No reusable walk cycle verified.** Locomotion = whole-figure slide (0.6–0.9 s, ≤2% vertical bounce if code must emulate) or a new pose. Do not build a Disney cycle.

## D6. Faces
- **No lip sync** (host mouth = held open/closed, 15207 00:31.30). **No periodic blink measurable** — leave eyes held. **Expression = one-frame PNG/overlay swap** (neutral → pain/fear/dead, 15215 10:27–10:32). Brows/eyes/mouth = one replaceable face group; **no phoneme morphing.**

## D7. Actions — author 2–4 states
1. anticipation/neutral hold 0.10–0.25 s; 2. action rotation/translation **0.20–0.45 s, fast ease-out**; 3. optional contact pose 1 frame→0.15 s; 4. result pose/label **held until cut**.
- Rigid = separate layer rotation (sword/arm 15207 10:22; door/red X 15219 00:10–00:13). Creature = source swap + local translation (15215 10:27–10:32). **Squash & stretch NOT defining; cap local scale deformation ~4%.**

## D8. Secondary motion — sparse, sentence-driven
- Apply only to tail/fin/beard/loose arm/smoke **involved in the current sentence**. One secondary element in active shot, **zero in frozen shots**. No parallax.

## D9. Effects — one-shot states, not particle systems
| Effect | Evidence | Rule |
|---|---|---|
| Red warning text/arrows | 15204 00:39; 15215 00:16 | local pop or 1-frame swap |
| Smoke/fire/meteor | 15215 00:04–00:16 | loops allowed locally, plate locked |
| Dark/night overlay | 15219 00:04–00:08.47 | state change, plate locked |
| Desaturation/death | 15204 00:40.57–00:50.60; 15215 13:39.37–13:51.57 | sat 1→0, brightness→0.65, hold, cut |
| Bubbles | sea shots | local loop ok |
| Speed lines/impact stars/sweat | **not verified** | do not default |

---

# PART E — TEXT & GRAPHICS

**1. Persistent chapter title strip**
- White strip **~10% frame height** top; centered uppercase black hand-lettered display; lasts **entire chapter (41–115 s)**; cut on with plate. Examples: `CAMBRIAN` (15204 00:10), `SIGURD THE MIGHTY` (15207 00:08), `PRECAMBRIAN` (15215 00:04), `THE AMBULANCE ATTACK` (15219 00:04).
- **Font:** hand-lettered uppercase (`Comic Sans MS Bold`, `Patrick Hand`, or traced custom alphabet) — **not** clean geometric sans. Size ~42–58 px @1080, ≤75% width. Position `x=50%, y=5%`.

**2. Fact/emphasis labels**
- Red `#E31B23` or yellow `#F0D010`, **~3–5% frame height**, black/white outline. Examples: "60 feet", "All teeth", "82-year-old Willie Murphy", "Fair fight".
- **Animation:** 1-frame swap OR ~0.20–0.50 s scale 0.92→1.00 + opacity 0→1 ease-out. **No typewriter.**
- Speech bubbles sparse (gag aid), **not** narration captions (15215 00:12–00:16).
- **Captions/lower-thirds/karaoke: NONE in 54:50. Do not add them.**

---

# PART F — SOUND DESIGN

## F1. Music
- **Continuous low electronic/ambient bed** under narration, full video; **no per-chapter reset** (flat loudness profile).
- Mixed-onset tempo estimate **~117–134 BPM** (117.2 / 133.9 / 125.0 / 125.0) — mixed-track range only; exact clean-stem BPM unavailable.
- **Target:** **−20.6…−20.7 LUFS**, true peak **≤ −2.3 dBTP**, bed **18–22 dB below voice**. Older pair −18.07/−17.73 LUFS (louder, older style).

## F2. Sound effects — restrained
- **Not mix-dominant:** LRA only **1.8–3.8 LU** over full runtimes.
- 20 strongest transients/video stored in `metrics/*.json` (15204 at 02:22.752, 05:01.728, 12:10.592), but flat mix can't separate quiet whoosh from TTS plosives without stems — **honest gap**.
- **Rule:** if used, short **0.15–0.30 s pop/impact on same frame** as reveal/action; below narration; never whoosh every cut.

## F3. Voice
- **Corpus median 214.39 WPM · TARGET 204–209 WPM** (15204: 204.30; 15207: 208.63). Older 220–221 WPM.
- Tone: steady explanatory TTS; continuous flow; designed chapter breaths, not actor pauses. **Chapter breath target 0.60–0.80 s** (measured median 0.615 s / mean 0.738 s; some 1.11–1.29 s).

---

# PART G — STORYTELLING & STRUCTURE

## G1. Hook — first 15 seconds
| Video | 00:00.00 | by 00:08 | by 00:15 |
|---|---|---|---|
| 15204 | pyramid mosaic 1.267 s | predator reveal 00:08.067 | "during the Cambrian period…" |
| 15207 | warrior mosaic 1.767 s | character change 00:07.50 | Sigurd setup |
| 15215 | era mosaic 1.433 s | lava plate + hazards 00:01.43–00:15.70 | second-person "as soon as you land…" |
| 15219 | incident mosaic 1.867 s | night plate 00:03.267, door threat 00:08.467 | dated ambulance-call |

**Hook formula: show the menu briefly (1.3–1.9 s mosaic) → enter one concrete dangerous scene → name a measurable/dated threat inside 15 s.** No logo/no intro; narration starts immediately.

## G2. Narration–visual sync
- Picture **anticipates its spoken keyword by ~0.05 s** and shows the **exact noun/consequence** (creature, person, date, "NO OXYGEN", door state). **Exact noun matching, never metaphorical B-roll.** Keyframes at `word_start − 0.050 s`.

## G3. Recurring motifs & gags
1. Giant recurring host head on white/plates (15207 00:31.30).
2. Red danger text/arrows as death markers (15204 00:39; 15219 00:13 red X).
3. **Silhouette → reveal → scale/fact label** creature grammar (15204 00:08.20–00:17.50; 09:51.20–09:54.80).
4. Ordinary stick person vs. specific threat → reaction/dead state (15215 00:04–00:16; 10:27–10:32).
5. Opening mosaic returns as chapter/menu language — **never as end card**.
6. **Ending:** no end card observed (honest note: confirm last 10 s of 15204 for exact outro).

## G4. Chapter introduction
New title + plate at chapter timestamp with **hard cut**; title persists; narrator names topic after 0.6–0.8 s breath. Every boundary + gap in `metrics/chapter_timing.json`.

---

# PART H — DELIVERABLE

## H1. Final rule table
| # | Rule | Measured value |
|---:|---|---|
| 1 | Canvas | 16:9; 640×360/30 fps source; author 1920×1080 |
| 2 | Timing precision | ±0.033 s (1 frame) |
| 3 | Median shot | **2.767 s corpus; 2.500 s TARGET** |
| 4 | Mean shot | 3.894 s corpus; 3.412 s TARGET |
| 5 | Shot distribution | 13.61% <1 s; 70.30% 1–6 s; 6.51% >10 s |
| 6 | Full-frame hard cut | 551/841 = 65.52% |
| 7 | Same-palette hard cut | 251/841 = 29.85% |
| 8 | Localized swap/pop | 39/841 = 4.64% |
| 9 | Dissolve/fade/wipe | **0 verified** |
| 10 | Cut lead vs word | median **−0.050 s** |
| 11 | Cut-word window | 95.96% in [−0.10, +0.15] s |
| 12 | Frozen shots | **46.27%** |
| 13 | Local animation shots | **40.83%** |
| 14 | Subtle local motion | 11.72% |
| 15 | Whole-canvas slide | 0.95%; 0.70–1.40 s |
| 16 | Camera zoom | **0 verified**; scale 1.0 default |
| 17 | Pan/follow/orbit/handheld | **0 verified** |
| 18 | Moving elements/active shot | **1–3** |
| 19 | Default idle | **none** — no auto-bob/breathe |
| 20 | Lip sync | none |
| 21 | Expression | one-frame face-group swap |
| 22 | Character slide-in | ~0.40–0.90 s; 15–35% travel; ease-out cubic; no overshoot |
| 23 | Local reveal/pop | ~0.20–0.50 s; scale 0.92→1.00; opacity 0→1; ease-out cubic |
| 24 | Arm/prop action | ~0.20–0.45 s; 12–30° rotation; 0–3% follow-through; fast ease-out |
| 25 | Chapters | 12/video, all four |
| 26 | Chapter duration | 41–115 s; median 68.5 s |
| 27 | Chapter breath | median 0.615 s; mean 0.738 s; target 0.6–0.8 s |
| 28 | Title strip | top 10% height; white; persists whole chapter |
| 29 | Stroke width | 2 px@640 = 0.3125% width ≈ 6 px@1920 |
| 30 | Env-heavy stroke | 4 px@640 ≈ 12 px@1920 |
| 31 | Ink centroid | x ≈ 0.50; y ∈ [0.54, 0.58] |
| 32 | Subject width | 25–65% frame; heads 35–45%; heroes 45–70% |
| 33 | Negative space | 35–70% on white scenes |
| 34 | Emphasis colors | red ≈ `#E31B23`, yellow ≈ `#F0D010` |
| 35 | Narration TARGET | **204–209 WPM** |
| 36 | Loudness TARGET | **−20.6…−20.7 LUFS**; ≤−2.3 dBTP; LRA 1.8–3.8 LU |
| 37 | Music | continuous low ambient bed; ~117–134 BPM (mixed estimate) |
| 38 | Captions/lower-thirds | none |
| 39 | Motion blur | none visible — crisp PNG edges |
| 40 | Parallax | none verified |
| 41 | Colors/frame | 11–22 significant (median 13–22 by mode) |
| 42 | Brightness median | 0.635–0.780 by mode |
| 43 | Saturation median | 0.125–0.559 by mode |

## H2. KEYFRAME RECIPE CARDS (10 moves)

### 1. Cold-open contents mosaic
- **When:** first frame. **Duration:** 1.27–1.87 s. **Tracks:** pos(50%,50%), scale 1.0, rot 0, opacity 1 — hold. **Ease:** none (hold → hard cut). **Notes:** narration starts 0:00; no logo/fade.

### 2. Noun-anticipation hard cut
- **When:** new creature/person/place/fact/consequence. **Duration:** 1 frame. **Tracks:** step layer set A→B; camera 1.0. **Timing:** key at `word_start − 0.050 s` (accept −0.10…+0.15). **Notes:** THE signature move — 841 instances.

### 3. Persistent chapter title lock
- **When:** chapter start. **Duration:** full 41–115 s. **Tracks:** strip y=5% (10% height), white bg, centered uppercase, opacity 1; not camera-parented. **Ease:** cut on with plate. **Font:** hand-lettered display ~42–58 px, ≤75% width.

### 4. Same-canvas asset reveal (the "fake punch-in")
- **When:** number/warning/arrow/label/prop. **Duration:** ~0.20–0.50 s. **Tracks:** scale 0.92→1.00, opacity 0→1, pos held; or 1-frame swap. **Ease:** ease-out cubic, no overshoot. **Evidence:** 15204 09:51.20–09:54.80, 15215 00:16, 15219 00:13.

### 5. Whole-canvas chapter slide (rare)
- **When:** occasional chapter reset (0.95%). **Duration:** ~0.70–1.40 s. **Tracks:** start 8–11% off final alignment → center; scale 1.0; rot 0. **Ease:** ease-out cubic. **Notes:** transition, not camera language.

### 6. Character slide-in
- **When:** new participant on established plate. **Duration:** ~0.40–0.90 s. **Tracks:** pos travel 15–35%; scale 1.0; rot 0. **Ease:** ease-out cubic, no overshoot. **Evidence:** 15207 00:17.20–00:19.80; 15219 00:10–00:13.

### 7. Reaction pose swap
- **When:** pain/surprise/death/reveal/joke. **Duration:** 1 frame. **Tracks:** swap neutral→reaction PNG; transforms held. **Ease:** step. **Notes:** face = one replaceable group; no morph (15215 10:27–10:32).

### 8. Arm/weapon/prop action
- **When:** point/strike/lift/attack. **Duration:** 0.20–0.45 s + optional 0.10–0.20 s contact hold. **Tracks:** child rotation 0→12–30°; pos 0–3% follow-through; body fixed. **Ease:** fast ease-out. **Notes:** rigid layer rotation; motion blur off (15207 10:22).

### 9. Threat build on locked plate
- **When:** narration escalates several hazards in one setting. **Duration:** 4.0–10.0 s. **Tracks:** background locked; 2–4 step pose swaps; labels pop sequentially; camera 1.0. **Ease:** step reveals + short ease-out local moves. **Evidence:** 15204 00:08.20–00:17.50; 15215 00:12–00:16.

### 10. Death / desaturation state
- **When:** fatal consequence or chapter kicker. **Duration:** state 0.3–1.5 s; sequences 10.0 s / 12.2 s. **Tracks:** saturation 1→0; brightness→0.65; pose alive→dead PNG; camera 1.0. **Ease:** linear or ease-out; hold then hard cut. **Notes:** optional smoke/bubble overlay; no camera shake.

## H3. DO / DON'T

**DO**
1. DO cut the picture 0.05 s **before** the spoken noun.
2. DO keep the camera locked (scale 1.0) in every shot.
3. DO implement 1–3 moving layers per active shot.
4. DO make expressions one-frame source swaps, not morphs.
5. DO hold frozen shots deliberately (46% of language).
6. DO reuse plates; swap layers on top.
7. DO use hard cuts exclusively; step timing for pose swaps.
8. DO use ease-out cubics for slides/pops; no overshoot unless a joke needs it.
9. DO keep a persistent white chapter strip (10% height) for the whole chapter.
10. DO keep flat fills and crisp edges; effects only where the sentence mentions them.

**DON'T**
1. DON'T add Ken Burns zooms, pans, orbits, or camera drift — zero verified.
2. DON'T use dissolves, wipes, or fade-to-black — zero verified.
3. DON'T add a whoosh to every hard cut — LRA says 1.8–3.8 LU.
4. DON'T auto-bob/breathe/blink idle characters.
5. DON'T lip-sync the narrator to the host.
6. DON'T build walk cycles; slide the figure or swap poses.
7. DON'T flatten plates into full-frame images — reuse layers.
8. DON'T use typewriter/karaoke captions or lower-thirds — none exist.
9. DON'T use clean geometric sans fonts for titles/labels.
10. DON'T add parallax, motion blur, or squash-and-stretch beyond ~4% local.

## H4. Top-5 qualities that make it feel professional (ranked)
1. **Noun-locked anticipation cutting** — 94% of 841 cuts land 0.05 s before the keyword; the eye lands on the noun as it's spoken.
2. **Radical camera restraint** — zero zooms/pans in 54:50; 46% frozen. Confident, editorial pacing, not decorative motion.
3. **Strict, consistent art grammar** — one ink color, one stroke weight, flat fills, world palettes, 11–22 colors/frame.
4. **Persistent chapter spine** — 12 chapters × 41–115 s with 10% strip + 0.6–0.8 s breath; viewer never loses the list structure.
5. **Restrained audio mix** — −20.6 LUFS, LRA 1.8–3.8, bed 18–22 dB under voice, 204–209 WPM. Voice is the whole show.

## H5. Honest gaps
| Gap | Why | What resolves |
|---|---|---|
| Exact easing curves | flattened 30 fps; interpolation baked | project files / 60 fps source |
| Clean music stems/BPM/genre | narration+SFX contaminate onset | stems or un-mixed bed |
| Exact SFX inventory/timing | can't separate quiet whoosh from TTS plosives | stems / clean audio |
| Blink frequency & non-reaction faces | 30 fps + small faces | project files / higher-res |
| Puppet-pin vs source-swap | flattened can't prove authoring | project files |
| True head:body ratios per character | measured on 360p | 1080p masters |
| Outro/end-card anatomy | corpus under-analysis of final 10 s | re-check final 10 s |
| Per-shot hand wobble phase | baked into art | layered source assets |

---

## ANNOTATED EVIDENCE FRAMES
| Grab | Proves |
|---|---|
| `frames/15204-01.jpg` (00:00.50) | G1 hook mosaic; A6 title band |
| `frames/15204-03.jpg` (00:08.20→00:17.50) | local reveal on locked plate; §D9/C5; E1 labels |
| `frames/15207-01.jpg` (00:00.50) | G1; A2 white history mode |
| `frames/15207-03.jpg` (00:17.20→00:19.80) | D2/D4 same-canvas reveal; E1 |
| `frames/15207-05.jpg` (10:22.00) | A4 named-character grammar |
| `frames/15219-03.jpg` (00:10.00→00:13.00) | A5 plate reuse; D4 poses; E1 |
| contact sheets | full corpus cross-check |

---

# TOP-3 TO REPLICATE FIRST (ranked)
1. **Noun-anticipation cut engine** — word-timestamp → cut at −0.050 s pipeline; 94% of the feel for ~5% of the work.
2. **Locked-camera local-reveal motion model** — pop, slide-in, pose-swap cards + 46% frozen; this IS the motion grammar.
3. **Art grammar lock** — `#101010` 6 px@1920 contours, flat fills, world palettes, 10% white title strip, hand-lettered fonts.
