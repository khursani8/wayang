/**
 * video-settings.yaml を読み込んで src/settings.generated.ts に変換するスクリプト
 *
 * 使用方法: npm run sync-settings
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "yaml";

const ROOT_DIR = process.cwd();
const YAML_PATH = path.join(ROOT_DIR, "video-settings.yaml");
const OUTPUT_PATH = path.join(ROOT_DIR, "src", "settings.generated.ts");
const IMAGES_DIR = path.join(ROOT_DIR, "public", "images");

interface VideoSettings {
  font: {
    family: string;
    size: number;
    weight: string;
    color: string;
    outlineColor: string;
    innerOutlineColor: string;
  };
  subtitle: {
    bottomOffset: number;
    maxWidthPercent: number;
    maxWidthPixels: number;
    outlineWidth: number;
    innerOutlineWidth: number;
  };
  character: {
    height: number;
    useImages: boolean;
    imagesBasePath: string;
  };
  content: {
    topPadding: number;
    sidePadding: number;
    bottomPadding: number;
  };
  video: {
    width: number;
    height: number;
    fps: number;
    playbackRate: number;
  };
  colors: {
    background: string;
    text: string;
    zundamon: string;
    metan: string;
  };
}

// キャラクターごとの利用可能な画像をスキャン
function scanCharacterImages(): Record<string, string[]> {
  const availableImages: Record<string, string[]> = {};

  if (!fs.existsSync(IMAGES_DIR)) {
    return availableImages;
  }

  const characters = fs.readdirSync(IMAGES_DIR).filter((name) => {
    const stat = fs.statSync(path.join(IMAGES_DIR, name));
    return stat.isDirectory() && !name.startsWith(".");
  });

  for (const character of characters) {
    const charDir = path.join(IMAGES_DIR, character);
    const files = fs.readdirSync(charDir).filter((f) => f.endsWith(".png"));
    availableImages[character] = files;
  }

  return availableImages;
}

function main() {
  console.log("📖 video-settings.yaml を読み込み中...");

  const yamlContent = fs.readFileSync(YAML_PATH, "utf-8");
  const settings: VideoSettings = yaml.parse(yamlContent);

  console.log("🖼️ キャラクター画像をスキャン中...");
  const availableImages = scanCharacterImages();

  for (const [char, files] of Object.entries(availableImages)) {
    console.log(`  ${char}: ${files.join(", ")}`);
  }

  console.log("✨ 設定を変換中...");

  const tsContent = `// このファイルは自動生成されます
// 編集する場合は video-settings.yaml を編集してください
// npm run sync-settings で再生成されます

export const SETTINGS = ${JSON.stringify(settings, null, 2)} as const;

// キャラクターごとの利用可能な画像ファイル
export const AVAILABLE_IMAGES: Record<string, string[]> = ${JSON.stringify(availableImages, null, 2)};

export type VideoSettings = typeof SETTINGS;
`;

  fs.writeFileSync(OUTPUT_PATH, tsContent);

  console.log("✅ src/settings.generated.ts を生成しました");
}

main();
