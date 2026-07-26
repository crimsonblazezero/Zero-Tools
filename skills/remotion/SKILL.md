---
name: remotion
description: "Comprehensive guide for programmatically creating videos with React using the Remotion framework. Use this skill when the user wants to: (1) Create or edit motion graphics and videos using React code, (2) Handle video rendering pipelines, (3) Implement complex animations like text effects, transitions, or 3D scenes, (4) Manage media assets like audio, images, GIFs, and Lottie animations, (5) Automate video generation based on data."
---

# Remotion Video Creation

Remotion is a powerful framework for creating videos programmatically with React. This skill provides the essential knowledge and rules for building professional-quality motion graphics.

## Quick Start

1. **Initialize a Project**: Use `npx create-remotion@latest` to start a new project.
2. **Define a Composition**: Every Remotion project starts with a composition that defines the dimensions, duration, and FPS.
3. **Animate with Code**: Use `useCurrentFrame()` and `useVideoConfig()` to drive your animations based on the current frame number.

## Core Reference Modules

This skill includes detailed reference files for various Remotion features. Each file contains specific patterns and code examples:

### Animation & Timing
- [animations.md](references/animations.md) - Fundamental animation skills.
- [timing.md](references/timing.md) - Interpolation curves (linear, easing, spring).
- [text-animations.md](references/text-animations.md) - Typography and text animation patterns.
- [transitions.md](references/transitions.md) - Scene transition patterns.

### Media & Assets
- [assets.md](references/assets.md) - Importing images, videos, audio, and fonts.
- [audio.md](references/audio.md) - Advanced audio handling (trimming, volume, pitch).
- [videos.md](references/videos.md) - Embedding and manipulating video components.
- [images.md](references/images.md) - Using the `Img` component.
- [gifs.md](references/gifs.md) - Synchronized GIF display.
- [lottie.md](references/lottie.md) - Lottie animation integration.
- [fonts.md](references/fonts.md) - Loading Google and local fonts.

### Specialized Features
- [3d.md](references/3d.md) - 3D content with Three.js and React Three Fiber.
- [charts.md](references/charts.md) - Data visualization patterns.
- [maps.md](references/maps.md) - Mapbox integration and animation.
- [tailwind.md](references/tailwind.md) - Styling with TailwindCSS.
- [parameters.md](references/parameters.md) - Parametrized videos with Zod schemas.

### Utility & Analysis (Mediabunny)
- [get-video-dimensions.md](references/get-video-dimensions.md) / [get-video-duration.md](references/get-video-duration.md) - Media metadata extraction.
- [extract-frames.md](references/extract-frames.md) - Extracting frames at specific timestamps.
- [calculate-metadata.md](references/calculate-metadata.md) - Dynamic composition settings.

## Best Practices

- **Avoid logic in render**: Keep your component clean. Use helper functions for complex calculations.
- **Prefer Spring animations**: They feel more natural than linear or easing for UI-like motion.
- **Use Mediabunny for Assets**: Always verify if a video can be decoded ([can-decode.md](references/can-decode.md)) before using it in a heavy pipeline.
- **Clean Sequences**: Use `Sequence` components to manage timing and modularize your video parts ([sequencing.md](references/sequencing.md)).

---
[中文说明] / [English Version]
生成的 Remotion 代码应包含中英双语注释。
Generated Remotion code should include bilingual comments (Chinese and English).
