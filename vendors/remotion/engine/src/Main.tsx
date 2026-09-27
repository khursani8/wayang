import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio, Sequence, staticFile, Loop, Img } from "remotion";
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

  return (
    <AbsoluteFill
      style={{
        background: COLORS.background,
        fontFamily: "'Noto Sans JP', 'Hiragino Sans', sans-serif",
      }}
    >
      {/* Background image (assets/background generators); a project can
          override it with assets/background.png */}
      <Img
        src={staticFile("background.png")}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
      {/* BGM (canonical settings.bgm) */}
      {SETTINGS.bgm && SETTINGS.bgm.src && (
        <Audio
          src={staticFile(`bgm/${SETTINGS.bgm.src}`)}
          volume={SETTINGS.bgm.volume ?? 0.3}
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
              SETTINGS.subtitles?.secondaryLanguage
                ? currentLine.translations?.[SETTINGS.subtitles.secondaryLanguage]
                : undefined
            }
          />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
