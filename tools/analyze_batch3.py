#!/usr/bin/env python3
"""Batch-3 deep analysis: palette/brightness per video + voiceover beat segmentation."""
import subprocess, json, re
from pathlib import Path
from PIL import Image
import numpy as np

FF = '.venv/bin/ffmpeg'
U = Path('tools/uploads')
OUT = Path('tools/style-reports/batch3-frames')
OUT.mkdir(parents=True, exist_ok=True)

new_vids = ['16060','16064','16068','16072','16076','16080','16084','16088','16092']
id2file = {}
for f in U.glob('*.mp4'):
    for vid in new_vids:
        if f'_{vid}.mp4' in f.name:
            id2file[vid] = f.name
print('found:', len(id2file), 'videos')

pal = {}
for vid, fname in sorted(id2file.items()):
    f = U / fname
    p = subprocess.run([FF,'-i',str(f)], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', p.stderr)
    dur = None
    if m:
        hh,mm,ss = m.groups(); dur = int(hh)*3600+int(mm)*60+float(ss)
    cols, brights, sats = [], [], []
    for i in range(6):
        t = max(0.3, min((dur or 600) - 1.0, (dur or 600) * i / 5))
        tmp = OUT / f'{vid}_s{i}.jpg'
        subprocess.run([FF,'-y','-v','error','-ss',str(t),'-i',str(f),
                        '-frames:v','1','-vf','scale=320:180','-q:v','4',str(tmp)],
                       capture_output=True)
        if tmp.exists():
            im = Image.open(tmp).convert('RGB')
            a = np.asarray(im).astype(float)
            hsv = np.asarray(im.convert('HSV')).astype(float)
            brights.append(a.mean())
            cols.append(a.mean(axis=(0,1)))
            sats.append(hsv[:,:,1].mean())
    if cols:
        pal[vid] = {'file': fname, 'dur': round(dur,1) if dur else None,
                    'bright': round(float(np.mean(brights))),
                    'sat': round(float(np.mean(sats))),
                    'bg': [int(v) for v in np.mean(cols, axis=0)]}
    print(vid, pal.get(vid))

json.dump(pal, open('tools/style-reports/batch3-palette.json','w'), indent=1)

# ---- voiceover beat segmentation (silence-based) ----
vo = 'tools/voiceovers/mtlaoetsvnh26p_my_20vouceover__160357619.mp3'
p = subprocess.run([FF,'-i',vo], capture_output=True, text=True)
m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', p.stderr)
hh,mm,ss = m.groups(); dur = int(hh)*3600+int(mm)*60+float(ss)
print(f'\nVOICEOVER duration: {dur:.1f}s')

# silencedetect -> pauses -> segment into beats 2-6s
sp = subprocess.run([FF,'-i',vo,'-af','silencedetect=noise=-32dB:d=0.35','-f','null','-'],
                    capture_output=True, text=True)
sil = []
for sl in sp.stderr.splitlines():
    m1 = re.search(r'silence_start: ([\d.]+)', sl)
    m2 = re.search(r'silence_end: ([\d.]+)', sl)
    if m1: sil.append(('s', float(m1.group(1))))
    if m2: sil.append(('e', float(m2.group(1))))
# build pause list (start,end)
pauses = []
i = 0
while i < len(sil)-1:
    if sil[i][0]=='s' and sil[i+1][0]=='e':
        pauses.append((sil[i][1], sil[i+1][1])); i += 2
    else:
        i += 1
# merge silence into beats: cut at each pause >=0.5s; merge if beat<2s
segs, cur = [], 0.0
bounds = [0.0]
for s,e in pauses:
    if e-s >= 0.5:
        bounds.append(s)
bounds.append(dur)
bounds = sorted(set(round(b,2) for b in bounds))
beats = []
for i in range(len(bounds)-1):
    d = bounds[i+1]-bounds[i]
    if d < 1.8 and beats:
        beats[-1][1] = bounds[i+1]
    else:
        beats.append([bounds[i], bounds[i+1]])
stats = [b[1]-b[0] for b in beats]
print(f'pauses>=0.5s: {len(pauses)} | beats: {len(beats)}')
print(f'beat len: min {min(stats):.2f}s median {sorted(stats)[len(stats)//2]:.2f}s mean {np.mean(stats):.2f}s max {max(stats):.2f}s')
out = {'file': Path(vo).name, 'duration': round(dur,2),
       'beats': [{'start': round(b[0],2), 'end': round(b[1],2), 'dur': round(b[1]-b[0],2)} for b in beats],
       'summary': {'count': len(beats), 'median': round(sorted(stats)[len(stats)//2],2),
                   'mean': round(float(np.mean(stats)),2), 'min': round(min(stats),2), 'max': round(max(stats),2)}}
json.dump(out, open('tools/style-reports/voiceover-beats.json','w'), indent=1)
print('saved voiceover-beats.json')
