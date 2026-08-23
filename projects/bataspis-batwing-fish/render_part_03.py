#!/usr/bin/env python3
"""Render Bataspis Part 3 against the continuous 30 fps frame contract."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ASSETS=HERE/'assets/part-03';AUDIO=HERE/'audio/voiceover.mp3';BEATS=HERE/'beats.json';OUT=HERE/'part-03.mp4';FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1376,768,30;START,END=2609,4125;A0,A1=86.970,137.490;BAR=round(H*.10)
INK=(15,18,18);PAPER=(250,247,237);RED=(229,38,45);YELLOW=(245,207,24);TEAL=(18,110,132)
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
 d=ImageDraw.Draw(im);d.rectangle((0,0,W,BAR),fill='white');d.line((0,BAR-2,W,BAR-2),fill=INK,width=3);d.text((W/2,BAR/2),'THE STRANGE FOSSIL',font=f(46),fill=INK,anchor='mm')
def annotate(im,n,t):
 if n==20:label(im,'ARMOR • EYES • SENSORY CANALS',(W//2,665),t,.45,38,TEAL)
 elif n==21:label(im,'OCEAN SERVING TRAY',(W//2,665),t,.45,46,RED)
 elif n==22:label(im,'THE USUAL SHAPES',(W//2,665),t,.45,47,TEAL)
 elif n==23:label(im,'LONG PROJECTIONS',(W//2,665),t,.45,47,RED)
 elif n==24:label(im,'CONCAVE REAR EDGE',(W//2,665),t,.45,45,TEAL)
 elif n==25:label(im,'BAT?  BOOMERANG?  AIRCRAFT?',(W//2,665),t,.45,38,RED)
 elif n==26:label(im,'QUJING, YUNNAN',(330,665),t,.35,42,RED);label(im,'COLLECTED IN THE 1980s',(1015,665),t,1.25,36,TEAL)
 elif n==27:label(im,'FINE YELLOW-GRAY SANDSTONE',(W//2,665),t,.45,38,INK,YELLOW)
 elif n==28:label(im,'IMPORTANT LIMITATION',(330,665),t,.35,38,RED);label(im,'BODY NOT PRESERVED',(1018,665),t,1.20,38,RED)
 elif n==29:label(im,'ONE HEADSHIELD + COUNTERPART',(W//2,665),t,.45,39,TEAL)
def beats():return [x for x in json.loads(BEATS.read_text())['beats'] if x['part']==3]
def prep(p,n):
 im=fit(p);colors=8 if n in {21,23,24,26,27,29} else 12;return im.quantize(colors=colors,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
def load(bs):
 out={}
 for b in bs:
  ps=list(ASSETS.glob(f'beat-{b["number"]:03d}-*.png'));assert len(ps)==1,(b['id'],ps);out[b['number']]=prep(ps[0],b['number'])
 return out
def frame(b,g,p):
 im=p.copy();annotate(im,b['number'],(g-b['start_frame'])/FPS);title(im);return im
def preflight(bs,ps):
 d=HERE/'qc/part-03-preflight';d.mkdir(parents=True,exist_ok=True)
 for x in d.glob('*.png'):x.unlink()
 for b in bs:frame(b,b['end_frame_exclusive']-12,ps[b['number']]).save(d/f'{b["id"]}.png')
def render(out,poster):
 bs=beats();ps=load(bs);cmd=[FFMPEG,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(AUDIO),'-filter_complex',f'[1:a]atrim={A0}:{A1},asetpts=PTS-STARTPTS,volume=-2.36dB[a]','-map','0:v','-map','[a]','-frames:v',str(END-START),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','44100','-ac','2','-movflags','+faststart',str(out)];p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE);i=0;wrote=False
 for g in range(START,END):
  while g>=bs[i]['end_frame_exclusive']:i+=1
  im=frame(bs[i],g,ps[bs[i]['number']])
  if poster and not wrote and g>=3800:poster.parent.mkdir(parents=True,exist_ok=True);im.save(poster);wrote=True
  p.stdin.write(im.tobytes())
 p.stdin.close();err=p.stderr.read().decode();code=p.wait()
 if code:raise RuntimeError(err[-4000:])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');a=ap.parse_args();bs=beats();ps=load(bs)
 if a.preflight:preflight(bs,ps);print('preflight 10 frames');return
 render(OUT,HERE/'qc/part-03-poster.png');print('wrote',OUT,OUT.stat().st_size)
if __name__=='__main__':main()
