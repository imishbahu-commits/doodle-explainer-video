#!/usr/bin/env python3
"""Render the faster, illustration-led Ancient Medicine quality pass."""
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "ancient-medicine-expressive-v2"
W, H, FPS = 1280, 720, 30
INK = (42, 29, 21)
CHALK = (241, 235, 205)
RED = (177, 55, 43)
PAPER = (248, 246, 237)
DURATIONS = [3.41, 3.32, 3.26, 3.09, 3.45, 2.77, 3.61, 3.54]
STARTS = []
_acc = 0.0
for _duration in DURATIONS:
    STARTS.append(_acc)
    _acc += _duration
TOTAL = round(_acc, 3)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", size)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def progress(local: float, at: float, duration: float = .25) -> float:
    return ease((local - at) / duration)


def load_art(name: str) -> Image.Image:
    image = Image.open(PROJECT / "art" / name).convert("RGB")
    scale = max(W / image.width, H / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    return image.crop(((image.width-W)//2, (image.height-H)//2, (image.width+W)//2, (image.height+H)//2))


def camera(image: Image.Image, amount: float, focus_x: float = .5, focus_y: float = .5,
           start_zoom: float = 1.0, end_zoom: float = 1.04) -> Image.Image:
    """A motivated crop wrapper; maximum push is intentionally restrained."""
    zoom = start_zoom + (end_zoom-start_zoom)*ease(amount)
    rw, rh = round(W*zoom), round(H*zoom)
    resized = image.resize((rw, rh), Image.Resampling.LANCZOS)
    left = round((rw-W)*clamp(focus_x)); top = round((rh-H)*clamp(focus_y))
    return resized.crop((left, top, left+W, top+H))


def text_layer(frame: Image.Image, xy: tuple[int,int], text: str, size: int, color,
               anchor: str = "mm", angle: float = 0) -> None:
    box = Image.new("RGBA", (900, 180), (0,0,0,0)); draw = ImageDraw.Draw(box)
    draw.text((450,90), text, font=font(size), fill=color+(255,), anchor="mm",
              stroke_width=1, stroke_fill=color+(255,))
    if angle: box = box.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
    frame.paste(box, (xy[0]-450, xy[1]-90), box)


def red_cross(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, width: int = 12) -> None:
    draw.line((x-radius,y-radius,x+radius,y+radius),fill=RED,width=width)
    draw.line((x+radius,y-radius,x-radius,y+radius),fill=RED,width=width)


def check(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1) -> None:
    draw.line((x,y,x+35*scale,y+38*scale,x+105*scale,y-55*scale),fill=(55,132,72),width=round(12*scale),joint="curve")


def render_1(local: float, art: Image.Image) -> Image.Image:
    frame=camera(art,local/DURATIONS[0],.38,.55,1,1.025)
    if local>.62: text_layer(frame,(840,170),"ONE TERRIFYING",40,CHALK,angle=-1.2)
    if local>.92: text_layer(frame,(840,225),"RULE",66,CHALK,angle=.7)
    if local>1.85: text_layer(frame,(760,360),"HURT",62,(245,177,109),angle=-1)
    if local>2.55: text_layer(frame,(930,360),"=  WORKS?",50,CHALK,angle=1)
    if local>2.72:
        draw=ImageDraw.Draw(frame); pulse=1+int(4*math.sin(local*16)**2)
        draw.rounded_rectangle((640-pulse,120-pulse,1070+pulse,430+pulse),15,outline=RED,width=7)
    return frame


def render_2(local: float, art: Image.Image) -> Image.Image:
    # Pan attention from anxious patient to the healer's tool exactly with the clause.
    focal=.20+.50*ease(local/DURATIONS[1])
    frame=camera(art,local/DURATIONS[1],focal,.48,1.04,1.075)
    draw=ImageDraw.Draw(frame)
    if local<.72: text_layer(frame,(245,95),"HEADACHE?",52,RED,angle=-1)
    if local>1.72:
        for i in range(3):
            p=progress(local,1.72+i*.12,.75); x=340+i*50+math.sin(p*6+i)*20; y=265-p*150-i*12
            draw.arc((x,y,x+56,y+56),25,330,fill=(67,116,106),width=6)
    return frame


def render_3(local: float, art: Image.Image) -> Image.Image:
    frame=camera(art,local/DURATIONS[2],.5,.5,1,1.018)
    draw=ImageDraw.Draw(frame)
    # Reveal the bowl half only when narration reaches the old treatment.
    reveal=progress(local,.65,.85)
    if reveal<1: draw.rectangle((round(520+760*reveal),0,W,H),fill=PAPER)
    if local>.15: text_layer(frame,(265,92),"FEVER",50,RED,angle=-1)
    if local>1.75: text_layer(frame,(965,610),"REMOVE BLOOD",36,INK,angle=.7)
    if local>2.35:
        for i,(x,y) in enumerate(((124,155),(220,118),(300,170))):
            r=38+int(4*math.sin(local*10+i)); draw.ellipse((x-r,y-r,x+r,y+r),outline=(70,109,62),width=6)
        text_layer(frame,(225,255),"MICROBES STAY",28,INK,angle=-1)
    return frame


def render_4(local: float, art: Image.Image) -> Image.Image:
    # Reframe from exhausted patient to confident bowl-carrying physician.
    focal=.18+.34*ease(local/DURATIONS[3])
    frame=camera(art,local/DURATIONS[3],focal,.58,1.01,1.04)
    draw=ImageDraw.Draw(frame)
    if local<1.55:
        text_layer(frame,(245,95),"ENERGY",30,INK)
        draw.rounded_rectangle((80,130,400,170),8,outline=INK,width=5)
        amount=max(.08,1-local/1.6); draw.rounded_rectangle((88,138,88+304*amount,162),5,fill=(74,133,72) if amount>.45 else RED)
    if local>1.55:
        text_layer(frame,(1010,120),"CONFIDENT",32,INK,angle=1)
    if local>2.30:
        draw.ellipse((1020,575,1180,630),fill=(174,130,73),outline=INK,width=6)
        draw.arc((1020,550,1180,630),0,180,fill=INK,width=6)
        text_layer(frame,(1095,670),"ANOTHER BOWL",26,RED,angle=-1)
    return frame


def render_5(local: float, art: Image.Image) -> Image.Image:
    frame=camera(art,local/DURATIONS[4],.48,.48,1,1.025); draw=ImageDraw.Draw(frame)
    if local>.12: text_layer(frame,(280,625),"MERCURY",46,INK,angle=-1)
    if local>.95:
        for i in range(6):
            a=i*math.pi/3+local; x=300+math.cos(a)*145; y=290+math.sin(a)*170
            draw.line((x-9,y,x+9,y),fill=(211,173,68),width=4); draw.line((x,y-9,x,y+9),fill=(211,173,68),width=4)
    if local>1.75: red_cross(draw,760,215,62)
    if local>2.20: red_cross(draw,1030,230,62)
    if local>2.62: red_cross(draw,885,475,62)
    return frame


def render_6(local: float, art: Image.Image) -> Image.Image:
    # Follow the leaving healer, then settle back on the recovering patient.
    phase=local/DURATIONS[5]
    focus=.70 if phase<.42 else .70-.50*ease((phase-.42)/.45)
    frame=camera(art,phase,focus,.55,1.04,1.085); draw=ImageDraw.Draw(frame)
    if local>1.05:
        arrow=progress(local,1.05,.45); draw.line((830,550,830+220*arrow,550),fill=INK,width=7)
        draw.polygon([(1040,550),(1010,535),(1010,565)],fill=INK)
    if local>1.58:
        stamp=progress(local,1.58,.2); pad=round(12*(1-stamp))
        draw.rounded_rectangle((335-pad,75-pad,970+pad,205+pad),16,fill=(249,240,210),outline=RED,width=8)
        text_layer(frame,(652,140),"DESPITE TREATMENT",48,RED,angle=-.8)
    return frame


def render_7(local: float, art: Image.Image) -> Image.Image:
    frame=camera(art,local/DURATIONS[6],.5,.5,1,1.015); draw=ImageDraw.Draw(frame)
    text_layer(frame,(640,78),"TEST OUTCOMES",50,INK,angle=-.5)
    # Sequentially reveal groups rather than moving all figures generically.
    left=progress(local,.45,.4); right=progress(local,1.05,.4)
    if left<1: draw.rectangle((0,120,round(560*(1-left)),610),fill=PAPER)
    if right<1: draw.rectangle((720+round(560*right),120,W,610),fill=PAPER)
    if local>1.65: draw.line((640,130,640,600),fill=INK,width=7)
    if local>2.25:
        check(draw,280,620,.7); red_cross(draw,980,630,58,11)
    if local>2.85: text_layer(frame,(640,655),"ADMIT FAILURE",34,RED,angle=.8)
    return frame


def render_8(local: float, art: Image.Image) -> Image.Image:
    frame=camera(art,local/DURATIONS[7],.36,.55,1,1.035); draw=ImageDraw.Draw(frame)
    if local>.25: text_layer(frame,(825,160),"BAD TASTE?",38,CHALK,angle=-1)
    if local>1.45: text_layer(frame,(825,260),"NO SKULL",52,(246,184,109),angle=.5)
    if local>1.85: text_layer(frame,(825,325),"DRILL",72,CHALK,angle=-.8)
    if local>2.28:
        amount=progress(local,2.28,.3); draw.line((665,395,1010,190),fill=RED,width=round(5+8*amount))
    if local>2.72:
        # Final hold gets only a tiny emphasis pulse, preserving the grimace.
        pulse=round(5*math.sin((local-2.72)*10)**2); draw.ellipse((82-pulse,125-pulse,405+pulse,610+pulse),outline=(225,176,94),width=4)
    return frame


def prepare_audio() -> None:
    audio=PROJECT/"audio"; timed=audio/"timed"; timed.mkdir(parents=True,exist_ok=True); lines=[]
    for i in range(1,9):
        src=audio/f"beat-{i:02d}.mp3"; dst=timed/f"beat-{i:02d}.wav"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(src),"-filter:a","atempo=2.0","-ar","48000","-ac","1",str(dst)],check=True)
        lines.append(f"file '{dst.name}'")
    concat=timed/"concat.txt"; concat.write_text("\n".join(lines)+"\n")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-af","loudnorm=I=-19:TP=-2.3:LRA=5","-ar","48000","-ac","1",str(audio/"narration.wav")],check=True)


def main() -> None:
    os.environ["PATH"]=str(Path.home()/".local"/"bin")+os.pathsep+os.environ.get("PATH","")
    prepare_audio()
    names=["beat-01-classroom-rule.png","beat-02-skull-drill.png","beat-03-bloodletting-card.png","beat-06-despite-treatment.png","beat-05-mercury-card.png","beat-06-despite-treatment.png","beat-07-testing-card.png","beat-08-classroom-payoff.png"]
    art=[load_art(n) for n in names]
    renderers=[render_1,render_2,render_3,render_4,render_5,render_6,render_7,render_8]
    silent=PROJECT/".silent.mp4"; output=PROJECT/"ancient-medicine-expressive-v2.mp4"
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","medium","-crf","17","-pix_fmt","yuv420p",str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE); assert proc.stdin
    total_frames=round(TOTAL*FPS)
    review=[]
    for number in range(total_frames):
        t=number/FPS; beat=max(i for i,start in enumerate(STARTS) if t>=start); local=t-STARTS[beat]
        frame=renderers[beat](local,art[beat]); proc.stdin.write(frame.tobytes())
        if abs(local-DURATIONS[beat]*.68)<1/FPS and len(review)<=beat: review.append(frame.resize((480,270),Image.Resampling.LANCZOS))
    proc.stdin.close()
    if proc.wait(): raise RuntimeError("video render failed")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(PROJECT/"audio/narration.wav"),"-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(output)],check=True)
    silent.unlink(missing_ok=True)
    sheet=Image.new("RGB",(960,1080),(226,216,196))
    for i,image in enumerate(review[:8]):
        ImageDraw.Draw(image).rounded_rectangle((8,8,62,42),8,fill=(248,244,230)); ImageDraw.Draw(image).text((35,25),f"{i+1:02d}",font=font(17),fill=INK,anchor="mm")
        sheet.paste(image,((i%2)*480,(i//2)*270))
    sheet.save(PROJECT/"beat-contact-sheet.jpg",quality=93)
    print(output)


if __name__=="__main__": main()
