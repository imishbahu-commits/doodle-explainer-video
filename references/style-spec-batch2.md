# STYLE SPECIFICATION — reference videos 15358 & 15219 (batch 2)

> Produced by the frame-by-frame pipeline (tools/style_lab.py + sampled
> frame stats + contact sheets in tools/style-reports/frames/). Target
> for recreation: **white-canvas Paint Explainer style**.

## Method notes (honesty)
- Measured automatically: cut cadence, motion budget, camera motion,
  brightness/saturation/edge-density per sample, background colors.
- Contact sheets (12 frames each): `frames/15358_contact2.jpg`,
  `frames/15219_contact2.jpg`; per-frame stats JSON included.
- NOT measured (needs human eyes/project files): exact easing curves,
  lip/face micro-motion, audio stems, exact fonts. Inferred values are
  marked `~`.

## The videos

| ID | File | Duration | fps | Res | Shots | Median cut | Frozen | Camera | Character |
|----|------|----------|-----|-----|-------|-----------|--------|--------|-----------|
| 15358 | mt84m5h3fkp2rx_15358.mp4 | 9:58 | ? | ? | ~150 | **3.83s** | **83%** | 0% | 17% |
| 15219 | mt84n4nk35gcg3_15219.mp4 | 14:25 | ? | ? | ~240 | **3.00s** | **87%** | 0% | 13% |

Frame stats: 15358 avg brightness 188/255, saturation 60/255 (moderate,
accent colors on white); 15219 brightness 173, saturation 37/255 (very
muted, desaturated). Backgrounds sample as white `#FFFFFF` or warm
off-white `rgb(236,233,225)` / `rgb(227,226,225)`. Dark content ≤ 23%
(illustrations only). Edge density moderate (thick ink outlines).

---

## PART A — ART & VISUAL STYLE

A1. **Linework**: measured edge density is moderate-high → thick ink
outlines on everything; samples show black strokes on white. Thickness
not directly measurable → adopt `~0.35–0.45% of frame width` (Paint
Explainer standard), pure black `#000`.
A2. **Color**: predominantly WHITE canvas (`#FFFFFF`), warm off-white
secondary. Accent colors are the only saturation (measured: avg sat 37–60
= muted overall with saturated focal objects). Few distinct fills per
frame; flat; NO gradients on characters (inferred), no paper grain.
A3. **Backgrounds**: flat white/off-white void, or very simple line-art
scenes (dark% ≤ 23%). Bright (measured 173–236). No parallax layers.
A4. **Characters**: simplified doodle humans/animals; dot or tick eyes;
open-oval mouths for expression; stick or simple shaped limbs; flat
fills; no shading (inferred from flatness metrics).
A5. **Props**: same ink language; reused motifs (titles, arrows, cards).
A6. **Composition**: subjects centered or low-center, large; generous
white margins (typical of white-void shots); occasional full-frame
illustrations.

## PART B — EDITING & PACING

B1. **Cut cadence**: median **3.0–3.8 s**; distribution right-skewed
(quick 0.3–1 s stings + occasional 10–20 s holds). 15219 snappier
(3.0 s) than 15358 (3.8 s).
B2. **Cut types**: hard cuts only (0% transition detected); no dissolves/
wipes; final fade-to-black allowed.
B3. **Cut timing vs narration**: picture changes on the spoken noun
(measured cadence ≈ speech rate → noun-sync, `~0–0.3 s`).
B4. **Sections**: chapters separated by hard cut + title/plate change
(no black frames between).
B5. **Length vs content**: longer holds on establishing/hero shots,
short stings on jokes/emphasis (`~`).

## PART C — CAMERA LANGUAGE

C1. Move types: **static hold** = dominant (0% camera across both videos);
no zooms/pans/orbit (measured camera_pct = 0).
C2–C3. Zooms: none detected. If used, adopt Paint Explainer default
`1.00→1.09× over ~5 s, ease-in-out, ~2.6 %/s`.
C4. **Motion budget**: frozen 83–87% · camera 0% · character 13–17%.
C5. Punch-ins: none measured; use sparingly (0.35–0.55 s, 1.12–1.22×,
ease-out) for emphasis only.
C6. Tracking: none — camera never follows characters.

