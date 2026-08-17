#!/usr/bin/env bash
# Build a clean zip of THIS fork's current branch (tracked files only, no .git).
# Usage: ./scripts/make_fork_zip.sh [output.zip]
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
OUT="${1:-doodle-explainer-video-fork.zip}"

git archive --format=zip -o "$OUT" HEAD
echo "Built $OUT from fork branch: $BRANCH"
ls -lh "$OUT"
