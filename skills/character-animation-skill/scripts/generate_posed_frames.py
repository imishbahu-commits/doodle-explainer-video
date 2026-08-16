#!/usr/bin/env python3
r"""
Coherent per-frame generation (Mode 2) for the character-animation skill.

Instead of asking Nano Banana 2 to draw a whole sprite sheet in one shot (which
gives no frame-to-frame coherence — good enough for amorphous creatures, bad for
rigid/humanoid characters), this generates each frame INDIVIDUALLY as an edit of
one fixed "base plate" image, changing only what the pose says. Because every
frame starts from the same anchored image (same character, size, position,
full-body framing, same background), the result is coherent: no missing legs, no
size jumps, a deliberate motion.

Inputs:
  base_plate.png   the character locked on a flat chroma background (full body,
                   centered, with headroom for raised limbs). Build it with, e.g.:
                     magick -size 1024x1024 xc:'#00B140' \
                       \( char.png -resize x820 \) -gravity south \
                       -geometry +0+24 -composite base_plate.png
  poses.json       a JSON list, one entry per frame, in play order:
                     [{"pose": "...", "eyes": "..."}, ...]
                   `pose` describes the limb/body change; `eyes` (optional)
                   describes the eye/face state. You (Claude) author this list
                   from the user's motion so the frames form a smooth loop.

Usage:
  python3 generate_posed_frames.py base_plate.png poses.json --out-dir frames \
      --size 1K --bg "flat solid green (#00B140)" --workers 4
"""
import argparse, base64, json, os, sys, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CONFIG_KEY = Path.home() / ".config" / "character-animation" / "key.env"
MODEL = "gemini-3.1-flash-image"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key.strip()
    if CONFIG_KEY.exists():
        for line in CONFIG_KEY.read_text().splitlines():
            if line.strip().startswith(("GEMINI_API_KEY", "GOOGLE_API_KEY")) and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: no API key ($GEMINI_API_KEY or ~/.config/character-animation/key.env)")


def frame_prompt(pose, eyes, bg):
    return (
        f"This image shows a character standing on a {bg} screen. Output the SAME "
        f"character with the EXACT same design, the exact same size, and the exact same "
        f"position and framing — the WHOLE body fully visible, feet in the same spot — on "
        f"the same flat {bg} background. The ONLY difference from this reference is the "
        f"pose: {pose} {eyes} "
        f"Do not move, rescale, rotate, restyle, chibi-fy, or crop the character. Keep the "
        f"entire body (including legs/feet) fully in frame. Flat solid {bg} background, the "
        f"same in every frame, no shadow, no text, no labels."
    )


def gen_one(idx, pose, eyes, base_b64, key, size, bg, out_dir, retries):
    prompt = frame_prompt(pose, eyes or "", bg)
    body = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/png", "data": base_b64}},
        ]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "1:1", "imageSize": size},
        },
    }
    payload = json.dumps(body).encode()
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                URL, data=payload, method="POST",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode())
            for part in data["candidates"][0]["content"]["parts"]:
                inl = part.get("inline_data") or part.get("inlineData")
                if inl and inl.get("data"):
                    out = Path(out_dir) / f"frame_{idx:02d}.png"
                    out.write_bytes(base64.b64decode(inl["data"]))
                    return idx, True, ""
            return idx, False, "no image part"
        except urllib.error.HTTPError as e:
            msg = f"HTTP {e.code}: {e.read().decode()[:200]}"
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(min(2 ** attempt * 4, 40)); continue
            return idx, False, msg
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(4); continue
            return idx, False, str(e)
    return idx, False, "exhausted retries"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base_plate")
    ap.add_argument("poses")
    ap.add_argument("--out-dir", default="frames")
    ap.add_argument("--size", default="1K", choices=["512", "1K", "2K", "4K"])
    ap.add_argument("--bg", default="flat solid green (#00B140)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--retries", type=int, default=3)
    args = ap.parse_args()

    key = load_api_key()
    poses = json.loads(Path(args.poses).read_text())
    base_b64 = base64.b64encode(Path(args.base_plate).read_bytes()).decode()
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    print(f"[posed] generating {len(poses)} frames at {args.size}, "
          f"{args.workers} workers...", file=sys.stderr)
    t0 = time.time()
    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(gen_one, i, p.get("pose", ""), p.get("eyes", ""),
                          base_b64, key, args.size, args.bg, args.out_dir, args.retries)
                for i, p in enumerate(poses)]
        for f in as_completed(futs):
            idx, good, err = f.result()
            ok += good
            print(f"[posed] frame {idx:02d} {'OK' if good else 'FAIL: ' + err}",
                  file=sys.stderr)
    print(f"[posed] {ok}/{len(poses)} frames in {time.time()-t0:.0f}s -> {args.out_dir}")
    sys.exit(0 if ok == len(poses) else 2)


if __name__ == "__main__":
    main()
