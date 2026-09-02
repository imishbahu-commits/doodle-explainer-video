#!/usr/bin/env python3
"""Generate VO for a part of the dumbest-wars script in ONE kokoro session."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from script import BEATS
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

KOKORO_MODEL = "assets/models/kokoro-quantized.onnx"
KOKORO_VOICES = "assets/models/voices.npz"
VOICE = "am_michael"
SPEED = 1.35

def main() -> None:
    part = int(sys.argv[1])
    outdir = Path("audio"); outdir.mkdir(exist_ok=True)
    kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
    def _style_for(voice, length):
        i = min(length, 509) * 256
        return voice[i:i+256][None, :]
    kokoro._style_for = _style_for
    beats = [b for b in BEATS if b["part"] == part]
    total = 0.0
    for b in beats:
        t0 = time.time()
        audio, sr = kokoro.create(b["text"], voice=VOICE, speed=SPEED, lang="en-us", trim=True)
        p = outdir / f"beat{b['n']:02d}.wav"
        sf.write(p, audio, sr)
        d = len(audio) / sr
        total += d
        print(f"beat{b['n']:02d} ok {d:.2f}s {b['text'][:60]}  ({time.time()-t0:.1f}s)", flush=True)
    print(f"PART {part} VO DONE: {len(beats)} clips, {total:.1f}s total")

if __name__ == "__main__":
    main()
