import { Img, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { CharacterId } from "../config";
import { CHARACTERS } from "../data/script";
import { SETTINGS, AVAILABLE_IMAGES } from "../settings.generated";

interface CharacterProps {
  characterId: CharacterId;
  isSpeaking: boolean;
  emotion?: string;
}

// 表情に応じた画像ファイル名を取得（存在チェック付き）
const getImageFileName = (
  characterId: string,
  emotion: string,
  mouthOpen: boolean
): string => {
  const state = mouthOpen ? "open" : "close";
  const availableFiles = AVAILABLE_IMAGES[characterId] || [];

  // 通常表情またはemotionがない場合
  if (emotion === "normal" || !emotion) {
    return `mouth_${state}.png`;
  }

  // 表情差分を試す: {emotion}_open.png, {emotion}_close.png
  const emotionFile = `${emotion}_${state}.png`;
  if (availableFiles.includes(emotionFile)) {
    return emotionFile;
  }

  // 表情の口開き画像だけある場合（口閉じがない）、口開き画像を使う
  const emotionOpenFile = `${emotion}_open.png`;
  if (availableFiles.includes(emotionOpenFile)) {
    return emotionOpenFile;
  }

  // 表情差分がない場合はデフォルトにフォールバック
  return `mouth_${state}.png`;
};

export const Character: React.FC<CharacterProps> = ({
  characterId,
  isSpeaking,
  emotion = "normal",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const characterConfig = CHARACTERS.find((c) => c.id === characterId);

  if (!characterConfig) {
    return null;
  }

  const isLeft = characterConfig.position === "left";

  // 口パクアニメーション（話している時、約6fpsで口を開閉）
  const mouthOpen = isSpeaking ? Math.floor(frame / 5) % 2 === 0 : false;

  // 話している時のアニメーション（上下に揺れる）
  const bounceY = isSpeaking
    ? interpolate(Math.sin(frame * 0.3), [-1, 1], [-3, 3])
    : 0;

  // 登場アニメーション（画面端からスライドイン）
  const slideIn = interpolate(frame, [0, fps * 0.5], [isLeft ? -200 : 200, 0], {
    extrapolateRight: "clamp",
  });

  // スケールは常に1（サイズ変更なし）
  const scale = 1;

  // 画像パスを取得（表情差分対応、存在チェック付き）
  const basePath = SETTINGS.character.imagesBasePath;
  const imageFileName = getImageFileName(characterId, emotion, mouthOpen);
  const currentImage = `${basePath}/${characterId}/${imageFileName}`;

  // 設定ファイルのuseImagesフラグをチェック
  const hasImage = SETTINGS.character.useImages;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        [characterConfig.position]: slideIn,
        transform: `translateY(${bounceY}px) scale(${scale})`,
        transformOrigin: isLeft ? "bottom left" : "bottom right",
      }}
    >
      {hasImage ? (
        <Img
          src={staticFile(currentImage)}
          style={{
            height: SETTINGS.character.height,
            objectFit: "contain",
            transform: characterConfig.flipX ? "scaleX(-1)" : "none",
          }}
        />
      ) : (
        // 画像がない場合のプレースホルダー
        <div
          style={{
            width: 200,
            height: 300,
            background: `${characterConfig.color}20`,
            border: `4px solid ${characterConfig.color}`,
            borderRadius: 16,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div style={{ fontSize: 48 }}>
            {characterId === "zundamon" ? "🟢" : characterId === "metan" ? "🩷" : "💬"}
          </div>
          <div
            style={{
              fontSize: 20,
              fontWeight: "bold",
              color: characterConfig.color,
              marginTop: 8,
            }}
          >
            {characterConfig.name}
          </div>
        </div>
      )}
    </div>
  );
};
