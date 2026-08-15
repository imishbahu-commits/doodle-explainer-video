---
name: doodle-explainer-video
description: Produce faceless 9:16 doodle-explainer videos in the viral three-band format — static clickbait banner on top, crude stick-figure illustrations in the middle, an empty black band on the bottom, over a single fast narration track with no music. Use when the user wants to make a video like this reference format, a faceless explainer/documentary short, an orca-style "paradox" video, or a long-form narrated Reel/Short/TikTok. Covers script, voiceover, images, banner, and final assembly.
---

# Doodle explainer video

Builds original faceless explainer videos in two modes:

1. **Three-band vertical** — the original static 9:16 Reel/Short format.
2. **Animated history** — an original 16:9 YouTube format using simple
   hand-drawn art, maps, staged motion, and fast historical narration. Use this
   mode for “entire history,” “POV,” “every rank,” and battle-cause videos. Read
   `references/unknown-frequencies-style.md` and
   `references/resumable-workflow.md` first. For the limited-animation comedy
   grammar (slide-ins, punch-ins, stamps, draw-on arrows), read
   `references/oversimplified-style.md` — the renderer implements every move.

Never copy a reference creator's exact drawings, script, voice, thumbnail,
branding, or scene sequence. Extract only high-level production techniques and
build an original identity.

For work expected to span chats, initialize a checkpoint immediately:

```bash
python3 scripts/project.py init "Video title" --template entire-history --duration 12
```

At every phase gate, update `project.json` and `HANDOFF.md` with
`scripts/project.py advance`, commit, and push. A replacement chat must run
`status` and `validate` before generating anything.

The instructions below describe **three-band vertical mode only**.

**Do not add subtitles or captions.** The bottom band stays empty black. It is
part of the layout — it keeps the illustration in the upper-middle of the frame,
clear of platform UI overlays — but no text goes in it. The build script leaves
it empty by default; do not pass `--captions` unless the user explicitly asks
for burned-in subtitles.

Media generation goes through the **Unsora MCP**. Assembly is local ffmpeg via
`scripts/build_video.py`, which already encodes the measured format spec.

## Before starting

Read `references/format-spec.md` for the measured geometry, then
`references/script-formula.md` before writing any narration. Read
`references/art-direction.md` before generating any image. The format's
distinctiveness lives in those details; skipping them produces something
generic.

Check `get_credits` early. A 10-minute video is roughly 150 images plus ~20
voiceover calls — confirm the budget covers it before generating, and offer a
shorter target length if it does not.

## Pick the target length first

| Length | Words | Sections | Illustrations |
|---|---|---|---|
| 60 s | ~215 | 3–4 | ~15 |
| 3 min | ~650 | 8–10 | ~45 |
| 10 min | ~2,200 | 18–25 | ~150 |

Narration runs ~217 wpm and one illustration covers 12–15 words. Default to
3 minutes unless the user asks for the full 10-minute treatment — it is the
cheapest length that still fits the whole nine-move arc.

## Workflow

### 1. Find the paradox

The format needs a subject with a real, resolvable paradox whose mechanism
generalises to the viewer's own life. Test the topic on three things:

- Is the central fact verifiable and genuinely surprising?
- Is the obvious explanation wrong, leaving somewhere to go?
- Does the real mechanism apply to the viewer personally?

If any answer is no, propose a different angle before writing. This test is what
makes the last 15% of the video land.

Research the topic properly and keep the real sources — named researchers,
institutions, and dates are load-bearing in this format. Do not invent
citations; verify each one, and drop any claim you cannot source.

### 2. Write the script

Follow the nine-move arc in `references/script-formula.md`. Write it as one
continuous narration, then split it into sections at paragraph boundaries.

