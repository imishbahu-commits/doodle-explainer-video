// ink-elements.mjs — v2 hand-drawn characters & scenes for the
// handdrawn-code skill.
//
// Original hand-built character system in the spirit of modular hand-drawn
// libraries (like Pablo Stanley's Open Peeps, CC0 — we took the *idea* of
// mix-and-match parts, all paths here are our own drawings): heads with
// hair, eyes/brows/mouths per emotion, outfits, cartoon limbs with bend
// elbows/knees, mitten hands, shoes — plus hand-drawn scenery (sky, sun,
// clouds, hills, ground, water, trees, room, mirror, stars, speckle, frame).
//
// Every stroke goes through rough.js (wobble + overdraw) and an optional
// ink filter (feTurbulence + feDisplacementMap) so the result reads as
// someone's pen, not a machine.

// ------------------------------------------------------------------ palettes
export const SKINS = {
  light: "#F6D7C0", tan: "#E8B48C", brown: "#C68863",
  deep: "#8D5A3B", dark: "#5C3A21",
};
export const HAIRS = {
  black: "#2C2A26", brown: "#6B4A2E", ginger: "#C68B3F",
  grey: "#E8E3DA", slate: "#4A4A55", auburn: "#B03A2E",
};
export const OUTFITS = {
  blue: "#3F81B2", orange: "#F2A63B", red: "#D9534F",
  green: "#4E9A51", purple: "#7A5FA8", grey: "#9AA0A6",
  navy: "#24455C", mustard: "#D9A13B",
};
const INK = "#16161a";
const SHOE = "#33333B";
const WHITE = "#FFFFFF";

// ------------------------------------------------------------- tiny helpers
function jitter(rnd, n) { return (rnd() - 0.5) * 2 * n; }

// Map a local point through translate/scale/flip
function mapper(x, y, s, flip) {
  return (px, py) => [x + (flip ? -px : px) * s, y + py * s];
}

