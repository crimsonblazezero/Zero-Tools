import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';
import { KovaScapeColors } from './styles/colors';

export const SolarRevealSchema = z.object({
    title: z.string(),
    sunColor: zColor(),
});

export const SolarLogoReveal: React.FC<z.infer<typeof SolarRevealSchema>> = ({
    title,
    sunColor,
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // --- TIMING CONFIG ---
    const startRise = 20;
    const endRise = 80;
    const dayBreak = 70;

    // --- ANIMATED VALUES ---

    // 1. Sky Background (Night -> Dawn -> Day)
    // We use CSS gradients to simulate the sky
    const skyProgress = interpolate(frame, [0, dayBreak, endRise + 20], [0, 0.5, 1], {
        extrapolateRight: 'clamp',
    });

    // Dark Night
    const bgNight = `linear-gradient(to bottom, ${KovaScapeColors.MidnightBlue}, #000000)`;
    // Warm Dawn
    const bgDawn = `linear-gradient(to bottom, #2C3E50, ${KovaScapeColors.DawnOrange})`;
    // Bright Nordic Day
    const bgDay = `linear-gradient(to bottom, ${KovaScapeColors.OffWhite}, ${KovaScapeColors.White})`;

    // We simply crossfade these backgrounds by stacking AbsoluteFills
    const opacityDawn = interpolate(frame, [startRise, dayBreak], [0, 1], { extrapolateRight: 'clamp' });
    const opacityDay = interpolate(frame, [dayBreak, endRise + 30], [0, 1], { extrapolateRight: 'clamp' });

    // 2. The Sun (Golden Square) Movement
    // It rises from below the house to the top right window position.
    // We need to guess the pixel offset. Based on standard icon proportions:
    // Let's say Icon is 400x400. The window is usually top-right quadrant.
    const riseSpring = spring({
        frame: frame - startRise,
        fps,
        config: { damping: 100, mass: 2, stiffness: 50 }, // Slow, majestic rise
    });

    const sunY = interpolate(riseSpring, [0, 1], [300, 0]); // Moves up by 300px

    // 3. House Lighting (Silhouette -> Lit)
    // Initially, the house is a black silhouette (backlit).
    // As sun rises, it gains color.
    const silhouetteBrightness = interpolate(frame, [dayBreak, endRise], [0, 1], { // 0 = Black, 1 = Normal
        extrapolateRight: 'clamp',
    });

    // 4. Text Fade In
    const textOpacity = interpolate(frame, [endRise, endRise + 30], [0, 1]);
    const textTracking = interpolate(frame, [endRise, endRise + 60], [20, -2]);


    return (
        <AbsoluteFill>
            {/* --- BACKGROUND LAYERS --- */}
            <AbsoluteFill style={{ background: bgNight }} />
            <AbsoluteFill style={{ background: bgDawn, opacity: opacityDawn }} />
            <AbsoluteFill style={{ background: bgDay, opacity: opacityDay }} />

            {/* --- CONTENT CONTAINER --- */}
            <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>

                {/* LOGO AREA CONTAINER */}
                <div style={{ position: 'relative', width: 400, height: 400 }}>

                    {/* THE SUN (Golden Square) */}
                    {/* We position it absolutely. It simulates the window. */}
                    {/* Assuming the window is approx 70x70px at top right of the house shape */}
                    <div
                        style={{
                            position: 'absolute',
                            // These coordinates are estimates to align with the KovaScape icon "Window"
                            // You might need to tweak 'top' and 'right' based on the actual PNG alignment
                            top: 85,
                            right: 95,
                            width: 90,
                            height: 90,
                            backgroundColor: sunColor,
                            transform: `translateY(${sunY}px)`,
                            boxShadow: `0 0 ${interpolate(frame, [dayBreak, endRise], [10, 50])}px ${sunColor}`, // Glow pulse
                            zIndex: 1, // Behind the house silhouette initially? 
                            // Actually, if we want it to look like it's INSIDE the window, it should be behind the house layer if there was a transparent hole.
                            // Since PNG is solid, we place it ON TOP but mask it? 
                            // Simplest approach for "Rising Sun": Place it BEHIND the main Logo layer (Z=0), 
                            // but since main logo is solid, it would be hidden.
                            // CORRECTION: The user wants "Success" -> Sun becomes the window.
                            // So we place it IN FRONT (Z=2), but initially it's hidden or rising from bottom?
                            // Let's make it rise from the BOTTOM of the screen and land in the window slot.
                        }}
                    />

                    {/* THE HOUSE (Icon) */}
                    {/* Layer Z=2. We use filter to make it look like a silhouette against the rising sun */}
                    <Img
                        src={staticFile('assets/kovascape_icon.png')}
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'contain',
                            // The Magic Trick:
                            // At night (brightness 0) -> It's a black shape blocking the sky.
                            // At day (brightness 1) -> It reveals its true colors.
                            filter: `brightness(${silhouetteBrightness}) drop-shadow(0px 10px 20px rgba(0,0,0,0.3))`,
                            zIndex: 2,
                        }}
                    />
                </div>

                {/* --- TEXT AREA --- */}
                <div style={{ marginTop: 450, position: 'absolute' }}>
                    <h1
                        style={{
                            fontFamily: 'Inter, sans-serif',
                            fontSize: 80,
                            fontWeight: 700,
                            color: KovaScapeColors.DeepEmerald,
                            opacity: textOpacity,
                            letterSpacing: `${textTracking}px`,
                            margin: 0,
                        }}
                    >
                        {title}
                    </h1>
                </div>

            </AbsoluteFill>
        </AbsoluteFill>
    );
};
