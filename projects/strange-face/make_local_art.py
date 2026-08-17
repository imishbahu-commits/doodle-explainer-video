#!/usr/bin/env python3
"""Draw beats 012-019 as crude flat stick-figure doodles (same visual grammar
as the AI-generated beats) and compose the banner title over banner_raw.png.

The format spec: thick uniform black outlines, flat fills, no gradients, one
flat background per frame, hand-lettered ALL-CAPS labels, 16:9 (1376x768 here,
matching the generated assets)."""

from PIL import Image, ImageDraw, ImageFont

W, H = 1376, 768
INK = (15, 15, 15)
RED = (226, 28, 28)
GREEN = (18, 150, 72)
PINK = (255, 180, 195)
GLASS = (255, 244, 224)
GRAY = (120, 120, 120)

CREAM = (255, 224, 172)   # #FFE0AC
ORANGE = (242, 166, 59)   # #F2A63B
WHITE = (255, 255, 255)
SKY = (95, 188, 228)      # #5FBCE4

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def canvas(bg):
    return Image.new("RGB", (W, H), bg)


def d(img):
    return ImageDraw.Draw(img)


def line(dr, a, b, w=9, c=INK):
    dr.line([a, b], fill=c, width=w)


def poly(dr, pts, fill=None, outline=INK, w=9):
    dr.polygon(pts, fill=fill, outline=outline, width=w)


def circ(dr, xy, r, fill=None, outline=INK, w=9):
    x, y = xy
    dr.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=w)


def oval(dr, x, y, rx, ry, fill=None, outline=INK, w=9):
    dr.ellipse([x - rx, y - ry, x + rx, y + ry],
               fill=fill, outline=outline, width=w)


def stick(dr, x, y, s=1.0, arms="down"):
    """Stick figure: circle head, single-line limbs. y = head centre."""
    r = int(46 * s)
    circ(dr, (x, y), r)
    body = y + int(120 * s)
    line(dr, (x, y + r), (x, body), w=int(11 * s))
    legs = body + int(115 * s)
    line(dr, (x, body), (x - int(55 * s), legs), w=int(11 * s))
    line(dr, (x, body), (x + int(55 * s), legs), w=int(11 * s))
    sh = y + int(35 * s)
    if arms == "up":
        line(dr, (x, sh), (x - int(65 * s), sh - int(45 * s)), w=int(11 * s))
        line(dr, (x, sh), (x + int(65 * s), sh - int(45 * s)), w=int(11 * s))
    elif arms == "facing":
        line(dr, (x, sh), (x - int(70 * s), sh - int(15 * s)), w=int(11 * s))
        line(dr, (x, sh), (x + int(70 * s), sh - int(15 * s)), w=int(11 * s))
    else:
        line(dr, (x, sh), (x - int(60 * s), sh + int(25 * s)), w=int(11 * s))
        line(dr, (x, sh), (x + int(60 * s), sh + int(25 * s)), w=int(11 * s))


def face(dr, x, y, r=46, angry=False, smile=True):
    circ(dr, (x, y), r)
    dr.ellipse([x - r + 18, y - r + 18, x - r + 34, y - r + 34], fill=INK)
    dr.ellipse([x + r - 34, y - r + 18, x + r - 18, y - r + 34], fill=INK)
    if angry:
        line(dr, (x - 26, y + 8), (x - 6, y + 2), w=6)
        line(dr, (x + 6, y + 2), (x + 26, y + 8), w=6)
    elif smile:
        dr.arc([x - 22, y + 4, x + 22, y + 30], 20, 160, fill=INK, width=7)


