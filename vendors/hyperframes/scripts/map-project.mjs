#!/usr/bin/env node
// map-project.mjs - canonical project.yaml -> HyperFrames composition.
// Usage: node map-project.mjs PROJECT_DIR WORK_DIR
// Writes: index.html, package.json, expected-seconds.txt, and copies
// voices/, images/, background.png from the project assets.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

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

// ---- HTML ----
const font = settings.font || {};
const fontFamily = font.family || "Inter";
const fontSize = font.size || 70;
const fontWeight = font.weight || "900";
const charH = settings.character?.height ?? 275;
const useImages = settings.character?.use_images ?? false;
const subWidth = settings.subtitle?.max_width_percent ?? 55;
const subBottom = settings.subtitle?.bottom_offset ?? 40;

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const clips = [];

clips.push(`    <img class="clip" src="background.png" data-start="0" data-duration="${total}" data-track-index="0" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0" />`);

const positions = { left: { left: "40px" }, right: { right: "40px" } };
const charIds = Object.keys(chars);
for (const id of charIds) {
  const c = chars[id];
  const side = c.position === "left" ? "left" : "right";
  const color = c.color || "#4B5563";
  if (useImages && fs.existsSync(path.join(workDir, "images", id, "mouth_close.png"))) {
    clips.push(`    <img class="clip" src="images/${id}/mouth_close.png" data-start="0" data-duration="${total}" data-track-index="10" style="position:absolute;bottom:0;${side}:40px;height:${charH}px;object-fit:contain;z-index:10" />`);
    for (const seg of timeline.filter((s) => s.line.character === id)) {
      let k = seg.start;
      let open = true;
      while (k < seg.end - 0.01) {
        const d = Math.min(0.2, seg.end - k);
        clips.push(`    <img class="clip" src="images/${id}/mouth_${open ? "open" : "close"}.png" data-start="${k.toFixed(3)}" data-duration="${d.toFixed(3)}" data-track-index="11" style="position:absolute;bottom:0;${side}:40px;height:${charH}px;object-fit:contain;z-index:11" />`);
        k += d;
        open = !open;
      }
    }
  } else {
    clips.push(`    <div class="clip" data-start="0" data-duration="${total}" data-track-index="10" style="position:absolute;bottom:0;${side}:40px;width:200px;height:300px;background:${color}20;border:4px solid ${color};border-radius:16px;display:flex;align-items:center;justify-content:center;z-index:10"><span style="font-weight:bold;color:${color};font-size:24px">${esc(c.name)}</span></div>`);
  }
}

for (const seg of timeline) {
  const line = seg.line;
  const text = line.display_text || line.text;
  clips.push(`    <audio class="clip" src="voices/${seg.file}" data-start="${seg.start.toFixed(3)}" data-duration="${seg.dur.toFixed(3)}" data-track-index="20"></audio>`);
  clips.push(`    <div class="clip" data-start="${seg.start.toFixed(3)}" data-duration="${(seg.subEnd - seg.start).toFixed(3)}" data-track-index="30" style="position:absolute;bottom:${subBottom}px;left:50%;transform:translateX(-50%);width:${subWidth}%;text-align:center;font-family:'${fontFamily}',sans-serif;font-size:${fontSize}px;font-weight:${fontWeight};color:${font.color || "#ffffff"};-webkit-text-stroke:${Math.round(fontSize * 0.2)}px ${font.outline_color || "#1F2937"};paint-order:stroke fill;overflow-wrap:anywhere;text-wrap:balance;z-index:20">${esc(text)}</div>`);
  const v = line.visual;
  if (v && v.type === "text" && v.text) {
    const vs = v.font_size || 84;
    clips.push(`    <div class="clip" data-start="${seg.start.toFixed(3)}" data-duration="${(seg.subEnd - seg.start).toFixed(3)}" data-track-index="5" style="position:absolute;inset:0 0 25% 0;display:flex;align-items:center;justify-content:center;font-family:'${fontFamily}',sans-serif;font-size:${vs}px;font-weight:bold;color:${v.color || "#ffffff"};-webkit-text-stroke:${Math.round(vs * 0.16)}px ${v.outline_color || "#1F2937"};paint-order:stroke fill;text-align:center;white-space:pre-wrap;text-wrap:balance;z-index:5">${esc(v.text)}</div>`);
  }
}

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=${settings.video?.width ?? 1920}, height=${settings.video?.height ?? 1080}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { margin: 0; width: ${settings.video?.width ?? 1920}px; height: ${settings.video?.height ?? 1080}px; overflow: hidden; background: #0a0a0a; }
#root { width: 100%; height: 100%; position: relative; font-family: '${fontFamily}', sans-serif; }
.clip { will-change: auto; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${total}" data-width="${settings.video?.width ?? 1920}" data-height="${settings.video?.height ?? 1080}">
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
console.log(`[map-project] characters: ${charIds.join(", ")}`);
console.log(`[map-project] lines: ${script.length}, total: ${total}s`);
