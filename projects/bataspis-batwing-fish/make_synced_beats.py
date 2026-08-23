#!/usr/bin/env python3
"""Align the approved Bataspis script to uploaded audio and make frame-locked beats."""
from __future__ import annotations
import difflib, json, math, re, subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent; AUDIO=ROOT/'audio'; SCRIPT=ROOT/'narration.txt'
ASR=AUDIO/'raw-transcript.json'; MASTER=AUDIO/'voiceover.mp3'; FFMPEG=imageio_ffmpeg.get_ffmpeg_exe(); FPS=30

def norm(s):
 s=s.lower().replace('’',"'").replace('—','-');s=re.sub(r"^[^a-z0-9]+|[^a-z0-9']+$",'',s);return s.replace('-','')

def duration(path):
 p=subprocess.run([FFMPEG,'-hide_banner','-i',str(path),'-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 m=re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)',p.stderr)
 return int(m[1])*3600+int(m[2])*60+float(m[3])

def tokens(text):
 words=[];pars=set();sections=set();chunks=re.split(r'\n\s*\n\s*\n+',text.strip())
 for si,sec in enumerate(chunks):
  for par in re.split(r'\n\s*\n',sec.strip()): words.extend(par.split());pars.add(len(words))
  if si<len(chunks)-1: sections.add(len(words))
 return words,pars,sections

def align(script,asr):
 a=[norm(x) for x in script];b=[x['word'].lower() for x in asr];sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
 out=[None]*len(script);exact=0;gid=0
 for tag,i1,i2,j1,j2 in sm.get_opcodes():
  if tag=='equal':
   for k in range(i2-i1):
    q=asr[j1+k];out[i1+k]={'index':i1+k,'token':script[i1+k],'start':q['start'],'end':q['end'],'alignment':'exact','group':None};exact+=1
  elif i2>i1:
   gid+=1;start=asr[j1]['start'] if j2>j1 else (asr[j1-1]['end'] if j1 else 0);end=asr[j2-1]['end'] if j2>j1 else (asr[j1]['start'] if j1<len(asr) else start+.25*(i2-i1))
   weights=[max(2,len(norm(x))) for x in script[i1:i2]];remaining=sum(weights);cur=start
   for n,w in enumerate(weights):
    stop=end if n==len(weights)-1 else cur+(end-cur)*w/remaining
    out[i1+n]={'index':i1+n,'token':script[i1+n],'start':cur,'end':stop,'alignment':'interpolated','group':gid};cur=stop;remaining-=w
 if any(x is None for x in out): raise RuntimeError('incomplete alignment')
 return out,sm.ratio(),exact

def kind(tok):
 t=tok.rstrip('”’"')
 if t.endswith(('.', '?','!')): return 'sentence'
 if t.endswith((';',':')): return 'clause'
 if t.endswith(','): return 'comma'
 return 'plain'

def boundaries(words,dur):
 b=[0.0]
 for i in range(1,len(words)):
  v=(words[i-1]['end']+words[i]['start'])/2;b.append(max(b[-1]+.001,min(v,dur)))
 return b+[dur]

def make_beats(words,b,pars,secs):
 n=len(words);cost=[float('inf')]*(n+1);prev=[None]*(n+1);cost[0]=0
 for i in range(n):
  if math.isinf(cost[i]):continue
  for j in range(i+5,min(n,i+21)+1):
   d=b[j]-b[i]
   if d<2 or d>6:continue
   wc=j-i;c=abs(wc-14)*.025 if 12<=wc<=16 else .8+1.25*min(abs(wc-12),abs(wc-16));c+=.16*(d-4.85)**2
   k=kind(words[j-1]['token']);c+={'sentence':-1.05,'clause':-.55,'comma':-.28,'plain':.42}[k]
   if j in pars:c-=.6
   if j in secs:c-=.9
   if j<n and words[j-1]['group'] is not None and words[j-1]['group']==words[j]['group']:c+=3.5
   if cost[i]+c<cost[j]:cost[j]=cost[i]+c;prev[j]=i
 if prev[n] is None:raise RuntimeError('no 2-6 second partition')
 ranges=[];x=n
 while x: ranges.append((prev[x],x));x=prev[x]
 ranges.reverse();beats=[];pf=0
 for num,(i,j) in enumerate(ranges,1):
  s=round(b[i],3);e=round(b[j],3);sf=pf;ef=math.ceil(e*FPS) if num==len(ranges) else round(e*FPS);ef=max(sf+1,ef);pf=ef
  beats.append({'id':f'B{num:03d}','number':num,'start':s,'end':e,'duration':round(e-s,3),'fps':FPS,'start_frame':sf,'end_frame_exclusive':ef,'frame_count':ef-sf,'word_count':j-i,'narration':' '.join(x['token'] for x in words[i:j]),'boundary':kind(words[j-1]['token']),'paragraph_end':j in pars,'section_end':j in secs})
 return beats

def parts(beats):
 n=len(beats);pc=math.ceil(n/10);target=beats[-1]['end']/pc;minb=max(6,n//pc-2);dp={(0,0):(0,None)}
 for p in range(1,pc+1):
  for e in range(1,n+1):
   best=(float('inf'),None)
   for s in range(max(0,e-10),e-minb+1):
    if (p-1,s) not in dp:continue
    rem=n-e;rp=pc-p
    if rem<rp*minb or rem>rp*10:continue
    g=beats[s:e];d=g[-1]['end']-g[0]['start'];pen={'sentence':0,'clause':1,'comma':2.2,'plain':4.5}[g[-1]['boundary']]
    if g[-1]['paragraph_end']:pen-=1.4
    if g[-1]['section_end']:pen-=2
    c=dp[p-1,s][0]+.015*(d-target)**2+pen
    if c<best[0]:best=(c,s)
   if best[1] is not None:dp[p,e]=best
 if (pc,n) not in dp:raise RuntimeError('part partition failed')
 rs=[];e=n
 for p in range(pc,0,-1):s=dp[p,e][1];rs.append((s,e));e=s
 rs.reverse();out=[]
 for pn,(s,e) in enumerate(rs,1):
  g=beats[s:e]
  for bi,x in enumerate(g,1):x['part']=pn;x['part_beat']=bi
  out.append({'id':f'P{pn:02d}','part':pn,'start':g[0]['start'],'end':g[-1]['end'],'duration':round(g[-1]['end']-g[0]['start'],3),'start_frame':g[0]['start_frame'],'end_frame_exclusive':g[-1]['end_frame_exclusive'],'frame_count':g[-1]['end_frame_exclusive']-g[0]['start_frame'],'beat_start':g[0]['id'],'beat_end':g[-1]['id'],'beat_count':len(g),'asset_cap':10})
 return out

def stamp(x):return f'{int(x//60):02d}:{x%60:06.3f}'

def main():
 text=SCRIPT.read_text();sw,pars,secs=tokens(text);raw=json.loads(ASR.read_text());dur=duration(MASTER);aw,ratio,exact=align(sw,raw['words']);beats=make_beats(aw,boundaries(aw,dur),pars,secs);ps=parts(beats)
 contract={'fps':FPS,'audio_duration':dur,'total_video_frames':beats[-1]['end_frame_exclusive'],'video_duration':round(beats[-1]['end_frame_exclusive']/FPS,6),'final_audio_strategy':'Join silent visual parts by global frame, then attach voiceover.mp3 once at 0.','time_stretch':False}
 (AUDIO/'script-alignment.json').write_text(json.dumps({'duration':dur,'script_words':len(sw),'asr_words':len(raw['words']),'exact_matches':exact,'sequence_ratio':ratio,'words':aw},indent=2,ensure_ascii=False)+'\n')
 (ROOT/'beats.json').write_text(json.dumps({'duration':dur,'beat_count':len(beats),'render_contract':contract,'beats':beats},indent=2,ensure_ascii=False)+'\n')
 (ROOT/'parts.json').write_text(json.dumps({'duration':dur,'part_count':len(ps),'render_contract':contract,'parts':ps},indent=2,ensure_ascii=False)+'\n')
 lines=['# Synchronized Voice-over Beat Map','',f'- Audio: **{stamp(dur)}** ({dur:.3f}s)',f'- Script words: **{len(sw)}**',f'- Alignment: **{exact}/{len(sw)} exact tokens**, ratio {ratio:.3f}',f'- Beats: **{len(beats)}**, all 2–6 seconds',f'- Parts: **{len(ps)}**, maximum 10 assets each',f'- Frame lock: **{FPS} fps / {contract["total_video_frames"]} frames**','']
 for p in ps:
  lines += [f'## Part {p["part"]} — {stamp(p["start"])} to {stamp(p["end"])}','',f'**{p["beat_count"]} beats · {p["duration"]:.3f}s**','', '| Beat | Time | Frames | Dur. | Words | Narration |','|---:|:---|:---|---:|---:|---|']
  for x in beats:
   if x['part']==p['part']:lines.append(f'| {x["id"]} | {stamp(x["start"])}–{stamp(x["end"])} | {x["start_frame"]}–{x["end_frame_exclusive"]-1} | {x["duration"]:.3f}s | {x["word_count"]} | {x["narration"].replace("|","/")} |')
  lines.append('')
 (ROOT/'beat-map.md').write_text('\n'.join(lines)+'\n')
 print('duration',dur,'words',len(sw),'exact',exact,'ratio',round(ratio,3));print('beats',len(beats),'range',min(x['duration'] for x in beats),max(x['duration'] for x in beats),'word range',min(x['word_count'] for x in beats),max(x['word_count'] for x in beats));print('parts',[(p['beat_count'],p['duration']) for p in ps]);print('frames',contract['total_video_frames'],contract['video_duration'])
if __name__=='__main__':main()