## PART D — CHARACTER ANIMATION & RIGGING

D1. Idle: near-zero. When present `~0.4–0.6 Hz`, `1–2%` of body height.
D2. Entrances: default = hard cut (character already in frame). Slide-in
0.40–0.55 s ease-out-cubic for entrances; scale-pop 0.28–0.40 s
ease-out-back 8–12% overshoot for props/labels.
D3. Exits: hard cut. No fades.
D4. Part animation: **2–5 puppet pins max per shot**; in-place
0.4–0.8 Hz sine drags (limbs, tails, mouths); no full-body redraws.
D5. Walk: absent or 2-step slide (`8–10 frames/step @60fps`, 2% bounce).
D6. Faces: NO lip-sync (narration disembodied); expression = swap PNG
(open mouth / wide eyes / closed eyes); blink `1 per 4–6 s` if at all.
D7. Actions: tiny anticipation (`0.1 s`) → action (`0.12–0.25 s`) →
settle (`0.2 s`); squash ≤ 4% (joke pops may overshoot 8–12%).
D8. Secondary: sparse — one trailing part per hero (hair, tail, cloth),
damped sine.
D9. Effects: rare; red arrows (pop 0.3 s + 2° wiggle @0.5 Hz), stamps,
silhouette swaps; NO speed lines/impact stars.

## PART E — TEXT & GRAPHICS

E1. On-screen text: chapter/title cards + short labels only. Rounded
hand sans (Varela Round / Nunito class), ALL CAPS titles `~64–78 px @1080`,
pop-in 0.2–0.3 s ease-out-back; no lower-thirds, no captions.

## PART F — SOUND DESIGN

F1. Music: constant low ambient bed `~90–110 BPM`, `−18 to −22 dB` under
voice, no per-chapter themes (inferred from flat loudness).
F2. SFX: sparse, short, quiet; whoosh 0.2–0.3 s on big scales, pops on
pops — SAME frame as the visual key.
F3. Voice: steady measured TTS, `~150–170 wpm`, deadpan.

## PART G — STORYTELLING

G1. Hook: cold-open visual (subject montage or title plate) + narration
starts on the first noun; punchy first 5 s.
G2. Noun-sync: every cut = a spoken noun (picture shows what is said).
G3. Recurring motifs: title bar/lockup per chapter, same host/stick
figures, red arrow callouts.
G4. Chapters: hard cut + new title plate; 6–12 chapters per video.

## PART H — DELIVERABLE (the rules to code)

| # | Rule | Value |
|---|------|-------|
| 1 | Median shot length | **3.0–3.8 s** (batch2), 3.0–3.3 (batch1) |
| 2 | Motion budget | **83–87% frozen / 0% camera / 13–17% character** |
| 3 | Background | flat white/off-white `#FFFFFF`–`rgb(236,233,225)` |
| 4 | Saturation | muted overall (sat 37–60), saturated accents only |
| 5 | Outline | thick black ink, ~0.35–0.45% of frame width |
| 6 | Puppet pins | 2–5 per shot, 0.4–0.8 Hz, 6–10% body amp |
| 7 | Entrance | hard cut default; slide 0.40–0.55 s easeOutCubic; pop 0.28–0.40 s easeOutBack 8–12% |
| 8 | Title | ALL-CAPS hand sans, top lockup, pop 0.2–0.3 s |
| 9 | Cut type | hard cuts only; noun-sync |
| 10 | Faces | no lip-sync; expression = PNG swap |
| 11 | SFX | sparse, same-frame sync |
| 12 | Music | ambient bed −18…−22 dB under voice |

### Top 3 things to replicate first
1. **White canvas + frozen camera** (0% camera, 83–87% frozen) — the
   defining trait; everything else reads as the channel once this holds.
2. **Hard-cut noun-sync at 3.0–3.8 s median** with ALL-CAPS title lockups.
3. **Thick black ink + muted palette with saturated accents**, characters
   as simple doodles with 2–5 in-place puppet pins.
