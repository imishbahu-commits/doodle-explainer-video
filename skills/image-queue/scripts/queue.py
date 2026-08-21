#!/usr/bin/env python3
"""Ledger + progress for the image-queue skill.

classify PROJECT        -> hint sources per beat (agent then corrects by hand)
ai-prompts PROJECT      -> pending ai prompts, one per line
mark PROJECT ID...      -> set status=done, image paths via --image in same order
free-report PROJECT     -> beats servable without AI (hold/doodle/asset/pose)
progress PROJECT --page -> table + progress.html gallery (images inline)
"""
import argparse, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))

def ledger(p):
    path = os.path.join(REPO, "projects", p, "beats.json")
    return json.load(open(path))

def save(p, data):
    path = os.path.join(REPO, "projects", p, "beats.json")
    json.dump(data, open(path, "w"), indent=2)

DOODLE_WORDS = ["diagram", "map", "chart", "arrow", "label", "timeline",
                "schematic", "flow", "graph", "equation", "list", "step"]
ASSET_WORDS = ["coin", "sword", "tool", "shield", "key", "gem", "scroll",
               "icon", "prop", "vase", "helmet", "crown", "pot"]

def classify_beat(b, subjects_seen):
    v = (b.get("visual", "") + " " + b.get("spoken", "")).lower()
    visual = b.get("visual", "").strip().lower()
    subj = b.get("subject", "").strip()
    if visual in ("hold", "same", "reuse previous", "no change", "") and not subj:
        return "hold"
    if any(w in v for w in DOODLE_WORDS):
        return "doodle"
    if any(w in v for w in ASSET_WORDS):
        return "asset"
    if subj and subj in subjects_seen:
        return "pose"
    if subj:
        subjects_seen.add(subj)
        return "ai"
    return "ai"

def cmd_classify(p):
    data = ledger(p)
    seen = set()
    for b in data["beats"]:
        b["source"] = classify_beat(b, seen)
        if b["source"] == "hold":
            b["status"] = "done"
        elif b.get("status", "planned") == "planned":
            b["status"] = "pending"
    save(p, data)
    ai = sum(1 for b in data["beats"] if b["source"] == "ai")
    free = len(data["beats"]) - ai
    print(f"{len(data['beats'])} beats: {free} local/hold (hold/doodle/asset/pose), "
          f"{ai} ai. Agent: correct each beat's source by hand, then run "
          f"ai-prompts.")

def cmd_ai_prompts(p):
    data = ledger(p)
    pending = [b for b in data["beats"]
               if b["source"] == "ai" and b.get("status") != "done"]
    print(f"{len(pending)} pending ai beats (max 10 per turn):")
    for b in pending:
        print(f"{b['id']} | {b.get('visual') or b.get('spoken') or ''}")

def cmd_mark(p, ids, images):
    data = ledger(p)
    imgs = list(images)
    for i, bid in enumerate(ids):
        for b in data["beats"]:
            if b["id"] == bid:
                b["status"] = "done"
                if i < len(imgs) and imgs[i]:
                    b["image"] = imgs[i]
    save(p, data)
    pending = sum(1 for b in data["beats"]
                  if b["source"] == "ai" and b.get("status") != "done")
    total = sum(1 for b in data["beats"])
    done = sum(1 for b in data["beats"] if b.get("status") == "done")
    print(f"{done}/{total} beats have images. {pending} ai beats remain "
          f"(stop for 'go' at 0 if you generated 10 this turn).")

def cmd_free(p):
    data = ledger(p)
    free = [b for b in data["beats"] if b["source"] in ("hold", "doodle", "asset", "pose")]
    print(f"{len(free)} local/hold beats: " + ", ".join(str(b['id']) for b in free))

def cmd_progress(p, page):
    data = ledger(p)
    d = os.path.join(REPO, "projects", p)
    rows = []
    for b in data["beats"]:
        img = ""
        if b.get("image"):
            rel = b["image"]
            img = f'<img src="{rel}" width="180">' if page else f"[{rel}]"
        rows.append((b["id"], b["duration"], b["source"], b.get("status", "?"),
                     (b.get("spoken") or b.get("visual") or "")[:70], img))
    print(f"{p}: {len(data['beats'])} beats, "
          f"{sum(b['duration'] for b in data['beats']):.0f}s")
    if page:
        head = ("<html><head><meta charset='utf-8'><title>Image progress</title>"
                "<style>body{font-family:system-ui;max-width:1000px;margin:24px auto}"
                "td{padding:6px;border-bottom:1px solid #ddd;vertical-align:top}"
                "img{border:2px solid #111;border-radius:4px}</style></head><body>"
                f"<h2>{p} — image progress</h2>"
                "<p>A beat may hold or reuse a visual state. 'pose' = subject reuse, "
                "'doodle' = local diagram, 'asset' = library. Only 'ai' beats cost "
                "generations.</p>"
                "<table>")
        for r in rows:
            head += (f"<tr><td>{r[0]}</td><td>{r[1]}s</td><td>{r[2]}</td>"
                     f"<td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>")
        head += "</table></body></html>"
        with open(os.path.join(d, "progress.html"), "w") as f:
            f.write(head)
        print(f"page: projects/{p}/progress.html")
    else:
        for r in rows:
            print(f"  {r[0]:>3} {r[1]:>4.1f}s {r[2]:<7} {r[3]:<8} {r[4]}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("classify"); a.add_argument("project"); a.set_defaults(fn=cmd_classify)
    a = sub.add_parser("ai-prompts"); a.add_argument("project"); a.set_defaults(fn=cmd_ai_prompts)
    a = sub.add_parser("mark"); a.add_argument("project"); a.add_argument("ids", nargs="+", type=int)
    a.add_argument("--image", nargs="*", default=[]); a.set_defaults(fn=cmd_mark)
    a = sub.add_parser("free-report"); a.add_argument("project"); a.set_defaults(fn=cmd_free)
    a = sub.add_parser("progress"); a.add_argument("project"); a.add_argument("--page", action="store_true")
    a.set_defaults(fn=cmd_progress)
    args = ap.parse_args()
    if args.cmd == "mark":
        args.fn(args.project, args.ids, args.image)
    elif args.cmd == "progress":
        args.fn(args.project, args.page)
    else:
        args.fn(args.project)

if __name__ == "__main__":
    main()
