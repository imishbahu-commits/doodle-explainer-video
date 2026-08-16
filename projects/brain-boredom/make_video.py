#!/usr/bin/env python3
"""Render the 60-second hand-drawn explainer from generated PNG assets."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parent
RENDERER = ROOT / "skills/ae-motion/scripts/ae_motion.py"
PYTHON = ROOT / ".venv/bin/python"
FPS = 60
SCENE_DURATION = 10.0

SHOTS = [
    ("01_hook.png", "WHY BOREDOM HELPS", 1.04, 0.945, (640, 360), (640, 360)),
    ("02_default_mode.png", "YOUR BRAIN SWITCHES JOBS", 0.945, 1.025, (650, 365), (630, 350)),
    ("03_brain_network.png", "MEMORY + FUTURE + IDEAS", 0.955, 1.02, (655, 360), (625, 360)),
    ("04_shower_idea.png", "AHA!", 0.95, 1.055, (640, 365), (640, 350)),
    ("05_phone_loop.png", "LEAVE SPACE TO THINK", 1.025, 0.95, (640, 360), (640, 360)),
    ("06_ten_minute.png", "TRY TEN QUIET MINUTES", 0.95, 1.025, (650, 365), (630, 350)),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    (PROJECT / "scenes").mkdir(exist_ok=True)
    (PROJECT / "clips").mkdir(exist_ok=True)
    env_path = os.environ.get("PATH", "")
    ffmpeg_dir = str(Path.home() / ".local/bin")
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + env_path

    clips: list[Path] = []
    for i, (asset, label, start_scale, end_scale, start_pos, end_pos) in enumerate(SHOTS, 1):
        scene = {
            "width": 1280,
            "height": 720,
            "fps": FPS,
            "duration": SCENE_DURATION,
            "bg_color": [247, 243, 232, 255],
            "motion_blur": 1,
            "layers": [
                {
                    "type": "image",
                    "src": str(PROJECT / "assets" / asset),
                    "isolate": False,
                    "tracks": {
                        "pos": [
                            {"t": 0.0, "v": list(start_pos), "e": "hold"},
                            {"t": 10.0, "v": list(end_pos), "e": "easeInOut"},
                        ],
                        "scale": [
                            {"t": 0.0, "v": start_scale, "e": "hold"},
                            {"t": 10.0, "v": end_scale, "e": "easeInOut"},
                        ],
                    },
                },
                {
                    "type": "text",
                    "text": label,
                    "size": 50 if len(label) > 18 else 62,
                    "font": "hand-bold",
                    "tracks": {
                        "pos": [{"t": 0.0, "v": [640, 76], "e": "hold"}],
                        "scale": [
                            {"t": 0.0, "v": 0.65, "e": "hold"},
                            {"t": 0.55, "v": 1.0, "e": "easeOutBack"},
                        ],
                        "opacity": [
                            {"t": 0.0, "v": 0.0, "e": "hold"},
                            {"t": 0.18, "v": 1.0, "e": "easeOut"},
                            {"t": 8.8, "v": 1.0, "e": "hold"},
                            {"t": 9.35, "v": 0.0, "e": "easeIn"},
                        ],
                    },
                },
            ],
        }
        scene_path = PROJECT / "scenes" / f"scene_{i:02d}.json"
        clip_path = PROJECT / "clips" / f"scene_{i:02d}.mp4"
        scene_path.write_text(json.dumps(scene, indent=2) + "\n")
        run([str(PYTHON), str(RENDERER), str(scene_path), "-o", str(clip_path)])
        clips.append(clip_path)

    concat = PROJECT / "clips.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips))
    output = PROJECT / "brain-boredom-60s.mp4"
    narration = PROJECT / "audio/narration.mp3"
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(narration),
        "-filter_complex",
        "[1:a]adelay=1030|1030,apad=pad_dur=2.1,atrim=duration=60,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-t", "60", "-movflags", "+faststart", str(output),
    ])
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
