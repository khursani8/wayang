/**
 * Maps config/script.yaml + config/characters.yaml to src/data/script.ts.
 * (characters also come from config/characters.yaml.)
 *
 * Usage: npm run sync-script
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "yaml";

const ROOT_DIR = process.cwd();
const SCRIPT_YAML_PATH = path.join(ROOT_DIR, "config", "script.yaml");
const CHARACTERS_YAML_PATH = path.join(ROOT_DIR, "config", "characters.yaml");
const DEFAULTS_YAML_PATH = path.join(ROOT_DIR, "config", "defaults.yaml");
const OUTPUT_PATH = path.join(ROOT_DIR, "src", "data", "script.ts");
const DURATIONS_PATH = path.join(ROOT_DIR, "public", "voices", "durations.json");
const LIPSYNC_PATH = path.join(ROOT_DIR, "public", "voices", "lipsync.json");
const VIDEO_SETTINGS_PATH = path.join(ROOT_DIR, "video-settings.yaml");

interface ScriptLine {
  id: number;
  character: string;
  text: string;
  displayText?: string;
  scene: number;
  pauseAfter: number;
  emotion?: string;
  mouth?: [number, number][];
  visual?: {
    type: string;
    src?: string;
    text?: string;
    fontSize?: number;
    color?: string;
    animation?: string;
  };
  se?: {
    src: string;
    volume?: number;
  };
}

interface CharacterConfig {
  name: string;
  position: string;
  color: string;
  flipX?: boolean;
  defaultPauseAfter: number;
}

interface Defaults {
  newLine: {
    character: string;
    pauseAfter: number;
    durationInFrames: number;
    scene: number;
    emotion: string | null;
  };
  automation: {
    voiceOnSave: boolean;
    autoVoiceFileName: boolean;
  };
}

function loadDurations(): Record<string, number> {
  if (fs.existsSync(DURATIONS_PATH)) {
    const content = fs.readFileSync(DURATIONS_PATH, "utf-8");
    return JSON.parse(content);
  }
  return {};
}

// Lipsync schedule (optional): open windows per wav stem, seconds relative to
// the voice start. Absent on draft/estimate renders -> no mouth field.
interface LipsyncSchedule {
  fps: number;
  lines: Record<string, [number, number][]>;
}

function loadLipsync(): LipsyncSchedule | null {
  if (!fs.existsSync(LIPSYNC_PATH)) return null;
  try {
    const parsed = JSON.parse(fs.readFileSync(LIPSYNC_PATH, "utf-8"));
    return parsed && parsed.lines ? (parsed as LipsyncSchedule) : null;
  } catch {
    console.warn("lipsync.json unreadable, falling back to the fixed mouth clock");
    return null;
  }
}

function main() {
  console.log("Reading config/script.yaml...");

  // Load YAML files
  const scriptYaml = fs.readFileSync(SCRIPT_YAML_PATH, "utf-8");
  const charactersYaml = fs.readFileSync(CHARACTERS_YAML_PATH, "utf-8");
  const defaultsYaml = fs.readFileSync(DEFAULTS_YAML_PATH, "utf-8");

  const scriptData: ScriptLine[] = yaml.parse(scriptYaml) || [];
  const characters: Record<string, CharacterConfig> = yaml.parse(charactersYaml);
  const defaults: Defaults = yaml.parse(defaultsYaml);

  // Load existing durations
  const durations = loadDurations();

  // Lipsync windows (seconds, wav-relative) -> line-relative wall frames.
  // Audio plays at playbackRate, so wav-second t lands at wall frame t*fps/rate.
  const lipsync = loadLipsync();
  let engineFps = 30;
  let playbackRate = 1;
  if (fs.existsSync(VIDEO_SETTINGS_PATH)) {
    const vs = yaml.parse(fs.readFileSync(VIDEO_SETTINGS_PATH, "utf-8"));
    engineFps = vs?.video?.fps ?? 30;
    playbackRate = vs?.video?.playbackRate ?? 1;
  }
  let mouthLines = 0;

  // Generate CharacterId type
  const characterIds = Object.keys(characters);
  const characterIdType = characterIds.map(id => `"${id}"`).join(" | ");

  // Wayang: data-driven character export
  const charsData = characterIds.map((id) => ({
    id,
    name: characters[id].name,
    position: characters[id].position ?? "right",
    color: characters[id].color ?? "#4B5563",
    flipX: characters[id].flipX ?? false,
  }));

  // Process script lines
  const processedLines = scriptData.map((line, index) => {
    const voiceFile = defaults.automation.autoVoiceFileName
      ? `${String(line.id).padStart(2, "0")}_${line.character}.wav`
      : `${String(line.id).padStart(2, "0")}_${line.character}.wav`;

    // Get duration from durations.json or use default
    const durationInFrames = durations[voiceFile] || defaults.newLine.durationInFrames;

    // Mouth open windows for this line, converted to line-relative frames
    let mouth: [number, number][] | undefined;
    const windows = lipsync?.lines?.[voiceFile.replace(/\.wav$/, "")];
    if (lipsync && Array.isArray(windows)) {
      mouth = windows.map(([a, b]) => [
        Math.round((a * engineFps) / playbackRate),
        Math.round((b * engineFps) / playbackRate),
      ] as [number, number]);
      if (mouth.length > 0) mouthLines += 1;
    }

    return {
      ...line,
      voiceFile,
      durationInFrames,
      pauseAfter: line.pauseAfter ?? defaults.newLine.pauseAfter,
      ...(mouth ? { mouth } : {}),
    };
  });

  // Generate TypeScript content
  const tsContent = `import { CharacterId } from "../config";

// Animation types
export type AnimationType = "none" | "fadeIn" | "slideUp" | "slideLeft" | "zoomIn" | "bounce";

// Visual types
export interface VisualContent {
  type: "image" | "text" | "none";
  src?: string;
  text?: string;
  fontSize?: number;
  color?: string;
  outlineColor?: string;
  animation?: AnimationType;
}

// Sound effect types
export interface SoundEffect {
  src: string;
  volume?: number;
}

// BGM types
export interface BGMConfig {
  src: string;
  volume?: number;
  loop?: boolean;
}

// BGM for the whole video
export const bgmConfig: BGMConfig | null = null;

// Script line types
export interface ScriptLine {
  id: number;
  character: CharacterId;
  text: string;
  displayText?: string;
  scene: number;
  voiceFile: string;
  durationInFrames: number;
  pauseAfter: number;
  emotion?: "normal" | "happy" | "surprised" | "thinking" | "sad";
  mouth?: [number, number][]; // audio-driven open windows, line-relative frames
  translations?: Record<string, string>;
  visual?: VisualContent;
  se?: SoundEffect;
}

// Scene metadata
export interface SceneInfo {
  id: number;
  title: string;
  background: string;
}

export const scenes: SceneInfo[] = [
  { id: 1, title: "Opening", background: "gradient" },
  { id: 2, title: "Main Content", background: "solid" },
  { id: 3, title: "Ending", background: "gradient" },
];

// Wayang: data-driven character definitions
export const CHARACTERS: { id: CharacterId; name: string; position: "left" | "right"; color: string; flipX: boolean }[] = ${JSON.stringify(charsData, null, 2)};

export const characterColors: Record<string, string> = ${JSON.stringify(
  Object.fromEntries(charsData.map((c) => [c.id, c.color]))
)};

// This file is generated from config/script.yaml; edit that and re-run npm run sync-script.

export const scriptData: ScriptLine[] = ${JSON.stringify(processedLines, null, 2)};

`;

  fs.writeFileSync(OUTPUT_PATH, tsContent);
  console.log("Generated src/data/script.ts");
  console.log(`   ${processedLines.length} line(s)`);
  if (mouthLines > 0) console.log(`   lipsync: audio-driven mouth on ${mouthLines} line(s)`);
}

main();
