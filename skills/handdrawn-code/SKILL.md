---
name: handdrawn-code
description: Generate high-end hand-drawn vector images entirely from code — sketchy diagrams, stick-figure explainer scenes, and xkcd-style charts — compiled from a tiny JSON scene language through rough.js plus real handwriting fonts, and rasterised to PNG. Use when the user wants hand-drawn-style illustrations, whiteboard doodles, sketchy diagrams, or hand-inked charts produced programmatically (no image model), at any resolution, reproducibly, with editable SVG output. Also drops straight into the doodle-explainer-video pipeline as beat illustrations.
---

# Hand-drawn images from code

Two renderers, one look: everything comes out as wobbly hand-inked vector
art, no image model involved.

1. **`scripts/doodle.mjs`** — scene JSON → hand-drawn **SVG + PNG**.
   rough.js primitives (wobble, bowing, hachure fills) + handwriting fonts
   (Caveat, Patrick Hand, Kalam — OFL licensed, shipped in `fonts/`),
   rasterised at 2x with resvg. Node 18+.
2. **`scripts/xkcd_chart.py`** — chart JSON → hand-drawn **chart PNG + SVG**
   (bar / line / pie) via matplotlib sketch path effects with the same
   handwriting fonts.

## Setup (once)

```bash
bash setup.sh
```

Installs npm deps (roughjs, @resvg/resvg-js, fontsource fonts), converts the
fonts to TTF, and pip-installs matplotlib + fonttools. No browser, no GPU, no
API keys. Rendering is offline after setup.

## Scene doodles

```bash
node scripts/doodle.mjs examples/brain-prediction.json --out out/demo
```

Writes `out/demo.svg` (pure vector — the editable, infinitely scalable
deliverable) and `out/demo.png` (2x supersampled raster for preview, slides,
or the video pipeline).

### Scene JSON

```json
{
  "width": 1376, "height": 768,
  "bg": "#FFFFFF",
  "seed": 42,
  "roughness": 1.3, "bowing": 1.0, "strokeWidth": 4,
  "title": "YOUR BRAIN IS A PREDICTION MACHINE",
  "elements": [ ... ]
}
```

- `seed` makes the wobble **reproducible** — the same scene renders the same
  sketch every time. Change the seed for a different hand.
- `roughness` (0–3) = sketchiness, `bowing` = bowed lines, `strokeWidth` = pen
  weight. Defaults match the reference look.
- `title` draws a hand-lettered banner + underline across the top.

### Element reference

| Type | Fields | Draws |
|---|---|---|
| `label` | x, y, text, size, font (`caveat`/`patrick`/`kalam`), rot, color | hand-lettered text, slight tilt |
| `stick` | x, y (feet centre), scale, pose: `stand`/`point`/`raise`/`walk`/`sit` | stick figure, dot eyes |
| `face` | x, y, r, mood: `plain`/`smile`/`worried` | stick-figure face |
| `box` | x, y, w, h, label, sub, fill, fillStyle | labelled box, hachure fill |
| `circle` | x, y, r, fill | circle, hachure fill |
| `line` | x1, y1, x2, y2 | free wobble line |
| `arrow` | x1, y1, x2, y2, label | arrow with head |
| `doubleArrow` | x1, y1, x2, y2, label | measure arrow, heads both ends |
| `giant` | x, y, text, size, color | one huge numeral (Kalam) |
| `bubble` | x, y, w, h, text, kind `speech`/`thought`, fromX, fromY | speech/thought bubble |
| `check` / `xmark` | x, y, s | green check / red cross |
| `brace` | x1, y1, x2, y2 | vertical panel brace |

### Visual grammar

Match the element to what the sentence does — the same table the video skill
uses: distances → `doubleArrow`, comparisons → two scaled `face`/`stick`
elements, counts → `giant`, options → rows of `check`/`xmark`, thoughts →
`bubble`, mechanisms → `box` + `arrow` chains, negations → `xmark` over the
thing.

### Style rules

- One flat background colour per scene (`#FFFFFF`, `#FFE0AC`, `#F2A63B`,
  `#5FBCE4`…). No gradients, no shading.
- Ink is near-black `#16161a`; accents only where the grammar asks (green
  check, red cross).
- 2–4 elements per scene. Empty space is the style.
- Labels short, ALL CAPS, `caveat` for titles, `patrick` for small notes,
  `kalam` for numerals.

## Hand-drawn charts

```bash
python3 scripts/xkcd_chart.py examples/mirror-study.json --out out/chart
```

```json
{
  "kind": "bar",
  "bg": "#FFFFFF",
  "title": "WHAT PEOPLE SAW IN THE MIRROR",
  "xlabel": "apparition", "ylabel": "percent",
  "labels": ["deformed\nface", "monster", "stranger", "animal"],
  "values": [66, 48, 28, 18],
  "color": "#F2A63B",
  "font": "caveat"
}
```

`kind`: `bar` | `line` | `pie`. For `line`, `"series"` can be a list of value
arrays for multiple lines. Outputs both `.svg` (text as vector paths — no
font embedding issues) and `.png` (200 dpi, 2x).

## Verify before shipping

```bash
# sizes + ink coverage (catches blank frames and missing text)
python3 - <<'EOF'
from PIL import Image
im = Image.open("out/demo.png").convert("RGB")
px = im.load(); w,h = im.size
ink = sum(1 for x in range(0,w,4) for y in range(0,h,4)
          if px[x,y][0] < 100 and px[x,y][1] < 100 and px[x,y][2] < 100)
print(im.size, f"{ink/((w//4+1)*(h//4+1)):.2%} ink")
EOF
```

Then actually look at the PNG. If a label overflows a box, shorten the text
or widen the box — text is never auto-wrapped.

## Feed the video pipeline

Scenes are 16:9 by default — the same geometry the doodle-explainer-video
build script centre-crops for band B. Point a beat at the PNG directly:

```json
{"image": "skills/handdrawn-code/out/demo.png", "text": "Your brain is a prediction machine."}
```

## Gotchas

- Text is positioned by centre and does not wrap — keep labels short, and
  check the render for overflow.
- The same `seed` + scene = same sketch, always. Vary `seed` per beat so
  repeated scenes don't look copy-pasted.
- `roughness` above 2.5 starts to break labels into scribbles; keep it
  ≤ 1.8 for scenes with small text.
