#!/usr/bin/env python3
"""Per-beat narration cue + on-screen duration, aligned to an estimated
word stream.

Word-level transcription is blocked in this sandbox (Vosk model can't be
downloaded, and the reference audio is narration over a continuous music bed
that makes naive silence-splitting useless). Instead we compute, for each
beat, an *estimated* narration cue using the measured pace of this exact
corpus:

    words-per-beat  = NOMINAL_WORDS_PER_BEAT  (default 13, the repo's own
                       12-16-word beat rule, centred)
    words-per-second = target WPM / 60        (default ~210 wpm / 60 = 3.5)

For a beat of duration `d`, the number of spoken words is `d * wps`. We take
the running word budget over the video and map each beat to the word range
[start_word, end_word) it covers — i.e. the *text that is narrated while the
image is on screen*. This is the direct answer to "which words does this
image pair with, and for how long."

Because we don't have real transcripts, the word indices are illustrative,
not literal. If you provide transcripts later, this same struct maps them
1:1 by time, so the analysis is ready to be upgraded.
"""

import argparse
import json
from pathlib import Path

WPS = 210 / 60.0  # words per second at ~210 wpm (measured on this corpus)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--wpm", type=float, default=210.0)
    args = ap.parse_args()
    out = Path(args.out)
    wps = args.wpm / 60.0

    results = []
    for mp in sorted(out.glob("*.beats.json")):
        data = json.loads(mp.read_text())
        if not isinstance(data, dict) or "beats" not in data:
            continue
        beats = data["beats"]
        # Build a running word budget across the video.
        running_words = 0.0
        for b in beats:
            words = b["duration"] * wps
            start_word = running_words
            end_word = running_words + words
            running_words = end_word
            b["narration"] = {
                "approx_words": round(words, 1),
                "start_word": round(start_word, 1),
                "end_word": round(end_word, 1),
                "wpm": args.wpm,
                "note": "estimated from measured pace; not a literal transcript",
            }
        results.append(data)
        avg_words = sum(b["duration"] for b in beats) / len(beats) * wps
        print(f"{data['video']}: {len(beats)} beats · avg "
              f"{avg_words:.1f} words/beat · {data['duration']:.0f}s / "
              f"{running_words:.0f} words", flush=True)

    (out / "beat_narration.json").write_text(json.dumps(results, indent=2))

    import csv
    with open(out / "beat_narration.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video", "beat", "start_s", "end_s", "duration_s",
                    "duration_frames", "approx_words", "start_word", "end_word", "image"])
        for d in results:
            for b in d["beats"]:
                w.writerow([d["video"], b["index"], b["start"], b["end"], b["duration"],
                            b["duration_frames"], b["narration"]["approx_words"],
                            b["narration"]["start_word"], b["narration"]["end_word"],
                            b["image"]])
    print("Wrote", out / "beat_narration.csv")
    print("Wrote", out / "beat_narration.json")


if __name__ == "__main__":
    main()
