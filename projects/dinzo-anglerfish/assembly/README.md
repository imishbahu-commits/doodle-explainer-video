# Assembly pack — find the clips here

This folder is the **saved, committed** copy of every finished part.
Use it for final concat. Do not depend on `../parts/` (gitignored).

| File | Beats |
|---|---|
| `part01.mp4` | 1–10 — The Beginning |
| `part02.mp4` | 11–20 — The Drop |
| `running-cut.mp4` | 1–20 already joined |
| `audio/beatNN.mp3` | voiceovers 01–20 |
| `concat.txt` | ffmpeg concat list (in order) |
| `manifest.json` | index for a later chat |

When part 3 is done:

```bash
cp ../parts/part03.mp4 part03.mp4
echo "file 'part03.mp4'" >> concat.txt
# update manifest.json
```

Final join:

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart FINAL.mp4
```
