import React from 'react';
import {
    AbsoluteFill,
    interpolate,
    spring,
    useCurrentFrame,
    useVideoConfig,
} from 'remotion';

export const KovaScapeSVGLogo: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 通用弹性配置 / Generic spring config
    const spr = (delay: number) =>
        spring({
            frame: frame - delay,
            fps,
            config: { damping: 12, stiffness: 100 },
        });

    // --- 动画进度控制 / Animation Progress ---
    const iconOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
    const iconScale = spr(0);
    const sunPop = spr(25); // 黄色方块延迟弹出 / Yellow square pops with delay
    const textReveal = interpolate(frame, [35, 60], [0, 1], { extrapolateRight: 'clamp' });

    // 窗户发光效果 / Window glow effect
    const windowGlow = interpolate(frame, [30, 50], [0, 20], { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill style={{ backgroundColor: '#064338', justifyContent: 'center', alignItems: 'center' }}>
            {/* 根据 SVG ViewBox (0 0 2000 1101) 进行布局 */}
            <svg
                viewBox="0 0 2000 1101"
                style={{
                    width: '80%',
                    height: 'auto',
                    overflow: 'visible'
                }}
            >
                {/* 发光滤镜定义 / Glow filter definition */}
                <defs>
                    <filter id="sunGlow" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation={windowGlow} result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* 1. K 字主体/房子 (白色部分) / K-House Icon (White) */}
                <g style={{ opacity: iconOpacity, transform: `scale(${iconScale})`, transformOrigin: '300px 550px' }}>
                    {/* 屋顶和主体 / Roof and main structure */}
                    <path
                        fill="white"
                        d="M 273.5,399.5 C 273.667,427.169 273.5,454.835 273,482.5 C 246.053,515.422 218.887,548.089 191.5,580.5 L 191.5,399.5 Z"
                    />
                    <path
                        fill="white"
                        d="M 274.5,481.5 C 301.833,481.5 329.167,481.5 356.5,481.5 L 436,581.5 L 436.5,646.5 L 354.5,646.5 L 353.5,581.5 Z"
                    />
                    {/* 房屋底部窗户框 / Bottom window frame */}
                    <path
                        fill="white"
                        d="M 191.5,581.5 L 273.5,481.5 L 273.5,646.5 L 191.5,646.5 Z"
                    />
                    {/* 小窗户 / Small windows */}
                    <rect x="205" y="590" width="25" height="25" fill="#064338" />
                    <rect x="240" y="590" width="25" height="25" fill="#064338" />
                    <rect x="205" y="620" width="25" height="25" fill="#064338" />
                    <rect x="240" y="620" width="25" height="25" fill="#064338" />
                </g>

                {/* 2. 黄色阳光方块 (关键品牌记忆点) / Golden Sun Square (Key Brand Element) */}
                <rect
                    x="357.5" y="399.5"
                    width="81" height="81"
                    fill="#F3C546"
                    filter="url(#sunGlow)"
                    style={{
                        transform: `scale(${sunPop})`,
                        transformOrigin: '397px 440px',
                    }}
                />

                {/* 3. 文字部分 ovaScape (白色) / Text "ovaScape" (White) */}
                <g style={{ opacity: textReveal }}>
                    {/* "o" */}
                    <ellipse cx="560" cy="590" rx="55" ry="55" fill="white" />
                    <ellipse cx="560" cy="590" rx="30" ry="30" fill="#064338" />

                    {/* "v" */}
                    <polygon fill="white" points="650,520 700,650 750,520 720,520 700,600 680,520" />

                    {/* "a" */}
                    <path fill="white" d="M 790,650 L 790,580 C 790,550 820,520 860,520 C 900,520 930,550 930,580 L 930,650 L 890,650 L 890,620 L 830,620 L 830,650 Z M 830,590 L 890,590 L 890,580 C 890,565 875,555 860,555 C 845,555 830,565 830,580 Z" />

                    {/* "S" */}
                    <path fill="white" d="M 1020,530 C 1020,510 1050,500 1080,500 C 1110,500 1140,510 1140,530 L 1140,550 C 1140,570 1110,580 1080,580 C 1050,580 1020,590 1020,610 L 1020,630 C 1020,650 1050,660 1080,660 C 1110,660 1140,650 1140,630 L 1100,630 C 1100,640 1090,645 1080,645 C 1070,645 1060,640 1060,630 L 1060,615 C 1060,600 1080,595 1100,595 C 1120,595 1140,585 1140,570 L 1140,530 C 1140,510 1110,500 1080,500 C 1050,500 1020,510 1020,530 Z" />

                    {/* "c" */}
                    <path fill="white" d="M 1200,590 C 1200,550 1230,520 1270,520 C 1300,520 1320,535 1320,555 L 1280,555 C 1280,545 1275,540 1270,540 C 1255,540 1240,555 1240,590 C 1240,625 1255,640 1270,640 C 1275,640 1280,635 1280,625 L 1320,625 C 1320,645 1300,660 1270,660 C 1230,660 1200,630 1200,590 Z" />

                    {/* "a" (second) */}
                    <path fill="white" d="M 1360,650 L 1360,580 C 1360,550 1390,520 1430,520 C 1470,520 1500,550 1500,580 L 1500,650 L 1460,650 L 1460,620 L 1400,620 L 1400,650 Z M 1400,590 L 1460,590 L 1460,580 C 1460,565 1445,555 1430,555 C 1415,555 1400,565 1400,580 Z" />

                    {/* "p" */}
                    <path fill="white" d="M 1540,520 L 1540,700 L 1580,700 L 1580,650 C 1595,655 1610,660 1630,660 C 1670,660 1700,630 1700,590 C 1700,550 1670,520 1630,520 C 1610,520 1595,525 1580,530 L 1580,520 Z M 1580,560 C 1595,555 1610,550 1630,550 C 1655,550 1670,565 1670,590 C 1670,615 1655,630 1630,630 C 1610,630 1595,625 1580,620 Z" />

                    {/* "e" */}
                    <path fill="white" d="M 1740,590 C 1740,550 1770,520 1810,520 C 1850,520 1880,550 1880,590 L 1880,600 L 1780,600 C 1785,625 1800,640 1820,640 C 1840,640 1855,630 1860,615 L 1895,625 C 1885,650 1855,660 1820,660 C 1775,660 1740,630 1740,590 Z M 1780,575 L 1845,575 C 1840,555 1825,545 1810,545 C 1795,545 1785,555 1780,575 Z" />
                </g>
            </svg>
        </AbsoluteFill>
    );
};
