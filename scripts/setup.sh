#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV:-$ROOT/.venv}"

command -v python3 >/dev/null || { echo "Python 3 is required" >&2; exit 1; }
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/pip" install -r "$ROOT/requirements.txt"

mkdir -p "$HOME/.local/bin"
if ! command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG_PATH="$($VENV/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
  ln -sfn "$FFMPEG_PATH" "$HOME/.local/bin/ffmpeg"
  echo "Installed a static ffmpeg fallback at $HOME/.local/bin/ffmpeg"
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  chmod +x "$ROOT/scripts/ffprobe_duration.py"
  ln -sfn "$ROOT/scripts/ffprobe_duration.py" "$HOME/.local/bin/ffprobe"
  echo "Installed the duration-probe fallback at $HOME/.local/bin/ffprobe"
fi

cat <<EOF
Setup complete.
Activate: source "$VENV/bin/activate"
Ensure local tools are visible: export PATH="\$HOME/.local/bin:\$PATH"
Check renderer: python scripts/build_video.py --help
EOF
