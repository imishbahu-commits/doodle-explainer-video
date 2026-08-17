# Code-drawn doodle showcase

Ten hand-drawn images generated **without any image model** — no Arena image
generation, no diffusion, no API key, no network. Every stroke is drawn by
code through the repo's own `skills/handdrawn-code`:

- **scenes** → `scripts/doodle.mjs` — [rough.js](https://roughjs.com) sketch
  primitives + real handwriting fonts (Caveat, Patrick Hand, Kalam, OFL),
  rasterised with resvg at 2x.
- **charts** → `scripts/xkcd_chart.py` — matplotlib xkcd sketch path effects
  with the same fonts.

## Render everything

```bash
bash projects/code-doodle-showcase/render.sh
```

Outputs to `out/`: a `.png` (2752x1536, 2x supersampled) and a matching
`.svg` (editable vector) per item. Takes ~3 seconds for all ten.

Prerequisites (once):

```bash
cd skills/handdrawn-code && npm install     # roughjs, resvg
python3 -m venv .venv && .venv/bin/pip install matplotlib pillow   # charts
```

## What's in the batch

| File | Type | Demonstrates |
|---|---|---|
| `01-cast` | scene | three `person` characters — poses, emotions, hair, outfits |
| `02-mechanism` | scene | `box` + `arrow` chain, hachure fills — the mechanism grammar |
| `03-cat` | scene | a creature built only from `circle` / `shape` / `line` + thought `bubble` |
| `04-compare` | scene | two-column `check` / `xmark` comparison |
| `05-giant` | scene | `giant` numeral on a flat colour field — the stat beat |
| `06-background-day` | scene | empty-middle daytime background (sky, hills, trees, ground) |
| `07-night` | scene | night palette, `stars` / `moon` / `speckle`, `says` speech bubble |
| `08-measure` | scene | `doubleArrow` scale comparison |
| `09-sightings` | chart | hand-inked bar chart |
| `10-retellings` | chart | hand-inked line chart |

All are 16:9 at the geometry the video pipeline expects, so any PNG drops
straight into a beat:

```json
{"image": "projects/code-doodle-showcase/out/03-cat.png", "text": "..."}
```

## Engine fixes made while building this

Three real bugs in `skills/handdrawn-code/scripts/ink-elements.mjs` surfaced
and were fixed:

1. **`cloth: "coat"` ignored the outfit colour** — the torso was hard-coded
   `WHITE`, so every coated character rendered as a blank bib. Now uses
   `outfit` with `outfit2` lapels and a button placket.
2. **`hair: "cap"` was drawn over the face** — the crown extended to y=-22
   and the brim to y=-4, below the eye line at y=-30. The cap now sits above
   the eyes, and takes an optional `capColor`.
3. **`says` bubbles rendered empty** — the text node was built but never
   appended to the scene. It's appended now, the bubble is positioned clear
   of the head, and it gets a proper tail.

## Style rules that make these look like one hand

- One flat background colour per scene. No gradients, no shading.
- Ink is `#16161a`; accent colour only where the grammar asks for it.
- 2–4 elements per scene — empty space is the style.
- Labels short and ALL CAPS; text does **not** wrap, so a `\n` in a label is
  drawn literally. Use one `label` element per line.
- Vary `seed` per scene, or repeated scenes look copy-pasted.
