import React from 'react';
import {
    AbsoluteFill,
    Img,
    interpolate,
    spring,
    staticFile,
    useCurrentFrame,
    useVideoConfig,
} from 'remotion';

/**
 * PNG遮罩动画版本 / PNG Mask Animation Version
 * 
 * 使用原始PNG图片，通过clip-path分步揭示：
 * 1. K-House图标先出现（左侧区域）
 * 2. 金色方块"太阳"升起并发光
 * 3. ovaScape文字从左到右逐步显现
 */
export const KovaScapePNGMask: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // --- 布局参数 / Layout Parameters ---
    // 基于原图分析：K-House图标大约占整个banner宽度的25%
    const ICON_WIDTH_PERCENT = 25;

    // 金色方块相对于图标区域的位置（需要根据实际PNG微调）
    // 这些值需要根据实际banner中窗户的位置调整
    const SUN_LEFT_PERCENT = 18; // 金色方块左边距占比
    const SUN_TOP_PERCENT = 28;  // 金色方块上边距占比

    // --- 动画时间线 / Animation Timeline ---
    const iconAppear = 10;   // 图标开始出现
    const sunRise = 25;      // 太阳开始升起
    const sunLand = 50;      // 太阳到达窗户位置
    const textStart = 55;    // 文字开始显现
    const textEnd = 100;     // 文字完全显现

    // --- 动画值 / Animation Values ---

    // 1. 图标淡入 + 缩放
    const iconOpacity = interpolate(frame, [iconAppear, iconAppear + 15], [0, 1], {
        extrapolateRight: 'clamp',
    });
    const iconScale = spring({
        frame: frame - iconAppear,
        fps,
        config: { damping: 12, stiffness: 100 },
    });

    // 2. 太阳升起
    const sunProgress = spring({
        frame: frame - sunRise,
        fps,
        config: { damping: 15, stiffness: 50 },
    });
    const sunY = interpolate(sunProgress, [0, 1], [100, 0]); // 从下往上
    const sunGlow = interpolate(frame, [sunLand, sunLand + 20], [0, 30], {
        extrapolateRight: 'clamp',
    });
    const sunOpacity = interpolate(frame, [sunRise, sunRise + 10], [0, 1], {
        extrapolateRight: 'clamp',
    });

    // 3. 文字揭示（从左到右擦除）
    const textRevealPercent = interpolate(frame, [textStart, textEnd], [100, 0], {
        extrapolateRight: 'clamp',
    });

    // 4. 图标区域在太阳到达后的亮度变化（模拟被点亮）
    const iconBrightness = interpolate(frame, [sunLand - 5, sunLand + 10], [0.5, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill style={{ backgroundColor: '#064338', justifyContent: 'center', alignItems: 'center' }}>

            {/* 容器：让所有层相对定位 */}
            <div style={{ position: 'relative', width: '80%', height: 'auto' }}>

                {/* 层1：K-House 图标区域（左侧裁剪） */}
                <Img
                    src={staticFile('assets/kovascape_banner_ref.png')}
                    style={{
                        width: '100%',
                        clipPath: `inset(0 ${100 - ICON_WIDTH_PERCENT}% 0 0)`, // 只显示左侧25%
                        opacity: iconOpacity,
                        transform: `scale(${iconScale})`,
                        transformOrigin: 'left center',
                        filter: `brightness(${iconBrightness})`,
                    }}
                />

                {/* 层2：金色太阳方块（独立div，动画升起） */}
                <div
                    style={{
                        position: 'absolute',
                        // 位置需要根据实际PNG中窗户的位置微调
                        left: `${SUN_LEFT_PERCENT}%`,
                        top: `${SUN_TOP_PERCENT}%`,
                        width: '5%',  // 方块宽度占容器的比例
                        aspectRatio: '1',
                        backgroundColor: '#F3C546',
                        opacity: sunOpacity,
                        transform: `translateY(${sunY}px)`,
                        boxShadow: `0 0 ${sunGlow}px #F3C546`,
                        zIndex: 10,
                    }}
                />

                {/* 层3：ovaScape 文字区域（右侧裁剪，逐步揭示） */}
                <Img
                    src={staticFile('assets/kovascape_banner_ref.png')}
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        // 只显示右侧75%，并且从右向左逐步揭示
                        // inset(top right bottom left)
                        // 初始：inset(0 100% 0 25%) -> 完全隐藏
                        // 结束：inset(0 0% 0 25%)   -> 完全显示文字部分
                        clipPath: `inset(0 ${textRevealPercent}% 0 ${ICON_WIDTH_PERCENT}%)`,
                    }}
                />

            </div>

        </AbsoluteFill>
    );
};
