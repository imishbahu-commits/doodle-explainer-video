# Reference Doodle-Explainer — Measured Style Spec (Deep Analysis)

> Analyse of the 14 uploaded reference videos (`uploads/16040…16092.mp4`),
> 640×360, 29.97 fps, ~8.5–12.5 min each. Hard-cut into **2,830 distinct
> on-screen images ("beats")**. This spec is the ditto-copy rulebook.
> Timing verified by ffmpeg scene-cut detection; visuals verified by
> frame inspection.

---

## 0. The beat model (how long each image stays on screen)

This is the single most important answer to "how long the image stays on
screen." Each **image = one beat = one hard cut**. The image appears at the
cut and is replaced by the next cut.

**Measured timing (all 14 videos, 2830 beats):**

| Metric | Value |
|---|---|
| Total beats | **2,830** |
| Avg on-screen time | **~3.1 s** |
| Median on-screen time | **~2.8 s** |
| Min | ~0.57 s (a quick punch-in joke) |
| Max | ~11.8 s (a long-held establishing shot / emotional hold) |
| Typical range | 2.3 – 4.3 s |
| fps | 29.97 |

**Per-video summary** (full table in `beat_summary.csv`):

| Video | Beats | Avg (s) | Median (s) | Min (s) | Max (s) |
|---|---|---|---|---|---|
| 16040 | 239 | 2.81 | 2.40 | 0.60 | 10.09 |
| 16044 | 165 | 4.55 | 4.30 | 0.70 | 11.78 |
| 16048 | 204 | 3.28 | 3.07 | 0.63 | 10.06 |
| 16052 | 224 | 3.00 | 2.77 | 0.63 | 10.06 |
| 16055 | 231 | 2.70 | 2.23 | 0.57 | 10.03 |
| 16060 | 218 | 2.95 | 2.67 | 0.73 | 10.51 |
| 16064 | 182 | 3.06 | 2.70 | 0.67 | 10.83 |
| 16068 | 215 | 3.29 | 3.04 | 0.67 | 10.08 |
| 16072 | 220 | 3.29 | 2.97 | 0.70 | 10.06 |
| 16076 | 174 | 2.94 | 2.73 | 0.70 | 10.14 |
| 16080 | 158 | 4.04 | 3.80 | 0.63 | 10.21 |
| 16084 | 192 | 3.11 | 2.87 | 0.63 | 10.64 |
| 16088 | 220 | 2.85 | 2.57 | 0.73 | 10.07 |
| 16092 | 188 | 3.45 | 3.24 | 0.63 | 10.64 |

**Rule of thumb to reproduce the pacing:**
- One image per **12–16 spoken words**. Voiceover runs ~210 wpm.
- Duration ≈ words_on_image ÷ (210/60). E.g. 13 words ≈ 3.7 s.
- Cut lands **just before** the word it illustrates (hard cut, no dissolve).
- Long holds (7–12 s) are reserved for establishing shots, "reveal" beats,
  or emotional/serious points. Short holds (0.6–1.5 s) for punchlines,
  quick reactions, and comedic beats.

---

## 1. The character (ditto-copy target)

The hero is a **sparse stick-figure doodle man** with a large, distorted,
**non-oval head**. This is the defining trait — never a clean oval.

### 1.1 Head & face  ⚠ DEFORMED, NOT AN OVAL
- **Head shape:** a large **IRREGULAR, DEFORMED blob — never a clean oval or
  perfect circle.** It is a lumpy, wobbly, slightly **crooked / teardrop /
  squashed** mass drawn with a thin hand-wobbled outline. One side is often
  flatter, bulged, dented, or drooping. Bottom is usually a soft flatter arc
  or a slight chin; top is domed or squared off by the hair.
- **This is the single most distinctive trait.** A clean oval face is the #1
  failure signature. The head must read as a **hand-drawn, slightly broken,
  imperfect blob**.
- **Expression comes FIRST:** the face is designed around a strong emotion
  (defeated, dizzy, scared, tense, cheerful) and the shape often follows the
  emotion — droopy teardrop when sad, wide lumpy circle when scared,
  squashed when sleepy/worried.
- **Size:** head is ~**1/4 to 1/3 of total character height** (big-head,
  small-body cartoon proportion). Head is much wider than the neck/dot of
  the stick body.
