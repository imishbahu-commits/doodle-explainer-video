#!/usr/bin/env python3
"""Kokoro-82M TTS helper (hexgrad/Kokoro-82M via the official `kokoro` package).

Usage (after weights are cached locally):
  .venv/bin/python tools/kokoro_tts.py "Hello from Ape." -o out.wav --voice am_michael
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("-o", "--out", default="kokoro.wav")
    ap.add_argument("--voice", default="am_michael",
                    help="masculine: am_adam, am_michael, bm_george, bm_lewis")
    ap.add_argument("--lang", default="a", help="a=US English, b=UK English")
    args = ap.parse_args()

    from kokoro import KPipeline

    pipe = KPipeline(lang_code=args.lang, repo_id="hexgrad/Kokoro-82M")
    chunks = [audio for _, _, audio in pipe(args.text, voice=args.voice)]
    if not chunks:
        raise SystemExit("Kokoro returned no audio")
    wav = np.concatenate(chunks)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.out, wav, 24000)
    print(f"wrote {args.out}  {len(wav)/24000:.2f}s  voice={args.voice}")


if __name__ == "__main__":
    main()
