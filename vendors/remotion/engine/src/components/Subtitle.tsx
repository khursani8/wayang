import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { loadDefaultJapaneseParser } from "budoux";
import { useMemo } from "react";
import { CharacterId } from "../config";
import { characterColors } from "../data/script";
import { SETTINGS } from "../settings.generated";

// BudouX parser (natural line breaks for Japanese/CJK text)
const parser = loadDefaultJapaneseParser();

interface SubtitleProps {
  text: string;
  character: CharacterId;
  secondaryText?: string;
}

// CJK lines segment via BudouX; other scripts wrap at word boundaries.
// Subtitle standard: ~42 chars per line, max 2 lines.
const CJK = /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]/;

const SegmentedText = ({ text }: { text: string }) => {
  // Split by newline first; only CJK lines go through BudouX
  const lines = useMemo(() => {
    return text.split("\n").map((line) => (CJK.test(line) ? parser.parse(line) : [line]));
  }, [text]);

  return (
    <>
      {lines.map((segments, lineIndex) => (
        <span key={lineIndex}>
          {segments.map((segment, index) =>
            CJK.test(segment) ? (
              <span
                key={index}
                style={{
                  display: "inline-block",
                  whiteSpace: "nowrap",
                }}
              >
                {segment}
              </span>
            ) : (
              <span key={index}>{segment}</span>
            ),
          )}
          {lineIndex < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
};

export const Subtitle: React.FC<SubtitleProps> = ({ text, character, secondaryText }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Settings
  const { font, subtitle, colors } = SETTINGS;

  // Fade in
  const opacity = interpolate(frame, [0, fps * 0.15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Character color
  const characterColor = characterColors[character] ?? colors.text;

  // Text and outline colors
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
    overflowWrap: "anywhere",
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
      {/* Outlined text: stroke layer behind the fill layer */}
      <div
        style={{
          position: "relative",
          display: "inline-block",
          textWrap: "balance",
          maxWidth: "100%",
        }}
      >
        {/* Outline (behind) */}
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
          {secondaryText && (
            <div
              style={{
                fontSize: Math.round(font.size * 0.55),
                fontWeight: 600,
                opacity: 0.92,
                marginBottom: Math.round(font.size * 0.15),
              }}
            >
              <SegmentedText text={secondaryText} />
            </div>
          )}
          <SegmentedText text={text} />
        </span>
        {/* Fill (front) */}
        <span
          style={{
            ...baseStyle,
            position: "relative",
            color: textColor,
          }}
        >
          {secondaryText && (
            <div
              style={{
                fontSize: Math.round(font.size * 0.55),
                fontWeight: 600,
                opacity: 0.92,
                marginBottom: Math.round(font.size * 0.15),
              }}
            >
              <SegmentedText text={secondaryText} />
            </div>
          )}
          <SegmentedText text={text} />
        </span>
      </div>
    </div>
  );
};
