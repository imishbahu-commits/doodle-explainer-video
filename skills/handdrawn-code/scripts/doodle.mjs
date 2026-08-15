#!/usr/bin/env node
/**
 * doodle.mjs — compile a scene JSON into a hand-drawn SVG + PNG.
 *
 * Stack: rough.js (the hand-drawn primitive engine) + svgdom (headless SVG
 * DOM) + @resvg/resvg-js (vector rasteriser) + real handwriting fonts
 * (Caveat, Patrick Hand, Kalam — OFL licensed, shipped in ../fonts).
 *
 * Usage:
 *   node doodle.mjs scene.json [--out output-name] [--png-only|--svg-only]
 *
 * Scene JSON:
 * {
 *   "width": 1376, "height": 768,      // default 16:9
 *   "bg": "#FFFFFF",                    // flat background colour
 *   "seed": 7,                          // reproducible wobble
 *   "title": "OPTIONAL TOP BANNER",     // auto-drawn at top, hand-lettered
 *   "elements": [ ... ]                 // see ELEMENT TYPES below
 * }
 *
 * ELEMENT TYPES (x/y = centre unless noted):
 *   {"type":"label","x","y","text","size":72,"font":"caveat|patrick|kalam","rot":-2,"color":"#111111"}
 *   {"type":"stick","x","y","scale":1,"pose":"stand|point|raise|walk|sit"}
 *   {"type":"face","x","y","r":60,"mood":"plain|smile|worried"}
 *   {"type":"box","x","y","w","h","label","sub","fill":"#FFE0AC","fillStyle":"hachure"}
 *   {"type":"circle","x","y","r","fill"}
 *   {"type":"line","x1","y1","x2","y2"}                        // free line
 *   {"type":"arrow","x1","y1","x2","y2","label"}               // single head
 *   {"type":"doubleArrow","x1","y1","x2","y2","label"}         // measure arrow
 *   {"type":"giant","x","y","text","size":260}                 // one huge numeral
 *   {"type":"bubble","x","y","w","h","text","kind":"speech|thought","fromX","fromY"}
 *   {"type":"check","x","y","s":1}  {"type":"xmark","x","y","s":1,"color":"#E21C1C"}
 *   {"type":"brace","x1","y1","x2","y2"}                       // vertical panel brace
 *
 * Outputs: <name>.svg (vector, crisp) and <name>.png (2x supersampled).
 * PNG dimensions match the video pipeline's 16:9 band art, so scenes drop
 * straight into a doodle-explainer-video manifest.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import rough from "roughjs";
import { Resvg } from "@resvg/resvg-js";
import { inkPerson, inkSky, inkGround, inkHills, inkTree, inkWater,
         inkStars, inkMoon, inkRoom, inkMirror, inkSpeckle, inkFrame } from "./ink-elements.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FONTS = path.join(HERE, "..", "fonts");

// ------------------------------------------------------------ fake SVG DOM
// rough.js's SVG renderer only needs createElementNS / setAttribute /
// appendChild / textContent — a minimal fake DOM is more robust than svgdom
// and serialises exactly what we want.
class FakeNode {
  constructor(tag) {
    this.tag = tag;
    this.attrs = {};
    this.children = [];
    this._text = "";
    this.style = {};
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  appendChild(c) {
    const i = this.children.indexOf(c);
    if (i >= 0) this.children.splice(i, 1);
    this.children.push(c);
    return c;
  }
  set textContent(t) { this._text = String(t); }
  get textContent() { return this._text; }
  setAttributeNS(ns, k, v) { this.attrs[k] = String(v); }
  removeAttribute(k) { delete this.attrs[k]; }
  cloneNode() { return new FakeNode(this.tag); }
  get ownerDocument() { return doc; }
  serialize() {
    const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const attrStr = Object.entries(this.attrs)
      .map(([k, v]) => `${k}="${esc(v)}"`).join(" ");
    const open = `<${this.tag}${attrStr ? " " + attrStr : ""}`;
    if (this._text && !this.children.length) {
      return `${open}>${esc(this._text)}</${this.tag}>`;
    }
    if (!this.children.length) return `${open}/>`;
    return `${open}>${this.children.map((c) => c.serialize()).join("")}</${this.tag}>`;
  }
}
const doc = { createElementNS: (_ns, tag) => new FakeNode(tag) };

const INK = "#16161a";
const FONT_FAMILIES = {
  caveat: "Caveat",
  patrick: "Patrick Hand",
  kalam: "Kalam",
};

// ---- tiny seeded rng so every render of the same scene is identical -------
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function renderScene(scene) {
  const W = scene.width ?? 1376;
  const H = scene.height ?? 768;
  const bg = scene.bg ?? "#FFFFFF";
  const seed = scene.seed ?? Math.floor(Math.random() * 1e9);
  const rnd = mulberry32(seed);

  const window = doc;
  const document = doc;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("xmlns", SVG_NS);
  svg.setAttribute("width", W);
  svg.setAttribute("height", H);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const bgRect = document.createElementNS(SVG_NS, "rect");
  bgRect.setAttribute("x", 0); bgRect.setAttribute("y", 0);
  bgRect.setAttribute("width", W); bgRect.setAttribute("height", H);
  bgRect.setAttribute("fill", bg);
  svg.appendChild(bgRect);

  const rc = rough.svg(svg, {
    options: {
      seed: 1 + Math.floor(rnd() * 2 ** 30),
      roughness: scene.roughness ?? 1.3,
      bowing: scene.bowing ?? 1.0,
      strokeWidth: scene.strokeWidth ?? 4,
      stroke: INK,
      fillWeight: 2.2,
      hachureGap: 13,
      hachureAngle: -41,
    },
  });

  // Draw into a content group so the optional ink filter can wrap it all.
  const content = document.createElementNS(SVG_NS, "g");
  const append = (node) => content.appendChild(node);

  // ------------------------------------------------------------ text helper
  function text(el) {
    const t = document.createElementNS(SVG_NS, "text");
    t.setAttribute("x", el.x);
    t.setAttribute("y", el.y);
    t.setAttribute("font-family", FONT_FAMILIES[el.font ?? "caveat"]);
    t.setAttribute("font-size", el.size ?? 68);
    t.setAttribute("font-weight", el.font === "patrick" ? 400 : 700);
    t.setAttribute("fill", el.color ?? INK);
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("dominant-baseline", "middle");
    const rot = el.rot ?? (rnd() * 3 - 1.5);
    if (rot) t.setAttribute("transform", `rotate(${rot.toFixed(2)} ${el.x} ${el.y})`);
    t.textContent = el.text;
    return t;
  }

  // ----------------------------------------------------------- stick figure
  const ctx2 = { rc, rnd, append, text };
  function stick(el) {
    const s = el.scale ?? 1;
    const y = el.y;
    const headR = 46 * s;
    const headC = y - 205 * s;
    const neck = y - 159 * s;
    const hip = y - 55 * s;
    const feet = y + 60 * s;
    append(rc.circle(el.x, headC, headR * 2, {
      strokeWidth: 4.4 * s, roughness: 0.9, fill: "none",
    }));
    // dot eyes
    append(rc.circle(el.x - headR * 0.38, headC - headR * 0.05, 4.5 * s, { fill: INK, stroke: "none" }));
    append(rc.circle(el.x + headR * 0.38, headC - headR * 0.05, 4.5 * s, { fill: INK, stroke: "none" }));
    // spine
    append(rc.line(el.x, neck, el.x, hip, { strokeWidth: 5 * s }));
    const legSwing = 48 * s, legLen = 118 * s;
    if (el.pose === "walk") {
      append(rc.line(el.x, hip, el.x - legSwing * 1.1, hip + legLen));
      append(rc.line(el.x, hip, el.x + legSwing * 1.1, hip + legLen * 0.8));
      append(rc.line(el.x, neck + 30 * s, el.x - 60 * s, neck - 20 * s));
      append(rc.line(el.x, neck + 30 * s, el.x + 60 * s, neck - 20 * s));
    } else if (el.pose === "sit") {
      append(rc.line(el.x, hip, el.x - legSwing, hip + 30 * s));
      append(rc.line(el.x, hip, el.x + legSwing, hip + 30 * s));
      append(rc.line(el.x - legSwing, hip + 30 * s, el.x + legSwing, hip + 30 * s));
      append(rc.line(el.x, neck + 25 * s, el.x - 45 * s, neck + 45 * s));
      append(rc.line(el.x, neck + 25 * s, el.x + 45 * s, neck + 45 * s));
    } else if (el.pose === "point") {
      append(rc.line(el.x, hip, el.x - legSwing, hip + legLen));
      append(rc.line(el.x, hip, el.x + legSwing, hip + legLen));
      append(rc.line(el.x, neck + 25 * s, el.x + 95 * s, neck - 15 * s)); // pointing arm
      append(rc.line(el.x + 95 * s, neck - 15 * s, el.x + 150 * s, neck - 35 * s));
      append(rc.line(el.x, neck + 25 * s, el.x - 55 * s, neck + 55 * s));
    } else if (el.pose === "raise") {
      append(rc.line(el.x, hip, el.x - legSwing, hip + legLen));
      append(rc.line(el.x, hip, el.x + legSwing, hip + legLen));
      append(rc.line(el.x, neck + 25 * s, el.x - 55 * s, neck - 40 * s));
      append(rc.line(el.x, neck + 25 * s, el.x + 55 * s, neck - 40 * s));
    } else { // stand
      append(rc.line(el.x, hip, el.x - legSwing, hip + legLen));
      append(rc.line(el.x, hip, el.x + legSwing, hip + legLen));
      append(rc.line(el.x, neck + 25 * s, el.x - 50 * s, neck + 50 * s));
      append(rc.line(el.x, neck + 25 * s, el.x + 50 * s, neck + 50 * s));
    }
  }

  // ------------------------------------------------------------------ face
  function face(el) {
    const r = el.r ?? 60;
    append(rc.circle(el.x, el.y, r * 2, { roughness: 0.8, fill: "none", strokeWidth: 4.5 }));
    const ex = r * 0.38, ey = r * 0.15;
    append(rc.circle(el.x - ex, el.y - ey, 5, { fill: INK, stroke: "none" }));
    append(rc.circle(el.x + ex, el.y - ey, 5, { fill: INK, stroke: "none" }));
    if (el.mood === "worried") {
      append(rc.line(el.x - r * 0.45, el.y - r * 0.55, el.x - r * 0.05, el.y - r * 0.45));
      append(rc.line(el.x + r * 0.45, el.y - r * 0.55, el.x + r * 0.05, el.y - r * 0.45));
      append(rc.curve([
        [el.x - r * 0.4, el.y + r * 0.55], [el.x - r * 0.15, el.y + r * 0.2],
        [el.x + r * 0.15, el.y + r * 0.2], [el.x + r * 0.4, el.y + r * 0.55],
      ]));
    } else if (el.mood === "smile") {
      append(rc.curve([
        [el.x - r * 0.4, el.y + r * 0.5], [el.x - r * 0.15, el.y + r * 0.75],
        [el.x + r * 0.15, el.y + r * 0.75], [el.x + r * 0.4, el.y + r * 0.5],
      ]));
    } else {
      append(rc.line(el.x - r * 0.3, el.y + r * 0.5, el.x + r * 0.3, el.y + r * 0.5));
    }
  }

  // ------------------------------------------------------------------ box
  function box(el) {
    const x0 = el.x - el.w / 2, y0 = el.y - el.h / 2;
    append(rc.rectangle(x0, y0, el.w, el.h, {
      fill: el.fill ?? "#FFFFFF",
      fillStyle: el.fillStyle ?? "hachure",
      roughness: 0.9,
    }));
    if (el.label) append(text({
      x: el.x, y: el.y - (el.sub ? 14 : 0),
      text: el.label, size: el.labelSize ?? 58, font: "caveat", rot: -0.8,
    }));
    if (el.sub) append(text({
      x: el.x, y: el.y + el.h * 0.24, text: el.sub,
      size: 34, font: "patrick", rot: 0.6, color: "#4a4a55",
    }));
  }

  // ------------------------------------------------------- arrows & lines
  function arrowHead(cx, cy, ang, size = 26, color = INK) {
    const a1 = ang + Math.PI - 0.42, a2 = ang + Math.PI + 0.42;
    append(rc.polygon([
      [cx, cy],
      [cx + size * Math.cos(a1), cy + size * Math.sin(a1)],
      [cx + size * Math.cos(a2), cy + size * Math.sin(a2)],
    ], { fill: color, stroke: "none", fillStyle: "solid" }));
  }

  function arrow(el, double = false) {
    const ang = Math.atan2(el.y2 - el.y1, el.x2 - el.x1);
    const len = Math.hypot(el.x2 - el.x1, el.y2 - el.y1);
    const head = Math.min(30, len * 0.28);
    const tip = { x: el.x2, y: el.y2 };
    append(rc.line(el.x1, el.y1, el.x2 - head * Math.cos(ang), el.y2 - head * Math.sin(ang), {
      strokeWidth: 4.5, roughness: 1.1,
    }));
    arrowHead(tip.x, tip.y, ang);
    if (double) arrowHead(el.x1, el.y1, ang + Math.PI);
    if (el.label) {
      const mx = (el.x1 + el.x2) / 2, my = (el.y1 + el.y2) / 2;
      append(text({
        x: mx + 26 * -Math.sin(ang), y: my - 30,
        text: el.label, size: 38, font: "patrick", rot: 0,
      }));
    }
  }

  // --------------------------------------------------------------- bubble
  function bubble(el) {
    const x0 = el.x - el.w / 2, y0 = el.y - el.h / 2;
    append(rc.ellipse(el.x, el.y, el.w, el.h, { fill: "#FFFFFF", fillStyle: "solid", roughness: 0.9 }));
    append(text({ x: el.x, y: el.y, text: el.text, size: el.textSize ?? 40, font: "caveat", rot: -0.6 }));
    if (el.kind === "thought") {
      const dx = (el.fromX ?? el.x) - el.x, dy = (el.fromY ?? el.y + el.h) - el.y;
      const ang = Math.atan2(dy, dx), d = Math.hypot(dx, dy);
      for (let i = 0; i < 3; i++) {
        const p = 0.35 + i * 0.28;
        const r = 16 - i * 4;
        append(rc.circle(el.x + d * p * Math.cos(ang), el.y + d * p * Math.sin(ang), r * 2, {
          fill: "#FFFFFF", fillStyle: "solid", roughness: 0.7, strokeWidth: 3.4,
        }));
      }
    } else {
      const fx = el.fromX ?? el.x, fy = el.fromY ?? el.y + el.h / 2;
      append(rc.polygon([
        [fx - 26, fy - 14], [fx + 26, fy - 14], [fx, fy + 40],
      ], { fill: "#FFFFFF", fillStyle: "solid", roughness: 0.7, strokeWidth: 3.4 }));
    }
  }

  // ------------------------------------------------------------- dispatch
  const draw = {
    label: (e) => append(text(e)),
    stick, face, box, bubble,
    person: (e) => inkPerson(ctx2, e),
    sky: (e) => inkSky(ctx2, e),
    ground: (e) => inkGround(ctx2, e),
    hills: (e) => inkHills(ctx2, e),
    tree: (e) => inkTree(ctx2, e),
    water: (e) => inkWater(ctx2, e),
    stars: (e) => inkStars(ctx2, e),
    moon: (e) => inkMoon(ctx2, e),
    room: (e) => inkRoom(ctx2, e),
    mirror: (e) => inkMirror(ctx2, e),
    speckle: (e) => inkSpeckle(ctx2, e),
    frame: (e) => inkFrame(ctx2, e),
    circle: (e) => append(rc.circle(e.x, e.y, (e.r ?? 60) * 2, {
      fill: e.fill ?? "none", fillStyle: e.fillStyle ?? "hachure",
    })),
    line: (e) => append(rc.line(e.x1, e.y1, e.x2, e.y2)),
    arrow: (e) => arrow(e, false),
    doubleArrow: (e) => arrow(e, true),
    giant: (e) => append(text({
      x: e.x, y: e.y, text: e.text, size: e.size ?? 260,
      font: "kalam", rot: -2, color: e.color ?? INK,
    })),
    check: (e) => {
      const s = e.s ?? 1;
      append(rc.line(e.x - 34 * s, e.y + 4 * s, e.x - 8 * s, e.y + 30 * s, { stroke: "#128A4A", strokeWidth: 9 * s, roughness: 0.8 }));
      append(rc.line(e.x - 8 * s, e.y + 30 * s, e.x + 40 * s, e.y - 32 * s, { stroke: "#128A4A", strokeWidth: 9 * s, roughness: 0.8 }));
    },
    xmark: (e) => {
      const s = e.s ?? 1, c = e.color ?? "#D91B1B";
      append(rc.line(e.x - 30 * s, e.y - 30 * s, e.x + 30 * s, e.y + 30 * s, { stroke: c, strokeWidth: 9 * s, roughness: 0.8 }));
      append(rc.line(e.x - 30 * s, e.y + 30 * s, e.x + 30 * s, e.y - 30 * s, { stroke: c, strokeWidth: 9 * s, roughness: 0.8 }));
    },
    brace: (e) => {
      const mx = (e.x1 + e.x2) / 2;
      append(rc.line(e.x1, e.y1, mx, e.y1, { strokeWidth: 4 }));
      append(rc.line(e.x2, e.y1, mx, e.y1, { strokeWidth: 4 }));
      append(rc.curve([
        [mx - 8, e.y1 - 6], [mx - 4, (e.y1 + e.y2) / 2], [mx - 8, e.y2 + 6],
      ]));
      append(rc.curve([
        [mx + 8, e.y1 - 6], [mx + 4, (e.y1 + e.y2) / 2], [mx + 8, e.y2 + 6],
      ]));
    },
  };

  if (scene.title) {
    append(text({ x: W / 2, y: 84, text: scene.title, size: 84, font: "caveat", rot: -1 }));
    append(rc.line(W / 2 - 300, 132, W / 2 + 300, 132, { strokeWidth: 4, roughness: 0.8 }));
  }
  for (const el of scene.elements ?? []) {
    const fn = draw[el.type];
    if (!fn) throw new Error(`unknown element type: ${el.type}`);
    fn(el);
  }

  // Optional hand-drawn ink wobble (feTurbulence + feDisplacementMap) over
  // the whole drawing. Scale 1.5-3 reads as a slightly nervous pen hand.
  // Kept in the SVG only: resvg's displacement at 2x raster is memory-hungry,
  // and rough.js already wobbles every stroke in the PNG.
  if (scene.ink > 0 && scene.inkSvg !== false) {
    const defs = document.createElementNS(SVG_NS, "defs");
    const filter = document.createElementNS(SVG_NS, "filter");
    filter.setAttribute("id", "inkwobble");
    filter.setAttribute("x", "-5%"); filter.setAttribute("y", "-5%");
    filter.setAttribute("width", "110%"); filter.setAttribute("height", "110%");
    const turb = document.createElementNS(SVG_NS, "feTurbulence");
    turb.setAttribute("type", "fractalNoise");
    turb.setAttribute("baseFrequency", scene.inkFreq ?? "0.012");
    turb.setAttribute("numOctaves", "2");
    turb.setAttribute("seed", String(seed));
    turb.setAttribute("result", "noise");
    const disp = document.createElementNS(SVG_NS, "feDisplacementMap");
    disp.setAttribute("in", "SourceGraphic");
    disp.setAttribute("in2", "noise");
    disp.setAttribute("scale", String(scene.ink));
    disp.setAttribute("xChannelSelector", "R");
    disp.setAttribute("yChannelSelector", "G");
    filter.appendChild(turb);
    filter.appendChild(disp);
    defs.appendChild(filter);
    svg.appendChild(defs);
    content.setAttribute("filter", "url(#inkwobble)");
  }
  svg.appendChild(content);

  return { svg, document };
}

function svgString(scene) {
  const { svg } = renderScene(scene);
  // rough.js marks fills evenodd; its wobbled closed curves self-intersect,
  // which makes evenodd cancel the whole fill. Nonzero keeps fills solid.
  return svg.serialize().replace(/fill-rule="evenodd"/g, 'fill-rule="nonzero"');
}

export function renderFiles(scene, outName) {
  const W = scene.width ?? 1376, H = scene.height ?? 768;
  const str = svgString(scene);
  const svgPath = `${outName}.svg`;
  fs.writeFileSync(svgPath, str);

  // PNG raster: drop the displacement filter (memory) — rough.js wobble stays.
  const pngScene = scene.ink > 0 ? { ...scene, inkSvg: false } : scene;
  const fontFiles = fs.readdirSync(FONTS).filter((f) => f.endsWith(".ttf"))
    .map((f) => path.join(FONTS, f));
  const resvg = new Resvg(svgString(pngScene), {
    font: { fontFiles, loadSystemFonts: false, defaultFontFamily: "Caveat" },
    fitTo: { mode: "zoom", value: 2 },
  });
  const png = resvg.render().asPng();
  fs.writeFileSync(`${outName}.png`, png);
  return { svgPath, pngPath: `${outName}.png`, width: W, height: H };
}

// ------------------------------------------------------------------- CLI
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const scenePath = args.find((a) => !a.startsWith("--"));
  if (!scenePath) {
    console.error("usage: node doodle.mjs scene.json [--out name]");
    process.exit(1);
  }
  const outIdx = args.indexOf("--out");
  const outName = outIdx >= 0 ? args[outIdx + 1] : scenePath.replace(/\.json$/, "");
  const scene = JSON.parse(fs.readFileSync(scenePath, "utf8"));
  const r = renderFiles(scene, outName);
  console.log(`wrote ${r.svgPath} and ${r.pngPath} (${r.width}x${r.height} at 2x)`);
}
