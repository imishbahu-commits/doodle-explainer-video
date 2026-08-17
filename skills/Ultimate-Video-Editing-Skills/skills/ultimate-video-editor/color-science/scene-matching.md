# Scene Matching & Color Continuity

## The Problem
Different shots in the same scene can look wildly different due to:
- Changing light (clouds, time of day, indoor/outdoor mix)
- Different cameras or camera settings
- Different angles catching different ambient light
- Auto white balance shifting between takes

## The Matching Pipeline

### Step 1: Choose a Reference
Pick the best-looking shot as your reference ("hero shot"). All other shots match to this.

### Step 2: Analyze with FFmpeg
```bash
# Get color statistics for reference shot
ffmpeg -i reference.mp4 -vf "signalstats=stat=tout+vrep+brng,metadata=mode=print" -f null -

# Get histogram
ffmpeg -i reference.mp4 -vf "histogram=display_mode=overlay" -frames:v 1 ref_histogram.png
ffmpeg -i target.mp4 -vf "histogram=display_mode=overlay" -frames:v 1 target_histogram.png

# Side-by-side comparison
ffmpeg -i reference.mp4 -i target.mp4 -filter_complex \
  "[0]crop=iw/2:ih:0:0[l];[1]crop=iw/2:ih:iw/2:0[r];[l][r]hstack" comparison.mp4
```

### Step 3: Match Exposure
```bash
# If target is darker than reference
-vf "eq=brightness=0.05"

# If target is brighter
-vf "eq=brightness=-0.05"

# Match contrast
-vf "eq=contrast=1.1"
```

### Step 4: Match Color Temperature
```bash
# Target is cooler than reference → warm it
-vf "colorbalance=rs=0.04:gs=0.02:bs=-0.03"

# Target is warmer → cool it
-vf "colorbalance=rs=-0.03:gs=-0.01:bs=0.04"
```

### Step 5: Match Saturation
```bash
-vf "eq=saturation=1.1"  # or 0.9 to reduce
```

### Step 6: Fine-Tune with Curves
```bash
# Match the tonal curve
-vf "curves=m='0/0.03 0.25/0.23 0.5/0.5 0.75/0.77 1/0.97'"
```

### Step 7: Verify
```bash
# Final side-by-side
ffmpeg -i reference_graded.mp4 -i target_graded.mp4 -filter_complex \
  "[0]crop=iw/2:ih:0:0[l];[1]crop=iw/2:ih:iw/2:0[r];[l][r]hstack" final_compare.mp4
```

## Auto Color Match (Histogram Matching)
```bash
# FFmpeg's normalize filter attempts automatic matching
ffmpeg -i input.mp4 -vf "normalize=blackpt=black:whitept=white:smoothing=0" output.mp4
```

## Multi-Camera Matching Workflow
For interviews or multi-cam shoots:
1. Shoot a color chart or gray card at the start of each camera
2. Match all cameras to the chart first
3. Then apply creative grade equally to all cameras
4. If no chart: pick Camera A as reference, match B and C to A

## Common Matching Scenarios

### Indoor to Outdoor Cut
Problem: Indoor is warm tungsten, outdoor is cool daylight.
```bash
# Warm up the outdoor shot to match indoor
-vf "colorbalance=rs=0.06:gs=0.03:bs=-0.04,eq=brightness=-0.03"
```

### Shade to Sun Cut
Problem: Shaded subject is blue/cool, sunny subject is warm.
```bash
# Cool down the sunny shot
-vf "colorbalance=rs=-0.04:bs=0.03,eq=brightness=-0.02"
```

### Different Cameras
Problem: One camera is more saturated, different color science.
```bash
# Desaturate the punchier camera and shift its color balance
-vf "eq=saturation=0.85,colorbalance=rs=ADJUST:gs=ADJUST:bs=ADJUST"
```

## Pro Tips
- Match in order: exposure → temperature → saturation → curves
- Small adjustments compound — 0.02-0.05 per parameter
- Always A/B test by cutting between matched shots
- If two shots refuse to match, add a transition between them
- Consistency matters more than perfection — slightly off but consistent beats perfect but inconsistent across cuts
