# Meme & sound-effect sources — verified with the platform fetcher (2026-08-18)

I tested the platform page-fetcher against real meme and sound sites. Result:
**YES — it can visit all of them** (text: names, descriptions, lists, and even
direct MP3 URLs). It cannot download the binary files into the sandbox
(firewall + text-only fetcher), but your phone can — see the pipeline below.

## ✅ Verified working via the fetcher (inspiration)

| Site | What it gives you | Verified this session |
|---|---|---|
| **knowyourmeme.com** | The meme encyclopedia — search any topic, get meme names, dates, origin stories, example images | `?q=shark` → Shark in the Woods, Hurricane Shark, Baby Shark, Terry the Fat Shark, IKEA Blåhaj, Shark Pog, Left Shark, Mick Fanning Shark Attack… |
| **myinstants.com** | Meme soundboard — search any phrase, get every sound button + **the direct MP3 download URL** | `?name=shark` → Baby Shark, Jaws Remix, Shark Bait Hoo Ha Ha, shark scream, Shark DJ… direct URL pattern `https://www.myinstants.com/media/sounds/<slug>.mp3` |
| **zapsplat.com** | 300k+ **royalty-free** SFX (safe for YouTube) | `?s=underwater` → 397 results incl. 40-file Underwater pack |
| **pixabay.com/sound-effects** | Royalty-free sounds (safe), durations shown | `ocean` → dozens of ocean/wave sounds |
| **imgflip.com** (via image-search) | Meme templates pulled into the workspace as images | "Shark Meme Template", "He punched my shark!", "shark attack" — downloaded |

## ⚠️ Copyright reality check (for YouTube upload-ready)

- **MyInstants sounds** are mostly ripped from movies/music/TV. Short comedic
  use is common, but a monetized upload can get **Content ID claims**.
- **Know Your Meme / Imgflip images** are copyrighted; fair-use territory for
  commentary, not guaranteed safe for monetization.
- **ZapSplat / Pixabay** are **royalty-free** → safe to upload and monetize.
- Smart approach: **take the format/idea from memes, recreate the art with our
  own generator** (like the paint-explainer channels do), and only drop in a
  meme sound as a short comedic beat.

## 🔁 The pipeline to get sounds INTO the video

1. I fetch the meme/sound list for your topic (free, any time).
2. You open the direct MP3 link on your phone → tap Download.
3. Phone studio landing page → **Upload** button → file lands in `uploads/`.
4. I mix it into the video with ffmpeg (boom, Jaws sting, etc.) at the right
   beat.

## One verified direct link to try now

- **Shark Bait Hoo Ha Ha** (113 favorites):
  https://www.myinstants.com/media/sounds/shark-bait-hoo-ha-ha-mp3cut.mp3
