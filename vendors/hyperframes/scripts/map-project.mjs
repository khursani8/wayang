#!/usr/bin/env node
// map-project.mjs - canonical project.yaml -> HyperFrames composition.
// Usage: node map-project.mjs PROJECT_DIR WORK_DIR
// Writes: index.html, package.json, expected-seconds.txt, fonts/, and copies
// voices/, images/, background.png from the project assets.
//
// HyperFrames authoring rules honored here (learned from the renderer's lint):
// - every timed element carries a stable id (media without id renders silent)
// - every clip is a full-frame wrapper div; content is positioned INSIDE it,
//   so the runtime's full-frame .clip rule cannot distort placement
// - fonts referenced by settings.font are downloaded at map time and
//   declared with @font-face (the renderer cannot supply them)
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const argv = process.argv.slice(2);
if (argv.length !== 2) {
  console.error("[map-project] usage: map-project.mjs PROJECT_DIR WORK_DIR");
  process.exit(2);
}
const projectDir = path.resolve(argv[0]);
const workDir = path.resolve(argv[1]);
const vendorDir = path.resolve(workDir, "..", "..");
// yaml lives in the vendor's own scripts/node_modules (build.sh installs it)
const require = createRequire(path.join(vendorDir, "scripts", "package.json"));
const YAML = require("yaml");

function die(msg) {
  console.error(`[map-project] ERROR: ${msg}`);
  process.exit(1);
}

const mergedPath = path.join(projectDir, ".merged.yaml");
const projectPath = fs.existsSync(mergedPath) ? mergedPath : path.join(projectDir, "project.yaml");
if (!fs.existsSync(projectPath)) die(`missing ${projectPath}`);
let project;
try {
  project = YAML.parse(fs.readFileSync(projectPath, "utf8"));
} catch (e) {
  die(`project parse error: ${e.message}`);
}

const chars = project.characters || {};
const script = project.script || [];
const settings = project.settings || {};
const vendorCfg = (project.vendor && project.vendor.hyperframes) || {};
const cps = vendorCfg.estimate_cps ?? 7.5;
const fps = settings.video?.fps ?? 30;
const W = settings.video?.width ?? 1920;
const H = settings.video?.height ?? 1080;

for (const k of Object.keys(vendorCfg)) {
  if (!["estimate_cps"].includes(k)) {
    die(`vendor.hyperframes: unknown key '${k}' (allowed: estimate_cps)`);
  }
}
if (settings.background !== undefined && typeof settings.background !== "string") {
  die("settings.background must be a theme name string");
}
for (const line of script) {
  if (line.se) die(`script id ${line.id}: sound effects are not supported by the hyperframes vendor yet`);
}

// ---- voices: platform manifest or estimates (never mixed) ----
const manifestPath = path.join(projectDir, "voices", "manifest.json");
let voiceSeconds = null;
let engines = [];
if (fs.existsSync(manifestPath)) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const entries = manifest.lines || {};
  const fileName = (line) => `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
  const missing = script.filter((l) => !entries[fileName(l)] || !fs.existsSync(path.join(projectDir, "voices", fileName(l))));
  if (missing.length === 0) {
    voiceSeconds = {};
    for (const line of script) {
      voiceSeconds[fileName(line)] = Number(entries[fileName(line)].seconds);
    }
    engines = manifest.engines || ["unknown"];
    console.log(`[map-project] TTS source: ${engines.join("+")} (platform-generated voices)`);
  }
}
if (voiceSeconds === null) {
  console.log("[map-project] TTS source: estimate (no platform voices complete)");
}

const pauseOf = (line) => (line.pause_after ?? 0.5);

// ---- timeline ----
let t = 0;
const timeline = [];
for (const line of script) {
  const file = `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
  const dur = voiceSeconds ? voiceSeconds[file] : Math.max(0.8, String(line.text).replace(/\s+/g, "").length / cps);
  const pause = pauseOf(line);
  timeline.push({ line, file, start: t, dur, end: t + dur, subEnd: t + dur + pause });
  t += dur + pause;
}
const total = +(t + 2).toFixed(3);

// ---- background: project custom > named theme > engine default (riverbank) ----
const catalogDir = path.join(vendorDir, "assets", "backgrounds");
const catalog = fs.existsSync(catalogDir)
  ? fs.readdirSync(catalogDir).filter((f) => f.endsWith(".png")).map((f) => f.replace(".png", ""))
  : [];
