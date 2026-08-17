---
name: youtube-seo
description: >
  Advanced YouTube SEO analysis and optimization for channels and videos.
  Routes to specialized sub-skills for audits, single-video deep dives,
  metadata optimization, channel branding, keyword research, thumbnails, and
  competitor intel. Models YouTube's modern recommender (session watch time
  / Reinforce / persona matching) not just keyword match. Use when user says
  "YouTube SEO", "optimize my video", "rank my YouTube video", "YouTube
  channel audit", "YouTube keywords", or provides a YouTube URL.
user-invokable: true
argument-hint: "[channel-url | video-url | query]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Agent
---

# YouTube SEO Orchestrator (Advanced)

Master skill for YouTube SEO work. Detect intent, delegate to the right
sub-skill, and provide the shared advanced ranking model that every
sub-skill references. If intent is ambiguous, ask once before proceeding.

## Routing Table

| User intent / input | Sub-skill |
|---------------------|-----------|
| "audit my channel", channel URL alone, "full YouTube check" | `youtube-seo-audit` |
| Single video URL, "analyze this video", "why isn't this ranking" | `youtube-seo-video` |
| "optimize title/description/tags", "rewrite metadata", "improve CTR copy" | `youtube-seo-optimize` |
| "channel branding", "about page", "banner", "playlists", "channel trailer" | `youtube-seo-channel` |
| "YouTube keywords", "topic research", "what should I make a video about" | `youtube-seo-keywords` |
| "thumbnail review", "CTR thumbnail", "is my thumbnail good" | `youtube-seo-thumbnail` |
| "competitor analysis", "what are [channel] doing", "competing videos" | `youtube-seo-competitor` |

## Advanced Ranking Model

YouTube's recommender is NOT a keyword-match system. It is a multi-surface
reinforcement-learning recommender that optimizes for **long-term user
satisfaction** (the "Reinforce" paper, Covington et al. 2016 + DRL updates).
Each surface has its own objective:

| Surface | Primary objective | Dominant signal |
|---------|-------------------|-----------------|
| **Browse** (Home feed) | Session watch time + return rate | CTR-on-impression, persona match, freshness |
| **Suggested** (sidebar / autoplay) | Next-video watch time | Topical adjacency, session continuation, co-view graph |
| **Search** | Query satisfaction | Keyword/entity match, APV for that query, click depth |
| **Shorts feed** | Swipe-through rate + watch loops | Hook in <1s, loopability, audio trend |
| **Notifications** | Open rate in first hour | Subscriber affinity, bell-on CTR history |
| **External** | Retention of new viewers | Intro strength, subscribe-from-external rate |

A video can be strong on one surface and dead on others. Always ask which
surface matters most for the user's goal before optimizing.

### Tier 1 — Watch-time & session signals (dominant)

- **CTR by surface** (Browse CTR ≠ Search CTR ≠ Suggested CTR)
- **APV** (Average Percentage Viewed) — the single best retention metric for
  videos <20 min. Benchmarks:
  - Excellent: ≥55% APV
  - Good: 45-55%
  - Needs work: 35-45%
  - Bad: <35% (algorithm suppresses distribution)
- **AVD** (Average View Duration) — use for videos >20 min, target >8 min
  for mid-roll ad revenue floor
- **Intro retention at 0:30** — target ≥70% of viewers still watching
- **Retention cliff detection** — any point where retention drops >10% in
  <5 seconds is a structural problem
- **Session watch time contribution** — does this video lead to another view
  on YouTube? Studio "Suggested videos" + "Browse" outbound CTR proxy this
- **Returning viewer rate** — % of viewers who come back within 7/28 days
- **Relative performance** — vs your own channel median and vs niche median
  for the same length bucket

### Tier 2 — Metadata & semantic signals

- **Title**: 60-70 char sweet spot (mobile cutoff ~56 on small screens, ~70
  on desktop). Keyword in first 40 chars for Search; emotional driver first
  for Browse.
- **Description**:
  - **Above-fold (first 150 chars)**: restates title intent, includes
    primary keyword, gives a click-for-more reason
  - **Full body (1,500-4,000 chars)**: semantic entity coverage (see below),
    natural density, not stuffed
  - **Key Moments / chapters**: first timestamp MUST be `0:00`, ≥3 chapters,
    each ≥10s, descriptive labels. Triggers Google Search "Key Moments"
    rich result and `VideoObject.hasPart[].Clip` schema eligibility.
  - **Links block**: grouped, labeled, with FTC disclosure if affiliate
  - **Hashtags**: max 3 meaningful (shown above title); first is strongest
- **Tags**: de-emphasized in 2020 but still used for typo/spelling
  disambiguation and topic classification. 5-15, first = exact keyword,
  total <500 chars.
