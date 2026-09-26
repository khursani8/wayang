// 動画設定
export const VIDEO_CONFIG = {
  width: 1920,
  height: 1080,
  fps: 30,
  playbackRate: 1.2, // 再生速度（音声生成時に考慮）
};

// カラーパレット（黒板風デザイン）
export const COLORS = {
  background: "#ffffff",      // 外側の白背景
  blackboard: "#2d5a3d",      // 黒板の緑
  blackboardBorder: "#8B4513", // 黒板の茶色フチ
  text: "#ffffff",            // 白文字
  textMuted: "#e0e0e0",
  primary: "#3b82f6",
  success: "#22c55e",
  warning: "#f59e0b",
  error: "#ef4444",
  pink: "#ec4899",
  zundamon: "#228B22",        // フォレストグリーン（暗め）
  metan: "#FF1493",           // ディープピンク
};

// キャラクター定義
// Character ids are data-driven: any id from config/characters.yaml works.
export type CharacterId = string;

export interface CharacterConfig {
  id: CharacterId;
  name: string;
  voicevoxSpeakerId: number;
  position: "left" | "right";
  color: string;
  // 画像設定（口パクアニメーション用）
  images: {
    mouthOpen: string; // 口開き画像パス
    mouthClose: string; // 口閉じ画像パス
  };
  flipX?: boolean; // 画像を左右反転するか
}

// Data-driven character list lives in src/data/script.ts (generated from
// config/characters.yaml by scripts/sync-script.ts).

// シーン背景タイプ
export type BackgroundType = "gradient" | "solid" | "image";

export interface SceneConfig {
  id: number;
  title: string;
  background: BackgroundType;
  backgroundColor?: string;
  backgroundImage?: string;
}

// VOICEVOX設定
export const VOICEVOX_CONFIG = {
  host: "http://localhost:50021",
  defaultSpeedScale: 1.0,
  defaultPitchScale: 0.0,
  defaultIntonationScale: 1.0,
  defaultVolumeScale: 1.0,
};
