#!/usr/bin/env python3
"""Split script.md narration into 12-16 word beats -> beats.json.

One spoken beat = one image (Dinzo format). Re-run anytime the script changes.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = (12, 16)  # words per beat


def load_narration(path: Path) -> str:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith(">"):
            continue
        if line.startswith("Sources:"):
            continue
        lines.append(line)
    return " ".join(lines)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def append_or_flush(beats: list[str], buf: str, piece: str) -> str:
    if not buf:
        return piece
    trial = f"{buf} {piece}".strip()
    if len(trial.split()) <= TARGET[1]:
        return trial
    beats.append(buf)
    return piece


def split_long(sentence: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"(?<=,)\s+", sentence) if p.strip()]
    out, buf = [], ""
    for p in parts:
        buf = append_or_flush(out, buf, p)
    if buf:
        out.append(buf)
    return out


def to_beats(sents: list[str]) -> list[str]:
    beats, buf = [], ""
    for s in sents:
        if len(s.split()) > TARGET[1]:
            if buf:
                beats.append(buf)
                buf = ""
            for piece in split_long(s):
                buf = append_or_flush(beats, buf, piece)
        else:
            buf = append_or_flush(beats, buf, s)
    if buf:
        beats.append(buf)
    return beats


def main() -> None:
    script = ROOT / "script.md"
    text = load_narration(script)
    beats = to_beats(sentences(text))
    out = ROOT / "beats.json"
    out.write_text(json.dumps(beats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_words = sum(len(b.split()) for b in beats)
    print(f"{len(beats)} beats, {total_words} words -> {out.name}")


if __name__ == "__main__":
    sys.exit(main())
