# Format spec

Every number here was measured off the reference video (a 10:09 orca explainer,
720x1280, 30fps). `scripts/build_video.py` already encodes all of it — this file
exists so you can reason about the format and change it deliberately.

## Canvas

| Property | Value |
|---|---|
| Resolution | 720 x 1280 (9:16) |
| Frame rate | 30 fps, constant |
| Video codec | H.264 High, yuv420p, ~210 kbps |
| Audio codec | AAC, 44.1 kHz, stereo, ~62 kbps |
| Duration | 609 s (10:09) |

The low bitrate is not a constraint to copy — it is what Facebook's transcode
left behind. Render at CRF 23 and let the platform compress.

## The three bands

The frame is split into three fixed horizontal bands that never move. This is
the single most recognisable trait of the format.

| Band | Y range | Height | Content |
|---|---|---|---|
| A — banner | 0–420 | 420 | Static clickbait title + character art |
| B — illustration | 420–840 | 420 | The doodle that changes per beat |
| C — empty | 840–1280 | 440 | Pure black, **no text** |

Band C stays empty in this skill. The reference put karaoke captions there, but
we deliberately leave it blank — see "Captions" below. The band itself is still
load-bearing: it pushes the illustration into the upper-middle of the frame,
clear of the play controls, caption text, and action buttons that platforms
overlay along the bottom of a vertical video.

Bands A and B are each ~16:9, so generate both at 16:9 and centre-crop to fill.

Band A is a **single image reused for the entire video**. It never animates. It
functions as a permanent thumbnail so a scroller who joins mid-video still sees
the hook question.

## Colours

| Role | Hex | Notes |
|---|---|---|
| Banner background | `#0A0D2F` | Near-black navy |
| Banner title (base) | `#FCEB00` | Yellow |
| Banner title (accent word) | `#FF0000` | Pure red, one word only |
| Band C background | `#000000` | Pure black, no texture, no text |
| Caption text | `#FFFFFF` | Unused — captions are off |
| Caption highlight | `#C1FF08` | Unused — captions are off |

## Captions — not used

**This skill renders no captions.** Band C is left empty black. Everything in
this section documents what the reference did, kept only so the option is
recoverable via `build_video.py --captions`.

| Property | Measured value |
|---|---|
| Font | Heavy grotesque, all-caps (Arial Black is a good stand-in) |
| Cap height | 40 px |
| Baseline pitch | 56 px — tighter than any font's default leading |
| Block anchor | Centred at y=996 **regardless of line count** |
| Lines per card | 1–3 |
| Words per card | 3–4 |
| Card duration | ~1.0 s median |
| Max text width | ~600 px |

Two details that matter more than they look:

- The block is centred at y=996, which is *above* the band's own centre
  (y=1060). One-line and three-line cards share that same centre, so cards do
  not appear to jump vertically as they change.
- The 56 px pitch against a 40 px cap height is deliberately tight. libass'
  default leading is much looser, so `build_video.py` emits one ASS event per
  line at an explicit `\pos` rather than using `\N` line breaks.

Exactly one word per card is lime. It is the most semantically loaded word, not
a fixed position. Everything else stays white.

## Illustration cadence

With captions off, illustration cuts are the only motion in the frame, so this
cadence matters more here than it did in the reference.

| Metric | Value |
|---|---|
| Distinct illustrations | ~150–195 over 609 s |
| Median hold | 2–3 s |
| Mean hold | 3.4–4.1 s |
| Longest hold | ~14 s |

So roughly **one illustration per 12–15 spoken words**. Images are fully static
while held — no Ken Burns, no pan, no zoom, no transitions. Cuts are hard. The
motion in this format comes entirely from the captions changing.

## Audio

| Metric | Value |
|---|---|
| Mean level | -17.5 dBFS |
| Peak | 0.0 dBFS |
| Speaking rate | ~217 wpm |
| Music bed | **None** |
| Sound effects | **None** |

This is worth stating plainly because it is counterintuitive: the reference has
no background music and no sound effects at all. Inter-sentence gaps drop to
-57 dBFS, i.e. true silence. The format carries a 10-minute video on a single
narration track.

The 217 wpm rate is brisk — noticeably faster than documentary narration. It is
what keeps a 10-minute retention curve alive.

Natural pauses of 0.4–0.8 s land at paragraph boundaries, not between every
sentence. `build_video.py --gap` appends that breath after each section.

If you do add a bed, `--music --music-db -26` keeps it far enough under the
voice to stay out of the way. Default is off, matching the reference.
