#!/usr/bin/env python3
"""qwen_media.py — generate images and videos with a Qwen key via
TokensRouter (OpenAI-compatible API).

SAFE KEY HANDLING:
  - The key is NEVER typed in chat and NEVER committed to git.
  - Put it in a `.env` file next to this script (gitignored):
        QWEN_API_KEY=sk-xxxxxxxx
  - Or export it:  export QWEN_API_KEY=sk-xxxxxxxx

Usage:
  python3 qwen_media.py models                          # what your key can do
  python3 qwen_media.py image "a campfire at night..."  # -> out.png
  python3 qwen_media.py video "a slow dolly over..."    # -> out.mp4 (text->video)
  python3 qwen_media.py i2v photo.png "slow zoom in"    # -> out.mp4 (image->video)

Requires: pip install requests python-dotenv
"""

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    sys.exit("pip install requests python-dotenv first")

load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.environ.get("QWEN_API_KEY", "")
BASE = os.environ.get("QWEN_BASE_URL", "https://api.tokensrouter.com/v1")

# Model slugs differ per router. These are sensible defaults; run
# `python3 qwen_media.py models` to see what YOUR key exposes and override
# with env vars QWEN_IMAGE_MODEL / QWEN_VIDEO_MODEL.
IMAGE_MODEL = os.environ.get("QWEN_IMAGE_MODEL", "qwen-image")
VIDEO_MODEL = os.environ.get("QWEN_VIDEO_MODEL", "wan-2.2-t2v")
I2V_MODEL = os.environ.get("QWEN_I2V_MODEL", "wan-2.2-i2v")


def headers():
    if not API_KEY:
        sys.exit("no QWEN_API_KEY — put it in .env (never in chat!)")
    return {"Authorization": f"Bearer {API_KEY}"}


def models():
    r = requests.get(f"{BASE}/models", headers=headers(), timeout=30)
    r.raise_for_status()
    for m in sorted(m["id"] for m in r.json().get("data", [])):
        print(m)


def gen_image(prompt, out):
    # chat-completions style (common on routers) with images fallback
    r = requests.post(
        f"{BASE}/images/generations",
        headers=headers(),
        json={"model": IMAGE_MODEL, "prompt": prompt, "size": "1328x1328"},
        timeout=300)
    if r.status_code == 404:  # router uses chat-completions for qwen-image
        r = requests.post(
            f"{BASE}/chat/completions",
            headers=headers(),
            json={"model": IMAGE_MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=300)
    r.raise_for_status()
    data = r.json()
    url = None
    if "data" in data and data["data"]:
        url = data["data"][0].get("url")
    elif "choices" in data and data["choices"]:
        content = data["choices"][0]["message"].get("content", "")
        for part in content.split():
            if part.startswith("http"):
                url = part.strip("()[]\"'")
    if not url:
        print("response:", str(data)[:600])
        sys.exit("could not find an image URL in the response")
    Path(out).write_bytes(requests.get(url, timeout=120).content)
    print(f"wrote {out}")


def gen_video(prompt, out, image_path=None, model=None):
    model = model or (I2V_MODEL if image_path else VIDEO_MODEL)
    payload = {"model": model, "prompt": prompt}
    if image_path:
        b64 = __import__("base64").b64encode(Path(image_path).read_bytes()).decode()
        payload["image"] = f"data:image/png;base64,{b64}"
    r = requests.post(f"{BASE}/videos/generations", headers=headers(),
                      json=payload, timeout=600)
    if r.status_code in (404, 400):
        print("video endpoint rejected — try:", str(r.json())[:400])
        sys.exit(1)
    r.raise_for_status()
    task = r.json()
    if "id" in task:  # async poll
        tid = task["id"]
        for _ in range(120):
            time.sleep(5)
            st = requests.get(f"{BASE}/videos/generations/{tid}",
                              headers=headers(), timeout=30).json()
            if st.get("status") in ("succeeded", "completed", "done"):
                url = st["data"][0].get("url") if "data" in st else st.get("video_url")
                Path(out).write_bytes(requests.get(url, timeout=300).content)
                print(f"wrote {out}")
                return
            if st.get("status") in ("failed", "error"):
                sys.exit(f"generation failed: {st}")
        sys.exit("timed out waiting for video")
    else:
        url = task["data"][0].get("url")
        Path(out).write_bytes(requests.get(url, timeout=300).content)
        print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models")
    p = sub.add_parser("image"); p.add_argument("prompt")
    p = sub.add_parser("video"); p.add_argument("prompt")
    p = sub.add_parser("i2v"); p.add_argument("image"); p.add_argument("prompt")
    args = ap.parse_args()
    if args.cmd == "models":
        models()
    elif args.cmd == "image":
        gen_image(args.prompt, "out.png")
    elif args.cmd == "video":
        gen_video(args.prompt, "out.mp4")
    elif args.cmd == "i2v":
        gen_video(args.prompt, "out.mp4", image_path=args.image)
