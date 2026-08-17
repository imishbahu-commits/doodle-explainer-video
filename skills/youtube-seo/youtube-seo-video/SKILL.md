---
name: youtube-seo-video
description: >
  Advanced single-video SEO analysis covering retention curve diagnosis,
  intro hook strength, APV vs niche benchmark, entity/semantic coverage,
  title/description/tags, chapters with Key Moments schema, thumbnail,
  captions, audio loudness, end-screens, and engagement signals. Use when
  user says "analyze this video", "why isn't my video ranking", or
  provides a single video URL.
user-invokable: true
argument-hint: "[video-url]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# Single Video Deep Analysis (Advanced)

Diagnose **why** a video underperforms and produce a paste-ready fix kit.
Retention and CTR are the primary levers; metadata is secondary. Always
ask for the Studio CSV export if the user wants retention diagnosis —
never guess Tier 1 numbers.

## Data Collection (in order)

1. **WebFetch** the watch URL → title, description (partial), view/like,
   duration, upload date, channel, visible chapters
2. **yt-dlp** (`scripts/fetch_video.py` or direct call) → full JSON
   metadata, tags, full description, chapters, thumbnails, captions
3. **YouTube Data API** (if key) → `videos.list?part=snippet,statistics,
   contentDetails,topicDetails,status,player,liveStreamingDetails` and
   `captions.list` + `captions.download` (if OAuth)
4. **Transcript**: prefer manual captions > auto-captions > Whisper
   transcription from audio stream
5. **Studio CSV** (user-provided): retention curve, traffic sources, CTR
   by source, impressions, audience tab, real-time first-24h curve
6. **Audio loudness**: `ffmpeg -i audio.m4a -af loudnorm=print_format=json
   -f null -` → integrated LUFS, true peak
7. **Thumbnail file**: download for analysis via `scripts/analyze_thumbnail.py`
8. **SERP grid**: fetch top-10 for primary keyword, save competitor
   thumbnails and titles for differentiation scoring

## Analysis Dimensions

### 1. Retention Curve (highest weight when Studio data provided)

Diagnose from the Studio retention curve:

- **0-15s intro**: target ≥70% still watching. Below → hook problem.
  Diagnose: weak first sentence, no payoff preview, long logo animation,
  re-introducing yourself ("Hey guys welcome back..."), asking to subscribe
  before value delivery.
- **15-60s premise**: target ≥60%. Below → premise unclear or mismatch
  with title/thumbnail.
- **Retention cliffs**: any drop >10% in <5s is a structural issue. Map
  cliffs to transcript timestamps and identify:
  - Tangent / digression
  - Ad or sponsor break placed badly
  - Pacing death (long, slow exposition)
  - Promise broken (title said X, video now does Y)
  - Visual monotony (static shot >20s without B-roll)
- **Mid-video sustain**: target curve slope ≥-0.3%/sec. Steeper = boring
  middle.
- **Ending**: the last 30s often rises (re-watchers, end-screen hover).
  If it drops hard, end-screen is poorly placed or content feels done
  before the promise delivered.
- **Spike detection**: peaks = rewatched moments = high-value moments.
  Reuse as chapter titles, thumbnails, Shorts clips.
- **APV vs niche median**: score video as ×median. Flag anything <0.8×.

If the curve is not provided, state explicitly that retention diagnosis
is unavailable and score only metadata, thumbnail, and engagement proxies.

### 2. Title (target: 60-70 chars, max 100)

- **Length** (flag >70 truncation risk, critical >100)
- **Keyword placement**: primary keyword in first 40 chars for Search;
  emotional driver in first 40 chars for Browse (which surface matters?)
- **Hook type**: curiosity, number, contrarian, benefit, authority, fear.
  A video should commit to one dominant hook type that matches surface.
- **Emotional intensity**: rate 1-5. Below 3 = passive titles that lose
  Browse impressions.
- **Clickability vs. deliverability**: can the video content back up the
  title? If no, score down (long-term CTR decay).
- **Front-load uniqueness**: avoid "My thoughts on", "A quick video about"
- **Case consistency** with channel brand

### 3. Description

- **Above-the-fold (first 150 chars)**: MUST include primary keyword,
  restate title intent, give a click-for-more reason
- **Full length**: 1,500-4,000 chars ideal. Flag <500 thin, >6,000 bloated
- **Entity coverage**: list 8-15 Knowledge Graph entities the video
  should mention for topic classification. Check transcript + description
  for coverage. Missing entities = missed semantic relevance.
- **Secondary keywords**: 3-5 naturally placed in lines 2-10
- **Chapters block**: present, first = `0:00`, ≥3, each ≥10s, descriptive
- **Links**: grouped and labeled (affiliate, social, related, resource)
- **CTA**: subscribe + next-video suggestion + lead magnet
- **Hashtags**: 3 meaningful at the bottom, first is strongest
- **FTC disclosure**: flag missing if affiliate/sponsored
- **Timestamps for Key Moments rich result**: correctly formatted
  (`M:SS - label` or `MM:SS label`), eligible for Google Search carousel

### 4. Tags

