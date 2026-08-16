#!/usr/bin/env bash
# Setup for the handdrawn-code skill: rough.js renderer (Node) + xkcd chart
# renderer (Python) + handwriting fonts (OFL, via fontsource on npm).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v node >/dev/null || { echo "Node.js is required" >&2; exit 1; }

echo "==> npm deps (roughjs, resvg-js)"
(cd "$ROOT" && npm install --no-audit --no-fund)

echo "==> handwriting fonts (fontsource -> ttf)"
FONTS="$ROOT/fonts"
mkdir -p "$FONTS"
PY="python3"
if [ -d "$ROOT/../../.venv" ]; then PY="$ROOT/../../.venv/bin/python"; fi
"$PY" -m pip install -q fonttools 2>/dev/null || "$PY" -m pip install --user -q fonttools
(
cd "$ROOT"
"$PY" - <<'EOF'
from fontTools.ttLib import TTFont
import os
pairs = [
    ("node_modules/@fontsource/caveat/files/caveat-latin-700-normal.woff2", "fonts/caveat-700.ttf"),
    ("node_modules/@fontsource/caveat/files/caveat-latin-600-normal.woff2", "fonts/caveat-600.ttf"),
    ("node_modules/@fontsource/patrick-hand/files/patrick-hand-latin-400-normal.woff2", "fonts/patrick-hand.ttf"),
    ("node_modules/@fontsource/kalam/files/kalam-latin-700-normal.woff2", "fonts/kalam-700.ttf"),
]
for src, dst in pairs:
    if os.path.exists(dst): continue
    f = TTFont(src); f.flavor = None; f.save(dst)
    print("font:", dst)
EOF
)

echo "==> python deps (matplotlib for charts)"
"$PY" -m pip install -q matplotlib

cat <<EOF
Setup complete.

Scene doodles:   node scripts/doodle.mjs examples/brain-prediction.json --out out/demo
Hand-drawn chart: $PY scripts/xkcd_chart.py examples/mirror-study.json --out out/chart
EOF
