#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG = str(Path.home() / ".local/bin/ffmpeg")
FPS = 30
frames = [96, 140, 101, 159, 164, 183, 217, 126]
expressions = [
    ("min(1.06,1+0.06*on/76)", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
    ("min(1.12,1+0.12*on/12)", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
    ("1.045", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
    ("min(1.10,1+0.10*on/80)", "(iw-iw/zoom)*on/158", "ih/2-ih/zoom/2"),
    ("1.06", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
    ("max(1,1.12-0.12*on/110)", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
    ("if(lt(on,3),1+0.035*on,if(lt(on,6),1.105-0.025*(on-3),1.03))", "iw/2-iw/zoom/2+if(lt(on,6),6*sin(on*4),0)", "ih/2-ih/zoom/2+if(lt(on,6),4*cos(on*3),0)"),
    ("min(1.08,1+0.08*on/90)", "iw/2-iw/zoom/2", "ih/2-ih/zoom/2"),
]

work = ROOT / "work"
work.mkdir(parents=True, exist_ok=True)
segments = []
for index, (count, motion) in enumerate(zip(frames, expressions), 1):
    src = ROOT / "scenes/stills" / f"{index:02d}-"  # resolved below
    matches = sorted((ROOT / "scenes/stills").glob(f"{index:02d}-*.png"))
    if len(matches) != 1:
        raise SystemExit(f"expected one still for scene {index}, found {matches}")
    out = work / f"scene-{index:02d}.mp4"
    z, x, y = motion
    vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={count}:s=1920x1080:fps={FPS},format=yuv420p"
    subprocess.run([
        FFMPEG, "-y", "-i", str(matches[0]), "-vf", vf,
        "-frames:v", str(count), "-an", "-c:v", "libx264", "-preset", "medium",
        "-crf", "17", "-pix_fmt", "yuv420p", str(out)
    ], check=True)
    segments.append(out)

concat = work / "segments.txt"
concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segments), encoding="utf-8")
silent = work / "picture.mp4"
subprocess.run([
    FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
    "-c", "copy", str(silent)
], check=True)

final = ROOT / "expressive-tickle-sample.mp4"
subprocess.run([
    FFMPEG, "-y", "-i", str(silent), "-i", str(ROOT / "audio/voiceover.mp3"),
    "-filter:a", "loudnorm=I=-20.28:LRA=3.5:TP=-2.3",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
    str(final)
], check=True)
print(final)