- **Entity/semantic coverage**: YouTube uses Knowledge Graph entities
  (people, brands, places, concepts). Mention 5-10 related entities in the
  description/captions to strengthen topic classification. Example: for a
  "Ryzen 9 review", include Intel, TDP, chiplet, AM5, Zen architecture.
- **Captions**: manually uploaded `.srt`/`.vtt` outrank auto-captions for
  Search. Translated captions unlock international impressions.
- **Translated metadata**: Custom Channel Translations for top 5 viewer
  languages typically lift international impressions 20-50%.
- **Category**: correct primary category
- **Audio language tag + default language** set correctly

### Tier 3 — Thumbnail / pre-click signals

- **1280x720**, <2MB, JPG/PNG, 16:9
- **Readable at 120px wide** (mobile feed) — the binding constraint
- **Face + strong emotion** lifts CTR ~20-30% in most niches (exceptions:
  product, gaming, tutorial close-ups)
- **≤4 words text**, ideally ≤3, bold sans-serif ≥80pt effective
- **SERP differentiation**: must pattern-break against the top-10 thumbnails
  for the target keyword (CLIP-embedding or manual grid check)
- **Native A/B test** via Studio "Test & Compare" (3 variants, 2-week window)
- **No bait-mismatch** with title or content — long-term CTR decay if broken

### Tier 4 — Engagement & velocity signals

- **Like ratio** vs channel baseline (not absolute count)
- **Comment velocity** in first 60 min, creator reply rate
- **Pinned comment engagement** (replies to pinned)
- **Shares, saves-to-playlist, playlist-add events**
- **End-screen CTR** (slots filled; hotspot 60-70% through video)
- **Card CTR** at attention moments
- **Subscribe-from-video rate** (per 1,000 views)
- **Bell-notification open rate** (for subscribed audience)
- **First-24h velocity** — for trending/topical content this is 60-80% of
  lifetime distribution; for evergreen, 10-20%

### Tier 5 — Channel-level signals

- **Topical authority**: concentration of topic clusters (YouTube classifies
  channels by topic IDs inherited from Knowledge Graph)
- **Upload cadence consistency**: predictable rhythm feeds the Browse
  surface
- **Channel persona profile**: who the algorithm believes watches you
- **Playlist binge-ability** (session chains)
- **Cross-video retention** (do viewers of video A also finish video B?)
- **Subscriber growth slope** (more signal than raw count)
- **Community tab engagement** (pre-upload momentum)
- **Verification + monetization status**
- **Strike / community-guidelines standing**

### Tier 6 — Technical / safety signals

