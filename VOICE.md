# VOICE.md — the Dinzo narration voice recipe

The channel voice used across all `projects/dinzo-*` videos is a **masculine,
deadpan, human-sounding narrator**. In Arena it is registered per-session via
the `add_voice` tool and was stored in-session as **`voice-02`**.

## ⚠️ Important
Voice IDs are **session-scoped**. They do NOT persist across new chats, and
the voice cannot be exported as an audio file. Every new chat must re-audition
and re-pick. The recipe below reproduces the exact candidate pair the user
chose.

## The recipe (copy this into any new chat)

```
Set up my narration voice using add_voice with:
- language: "en"
- voice_identity: {"gender": "masculine", "use_case": "narration", "index": 2}
- audition text: "Now you're hungry. And this is where being a mosquito stops
  being a comedy and starts being a horror movie — for you. You need blood to
  make eggs. It is not optional. So you follow the breath, the sweat, the
  heat, toward a giant warm thing that has no idea you exist."
Then I'll pick the voice I like (the deeper, clear, deadpan one).
```

When the audition plays, **pick the same voice as before** — the deeper,
clear, engaging, deadpan masculine one. It will then be registered and
`generate_speech` can use it for the whole video.

## Why `index: 2`
- `index: 0` = first audition pair (rejected — not deep/clear enough)
- `index: 1` = second pair (rejected — wanted more human/deadpan)
- `index: 2` = the pair the user approved → registered as `voice-02` ✅

Use the SAME `gender`, `use_case`, and `index` on re-audition to get the same
candidate pair. (The exact voice model is selected by Arena; these parameters
are what reproduce the choice.)

## If the voice ever sounds different
- Re-audition with `index` bumped by 1 (e.g. `index: 3`) and listen for the
  same character: masculine, deep-ish, steady, deadpan, not sing-song.
- Voice consistency across beats matters more than the art — keep one
  registered `voice_id` for an entire video.
