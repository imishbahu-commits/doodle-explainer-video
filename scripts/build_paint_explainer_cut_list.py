#!/usr/bin/env python3
"""Render the machine-readable per-video cut CSVs as one Markdown appendix."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "references" / "paint-explainer-analysis-4v"


def main() -> None:
    manifest = json.loads((BASE / "analysis_manifest.json").read_text(encoding="utf-8"))
    lines = [
        "# Complete detected cut/edit-event list",
        "",
        "> Every source frame was decoded at 30 fps. Boundaries use PySceneDetect",
        "> ContentDetector threshold 18, minimum 6 frames. Timing uncertainty is",
        "> ±1 source frame (±0.033 s). `localized_swap_or_pop` is an abrupt",
        "> same-canvas visual event; the flattened MP4 cannot prove whether it was",
        "> authored as an editor cut or as a one-frame layer swap inside one comp.",
        "",
        "Machine-readable originals: [`cuts/`](cuts/).",
        "",
    ]
    for item in manifest["videos"]:
        file_id = str(item["file_id"])
        path = BASE / "cuts" / f"{file_id}-cuts.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        lines += [
            f"## {item['title']}",
            "",
            f"- Source ID: `{file_id}` / YouTube `{item['youtube_id']}`",
            f"- Detected edit events: **{len(rows)}**",
            f"- Runtime: **{item['duration_seconds']:.2f} s**",
            "",
            "| # | Cut at | Prior shot | Class | Chapter | Nearest spoken word | Cut − word start |",
            "|---:|---:|---:|---|---|---|---:|",
        ]
        for row in rows:
            delta = float(row["cut_minus_word_start_seconds"])
            lines.append(
                f"| {row['event']} | {row['timestamp']} | {float(row['preceding_shot_duration_seconds']):.3f} s "
                f"| {row['transition_class']} | {row['chapter'].replace('|', '/')} "
                f"| {row['nearest_spoken_word']} | {delta:+.3f} s |"
            )
        lines.append("")
    (BASE / "CUT_LIST.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {BASE / 'CUT_LIST.md'}")


if __name__ == "__main__":
    main()
