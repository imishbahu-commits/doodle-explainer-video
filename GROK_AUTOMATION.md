# Grok Automation Guide — run this video pipeline from Grok

This repo builds **Paint Explainer style hand-drawn explainer videos**. This
guide explains how to make **Grok** drive the pipeline: Grok writes the
script, plans the beats, writes the image prompts, generates the images, and
packages the YouTube metadata — using the same rules the Arena workspace
follows.

## 1. Get the files into Grok (pick ONE)

**Option A — connect Grok to GitHub (recommended):**

1. Open `https://github.com/imishbahu-commits/doodle-explainer-video`
2. Tap **Fork** (top right) → **Create fork**. Now you have your own copy.
3. In Grok, connect GitHub (Grok's integrations / MCP), point it at your
   fork, branch `arena/01a002e2-doodle-explainer-video`.

**Option B — upload the zip:**

1. Download `doodle-explainer-video-bundle.zip` (all files, no git history).
2. In Grok, attach the zip and start with the prompt below.

## 2. The starter prompt (paste this into Grok, fill the topic)

```text
Read CLAUDE.md and SKILL.md first — they are the master rules.

I want a Paint Explainer style hand-drawn explainer video about
[TOPIC]. Follow the repo workflow exactly:

1. Script: use the youtube-script skill (pick the right format from
   references/formats.md). One spoken beat = one sentence = one image,
   2-6 seconds each. Hooks, but-therefore seams, misconception-first,
   facts from research. Output script.md and beats.json (the exact
   schema from the skill).
2. Image plan: classify every beat doodle / asset / pose / ai
   (image-queue skill). Only "ai" beats get generated images.
3. Images: for every ai beat, generate with your image generator using
   the VERBATIM prompt templates in CLAUDE.md — PURE WHITE background,
   thick black outlines, flat colors. Backgrounds and characters are
   SEPARATE images. No "cinematic", no "moody", no dark colors, no text.
   Generate one image per beat — never stretch, never reuse.
4. SEO: after the script is approved, run the youtube-seo skill —
   title (Browse + Search versions), description, tags, chapters,
   15-second hook line, thumbnail concept.
5. Output: script.md, beats.json, the SEO metadata, and all generated
   images, clearly numbered by beat.
```

## 3. What Grok can and cannot do

| Task | Where it happens |
|---|---|
| Script, beat plan, image prompts, SEO metadata | ✅ Grok (using the skills' rules) |
| Generating the hand-drawn images | ✅ Grok's image generator (use the verbatim templates) |
| Free beats: diagrams, charts, stick figures | ✅ Grok can write the doodle-engine JSON or generate them |
| Fetched library assets (Kenney, game-icons…) | ⚠️ needs GitHub access — the asset-library skill's `search`/`get` commands work in any terminal with `gh` |
| Final video assembly (ae-motion keyframes, ffmpeg, 60 fps, audio mix) | ⚠️ in this Arena workspace — upload the images here and say "uploaded" |
| Voiceover | ✅ Grok's voice / or your own recording |

## 4. Bring the results back here to finish

1. Put every image in the uploads folder (or use the phone studio page —
   it uploads straight from your phone).
2. Put `script.md` + `beats.json` in the project folder.
3. Tell the agent: "uploaded — assemble the video".

The workspace then does: style check → ae-motion animation (slide-ins,
pops, punch-ins, 60 fps, hard cuts every 2-6 s) → audio (−23 dB, 0.7 s
chapter pauses) → quality gates → final.mp4.

## 5. Non-negotiable rules (Grok must not break these)

1. **1 beat = 1 image.** A longer voiceover = more beats = more images.
   Never stretch an image to cover time.
2. **Style lock.** First accepted image is the reference for every later
   generation. All prompts from the CLAUDE.md templates.
3. **Forbidden words in image prompts:** cinematic, moody, painterly,
   film grain, dark palettes, shadows, gradients, photorealism.
4. **Subjects centered** (x = 0.50), bright white/pastel backgrounds.
5. **No captions unless asked. Hard cuts only.**
6. **Batch stops:** if an image generator limits images per message,
   generate a batch, mark it in beats.json, then continue in the next
   message — the same "go" loop the Arena agent uses.

## 6. Handy numbers

| Video length | Beats (images) | Typical AI images needed |
|---|---|---|
| 1 min | ~17 | 6-9 |
| 3 min | ~50 | 14-22 |
| 8 min | ~133 | 40-60 |

The rest come free: doodle engine (diagrams), asset-library (23 cloud
sources), pose reuse (characters re-posed from one generation).
