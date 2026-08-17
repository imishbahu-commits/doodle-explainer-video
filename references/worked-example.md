# Worked example — copy this pattern exactly

A 60-second "myth" chapter, 10 beats, 10 images + keyframes. This is the
pattern a new chat should replicate for EVERY chapter of a video.

## Script (5 acts)

```
THE MYTH:    The Minotaur, the monster with the body of a man and the head
             of a bull, locked inside a giant maze on the island of Crete.
THE DOUBT:   For centuries people assumed it was just a story.
THE DIG:     Then archaeologists dug on Crete in the early nineteen
             hundreds. Under the ground they found a palace with over a
             thousand rooms. It looked almost exactly like a labyrinth.
THE EXPLANATION: Wall paintings showed young people leaping over the horns
             of a charging bull — a real sport, practiced by real people.
THE KICKER:  This is likely where the myth came from.
```

## Images (10 prompts — copy the template, change only SUBJECT)

1. `Hand-drawn doodle illustration of a minotaur, body of a man and head of a bull, on a PURE WHITE background. MS-Paint-like style: thick black outlines, flat bold colors, slightly imperfect hand-drawn lines, simple and menacing. No text, no background scenery, no shadows, no gradients.`
2. `... a giant maze seen from above, on a PURE WHITE background ...`
3. `... a cartoon Greek island in a blue sea ...`
4. `... an archaeologist with a shovel ...`
5. `... an ancient palace with many rooms and twisting hallways ...`
6. `... a stick figure jumping over the horns of a bull ...`
7. `... a charging bull, front view ...`
8. `... a young person mid-leap, arms up ...`
9. `... the same minotaur, sad, sitting in a corner ...`
10. `... the wordless image: the maze and the minotaur fading into one ...`

Backgrounds (2, reused): `Simple hand-drawn doodle landscape background,
MS-Paint-like style: flat cream and light-blue colors, thick black
outlines, wavy hand-drawn lines, completely EMPTY in the middle. No text.`

**The reference lock:** image 1 is generated first, accepted, and passed
as the reference image for images 2–10.

## Motion (ae-motion scene snippets)

- Beat 1 (myth): minotaur slide-in from left, easeOutExpo 0.5s, then idle
  bob. Label "THE MINOTAUR" pops at 0.8s (scale 0.6→1.0 easeOutBack).
- Beat 3 (dig): punch-in on the palace (1.0→1.15, easeInCubic, 1.2s).
- Beat 6 (leap): puppet-pin the jumper's legs (drag track, 1Hz loop) —
  the "character doing something" moment.
- Beats 8→9: hard cut; minotaur pose changes to sad (expression change).
- Every cut: 2–6s holds, hard cuts only, subjects centered, 60 fps.

## Audio

Narration per beat; 0.7s silence at the chapter end; music bed −26 dB
under the voice; final loudness −23 dB. No captions.

## Verify (video-polish)

- cuts ≈ 10 per chapter (one per beat), median hold 2–6s
- pauses ≈ 0.7s at chapter boundary
- every image passes: white bg, thick ink outlines, flat colors
