# VOICEOVER-BEATS.md — get SHORT beat clips (2–6s), not 12–14s

## The problem
In a new chat the narration clips come out 12–14 seconds per beat. That means
the agent is feeding WHOLE PARAGRAPHS (or whole sections) into the speech tool
instead of one short beat. Long clips = long beats = stretched images = wrong.

## The rule (what made the beats short in the original chat)
**1 beat = 1 sentence = 12–16 words = ONE generate_speech call = ~2–6 seconds.**

Measured examples (voice-02, before the 0.25s breath pad):
- "You are born in a puddle." (5 words) → ~1.5 s
- "You are born in a hole in the ground, in the dark," (12 words) → ~3.1 s
- "In the wild, about one cub in four dies this way." (11 words) → ~3.3 s
- "Hyena cubs are born armed. Full canines, full incisors," (10 words) → ~3.3 s
- A ~20-word beat → ~6 s  ← this is the UPPER limit, do not exceed

Never longer than ~7 s. If a clip is 12–14 s, the text is ~3× too long — split it.

## The exact workflow (paste this into a new chat)

```
Read VOICE.md first to register my narration voice (masculine, use_case
narration, index 2 — I'll pick the deeper deadpan one).

Then follow these voiceover rules EXACTLY:

1. Beats come from beats.json (already split to 12-16 words each), NOT from
   script.md paragraphs. If beats.json is missing, run
   `.venv/bin/python make_beats.py` to regenerate it from script.md.
2. Generate ONE audio clip PER BEAT, using the exact beat text, nothing else.
   NEVER merge two beats into one clip. NEVER narrate a whole section in one
   call. NEVER add words to a beat's text.
3. Beat text stays 12-16 words. If a beat is longer than ~16 words, split it
   into two beats first. If it's 2-4 words, leave it (a ~1.5s punchy clip is
   correct — that's the Dinzo rhythm).
4. Save each clip as audio/beatNN.mp3 (NN = 01, 02, 03…).
5. Do 10 clips per turn, in parallel. After each 10, stop and say "go".
```

## The numbers (why it works)
- The narration voice reads ~2.5–3 words/second.
- 12–16 words ÷ 2.7 ≈ 4.5–6 seconds. ✅
- 40+ words (a paragraph) ÷ 2.7 ≈ 14+ seconds. ❌ ← this is the bug you hit.

## Good vs bad (concrete)

| ✅ Correct beat text (→ ~4–5s clip) | ❌ Wrong (paragraph → 12–14s clip) |
|---|---|
| "You are born in a puddle." | "You are born in a puddle. Not an ocean, not a nest, not anywhere special — a puddle. A tire track. A clogged gutter. A bucket someone forgot outside last July. Any inch of stagnant water will do..." |
| "Hyena cubs are born armed. Full canines, full incisors," | "You are born in a hole in the ground with your eyes open and teeth in, and the first thing that happens is someone tries to kill you — your twin, born an hour before, who shakes you by the shoulders..." |

## Assembly (after audio is generated)
Each image is held for exactly its own clip's length, hard cuts:
```bash
.venv/bin/python make_video.py <start> <end> -o partN.mp4
.venv/bin/python make_video.py 1 <total> -o dinzo-<animal>-final.mp4
```
The assembler reads the REAL duration of each audio/beatNN.mp3 with ffprobe,
so short clips = short image holds = the 2–6s cut rhythm. Nothing to tune.

## If beats.json got too long anyway
The splitter targets 12–16 words. If a chat ever produced longer beats, just
regenerate from the script:
```bash
.venv/bin/python make_beats.py   # rewrites beats.json at 12-16 words/beat
```
