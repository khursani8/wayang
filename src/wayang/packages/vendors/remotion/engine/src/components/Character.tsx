import { Img, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { CharacterId } from "../config";
import { CHARACTERS } from "../data/script";
import { SETTINGS, AVAILABLE_IMAGES } from "../settings.generated";

interface CharacterProps {
  characterId: CharacterId;
  isSpeaking: boolean;
  emotion?: string;
  mouth?: [number, number][]; // audio-driven open windows, line-relative frames
  lineFrame?: number; // frames since the current line started
}

// Image file name for the current emotion (existence-checked)
const getImageFileName = (
  characterId: string,
  emotion: string,
  mouthOpen: boolean
): string => {
  const state = mouthOpen ? "open" : "close";
  const availableFiles = AVAILABLE_IMAGES[characterId] || [];

  // Normal expression or no emotion
  if (emotion === "normal" || !emotion) {
    return `mouth_${state}.png`;
  }

  // Emotion variants: {emotion}_open.png, {emotion}_close.png
  const emotionFile = `${emotion}_${state}.png`;
  if (availableFiles.includes(emotionFile)) {
    return emotionFile;
  }

  // Emotion open art only? Fall back to the open image
  const emotionOpenFile = `${emotion}_open.png`;
  if (availableFiles.includes(emotionOpenFile)) {
    return emotionOpenFile;
  }

  // No emotion variant: fall back to the default
  return `mouth_${state}.png`;
};

export const Character: React.FC<CharacterProps> = ({
  characterId,
  isSpeaking,
  emotion = "normal",
  mouth,
  lineFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const characterConfig = CHARACTERS.find((c) => c.id === characterId);

  if (!characterConfig) {
    return null;
  }

  const isLeft = characterConfig.position === "left";

  // Mouth: audio-driven windows when the line carries a schedule, else the
  // fixed ~6fps clock (draft/estimate renders have no schedule).
  const clockOpen = Math.floor(frame / 5) % 2 === 0;
  const scheduledOpen =
    mouth !== undefined &&
    mouth.length > 0 &&
    lineFrame !== undefined &&
    mouth.some(([a, b]) => lineFrame >= a && lineFrame < b);
  const mouthOpen = isSpeaking
    ? mouth !== undefined
      ? scheduledOpen
      : clockOpen
    : false;

  // Gentle bob while speaking
  const bounceY = isSpeaking
    ? interpolate(Math.sin(frame * 0.3), [-1, 1], [-3, 3])
    : 0;

  // Slide in from the character side
  const slideIn = interpolate(frame, [0, fps * 0.5], [isLeft ? -200 : 200, 0], {
    extrapolateRight: "clamp",
  });

  // Scale stays 1 (no size changes)
  const scale = 1;

  // Image path (emotion variants, existence-checked)
  const basePath = SETTINGS.character.imagesBasePath;
  const imageFileName = getImageFileName(characterId, emotion, mouthOpen);
  const currentImage = `${basePath}/${characterId}/${imageFileName}`;

  // useImages flag from settings
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
        // Placeholder when no art exists
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
