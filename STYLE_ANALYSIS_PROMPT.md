# MASTER PROMPT — Analyze "The Paint Explainer" Animation Style

> Copy everything between the lines below into a new chat that can watch
> videos (attach 2–5 Paint Explainer videos, e.g. the ones you downloaded).
> The AI will produce a quantified "style bible" you can paste to your
> video-builder agent, who will implement it with code-driven keyframes
> (position / scale / rotation / opacity / puppet-pin deformation on still
> hand-drawn PNGs — the same math After Effects uses).

────────────────────────────────────────────────────────────────────────

You are a senior animation director + motion designer + video editor. I
need you to analyze the attached videos frame by frame and produce a
COMPLETE, IMPLEMENTABLE style specification of this YouTube channel's
animation style. A developer will recreate this exact style using still
hand-drawn PNG images animated with code-driven keyframes (per-property
tracks: position, scale, rotation, opacity, plus puppet-pin deformation of
parts inside the image) — the same keyframe model After Effects uses.

There are N videos attached:
1. <title> — <duration>
2. <title> — <duration>
…

## WATCHING PROTOCOL (mandatory)

1. Watch every video once WITH sound. Note story structure, narration
   pacing, music, and sound effects.
2. Watch a second time MUTED, and step through frame by frame (use slow
   playback / pause / frame-step). Focus ONLY on motion: camera moves,
   character movement, timing, easing.
3. Every observation MUST have a timestamp (mm:ss or second-within-shot)
   and a duration. No unsupported generalizations.
4. Quantify EVERYTHING. Never say "a bit", "slightly", "small zoom".
   Give numbers: % of frame, seconds, cycles per second, pixels.
   If you estimate, mark it with "~" and say why.
5. Compare the videos. If the style evolved between older and newer
   uploads, say so explicitly and declare which version is the target.
6. If you can extract frames, include 3–5 annotated frame grabs per video
   showing composition, linework, and a motion moment (before/after).

## PART A — ART & VISUAL STYLE

A1. Linework: thickness relative to frame width (e.g. ~0.4% of frame),
    color (black? dark gray? colored?), consistency, wobble, roughness.
A2. Color: background palette per scene (dominant hues, hex if possible),
    subject palette, number of distinct colors per frame, saturation,
    contrast. Are there ANY gradients, shadows, or textures? (confirm)
A3. Backgrounds: flat single color vs painted scenes vs minimal line art;
    brightness (dark/medium/light); level of detail; do backgrounds have
    depth layers; do they move independently (parallax)?
A4. Character design: proportions (head:body ratio), outline style, eyes
    (dot? oval? expressive?), mouths (drawn? moving?), limbs (stick vs
    shaped), hands/feet (present? simplified?), shading (none?).
A5. Props & environment: style match with characters, level of detail,
    reuse across shots.
A6. Composition: subject position (center? thirds?), subject size vs
    frame, margins/empty space, foreground/mid/background layering.

## PART B — EDITING & PACING

B1. Cut cadence: list EVERY cut with timestamp; compute shot-length min,
    median, mean, max; describe the distribution (mostly short with some
    long? consistent?).
B2. Cut types: hard cuts only? any wipes, dissolves, fades, and WHERE
    (section transitions? ending?).
B3. Cut timing vs narration: do cuts land on sentence starts, on
    keywords, or slightly before/after the spoken word? (anticipation or
    lag — measure a few examples in seconds).
B4. Section structure: how are chapters separated (pause, black frame,
    title card, music change)?
B5. Do complex or emotional scenes get longer shots than simple jokes?

## PART C — CAMERA LANGUAGE (keyframes on the whole scene)

For EVERY shot, classify the camera move:
C1. Move types present: static hold / slow zoom-in / slow zoom-out /
    punch-in (fast zoom) / pan / tilt / drift / parallax / orbit /
    handheld wobble / whip pan / none.
C2. For every zoom: start scale and end scale (as multiplier or % of
    frame), duration, and the EASING CHARACTER (linear? ease-in?
    ease-out? ease-in-out? overshoot/bounce?).
C3. Zoom speed: % per second. (e.g. slow = 1–3%/s, fast punch = 40%/s)
C4. Motion budget across the whole video: % of shots with camera motion
    vs static; and within moving shots, % frozen vs camera-only vs
    character-animation.
