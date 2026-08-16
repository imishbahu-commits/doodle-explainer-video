# FFmpeg Color Grading Recipes

## Cinema Looks

```bash
# Warm Cinematic (Hollywood blockbuster)
-vf "eq=brightness=0.03:contrast=1.1:saturation=1.15,colorbalance=rs=0.05:gs=0.02:bs=-0.03,curves=m='0/0.04 0.5/0.5 1/0.96'"

# Cool Moody (thriller/drama)
-vf "eq=contrast=1.2:saturation=0.85,colorbalance=rs=-0.05:gs=0.0:bs=0.08,curves=m='0/0.05 0.5/0.45 1/0.95'"

# Vintage Film (lifted blacks, rolled highlights)
-vf "curves=m='0/0.06 0.25/0.22 0.5/0.5 0.75/0.78 1/0.94':r='0/0.08 1/0.95':b='0/0.04 1/0.92',eq=saturation=0.85"

# Teal & Orange (blockbuster split-tone)
-vf "colorbalance=rs=0.1:gs=-0.05:bs=-0.1:rh=0.05:gh=-0.03:bh=-0.08:ms=-0.05:bs=0.1,eq=contrast=1.15:saturation=1.2"

# Bleach Bypass (war/gritty film)
-vf "eq=contrast=1.4:saturation=0.5:brightness=-0.05,curves=m='0/0 0.25/0.15 0.75/0.85 1/1'"

# Film Noir (high contrast B&W)
-vf "hue=s=0,eq=contrast=1.5:brightness=-0.05,curves=m='0/0 0.2/0.1 0.5/0.5 0.8/0.9 1/1'"

# Day for Night
-vf "eq=brightness=-0.15:contrast=1.2:saturation=0.6,colorbalance=rs=-0.1:gs=-0.05:bs=0.15"
```

## Director-Style Looks

```bash
# Wes Anderson (pastel, warm, saturated, centered aesthetic)
-vf "eq=saturation=1.3:brightness=0.05,colorbalance=rs=0.08:gs=0.04:bs=-0.02,curves=m='0/0.08 0.5/0.52 1/0.95'"

# David Fincher (desaturated teal, high contrast, crushed greens)
-vf "eq=saturation=0.65:contrast=1.25,colorbalance=rs=-0.03:gs=0.0:bs=0.06:ms=-0.04:gs=0.02:bs=0.08,curves=m='0/0.02 0.3/0.22 0.7/0.78 1/0.98'"

# Michael Bay (orange/teal, high sat, blown highlights)
-vf "eq=saturation=1.35:contrast=1.3:brightness=0.03,colorbalance=rs=0.12:gs=0.02:bs=-0.1:rh=0.08:gh=-0.02:bh=-0.05"

# Blade Runner (neon + dark, selective saturation)
-vf "eq=contrast=1.4:saturation=0.7:brightness=-0.1,colorbalance=rs=-0.02:gs=-0.05:bs=0.12,curves=m='0/0 0.15/0.05 0.85/0.95 1/1'"

# Spielberg (warm golden, natural, slightly lifted blacks)
-vf "eq=brightness=0.02:saturation=1.1,colorbalance=rs=0.06:gs=0.03:bs=-0.02,curves=m='0/0.04 0.5/0.52 1/0.98'"

# Kubrick (cold, precise, high contrast, clinical)
-vf "eq=contrast=1.2:saturation=0.9,colorbalance=rs=-0.02:gs=0.0:bs=0.04,curves=m='0/0.02 0.5/0.5 1/0.98'"
```

## Mood-Based Grades

```bash
# Romance (warm golden glow, soft)
-vf "eq=brightness=0.04:saturation=1.15,colorbalance=rs=0.08:gs=0.04:bs=-0.04,curves=m='0/0.06 0.5/0.52 1/0.96',gblur=sigma=0.5"

# Horror (cool green tint, crushed blacks, harsh)
-vf "eq=contrast=1.35:saturation=0.55:brightness=-0.08,colorbalance=rs=-0.05:gs=0.03:bs=0.0,curves=m='0/0 0.3/0.15 0.7/0.8 1/0.95'"

# Sci-Fi (cool blue, selective saturation, clean)
-vf "eq=contrast=1.15:saturation=0.8,colorbalance=rs=-0.08:gs=-0.02:bs=0.12,curves=m='0/0.03 0.5/0.48 1/0.97'"

# Nostalgic/Memory (warm, desaturated, soft, lifted blacks)
-vf "eq=saturation=0.7:brightness=0.03,colorbalance=rs=0.06:gs=0.03:bs=-0.02,curves=m='0/0.1 0.5/0.52 1/0.93'"

# Dream Sequence (soft glow, warm, low contrast)
-vf "eq=contrast=0.85:saturation=0.9:brightness=0.05,colorbalance=rs=0.04:gs=0.02:bs=0.0,gblur=sigma=1.5,curves=m='0/0.08 0.5/0.52 1/0.95'"

# Golden Hour (warm, rich, glowing)
-vf "colorbalance=rs=0.12:gs=0.06:bs=-0.08,eq=brightness=0.04:saturation=1.2,curves=m='0/0.02 1/0.98'"

# Moonlit Night (cool blue, low light, moody)
-vf "eq=brightness=-0.1:contrast=1.15:saturation=0.6,colorbalance=rs=-0.08:gs=-0.02:bs=0.15,curves=m='0/0.02 0.5/0.42 1/0.9'"
```

## Social Media Looks

```bash
# Instagram Warm (popular filter recreation)
-vf "eq=brightness=0.05:saturation=1.2,colorbalance=rs=0.06:gs=0.03:bs=-0.03,curves=m='0/0.06 0.5/0.53 1/0.96'"

# VSCO Film Emulation
-vf "curves=m='0/0.05 0.25/0.2 0.5/0.5 0.75/0.8 1/0.95':r='0/0.06':b='0/0.03',eq=saturation=0.9"

# Moody Desaturated (trendy editorial)
-vf "eq=saturation=0.6:contrast=1.15,colorbalance=rs=-0.02:gs=0.0:bs=0.04,curves=m='0/0.05 0.5/0.48 1/0.95'"

# Cross-Processed (fashion/music video)
-vf "curves=r='0/0.1 0.5/0.6 1/0.9':g='0/0 0.5/0.45 1/1':b='0/0.15 0.5/0.5 1/0.85'"

# High-Key Bright (beauty/lifestyle)
-vf "eq=brightness=0.08:contrast=0.95:saturation=1.1,curves=m='0/0.1 0.5/0.55 1/1'"
```

## Utility Grades

```bash
# Auto White Balance (approximate)
-vf "colorbalance=rs=0:gs=0:bs=0,normalize"

# Black & White (cinematic)
-vf "hue=s=0,eq=contrast=1.3:brightness=0.02,curves=m='0/0.03 0.3/0.25 0.7/0.75 1/0.97'"

# Sepia
-vf "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"

# Vignette (darken edges)
-vf "vignette=angle=PI/4:mode=forward"

# Strong Vignette
-vf "vignette=angle=PI/3:mode=forward:aspect=3/2"

# Add Film Grain
-vf "noise=alls=15:allf=t+u"
```
