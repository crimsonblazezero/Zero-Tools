---
description: Remotion 最佳实践 (KovaScape 品牌定制版) | Remotion Best Practices (KovaScape Custom)
---

# Remotion 视频创作最佳实践 (KovaScape)
# Remotion Video Creation Best Practices (KovaScape)

本工作流基于 `remotion-best-practices` 技能，并结合 **KovaScape** (北欧简约风) 品牌规范，指导你创建高质量、高性能的渲染视频。

This workflow is based on the `remotion-best-practices` skill and integrated with **KovaScape** (Nordic Minimalist) brand standards to guide the creation of high-quality, high-performance videos.

---

## 1. 项目初始化 | Project Initialization
// turbo
1. 确保已安装必要的依赖：
   ```powershell
   npm install remotion zod@3.22.3 @remotion/zod-types
   ```
2. 建立符合 KovaScape 标准的目录结构：
   - `src/remotion/`: 存放所有组件与 Compositions
   - `public/assets/`: 存放品牌素材（Logo, 产品图）
   - `src/remotion/styles/`: 存放品牌颜色与字体定义

---

## 2. 定义 Composition 与 Schema | Define Composition & Schema
按照以下规范在 `Root.tsx` 中定义：

1. **类型安全 (Type Safety)**: 必须使用 `zod` 定义 `Schema`。
2. **属性默认值 (Default Props)**: 提供符合品牌审美的默认参数。

```tsx
// 示例代码 / Example Code
import { Composition } from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';

export const KovaScapeSchema = z.object({
  title: z.string(),
  brandColor: zColor(),
});

export const RemotionRoot = () => {
  return (
    <Composition
      id="KovaScapePromo"
      component={PromoComponent}
      durationInFrames={150}
      fps={30}
      width={1080}
      height={1920}
      schema={KovaScapeSchema}
      defaultProps={{
        title: 'KovaScape Nordic Home',
        brandColor: '#064338', // KovaScape Deep Emerald
      }}
    />
  );
};
```

---

## 3. 核心动画原则 | Core Animation Principles
**禁止使用 CSS Transitions 或 Animations!** 必须使用 `useCurrentFrame`。

1. **Spring 动画**: 用于自然的进入、缩放效果。
2. **Interpolate 插值**: 用于颜色变化、淡入淡出。

```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// 自然伸缩动画 / Natural spring animation
const scale = spring({
  frame,
  fps,
  config: { stiffness: 100 },
});

// 透明度淡入 / Opacity fade-in
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateRight: 'clamp',
});
```

---

## 4. KovaScape 品牌应用 | KovaScape Brand Application
在视频中贯彻北欧简约风：

- **配色 (Colors)**: 
  - 主色: `Deep Emerald Green (#064338)`
  - 点缀: `Gold (#F3C546)`
  - 背景: `Warm Wood / Minimalist White`
- **字体 (Fonts)**: 优先使用 `Inter` 或 `Outfit`。
- **节奏 (Rhythm)**: 动作应平缓而有力，避免过快的闪烁。

---

## 5. 资源引用 | Asset Handling
1. 图片/视频必须放在 `public/` 目录下。
2. 使用 `staticFile()` 来获取路径。

```tsx
import { Img, staticFile } from 'remotion';

const Logo = () => <Img src={staticFile('assets/logo.png')} />;
```

---

## 6. 渲染预览 | Preview & Render
// turbo
1. 启动预览模式：
   ```powershell
   npx remotion preview
   ```
2. 导出视频：
   ```powershell
   npx remotion render MyComposition out/video.mp4
   ```

---

## 💡 扩展提示 (Extensions)
- **多尺寸自动生产**: 建立 `9:16` (Shorts/TikTok) 和 `16:9` (Amazon Page) 的 Composition。
- **动态元数据**: 使用 `calculateMetadata` 根据不同产品 ID 自动调整视频长度。
