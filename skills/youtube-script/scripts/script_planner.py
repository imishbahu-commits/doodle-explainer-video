#!/usr/bin/env python3
"""Beat math for youtube-script.

plan  PROJECT TOPIC --duration 180 --format myth
      -> projects/PROJECT/beats.json  (rough row budget from measured cadence)
      -> projects/PROJECT/script.md   (skeleton with act headings)
fit   PROJECT --segments vo_segments.txt   (one duration per line, seconds)
      -> maps spoken timing rows to final voiceover segment durations;
         inserted rows default to a visual hold, not a new image
report PROJECT
      -> beat table on stdout
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))

MEDIAN = 2.7667   # four-video corpus median shot duration; planning hint only
MIN_B, MAX_B = 2.0, 6.0

FORMATS = {
    "myth":         ["HOOK (0-8s): the myth + the promise",
                     "THE MYTH (8-30s): the story as people believed it",
                     "THE DOUBT (30-55s): who assumed it was just a myth",
                     "THE DIG (55-95s): names, dates, the real evidence",
                     "THE EXPLANATION (95-150s): diagram of what really happened",
                     "THE KICKER (150-180s): how the story spread + new gap"],
    "misconception": ["HOOK: the belief everyone holds",
                      "WHY IT FEELS RIGHT: steelman it",
                      "THE BREAK: the experiment/data that breaks it",
                      "THE REAL MECHANISM: built layer by layer",
                      "SO WHAT: what changes now"],
    "mystery":       ["HOOK: the impossible event",
                      "STAKES: who cared",
                      "CLUE TRAIL: 3 clues, rising tension",
                      "THE TWIST: the clue that breaks the obvious answer",
                      "THE REVEAL: what really happened",
                      "THE MEANING: why it still matters"],
    "how-it-works":  ["HOOK: the result",
                      "BIG PICTURE: whole system, parts named",
                      "LAYERS: each part, one image per piece",
                      "THE KEY INSIGHT: the one trick it leans on",
                      "IMPLICATIONS: what it means"],
    "comparison":    ["HOOK: the rivalry",
                      "ROUNDS: 4-6 categories, score kept",
                      "THE DECIDING FACTOR: the flip",
                      "VERDICT: winner + honest caveat"],
    "timeline":      ["HOOK: the through-line question",
                      "TURNING POINTS: 4-6 era beats, date + change",
                      "THE PAYOFF: the modern world it produced",
                      "THE LOOP: callback answered"],
    "big-question":  ["HOOK: a concrete, oddly specific question",
                      "NAIVE ATTEMPT: let it partially work, then break",
                      "THE KEY INSIGHT: ONE new idea, then a visual pause",
                      "THE BUILD: step by step, each step inevitable",
                      "THE GENERALIZATION: beyond this example"],
}

def proj_dir(name):
    d = os.path.join(REPO, "projects", name)
    os.makedirs(d, exist_ok=True)
    return d

def distribute(total_secs, n):
    """Spread total seconds over n beats, each within [MIN_B, MAX_B]."""
    if total_secs <= 0 or n <= 0:
        return []
    if total_secs / n < MIN_B:
        n = int(total_secs // MIN_B) or 1
    if total_secs / n > MAX_B:
        n = int(total_secs // MEDIAN) + 1
    base = total_secs / n
    # nudge each beat to a plausible jittered duration that still sums up
    durs = []
    remaining = total_secs
    for i in range(n):
        left = n - i
        lo = max(MIN_B, remaining - MAX_B * (left - 1))
        hi = min(MAX_B, remaining - MIN_B * (left - 1))
        d = min(hi, max(lo, base * (0.9 + 0.2 * ((i * 7 + 3) % 5) / 5.0)))
        durs.append(round(d, 2))
        remaining -= d
    # fix rounding drift on the last beat
    drift = round(total_secs - sum(durs), 2)
    durs[-1] = round(durs[-1] + drift, 2)
    return durs

def cmd_plan(args):
    n = int(round(args.duration / MEDIAN))
    durs = distribute(args.duration, n)
    beats = []
    for i, d in enumerate(durs, 1):
        beats.append({"id": i, "spoken": "", "visual": "",
                      "subject": "", "event_type": "hold", "event_time": None,
                      "visual_state_id": None, "duration": d,
                      "source_hint": "hold", "status": "planned"})
    data = {"project": args.project, "topic": args.topic,
            "format": args.format, "target_seconds": args.duration,
            "beat_seconds": n and round(args.duration / n, 2),
            "beats": beats}
    out = os.path.join(proj_dir(args.project), "beats.json")
    json.dump(data, open(out, "w"), indent=2)
    skel = os.path.join(proj_dir(args.project), "script.md")
    with open(skel, "w") as f:
        f.write(f"# {args.topic} — {args.format} format, ~{args.duration}s\n\n")
        f.write("HOOK (first 15 s, one sentence):\n\n")
        for act in FORMATS.get(args.format, FORMATS["myth"]):
            f.write(f"## {act}\n\n")
        f.write("\nFill each act as spoken timing rows. A row may hold/reuse the "
                f"same visual state; do not force one image per beat. Seams are "
                f"'but' or 'therefore'. ~{n} planning rows — see beats.json.\n")
    print(f"{n} beats, median {round(args.duration/n,1)}s each "
          f"-> {out} and {skel}")

def cmd_fit(args):
    path = os.path.join(proj_dir(args.project), "beats.json")
    data = json.load(open(path))
    segs = [float(x) for x in open(args.segments).read().split() if x.strip()]
    segs = [s for s in segs if s > 0.05]
    if not segs:
        raise SystemExit("no positive voiceover segment durations found")
    beats = data["beats"]
    inserted = 0
    # merge short silences into neighbors handled by caller; here: map 1:1
    if len(segs) < len(beats):
        # fewer voiceover segments: merge beats, keep images for reuse order
        merged = []
        # group trailing beats into the last segments
        ratio = len(beats) / len(segs)
        idx = 0
        for si, s in enumerate(segs):
            take = int(round((si + 1) * ratio - round(si * ratio)) or 1)
            grp = beats[idx:idx + take] or beats[idx:idx + 1]
            if grp:
                b = grp[0]
                b["duration"] = round(s, 2)
                if len(grp) > 1:
                    b["spoken"] = " / ".join(x["spoken"] for x in grp if x["spoken"])
                merged.append(b)
            idx += take
        data["beats"] = merged
    elif len(segs) > len(beats):
        # New spoken rows default to a visual hold until semantic planning.
        inserted = len(segs) - len(beats)
        for _ in range(inserted):
            beats.append({"id": len(beats) + 1, "spoken": "",
                          "visual": "", "subject": "", "event_type": "hold",
                          "event_time": None, "visual_state_id": None,
                          "duration": MEDIAN, "source_hint": "hold",
                          "status": "planned", "inserted_by_fit": True})
        data["beats"] = beats
    for b, s in zip(data["beats"], segs):
        b["duration"] = round(s, 2)
    data["voiceover_seconds"] = round(sum(segs), 2)
    json.dump(data, open(path, "w"), indent=2)
    print(f"{len(data['beats'])} beats fitted to {len(segs)} voiceover "
          f"segments ({data['voiceover_seconds']}s)."
          + (f" {inserted} spoken rows inserted; they default to visual hold."
             if inserted else ""))

def cmd_report(args):
    data = json.load(open(os.path.join(proj_dir(args.project), "beats.json")))
    total = sum(b["duration"] for b in data["beats"])
    print(f"{data['project']}: {len(data['beats'])} beats, {round(total,1)}s "
          f"({data['format']})")
    for b in data["beats"]:
        print(f"  {b['id']:>3} {b['duration']:>4.1f}s  {b['source_hint']:<7} "
              f"{b.get('status','?')}  {(b.get('spoken') or '')[:60]}")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("plan"); a.add_argument("project"); a.add_argument("topic")
    a.add_argument("--duration", type=int, default=180)
    a.add_argument("--format", default="myth", choices=list(FORMATS))
    a.set_defaults(fn=cmd_plan)
    a = sub.add_parser("fit"); a.add_argument("project"); a.add_argument("--segments", required=True)
    a.set_defaults(fn=cmd_fit)
    a = sub.add_parser("report"); a.add_argument("project"); a.set_defaults(fn=cmd_report)
    args = p.parse_args(); args.fn(args)

if __name__ == "__main__":
    main()
