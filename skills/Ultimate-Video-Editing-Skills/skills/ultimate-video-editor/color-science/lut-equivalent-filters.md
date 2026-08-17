# LUT-Equivalent FFmpeg Filter Chains

LUTs (Look-Up Tables) are the industry standard for color grading. Since FFmpeg can apply 3D LUTs directly, but you may not always have LUT files, here are filter-chain equivalents that approximate popular LUT looks.

## Applying Actual LUT Files
```bash
# Apply a .cube LUT
ffmpeg -i input.mp4 -vf "lut3d=film_look.cube" output.mp4

# Apply LUT at partial intensity (blend 50% with original)
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[a][b];[b]lut3d=strong_look.cube[graded]; \
   [a][graded]blend=all_mode=normal:all_opacity=0.5" output.mp4
```

## Film Stock Emulations

### Kodak Vision3 500T (Cinema Standard)
```bash
-vf "colorbalance=rs=0.04:gs=0.01:bs=-0.02:rh=0.03:bh=-0.04, \
     curves=m='0/0.04 0.25/0.22 0.5/0.5 0.75/0.78 1/0.96': \
     r='0/0.05 1/0.97':b='0/0.03 1/0.93', \
     eq=saturation=1.05:contrast=1.05, \
     noise=alls=8:allf=t"
```

### Fujifilm Pro 400H (Portrait)
```bash
-vf "colorbalance=rs=-0.02:gs=0.02:bs=0.04:rh=0.02:gh=0.01:bh=-0.01, \
     curves=m='0/0.05 0.5/0.52 1/0.97', \
     eq=saturation=0.9:brightness=0.02, \
     noise=alls=6:allf=t"
```

### Kodak Portra 400 (Warm Portrait)
```bash
-vf "colorbalance=rs=0.05:gs=0.02:bs=-0.03:rh=0.03:bh=-0.02, \
     curves=m='0/0.06 0.5/0.52 1/0.95', \
     eq=saturation=0.95:contrast=1.02, \
     noise=alls=7:allf=t"
```

### Kodak Tri-X 400 (B&W Classic)
```bash
-vf "hue=s=0, \
     curves=m='0/0.02 0.15/0.08 0.5/0.52 0.85/0.92 1/0.98', \
     eq=contrast=1.35, \
     noise=alls=18:allf=t+u"
```

### CineStill 800T (Tungsten, halation glow)
```bash
-vf "colorbalance=rs=0.06:gs=-0.02:bs=0.04:rh=0.08:gh=-0.01:bh=0.02, \
     curves=m='0/0.03 0.5/0.48 1/0.95', \
     eq=saturation=1.1:contrast=1.1, \
     noise=alls=12:allf=t"
```

## Digital Camera Emulations

### RED Epic Look
```bash
-vf "eq=contrast=1.2:saturation=0.85, \
     colorbalance=rs=-0.03:bs=0.05:rh=0.02:bh=-0.03, \
     curves=m='0/0.02 0.5/0.48 1/0.97'"
```

### ARRI Alexa Natural
```bash
-vf "eq=contrast=1.08:saturation=0.95:brightness=0.01, \
     colorbalance=rs=0.02:gs=0.01:rh=0.01:gh=0.01, \
     curves=m='0/0.03 0.5/0.51 1/0.97'"
```

## TV/Film Reference Looks

### Breaking Bad (Yellow Desert)
```bash
-vf "colorbalance=rs=0.1:gs=0.06:bs=-0.08, \
     eq=saturation=1.2:contrast=1.15:brightness=0.03, \
     curves=m='0/0.02 0.5/0.52 1/0.98'"
```

### The Matrix (Green Tint)
```bash
-vf "colorbalance=rs=-0.08:gs=0.06:bs=-0.04:mh=-0.03:gh=0.04:bh=-0.02, \
     eq=contrast=1.2:saturation=0.7, \
     curves=m='0/0 0.5/0.45 1/0.95'"
```

### Mad Max: Fury Road (Orange/Teal Extreme)
```bash
-vf "colorbalance=rs=0.15:gs=0.02:bs=-0.12:rh=0.08:bh=-0.08, \
     eq=saturation=1.4:contrast=1.3, \
     curves=m='0/0 0.5/0.5 1/1'"
```

### Moonlight (Blue/Purple)
```bash
-vf "colorbalance=rs=-0.04:gs=-0.02:bs=0.1:rh=0.03:gh=-0.02:bh=0.06, \
     eq=saturation=0.8:contrast=1.15, \
     curves=m='0/0.03 0.5/0.48 1/0.95'"
```

## Intensity Control
Always offer the grade at adjustable intensity. Blend with original:
```bash
# 70% grade intensity
ffmpeg -i input.mp4 -filter_complex \
  "[0]split[orig][grade]; \
   [grade]YOUR_GRADE_FILTERS[graded]; \
   [orig][graded]blend=all_mode=normal:all_opacity=0.7" output.mp4
```
