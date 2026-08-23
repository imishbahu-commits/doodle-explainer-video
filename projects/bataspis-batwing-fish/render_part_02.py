#!/usr/bin/env python3
"""Render Bataspis Part 2 against the continuous 30 fps frame contract."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ASSETS=HERE/'assets/part-02';AUDIO=HERE/'audio/voiceover.mp3';BEATS=HERE/'beats.json';OUT=HERE/'part-02.mp4';FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1376,768,30;START,END=1251,2609;A0,A1=41.715,86.970;BAR=round(H*.10)
INK=(15,18,18);PAPER=(250,247,237);RED=(229,38,45);YELLOW=(245,207,24);TEAL=(18,110,132);GREEN=(31,145,83)
FONT=HERE.parent.parent/'skills/handdrawn-code/fonts/kalam-700.ttf'
def f(s):return ImageFont.truetype(str(FONT),s)
def ease(x):x=max(0,min(1,x));return 1-(1-x)**3
def pop(t,start,d=.22):return ease((t-start)/d)
def fit(p):
 im=Image.open(p).convert('RGB');sc=max(W/im.width,H/im.height);im=im.resize((round(im.width*sc),round(im.height*sc)),Image.Resampling.LANCZOS);x=(im.width-W)//2;y=(im.height-H)//2;return im.crop((x,y,x+W,y+H))
def label(im,text,xy,t,start,size=42,fill=INK,bg=PAPER):
 q=pop(t,start)
 if q<=0:return
 ft=f(size);b=ft.getbbox(text);tw,th=b[2]-b[0],b[3]-b[1];lay=Image.new('RGBA',(tw+40,th+30),(0,0,0,0));d=ImageDraw.Draw(lay);d.rounded_rectangle((3,3,lay.width-4,lay.height-4),radius=13,fill=(*bg,245),outline=(*INK,255),width=4);d.text((lay.width/2,lay.height/2),text,font=ft,fill=(*fill,255),anchor='mm');sc=.9+.1*q;lay=lay.resize((round(lay.width*sc),round(lay.height*sc)),Image.Resampling.LANCZOS);im.paste(lay,(round(xy[0]-lay.width/2),round(xy[1]-lay.height/2)),lay)
def title(im):
 d=ImageDraw.Draw(im);d.rectangle((0,0,W,BAR),fill='white');d.line((0,BAR-2,W,BAR-2),fill=INK,width=3);d.text((W/2,BAR/2),'A WORLD WITHOUT MODERN FISH',font=f(44),fill=INK,anchor='mm')
def annotate(im,n,t):
 if n==10:label(im,'A BIGGER QUESTION',(W//2,665),t,.45,48,RED)
 elif n==11:label(im,"EVOLUTION'S WORKBENCH",(W//2,665),t,.45,45,TEAL)
 elif n==12:label(im,'EARLY DEVONIAN',(W//2,665),t,.45,49,INK,YELLOW)
 elif n==13:label(im,'NO MODERN OCEAN',(W//2,665),t,.45,47,RED)
 elif n==14:label(im,'JAWS: OPTIONAL',(330,665),t,.35,38,RED);label(im,'PAIRED FINS: OPTIONAL',(1020,665),t,1.25,35,RED)
 elif n==15:label(im,'NO STANDARD FISH SHAPE',(W//2,665),t,.45,42,TEAL)
 elif n==16:label(im,'GALEASPIDS',(W//2,665),t,.45,52,TEAL)
 elif n==17:label(im,'CHINA + NORTHERN VIETNAM',(W//2,665),t,.45,40,RED)
 elif n==18:label(im,'RIGID HEADSHIELD',(W//2,665),t,.45,46,RED)
 elif n==19:label(im,'SOFT TRUNK + TAIL',(350,665),t,.35,39,TEAL);label(im,'NO MOVABLE JAW',(1030,665),t,1.25,39,RED)
def beats():return [x for x in json.loads(BEATS.read_text())['beats'] if x['part']==2]
def prep(p,n):
 im=fit(p);colors=8 if n in {10,12,13,16,17} else 12;return im.quantize(colors=colors,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
def load(bs):
 out={}
 for b in bs:
  ps=list(ASSETS.glob(f'beat-{b["number"]:03d}-*.png'));assert len(ps)==1,(b['id'],ps);out[b['number']]=prep(ps[0],b['number'])
 return out
def frame(b,g,p):
 im=p.copy();annotate(im,b['number'],(g-b['start_frame'])/FPS);title(im);return im
def preflight(bs,ps):
 d=HERE/'qc/part-02-preflight';d.mkdir(parents=True,exist_ok=True)
 for x in d.glob('*.png'):x.unlink()
 for b in bs:frame(b,b['end_frame_exclusive']-12,ps[b['number']]).save(d/f'{b["id"]}.png')
def render(out,poster):
 bs=beats();ps=load(bs);cmd=[FFMPEG,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(AUDIO),'-filter_complex',f'[1:a]atrim={A0}:{A1},asetpts=PTS-STARTPTS,volume=-2.36dB[a]','-map','0:v','-map','[a]','-frames:v',str(END-START),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','44100','-ac','2','-movflags','+faststart',str(out)];p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE);i=0;wrote=False
 for g in range(START,END):
  while g>=bs[i]['end_frame_exclusive']:i+=1
  im=frame(bs[i],g,ps[bs[i]['number']])
  if poster and not wrote and g>=2100:poster.parent.mkdir(parents=True,exist_ok=True);im.save(poster);wrote=True
  p.stdin.write(im.tobytes())
 p.stdin.close();err=p.stderr.read().decode();code=p.wait()
 if code:raise RuntimeError(err[-4000:])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');a=ap.parse_args();bs=beats();ps=load(bs)
 if a.preflight:preflight(bs,ps);print('preflight 10 frames');return
 render(OUT,HERE/'qc/part-02-poster.png');print('wrote',OUT,OUT.stat().st_size)
if __name__=='__main__':main()
