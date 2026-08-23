---
name: historical-doodle-classroom
description: Recreate the production grammar measured from the user's two uploaded historical doodle references using original content: recurring classroom host, semi-detailed asymmetric heads on crude bodies, immersive painted history plates, white diagram cards, sparse source-swap acting, limited cutout motion, subtle motivated camera moves, hard-cut pacing, and dynamic narration audio.
---

# Historical Doodle Classroom

This is the authoritative profile when the user asks to match the two references
uploaded on 2026-08-23. Read first:

- `references/uploaded-historical-doodle-2v/STYLE_SPEC.md`;
- `references/uploaded-historical-doodle-2v/style_rules.json`;
- `skills/expressive-doodle-acting/SKILL.md` for performance construction.

This profile is separate from measured Paint Explainer recreation. Do not inherit
its title strip, 2.3–3.1 s cadence, locked-camera prohibition, palette or −20.65 LUFS
mix. The uploaded-reference rules win for this mode.

## Core visual alternation

Tag every beat as exactly one mode:

1. `CLASSROOM` — original recurring teacher set, board, evidence insert;
2. `WORLD` — full historical environment with layered actors/props;
3. `WHITE` — one isolated diagram, noun, number, comparison, timeline or gag.

A sequence should not remain in one mode indefinitely. The typical rhythm is
`CLASSROOM → WHITE → WORLD → WHITE → WORLD → CLASSROOM`, varied by story need.

## Character production

### Build the bible

Each recurring actor requires:

- front and three-quarter head masters;
- locked skull, hairline, beard edge, nose and eye spacing;
- neutral/narrow/wide/closed/glance-left/glance-right eye sources;
- neutral/raised/angry/worried brow sources;
- five mouth groups;
- neutral and two tilted head sources;
- crude body/costume block;
- independent left/right noodle arms and semantic hands/props;
- standing, leaning, lying/collapsed and one topic-specific pose replacement.

Generate the head larger than final delivery, re-ink it, then composite it onto the
simple body. Do not ask an image generator for every shot independently.

### Acting hierarchy

`eyes → mouth/brows → head tilt → one arm/prop → whole cutout → camera`

Most dialogue holds the body and changes only eyes/mouth. Use 2–4 golden states for
physical action. A collapse, death, recoil, costume transformation or foreshortened
pose is a source replacement, not mesh deformation.

For crowds or historical spread, duplicate one accepted character and vary scale,
position, expression/accessory and entry time. Avoid generating a crowded plate as
one uneditable image.

## Asset queue

Minimum reusable pack:

```text
assets/
  classroom/{plate,board,desks,projector,sign}.png
  host/{head-sources,body,arms,hands,pointer,glasses}.png
  characters/NAME/{bible,heads,bodies,poses,props}.png
  worlds/CHAPTER/{wide,medium,foreground}.png
  diagrams/{timeline,map,icons,arrows}.png
  evidence/{licensed-or-public-domain-inserts}.png
```

World plates and actors must remain separate. White-card diagrams should use
isolated transparent elements whenever they will enter sequentially.

## Shot planning

Normal shot: 3–6 seconds. A stable composition can hold 8–15 seconds only if its
internal state ledger specifies meaningful entrances/swaps. Exceptional timelines,
relationships or escalation plates may reach 18–25 seconds.

Every shot ledger records:

- mode (`CLASSROOM`, `WORLD`, `WHITE`);
- narration clause and accent word;
- background plate;
- initial/final character pose;
- eye/mouth/brow sources;
- one primary local action;
- prop/overlay event;
- camera state and written motivation;
- hold duration after the extreme;
- hard-cut or local-swap boundary.

## Motion implementation

Use `ae-motion` for:

- character/prop x/y translation;
- 1–8% scale changes;
- head/torso/arm rotation;
- eye/mouth/brow/pose source swaps;
- fire, smoke, rain, germ or stink overlays;
- sequential clones and simple maps.

Use HyperFrames for a long timeline, chart, map, many indexed entrants, deterministic
camera wrapper, or diagnostic motion strip.

Default to one to three moving elements. Concentrate movement around a word/action,
then hold. Across the references, 56.5% of adjacent frame pairs are near-frozen.

## Camera grammar

- start locked;
- add a 1–4% slow push when a long hold needs emphasis;
- use 4–8% for a host close-up or evidence reveal;
- use a stronger short punch only after a collapse, alarming fact or joke;
- pan/reframe only to reveal a new subject or follow an approach;
- pull back to expose population, more huts, distance or scale;
- do not let camera and limb action peak together unless intentionally comic.

Validate camera motion against fixed background features. A moving foreground cutout
must not be mislabeled as camera motion.

## Editing

- hard cuts are the default (over 92% of detected boundaries are full/broad hard
  changes);
- local pops/source swaps are acceptable inside a retained world;
- use a white word/diagram card as punctuation, not as subtitle coverage;
- reserve sub-second cuts for corrections, reaction stings, static/glitch or a
  literal word joke;
- no routine dissolve, whip, whoosh or motion-graphic transition.

## Image-generation prompts

### Character head master

```text
Original hand-drawn editorial-comedy character head of {IDENTITY}, three-quarter
view, very large asymmetric head, specific irregular {HAIR} silhouette and {BEARD}
edge, visible eye whites and small irises, long expressive nose, subtle forehead
lines, readable skeptical expression. Single clean slightly imperfect dark-brown
ink contour, flat earthy skin colors with restrained hand-painted texture. Isolated
on pure white, no body, no text, no shadow, no glossy vector finish, no 3D.
```

### Crude body master

```text
Original deliberately crude doodle body for {ROLE}, short blocky {COSTUME} torso,
two thin near-black noodle arms, tiny simple hands, minimal or hidden legs, flat
earthy colors, front view, isolated on pure white. No head, no text, no shading,
no 3D. Designed to receive a separately drawn oversized detailed head.
```

### Environment plate

```text
Original 16:9 hand-drawn historical environment plate of {SETTING}, dark brown
clean irregular contours, muted ochre olive umber palette with {ACCENT}, broad flat
color regions, gentle atmospheric depth bands, readable architecture and props,
clear staging lanes for separately composited characters. No people, no embedded
text, no photorealism, no cinematic lens effects, no 3D.
```

Run generated construction through `handdrawnize.py` with a consistent character or
world seed. Manually redraw identity-critical heads, hands and hero close-ups.

## Text

- white card: irregular black handwritten print;
- classroom board: white chalk script;
- labels: compact black print with one curved arrow;
- default maximum: six words per label;
- never add running subtitles unless explicitly requested.

## Audio

Target approximately −19.1 to −18.6 LUFS, true peak ≤−2.3 dBTP and LRA 4–6 LU.
Keep frequent ~0.46 s sentence breaths and explicit longer chapter pauses. Do not
compress the mix to the quieter/narrower Paint Explainer profile.

## Quality gates

Reject when:

- the detailed-head/crude-body contrast is missing;
- character skull/hair/beard changes between shots;
- a generated crowd/scene is flattened and cannot be staged;
- all body parts interpolate continuously;
- mouth motion is smooth phoneme mush instead of readable grouped sources;
- world plate moves when only a character should move;
- white cards become slides full of text;
- classroom, white and world modes do not alternate;
- shot changes are faster than the narration without a joke/reveal reason;
- camera motion has no story function;
- source drawings, characters, scripts or branding were copied.

## Deliverables

In addition to the normal project artifacts, keep:

```text
characters/*/character-bible.json
characters/*/expression-contact-sheet.png
scenes/*/state-ledger.json
qc/shot-atlases/
qc/motion-strips/
qc/identity-report.md
```
