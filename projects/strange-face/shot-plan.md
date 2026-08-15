# Shot Plan — "Why isn't your reflection you?" (director cut)

Produced with `skills/cinematic-director` (DirectorSKILL v2.0), Modes A–D,
lens: **David Fincher** (surgical dread). 720×1280, three fixed bands,
band B is a locked "monitor" frame — one fixed illustration per beat, hard
cuts, exactly ONE camera move in the whole video.

## Directing rules (Director's Book)

1. **The mirror is the only thing that moves its gaze** — zero motion
   elsewhere; motion is the viewer's imagination.
2. **Teal shadows, one amber practical, red reserved for the threat**
   (monster eyes, X marks, the accent word) — implemented as a colour grade:
   40% desaturation, teal shifted shadows, lifted blacks, boosted reds.
3. **Every frame carries one readable fact** (a number, a name, a diagram).

## Beat sheet → shots

19 beats (B1 cold open → B3 impossible fact → B4/B5/B6 evidence → B7 wound
(1.2s cut, deliberate) → B9 promise → B10 mechanism → B12 Troxler → B14
fragments → B15 reversal (**the only punch-in**, lands on "model") → B16/B17
natural experiment → B18/B19 turn to the viewer, unanswerable close, 1s
silence. ASL 3.4s; sizes alternate WS/MCU/ECU; B3/B6/B14 are the ECU
"specimen cards".

## Implemented in make_director_cut.py

- `fincher_grade()` — teal shadow grade + lifted blacks + red threat boost
- single ease-in punch (1.0→1.18) on beat 15 (IN THE BRAIN)
- band C verified pure black; beat boundaries re-measured from the encoded
  video; narration reused from final.mp4
