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

function probeDims(file) {
  try {
    const out = execSync(
      `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 '${file}'`,
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    );
    const [w, h] = out.trim().split(",").map(Number);
    if (w > 0 && h > 0) return [w, h];
  } catch {
    return [9, 16];
  }
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
// Portrait (shorts) compositions stack instead of spreading: cards go
// narrow with wide margins, type grows, embeds carry a frame.
const portrait = H > W;
// Produced layout variants: settings.layout.variant switches the portrait
// composition. "two-panel" renders the scene (background, visual card,
// terminal, embed, subtitle, corner art) inside the top 56.25% and gives
// the speaking character a close-up panel plus the meta.title card below.
const layoutVariant = settings.layout?.variant || "single";
const twoPanel = portrait && layoutVariant === "two-panel";
const panelSplit = Math.round(H * 0.5625);
const panelGap = 16;
const topBottom = twoPanel ? panelSplit : H;

for (const k of Object.keys(vendorCfg)) {
  if (!["estimate_cps"].includes(k)) {
    die(`vendor.hyperframes: unknown key '${k}' (allowed: estimate_cps)`);
  }
}
if (settings.background !== undefined && typeof settings.background !== "string") {
  die("settings.background must be a theme name string");
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

const TONES = { cinematic: 1.5, playful: 0.85, calm: 1.25, energetic: 0.8 };
const toneFactor = TONES[settings.tone] ?? 1;
const targetDuration = settings.duration;
const pauseOf = (line) => (line.pause_after ?? 0.5);
const openingDur = settings.title_card ? 3 : 0;

// ---- timeline ----
let t = openingDur;
const timeline = [];
for (const line of script) {
  const file = `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
  const raw = voiceSeconds ? voiceSeconds[file] : Math.max(0.8, String(line.text).replace(/\s+/g, "").length / cps);
  const dur = raw / playbackRate;
  const pause = pauseOf(line);
  timeline.push({ line, file, start: t, dur, end: t + dur, pause, subEnd: t + dur + pause / playbackRate });
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

const closingDur = settings.closing_card ? 2.5 : 0;
// target duration: rescale the pause budget so the total lands on it
const voiceWall = timeline.reduce((s, seg) => s + seg.dur, 0);
const pauseWall = timeline.reduce((s, seg) => s + (seg.pause ?? 0) / playbackRate, 0);
const tail = 1 + (settings.title_card ? 3 : 0) + (settings.closing_card ? 2.5 : 0);
let pauseScale = 1;
if (targetDuration && pauseWall > 0) {
  pauseScale = Math.min(2.5, Math.max(0.3, (targetDuration - tail - voiceWall) / pauseWall));
}
let cursor = (settings.title_card ? 3 : 0);
for (const seg of timeline) {
  seg.start = cursor;
  seg.dur = seg.dur;
  seg.end = cursor + seg.dur + seg.pause / playbackRate * pauseScale;
  seg.subEnd = seg.end;
  cursor = seg.end;
}
const total = +(cursor + 1).toFixed(3);

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

// ---- lipsync schedule (optional): audio-driven mouth windows ----
// voices/lipsync.json: { fps, lines: { wav-stem: [[open_start, open_end], ...] } }
// with seconds relative to the voice start. Absent on draft/estimate renders;
// the fixed 0.2s mouth clock stays the fallback.
let lipsyncLines = null;
const lipsyncPath = path.join(workDir, "voices", "lipsync.json");
if (fs.existsSync(lipsyncPath)) {
  try {
    lipsyncLines = JSON.parse(fs.readFileSync(lipsyncPath, "utf8")).lines || null;
  } catch {
    lipsyncLines = null;
  }
  if (lipsyncLines) console.log("[map-project] lipsync: audio-driven mouth (voices/lipsync.json present)");
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
const charInset = portrait ? 56 : 40;
const subWidthPct = settings.subtitle?.max_width_percent ?? 55;
const subBottom = settings.subtitle?.bottom_offset ?? 40;
const subW = (W * subWidthPct) / 100;
// Per-speaker subtitle styling: settings.subtitle.per_character keys the
// primary subtitle color (and optional font_size) by speaking character.
// The declared band uses the largest configured size so lint ink checks
// probe the box the biggest speaker actually draws.
const perChar = settings.subtitle?.per_character || {};
const subFsMax = Math.max(
  fontSize,
  ...Object.values(perChar).map((spk) => spk.font_size || 0),
);
const subLineH = subFsMax * 1.5;
const SUB_MAX_LINES = 2;
const subH = subLineH * SUB_MAX_LINES;
const subX0 = (W - subW) / 2;
const subX1 = (W + subW) / 2;
const charBoxes = Object.values(chars).map((c) => {
  const side = c.position === "left" ? "left" : "right";
  const x0 = side === "left" ? charInset : W - charInset - charH;
  return { side, x0, x1: x0 + charH, y0: topBottom - charH, y1: topBottom };
});
let subY0 = topBottom - subBottom - subH;
let subMoved = false;
for (const box of charBoxes) {
  const intersects = subX0 < box.x1 && subX1 > box.x0 && subY0 < box.y1 && subY0 + subH > box.y0;
  if (intersects) {
    subY0 = Math.min(subY0, box.y0 - 24 - subH);
    subMoved = true;
  }
}
const subBottomFinal = Math.max(0, H - subY0 - subH); // frame-based: the sub div measures from the frame bottom
if (subMoved) {
  console.log(`[map-project] overlap: subtitle moved above characters (bottom ${subBottom} -> ${Math.round(subBottomFinal)}px)`);
}

// ---- HTML generation ----
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const clips = [];
const tweenLines = [];
const embeds = [];
let idSeq = 0;
const clip = (inner, extraAttrs, style) => {
  idSeq += 1;
  return `    <div class="clip" id="clip-${idSeq}" data-start="${extraAttrs.start}" data-duration="${extraAttrs.dur}" data-track-index="${extraAttrs.track}" style="position:absolute;inset:0;z-index:${extraAttrs.z}">\n      ${inner}\n    </div>`;
};


// Two-panel: scene elements are percent-positioned; confining them to the
// top panel needs a positioned ancestor of panel height, so those inners
// are wrapped. px-positioned elements (subtitles, art) need no wrapper.
const sceneWrap = (inner) =>
  twoPanel
    ? `<div style="position:absolute;top:0;left:0;width:100%;height:${panelSplit}px;overflow:hidden">${inner}</div>`
    : inner;
// ---- background: one segment per scene run (per-scene themes) ----
const sceneOf = (line) => line.scene ?? 1;
const runs = [];
for (const seg of timeline) {
  const sc = sceneOf(seg.line);
  if (runs.length && runs[runs.length - 1].scene === sc) {
    runs[runs.length - 1].end = seg.subEnd;
  } else {
    runs.push({ scene: sc, start: seg.start, end: seg.subEnd });
  }
}
for (let i = 0; i < runs.length; i++) {
  runs[i].end = i < runs.length - 1 ? runs[i + 1].start : total;
}
const usedThemes = new Set();
for (const run of runs) {
  const theme = (settings.scenes && settings.scenes[String(run.scene)]) || settings.background || "riverbank";
  usedThemes.add(theme);
  const src = `bg-scene${run.scene}.png`;
  fs.copyFileSync(path.join(repoRoot, "assets", "backgrounds", `${theme}.png`), path.join(workDir, src));
  clips.push(clip(
    `<img src="${src}" style="position:absolute;top:0;left:0;width:100%;height:${twoPanel ? panelSplit : H}px;object-fit:cover" />`,
    { start: run.start.toFixed(3), dur: (run.end - run.start).toFixed(3), track: 0, z: 0 },
  ));
}
if (usedThemes.size > 1) console.log(`[map-project] scene backgrounds: ${[...usedThemes].join(", ")}`);
// (per-scene background segments replace the single full-video image)
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
    const imgStyle = `position:absolute;${twoPanel ? `top:${panelSplit - charH}px` : "bottom:0"};${side}:${charInset}px;height:${charH}px;object-fit:contain`;
    clips.push(clip(
      `<img src="images/${id}/mouth_close.png" style="${imgStyle}" />`,
      { start: 0, dur: total, track: 10, z: 10 },
    ));
    for (const seg of timeline.filter((s) => s.line.character === id)) {
      const windows = lipsyncLines ? lipsyncLines[seg.file.replace(/\.wav$/, "")] : undefined;
      const voiceEnd = seg.start + seg.dur;
      if (windows !== undefined) {
        // Audio-driven: open art on each window, explicit closed art on the
        // gaps (the runtime cannot be trusted to show the track-10 base
        // through 2-frame holes). The pause after the voice falls back to
        // the track-10 base image. Window seconds are wav-relative; wall
        // time divides by the playback rate like the audio element does.
        const emit = (kind, s, e) => {
          if (e - s < 0.02) return;
          clips.push(clip(
            `<img src="images/${id}/mouth_${kind}.png" style="${imgStyle}" />`,
            { start: s.toFixed(3), dur: (e - s).toFixed(3), track: 11, z: 11 },
          ));
        };
        const wall = (t) => Math.max(seg.start, Math.min(voiceEnd, seg.start + t / playbackRate));
        let cursor = seg.start;
        for (const w of windows) {
          const s = wall(Number(w[0]));
          const e = wall(Number(w[1]));
          emit("close", cursor, s);
          emit("open", s, e);
          cursor = e;
        }
        emit("close", cursor, voiceEnd);
      } else {
        // Fixed 0.2s mouth clock (schedule absent: draft/estimate renders)
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
    }
  } else {
    const posCss = side === "left" ? `left:${charInset}px` : `right:${charInset}px`;
    clips.push(clip(
      `<div style="position:absolute;${twoPanel ? `top:${panelSplit - 300}px` : "bottom:0"};${posCss};width:200px;height:300px;background:${color}20;border:4px solid ${color};border-radius:16px;display:flex;align-items:center;justify-content:center"><span style="font-weight:bold;color:${color};font-size:24px">${esc(c.name)}</span></div>`,
      { start: 0, dur: total, track: 10, z: 10 },
    ));
  }
}

// ---- two-panel variant: bottom panel (backdrop, title card, close-up) ----
if (twoPanel) {
  const backdropTop = panelSplit + panelGap;
  const panelStyle = `position:absolute;top:${backdropTop}px;left:0;right:0;bottom:0;background:#0E141B`;
  const titleStyle = `position:absolute;top:${backdropTop + 36}px;left:50%;transform:translateX(-50%);max-width:84%;background:rgba(22,27,34,0.88);border:2px solid #30363D;border-radius:14px;padding:16px 34px;text-align:center;font-family:'${fontFamily}',sans-serif;font-size:54px;font-weight:${fontWeight};color:#FFFFFF;-webkit-text-stroke:10px #1F2937;paint-order:stroke fill`;
  const panelInner = `<div style="${panelStyle}"></div>` +
    (project.meta?.title ? `<div style="${titleStyle}">${esc(project.meta.title)}</div>` : "");
  clips.push(clip(panelInner, { start: 0, dur: total, track: 4, z: 4 }));
  // Speaker-follow close-up: each line parks its character's enlarged art
  // from the line start to the next line start (close art as the base,
  // mouth overlays during the voice windows, same schedule as corner art).
  const closeH = Math.round((H - backdropTop) * 0.78);
  const closeStyle = `position:absolute;bottom:16px;left:50%;transform:translateX(-50%);height:${closeH}px;object-fit:contain`;
  for (let i = 0; i < timeline.length; i++) {
    const seg = timeline[i];
    const until = i + 1 < timeline.length ? timeline[i + 1].start : total;
    const cid = seg.line.character;
    if (!charPos[cid] || !charPos[cid].art) continue;
    clips.push(clip(
      `<img src="images/${cid}/mouth_close.png" style="${closeStyle}" />`,
      { start: seg.start.toFixed(3), dur: (until - seg.start).toFixed(3), track: 12, z: 12 },
    ));
    const windows = lipsyncLines ? lipsyncLines[seg.file.replace(/\.wav$/, "")] : undefined;
    const voiceEnd = seg.start + seg.dur;
    const emit = (kind, s, e) => {
      if (e - s < 0.02) return;
      clips.push(clip(
        `<img src="images/${cid}/mouth_${kind}.png" style="${closeStyle}" />`,
        { start: s.toFixed(3), dur: (e - s).toFixed(3), track: 13, z: 13 },
      ));
    };
    const wall = (t) => Math.max(seg.start, Math.min(voiceEnd, seg.start + t / playbackRate));
    if (windows !== undefined) {
      let cur = seg.start;
      for (const w of windows) {
        const s = wall(Number(w[0]));
        const e = wall(Number(w[1]));
        emit("close", cur, s);
        emit("open", s, e);
        cur = e;
      }
      emit("close", cur, voiceEnd);
    } else {
      let k = seg.start;
      let open = true;
      while (k < seg.end - 0.01) {
        const d = Math.min(0.2, seg.end - k);
        emit(open ? "open" : "close", k, k + d);
        k += d;
        open = !open;
      }
    }
  }
}
function useImagesCheck(settings) {
  return settings.character?.use_images ?? false;
}

const secondaryLang = settings.subtitle?.secondary_language;
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
  // Per-speaker styling: the speaking character's per_character entry
  // colors (and optionally resizes) the primary subtitle.
  const spk = perChar[line.character] || {};
  const subColor = spk.color || font.color || "#ffffff";
  const subFs = spk.font_size || fontSize;
  const subStyle = `position:absolute;bottom:${Math.round(subBottomFinal)}px;left:50%;transform:translateX(-50%);width:${subWidthPct}%;text-align:center;font-family:'${fontFamily}',sans-serif;font-size:${subFs}px;font-weight:${fontWeight};color:${subColor};-webkit-text-stroke:${Math.round(subFs * 0.2)}px ${font.outline_color || "#1F2937"};paint-order:stroke fill;overflow-wrap:anywhere;text-wrap:balance;line-height:1.4`;
  let subInner = `<div style="${subStyle}">${esc(text)}${secondaryText ? `<div style="margin-top:${Math.round(subH / 3)}px;font-size:${Math.round(fontSize * 0.55)}px;font-weight:600;opacity:0.92">${esc(secondaryText)}</div>` : ""}</div>`;
  clips.push(clip(`<div>${subInner}</div>`, { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 30, z: 30 }));
  const v = line.visual;
  if (v && v.type === "terminal") {
    if (!v.command) die(`script id ${line.id}: terminal visual needs a command`);
    const outs = Array.isArray(v.output) ? v.output : [];
    const termFs = portrait ? 40 : 34;
    const outFs = portrait ? 34 : 30;
    const termW = portrait ? 0.88 : 0.76;
    const innerW = W * termW - 56;
    const charsPerLine = Math.max(20, Math.floor(innerW / (termFs * 0.62)));
    const cmdLines = Math.max(1, Math.ceil(v.command.length / charsPerLine));
    const minH = 30 + Math.round((cmdLines + outs.length) * termFs * 1.7);
    idSeq += 1;
    const cmdId = `cmd-${idSeq}`;
    let inner =
      `<div style="position:absolute;top:${portrait ? 14 : 12}%;left:50%;transform:translateX(-50%);width:${Math.round(termW * 100)}%;background:#161B22;border:2px solid #30363D;border-radius:12px;box-shadow:0 24px 60px rgba(0,0,0,0.45);overflow:hidden">` +
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
    clips.push(clip(sceneWrap(inner), { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 }));
  } else if (v && v.type === "image" && v.src) {
    const maxH = v.font_size ? Math.min(v.font_size, H * 0.45) : H * 0.45;
    clips.push(clip(
      sceneWrap(`<img src="${v.src}" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);max-width:70%;max-height:${maxH}px;object-fit:contain;border-radius:12px" />`),
      { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 },
    ));
  } else if (v && v.type === "video" && v.src) {
    // Real-footage payoff: the line shows an actual rendered clip as an
    // inset, timed to the line window. The renderer extracts video frames
    // server-side, so the element only needs timing + muted (never fights
    // the voice track; a muted video carries no audio of its own).
    const vidAbs = path.join(projectDir, v.src);
    if (!fs.existsSync(vidAbs)) die(`script id ${line.id}: visual video missing: ${v.src}`);
    const vidWork = path.join(workDir, v.src);
    fs.mkdirSync(path.dirname(vidWork), { recursive: true });
    fs.copyFileSync(vidAbs, vidWork);
    const vidW = v.width ?? Math.round(W * (portrait ? 0.62 : 0.45));
    const mutedAttr = v.muted === false ? "" : " muted";
    // Frame treatment (owner ruling): embeds never float bare on the
    // scene. The render engine swaps <video> for an injected frame
    // image and does not carry element borders onto it, so the frame
    // lives on a card div wrapping the video: plain DOM chrome renders
    // through the screenshot path and stays glued to the video box.
    // frame: false only for genuinely full-bleed embeds.
    const ring = v.frame === false ? 0 : 6;
    const frameCss = ring
      ? `border:${ring}px solid rgba(255,255,255,0.92);border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,0.45);background:#0B1220;overflow:hidden;`
      : "";
    const [fw, fh] = probeDims(vidWork);
    const cardW = vidW + 2 * ring;
    const cardH = Math.round((vidW * fh) / fw) + 2 * ring;
    const cardX0 = Math.round(W / 2 - cardW / 2);
    const cardY0 = Math.round((twoPanel ? panelSplit : H) * 0.47 - cardH / 2);
    embeds.push({ id: `line-${line.id}`, box: [cardX0, cardY0, cardX0 + cardW, cardY0 + cardH] });
    clips.push(clip(
      sceneWrap(`<div style="position:absolute;top:47%;left:50%;transform:translate(-50%,-50%);width:${cardW}px;${frameCss}">` +
      `<video class="clip" id="line-${line.id}-video" src="${v.src}"${mutedAttr} playsinline style="display:block;width:100%;object-fit:contain" data-start="${seg.start.toFixed(3)}" data-duration="${(seg.subEnd - seg.start).toFixed(3)}" data-track-index="6"></video></div>`),
      { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 6, z: 6 },
    ));
    console.log(`[map-project] video inset: line ${line.id} shows ${v.src} (${probeSeconds(vidWork).toFixed(2)}s source)`);
  } else if (v && v.type === "text" && v.text) {
    const vs = v.font_size || 84;
    const cardStyle = `position:absolute;${portrait ? "inset:8% 8% 60% 0" : "inset:0 0 25% 0"};display:flex;align-items:center;justify-content:center;font-family:'${fontFamily}',sans-serif;font-size:${vs}px;font-weight:bold;color:${v.color || "#ffffff"};-webkit-text-stroke:${Math.round(vs * 0.16)}px ${v.outline_color || "#1F2937"};paint-order:stroke fill;text-align:center;white-space:pre-wrap;text-wrap:balance`;
    clips.push(clip(sceneWrap(`<div style="${cardStyle}">${esc(v.text)}</div>`), { start: seg.start.toFixed(3), dur: (seg.subEnd - seg.start).toFixed(3), track: 5, z: 5 }));
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
  // Declared layout (same shape as the remotion vendor): the subtitle
  // band after the overlap lift (portrait raises it above the
  // characters) plus the character corner boxes, so the platform lint
  // probes the band the composition actually draws.
  layout: {
    subtitle_band: [subX0, subY0, subX1, subY0 + subH].map(Math.round),
    characters: Object.entries(chars).map(([id], i) => ({
      id,
      box: [charBoxes[i].x0, charBoxes[i].y0, charBoxes[i].x1, charBoxes[i].y1].map(Math.round),
    })),
    embeds,
    panels: twoPanel ? { split: panelSplit, gap: panelGap } : undefined,
  },
}));
console.log(`[map-project] characters: ${Object.keys(chars).join(", ")}`);
console.log(`[map-project] lines: ${script.length}, total: ${total}s`);
