import React from "react";
import { Composition } from "remotion";
import { LogoAnimation } from "./LogoAnimation";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="KovaScape-NordicBuild"
      component={LogoAnimation}
      durationInFrames={180}
      fps={60}
      width={800}
      height={200}
      defaultProps={{}}
    />
  );
};
