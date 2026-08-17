---
name: youtube-seo-keywords
description: >
  Advanced YouTube keyword and topic research with search-intent
  classification, Knowledge Graph entity coverage, seasonality curves,
  refined difficulty scoring, and topic-cluster planning for topical
  authority. Use when user says "YouTube keywords", "what should I make
  a video about", "keyword research", or "YouTube topic ideas".
user-invokable: true
argument-hint: "[seed-keyword | channel-url | niche]"
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
---

# YouTube Keyword & Topic Research (Advanced)

## Process

1. **Capture seed**: keyword, channel URL, or niche description. If only
   a channel URL is provided, extract 5-10 seed topics from:
   - The channel's top 25 videos by views (title + description entities)
   - The channel's topic IDs from `channels.list?part=topicDetails`
2. **Expand** the seed set to 100-300 candidate keywords from
   **first-party sources only** (third-party tools like VidIQ,
   TubeBuddy, Ahrefs, and SocialBlade rate-limit and generate errors —
   avoid them):
   - YouTube suggest API (`https://suggestqueries.google.com/complete/
     search?client=firefox&ds=yt&q={seed}`) — no key, returns JSON,
     iterate by appending `a`-`z` to the seed for long-tail expansion
   - YouTube Data API `search.list?part=snippet&q={seed}&type=video`
     — surface the top 50 ranking titles and mine their titles/tags
     for co-occurring terms
   - yt-dlp `ytsearch50:{seed}` as an API-less equivalent
   - Google autocomplete (`suggestqueries.google.com/complete/search?
     client=firefox&q={seed}`) for parent-topic discovery
   - User-provided seed list or topic outline
3. **Classify intent** for each keyword:
   - **Informational** ("what is ...", "how does ... work")
   - **Tutorial** ("how to ...", "... tutorial", "step by step")
   - **Commercial / Review** ("... review", "best ...", "... vs ...")
   - **Entertainment** (celebrity names, event names, memes)
   - **News / Topical** (breaking or time-sensitive)
   - **Navigational** (brand or channel names)
   → Each intent class maps to a different video format and surface.
4. **Classify primary surface**:
   - **Search-dominant**: "how to", "tutorial", long-tail specific queries
   - **Browse-dominant**: broad topics, personalities, trending
   - **Suggested-dominant**: sits adjacent to an existing popular video
5. **Entity mapping**: for each keyword, identify the Knowledge Graph
   entities involved (people, brands, products, concepts). Group
   keywords that share entities into **topic clusters**.
6. **Competition analysis** per keyword (top 10 SERP):
   - Median subscriber count of ranking channels
   - Median video age (weeks)
   - Median view count
   - Presence of mega channels (>1M subs) in top 3
   - Thumbnail/title quality median (estimate)
   - SERP features (Shorts shelf, mix shelf, promoted result)
7. **Seasonality**: pull Google Trends 5-year curve per keyword cluster.
   Classify:
   - **Evergreen**: flat or slowly rising
   - **Seasonal**: predictable annual peak (gift guides, tax season)
   - **Trending**: fast-rising, <6 months of data
   - **Decaying**: fast-dropping
8. **Opportunity scoring** (refined formula below)
9. **Cluster** keywords into 3-6 topic buckets with a pillar + satellites
   shape optimized for topical authority
10. **Content calendar** (optional) with pillar cadence and reactive
    slots

## Refined Opportunity Formula

```
opportunity = (0.30 * log(volume + 1)) +
              (0.25 * (100 - difficulty)) +
              (0.15 * channel_fit) +
              (0.15 * entity_overlap_with_channel) +
              (0.10 * freshness_bonus) +
              (0.05 * session_chain_bonus)
```

- `volume`: YouTube monthly searches (estimated — YouTube doesn't
  expose this directly). Use one of these native-only proxies, in
  order: (a) YouTube suggest rank depth (keywords that appear at
  position 1-3 across `a`-`z` expansions = high demand); (b) total
  result count from `search.list?q={kw}&type=video` + median views of
  the top 10 as a demand proxy; (c) Google Trends relative interest
  via WebFetch on `trends.google.com/trends/api/explore`. Never
  fabricate a volume number — label it "low/med/high" when the only
  evidence is ordinal
- `difficulty` (0-100): derived from competition analysis —
  ```
  difficulty = (0.35 * normalize(median_subs)) +
               (0.25 * normalize(median_views)) +
               (0.20 * mega_channel_top3_flag) +
               (0.10 * thumbnail_title_quality) +
               (0.10 * (1 - median_age_weeks / 104))   # newer rankings = easier
  ```
