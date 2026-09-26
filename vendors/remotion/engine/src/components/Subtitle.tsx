import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { loadDefaultJapaneseParser } from "budoux";
import { useMemo } from "react";
import { CharacterId } from "../config";
import { characterColors } from "../data/script";
import { SETTINGS } from "../settings.generated";

// BudouXパーサーを初期化（日本語の自然な改行位置を計算）
const parser = loadDefaultJapaneseParser();

interface SubtitleProps {
  text: string;
  character: CharacterId;
}

// BudouXで分割したテキストをレンダリングするコンポーネント
const BudouXText = ({ text }: { text: string }) => {
  // まず\nで行分割し、各行をBudouXで処理
  const lines = useMemo(() => {
    return text.split("\n").map((line) => parser.parse(line));
  }, [text]);

  return (
    <>
      {lines.map((segments, lineIndex) => (
        <span key={lineIndex}>
          {segments.map((segment, index) => (
            <span
              key={index}
              style={{
                display: "inline-block",
                whiteSpace: "nowrap",
              }}
            >
              {segment}
            </span>
          ))}
          {lineIndex < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
};

export const Subtitle: React.FC<SubtitleProps> = ({ text, character }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 設定から値を取得
  const { font, subtitle, colors } = SETTINGS;

  // フェードインアニメーション
  const opacity = interpolate(frame, [0, fps * 0.15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // キャラクター色を取得
  const characterColor = characterColors[character] ?? colors.text;

  // フォント色の決定
  const getColor = (colorValue: string) => {
    if (colorValue === "character") {
      return characterColor;
    }
    return colorValue;
  };

  const textColor = getColor(font.color);
  const outlineColor = getColor(font.outlineColor);

  const baseStyle: React.CSSProperties = {
    fontSize: font.size,
    fontWeight: font.weight as React.CSSProperties["fontWeight"],
    lineHeight: 1.5,
    fontFamily: `'${font.family}', 'Hiragino Maru Gothic ProN', sans-serif`,
  };

  return (
    <div
      style={{
        position: "absolute",
        bottom: subtitle.bottomOffset,
        left: "50%",
        transform: "translateX(-50%)",
        opacity,
        width: `${subtitle.maxWidthPercent}%`,
        maxWidth: subtitle.maxWidthPixels,
        textAlign: "center",
      }}
    >
      {/* 袋文字: アウトラインと本文を重ねて表示 */}
      <div style={{ position: "relative", display: "inline-block" }}>
        {/* アウトライン（後ろ） */}
        <span
          style={{
            ...baseStyle,
            position: "absolute",
            left: 0,
            top: 0,
            color: outlineColor,
            WebkitTextStroke: `${subtitle.outlineWidth}px ${outlineColor}`,
            paintOrder: "stroke fill",
          }}
        >
          <BudouXText text={text} />
        </span>
        {/* 本文（前） */}
        <span
          style={{
            ...baseStyle,
            position: "relative",
            color: textColor,
          }}
        >
          <BudouXText text={text} />
        </span>
      </div>
    </div>
  );
};
