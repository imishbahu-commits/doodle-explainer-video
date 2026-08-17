# Color Grading Master Reference

## The Color Pipeline

### Order of Operations
1. **White balance** — correct color temperature first
2. **Exposure** — set overall brightness
3. **Contrast** — set black/white points
4. **Saturation** — global color intensity
5. **Color balance** — shadows/mids/highlights tinting
6. **Curves** — fine-tune tonal response
7. **Selective color** — individual hue adjustments
8. **Vignette** — darken/lighten edges
9. **Film grain** — add texture last

### Color Wheels (3-Way)
| Wheel | Controls | Typical Use |
|-------|----------|-------------|
| Shadows | Dark tones (<30% luminance) | Add depth: cool blue/teal for cinematic, warm for nostalgic |
| Midtones | Middle tones (30-70%) | Skin tone correction, overall mood shift |
| Highlights | Bright tones (>70%) | Sky/light color, warmth/coolness of light sources |

### The Complementary Split Rule
The most cinematic grades use complementary colors split between shadows and highlights:
- **Teal shadows + Orange highlights** (blockbuster standard)
- **Blue shadows + Amber highlights** (warm cinematic)
- **Green shadows + Magenta highlights** (stylized/fashion)
- **Purple shadows + Gold highlights** (luxury/premium)

Keep midtones relatively neutral — they're the anchor.

## Color Temperature

### Kelvin Guide
| Source | Kelvin | FFmpeg Equivalent |
|--------|--------|-------------------|
| Candlelight | 1800K | colorbalance rs=0.15 gs=0.08 bs=-0.12 |
| Tungsten | 2700K | colorbalance rs=0.08 gs=0.04 bs=-0.06 |
| Halogen | 3200K | colorbalance rs=0.05 gs=0.02 bs=-0.04 |
| Neutral | 5500K | (no shift) |
| Overcast | 6500K | colorbalance rs=-0.03 gs=0.0 bs=0.04 |
| Shade | 7500K | colorbalance rs=-0.06 gs=-0.02 bs=0.08 |
| Blue sky | 10000K | colorbalance rs=-0.1 gs=-0.03 bs=0.12 |

### Correcting Wrong White Balance
- Shot too warm (orange) → add blue: `colorbalance=rs=-0.05:bs=0.08`
- Shot too cool (blue) → add warmth: `colorbalance=rs=0.06:bs=-0.05`
- Shot too green → add magenta: `colorbalance=gs=-0.05:rs=0.02:bs=0.02`
- Shot too magenta → add green: `colorbalance=gs=0.04:rs=-0.02:bs=-0.01`

## Dynamic Range & Contrast

### Log Footage Conversion
```bash
# S-Log to Rec.709 (approximate)
-vf "curves=m='0/0 0.1/0 0.18/0.09 0.3/0.27 0.5/0.55 0.7/0.78 0.9/0.95 1/1',eq=contrast=1.15:saturation=1.3"

# Flat/Log to punchy (generic lift)
-vf "curves=m='0/0 0.15/0.05 0.3/0.25 0.5/0.55 0.7/0.8 0.85/0.92 1/1',eq=saturation=1.2"
```

### Contrast Styles
| Style | Black Point | White Point | Midtone | Use |
|-------|-------------|-------------|---------|-----|
| Crushed | 0 (true black) | 1.0 | Steep S | Drama, noir, action |
| Lifted | 0.05-0.10 | 0.95 | Gentle S | Vintage, dreamy, soft |
| Linear | 0 | 1.0 | Straight | Documentary, neutral |
| High-key | 0.1 | 1.0 | Bright bias | Comedy, beauty, lifestyle |
| Low-key | 0 | 0.85 | Dark bias | Horror, thriller, moody |

## Skin Tone Protection

### The Vectorscope Line
Skin tones of all ethnicities fall along a narrow line on the vectorscope (the "skin tone line" between yellow and red). When grading:
- Check that skin hasn't shifted to green, magenta, or orange
- Desaturation affects skin first — keep skin sat above 30%
- Heavy teal/blue grades push skin toward green — compensate with slight warmth in mids

### Skin Tone Recovery
```bash
# If skin has gone too green
-vf "colorbalance=ms=0.03:mr=0.02,eq=saturation=1.05"

# If skin has gone too orange
-vf "colorbalance=ms=-0.02:mr=-0.03"

# If skin has gone too pale/desaturated
-vf "eq=saturation=1.15,colorbalance=mr=0.02:mg=0.01"
```

## Scene-to-Scene Matching
1. Pick a reference frame from the "hero" shot
2. Match exposure first (brightness/contrast)
3. Match color temperature second
4. Match saturation third
5. Fine-tune with curves
6. A/B compare constantly

```bash
# Rough match tool: normalize + apply same grade to both
-vf "normalize,YOUR_GRADE_FILTERS_HERE"
```
