# handdrawn-code

Generate high-end hand-drawn vector images entirely from code — no image
model, no API keys, reproducible, offline.

Combines the best code-to-sketch tooling found on GitHub into one skill:

| Piece | Source | Role |
|---|---|---|
| rough.js | [rough-stuff/rough](https://github.com/rough-stuff/rough) (MIT) | wobbly hand-drawn primitives |
| @resvg/resvg-js | [resvg](https://github.com/RazrFalcon/resvg) (MPL) | vector → PNG rasteriser |
| Caveat / Patrick Hand / Kalam | [@fontsource](https://fontsource.org) (OFL) | handwriting fonts |
| matplotlib xkcd mode | matplotlib (sketch path effects) | hand-drawn bar/line/pie charts |

Why these and not Excalidraw CLIs (`excalidraw-brute-export-cli` etc.)?
Excalidraw export needs a headless browser + a CDN at render time; this stack
renders with two tiny npm packages and no network.

## Quick start

```bash
bash setup.sh
node scripts/doodle.mjs examples/brain-prediction.json --out out/demo
python3 scripts/xkcd_chart.py examples/mirror-study.json --out out/chart
```

See `SKILL.md` for the full scene DSL, chart spec, style rules, and how the
output drops into the doodle-explainer-video pipeline.

## Layout

```
handdrawn-code/
├── SKILL.md            # the skill instructions an agent follows
├── setup.sh            # npm + fonts + matplotlib
├── fonts/              # converted TTF handwriting fonts (OFL)
├── scripts/
│   ├── doodle.mjs      # scene JSON -> hand-drawn SVG + PNG (rough.js)
│   └── xkcd_chart.py   # chart JSON -> hand-drawn chart PNG + SVG
├── examples/           # sample scenes and a sample chart
└── out/                # rendered demos (gitignored)
```

## Example outputs

**v2 — ink characters & scenes** (the high-end look):
- `out/v2-mirror.png` — worried character in a dim room, mirror, moon
- `out/v2-park.png` — two friends outdoors: sky, sun, hills, ground
- `out/v2-experiment.png` — scientist + subject + experiment flow
- `out/v2-troxler.png` — bearded 1804 physician
- `out/v2-cast.png` — character sheet: 5 hairstyles × emotions × outfits
- `out/v2-contact-sheet.png` — all of the above in one grid

v1 — diagram mode (sticks, boxes, numerals, charts):
- `out/brain-prediction.png`, `out/two-thirds.png`, `out/mirror-study.png`

## The character system

`person` is a modular hand-drawn character system in the spirit of CC0
libraries like Open Peeps (idea only — all paths here are original):
9 poses, 7 emotions, 7 hairstyles + beard, 6 clothings, 8+8 colours,
5 skin tones. Every stroke goes through rough.js (wobble + overdraw) and an
optional feTurbulence ink filter, so it reads as pen-and-ink rather than
clip-art.
