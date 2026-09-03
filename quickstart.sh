#!/usr/bin/env bash
# QUICKSTART — restore the sandbox after any reset in ONE command (~15s)
#   bash quickstart.sh      -> rebuilds .venv + ffmpeg symlink
# (Servers must be started with the platform process tool, e.g.:
#   python3 tools/style_lab.py 8080        -> upload studio
#   python3 projects/dinzo-samples/studio.py "samples" 8081 )
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt numpy 2>&1 | tail -1
fi
FF=$(.venv/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null)
ln -sf "$FF" .venv/bin/ffmpeg 2>/dev/null || true
echo "READY — .venv rebuilt. Start servers with the process tool."
