#!/usr/bin/env node
// map-project.mjs - canonical project.yaml -> remotion engine inputs.
// Usage: node map-project.mjs PROJECT_DIR WORK_DIR
// Writes: config/characters.yaml, config/script.yaml, config/defaults.yaml,
//         video-settings.yaml, public/voices/durations.json + silent wavs.
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
const require = createRequire(path.join(workDir, "package.json"));
const YAML = require("yaml");

function die(msg) {
  console.error(`[map-project] ERROR: ${msg}`);
  process.exit(1);
}

// Platform materializes series inheritance into .merged.yaml; prefer it.
const mergedPath = path.join(projectDir, ".merged.yaml");
const projectPath = fs.existsSync(mergedPath)
  ? mergedPath
  : path.join(projectDir, "project.yaml");
if (!fs.existsSync(projectPath)) die(`missing ${projectPath}`);
let project;
try {
  project = YAML.parse(fs.readFileSync(projectPath, "utf8"));
} catch (e) {
  die(`project.yaml parse error: ${e.message}`);
}

const chars = project.characters || {};
const script = project.script || [];
const settings = project.settings || {};
const vendorCfg = (project.vendor && project.vendor.remotion) || {};
const fps = settings.video?.fps ?? 30;
const playbackRate = settings.video?.playback_rate ?? 1.2;
const cps = vendorCfg.estimate_cps ?? 7.5;

// ---- vendor key gate: unknown keys error (platform rule) ----
const vendorKeysAllowed = ["estimate_cps"];
for (const k of Object.keys(vendorCfg)) {
  if (!vendorKeysAllowed.includes(k)) {
    die(`vendor.remotion: unknown key '${k}' (allowed: ${vendorKeysAllowed.join(", ")})`);
  }
}

// ---- settings gate + snake_case -> engine camelCase ----
const settingsMap = {
  video: { width: "width", height: "height", fps: "fps", playback_rate: "playbackRate" },
  font: { family: "family", size: "size", weight: "weight", color: "color" },
  subtitle: { bottom_offset: "bottomOffset", max_width_percent: "maxWidthPercent", outline_width: "outlineWidth" },
  character: { height: "height", use_images: "useImages", images_base_path: "imagesBasePath" },
  content: { top_padding: "topPadding", side_padding: "sidePadding", bottom_padding: "bottomPadding" },
};
const engineDefaults = {
  font: { family: "M PLUS Rounded 1c", size: 70, weight: "900", color: "#ffffff", outlineColor: "character", innerOutlineColor: "none" },
  subtitle: { bottomOffset: 40, maxWidthPercent: 55, maxWidthPixels: 1000, outlineWidth: 14, innerOutlineWidth: 8 },
  character: { height: 275, useImages: false, imagesBasePath: "images" },
  content: { topPadding: 0, sidePadding: 0, bottomPadding: 0 },
  video: { width: 1920, height: 1080, fps: 30, playbackRate: 1.2 },
};
const engineSettings = structuredClone(engineDefaults);
for (const section of Object.keys(settings)) {
  const map = settingsMap[section];
  if (!map) die(`settings: unknown section '${section}' (allowed: ${Object.keys(settingsMap).join(", ")})`);
  for (const key of Object.keys(settings[section])) {
    if (!(key in map)) die(`settings.${section}: unknown key '${key}' (allowed: ${Object.keys(map).join(", ")})`);
    if (!engineSettings[section]) die(`settings: unknown section '${section}'`);
    engineSettings[section][map[key]] = settings[section][key];
  }
}

// ---- characters -> config/characters.yaml ----
const engineCharacters = {};
for (const [id, c] of Object.entries(chars)) {
  // Voice engine validation is the platform's job (tools/ce.py via the
  // provider registry). The vendor consumes project voices regardless of
  // which engine produced them.
  engineCharacters[id] = {
    name: c.name,
    speakerId: c.voice.speaker_id ?? null,
    position: c.position ?? "right",
    color: c.color ?? "#4B5563",
    flipX: c.flip_x ?? false,
    defaultPauseAfter: 15,
  };
}
const charIds = Object.keys(engineCharacters);
if (charIds.length === 0) die("no characters defined");

