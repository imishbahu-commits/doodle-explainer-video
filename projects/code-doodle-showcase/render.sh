#!/usr/bin/env bash
# Render every scene + chart in this project with the handdrawn-code skill.
# Pure code — rough.js + matplotlib xkcd mode. No image model, no API key.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SKILL="$ROOT/skills/handdrawn-code"
OUT="$HERE/out"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY=python3

mkdir -p "$OUT"

for f in "$HERE"/scenes/*.json; do
  name="$(basename "$f" .json)"
  node "$SKILL/scripts/doodle.mjs" "$f" --out "$OUT/$name"
done

for f in "$HERE"/charts/*.json; do
  name="$(basename "$f" .json)"
  "$PY" "$SKILL/scripts/xkcd_chart.py" "$f" --out "$OUT/$name"
done

echo
echo "Rendered $(ls "$OUT"/*.png | wc -l) PNGs (+ matching SVGs) -> $OUT"
