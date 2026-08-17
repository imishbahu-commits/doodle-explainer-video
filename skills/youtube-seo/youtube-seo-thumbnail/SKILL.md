---
name: youtube-seo-thumbnail
description: >
  Advanced thumbnail CTR analysis using computer vision, face/emotion
  detection, CLIP-embedding SERP similarity, Gestalt composition rules,
  and YouTube native Test & Compare planning. Use when user says
  "thumbnail review", "improve CTR", "thumbnail design", or provides a
  thumbnail image/URL.
user-invokable: true
argument-hint: "[video-url | thumbnail-image-path]"
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
---

# Thumbnail Analysis (Advanced)

Diagnose CTR potential quantitatively when possible, qualitatively when
not. Thumbnail is the single biggest pre-click lever after title.

## Data Collection

1. **Source thumbnail**: download the maxres (`maxresdefault.jpg`) from
   `https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg`, fall back to
   `hqdefault.jpg` if missing
2. **SERP grid**: fetch the top 12 YouTube results for the primary
   keyword, download each thumbnail, build a 4x3 contact sheet
3. **Computer-vision pass** via `scripts/analyze_thumbnail.py`:
   - OpenCV face detection (count, bbox, size %)
   - MediaPipe face-mesh for emotion inference (or DeepFace fallback)
   - Color histogram (HSV) — dominant 3 colors
   - Contrast score (stddev of luminance)
   - Text region detection (EAST or Tesseract) — estimated word count
     and coverage %
   - CLIP embedding (`ViT-B/32`) for similarity scoring vs SERP grid
4. **Mobile preview**: resize to 120x68, 246x138, 480x270 and inspect
   legibility manually

## Analysis Dimensions

### 1. Technical
- Resolution 1280x720, 16:9, max 2MB
- Format JPG / PNG
- Safe area: no critical content in bottom-right (duration overlay
  ~6% of area) or top-right (menu dots)

### 2. Legibility at small sizes (binding constraint)

At 120x68:
- Subject identifiable? (pass/fail)
- Text readable? (pass/fail)
- Emotion readable? (pass/fail)

If any fail → critical issue. Most thumbnails designed on a desktop
monitor at 500px+ fail at 120px.

### 3. Composition — Gestalt principles

- **Figure-ground separation**: subject clearly separated from background
  (rim light, cutout, color contrast, background blur)
- **Closure**: viewer's brain completes an implied shape or story —
  works against scroll blindness
- **Continuity**: eye travels in a designed path (eye direction of face,
  arrow of object, gradient)
- **Similarity/proximity**: elements that belong together are grouped
- **Rule of thirds**: focal point at intersections, not dead-center
- **Depth**: foreground / midground / background create dimensionality
- **Negative space**: enough breathing room for the focal point to pop
  at small sizes

### 4. Face + emotion

- Face present? (niche-dependent: boost for most, neutral for gaming/
  product review close-ups)
- Facial emotion (from MediaPipe/DeepFace): surprise, fear, joy, anger,
  disgust, sadness, neutral. Surprise and fear typically lift Browse CTR
  most.
- Eye contact direction: direct-gaze lifts trust; side-gaze creates
  curiosity
- Face size: 20-35% of thumbnail area is the sweet spot
- Single face outperforms multiple faces in most A/B tests

### 5. Text overlay

- ≤4 words (ideally ≤3)
- Font: bold sans-serif, 80-120pt effective
- Legibility: stroke or drop-shadow against variable backgrounds
- **Complementary to title** (not redundant): the thumbnail text should
  say what the title does NOT
- Placement: top-left or top-right (viewers scan F-pattern on feeds)

### 6. Color palette

- 2-3 dominant colors (from histogram)
- High-saturation accent against low-saturation base
- **Contrast vs YouTube UI** (white on light mode, dark gray on dark
  mode): ensure thumbnail pops in both modes
- **Brand consistency** across the channel grid (same accent color,
  same typography family)

### 7. SERP differentiation (CLIP embedding)

Compute cosine similarity between the target thumbnail and each of the
top-12 SERP thumbnails. Scoring:

- **Avg similarity <0.55**: strong pattern-break (good)
- **0.55-0.70**: typical
- **>0.70**: too similar to competitors, will blend in

Also report the 3 most similar SERP thumbnails as visual references
for the user.

### 8. Channel brand consistency

Compare the target thumbnail to the last 11 channel thumbnails (4x3
grid). Measure:
- Color palette overlap
- Typography consistency
- Face presence consistency
- Style template adherence

Flag if the target is an outlier — brand recognition in the subscriber
feed drops when styles drift.

### 9. Title-thumbnail synergy

- Zero redundant words between title and thumbnail text
- Thumbnail emotion matches title promise
- No bait-mismatch with video content (long-term CTR decay risk)

## Output

### Thumbnail Score Card

```
Overall: XX/100

Technical:         XX/100
Legibility (120px):XX/100   ← hard gate
Composition:       XX/100
Face + Emotion:    XX/100
Text Overlay:      XX/100
Color / Contrast:  XX/100
SERP Differentiation: XX/100  (cosine avg: 0.XX)
Brand Consistency: XX/100
Title Synergy:     XX/100
```

### CV Report
```
Faces detected: N
Dominant emotion: surprise (0.XX confidence)
Face area: XX% of thumbnail
Dominant colors: #RRGGBB, #RRGGBB, #RRGGBB
Contrast score: X.XX
Text regions: N  (est. words: M)
SERP similarity (avg cosine): 0.XX
Most similar SERP entry: {URL}
```

### Issues Found
Critical → High → Medium → Low.

### Redesign Brief (paste-ready for designer or image generator)

```
Subject: {who/what is centered}
Expression: {facial emotion — cite research-backed CTR driver}
Composition: {rule of thirds position, focal point, leading line}
Background: {setting, depth layers, color wash, blur level}
Foreground element: {optional prop or graphic element}
Text overlay: "{≤3 words}" in {font family, weight}, {color} with
              {stroke/shadow}, {position}, {size %}
Palette: {2-3 hex colors + accent}
Style: {photographic / illustrated / hybrid / 3D}
Differentiator vs SERP: {specific pattern break — "all competitors use
                         red + face left, we use teal + face right"}
References: {2-3 high-performing thumbnails from outside the niche}
Safe area: {avoid bottom-right duration overlay}
Export: 1280x720 JPG, <2MB, sRGB
```

### Native A/B Test Plan

YouTube Studio → Content → Edit → Thumbnail → Test & Compare:

- **Variant A**: current thumbnail (control)
- **Variant B**: redesigned with strongest recommended change (e.g.,
  swap emotion surprise→fear)
- **Variant C**: second-strongest change (e.g., different color palette)
- **Rotation**: YouTube decides split based on impressions
- **Window**: 2 weeks minimum, 10k impressions minimum for significance
- **Success metric**: Browse CTR (not Search CTR — Search is keyword-
  bound). Require ≥0.5 absolute point lift for decision.

### Generation (optional)

If the user wants an actual image generated, delegate to `seo-image-gen`
with the redesign brief as the prompt. Set aspect 16:9 and size
1280x720.

## Error Handling

| Scenario | Action |
|----------|--------|
| No image provided | Ask for video URL or thumbnail file |
| Image <640px wide | Flag and ask for the source file |
| Channel niche unknown | Ask before running SERP differentiation |
| CLIP unavailable in environment | Fall back to manual grid inspection and description-based similarity |
| MFK channel | Emphasize legibility + brand; skip face-emotion lift (kids thumbnails have different rules) |
