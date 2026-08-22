# stylehub/ — Reference Studio working data (gitignored)

Everything under this directory except this README is generated at runtime
and is deliberately excluded from Git:

| Path | Contents |
|---|---|
| `uploads/` | the user's uploaded reference videos (never committed) |
| `profiles/<id>/` | per-video analysis: `metrics.json`, `shots.csv`, `cuts.csv`, `transcript.json`, `style_rules.json`, `style_profile.md`, `frames/` |
| `combined/` | merged style bible (`style_rules.json`, `combined.json`) |
| `current.json` | promoted profile — the pipeline's first-choice style authority |
| `studio.json` | server session state |

See `REFERENCE_STUDIO.md` and `skills/style-analyzer/SKILL.md`.
