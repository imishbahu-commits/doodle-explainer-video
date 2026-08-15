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

- `out/brain-prediction.png` — boxes, arrow, stick figure, thought bubble
- `out/two-thirds.png` — giant numeral, faces, check/cross, measure arrow
- `out/mirror-study.png` — xkcd-style bar chart of the strange-face study
