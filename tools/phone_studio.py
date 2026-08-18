#!/usr/bin/env python3
"""phone_studio.py — batch AI image generation for video beats, mobile-first.

WHY THIS EXISTS
  This sandbox's firewall only allows PyPI / GitHub / npm — it cannot reach
  image APIs. But YOUR PHONE has normal internet. So this server turns your
  phone into the image generator:

    1. open the live-preview URL on your phone
    2. every pending video beat is a card with its prompt
    3. generation starts AUTOMATICALLY (zero taps) and runs through the
       best available model — the page picks from Pollinations' catalogue
       (Z-Image Turbo, Qwen-Image, FLUX.2 klein, Seedream 5, Nano Banana 2,
       GPT Image, Ideogram 4.0, Grok Imagine, FLUX.1) with a smart
       fallback chain, then uploads each PNG into projects/<name>/assets/
       + images.json (model used is recorded per beat)
    4. if every model fails, the card offers a retry + manual Upload

Routes
  GET  /                          project picker
  GET  /studio?project=NAME       tap-to-generate cards
  GET  /img?project=NAME&id=N     show a generated image
  POST /save?project=NAME&id=N&model=M    raw image body -> beat N
  POST /chunk + /done             chunked upload (+ ?project=&id= target)
  POST /refresh?project=NAME      re-scan images.json

Run:  python3 tools/phone_studio.py 8012        (system python, no deps)
"""

