# About this copy

This folder is a full working copy of
[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)
(MIT license — included in `LICENSE`), checked out at the 2026-08-15 state
plus this repo's own video-production skill pack:

- `skills/doodle-explainer-video` — 9:16 three-band explainer pipeline
- `skills/handdrawn-code` — code → hand-drawn SVG/PNG renderer
- `skills/video-polish` — script doctor, audio report, pacing check
- `skills/image-batcher` — hands-free image generation ledger

Why a folder instead of a separate repo: it lives in a repository this
workspace can push to directly, so it can be updated any time without
fork/pull-request permissions.

To sync newer upstream changes later:

```bash
git remote add upstream https://github.com/Panniantong/Agent-Reach.git
git fetch upstream && git diff upstream/main -- agent-reach
```

To turn this into its own standalone repo, use GitHub's "Import repository"
page with the upstream URL, then upload the `skills/` folder (or the zip
export) via the web uploader.
