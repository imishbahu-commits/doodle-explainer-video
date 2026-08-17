---
name: youtube-seo-channel
description: >
  Advanced channel-level YouTube SEO: identity, about, channel keywords,
  topical authority, playlist session chains, bingeable series structure,
  channel trailer, community tab strategy, translated metadata, and
  premiere/upload cadence planning. Use when user says "channel branding",
  "YouTube about page", "playlists", "channel trailer", or "optimize my
  channel".
user-invokable: true
argument-hint: "[channel-url]"
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
---

# Channel Setup, Authority & Session Strategy (Advanced)

Channels don't rank — topics and videos rank. But channels accumulate
**topical authority** (the algorithm's classification of what the
channel is known for), **session contribution** (how much watch time
the channel drives to YouTube overall), and **Browse feed friendliness**
(cadence + freshness). All three are set at the channel level.

## What to Analyze

### 1. Identity

- **Handle** (`@name`): ≤30 chars, memorable, brand-aligned, no
  underscores/numbers if avoidable
- **Channel name**: ≤30 chars
- **Profile picture**: 800x800, readable at 48px (subscriber feed size)
- **Banner**: 2560x1440, safe area 1546x423. Must communicate:
  - Value proposition in one line
  - Upload schedule
  - Social proof (subs, press, awards) if relevant
  - Brand colors + logo
- **Watermark subscribe badge**: present, positioned last 25% of video
- **Channel trailer** set for non-subscribers (60-90s, keyword-rich
  description, strong hook)
- **Featured video** set for subscribers (latest hero)

### 2. About Page

- **Description**: 1,000-5,000 chars. Structure:
  - **Elevator pitch** (first 150 chars — appears in channel search
    results)
  - **Who the channel is for**
  - **What viewers will learn / experience**
  - **Upload schedule**
  - **Primary + 3-5 secondary keywords naturally placed**
  - **5-10 Knowledge Graph entities** from the topic cluster for
    classification
  - **Subscribe CTA**
- **Channel keywords** (Studio → Settings → Channel → Basic info): 10
  keywords max, most important first, total <500 chars, must overlap
  with the entities from the description
- **Links**: 3-5 labeled links (website, social, merch, mailing list,
  Discord)
- **Country**: set correctly (regional Browse ranking signal)
- **Business email**: present
- **Contact / inquiries link**

### 3. Topical Authority (most important advanced check)

Cluster the channel's last 25 videos by topic (via title + description
+ tag + caption entities). Compute:

- **Concentration score** (0-100): how focused the channel is on its
  dominant cluster. Entropy-based.
- **Drift**: compare the topic mix of the first 10 videos with the most
  recent 10. Drifting channels lose Browse promotion because the
  algorithm has to re-classify.
- **Topic IDs**: from API `channels.list?part=topicDetails` — report
  the topics YouTube assigns and whether they match the creator's
  intended niche.
- **Action**: recommend consolidation (unlist or playlist off-topic
  videos), topic focus going forward, and playlist restructuring to
  reinforce the dominant cluster.

### 4. Playlists — Session Chain Strategy

Playlists are the primary lever for session watch time (the dominant
ranking signal). Audit:

- **Count**: ≥3 if channel has 10+ videos; ≥1 per topic cluster
- **Each playlist**:
  - Keyword-rich title ≤60 chars
  - 100-500 char description with primary keyword in line 1
  - Custom thumbnail (where possible)
  - Logical ordering (binge order, not chronological)
  - ≥5 videos (thin playlists look abandoned)
- **Series playlists**: videos explicitly framed as Episode 1, 2, 3 —
  these generate the longest sessions
- **Session chain design**: video A should end-screen to video B; video
  B should be the first video of a playlist C. Map the intended session
  flow for the user.
- **Playlist as SEO asset**: playlists themselves rank in YouTube and
  Google search ("Best X of 2026" playlists often outrank videos)
- **Playlist mix on channel home**: organized sections reflecting
  strategy (not YouTube default order)

### 5. Channel Home Layout

