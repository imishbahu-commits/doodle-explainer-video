# Anglerfish — pause / resume pack

Take a break. Everything needed to finish the video is here.

**When you come back, say:** `continue anglerfish from beat 21`  
(or just `go` / `next`)

---

## What this video is

| | |
|---|---|
| Title | Why It Sucks to Be Born as an Anglerfish |
| Format | Dinzo-style 16:9 doodle, 1920×1080, 30 fps, hard cuts, no music, no captions |
| Folder | `projects/dinzo-anglerfish/` |
| Length target | ~8 min, **114 beats / 12 parts** |
| Done | **Beats 1–20** (parts 1–2), ~87 seconds |
| Next | **Beats 21–30** (part 3) — midnight zone + the male/female split |

Already in the catalog (do not remake): crocodile, mosquito, honeybee, octopus.

---

## Saved clips (use these in final assembly)

Frozen copies live in **`projects/dinzo-anglerfish/assembly/`** — committed to git so a later chat can find them.

| File | What | Beats | Duration |
|---|---|---|---|
| `assembly/part01.mp4` | Birth / the beginning | 1–10 | ~44.7 s |
| `assembly/part02.mp4` | The drop into the midnight zone | 11–20 | ~42.6 s |
| `assembly/running-cut.mp4` | Parts 1+2 already concatenated | 1–20 | ~87.3 s |
| `assembly/audio/beat01.mp3` … `beat20.mp3` | Per-beat voiceovers | 1–20 | — |
| `assembly/concat.txt` | ffmpeg concat list, in order | | |
| `assembly/manifest.json` | Machine-readable clip index | | |

**Final assembly (after later parts exist):**

```bash
cd projects/dinzo-anglerfish
# either drop new parts into assembly/ as part03.mp4, part04.mp4…
# then:
ffmpeg -y -f concat -safe 0 -i assembly/concat.txt \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart assembly/FINAL.mp4
```

Or keep using `python3 build.py part N` then `python3 build.py final` — that reads `parts/`. After each part, **copy** `parts/partNN.mp4` into `assembly/` and append a line to `assembly/concat.txt`.

Scratch folders (`audio/`, `parts/`, `build_work/`) are gitignored. **Do not rely on those after a pause.** Rely on `assembly/`.

---

## Also already saved (in git)

- `script.md` — full 8-minute narration
- `beats.json` — all 114 beats (id, part, narration, scene, label)
- `research.md` — sourced facts
- `build.py` — assembler (1 image + 1 mp3 = 1 beat)
- `assets/beat01.png` … `beat20.png` — doodles (style lock)

---

## Style lock (do not drift)

Hand-drawn MS-Paint doodle: thick black marker outlines, flat bold colors, cream / pale yellow background, ALL-CAPS handwritten labels, 1–3 elements, lots of empty space. **No cinematic, no dark palette, no gradients, no photoreal.**

Pass these as reference images on every later generation:

1. `assets/beat01.png` (jelly raft / OPEN OCEAN)
2. `assets/beat07.png` (larva vs adult / NOT YET)
3. `assets/beat10.png` (waving larva / FOR NOW)

Larva character = tiny pale-blue oval fish, two dot eyes, tiny fins. Adult female = round grey body, huge needle teeth, yellow lure.

---

## Voice

Session voice was `voice-00` (masculine narration, English). A **new chat must re-run `add_voice`** — ids do not carry over.

Audition text (use this again so the user can pick a similar voice):

> You are born inside an egg buried in a muddy mound on the edge of a mangrove swamp in Northern Australia. The nest is a stinking pile of rotting leaves and mud your mother kicked together a few months ago. She's long gone now. She doesn't care about you. She cares about the next meal.

Language: `en` · gender: masculine · use_case: narration · index: 0

Keep one spoken beat = one image = one mp3. Cap: **10 images + 10 voiceovers per turn**, then stop.

---

## Next 10 beats (part 3) — ready to generate

From `beats.json`:

21. There is no sun here. Ever. — `NO SUN. EVER.`
22. The water is just above freezing. — `JUST ABOVE FREEZING`
23. The pressure would fold a human like paper. — `HUMAN ORIGAMI`
24. Food is whatever dead stuff rains down from above. Scientists call it marine snow. — `MARINE SNOW`
25. You call it dinner. If you're lucky. — `DINNER?`
26. Most animals down here starve. — `MOST STARVE`
27. You are about to become two completely different animals, depending on one thing. — `TWO ANIMALS`
28. Whether you hatched female, or male. — `FEMALE OR MALE`
29. And if you hatched male — I am sorry. — `I AM SORRY`
30. Let's start with the girls. They have it better. Relatively. — `RELATIVELY`

Then parts 4–12 continue female lure → male nose → the bite / fusion → kicker → credits.

---

## Switch artwork + use YOUR voiceover

Yes. Two things, in this order:

1. Open **Fast ingest** (live preview on port 8088) and drop:
   - **Voiceover** — one long track, or many per-beat mp3s
   - **Reference** — a video (or images) of the art style you want
2. Type **`uploaded`** in chat.

Then I will:
- Pull files from `uploads/inbox/voiceover/` and `uploads/inbox/reference/`
- Lock the new doodle style to the reference (frames from the video)
- Cut every image to the voiceover: **1 beat = 1 image = exact audio length**
  - many files → filename order (`beat01.mp3`…)
  - one long file → split by the script’s beats, weighted to the measured duration (same as `build.py`)

Do **not** wait on the old `parts/` folder. New synced cuts still go into `assembly/`.

---

## Rules that never change

- 1 beat = 1 image = 1 voiceover. Never stretch or reuse.
- Hard cuts only. No captions. No music.
- After each batch of 10: build the part, **copy the mp4 into `assembly/`**, update `concat.txt` + `manifest.json`, commit.
- Studio: `python3 studio.py 8090`
