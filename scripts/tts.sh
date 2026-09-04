#!/usr/bin/env bash
# Lightweight Piper TTS for this sandbox (CPU, no GPU).
# Usage:
#   scripts/tts.sh "Hello there." out.wav
#   scripts/tts.sh --voice en_US-joe-medium "Hello." out.wav
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/tts-venv"
VOICES="$ROOT/tts-voices"
VOICE="en_US-lessac-medium"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --voice|-v) VOICE="$2"; shift 2 ;;
    --list) ls -1 "$VOICES"/*.onnx 2>/dev/null | xargs -n1 basename | sed 's/.onnx$//'; exit 0 ;;
    --) shift; break ;;
    -*) echo "unknown flag $1" >&2; exit 2 ;;
    *) break ;;
  esac
done

TEXT="${1:-}"
OUT="${2:-}"
if [[ -z "$TEXT" || -z "$OUT" ]]; then
  echo "usage: $0 [--voice NAME] TEXT OUT.wav" >&2
  echo "voices:" >&2
  ls -1 "$VOICES"/*.onnx 2>/dev/null | xargs -n1 basename | sed 's/.onnx$//' >&2
  exit 2
fi

MODEL="$VOICES/${VOICE}.onnx"
CFG="$VOICES/${VOICE}.onnx.json"
if [[ ! -f "$MODEL" ]]; then
  echo "missing voice $VOICE  ($MODEL)" >&2
  exit 1
fi

printf '%s\n' "$TEXT" | "$VENV/bin/piper" --model "$MODEL" --config "$CFG" -f "$OUT"
echo "wrote $OUT"
