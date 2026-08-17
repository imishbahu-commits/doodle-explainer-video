---
name: image-batcher
description: Hands-free AI image generation across the platform's per-turn image cap. The agent keeps a ledger of every image (id, prompt, status), generates up to 10 per turn in parallel, marks them done, and resumes from the ledger on the next user message with zero re-asking. Use whenever a project needs more than one turn's worth of AI images, or must continue generating in a new chat.
---

# Image batcher — never ask the human twice

## The platform reality (stated plainly)

The image tool allows at most **10 generations per turn**. A turn ends when
the agent stops responding; a new turn starts only when the human sends a
message. Therefore the human's minimum participation is **one message per
10 images**. This skill reduces that message to a single word ("go", "ok",
"k" — anything) and removes every other instruction, so generation *feels*
automatic even though each turn needs one tap.

## Workflow

1. **Init once.** The agent writes every prompt into a prompts file (one per
   line, same order as the storyboard) and runs:

   ```bash
   python3 batch_images.py init PROJECT --prompts prompts.txt
   ```

   Commit. From here on, the ledger is the memory.

2. **Generate.** Read `images.json`; take the first 10 pending images; call
   the image tool for all 10 **in parallel, in one go**. Never generate a
   `done` image again. Pass the first accepted image as the style reference
   on every later call.

3. **Mark + commit.** After the batch lands:

   ```bash
   python3 batch_images.py mark 1..10
   ```

   Commit immediately — a crash must never cause regeneration.

4. **End the turn** with exactly this if images remain:

   > `N images left — send any one word (e.g. "go") and I'll generate the next 10 automatically.`

5. **New chat:** the human says one word (`resume`, `go`, `continue`). The
   agent runs `report` + `resume` and continues from step 2 with no
   re-briefing. The repo is the memory; the ledger is the position.

## Commands

| Command | Purpose |
|---|---|
| `init PROJECT --prompts FILE` | queue all prompts (or `--count N`) |
| `status` | done/pending counts + ids of the next batch |
| `resume` | print the next batch's prompts |
| `mark 11..20` | mark generated images done (also accepts `11 12 13`) |
| `report` | progress bar + turns left |

## Hard rules

- Generate in parallel batches of exactly `min(10, pending)` per turn.
- Mark done immediately after each batch, and commit.
- Never re-ask the human which images to make next — the ledger answers.
- If a generation fails, leave that image `pending`; it retries next turn.
- Keep prompts in the ledger, not in chat history, so any chat can resume.
