# OmniVoice — installed in this workspace

Fork: https://github.com/imishbahu-commits/OmniVoice  
Upstream: https://github.com/k2-fsa/OmniVoice  
Install: `OmniVoice/` (editable) + `omnivoice-venv/`

## Commands

```bash
source omnivoice-venv/bin/activate
export HF_HOME="$PWD/omnivoice-models"
export PATH="$HOME/.local/bin:$PATH"

# Auto voice
omnivoice-infer --model k2-fsa/OmniVoice \
  --text "This is a test for text to speech." \
  --output hello.wav --device cpu --language en

# Voice design (no reference clip)
omnivoice-infer --model k2-fsa/OmniVoice \
  --text "This is a test for text to speech." \
  --instruct "male, low pitch, british accent" \
  --output hello.wav --device cpu --language en

# Voice clone
omnivoice-infer --model k2-fsa/OmniVoice \
  --text "This is a test for text to speech." \
  --ref_audio ref.wav --ref_text "Transcript of that clip." \
  --output hello.wav --device cpu --language en

# Gradio UI
omnivoice-demo --ip 0.0.0.0 --port 8001
```

Shortcut:

```bash
scripts/omnivoice_tts.sh --instruct "male, low pitch" "Hello." hello.wav
```

First run downloads **~3.3 GB** of weights from Hugging Face into `omnivoice-models/`.

## This sandbox

This machine has **no GPU** and **~4 GB RAM**. OmniVoice wants a GPU (~4 GB VRAM) and ~8 GB system RAM. The package and CLIs are installed; a real generate will likely OOM here. Use a GPU box, or keep using Fast ingest + your own voiceover for the anglerfish video.