let theme = "riverbank";
if (settings.background !== undefined) {
  if (!catalog.includes(settings.background)) {
    die(`settings.background: unknown theme '${settings.background}' (available: ${catalog.join(", ")})`);
  }
  theme = settings.background;
}
const projectBackground = path.join(projectDir, "assets", "background.png");
fs.copyFileSync(path.join(catalogDir, `${theme}.png`), path.join(workDir, "background.png"));
if (fs.existsSync(projectBackground)) {
  fs.copyFileSync(projectBackground, path.join(workDir, "background.png"));
  console.log("[map-project] background: project custom override (assets/background.png)");
} else {
  console.log(`[map-project] background theme: ${theme}`);
}

// ---- copy voices + character art into the workdir ----
if (fs.existsSync(path.join(projectDir, "voices"))) {
  fs.cpSync(path.join(projectDir, "voices"), path.join(workDir, "voices"), { recursive: true });
}
if (fs.existsSync(path.join(projectDir, "assets", "images"))) {
  fs.cpSync(path.join(projectDir, "assets", "images"), path.join(workDir, "images"), { recursive: true });
}

// ---- font: download the requested Google font for @font-face ----
const font = settings.font || {};
const fontFamily = font.family || "Inter";
const fontSize = font.size || 70;
const fontWeight = String(font.weight || "900");
let fontFaceCss = "";
const fontsDir = path.join(workDir, "fonts");
fs.mkdirSync(fontsDir, { recursive: true });
try {
  const cssUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fontFamily).replace(/%20/g, "+")}:wght@${fontWeight}&display=swap`;
  const css = execSync(
    `curl -fsS --max-time 15 -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36" "${cssUrl}"`,
    { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
  );
  const urlMatch = css.match(/url\((https:[^)]+\.woff2)\)/);
  if (urlMatch) {
    const woff2 = path.join(fontsDir, "text.woff2");
    execSync(`curl -fsS --max-time 20 -o "${woff2}" "${urlMatch[1]}"`, { stdio: ["ignore", "ignore", "ignore"] });
    fontFaceCss = `@font-face { font-family: '${fontFamily}'; src: url('fonts/text.woff2') format('woff2'); font-weight: ${fontWeight}; font-style: normal; }`;
    console.log(`[map-project] font: downloaded ${fontFamily} ${fontWeight} -> fonts/text.woff2`);
  } else {
    console.warn("[map-project] font: no woff2 url in google css, using system fallback");
  }
} catch (e) {
  console.warn(`[map-project] font: download failed (${String(e.message).slice(0, 80)}), using system fallback`);
}

// ---- geometry + overlap detection ----
const charH = settings.character?.height ?? 275;
const subWidthPct = settings.subtitle?.max_width_percent ?? 55;
const subBottom = settings.subtitle?.bottom_offset ?? 40;
const subW = (W * subWidthPct) / 100;
const subLineH = fontSize * 1.5;
const SUB_MAX_LINES = 2;
const subH = subLineH * SUB_MAX_LINES;
const subX0 = (W - subW) / 2;
const subX1 = (W + subW) / 2;
const charBoxes = Object.values(chars).map((c) => {
  const side = c.position === "left" ? "left" : "right";
  const x0 = side === "left" ? 40 : W - 40 - charH;
  return { side, x0, x1: x0 + charH, y0: H - charH, y1: H };
});
let subY0 = H - subBottom - subH;
let subMoved = false;
for (const box of charBoxes) {
  const intersects = subX0 < box.x1 && subX1 > box.x0 && subY0 < box.y1 && subY0 + subH > box.y0;
  if (intersects) {
    subY0 = Math.min(subY0, box.y0 - 24 - subH);
    subMoved = true;
  }
}
const subBottomFinal = Math.max(0, H - subY0 - subH);
if (subMoved) {
  console.log(`[map-project] overlap: subtitle moved above characters (bottom ${subBottom} -> ${Math.round(subBottomFinal)}px)`);
}

// ---- HTML generation ----
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const clips = [];
let idSeq = 0;
const clip = (inner, extraAttrs, style) => {
  idSeq += 1;
  return `    <div class="clip" id="clip-${idSeq}" data-start="${extraAttrs.start}" data-duration="${extraAttrs.dur}" data-track-index="${extraAttrs.track}" style="position:absolute;inset:0;z-index:${extraAttrs.z}">\n      ${inner}\n    </div>`;
};

clips.push(clip(
  `<img src="background.png" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover" />`,
  { start: 0, dur: total, track: 0, z: 0 },
));

