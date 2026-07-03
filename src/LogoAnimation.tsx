import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";

export const LogoAnimation: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 1. Left Pillar Animation (Fades and slides down without scale/deformation)
  // 左立柱平移淡入（无形变与缩放）
  const pillarProgress = spring({
    frame: frame - 0,
    fps,
    config: { stiffness: 100, damping: 15 },
  });
  const pillarY = interpolate(pillarProgress, [0, 1], [-15, 0]);
  const pillarOpacity = interpolate(pillarProgress, [0, 1], [0, 1]);

  // 2. Roof & Chimney & Window Animations (Translation & Opacity only)
  // 屋顶、烟囱与窗户平移淡入（无形变与缩放）
  const roofProgress = spring({
    frame: frame - 15,
    fps,
    config: { stiffness: 80, damping: 15 },
  });
  const roofY = interpolate(roofProgress, [0, 1], [-15, 0]);
  const roofOpacity = interpolate(roofProgress, [0, 1], [0, 1]);

  const chimneyProgress = spring({
    frame: frame - 30,
    fps,
    config: { stiffness: 100, damping: 15 },
  });
  const chimneyY = interpolate(chimneyProgress, [0, 1], [-15, 0]);
  const chimneyOpacity = interpolate(chimneyProgress, [0, 1], [0, 1]);

  const windowProgress = spring({
    frame: frame - 45,
    fps,
    config: { stiffness: 120, damping: 12 },
  });
  const windowY = interpolate(windowProgress, [0, 1], [-15, 0]);
  const windowOpacity = interpolate(windowProgress, [0, 1], [0, 1]);

  // 3. Sun (Gold Square) Sunrise Arc (Original size, no scaling during rise)
  // 太阳东升弧线轨迹（原尺寸，升起时不缩放）
  const sunProgress = spring({
    frame: frame - 35,
    fps,
    config: { stiffness: 50, damping: 14 },
  });
  const sunX = interpolate(sunProgress, [0, 1], [90, 157.5]);
  const sunY = interpolate(sunProgress, [0, 0.5, 1], [150, 45, 77.5]);
  const sunOpacity = interpolate(sunProgress, [0, 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 4. Sun Flash Effect (Final shine at frames 115-130) / 太阳亮一下
  const sunFlash = interpolate(frame, [115, 122, 130], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const currentSunScale = 1 + 0.15 * sunFlash;

  // 5. Staggered reveal for letters "ovaScape" / 字母 "ovaScape" 逐字缓入
  const textLetters = ["o", "v", "a", "S", "c", "a", "p", "e"];
  const letterAnimations = textLetters.map((_, i) => {
    const startFrame = 65 + i * 4;
    const letterProgress = spring({
      frame: frame - startFrame,
      fps,
      config: { stiffness: 120, damping: 14 },
    });
    
    const yOffset = interpolate(letterProgress, [0, 1], [15, 0]);
    const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    
    return { yOffset, opacity };
  });

  // 6. Global Outro Fade (frames 155-175) / 全局出场渐隐
  const globalOpacity = interpolate(frame, [155, 175], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#064338", // KovaScape Deep Emerald Green / 品牌墨绿
        width: "100%",
        height: "100%",
        display: "flex",
        position: "relative",
        opacity: globalOpacity,
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700&display=swap');
      `}</style>

      {/* SVG Container for Icon "K" / 图标 SVG 容器 */}
      <svg
        width="240"
        height="200"
        style={{
          position: "absolute",
          left: "20px",
          top: "0px",
        }}
      >
        {/* Left Pillar (Left side of "K") / 左侧立柱 */}
        <g
          style={{
            transform: `translateY(${pillarY}px)`,
            opacity: pillarOpacity,
          }}
        >
          <polygon points="90,60 115,60 115,120 90,145" fill="#ffffff" />
        </g>

        {/* Chimney / 烟囱 */}
        <g
          style={{
            transform: `translateY(${chimneyY}px)`,
            opacity: chimneyOpacity,
          }}
        >
          <line
            x1="105"
            y1="130"
            x2="105"
            y2="110"
            stroke="#ffffff"
            strokeWidth="8"
            strokeLinecap="round"
          />
        </g>

        {/* Roof (Middle-Right of "K") / 屋顶 */}
        <path
          d="M 90 145 L 125 110 L 160 145"
          stroke="#ffffff"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transform: `translateY(${roofY}px)`,
            opacity: roofOpacity,
          }}
        />

        {/* 4-Pane Window / 窗户四格 */}
        <g
          style={{
            transform: `translateY(${windowY}px)`,
            opacity: windowOpacity,
          }}
        >
          <rect x="114" y="123" width="5" height="5" fill="#ffffff" />
          <rect x="122" y="123" width="5" height="5" fill="#ffffff" />
          <rect x="114" y="131" width="5" height="5" fill="#ffffff" />
          <rect x="122" y="131" width="5" height="5" fill="#ffffff" />
        </g>

        {/* Sun (Gold Square) with Sunrise Arc & Settle Flash / 太阳金砖（平移东升，定格后闪烁） */}
        <g
          style={{
            transform: `translate(${sunX - 157.5}px, ${sunY - 77.5}px) scale(${currentSunScale})`,
            transformOrigin: "157.5px 77.5px",
            opacity: sunOpacity,
            filter: `brightness(${1 + 0.4 * sunFlash})`,
          }}
        >
          <polygon points="145,65 170,65 170,90 145,90" fill="#F3C546" />
        </g>
      </svg>

      {/* Wordmark Container / 品牌字标容器 */}
      <div
        style={{
          position: "absolute",
          left: "195px",
          top: "0px",
          height: "200px",
          display: "flex",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: "66px",
            fontWeight: 700,
            color: "#ffffff",
            display: "flex",
            flexDirection: "row",
            letterSpacing: "-1.5px",
          }}
        >
          {textLetters.map((char, index) => (
            <span
              key={index}
              style={{
                display: "inline-block",
                transform: `translateY(${letterAnimations[index].yOffset}px)`,
                opacity: letterAnimations[index].opacity,
              }}
            >
              {char}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