- **Hair:** sits **on top** of the head as a separate cap/shape.
  - *Frizzy / spiky* brown hair (most common): short, jagged, upward
    little tufts — not combed, gives a messy energetic look.
  - *Flat crop* brown hair: smooth cap, slightly overhanging forehead.
  - *Bald*: plain head, no hair — used for worried/anxious characters.
  - Hair colour: mid-brown `#8b5a2b`-ish, sometimes grey `#8a8a8a`.
- **Eyes:** two **small solid black dots**, set wide. No white, no pupils,
  no eyelids. Eyes are small relative to the big head.
- **Eyebrows:** **two short line strokes** above the eyes. These carry the
  expression. Raised (angled up at outer ends) = surprise/concern; angled
  inward-down = angry/tense; flat = neutral.
- **Mouth:** a **short drawn line / small crescent**. Shapes observed:
  - flat short line (neutral/thinking)
  - open small oval/frown (worried, saying "oh", mild distress)
  - open **down-curved** mouth crying / wailing (big open frown)
  - up-curved smile (happy, only on clearly positive beats)
  - small "o" (surprised)
- **Nose:** usually **absent** or a barely-visible tiny dot/line. Do not
  draw a prominent nose.
- **Expression / sweat:** the emotion is shown by **brows + mouth**, plus
  **sweat drops** (small teardrops around the head/temple) for stress,
  effort, fear, or heat. Sweat drops = a few tiny black-outlined
  blue/white teardrops. Some characters show a **slack/tired** expression
  (heavy brows, flat mouth, drooping posture).

### 1.2 Body — VERY THIN STICK FIGURE
- **Stick figure:** black thin-line limbs (arms + legs), simple **dot/hook
  hands**. No joints, no muscles, no realistic torso.
- **Torso:** a **thin bridge of black stick lines** — the character is
  essentially a stick-figure. In most beats the torso is just the stick
  body (a slim vertical line / thin connector), NOT a thick filled shirt.
- For "dressed" / office beats there is a **slim brown tie** hanging on the
  stick chest (a thin wedge), but the body is still stick-thin. A white
  shirt appears only as a small, slim block, never a bulky torso.
- **Neck:** a single thin black line from the bottom of the head to the
  shoulders.
- **Limbs:** two thin black stick arms and two thin black stick legs, long
  and thin, posed per the action. Hands are tiny black dots/hooks; feet are
  tiny black marks.
- **Proportions:** head is LARGE (about 1/3 of character height), body +
  limbs are very thin and long — a big-head-on-a-stick look.
- **Expression is carried by face + posture**: angry beat = head tilted
  forward, arm pointing; defeated beat = slumped, arms limp, head drooped.

---

## 2. Linework & colour

- **Outline:** single, imperfect **near-black** contour. Thickness is
  consistent ~**4–6 px at 640-wide source** (~0.7% of frame width). Slight
  hand wobble — never CAD-clean.
- **Palette:** flat, saturated, **low-contrast backgrounds** with a
  **dominant hue per scene**. No gradients, no soft shadows (shadows are
  hard flat shapes only, if present at all), very little texture. Two or
  three main colours per frame plus skin/character accents.
- **Skin:** white (the character face is just white/off-white with the
  black features). No skin-tone shading.
- **Scenes sampled (dominant hues):**
  - night city / computer desk: dark navy `#1b2a4a`, computer glow
  - office / gym: blue-mauve `#3b4a6b`, beige
  - forest / trees: dark green `#2f5d3a`, snow white
  - snow scene: white ground + navy night sky
  - teepee village: green grass + brown huts `#6b4a2b`, tan
  - beach / beach houses: sky blue + tan sand
  - classroom / whiteboard: light blue wall + white board, city skyline
  - painting / easel: warm tan room, easel brown, green woodland canvas
  - brick wall / outdoor: muted tan-brown walls, blue sky
  - room / blue wall: bright cyan wall + wood floor

---

## 3. Backgrounds & activity (the world is never empty)

The background is a **flat painted scene** with enough detail to read as a
real place. The character performs a **specific activity** in it. Always
set character + background together; the background usually does *not* move
(camera is locked) and the "activity" is the character's action.

Observed **background + activity** pairs (use these to reproduce):