const charPos = {};
for (const id of Object.keys(chars)) {
  const c = chars[id];
  const side = c.position === "left" ? "left" : "right";
  const color = c.color || "#4B5563";
  const hasArt = fs.existsSync(path.join(workDir, "images", id, "mouth_close.png"));
  charPos[id] = { side, hasArt };
  if (useImagesCheck(settings) && hasArt) {
    charPos[id].art = true;
    const imgStyle = `position:absolute;bottom:0;${side}:40px;height:${charH}px;object-fit:contain`;
    clips.push(clip(
      `<img src="images/${id}/mouth_close.png" style="${imgStyle}" />`,
      { start: 0, dur: total, track: 10, z: 10 },
    ));
    for (const seg of timeline.filter((s) => s.line.character === id)) {
      let k = seg.start;
      let open = true;
      let n = 0;
      while (k < seg.end - 0.01) {
        const d = Math.min(0.2, seg.end - k);
        n += 1;
        clips.push(clip(
          `<img src="images/${id}/mouth_${open ? "open" : "close"}.png" style="${imgStyle}" />`,
          { start: k.toFixed(3), dur: d.toFixed(3), track: 11, z: 11 },
        ));
        k += d;
        open = !open;
      }
    }
  } else {
    const posCss = side === "left" ? "left:40px" : "right:40px";
    clips.push(clip(
      `<div style="position:absolute;bottom:0;${posCss};width:200px;height:300px;background:${color}20;border:4px solid ${color};border-radius:16px;display:flex;align-items:center;justify-content:center"><span style="font-weight:bold;color:${color};font-size:24px">${esc(c.name)}</span></div>`,
      { start: 0, dur: total, track: 10, z: 10 },
    ));
  }
}
function useImagesCheck(settings) {
  return settings.character?.use_images ?? false;
}

for (const seg of timeline) {
  const line = seg.line;
  const text = line.display_text || line.text;
  idSeq += 1;
  clips.push(`    <audio class="clip" id="line-${line.id}-audio" src="voices/${seg.file}" data-start="${seg.start.toFixed(3)}" data-duration="${seg.dur.toFixed(3)}" data-track-index="20"></audio>`);
  const subStyle = `position:absolute;bottom:${Math.round(subBottomFinal)}px;left:50%;transform:translateX(-50%);width:${subWidthPct}%;text-align:center;font-family:'${fontFamily}',sans-serif;font-size:${fontSize}px;font-weight:${fontWeight};color:${font.color || "#ffffff"};-webkit-text-stroke:${Math.round(fontSize * 0.2)}px ${font.outline_color || "#1F2937"};paint-order:stroke fill;overflow-wrap:anywhere;text-wrap:balance;line-height:1.4`;
  clips.push(clip(`<div style="${subStyle}">${esc(text)}</div>`, { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 30, z: 30 }));
  const v = line.visual;
  if (v && v.type === "text" && v.text) {
    const vs = v.font_size || 84;
    const cardStyle = `position:absolute;inset:0 0 25% 0;display:flex;align-items:center;justify-content:center;font-family:'${fontFamily}',sans-serif;font-size:${vs}px;font-weight:bold;color:${v.color || "#ffffff"};-webkit-text-stroke:${Math.round(vs * 0.16)}px ${v.outline_color || "#1F2937"};paint-order:stroke fill;text-align:center;white-space:pre-wrap;text-wrap:balance`;
    clips.push(clip(`<div style="${cardStyle}">${esc(v.text)}</div>`, { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 }));
  }
}

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=${W}, height=${H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { margin: 0; width: ${W}px; height: ${H}px; overflow: hidden; background: #0a0a0a; }
#root { width: 100%; height: 100%; position: relative; font-family: '${fontFamily}', sans-serif; }
${fontFaceCss}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${total}" data-width="${W}" data-height="${H}">
${clips.join("\n")}
</div>
<script>
const tl = gsap.timeline({ paused: true });
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(workDir, "index.html"), html);
fs.writeFileSync(path.join(workDir, "package.json"), JSON.stringify({
  name: "content-engine-hyperframes-render",
  private: true,
  type: "module",
  scripts: { render: "npx --yes hyperframes render" },
}, null, 2) + "\n");

fs.writeFileSync(path.join(workDir, "expected-seconds.txt"), String(total));
console.log(`[map-project] characters: ${Object.keys(chars).join(", ")}`);
console.log(`[map-project] lines: ${script.length}, total: ${total}s`);
