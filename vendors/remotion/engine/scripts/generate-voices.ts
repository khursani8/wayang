#!/usr/bin/env npx ts-node

/**
 * VOICEVOX batch voice generation
 *
 * Usage:
 *   npx ts-node scripts/generate-voices.ts
 *
 * Requires:
 *   - VOICEVOX running at localhost:50021
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "yaml";

const ROOT_DIR = process.cwd();

// Settings
const CONFIG_PATH = path.join(ROOT_DIR, "src/config.ts");
const SCRIPT_PATH = path.join(ROOT_DIR, "src/data/script.ts");
const OUTPUT_DIR = path.join(ROOT_DIR, "public/voices");

interface VoiceGenerationConfig {
  host: string;
  playbackRate: number;
  fps: number;
}

interface ScriptLine {
  id: number;
  character: string;
  text: string;
  voiceFile: string;
}

interface CharacterConfig {
  id: string;
  voicevoxSpeakerId: number;
}

// Check VOICEVOX is up
async function checkVoicevox(host: string): Promise<boolean> {
  try {
    const response = await fetch(`${host}/version`);
    if (response.ok) {
      const version = await response.text();
      console.log(`VOICEVOX version: ${version}`);
      return true;
    }
  } catch (e) {
    console.error("Cannot reach VOICEVOX. Start it and retry.");
  }
  return false;
}

// Fetch an audio query
async function getAudioQuery(
  host: string,
  text: string,
  speakerId: number
): Promise<any> {
  const encodedText = encodeURIComponent(text);
  const response = await fetch(
    `${host}/audio_query?speaker=${speakerId}&text=${encodedText}`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error(`audio_query failed: ${response.statusText}`);
  }
  return response.json();
}

// Synthesize
async function synthesize(
  host: string,
  query: any,
  speakerId: number
): Promise<ArrayBuffer> {
  const response = await fetch(`${host}/synthesis?speaker=${speakerId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
  if (!response.ok) {
    throw new Error(`synthesis failed: ${response.statusText}`);
  }
  return response.arrayBuffer();
}

// WAV duration in seconds - RIFF header parsed in node (no python3 shell-out)
function getWavDuration(filePath: string): number {
  const buf = fs.readFileSync(filePath);
  if (buf.length < 44 || buf.toString("ascii", 0, 4) !== "RIFF") {
    console.error(`Failed to get duration for ${filePath}: not a RIFF wav`);
    return 0;
  }
  const byteRate = buf.readUInt32LE(28);
  const dataSize = buf.readUInt32LE(40);
  if (byteRate === 0) {
    console.error(`Failed to get duration for ${filePath}: bad byte rate`);
    return 0;
  }
  return dataSize / byteRate;
}

// Main
async function main() {
  const host = "http://localhost:50021";
  const settingsYaml = yaml.parse(
    fs.readFileSync(path.join(ROOT_DIR, "video-settings.yaml"), "utf-8")
  );
  const fps = settingsYaml.video?.fps ?? 30;
  const playbackRate = settingsYaml.video?.playbackRate ?? 1.2;

  // VOICEVOX check
  if (!(await checkVoicevox(host))) {
    process.exit(1);
  }

  // Output directory
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Load script data
  // (simple regex parse of src/data/script.ts below)
  console.log("Loading script data...");
  // Data comes from the parse below.

 
  const scriptData: ScriptLine[] = [];
  // Character speaker ids come from config/characters.yaml (data-driven)
  const charactersYaml = yaml.parse(
    fs.readFileSync(path.join(ROOT_DIR, "config", "characters.yaml"), "utf-8")
  ) as Record<string, { speakerId: number | null }>;
  const characters: Map<string, number> = new Map(
    Object.entries(charactersYaml)
      .filter(([, c]) => c.speakerId !== null)
      .map(([id, c]) => [id, c.speakerId as number])
  );

  // Parse src/data/script.ts
  const scriptContent = fs.readFileSync(SCRIPT_PATH, "utf-8");
  const scriptDataMatch = scriptContent.match(
    /export const scriptData[^=]*=\s*\[([\s\S]*?)\];/
  );

  if (scriptDataMatch) {
    // Simple regex parse
    const dataStr = scriptDataMatch[1];
    const lineMatches = dataStr.matchAll(
      /\{\s*"?id"?:\s*(\d+),\s*"?character"?:\s*"([^"]+)",\s*"?text"?:\s*"([^"]+)"[\s\S]*?"?voiceFile"?:\s*"([^"]+)"/g
    );

    for (const match of lineMatches) {
      scriptData.push({
        id: parseInt(match[1]),
        character: match[2],
        text: match[3],
        voiceFile: match[4],
      });
    }
  }

  console.log(`Processing ${scriptData.length} line(s)...`);

  const durationsArray: { id: number; file: string; duration: number; frames: number }[] = [];
  const durationsMap: Record<string, number> = {};

  for (const line of scriptData) {
    const speakerId = characters.get(line.character);
    if (speakerId === undefined) {
      throw new Error(
        `Unknown character: ${line.character} (config/characters.yaml has no VOICEVOX speakerId)`
      );
    }

    const outputPath = path.join(OUTPUT_DIR, line.voiceFile);

    // Optional skip of existing files
    // if (fs.existsSync(outputPath)) {
    //   console.log(`Skip: ${line.voiceFile} (already exists)`);
    //   continue;
    // }

    try {
      console.log(`Generating: ${line.voiceFile} - "${line.text.substring(0, 30)}..."`);

    // Audio query
      const query = await getAudioQuery(host, line.text, speakerId);

    // Synthesis
      const audio = await synthesize(host, query, speakerId);

    // Save
      fs.writeFileSync(outputPath, Buffer.from(audio));

    // Measure duration and convert to frames
      const duration = getWavDuration(outputPath);
      const frames = Math.ceil(duration * fps * playbackRate);

      durationsArray.push({
        id: line.id,
        file: line.voiceFile,
        duration,
        frames,
      });
      durationsMap[line.voiceFile] = frames;

      console.log(`  -> ${duration.toFixed(2)}s, ${frames} frames`);

    } catch (e) {
      console.error(`Error generating ${line.voiceFile}:`, e);
    }
  }

  // Save durations.json (the format sync-script.ts expects)
  const resultPath = path.join(OUTPUT_DIR, "durations.json");
  fs.writeFileSync(resultPath, JSON.stringify(durationsMap, null, 2));
  console.log(`\nDuration data saved to: ${resultPath}`);

  // Output snippet for script.ts updates
  console.log("\n=== script.ts update snippet ===");
  for (const d of durationsArray) {
    console.log(`ID ${d.id}: durationInFrames: ${d.frames}, // ${d.duration.toFixed(2)}s`);
  }
}

main().catch(console.error);