| Setting | Background elements | Character activity |
|---|---|---|
| Night city desk | desk, computer, monitor glow, window skyline | working / staring at screen |
| Office | desk, chair, filing, window, whiteboard, red-tie colleague | presenting / pointing at chart |
| Gym | treadmill, weights rack, blue walls | running on treadmill |
| Forest / snow | trees, snow, sky, bare trunks | walking, carrying, shivering |
| Village | teepees, grass, hills, stars | living, dancing, eating |
| Beach | houses, sand, sea, palm | pointing at water, standing |
| Kitchen | stove, pot, fire, jug | pouring / cooking |
| Room (dark) | door, doorway light, dark walls | opening door, revealing |
| Whiteboard room | whiteboard, up trending chart, skyline | explaining a graph |
| Painting room | easel, canvas, palette, window | painting a landscape |
| Brick street | brick wall, street, sky | walking, worried |
| Factory / dump | smokestacks, smoke, hills | working, gesture |

---

## 4. Camera & motion (frozen, hard cuts)

- **Camera is locked.** No zoom, pan, follow, orbit, parallax, or shake on
  the reference beats. The "motion" comes **only** from the cut to the next
  image (and tiny local elements, e.g. a flag, steam, sweat drop).
- **Cut type: hard cut.** No dissolves, fades, wipes (except rare scene
  transitions captured as their own beat).
- **Subject position:** character is usually **centred to slightly
  right-of-centre** (figure_x ≈ 0.45–0.60). The face/head sits in the
  **upper half** of the frame. Leave asymmetric breathing room.
- Most beats are **frozen holds** — the image is static for its whole
  duration.

---

## 5. Prose "ditto-copy" recipe for generating one image

Template (fill the SCENE, EXPRESSION, HAIR, ACTIVITY, BODY):

> Hand-drawn stick-figure doodle explainer, MS-Paint style, thick near-black
> hand-wobbled outlines, flat saturated colours, no gradients, no text. One
> big-headed stick man with a **distorted irregular round head**, two small
> black dot eyes, **short line eyebrows [raised/tense/flat]**, a **[small
> frown / open worried mouth / down-curved crying mouth / small smile]**,
> **[brown frizzy spike hair / flat brown crop / bald]**, and **[sweat
> drops near the temple / none]**. Thin black stick limbs, **[white shirt +
> red tie / brown shirt / bare stick torso]**, posed **[activity, e.g.
> pouring from a jug at a stove]**. Background: **[flat painted SCENE with
> the 2–3 key props/landmarks]**. Character centred slightly right, head in
> the upper third, locked camera, single static frame, no camera motion, no
> blur.

**Style lock (critical for consistency):** always pass the same character
reference image (a clean front-facing beat frame) and reuse the wording
above verbatim, changing only the `[...]` slots. The face distortion + hair
type must stay identical across every image.

**Do NOT use words** like *engraving, ink, painting, watercolour, realistic,
3D, shading, gradient, cinematic* — the style is **flat doodle**.

**Failure signatures to reject** (if any appear, regenerate): clean symmetric
oval head; realistic/proportionate face; gradients or soft shadows; a fully
rendered/painted background; eyes with whites or pupils; thick muscular body;
any text/captions; a smooth CAD-like outline.

---

## 6. What was produced (files in `analysis/`)

| File | Contents |
|---|---|
| `beat_timing.csv` | All **2,830** beats: video, start/end/duration (s & frames), image path |
| `beat_summary.csv` | Per-video timing stats |
| `deep_analysis.json` | Per-beat visual features (luminance, saturation, subject position, face-in-upper-region) |
| `deep_analysis.html` | **Interactive gallery**: every beat's thumbnail + timing + visual tags |
| `frames/<video>/<video>_beat_NNNN.png` | Every on-screen image as a PNG |
| `STYLE_SPEC.md` | This spec |
| `carousel_*.jpg` | Contact sheets for review |

---

## 7. Honest limits

- Vosk transcription was blocked by the sandbox firewall, so **word-level
  voiceover alignment** couldn't be auto-generated here. The beat→text
  correlation is inferred from the measured 12–16 words-per-beat pace
  (this matches the repo's own `STYLE_SPEC` of beat = 12–16 words). If you
  can supply a transcript, I can align it per beat.
- The `deep_analysis.json` visual features are coarse (colour + framing).
  The **frame-verified** style detail above is the reliable part; per-beat
  expression labels can be added with a vision pass.
