---
name: design-taste-frontend
description: "Anti-slop frontend design taste system. Set visual dials, override default AI aesthetics, and enforce high-fidelity layouts."
---

# Design Taste Frontend (Leonxlnx/taste-skill)

This skill overrides default LLM biases (such as generic purple gradients, centered H1 heroes, and repetitive 3-column card layouts) to build production-grade, visually striking user interfaces.

## Configuration Dials

These three global variables steer the layout and density baseline of generated UIs. Adjust them to fine-tune the aesthetic direction:

*   **`DESIGN_VARIANCE`**: `8` (Scale 1-10)
    *   `1` = Perfect Symmetry / Rigid structure.
    *   `10` = Asymmetric Chaos / Highly editorial.
    *   *Rule*: When `DESIGN_VARIANCE > 4`, avoid centered hero/H1 titles. Favor left-aligned content, split-screen designs, or asymmetric layouts.
*   **`MOTION_INTENSITY`**: `6` (Scale 1-10)
    *   `1` = Static / No transitions.
    *   `10` = Heavy / Physics-based animations.
*   **`VISUAL_DENSITY`**: `4` (Scale 1-10)
    *   `1` = Spacious / Gallery-like (Airy).
    *   `10` = Dense / Dashboard (Packed).

## Coding & Architectural Conventions

*   **Grid Over Flex**: Prefer CSS Grid layouts over complex Flexbox margin-math for structural layouts to ensure predictability.
*   **Responsive Viewports**: Always use `min-h-[100dvh]` to avoid mobile safari viewport resizing issues.
*   **Typography Pairing**: Pair an expressive display serif or brutalist font for headers with a clean sans-serif for body text.
*   **Color Accents**: Rely on custom curated HSL/OKLCH color themes with sharp, intentional accent highlights instead of generic AI-purple color palettes.

## Anti-Pattern Ban List

*   ❌ **No repetitive 3-column grids** of cards with identical structure and placeholder icons.
*   ❌ **No flat, solid background blocks** without subtle grid overlays, meshes, or grain textures.
*   ❌ **No centered everything**. Alignment must feel designed, asymmetrical, and purposeful.
*   ❌ **No emojis used as icons** — always use Lucide or inline SVG vectors.
