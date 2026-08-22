/* Reference Studio — frontend logic. All requests are relative to this origin. */

const $ = (sel) => document.querySelector(sel);
const state = { videos: [], combined: null, current: null, selected: null, polling: null };

const MOTION_COLORS = {
  frozen_hold: "#8fd14f",
  character_or_graphic_animation: "#74c0fc",
  subtle_local_motion: "#9775fa",
  whole_canvas_slide: "#ffa94d",
  short_graphic_sting: "#ffd43b",
  whole_scene_zoom_in: "#ff6b6b",
  whole_scene_zoom_out: "#ff8787",
};

const MOTION_LABEL = {
  frozen_hold: "frozen hold",
  character_or_graphic_animation: "character/graphic",
  subtle_local_motion: "subtle local",
  whole_canvas_slide: "canvas slide",
  short_graphic_sting: "sting",
  whole_scene_zoom_in: "zoom in",
  whole_scene_zoom_out: "zoom out",
};

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

/* ------------------------------------------------------------------ studio */

async function refresh() {
  try {
    const data = await api("/api/studio");
    state.videos = data.videos || [];
    state.combined = data.combined || null;
    state.current = data.current || null;
    renderList();
    renderCurrent();
    renderCombined();
    if (state.selected) {
      const card = state.videos.find((v) => v.id === state.selected);
      if (card) renderDetail(card); else renderDetail(null);
    }
    const busy = state.videos.some((v) => v.status === "queued" || v.status === "analyzing")
      || data.queue_depth > 0;
    schedulePolling(busy);
  } catch (err) {
    console.error(err);
    schedulePolling(true);
  }
}

function schedulePolling(busy) {
  if (busy && !state.polling) {
    state.polling = setInterval(refresh, 2500);
  } else if (!busy && state.polling) {
    clearInterval(state.polling);
    state.polling = null;
  }
}

/* -------------------------------------------------------------------- list */

function renderList() {
  const list = $("#video-list");
  if (!state.videos.length) {
    list.innerHTML = `<div class="empty">No references yet.<br>Upload a video to measure its style.</div>`;
    return;
  }
  list.innerHTML = "";
  for (const v of state.videos) {
    const el = document.createElement("div");
    el.className = "video-item" + (state.selected === v.id ? " selected" : "");
    const poster = v.has_frames && v.has_frames.includes("contact-sheet.jpg")
      ? `<img class="vi-thumb" src="/api/videos/${v.id}/frames/contact-sheet.jpg" alt="">`
      : `<div class="vi-thumb">🎬</div>`;
    const meta = v.metrics
      ? `${fmtDuration(v.metrics.duration_seconds)} · ${v.metrics.width}×${v.metrics.height} · ${v.metrics.shot_count} shots`
      : (v.probe ? `${fmtDuration(v.probe.duration_seconds)} · ${v.probe.width}×${v.probe.height}` : "");
    let statusHtml = "";
    if (v.status === "analyzing") {
      const p = v.progress || {};
      statusHtml = `<span class="chip analyzing">analyzing ${Math.round(p.pct || 0)}%</span>
        <span class="vi-msg">${esc((p.message || "").slice(0, 60))}</span>`;
    } else if (v.status === "queued") {
      statusHtml = `<span class="chip queued">queued</span>`;
    } else if (v.status === "done") {
      statusHtml = `<span class="chip done">done</span>
        ${v.metrics ? `<span class="vi-pct">median shot ${v.metrics.median_shot}s</span>` : ""}`;
    } else if (v.status === "failed") {
      statusHtml = `<span class="chip failed">failed</span>`;
    } else {
      statusHtml = `<span class="chip interrupted">interrupted</span>`;
    }
    el.innerHTML = `
      ${poster}
      <div>
        <div class="vi-name" title="${esc(v.label)}">${esc(v.label)}</div>
        <div class="vi-meta">${meta}</div>
        <div class="vi-status">${statusHtml}</div>
      </div>`;
    el.onclick = () => { state.selected = v.id; renderList(); renderDetail(v); };
    list.appendChild(el);
  }
}

function renderCurrent() {
  const badge = $("#current-badge");
  if (!state.current) {
    badge.classList.add("hidden");
    return;
  }
  badge.classList.remove("hidden");
  badge.textContent = `▶ Current style: ${state.current.source_video} — pipeline uses its style_rules.json`;
  badge.title = state.current.style_rules;
}

