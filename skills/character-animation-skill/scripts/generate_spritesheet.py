#!/usr/bin/env python3
"""
Generate a 4K sprite-sheet animation from a single character image using
Nano Banana 2 (Gemini 3.1 Flash Image, model id `gemini-3.1-flash-image`).

The character image anchors identity; the --motion text describes the animation.
Nano Banana 2 lays the frames out in a regular grid on a flat white background.

Usage:
  python3 generate_spritesheet.py CHARACTER_IMAGE OUTPUT.png \
      --motion "the octopus gently waves its tentacles and bobs up and down, looping"

Common options:
  --rows 6 --cols 6        grid layout (default 6x6 = 36 frames)
  --size 4K                512 | 1K | 2K | 4K  (default 4K)
  --aspect 1:1             output aspect ratio (default 1:1)
  --model gemini-3.1-flash-image   (Nano Banana 2; do NOT use the Pro model)
  --extra "..."            extra art-direction appended to the prompt
  --dry-run                print the assembled prompt and exit (no API call)

The API key is read from $GEMINI_API_KEY, falling back to
~/.config/character-animation/key.env.
"""
import argparse, base64, json, mimetypes, os, sys, time
from pathlib import Path

import urllib.request
import urllib.error

CONFIG_KEY = Path.home() / ".config" / "character-animation" / "key.env"


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key.strip()
    if CONFIG_KEY.exists():
        for line in CONFIG_KEY.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                return v.strip().strip('"').strip("'")
    sys.exit(
        "ERROR: no API key. Set $GEMINI_API_KEY or create "
        f"{CONFIG_KEY} with a GEMINI_API_KEY=... line."
    )


def build_prompt(motion: str, rows: int, cols: int, extra: str,
                 bg: str = "white (#FFFFFF)") -> str:
    n = rows * cols
    return (
        f"Take the SUPPLIED IMAGE as the one and only reference character. Reproduce that "
        f"exact character — identical colors, materials, design, markings and body "
        f"proportions — in every single frame.\n\n"
        f"Produce ONE image that is a SPRITE SHEET: a perfectly regular {cols}x{rows} grid "
        f"({n} cells, {cols} columns by {rows} rows). Every cell is the same size and evenly "
        f"spaced. Place exactly one instance of the character, centered, in each cell, at the "
        f"SAME scale and the SAME position within its cell across all frames, with a small even "
        f"margin so nothing is ever clipped at the cell edges.\n\n"
        f"The {n} frames are consecutive frames of this looping animation:\n"
        f"  {motion}\n"
        f"Read the grid left-to-right, top-to-bottom. Frame 1 is the start; each following frame "
        f"advances the motion by a small, even step; the last frame leads smoothly back into the "
        f"first so the loop is seamless. Keep the change between neighbouring frames small and "
        f"continuous — no sudden jumps.\n\n"
        f"Background and cleanliness rules (critical for downstream processing):\n"
        f"  - Pure flat solid {bg} background everywhere — the same exact background color in "
        f"every cell. No gradient, no vignette, no floor, no cast shadow, no reflection. The "
        f"background color must NOT appear anywhere on the character itself.\n"
        f"  - Absolutely NO text, numbers, frame labels, captions, watermarks, borders, frame "
        f"outlines, boxes, or grid lines. Just the characters on white.\n"
        f"  - Keep lighting, color and style identical across every frame.\n"
        + (f"\nAdditional art direction: {extra}\n" if extra else "")
    )


def generate(args) -> int:
    prompt = build_prompt(args.motion, args.rows, args.cols, args.extra, args.bg_color)
    if args.dry_run:
        print(prompt)
        return 0

    key = load_api_key()
    img_path = Path(args.image)
    if not img_path.exists():
        sys.exit(f"ERROR: character image not found: {img_path}")
    mime = mimetypes.guess_type(str(img_path))[0] or "image/png"
    b64 = base64.b64encode(img_path.read_bytes()).decode()

    body = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": b64}},
        ]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": args.aspect, "imageSize": args.size},
        },
    }
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{args.model}:generateContent")
    payload = json.dumps(body).encode()

    last_err = None
    for attempt in range(1, args.retries + 1):
        try:
            req = urllib.request.Request(
                url, data=payload, method="POST",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            )
            print(f"[nb2] {args.model} {args.size} {args.aspect} "
                  f"{args.cols}x{args.rows} (attempt {attempt})...", file=sys.stderr)
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode())
            return _save_image(data, args.output)
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:1000]
            last_err = f"HTTP {e.code}: {detail}"
            # 429/5xx are worth retrying; 4xx (other) are not
            if e.code in (429, 500, 502, 503, 504) and attempt < args.retries:
                wait = min(2 ** attempt * 5, 60)
                print(f"[nb2] {last_err}\n[nb2] retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            break
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = str(e)
            if attempt < args.retries:
                time.sleep(5)
                continue
            break
    sys.exit(f"ERROR: generation failed. {last_err}")


def _save_image(data: dict, out_path: str) -> int:
    cands = data.get("candidates") or []
    if not cands:
        fb = data.get("promptFeedback")
        sys.exit(f"ERROR: no candidates returned. promptFeedback={fb}")
    parts = cands[0].get("content", {}).get("parts", [])
    saved = False
    for part in parts:
        if "text" in part and part["text"]:
            print("[nb2] model note:", part["text"][:300], file=sys.stderr)
        inl = part.get("inline_data") or part.get("inlineData")
        if inl and inl.get("data"):
            raw = base64.b64decode(inl["data"])
            Path(out_path).write_bytes(raw)
            print(f"[nb2] saved {out_path} ({len(raw)} bytes)")
            saved = True
    if not saved:
        fr = cands[0].get("finishReason")
        sys.exit(f"ERROR: response contained no image (finishReason={fr}). "
                 f"Try rephrasing the motion or rerun.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Generate a sprite sheet with Nano Banana 2.")
    ap.add_argument("image", help="path to the single character reference image")
    ap.add_argument("output", help="output sprite-sheet path (.png)")
    ap.add_argument("--motion", required=True, help="description of the looping animation")
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--size", default="4K", choices=["512", "1K", "2K", "4K"])
    ap.add_argument("--aspect", default="1:1")
    ap.add_argument("--model", default="gemini-3.1-flash-image",
                    help="Nano Banana 2. Do not use gemini-3-pro-image (that is Pro).")
    ap.add_argument("--extra", default="")
    ap.add_argument("--bg-color", dest="bg_color", default="white (#FFFFFF)",
                    help="background color described to the model. For light/white "
                         "characters use a chroma color the subject lacks, e.g. "
                         "'chroma-key green (#00B140)'. Pair with the converter's "
                         "matching --bg-color.")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    sys.exit(generate(ap.parse_args()))


if __name__ == "__main__":
    main()
