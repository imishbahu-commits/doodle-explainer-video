#!/usr/bin/env python3
"""ML background removal (U^2-Net) for frames whose subject color matches the
background — the case the connected-components / chroma keyers in
`spritesheet_to_animation.py` cannot handle.

Use this when the subject CANNOT be separated by color:
  - a white / pale / light-grey subject on a white or light background
    (the connected-components keyer removes large white regions, so it eats a
    white robot's body along with the background);
  - frames pulled from a real photo or VIDEO, where the background isn't a flat
    chroma you control (see Path C — `video_to_frames.py`).

It segments the subject by SHAPE, not color, with the U^2-Net matting model run
directly through onnxruntime — no `rembg` install required (rembg's numba /
pymatting / scikit-image chain doesn't build on every Python). The only
dependencies are onnxruntime, numpy and Pillow.

The model (~176 MB) is downloaded once and cached at
`~/.config/character-animation/u2net.onnx` (alongside the skill's key.env).
Override with --model or $CHARACTER_ANIM_U2NET.

After this, the frames are transparent PNGs — montage them into a sheet
(`magick montage ... -background none`, which PRESERVES each frame's position,
unlike frames_to_sheet.py) and finish with `spritesheet_to_animation.py --keep-bg`.

Usage:
  # a whole folder of frames -> a folder of cutouts
  python3 remove_bg_ml.py frames_raw/ frames_cut/
  # a single image
  python3 remove_bg_ml.py character.png character_cut.png
"""
import argparse, os, sys, urllib.request
from pathlib import Path

MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_MIN_BYTES = 50_000_000  # real model is ~176 MB; guard against HTML error pages
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def default_model_path():
    env = os.environ.get("CHARACTER_ANIM_U2NET")
    if env:
        return Path(env)
    return Path.home() / ".config" / "character-animation" / "u2net.onnx"


def ensure_model(path):
    path = Path(path)
    if path.exists() and path.stat().st_size >= MODEL_MIN_BYTES:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    sys.stderr.write(f"Downloading U^2-Net model (~176 MB) -> {path}\n")
    sys.stderr.flush()
    tmp = path.with_suffix(".part")
    urllib.request.urlretrieve(MODEL_URL, tmp)
    if tmp.stat().st_size < MODEL_MIN_BYTES:
        tmp.unlink(missing_ok=True)
        sys.exit("ERROR: model download failed (file too small / not the model).")
    tmp.replace(path)
    return path


def load_session(model_path):
    try:
        import onnxruntime as ort
    except ImportError:
        sys.exit("ERROR: onnxruntime is required (pip install onnxruntime).")
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(model_path), sess_options=so,
                                providers=["CPUExecutionProvider"])
    return sess, sess.get_inputs()[0].name


def predict_mask(sess, inp_name, img, size):
    import numpy as np
    from PIL import Image
    im = img.convert("RGB").resize((size, size), Image.LANCZOS)
    ary = np.array(im).astype("float32")
    ary = ary / max(1e-6, ary.max())
    tmp = np.zeros((size, size, 3), dtype="float32")
    for c in range(3):
        tmp[:, :, c] = (ary[:, :, c] - MEAN[c]) / STD[c]
    tmp = np.expand_dims(tmp.transpose(2, 0, 1), 0)
    pred = sess.run(None, {inp_name: tmp})[0][:, 0, :, :]
    mi, ma = pred.min(), pred.max()
    pred = np.squeeze((pred - mi) / max(1e-6, (ma - mi)))
    mask = Image.fromarray((pred * 255).astype("uint8"), mode="L")
    return mask.resize(img.size, Image.LANCZOS)


def cut_one(sess, inp_name, src, dst, size, lo, hi):
    import numpy as np
    from PIL import Image
    img = Image.open(src).convert("RGBA")
    mask = predict_mask(sess, inp_name, img, size)
    a = np.array(mask).astype("float32")
    # Levels on the alpha: stretch [lo,hi] -> [0,255], clamp outside. lo kills the
    # faint matte halo a near-same-color background leaves; hi keeps edges soft.
    a = np.clip((a - lo) / max(1e-6, (hi - lo)) * 255.0, 0, 255).astype("uint8")
    rgba = np.array(img)
    rgba[:, :, 3] = a
    Image.fromarray(rgba, "RGBA").save(dst)


def main():
    ap = argparse.ArgumentParser(description="U^2-Net ML background removal.")
    ap.add_argument("src", help="input image OR folder of frames")
    ap.add_argument("dst", help="output image OR folder")
    ap.add_argument("--model", default=None,
                    help="path to u2net.onnx (default: cached in "
                         "~/.config/character-animation, downloaded if absent)")
    ap.add_argument("--size", type=int, default=320,
                    help="model input size (default 320; U^2-Net native)")
    ap.add_argument("--alpha-floor", type=float, default=0.06,
                    help="alpha fraction below this -> fully transparent (kills halo)")
    ap.add_argument("--alpha-ceil", type=float, default=0.95,
                    help="alpha fraction above this -> fully opaque")
    args = ap.parse_args()

    model = ensure_model(args.model or default_model_path())
    sess, inp_name = load_session(model)
    lo, hi = args.alpha_floor * 255.0, args.alpha_ceil * 255.0

    src = Path(args.src)
    if src.is_dir():
        out_dir = Path(args.dst)
        out_dir.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in src.iterdir()
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")])
        if not files:
            sys.exit(f"no images in {src}")
        for i, f in enumerate(files):
            cut_one(sess, inp_name, f, out_dir / (f.stem + ".png"), args.size, lo, hi)
            print(f"  [{i+1}/{len(files)}] {f.name}", flush=True)
        print(f"done -> {out_dir} ({len(files)} cutouts)")
    else:
        dst = Path(args.dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        cut_one(sess, inp_name, src, dst, args.size, lo, hi)
        print(f"done -> {dst}")


if __name__ == "__main__":
    main()
