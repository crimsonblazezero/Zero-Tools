import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';
import { KovaScapeColors } from './styles/colors';

export const LogoRevealSchema = z.object({
    title: z.string(),
    primaryColor: zColor(),
    secondaryColor: zColor(),
});

export const LogoReveal: React.FC<z.infer<typeof LogoRevealSchema>> = ({
    title,
    primaryColor,
    secondaryColor,
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 1. Background Fade In (Subtle)
    const bgOpacity = interpolate(frame, [0, 20], [0, 1], {
        extrapolateRight: 'clamp',
    });

    // 2. Icon Assembly Animation
    // The icon parts sliding in. We'll simulate this by scaling/moving the icon 
    // since we have a single PNG. Ideally we'd use SVG paths, but for now 
    // we'll use a spring Pop-In effect for the "Building" feel.
    const iconScale = spring({
        frame: frame - 15, // Delay
        fps,
        config: {
            damping: 10,
            stiffness: 100,
        },
    });

    // 3. Text Slide Up & Fade
    const textOpacity = interpolate(frame, [40, 60], [0, 1], {
        extrapolateRight: 'clamp',
    });
    const textTranslateY = interpolate(frame, [40, 60], [20, 0], {
        extrapolateRight: 'clamp',
    });

    // 4. "Snap" effect visual (Gold accent flash)
    const flashOpacity = interpolate(frame, [45, 50, 55], [0, 0.6, 0], {
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill
            style={{
                backgroundColor: KovaScapeColors.OffWhite,
                justifyContent: 'center',
                alignItems: 'center',
            }}
        >
            {/* Background Texture/Color */}
            <AbsoluteFill style={{ opacity: bgOpacity, backgroundColor: KovaScapeColors.OffWhite }} />

            {/* Main Container */}
            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 40,
                }}
            >
                {/* Icon Area */}
                <div style={{ transform: `scale(${iconScale})`, position: 'relative' }}>
                    <Img
                        src={staticFile('assets/kovascape_icon.png')}
                        style={{
                            width: 300,
                            height: 300,
                            objectFit: 'contain',
                            // Drop shadow for depth (Nordic architectural feel)
                            filter: 'drop-shadow(0px 10px 20px rgba(0,0,0,0.15))',
                        }}
                    />
                    {/* Gold Snap Flash Overlay */}
                    <div
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: secondaryColor,
                            opacity: flashOpacity,
                            borderRadius: '50%', // Assuming icon is roughly circular/contained 
                            filter: 'blur(20px)',
                            mixBlendMode: 'overlay',
                        }}
                    />
                </div>

                {/* Title Text */}
                <h1
                    style={{
                        fontFamily: 'Inter, sans-serif',
                        fontSize: 80,
                        fontWeight: 700,
                        color: KovaScapeColors.DeepEmerald,
                        opacity: textOpacity,
                        transform: `translateY(${textTranslateY}px)`,
                        margin: 0,
                        letterSpacing: '-2px',
                    }}
                >
                    {title}
                </h1>
            </div>
        </AbsoluteFill>
    );
};
