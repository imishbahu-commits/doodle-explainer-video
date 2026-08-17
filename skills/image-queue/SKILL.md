---
name: image-queue
description: Smart image supply for long videos. Every script beat gets ONE image, but not every beat needs an AI generation: the queue classifies beats as doodle (free local vector), asset (free local library), pose (reuse of an already-generated rigged character), or ai (genuinely new subject). Only ai beats consume the platform's 10-images-per-turn cap, so a 3-minute video typically needs 2 turns of generation instead of 6. The queue lives in a committed JSON file, so progress survives restarts and new chats; the user only ever types "go". Use at content-router stage 2 for every multi-beat video.
---

# Image queue — beat math beats the image cap

## The problem (stated plainly)

A 3-minute video has ~50 beats and the image tool allows 10 generations per
turn. Blindly generating 50 AI images = 5-6 turns AND a wall of near-duplicate
pictures. The smart answer is a **supply chain**, not a longer queue.

## The four sources (in priority order)

| # | Source | Cost | What it covers |
|---|---|---|---|
| 1 | `doodle` — handdrawn-code engine | FREE, unlimited, local | diagrams, maps, arrows, labels, charts, schematics, "the explanation" beats |
| 2 | `asset` — asset-library (23 cloud libraries: Kenney CC0, game-icons, 4 emoji sets, humaaans, 0x72 + Pixel Adventure pixel backgrounds, 5 icon sets, openclipart) | FREE, unlimited, fetched one file at a time | props, icons, fish, people, backgrounds, small objects |
| 3 | `pose` — rig + pose library of an already-generated character | FREE, unlimited, local | the SAME character reacting/pointing/looking — the character is generated ONCE, poses are computed |
| 4 | `ai` — image generation | 10 per turn, queue resumable | ONLY genuinely new subjects: the character's first appearance, a unique artifact, a location |

A beat is `ai` only when none of 1-3 can draw it. Characters appear once as
`ai`, then every later beat reuses them as `pose`. Backgrounds appear once as
`ai` (or doodle), then every later beat reuses them.

## Workflow

1. **Classify.** With `beats.json` from youtube-script in hand:

   ```bash
   python3 skills/image-queue/scripts/queue.py classify PROJECT
   ```

   The agent then corrects `source` per beat by hand: same `subject` name
   across beats = first beat `ai`, later beats `pose` (name the pose from the
   character's pose library); diagram/explanation beats = `doodle`; props =
   `asset` (verify with `asset-library` search before trusting).

2. **Free beats first.** Render every `doodle` beat (doodle engine), fetch
   every `asset` beat (asset-library), and compute every `pose` beat
   (character rig + ae-motion). Commit. The queue now shows how many `ai`
   beats remain — usually far fewer than the beat count.

3. **Generate the ai beats, 10 per turn.** Read the pending prompts:

   ```bash
   python3 skills/image-queue/scripts/queue.py ai-prompts PROJECT
   ```

   Generate up to 10 in parallel this turn — with the style-lock: the first
   accepted image becomes the reference image for every later generation.
   Save each result to `projects/PROJECT/assets/beatNN.png`, then:

   ```bash
   python3 skills/image-queue/scripts/queue.py mark PROJECT 7 9 12 --image beat07.png beat09.png beat12.png
   ```

   Commit. Then tell the user: **"18 of 24 images done — type 'go' for the
   next batch."** The ledger is the memory; a crash or a new chat resumes
   from the committed file with zero re-asking.

4. **Progress page** (so the user SEES images as they land, never asks twice):

   ```bash
   python3 skills/image-queue/scripts/queue.py progress PROJECT --page
   # serve: python3 -m http.server 8000 --directory projects/PROJECT
   ```

5. **Voiceover arrives late / is longer than planned.** Re-fit, never stretch:

   ```bash
   python3 skills/youtube-script/scripts/script_planner.py fit PROJECT --segments vo_segments.txt
   python3 skills/image-queue/scripts/queue.py classify PROJECT   # re-classify new beats
   ```

   More voiceover segments = MORE beats = MORE images. An image is NEVER
   shown longer than its beat, and a beat NEVER borrows another beat's image.

## Hard rules (do not bend)

1. 1 beat = 1 image. No stretching, no reuse, no freeze-frames to fill time.
2. The `ai` queue is the ONLY thing that consumes the 10-per-turn cap.
3. After every batch of up to 10: mark, commit, report, and stop for "go".
4. The first accepted image is the style reference for all later `ai` beats.
5. Every image lands in `projects/PROJECT/assets/` and the path goes into the
   ledger. The ledger is committed. Untracked images do not exist.

## Beat-count cheat sheet

| Video | Beats (~3.6 s) | Typical ai beats after classification | Turns at 10/turn |
|---|---|---|---|
| 1 min | ~17 | 6-9 | 1 |
| 3 min | ~50 | 14-22 | 2-3 |
| 8 min | ~133 | 40-60 | 4-6 |

The 8-minute row is why the supply chain matters: 50 AI images instead of
133, and the rest come free from local sources.
