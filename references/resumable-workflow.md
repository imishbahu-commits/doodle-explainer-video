# Resumable cloud workflow

This repository is designed so another Arena chat can continue a video without
relying on the previous chat's memory.

## The rule

**The repository is the memory.** At the end of every meaningful step, update
`projects/<slug>/project.json`, `projects/<slug>/HANDOFF.md`, and the source
ledger, then commit and push the working branch. Large generated media should
live at stable HTTPS URLs or external storage; do not commit gigabytes of media.

## Start a project

```bash
python3 scripts/project.py init "The History of the Silk Road" \
  --template entire-history --duration 12
```

This creates:

```text
projects/the-history-of-the-silk-road/
├── project.json       # machine-readable status and decisions
├── HANDOFF.md         # short briefing for the next chat
├── sources.json       # claims and asset provenance
├── script.md          # narration draft
└── animated-manifest.json
```

## Phase gates

`research → outline → script → storyboard → assets → voice → assembly → qa → done`

Move forward only after the current phase's deliverables exist. Update status:

```bash
python3 scripts/project.py advance projects/the-history-of-the-silk-road script \
  --note "Script approved; 1,850 words. Next: storyboard every 2.5–5 seconds."
```

Inspect a project after opening a new chat:

```bash
python3 scripts/project.py status projects/the-history-of-the-silk-road
python3 scripts/project.py validate projects/the-history-of-the-silk-road
cat projects/the-history-of-the-silk-road/HANDOFF.md
```

## Prompt for a replacement chat

> Clone https://github.com/imishbahu-commits/doodle-explainer-video and check out
> the project branch I provide. Run `bash scripts/setup.sh`, read `SKILL.md`,
> `references/unknown-frequencies-style.md`, and
> `projects/<slug>/HANDOFF.md`. Then run `python3 scripts/project.py validate
> projects/<slug>` and continue only the listed next action. Preserve existing
> approved work and update the handoff before stopping.

## What belongs in the handoff

- Exact phase and next action.
- Approved title, template, duration, visual identity, and voice.
- What the user has approved versus what is still provisional.
- Stable URLs or relative paths for generated assets.
- Failed attempts and their error messages.
- Commands needed to reproduce the current draft.
- Open factual/licensing questions.

## Commit rhythm

Commit after research, script approval, storyboard approval, each generated
asset batch, narration completion, first assembly, and final QA. Push only after
checking that no API keys, cookies, tokens, or unlicensed large files are staged.

## Credentials

Never put API keys or cookies in project files. Use environment variables and
copy `.env.example` to `.env`; `.env` is ignored. A future chat should ask the
user to reconnect a provider rather than reading secrets from Git history.