// ---- script -> config/script.yaml (pause seconds -> frames) ----
const engineScript = [];
for (const line of script) {
  if (!chars[line.character]) die(`script id ${line.id}: unknown character '${line.character}'`);
  const mapped = {
    id: line.id,
    character: line.character,
    text: line.text,
  };
  if (line.display_text) mapped.displayText = line.display_text;
  if (line.scene) mapped.scene = line.scene;
  if (line.pause_after !== undefined) mapped.pauseAfter = Math.round(line.pause_after * fps);
  if (line.emotion) mapped.emotion = line.emotion;
  if (line.visual && line.visual.type !== "none") {
    const v = { type: line.visual.type };
    if (line.visual.text) v.text = line.visual.text;
    if (line.visual.src) {
      if (!fs.existsSync(path.join(projectDir, line.visual.src))) {
        die(`script id ${line.id}: visual image missing: ${line.visual.src}`);
      }
      v.src = line.visual.src;
    }
    if (line.visual.font_size) v.fontSize = line.visual.font_size;
    if (line.visual.color) v.color = line.visual.color;
    if (line.visual.animation) v.animation = line.visual.animation;
    mapped.visual = v;
  }
  if (line.se) {
    if (!fs.existsSync(path.join(projectDir, line.se.src))) {
      die(`script id ${line.id}: sound effect missing: ${line.se.src}`);
    }
    mapped.se = { src: line.se.src, volume: line.se.volume ?? 1 };
  }
  engineScript.push(mapped);
}
if (engineScript.length === 0) die("script is empty");

// ---- defaults.yaml ----
const engineDefaultsYaml = {
  newLine: {
    character: engineScript[0].character,
    pauseAfter: 15,
    durationInFrames: 60,
    scene: 1,
    emotion: null,
  },
  automation: { voiceOnSave: false, autoVoiceFileName: true },
};

// ---- write engine configs ----
fs.mkdirSync(path.join(workDir, "config"), { recursive: true });
fs.writeFileSync(path.join(workDir, "config", "characters.yaml"), YAML.stringify(engineCharacters));
fs.writeFileSync(path.join(workDir, "config", "script.yaml"), YAML.stringify(engineScript));
fs.writeFileSync(path.join(workDir, "config", "defaults.yaml"), YAML.stringify(engineDefaultsYaml));

// ---- video-settings.yaml ----
const charColors = charIds.map((id) => engineCharacters[id].color);
engineSettings.colors = {
  background: "#ffffff",
  text: engineSettings.font.color,
  zundamon: charColors[0],
  metan: charColors[1] ?? charColors[0],
};
fs.writeFileSync(path.join(workDir, "video-settings.yaml"), YAML.stringify(engineSettings));

// ---- estimated timing + silent placeholder wavs (TTS source: estimate) ----
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

const workVoices = path.join(workDir, "public", "voices");
fs.mkdirSync(workVoices, { recursive: true });
const durations = {};

// ---- Priority 1: platform-generated voices in PROJECT_DIR/voices ----
const projectVoices = path.join(projectDir, "voices");
const manifestPath = path.join(projectVoices, "manifest.json");
let platformEngines = null;
if (fs.existsSync(manifestPath)) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const entries = manifest.lines || {};
  const fileName = (line) => `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
  const missing = engineScript.filter(
    (line) => !entries[fileName(line)] || !fs.existsSync(path.join(projectVoices, fileName(line)))
  );
  if (missing.length === 0) {
    for (const line of engineScript) {
      const f = fileName(line);
      const seconds = Number(entries[f].seconds);
      if (!Number.isFinite(seconds) || seconds <= 0) {
        die(`voices/manifest.json: bad seconds for ${f}`);
      }
      fs.copyFileSync(path.join(projectVoices, f), path.join(workVoices, f));
      durations[f] = Math.ceil(seconds * fps * playbackRate);
    }
    platformEngines = manifest.engines && manifest.engines.length ? manifest.engines : ["unknown"];
    console.log(`[map-project] TTS source: ${platformEngines.join("+")} (platform-generated voices)`);
  }
}

// ---- Priority 2: estimate + silent placeholder wavs ----
if (platformEngines === null) {
  console.log("[map-project] TTS source: estimate (durations.json + silent placeholder wavs written)");
  for (const line of engineScript) {
    const visible = String(line.text).replace(/\s+/g, "").length;
    const seconds = visible / (cps * playbackRate);
    const frames = Math.max(24, Math.ceil(seconds * fps));
    const f = `${String(line.id).padStart(2, "0")}_${line.character}.wav`;
    durations[f] = frames;
    fs.writeFileSync(path.join(workVoices, f), silentWav(frames / fps));
  }
}
fs.writeFileSync(path.join(workVoices, "durations.json"), JSON.stringify(durations, null, 2));
fs.writeFileSync(path.join(workVoices, ".source"), platformEngines ? "platform" : "estimate");

console.log(`[map-project] characters: ${charIds.join(", ")}`);
console.log(`[map-project] lines: ${engineScript.length}, fps: ${fps}, playbackRate: ${playbackRate}, estimate_cps: ${cps}`);