C5. Punch-ins: how fast, how far, what easing, and WHEN they're used
    (jokes? reveals? emphasis? numbers?).
C6. Does the camera ever track/follow a moving character? Describe.

## PART D — CHARACTER ANIMATION & RIGGING

D1. Idle motion: do static characters breathe/bob/sway? Frequency
    (cycles/second), amplitude (% of character height), which parts move.
D2. Entrances: how do characters enter a shot — slide from an edge?
    scale-pop? fade? drop from top? Direction, duration, easing,
    overshoot amount, motion blur feel.
D3. Exits: how do characters leave? (slide out? pop away? fade? walk?)
D4. Part animation: which parts move independently (arms, legs, head,
    tail, fin, antennae, mouth, eyes)? Is the motion puppet-pin warp
    (image deforms) or rotation of a separate part, or a new drawing?
    How many moving parts per character per shot (typical)?
D5. Walk/gait: are there walk cycles? How many frames per step, leg
    articulation, body bounce?
D6. Faces: do characters blink (how often, duration)? Do mouths move
    when a character speaks (lip flap) or is narration disembodied?
    Eyebrow/expression changes — new drawing or morph?
D7. Actions: eating, attacking, pointing, waving, reacting — how staged?
    Anticipation/wind-up before the action? Follow-through after?
    Squash & stretch? How many keyframes does an action take?
D8. Secondary motion: hair, fins, tails, leaves, clothing moving as a
    consequence. How often? How subtle?
D9. Effects: bubbles, splashes, particles, dust puffs, speed lines,
    impact stars, sweat drops — when and how often? How animated (loop?
    one-shot?)?

## PART E — TEXT & GRAPHICS

E1. Any on-screen text? Title cards? Labels? Captions? Where and how
    often? Font style (handwritten? marker? uppercase?), size vs frame,
    animation (pop-in? typewriter? slide? fade?), duration on screen.

## PART F — SOUND DESIGN

F1. Music: genre, tempo (BPM if estimable), when it starts/stops, does
    it change per section, loudness relative to voice.
F2. SFX: whooshes on entrances, pops on pops, impacts, bubbles, water —
    how synced to visuals (same frame? early? late?), how often.
F3. Voice: words per minute, energy/tone, pauses, delivery style.

## PART G — STORYTELLING & STRUCTURE

G1. Hook: how do the first 15 seconds work (bold claim? question?
    immediate scene? joke?)?
G2. Narration–visual sync: does the picture show the exact noun being
    spoken? Lead or lag?
G3. Recurring motifs, running gags, callbacks across the video.
G4. How are new sections/chapters introduced visually?

## PART H — THE DELIVERABLE (quantified summary)

H1. Final table — every measurable rule with its measured value:
| # | Rule | Measured value |
|---|------|----------------|
| 1 | Median shot length | ~3.2 s |
| 2 | Motion budget | 55% frozen / 25% camera / 20% character |
| 3 | Slow zoom speed | ~2%/s, ease-in-out |
| 4 | Punch-in zoom | ~15% over 0.4 s, ease-out-back |
| 5 | Idle bob | 0.5 cycles/s, 2% of height |
| 6 | Entrance slide | 0.5 s, ease-out-expo, 10% overshoot |
| 7 | Pop-in scale | 0.6 → 1.1 ease-out-back, 0.35 s |
| … | (add every metric you measured) | |

H2. KEYFRAME RECIPE CARDS for the 10 most common moves. Each card:
    - Name
    - When to use (narration/context trigger)
    - Duration
    - Start and end values (pos/scale/rot)
    - Easing curve description (e.g. fast out, slow settle; overshoot 8%)
    - Notes (motion blur? secondary motion? paired with which audio?)

H3. DO / DON'T list (10 each) — what makes it feel professional.

H4. The 5 most important qualities that make this style feel
    professional/expensive (ranked, with evidence from the videos).

H5. "What I still can't measure from these videos" — be honest about
    gaps (e.g. exact easing curves) and what you'd need (project files,
    more videos, specific scenes).

Rules: timestamps mandatory; numbers mandatory; be exhaustive; the goal
is a spec a developer can code from. Output as clean markdown with
tables. End with the ranked top-3 things to replicate first.

────────────────────────────────────────────────────────────────────────

## Short version (if you only have one video / little time)

Paste the same text but replace "N videos" with 1 and skip the video
comparison; still demand timestamps + numbers + recipe cards.