function renderCombined() {
  const card = $("#combined-card");
  const body = $("#combined-body");
  if (!state.combined) { card.hidden = true; return; }
  card.hidden = false;
  const c = state.combined;
  body.innerHTML = `
    <div class="metric-grid" style="grid-template-columns:repeat(auto-fill,minmax(120px,1fr))">
      ${metric("videos", c.video_count)}
      ${metric("shots", c.total_detected_shots)}
      ${metric("median shot", c.median_shot_seconds + " s")}
      ${metric("WPM", c.median_recognized_wpm ?? "—")}
      ${metric("LUFS", c.median_integrated_lufs ?? "—")}
    </div>
    <div class="muted" style="margin-top:10px">Merged from all analyzed references. Open the style bible:</div>
    <div class="d-actions" style="margin-top:8px">
      <a class="btn small" href="/api/combined/file/style_rules.json" target="_blank">style_rules.json</a>
      <a class="btn small" href="/api/combined/file/combined.json" target="_blank">combined.json</a>
      <button class="btn small" id="promote-combined-btn">Use as current style</button>
    </div>`;
  $("#promote-combined-btn").onclick = promoteCombined;
}

async function promoteCombined() {
  const res = await fetch("/api/promote-combined", { method: "POST" });
  if (!res.ok) { alert("promote failed"); return; }
  await refresh();
}

/* ------------------------------------------------------------------ detail */

async function renderDetail(video) {
  const detail = $("#detail");
  if (!video) {
    detail.innerHTML = `<div class="empty-detail">
      <div class="empty-detail-glyph">◉</div>
      <h3>Every video you upload becomes a measured style bible</h3>
      <p class="muted">The analyzer scans every frame — shots and hard cuts, motion per shot,
        palette, linework width, composition, loudness, narration pace and cut-to-word timing —
        then writes a <code>style_rules.json</code> the video pipeline already understands.</p>
      <ol class="how">
        <li><b>1.</b> Upload one or more reference videos</li>
        <li><b>2.</b> The studio measures the style (frame-by-frame)</li>
        <li><b>3.</b> Promote a profile (or merge several) as the current style</li>
        <li><b>4.</b> The production pipeline builds new videos to those measured rules</li>
      </ol>
    </div>`;
    return;
  }
  const m = video.metrics || {};
  const p = video.progress || {};

  let head = "";
  if (video.status === "analyzing" || video.status === "queued") {
    head = `
      <div class="card">
        <h2>${video.status === "queued" ? "Queued" : "Analyzing"}</h2>
        <div class="row" style="gap:14px">
          <div class="bar" style="flex:1"><div id="job-bar-fill" style="height:100%;width:${p.pct || 0}%;background:linear-gradient(90deg,var(--accent),var(--green))"></div></div>
          <span style="color:var(--accent);font-weight:700">${Math.round(p.pct || 0)}%</span>
        </div>
        <div class="muted" style="margin-top:8px">${esc(p.message || "")}</div>
        <div class="muted" style="margin-top:8px">The analyzer scans every decoded frame: shot detection, per-shot motion, palette, stroke widths, loudness, narration pace and cut-to-word timing.</div>
      </div>`;
  } else if (video.status === "failed") {
    head = `<div class="flag warn">Analysis failed: <code>${esc(video.error || "unknown error")}</code></div>`;
  }

  const poster = video.has_frames.includes("contact-sheet.jpg")
    ? `/api/videos/${video.id}/frames/contact-sheet.jpg` : "";

  const threeBand = m.three_band && m.banner_staticness >= 0.85;
  const fmtFlags = [
    m.orientation === "vertical" ? "vertical 9:16" : "horizontal 16:9",
    threeBand ? "three-band layout detected" : (m.orientation === "vertical" ? "not three-band" : ""),
    m.title_strip_detected ? "persistent title strip" : "",
    m.transcript_available ? `transcript · ${m.word_count} words` : "no transcript (model missing)",
  ].filter(Boolean).join(" · ");

  detail.innerHTML = `
  <div class="detail-wrap">
    ${head}
    <div class="card">
      <div class="d-head">
        ${poster ? `<img class="poster" src="${poster}" alt="contact sheet">` : ""}
        <div style="flex:1;min-width:0">
          <h1 class="d-title">${esc(video.label)}</h1>
          <div class="d-sub">${esc(video.original_name)}</div>
          ${video.status === "done" ? `
          <div class="d-sub" style="margin-top:6px">${fmtFlags}</div>
          <div class="d-actions">
            <button class="btn primary" id="promote-btn">${isCurrent() ? "✓ Current style" : "Use as current style"}</button>
            <a class="btn" href="/api/videos/${video.id}/file/style_profile.md" target="_blank">Style profile (md)</a>
            <a class="btn" href="/api/videos/${video.id}/file/style_rules.json" target="_blank">style_rules.json</a>
            <a class="btn" href="/api/videos/${video.id}/file/shots.csv" target="_blank">shots.csv</a>
            <a class="btn" href="/api/videos/${video.id}/file/cuts.csv" target="_blank">cuts.csv</a>
            <button class="btn danger" id="delete-btn">Delete</button>
          </div>` : ""}
        </div>
      </div>
      ${video.status === "done" && video.metrics ? await detailBody(video) : ""}
    </div>
  </div>`;

  if (video.status === "done") {
    $("#promote-btn").onclick = () => promote(video.id);
    $("#delete-btn").onclick = () => remove(video.id);
  }
}

