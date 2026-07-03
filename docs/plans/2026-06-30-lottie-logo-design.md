# KovaScape Lottie Logo Animation Design Specification

## Overview
This document specifies the animation design for the KovaScape horizontal brand logo banner. The animation will be built as a Lottie JSON scene and verified using the Skia Skottie player.

## 1. Composition Setup
- **File Path:** `public/projects/kovascape/logo-banner/lottie.json`
- **Control Path:** `public/projects/kovascape/logo-banner/controls.json`
- **Canvas Size:** 800 x 200 pixels
- **Duration:** 180 frames (3 seconds at 60 FPS)
- **Background Policy:** Transparent by default, with a configurable background color solid layer.

---

## 2. Layer Hierarchy & Geometry
The composition contains three primary logical groups:

### 2.1. Background Layer (`bg_layer`)
- **Type:** Solid color layer.
- **Size:** 800 x 200 pixels.
- **Color:** Configured via `bgColor` slot (Default: `#064338` / `[0.0235, 0.2627, 0.2196, 1.0]`).
- **Opacity:** Configured via `bgOpacity` slot (Default: `0` / transparent, range `0` to `100`).

### 2.2. Icon Group (`icon_group`)
- **Position:** Positioned on the left, centered vertically at `(150, 100)`.
- **Elements:**
  1. **Left Pillar (`pillar_path`):** White stroke path.
  2. **Center House (`house_path`):** White fill/stroke path with 4 window panes cut out.
  3. **Right Ribbon (`ribbon_path`):** White stroke path.
  4. **Accent Square (`accent_square`):** Solid gold square (`#F3C546` / `[0.9529, 0.7725, 0.2745, 1.0]`).

### 2.3. Wordmark Text Group (`text_group`)
- **Position:** Right-aligned starting from `x = 280`, vertically centered.
- **Type:** Vector shapes representing the letters "KovaScape" (White color, bound to `mainColor` slot).

---

## 3. Timeline & Easing
All easing profiles utilize a smooth custom cubic-bezier ease-out curve `[0.16, 1, 0.3, 1]` unless specified.

| Frame Range | Time (s) | Target Element | Animation Type | Easing / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **0 - 60** | 0.0 - 1.0s | `icon_group` Paths | Trim Path End (`0% -> 100%`) | Staggered: Pillar (0f) -> House (10f) -> Ribbon (15f). |
| **45 - 105** | 0.75 - 1.75s | `text_group` | Mask Width & Position | Mask slides left-to-right (`0 -> 450px`). Text position slides `x: 260 -> 280`. |
| **60 - 90** | 1.0 - 1.5s | `accent_square` | Scale (`0% -> 100%`) | Elastic Bounce/Overshoot: Peak at 115% (75f), settle at 100% (90f). |
| **90 - 150** | 1.5 - 2.5s | All Layers | None | Hold for brand visibility. |
| **150 - 180** | 2.5 - 3.0s | Global Comp | Opacity (`100% -> 0%`) | Fade out to prepare for seamless loop reset. |

---

## 4. Slots & controls.json Configuration

### 4.1. Slots Mapping
- **`bgColor`**: Color picker for background. Default `[0.0235, 0.2627, 0.2196, 1.0]`.
- **`bgOpacity`**: Slider `0` to `100`. Default `0`.
- **`mainColor`**: Color picker for Icon paths and Wordmark text. Default `[1.0, 1.0, 1.0, 1.0]`.
- **`accentColor`**: Color picker for the accent gold square. Default `[0.9529, 0.7725, 0.2745, 1.0]`.

### 4.2. `controls.json` Structure
```json
{
  "controls": [
    { "sid": "bgColor", "label": "Background Color" },
    { "sid": "bgOpacity", "label": "Background Opacity", "min": 0, "max": 100, "step": 1 },
    { "sid": "mainColor", "label": "Main Icon/Text Color" },
    { "sid": "accentColor", "label": "Accent Square Color" }
  ]
}
```
