---
name: asset-library
description: Live on-demand access to 23 open hand-drawn asset libraries (Kenney CC0, game-icons sketchy icons, 4 emoji sets incl. Fluent/fxemoji/twemoji/openmoji/noto, humaaans/open-peeps people, 36k public-domain clipart, 5 icon sets, 0x72 + Pixel Adventure hand-drawn pixel backgrounds, LPC characters, textures, particles, SFX) WITHOUT cloning repos or committing assets. Use when an image is missing (a prop, character, fish, icon, background, sound), when the style-lock generator can't produce something, or when you want free hand-drawn images for a video beat. Fetch single files via the GitHub API; only a tiny used-assets manifest is ever committed.
---

# Asset Library — fetch assets on demand, never commit them

The rule the user cares about: **assets live in the cloud (GitHub-hosted
open libraries) and are fetched ONE FILE at a time when needed.** Nothing
is downloaded in bulk, nothing lands in the repo, nothing is committed —
only `used-assets.json` (paths + licenses) is ever committed as the audit
trail.

## The libraries (23 sources, license-checked)

| src | Content | License |
|---|---|---|
| `kenney` | **complete Kenney pack (~5,000 files)**: sprites, tilesets, UI, props, **fish** (fishSwim/fishPink/fishGreen), tile backgrounds | CC0 — zero restrictions |
| `game-icons` | **4,283 sketchy hand-drawn icons**: angler-fish, clownfish, giant-squid, shark-fin, sperm-whale, creatures, weapons, buildings | CC BY 3.0 (some CC0) — one credit line |
| `fxemoji` | **Mozilla emoji, flat + bold outlines (most doodle-like set)**: fish, shark, animals, objects | CC BY 4.0 — one credit line |
| `twemoji` | Twitter emoji, flat style: ready 72x72 PNGs by codepoint | CC BY 4.0 — one credit line |
| `openmoji` | high-quality open emoji, 618px PNGs + outlines by codepoint | CC BY-SA 4.0 — one credit line |
| `noto-emoji` | Google emoji, 512px PNGs by codepoint | OFL-1.1 — credit |
| `fluent-emoji` | Microsoft Fluent emoji: flat colors + dark outlines | MIT |
| `humaaans` | flat hand-drawn people, mix & match (PNG + @2x) — the asset equivalent of stick figures | CC BY 4.0 — one credit line |
| `open-peeps` | hand-drawn people PARTS (bodies, hair, faces, accessories) | MIT (originals CC0) |
| `openclipart` | 36,000+ public-domain clipart SVGs by category (animals, food, scenery…) | Public domain |
| `dungeontileset-0x72` | **hand-drawn pixel backgrounds**: dungeon walls, floors, doors, chests, props (atlases + frames) | CC0 (0x72) |
| `pixel-adventure` | **hand-drawn pixel scenes**: terrain tiles, characters (Mask Dude, Ninja Frog…), items | CC0 (Pixel Frog) |
| `tabler-icons` | 6,100+ outline stroke icons | MIT |
| `feather` | 280 minimal stroke icons | MIT |
| `phosphor` | 18,000 icons, 6 weights (regular/light look hand-sketched) | MIT |
| `bootstrap-icons` | 4,200+ filled icons | MIT |
| `font-awesome` | 2,000+ free icons (solid/regular/brands) | CC BY 4.0 — one credit line |
| `simple-icons` | 3,500+ brand logos (YouTube, Google…) — thumbnails, end cards | CC0 |
| `lpc` | Liberated Pixel Cup characters — bodies, hair, walk cycles | CC-BY-SA/GPL — credit + share-alike |
| `kenney-particles` | smoke, dust, fire, sparkle textures | CC0 |
| `kenney-textures` | grass, stone, wood patterns — background fills | CC0 |
| `kenney-ui-sounds` / `kenney-interface-sounds` | UI SFX | CC0 |

## Workflow