function isCurrent() {
  return state.current && state.current.video_id === state.selected;
}

async function detailBody(video) {
  const m = video.metrics;
  const pal = (m.palette || []).map((c) =>
    `<span class="swatch" style="background:${c.hex}" title="${c.hex} ${(c.relative_weight * 100).toFixed(1)}%"><span>${c.hex}</span></span>`).join("");
  const motionSegs = Object.entries(m.motion_pct || {})
    .filter(([, pct]) => pct > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([kind, pct]) =>
      `<div class="seg" style="width:${pct}%;background:${MOTION_COLORS[kind] || "#888"}" title="${MOTION_LABEL[kind] || kind}: ${pct}%">${pct >= 6 ? Math.round(pct) + "%" : ""}</div>`).join("");
  const motionLegend = Object.entries(m.motion_pct || {})
    .filter(([, pct]) => pct > 0)
    .map(([kind, pct]) => `<span><i style="background:${MOTION_COLORS[kind] || "#888"}"></i>${MOTION_LABEL[kind] || kind} ${pct}%</span>`).join("");

  let transcriptHtml = "";
  if (m.transcript_available) {
    try {
      const t = await (await fetch(`/api/videos/${video.id}/file/transcript.json`)).json();
      transcriptHtml = `<div class="transcript">${esc(t.text || "")}</div>`;
    } catch (_) {}
  }

  let chaptersHtml = "";
  if (m.chapters && m.chapters.length) {
    chaptersHtml = `<div class="chapter-list">${m.chapters.map((c) =>
      `<div class="chapter-item"><b>${c.start}</b>${esc(c.title || "")}</div>`).join("")}</div>`;
  }

  const frames = (video.has_frames || []).filter((f) => f.startsWith("evidence-"))
    .map((f) => `<img src="/api/videos/${video.id}/frames/${f}" alt="${f}" onclick="window.open(this.src)">`).join("");

  let reportHtml = "";
  try {
    const md = await (await fetch(`/api/videos/${video.id}/file/style_profile.md`)).text();
    reportHtml = `<div class="md-report">${mdToHtml(md)}</div>`;
  } catch (_) {}

  const hist = await shotHistogram(video.id);
  const trans = m.transition_counts || {};
  const totalTrans = Object.values(trans).reduce((a, b) => a + b, 0) || 1;

  return `
    <div style="margin-top:18px">
      <div class="detail-tabs">
        <button class="tab active" data-tab="overview">Overview</button>
        <button class="tab" data-tab="report">Style bible (md)</button>
        <button class="tab" data-tab="frames">Evidence frames</button>
        <button class="tab" data-tab="transcript">Transcript</button>
        <button class="tab" data-tab="chapters">Chapters</button>
      </div>

      <div id="tab-overview" class="tab-pane">
        <div class="metric-grid" style="margin-top:14px">
          ${metric("duration", fmtDuration(m.duration_seconds))}
          ${metric("shots / cuts", `${m.shot_count} / ${m.cut_count}`)}
          ${metric("median shot", m.median_shot + " s", `mean ${m.mean_shot}s`)}
          ${metric("narration pace", m.wpm != null ? m.wpm + " WPM" : "—")}
          ${metric("loudness", m.lufs != null ? m.lufs + " LUFS" : "—", m.true_peak != null ? `TP ${m.true_peak} dBTP` : "")}
          ${metric("cut→word offset", m.cut_word_offset_median != null ? m.cut_word_offset_median + " s" : "—", m.cuts_before_word_pct != null ? `${m.cuts_before_word_pct}% before word` : "")}
          ${metric("stroke @1920", m.stroke_1920_median != null ? m.stroke_1920_median + " px" : "—")}
          ${metric("white frames", m.majority_white_pct + "%")}
          ${metric("tempo", m.tempo != null ? Math.round(m.tempo) + " BPM" : "—")}
        </div>

        <h3>Motion budget</h3>
        <div class="motion-bar">${motionSegs || '<div class="seg" style="width:100%;background:#232a3b;color:#8b92a5">no motion detected</div>'}</div>
        <div class="motion-legend">${motionLegend}</div>

        <h3>Shot-length histogram</h3>
        ${hist}

        <h3>Transitions</h3>
        <div class="motion-legend">
          <span><i style="background:#8fd14f"></i>full-frame hard cut ${((trans.hard_cut_full_frame || 0) / totalTrans * 100).toFixed(1)}%</span>
          <span><i style="background:#74c0fc"></i>same-palette hard cut ${((trans.hard_cut_same_palette || 0) / totalTrans * 100).toFixed(1)}%</span>
          <span><i style="background:#ffd43b"></i>localized swap/pop ${((trans.localized_swap_or_pop || 0) / totalTrans * 100).toFixed(1)}%</span>
        </div>

        <h3>Measured palette</h3>
        <div class="palette-row" style="padding-top:12px">${pal || '<span class="muted">no dominant colors measured</span>'}</div>

        <h3>Composition</h3>
        <div class="muted">ink centroid x <b>${m.ink_centroid[0]}</b> · y <b>${m.ink_centroid[1]}</b> of frame</div>
      </div>

      <div id="tab-report" class="tab-pane hidden">${reportHtml || '<div class="muted">report not available</div>'}</div>
      <div id="tab-frames" class="tab-pane hidden"><div class="frames-row" style="margin-top:14px">${frames || '<span class="muted">no evidence frames</span>'}</div></div>
      <div id="tab-transcript" class="tab-pane hidden" style="margin-top:14px">${transcriptHtml || '<span class="muted">transcript unavailable — install tools/models/vosk-model-small-en-us-0.15 to enable word timings, WPM and cut-sync analysis</span>'}</div>
      <div id="tab-chapters" class="tab-pane hidden" style="margin-top:14px">${chaptersHtml || '<span class="muted">no chapter boundaries estimated</span>'}</div>
    </div>`;
}

