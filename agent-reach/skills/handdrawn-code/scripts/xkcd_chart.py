#!/usr/bin/env python3
"""xkcd_chart.py — hand-drawn charts from a tiny JSON spec.

Uses matplotlib's xkcd mode (sketchy path effects) with real handwriting
fonts (Caveat / Patrick Hand / Kalam, OFL, shipped in ../fonts) so the output
looks hand-inked rather than comic-sans-y.

Usage:
    python3 xkcd_chart.py chart.json [--out name]

Chart JSON:
    {
      "kind": "bar",                       // bar | line | pie
      "width": 1376, "height": 768,        // default 16:9
      "bg": "#FFFFFF",
      "title": "WHAT PEOPLE SAW",
      "xlabel": "apparition", "ylabel": "percent",
      "labels": ["deformed", "monster", "stranger", "animal"],
      "values": [66, 48, 28, 18],
      "color": "#F2A63B",                  // optional accent
      "font": "caveat"                     // caveat | patrick | kalam
    }

Outputs: <name>.png (2x) and <name>.svg (pure vector, text as paths).
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE.parent / "fonts"

FONTS = {
    "caveat": FONT_DIR / "caveat-700.ttf",
    "patrick": FONT_DIR / "patrick-hand.ttf",
    "kalam": FONT_DIR / "kalam-700.ttf",
}
FONT_NAMES = {"caveat": "Caveat", "patrick": "Patrick Hand", "kalam": "Kalam"}

_registered = set()


def register_font(key):
    if key in _registered:
        return
    p = FONTS[key]
    font_manager.fontManager.addfont(str(p))
    _registered.add(key)


def style(key, bg):
    register_font(key)
    # xkcd sketchiness, but with our own handwriting font
    plt.rcParams.update({
        "path.sketch": (2.0, 120, 1),
        "font.family": FONT_NAMES[key],
        "text.color": "#16161a",
        "axes.edgecolor": "#16161a",
        "axes.linewidth": 2.2,
        "axes.labelcolor": "#16161a",
        "xtick.color": "#16161a",
        "ytick.color": "#16161a",
        "axes.facecolor": bg,
        "figure.facecolor": bg,
    })


def render(spec, out_name):
    kind = spec.get("kind", "bar")
    W = spec.get("width", 1376)
    H = spec.get("height", 768)
    bg = spec.get("bg", "#FFFFFF")
    ink = "#16161a"
    accent = spec.get("color", "#F2A63B")
    font = spec.get("font", "caveat")
    style(font, bg)

    fig, ax = plt.subplots(figsize=(W / 100, H / 100), dpi=200)

    if kind == "bar":
        labels = spec["labels"]
        values = spec["values"]
        colors = [accent if i == 0 else "#C9CED8" for i in range(len(values))]
        ax.bar(labels, values, color=colors, edgecolor=ink, linewidth=2.0,
               hatch="///")
        ax.set_ylim(0, max(values) * 1.22)
        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.02, f"{v}%", ha="center",
                    fontsize=20, family=FONT_NAMES[font])
        ax.tick_params(axis="x", labelsize=18)
        ax.tick_params(axis="y", labelsize=15)
    elif kind == "line":
        labels = spec["labels"]
        series = spec.get("series", [spec["values"]])
        for s in series:
            ax.plot(labels, s, color=accent, linewidth=3.4, marker="o",
                    markersize=10)
        ax.tick_params(labelsize=18)
    elif kind == "pie":
        vals = spec["values"]
        labels = spec["labels"]
        wedges, _ = ax.pie(vals, labels=None, startangle=90, counterclock=False,
                           wedgeprops={"edgecolor": ink, "linewidth": 2.2})
        from matplotlib.patches import Patch
        ax.legend(wedges, [f"{l} ({v}%)" for l, v in zip(labels, vals)],
                  loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False,
                  fontsize=20, prop={"family": FONT_NAMES[font]})
    else:
        sys.exit(f"unknown chart kind: {kind}")

    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=44, pad=24, family=FONT_NAMES[font],
                     fontweight="bold")
    if spec.get("xlabel"):
        ax.set_xlabel(spec["xlabel"], fontsize=24, family=FONT_NAMES[font])
    if spec.get("ylabel"):
        ax.set_ylabel(spec["ylabel"], fontsize=24, family=FONT_NAMES[font])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_linewidth(2.2)

    fig.tight_layout()
    fig.savefig(f"{out_name}.png", facecolor=bg)
    fig.savefig(f"{out_name}.svg", facecolor=bg)
    plt.close(fig)
    print(f"wrote {out_name}.png and {out_name}.svg ({W}x{H})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    spec = json.loads(Path(args.spec).read_text())
    out = args.out or args.spec.replace(".json", "")
    render(spec, out)