// --------------------------------------------------------------- character
export function inkPerson(ctx, el) {
  const { rc, rnd, append } = ctx;
  const x = el.x, y = el.y;               // feet centre
  const s = ((el.scale ?? 1) * (el.height ?? 560)) / 560;
  const flip = el.flip ? -1 : 1;
  const M = mapper(x, y, s, flip);

  const skin = SKINS[el.skin ?? "light"];
  const hair = HAIRS[el.hairColor ?? "brown"];
  const outfit = OUTFITS[el.outfit ?? "blue"];
  const outfit2 = OUTFITS[el.outfit2 ?? "navy"];
  const emotion = el.emotion ?? "neutral";
  const hairStyle = el.hair ?? "short";
  const cloth = el.cloth ?? "shirt";
  const pose = el.pose ?? "stand";

  const P = (pts) => pts.map((p) => M(p[0], p[1]));
  // open rough curve (stroke only)
  const line = (pts, w = 5, roughness = 0.7) => {
    append(rc.curve(P(pts), { stroke: INK, strokeWidth: w * s, roughness, fill: "none" }));
  };
  // closed filled shape with wobbled outline
  const shape = (pts, fill, roughness = 0.7, w = 5) => {
    append(rc.curve(P(pts.concat([pts[0]])), {
      stroke: INK, strokeWidth: w * s, roughness,
      fill: fill ?? "none", fillStyle: "solid",
    }));
  };
  const dot = (px, py, r, fill, roughness = 0.5) => {
    const [cx, cy] = M(px, py);
    append(rc.circle(cx, cy, r * 2 * s, { fill, stroke: "none", roughness }));
  };
  // cartoon limb: two segments with an elbow/knee bend, uniform width
  const limb = (a, mid, b, w, color) => {
    append(rc.line(...M(a[0], a[1]), ...M(mid[0], mid[1]),
      { stroke: color, strokeWidth: w * s, roughness: 0.5 }));
    append(rc.line(...M(mid[0], mid[1]), ...M(b[0], b[1]),
      { stroke: color, strokeWidth: w * s, roughness: 0.5 }));
    // outline passes over the colour so limbs read as drawn, not shapes
    append(rc.line(...M(a[0], a[1]), ...M(mid[0], mid[1]),
      { stroke: INK, strokeWidth: 4.5 * s, roughness: 0.5 }));
    append(rc.line(...M(mid[0], mid[1]), ...M(b[0], b[1]),
      { stroke: INK, strokeWidth: 4.5 * s, roughness: 0.5 }));
  };
  const hand = (px, py, r = 11) => {
    const [cx, cy] = M(px, py);
    append(rc.circle(cx, cy, r * 2 * s, { fill: skin, stroke: INK, strokeWidth: 4 * s, roughness: 0.4 }));
    // thumb
    const [tx, ty] = M(px + r * 0.8, py - r * 0.5);
    append(rc.circle(tx, ty, r * 0.8 * s, { fill: skin, stroke: INK, strokeWidth: 3.5 * s, roughness: 0.4 }));
  };
  const foot = (px, py, ang) => {
    const cos = Math.cos(ang), sin = Math.sin(ang);
    const pts = [[-2, 0], [24, -3], [32, 5], [24, 14], [-6, 12], [-12, 6]]
      .map(([a, b]) => [px + a * cos - b * sin, py + a * sin + b * cos]);
    shape(pts, SHOE, 0.6, 4);
    const [sx, sy] = M(px - 8 * cos, py - 8 * sin);
    append(rc.line(sx, sy, sx + 14 * s * cos, sy + 14 * s * sin,
      { stroke: INK, strokeWidth: 4 * s, roughness: 0.5 }));
  };

  // --- torso geometry -----------------------------------------------------
  const torsoDy = pose === "sit" ? 46 : 0;
  const t = (pts) => pts.map(([px, py]) => [px, py + torsoDy]);

  // --- draw order: torso, legs/arms (behind is fine), head, hair, face ----
  const hipY = -252 + torsoDy;

  // legs first (behind torso bottom)
  const LEG = { stand: null };
  const poses = {
    stand: {
      legL: { knee: [26, -120], foot: [26, 0], ang: 0.05 },
      legR: { knee: [-26, -120], foot: [-26, 0], ang: -0.05 },
      armL: { a: [66, -330], mid: [88, -272], b: [94, -210] },
      armR: { a: [-66, -330], mid: [-88, -272], b: [-94, -210] },
    },
    walk: {
      legL: { knee: [46, -128], foot: [54, 0], ang: 0.18 },
      legR: { knee: [-42, -118], foot: [-50, 0], ang: -0.22 },
      armL: { a: [66, -330], mid: [104, -272], b: [92, -204] },
      armR: { a: [-66, -330], mid: [-96, -266], b: [-118, -212] },
    },
    point: {
      legL: { knee: [40, -124], foot: [42, 0], ang: 0.08 },
      legR: { knee: [-38, -124], foot: [-40, 0], ang: -0.08 },
      armL: { a: [66, -330], mid: [96, -312], b: [128, -318], point: [156, -322] },
      armR: { a: [-66, -330], mid: [-84, -270], b: [-90, -212] },
    },
    raise: {
      legL: { knee: [28, -122], foot: [28, 0], ang: 0.04 },
      legR: { knee: [-28, -122], foot: [-28, 0], ang: -0.04 },
      armL: { a: [66, -330], mid: [96, -368], b: [104, -432] },
      armR: { a: [-66, -330], mid: [-96, -368], b: [-104, -432] },
    },
    wave: {
      legL: { knee: [28, -122], foot: [28, 0], ang: 0.04 },
      legR: { knee: [-28, -122], foot: [-28, 0], ang: -0.04 },
      armL: { a: [66, -330], mid: [88, -368], b: [84, -428] },
      armR: { a: [-66, -330], mid: [-84, -270], b: [-90, -212] },
    },
    think: {
      legL: { knee: [28, -122], foot: [28, 0], ang: 0.04 },
      legR: { knee: [-28, -122], foot: [-28, 0], ang: -0.04 },
      armL: { a: [66, -330], mid: [52, -336], b: [22, -364] },
      armR: { a: [-66, -330], mid: [-78, -268], b: [-16, -256] },
    },
    hold: {
      legL: { knee: [28, -122], foot: [28, 0], ang: 0.04 },
      legR: { knee: [-28, -122], foot: [-28, 0], ang: -0.04 },
      armL: { a: [66, -330], mid: [102, -302], b: [116, -256] },
      armR: { a: [-66, -330], mid: [-102, -302], b: [-116, -256] },
    },
    shrug: {
      legL: { knee: [28, -122], foot: [28, 0], ang: 0.04 },
      legR: { knee: [-28, -122], foot: [-28, 0], ang: -0.04 },
      armL: { a: [66, -330], mid: [100, -330], b: [132, -306], shrug: true },
      armR: { a: [-66, -330], mid: [-100, -330], b: [-132, -306], shrug: true },
    },
    sit: {
      legL: { knee: [92, -216], foot: [66, -48], ang: 0.35 },
      legR: { knee: [-92, -216], foot: [-66, -48], ang: -0.35 },
      armL: { a: [66, -318], mid: [58, -286], b: [20, -272] },
      armR: { a: [-66, -318], mid: [-58, -286], b: [-20, -272] },
    },
  };
  const POSE = poses[pose] ?? poses.stand;

  // legs
  const legW = cloth === "dress" ? 24 : 26;
  for (const side of ["legL", "legR"]) {
    const l = POSE[side];
    limb([side === "legL" ? 30 : -30, hipY], l.knee, l.foot, legW, outfit2);
    foot(l.foot[0], l.foot[1], l.ang);
  }
  // arms
  for (const side of ["armL", "armR"]) {
    const a = POSE[side];
    const sleeveEnd = [a.mid[0] * 0.85, a.mid[1] * 0.9 + a.a[1] * 0.1];
    limb(a.a, a.mid, a.b, 20, outfit);
    hand(a.b[0], a.b[1]);
    if (a.point) {
      const [fx, fy] = M(a.point[0], a.point[1]);
      const [hx, hy] = M(a.b[0], a.b[1]);
      append(rc.line(hx, hy, fx, fy, { stroke: INK, strokeWidth: 4 * s, roughness: 0.5 }));
    }
    if (a.shrug) {
      const [hx, hy] = M(a.b[0], a.b[1]);
      append(rc.line(hx - 10 * s, hy - 14 * s, hx + 10 * s, hy - 14 * s,
        { stroke: INK, strokeWidth: 4 * s, roughness: 0.5 }));
    }
  }

  // torso / clothing
  if (cloth === "dress") {
    shape(t([[-56, -384], [0, -370], [56, -384], [80, -298], [62, -206], [-62, -206], [-80, -298]]), outfit);
  } else if (cloth === "coat") {
    // body in the character's outfit colour (was hard-coded white, which
    // made every coat read as a blank bib on coloured backgrounds)
    shape(t([[-72, -388], [0, -372], [72, -388], [68, -266], [0, -254], [-68, -266]]), outfit, 0.7, 5);
    // lapels + button placket
    shape(t([[-12, -372], [-34, -380], [-30, -300], [-18, -300]]), outfit2, 0.6, 4);
    shape(t([[12, -372], [34, -380], [30, -300], [18, -300]]), outfit2, 0.6, 4);
    line(t([[0, -366], [0, -262]]), 3.5);
    dot(0, -340, 4.5, INK); dot(0, -310, 4.5, INK); dot(0, -280, 4.5, INK);
  } else {
    shape(t([[-64, -384], [-6, -370], [64, -384], [70, -322], [56, -252], [-56, -252], [-70, -322]]), outfit);
    // sleeves
    shape(t([[-64, -382], [-94, -366], [-98, -330], [-70, -326]]), outfit);
    shape(t([[64, -382], [94, -366], [98, -330], [70, -326]]), outfit);
    if (cloth === "sweater") {
      line(t([[-20, -372], [0, -364], [20, -372]]), 4);
      line(t([[-48, -252], [-20, -264], [0, -252], [20, -264], [48, -252]]), 3);
    } else if (cloth === "suit") {
      shape(t([[-10, -372], [10, -372], [6, -312], [-6, -312]]), OUTFITS.red);
      shape(t([[-12, -372], [12, -372], [0, -356]]), WHITE);
    } else if (cloth === "hoodie") {
      shape(t([[-34, -392], [0, -400], [34, -392], [30, -358], [0, -364], [-30, -358]]), outfit2);
      line(t([[-20, -290], [20, -290], [20, -240], [-20, -240]]), 3.5);
    } else {
      // plain shirt: collar + hem
      line(t([[-14, -372], [0, -362], [14, -372]]), 4);
      line(t([[-48, -252], [48, -252]]), 3.5);
    }
  }

  // head
  const headC = [0, -452 + torsoDy * 0.35];
  const H = (pts) => pts.map(([px, py]) => [headC[0] + px, headC[1] + py]);
  const E = (px, py) => [headC[0] + px, headC[1] + py];
  const hx = (pts) => pts.map(([px, py]) => E(px, py));
  shape(H([[-52, -58], [-34, -74], [-12, -82], [10, -80], [30, -68], [44, -48], [46, -22], [38, 4], [22, 20], [8, 28], [-8, 28], [-22, 20], [-38, 4], [-46, -22], [-44, -48], [-30, -68]]), skin, 0.6, 5);
  // ears
  line(H([[-46, -22], [-56, -12], [-50, 2]]), 4.5);
  line(H([[46, -22], [56, -12], [50, 2]]), 4.5);
  // neck
  line(H([[-10, 24], [-12, 46]]), 6);
  line(H([[10, 24], [12, 46]]), 6);

  // ---- hair --------------------------------------------------------------
  if (hairStyle === "messy") {
    shape(hx([[-52, -64], [-42, -92], [-20, -106], [4, -110], [30, -102], [48, -80], [52, -50], [44, -34], [24, -30], [-26, -30], [-44, -34]]), hair);
    shape(hx([[-40, -44], [-52, -36], [-42, -24]]), hair, 0.6, 4);
    shape(hx([[34, -38], [46, -30], [36, -20]]), hair, 0.6, 4);
    line(hx([[-30, -56], [-40, -74]]), 3);
    line(hx([[28, -52], [38, -70]]), 3);
  } else if (hairStyle === "bun") {
    shape(hx([[-50, -58], [-36, -86], [-14, -98], [10, -94], [32, -78], [46, -50], [46, -26], [32, -22], [-34, -22], [-46, -26]]), hair);
    shape(hx([[26, -92], [44, -92], [50, -74], [34, -66], [20, -70]]), hair, 0.6, 4);
    line(hx([[16, -96], [30, -90]]), 3);
  } else if (hairStyle === "side") {
    shape(hx([[-52, -60], [-34, -90], [-8, -102], [18, -96], [40, -74], [50, -46], [50, -20], [34, -14], [-36, -22], [-48, -24]]), hair);
    line(hx([[-46, -34], [-16, -22], [12, -22], [36, -16]]), 3.5);
  } else if (hairStyle === "long") {
    shape(hx([[-50, -58], [-36, -88], [-10, -100], [14, -94], [34, -78], [44, -48], [42, -18], [28, -12], [-30, -16], [-44, -20]]), hair);
    shape(hx([[-50, -50], [-58, -10], [-64, 26], [-48, 44], [-36, 30], [-42, -8], [-44, -26]]), hair, 0.6, 4);
    shape(hx([[50, -50], [58, -10], [64, 26], [48, 44], [36, 30], [42, -8], [44, -26]]), hair, 0.6, 4);
  } else if (hairStyle === "bald") {
    line(hx([[-20, -80], [-8, -84]]), 3);
    line(hx([[8, -82], [20, -78]]), 3);
  } else if (hairStyle === "cap") {
    // crown sits ABOVE the eye line (eyes are at y=-30); the old crown
    // reached y=-22 and the brim y=-4, which drew the hat over the face.
    const capC = OUTFITS[el.capColor] ?? OUTFITS.red;
    shape(hx([[-50, -60], [-30, -92], [0, -100], [30, -92], [50, -60], [50, -48], [-50, -48]]), capC, 0.7, 5);
    shape(hx([[10, -48], [68, -42], [66, -30], [10, -36]]), capC, 0.6, 4);
    const [px0, py0] = E(0, -100);
    dot(px0, py0, 10, capC);
  } else { // short (default)
    shape(hx([[-50, -58], [-38, -84], [-16, -96], [8, -92], [28, -76], [42, -48], [44, -24], [32, -18], [-32, -18], [-44, -24]]), hair);
  }
  if (el.beard) {
    shape(hx([[-16, 10], [0, 18], [16, 10], [24, 26], [20, 44], [8, 54], [0, 56], [-8, 54], [-20, 44], [-24, 26]]), hair, 0.6, 4);
  }

  // ---- face --------------------------------------------------------------
  const eyeY = -30;
  const eyeL = E(-17, eyeY), eyeR = E(17, eyeY);
  if (emotion === "happy" || emotion === "laugh") {
    line(hx([[-24, -34], [-10, -26], [-6, -34]]), 4.5);
    line(hx([[6, -34], [10, -26], [24, -34]]), 4.5);
  } else if (emotion === "surprised" || emotion === "worried") {
    dot(eyeL[0], eyeL[1], 6.5, INK); dot(eyeR[0], eyeR[1], 6.5, INK);
    dot(eyeL[0] - 2 * s, eyeL[1] - 2 * s, 2, WHITE); dot(eyeR[0] - 2 * s, eyeR[1] - 2 * s, 2, WHITE);
  } else if (emotion === "angry") {
    line(hx([[-26, -36], [-8, -30]]), 4.5);
    line(hx([[8, -30], [26, -36]]), 4.5);
    dot(eyeL[0], eyeL[1], 4.5, INK); dot(eyeR[0], eyeR[1], 4.5, INK);
  } else if (emotion === "sad") {
    line(hx([[-26, -30], [-8, -36]]), 4.5);
    line(hx([[8, -36], [26, -30]]), 4.5);
    dot(eyeL[0], eyeL[1] + 2 * s, 4.5, INK); dot(eyeR[0], eyeR[1] + 2 * s, 4.5, INK);
  } else {
    dot(eyeL[0], eyeL[1], 4.5, INK); dot(eyeR[0], eyeR[1], 4.5, INK);
    dot(eyeL[0] - 1.5 * s, eyeL[1] - 1.5 * s, 1.5, WHITE);
    dot(eyeR[0] - 1.5 * s, eyeR[1] - 1.5 * s, 1.5, WHITE);
  }
  // brows
  if (emotion === "worried" || emotion === "sad") {
    line(hx([[-26, -48], [-8, -56]]), 4);
    line(hx([[8, -56], [26, -48]]), 4);
  } else if (emotion === "surprised") {
    line(hx([[-24, -54], [-10, -60]]), 4);
    line(hx([[10, -60], [24, -54]]), 4);
  } else if (emotion === "angry") {
    line(hx([[-26, -52], [-8, -46]]), 4.5);
    line(hx([[8, -46], [26, -52]]), 4.5);
  } else {
    line(hx([[-24, -50], [-10, -53]]), 3.5);
    line(hx([[10, -53], [24, -50]]), 3.5);
  }
  // nose
  line(hx([[-4, -8], [0, -4], [-1, 6]]), 3.5);
  // mouth
  if (emotion === "happy") {
    line(hx([[-13, 14], [0, 24], [13, 14]]), 4.5);
  } else if (emotion === "laugh") {
    shape(hx([[-15, 14], [0, 34], [15, 14], [0, 8]]), "#7A2E2E", 0.5, 4);
    shape(hx([[-15, 14], [0, 22], [15, 14]]), WHITE, 0.5, 3);
  } else if (emotion === "worried") {
    line(hx([[-11, 14], [0, 8], [11, 14]]), 4);
  } else if (emotion === "sad") {
    line(hx([[-11, 10], [0, 18], [11, 10]]), 4);
  } else if (emotion === "angry") {
    line(hx([[-11, 12], [0, 18], [11, 12]]), 4.5);
  } else if (emotion === "surprised") {
    const [mx0, my0] = E(0, 16);
    dot(mx0, my0, 5, INK);
  } else {
    line(hx([[-9, 14], [9, 14]]), 4);
  }
  // blush
  if (emotion === "happy" || emotion === "laugh" || emotion === "surprised") {
    const [bx1, by1] = E(-30, 0); const [bx2, by2] = E(30, 0);
    append(rc.circle(bx1, by1, 9 * s, { fill: "#F2A0A0", fillStyle: "solid", stroke: "none", roughness: 0.4, fillWeight: 0 }));
    append(rc.circle(bx2, by2, 9 * s, { fill: "#F2A0A0", fillStyle: "solid", stroke: "none", roughness: 0.4, fillWeight: 0 }));
  }
  // optional speech/thought bubble above
  if (el.says) {
    // Clear the head: the head top is headC[1] - 90 in local units, so the
    // bubble is centred well above it and its tail bridges the gap.
    const bw = el.sayW ?? 260 * s;
    const bh = el.sayH ?? 110 * s;
    const [bx, by] = M(0, headC[1] - 90 - bh / (2 * s) - 46);
    append(rc.ellipse(bx, by, bw, bh,
      { fill: WHITE, fillStyle: "solid", stroke: INK, strokeWidth: 4 * s, roughness: 0.7 }));
    // tail — three shrinking dots down toward the head
    const [hxp, hyp] = M(14, headC[1] - 86);
    for (let i = 0; i < 3; i++) {
      const p = 0.34 + i * 0.26;
      append(rc.circle(bx + (hxp - bx) * p, by + bh / 2 + (hyp - by - bh / 2) * p,
        (13 - i * 3) * 2 * s,
        { fill: WHITE, fillStyle: "solid", stroke: INK, strokeWidth: 3.2 * s, roughness: 0.6 }));
    }
    // the text node must be APPENDED — previously it was built and dropped,
    // so every `says` bubble rendered empty.
    append(ctx.text({ x: bx, y: by, text: el.says, size: (el.saySize ?? 34) * s, font: "caveat", rot: -0.6 }));
  }
  return { top: headC[1] - 90 * s, feet: y };
}

