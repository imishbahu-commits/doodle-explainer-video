# 📋 COPY-PASTE — Rebuild the channel style after any wipe

Paste into any new Arena chat (same repo). Recreates the measured channel style,
the fast uploader, and the TTS stack. **All work below must be pushed to the
session branch so it survives resets.**

---

```
The workspace maintains a committed Style DNA Kit at
references/paint-explainer-analysis-4v/SURVIVAL_KIT/.

1. READ FIRST (in order):
   - SURVIVAL_KIT/STYLE_DNA_KIT.md   (style rules + rebuild commands)
   - SURVIVAL_KIT/PROVEN_PROMPTS.md  (exact image prompts + 7 failure checks)
   - STYLE_SPEC_IMPLEMENTABLE.md     (full 44-rule spec + 10 recipe cards)

2. REBUILD ENV (never HuggingFace — blocked):
   - python3 -m venv /home/user/.venv
   - pip install kokoro-onnx onnxruntime espeakng-loader phonemizer numpy soundfile pillow imageio-ffmpeg
   - TTS weights: npm pack expo-kokoro → copy kokoro-quantized.onnx + build voices/*.bin into
     <project>/assets/models/voices.npz (STYLE_DNA_KIT.md §5)
   - ffmpeg: .venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())" → /usr/local/bin/ffmpeg
   - ffprobe: npm ffprobe-static → linux/x64/ffprobe → /usr/local/bin/ffprobe

3. GENERATING STYLE IMAGES (STRICT):
   - ALWAYS pass style_locked_crops/ref_blackbeard_char.png as image reference.
   - Use PROVEN_PROMPTS.md base template; fill only the SCENE string.
   - Check the 7 failure signatures before using any image; regenerate if any appear.
   - NEVER use "engraving/ink/painting" wording — the style is FLAT DOODLE.

4. VIDEO RENDER RULES (measured, non-negotiable):
   - Locked camera (scale 1.0); no zoom/pan/dissolve/parallax.
   - Hard cut at word_start − 0.050 s.
   - One image per beat; beat = 12–16 words; image shown exactly the beat duration.
   - No idle animation, no lip sync, no captions.
   - 1280×720 @ 30 fps, h264, loudnorm −16 LUFS mix.

5. Also run the fast uploader on 8013: python3 tools/upload_server.py 8013
   (and video preview: python3 -m http.server 8090 --bind 0.0.0.0 in the project dir).

6. Report the live preview URLs + confirm GET / on 8013 returns 200.
7. git add + git commit + git push origin <session-branch> after every deliverable.
```

---

## Why this works across resets
- All analysis + prompts + spec live in **git** (`references/…`), pushed to origin.
- Large binaries (model weights, mp4s) are re-fetchable: TTS model = npm
  `expo-kokoro`; ffmpeg = PyPI `imageio-ffmpeg`; both allowed.
- No external service required: images reuse committed reference crops; voice
  uses local ONNX stack; renderer is pure ffmpeg + PIL.
