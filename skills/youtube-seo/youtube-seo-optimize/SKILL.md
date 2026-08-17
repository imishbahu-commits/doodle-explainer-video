---
name: youtube-seo-optimize
description: >
  Advanced YouTube metadata optimizer. Generates Browse-primary and
  Search-primary title variants, entity-rich descriptions, tags, chapters
  with Key Moments schema, 15-second hook script, translated metadata for
  top markets, pinned comment, and end-screen plan. Use when user says
  "optimize my video", "rewrite my title", "write YouTube description",
  "generate tags", or provides raw video info asking for metadata.
user-invokable: true
argument-hint: "[video-url | topic]"
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
---

# YouTube Metadata Optimizer (Advanced)

Produce paste-ready metadata that optimizes for **the specific surface**
the user cares about, not a generic keyword-stuffing pass. Browse and
Search require different strategies; generate both when the goal is
mixed discovery.

## Required Inputs (ask in one batch if missing)

1. Video URL **or** raw topic + video outline/script
2. **Target surface**: Browse (Home feed) / Search / Suggested / Shorts /
   mixed — this changes the title and thumbnail strategy
3. **Primary target keyword** (or ask for suggestions via
   `youtube-seo-keywords`)
4. **Secondary keywords** (2-4) for semantic coverage
5. **Target audience** (beginner / intermediate / expert) and viewer
   persona if known
6. **Channel niche + brand voice** (serious / playful / contrarian /
   warm)
7. **Is this long-form or Shorts?** (and length if long-form)
8. **Top 3 audience countries/languages** (for translated metadata)
9. **Competing videos**: 3 URLs or keyword for SERP grid fetch

## Optimization Strategy by Surface

| Surface | Title pattern | Thumbnail rule | Description priority |
|---------|--------------|----------------|---------------------|
| Browse | Emotional hook first, keyword second | Face + emotion + ≤3 words text | Above-fold selling the click |
| Search | Keyword first, hook second | Clarity over drama | Full keyword + entity coverage |
| Suggested | Adjacency to parent video | Same grid style as parent | Cross-link to parent video |
| Shorts | ≤40 chars, visceral hook | Vertical crop, muted-readable text | Minimal — first 2 lines only |
| Mixed | Browse title + Search-heavy description | Browse-style thumbnail | Full entity coverage |

## Outputs (deliver all nine blocks)

### 1. Titles — 5 variants tagged by surface

Deliver as a table with length, surface tag, hook type, and primary
keyword position:

| # | Title | Chars | Surface | Hook | KW Pos |
|---|-------|-------|---------|------|--------|
| A | ... | 64 | Browse | Curiosity | char 42 |
| B | ... | 68 | Search | Authority | char 1 |
| C | ... | 59 | Browse | Number | char 3 |
| D | ... | 71 | Mixed | Contrarian | char 8 |
| E | ... | 66 | Search | Benefit | char 5 |

Rules:
- All ≤70 chars (mobile cutoff) unless intentional overflow justified
- Primary keyword present in all
- No bait-mismatch with the actual video content
- Include an emotional driver tag: `[curiosity|urgency|benefit|fear|
  authority|contrarian|novelty]`
- At least 2 Browse-primary and 2 Search-primary variants

### 2. Description (full, paste-ready)

Template:
```
{HOOK LINE — 100-150 chars, primary keyword in first 60 chars, restates
title intent, gives a click-for-more reason. This is the above-the-fold.}

{BODY — 3-5 paragraphs, 1,500-3,500 chars total. Explains what the
viewer will learn, why it matters, who it is for, what they will be able
to do after watching. Mentions all secondary keywords and 8-15 Knowledge
Graph entities from the topic cluster (people, brands, concepts, places,
products). Natural density. Uses short paragraphs for scan-reading.}

⏱️ CHAPTERS
0:00 {descriptive keyword-rich label}
0:XX {label 2}
X:XX {label 3}
...

🔗 LINKS MENTIONED
- {link 1 — labeled}
- {link 2 — labeled}

📚 RESOURCES
- {resource 1}
- {resource 2}

📺 RELATED VIDEOS
- {related video 1}
- {related video 2}

👋 ABOUT {channel name}
{1-2 sentence channel pitch} → Subscribe: {channel URL}

📩 BUSINESS INQUIRIES
{email}

{FTC disclosure if affiliate/sponsored}

#primaryKeyword #secondaryTopic #niche
```

Rules:
- First line contains primary keyword
- 1,500-3,500 chars total
- All secondary keywords covered naturally
- **Entity coverage list** printed as a checklist before the description
  so the user sees which entities were included
- Exactly 3 bottom hashtags (first = strongest, will show above title)
- Key Moments / chapter format: `M:SS label` or `MM:SS label` (Google
  Search rich result compatible)

### 3. Tags (comma-separated, paste-ready)

```
primary keyword, secondary 1, secondary 2, long-tail 1, long-tail 2,
entity 1, entity 2, broad niche, channel brand
```

