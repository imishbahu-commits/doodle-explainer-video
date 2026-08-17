#!/usr/bin/env python3
"""batch_images.py — hands-free image generation ledger.

The platform's image tool is capped per turn (10 in Arena Agent Mode), and a
new turn only starts when the human sends a message. This ledger makes that
cap painless: every image (id, prompt, status) is recorded, the agent
generates min(10, pending) per turn in parallel, marks them done, and the
next turn resumes from the ledger with zero re-asking. The human's only job
is to send any one word ("go") to open the next turn.

Usage:
    python3 batch_images.py init PROJECT --prompts prompts.txt
    python3 batch_images.py status              # done/pending, next batch ids
    python3 batch_images.py resume              # print the next batch's prompts
    python3 batch_images.py mark 11..20         # mark generated images done
    python3 batch_images.py report              # progress bar + turns left
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path("images.json")


def load():
    if not LEDGER.exists():
        sys.exit("no images.json here — run `init` first")
    return json.loads(LEDGER.read_text())


def save(d):
    LEDGER.write_text(json.dumps(d, indent=2) + "\n")


def init(args):
    if LEDGER.exists() and not args.force:
        sys.exit("images.json exists — use --force to replace it")
    prompts = []
    if args.prompts:
        raw = Path(args.prompts).read_text().splitlines()
        prompts = [ln.strip() for ln in raw if ln.strip()]
    if args.count and not prompts:
        prompts = [""] * args.count
    if not prompts:
        sys.exit("give --prompts FILE or --count N")
    d = {
        "project": args.project,
        "batch_size": args.batch,
        "created": datetime.now(timezone.utc).isoformat(),
        "images": [{"id": i + 1, "prompt": p, "status": "pending"}
                   for i, p in enumerate(prompts)],
    }
    save(d)
    print(f"ledger: {len(prompts)} images queued for {args.project} "
          f"({args.batch}/turn)")


def pending(d):
    return [i for i in d["images"] if i["status"] != "done"]


def status(args):
    d = load()
    p = pending(d)
    done = len(d["images"]) - len(p)
    print(f"project: {d['project']} | done {done}/{len(d['images'])} | "
          f"pending {len(p)}")
    if p:
        first, last = p[0]["id"], p[min(len(p), d["batch_size"]) - 1]["id"]
        print(f"next batch: images {first}..{last} "
              f"(generate in parallel, one tool call each)")


def mark(args):
    d = load()
    ids = []
    for tok in args.ids:
        if ".." in tok:
            a, b = tok.split("..")
            ids += list(range(int(a), int(b) + 1))
        else:
            ids.append(int(tok))
    for im in d["images"]:
        if im["id"] in ids:
            im["status"] = "done"
    save(d)
    print(f"marked {len(ids)} done; {len(pending(d))} still pending")


def resume(args):
    d = load()
    p = pending(d)[:d["batch_size"]]
    if not p:
        print("ALL DONE — no images left to generate")
        return
    print(f"next batch ({len(p)} images):")
    for i in p:
        print(f"--- image {i['id']}")
        print(i["prompt"] or "(no prompt recorded — ask the human for one)")


def report(args):
    d = load()
    n = len(d["images"])
    done = n - len(pending(d))
    filled = round(10 * done / n) if n else 0
    bar = "█" * filled + "░" * (10 - filled)
    turns = -(-(n - done) // d["batch_size"])
    print(f"{d['project']}: {done}/{n} [{bar}] ({100 * done / n:.0f}%)")
    if turns:
        print(f"turns left at {d['batch_size']}/turn: {turns} — the human "
              f"sends ONE word per turn (e.g. 'go'); the agent does the rest")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("project")
    p.add_argument("--prompts")
    p.add_argument("--count", type=int)
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=init)

    p = sub.add_parser("status"); p.set_defaults(fn=status)
    p = sub.add_parser("resume"); p.set_defaults(fn=resume)
    p = sub.add_parser("report"); p.set_defaults(fn=report)
    p = sub.add_parser("mark")
    p.add_argument("ids", nargs="+")
    p.set_defaults(fn=mark)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
