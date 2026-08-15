# image-batcher

Hands-free AI image generation across the platform's 10-images-per-turn cap.

**What the human does:** one word per batch ("go").
**What the agent does:** everything else — reads the ledger, generates the
next 10 in parallel, marks them done, commits, and reports how many turns
remain. A new chat resumes with the same one word.

## Quick start

```bash
# 1. write every prompt, one per line, in storyboard order
python3 scripts/batch_images.py init "my-video" --prompts prompts.txt

# 2. the agent generates the next 10, then:
python3 scripts/batch_images.py mark 1..10

# 3. repeat; between turns check progress with:
python3 scripts/batch_images.py report
```

## Files

| File | Purpose |
|---|---|
| `images.json` | the ledger: every image id, prompt, status |
| `prompts.txt` | all prompts, one per line (source of truth at init) |
| `SKILL.md` | agent instructions |

No dependencies — Python 3 stdlib only. See `SKILL.md` for the full
workflow rules.
