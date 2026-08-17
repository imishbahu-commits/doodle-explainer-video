---
name: youtube-seo-audit
description: >
  Advanced full YouTube channel audit with parallel sub-skill delegation.
  Analyzes topical authority, channel-level retention patterns, traffic-
  source mix, upload velocity consistency, playlist session chains, and
  sub-skill breakdowns. Generates health score and prioritized action
  plan. Use when user says "YouTube audit", "audit my channel", "full
  YouTube check", or provides a channel URL.
user-invokable: true
argument-hint: "[channel-url]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Agent
---

# Full YouTube Channel Audit (Advanced)

## Process

1. **Resolve channel**: accept `@handle`, `/channel/UC...`, `/c/name`, or
   a video URL. Normalize to channel ID via API or WebFetch.
2. **Ask for Studio exports** before starting any retention or CTR analysis:
   - Analytics → Advanced Mode → Last 28/90 days CSV for:
     - Content (video-level stats)
     - Traffic source
     - Audience → geography + top subtitles
     - Key moments (retention curves for top 10 videos)
   Without these, score only metadata and structure; label retention
   metrics as "unknown".
3. **Fetch channel surface**: `/about`, `/videos`, `/shorts`, `/playlists`,
   `/community`, `/featured`. Extract:
   - Channel name, handle, description, country, links, join date
   - Banner and profile image presence
   - Total videos, views, subs (if public)
   - Topic categories (from API `channels.list?part=topicDetails`)
   - Upload cadence from last 25 long-form + last 25 Shorts
4. **Sample videos**: pull the last 25 uploads and the top 25 all-time
   by views. For each: title, description, visible tags, view count, like
   count, comment count, duration, upload date, thumbnail URL, chapters.
5. **Delegate** (parallel via Agent tool when available):
   - `youtube-seo-channel` — identity, about, playlists, trailer, session chains
   - `youtube-seo-video` — run on top 3 + bottom 3 performers (contrast analysis)
   - `youtube-seo-thumbnail` — review last 12 thumbnails as a grid + SERP differentiation
   - `youtube-seo-keywords` — topical authority score + gap analysis
   - `youtube-seo-competitor` — detect 3-5 direct competitors + pattern extraction
6. **Compute topical authority**: cluster the channel's videos by topic
   and measure concentration (entropy). High concentration = high authority
   on that cluster. Diffuse = weak algorithmic classification.
7. **Compute velocity consistency**: stddev of days-between-uploads. Low
   stddev + regular cadence = Browse feed promotion friendly.
8. **Compute session chain strength**: % of videos that appear in at least
   one playlist; % of playlists with ≥5 videos; avg playlist view count.
9. **Score**: aggregate into YouTube Health Score (0-100)
10. **Report**: write `YT-AUDIT-REPORT.md` + `YT-ACTION-PLAN.md` to the
    current directory.

## Scoring Weights

| Category | Weight | Why |
|----------|--------|-----|
| Retention & Watch Time (Tier 1) | 25% | Dominant ranking signal; only scorable with Studio CSV |
| Video Metadata Quality | 18% | Title, description, tags, chapters, entities, captions |
| Thumbnails (CTR) | 15% | Second-largest lever for impressions |
| Topical Authority | 12% | Channel classification strength |
| Content Strategy (cadence, format mix, length) | 10% | Browse feed friendliness |
| Channel Setup (identity, about, playlists) | 8% | Foundational but ceiling-limited |
| Discoverability (translations, captions, hashtags) | 7% | International + accessibility multiplier |
| Engagement (likes, comments, saves) | 5% | Secondary signal, correlates with above |

If Studio CSV is missing, Retention & Watch Time drops to 0 weight and
other weights rescale proportionally — the report flags this explicitly.

## Report Structure

### Executive Summary
- Overall YouTube Health Score (0-100) with CSV-available flag
- Channel stage: Starter (0-1k) / Growing (1k-100k) / Established (100k+)
- Niche detected + topical authority concentration score
- Top 5 critical issues with estimated impact
- Top 5 quick wins with expected lift

### Retention & Watch Time (only if Studio CSV provided)
- APV distribution across sample (median, p25, p75)
- Retention-cliff inventory: which videos have cliffs, where, why
- Intro-retention (0:30) median vs niche benchmark
- Session contribution: which videos drive next views
- End-of-video drop analysis

