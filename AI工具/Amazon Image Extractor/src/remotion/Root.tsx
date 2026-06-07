import { Composition } from 'remotion';
import { LogoReveal, LogoRevealSchema } from './LogoReveal';
import { SolarLogoReveal, SolarRevealSchema } from './SolarLogoReveal';
import { BannerSolarReveal, BannerSolarSchema } from './BannerSolarReveal';
import { KovaScapeSVGLogo } from './KovaScapeSVGLogo';
import { KovaScapePNGMask } from './KovaScapePNGMask';
import { KovaScapeColors } from './styles/colors';
import './styles/global.css'; // We will create this for fonts

export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="KovaScape-NordicBuild"
                component={LogoReveal}
                durationInFrames={120} // 4 seconds
                fps={30}
                width={1920}
                height={1080}
                schema={LogoRevealSchema}
                defaultProps={{
                    title: 'KovaScape',
                    primaryColor: KovaScapeColors.DeepEmerald,
                    secondaryColor: KovaScapeColors.Gold,
                }}
            />
            <Composition
                id="KovaScape-SolarCycle"
                component={SolarLogoReveal}
                durationInFrames={150} // 5 seconds
                fps={30}
                width={1920}
                height={1080}
                schema={SolarRevealSchema}
                defaultProps={{
                    title: 'KovaScape',
                    sunColor: KovaScapeColors.Gold,
                }}
            />
            <Composition
                id="KovaScape-BannerSolar"
                component={BannerSolarReveal}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                schema={BannerSolarSchema}
                defaultProps={{
                    sunColor: KovaScapeColors.Gold,
                }}
            />
            <Composition
                id="KovaScape-SVGBanner"
                component={KovaScapeSVGLogo}
                durationInFrames={90} // 3 seconds
                fps={30}
                width={1920}
                height={1080}
            />
            <Composition
                id="KovaScape-PNGMask"
                component={KovaScapePNGMask}
                durationInFrames={120} // 4 seconds
                fps={30}
                width={1920}
                height={1080}
            />
        </>
    );
};
