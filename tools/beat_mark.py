#!/usr/bin/env python3
"""Refine voiceover beat marks (2-6s) + export keyface frame sets for git."""
import subprocess, json, re
from pathlib import Path
import numpy as np

FF = '.venv/bin/ffmpeg'
U = Path('tools/uploads')
OUT = Path('tools/style-reports/batch3-frames')
OUT.mkdir(parents=True, exist_ok=True)

# ---------- 1) finer silence detection (music bed tolerated) ----------
vo = 'tools/voiceovers/mtlaoetsvnh26p_my_20vouceover__160357619.mp3'
p = subprocess.run([FF,'-i',vo], capture_output=True, text=True)
m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', p.stderr)
hh,mm,ss = m.groups(); DUR = int(hh)*3600+int(mm)*60+float(ss)

# two-pass silence: -35dB d=0.18 (catch short breaths)
best = None
for noise, dmin in [(-38, 0.15), (-35, 0.2), (-32, 0.25)]:
    sp = subprocess.run([FF,'-i',vo,'-af',f'silencedetect=noise={noise}dB:d={dmin}','-f','null','-'],
                        capture_output=True, text=True)
    sil = []
    for sl in sp.stderr.splitlines():
        m1 = re.search(r'silence_start: ([\d.]+)', sl)
        m2 = re.search(r'silence_end: ([\d.]+)', sl)
        if m1: sil.append(float(m1.group(1)))
        if m2: sil.append(float(m2.group(1)))
    pauses = [(sil[i], sil[i+1]) for i in range(0, len(sil)-1, 2) if sil[i+1]-sil[i] >= 0.4]
    n_beats = max(1, int(round(sum(e-s for s,e in pauses) / 4.0)))  # rough
    if best is None or len(pauses) > len(best[1]):
        best = (pauses, sil)
pauses = best[0]
print(f'fine pauses: {len(pauses)}')

# greedy 2-6s beat build using pause centers as preferred cut points
centers = sorted([(s+e)/2 for s,e in pauses])
cuts = [0.0]
for c in centers:
    if c - cuts[-1] >= 1.6 and c - cuts[-1] <= 7.5:
        cuts.append(c)
# force-close any trailing beat > 7s by adding evenly spaced cuts
i = 1
while i < len(cuts):
    gap = cuts[i] - cuts[i-1]
    if gap > 7.0:
        n = int(gap // 5.0)
        for k in range(1, n+1):
            cuts.insert(i, cuts[i-1] + gap * k / (n+1))
        i += n
    i += 1
cuts.append(DUR)
beats = [[cuts[i], cuts[i+1]] for i in range(len(cuts)-1)]
# merge sub-1.6s slivers
merged = []
for b in beats:
    if b[1]-b[0] < 1.5 and merged:
        merged[-1][1] = b[1]
    else:
        merged.append(b)
stats = [b[1]-b[0] for b in merged]
srt = sorted(stats)
print(f'BEATS: {len(merged)} | min {min(stats):.2f} | median {srt[len(srt)//2]:.2f} | mean {np.mean(stats):.2f} | max {max(stats):.2f}')

res = {'file': Path(vo).name, 'duration': round(DUR,2),
       'beats': [{'start': round(b[0],2), 'dur': round(b[1]-b[0],2)} for b in merged],
       'summary': {'count': len(merged), 'median': round(srt[len(srt)//2],2),
                   'mean': round(float(np.mean(stats)),2), 'min': round(min(stats),2),
                   'max': round(max(stats),2)}}
json.dump(res, open('tools/style-reports/voiceover-beats.json','w'), indent=1)
print('saved voiceover-beats.json')

# ---------- 2) keyface frames: 4 frames/video at 640x360 (git-safe) ----------
new_vids = ['16060','16064','16068','16072','16076','16080','16084','16088','16092']
saved = 0
for vid in new_vids:
    f = U / f'mtla*.mp4'
    import glob
    cands = glob.glob(str(U / f'mtla*_{vid}.mp4'))
    if not cands:
        continue
    src = cands[0]
    for i in range(4):
        t = max(0.5, min(DUR-1, DUR*(i+1)/5))
        out = OUT / f'{vid}_kf{i}.jpg'
        subprocess.run([FF,'-y','-v','error','-ss',str(t),'-i',src,
                        '-frames:v','1','-vf','scale=640:360','-q:v','4',str(out)],
                       capture_output=True)
        if out.exists():
            saved += 1
print(f'keyframes saved: {saved}')
