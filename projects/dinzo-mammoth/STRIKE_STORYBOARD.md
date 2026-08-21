# STORYBOARD — "THE STRIKE" (tiger-hunt scene recreation, ref 15227 style)

> Recreates the STRIKE section of the mammoth/tiger hunt (throw → hit →
> blood → fall) using the measured reference style: locked camera, frozen
> background, in-place/short keyframe motion, hard cuts, voice-synced.
> NEW keyframing (better than the old build):
>   - spear projectile with REAL gravity arc + rotation follows velocity
>   - freeze-frame impact (0.15s hold) right when the spear hits
>   - blood burst with squash-and-stretch (scale 0.6->1.25->1.0)
>   - mammoth fall with anticipation (rears up first) then rotate-to-ground
>     with ease-in, dust pop on landing
>   - hunter follow-through pose held with micro-bob

## Shots (7 short beats, ~28s total, median ~4s)

| # | dur | shot | action | bg |
|---|-----|------|--------|-----|
| 1 | 4.2 | Hunter wind-up (arm back, spear) | anticipation dip (scale 0.95), hold | savanna |
| 2 | 4.5 | THROW: arm whips, spear releases | spear gravity arc, whoosh | savanna |
| 3 | 2.0 | FREEZE-FRAME impact: spear hits mammoth side | 0.15s hold, then blood | savanna |
| 4 | 4.0 | BLOOD BURST (squash-stretch pop) + mammoth hurt shake | blood scale 0.6->1.25->1.0, shake 6Hz damped | savanna |
| 5 | 4.5 | Mammoth REARS (anticipation) then tips | rear up 12deg, rotate fall ease-in | savanna |
| 6 | 4.0 | LAND: dust puff + thud, mammoth down | dust scale-pop, small shake | savanna |
| 7 | 4.5 | Hunter walks up (3-pose cycle), spear stuck | slow walk + spear held, dusk fade | dusk |

## Keyframe grammar (from MASTER_STYLE + ref)
- background NEVER moves (0% camera)
- in-place + short motions only; hard cuts; no mid-shot fades (except final)
- spear: vx -540, vy -300, g 1000; rotation = atan2(velocity)
- blood: scale pop with overshoot; dust: scale + fade; thud: 85Hz sine

## Assets (reuse existing mammoth kit — no new generations needed)
bg_savanna, bg_dusk, char_hunter_run1-3, char_hunter_windup, char_hunter_follow,
char_mammoth_s (small), char_mammoth_hurt_s, char_mammoth_fall_s,
char_mammoth_down_s, fx_blood2, fx_dust, prop_spear