Write for the ear, not the page: spell numbers as spoken ("twelve thousand
pounds", "nineteen seventies"), keep sentences short, and use fragments for
emphasis.

Show the user the script and get sign-off before generating any media. It is the
cheapest thing to change and everything else depends on it.

### 3. Break it into beats

Split each section into beats of 12–15 words. One beat is one illustration and
its narration text. Give every beat a visual concept drawn from the visual
grammar table in `references/art-direction.md` — match the diagram type to what
the sentence is actually doing.

### 4. Generate the banner

One image for the whole video, via `create_image` with the banner template in
`references/art-direction.md`, at `aspectRatio: "16:9"`.

Ask the image model for the artwork only, never the title text — models mangle
lettering. Compose the title in afterwards: all caps, heavy grotesque, `#FCEB00`
with exactly one word in `#FF0000`, phrased as a question.

### 5. Generate the illustrations

`create_image` per beat, 16:9, using the doodle template. Two things keep 150
images coherent:

- Pass the first accepted illustration as `referenceImages` on later calls, or
  style drifts visibly across the runtime.
- Cycle the background colour by scene mood using the table in the art
  direction reference.

Batch these and poll with `wait_for_image`. Collect the returned URLs — the
build script accepts URLs directly and downloads them.

**When the image tool is capped per turn (e.g. Arena Agent Mode, 10/turn),
use the `skills/image-batcher` skill:** `init` a ledger with every beat's
prompt up front, generate min(10, pending) in parallel each turn, `mark`
them done, commit, and end the turn with "send any one word to continue".
The human never explains anything twice; a new chat resumes with one word.

### 6. Generate the voiceover

`list_voiceover_voices` first and let the user pick. A steady male narrator
suits the format; the reference is measured and slightly ominous, not excited.

Generate **one call per section**, not per beat — voiceover bills per 1,000
characters started, so per-beat calls waste most of every charge. Use
`stability: 0.5` for expressive-but-consistent delivery, and `<#0.5#>` between
sentences where you want a beat of silence.

Poll with `wait_for_voiceover` and keep the section order stable.

Two things measured on real output, both handled by the build script:

- **TTS runs slow.** ElevenLabs delivers ~155 wpm against the format's ~217, so
  a script written to the word budget above lands ~40% longer than planned.
  Either accept the slower runtime or pass `--tempo 1.4`, which hits the target
  duration *and* the reference's brisk pacing. Measure the audio before
  promising the user a duration — do not assume the word count.
- **TTS is quiet.** Raw output sits ~5 dB under the reference. The script
  normalises to -16 LUFS by default; `--no-normalize` opts out.

### 7. Assemble

Write a manifest (see `scripts/manifest_example.json`) and run:

```bash
python3 scripts/build_video.py manifest.json
```

Beat timings are derived from each section's measured audio duration, weighted
by character count, so cuts land with the narration. Paths may be local files or
https URLs.

The script needs `ffmpeg` plus Pillow. The bottom band is left empty.

Useful flags:

- `--keep` — keep composed frames for inspection
- `--gap 0.35` — breath appended after each section
- `--music bed.mp3 --music-db -26` — optional bed, **off by default**
- `--captions` — burn in karaoke subtitles; **off by default, leave it off**

Do not add a music bed or sound effects unless the user asks. The reference has
neither, and that restraint is part of the format — see the audio section of the
format spec.

### 8. Check the result

Extract a few frames and actually look at them before handing the video over:

```bash
ffmpeg -v error -ss 30 -i final.mp4 -frames:v 1 check.png
```

Verify captions are inside the black band and never overflow the width, the
banner is legible, and illustration cuts land with the narration.

## Publishing

`create_post` schedules to connected accounts (`get_accounts` to list them).
Confirm with the user before posting — publishing is outward-facing and not
reversible.

## Notes

- The bottom band carries no text. Leave it empty black.
- Illustrations are fully static while held. No Ken Burns, no zooms, no
  transitions, hard cuts only. With no captions, the illustration cuts are the
  only motion in the frame, so beat pacing matters more — keep beats to 12–15
  words so a cut never sits still for too long.
- Because nothing on screen carries the words, the illustrations have to do more
  work. Favour the labelled-diagram types in the visual grammar table over
  purely decorative scenes.
- The banner never changes. It works as a persistent thumbnail for viewers who
  arrive mid-video.
- Speaking rate is brisk by design. Slowing it down loses the retention curve
  this format depends on.
