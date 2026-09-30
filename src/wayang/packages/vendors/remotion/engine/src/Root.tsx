import { Composition } from "remotion";
import { Main } from "./Main";
import { scriptData } from "./data/script";
import { VIDEO_CONFIG } from "./config";
import { SETTINGS } from "./settings.generated";

// Total composition frames.
// Apply the same per-line playback-rate adjustment Main.tsx uses. Summing
// raw frames leaves an empty tail whenever rate > 1 (Main advances in
// adjusted frames). The first line starts at frame 0, so no opening buffer.
const playbackRate = SETTINGS.video.playbackRate ?? 1;
const fps = SETTINGS.video.fps ?? 30;
const adjusted = (frames: number) => Math.ceil(frames / playbackRate);
// Opening/closing cards: title 3s, closing 2.5s, else the 60-frame buffer.
// Must match Main.tsx exactly (both read the generated settings).
const openingFrames = SETTINGS.titleCard ? Math.round(3 * fps) : 0;
const closingFrames = SETTINGS.closingCard ? Math.round(2.5 * fps) : 60;
const calculateTotalFrames = () => {
  let total = openingFrames;
  for (const line of scriptData) {
    total += adjusted(line.durationInFrames) + adjusted(line.pauseAfter);
  }
  total += closingFrames;
  return total;
};

export const RemotionRoot: React.FC = () => {
  const totalFrames = calculateTotalFrames();

  return (
    <>
      <Composition
        id="Main"
        component={Main}
        durationInFrames={totalFrames}
        fps={SETTINGS.video.fps ?? VIDEO_CONFIG.fps}
        width={SETTINGS.video.width ?? VIDEO_CONFIG.width}
        height={SETTINGS.video.height ?? VIDEO_CONFIG.height}
      />
    </>
  );
};