// -------------------------------------------------------------- scenery
export function inkSky(ctx, el) {
  const { rc, rnd, append } = ctx;
  // sun
  if (el.sun !== false) {
    const sx = el.sunX ?? el.x, sy = el.sunY ?? el.y;
    append(rc.circle(sx, sy, 150, { fill: "#FFE28A", fillStyle: "solid", stroke: "none", roughness: 0.5 }));
    append(rc.circle(sx, sy, 150, { fill: "none", stroke: "#16161a", strokeWidth: 4.5, roughness: 0.8 }));
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * Math.PI * 2 + rnd() * 0.3;
      const r1 = 95 + rnd() * 26, r2 = 135 + rnd() * 34;
      append(rc.line(sx + Math.cos(a) * r1, sy + Math.sin(a) * r1,
        sx + Math.cos(a) * r2, sy + Math.sin(a) * r2,
        { strokeWidth: 5.5, roughness: 1 }));
    }
  }
  // clouds
  const n = el.clouds ?? 2;
  for (let i = 0; i < n; i++) {
    const cx = el.x + (i - (n - 1) / 2) * (el.cloudGap ?? 380) + rnd() * 60;
    const cy = el.y - (el.cloudDy ?? 120) + rnd() * 40;
    const r = (el.cloudR ?? 55) * (0.8 + rnd() * 0.5);
    append(rc.circle(cx, cy, r * 2, { fill: WHITE, fillStyle: "solid", stroke: "#16161a", strokeWidth: 4, roughness: 0.8 }));
    append(rc.circle(cx + r * 0.9, cy + r * 0.35, r * 1.5, { fill: WHITE, fillStyle: "solid", stroke: "#16161a", strokeWidth: 4, roughness: 0.8 }));
    append(rc.circle(cx - r * 0.95, cy + r * 0.35, r * 1.3, { fill: WHITE, fillStyle: "solid", stroke: "#16161a", strokeWidth: 4, roughness: 0.8 }));
    append(rc.line(cx - r * 1.6, cy + r * 0.55, cx + r * 1.6, cy + r * 0.55, { strokeWidth: 4, roughness: 0.8 }));
  }
  // birds
  const birds = el.birds ?? 0;
  for (let i = 0; i < birds; i++) {
    const bx = el.x + (i - birds / 2) * 170 + rnd() * 50;
    const by = el.y - 260 + rnd() * 60;
    append(rc.curve([[bx - 22, by], [bx - 8, by - 14], [bx + 8, by - 14], [bx + 22, by]], { strokeWidth: 4, roughness: 0.9 }));
  }
}

