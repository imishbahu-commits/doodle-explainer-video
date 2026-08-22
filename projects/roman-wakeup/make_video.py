#!/usr/bin/env python3
"""Assemble "You Wake Up in Ancient Rome" to the user's measured style.

Measured profile (stylehub profile 91d967adab, from the user's reference
15289.mp4):
  - 1920x1080, 30 fps, white canvas, 6 px near-black contour @1920, earthy flat palette
  - hard cuts only; cut lands ~0.055 s before the spoken word (73% before word)
  - ~35% of shots are slow zoom-ins at ~1%/s; ~3.8 s median shot; pose-swap character pops
  - 160-173 WPM narration, chapter breaths ~0.6 s
  - mix: integrated -18.6 LUFS, true peak <= -2.3 dBTP, quiet low ambient bed

Run:  .venv/bin/python projects/roman-wakeup/make_video.py
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "projects" / "roman-wakeup"
ASSETS = PROJ / "assets"
AUDIO = PROJ / "audio"
WORK = PROJ / "work"
FF = imageio_ffmpeg.get_ffmpeg_exe()

W, H, FPS = 1920, 1080, 30
BREATH = 0.60          # s between chapters
CUT_LEAD = 0.055       # s before word onset
ZOOM_PCT_PER_S = 1.0   # measured median 0.93 %/s
ZOOM_MAX = 1.06
LUFS, TP = -18.6, -2.3

# Each chapter: clip file + sentences with (spoken text, plate, mode).
# mode: wide | zoom(crop) | char(pose) | hold (no cut - extend previous shot)
CHAPTERS = [
    ("01-hook", [
        ("You open your eyes.", "rome-street", "wide"),
        ("You're in ancient Rome, and no, you're not the emperor.", "rome-street", "hold"),
        ("You're one of a million people stacked inside apartment blocks so badly built, they collapse for fun.", "rome-street", "zoom:upper"),
        ("Welcome to the year one seventeen.", "character-neutral", "char"),
    ]),
    ("02-home", [
        ("Your home is an insula. Seven floors.", "insula-room", "wide"),
        ("The rich live at the bottom. You live at the top, where the walls are thinnest and the rent is cheapest.", "insula-room", "zoom:window"),
        ("There's no kitchen. No toilet. One room.", "character-shocked", "char"),
        ("And if the building burns, you're the last one to find out.", "character-shocked", "hold"),
    ]),
    ("03-breakfast", [
        ("Breakfast is bread. Maybe some olives, if you're lucky.", "breakfast", "wide"),
        ("No coffee. That hasn't been invented yet.", "breakfast", "zoom:flies"),
        ("You eat standing up, because chairs are for people with money.", "character-neutral", "char"),
    ]),
    ("04-work", [
        ("You're a porter at the grain market. All day, you haul sacks. The pay is one loaf a day.", "grain-market", "wide"),
        ("But at least there's the public toilet. A long bench with holes.", "latrine", "wide"),
        ("And the sponge on a stick. Shared. By everyone. Good luck.", "latrine", "zoom:sponge"),
    ]),
    ("05-baths", [
        ("After work, the baths. You pay a quarter coin.", "baths", "wide"),
        ("For that, you get hot water, cold water, and gossip.", "baths", "zoom:pool"),
        ("The rich sweat in their own rooms. You get the big pool. Not bad.", "baths", "hold"),
    ]),
    ("06-games", [
        ("On holidays, the Colosseum opens. Free entry. Free bread.", "colosseum", "wide"),
        ("You sit at the very top, a hundred meters from the sand.", "colosseum", "zoom:arena"),
        ("You can't see the fights. But you can feel the crowd.", "colosseum", "hold"),
    ]),
    ("07-health", [
        ("Got a fever? The doctor will balance your four humors. Maybe with leeches.", "doctor", "wide"),
        ("The water pipes are lead.", "doctor", "zoom:pipe"),
        ("The average Roman lives to about thirty-five. So enjoy the bread.", "character-shocked", "char"),
    ]),
    ("08-outro", [
        ("And yet, they built aqueducts that still stand. Roads we still drive on. Laws we still quote.", "rome-street", "zoom:center"),
        ("You woke up in the wrong century.", "character-neutral", "char"),
        ("But not the wrong civilization.", "rome-street", "wide"),
    ]),
]

# zoom crops: (normalized center x, y, crop width fraction)
CROPS = {
    "upper": (0.50, 0.28, 0.85),
    "window": (0.50, 0.38, 0.80),
    "flies": (0.50, 0.45, 0.80),
    "sponge": (0.68, 0.50, 0.70),
    "pool": (0.50, 0.52, 0.75),
    "arena": (0.50, 0.45, 0.80),
    "pipe": (0.68, 0.50, 0.70),
    "center": (0.50, 0.50, 0.80),
}


def run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(args[:6])}...\n{proc.stderr[-800:]}")


def duration(path: Path) -> float:
    proc = subprocess.run([FF, "-hide_banner", "-i", str(path)],
                          capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr)
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def prep_plates() -> None:
    """Composite every plate onto the white 1920x1080 canvas; build zoom crops."""
    (WORK / "plates").mkdir(parents=True, exist_ok=True)
    for plate in sorted(ASSETS.glob("*.png")):
        img = Image.open(plate).convert("RGB")
        canvas = Image.new("RGB", (W, H), (240, 240, 240))
        if img.width / img.height >= 1.6:  # wide plate: cover-fit
            scale = max(W / img.width, H / img.height)
        else:  # portrait character: height ~62% of frame, centered
            scale = 0.62 * H / img.height
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        canvas.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
        canvas.save(WORK / "plates" / f"{plate.stem}-full.png")

    for name, (cx, cy, cw) in CROPS.items():
        pass  # crops are built lazily per shot via zoom_input()


def zoom_input(plate: str, crop: str) -> Path:
    src = ASSETS / f"{plate}.png"
    cx, cy, cw = CROPS[crop]
    img = Image.open(src).convert("RGB")
    ch = cw * img.height / img.width * (W / H)
    left = max(0, int((cx - cw / 2) * img.width))
    top = max(0, int((cy - ch / 2) * img.height))
    right = min(img.width, int((cx + cw / 2) * img.width))
    bottom = min(img.height, int((cy + ch / 2) * img.height))
    region = img.crop((left, top, right, bottom))
    region = region.resize((2 * W, 2 * H), Image.LANCZOS)
    out = WORK / "plates" / f"{plate}-{crop}-zoom.png"
    region.save(out)
    return out


def render_shot(index: int, plate: str, mode: str, dur_s: float) -> Path:
    frames = max(2, round(dur_s * FPS))
    out = WORK / f"shot-{index:03d}.mp4"
    if mode.startswith("zoom:"):
        source = zoom_input(plate, mode.split(":", 1)[1])
        zinc = f"{ZOOM_PCT_PER_S / 100.0 / FPS:.6f}"
        run([FF, "-hide_banner", "-loglevel", "error", "-y",
             "-loop", "1", "-framerate", str(FPS), "-i", str(source),
             "-vf", (f"zoompan=z='min(1+{zinc}*on,{ZOOM_MAX})'"
                     f":x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
                     f":d={frames}:s={W}x{H}:fps={FPS}"),
             "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", str(out)])
    else:
        source = WORK / "plates" / f"{plate}-full.png"
        run([FF, "-hide_banner", "-loglevel", "error", "-y",
             "-loop", "1", "-framerate", str(FPS), "-i", str(source),
             "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", str(out)])
    return out


def sentence_times(chapter: tuple[str, list], clip_dur: float) -> list[float]:
    """Approximate word timings by proportional interpolation inside the clip."""
    _, sentences = chapter
    total_chars = sum(len(text) for text, _, _ in sentences)
    starts = []
    acc = 0.0
    for text, _, _ in sentences:
        starts.append(acc / total_chars * clip_dur)
        acc += len(text)
    return starts


def main() -> None:
    WORK.mkdir(exist_ok=True)
    prep_plates()

    # ---- timing: chapter starts, cut points, shot plan
    chapters_start: dict[str, float] = {}
    clips: dict[str, tuple[str, float]] = {}
    t = 0.0
    for name, sentences in CHAPTERS:
        chapters_start[name] = t
        clips[name] = (name, t)
        t += duration(AUDIO / f"{name}.mp3") + BREATH
    total_dur = t - BREATH

    shots: list[dict] = []
    for name, sentences in CHAPTERS:
        clip_dur = duration(AUDIO / f"{name}.mp3")
        starts = sentence_times((name, sentences), clip_dur)
        for (text, plate, mode), rel in zip(sentences, starts):
            cut_at = chapters_start[name] + max(0.0, rel - CUT_LEAD)
            if mode == "hold" and shots:
                continue  # no cut: the previous shot keeps running
            shots.append({
                "shot": len(shots) + 1,
                "plate": plate,
                "mode": mode,
                "start": round(cut_at, 4),
                "end": round(cut_at + 1.0, 4),  # fixed below
                "sentence": text,
                "chapter": name,
            })
    for i, shot in enumerate(shots):
        end = shots[i + 1]["start"] if i + 1 < len(shots) else total_dur
        shot["end"] = round(end, 4)
    shots = [s for s in shots if s["end"] - s["start"] >= 0.12]

    # ---- render shots
    print(f"rendering {len(shots)} shots over {total_dur:.1f} s")
    rendered = []
    for i, shot in enumerate(shots, 1):
        rendered.append(render_shot(i, shot["plate"], shot["mode"],
                                    shot["end"] - shot["start"]))
        if i % 8 == 0:
            print(f"  {i}/{len(shots)}")

    # ---- concat video
    concat_list = WORK / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in rendered),
                           encoding="utf-8")
    video_silent = WORK / "video-silent.mp4"
    run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(video_silent)])

    # ---- narration track with chapter breaths
    (WORK / "wav").mkdir(exist_ok=True)
    silence = WORK / "wav" / "silence.wav"
    run([FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"aevalsrc=0:d={BREATH}", str(silence)])
    audio_list = WORK / "audio.txt"
    lines = []
    for name, _ in CHAPTERS:
        wav = WORK / "wav" / f"{name}.wav"
        lines.append(f"file '{wav.resolve()}'\nfile '{silence.resolve()}'\n")
    audio_list.write_text("".join(lines), encoding="utf-8")
    for name, _ in CHAPTERS:
        run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i",
             str(AUDIO / f"{name}.mp3"), "-ar", "48000", "-ac", "2",
             str(WORK / "wav" / f"{name}.wav")])
    narration = WORK / "narration.wav"
    run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(audio_list), "-c", "copy", str(narration)])

    # ---- quiet low ambient bed (fifths drone), mixed under the voice
    bed = WORK / "bed.wav"
    expr = ("0.030*(0.6+0.4*sin(0.11*2*PI*t))*sin(2*PI*110*t)"
            "+0.020*(0.6+0.4*sin(0.07*2*PI*t))*sin(2*PI*164.81*t)"
            "+0.014*(0.6+0.4*sin(0.13*2*PI*t))*sin(2*PI*220*t)")
    run([FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"aevalsrc={expr}:s=48000:d={total_dur:.3f}",
         "-af", "lowpass=f=500", str(bed)])
    mix = WORK / "mix.wav"
    run([FF, "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(narration), "-i", str(bed),
         "-filter_complex",
         f"[0:a]aformat=channel_layouts=stereo,apad,atrim=0:{total_dur:.3f}[n];"
         f"[1:a]atrim=0:{total_dur:.3f},aformat=channel_layouts=stereo[b];"
         f"[n][b]amix=inputs=2:duration=longest:normalize=0,"
         f"loudnorm=I={LUFS}:TP={TP}:LRA=11[a]",
         "-map", "[a]", "-ar", "48000", str(mix)])

    # ---- mux final
    final = PROJ / "final.mp4"
    run([FF, "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(video_silent), "-i", str(mix),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "160k", "-movflags", "+faststart", str(final)])

    # ---- ledger
    beats = {
        "style_profile": "stylehub/profiles/91d967adab/style_rules.json (user reference 15289.mp4)",
        "video": {"duration_seconds": round(total_dur, 3), "width": W, "height": H, "fps": FPS},
        "shots": shots,
        "stats": {
            "shot_count": len(shots),
            "median_shot_seconds": round(sorted(
                s["end"] - s["start"] for s in shots)[len(shots) // 2], 3),
            "zoom_shot_pct": round(sum(1 for s in shots if s["mode"].startswith("zoom"))
                                    / len(shots) * 100, 1),
            "chapter_breath_seconds": BREATH,
            "cut_lead_seconds": CUT_LEAD,
            "mix_targets": {"lufs": LUFS, "true_peak": TP},
        },
    }
    (PROJ / "beats.json").write_text(json.dumps(beats, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    print(f"\ndone -> {final.relative_to(ROOT)}")
    print(json.dumps(beats["stats"], indent=2))


if __name__ == "__main__":
    main()