- `channel_fit` (0-100): how well the keyword aligns with the channel's
  existing topical authority
- `entity_overlap_with_channel`: % of the keyword's entities already
  covered by the channel's existing content
- `freshness_bonus`: 10 if Trending, 5 if Seasonal peak within 60 days,
  0 if Evergreen, -10 if Decaying
- `session_chain_bonus`: 5 if the keyword sits adjacent to existing
  high-performing channel content (suggested-video pathway)

Weights can be adjusted if the user explicitly wants low-competition or
high-volume bias.

## Data Sources (priority order — first-party only)

1. **YouTube suggest API** (no key, no rate limits in practice):
   `https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={seed}`
   — iterate `{seed}{a..z}` for long-tail expansion
2. **YouTube Data API v3** (`search.list`, `videos.list`,
   `channels.list`) via `YOUTUBE_API_KEY` for ranked results, titles,
   tags, topicDetails
3. **yt-dlp `ytsearch50:{query}`** as an API-less equivalent when no
   key is set or quota is exhausted
4. **Google Trends** (public WebFetch on `trends.google.com`) for
   seasonality and relative interest
5. **WebFetch on `youtube.com/results?search_query=...`** for
   competition analysis when the API is unavailable
6. **User-provided seed list or outline**

> Third-party analytics (VidIQ, TubeBuddy, Ahrefs, SocialBlade,
> NoxInfluencer) are intentionally excluded — they rate-limit or
> error. If the user volunteers a CSV from one of these, it is OK to
> read it, but never instruct the user to go acquire one.

## Output

### Keyword Sheet

| Keyword | Intent | Surface | YT Vol | Difficulty | Fit | Entity% | Trend | Opportunity |
|---------|--------|---------|--------|-----------|-----|---------|-------|-------------|
| how to ... | Tutorial | Search | 12k | 42 | 85 | 90% | Evergreen | 78 |
| ... vs ... | Commercial | Search | 4.2k | 55 | 72 | 65% | Evergreen | 64 |
| ... 2026 | News | Browse | 8k | 68 | 80 | 50% | Trending | 71 |

Sort by Opportunity descending. Limit to top 30-50.

### Topic Clusters (3-6 clusters)

For each cluster, report:
- **Theme**: one-sentence description
- **Shared entities**: 5-10 Knowledge Graph entities
- **Pillar video**: title, format, length, target keyword (highest-
  opportunity broad keyword in the cluster)
- **Satellite videos**: 5-10 specific long-tail follow-ups, each with
  title + target keyword
- **Suggested playlist**: title + description
- **Topical authority contribution**: how this cluster strengthens the
  channel's classification

### Intent Mix Chart

Report the intent distribution of the recommended keywords:
```
Tutorial:       40%  ████████
Commercial:     25%  █████
Informational:  20%  ████
Entertainment:  10%  ██
News:            5%  █
```

Flag if the mix is mismatched with the channel's current format strength.

### Gap vs Channel (when channel URL provided)

- Keywords competitors cover that the channel does not
- Entities competitors own that the channel does not reference
- Format gaps (e.g., no reviews, no tutorials, no comparisons)

### Content Calendar (optional, 8-12 weeks)

Alternates:
- **Evergreen pillar** (every 3-4 weeks): broad, high-opportunity
  keyword, long-form, binge-playlist anchor
- **Topical/reactive slot** (weekly): trending or news keyword
- **Satellite fill** (weekly): specific long-tail serving the pillar

### Seasonality Calendar

Report any Seasonal-classified keywords with their peak windows so the
user can plan 4-6 weeks ahead of each peak.

## Integration

- Hand off top keywords to `youtube-seo-optimize` for metadata generation
- Hand off cluster plan to `youtube-seo-channel` for playlist structure
- Hand off competitor-entity gaps to `youtube-seo-competitor` for deeper
  analysis

## Error Handling

| Scenario | Action |
|----------|--------|
| No API key AND WebFetch blocked | Fall back to yt-dlp `ytsearch50:` + suggest API (both key-less); if still failing, ask the user for 5-10 seed keywords directly |
| API quota exhausted mid-run | Cache partial results, switch remaining expansion to yt-dlp + suggest API, continue |
| Niche too narrow (no volume data) | Pivot to broader parent topic, report the gap, score as "low demand, qualitative only" |
| Brand/product name with no search volume | Research category terms and comparison keywords instead |
| Trending keyword with <2 weeks of data | Flag as unstable; suggest pairing with an evergreen pillar |
| Google Trends returns empty | Skip seasonality classification for that keyword — do not guess the curve |