- **Count**: 5-15 (flag <5 or >20)
- **Tag 1 = exact primary keyword**
- **Mix**: 1-3 broad + 5-8 specific long-tail + 2-3 brand/channel tags
- **Total chars** <500
- **Entity overlap**: tags should reference the same entities present in
  description and transcript (consistency strengthens classification)
- **No tag spam** (unrelated popular terms)

### 5. Thumbnail

Delegate to `youtube-seo-thumbnail` for full treatment. Include a quick
score here:
- Resolution 1280x720, <2MB
- Readable at 120px wide (mobile test)
- Face + strong emotion present (niche-appropriate)
- Text ≤4 words, ≥80pt effective
- SERP differentiation (pattern-break vs top-10)
- Consistency with channel grid
- No title-thumbnail redundancy

### 6. Chapters & Key Moments

- ≥3 chapters
- First is `0:00`
- Each ≥10s
- Descriptive, keyword-rich labels (not "Intro / Main / Outro")
- Matches actual structure
- **Schema check**: propose `VideoObject` with `hasPart[].Clip` and
  `SeekToAction` entries so the embed/page unlocks Google "Key Moments"
  rich result (see optimize skill for code)

### 7. Captions & Transcript

- Manual captions present (flag auto-only)
- Language tag correct
- Translated captions for top 3 audience countries (from Studio → Audience)
- Transcript contains primary keyword in first 60s and final 60s
- Transcript contains ≥5 Knowledge Graph entities from the topic cluster

### 8. Audio Loudness

Run FFmpeg loudnorm analysis. Flag:
- Integrated loudness outside -14 to -13 LUFS (quiet = retention drag)
- True peak > -1 dBTP (clipping risk)
- Loudness range >15 LU (inconsistent — causes volume hunting)

### 9. End-screens & Cards

- End-screen uses all 4 slots (best related, playlist, subscribe, channel)
- Cards at moments of attention (peaks in retention curve if available,
  else 60-70% mark)
- Pinned comment: CTA that drives replies (question prompt)
- Pinned comment reply rate (from Studio if available)

### 10. Engagement Signals

- Like-to-view ratio vs channel median
- Comment velocity (comments / views / day since upload)
- Creator reply rate in first 24h
- Shares, saves-to-playlist visible
- Subscribe-per-1000-views (from Studio)
- Pinned-comment replies

### 11. Technical & Safety

- Resolution ≥1080p
- Made-for-Kids flag matches content (flag mismatch)
- Altered/synthetic content disclosure if AI-generated
- Copyright claims present? (from Studio)
- Embedding enabled
- Comments enabled with moderation
- Default language + audio language tags set

### 12. Shorts (if applicable, <60s vertical)

If the video is a Short, apply Shorts-specific rules INSTEAD of the long-
form retention analysis:
- **0-1s hook** (swipe-away rate)
- **Loopability** (does the end tie back to the start?)
- **Caption overlay** for muted viewing
- **Audio**: trending library audio or original remixable?
- **Title ≤40 chars**, front-loaded emotion
- **`#Shorts`** present
- **Length sweet spot**: 15-30s for loop rate, 45-60s for watch time
- **CTA to long-form** via pinned comment or end card

## Output

### Video Score Card
```
Overall Score: XX/100   (vs niche median: X.Xx)

Retention:         XX/100  ████████░░   [requires Studio CSV]
Title:             XX/100  ██████████
Description:       XX/100  ███████░░░
Tags:              XX/100  █████░░░░░
Thumbnail:         XX/100  ████████░░
Chapters:          XX/100  ██████░░░░
Captions:          XX/100  ███████░░░
Audio Loudness:    XX/100  ████████░░
Engagement:        XX/100  ███████░░░
Technical/Safety:  XX/100  █████████░
```

### Root-Cause Ranking
Rank the 3 largest drags on performance in order, each with estimated
impact (e.g., "Hook problem — fixing 0:15 retention from 55% → 70% adds
~20% AVD, estimated +30% impressions").

### Issues Found
Critical → High → Medium → Low with one-line fixes and Tier reference.

### Paste-Ready Rewrites
Hand off to `youtube-seo-optimize` for full rewrites OR inline:
- 5 title alternatives (tagged Browse-primary / Search-primary)
- New description body (with chapters, entities, hashtags)
- Tag list
- `VideoObject` + `Clip` + `SeekToAction` JSON-LD schema block
- Pinned comment CTA

### Measurement Plan
| Change | Metric to watch | Window | Success threshold |
|--------|----------------|--------|-------------------|
| New title | Browse CTR | 7 days | +15% vs baseline |
| New thumbnail | Impressions CTR | 14 days | +1 absolute pt |
| Fixed intro | 0:30 retention | next upload | ≥70% |
| Key Moments schema | Google Search video clicks | 30 days | first rich result |

## Error Handling

| Scenario | Action |
|----------|--------|
| No Studio CSV | Score retention as "unknown"; do not fabricate a curve |
| Tags not visible | Use API or ask; never invent a tag list |
| Video <48h old | Flag that velocity and CTR data are too early to judge |
| Private/unlisted | Ask for unlisted-shareable link or metadata paste |
| Shorts video | Use Shorts ruleset; skip long-form retention checks |
| Live stream VOD | Analyze the VOD as long-form but flag that chat spikes distort retention |
