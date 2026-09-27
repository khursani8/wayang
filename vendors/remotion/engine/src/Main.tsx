import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio, Sequence, staticFile, Loop, Img } from "remotion";
import { useMemo } from "react";
import { loadFont } from "@remotion/google-fonts/MPLUSRounded1c";
import { scriptData, scenes, ScriptLine, bgmConfig, CHARACTERS } from "./data/script";
import { COLORS } from "./config";
import { SETTINGS } from "./settings.generated";
import { Subtitle } from "./components/Subtitle";
import { Character } from "./components/Character";
import { SceneVisuals } from "./components/SceneVisuals";

// Load Google Fonts
const { fontFamily } = loadFont();

// Frame counts adjusted for playback rate
const getAdjustedFrames = (frames: number): number =>
  Math.ceil(frames / SETTINGS.video.playbackRate);

export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Card window (frames). Must match Root.tsx exactly.
  const fpsSetting = SETTINGS.video.fps ?? 30;
  const openingFrames = SETTINGS.titleCard ? Math.round(3 * fpsSetting) : 0;
  const closingFrames = SETTINGS.closingCard ? Math.round(2.5 * fpsSetting) : 60;
  const linesWall = scriptData.reduce(
    (sum, l) => sum + getAdjustedFrames(l.durationInFrames) + getAdjustedFrames(l.pauseAfter),
    0
  );

  // Voice windows (adjusted frames, absolute) for the BGM duck.
  const voiceWindows = useMemo(() => {
    const rate = SETTINGS.video.playbackRate;
    let acc = openingFrames;
    return scriptData.map((line) => {
      const d = Math.ceil(line.durationInFrames / rate);
      const p = Math.ceil(line.pauseAfter / rate);
      const start = acc;
      acc += d + p;
      return { start, end: start + d };
    });
  }, []);

  // Current line
  let accumulatedFrames = 0;
  let currentLine: ScriptLine | null = null;
  let currentLineStartFrame = 0;
  let currentScene = 1;
  let isSpeaking = false;

  for (const line of scriptData) {
    const adjustedDuration = getAdjustedFrames(line.durationInFrames);
    const adjustedPause = getAdjustedFrames(line.pauseAfter);
    const lineEndFrame = accumulatedFrames + adjustedDuration + adjustedPause;

    if (frame >= accumulatedFrames && frame < lineEndFrame) {
      currentLine = line;
      currentLineStartFrame = accumulatedFrames;
      currentScene = line.scene;
      // Speaking while inside adjustedDuration
      isSpeaking = frame < accumulatedFrames + adjustedDuration;
      break;
    }
    accumulatedFrames = lineEndFrame;
    currentScene = line.scene;
  }

  const sceneInfo = scenes.find((s) => s.id === currentScene) || scenes[0];

  // Start frame per line
  const getLineStartFrame = (index: number): number => {
    let startFrame = 0;
    for (let i = 0; i < index; i++) {
      startFrame +=
        getAdjustedFrames(scriptData[i].durationInFrames) +
        getAdjustedFrames(scriptData[i].pauseAfter);
    }
    return startFrame;
  };

  // Rate-adjusted duration per line
  const getLineDuration = (line: ScriptLine): number =>
    getAdjustedFrames(line.durationInFrames);

  // Title/closing cards take over the composition during their windows.
  const cardBox = (card: { text: string; sub?: string }) => (
    <AbsoluteFill>
      <Img
        src={staticFile("background.png")}
        style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", objectFit: "cover" }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round((SETTINGS.video.height ?? 1080) * 0.03),
        }}
      >
        <div
          style={{
            fontSize: Math.round((SETTINGS.video.height ?? 1080) * 0.11),
            fontWeight: 900,
            color: SETTINGS.font.color,
            WebkitTextStroke: `${Math.round((SETTINGS.video.height ?? 1080) * 0.011)}px ${SETTINGS.font.outlineColor === "character" ? "#1F2937" : SETTINGS.font.outlineColor || "#1F2937"}`,
            paintOrder: "stroke fill",
            textAlign: "center",
          }}
        >
          {card.text}
        </div>
      </div>
    </AbsoluteFill>
  );
  if (frame < openingFrames && SETTINGS.titleCard) {
    return cardBox(SETTINGS.titleCard);
  }
  if (frame >= openingFrames + linesWall && SETTINGS.closingCard) {
    return cardBox(SETTINGS.closingCard);
  }

  // Per-scene background: settings.scenes maps scene id -> theme image
  // (copied to the workdir by map-project.mjs); falls back to the project
  // background.
  const sceneBg = currentScene != null ? SETTINGS.scenes?.[String(currentScene)] : undefined;

  return (
    <AbsoluteFill
      style={{
        background: COLORS.background,
        fontFamily: "'Noto Sans JP', 'Hiragino Sans', sans-serif",
      }}
    >
      {/* Background: per-scene theme image or the project background */}
      <Img
        src={staticFile(sceneBg ?? "background.png")}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
      {/* BGM (canonical settings.bgm, ducked under voice lines) */}
      {SETTINGS.bgm && SETTINGS.bgm.src && (
        <Audio
          src={staticFile(`bgm/${SETTINGS.bgm.src}`)}
          volume={(f) => {
            const base = SETTINGS.bgm.volume ?? 0.3;
            const speaking = voiceWindows.some((w) => f >= w.start && f < w.end);
            return speaking ? base * 0.25 : base;
          }}
          loop={SETTINGS.bgm.loop ?? false}
        />
      )}

      {/* Voice lines */}
      {scriptData.map((line, index) => {
        const startFrame = getLineStartFrame(index);
        return (
          <Sequence
            key={`audio-${line.id}`}
            from={startFrame}
            durationInFrames={getLineDuration(line)}
            premountFor={fps}
          >
            <Audio
              src={staticFile(`voices/${line.voiceFile}`)}
              playbackRate={SETTINGS.video.playbackRate}
            />
            {/* Sound effect */}
            {line.se && (
              <Audio
                src={staticFile(`se/${line.se.src}`)}
                volume={line.se.volume ?? 1}
              />
            )}
          </Sequence>
        );
      })}

      {/* Per-scene visuals */}
      <SceneVisuals
        scene={currentScene}
        lineId={currentLine?.id ?? null}
        frame={frame}
        fps={fps}
        visual={currentLine?.visual}
      />

      {/* Characters (data-driven from config/characters.yaml) */}
      {CHARACTERS.map((c) => (
        <Character
          key={c.id}
          characterId={c.id}
          isSpeaking={isSpeaking && currentLine?.character === c.id}
          emotion={currentLine?.character === c.id ? currentLine.emotion : "normal"}
        />
      ))}

      {/* Subtitle */}
      {currentLine && (
        <Sequence
          key={`subtitle-${currentLine.id}`}
          from={currentLineStartFrame}
          durationInFrames={getLineDuration(currentLine)}
        >
          <Subtitle
            text={currentLine.displayText ?? currentLine.text}
            character={currentLine.character}
            secondaryText={
              SETTINGS.subtitle?.secondaryLanguage
                ? currentLine.translations?.[SETTINGS.subtitle.secondaryLanguage]
                : undefined
            }
          />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
