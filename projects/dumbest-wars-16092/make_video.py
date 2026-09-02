#!/usr/bin/env python3
"""Render beats of History's Dumbest Wars.
RULE (user's): one image per beat; image duration = that beat's VO length + 0.15s tail.
NEVER stretch an image to cover a longer VO. Hard cuts only, locked camera (ref style).
Usage:
  make_video.py <part>          -> all beats with that part label (script.py)
  make_video.py <lo> <hi>       -> exact beat range, e.g. 11 20
"""
import sys, subprocess, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from script import BEATS

FPS = 30
W, H = 1280, 720
TAIL = 0.15          # small measured-style tail after VO end (ref: cut ~VO end)
GAP = 0.05           # tiny breath before next VO

def probe(path):
    out = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                   "-of","csv=p=0", str(path)]).decode().strip()
    return float(out)

def main() -> None:
    if len(sys.argv) >= 3:
        lo, hi = int(sys.argv[1]), int(sys.argv[2])
        beats = [b for b in BEATS if lo <= b["n"] <= hi]
        out = Path(f"dumbest_wars_part{lo}-{hi}.mp4")
    else:
        part = int(sys.argv[1])
        beats = [b for b in BEATS if b["part"] == part]
        out = Path(f"dumbest_wars_part{part}.mp4")
    assets = Path("assets"); audio = Path("audio"); tmp = Path("tmp"); tmp.mkdir(exist_ok=True)
    beats = sorted(beats, key=lambda b: b["n"])
    if not beats:
        print("no beats in range"); return
    segs = []
    cursor = 0.0
    manifest = []
    for b in beats:
        img = assets / f"beat{b['n']:02d}.png"
        wav = audio / f"beat{b['n']:02d}.wav"
        if not img.exists() or not wav.exists():
            print(f"MISSING beat{b['n']:02d} asset — aborting (nothing stretched, per rule)")
            return
        d = probe(wav)
        hold = d + TAIL
        seg = tmp / f"seg{b['n']:02d}.mp4"
        subprocess.run(["ffmpeg","-y","-loglevel","error",
                        "-loop","1","-i",str(img),
                        "-i",str(wav),
                        "-t",f"{hold:.3f}",
                        "-vf",f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                        "-af","apad",
                        "-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","20",
                        "-c:a","aac","-b:a","192k","-ar","44100","-ac","2",
                        str(seg)])
        segs.append(seg)
        manifest.append(dict(n=b["n"], vo=d, hold=hold, start=cursor,
                             end=cursor+hold, text=b["text"]))
        cursor += hold + GAP
        print(f"beat{b['n']:02d}: vo={d:.2f}s hold={hold:.2f}s", flush=True)
    listf = tmp / "list.txt"
    listf.write_text("\n".join(f"file '{s.resolve()}'" for s in segs))
    Path(f"manifest_{out.stem}.json").write_text(json.dumps(manifest, indent=1))
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0",
                    "-i",str(listf),"-c","copy",str(out)])
    print(f"RENDER DONE: {out} ({out.stat().st_size/1e6:.1f} MB, {cursor:.1f}s)")

if __name__ == "__main__":
    main()