export function inkGround(ctx, el) {
  const { rc, rnd, append } = ctx;
  const W = el.width ?? 1376;
  const pts = [];
  for (let px = -40; px <= W + 40; px += 120) {
    pts.push([px, el.y + rnd() * 18 - 9]);
  }
  append(rc.curve(pts, { stroke: "#16161a", strokeWidth: 5, roughness: 1 }));
  // hatching under the line
  for (let i = 0; i < 16; i++) {
    const hx = rnd() * W, hy = el.y + 12 + rnd() * 60;
    append(rc.line(hx, hy, hx - 26, hy + 30, { stroke: "#16161a", strokeWidth: 3.5, roughness: 0.9 }));
  }
  // grass tufts
  for (let i = 0; i < 8; i++) {
    const gx = rnd() * W, gy = el.y - 8 - rnd() * 14;
    append(rc.line(gx, gy, gx - 10, gy - 20, { strokeWidth: 3.5, roughness: 0.8 }));
    append(rc.line(gx, gy, gx + 2, gy - 24, { strokeWidth: 3.5, roughness: 0.8 }));
    append(rc.line(gx, gy, gx + 12, gy - 18, { strokeWidth: 3.5, roughness: 0.8 }));
  }
}

export function inkHills(ctx, el) {
  const { rc, rnd, append } = ctx;
  const W = el.width ?? 1376;
  const H = el.height ?? 768;
  // far hill
  const pts1 = [[-60, el.y], [180, el.y - 150], [420, el.y - 40], [700, el.y - 180], [980, el.y - 60], [1240, el.y - 140], [W + 60, el.y]];
  append(rc.curve(pts1.concat([[W + 60, H + 20], [-60, H + 20], [-60, el.y]]), {
    stroke: "#16161a", strokeWidth: 4.5, roughness: 1,
    fill: el.far ?? "#CFE8C0", fillStyle: "solid",
  }));
  // near hill
  const pts2 = [[-60, el.y + 120], [260, el.y - 20], [560, el.y + 60], [900, el.y - 40], [W + 60, el.y + 100]];
  append(rc.curve(pts2.concat([[W + 60, H + 20], [-60, H + 20], [-60, el.y + 120]]), {
    stroke: "#16161a", strokeWidth: 4.5, roughness: 1,
    fill: el.near ?? "#AEDFA4", fillStyle: "solid",
  }));
}

