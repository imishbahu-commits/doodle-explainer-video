#!/usr/bin/env bash
# video-polish setup — the three checkers need only ffmpeg and Python 3,
# both already installed by the repository root setup. This script just
# verifies and reports usage.
set -euo pipefail

command -v ffmpeg >/dev/null || {
  echo "ffmpeg not found — run scripts/setup.sh at the repo root first" >&2
  exit 1
}
command -v python3 >/dev/null || {
  echo "Python 3 required" >&2
  exit 1
}

cat <<'EOF'
video-polish is ready (no new installs needed).

  script:   python3 scripts/script_doctor.py script.md [--json]
  audio:    python3 scripts/audio_report.py video.mp4 [--tighten out.m4a]
  pacing:   python3 scripts/qa_pacing.py final.mp4 [--manifest manifest.json]
EOF
