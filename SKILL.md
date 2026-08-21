---
name: doodle-explainer-video
description: Produce faceless hand-drawn explainer videos in the measured Paint Explainer style — human hand-drawn PNG characters and backgrounds, locked camera, hard noun-synced cuts, and sparse local keyframes (slide-ins, labels, pose swaps, puppet-rigged limbs; no routine lip sync). Use when the user wants a faceless explainer video, a myth/creature/history list video, a "5-act" story video, or any narrated YouTube video with hand-drawn art. Covers script, style lock, image batching, keyframe animation, character rigging, audio, and assembly.
---

# Hand-drawn explainer video (Paint Explainer style)

**The default mode is ANIMATED hand-drawn PNGs, not static stills.**

## ⚠️ STYLE LOCK — copy these prompts VERBATIM (change ONLY {SUBJECT})

**Subject PNG (characters, creatures, objects):**
```
Hand-drawn doodle illustration of {SUBJECT}, on a PURE WHITE background.
MS-Paint-like style: thick black outlines, flat bold colors, slightly
imperfect hand-drawn lines, simple and {MOOD}.
No text, no background scenery, no shadows, no gradients.
```

**Background PNG (separate image):**
```
Simple hand-drawn doodle {SETTING} background, MS-Paint-like style:
flat {PALETTE} colors, thick black outlines, wavy hand-drawn lines,
completely EMPTY in the middle. No text.
```

**Never** write "cinematic", "moody", "painterly", "film grain", or dark
palettes in an image prompt — that produces the WRONG (Zenn-like) style.
**Pass the first accepted image as the reference image on every later
generation.** This lock is what makes 100 images look like one hand.

Reference: The Paint Explainer channel. The current authority is a four-video,
54:50 corpus scanned across 98,705 frames. Read
`references/paint-explainer-analysis-4v/STYLE_SPEC.md` and
`references/paint-explainer-analysis-4v/style_rules.json`. These supersede the
older single-video autopsy when values conflict.

## The measured formula (follow these numbers)

| Rule | Value |
|---|---|
| Cut rhythm | **2.77 s median**; 70.30% of shots are 1–6 s; hard cuts/step swaps |
| Word sync | visual changes **0.050 s before** nearest word start (median) |
| Motion budget | **46.27% frozen / 40.83% active local / 11.72% subtle local / 0.95% canvas slides** |
| Camera | **locked; zero sustained whole-scene zooms verified** |
| Subject position | **center x≈0.50, slightly low y≈0.54–0.58** |
| Backgrounds | topic-driven: white void, simple plate, or illustrated environment; no global film grain |
| Timing source | measured at 30 fps (±0.033 s); author keyframe times independently of render fps |
| Chapter pauses | **0.60–0.80 s target**; measured median 0.615 s |
| Art | ~0.31%-width black contour, flat character fills, gradients reserved for world plates |
| Voice | current target **204–209 WPM**, **−20.6 to −20.7 LUFS** master |

## The smart router is the entry point

For any video request, first read `skills/content-router/SKILL.md`. It
decides which skill fires when — one specialist at a time, never all at
once:

```
1 script   → skills/youtube-script (any topic, 7 formats)  [beats.json]
1b QC      → skills/video-polish (script_doctor)           [grades the script]
2 plan     → skills/image-queue (doodle/asset/pose/ai)     [resumable ledger]
3 art      → skills/handdrawn-style-lock                   [locks the hand]
3b batch   → skills/image-queue (10 ai per turn, "go")     [image-batcher = legacy]
4 motion   → skills/ae-motion + skills/motion-design       [keyframes, easing]
4b action  → skills/character-animation-skill              [walk/wave/blink]
4c props   → skills/asset-library                          [23 libs: Kenney, game-icons, 4 emoji sets, humaaans, 0x72 + Pixel Adventure backgrounds…]
5 edit     → skills/Ultimate-Video-Editing-Skills          [mix, grade, SFX]
6 gates    → skills/video-polish (audio + pacing reports)  [verify numbers]
7 SEO      → skills/youtube-seo (title/desc/tags/thumbnail) [upload metadata]
```

## Scripts for ANY niche (skills/youtube-script)

The 5-act myth template below is ONE of seven formats. `youtube-script`
handles any topic: myth, misconception, mystery, how-it-works, comparison,
timeline, big-question — see `skills/youtube-script/references/formats.md`.
Depth rules: misconception-first research, but-therefore seams, one
curiosity gap per minute, every fact sourced, beats fitted to the
voiceover (a longer voiceover = more beats = more images, never stretch).

## The 5-act story template (from the reference)

Every chapter (~60 s) repeats the same 5 acts. Write them in order, then
cut the visuals to the narration clauses:

1. **THE MYTH** — dramatic hand-drawn subject + a number/detail
2. **THE DOUBT** — "of course most people assumed it was just a myth"
3. **THE DIG** — real evidence enters (ruins, bones, gases, fossils)
4. **THE EXPLANATION** — drawn diagram/map/mechanism
5. **THE KICKER** — "this is likely how the story spread" (soft verb)

11 chapters = 11 repetitions of this template. The repetition is the format.

## Workflow per chapter

1. Write the 5-act narration for the chapter (video-polish grades it).
2. Generate the subjects via the **style-lock prompt templates**
   (subject PNG on PURE WHITE + separate empty-middle background PNG).
   Batch through the image-queue ledger (doodle/asset/pose first, then ai
   10 per turn); pass the first accepted image as the style reference on
   every later call.
3. Animate with **ae-motion**: slide-in subject, pop label, punch-in on
   the reveal, puppet-pin any body part that acts (tail, wings, limbs).
   Use `--plan "narration beat"` to pick the move. 60 fps, motion blur on
   slides, hand fonts for all text.
4. A character that WALKS/WAVES/BLINKS → character-animation-skill.
   A missing prop (boat, tree, shield) → asset-library fetch (CC0).
5. Assemble: hard cuts at 2–6 s, 0.7 s chapter pauses, music bed ducked
   under the voice, loudness −23 dB.
6. video-polish checks: cut cadence ≈ 3.6 s median, pauses 0.7 s, no
   captions unless asked.

## Legacy mode (optional — NOT the default)

The old "three-band vertical" static format (clickbait banner / static
doodle / empty black band, no motion) still exists in
`scripts/build_video.py`. Use it ONLY when the user explicitly asks for
that specific vertical Reels format. For everything else, this animated
Paint Explainer workflow is the default.

## Rules that never change

- Never copy another creator's drawings, script, voice, or branding —
  extract technique only, build original work.
- No captions unless the user asks. No music louder than −23 dB under the
  voice. Hard cuts only — no transitions between beats.
- The repo is the memory: commit script, ledger, scenes and manifests at
  each stage so a new chat resumes without re-asking.
