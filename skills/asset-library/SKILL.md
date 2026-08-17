---
name: asset-library
description: Live on-demand access to open hand-drawn asset libraries (Kenney CC0, game-icons sketchy icons, Microsoft Fluent emoji, humaaans/open-peeps people, 36k public-domain clipart, LPC characters, textures, particles, SFX) WITHOUT cloning repos or committing assets. Use when an image is missing (a prop, character, fish, icon, background, sound), when the style-lock generator can't produce something, or when you want free hand-drawn images for a video beat. Fetch single files via the GitHub API; only a tiny used-assets manifest is ever committed.
---

# Asset Library — fetch assets on demand, never commit them

The rule the user cares about: **assets live in the cloud (GitHub-hosted
open libraries) and are fetched ONE FILE at a time when needed.** Nothing
is downloaded in bulk, nothing lands in the repo, nothing is committed —
only `used-assets.json` (paths + licenses) is ever committed as the audit
trail.

## The libraries (11 sources, license-checked)

| src | Content | License |
|---|---|---|
| `kenney` | **complete Kenney pack (~5,000 files)**: sprites, tilesets, UI, props, **fish** (fishSwim/fishPink/fishGreen), tile backgrounds | CC0 — zero restrictions |
| `game-icons` | **4,283 sketchy hand-drawn icons**: angler-fish, clownfish, giant-squid, shark-fin, sperm-whale, creatures, weapons, buildings | CC BY 3.0 (some CC0) — one credit line |
| `fluent-emoji` | Microsoft Fluent emoji: flat bold colors + dark outlines (doodle-like). Animals incl. fish/crab/whale/octopus | MIT |
| `humaaans` | flat hand-drawn people, mix & match (PNG + @2x) — the asset equivalent of stick figures | CC BY 4.0 — one credit line |
| `open-peeps` | hand-drawn people PARTS (bodies, hair, faces, accessories) | MIT (originals CC0) |
| `openclipart` | 36,000+ public-domain clipart SVGs by category (animals, food, scenery…) | Public domain |
| `lpc` | Liberated Pixel Cup characters — bodies, hair, walk cycles | CC-BY-SA/GPL — credit + share-alike |
| `kenney-particles` | smoke, dust, fire, sparkle textures | CC0 |
| `kenney-textures` | grass, stone, wood patterns — background fills | CC0 |
| `kenney-ui-sounds` / `kenney-interface-sounds` | UI SFX | CC0 |

## Workflow

```bash
# 1. find something (searches PNG/SVG names across all 11 libraries)
python3 scripts/asset_fetch.py search fish
python3 scripts/asset_fetch.py search angler

# 2. fetch ONE file (lands in --out dir; cached, not committed)
python3 scripts/asset_fetch.py get game-icons lorc/angler-fish.svg --out assets --rasterize
python3 scripts/asset_fetch.py get fluent-emoji "assets/Fish/3D/fish_3d.png" --out assets

# 3. check the license + required credit line before use
python3 scripts/asset_fetch.py license game-icons

# 4. see everything already used (the only thing that gets committed)
python3 scripts/asset_fetch.py used
```

## SVG handling

`game-icons`, `open-peeps`, `openclipart`, and `fluent-emoji` Flat style are
SVG. Add `--rasterize` to `get` — it converts to a white-background PNG
(1,024px, flat colors) via a bundled Node script that self-installs resvg-js
into `~/.asset-library` (npm registry; never the repo). Fluent emoji also
has ready PNGs under `assets/<Name>/3D/`.

## Rules

1. **Search before generating.** A missing prop, fish, icon, or person is
   almost always already in the libraries — especially `kenney` (CC0) and
   `game-icons`. Never spend an AI generation on something a library has.
2. **CC0/MIT first.** `kenney`, `fluent-emoji`, `open-peeps`,
   `openclipart`, and the Calinou packs need no attribution. `game-icons`
   and `humaaans` need ONE credit line in the video description — the
   `license` command prints the exact line; paste it.
3. **Fetch single files, never clone.** The GitHub API returns one file at
   a time; tree listings are cached in `~/.asset-library/trees/` so search
   is instant after the first use.
4. **Commit only the manifest.** `used-assets.json` records what was used
   and its license — that's the audit trail. The cache stays local.
5. **Hand-drawn style check.** Kenney's flat sprites and game-icons' sketchy
   lines fit the explainer look. Flat-style sources (fluent-emoji,
   openclipart) work for icons/props; if a fetch looks off-style, run it
   through the style-lock checks or regenerate instead.
6. **True stick figures** (skeleton-style) come from
   `skills/handdrawn-code` (`ink-elements.mjs`) — drawn from code, free and
   unlimited. `humaaans`/`open-peeps` cover the flat-person look.

## Notes

- Works anywhere `gh` is authenticated (this sandbox and any new chat).
- New libraries: add an entry to `libraries.json` (repo + license + fmt) —
  search and fetch pick it up automatically.
