#!/usr/bin/env python3
"""Assemble a 3-band doodle explainer video.

Reads a manifest JSON describing a banner and a list of sections. Each section
carries ONE narration audio file plus the beats (illustrations) that play over
it. Beat timings are derived from the section's measured duration, weighted by
character count.

Voiceover is billed per 1,000 characters started, so narrate a whole section in
one call rather than one call per beat.

The bottom band is left empty black by default. Pass --captions to burn in
karaoke captions instead.

Usage:
    python3 build_video.py manifest.json [--workdir build] [--keep]
    python3 build_video.py manifest.json --captions
    python3 build_video.py manifest.json --music bed.mp3 --music-db -26

Manifest shape (see manifest_example.json):
    {
      "output": "final.mp4",
      "banner": "assets/banner.png",          # path or https URL
      "sections": [
        {
          "audio": "audio/01.mp3",
          "beats": [
            {"image": "assets/001.png", "text": "Imagine you are floating."},
            {"image": "assets/002.png", "text": "The water is dark and cold."}
          ]
        }
      ]
    }

A flat {"beats": [{image, audio, text}, ...]} manifest also works; each beat is
then treated as its own single-beat section.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image

# ---------------------------------------------------------------- format spec
# Every number below was measured off the reference video.
W, H = 720, 1280
BANNER_H = 420          # band A: y 0..420    static clickbait banner
ART_H = 420             # band B: y 420..840  illustration
CAPTION_TOP = 840       # band C: y 840..1280 captions on pure black
CAPTION_CENTER_Y = 996  # caption block is centred here for any line count
CAPTION_BG = (0, 0, 0)
FPS = 30

# Arial Black at 75 renders a 40px cap height; the reference holds a tight
# 56px baseline pitch. Lines are positioned explicitly, so the pitch does not
# depend on libass' default leading.
FONT_SIZE = 75
LINE_PITCH = 56
COLOR_WHITE = "&H00FFFFFF"
COLOR_HIGHLIGHT = "&H0008FFC1"   # #C1FF08 lime; ASS is &H00BBGGRR
OUTLINE = 0

MAX_WORDS_PER_CARD = 4
MAX_CHARS_PER_CARD = 26
MAX_CHARS_PER_LINE = 15

FONT_CANDIDATES = [
    "Montserrat ExtraBold", "Montserrat Black", "Poppins Black",
    "Arial Black", "Impact", "Helvetica Bold", "DejaVu Sans Bold",
]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "did", "do", "does", "for", "from", "had", "has", "have", "he", "her",
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just",
    "me", "might", "my", "no", "not", "of", "on", "or", "our", "out", "over",
    "she", "so", "some", "than", "that", "the", "their", "them", "then",
    "there", "these", "they", "this", "to", "up", "us", "was", "we", "were",
    "what", "when", "which", "who", "why", "will", "with", "you", "your",
}


def run(cmd, **kw):
    proc = subprocess.run([str(c) for c in cmd], capture_output=True,
                          text=True, **kw)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(str(c) for c in cmd)}\n"
                           f"{proc.stderr[-2000:]}")
    return proc.stdout


def resolve_font():
    """First installed family wins; fc-list reports nothing for absent ones."""
    for name in FONT_CANDIDATES:
        try:
            if run(["fc-list", name]).strip():
                return name
        except (RuntimeError, FileNotFoundError):
            continue
    if Path("/System/Library/Fonts/Supplemental/Arial Black.ttf").exists():
        return "Arial Black"
    return "Arial Black"


def fetch(src, dest_dir, stem, base=None):
    """Local path for src, downloading first when it is an https URL.

    Relative paths resolve against the manifest's directory, so a manifest is
    portable regardless of the caller's working directory.
    """
    if str(src).startswith(("http://", "https://")):
        suffix = Path(str(src).split("?")[0]).suffix or ".bin"
        dest = dest_dir / f"{stem}{suffix}"
        if not dest.exists():
            urllib.request.urlretrieve(src, dest)
        return dest
    path = Path(src).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    if not path.exists():
        raise FileNotFoundError(f"missing asset: {src} (resolved to {path})")
    return path


def audio_duration(path):
    return float(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", path,
    ]).strip())


def fit_band(img, width, height):
    """Scale to cover, then centre-crop — never letterbox."""
    img = img.convert("RGB")
    scale = max(width / img.width, height / img.height)
    new = img.resize((max(1, round(img.width * scale)),
                      max(1, round(img.height * scale))), Image.LANCZOS)
    left, top = (new.width - width) // 2, (new.height - height) // 2
    return new.crop((left, top, left + width, top + height))


def compose_frame(banner_img, art_path, dest):
    frame = Image.new("RGB", (W, H), CAPTION_BG)
    frame.paste(banner_img, (0, 0))
    frame.paste(fit_band(Image.open(art_path), W, ART_H), (0, BANNER_H))
    frame.save(dest, "PNG")


# ------------------------------------------------------------------ captions
def split_cards(text):
    """Group narration into caption cards of 3-4 words, breaking on clauses."""
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    cards, current = [], []
    for word in words:
        candidate = current + [word]
        if current and (len(candidate) > MAX_WORDS_PER_CARD
                        or len(" ".join(candidate)) > MAX_CHARS_PER_CARD):
            cards.append(current)
            current = [word]
        else:
            current = candidate
        if current and current[-1][-1] in ".,!?;:—":
            cards.append(current)
            current = []
    if current:
        cards.append(current)
    return cards


def pick_highlight(card):
    """Index of the word to render lime — the longest non-stopword."""
    best, best_len = 0, -1
    for i, word in enumerate(card):
        bare = re.sub(r"[^A-Za-z0-9'-]", "", word).lower()
        if bare and bare not in STOPWORDS and len(bare) > best_len:
            best, best_len = i, len(bare)
    return best if best_len > 0 else 0


def wrap_lines(card, highlight_idx):
    """Wrap a card to <=3 lines, tagging the highlight word inline."""
    lines, current, current_plain = [], [], []
    for i, word in enumerate(card):
        upper = word.upper()
        tagged = (f"{{\\c{COLOR_HIGHLIGHT}}}{upper}{{\\c{COLOR_WHITE}}}"
                  if i == highlight_idx else upper)
        if current and len(" ".join(current_plain + [upper])) > MAX_CHARS_PER_LINE:
            lines.append(" ".join(current))
            current, current_plain = [tagged], [upper]
        else:
            current.append(tagged)
            current_plain.append(upper)
    if current:
        lines.append(" ".join(current))
    return lines[:3]


def ass_time(seconds):
    seconds = max(0.0, seconds)
    h, m = int(seconds // 3600), int((seconds % 3600) // 60)
    return f"{h}:{m:02d}:{seconds % 60:05.2f}"


def build_ass(beats, font, dest):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{FONT_SIZE},{COLOR_WHITE},{COLOR_WHITE},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{OUTLINE},0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for beat in beats:
        cards = split_cards(beat["text"])
        if not cards:
            continue
        weights = [max(1, len(" ".join(c))) for c in cards]
        total = sum(weights)
        cursor = beat["start"]
        for card, weight in zip(cards, weights):
            span = beat["duration"] * weight / total
            lines = wrap_lines(card, pick_highlight(card))
            # One event per line so pitch matches the reference exactly.
            for i, line in enumerate(lines):
                y = round(CAPTION_CENTER_Y
                          + (i - (len(lines) - 1) / 2) * LINE_PITCH)
                events.append(
                    f"Dialogue: 0,{ass_time(cursor)},{ass_time(cursor + span)},"
                    f"Caption,,0,0,0,,{{\\an5\\pos({W // 2},{y})}}{line}")
            cursor += span
    dest.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- manifest
def normalise(manifest):
    """Accept either the sections form or the flat beats form."""
    if "sections" in manifest:
        return manifest["sections"]
    if "beats" in manifest:
        return [{"audio": b["audio"],
                 "beats": [{"image": b["image"], "text": b["text"]}]}
                for b in manifest["beats"]]
    raise ValueError("manifest needs either 'sections' or 'beats'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--workdir", default="build")
    ap.add_argument("--keep", action="store_true",
                    help="keep intermediate frames and padded audio")
    ap.add_argument("--gap", type=float, default=0.35,
                    help="silence appended after each section, seconds")
    ap.add_argument("--music", help="optional background bed (reference has none)")
    ap.add_argument("--music-db", type=float, default=-26.0,
                    help="bed level in dBFS; keep it far under the narration")
    ap.add_argument("--captions", action="store_true",
                    help="burn karaoke captions into the bottom band; "
                         "off by default, which leaves the band empty black")
    ap.add_argument("--tempo", type=float, default=1.0,
                    help="speed up narration, pitch preserved. TTS delivers "
                         "~155 wpm but the format wants ~217, so 1.4 is the "
                         "usual value for matching the reference pacing")
    ap.add_argument("--no-normalize", action="store_true",
                    help="skip loudness normalisation; raw TTS lands ~5 dB "
                         "under the reference, which reads as quiet on social")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text())
    base = manifest_path.parent
    sections = normalise(manifest)

    work = (base / args.workdir).resolve()
    dl, frames = work / "downloads", work / "frames"
    for d in (work, dl, frames):
        d.mkdir(parents=True, exist_ok=True)

    if args.captions:
        font = resolve_font()
        print(f"captions on, font: {font}")
    else:
        font = None
        print("captions off — bottom band stays empty")

    banner_src = fetch(manifest["banner"], dl, "banner", base)
    banner_img = fit_band(Image.open(banner_src), W, BANNER_H)

    beats, parts = [], []
    cursor = 0.0
    n_beats = sum(len(s["beats"]) for s in sections)
    idx = 0

    for si, section in enumerate(sections, start=1):
        audio = fetch(section["audio"], dl, f"sec_{si:03d}", base)
        # Speed up to the format's brisk rate, then pad with a breath so a
        # section's visuals cover its narration. atempo preserves pitch.
        padded = work / f"pad_{si:03d}.m4a"
        af = (f"atempo={args.tempo}," if args.tempo != 1.0 else "")
        run(["ffmpeg", "-y", "-v", "error", "-i", audio,
             "-af", f"{af}apad=pad_dur={args.gap},aresample=44100",
             "-ac", "2", "-c:a", "aac", "-b:a", "160k", padded])
        parts.append(padded)
        sec_dur = audio_duration(padded)

        # Split the section's time across its beats by character weight.
        sb = section["beats"]
        weights = [max(1, len(b["text"])) for b in sb]
        wsum = sum(weights)
        for beat, weight in zip(sb, weights):
            idx += 1
            dur = sec_dur * weight / wsum
            art = fetch(beat["image"], dl, f"art_{idx:03d}", base)
            frame = frames / f"f_{idx:04d}.png"
            compose_frame(banner_img, art, frame)
            beats.append({"frame": frame, "text": beat["text"],
                          "start": cursor, "duration": dur})
            cursor += dur
            print(f"  beat {idx:>3}/{n_beats}  {dur:5.2f}s  {beat['text'][:46]}")
        print(f"section {si}/{len(sections)}: {sec_dur:.2f}s, {len(sb)} beats")

    total = cursor
    print(f"total: {total:.1f}s ({total / 60:.1f} min), {n_beats} illustrations")

    # Narration track.
    listing = work / "audio.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts),
                       encoding="utf-8")
    narration = work / "narration.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c", "copy", narration])

    if not args.no_normalize:
        # Raw TTS sits ~5 dB under the reference. -16 LUFS is the streaming
        # norm and lands close to the reference's -17.5 dBFS mean.
        levelled = work / "narration_norm.m4a"
        run(["ffmpeg", "-y", "-v", "error", "-i", narration,
             "-af", "loudnorm=I=-16:TP=-1.0:LRA=11",
             "-c:a", "aac", "-b:a", "160k", "-ar", "44100", levelled])
        narration = levelled

    if args.music:
        bed = fetch(args.music, dl, "music", base)
        mixed = work / "mixed.m4a"
        run(["ffmpeg", "-y", "-v", "error", "-i", narration,
             "-stream_loop", "-1", "-i", bed,
             "-filter_complex",
             f"[1:a]volume={args.music_db}dB[bed];"
             f"[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0"
             f":normalize=0[out]",
             "-map", "[out]", "-c:a", "aac", "-b:a", "160k", mixed])
        narration = mixed

    # Video track: one still per beat, held for that beat's duration.
    vlist = work / "video.txt"
    lines = []
    for beat in beats:
        lines.append(f"file '{beat['frame'].as_posix()}'")
        lines.append(f"duration {beat['duration']:.4f}")
    lines.append(f"file '{beats[-1]['frame'].as_posix()}'")  # demuxer quirk
    vlist.write_text("\n".join(lines) + "\n", encoding="utf-8")

    vf = f"scale={W}:{H},fps={FPS}"
    if args.captions:
        ass = work / "captions.ass"
        build_ass(beats, font, ass)
        fontsdir = ("/System/Library/Fonts/Supplemental"
                    if sys.platform == "darwin" else ".")
        vf += f",ass={ass.as_posix()}:fontsdir={fontsdir}"
    vf += ",format=yuv420p"

    output = base / manifest.get("output", "final.mp4")
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", vlist,
        "-i", narration,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
        "-movflags", "+faststart", "-shortest", output,
    ])
    print(f"wrote {output} ({output.stat().st_size / 1e6:.1f} MB)")

    if not args.keep:
        shutil.rmtree(frames, ignore_errors=True)
        for p in parts:
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