export function inkTree(ctx, el) {
  const { rc, rnd, append } = ctx;
  const x = el.x, y = el.y;
  append(rc.curve([[x, y], [x - 10, y - 90], [x + 4, y - 180], [x - 6, y - 250]], { stroke: "#6B4A2E", strokeWidth: 20, roughness: 1 }));
  append(rc.circle(x, y - 300, 200, { fill: "#7CB86B", fillStyle: "hachure", stroke: "#16161a", strokeWidth: 5, roughness: 1.1, hachureGap: 12 }));
  append(rc.circle(x - 110, y - 250, 120, { fill: "#7CB86B", fillStyle: "hachure", stroke: "#16161a", strokeWidth: 4.5, roughness: 1 }));
  append(rc.circle(x + 115, y - 250, 125, { fill: "#7CB86B", fillStyle: "hachure", stroke: "#16161a", strokeWidth: 4.5, roughness: 1 }));
  // falling leaf
  append(rc.curve([[x + 90, y - 160], [x + 120, y - 130], [x + 105, y - 100]], { stroke: "#16161a", strokeWidth: 3.5, roughness: 0.9 }));
}

export function inkWater(ctx, el) {
  const { rc, rnd, append } = ctx;
  const W = el.width ?? 1376;
  for (let row = 0; row < 3; row++) {
    const pts = [];
    for (let px = -40; px <= W + 40; px += 90) {
      pts.push([px, el.y + row * 46 + rnd() * 12 - 6]);
    }
    append(rc.curve(pts, { stroke: "#3F81B2", strokeWidth: 4.5, roughness: 1 }));
  }
}

