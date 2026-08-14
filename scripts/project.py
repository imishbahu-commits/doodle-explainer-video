#!/usr/bin/env python3
"""Create and maintain resumable animated-video project checkpoints."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASES = ["research", "outline", "script", "storyboard", "assets", "voice", "assembly", "qa", "done"]
TEMPLATES = ["entire-history", "battle-cause", "pov-ordeal", "rank-ladder"]
ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "untitled-video"


def load_project(path: str | Path) -> tuple[Path, dict]:
    directory = Path(path).expanduser().resolve()
    if directory.is_file():
        directory = directory.parent
    project_file = directory / "project.json"
    if not project_file.exists():
        raise SystemExit(f"project not found: {project_file}")
    return directory, json.loads(project_file.read_text(encoding="utf-8"))


def save(directory: Path, data: dict) -> None:
    data["updated_at"] = now()
    (directory / "project.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_handoff(directory, data)


def write_handoff(directory: Path, data: dict) -> None:
    notes = data.get("notes", [])[-8:]
    note_text = "\n".join(f"- {item['at']}: {item['text']}" for item in notes) or "- None yet."
    blocked = data.get("blocked_by") or []
    blocked_text = "\n".join(f"- {item}" for item in blocked) or "- Nothing recorded."
    text = f"""# Handoff — {data['title']}

Updated: {data['updated_at']}

## Resume here

- **Phase:** `{data['phase']}`
- **Next action:** {data['next_action']}
- **Template:** `{data['template']}`
- **Target:** {data['target_minutes']} minutes, 16:9 animated history
- **Approval state:** {data.get('approval_state', 'not reviewed')}

## Decisions

- Original visual identity; do not copy another channel's drawings or branding.
- Sources and asset licenses go in `sources.json`.
- Secrets stay in environment variables, never this directory.

## Recent notes

{note_text}

## Blockers

{blocked_text}

## Commands

```bash
python3 scripts/project.py status {directory.relative_to(ROOT)}
python3 scripts/project.py validate {directory.relative_to(ROOT)}
python3 scripts/build_animated_video.py {directory.relative_to(ROOT) / 'animated-manifest.json'}
```
"""
    (directory / "HANDOFF.md").write_text(text, encoding="utf-8")


def init(args: argparse.Namespace) -> None:
    slug = args.slug or slugify(args.title)
    directory = ROOT / "projects" / slug
    if directory.exists() and any(directory.iterdir()):
        raise SystemExit(f"project already exists: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = now()
    data = {
        "schema_version": 1,
        "title": args.title,
        "slug": slug,
        "template": args.template,
        "target_minutes": args.duration,
        "phase": "research",
        "next_action": "Research the topic and fill sources.json with verified claims.",
        "approval_state": "concept pending",
        "created_at": timestamp,
        "updated_at": timestamp,
        "notes": [{"at": timestamp, "text": "Project initialized."}],
        "blocked_by": [],
        "artifacts": {},
    }
    (directory / "script.md").write_text(f"# {args.title}\n\n## Hook\n\n## Narration\n", encoding="utf-8")
    (directory / "sources.json").write_text(
        json.dumps({"claims": [], "assets": []}, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "output": "draft.mp4",
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "background": "#f2eadb",
        "scenes": [
            {
                "duration": 4.0,
                "background": "#f2eadb",
                "text": args.title,
                "motion": "slow_zoom_in",
                "layers": [],
            }
        ],
    }
    (directory / "animated-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    save(directory, data)
    print(f"created {directory.relative_to(ROOT)}")
    print(f"next: {data['next_action']}")


def status(args: argparse.Namespace) -> None:
    directory, data = load_project(args.project)
    print(f"{data['title']} [{data['template']}]")
    print(f"phase: {data['phase']} ({PHASES.index(data['phase']) + 1}/{len(PHASES)})")
    print(f"next:  {data['next_action']}")
    print(f"path:  {directory}")
    if data.get("blocked_by"):
        print("blocked by:")
        for blocker in data["blocked_by"]:
            print(f"  - {blocker}")


def advance(args: argparse.Namespace) -> None:
    directory, data = load_project(args.project)
    current = PHASES.index(data["phase"])
    target = PHASES.index(args.phase)
    if target < current and not args.force:
        raise SystemExit("refusing to move backward without --force")
    data["phase"] = args.phase
    if args.next:
        data["next_action"] = args.next
    elif target + 1 < len(PHASES):
        data["next_action"] = f"Complete and review the {PHASES[target + 1]} phase."
    else:
        data["next_action"] = "Archive deliverables and publish only with explicit approval."
    if args.note:
        data.setdefault("notes", []).append({"at": now(), "text": args.note})
    if args.approval:
        data["approval_state"] = args.approval
    save(directory, data)
    status(argparse.Namespace(project=directory))


def validate(args: argparse.Namespace) -> None:
    directory, data = load_project(args.project)
    errors, warnings = [], []
    if data.get("phase") not in PHASES:
        errors.append(f"unknown phase: {data.get('phase')}")
    if data.get("template") not in TEMPLATES:
        errors.append(f"unknown template: {data.get('template')}")
    required = ["project.json", "HANDOFF.md", "sources.json", "script.md", "animated-manifest.json"]
    for name in required:
        if not (directory / name).exists():
            errors.append(f"missing {name}")
    try:
        sources = json.loads((directory / "sources.json").read_text(encoding="utf-8"))
        if data["phase"] not in ("research", "outline") and not sources.get("claims"):
            warnings.append("source ledger has no claims")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid sources.json: {exc}")
    try:
        manifest = json.loads((directory / "animated-manifest.json").read_text(encoding="utf-8"))
        if not manifest.get("scenes"):
            errors.append("animated manifest has no scenes")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid animated-manifest.json: {exc}")
    print(f"validated {directory.relative_to(ROOT)}")
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    raise SystemExit(1 if errors else 0)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    create = sub.add_parser("init", help="create a resumable project")
    create.add_argument("title")
    create.add_argument("--slug")
    create.add_argument("--template", choices=TEMPLATES, default="entire-history")
    create.add_argument("--duration", type=float, default=12.0)
    create.set_defaults(func=init)
    show = sub.add_parser("status", help="show the current checkpoint")
    show.add_argument("project")
    show.set_defaults(func=status)
    move = sub.add_parser("advance", help="update phase and handoff")
    move.add_argument("project")
    move.add_argument("phase", choices=PHASES)
    move.add_argument("--next", help="exact next action")
    move.add_argument("--note")
    move.add_argument("--approval")
    move.add_argument("--force", action="store_true")
    move.set_defaults(func=advance)
    check = sub.add_parser("validate", help="validate checkpoint files")
    check.add_argument("project")
    check.set_defaults(func=validate)
    return ap


if __name__ == "__main__":
    args = parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)
