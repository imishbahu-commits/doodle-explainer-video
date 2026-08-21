---
name: image-queue
description: Persistent visual-asset ledger for Paint Explainer production. Classifies script beats as doodle, asset, pose/reuse, hold, or genuinely new AI subject, so generation is spent only on new semantic masters. A beat may hold or reuse an approved plate; do not force a new image per sentence. Use after youtube-script and before rendering.
---

# Image queue — semantic states, not image churn

Authority: `references/paint-explainer-analysis-4v/style_rules.json` overrides
all generic timing or asset-count advice here.

A narration beat is a timing row, **not a requirement for a unique image**.
Measured edits are usually noun/idea changes, with long frozen holds and sparse
local motion. Reuse approved subjects and plates whenever continuity calls for
it; record the state in the ledger so reuse is intentional.

## Sources, in priority order

| Source | Cost | Use |
|---|---:|---|
| `hold` | local | preserve the preceding visual state unchanged |
| `doodle` | local | diagrams, maps, arrows, labels, charts, schematics |
| `asset` | local/download | permitted props, icons, objects, backgrounds |
| `pose` | local | reuse an accepted character/subject; optional semantic pose/source swap |
| `ai` | generation | first appearance of a genuinely new subject, artifact, or location |

A character is normally `ai` once and then `pose`/`hold`. A background is
normally sourced once and then reused. Do not regenerate near-duplicates.

## Workflow

1. Start from `beats.json` and classify:

   ```bash
   python3 skills/image-queue/scripts/queue.py classify PROJECT
   ```

2. Correct the heuristic output manually. Add `hold` where a beat does not need
   a visual event. For each event record:

   - `visual_state_id` and reusable asset paths;
   - event type: `hard_cut`, `source_swap`, `local_motion`, or `hold`;
   - `event_time`, usually ~0.033–0.067 s before the noun onset;
   - persistent chapter title;
   - moving element list, normally zero and never more than three.

3. Render/fetch local sources first. Pass subject images through
   `transparent-asset-prep`; pass all masters through
   `handdrawn-style-lock` and `paint-style-qc image`.

4. Generate only pending `ai` masters:

   ```bash
   python3 skills/image-queue/scripts/queue.py ai-prompts PROJECT
   ```

   Generate up to 10 per turn with the accepted style reference. Save results
   under `projects/PROJECT/assets/`, mark them, and commit the ledger:

   ```bash
   python3 skills/image-queue/scripts/queue.py mark PROJECT 7 9 12 \
     --image assets/beat07.png assets/beat09.png assets/beat12.png
   ```

5. Review the progress page:

   ```bash
   python3 skills/image-queue/scripts/queue.py progress PROJECT --page
   ```

6. If voice timing changes, re-fit beats and update event times. Do not stretch
   the entire edit or add visual changes merely to fill time.

## Hard rules

1. Script beats and visual events are separate concepts.
2. A beat may intentionally hold/reuse the prior visual.
3. A new visual state is justified by a noun, idea, relationship, or action.
4. Default to hard cuts/source swaps; do not invent dissolves or entrances.
5. Camera remains locked. No generic pan/zoom/parallax/Ken Burns treatment.
6. In-shot motion is local and sparse: normally 0–3 moving elements.
7. Every generated/fetched asset path and reuse decision is recorded.
8. The first accepted generated master is the style reference for later AI art.
9. Do not add lower-third captions or subtitles unless explicitly requested.
10. `style_rules.json` is authoritative over this skill.

## Planning budget

Do not estimate image count from runtime alone. Estimate **new semantic
masters** after reuse/hold classification. Cadence is checked separately:
median shot duration should remain within the measured 2.3–3.1 s envelope,
while ~35–60% of shots are frozen holds.