export function inkStars(ctx, el) {
  const { rc, rnd, append } = ctx;
  const n = el.count ?? 6;
  for (let i = 0; i < n; i++) {
    const sx = rnd() * (el.width ?? 1376), sy = rnd() * (el.height ?? 300);
    const r = 6 + rnd() * 8;
    append(rc.line(sx - r, sy, sx + r, sy, { stroke: "#16161a", strokeWidth: 3.5, roughness: 0.6 }));
    append(rc.line(sx, sy - r, sx, sy + r, { stroke: "#16161a", strokeWidth: 3.5, roughness: 0.6 }));
  }
}

export function inkMoon(ctx, el) {
  const { rc, append } = ctx;
  append(rc.path(`M ${el.x - 46} ${el.y - 20} A 52 52 0 1 0 ${el.x - 46} ${el.y + 20} A 40 40 0 1 1 ${el.x - 46} ${el.y - 20} Z`,
    { fill: "#FFE28A", fillStyle: "solid", stroke: "#16161a", strokeWidth: 4.5, roughness: 0.7 }));
}

export function inkRoom(ctx, el) {
  const { rc, append } = ctx;
  const W = el.width ?? 1376;
  const baseX = el.x ?? 0;
  const baseY = el.y ?? 560;
  const floorY = el.floorY ?? baseY;
  append(rc.line(0, floorY, W, floorY, { stroke: "#16161a", strokeWidth: 5, roughness: 0.9 }));
  // picture frame
  const fx = el.frameX ?? baseX, fy = el.frameY ?? baseY - 260, fw = el.frameW ?? 220, fh = el.frameH ?? 170;
  append(rc.rectangle(fx - fw / 2, fy - fh / 2, fw, fh, { strokeWidth: 5, roughness: 0.9, fill: "none" }));
  append(rc.line(fx, fy - fh / 2 - 14, fx, fy - fh / 2, { strokeWidth: 4, roughness: 0.6 }));
  append(rc.curve([[fx - fw * 0.3, fy + fh * 0.2], [fx - fw * 0.1, fy - fh * 0.1], [fx + fw * 0.2, fy + fh * 0.05], [fx + fw * 0.32, fy - fh * 0.2]], { strokeWidth: 4, roughness: 1 }));
  // window
  const wx = el.windowX ?? baseX + 420, wy = el.windowY ?? baseY - 240, ww = el.windowW ?? 190, wh = el.windowH ?? 220;
  append(rc.rectangle(wx - ww / 2, wy - wh / 2, ww, wh, { strokeWidth: 5, roughness: 0.9, fill: "#FFE9B8", fillStyle: "solid" }));
  append(rc.line(wx, wy - wh / 2, wx, wy + wh / 2, { strokeWidth: 4.5, roughness: 0.7 }));
  append(rc.line(wx - ww / 2, wy, wx + ww / 2, wy, { strokeWidth: 4.5, roughness: 0.7 }));
  // rug
  append(rc.ellipse(baseX + 140, floorY + 30, el.rugW ?? 300, 40, { stroke: "#16161a", strokeWidth: 4, roughness: 1, fill: "none" }));
}

