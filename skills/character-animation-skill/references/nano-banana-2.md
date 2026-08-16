# Nano Banana 2 — Gemini image API reference

Verified against the live Gemini API (June 2026) for this project's key.

## Model IDs (confirmed from `models.list`)

| Nickname        | Model ID                          | Notes                                  |
|-----------------|-----------------------------------|----------------------------------------|
| **Nano Banana 2** | `gemini-3.1-flash-image`        | **Use this.** Gemini 3.1 Flash Image (codename GEMPIX2). Fast, cheap, near-Pro quality. |
| Nano Banana 2 (preview) | `gemini-3.1-flash-image-preview` | Same family; the non-preview id is fine. |
| Nano Banana Pro | `gemini-3-pro-image` / `-preview` | **Do NOT use** — the user specifically asked for NB2, not Pro. |
| Nano Banana (v1)| `gemini-2.5-flash-image`          | Older; no 4K, weaker.                  |

## Endpoint & auth

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent
Header: x-goog-api-key: $GEMINI_API_KEY      (or ?key=$GEMINI_API_KEY)
```

The key for this skill lives in `~/.config/character-animation/key.env`
(`GEMINI_API_KEY=...`, chmod 600). `generate_spritesheet.py` loads it from
there or from `$GEMINI_API_KEY`.

## Resolution & aspect ratio (the 4K knob)

Set them in `generationConfig.imageConfig`:

```json
{
  "contents": [{"parts": [
    {"text": "<prompt>"},
    {"inline_data": {"mime_type": "image/png", "data": "<base64 character image>"}}
  ]}],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {"aspectRatio": "1:1", "imageSize": "4K"}
  }
}
```

- `imageSize`: `"512"`, `"1K"`, `"2K"`, `"4K"`. **Uppercase K is required** (lowercase is rejected). `512` is Flash-only.
- `aspectRatio`: `1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9`.
- `4K` + `1:1` returns a 4096×4096 image. Tested: ~2K returns 2048×2048.

## Response shape

Image bytes come back base64 in `candidates[0].content.parts[*].inline_data.data`
(SDKs also expose `part.inlineData`). There may also be a text part — log it, it
sometimes explains a refusal. If no image part exists, check
`candidates[0].finishReason` and `promptFeedback` (safety blocks).

## Behaviour notes that matter for sprite sheets

- **Output is usually JPEG**, even for a "white background" — there is **no
  transparent-background option**. Always key out the background afterward
  (the converter does this).
- The background it paints is near-white but **not perfectly pure** and can carry
  faint shadows; that's why the converter uses a tolerant connected-components
  key rather than a naive `-transparent white`.
- It honours an explicit grid ("a perfectly regular 6x6 grid, equal cells")
  reasonably well, but cells are **not pixel-perfect**; the converter slices on
  an even grid, which tolerates small drift. If a sheet comes back badly
  misaligned, regenerate (variability is normal) or drop to a smaller grid.
- Character identity holds best with **fewer frames**; 36 in one sheet is the
  upper end. If consistency drifts across 6x6, try 5x5 or 4x4.
- It will sometimes still add tiny labels/numbers despite instructions — keep the
  "NO text/labels/borders/grid lines" rule prominent, and the `--label-crop`
  option exists as a fallback for captioned sheets.

## Cost / latency (rough)

NB2 ≈ \$0.04–0.08 per image at standard res; 4K costs more and takes noticeably
longer than 2K (tens of seconds). Generate at 2K while iterating on the motion
prompt, then do the final pass at 4K.
