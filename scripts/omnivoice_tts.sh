#!/usr/bin/env bash
# OmniVoice TTS helper for this workspace.
# Usage:
#   scripts/omnivoice_tts.sh "Hello, this is a test." out.wav
#   scripts/omnivoice_tts.sh --instruct "male, low pitch" "Hello." out.wav
#   scripts/omnivoice_tts.sh --ref-audio clip.wav --ref-text "the transcript" "Hello." out.wav
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/omnivoice-venv"
export PATH="$VENV/bin:$HOME/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-$ROOT/omnivoice-models}"
export PYTHONUNBUFFERED=1

if [[ ! -x "$VENV/bin/omnivoice-infer" ]]; then
  echo "OmniVoice venv missing. Recreate with:" >&2
  echo "  python3 -m venv omnivoice-venv && omnivoice-venv/bin/pip install -e ./OmniVoice" >&2
  exit 1
fi

INSTRUCT=""
REF_AUDIO=""
REF_TEXT=""
DEVICE="${OMNIVOICE_DEVICE:-cpu}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --instruct) INSTRUCT="$2"; shift 2 ;;
    --ref-audio) REF_AUDIO="$2"; shift 2 ;;
    --ref-text) REF_TEXT="$2"; shift 2 ;;
    --device) DEVICE="$2"; shift 2 ;;
    --) shift; break ;;
    -*) echo "unknown flag $1" >&2; exit 2 ;;
    *) break ;;
  esac
done

TEXT="${1:-}"
OUT="${2:-}"
if [[ -z "$TEXT" || -z "$OUT" ]]; then
  echo "usage: $0 [--instruct 'male, british accent'] [--ref-audio wav --ref-text txt] TEXT OUT.wav" >&2
  exit 2
fi

args=( --model k2-fsa/OmniVoice --text "$TEXT" --output "$OUT" --device "$DEVICE" --language en )
[[ -n "$INSTRUCT" ]] && args+=( --instruct "$INSTRUCT" )
[[ -n "$REF_AUDIO" ]] && args+=( --ref_audio "$REF_AUDIO" )
[[ -n "$REF_TEXT" ]] && args+=( --ref_text "$REF_TEXT" )

exec omnivoice-infer "${args[@]}"