function metric(k, v, sub) {
  return `<div class="metric"><div class="k">${k}</div><div class="v">${v}${sub ? ` <small>${sub}</small>` : ""}</div></div>`;
}

async function shotHistogram(id) {
  try {
    const { shots } = await api(`/api/videos/${id}/shots`);
    if (!shots.length) return "";
    const BINS = 24;
    const maxDur = Math.min(15, Math.max(...shots.map((s) => s.duration)));
    const counts = new Array(BINS).fill(0);
    for (const s of shots) {
      const idx = Math.min(BINS - 1, Math.floor(s.duration / maxDur * BINS));
      counts[idx]++;
    }
    const top = Math.max(...counts, 1);
    const cols = counts.map((c, i) => {
      const h = Math.max(2, Math.round(c / top * 100));
      return `<div class="col" style="height:${h}%" data-tip="${(i * maxDur / BINS).toFixed(1)}–${((i + 1) * maxDur / BINS).toFixed(1)}s · ${c} shot${c === 1 ? "" : "s"}"></div>`;
    }).join("");
    return `<div class="hist">${cols}</div><div class="muted" style="display:flex;justify-content:space-between"><span>0s</span><span>${maxDur.toFixed(0)}s+</span></div>`;
  } catch (_) { return ""; }
}

/* ----------------------------------------------------------------- actions */

async function promote(id) {
  try {
    await api(`/api/videos/${id}/promote`, { method: "POST" });
    await refresh();
  } catch (err) { alert(err.message); }
}

async function remove(id) {
  if (!confirm("Delete this reference and its analysis?")) return;
  try {
    await fetch(`/api/videos/${id}`, { method: "DELETE" });
    state.selected = null;
    await refresh();
  } catch (err) { alert(err.message); }
}

async function mergeAll() {
  try {
    await api("/api/combine", { method: "POST" });
    await refresh();
  } catch (err) { alert(err.message); }
}

/* ------------------------------------------------------------------ upload */

function setupUpload() {
  const dz = $("#dropzone");
  const input = $("#file-input");
  dz.onclick = () => input.click();
  input.onchange = () => input.files.length && uploadFiles([...input.files]);
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => {
    e.preventDefault(); dz.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => {
    e.preventDefault(); dz.classList.remove("dragover");
  }));
  dz.addEventListener("drop", (e) => uploadFiles([...e.dataTransfer.files]));
}

