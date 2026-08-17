# FFmpeg Subtitle Recipes

## Burn Subtitles from SRT

```bash
# Classic (white text, black outline)
ffmpeg -i input.mp4 -vf \
  "subtitles=subs.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1,Alignment=2,MarginV=30'" \
  output.mp4

# Modern (semi-transparent background bar)
ffmpeg -i input.mp4 -vf \
  "subtitles=subs.srt:force_style='FontName=Helvetica,FontSize=22,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,Alignment=2,MarginV=25'" \
  output.mp4

# Cinematic (thin, elegant, in letterbox)
ffmpeg -i input.mp4 -vf \
  "subtitles=subs.srt:force_style='FontName=Futura,FontSize=20,PrimaryColour=&H00E0E0E0,OutlineColour=&H40000000,Outline=1,Bold=0,Alignment=2,MarginV=15'" \
  output.mp4

# Large for mobile viewing (TikTok/Reels size)
ffmpeg -i input.mp4 -vf \
  "subtitles=subs.srt:force_style='FontName=Impact,FontSize=36,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=2,MarginV=60'" \
  output.mp4

# Top-positioned subtitles
ffmpeg -i input.mp4 -vf \
  "subtitles=subs.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1,Alignment=6,MarginV=30'" \
  output.mp4
```

## ASS Subtitle Alignment Reference
| Value | Position |
|-------|----------|
| 1 | Bottom-left |
| 2 | Bottom-center (default) |
| 3 | Bottom-right |
| 5 | Top-left |
| 6 | Top-center |
| 7 | Top-right |
| 9 | Middle-left |
| 10 | Middle-center |
| 11 | Middle-right |

## Color Format
ASS/SSA uses `&HAABBGGRR` format (alpha, blue, green, red — reversed from hex):
- White: `&H00FFFFFF`
- Black: `&H00000000`
- Yellow: `&H0000FFFF`
- Red: `&H000000FF`
- Semi-transparent black: `&H80000000`

## Subtitle Rules
1. Max 2 lines, ~42 chars per line
2. Display: minimum 1s, maximum 7s
3. Reading speed: 15-20 chars/second
4. Apply subtitles LAST in the filter chain
5. 30ms audio fades at cut points prevent subtitle-audio misalignment perception

## Generate SRT from Whisper
```bash
# Using whisper CLI
whisper input.mp4 --model medium --output_format srt --output_dir .

# Word-level timestamps (for social-style animated captions)
whisper input.mp4 --model medium --word_timestamps True --output_format json
```
