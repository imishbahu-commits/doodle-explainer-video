#!/usr/bin/env python3
"""Render a narration-synchronised expressive ancient-medicine sample."""
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "ancient-medicine-expressive"
W, H, FPS = 1280, 720, 30
INK = (42, 29, 21)
PAPER = (246, 242, 226)
RED = (177, 55, 43)
OLIVE = (115, 114, 65)
CHALK = (239, 237, 210)

BEATS = [
    (0.00, 3.87), (3.87, 4.36), (8.23, 3.94), (12.17, 3.57),
    (15.74, 4.18), (19.92, 3.52), (23.44, 4.08), (27.52, 4.11),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSansCondensed-Bold.ttf" if bold else "DejaVuSans.ttf"
    paths = [Path("/usr/share/fonts/truetype/dejavu") / name,
             Path("/usr/share/fonts/truetype/liberation2") / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")]
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def cover(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max(W / image.width, H / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    return image.crop(((image.width - W) // 2, (image.height - H) // 2,
                       (image.width + W) // 2, (image.height + H) // 2))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def pop(local: float, at: float, length: float = 0.25) -> float:
    return ease((local - at) / length)


def actor_variant(base: Image.Image, expression: str = "neutral", talk: bool = False,
                  patient: bool = False) -> Image.Image:
    """Programmatically redraw face/accessory states on the accepted master."""
    actor = base.copy()
    draw = ImageDraw.Draw(actor)
    w, h = actor.size
    if patient:
        # A hand-drawn bandage creates a second role without regenerating the face.
        draw.polygon([(w*.20, h*.115), (w*.71, h*.075), (w*.73, h*.13), (w*.22, h*.17)],
                     fill=(220, 209, 169, 255), outline=INK + (255,))
        draw.line((w*.30, h*.13, w*.34, h*.105), fill=(140, 120, 90, 255), width=3)
    if expression == "alarm":
        draw.arc((w*.28, h*.245, w*.48, h*.34), 190, 345, fill=INK + (255,), width=6)
        draw.arc((w*.61, h*.235, w*.77, h*.32), 195, 345, fill=INK + (255,), width=6)
        draw.ellipse((w*.525, h*.476, w*.635, h*.515), fill=(42, 22, 18, 255))
    elif expression == "weak":
        draw.line((w*.30, h*.30, w*.45, h*.315), fill=INK + (255,), width=6)
        draw.line((w*.63, h*.29, w*.75, h*.305), fill=INK + (255,), width=6)
        draw.arc((w*.52, h*.48, w*.66, h*.535), 190, 345, fill=INK + (255,), width=5)
    elif expression == "smug":
        draw.line((w*.29, h*.25, w*.47, h*.225), fill=INK + (255,), width=7)
        draw.arc((w*.52, h*.475, w*.68, h*.525), 15, 160, fill=INK + (255,), width=5)
    elif expression == "grimace":
        draw.rectangle((w*.52, h*.475, w*.68, h*.515), fill=(239, 226, 191, 255), outline=INK + (255,), width=4)
        for x in (.56, .60, .64):
            draw.line((w*x, h*.478, w*x, h*.512), fill=(115, 91, 61, 255), width=2)
    if talk:
        draw.ellipse((w*.54, h*.475, w*.66, h*.515), fill=(51, 24, 21, 255), outline=INK + (255,), width=3)
        draw.arc((w*.565, h*.493, w*.64, h*.522), 185, 355, fill=(184, 75, 66, 255), width=3)
    return actor


def paste_actor(frame: Image.Image, actor: Image.Image, x: float, baseline: float, height: float,
                angle: float = 0, mirror: bool = False, opacity: float = 1.0) -> tuple[int, int, int, int]:
    source = ImageOps.mirror(actor) if mirror else actor
    scale = height / source.height
    source = source.resize((round(source.width * scale), round(height)), Image.Resampling.LANCZOS)
    if opacity < 1:
        alpha = source.getchannel("A").point(lambda p: round(p * opacity))
        source.putalpha(alpha)
    if angle:
        source = source.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    px, py = round(x), round(baseline - source.height)
    frame.paste(source, (px, py), source)
    return px, py, source.width, source.height


def hand_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, size: int,
              fill=INK, anchor: str = "la", stroke: int = 0) -> None:
    x, y = xy
    # Slight duplicate offset provides an intentionally imperfect ink edge.
    draw.text((x+1, y), text, font=font(size, True), fill=fill, anchor=anchor,
              stroke_width=stroke, stroke_fill=fill)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill=INK, width=6) -> None:
    draw.line((start, end), fill=fill, width=width)
    angle = math.atan2(end[1]-start[1], end[0]-start[0])
    for delta in (-.65, .65):
        point = (end[0]-20*math.cos(angle+delta), end[1]-20*math.sin(angle+delta))
        draw.line((end, point), fill=fill, width=width)


def bowl(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float = 1.0, level: float = 0.0) -> None:
    box = (x, y, x+130*scale, y+62*scale)
    draw.arc(box, 0, 180, fill=INK, width=max(3, round(6*scale)))
    draw.line((x, y+31*scale, x+130*scale, y+31*scale), fill=INK, width=max(3, round(6*scale)))
    if level:
        draw.ellipse((x+12*scale, y+20*scale, x+118*scale, y+(28+12*level)*scale), fill=RED, outline=INK)


def drill(draw: ImageDraw.ImageDraw, x: float, y: float, angle: float = 0, scale: float = 1.0) -> None:
    layer = Image.new("RGBA", (260, 140), (0,0,0,0)); d = ImageDraw.Draw(layer)
    d.line((24, 70, 200, 70), fill=INK+(255,), width=10)
    d.polygon([(200,60),(246,70),(200,80)], fill=(95,82,57,255), outline=INK+(255,))
    d.arc((3,26,80,112), 70, 290, fill=INK+(255,), width=9)
    d.line((25,33,25,107), fill=INK+(255,), width=8)
    if scale != 1:
        layer=layer.resize((round(260*scale),round(140*scale)),Image.Resampling.LANCZOS)
    layer=layer.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
    draw._image.paste(layer,(round(x),round(y)),layer)


def scene_classroom(local: float, duration: float, base: Image.Image, bg: Image.Image, final: bool=False) -> Image.Image:
    frame = bg.copy(); draw = ImageDraw.Draw(frame)
    talk = int(local * 5) % 2 == 0
    expression = "grimace" if final and local > 1.0 else ("alarm" if not final and local > 2.25 else "neutral")
    host = actor_variant(base, expression, talk)
    entrance = pop(local, 0.0, .55)
    x = -180 + 250*entrance
    bob = math.sin(local*8)*3 if local < duration-.4 else 0
    paste_actor(frame, host, x, 690+bob, 605, angle=-1.5+math.sin(local*3)*.8)
    # Independently animated pointer arm/prop, not generic whole-body movement.
    shoulder=(310,430); target=(780,255 if not final else 300)
    amount=pop(local, .55 if not final else 1.65, .35)
    tip=(round(shoulder[0]+(target[0]-shoulder[0])*amount),round(shoulder[1]+(target[1]-shoulder[1])*amount))
    draw.line((shoulder,tip),fill=INK,width=10); draw.line((tip,(tip[0]+38,tip[1]-10)),fill=(177,139,76),width=7)
    if not final:
        if local>1.05: hand_text(draw,(820,170),"TERRIFYING",46,CHALK,"mm")
        if local>1.35: hand_text(draw,(820,224),"RULE",68,CHALK,"mm")
        if local>2.38: hand_text(draw,(720,340),"HURT",62,(236,150,104),"mm")
        if local>3.02: hand_text(draw,(925,340),"= WORKED?",52,CHALK,"mm")
        if local>3.0:
            for i in range(3):
                draw.line((430+i*20,210-i*12,445+i*20,185-i*12),fill=RED,width=5)
    else:
        hand_text(draw,(875,160),"MEDICINE",45,CHALK,"mm")
        if local>1.0:
            draw.ellipse((330,555,372,592),fill=(108,72,40),outline=INK,width=4)
            draw.arc((360,558,392,588),270,90,fill=INK,width=4)
        if local>2.02:
            hand_text(draw,(850,275),"NO SKULL",58,(244,186,115),"mm")
            hand_text(draw,(850,342),"DRILL",78,CHALK,"mm")
            draw.line((680,395,1030,215),fill=RED,width=13)
        if local>2.75:
            amount=pop(local,2.75,.28)
            drill(draw,960+240*amount,400-90*amount,angle=-18+amount*25,scale=.6)
    return frame


def scene_clinic_drill(local: float, base: Image.Image, bg: Image.Image) -> Image.Image:
    frame=bg.copy(); draw=ImageDraw.Draw(frame)
    patient=actor_variant(base,"alarm" if local>1.7 else "weak",False,True)
    paste_actor(frame,patient,190,545,405,angle=88)
    doctor=actor_variant(base,"smug",int(local*5)%2==0)
    paste_actor(frame,doctor,855,700,575,angle=-2)
    if local>.75:
        descend=pop(local,1.15,.8)
        drill(draw,390,55+170*descend,angle=68,scale=.7)
    if local>2.7:
        for i in range(3):
            p=clamp((local-2.7-i*.18)/.8)
            x=390+i*50+math.sin(p*8+i)*30; y=300-p*210-i*12
            draw.arc((x,y,x+65,y+65),30,330,fill=(78,111,102),width=7)
            draw.ellipse((x+45,y+4,x+54,y+13),fill=(78,111,102))
    if local<.7: hand_text(draw,(95,90),"HEADACHE?",56,RED)
    return frame


def scene_blood_card(local: float, base: Image.Image) -> Image.Image:
    frame=Image.new("RGB",(W,H),PAPER); draw=ImageDraw.Draw(frame)
    hand_text(draw,(80,75),"FEVER",70,RED)
    if local>.65:
        progress=pop(local,.65,.75)
        draw.line((160,260,160+650*progress,260),fill=RED,width=42)
        draw.line((160,260,160+650*progress,260),fill=(225,111,91),width=18)
        hand_text(draw,(485,210),"TOO MUCH BLOOD?",38,INK,"mm")
    if local>1.55:
        bowl(draw,850,510,1.4,min(1,(local-1.55)/1.2))
        for i in range(3):
            y=300+((local*170+i*80)%190)
            draw.ellipse((930+i*28,y,945+i*28,y+22),fill=RED,outline=INK)
        arrow(draw,(760,280),(900,500),RED,7)
    if local>2.55:
        for i,(x,y) in enumerate(((310,470),(420,540),(575,455),(690,535))):
            r=25+6*math.sin(local*7+i)
            draw.ellipse((x-r,y-r,x+r,y+r),fill=(124,164,98),outline=INK,width=4)
            for a in range(0,360,60):
                draw.line((x+r*math.cos(math.radians(a)),y+r*math.sin(math.radians(a)),x+(r+14)*math.cos(math.radians(a)),y+(r+14)*math.sin(math.radians(a))),fill=INK,width=3)
        hand_text(draw,(500,630),"MICROBES",34,INK,"mm")
    return frame


def scene_weak_patient(local: float, base: Image.Image, bg: Image.Image) -> Image.Image:
    frame=bg.copy(); draw=ImageDraw.Draw(frame)
    slump=pop(local,2.25,.6)
    patient=actor_variant(base,"weak",False,True)
    paste_actor(frame,patient,170,555+40*slump,410,angle=88+10*slump)
    doctor=actor_variant(base,"smug",int(local*4)%2==0)
    paste_actor(frame,doctor,860,700,575,angle=-4)
    hand_text(draw,(90,95),"ENERGY",34,INK)
    draw.rectangle((90,135,390,180),outline=INK,width=5)
    level=max(0.07,1-local/2.5)
    draw.rectangle((98,143,98+284*level,172),fill=(77,139,80) if level>.45 else RED)
    if local>1.5:
        lift=pop(local,1.5,.45)
        bowl(draw,785,390-90*lift,1.0,1)
        for i in range(4):
            x=880+i*22; y=315-i*9
            draw.line((x,y,x+10,y-18),fill=(225,190,105),width=4)
    if local>2.55:
        second=pop(local,2.55,.3); bowl(draw,1030,660-100*second,.85,.25)
        hand_text(draw,(1050,590),"ANOTHER?",30,RED,"mm")
    return frame


def organ_icon(draw: ImageDraw.ImageDraw, center: tuple[int,int], kind: str, bad: float) -> None:
    x,y=center; color=(194,109,92) if bad else (155,139,92)
    if kind=="kidneys":
        draw.ellipse((x-65,y-55,x-5,y+45),fill=color,outline=INK,width=5); draw.ellipse((x+5,y-55,x+65,y+45),fill=color,outline=INK,width=5)
    elif kind=="brain":
        for dx,dy in ((-35,-15),(0,-25),(35,-12),(-20,20),(22,18)): draw.ellipse((x+dx-30,y+dy-27,x+dx+30,y+dy+27),fill=color,outline=INK,width=4)
    else:
        draw.arc((x-75,y-40,x+75,y+55),5,175,fill=INK,width=8); draw.arc((x-50,y-5,x+50,y+35),185,355,fill=RED if bad else INK,width=7)
    if bad:
        draw.line((x-72,y-65,x+72,y+65),fill=RED,width=10); draw.line((x+72,y-65,x-72,y+65),fill=RED,width=10)


def scene_mercury(local: float) -> Image.Image:
    frame=Image.new("RGB",(W,H),PAPER); draw=ImageDraw.Draw(frame)
    hand_text(draw,(90,75),"MERCURY",70,INK)
    land=pop(local,0,.45); y=150-100*(1-land)
    draw.rounded_rectangle((120,y,350,y+390),28,fill=(154,132,76),outline=INK,width=8)
    draw.rectangle((178,y-45,292,y+25),fill=(108,91,61),outline=INK,width=7)
    hand_text(draw,(235,y+190),"Hg",92,CHALK,"mm")
    draw.ellipse((160,y+305,310,y+360),fill=(193,198,190),outline=INK,width=5)
    if local>1.0:
        for i in range(7):
            a=i*0.9; cx=300+math.cos(a)*120; cy=190+math.sin(a)*95
            draw.line((cx-10,cy,cx+10,cy),fill=(219,185,84),width=4); draw.line((cx,cy-10,cx,cy+10),fill=(219,185,84),width=4)
        hand_text(draw,(240,620),"SHINY CURE",34,INK,"mm")
    organ_icon(draw,(610,280),"kidneys",local>2.05)
    organ_icon(draw,(860,280),"brain",local>2.55)
    organ_icon(draw,(1090,280),"mouth",local>2.9)
    hand_text(draw,(610,430),"KIDNEYS",27,INK,"mm"); hand_text(draw,(860,430),"BRAIN",27,INK,"mm"); hand_text(draw,(1090,430),"MOUTH",27,INK,"mm")
    return frame


def scene_despite(local: float, base: Image.Image, bg: Image.Image) -> Image.Image:
    frame=bg.copy(); draw=ImageDraw.Draw(frame)
    exit_amount=ease((local-.55)/.9)
    doctor=actor_variant(base,"smug",False)
    paste_actor(frame,doctor,850+500*exit_amount,700,570,angle=-3+7*exit_amount)
    rise=pop(local,1.25,.8)
    patient=actor_variant(base,"weak" if rise<.6 else "neutral",False,True)
    paste_actor(frame,patient,210,560+105*rise,410+80*rise,angle=88*(1-rise))
    if local>2.2:
        stamp=pop(local,2.2,.18); size=round(95*(1.35-.35*stamp))
        draw.rounded_rectangle((430,90,1000,245),18,fill=(246,231,186),outline=RED,width=10)
        hand_text(draw,(715,167),"DESPITE TREATMENT",size,RED,"mm")
        draw.line((465,220,955,220),fill=RED,width=7)
    return frame


def mini_person(draw: ImageDraw.ImageDraw,x:int,y:int,color:tuple[int,int,int],weak:bool=False)->None:
    draw.ellipse((x-34,y-95,x+34,y-27),fill=(201,143,82),outline=INK,width=5)
    draw.polygon([(x-42,y-25),(x+42,y-25),(x+58,y+75),(x-58,y+75)],fill=color,outline=INK)
    draw.line((x-20,y-68,x-6,y-66),fill=INK,width=4); draw.line((x+8,y-66,x+22,y-68),fill=INK,width=4)
    if weak: draw.arc((x-20,y-52,x+20,y-27),190,350,fill=INK,width=4)
    else: draw.arc((x-20,y-52,x+20,y-24),10,170,fill=INK,width=4)


def scene_testing(local: float) -> Image.Image:
    frame=Image.new("RGB",(W,H),PAPER); draw=ImageDraw.Draw(frame)
    hand_text(draw,(640,72),"TEST OUTCOMES",62,INK,"mm")
    if local>.65:
        for i in range(3): mini_person(draw,220+i*120,360,(126,134,77),weak=i==1)
        for i in range(3): mini_person(draw,810+i*120,360,(157,104,67),weak=i!=1)
        hand_text(draw,(330,520),"GROUP A",35,INK,"mm"); hand_text(draw,(930,520),"GROUP B",35,INK,"mm")
    if local>1.6:
        length=520*pop(local,1.6,.4); draw.line((640,140,640,140+length),fill=INK,width=7)
        hand_text(draw,(640,590),"COMPARE",30,INK,"mm")
    if local>2.45:
        draw.ellipse((245,565,410,700),outline=(53,134,73),width=10); draw.line((275,630,320,675,385,585),fill=(53,134,73),width=14)
        draw.line((855,585,1005,690),fill=RED,width=14); draw.line((1005,585,855,690),fill=RED,width=14)
    if local>3.22:
        hand_text(draw,(640,650),"ADMIT FAILURE",39,RED,"mm"); draw.line((480,685,800,685),fill=RED,width=6)
    return frame


def render_frame(time_s: float, base: Image.Image, classroom: Image.Image, clinic: Image.Image) -> Image.Image:
    beat=7
    for index,(start,duration) in enumerate(BEATS):
        if time_s < start+duration or index==7:
            beat=index; local=time_s-start; break
    if beat==0: return scene_classroom(local,BEATS[0][1],base,classroom)
    if beat==1: return scene_clinic_drill(local,base,clinic)
    if beat==2: return scene_blood_card(local,base)
    if beat==3: return scene_weak_patient(local,base,clinic)
    if beat==4: return scene_mercury(local)
    if beat==5: return scene_despite(local,base,clinic)
    if beat==6: return scene_testing(local)
    return scene_classroom(local,BEATS[7][1],base,classroom,True)


def prepare_audio() -> None:
    """Tempo-match the selected per-beat TTS and build the measured final mix."""
    audio = PROJECT / "audio"
    timed = audio / "timed"
    timed.mkdir(parents=True, exist_ok=True)
    concat_lines = []
    for index in range(1, 9):
        source = audio / f"beat-{index:02d}.mp3"
        target = timed / f"beat-{index:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                        "-filter:a", "atempo=1.65", "-ar", "48000", "-ac", "1", str(target)], check=True)
        concat_lines.append(f"file '{target.name}'")
    concat = timed / "concat.txt"
    concat.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(concat), "-af", "loudnorm=I=-19:TP=-2.3:LRA=5",
                    "-ar", "48000", "-ac", "1", str(audio / "narration.wav")], check=True)


def main() -> None:
    os.environ["PATH"] = str(Path.home()/".local"/"bin") + os.pathsep + os.environ.get("PATH","")
    prepare_audio()
    base=Image.open(ROOT/"projects/character-workflow-demo/original-character-long-robe.png").convert("RGBA")
    classroom=cover(PROJECT/"assets/classroom-background.png")
    clinic=cover(PROJECT/"assets/ancient-clinic-background.png")
    output=PROJECT/"ancient-medicine-expressive.mp4"; silent=PROJECT/".silent.mp4"
    duration=31.63; total=round(duration*FPS)
    command=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",str(silent)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE); assert process.stdin
    for number in range(total):
        frame=render_frame(number/FPS,base,classroom,clinic)
        process.stdin.write(frame.convert("RGB").tobytes())
    process.stdin.close()
    if process.wait(): raise RuntimeError("silent render failed")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(PROJECT/"audio/narration.wav"),"-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(output)],check=True)
    silent.unlink(missing_ok=True)
    # Representative review frames and acting/contact sheet.
    thumbs=[]
    for index,(start,duration_b) in enumerate(BEATS,1):
        frame=render_frame(start+duration_b*.68,base,classroom,clinic).resize((480,270),Image.Resampling.LANCZOS)
        d=ImageDraw.Draw(frame); d.rectangle((0,0,74,34),fill=(245,240,224)); hand_text(d,(12,5),f"{index:02d}",21,INK)
        frame.save(PROJECT/f"beat-{index:02d}.jpg",quality=91); thumbs.append(frame)
    sheet=Image.new("RGB",(960,1080),(225,216,196))
    for i,image in enumerate(thumbs): sheet.paste(image,((i%2)*480,(i//2)*270))
    sheet.save(PROJECT/"beat-contact-sheet.jpg",quality=92)
    print(output)


if __name__=="__main__": main()
