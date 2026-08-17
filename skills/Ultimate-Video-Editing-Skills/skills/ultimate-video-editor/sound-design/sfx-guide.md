# Sound Effects & Foley — The Secret Weapon of Pro Edits

## Why Sound Design Matters
80% of "cinematic feel" comes from audio. A mediocre video with great sound design always outperforms a beautiful video with bad audio.

## SFX Categories

### Hard SFX (Must Sync to Action)
| Type | When to Use | FFmpeg Generation |
|------|-------------|-------------------|
| Impact | Object hits, cuts, reveals | Low sine burst: `aevalsrc='sin(440*t)*exp(-8*t)'` |
| Whoosh | Fast motion, swipes, transitions | Noise sweep: filter existing audio |
| Click | Button press, selection, UI | Short impulse |
| Snap | Beat drops, transitions | Sharp transient |

### Soft SFX (Ambient, Don't Need Sync)
| Type | When to Use |
|------|-------------|
| Room tone | Fill silence between cuts |
| Ambient | Establish mood/location |
| Texture | Add depth (rain, wind, hum) |
| Music bed | Continuous background energy |

## Layering Technique (How Pros Build Sound)

A single sound event should be 2-4 layers:

### Example: Transition Whoosh
```
Layer 1: Low rumble (sub-bass, 40-80 Hz) — weight
Layer 2: Mid whoosh (200-2000 Hz) — body
Layer 3: High air (4000-12000 Hz) — presence
Layer 4: Click/snap at the peak — punctuation
```

### Example: Impact Hit
```
Layer 1: Sub-bass thump (30-60 Hz) — physical impact
Layer 2: Mid crack (500-2000 Hz) — character
Layer 3: High sizzle/debris (3000+ Hz) — detail
Layer 4: Reverb tail (0.3-1s) — space
```

## FFmpeg SFX Generation

### Generate Whoosh
```bash
# Rising whoosh (transition in)
ffmpeg -f lavfi -i "anoisesrc=d=0.5:c=pink:a=0.3" -af \
  "afade=t=in:st=0:d=0.2,afade=t=out:st=0.3:d=0.2,highpass=f=500,lowpass=f=8000,asetrate=44100*1.5" \
  whoosh_in.wav

# Falling whoosh (transition out)
ffmpeg -f lavfi -i "anoisesrc=d=0.5:c=pink:a=0.3" -af \
  "afade=t=in:st=0:d=0.1,afade=t=out:st=0.2:d=0.3,highpass=f=200,lowpass=f=6000,asetrate=44100*0.7" \
  whoosh_out.wav
```

### Generate Impact
```bash
# Sub-bass impact
ffmpeg -f lavfi -i "aevalsrc='0.8*sin(2*PI*50*t)*exp(-6*t)':s=44100:d=0.5" impact_sub.wav

# Cinematic boom
ffmpeg -f lavfi -i "aevalsrc='0.6*sin(2*PI*40*t)*exp(-3*t)+0.3*sin(2*PI*80*t)*exp(-5*t)':s=44100:d=1" boom.wav
```

### Generate Riser (Build-Up)
```bash
# Tension riser (great before beat drops)
ffmpeg -f lavfi -i "sine=f=200:d=3" -af \
  "vibrato=f=2:d=0.5,afade=t=in:st=0:d=3,asetrate=44100*0.5" \
  riser.wav
```

### Add SFX to Video
```bash
# Mix SFX with video audio
ffmpeg -i video.mp4 -i whoosh.wav -filter_complex \
  "[1]adelay=2000|2000,volume=0.5[sfx]; \
   [0:a][sfx]amix=inputs=2:duration=longest[a]" \
  -map 0:v -map "[a]" -c:v copy output.mp4

# Multiple SFX at different timestamps
ffmpeg -i video.mp4 -i impact.wav -i whoosh.wav -filter_complex \
  "[1]adelay=1500|1500,volume=0.6[sfx1]; \
   [2]adelay=4000|4000,volume=0.4[sfx2]; \
   [0:a][sfx1][sfx2]amix=inputs=3:duration=longest[a]" \
  -map 0:v -map "[a]" -c:v copy output.mp4
```

## Free SFX Sources (Royalty-Free)

| Source | URL | Notes |
|--------|-----|-------|
| Freesound.org | freesound.org | Largest free library, CC licensed |
| Mixkit | mixkit.co/free-sound-effects | High quality, no attribution needed |
| Pixabay Audio | pixabay.com/sound-effects | Free, no signup required |
| BBC Sound Effects | sound-effects.bbcrewind.co.uk | 33,000+ sounds, personal/educational use |
| Zapsplat | zapsplat.com | 150,000+ sounds, free tier |
| SoundBible | soundbible.com | Public domain & CC sounds |

## SFX Timing Rules

| Action | SFX Timing | Duration |
|--------|-----------|----------|
| Cut/transition | Whoosh starts 0.1s before cut | 0.3-0.5s |
| Impact/reveal | Hit lands exactly on frame | 0.2-0.4s |
| Text appearance | Pop/snap at first frame of text | 0.1-0.2s |
| Scene change | Riser peaks at cut point | 1-3s riser |
| Slow-mo start | Low boom at speed change | 0.5-1s |
| Speed-up | Whoosh accelerates with footage | 0.3-0.5s |

## Audio Ducking (Lower Music During Speech)
```bash
# Auto-duck music under voice
ffmpeg -i video.mp4 -i music.mp3 -filter_complex \
  "[0:a]asplit=2[voice][sc]; \
   [sc]sidechaincompress=threshold=0.02:ratio=8:attack=100:release=500[ducked_music]; \
   [1:a][ducked_music]amix=inputs=2:weights=0.3 0.7[a]" \
  -map 0:v -map "[a]" output.mp4
```

## Pro Tips
1. **Room tone fill**: Always add 2-3 seconds of room tone to fill awkward silence between cuts
2. **Pre-lap audio**: Start the next scene's audio 0.5s before the visual cut (J-cut audio equivalent)
3. **Reverb matching**: Apply the same reverb tail to all SFX in a scene for cohesion
4. **Less is more**: 2-3 well-placed SFX beat 20 random sounds every time
5. **Test on phone speakers**: 70%+ of social media is consumed on phone speakers — check your mix there
