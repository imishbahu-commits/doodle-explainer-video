---
name: content-router
description: The smart orchestrator for video production. Decides WHICH skill fires at WHICH moment and NEVER loads skills that are not needed for the current stage. Load this skill first for any video task; it routes to the right specialist, chains their outputs, and keeps the workflow clean instead of messy.
---

# Content Router — one skill active at a time

Every other skill in this repo is DORMANT until its trigger. This router
is the only one that starts: it reads the request, identifies the stage,
activates exactly the skills that stage needs, passes artifacts between
them, and deactivates them when the stage ends. No skill ever runs "just
because it exists".

## The stage map

| Stage | Trigger (what the user/state says) | Skill(s) that fire | Handoff artifact |
|---|---|---|---|
| 0 Route | any video request | content-router | stage decision |
| 1 Script | "write a script / story / narration" | `video-polish` (script_doctor) | `script.md` graded ≥8 |
| 2 Plan | "plan shots / multiple scenes / storyboard" | `cinematic-director` (or `ai-video-storyboard` for a quick shot list) | `shot-plan.md` |
| 3 Art lock | any image generation | `handdrawn-style-lock` (sets the style rules, picks the palette) | style reference PNG |
| 3b Batch | more images than one turn allows | `image-batcher` (ledger, 10/turn) | `images.json` |
| 4 Motion | "animate / add motion / keyframes" | `ae-motion` (keyframes, puppet pins, motion blur, hand fonts) | `scene.json` → mp4 |
| 4b Character does something | a character must WALK/WAVE/BLINK/repeat an action | `character-animation-skill` (sprite from one PNG) — and ONLY then | sprite sheet |
| 4c Character acts via AI video (needs an API key) | action is complex/photographic, user has Qwen/Kling key | `claude-skill-klingai-animation` | mp4 clip |
| 4d Logo/badge/icon motion | animating a LOGO or icon (not a scene) | `wiggle-claude-skill` | lottie/gif/mp4 |
| 5 Editing | "add transitions / effects / captions / color" | `Ultimate-Video-Editing-Skills` (ffmpeg recipes) | graded mp4 |
| 6 Quality gates | before delivery, and after any stage that changed audio/pacing | `video-polish` (audio_report, qa_pacing) | report |
| 7 Done | — | nothing fires. | final.mp4 |

## Routing rules

1. **One specialist at a time.** Stages run in order; a stage loads its
   skill, does the work, writes the artifact, and releases the skill.
2. **Trigger-driven.** 4b/4c/4d only fire on their specific triggers.
   A video with no character actions never loads 4b. A video with no logo
   never loads 4d. A video under the image cap never loads 3b.
3. **Missing input = stop and ask.** No script → stage 1 first. No images
   → stage 3 first. Never skip a stage and never generate without the
   artifact the next stage needs.
4. **The repo is the memory.** Every artifact lands in `projects/<slug>/`
   and is committed — a new chat resumes by reading the artifacts, not by
   re-asking the user.
5. **Small jobs skip the router.** A single image request = stage 3 only.
   A single keyframe tweak = stage 4 only. The router scales with the job.

## Example routing

User: "make me a 3-minute video about the Minotaur myth"
→ 1 script (script_doctor) → 2 plan (cinematic-director) → 3 art lock
(handdrawn-style-lock) → 3b batches (image-batcher, as needed) →
4 motion (ae-motion; 4b only when a beat shows the minotaur CHARGING) →
5 edit (Ultimate-Video-Editing) → 6 gates (video-polish) → 7 deliver.
That is 6 skills across 6 moments — never 6 at once.
