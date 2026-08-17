#!/usr/bin/env python3
"""Draw beats 001 and 002 (the two simple cold-open frames) in the same
flat stick-figure grammar as the rest of the set."""

from PIL import Image, ImageDraw, ImageFont

W, H = 1376, 768
INK = (15, 15, 15)
CREAM = (255, 224, 172)
ORANGE = (242, 166, 59)
GLASS = (255, 244, 224)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def canvas(bg):
    return Image.new("RGB", (W, H), bg)


def d(img):
    return ImageDraw.Draw(img)


def circ(dr, xy, r, fill=None, outline=INK, w=9):
    x, y = xy
    dr.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=w)


def oval(dr, x, y, rx, ry, fill=None, outline=INK, w=9):
    dr.ellipse([x - rx, y - ry, x + rx, y + ry], fill=fill, outline=outline, width=w)


def stick(dr, x, y, s=1.0, arm_up=False):
    r = int(46 * s)
    circ(dr, (x, y), r)
    body = y + int(120 * s)
    dr.line([x, y + r, x, body], fill=INK, width=int(11 * s))
    legs = body + int(115 * s)
    dr.line([x, body, x - int(55 * s), legs], fill=INK, width=int(11 * s))
    dr.line([x, body, x + int(55 * s), legs], fill=INK, width=int(11 * s))
    sh = y + int(35 * s)
    if arm_up:
        dr.line([x, sh, x - int(60 * s), sh - int(50 * s)], fill=INK, width=int(11 * s))
        dr.line([x, sh, x + int(60 * s), sh - int(30 * s)], fill=INK, width=int(11 * s))
    else:
        dr.line([x, sh, x - int(60 * s), sh + int(25 * s)], fill=INK, width=int(11 * s))
        dr.line([x, sh, x + int(60 * s), sh + int(25 * s)], fill=INK, width=int(11 * s))


def label(dr, text, x, y, size=64, c=INK, rot=-2):
    fnt = ImageFont.truetype(FONT, size)
    tmp = Image.new("RGBA", (len(text) * size, size * 3), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((len(text) * size // 2, size * 3 // 2), text,
                             font=fnt, fill=c + (255,), anchor="mm")
    tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC)
    img = dr._image
    img.paste(tmp, (int(x - tmp.width / 2), int(y - tmp.height / 2)), tmp)


# --- beat 001: TURN OFF THE LIGHTS (cream) --------------------------------
img = canvas(CREAM)
dr = d(img)
# hanging lamp
dr.line([990, 40, 990, 180], fill=INK, width=10)
dr.polygon([(930, 180), (1050, 180), (1010, 240), (970, 240)], fill=INK, outline=INK)
dr.ellipse([960, 240, 1020, 310], fill=(255, 238, 150), outline=INK, width=9)
# stick figure reaching for the cord
stick(dr, 760, 420, 1.1, arm_up=True)
# oval mirror on the wall
oval(dr, 400, 330, 130, 190, fill=GLASS)
dr.ellipse([330, 230, 470, 430], outline=INK, width=14)
label(dr, "TURN OFF THE LIGHTS", 690, 660, 72)
img.save("assets/001.png")

# --- beat 002: 10 MINUTES (orange) ----------------------------------------
img = canvas(ORANGE)
dr = d(img)
stick(dr, 460, 330, 1.0)
oval(dr, 930, 330, 160, 230, fill=GLASS)
dr.ellipse([840, 170, 1020, 490], outline=INK, width=14)
# reflection inside mirror
circ(dr, (930, 300), 40, fill=INK)
dr.line([930, 340, 930, 430], fill=INK, width=10)
dr.line([900, 370, 900, 460], fill=INK, width=10)
dr.line([960, 370, 960, 460], fill=INK, width=10)
# eye-lock lines between figure and mirror
dr.line([560, 300, 760, 300], fill=INK, width=6)
dr.line([1100, 300, 1220, 300], fill=INK, width=6)
label(dr, "10 MINUTES", 690, 660, 72)
img.save("assets/002.png")

print("wrote assets/001.png and assets/002.png")
