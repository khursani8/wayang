/**
 * Maps video-settings.yaml to src/settings.generated.ts.
 *
 * Usage: npm run sync-settings
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
    accent1: string;
    accent2: string;
  };
}

// Scan public/images/<id>/ for available character art.
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
  console.log("Reading video-settings.yaml...");

  const yamlContent = fs.readFileSync(YAML_PATH, "utf-8");
  const settings: VideoSettings = yaml.parse(yamlContent);

  console.log("Scanning character images...");
  const availableImages = scanCharacterImages();

  for (const [char, files] of Object.entries(availableImages)) {
    console.log(`  ${char}: ${files.join(", ")}`);
  }

  console.log("Generating settings...");

  const tsContent = `// This file is generated from video-settings.yaml by sync-settings.ts.
// Edit video-settings.yaml and re-run npm run sync-settings.

export const SETTINGS = ${JSON.stringify(settings, null, 2)} as const;

// Available art files per character id (scanned from public/images).
export const AVAILABLE_IMAGES: Record<string, string[]> = ${JSON.stringify(availableImages, null, 2)};

export type VideoSettings = typeof SETTINGS;
`;

  fs.writeFileSync(OUTPUT_PATH, tsContent);

  console.log("Generated src/settings.generated.ts");
}

main();
