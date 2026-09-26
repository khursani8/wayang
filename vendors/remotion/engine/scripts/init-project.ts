/**
 * 新規プロジェクト初期化スクリプト
 *
 * 使用方法: npm run init
 *
 * - script.tsをサンプルにリセット
 * - 音声ファイルを削除
 * - 出力ファイルを削除
 */

import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";

const PROJECT_ROOT = path.join(__dirname, "..");
const VOICES_DIR = path.join(PROJECT_ROOT, "public", "voices");
const OUT_DIR = path.join(PROJECT_ROOT, "out");
const SCRIPT_PATH = path.join(PROJECT_ROOT, "src", "data", "script.ts");

const SAMPLE_SCRIPT = `import { CharacterId } from "../config";

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

// シーン定義
export const scenes: SceneInfo[] = [
  { id: 1, title: "オープニング", background: "gradient" },
  { id: 2, title: "メインコンテンツ", background: "solid" },
  { id: 3, title: "エンディング", background: "gradient" },
];

// セリフデータ
// Claude Codeに「〇〇の紹介動画を作りたい」と伝えてください
export const scriptData: ScriptLine[] = [
  {
    id: 1,
    character: "zundamon",
    text: "こんにちは！今日は〇〇を紹介するのだ！",
    scene: 1,
    voiceFile: "01_zundamon.wav",
    durationInFrames: 100,
    pauseAfter: 10,
    emotion: "happy",
  },
  {
    id: 2,
    character: "metan",
    text: "楽しみね。詳しく教えて？",
    scene: 1,
    voiceFile: "02_metan.wav",
    durationInFrames: 80,
    pauseAfter: 10,
  },
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
`;

async function confirm(question: string): Promise<boolean> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(question + " (y/N): ", (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === "y");
    });
  });
}

function deleteDirectory(dirPath: string): void {
  if (fs.existsSync(dirPath)) {
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      if (fs.statSync(filePath).isDirectory()) {
        deleteDirectory(filePath);
      } else {
        fs.unlinkSync(filePath);
      }
    }
  }
}

async function main() {
  console.log("🎬 Remotion + VOICEVOX プロジェクト初期化\n");

  const shouldContinue = await confirm(
    "⚠️  現在のスクリプトと音声ファイルが削除されます。続行しますか？"
  );

  if (!shouldContinue) {
    console.log("キャンセルしました。");
    process.exit(0);
  }

  // 1. script.tsをリセット
  console.log("\n📝 script.ts をリセット中...");
  fs.writeFileSync(SCRIPT_PATH, SAMPLE_SCRIPT);
  console.log("   ✅ script.ts をサンプルにリセットしました");

  // 2. 音声ファイルを削除
  console.log("\n🔊 音声ファイルを削除中...");
  if (fs.existsSync(VOICES_DIR)) {
    const files = fs.readdirSync(VOICES_DIR).filter((f) => f.endsWith(".wav"));
    for (const file of files) {
      fs.unlinkSync(path.join(VOICES_DIR, file));
    }
    console.log(`   ✅ ${files.length}個の音声ファイルを削除しました`);
  } else {
    console.log("   ℹ️  音声ファイルはありません");
  }

  // 3. 出力ファイルを削除
  console.log("\n🎥 出力ファイルを削除中...");
  if (fs.existsSync(OUT_DIR)) {
    const files = fs.readdirSync(OUT_DIR);
    for (const file of files) {
      fs.unlinkSync(path.join(OUT_DIR, file));
    }
    console.log(`   ✅ ${files.length}個の出力ファイルを削除しました`);
  } else {
    console.log("   ℹ️  出力ファイルはありません");
  }

  console.log("\n🎉 初期化完了！");
  console.log("\n次のステップ:");
  console.log("  1. Claude Codeを起動: claude");
  console.log('  2. 「〇〇の紹介動画を作りたい」と伝える');
  console.log("");
}

main();
