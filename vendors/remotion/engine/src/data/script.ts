import { CharacterId } from "../config";

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

// content_engine: data-driven character definitions
export const CHARACTERS: { id: CharacterId; name: string; position: "left" | "right"; color: string; flipX: boolean }[] = [
  {
    "id": "momo",
    "name": "Momo",
    "position": "right",
    "color": "#37474F",
    "flipX": false
  },
  {
    "id": "kiki",
    "name": "Kiki",
    "position": "left",
    "color": "#F9A825",
    "flipX": false
  }
];

export const characterColors: Record<string, string> = {"momo":"#37474F","kiki":"#F9A825"};

// This file is generated from config/script.yaml; edit that and re-run npm run sync-script.

export const scriptData: ScriptLine[] = [
  {
    "id": 1,
    "character": "momo",
    "text": "Hai semua! Saya Momo, tapir paling ceria!",
    "scene": 1,
    "pauseAfter": 12,
    "visual": {
      "type": "text",
      "text": "Momo & Kiki",
      "fontSize": 96,
      "color": "#ffffff",
      "animation": "zoomIn"
    },
    "voiceFile": "01_momo.wav",
    "durationInFrames": 60
  },
  {
    "id": 2,
    "character": "kiki",
    "text": "Dan saya Kiki, burung enggang yang tak pernah senyap!",
    "scene": 1,
    "pauseAfter": 12,
    "voiceFile": "02_kiki.wav",
    "durationInFrames": 60
  },
  {
    "id": 3,
    "character": "momo",
    "text": "Kami nak bercerita pasal rakan baharu kita hari ini!",
    "scene": 2,
    "pauseAfter": 12,
    "visual": {
      "type": "text",
      "text": "Rakan Baharu!",
      "fontSize": 84,
      "color": "#ffffff",
      "animation": "slideLeft"
    },
    "voiceFile": "03_momo.wav",
    "durationInFrames": 60
  },
  {
    "id": 4,
    "character": "kiki",
    "text": "Jom kita kenali mereka sama-sama.",
    "scene": 2,
    "pauseAfter": 12,
    "voiceFile": "04_kiki.wav",
    "durationInFrames": 60
  },
  {
    "id": 5,
    "character": "momo",
    "text": "Jangan lupa follow untuk lebih banyak video!",
    "scene": 3,
    "pauseAfter": 12,
    "visual": {
      "type": "text",
      "text": "Follow Kami!",
      "fontSize": 88,
      "color": "#ffffff",
      "animation": "bounce"
    },
    "voiceFile": "05_momo.wav",
    "durationInFrames": 60
  },
  {
    "id": 6,
    "character": "kiki",
    "text": "Jumpa lagi di episod akan datang!",
    "scene": 3,
    "pauseAfter": 15,
    "voiceFile": "06_kiki.wav",
    "durationInFrames": 60
  }
];

// VOICEVOX script generation helper
export const generateVoicevoxScript = (
  data: ScriptLine[],
  characterSpeakerMap: Record<CharacterId, number>
) => {
  return data.map((line) => ({
    id: line.id,
    character: line.character,
    speakerId: characterSpeakerMap[line.character],
    text: line.text,
    outputFile: line.voiceFile,
  }));
};
