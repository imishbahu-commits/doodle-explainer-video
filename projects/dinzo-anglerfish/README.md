# Why It Sucks to Be Born as an Anglerfish

Dinzo-style 16:9 doodle explainer. 114 beats / 12 parts.

**Paused after parts 1–2 (beats 1–20).** Full resume notes: [`STATUS.md`](STATUS.md).

## Saved clips (final assembly)

Do not hunt in `parts/` — that folder is gitignored. Use:

```
assembly/part01.mp4      beats 1–10   (~45s)
assembly/part02.mp4      beats 11–20  (~43s)
assembly/running-cut.mp4 beats 1–20   (~87s)   ← watch this
assembly/audio/          voiceovers 01–20
assembly/concat.txt      join list
```

Coming back: `continue anglerfish from beat 21`

```bash
python3 build.py part 3        # next batch
python3 build.py final         # concat whatever is in parts/
# then copy parts/part03.mp4 → assembly/part03.mp4
```
