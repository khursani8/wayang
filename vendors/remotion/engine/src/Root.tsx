import { Composition } from "remotion";
import { Main } from "./Main";
import { scriptData } from "./data/script";
import { VIDEO_CONFIG } from "./config";
import { SETTINGS } from "./settings.generated";

// 動画の総フレーム数を計算
// Main と同じ再生速度調整を 1 行ごとに適用する。未調整のまま合計すると、
// 速度 > 1 のとき末尾に空き映像が残る（Main は調整済みフレームで進む）。
// 最初のセリフはフレーム 0 から始まるため、オープニング余白は不要。
const playbackRate = SETTINGS.video.playbackRate ?? 1;
const adjusted = (frames: number) => Math.ceil(frames / playbackRate);
const calculateTotalFrames = () => {
  let total = 0;
  for (const line of scriptData) {
    total += adjusted(line.durationInFrames) + adjusted(line.pauseAfter);
  }
  total += 60; // エンディング用の余白
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
