# The Paint Explainer — Complete Animation Style Specification (2026)

> User-provided analysis (vision AI, frame-by-frame), target = "The
> Deadliest Sea Animal From Every Single Period" (x2x0kjTBs48, 2026-08-16,
> 13:25, 1920×1080, 60 fps). This file is the AUTHORITY for builds.
> Engine: still hand-drawn PNGs + AE-style keyframe tracks (pos/scale/
> rot/opacity + puppet-pin deformation).

## Target version (ship this look)
Fully illustrated explainer: white canvas or simple painted water,
persistent chapter title bar, inked creatures, host stick-scientist,
hard cuts, slow zooms. Older 2025 listicle grid = secondary mode only.

## PART A — ART

| Property | Value |
|---|---|
| Stroke | pure black #000; ~8 px @1920 (=~5.7 px @1376); stick strokes ~5 px; panels ~10 px; round joins |
| Wobble | low — one clean contour, no sketch-scribble |
| Gradients | YES on water/sky/ground bands only (cyan→deep blue vertical); NOT on characters |
| Shadows | almost none (host skull soft gray radial ~10–15%) |
| Texture | limited speckle fills; teeth/eyes get 1 highlight |
| White canvas | #FFFFFF, no paper grain |
| Sea palette | top #5EE0D8→#3ABBCC, mid #1F789D/#2A7CB8, deep #0B3A6A, floor #C4C48A/#8A8A3A/#5A5A28 |
| Accent | #E31B23 (arrows, "Extinction" stamp) |
| Mouth fill | #F48FB1, tongue #E07090 |
| Colors/frame | 4–8 distinct fills + black + white |

Backgrounds — ONLY these 3 modes:
- A. White void (host/stick gags). No motion, characters float.
- B. Title-bar + gradient world (chapter body). Gradient zooms WITH camera
  (locked), seafloor optional 2nd layer at 0.7× camera scale. Max 2 layers.
- C. Card mosaic on white (2025 cold open). Scale 1.00→1.08–1.25.

Title bar (target): white full-width strip, top 10–12% of frame (~108–130
px @1080). Chapter name centered, black, rounded-hand sans, ALL CAPS,
weight 700. World clipped below strip. On white-void shots the title
floats top without bar.

Characters:
- Host: head:body ≈ 1.6:1, head ≈ 38–42% frame height; downward-arc eyes
  (no pupils); rectangle glasses; open pink oval mouth (held pose, not
  visemes); tiny lab coat, stick arms, triangle pointer.
- Stick humans: circle head 12–18% (two-shot) / 35–45% (close-up); vertical
  dash eyes; Y-stick body; no hands/feet; hair = 1–3 filled blobs.
- Creatures: closed silhouettes, cartoon anatomy readable at 50%, disc
  eyes + pupil + optional iris, white triangle teeth, exaggerated weapons.

Composition: 16:9 1920×1080; subject center or slightly low-center; host
left-third; icon creature 45–70% frame width; generous margins (20–30%
empty); layering = bg → bands → chars → arrows/labels → title.

## PART B — EDITING

| Metric | Value |
|---|---|
| Cut cadence | median 3.17 s, mean 4.71 s, p25 1.5 s, p75 6 s; right-skewed |
| Default shot | ~3.0 s; stings 0.5 s; hero holds 12–25 s |
| Cut type | hard cuts 99%+; NO dissolves/wipes/fades; chapter change = hard cut + title swap |
| Title sync | title lands on or 0.0–0.3 s BEFORE spoken name; creature on the noun (+0.0–0.2 s); arrow on feature (+0.0–0.15 s); jokes +0.1–0.3 s after clause. NEVER lag 0.5 s+ |
| Chapters | 6–12 per video, each 60–90 s |

## PART C — CAMERA (motion budget)

- ~50% camera locked + character/puppet only
- ~35% slow zoom in/out ("Ken Burns on a drawing")
- ~12% punch-in for nouns/arrows/openers
- ~3% true static; ~0% pan/orbit/tilt/handheld

Zoom recipe: net scale 1.09× over ~5.2 s → ~2.6 %/s (p90 6 %/s); easing
ease-in-out (0.42,0,0.58,1); anchor = subject eye or frame center.
Zoom-out: net 0.78× over 4.4 s (−4.4 %/s).
Punch-in: 0.35–0.55 s, 1.00→1.12–1.22, ease-out, NO overshoot (except
joke pops 8–12% overshoot).

## PART D — CHARACTER / PUPPET

- Idle: stick = none or bob 1.5% head height @0.35 Hz; host 0.4 Hz 1–2%
  Y-only; creatures ALWAYS swim idle (pin-wave 0.6 Hz).
- Entrances: cut-on is default (hard cut = entrance). Scale-pop 0.28–0.40 s
  ease-out-back 8–12% overshoot (labels/arrows/props). Slide 0.40–0.55 s
  ease-out-cubic (creatures). No fades. No motion blur (crisp stills).
- Exits: hard cut. Never fade out.
- Puppet pins: 2–5 per shot. Jaw: rotate child or swap 2 PNGs, 15–25°
  open, 0.15 s down / 0.20 s up. Tail/tentacle/worm: 3–5 pins, sine offset
  0.4–0.8 Hz, amp 6–10% of body length, follow-through 0.2 s damped sine.
  Fins: ±8–12° @0.5 Hz. Arm: ±10–20° at shoulder. Head tilt 0–4°.
- Swim: body pin-wave 0.6 Hz, travel 8–20 px/s ±X, loop.
- Walk: mostly absent; if needed 8–10 frames/step @60fps, 2-step cycle,
  no squash, 2% body bounce; prefer sliding layer 40–80 px over 0.5 s.
