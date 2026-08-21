# Grok Automation Guide — measured Paint Explainer workflow

This is a handoff guide for using an external agent to prepare scripts, state
plans, art masters, and metadata. Current authority is
`references/paint-explainer-analysis-4v/style_rules.json`; read `CLAUDE.md`,
`SKILL.md`, and `skills/paint-explainer-recreation/SKILL.md` first.

## Starter prompt

```text
Read CLAUDE.md, SKILL.md, skills/paint-explainer-recreation/SKILL.md, and
references/paint-explainer-analysis-4v/style_rules.json. The JSON rules override
all generic defaults.

Create original preparation artifacts for a Paint Explainer-style video about
[TOPIC]:

1. Research and script using youtube-script. Cite claims in research.md. Target
   204–209 spoken WPM and retain final word-level timing.
2. Build beats.json as spoken timing rows plus semantic visual states. A beat
   may hold or reuse the previous state; do not force one image per beat.
3. Classify assets with image-queue: hold / doodle / asset / pose / ai. Generate
   only genuinely new ai masters and record every source/reuse decision.
4. Follow handdrawn-style-lock: one clean imperfect near-black #101010 contour,
   measured mode palette, flat character fills, and illustrated world plates
   where appropriate. Keep the top 10% clear for the persistent white title
   strip. No embedded text, photorealism, 3D rendering, cinematic lighting, or
   film grain.
5. For each justified visual change, record hard_cut / source_swap /
   local_motion and schedule it about 0.033–0.067 seconds before the keyword.
   Camera remains locked; do not prescribe generic zoom, pan, parallax,
   dissolve, idle breathing, blink, or lip-sync.
6. After approval, prepare youtube-seo metadata. Do not change production style
   or loudness for generic SEO advice.

Output research.md, script.md, beats.json, word timings, source masters, style
references, and metadata.md. Keep original artwork rather than copying reference
creator assets or branding.
```

## What an external agent can prepare

| Artifact | External preparation |
|---|---|
| research, script, state/event ledger | yes |
| new art masters | yes, if its generator supports reference images |
| deterministic diagram scene JSON/SVG | yes |
| word timings | yes, if it can align the final narration |
| YouTube metadata | yes |
| final ae-motion/HyperFrames render and repository QC | preferably this repository environment |

## Return package

Place the approved files under `projects/SLUG/`:

```text
research.md
script.md
beats.json
audio/word-timings.json
assets/source/
metadata.md
```

The repository then performs transparent asset prep, renderer selection,
scene authoring, audio assembly, and measured QC.

## Non-negotiable handoff rules

1. Spoken beat count does not determine image count.
2. Reuse stable approved subject/world masters intentionally.
3. Camera stays locked and only 1–3 local elements normally move.
4. Preserve the persistent chapter-title strip and noun-anticipated event time.
5. Current final mix target is −20.7 to −20.6 LUFS, true peak ≤−2.3 dBTP,
   LRA 1.8–3.8 LU.
6. A low ambient/electronic bed is allowed; captions require an explicit request.
7. Generation batching affects only pending `ai` masters. Keep the ledger so a
   later turn resumes without regenerating accepted assets.