```bash
# 1. find something (searches image filenames across all 23 libraries)
python3 scripts/asset_fetch.py search fish
python3 scripts/asset_fetch.py search shark

# 2. fetch ONE file (lands in --out dir; cached, not committed)
python3 scripts/asset_fetch.py get game-icons lorc/angler-fish.svg --out assets --rasterize
python3 scripts/asset_fetch.py get fxemoji "svgs/FirefoxEmoji/u1F41F-fish.svg" --out assets --rasterize
python3 scripts/asset_fetch.py get openmoji "color/618x618/1F41F.png" --out assets
python3 scripts/asset_fetch.py get pixel-adventure "Assets/Pixel Adventure 1/Assets/Background/Blue.png" --out assets

# 3. check the license + required credit line before use
python3 scripts/asset_fetch.py license game-icons

# 4. see everything already used (the only thing that gets committed)
python3 scripts/asset_fetch.py used
```

## Emoji libraries: search by codepoint

`twemoji`, `openmoji`, `noto-emoji` name files by EMOJI CODEPOINT, so
searching "fish" won't match them (fxemoji and fluent-emoji DO match
names). The agent already knows emoji codepoints — common ones:

| Subject | Codepoint | Subject | Codepoint |
|---|---|---|---|
| fish | 1f41f / 1F41F | whale | 1f40b |
| tropical fish | 1f420 | dolphin | 1f42c |
| shark | 1f988 | turtle | 1f422 |
| octopus | 1f419 | crab | 1f980 |
| squid | 1f991 | lobster | 1f99e |
| dragon | 1f409 | snake | 1f40d |
| owl | 1f989 | eagle | 1f985 |
| lion | 1f981 | horse | 1f434 |

## SVG handling

SVG libraries (`game-icons`, `open-peeps`, `openclipart`, `fxemoji`,
`tabler`, `feather`, `phosphor`, `bootstrap`, `font-awesome`,
`simple-icons`, `fluent-emoji` Flat) — add `--rasterize` to `get`; it
converts to a white-background PNG (1,024px, flat colors) via a bundled
Node script that self-installs resvg-js into `~/.asset-library` (npm
registry; never the repo). Ready PNGs exist in: `twemoji` (72x72),
`openmoji` (color/618x618), `noto-emoji` (png/512), `fluent-emoji`
(assets/<Name>/3D), `kenney`, `humaaans`, `dungeontileset-0x72`,
`pixel-adventure`.

## Rules

1. **Search before generating.** A missing prop, fish, icon, or person is
   almost always already in the libraries — especially `kenney` (CC0) and
   `game-icons`. Never spend an AI generation on something a library has.
2. **CC0/MIT first.** `kenney`, `simple-icons`, `openclipart`,
   `dungeontileset-0x72`, `pixel-adventure`, `open-peeps`,
   `fluent-emoji`, and the Calinou packs need no attribution. The rest
   need ONE credit line in the video description — the `license` command
   prints the exact line; paste it.
3. **Fetch single files, never clone.** The GitHub API returns one file at
   a time; tree listings are cached in `~/.asset-library/trees/` so search
   is instant after the first use.
4. **Commit only the manifest.** `used-assets.json` records what was used
   and its license — that's the audit trail. The cache stays local.
5. **Hand-drawn style check.** Kenney's flat sprites and game-icons' sketchy
   lines fit the explainer look. Flat-style sources (emoji sets,
   openclipart) work for icons/props; if a fetch looks off-style, run it
   through the style-lock checks or regenerate instead.
6. **True stick figures** (skeleton-style) come from
   `skills/handdrawn-code` (`ink-elements.mjs`) — drawn from code, free and
   unlimited. `humaaans`/`open-peeps` cover the flat-person look.

## Notes

- Works anywhere `gh` is authenticated (this sandbox and any new chat).
- New libraries: add an entry to `libraries.json` (repo + license + fmt) —
  search and fetch pick it up automatically.
