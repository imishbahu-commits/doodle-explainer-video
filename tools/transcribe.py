#!/usr/bin/env python3
"""Transcribe an audio file with the local Vosk model.

Usage:
    transcribe.py INPUT_AUDIO [--out OUT_JSON] [--wpm N]

Converts the input to 16 kHz mono WAV with the bundled imageio-ffmpeg,
runs the Vosk small English model, and writes:
  - plain text transcript
  - word-level timestamps (JSON)
  - estimated beats (chunks of ~12-15 words with start/end times)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import imageio_ffmpeg
from vosk import KaldiRecognizer, Model

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "vosk-model-small-en-us-0.15")


def to_wav16k(src: str, dst: str):
    subprocess.run(
        [FFMPEG, "-y", "-i", src, "-ar", "16000", "-ac", "1", "-f", "wav", dst],
        check=True, capture_output=True,
    )


def transcribe(wav_path: str):
    model = Model(MODEL_DIR)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    with open(wav_path, "rb") as f:
        data = f.read()
    results = []
    # Vosk expects ~4KB chunks
    chunk = 4000
    for i in range(0, len(data), chunk):
        if rec.AcceptWaveform(data[i:i + chunk]):
            res = json.loads(rec.Result())
            if res.get("result"):
                results.append(res)
    res = json.loads(rec.FinalResult())
    if res.get("result"):
        results.append(res)
    words = [w for r in results for w in r.get("result", [])]
    text = " ".join(w["word"] for w in words)
    return words, text


def make_beats(words, words_per_beat=13):
    """Group words into beats of ~13 words (roughly 3.6 s at ~217 wpm)."""
    beats = []
    for i in range(0, len(words), words_per_beat):
        chunk = words[i:i + words_per_beat]
        beats.append({
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "text": " ".join(w["word"] for w in chunk),
        })
    return beats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", default=None)
    ap.add_argument("--wpm", type=int, default=217)
    args = ap.parse_args()

    workdir = os.path.dirname(os.path.abspath(args.input)) or "."
    # A fixed `_tmp_16k.wav` races when several videos are transcribed in
    # parallel. Give every process its own scratch file in the media folder.
    fd, wav = tempfile.mkstemp(
        prefix=f"_{os.path.splitext(os.path.basename(args.input))[0]}_",
        suffix="_16k.wav",
        dir=workdir,
    )
    os.close(fd)
    try:
        print(f"[1/3] converting {args.input} -> 16kHz mono wav", file=sys.stderr)
        to_wav16k(args.input, wav)
        print("[2/3] transcribing with vosk small en-us", file=sys.stderr)
        words, text = transcribe(wav)
        beats = make_beats(words, words_per_beat=max(8, args.wpm // 17))
        out = {
            "duration": words[-1]["end"] if words else 0,
            "word_count": len(words),
            "text": text,
            "words": words,
            "beats": beats,
        }
        out_path = args.out or os.path.join(workdir, "transcript.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"[3/3] wrote {out_path} ({len(words)} words, {len(beats)} beats)", file=sys.stderr)
        print()
        print("=== TRANSCRIPT ===")
        print(text)
        print()
        print(f"=== {len(beats)} BEATS ===")
        for i, b in enumerate(beats, 1):
            print(f"{i:02d} [{b['start']:7.2f} -> {b['end']:7.2f}] {b['text']}")
    finally:
        if os.path.exists(wav):
            os.remove(wav)


if __name__ == "__main__":
    main()