export function inkMirror(ctx, el) {
  const { rc, append } = ctx;
  const x = el.x, y = el.y, rw = el.w ?? 170, rh = el.h ?? 260;
  // stand
  append(rc.line(x - 14, y + rh / 2 + 10, x - 40, y + rh / 2 + 90, { strokeWidth: 6, roughness: 0.7 }));
  append(rc.line(x + 14, y + rh / 2 + 10, x + 40, y + rh / 2 + 90, { strokeWidth: 6, roughness: 0.7 }));
  // frame + glass
  append(rc.ellipse(x, y, rw * 2, rh * 2, { fill: "#FFE9B8", fillStyle: "solid", stroke: "#16161a", strokeWidth: 7, roughness: 0.8 }));
  append(rc.ellipse(x, y, rw * 1.55, rh * 1.7, { fill: "#FFF6E0", fillStyle: "solid", stroke: "#16161a", strokeWidth: 4, roughness: 0.7 }));
  // glow sparkle
  const [gx, gy] = [x + rw * 0.5, y - rh * 0.45];
  append(rc.line(gx - 16, gy, gx + 16, gy, { strokeWidth: 3.5, roughness: 0.5 }));
  append(rc.line(gx, gy - 16, gx, gy + 16, { strokeWidth: 3.5, roughness: 0.5 }));
}

export function inkSpeckle(ctx, el) {
  const { rc, rnd, append } = ctx;
  const n = el.count ?? 400;
  const W = el.width ?? 1376, H = el.height ?? 768;
  const c = el.color ?? "#8a7f6a";
  for (let i = 0; i < n; i++) {
    append(rc.circle(rnd() * W, rnd() * H, (1 + rnd() * 2.4) * 2, {
      fill: c, stroke: "none", roughness: 0, fillWeight: 0,
    }));
  }
}

export function inkFrame(ctx, el) {
  const { rc, append } = ctx;
  const W = el.width ?? 1376, H = el.height ?? 768, m = el.margin ?? 26;
  append(rc.rectangle(m, m, W - 2 * m, H - 2 * m, { strokeWidth: 6, roughness: 1.1, fill: "none" }));
  append(rc.rectangle(m + 16, m + 16, W - 2 * m - 32, H - 2 * m - 32, { strokeWidth: 2.5, roughness: 1.2, fill: "none" }));
}
