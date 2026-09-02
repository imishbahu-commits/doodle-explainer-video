# PROVEN prompt + style-lock (verified against full-res frames)

> Studied the actual 640×360 reference frames (`analysis/reference_frames/`) rather than
> 480px thumbnails. This corrected several things: the body is a **thin stick
> figure** (no thick torso), the head is a **big round white hand-wobbled
> blob**, and expression lives in **brows + eyes + mouth + posture**.

## 0. Style-lock reference (pass to `generate_image` as `images`)

Use the clean full-res reference frame, not a generated one:
- `analysis/reference_frames/16092_12.png`  (cheerful office / whiteboard)
- `analysis/reference_frames/16092_60.png`  (angry + defeated two-character scene)
- `analysis/reference_frames/16092_32.png`  (dizzy spiral-eyes, laurel crown, burning city)

## 1. The verified character (from actual frames)

| Trait | Rule (verified) |
|---|---|
| Head | BIG, round, WHITE fill, **hand-wobbled thin black outline** (slightly irregular, not a perfect circle) |
| Hair | brown spiky/messy cap, or orange-brown; sometimes bald |
| Eyes | small filled black dots (cheerful) / large filled black OVALS (angry) / **spirals** (dizzy) / closed lines (pain) — change with emotion |
| Brows | thick angled black strokes (V = angry, raised = surprise, sad-tilted = upset) |
| Mouth | small — closed smile / open smile / open angry (red) / frown / neutral line |
| Neck | single thin black line |
| Body | **thin black stick** — thin stick arms + legs, dot hands, tiny feet, NO thick torso |
| Clothing | slim brown tie on the chest (office); otherwise the stick body bare |
| Posture | carries expression: angry = point + lean; defeated = slumped/curled; cheerful = upright |
| Sweat | tiny teardrops near head for stress/fear/heat |

## 2. The VERIFIED base prompt (fill the [SCENE] and [ACTION/EXPRESSION] slots)

> Copy this exact hand-drawn flat MS-Paint doodle style precisely, same
> character. One big round WHITE head, hand-wobbled thin near-black outline
> (slightly irregular, not a perfect clean circle), brown spiky messy hair
> cap, [two small filled black dot eyes / large black oval eyes / spiral
> eyes / closed line eyes], [thick angled / raised / sad-tilted] eyebrows, a
> small [open smile / open angry red mouth / worried frown / neutral line]
> mouth, a very thin neck line, and a **VERY THIN black stick body** — thin
> stick arms and legs with tiny dot hands and tiny feet, and a slim brown tie
> on the chest (if dressed). Flat naive doodle, thin hand-wobbled near-black
> outlines (~2-3px), flat colors, NO gradients, NO shadows, NO texture, NO
> thick torso, NO polished vector look. [SCENE]. [ACTION + EXPRESSION].
> 640x360 landscape.

## 3. Non-negotiable rules / failure signatures — reject and regenerate

- thick / bulky torso → body must be a **thin stick figure**
- skin-toned face → face fill must be **WHITE**
- a perfectly smooth circle / clean oval head → head must be **hand-wobbled / slightly irregular**
- a big open fill / realistic mouth → **small** mouth
- crisp vector outlines, gradients, shadows, airbrush → thin wobbly doodle lines
- eyes with whites/pupils → dots, ovals, spirals, or closed lines only
- any text / captions / labels / watermarks

## 4. Verified results (in `work/cmp/`, side-by-side in `work/cmp/side_v5.jpg`)

- `match_office_v5.png` — cheerful office / whiteboard / skyline (matches 16092_12)
- `match_defeated_v5.png` — angry + defeated two-figure scene (matches 16092_60)
- `side_v5.jpg` — top = real reference, bottom = my match

## 5. Repeat recipe

1. Read the target beat frame (full-res) to note expression + scene.
2. Pass that reference as `images`.
3. Use the base prompt, filling only the scene/action/expression slots.
4. Keep "WHITE face", "thin stick body", "hand-wobbled outline" verbatim.
