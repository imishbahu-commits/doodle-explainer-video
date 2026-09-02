# Deformed-face + expression spec (the "destroyed" look) — VERIFIED

> This is the correction the user kept pointing at. The reference faces are
> NOT clean ovals. They are **irregular, lumpy, slightly crooked / teardrop /
> squashed blobs** drawn with a thin hand-wobbled outline. The *expression*
> (brows + eyes + mouth + posture + sweat) carries nearly all the
> character, and it varies a lot between beats.

## 1. The face is DEFORMED, never an oval

| Trait | Exact rule |
|---|---|
| Head outline | **not a clean circle/oval** — a lumpy, wobbly, slightly crooked blob; may be a teardrop, a squashed egg, or have a flat side / bulge / dent |
| Wobble | thin hand-wobbled near-black line (~2-3px), uneven — never a smooth arc |
| Fill | **WHITE** (blank), never skin tone |
| Shape variance | depressed/dizzy = droopy teardrop; scared = wide lumpy circle; sleepy = squashed; angry = tight |
| Chin | small soft chin line, sometimes a tiny ear bump |

## 2. Eyes are varied, not always dots

| Eye type | When | Look |
|---|---|---|
| small filled black dots | neutral / default | tiny round black dots, moderate spacing |
| filled oval dots | cheerful | small filled black ovals |
| **spiral / pinwheel** | dizzy, drunk, overwhelmed | concentric spiral in each eye (yellow/green hair often) |
| **closed / line eyes** | pain, crying, straining | short curved black lines instead of dots |
| wide open dots | surprise / fear | slightly larger black dots |

## 3. Eyebrows carry the emotion (short thin line strokes)

- **sad / defeated**: tilted down at the outer edges, heavy
- **tense / angry**: angled inward-down (V-ish)
- **surprised**: raised, arched up
- **neutral**: flat short strokes
- crying faces often combine negative brows + a wobbly open mouth

## 4. Mouth shapes (small, never a big fill)

- **thin flat line** — neutral / thinking
- **small downward open frown** — worried, upset, defeated (most common "destroyed" look)
- **small open oval** — "oh", mild surprise
- **crying / wailing** — wide open down-curved with possible tongue/upper teeth
- **small smile** — only on clearly happy beats (upper teeth, closed)
- **dizzy** — a big goofy grin

## 5. Sweat & distress marks

- tiny **teardrops at the temple / beside the head** for stress, effort, fear, heat
- horizontal **strain lines** near the face or head when pushing hard
- a **shock/sweat mark** on top (the little curved drop + highlight) when alarmed

## 6. Posture reinforces the expression

- **defeated / destroyed**: slumped, shoulders forward, arms limp, head tilted down
- **tense**: compact, leaning in, arms raised/gripping
- **surprised**: upright, arms up
- **pain**: doubled over, hands on the affected area

## 7. VERIFIED working prompt (use the actual reference frame as `images`)

> Copy this exact naive flat MS-Paint doodle character precisely, same
> deformed destroyed face look. One big IRREGULAR deformed head — NOT a clean
> oval or circle: a lumpy, wobbly, slightly crooked / teardrop / squashed blob
> with a thin hand-wobbled black outline. Head fill is WHITE (blank, not skin
> tone). Two small filled black [dot / spiral / closed-line] eyes. Thin short
> [sad / tense / raised / flat] tilted eyebrows. A small [downward open frown /
> flat line / small smile]. A few tiny sweat drops near the temple. Brown
> spiky frizzy hair cap, thin neck, small WHITE shirt block with a dark brown
> tie, very thin black stick arms and legs, tiny hands and feet. He is [slumped
> defeated / tense / surprised], [expression], shoulders [down/up]. Flat
> colours only, thin near-black wobbly outlines (~2-3px), NO gradients, NO
> shadows, NO texture, naive child-drawn doodle feel. 640x360 landscape.

## 8. Reject these (failure signatures) — regenerate if seen

- a **clean symmetric oval / perfect circle** head  →  head must be lumpy/irregular
- skin-toned face  →  face fill must be WHITE
- a big open fill / realistic mouth  →  small mouth
- realistic eyes with whites/lids   →  dots, spirals, or closed lines only
- crisp vector outlines, gradients, shadows, airbrush  →  thin wobbly doodle lines
- clean muscular/realistic body  →  thin stick limbs, big head
- any text/captions/labels

## 9. Verified results (in `work/cmp/`)

- `match_deformed_v4.png` — deformed lumpy head, sad tilted brows, worried frown,
  sweat, slumped defeated posture (matches the "destroyed" face).
- `match_office_v3.png` — cheerful white round-ish face, spiky hair, smile,
  white shirt + tie, whiteboard + skyline (matches a clean front-face beat).
- `side_office.jpg` — top = real reference, bottom = my match.
