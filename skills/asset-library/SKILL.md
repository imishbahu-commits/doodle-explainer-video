---
name: asset-library
description: Live on-demand access to open hand-drawn asset libraries (5,000+ Kenney CC0 assets, LPC characters, textures, particles, SFX) WITHOUT cloning repos or committing assets. Use when an image is missing (a prop, character, texture, sound), when the style-lock generator can't produce something, or when you want free CC0 hand-drawn PNGs for a video beat. Fetch single files via the GitHub API; only a tiny used-assets manifest is ever committed.
---

# Asset Library — fetch assets on demand, never commit them

The rule the user cares about: **assets are used without downloading the
whole repo and without committing the files.** Every fetch pulls exactly
ONE file via the GitHub API; the file lands in the local cache
(`~/.asset-library/cache/`, gitignored); only `used-assets.json` (paths +
licenses) is ever committed.

## The libraries (curated, license-checked)

| src | Content | License |
|---|---|---|
| `kenney` | **complete Kenney pack — 5,190 files**: sprites, tilesets, UI, props | CC0 — zero restrictions |
| `lpc` | Liberated Pixel Cup characters — bodies, hair, walk cycles | CC-BY-SA/GPL — credit + share-alike |
| `kenney-particles` | smoke, dust, fire, sparkle textures | CC0 |
| `kenney-textures` | grass, stone, wood patterns | CC0 |
| `kenney-ui-sounds` / `kenney-interface-sounds` | UI SFX | CC0 |

## Workflow

```bash
# 1. find something (searches PNG/SVG names across all libraries)
python3 scripts/asset_fetch.py search dragon

# 2. fetch ONE file (lands in ./assets or --out dir; cached, not committed)
python3 scripts/asset_fetch.py get kenney "Art (5190 files)/…/dragon.png" --out assets

# 3. check the license before using it commercially
python3 scripts/asset_fetch.py license kenney

# 4. see everything already used (the only thing that gets committed)
python3 scripts/asset_fetch.py used
```

## Rules

1. **Search before generating.** A missing prop (boat, tree, shield) is
   almost always already in `kenney`. Never generate what a CC0 library
   already has — that saves image-batch turns.
2. **CC0 first.** `kenney` and the Calinou packs need zero attribution and
   are safe for commercial videos. Use `lpc` only when its character style
   is wanted AND you can credit "Liberated Pixel Cup".
3. **Fetch single files, never clone.** The GitHub API returns one file at
   a time; tree listings are cached locally so search is instant and cheap.
4. **Commit only the manifest.** `used-assets.json` records what was used
   and its license — that's the audit trail. The cache stays local.
5. **Hand-drawn style check.** Kenney's flat vector-ish sprites fit the
   explainer look; if a fetch looks off-style, run it through the
   style-lock checks or regenerate instead.

## Notes

- Works anywhere `gh` is authenticated with a GitHub account (this sandbox
  and any new chat with the repo).
- New libraries: add an entry to `libraries.json` (repo + license) — the
  search and fetch tools pick it up automatically.
