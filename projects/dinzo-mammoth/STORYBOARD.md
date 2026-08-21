# STORYBOARD — The Mammoth Hunt (stick-figure hunter vs mammoth)

> Part-by-part production. Part 1 = beats 1-10 (the whole hunt, 10 assets).
> Style: static painted backgrounds + code-rigged stick-figure hunter
> (real skeletal run cycle, not PNG warps) + mammoth PNGs (keyed) with
> rotate-to-fall. 60fps. No background motion. Hard cuts. Title bar.

## Beats

| # | Time | Shot | Action | FX / SFX | Voice line |
|---|------|------|--------|----------|------------|
| 1 | 0-6 | Wide savanna. Mammoth grazing R, rock L. | Mammoth idle bob. Empty. | birds? none | "A mammoth grazes on the savanna. It has no idea it is being watched." |
| 2 | 6-11 | Same wide. | Hunter PEEKS from behind rock (head + spear tip). | none | "Behind the rock, a hunter grips his spear. He has not eaten in two days." |
| 3 | 11-17 | Same wide. | Hunter RUNS across frame L→R (full run cycle, lean, bob). | footstep ticks | "He breaks into a run. The grass barely moves under his feet." |
| 4 | 17-22 | Medium: hunter R-of-center, mammoth further R. | Hunter stops, WIND-UP: arm pulls back with spear (anticipation). | none | "He stops. He pulls his arm back. The whole hunt comes down to this." |
| 5 | 22-27 | Medium. | THROW: arm whips forward, spear RELEASES and arcs through air (rotation follows velocity). | whoosh at release | "He throws. The spear leaves his hand like a bird." |
| 6 | 27-33 | Medium. | Spear flies, IMPACT on mammoth's side: BLOOD splash blooms, spear sticks. | thud + blood | "It hits the mammoth's side. Blood blooms against the fur." |
| 7 | 33-38 | Medium. | Mammoth REARS/hurt pose + shakes (stagger). Hunter holds follow-through. | growl shake | "The mammoth roars. It staggers. It does not fall." |
| 8 | 38-44 | Wide. | Mammoth FALLS: rotates down to the ground (ease-in), DUST puff, thud. | big thud + dust | "Then gravity remembers. The giant tips and crashes into the dust." |
| 9 | 44-49 | Wide. | Mammoth DOWN on ground. Hunter walks closer, spear raised. | footsteps | "The hunter walks closer. His hands are shaking. His dinner is huge." |
| 10 | 49-56 | Dusk. | Silhouette: mammoth down + hunter standing. Slow fade out. | wind | "One spear. One throw. One giant. That is how you survive the ice age." |

## Chapters
THE HUNT (1-3) · THE THROW (4-7) · THE FALL (8-10)

## Rig plan (code, not PNG warps)
- Hunter = skeletal stick rig drawn per-frame: hip/knee/ankle joints,
  run cycle (contact→down→pass→up, 3 Hz, leg swing ±40°, knee bend),
  lean 12°, arm counter-swing, body bob. Spear attached to right hand.
- Spear = projectile with gravity, rotation = velocity angle.
- Mammoth = keyed PNG; idle bob / hurt shake / fall rotate (pivot feet,
  ease-in) / down pose. Blood + dust = keyed PNG FX with scale-pop.