Rules:
- Tag 1 = exact primary keyword
- 5-15 tags
- <500 chars total
- Mix: 1-3 broad + 5-8 specific + 2-3 entity-based + 1-2 brand
- Tags reference the same entities present in the description

### 4. Chapters (paste-ready, ≥3, first = `0:00`)

Each chapter label is keyword-rich but natural, ≥10s apart, matches the
actual video structure. Return as a plain block the user pastes into the
description.

### 5. 15-Second Hook Script

The most under-optimized part of most videos. Write a ready-to-shoot
opening that solves the 0:30 retention problem:

```
[0-2s]   VISUAL HOOK: {what is on screen}
         AUDIO HOOK:  "{first sentence, ≤12 words, payoff preview or
                       pattern-interrupt}"

[2-6s]   "{stake / why this matters — make the viewer feel the cost
          of not knowing}"

[6-10s]  "{credibility flash — 1 sentence, what gives you authority
          here}"

[10-15s] "{explicit promise — what the viewer will have by the end}"
         → CUT TO: first content beat
```

Rules:
- No "Hey guys welcome back to the channel"
- No long logo animation
- No subscribe request before value delivery
- Promise must match the title and thumbnail exactly

### 6. Pinned Comment (paste-ready)

A 1-2 sentence comment that drives replies (open question preferred).
At most 1 link. Used as a soft ranking signal via reply velocity.

Example pattern: `{specific question that viewers will have an opinion on}
{optional link to lead magnet or next video}`

### 7. End-Screen Plan

- **Slot 1** (best related video): `{title suggestion}` — why it
  continues the session
- **Slot 2** (playlist): `{playlist name}` — the binge path
- **Slot 3** (subscribe)
- **Slot 4** (channel)
- **Card placements**: at retention peaks (from curve if provided) or
  at 25%, 55%, 75% marks as fallback

### 8. Translated Metadata (top 3 audience languages)

For each target language, produce:
- Translated title (same surface strategy)
- Translated description (hook line + full body) — NOT machine-
  translated, culturally adapted
- Translated caption file recommendation

YouTube's Custom Channel Translations apply this automatically to
viewers with matching language preferences and typically lift
international impressions 20-50%.

### 9. Schema Markup (JSON-LD for the embed page)

Produce a `VideoObject` JSON-LD block with `hasPart[].Clip` entries and
a `SeekToAction` target so the video is eligible for Google Search
"Key Moments" rich result when embedded on the creator's website:

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "{title}",
  "description": "{above-fold description}",
  "thumbnailUrl": "{thumbnail URL}",
  "uploadDate": "YYYY-MM-DDTHH:MM:SSZ",
  "duration": "PT{H}H{M}M{S}S",
  "contentUrl": "{watch URL}",
  "embedUrl": "{embed URL}",
  "publisher": {
    "@type": "Organization",
    "name": "{channel name}",
    "logo": { "@type": "ImageObject", "url": "{logo URL}" }
  },
  "hasPart": [
    {
      "@type": "Clip",
      "name": "{chapter 1 label}",
      "startOffset": 0,
      "endOffset": 60,
      "url": "{watch URL}&t=0s"
    }
    /* ... one per chapter */
  ],
  "potentialAction": {
    "@type": "SeekToAction",
    "target": "{watch URL}&t={seek_to_second_number}",
    "startOffset-input": "required name=seek_to_second_number"
  }
}
```

## Rationale Block (always include)

After the nine blocks, include a **"Why these choices"** section (≤250
words) citing which Tier signals from `youtube-seo` each artifact
targets (e.g., "Title A targets Browse CTR by leading with curiosity;
Title B targets Search APV by leading with exact keyword and intent
match."). Do not restate the full ranking model.

## Keyword Discovery Fallback

If no primary keyword is given:
1. Ask for the topic
2. Run `youtube-seo-keywords` on the topic
3. Present 5 candidate keywords ranked by opportunity score
4. Wait for user selection before generating metadata

## Shorts Template (when <60s vertical)

Replace blocks 1-5 with the Shorts template:

- **Title**: ≤40 chars, visceral hook, optional `#Shorts`
- **Description**: ≤500 chars, first 2 lines only matter. Include primary
  keyword and 1-2 hashtags max.
- **Chapters**: skip (Shorts don't use chapters)
- **Hook script**: 0-1s visual + audio pattern-interrupt, loop ending
- **CTA**: pinned comment to long-form video
- **Audio note**: trending-library audio vs original remixable — pick
  based on goal (discovery vs brand)

## Error Handling

| Scenario | Action |
|----------|--------|
| No topic or URL provided | Ask the required-inputs batch above |
| Non-English video | Produce all blocks in the video's native language, plus English translation as a secondary block |
| Multi-language target | Generate the translated metadata block (output #8) for all target languages |
| Sponsored / affiliate | Include FTC disclosure automatically; flag if user does not request it |
| Made-for-Kids content | Skip pinned comment block (comments disabled); emphasize thumbnail + title |