- Faces: NO lip-sync (narration disembodied). Blink skip, or 1 per 4–6 s,
  2 frames down/up. Expression change = swap PNG, never morph.
- Actions: point = arm rotate hold 2 keys 0.25 s ease-out. Bite =
  anticipation −6° 0.12 s → snap +18° 0.12 s → settle 0.20 s, squash ≤4%.
  Eat = jaw cycle 2–3× @0.35 s/cycle. React = swap open-mouth PNG, freeze.
- Secondary: sparse — one per hero creature, damped sine 0.2 s.
- FX: red chevron arrow pops 0.30 s + 2° wiggle @0.5 Hz; "EXTINCTION"
  stamp scale 0.6→1.08→1.00 in 0.40 s red #E31B23; silhouette = swap fill
  #000; bubbles 4–8 circles loop 3 s @40% opacity (sea only); gray wash
  desaturate 100% over 0.3 s (death). NO speed lines/impact stars.

## PART E — TEXT

- Family: rounded hand-drawn sans (Varela Round / Nunito / Baloo 2).
- Chapter title: ~64–78 px @1080 (≈46–55 @768), ALL CAPS, 700 weight,
  cut-on or 0.20 s scale 0.92→1.00, whole chapter.
- Date subtitle: 22–28 px, title card only.
- Card labels: 28–36 px. In-scene labels: 36–44 px, pop 0.28 s.
- Stamps: 70–90 px red #E31B23 white+black edge, pop with overshoot.
- No lower-thirds, no captions, no end subscribe pop.

## PART F — SOUND

- Music: constant low electronic/ambient bed, ~90–110 BPM pulse,
  −18 to −22 dB under voice, no per-chapter themes. Integrated loudness
  ≈ −20.7 LUFS, LRA ~1.5 (very flat).
- SFX: short and quiet. Whoosh 0.2–0.3 s on punch-in/big scale, SAME
  frame as key (not early). Pops on pops.

## Implementation mapping (this repo)
- Canvas 1376×768 @60 fps (target 1920×1080; art scales 1376/1920=0.7167)
- Stroke: use generator linework (thick black); strip = 92 px white bar
- Fonts: chapter title = `sans` (DejaVu Bold, closest rounded sans);
  labels = `hand-note` sparingly
- Easing: zoom = `easeInOut` (0.42,0,0.58,1) ✓; punch/slide = easeOutCubic;
  pops = easeOutBack; motion_blur = 1 (crisp)
- Audio: narration loudnorm −16; bed −19 dB under voice; SFX −14 dB

## Part II — Recipe cards & production rules (user-provided continuation)

### Recipe cards (the 10 most common moves)

1. **Cold open TOC grid** — When: 0:00, table of contents. Duration
   2.0–3.5 s then cut. Camera: scale 1.00→1.10 (or pos x 0→−6% if grid wider
   than frame), ease-in-out. Audio: TTS thesis line + bed (NO whoosh).
   Grid = ONE precomposed PNG (never spawn cards one-by-one).
2. **Chapter title slam** — every chapter start. 0.20 s, scale 0.92→1.00,
   opacity 0→1 in 0.08 s, ease-out-cubic, overshoot 0, hold rest of chapter.
   Audio: period name lands here.
3. **Documentary slow zoom (hero)** — "here is the animal" hold. 5.0 s
   (12–25 s ok). Camera scale 1.00→1.12, anchor on eye/jaw, cubic-bezier
   (0.42,0,0.58,1). Creature swim loop underneath. Audio bed+TTS, NO whoosh.
4. **Noun punch-in** — cut hard, put the noun on screen at the word, chapter
   title glued on top. One black stroke weight per character class. White
   air around icons. Let the camera zoom carry the "animation budget."
   Puppet 2–5 pins, not a full rig. Flat fills, red for emphasis only.
   Stick people for humans; inked silhouettes for beasts. Loop swims, hold faces.

### DON'T list
Dissolves, wipes, film grain, handheld. Lip-sync the TTS. Walk cycles as
default locomotion. 3D lighting / drop shadows on characters. Gradient fills
on bodies. Comic-book speed lines / anime smear frames. Busy multi-layer
parallax. Lower-thirds and caption karaoke. Raw photos in 2026-style void
scenes. Bounce/overshoot on documentary zooms.

### What makes it feel expensive (ranked)
1. **Noun-locked editing** — every cut is a word (title at chapter
   timestamps, arrow at the jaw, "extinction" on the gray plate).
2. **Restraint of motion** — ~45% of shots are a still with tiny puppetry;
   zooms 2–3%/s. Looks like a designed AE board, not effects junk.
3. **Stroke discipline** — one weight, round joins, no sketch noise. Reads
   as a brand.
4. **Compositional air + lockups** — top title bar, huge heads, empty white
   (50%+ negative space still balanced).
5. **Systemized chapter machine** — 12× ~67 s blocks, same title treatment,
   same sting. Industrial, not one-off.

### Implementation stack (PNG + keyframe engine)
- Timeline 60 fps
- Layer = { png, parent, anchor, tracks: posX posY scale rot opacity,
  pins[]: {bind, rot, scale} }
- Camera = { scale, pos, anchor }  // never rotate
- Title = always-on text layer, top 12%
- Cut = instantaneous layer-set swap (no mix)
- Asset sheet per shot: bg.png (white or gradient), env.png (optional
  floor), char_body.png + char_jaw.png / pin mesh, arrow.png / label.png,
  title string

### First three things to replicate (priority)
1. Hard-cut noun sync + top chapter title bar (if wrong, nothing reads as
   the channel).
2. Still PNG + slow ~2.5%/s ease-in-out zoom as the default "animation".
3. Black ~8 px stroke, flat fill, stick-host / inked-beast, red arrow pops.
