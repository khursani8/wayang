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

function probeSeconds(file) {
  try {
    const out = execSync(
      `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '${file}'`,
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    );
    return Number(out.trim());
  } catch {
    return 1.5;
  }
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
const playbackRate = settings.video?.playback_rate ?? 1;
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

// ---- estimated timing: silent placeholder wavs (TTS source: estimate) ----
// Every audio element needs a real source; the hyperframes runtime blocks the
// render on missing sources. The platform lint labels these renders and skips
// the voice check (manifest absent -> estimate).
function silentWav(seconds) {
  const rate = 24000;
  const samples = Math.max(1, Math.ceil(seconds * rate));
  const dataSize = samples * 2;
  const buf = Buffer.alloc(44 + dataSize);
  buf.write("RIFF", 0);
  buf.writeUInt32LE(36 + dataSize, 4);
  buf.write("WAVE", 8);
  buf.write("fmt ", 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(rate, 24);
  buf.writeUInt32LE(rate * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write("data", 36);
  buf.writeUInt32LE(dataSize, 40);
  return buf;
}

const pauseOf = (line) => (line.pause_after ?? 0.5);

// ---- timeline ----
let t = 0;
const timeline = [];
for (const line of script) {
  const file = `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
  const raw = voiceSeconds ? voiceSeconds[file] : Math.max(0.8, String(line.text).replace(/\s+/g, "").length / cps);
  const dur = raw / playbackRate;
  const pause = pauseOf(line);
  timeline.push({ line, file, start: t, dur, end: t + dur, subEnd: t + dur + pause / playbackRate });
  t += dur + pause / playbackRate;
}
// Write silent placeholder wavs on the estimate path so audio sources exist.
if (voiceSeconds === null) {
  const voicesDir = path.join(workDir, "voices");
  fs.mkdirSync(voicesDir, { recursive: true });
  for (const seg of timeline) {
    fs.writeFileSync(path.join(voicesDir, seg.file), silentWav(seg.dur));
  }
}

const total = +(t + 2).toFixed(3);

// ---- background: project custom > named theme > engine default (riverbank) ----
const repoRoot = path.resolve(workDir, "..", "..", "..", "..");
const catalogDir = path.join(repoRoot, "assets", "backgrounds");
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
const tweenLines = [];
let idSeq = 0;
const clip = (inner, extraAttrs, style) => {
  idSeq += 1;
  return `    <div class="clip" id="clip-${idSeq}" data-start="${extraAttrs.start}" data-duration="${extraAttrs.dur}" data-track-index="${extraAttrs.track}" style="position:absolute;inset:0;z-index:${extraAttrs.z}">\n      ${inner}\n    </div>`;
};

clips.push(clip(
  `<img src="background.png" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover" />`,
  { start: 0, dur: total, track: 0, z: 0 },
));
if (settings.bgm && settings.bgm.src) {
  const bgmAbs = path.join(projectDir, settings.bgm.src);
  if (!fs.existsSync(bgmAbs)) die(`settings.bgm.src missing: ${settings.bgm.src}`);
  fs.copyFileSync(bgmAbs, path.join(workDir, "bgm.mp3"));
  const bgmVol = settings.bgm.volume ?? 0.3;
  clips.push(`    <audio class="clip" id="bgm" src="bgm.mp3" data-start="0" data-duration="${total}" data-volume="${bgmVol}" data-track-index="15"></audio>`);
  console.log(`[map-project] bgm: ${settings.bgm.src} at volume ${bgmVol}`);
}

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

const secondaryLang = settings.subtitles?.secondary_language;
for (const seg of timeline) {
  const line = seg.line;
  const text = line.display_text || line.text;
  const secondaryText = secondaryLang
    ? (line.translations || {})[secondaryLang]
    : undefined;
  idSeq += 1;
  clips.push(`    <audio class="clip" id="line-${line.id}-audio" src="voices/${seg.file}" data-start="${seg.start.toFixed(3)}" data-duration="${seg.dur.toFixed(3)}" data-playback-rate="${playbackRate}" data-track-index="20"></audio>`);
  if (line.se) {
    let seAbs = path.join(projectDir, line.se.src);
    if (!fs.existsSync(seAbs)) {
      const shared = path.join(repoRoot, "assets", "se", path.basename(line.se.src));
      if (!fs.existsSync(shared)) die(`script id ${line.id}: sound effect missing: ${line.se.src}`);
      seAbs = shared;
    }
    const seWork = path.join(workDir, line.se.src);
    fs.mkdirSync(path.dirname(seWork), { recursive: true });
    fs.copyFileSync(seAbs, seWork);
    const seDur = probeSeconds(seWork);
    idSeq += 1;
    clips.push(`    <audio class="clip" id="line-${line.id}-se" src="${line.se.src}" data-start="${seg.start.toFixed(3)}" data-duration="${Math.min(seDur, seg.dur + (line.pause_after ?? 0.5)).toFixed(3)}" data-volume="${(line.se.volume ?? 1).toFixed(2)}" data-track-index="21"></audio>`);
  }
  const subStyle = `position:absolute;bottom:${Math.round(subBottomFinal)}px;left:50%;transform:translateX(-50%);width:${subWidthPct}%;text-align:center;font-family:'${fontFamily}',sans-serif;font-size:${fontSize}px;font-weight:${fontWeight};color:${font.color || "#ffffff"};-webkit-text-stroke:${Math.round(fontSize * 0.2)}px ${font.outline_color || "#1F2937"};paint-order:stroke fill;overflow-wrap:anywhere;text-wrap:balance;line-height:1.4`;
  let subInner = `<div style="${subStyle}">${esc(text)}</div>`;
  if (secondaryText) {
    subInner += `<div style="margin-top:${Math.round(subH / 3)}px;font-size:${Math.round(fontSize * 0.55)}px;font-weight:600;opacity:0.92">${esc(secondaryText)}</div>`;
  }
  clips.push(clip(`<div>${subInner}</div>`, { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 30, z: 30 }));
  const v = line.visual;
  if (v && v.type === "terminal") {
    if (!v.command) die(`script id ${line.id}: terminal visual needs a command`);
    const outs = Array.isArray(v.output) ? v.output : [];
    const termFs = 34;
    const outFs = 30;
    const innerW = W * 0.76 - 56;
    const charsPerLine = Math.max(20, Math.floor(innerW / (termFs * 0.62)));
    const cmdLines = Math.max(1, Math.ceil(v.command.length / charsPerLine));
    const minH = 30 + Math.round((cmdLines + outs.length) * termFs * 1.7);
    idSeq += 1;
    const cmdId = `cmd-${idSeq}`;
    let inner =
      `<div style="position:absolute;top:12%;left:50%;transform:translateX(-50%);width:76%;background:#161B22;border:2px solid #30363D;border-radius:12px;box-shadow:0 24px 60px rgba(0,0,0,0.45);overflow:hidden">` +
      `<div style="background:#21262D;padding:10px 16px;display:flex;gap:9px;align-items:center">` +
      `<span style="width:13px;height:13px;border-radius:50%;background:#FF5F56"></span>` +
      `<span style="width:13px;height:13px;border-radius:50%;background:#FFBD2E"></span>` +
      `<span style="width:13px;height:13px;border-radius:50%;background:#27C93F"></span>` +
      `<span style="color:#8B949E;font-size:20px;margin-left:10px">wayang</span></div>` +
      `<div style="padding:22px 28px;font-size:${termFs}px;line-height:1.55;color:#C9D1D9;text-align:left;overflow-wrap:anywhere">` +
      `<div id="${cmdId}"><span style="color:#7EE787">$ </span>`;
    const cmdChars = [...String(v.command)];
    cmdChars.forEach((ch) => {
      inner += `<span class="ch" style="opacity:0">${esc(ch)}</span>`;
    });
    inner += `</div>`;
    outs.forEach((o, i) => {
      const oid = `out-${idSeq}-${i}`;
      inner += `<div id="${oid}" style="opacity:0;color:#9EAEBC;margin-top:12px;font-size:${outFs}px;white-space:pre-wrap">${esc(o)}</div>`;
      tweenLines.push(`tl.to("#${oid}", { opacity: 1, duration: 0.18 }, ${(seg.start + 0.9 + i * 0.5).toFixed(3)});`);
    });
    inner += `</div></div>`;
    const typeStart = seg.start + 0.35;
    const typeDur = Math.min(1.6, Math.max(0.6, cmdChars.length * 0.035));
    tweenLines.push(`tl.to("#${cmdId} .ch", { opacity: 1, duration: 0.02, stagger: ${(typeDur / cmdChars.length).toFixed(4)}, ease: "none" }, ${typeStart.toFixed(3)});`);
    clips.push(clip(inner, { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 }));
  } else if (v && v.type === "image" && v.src) {
    const maxH = v.font_size ? Math.min(v.font_size, H * 0.45) : H * 0.45;
    clips.push(clip(
      `<img src="${v.src}" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);max-width:70%;max-height:${maxH}px;object-fit:contain;border-radius:12px" />`,
      { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 },
    ));
  } else if (v && v.type === "text" && v.text) {
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
${tweenLines.join("\n")}
tl.seek(0);
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(workDir, "index.html"), html);
fs.writeFileSync(path.join(workDir, "package.json"), JSON.stringify({
  name: "wayang-render",
  private: true,
  type: "module",
  scripts: { render: "npx --yes hyperframes render" },
}, null, 2) + "\n");

fs.writeFileSync(path.join(workDir, "expected-seconds.txt"), String(total));
fs.writeFileSync(path.join(workDir, "timeline.json"), JSON.stringify({
  lines: timeline.map((s) => ({ id: s.line.id, start: +s.start.toFixed(3), end: +s.end.toFixed(3) })),
  total,
}));
console.log(`[map-project] characters: ${Object.keys(chars).join(", ")}`);
console.log(`[map-project] lines: ${script.length}, total: ${total}s`);