- **Non-subscriber view**: channel trailer with persuasive description
  (keyword-rich, subscribe CTA, value prop)
- **Subscriber view**: featured video (hero), not a default autoplay
- **Sections** (customize order):
  1. Popular (social proof)
  2. Active series / playlists (binge path)
  3. Recent uploads (freshness)
  4. Shorts shelf (if the channel posts Shorts)
  5. Topic-based playlist shelves
  6. Live / upcoming (if applicable)

### 6. Community Tab

- Activity in the last 30 days: ≥4 posts minimum for an active channel
- Mix: polls (highest engagement), images, GIFs, video teasers, links
- Posts should drive to videos or tease upcoming uploads
- Pre-upload polls seed audience anticipation (Browse boost on upload day)
- Reply rate on community posts

### 7. Upload Cadence & Freshness

- Median days-between-uploads
- Stddev (consistency — lower is better for Browse friendliness)
- Format mix: long-form / Shorts / live / premiere
- Scheduling windows: which days/times does the channel upload? Compare
  to Studio → Audience → "When your viewers are on YouTube" heatmap
- Premiere usage: Premieres boost first-hour velocity via the waiting
  room chat and notification

### 8. Translated Metadata (Custom Channel Translations)

For the top 3-5 audience languages (from Studio → Audience → Top
subtitle/CC languages), recommend:
- Translated channel name (if applicable in culture)
- Translated channel description
- Translated titles and descriptions on recent videos
- Translated captions on recent videos

Typical lift: +20-50% international impressions.

### 9. Verification & Safety

- Verification eligibility (100k+ subs) or brand-account verification
- Monetization status (YPP eligible / in program / limited)
- Active strikes or community-guidelines warnings
- Copyright claim rate on top videos

### 10. Channel Trailer Script

The trailer is a free ad for the channel to non-subscribers. It must:
- **0-5s**: pattern interrupt visual + "If you're the kind of person
  who [desire/pain], this channel is for you"
- **5-20s**: 3 specific promises of what viewers will get
- **20-45s**: social proof (subs, press, case study)
- **45-60s**: upload schedule + explicit subscribe CTA
- **60-90s**: end with the most-rewatched moment from the channel's
  best-performing video

## Output

### Channel Score Card

```
Overall: XX/100

Identity:            XX/100
About Page:          XX/100
Topical Authority:   XX/100   ← most important
Playlists / Chains:  XX/100
Channel Home Layout: XX/100
Community Tab:       XX/100
Cadence / Freshness: XX/100
Translations:        XX/100
Safety / Verification: XX/100
```

### Topical Authority Map

Visualize the channel's topic clusters as a list with concentration %:

```
Cluster 1 — Topic A (42%)  ████████████░░░░░  [dominant]
Cluster 2 — Topic B (28%)  ████████░░░░░░░░░
Cluster 3 — Topic C (18%)  █████░░░░░░░░░░░░
Off-cluster (12%)          ███░░░░░░░░░░░░░░  [drift]
```

Concentration score and drift trend.

### Paste-Ready Rewrites

- New channel description (full, with entity coverage)
- 10 channel keywords, comma-separated
- 3 playlist title + description rewrites
- Channel trailer script (90s, shot-by-shot)
- Community post ideas (5, one per type)
- Translated metadata for the top 3 audience languages

### Session Chain Map

For the user's top 5 videos, propose:
```
Video A → end-screen → Video B → playlist C (5 videos) → autoplay D
```
Shows how session time compounds across the channel.

### Missing Assets List

Checklist of missing banner dimensions, watermark, links, featured
video, trailer, custom channel URL, sections, community posts, etc.

## Error Handling

| Scenario | Action |
|----------|--------|
| Channel keywords not visible publicly | Ask user to paste from Studio → Settings → Channel → Basic info |
| Channel too small for custom layout | Skip layout section; focus on identity, about, playlists |
| MFK channel | Skip community tab (disabled); focus on identity and playlists |
| Multi-topic channel with no clear niche | Flag as critical — recommend splitting into separate channels or consolidating |
