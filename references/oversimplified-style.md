# OverSimplified-style animation grammar

> This profile captures high-level animation and storytelling technique from
> studying the OverSimplified channel's public format: flat 2D cartoon
> illustration driven by fast narration, where almost nothing "walks" and
> almost everything slides, slaps, stamps and sweeps. Create original
> scripts, characters, scenes and branding — never copy their drawings,
> narration, scene sequence, or identity. Their value here is the *grammar
> of motion*, which is a shared cartoon vocabulary, not their content.

## The core insight: "limited animation" is the point

The channel's comedy survives on cheap, precise motion. Nothing is
smoothly animated for its own sake. Every single thing that moves moves
for one of four reasons: a joke lands, attention is directed, time passes,
or the narration needs a visual beat. The viewer reads this as energy, not
laziness, because each move is timed to the audio.

## The seven signature moves

### 1. Character slide-in (instead of walking)

Characters almost never walk. They **slide** into frame from off-screen,
often with a slight overshoot ("boing") at the end, then sit with a subtle
**bob** while talking. Entrance is fast (0.2–0.4s); the settle is where the
character lives. In the manifest:

```json
{"type": "image", "image": "character.png", "x": 500, "y": 400,
 "enter": "slide_left", "enter_ease": "back", "animation": "bob",
 "amount": 6, "speed": 3.2}
```

### 2. Punch-in for the punchline

At a dramatic or comedic beat the camera slams toward the subject — a fast
zoom (not a slow Ken Burns). Use `motion: "punch_in"` with `focus` on the
subject, then hold 2–3 frames, then cut. Reserve it: one punch per scene
max, or it stops being funny.

```json
{"duration": 2.0, "motion": "punch_in", "focus": [640, 360],
 "background_image": "scene.png", "layers": []}
```

### 3. The text slap

Dates, numbers, and reaction words appear as big cards that **slap into
place** — pop with overshoot, sometimes a `stamp` (starts oversized, slams
down, settles). Never fade-only; a fade reads as a slideshow.

```json
{"type": "text", "text": "66%", "x": 640, "y": 300, "font_size": 140,
 "enter": "pop_boing", "enter_duration": 0.45}
```

### 4. Map sweeps and route traces

Territory and travel are shown as an **arrow drawing itself** across the
frame (`reveal: "draw"`) while the narration moves. The line leads the eye
exactly at narration speed.

```json
{"type": "arrow", "from": [0, 80], "to": [520, 80], "x": 400, "y": 400,
 "color": "#d92727", "stroke": 16, "reveal": "draw", "start": 0.4}
```

### 5. The cross-out and the check

Refuting something = the thing appears, then a thick **X slams over it**
(use a rectangle/ellipse layer plus an X drawn as two arrows, or an X image
with `enter: "stamp"`). Confirming = a check with the same slam.

### 6. Shake on impact

When something hits — a title slap, an explosion, a dramatic number — the
*hit object itself* shakes, not the whole frame (whole-frame shake reads as
amateur). `animation: "shake"` with `amount: 4-6` on the layer, for a short
window right after its entrance.

### 7. Wobble and flash for attention

A layer with `animation: "wobble"` rotates a few degrees like someone
pointing at it; `animation: "flash"` pulses opacity — used for "look here"
beats and caution labels. Both cheap, both strong.

## Timing rules (measured feel, not copied content)

| Rule | Value |
|---|---|
| Entrance durations | 0.25–0.45s |
| Punch-in duration | 0.6–1.2s, then hard cut |
| Cut rhythm | 1.5–4s per visual beat, driven by narration |
| Text on screen | 3–5 words max; one idea per card |
| Camera moves | one per scene; hard cuts between scenes |
| Recurring elements | same asset slides in again — repetition is a joke |

## Storytelling grammar

- **Setup → misdirect → payoff.** The narration says something absurd
  matter-of-factly while the visual shows it literally; the punch-in or
  text-slap lands on the payoff word, never before it.
- **The narrator argues with the picture.** Character poses a question in
  the narration; the visual "answers" with an object, then the camera
  punches in. The mismatch between calm voice and deadpan image is the
  engine.
- **Numbers get physical scale.** A big number is always a big object on
  screen (giant numeral, oversized coin, long arrow), not a spoken aside.
- **Silence is a beat.** A 0.4–0.8s gap right before a stamp or punch-in
  makes the hit land twice as hard.
- **Recurring props.** One prop per video that keeps returning with the
  same entrance — repetition becomes the running joke.

## How to author a scene (agent workflow)

1. Take the narration beat and write the ONE visual idea (never two).
2. Choose the single signature move that matches the beat: slide-in for
   characters, punch-in for drama, stamp for numbers, draw-arrow for
   routes, shake for impacts, wobble/flash for "look here".
3. Write the layer with explicit `start`, `enter`, `enter_ease`,
   `enter_duration`, and `animation`.
4. Hard cut to the next scene; no cross-fades.
5. Watch the render and check that every move lands on its narration word —
   if a move is early or late by even 0.3s, fix the `start` value.

## Tooling note

This grammar is implemented in `scripts/build_animated_video.py`
(PIL + ffmpeg, fully offline — no browser needed). Motion Canvas, Revideo
and Remotion are the open-source browser-based equivalents; they are
heavier to run headless and this repository deliberately ships the
zero-dependency renderer.