import http.server
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, parse_qs, quote

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
UPLOAD_DIR = ROOT / "uploads"
PARTS_DIR = UPLOAD_DIR / ".parts"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8012
MAX_CHUNK = 2 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone studio — batch AI images</title>
<script src="https://js.puter.com/v2/"></script>
<style>
  body { margin:0; background:#0d0f1a; color:#eee; font-family:system-ui,sans-serif; }
  header { padding:18px 16px 10px; text-align:center; }
  h1 { font-size:19px; margin:0 0 4px; }
  #prog { font-size:13px; color:#9aa; }
  #bar { width:82%; height:10px; background:#161a2b; border-radius:6px;
         margin:8px auto 0; overflow:hidden; }
  #fill { height:100%; width:0%; background:#7ee08a; transition:width .3s; }
  .ctrls { max-width:520px; margin:12px auto 0; text-align:left;
           background:#131727; border:1px solid #2a3045; border-radius:12px;
           padding:12px 14px; font-size:13px; }
  .ctrls label { display:block; margin:8px 0 3px; color:#9aa; }
  .ctrls select, .ctrls input { width:100%; padding:9px; border-radius:8px;
    border:1px solid #2a3045; background:#161a2b; color:#eee; font-size:14px; }
  button.regen { width:82%; padding:12px; border:0; border-radius:10px;
    background:#b06cf5; color:#fff; font-weight:700; font-size:14px;
    margin-top:10px; }
  button.start { width:82%; padding:12px; border:0; border-radius:10px;
    background:#7ee08a; color:#000; font-weight:700; font-size:14px;
    margin-top:10px; }
  .card { margin:12px 14px; background:#161a2b; border:1px solid #2a3045;
          border-radius:14px; padding:14px; }
  .card.done { border-color:#2f6b3f; background:#12241a; }
  .beat { color:#778; font-size:12px; letter-spacing:.5px; }
  .modelused { color:#b06cf5; font-size:11px; margin-top:4px; }
  .prompt { font-size:14px; line-height:1.45; margin:8px 0 12px; color:#dde; }
  button.gen { width:100%; padding:14px; border:0; border-radius:12px;
    background:#7ee08a; color:#000; font-weight:700; font-size:16px; }
  .card.done button.gen { display:none; }
  .card.done .ok { color:#7ee08a; font-size:14px; font-weight:600; }
  .err { color:#ff8080; font-size:12px; margin-top:8px; min-height:15px; }
  .uploadrow { display:none; margin-top:10px; }
  .uploadrow.show { display:block; }
  input[type=file] { width:100%; margin-bottom:8px; }
  button.upload { width:100%; padding:12px; border:0; border-radius:10px;
    background:#f5c63c; color:#000; font-weight:700; font-size:15px; }
  .note { font-size:12px; color:#778; text-align:center; margin:18px 14px 30px;
    line-height:1.6; }
  #status { font-size:13px; color:#f5c63c; text-align:center; min-height:18px;
    margin-top:8px; }
</style>
</head>
<body>
<header>
  <h1>🎨 Batch AI images — {{PROJECT}}</h1>
  <div id="prog">0 / 0</div>
  <div id="bar"><div id="fill"></div></div>
  <button class="regen" id="regenbtn">✨ Generate ALL with best model (overwrite)</button>
</header>
<div id="status"></div>
<div class="ctrls">
  <label>Model (fallback chain: if it fails, auto-tries the next)</label>
  <select id="modelSel">
    <option value="puter:auto" selected>🚀 Puter — FREE UNLIMITED, best models (default)</option>
    <option value="puter:openai/gpt-image-2">  Puter · GPT Image 2</option>
    <option value="puter:google/nano-banana-pro">  Puter · Nano Banana Pro (Gemini)</option>
    <option value="puter:black-forest-labs/flux-2-pro">  Puter · FLUX.2 Pro</option>
    <option value="puter:xai/grok-imagine-image">  Puter · Grok Imagine</option>
    <option value="puter:stabilityai/stable-diffusion-3.5">  Puter · Stable Diffusion 3.5</option>
    <option value="horde:auto">🌐 AI Horde — FREE, NO ACCOUNT, NO LOGIN (community GPU network, 200+ open models)</option>
    <option value="horde:AlbedoBase XL (SDXL)">  Horde · AlbedoBase XL (SDXL) — recommended</option>
    <option value="horde:Juggernaut XL">  Horde · Juggernaut XL</option>
    <option value="horde:flux.1-dev">  Horde · FLUX.1 dev</option>
    <option value="horde:Deliberate">  Horde · Deliberate</option>
    <option value="horde:Realistic Vision">  Horde · Realistic Vision</option>
    <option value="horde:Anything v3">  Horde · Anything v3</option>
    <option value="zimage">Z-Image Turbo — top open model 2026 (Apache-2.0)</option>
    <option value="qwen-image">Qwen-Image — open (Apache-2.0)</option>
    <option value="klein">FLUX.2 klein — open</option>
    <option value="seedream5">Seedream 5 — premium</option>
    <option value="nanobanana-2">Nano Banana 2 (Gemini) — premium</option>
    <option value="ideogram-v4-quality">Ideogram 4.0 Quality — premium</option>
    <option value="gptimage-large">GPT Image — premium</option>
    <option value="grok-imagine-pro">Grok Imagine — premium</option>
    <option value="flux">FLUX.1 — free fallback</option>
  </select>
  <label>Resolution</label>
  <select id="resSel">
    <option value="1024">1024 × 1024 (fast)</option>
    <option value="1536" selected>1536 × 1536 (high)</option>
    <option value="2048">2048 × 2048 (ultra — slower)</option>
  </select>
  <label>Style</label>
  <select id="styleSel">
    <option value="doodle" selected>Doodle — video format (thick black outlines, flat colors)</option>
    <option value="rich">Premium illustration — rich detail, cinematic lighting</option>
    <option value="photo">Photorealistic</option>
  </select>
  <label>Pollinations key (optional — free publishable pk_ key from
  enter.pollinations.ai; unlocks premium models. Stored only in this browser.)</label>
  <input id="keyIn" type="text" placeholder="pk_…">
  <div style="margin-top:10px;border-top:1px solid #2a3045;padding-top:10px">
    <label>🚀 Puter (default — best quality: GPT Image 2 / Nano Banana Pro / FLUX.2 Pro)</label>
    <button class="start" id="puterBtn" type="button" style="width:100%">🔑 Sign in to Puter (one time, free)</button>
    <div id="puterStatus" style="font-size:12px;color:#9aa;margin-top:6px">checking…</div>
    <div style="font-size:11px;color:#778;margin-top:8px">💡 If the preview is embedded and popups are blocked, open the studio in a
    real tab: <a href="{{SELF_URL}}" target="_blank" rel="noopener" style="color:#7ee08a">open in new tab</a> —
    popups work fine there.</div>
  </div>
</div>
<div id="cards"></div>
<div class="note"><b>Default: 🚀 Puter</b> — the best free unlimited engine (GPT
Image 2 / Nano Banana Pro / FLUX.2 Pro / Grok Imagine). It tries
<b>anonymously first</b>; if Puter asks for an account, tap <b>🔑 Sign in to
Puter</b> once (free, ~10 s) and auto-run resumes by itself — after that it's
unlimited. Fallbacks if Puter is unreachable: AI Horde (no account, no login)
and Pollinations FLUX. Keep this tab open; failed cards show Retry + Upload.</div>

<script>
const PROJECT = {{PROJECT_JSON}};
const CARDS = {{CARDS_JSON}};

const MODEL_IDS = ['zimage','qwen-image','klein','seedream5','nanobanana-2',
  'ideogram-v4-quality','gptimage-large','grok-imagine-pro','flux'];
const AUTO_CHAIN = ['zimage','qwen-image','klein','flux','horde:AlbedoBase XL (SDXL)'];

// ---------------- AI HORDE: FREE + ANONYMOUS, no account, no login ----------
// Community GPU network (Haidra-Org/AI-Horde, open source). Anonymous key
// 0000000000 needs no account. Queue-based; returns base64 in JSON.
const HORDE = 'https://aihorde.net/api/v2';

async function genHorde(cardObj, fullPrompt, err, card, sel){
  let model = sel.slice(6);
  if (!model || model === 'auto') model = 'AlbedoBase XL (SDXL)';
  try {
    const body = {
      prompt: fullPrompt,
      params: {
        width: 1024, height: 1024, steps: 22, cfg_scale: 6.5,
        sampler_name: 'k_euler_a', n: 1, models: [model]
      },
      nsfw: false, censor_nsfw: true
    };
    err.textContent = 'queueing on AI Horde (anonymous, free)…';
    const q = await fetch(HORDE + '/generate/async', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'apikey': '0000000000' },
      body: JSON.stringify(body)
    });
    if (!q.ok){
      const qj = await q.json().catch(() => ({}));
      throw new Error('horde queue: HTTP ' + q.status + ' ' + (qj.message || ''));
    }
    const job = await q.json();
    if (!job.id) throw new Error('horde: no job id — ' + JSON.stringify(job).slice(0, 200));
    for (let i = 0; i < 100; i++){
      await sleep(5000);
      const s = await fetch(HORDE + '/generate/status/' + job.id);
      const st = await s.json();
      if (st.done){
        const g = st.generations && st.generations[0];
        if (!g || !g.img) throw new Error('horde: done but no image');
        const blob = await (await fetch('data:image/jpeg;base64,' + g.img)).blob();
        if (blob.size < 3000) throw new Error('horde: empty image');
        const up = await fetch('/save?project=' + encodeURIComponent(PROJECT) +
          '&id=' + cardObj.id + '&model=' + encodeURIComponent('horde/' + (g.model || model)),
          { method: 'POST', body: blob });
        if (!up.ok) throw new Error('horde: save failed');
        return g.model || model;
      }
      const pos = st.queue_position != null ? st.queue_position : (st.processing ? 'processing' : '?');
      err.textContent = 'horde: ' + pos + ' ahead' + (st.wait_time ? ' (~' + st.wait_time + 's)' : '') +
                        ' — poll ' + (i + 1) + '/100';
    }
    throw new Error('horde: timed out after ~8 min');
  } catch(e){
    err.textContent = '❌ ' + e.message;
    if (card.querySelector('.uploadrow')) card.querySelector('.uploadrow').classList.add('show');
    return null;
  }
}

function el(tag, cls, html){ const e=document.createElement(tag);
  if(cls) e.className=cls; if(html!=null) e.innerHTML=html; return e; }

function pad(n){ return String(n).padStart(3,'0'); }
const sleep = ms => new Promise(r => setTimeout(r, ms));

// --------------- settings (persisted in this browser only) ---------------
function saveSettings(){
  localStorage.setItem('ps_model', document.getElementById('modelSel').value);
  localStorage.setItem('ps_res', document.getElementById('resSel').value);
  localStorage.setItem('ps_style', document.getElementById('styleSel').value);
  localStorage.setItem('ps_key', document.getElementById('keyIn').value.trim());
}
function loadSettings(){
  const g = (id, def) => { const v = localStorage.getItem(id); return v || def; };
  document.getElementById('modelSel').value = g('ps_model','puter:auto');
  document.getElementById('resSel').value = g('ps_res','1536');
  document.getElementById('styleSel').value = g('ps_style','doodle');
  document.getElementById('keyIn').value = g('ps_key','');
}
['modelSel','resSel','styleSel','keyIn'].forEach(id =>
  document.getElementById(id).addEventListener('change', saveSettings));

const STYLE_SUFFIX = {
  doodle: ', hand-drawn doodle style: thick black outlines, flat bold colors, slightly imperfect hand-drawn lines, pure white background, no text, no watermark',
  rich: ', rich detailed illustration, crisp clean linework, vibrant colors, soft shading, cinematic lighting, clean composition, pure white background, no text, no watermark',
  photo: ', professional photorealistic render, dramatic natural lighting, sharp focus, high detail, clean studio background, no text, no watermark'
};

function chainFor(sel){
  if (sel === 'auto') return AUTO_CHAIN.slice();
  if (MODEL_IDS.includes(sel)){
    const i = MODEL_IDS.indexOf(sel);
    return MODEL_IDS.slice(i).concat(AUTO_CHAIN.filter(m => !MODEL_IDS.includes(m)));
  }
  return AUTO_CHAIN.slice();
}

async function fetchImage(id, prompt, model, res, key){
  // returns blob; throws on failure
  const seed = id * 13 + 7;
  const qs = 'model=' + model + '&width=' + res + '&height=' + res +
    '&nologo=true&seed=' + seed +
    ((model.startsWith('gpt') || model.indexOf('grok') === 0) ? '&quality=hd' : '') +
    (key ? '&key=' + encodeURIComponent(key) : '');
  let lastErr = null;
  for (const host of ['gen.pollinations.ai/image/',
                      'image.pollinations.ai/prompt/']){
    const url = 'https://' + host + encodeURIComponent(prompt) +
                (host.startsWith('gen') ? '?' : '?enhance=true&') + qs;
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const blob = await r.blob();
      if (blob.size < 3000) throw new Error('empty image');
      return blob;
    } catch(e){ lastErr = e; }
  }
  throw lastErr || new Error('network failed');
}

// ---------------- AUTO-RUN: no taps needed, best model with fallback ----
let autoRunning = false;

// ---------------- PUTER: free unlimited top-model generation ----------------
// Default engine. Works ANONYMOUSLY with a small free allowance; signing in
// once (free Puter account) raises it to the full monthly allowance +
// 30 req/10s. User-Pays: the logged-in user's own free account covers cost.
const PUTER_MODELS = {
  'puter:auto':               { provider: undefined,            model: undefined,
                                label: 'auto (gpt-image-1-mini default)' },
  'puter:openai/gpt-image-2': { provider: 'openai-image-generation', model: 'gpt-image-2', quality: 'high' },
  'puter:google/nano-banana-pro': { provider: 'gemini',         model: 'nano-banana-pro', quality: '1K' },
  'puter:black-forest-labs/flux-2-pro': { provider: 'replicate-image-generation', model: 'black-forest-labs/flux-2-pro' },
  'puter:xai/grok-imagine-image': { provider: 'xai',            model: 'grok-imagine-image', quality: '1k' },
  'puter:stabilityai/stable-diffusion-3.5': { provider: 'replicate-image-generation', model: 'stabilityai/stable-diffusion-3.5' },
};

async function puterSignedIn(){
  try { return !!(await window.puter.auth.isSignedIn()); } catch(e){ return false; }
}

async function puterSignIn(){
  // attempt_temp_user_creation: Puter can create a temporary guest account
  // with NO registration — the user just confirms. Docs verified.
  try {
    await window.puter.auth.signIn({ attempt_temp_user_creation: true });
    return { ok: true, code: null, msg: '' };
  } catch(e){
    const code = (e && (e.code || e.error)) || 'unknown';
    const msg = (e && (e.msg || e.message)) || '';
    return { ok: false, code, msg };
  }
}

async function refreshPuterStatus(){
  const st = document.getElementById('puterStatus');
  if (!window.puter){
    st.textContent = '⚠ Puter SDK did not load here (embedded preview often blocks it) — ' +
                     'open the studio in a NEW TAB, then it works.';
    const b = document.getElementById('puterBtn');
    if (b){ b.textContent = 'Open studio in new tab →'; b.onclick = () => window.open(window.location.href, '_blank'); }
    return false;
  }
  try {
    const ok = await puterSignedIn();
    if (ok){
      let u = '';
      try { const uu = await window.puter.auth.getUser(); u = uu ? ' — ' + (uu.username || uu.email || uu.uuid || '') : ''; } catch(e){}
      st.textContent = '✅ Signed in' + u + ' — unlimited free generation';
      document.getElementById('puterBtn').textContent = 'Signed in (tap to switch account)';
      return true;
    }
  } catch(e){}
  st.textContent = 'Not signed in — tap "Sign in to Puter" (guest account is automatic, no email needed)';
  return false;
}

async function genPuter(cardObj, modelId, fullPrompt, errEl, card){
  if (!window.puter){
    errEl.textContent = 'Puter SDK not loaded (js.puter.com blocked?)';
    return null;
  }
  const cfg = PUTER_MODELS[modelId] || { model: undefined };
  const opts = { prompt: fullPrompt, ratio: { w: 1, h: 1 } };
  if (cfg.provider) opts.provider = cfg.provider;
  if (cfg.model) opts.model = cfg.model;
  if (cfg.quality) opts.quality = cfg.quality;
  // anonymous-first: only prompt for sign-in if Puter itself refuses
  try {
    errEl.textContent = 'Puter: generating (free)…';
    const img = await window.puter.ai.txt2img(opts);
    if (!img || !img.src) throw new Error('Puter returned no image');
    const blob = await fetch(img.src).then(r => r.blob());
    if (blob.size < 3000) throw new Error('empty image from Puter');
    const up = await fetch('/save?project=' + encodeURIComponent(PROJECT) +
      '&id=' + cardObj.id + '&model=' + encodeURIComponent('puter/' + (cfg.model || 'auto')),
      { method:'POST', body: blob });
    if (!up.ok) throw new Error('save failed');
    return cfg.model || 'auto';
  } catch(e){
    const msg = (e && (e.message || e.msg || String(e))) || String(e);
    if (/popup.?block|blocked/i.test(msg) && /auth|sign|popup/i.test(msg)){
      errEl.innerHTML = 'Puter popup blocked by the embedded preview — open the studio in a ' +
                        '<a href="' + window.location.href + '" target="_blank" rel="noopener" ' +
                        'style="color:#7ee08a;font-weight:700">new tab</a> and it will just work.';
      return 'need_signin';
    }
    if (/sign|auth|login|credit|upgrade|402|subscription/i.test(msg)){
      errEl.textContent = 'Puter needs a free account: tap "🔑 Sign in to Puter" above (guest is automatic), then Retry.';
      document.getElementById('puterBtn').style.display = 'block';
      document.getElementById('puterStatus').textContent = 'Sign-in required — tap the button, guest account is automatic';
      return 'need_signin';
    }
    errEl.textContent = 'Puter: ' + msg.slice(0, 200);
    if (card.querySelector('.uploadrow')) card.querySelector('.uploadrow').classList.add('show');
    return null;
  }
}

async function genOne(cardObj, forceModel){
  // cardObj: {id, prompt} — returns {ok, model}
  const card = [...document.querySelectorAll('.card')].find(
      c => c.querySelector('.beat').textContent === 'BEAT ' + cardObj.id);
  const btn = card.querySelector('button.gen');
  const err = card.querySelector('.err');
  if (btn){ btn.disabled = true; btn.textContent = '⏳…'; }
  err.textContent = '';
  const style = document.getElementById('styleSel').value;
  const fullPrompt = cardObj.prompt + STYLE_SUFFIX[style] || cardObj.prompt;
  const key = document.getElementById('keyIn').value.trim();
  const res0 = parseInt(document.getElementById('resSel').value, 10) || 1536;

  const sel = forceModel || document.getElementById('modelSel').value;
  if (sel.startsWith('puter')){
    const res = await genPuter(cardObj, sel, fullPrompt, err, card);
    if (res && res !== 'need_signin'){
      const c = CARDS.find(c => c.id === cardObj.id); c.done = true; c.model = 'puter/' + res;
      err.textContent = '';
      render();
      return { ok:true, model:'puter/' + res };
    }
    if (res === 'need_signin'){
      // wait (up to ~5 min) for the user to tap Sign in, then resume
      err.textContent = '⏸ waiting for Puter sign-in…';
      const t0 = Date.now();
      while (Date.now() - t0 < 300000){
        await sleep(2000);
        if (await puterSignedIn()){
          err.textContent = '✅ signed in — generating…';
          return genOne(cardObj, sel);   // retry with session
        }
        refreshPuterStatus();
      }
      err.textContent = 'sign-in timed out — tap Retry after signing in';
      if (btn){ btn.disabled = false; btn.textContent = '🔄 Retry'; }
      return { ok:false, model:null };
    }
    if (btn){ btn.disabled = false; btn.textContent = '🔄 Retry'; }
    return { ok:false, model:null };
  }
  if (sel.startsWith('horde')){
    const got = await genHorde(cardObj, fullPrompt, err, card, sel);
    if (got){
      const c = CARDS.find(c => c.id === cardObj.id); c.done = true; c.model = 'horde/' + got;
      err.textContent = '';
      render();
      return { ok:true, model:'horde/' + got };
    }
    if (btn){ btn.disabled = false; btn.textContent = '🔄 Retry'; }
    return { ok:false, model:null };
  }
  let chain;
  if (sel === 'auto'){
    chain = AUTO_CHAIN.slice();
  } else {
    const i = MODEL_IDS.indexOf(sel);
    chain = (i >= 0 ? MODEL_IDS.slice(i) : []).concat(AUTO_CHAIN.filter(m => !MODEL_IDS.includes(m)));
    chain = chain.filter((m, j, a) => a.indexOf(m) === j);
  }
  let lastErr = 'no models tried';
  for (const model of chain){
    if (model.startsWith('horde')){
      const got = await genHorde(cardObj, fullPrompt, err, card, model);
      if (got) return { ok:true, model:'horde/' + got };
      continue;
    }
    for (const res of [res0, 1024]){   // on failure, drop resolution
      err.textContent = 'trying ' + model + ' @ ' + res + '…';
      try {
        const blob = await fetchImage(cardObj.id, fullPrompt, model, res, key);
        const up = await fetch('/save?project=' + encodeURIComponent(PROJECT) +
          '&id=' + cardObj.id + '&model=' + encodeURIComponent(model),
          { method:'POST', body: blob });
        if (!up.ok) throw new Error('save failed');
        const c = CARDS.find(c => c.id === cardObj.id); c.done = true;
        c.model = model;
        err.textContent = '';
        render();
        return { ok:true, model };
      } catch(e){ lastErr = model + '@' + res + ': ' + e.message; }
    }
  }
  err.textContent = '❌ all models failed (' + lastErr.slice(-140) + ') — tap Retry or Upload.';
  if (btn){ btn.disabled = false; btn.textContent = '🔄 Retry'; }
  card.querySelector('.uploadrow').classList.add('show');
  return { ok:false, model:null };
}

async function autoRunAll(){
  if (autoRunning) return;
  autoRunning = true;
  saveSettings();
  if (navigator.wakeLock){
    try { await navigator.wakeLock.request('screen'); } catch(e){}
  }
  const pending = CARDS.filter(c => !c.done);
  if (!pending.length){
    document.getElementById('status').textContent = '✅ All images already done.';
    return;
  }
  document.getElementById('status').textContent =
      '▶ AUTO-RUN: ' + pending.length + ' images — keep this tab open, no taps needed';
  const CONC = 2; let idx = 0;
  async function worker(){
    while (true){
      const next = idx++;
      if (next >= pending.length) return;
      await genOne(pending[next], null);
    }
  }
  await Promise.all([worker(), worker()]);
  autoRunning = false;
  const left = CARDS.filter(c => !c.done).length;
  document.getElementById('status').textContent =
      left ? '⏸ ' + left + ' failed — tap Retry on those cards.' :
             '✅ BATCH COMPLETE — all images saved with best available models!';
}

// auto-start shortly after the page loads
setTimeout(() => {
  loadSettings();
  if (!autoRunning && CARDS.some(c => !c.done)){
    const sb = document.getElementById('startbtn');
    if (sb){ sb.style.display = 'block';
      sb.onclick = () => { sb.style.display = 'none'; autoRunAll(); }; }
    setTimeout(() => { if (!autoRunning) autoRunAll(); }, 2000);
  }
}, 1200);

document.getElementById('regenbtn').onclick = () => {
  if (!confirm('Generate ALL ' + CARDS.length + ' images with the chosen model? ' +
               'This overwrites the current images (2-5 min).')) return;
  CARDS.forEach(c => { c.done = false; });
  render();
  autoRunAll();
};

// ---- Puter sign-in button (must be called from a user tap) ----
const pBtn = document.getElementById('puterBtn');
pBtn.onclick = async () => {
  if (!window.puter){
    window.open(window.location.href, '_blank');
    return;
  }
  pBtn.textContent = '⏳ opening sign-in…';
  const r = await puterSignIn();
  const st = document.getElementById('puterStatus');
  if (r.ok){
    pBtn.textContent = '✅ Signed in!';
    st.textContent = 'Signed in — unlimited. Auto-run continues.';
    refreshPuterStatus();
    // kick any pending auto-run
    if (!autoRunning && CARDS.some(c => !c.done)) autoRunAll();
  } else if (r.code === 'popup_blocked' || /blocked/i.test(r.msg)){
    pBtn.textContent = '🔑 Sign in (blocked here — see below)';
    st.innerHTML = '❌ <b>Popup blocked by the embedded preview.</b> The phone-studio lives ' +
                   'inside a frame that blocks popups. Fix: open it in a real tab — ' +
                   'tap here → ' +
                   '<a href="' + window.location.href + '" target="_blank" rel="noopener" ' +
                   'style="color:#7ee08a;font-weight:700">open studio in new tab</a> ' +
                   'and sign in there once. Popups work fine in a normal tab.';
  } else if (r.code === 'auth_window_closed'){
    pBtn.textContent = '🔑 Sign in to Puter (one time, free)';
    st.textContent = 'The sign-in window was closed before finishing — tap the button again and complete it.';
  } else {
    pBtn.textContent = '🔑 Sign in to Puter (one time, free)';
    st.textContent = 'Sign-in failed (' + r.code + ': ' + r.msg.slice(0,120) + ') — tap again, or open in a new tab.';
  }
};
refreshPuterStatus();

function render(){
  const wrap = document.getElementById('cards');
  wrap.innerHTML = '';
  let done = 0;
  CARDS.forEach(c => {
    const card = el('div', 'card' + (c.done ? ' done' : ''));
    card.appendChild(el('div','beat','BEAT ' + c.id));
    card.appendChild(el('div','prompt', c.prompt));
    if (c.done){
      card.appendChild(el('div','ok','✓ done — assets/' + pad(c.id) + '.png'));
      if (c.model) card.appendChild(el('div','modelused','model: ' + c.model));
      const im = el('img');
      im.src = '/img?project=' + encodeURIComponent(PROJECT) + '&id=' + c.id;
      im.style.cssText = 'width:100%;border-radius:8px;margin-top:8px;';
      card.appendChild(im);
      done++;
    } else {
      const b = el('button','gen','⚡ Generate image');
      b.onclick = () => { genOne(c, document.getElementById('modelSel').value); };
      card.appendChild(b);
      card.appendChild(el('div','err',''));
      const row = el('div','uploadrow');
      row.innerHTML = '<input type="file" accept="image/*"><button class="upload">⬆ Upload saved image</button>';
      const inp = row.querySelector('input');
      row.querySelector('button').onclick = () => uploadFile(inp, c.id, card);
      card.appendChild(row);
    }
    wrap.appendChild(card);
  });
  document.getElementById('prog').textContent = done + ' / ' + CARDS.length;
  document.getElementById('fill').style.width = (done / CARDS.length * 100) + '%';
}

async function uploadFile(inp, id, card){
  const f = inp.files[0]; const err = card.querySelector('.err');
  if (!f){ err.textContent = 'pick the saved image first'; return; }
  err.textContent = 'uploading…';
  try {
    const CHUNK = 512 * 1024;
    const total = Math.ceil(f.size / CHUNK);
    const name = 'beat' + pad(id) + '.png';
    for (let i = 0; i < total; i++){
      const r = await fetch('/chunk?name=' + encodeURIComponent(name) +
        '&index=' + i + '&total=' + total + '&project=' + encodeURIComponent(PROJECT) +
        '&id=' + id, { method:'POST', body: f.slice(i*CHUNK, (i+1)*CHUNK) });
      if (!r.ok) throw new Error('chunk ' + i + ' failed');
    }
    const d = await fetch('/done?name=' + encodeURIComponent(name) + '&total=' + total +
      '&project=' + encodeURIComponent(PROJECT) + '&id=' + id, { method:'POST' });
    if (!d.ok) throw new Error('assembly failed');
    const c = CARDS.find(c => c.id === id); c.done = true; c.model = 'upload';
    render();
  } catch(e){ err.textContent = '❌ ' + e.message; }
}

render();
</script>
</body>
</html>
"""


def safe_name(name):
    return re.sub(r"[^\w.\-]", "_", name or "file") or "file"


def project_names():
    out = []
    for d in sorted(PROJECTS.iterdir()):
        if (d / "prompts.json").exists():
            out.append(d.name)
    return out


def project_meta(name):
    d = PROJECTS / safe_name(name)
    pf, imf = d / "prompts.json", d / "images.json"
    if not pf.exists():
        return None
    prompts = json.loads(pf.read_text())
    images = json.loads(imf.read_text()) if imf.exists() else []
    done = {im["id"] for im in images if not im.get("error")}
    return {"name": d.name, "total": len(prompts), "done": len(done)}


def images_json(name):
    d = PROJECTS / safe_name(name)
    return json.loads((d / "images.json").read_text()) if (d / "images.json").exists() else []


def save_beat(project, bid, data, model="zimage"):
    d = PROJECTS / safe_name(project)
    (d / "assets").mkdir(parents=True, exist_ok=True)
    out = d / "assets" / f"{int(bid):03d}.png"
    out.write_bytes(data)
    images = images_json(project)
    images = [im for im in images if im["id"] != int(bid)]
    p = json.loads((d / "prompts.json").read_text())
    kw = next((x["keyword"] for x in p if x["id"] == int(bid)), "")
    images.append({"id": int(bid), "keyword": kw, "backend": "pollinations",
                   "file": f"assets/{out.name}", "source": "pollinations",
                   "model": model, "license": "Pollinations API (open-source models)",
                   "bytes": len(data)})
    images.sort(key=lambda x: x["id"])
    (d / "images.json").write_text(json.dumps(images, indent=2))
    write_credits(d, images)
    return out


def write_credits(d, images):
    used = [im for im in images if im.get("source")]
    if not used:
        return
    lines = ["# CREDITS — open-source artwork used by this project", ""]
    for im in sorted(used, key=lambda x: x["id"]):
        lines.append(f"- `{im['file']}` — **{im['keyword'][:60]}** — generated via "
                     f"Pollinations ({im.get('model', 'zimage')}) — {im['license']}")
    (d / "CREDITS.md").write_text("\n".join(lines) + "\n")


class Handler(http.server.BaseHTTPRequestHandler):
    def _q(self):
        return {k: v[0] for k, v in parse_qs(
            self.path.split("?", 1)[1]).items()} if "?" in self.path else {}

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_video(self, path):
        """Serve an mp4 with HTTP Range support so browsers can seek."""
        size = path.stat().st_size
        data = path.read_bytes()
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)", rng or "")
        if rng and m:
            start = int(m.group(1) or 0)
            end = int(m.group(2) or size - 1)
            end = min(end, size - 1)
            chunk = data[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        q = self._q()
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            projects = project_names()
            cards = ""
            for n in projects:
                m = project_meta(n)
                if not m:
                    continue
                watch = ""
                if (PROJECTS / m["name"] / "final.mp4").exists():
                    watch = (f'<a style="display:inline-block;margin-top:8px;padding:8px 14px;'
                             f'background:#f5c63c;color:#000;font-weight:700;border-radius:10px;'
                             f'text-decoration:none" href="/watch?project={quote(m["name"])}">'
                             f'▶ Watch video</a>')
                cards += (f'<div style="margin:10px 20px;padding:16px;background:#161a2b;'
                          f'border-radius:12px;color:#eee;text-align:center">'
                          f'<b>{m["name"]}</b> — {m["done"]}/{m["total"]} done<br>'
                          f'<a style="display:inline-block;margin-top:8px;padding:8px 14px;'
                          f'background:#2a3045;color:#eee;font-weight:700;border-radius:10px;'
                          f'text-decoration:none" href="/studio?project={quote(m["name"])}">'
                          f'🎨 Image studio</a> {watch}</div>')
            html = ("<!doctype html><html><head><meta charset=utf-8>"
                    "<meta name=viewport content='width=device-width,initial-scale=1'>"
                    "<title>Phone studio</title></head><body style='background:#0d0f1a;"
                    "color:#eee;font-family:system-ui;padding:20px 0'>"
                    "<h1 style='font-size:19px;text-align:center'>🎨 Phone studio — "
                    "pick a project</h1>" + cards +
                    "<div style='margin:24px 20px;padding:16px;background:#161a2b;"
                    "border-radius:12px;color:#eee;text-align:center'>"
                    "<b>🎵 Meme sounds</b> — tap to download on your phone, then Upload below<br>"
                    "<div style='margin-top:8px'>"
                    "<a href='https://www.myinstants.com/media/sounds/shark-bait-hoo-ha-ha-mp3cut.mp3' "
                    "target='_blank' rel='noopener' style='display:inline-block;margin:4px;padding:8px 12px;"
                    "background:#2a3045;border-radius:8px;color:#7ee08a;text-decoration:none'>"
                    "🦈 Shark Bait Hoo Ha Ha</a>"
                    "<a href='https://www.myinstants.com/en/search/?name=shark' "
                    "target='_blank' rel='noopener' style='display:inline-block;margin:4px;padding:8px 12px;"
                    "background:#2a3045;border-radius:8px;color:#7ee08a;text-decoration:none'>"
                    "🔎 More shark sounds (MyInstants)</a>"
                    "<a href='https://zapsplat.com/?s=underwater' target='_blank' rel='noopener' "
                    "style='display:inline-block;margin:4px;padding:8px 12px;background:#2a3045;"
                    "border-radius:8px;color:#7ee08a;text-decoration:none'>"
                    "🌊 Royalty-free SFX (ZapSplat)</a></div>"
                    "<input type='file' id='upf' accept='audio/*,video/*,image/*' "
                    "style='width:100%;margin:14px 0 8px'>"
                    "<button class='upload' id='upbtn' style='width:100%;padding:12px;border:0;"
                    "border-radius:10px;background:#f5c63c;color:#000;font-weight:700'>"
                    "⬆ Upload meme sound / file → uploads/</button>"
                    "<div id='upst' style='font-size:12px;color:#9aa;margin-top:8px'></div>"
                    "<div style='font-size:11px;color:#778;margin-top:10px'>Uploads land in "
                    "<b>uploads/</b> — tell me what you uploaded and I'll mix it into the video. "
                    "MyInstants sounds are fan rips (Content-ID risk); ZapSplat/Pixabay are "
                    "royalty-free and safe.</div></div>"
                    "</body></html>"
                    "<script>"
                    "const upf=document.getElementById('upf'),upb=document.getElementById('upbtn'),"
                    "upst=document.getElementById('upst');"
                    "upb.onclick=async()=>{const f=upf.files[0];if(!f){upst.textContent='pick a file first';return;}"
                    "const CHUNK=512*1024,total=Math.ceil(f.size/CHUNK),name=encodeURIComponent(f.name);"
                    "upst.textContent='uploading 0/'+total;"
                    "try{for(let i=0;i<total;i++){const r=await fetch('/chunk?name='+name+'&index='+i+'&total='+total,"
                    "{method:'POST',body:f.slice(i*CHUNK,(i+1)*CHUNK)});if(!r.ok)throw Error('chunk '+i);"
                    "upst.textContent='uploading '+(i+1)+'/'+total;}"
                    "const d=await fetch('/done?name='+name+'&total='+total,{method:'POST'});if(!d.ok)throw Error('done');"
                    "upst.textContent='✅ uploaded '+f.name+' → uploads/';}"
                    "catch(e){upst.textContent='❌ '+e.message;}};"
                    "</script>")
            self._send(200, html)
        elif path == "/watch":
            meta = project_meta(q.get("project", ""))
            if not meta:
                self._send(404, "unknown project")
                return
            f = PROJECTS / meta["name"] / "final.mp4"
            if not f.exists():
                self._send(404, "no final.mp4 yet — build it first")
                return
            html = (f"<!doctype html><html><head><meta charset=utf-8>"
                    f"<meta name=viewport content='width=device-width,initial-scale=1'>"
                    f"<title>▶ {meta['name']}</title><style>"
                    f"body{{margin:0;background:#0d0f1a;color:#eee;font-family:system-ui;"
                    f"display:flex;flex-direction:column;align-items:center;padding:20px 0}}"
                    f"h1{{font-size:18px;margin:0 0 12px}}"
                    f"video{{width:100%;max-width:960px;border-radius:12px;background:#000}}"
                    f"p{{color:#778;font-size:12px}}</style></head><body>"
                    f"<h1>▶ {meta['name']}</h1>"
                    f'<video controls autoplay playsinline preload="auto" '
                    f'src="/media?project={quote(meta["name"])}"></video>'
                    f"<p>If it doesn't start, tap play. 1:42 · 1280x720 · H.264 + AAC</p>"
                    f"</body></html>")
            self._send(200, html)
        elif path == "/media":
            meta = project_meta(q.get("project", ""))
            if not meta:
                self._send(404, "unknown project")
                return
            f = PROJECTS / meta["name"] / "final.mp4"
            if not f.exists():
                self._send(404, "no final.mp4 yet")
                return
            self._send_video(f)
        elif path == "/studio":
            meta = project_meta(q.get("project", ""))
            if not meta:
                self._send(404, "unknown project")
                return
            d = PROJECTS / meta["name"]
            prompts = json.loads((d / "prompts.json").read_text())
            done_ids = {im["id"] for im in images_json(meta["name"])
                        if not im.get("error")}
            cards = [{"id": p["id"], "prompt": p["keyword"],
                      "done": p["id"] in done_ids} for p in prompts]
            self_url = "http://" + (self.headers.get("Host") or f"localhost:{PORT}") + self.path
            html = (PAGE.replace("{{PROJECT}}", meta["name"])
                        .replace("{{PROJECT_JSON}}",
                                 json.dumps(meta["name"]))
                        .replace("{{CARDS_JSON}}", json.dumps(cards))
                        .replace("{{SELF_URL}}", self_url))
            self._send(200, html)
        elif path == "/img":
            d = PROJECTS / safe_name(q.get("project", ""))
            f = d / "assets" / f"{int(q.get('id', 0)):03d}.png"
            if f.exists():
                self._send(200, f.read_bytes(), "image/png")
            else:
                self._send(404, "not yet")
        else:
            self._send(404, "nope")

    def _read(self, limit):
        chunks, got = [], 0
        while got < limit:
            c = self.rfile.read(min(65536, limit - got))
            if not c:
                break
            chunks.append(c)
            got += len(c)
        return b"".join(chunks)

    def do_POST(self):
        q = self._q()
        path = self.path.split("?", 1)[0]
        try:
            if path == "/save":
                length = int(self.headers.get("Content-Length", 0))
                data = self._read(length)
                model = q.get("model", "zimage")[:40]
                out = save_beat(q.get("project", ""), int(q.get("id", 0)),
                                data, model)
                print(f"SAVE beat {q.get('id')} [{model}] -> {out} ({len(data)} B)",
                      flush=True)
                self._send(200, "ok")
            elif path == "/chunk":
                self._chunk(q)
            elif path == "/done":
                self._done(q)
            else:
                self._send(404, "nope")
        except Exception as e:
            print("ERR", e, flush=True)
            self._send(500, str(e)[:200])

    def _chunk(self, q):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_CHUNK:
            self._send(413, "too big"); return
        data = self._read(length)
        PARTS_DIR.mkdir(parents=True, exist_ok=True)
        name = safe_name(q.get("name", "f"))
        part = PARTS_DIR / f"{name}.{int(q.get('index', 0)):05d}"
        part.write_bytes(data)
        self._send(200, "ok")

    def _done(self, q):
        name = safe_name(q.get("name", "f"))
        total = int(q.get("total", 0))
        parts = []
        for i in range(total):
            part = PARTS_DIR / f"{name}.{i:05d}"
            if not part.exists():
                self._send(400, f"missing part {i}"); return
            parts.append(part.read_bytes())
        data = b"".join(parts)
        project, bid = q.get("project", ""), q.get("id", "")
        if project and bid:
            out = save_beat(project, int(bid), data)
            print(f"UPLOAD beat {bid} -> {out} ({len(data)} B)", flush=True)
        else:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest = UPLOAD_DIR / name
            dest.write_bytes(data)
            print(f"UPLOAD {len(data)/1e6:.1f} MB -> {dest}", flush=True)
        for part in PARTS_DIR.glob(f"{name}.*"):
            part.unlink()
        self._send(200, "done")

    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] " + fmt % args + "\n")


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"phone studio on :{PORT}  projects: {project_names()}", flush=True)
    srv.serve_forever()
