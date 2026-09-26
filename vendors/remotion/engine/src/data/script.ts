import { CharacterId } from "../config";

// アニメーションの型定義
export type AnimationType = "none" | "fadeIn" | "slideUp" | "slideLeft" | "zoomIn" | "bounce";

// ビジュアルの型定義
export interface VisualContent {
  type: "image" | "text" | "none";
  src?: string;
  text?: string;
  fontSize?: number;
  color?: string;
  animation?: AnimationType;
}

// 効果音の型定義
export interface SoundEffect {
  src: string;
  volume?: number;
}

// BGM設定
export interface BGMConfig {
  src: string;
  volume?: number;
  loop?: boolean;
}

// BGM設定（動画全体で使用）
export const bgmConfig: BGMConfig | null = null;

// セリフデータの型定義
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

// シーン定義
export interface SceneInfo {
  id: number;
  title: string;
  background: string;
}

export const scenes: SceneInfo[] = [
  { id: 1, title: "オープニング", background: "gradient" },
  { id: 2, title: "メインコンテンツ", background: "solid" },
  { id: 3, title: "エンディング", background: "gradient" },
];

// content_engine: データ駆動キャラクター定義
export const CHARACTERS: { id: CharacterId; name: string; position: "left" | "right"; color: string; flipX: boolean }[] = [
  {
    "id": "zundamon",
    "name": "ずんだもん",
    "position": "right",
    "color": "#228B22",
    "flipX": false
  },
  {
    "id": "metan",
    "name": "四国めたん",
    "position": "left",
    "color": "#FF1493",
    "flipX": false
  },
  {
    "id": "kuro_zunda",
    "name": "くろずんだ",
    "position": "right",
    "color": "#333333",
    "flipX": false
  }
];

export const characterColors: Record<string, string> = {"zundamon":"#228B22","metan":"#FF1493","kuro_zunda":"#333333"};

// このファイルは config/script.yaml から自動生成されます
// 編集する場合は config/script.yaml を編集して npm run sync-script を実行してください
export const scriptData: ScriptLine[] = [
  {
    "id": 1,
    "character": "zundamon",
    "text": "ずんだもんなのだ！",
    "scene": 1,
    "pauseAfter": 15,
    "visual": {
      "type": "text",
      "text": "Remotion × VOICEVOX\nテンプレート",
      "fontSize": 80,
      "color": "#ffffff",
      "animation": "zoomIn"
    },
    "voiceFile": "01_zundamon.wav",
    "durationInFrames": 53
  },
  {
    "id": 2,
    "character": "metan",
    "text": "四国めたんです。",
    "scene": 1,
    "pauseAfter": 15,
    "voiceFile": "02_metan.wav",
    "durationInFrames": 44
  },
  {
    "id": 3,
    "character": "zundamon",
    "text": "このテンプレートで紹介動画が作れるのだ！",
    "scene": 1,
    "pauseAfter": 10,
    "voiceFile": "03_zundamon.wav",
    "durationInFrames": 123
  },
  {
    "id": 4,
    "character": "metan",
    "text": "よろしくね。",
    "scene": 1,
    "pauseAfter": 30,
    "voiceFile": "04_metan.wav",
    "durationInFrames": 31
  }
];

// VOICEVOXスクリプト生成用
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