### Traffic Source Mix (from Studio CSV)
- % Browse / Suggested / Search / External / Notifications / Shorts feed
- Which surface is over/under-indexed vs niche norm
- Strategy implication: optimize for the dominant surface, then diversify

### Video Metadata (aggregate)
- Title patterns: avg length, keyword-front usage, hook types, emotional
  intensity
- Description: above-fold usage, avg length, entity coverage, link block
  presence, chapter presence
- Tags: avg count, first-tag alignment with title
- Chapters: % of videos with ≥3 starting at 0:00
- Captions: manual vs auto, languages translated
- Key Moments schema eligibility

### Thumbnails
- Style consistency across the last 12
- Text legibility at 120px
- Face / emotion usage vs niche
- Color palette analysis (dominant colors across the grid)
- SERP differentiation sample for top 3 target keywords
- Specific thumbnails to redesign

### Topical Authority
- Topic cluster map (from video titles, tags, transcripts)
- Concentration score (0-100, higher = stronger classification)
- Cluster drift: is the channel becoming more or less focused over time?
- Recommended consolidation: playlists to build, videos to unlist or
  reclassify, topics to stop covering

### Content Strategy
- Upload cadence: median days-between, stddev, regularity score
- Format mix: long-form / Shorts / live %
- Length distribution: median, with mid-roll ad eligibility %
- Series / playlist alignment
- Premiere usage

### Channel Setup
- Delegated to `youtube-seo-channel`

### Engagement Snapshot
- Like-to-view ratio trend
- Comment velocity and creator reply rate
- Pinned-comment usage and reply rate
- Community tab activity (last 30 days)

### Discoverability
- Target keywords present in titles/descriptions
- Translated metadata for top 3 audience countries
- Caption languages available
- Hashtag strategy

### Velocity & Freshness
- First-24h view velocity distribution for last 25 videos
- Videos decaying fast vs holding evergreen
- Evergreen:topical mix recommendation

### Safety & Compliance
- Made-for-Kids flag consistency
- Altered/synthetic content disclosure usage (for AI content)
- Copyright claims on top videos
- Community guideline strikes
- Monetization status

## Priority Definitions

- **Critical**: Blocks discovery, damages CTR, or breaks algorithmic
  classification (fix this week)
- **High**: Significantly limits ranking or watch time (fix this month)
- **Medium**: Optimization opportunity (fix this quarter)
- **Low**: Nice to have (backlog)

Each recommendation includes estimated impact and the Studio metric to
watch after implementation.

## Data Sources Policy

**First-party only.** YouTube Data API v3, YouTube Studio CSV exports
(user-provided), yt-dlp, YouTube suggest API, WebFetch on youtube.com,
and the local helper scripts in `scripts/`. Do NOT pull data from
SocialBlade, VidIQ, TubeBuddy, NoxInfluencer, HypeAuditor, or similar
third parties — they rate-limit and error, which blocks the audit.

The `seo-dataforseo` MCP is OPTIONAL. If it is installed AND returns
data cleanly, it may supplement SERP position checks. On any error,
skip it silently and continue with native sources — do not retry.

## Error Handling

Core principle: degrade gracefully, score what you can, flag what
you can't, never fabricate Tier 1 numbers.

| Scenario | Action |
|----------|--------|
| Channel URL not resolvable | Try `@handle`, `/channel/UC...`, and `/c/name` forms; if all fail, ask user for the canonical URL |
| Fewer than 5 videos published | Skip metadata aggregation; focus on setup + strategy |
| API key missing or quota exhausted | Fall back to `yt-dlp --flat-playlist -J` for channel crawl; `tags` and `topicDetails` will be missing — note in report |
| WebFetch blocked on a page | Retry once with the `/channel/UC...` canonical form; if still blocked, skip that section and flag |
| Any optional tool (DataForSEO etc.) errors | Skip it, continue, do not retry — the audit must not depend on optional tools |
| yt-dlp transcript fetch fails | Retry with `--sub-lang en.*,a.en`; on second failure, skip transcript-dependent analysis for that video |
| No Studio CSV provided | Retention and CTR analysis skipped; rescale scoring weights and flag explicitly in the executive summary |
| Mixed-language channel | Segment metadata analysis per language before aggregation |
| MFK channel | Skip comment/engagement analysis (disabled); emphasize thumbnail + playlist |
| Partial sub-skill failure | Continue the audit with remaining sub-skills; list failed sections at the bottom of the report with their error codes |
