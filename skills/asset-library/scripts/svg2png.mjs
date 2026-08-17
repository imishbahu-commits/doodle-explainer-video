#!/usr/bin/env node
// svg2png.mjs — rasterize an SVG to PNG using resvg-js (pure Rust/WASM, no
// system libraries). If resvg-js is not found, it self-installs into the
// user cache (~/.asset-library/resvg) from the npm registry. Nothing is
// written into the repo.
//
// Usage: node svg2png.mjs input.svg output.png [width=1024]

import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));

function findResvg() {
  const candidates = [
    process.env.RESVG_DIR && join(process.env.RESVG_DIR, "node_modules", "@resvg", "resvg-js"),
    join(homedir(), ".asset-library", "resvg", "node_modules", "@resvg", "resvg-js"),
    join(__dirname, "..", "..", "..", "handdrawn-code", "node_modules", "@resvg", "resvg-js"),
    join(__dirname, "node_modules", "@resvg", "resvg-js"),
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsSync(join(c, "package.json"))) return c;
  }
  return null;
}

function selfInstall() {
  const prefix = join(homedir(), ".asset-library", "resvg");
  console.error("resvg-js not found — installing into", prefix);
  execFileSync("npm", ["install", "--prefix", prefix, "--no-audit", "--no-fund",
                       "@resvg/resvg-js"], { stdio: "inherit" });
  return join(prefix, "node_modules", "@resvg", "resvg-js");
}

const [, , inFile, outFile, widthArg] = process.argv;
if (!inFile || !outFile) {
  console.error("usage: node svg2png.mjs input.svg output.png [width=1024]");
  process.exit(2);
}
const width = Number(widthArg || 1024);

let resvgPath = findResvg() || selfInstall();
const { Resvg } = require(resvgPath);

const svg = readFileSync(inFile, "utf-8");
const r = new Resvg(svg, {
  fitTo: { mode: "width", value: width },
  background: "white",
});
writeFileSync(outFile, r.render().asPng());
console.error(`rasterized -> ${outFile} (${width}px wide)`);
