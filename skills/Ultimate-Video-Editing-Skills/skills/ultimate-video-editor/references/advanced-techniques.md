# Advanced AI Video Editing Techniques

## AI-Powered Editing (Research-Grade)

### AnimateAnything (Alibaba)
Animates static images into video via text prompts using 3D U-Net video diffusion.
- Motion area masks control which regions animate
- Multiple simultaneous motion regions supported
- Motion strength parameter: subtle to pronounced
- Paper: [arxiv.org/abs/2311.12886](https://arxiv.org/abs/2311.12886)
- Code: [github.com/alibaba/animate-anything](https://github.com/alibaba/animate-anything)

### I2VEdit (SIGGRAPH ASIA 2024)
Edit one frame → propagate edits through entire video via image-to-video diffusion.
- Handles: global edits, local edits, moderate shape changes
- Coarse motion extraction → appearance refinement pipeline
- Skip-interval strategy prevents quality degradation in long videos
- Use cases: virtual try-on, subject replacement, style transfer
- Site: [i2vedit.github.io](https://i2vedit.github.io/)

### Multi-Modal Material Analysis
Before editing, analyze each clip across 3 dimensions:
1. **Visual** — scene content, composition, movement, lighting, color temperature
2. **Audio** — speech content, volume levels, ambient sound, music presence
3. **Temporal** — duration, pacing, energy curve, action density

---

## 30+ Hard-Won Pitfalls

### Transcription Pitfalls
1. Whisper hallucinates on silent footage — always verify transcript vs actual audio
2. Check for phantom text on silent clips (Whisper's most common hallucination)
3. Subtitle timing drifts 50-100ms from ASR — pad cut edges to absorb
4. Word-level ASR only — never SRT/phrase mode (loses sub-second gap data)
5. Cache transcripts per source — never re-transcribe unless the source file changed
6. FunASR gives character-level timestamps (better for CJK); Whisper gives word-level (better for English)

### FFmpeg Pitfalls
7. Concat demuxer can lose frames — use `filter_complex` for frame-accurate joins
8. Never `2>/dev/null` during setup — you need to see actual errors
9. Re-encoding degrades quality — use `-c copy` lossless concat where possible
10. Check codec compatibility before concatenating clips from different sources
11. Audio sample rate mismatches cause sync drift — normalize to 48kHz first
12. Frame rate mismatches between clips cause stuttering — normalize fps first
13. `-movflags +faststart` is critical for web playback — always include it
14. Filter chain order matters: resize → crop → effects → text → subtitles
15. `setpts` filter doesn't affect audio — pair with `atempo` for speed changes

### Production Pitfalls
16. Vertical video (9:16) requires explicit handling — don't just letterbox
17. Audio normalization must happen AFTER all cuts, not before
18. Scene detection tools (scenedetect) help but aren't perfect — verify visually
19. Always preserve original files — never edit source material in place
20. Long videos: process in segments to avoid memory issues
21. GPU acceleration (NVENC/VideoToolbox) speeds rendering 5-10x but has quality trade-offs
22. Never reuse output filenames — caches show stale content (learned from [Monet](https://github.com/Monet-AI-Editor/Monet))
23. Overlay timing requires `setpts=PTS-STARTPTS+T/TB` to sync frame 0 to window start
24. Master SRT must use output-timeline offsets, not source-timeline offsets
25. Subtitles LAST in filter chain — overlays hide captions otherwise

### Workflow Pitfalls
26. Don't auto-merge clips without user confirmation
27. Don't assume video type — look at the material, ask the user, then edit
28. Don't over-cut — sometimes the best edit is no edit
29. Don't add music louder than dialogue — duck 6-12dB
30. Don't export at higher quality than source — it just wastes filesize
31. Test on target platform before final delivery — what looks good locally may compress badly
32. Always check the first and last frame of every segment for flash frames

---

## Pro Editor Heuristics

### The 6-Second Rule
Every 6 seconds, something should change — cut, camera move, new info, music shift, or visual change. This keeps viewer attention.

### The Breath Principle
Great editing breathes. Tension needs release. Fast sections need slow follow-ups. Silence after noise is powerful. Don't fill every second.

### The 180-Degree Rule
Keep camera on one side of the action line. Crossing it disorients. Bridge with a neutral shot when you must cross.

### Continuity of Energy
Match energy levels across cuts. Don't jump from calm to chaos without a bridge shot or audio transition.

### The Kuleshov Effect
Meaning is created by juxtaposition. A face + food = hunger. A face + coffin = grief. Same face, different meaning.

### Sound Leads Image
The ear processes faster than the eye. Bring in audio 2-4 frames before the visual cut. J-cuts exploit this.

### The Rule of Three
Three beats, three acts, three examples. The brain processes patterns of three. Use it in montages, reveals, and sequences.

### Eye Trace
Track where the viewer's eye will be at each cut. Place the next shot's point of interest near where the eye already is.
