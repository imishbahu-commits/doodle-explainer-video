# Lightweight TTS (runs on this sandbox)

OmniVoice was removed — it needs a GPU and ~8 GB RAM. This box has **2 CPUs, 4 GB RAM, no GPU**.

Installed engine: **Piper** (`piper-tts` 1.7, ONNX Runtime, CPU).

## Voices that work here (verified)

| Name | Who | Notes |
|---|---|---|
| **en_US-lessac-medium** | US male | Clear narration. **Default.** |
| **en_US-joe-medium** | US male | More casual |
| **en_US-Jarvis_Real-medium** | US male | Deeper “assistant” tone |

These are the same family of small Piper voices (~60 MB each). Any other Piper `*-medium` / `*-low` English voice would also run if we add the `.onnx` + `.onnx.json`. Names that fit this machine but are **not downloaded yet** (Hugging Face is blocked here):

- `en_US-ryan-medium` / `en_US-ryan-high` — popular male
- `en_US-norman-medium` — male
- `en_GB-alan-medium` — British male
- `en_US-amy-medium` — US female
- `en_US-lessac-high` — same speaker as default, higher quality

## Generate

```bash
scripts/tts.sh "You are born in a floating raft of eggs." out.wav
scripts/tts.sh --voice en_US-joe-medium "Hello." joe.wav
scripts/tts.sh --list
```

Samples: `tts-voices/samples/*.wav`
