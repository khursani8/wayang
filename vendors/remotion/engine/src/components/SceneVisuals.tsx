import { Img, staticFile, interpolate, spring, useVideoConfig } from "remotion";
import { COLORS } from "../config";
import { VisualContent, AnimationType } from "../data/script";

interface SceneVisualsProps {
  scene: number;
  lineId: number | null;
  frame: number;
  fps: number;
  visual?: VisualContent;
}

// アニメーションスタイルを計算
const useAnimationStyle = (
  frame: number,
  fps: number,
  animation: AnimationType = "fadeIn"
): React.CSSProperties => {
  const progress = interpolate(frame, [0, fps * 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });

  const springProgress = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  switch (animation) {
    case "none":
      return { opacity: 1 };

    case "fadeIn":
      return { opacity: progress };

    case "slideUp":
      return {
        opacity: progress,
        transform: `translateY(${interpolate(progress, [0, 1], [50, 0])}px)`,
      };

    case "slideLeft":
      return {
        opacity: progress,
        transform: `translateX(${interpolate(progress, [0, 1], [100, 0])}px)`,
      };

    case "zoomIn":
      return {
        opacity: progress,
        transform: `scale(${interpolate(progress, [0, 1], [0.8, 1])})`,
      };

    case "bounce":
      return {
        opacity: Math.min(1, frame / (fps * 0.1)),
        transform: `scale(${springProgress})`,
      };

    default:
      return { opacity: progress };
  }
};

export const SceneVisuals: React.FC<SceneVisualsProps> = ({
  scene,
  lineId,
  frame,
  fps,
  visual,
}) => {
  const animationStyle = useAnimationStyle(frame, fps, visual?.animation);

  // コンテンツコンテナ（黒板内に収まるよう調整）
  const contentContainer: React.CSSProperties = {
    position: "absolute",
    top: 60,
    left: 80,
    right: 80,
    bottom: 180,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    ...animationStyle,
  };

  // ビジュアルがない場合はデフォルト表示
  if (!visual || visual.type === "none") {
    return null;
  }

  // 画像表示
  if (visual.type === "image" && visual.src) {
    return (
      <div style={contentContainer}>
        <Img
          src={staticFile(`content/${visual.src}`)}
          style={{
            maxWidth: "100%",
            maxHeight: "100%",
            objectFit: "contain",
            borderRadius: 8,
          }}
        />
      </div>
    );
  }

  // テキスト表示
  if (visual.type === "text" && visual.text) {
    return (
      <div style={contentContainer}>
        <div
          style={{
            fontSize: visual.fontSize || 64,
            fontWeight: "bold",
            color: visual.color || COLORS.text,
            textAlign: "center",
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
          }}
        >
          {visual.text}
        </div>
      </div>
    );
  }

  return null;
};
