---
name: ae-motion
description: After-Effects-grade keyframe motion for still hand-drawn PNGs. Implements AE's exact keyframe semantics — per-property keyframes (position, scale, rotation, opacity, puppet-pin drags) with cubic-bezier easing, plus motion blur, springs and overshoot — and a script-aware move chooser that reads the narration beat and picks the right move automatically. Use when animating explainer-video stills, layering subjects over hand-drawn backgrounds, making part-motion inside a PNG (limbs, tails, fins, mouths), or whenever motion must feel buttery rather than robotic.
---

# AE Motion — keyframes like After Effects, in code

The renderer `scripts/ae_motion.py` uses the SAME keyframe math AE uses:
per-property tracks, cubic-bezier easing (AE's own curve definitions),
anchor-point transforms, and motion blur by sub-frame accumulation. A
layer's position, scale, rotation, opacity — and its puppet pins — are
independent tracks, so a subject can slide in, overshoot, settle and wag
a fin at once.

## The one rule that makes it buttery

**Never linear.** Every interpolating keyframe carries an easing. Use:
`easeInOut` (default), `easeOutExpo` (fast settle), `easeOutBack`
(overshoot — the cartoon boing), `easeOutBounce`, `easeInCubic`
(weight), `linear` (only for constant pans). If motion feels robotic,
the cause is always an uneased keyframe.

## Scene JSON

```json
{
  "width": 1280, "height": 720, "fps": 24,
  "duration": 3.0,
  "background": "assets/background.png",
  "motion_blur": 6,
  "layers": [
    {"type": "image", "src": "assets/anglerfish.png",
     "tracks": {
       "pos":  [{"t": 0.0, "v": [-300, 320], "e": "easeOutExpo"},
                {"t": 1.0, "v": [580, 320], "e": "easeInOut"}],
       "rot":  [{"t": 0.0, "v": 0, "e": "hold"},
                {"t": 1.0, "v": -4, "e": "easeInOut"},
                {"t": 2.0, "v": 4, "e": "easeInOut"}]
     }},
    {"type": "text", "text": "ANGLERFISH", "size": 52,
     "tracks": {"scale": [{"t": 1.0, "v": 0.6, "e": "hold"},
                          {"t": 1.4, "v": 1.0, "e": "easeOutBack"}]}}
  ]
}
```

`e: "hold"` = no interpolation from the previous key (AE's hold
keyframe). `pos` values are the layer's anchor (default: center).
Puppet pins live in `puppet`: `{"pins": [[x,y]...], "drag": [idx...],
"tracks": {"drag0": [{"t":0,"v":[0,0]},{"t":1,"v":[0,40],"e":"easeInOut"}]}}`
— the pin drags interpolate like any property, so a fin/tail/limb moves
inside the PNG while the body slides.

## Hand-drawn fonts for text layers

Text layers carry a `font` field (OFL-licensed fonts shipped in
`skills/ae-motion/fonts/`, so the skill is self-contained):

| `font` | Face | Use for |
|---|---|---|
| `hand` (default) | Caveat | titles, labels — loose marker hand |
| `hand-note` | Patrick Hand | small notes, captions, fine print |
| `hand-bold` | Kalam | big numerals, stamps |
| `sans` | DejaVu Bold | when a clean non-hand look is wanted |

Rule: explainer videos read as hand-drawn when the TEXT is hand-drawn too —
a machine font on a doodle breaks the illusion faster than any motion.
Default everything to `hand` unless a beat explicitly wants machine text.

## The smart move chooser (script-aware)

`scripts/ae_motion.py --plan "beat text"` classifies the sentence by
function and returns the move. The decision tree:

| The narration does this | Choose this move | Keyframe shape |
|---|---|---|
| Introduces a subject / new idea | `slide-in` from off-frame | easeOutExpo 0.3–0.5s, then idle bob |
| States a number / date / stat | `pop` the numeral | scale 0.5→1 easeOutBack, 0.3s |
| A threat / a reveal / "but here's" | `punch-in` on the subject | easeInCubic, 10–20% zoom |
| Travel / movement / a journey | `slide-across` + `parallax` | linear pan bg, subject counter-drift |
| A list item / catalog entry | `stamp` + label pop | scale 1.6→1 easeOutBack |
| Negates / refutes ("not", "never") | `cross-out` (X layer) | stamp the X, 0.2s |
| Asks a question / turn to viewer | `hold + slow-zoom-out` | 8% zoom over 2s, quiet |
| Action by the subject (eats, swims) | `puppet` the part | pin drag loop at 0.5–1Hz |
| A joke / punchline | `pop_boing` + micro-shake | easeOutBack + 2-frame shake |
| Describes a mechanism | `draw-on` arrow + boxes | wipe reveal 0.4s each |
| Lists options | `stagger-pop` items | 0.15s offsets between pops |
| Ends the video | `slow-zoom-in` + fade | 5% zoom, 0.8s fade |

## The full move catalog (22)

slide-in (4 dirs) · slide-across · pop · pop_boing · stamp · drop/bounce ·
punch-in · punch-out · slow-zoom-in/out · pan (4 dirs) · whip · shake ·
wobble · bob (idle breathe) · blink/expression swap · typewriter ·
wipe reveal · draw-on · orbit (2.5D tilt) · parallax · puppet pins ·
follow-through (part keeps moving after the body stops).

Stagger rule: entrances animate 2–3 properties together (pos+rot+scale);
exits are faster than entrances; idle elements always breathe (sin-wave
bob, 1.5–2.5s cycle); every still gets a slow zoom unless a stronger
move owns the beat.

## Motion blur

`motion_blur: N` accumulates N sub-frame samples per output frame — true
AE-style blur on fast moves. Use 6 for slides/punches, 1 (off) for
holds. This single setting is what separates "slideshow" from "film".

## Render

```bash
python3 scripts/ae_motion.py scene.json -o out.mp4
python3 scripts/ae_motion.py --plan "Forty eight percent saw a monster."
```

Frames pipe straight to ffmpeg (no moviepy). Verify by extracting frames
and watching the move land on its word.

## Not used here (and why)

AE/Premiere themselves need a GUI + license (can't run headless here).
Lottie (AE's JSON format, via `lottie-nodejs`) and Remotion are the
open-source equivalents — both need node-canvas/Chrome which this
sandbox blocks. This engine reproduces their *math* (bezier tracks,
overshoot, blur) with zero extra installs, and any new chat can run it
immediately.