def label(dr, text, x, y, size=64, c=INK, rot=-2, anchor="mm"):
    fnt = ImageFont.truetype(FONT, size)
    tmp = Image.new("RGBA", (len(text) * size, size * 3), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((len(text) * size // 2, size * 3 // 2), text,
                             font=fnt, fill=c + (255,), anchor="mm")
    tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC)
    dr._image.paste(tmp, (int(x - tmp.width / 2), int(y - tmp.height / 2)), tmp)
    return dr._image


# ------------------------------------------------------------------ beat 012
img = canvas(CREAM)
dr = d(img)
stick(dr, 480, 330, 1.0, arms="facing")
# quill in right hand
poly(dr, [(620, 300), (700, 330), (625, 360)], fill=INK, outline=INK)
line(dr, (620, 330), (700, 330), w=7)
# scroll
dr.rounded_rectangle([680, 400, 1080, 540], radius=30, fill=WHITE,
                     outline=INK, width=9)
line(dr, (710, 450), (1050, 450), w=7)
line(dr, (710, 490), (1050, 490), w=7)
img = label(dr, "TROXLER 1804", 690, 660, 72)
img.save("assets/012.png")

# ------------------------------------------------------------------ beat 013
img = canvas(SKY)
dr = d(img)
oval(dr, 690, 380, 210, 150, fill=PINK)
for (x, y) in [(450, 230), (340, 380), (450, 530), (930, 230),
               (1040, 380), (930, 530)]:
    line(dr, (690, 380), (x, y), w=10)
    circ(dr, (x, y), 22, fill=PINK)
# sleeping eyes
dr.arc([600, 320, 660, 380], 200, 340, fill=INK, width=9)
dr.arc([720, 320, 780, 380], 200, 340, fill=INK, width=9)
img = label(dr, "Z Z Z", 690, 130, 96, rot=6)
img.save("assets/013.png")

# ------------------------------------------------------------------ beat 014
img = canvas(WHITE)
dr = d(img)
for x in (300, 690, 1080):
    face(dr, x, 380, r=110)
line(dr, (980, 270), (1180, 490), w=26, c=RED)
line(dr, (1180, 270), (980, 490), w=26, c=RED)
img = label(dr, "NOT YOURS", 690, 650, 72)
img.save("assets/014.png")

# ------------------------------------------------------------------ beat 015
img = canvas(ORANGE)
dr = d(img)
oval(dr, 400, 390, 200, 240, fill=GLASS)
# monster in mirror
circ(dr, (400, 330), 92, fill=INK)
poly(dr, [(330, 260), (352, 160), (382, 252)], fill=INK, outline=INK)
poly(dr, [(418, 252), (448, 160), (470, 260)], fill=INK, outline=INK)
dr.ellipse([360, 290, 388, 318], fill=RED)
dr.ellipse([412, 290, 440, 318], fill=RED)
for i in range(4):
    line(dr, (352 + i * 20, 392), (352 + i * 20, 412), w=8)
line(dr, (352, 392), (416, 392), w=8)
line(dr, (210, 170), (590, 610), w=26, c=RED)
line(dr, (590, 170), (210, 610), w=26, c=RED)
# brain with tiny monster
oval(dr, 980, 390, 190, 150, fill=PINK)
dr.arc([880, 330, 940, 390], 200, 340, fill=INK, width=8)
dr.arc([1020, 330, 1080, 390], 200, 340, fill=INK, width=8)
circ(dr, (980, 360), 52, fill=INK)
poly(dr, [(942, 318), (952, 262), (968, 312)], fill=INK, outline=INK)
poly(dr, [(992, 312), (1008, 262), (1018, 318)], fill=INK, outline=INK)
dr.ellipse([958, 338, 974, 354], fill=RED)
dr.ellipse([986, 338, 1002, 354], fill=RED)
img = label(dr, "IN THE BRAIN", 700, 690, 68)
img.save("assets/015.png")

# ------------------------------------------------------------------ beat 016
img = canvas(WHITE)
dr = d(img)
# lightbulb
circ(dr, (300, 300), 115, fill=(255, 244, 170))
line(dr, (300, 300), (275, 340), w=8)
dr.rounded_rectangle([260, 410, 340, 470], radius=12, fill=INK, outline=INK)
for (a, b) in [(300, 130), (170, 220), (170, 380), (300, 470),
               (430, 220), (430, 380)]:
    line(dr, (300, 300), (a, b), w=8)
# eye with motion arrows
oval(dr, 900, 320, 135, 95, fill=WHITE)
circ(dr, (900, 320), 48, fill=INK)
circ(dr, (880, 300), 14, fill=WHITE, outline=WHITE)
dr.arc([770, 190, 1030, 450], 300, 130, fill=INK, width=9)
dr.arc([770, 190, 1030, 450], 120, 310, fill=INK, width=9)
# green check
line(dr, (600, 560), (650, 610), w=30, c=GREEN)
line(dr, (650, 610), (760, 470), w=30, c=GREEN)
img = label(dr, "NO ILLUSION", 690, 690, 68)
img.save("assets/016.png")

# ------------------------------------------------------------------ beat 017
img = canvas(ORANGE)
dr = d(img)
# dim bulb
circ(dr, (300, 250), 95, fill=(255, 238, 150))
dr.rounded_rectangle([268, 345, 332, 400], radius=10, fill=GRAY, outline=INK)
for (a, b) in [(300, 110), (180, 160), (180, 330)]:
    line(dr, (300, 250), (a, b), w=7, c=GRAY)
# staring eye
oval(dr, 300, 540, 100, 65, fill=WHITE)
circ(dr, (300, 540), 38, fill=INK)
# fading mirror (dashed)
for t in range(0, 360, 24):
    dr.arc([760, 180, 1140, 560], t, t + 12, fill=GRAY, width=10)
circ(dr, (950, 380), 70, outline=GRAY, w=5)
dr.ellipse([918, 348, 938, 368], fill=GRAY)
dr.ellipse([962, 348, 982, 368], fill=GRAY)
img = label(dr, "FADES", 950, 680, 72)
img.save("assets/017.png")

# ------------------------------------------------------------------ beat 018
img = canvas(CREAM)
dr = d(img)
stick(dr, 460, 330, 1.0, arms="facing")
stick(dr, 910, 330, 1.0, arms="facing")
img = label(dr, "?", 688, 430, 260, rot=0)
img = label(dr, "WHO ARE YOU SEEING?", 688, 660, 58, rot=0)
img.save("assets/018.png")

# ------------------------------------------------------------------ beat 019
img = canvas(WHITE)
dr = d(img)
# brain with arm
oval(dr, 300, 300, 170, 135, fill=PINK)
dr.arc([190, 250, 250, 310], 200, 340, fill=INK, width=8)
dr.arc([350, 250, 410, 310], 200, 340, fill=INK, width=8)
line(dr, (300, 300), (240, 380), w=10)
dr.ellipse([228, 348, 264, 384], fill=INK)
# paintbrush
line(dr, (420, 380), (680, 430), w=12)
poly(dr, [(670, 420), (740, 452), (690, 462)], fill=INK, outline=INK)
# easel + canvas with face
dr.polygon([(760, 620), (690, 300), (830, 300)], outline=INK, width=11)
dr.rounded_rectangle([680, 300, 840, 500], radius=0, fill=WHITE,
                     outline=INK, width=11)
circ(dr, (760, 385), 55)
dr.ellipse([726, 356, 742, 372], fill=INK)
dr.ellipse([778, 356, 794, 372], fill=INK)
dr.arc([735, 390, 785, 430], 20, 160, fill=INK, width=7)
img = label(dr, "ITS GUESS", 760, 660, 72)
img.save("assets/019.png")

print("doodles written")

# --------------------------------------------------------------- banner title
banner = Image.open("assets/banner_raw.png").convert("RGB")
# centre-crop to band A exactly as build_video.fit_band would
bw, bh = 720, 420
scale = max(bw / banner.width, bh / banner.height)
banner = banner.resize((round(banner.width * scale), round(banner.height * scale)),
                       Image.LANCZOS)
left = (banner.width - bw) // 2
top = (banner.height - bh) // 2
banner = banner.crop((left, top, left + bw, top + bh))

dr = ImageDraw.Draw(banner)
fnt = ImageFont.truetype(FONT, 72)
YELLOW = (252, 235, 0)    # #FCEB00
RED_T = (255, 0, 0)       # #FF0000

line1 = "WHY ISN'T YOUR"
line2_w1 = "REFLECTION "
line2_w2 = "YOU?"

w1 = dr.textlength(line1, font=fnt)
w2 = dr.textlength(line2_w1, font=fnt) + dr.textlength(line2_w2, font=fnt)
x1 = (bw - w1) / 2
x2 = (bw - w2) / 2

for y, txt, col, x in [
    (288, line1, YELLOW, x1),
    (372, line2_w1, YELLOW, x2),
    (372, line2_w2, RED_T, x2 + dr.textlength(line2_w1, font=fnt)),
]:
    dr.text((x, y), txt, font=fnt, fill=col, anchor="lm",
            stroke_width=7, stroke_fill=(0, 0, 0))
banner.save("assets/banner.png")
print("banner composed")
