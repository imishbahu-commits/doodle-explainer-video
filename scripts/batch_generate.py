#!/usr/bin/env python3
"""batch_generate.py — UNLIMITED batch image generation with open-source
pipelines only. No Arena image tool, no paid API, no per-image cap.

Three backends, all open source:

  assets  23 open hand-drawn libraries (Kenney CC0, game-icons CC BY,
          openclipart public domain, fxemoji/twemoji/openmoji CC BY,
          humaaans CC BY, ...) fetched one file at a time through the
          GitHub API. Unlimited, works from any machine that can reach
          api.github.com (including this sandbox). SVG assets are
          rasterised locally with resvg-js (npm). Every file's licence is
          recorded in the ledger and CREDITS.md.

  hf      Real open diffusion models via HuggingFace `diffusers`
          (defaults: OFA-Sys/small-stable-diffusion-v0 on CPU,
          stabilityai/sd-turbo on CUDA; override with --model — e.g.
          black-forest-labs/FLUX.1-schnell on a good GPU). Unlimited,
          seeded, style-prefixed. Needs internet to download the weights
          ONCE and a GPU for speed — run it on your own machine:
              pip install torch diffusers
              python3 scripts/batch_generate.py run PROJECT --backend hf

  qwen    Qwen-Image (Apache-2.0 open model) through your QWEN_API_KEY
          (see tools/qwen_media.py). Run where api.tokensrouter.com is
          reachable; the key lives in tools/.env, never in chat or git.

Workflow
--------
  1. queue prompts — one per line. For `assets` each line is a SEARCH
     KEYWORD, optionally pinned to one library with @library:
         shark-fin@game-icons        (pinned)
         ocean                      (any library)
  2. generate (resumes automatically, --limit caps a run):
         python3 scripts/batch_generate.py run PROJECT --backend assets
  3. watch progress, build a contact sheet:
         python3 scripts/batch_generate.py status PROJECT
         python3 scripts/batch_generate.py sheet PROJECT

Output
------
  projects/PROJECT/assets/NNN.ext    images (manifest-ready: assets/001.png)
  projects/PROJECT/images.json       ledger: prompt, source, licence, seed
  projects/PROJECT/CREDITS.md        licence/credit lines per image
  projects/PROJECT/contact-sheet.png visual index (needs Pillow)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SKILL_SCRIPTS = ROOT / "skills" / "asset-library" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
import asset_fetch  # noqa: E402  (reuses LIBS + cached git trees)

LIBS = asset_fetch.LIBS

# Doodle-style library preference (sketchy hand-drawn first).
PRIORITY = [
    "game-icons", "openclipart", "fxemoji", "twemoji", "openmoji",
    "noto-emoji", "kenney", "tabler-icons", "feather", "phosphor",
    "bootstrap-icons", "font-awesome", "fluent-emoji", "humaaans",
    "open-peeps", "dungeontileset-0x72", "pixel-adventure", "lpc",
    "simple-icons",
]
PRIO = {name: (len(PRIORITY) - i) * 8 for i, name in enumerate(PRIORITY)}

DOODLE_STYLE = ("Simple hand-drawn doodle illustration, whiteboard sketch "
                "style: black ink outlines, minimal shading, stick figures, "
                "clean white background, no text, no words, no watermark.")


# ---------------------------------------------------------------- helpers

def project_dir(project):
    d = ROOT / "projects" / project
    d.mkdir(parents=True, exist_ok=True)
    (d / "assets").mkdir(exist_ok=True)
    return d


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def ledgers(project):
    d = project_dir(project)
    prompts = load_json(d / "prompts.json", [])
    images = load_json(d / "images.json", [])
    return d, prompts, images


def done_ids(images, assets_dir):
    return {im["id"] for im in images
            if (assets_dir / im["file"].split("/")[-1]).exists()}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------- assets backend

def _norm(s):
    return (s.lower().replace("-", " ").replace("_", " ")
            .replace(".", " ").strip())


def _search_lib(src, keyword):
    """All image paths in one library whose filename matches the keyword."""
    hits = []
    try:
        entries = asset_fetch.tree(src).get("tree", [])
    except Exception:
        return hits
    kw_tokens = set(_norm(keyword).split())
    for e in entries:
        path = e.get("path", "")
        low = path.lower()
        if not low.endswith((".png", ".svg", ".jpg", ".jpeg", ".webp")):
            continue
        name = _norm(path.split("/")[-1])
        if not name or not any(t in name or name.startswith(t) or name.endswith(t)
                               for t in kw_tokens):
            continue
        hits.append(path)
    return hits


def rank_candidates(src, path, keyword):
    """Higher = better doodle match for this keyword."""
    name = _norm(path.split("/")[-1])
    kw = _norm(keyword)
    score = 0
    if name == kw:
        score += 100
    elif name.startswith(kw) or name.endswith(kw):
        score += 70
    elif kw in name:
        score += 45
    else:
        tokens = kw.split()
        score += 15 * sum(1 for t in tokens if t in name)
    score += PRIO.get(src, 5)
    if "flat" in name:
        score += 20          # flat emoji = closest to doodle style
    if "3d" in name:
        score -= 25          # 3D renders are off-style
    if "color" in name and "flat" not in name:
        score -= 5
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        score += 4  # no rasterisation step needed
    return score


def fetch_via_gh(src, path):
    """One file through the GitHub contents API (base64, <=1MB)."""
    repo = LIBS[src]["repo"]
    quoted = urllib.parse.quote(path, safe="/() ")
    p = subprocess.run(["gh", "api", f"repos/{repo}/contents/{quoted}"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[:200])
    meta = json.loads(p.stdout)
    if not meta.get("content"):
        raise RuntimeError("file too large for the contents API")
    return base64.b64decode(meta["content"])


def rasterize(svg_path, png_path, width=1024):
    p = subprocess.run(["node", str(SKILL_SCRIPTS / "svg2png.mjs"),
                        str(svg_path), str(png_path), str(width)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "")[-300:])


def gen_assets_one(keyword, out_dir, delay=0.2):
    """Fetch the best open-library image for a keyword -> (bytes, ext, src, path)."""
    src_pin = None
    if "@" in keyword:
        keyword, src_pin = keyword.split("@", 1)
        if src_pin not in LIBS:
            raise RuntimeError(f"unknown library '{src_pin}' (see libraries.json)")
    keyword = keyword.strip()
    if not keyword:
        raise RuntimeError("empty keyword")

    libs = [src_pin] if src_pin else PRIORITY
    candidates = []
    for src in libs:
        fmt = LIBS[src]["fmt"]
        if "svg" not in fmt and "png" not in fmt:
            continue  # audio or other
        for path in _search_lib(src, keyword):
            candidates.append((rank_candidates(src, path, keyword), src, path))
    if not candidates:
        raise RuntimeError(f"no open asset found for '{keyword}'")

    last_err = "no candidates"
    for _, src, path in sorted(candidates, reverse=True)[:8]:
        time.sleep(delay)
        try:
            data = fetch_via_gh(src, path)
        except Exception as e:
            last_err = f"{src}/{path}: {e}"
            continue
        ext = ".svg" if path.lower().endswith(".svg") else Path(path).suffix.lower()
        return data, ext, src, path
    raise RuntimeError(f"fetch failed for '{keyword}': {last_err}")


def save_asset(data, ext, out_path):
    if ext != ".png":
        tmp = out_path.with_suffix(ext)
        tmp.write_bytes(data)
        rasterize(tmp, out_path)
        tmp.unlink(missing_ok=True)
    else:
        out_path.write_bytes(data)


# ------------------------------------------------------------ hf backend

def gen_hf_one(prompt, out_path, model, size, steps, seed, style):
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError:
        sys.exit(
            "\n[ERROR] diffusers/torch not installed — the HF backend downloads\n"
            "        open model weights and runs them locally, which this\n"
            "        sandbox cannot reach (huggingface.co is firewalled here).\n"
            "        Run it on your own machine:\n"
            "            pip install torch diffusers\n"
            "            python3 scripts/batch_generate.py run PROJECT "
            "--backend hf --model stabilityai/sd-turbo\n")
    device = ("cuda" if torch.cuda.is_available() else
              "mps" if getattr(torch.backends, "mps", None) and
              torch.backends.mps.is_available() else "cpu")
    dtype = (torch.float16 if device != "cpu" else torch.float32)
    if model is None:
        model = ("stabilityai/sd-turbo" if device == "cuda" else
                 "OFA-Sys/small-stable-diffusion-v0")
    log(f"hf: loading open model '{model}' on {device} "
        f"(first run downloads weights, then it is unlimited)")
    pipe = AutoPipelineForText2Image.from_pretrained(
        model, torch_dtype=dtype, safety_checker=None)
    pipe = pipe.to(device)
    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing()
    w, h = size
    full = f"{style} {prompt}".strip()
    gen = torch.Generator(device="cpu").manual_seed(seed)
    log(f"hf: generating '{prompt[:60]}' (seed {seed}, {steps} steps)")
    image = pipe(full, num_inference_steps=steps, generator=gen,
                 width=w, height=h).images[0]
    image.save(out_path)
    return {"model": model, "device": device, "seed": seed,
            "steps": steps, "size": f"{w}x{h}"}


# ---------------------------------------------------------- qwen backend

def gen_qwen_one(prompt, out_path):
    script = ROOT / "tools" / "qwen_media.py"
    tmp = out_path.parent / "qwen_tmp.png"
    p = subprocess.run([sys.executable, str(script), "image", prompt],
                       capture_output=True, text=True, cwd=script.parent)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "")[-400:])
    if not tmp.exists():
        raise RuntimeError("qwen_media.py produced no out.png — check QWEN_API_KEY")
    tmp.replace(out_path)
    return {"model": "qwen-image", "backend_note": "Qwen-Image (Apache-2.0)"}


def write_credits(d, images):
    """CREDITS.md — licence + attribution line per generated image."""
    used = [im for im in images if im.get("source")]
    if not used:
        return
    lines = ["# CREDITS — open-source artwork used by this project", ""]
    for im in sorted(used, key=lambda x: x["id"]):
        src = im["source"]
        credit = LIBS[src].get("credit", "") if src in LIBS else ""
        lines.append(f"- `{im['file']}` — **{im['keyword'][:60]}** — {src} "
                     f"({im['license']}) {credit}".rstrip())
    (d / "CREDITS.md").write_text("\n".join(lines) + "\n")


def cmd_fill(args):
    """Server-side: generate beats whose open-map entry points at an open
    library keyword. No phone, no AI API — pure GitHub-fetched CC/PD art."""
    d, prompts, images = ledgers(args.project)
    if not prompts:
        sys.exit(f"no prompts — run init first (projects/{args.project}/prompts.json)")
    map_path = d / (args.map or "open-map.json")
    if not map_path.exists():
        sys.exit(f"no open map at {map_path} — create it as {{beat_id: keyword}}")
    mapping = json.loads(map_path.read_text())
    assets = d / "assets"
    done = done_ids(images, assets)
    todo = [p for p in prompts
            if str(p["id"]) in mapping and p["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print(f"nothing to fill — all mapped beats already have images "
              f"in projects/{args.project}/assets/")
        return
    log(f"fill project={args.project} beats={len(todo)} (open-library backend)")
    for i, p in enumerate(todo, 1):
        num = p["id"]
        out = assets / f"{num:03d}.png"
        entry = {"id": num, "keyword": p["keyword"], "backend": "assets",
                 "file": f"assets/{out.name}"}
        try:
            kw = str(mapping[str(num)])
            data, ext, src, path = gen_assets_one(kw, assets, args.delay)
            save_asset(data, ext, out)
            entry.update({"source": src, "asset_path": path,
                          "license": LIBS[src]["license"], "bytes": len(data),
                          "open_keyword": kw})
        except Exception as e:
            log(f"[{i}/{len(todo)}] FAIL id {num} '{mapping[str(num)]}': {e}")
            entry["error"] = str(e)[:300]
            images.append(entry)
            save_json(d / "images.json", images)
            continue
        log(f"[{i}/{len(todo)}] ok id {num} '{mapping[str(num)]}' "
            f"-> {entry['file']} ({entry.get('license','')})")
        images.append(entry)
        save_json(d / "images.json", images)
    write_credits(d, images)
    log("done — re-run to retry failures; `status` / `sheet` show progress.")


# ------------------------------------------------------------- commands

def cmd_init(args):
    if not args.prompts and not args.keywords:
        sys.exit("init needs --prompts FILE or --keywords 'a,b,c'")
    d, _, _ = ledgers(args.project)
    if args.prompts:
        lines = [l.strip() for l in Path(args.prompts).read_text().splitlines()
                 if l.strip()]
    else:
        lines = [k.strip() for k in args.keywords.split(",") if k.strip()]
    prompts = [{"id": i + 1, "keyword": k} for i, k in enumerate(lines)]
    save_json(d / "prompts.json", prompts)
    save_json(d / "images.json", [])
    print(f"queued {len(prompts)} prompts in projects/{args.project}/prompts.json")


def cmd_run(args):
    d, prompts, images = ledgers(args.project)
    if not prompts:
        sys.exit(f"no prompts — run init first (projects/{args.project}/prompts.json)")
    done = done_ids(images, d / "assets")
    todo = [p for p in prompts if p["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print(f"nothing to do — all {len(prompts)} images already generated "
              f"in projects/{args.project}/assets/")
        return
    log(f"backend={args.backend} project={args.project} "
        f"queued={len(todo)} already_done={len(done)}")
    assets = d / "assets"
    for i, p in enumerate(todo, 1):
        num = p["id"]
        out = assets / f"{num:03d}.png"
        entry = {"id": num, "keyword": p["keyword"], "backend": args.backend,
                 "file": f"assets/{out.name}"}
        t0 = time.time()
        try:
            if args.backend == "assets":
                data, ext, src, path = gen_assets_one(p["keyword"], assets,
                                                      args.delay)
                save_asset(data, ext, out)
                entry.update({"source": src, "asset_path": path,
                              "license": LIBS[src]["license"],
                              "bytes": len(data)})
            elif args.backend == "hf":
                entry.update(gen_hf_one(p["keyword"], out, args.model,
                                        args.size, args.steps, args.seed + num,
                                        args.style))
            elif args.backend == "qwen":
                entry.update(gen_qwen_one(p["keyword"], out))
            else:
                sys.exit(f"unknown backend '{args.backend}' "
                         f"(use assets | hf | qwen)")
        except Exception as e:
            log(f"[{i}/{len(todo)}] FAIL id {num} '{p['keyword'][:50]}': {e}")
            entry["error"] = str(e)[:300]
            images.append(entry)
            save_json(d / "images.json", images)
            continue
        secs = time.time() - t0
        log(f"[{i}/{len(todo)}] ok id {num} '{p['keyword'][:50]}' "
            f"-> {entry['file']} ({entry.get('license','')} "
            f"from {entry.get('source','?')}) in {secs:.1f}s")
        images.append(entry)
        save_json(d / "images.json", images)
    write_credits(d, images)
    log(f"done — {len(todo)} attempted. Re-run to retry failures; "
        f"`status` shows totals, `sheet` builds a contact sheet.")
    if args.sheet:
        cmd_sheet(args)


def cmd_status(args):
    d, prompts, images = ledgers(args.project)
    assets = d / "assets"
    done = done_ids(images, assets)
    print(f"project: {args.project}  queued: {len(prompts)}  "
          f"done: {len(done)}  failed: "
          f"{sum(1 for im in images if im.get('error'))}")
    for im in sorted(images, key=lambda x: x["id"]):
        mark = "ok " if not im.get("error") else "ERR"
        extra = im.get("source") or im.get("model", "")
        print(f"  [{mark}] {im['id']:>3} {im['file']:>16}  "
              f"{im['keyword'][:44]:44} {extra}")


def cmd_sheet(args):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("sheet needs Pillow: pip install Pillow")
    d, _, images = ledgers(args.project)
    assets = d / "assets"
    rows = [im for im in images if not im.get("error")]
    if not rows:
        print("no images to sheet")
        return
    thumb, gap, label = 300, 10, 22
    cols = 4
    n = len(rows)
    rows_n = (n + cols - 1) // cols
    W = cols * thumb + (cols + 1) * gap
    H = rows_n * (thumb + label) + (rows_n + 1) * gap
    sheet = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(rows):
        r, c = divmod(i, cols)
        x = gap + c * (thumb + gap)
        y = gap + r * (thumb + label + gap)
        try:
            img = Image.open(assets / im["file"].split("/")[-1])
            img.thumbnail((thumb, thumb))
            sheet.paste(img, (x + (thumb - img.width) // 2,
                              y + (thumb - img.height) // 2))
        except Exception:
            pass
        draw.text((x + 4, y + thumb + 3),
                  f"{im['id']:03d} {im['keyword'][:38]}",
                  fill="black")
    out = d / "contact-sheet.png"
    sheet.save(out)
    print(f"wrote {out} ({n} images)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="queue prompts for a project")
    p.add_argument("project")
    p.add_argument("--prompts", help="text file, one keyword/prompt per line")
    p.add_argument("--keywords", help="inline comma list")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("run", help="generate (resumes; --limit caps a run)")
    p.add_argument("project")
    p.add_argument("--backend", choices=["assets", "hf", "qwen"],
                   default="assets")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--delay", type=float, default=0.25,
                   help="assets backend: seconds between GitHub fetches")
    p.add_argument("--model", default=None, help="hf: diffusers model id")
    p.add_argument("--size", default="512x512", help="hf: WxH")
    p.add_argument("--steps", type=int, default=0,
                   help="hf: inference steps (0 = model default)")
    p.add_argument("--seed", type=int, default=42, help="hf: base seed")
    p.add_argument("--style", default=DOODLE_STYLE,
                   help="hf: style prefix for every prompt")
    p.add_argument("--sheet", action="store_true",
                   help="build contact-sheet.png when the run finishes")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("fill", help="server-side open-library fill of mapped beats")
    p.add_argument("project")
    p.add_argument("--map", default="open-map.json",
                   help="mapping file inside the project dir")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--delay", type=float, default=0.25)
    p.set_defaults(fn=cmd_fill)

    p = sub.add_parser("status", help="progress")
    p.add_argument("project")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("sheet", help="build contact-sheet.png")
    p.add_argument("project")
    p.set_defaults(fn=cmd_sheet)

    args = ap.parse_args()
    if args.cmd == "run":
        try:
            w, h = args.size.lower().split("x")
            args.size = (int(w), int(h))
        except Exception:
            sys.exit("--size must be WxH, e.g. 512x512")
    args.fn(args)


if __name__ == "__main__":
    main()
