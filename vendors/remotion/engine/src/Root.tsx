import { Composition } from "remotion";
import { Main } from "./Main";
import { scriptData } from "./data/script";
import { VIDEO_CONFIG } from "./config";
import { SETTINGS } from "./settings.generated";

// 動画の総フレーム数を計算
const calculateTotalFrames = () => {
  let total = 60; // オープニング用の余白
  for (const line of scriptData) {
    total += line.durationInFrames + line.pauseAfter;
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
