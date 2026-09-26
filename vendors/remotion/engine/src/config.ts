// Video settings and palette for the remotion engine (content_engine port).
export const VIDEO_CONFIG = {
  width: 1920,
  height: 1080,
  fps: 30,
  playbackRate: 1.2,
};

// Palette. Character colors come from config/characters.yaml (generated
// into src/data/script.ts); these are engine-level fallbacks.
export const COLORS = {
  background: "#ffffff",
  text: "#ffffff",
  textMuted: "#e0e0e0",
  accent1: "#37474F",
  accent2: "#F9A825",
};

// Character ids are data-driven: any id from config/characters.yaml works.
export type CharacterId = string;

// VOICEVOX speaker ids live in config/characters.yaml (see map-project.mjs
// and generate-voices.ts). Kept empty for the standalone sample.
export const characterSpeakerMap: Record<CharacterId, number> = {};
