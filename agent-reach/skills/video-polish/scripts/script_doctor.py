#!/usr/bin/env python3
"""script_doctor.py — grade a narration script like an editor, before any
media is generated. Pure Python, no downloads, no internet.

Checks the nine-move arc from references/script-formula.md plus sentence
craft rules, and prints a scorecard with specific fixes.

Usage:
    python3 script_doctor.py script.txt
    python3 script_doctor.py script.txt --json            # machine-readable
    python3 script_doctor.py --manifest manifest.json     # reconstruct script
                                                            from a build manifest
"""

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

# ---------------------------------------------------------------- helpers

def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def word_count(text):
    return len(re.findall(r"\S+", text))


def first_words(text, n):
    return " ".join(text.split()[:n])


def last_words(text, n):
    return " ".join(text.split()[-n:])


def proper_names(text):
    """Capitalised words that are not sentence starts — crude name detector."""
    candidates = []
    for sentence in sentences(text):
        toks = re.findall(r"\b[A-Z][a-z]{2,}\b", sentence)
        candidates += toks[1:]  # skip the sentence-opening capital
    stop = {"The", "This", "That", "These", "Those", "Your", "You", "It",
            "But", "And", "When", "What", "Why", "How", "Stay", "In",
            "Back", "Imagine", "Turn", "Sit", "Stare", "Bright", "Dim",
            "So", "By", "Familiar", "Old", "Ten", "Don", "Let"}
    return [n for n in candidates if n not in stop]


def years(text):
    """Years as digits or spelled out ('two thousand ten', 'eighteen oh four')."""
    digit_years = re.findall(r"\b(?:1[4-9]\d{2}|20[0-2]\d)\b", text)
    spelled = re.findall(
        r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
        r"twenty)\s+(?:hundred|thousand|oh|forty|fifty|sixty|seventy|eighty|"
        r"ninety)(?:\s+\w+)?\b", text, re.I)
    return digit_years, spelled


def digits_as_tokens(text):
    """Digits that will be read aloud as numbers — should be spelled out."""
    return re.findall(r"\b\d[\d,]*\b", text)


def checks(text):
    words = word_count(text)
    sens = sentences(text)
    first45 = first_words(text, 45)
    last20 = last_words(text, 20)
    third = max(1, math.ceil(words * 0.35))
    first_third = first_words(text, third)
    last15 = " ".join(text.split()[int(words * 0.85):])
    lens = [word_count(s) for s in sens]

    results = []

    # 1. cold open — second person, sensory, within the first ~15 seconds
    ok = ("you" in first45.lower() or "your" in first45.lower())
    results.append(("Hook: second person in the cold open", ok,
                    "Open with the viewer inside a scene: 'you' in the first ~45 words."))

    # 2. impossible fact stated flatly, early
    pat = r"(should not|shouldn't|cannot|can't|never|not once|impossible|no .* has ever)"
    ok = bool(re.search(pat, first_third, re.I))
    results.append(("Paradox: the impossible fact in the first third", ok,
                    "State the contradiction early and flatly ('That should not be possible')."))

    # 3. retention promise
    pat = r"(stay|until the end|end of this video|last part|change how|change the way)"
    ok = bool(re.search(pat, text, re.I))
    results.append(("Promise: explicit reason to stay", ok,
                    "Promise something that lands at the end and ties to the viewer."))

    # 4. mid-video re-hook
    pat = r"(only half|half (the|of)|but (that's|here)|not just)"
    ok = bool(re.search(pat, text, re.I))
    results.append(("Re-hook: pivot around the midpoint", ok,
                    "Declare the story only half told and pivot the question."))

    # 5. turn to the viewer — close on an unanswerable question
    ok = ("?" in last15) and ("you" in last20.lower() or "your" in last20.lower())
    results.append(("Close: question to the viewer, no answer", ok,
                    "End on an open question aimed at the viewer's own life."))

    # 6. named sources — researchers, institutions, dates (digits or spelled out)
    names = proper_names(text)
    inst = re.findall(r"(university|institute|journal|researchers|scientists|"
                      r"psychologist|physician|study|studies)", text, re.I)
    yr, spelled_yr = years(text)
    ok = len(names) >= 1 and (len(inst) >= 1 or len(yr) >= 1 or len(spelled_yr) >= 1)
    results.append((f"Sources: {len(names)} names, {len(inst)} roles, "
                    f"{len(yr) + len(spelled_yr)} dates", ok,
                    "Name real researchers, institutions, and dates; drop claims you cannot source."))

    # 7. sentence length — short-short-long rhythm, fragments for emphasis
    long_sens = [s for s in sens if word_count(s) > 28]
    frags = [s for s in sens if word_count(s) <= 4]
    ok = not long_sens and len(frags) >= 2
    results.append((f"Rhythm: avg {statistics.mean(lens):.1f} words/sentence, "
                    f"max {max(lens)}, {len(frags)} fragments", ok,
                    "Keep sentences short; cut any sentence over ~28 words; use fragments."))

    # 8. numbers spelled out for the ear
    d = digits_as_tokens(text)
    ok = not d
    results.append((f"Spoken numbers: {len(d)} digit tokens", ok,
                    f"Write numbers as speech: {', '.join(d) if d else 'none'}"))

    # 9. word budget vs target length
    minutes = words / 217.0
    est = minutes * 60
    results.append((f"Budget: {words} words ≈ {est:.0f}s ({minutes:.1f} min) at 217 wpm", True,
                    "60s ≈ 215 words · 3min ≈ 650 · 10min ≈ 2,200"))

    return results, words, est


def from_manifest(path):
    m = json.loads(Path(path).read_text())
    parts = []
    if "sections" in m:
        for s in m["sections"]:
            parts.append(" ".join(b["text"] for b in s["beats"]))
    elif "beats" in m:
        parts.append(" ".join(b["text"] for b in m["beats"]))
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="script text file")
    ap.add_argument("--manifest", help="or a build manifest to reconstruct from")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.manifest:
        text = from_manifest(args.manifest)
    elif args.input:
        text = Path(args.input).read_text()
    else:
        sys.exit("give a script file or --manifest")

    results, words, est = checks(text)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    grade = round(10 * passed / total)

    if args.json:
        print(json.dumps({
            "words": words, "est_seconds": round(est, 1),
            "grade": grade, "passed": passed, "total": total,
            "checks": [{"name": n, "ok": ok, "fix": fix}
                       for n, ok, fix in results],
        }, indent=2))
        return

    bar = "█" * grade + "░" * (10 - grade)
    print(f"SCRIPT DOCTOR — {words} words, ≈{est:.0f}s at 217 wpm")
    print(f"grade: {grade}/10  [{bar}]")
    print()
    for name, ok, fix in results:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}")
        if not ok:
            print(f"      fix: {fix}")
    print()
    if grade >= 8:
        print("Verdict: ready to record. Generate media.")
    elif grade >= 6:
        print("Verdict: fix the FAILs above, then show the script for sign-off.")
    else:
        print("Verdict: restructure before generating anything — script is the cheapest thing to change.")


if __name__ == "__main__":
    main()
