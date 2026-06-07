import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';
import { KovaScapeColors } from './styles/colors';

export const BannerSolarSchema = z.object({
    sunColor: zColor(),
});

export const BannerSolarReveal: React.FC<z.infer<typeof BannerSolarSchema>> = ({
    sunColor,
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // --- CONFIG ---
    // Cut point for the image (Where the Icon ends and Text begins)
    // Assuming the image is roughly 30% Icon, 70% Text
    const SPLIT_PERCENT = 26;

    // Banner Image Dimensions reference (to help positioning sun)
    // Let's assume we maintain aspect ratio. 
    // We will position the sun relative to the center of the screen.

    // --- ANIMATION TIMING ---
    const startRise = 10;
    const sunLand = 50;
    const textRevealStart = 60;

    // 1. Sun Movement
    // Rises from bottom and lands in the "Window" spot
    const riseProgress = spring({
        frame: frame - startRise,
        fps,
        config: { damping: 15, stiffness: 60 },
    });

    // Translate Y: Starts low (offset 200px), settles at 0 (correct window pos)
    // We need to fine tune the "Window" position manually since it's a static PNG.
    const sunY = interpolate(riseProgress, [0, 1], [300, 0]);

    // 2. Icon Lighting (Silhouette -> Lit)
    const iconBrightness = interpolate(frame, [sunLand - 10, sunLand + 10], [0.1, 1], {
        extrapolateRight: 'clamp',
    });

    // 3. Sun Glow (Bloom)
    const sunGlow = interpolate(frame, [sunLand, sunLand + 15], [0, 60], {
        extrapolateRight: 'clamp',
    });

    // 4. Text Reveal (Wipe)
    // Text is masked initially. We reveal it by changing clip-path inset.
    const textWipe = interpolate(frame, [textRevealStart, textRevealStart + 40], [100, 0], {
        extrapolateRight: 'clamp',
    });

    // --- BACKGROUND GRADIENT ---
    // Dark Green to slightly lighter Green/Black
    const bg = `linear-gradient(to bottom, ${KovaScapeColors.DeepEmerald}, #021a15)`;

    return (
        <AbsoluteFill style={{ background: bg, justifyContent: 'center', alignItems: 'center' }}>

            {/* CONTAINER FOR BANNER */}
            {/* We center everything */}
            <div style={{ position: 'relative', width: 1200, height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>

                {/* --- THE SUN DIV --- */}
                {/* Manually positioned to match the PNG's window slot */}
                <div
                    style={{
                        position: 'absolute',
                        // These are MAGIC NUMBERS estimated for the wide banner.
                        // You WILL need to tweak 'left' and 'top' to align perfectly with the K-Window.
                        left: 215, // Approx position of window in the wide banner
                        top: 110,
                        width: 70,
                        height: 70,
                        backgroundColor: sunColor,
                        boxShadow: `0 0 ${sunGlow}px ${sunColor}`,
                        transform: `translateY(${sunY}px)`,
                        zIndex: 1,
                        borderRadius: 2,
                    }}
                />

                {/* --- LAYER 1: THE ICON (Masked Left Side) --- */}
                {/* We show only the left part of the image */}
                <Img
                    src={staticFile('assets/kovascape_banner_wide.png')}
                    style={{
                        position: 'absolute',
                        width: '100%',
                        top: 0,
                        // CLIP: Keep left side (0% to SPLIT_PERCENT%)
                        clipPath: `inset(0 ${100 - SPLIT_PERCENT}% 0 0)`,
                        filter: `brightness(${iconBrightness}) drop-shadow(0 10px 20px rgba(0,0,0,0.5))`,
                        zIndex: 2, // In front of sun
                    }}
                />

                {/* --- LAYER 2: THE TEXT (Masked Right Side) --- */}
                {/* We show only the right part of the image */}
                <Img
                    src={staticFile('assets/kovascape_banner_wide.png')}
                    style={{
                        position: 'absolute',
                        width: '100%',
                        top: 0,
                        // CLIP: Keep right side.
                        // ANIMATION: We animate the RIGHT inset to reveal? No, we animate the LEFT inset of this layer
                        // Initially, we want it HIDDEN. 
                        // Wait... the text is on the right. 
                        // To hide it, we clip the RIGHT side fully? No.
                        // The Text is in the region [SPLIT_PERCENT, 100].
                        // To hide it, we can set clipPath to `inset(0 100% 0 SPLIT_PERCENT)` -> It shows nothing.
                        // To reveal it, we transition to `inset(0 0 0 SPLIT_PERCENT)`.
                        // Actually, let's just clip the LEFT side fixed at SPLIT_PERCENT, and animate the RIGHT side?
                        // No, standard wipe is usually Left->Right.
                        // So we want to reveal FROM SPLIT_PERCENT TO 100.
                        // clipPath: inset(0 [animating value]% 0 SPLIT_PERCENT)
                        // Start: inset(0 100% 0 SPLIT_PERCENT) -> Visible width is 0.
                        // End:   inset(0 0% 0 SPLIT_PERCENT)   -> Visible width is (100-SPLIT_PERCENT).
                        clipPath: `inset(0 ${textWipe}% 0 ${SPLIT_PERCENT}%)`,

                        // Text is always fully lit, or maybe fades in?
                        // Let's make it start slightly dim and go to full brightness
                        filter: `brightness(${interpolate(frame, [textRevealStart, textRevealStart + 20], [0.5, 1])})`,
                        zIndex: 2,
                    }}
                />

            </div>
        </AbsoluteFill>
    );
};