- **Video format**: 1080p minimum (4K bonus on supporting devices)
- **Audio loudness**: target -14 LUFS (YouTube's normalization target).
  Under -16 LUFS feels quiet and correlates with lower retention.
- **Duration**: >8 min unlocks mid-roll ads; >10 min is the legacy watch-time
  optimum; <60s (vertical) goes to Shorts feed
- **Made-for-Kids flag**: must match content truthfully; incorrect setting
  disables engagement features and suppresses discovery
- **Altered/synthetic content disclosure** for AI-generated video/voice
- **Copyright claims** (Content ID): block/monetize/track status affects
  revenue share and can cap reach
- **Embedding enabled** (third-party embed views count)
- **Comments enabled** with active moderation

### Shorts-specific signals

- **First 0.5-1.0s hook** — swipe-away rate here is the #1 metric
- **Loop rate** — the video should end where it starts (narratively or
  visually)
- **Vertical 9:16**, 1080x1920
- **Caption overlay** for silent viewing (most Shorts are watched muted)
- **Audio trend** — use trending audio from the Shorts audio library
  (boost) OR original audio that can be remixed
- **Title**: ≤40 chars, emotional hook front-loaded
- **`#Shorts`** in description or title (no longer required but still
  de-risks classification)
- **Length**: 15-30s has highest loop rate; 45-60s has highest watch time.
  Pick based on goal (discovery vs watch time)

## Data Sources

**First-party only.** These skills deliberately avoid third-party
analytics tools (VidIQ, TubeBuddy, Ahrefs, SocialBlade, NoxInfluencer,
HypeAuditor, etc.) — they rate-limit, change their HTML, or return
errors. Every source below is an official Google/YouTube endpoint, a
local CLI, or data the user provides directly.

Priority order (degrade gracefully from top to bottom):

| Source | Use | How |
|--------|-----|-----|
| **YouTube Data API v3** | Full snippet, tags, statistics, topicDetails, contentDetails, playerCaptions, commentThreads, search, channels, playlistItems | `YOUTUBE_API_KEY` env var + `scripts/fetch_video.py` / `scripts/fetch_channel.py` |
| **YouTube Studio CSV exports** (user-provided) | Real CTR, APV, retention curves, traffic sources, audience, impressions — the only source for Tier 1 signals | Ask user to export from Studio → Analytics → Advanced Mode → download CSV |
| **yt-dlp** | Full metadata, auto + manual captions, chapters, transcript, audio extract, `ytsearch:` SERP, channel playlists — works without an API key | `yt-dlp --dump-json --skip-download URL`, `yt-dlp "ytsearch50:query" --flat-playlist -J` |
| **YouTube suggest API** | Keyword expansion (no key, no rate limit in practice) | `suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={seed}` |
| **Google Trends** (WebFetch) | Trending vs evergreen, seasonality, breakout topics | `trends.google.com/trends/api/explore...` |
| **WebFetch on watch / channel / results page** | Public title, view/like counts, upload date, visible description, SERP results — last resort, structure can change | `youtube.com/results?search_query=...`, `youtube.com/@handle` |
| **Whisper** (local or API) | Transcript fallback when captions unavailable | `whisper --model base --language en` |
| **OpenCV + CLIP** | Face detection, emotion, thumbnail-similarity vs SERP | `scripts/analyze_thumbnail.py` |
| **FFmpeg / loudnorm** | Audio loudness (LUFS), true peak, loudness range | `ffmpeg -i IN -af loudnorm=print_format=json -f null -` |
| **seo-dataforseo MCP** *(OPTIONAL — only if explicitly available and not erroring)* | Extra YouTube SERP positions and volume estimates | `serp_youtube_organic_live_advanced`, `keywords_for_youtube` — skip on any error, do not retry |

### Data Source Matrix (what you need for what)

| Analysis | Minimum data | Ideal data |
|----------|-------------|-----------|
| Metadata score | WebFetch only | API + Studio CSV |
| Retention diagnosis | Studio CSV | Studio CSV + transcript |
| Thumbnail score | Image URL | Image + SERP grid + CLIP embeddings |
| Competitor intel | API + WebFetch | API + yt-dlp transcripts + Studio benchmarks |
| Audio/loudness | yt-dlp audio extract | FFmpeg loudnorm pass |

If critical data is missing, ASK for it before analyzing — do not guess
Tier 1 signals.

## Niche Benchmarks (APV, CTR, like ratio)

Benchmarks vary. When possible, compute live from top-10 SERP for the
target keyword. Use these as fallback medians:

| Niche | CTR (Browse) | APV (long-form) | Like/view ratio |
|-------|-------------|-----------------|-----------------|
| Tech review | 4-8% | 40-50% | 3-5% |
| Gaming | 5-10% | 45-55% | 4-6% |
| Education / how-to | 4-7% | 40-50% | 4-6% |
| Vlog / lifestyle | 3-6% | 35-45% | 3-5% |
| Finance / business | 5-9% | 45-55% | 3-5% |
| Music / entertainment | 6-12% | 50-65% | 5-8% |
| Kids (MFK compliant) | 8-15% | 55-70% | N/A (disabled) |
| Shorts (any) | 8-20% | 80-100%+ (loops) | 5-10% |

If the user's numbers are 1.5x median, recommend scaling (more similar
content); if <0.7x median, recommend structural change.

## Output Conventions (all sub-skills must follow)

1. **Score card** (0-100) with weighted sub-scores
2. **Issues** organized Critical → High → Medium → Low, each with an
   estimated impact (CTR%, APV%, impressions%)
3. **Paste-ready artifacts** (titles, descriptions, tags, schema) in fenced
   code blocks
4. **Rationale block** citing which Tier signal each fix targets
5. **Measurement plan**: which Studio metric to watch after the change,
   over what window, with what success threshold

## Error Handling

Fail loud, degrade gracefully, never fabricate. If a third-party tool
(DataForSEO MCP, any scraper, or an optional service) errors, **skip
it and continue with native sources** — do not retry, do not block
the run.

| Scenario | Action |
|----------|--------|
| Video private/unlisted | Ask user to make unlisted-shareable or paste raw metadata + Studio CSV |
| No API key AND WebFetch blocked | Fall back to yt-dlp (`--dump-json`, `ytsearch:`); if still failing, ask user for a metadata paste — never fabricate tags/views |
| DataForSEO MCP or any optional tool errors | Log it, skip that source, continue with YouTube Data API + yt-dlp |
| yt-dlp fails on a single video | Retry once with `--extractor-args "youtube:player_client=web"`; on second failure, skip that video and note it |
| API quota exhausted | Switch to yt-dlp + suggest API; report which checks are degraded |
| Age-restricted / region-blocked | Note limitation; analyze what is accessible |
| Channel <10 videos | Focus on channel setup, keyword research, and format selection — not ranking diagnosis |
| Studio CSV not provided but user asks for retention diagnosis | Explicitly refuse to guess; ask for the export |
| MFK channel | Skip engagement/comment analysis (disabled); focus on thumbnail, title, playlist binge |
| User asks for SocialBlade/VidIQ/TubeBuddy/Ahrefs data | Explain these are not used (rate-limit / error-prone); offer the native equivalent (API + yt-dlp) instead |
