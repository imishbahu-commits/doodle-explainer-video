#!/usr/bin/env python3
"""Kokoro-82M local neural TTS (fully offline, npm-recovered weights)."""
import argparse
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

KOKORO_MODEL = "projects/dumbest-wars-16092/assets/models/kokoro-quantized.onnx"
KOKORO_VOICES = "projects/dumbest-wars-16092/assets/models/voices.npz"

def main() -> None:
    ap = argparse.ArgumentParser(description="Kokoro local TTS (offline)")
    ap.add_argument("text")
    ap.add_argument("-o", "--out", default="out.wav")
    ap.add_argument("-v", "--voice", default="am_michael")
    ap.add_argument("-s", "--speed", type=float, default=1.05)
    args = ap.parse_args()
    kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
    def _style_for(voice, length):
        i = min(length, 509) * 256
        return voice[i:i+256][None, :]
    kokoro._style_for = _style_for
    audio, sr = kokoro.create(args.text, voice=args.voice, speed=args.speed, lang="en-us", trim=True)
    sf.write(args.out, audio, sr)
    print(f"wrote {args.out} ({len(audio)/sr:.1f}s, voice={args.voice})")

if __name__ == "__main__":
    main()
