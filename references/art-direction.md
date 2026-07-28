# Art direction

Two distinct visual jobs: the banner (one image, whole video) and the beat
illustrations (~150 for a 10-minute video). They look nothing alike.

## Banner (band A)

One 16:9 image, reused for the entire runtime. Semi-realistic cartoon, menacing,
saturated — it is a thumbnail, not an illustration.

Reference: three cartoon orcas on `#0A0D2F` navy, mouths open, glowing red eyes,
one large centre-facing subject flanked by two smaller ones.

Prompt template:

```
Cartoon vector illustration, 16:9, flat dark navy background (#0A0D2F).
Three menacing cartoon {SUBJECT}s facing the viewer — one large in the centre,
two smaller flanking it. Glowing red eyes, open mouths showing teeth, bold black
outlines, saturated flat colour, high contrast, no gradients, no text.
YouTube thumbnail style, dramatic and slightly comedic.
```

Generate the title text separately rather than asking the image model for it —
models mangle lettering. Compose it in with PIL or an ASS overlay:

- All caps, heavy grotesque, ~3–5 words, phrased as a question
- Base colour `#FCEB00`, with exactly **one** word in `#FF0000`
- The red word is the threat or the stake: "WON'T **KILL** US?"

## Beat illustrations (band B)

The opposite register: crude, minimal, hand-drawn stick figures. The naivety is
the point — it reads as an explainer sketch, not as art, and it keeps attention
on the narration.

Fixed rules across every beat:

- **Stick figures** for humans: circle head, single-line limbs, no clothing
  detail, dot eyes, minimal expression
- **Thick uniform black outlines** on everything
- **Flat colour fills only** — no gradients, no shading, no texture
- **One flat background colour** per illustration, filling the frame
- **Hand-lettered ALL-CAPS labels** where a label clarifies (`100 METERS`,
  `LARGEST ANIMAL ON EARTH`, `SELECTIVE EATER`)
- **Empty space is fine.** Most reference frames have 2–4 elements total.

Background colours seen in the reference, cycled by scene mood:

| Colour | Hex | Used for |
|---|---|---|
| White | `#FFFFFF` | Neutral diagrams, comparisons, charts |
| Sky blue | `#5FBCE4` | Underwater / ocean surface |
| Ocean blue | `#3F81B2` | Deeper water |
| Cream | `#FFE0AC` | Land, savanna, above-water |
| Orange | `#F2A63B` | Emotional or tense beats |

Prompt template:

```
Minimalist hand-drawn doodle illustration, 16:9, flat {BACKGROUND} background.
Crude stick-figure style: circle heads, single-line limbs, thick uniform black
outlines, flat colour fills, no gradients, no shading. {SCENE DESCRIPTION}.
Hand-lettered all-caps label reading "{LABEL}". Lots of empty space, simple and
childlike, whiteboard-explainer aesthetic.
```

### Visual grammar

The reference reuses a small set of diagram types. Pick whichever matches the
sentence — this is what makes the visuals feel authored rather than decorative.

| Narration does this | Draw this |
|---|---|
| States a distance or size | Double-headed arrow + labelled measurement |
| Compares two things | Side-by-side silhouettes, scaled, both labelled |
| States a count or a zero | One giant numeral + tiny icon + caption |
| Lists options / preferences | Hand-drawn checklist with ticks and crosses |
| Describes a thought or fear | Thought bubble above a stick figure |
| Names a mechanism | Labelled boxes joined by arrows |
| Negates a cause | The thing with a large red X struck through it |
| Describes lineage or inheritance | Family-tree of stick figures joined by lines |
| Describes a technique or process | Stacked labelled panels with a brace |

### Consistency

Reuse the same drawing of a recurring subject across all beats. Feed the first
accepted illustration back as a `referenceImages` entry so the style holds over
150 images — otherwise the line weight and character design drift visibly across
a 10-minute runtime.

With the Arcads MCP, `referenceImages` takes S3 paths, not https URLs, and a
presigned `external-api-temp-uploads/...` path is **single-use**. Upload the
style reference once, call `arcads_register_image` on it, and reuse the returned
`videoassets/<id>.png` path on every subsequent call — that one is stable.

### Lettering fails sometimes

Hand-lettered labels are the least reliable part of these prompts. Expect
roughly one in fifteen images to come back with smudged or illegible text.
Review every illustration before assembly and regenerate the failures; a plain
white background and an explicit "crisp, black, clearly legible" instruction
recovers most of them. Since there are no captions, an unreadable label means
that beat conveys nothing on screen.

Generate at 16:9 and let `build_video.py` centre-crop to the 720x420 band, so
keep the subject away from the extreme left and right edges.