async function uploadFiles(files) {
  if (!files.length) return;
  const vids = files.filter((f) => /\.(mp4|mov|webm|mkv|m4v|avi|mpeg|mpg)$/i.test(f.name));
  const form = new FormData();
  for (const f of vids) form.append("files", f);
  if (!vids.length) { alert("No supported video files selected (mp4, mov, webm, mkv)."); return; }

  $("#upload-progress").classList.remove("hidden");
  $("#upload-status").textContent = `Uploading ${vids.length} file(s)…`;
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/upload");
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      $("#upload-bar-fill").style.width = Math.round(e.loaded / e.total * 100) + "%";
    }
  };
  xhr.onload = async () => {
    $("#upload-progress").classList.add("hidden");
    let result = null;
    try { result = JSON.parse(xhr.responseText); } catch (_) {}
    if (result) {
      const notes = [];
      for (const a of result.accepted || []) notes.push({ ok: true, text: `✓ ${a.name} — measuring style…` });
      for (const r of result.rejected || []) notes.push({ ok: false, text: `✗ ${r.name}: ${r.reason}` });
      $("#upload-notes").innerHTML = notes.map((n) =>
        `<div class="note ${n.ok ? "ok" : "bad"}">${esc(n.text)}</div>`).join("");
      if (result.accepted && result.accepted.length) {
        const first = result.accepted[0];
        state.selected = first.id;
      }
    }
    input.value = "";
    await refresh();
  };
  xhr.onerror = () => {
    $("#upload-progress").classList.add("hidden");
    alert("Upload failed — check the connection and try again.");
  };
  xhr.send(form);
}

/* ------------------------------------------------------------------- utils */

function fmtDuration(s) {
  if (s == null) return "—";
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.round(s % 60)).padStart(2, "0")}`;
}

function esc(text) {
  const div = document.createElement("div");
  div.textContent = String(text ?? "");
  return div.innerHTML;
}

function mdToHtml(md) {
  const lines = md.split("\n");
  let html = "";
  let inTable = false;
  let inList = false;
  let inCode = false;
  const inline = (s) => s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\*([^*]+)\*/g, "<i>$1</i>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  const closeTable = () => { if (inTable) { html += "</table>"; inTable = false; } };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.startsWith("```")) { inCode = !inCode; html += inCode ? "<pre><code>" : "</code></pre>"; continue; }
    if (inCode) { html += line.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "\n"; continue; }
    if (!line.trim()) { closeList(); closeTable(); continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      closeTable();
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${inline(line.replace(/^\s*[-*]\s+/, ""))}</li>`;
      continue;
    }
    if (line.startsWith("|") && line.trimEnd().endsWith("|")) {
      closeList();
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      if (cells.every((c) => /^:?-{2,}:?$/.test(c))) continue;
      const tag = inTable ? "td" : "th";
      if (!inTable) { html += "<table>"; inTable = true; }
      html += `<tr>${cells.map((c) => `<${tag}>${inline(c)}</${tag}>`).join("")}</tr>`;
      continue;
    }
    closeList(); closeTable();
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const level = h[1].length;
      html += `<h${Math.min(level + 1, 3)}>${inline(h[2])}</h${Math.min(level + 1, 3)}>`;
      continue;
    }
    if (/^(---|\*\*\*)\s*$/.test(line)) { html += "<hr>"; continue; }
    if (line.startsWith("> ")) { html += `<blockquote>${inline(line.slice(2))}</blockquote>`; continue; }
    html += `<p>${inline(line)}</p>`;
  }
  closeList(); closeTable();
  if (inCode) html += "</code></pre>";
  return html;
}

/* ------------------------------------------------------------------ tabbing */

document.addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  const wrap = tab.closest(".detail-wrap");
  if (!wrap) return;
  wrap.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
  wrap.querySelectorAll(".tab-pane").forEach((pane) => {
    pane.classList.toggle("hidden", pane.id !== "tab-" + tab.dataset.tab);
  });
});

/* -------------------------------------------------------------------- boot */

setupUpload();
$("#merge-btn").onclick = mergeAll;
refresh();
setInterval(() => {
  // keep the merge button visibility in sync
  const doneCount = state.videos.filter((v) => v.status === "done").length;
  $("#merge-btn").classList.toggle("hidden", doneCount < 2);
}, 1500);
