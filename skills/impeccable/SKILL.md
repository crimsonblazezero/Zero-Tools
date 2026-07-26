---
name: impeccable
description: "Impeccable UI Design manual & steering commands. Applies Paul Bakaus' design rules (OKLCH, typography, micro-interactions, UX writing) and triggers design actions (/audit, /polish, /bolder, /distill)."
---

# Impeccable (pbakaus/impeccable)

This skill equips the AI agent with a professional design vocabulary and actionable steering commands to audit, polish, and optimize generated user interfaces.

## Steering Commands

Use these commands directly in your prompt to trigger specific design actions:

*   **`/audit`**: Audit the current layout and UI from a professional designer's perspective. Output an audit checklist covering contrast (WCAG AA), typography hierarchy, spacing alignments, and visual friction points.
*   **`/polish`**: Focus on micro-interactions, spacing (padding/margins), borders, border-radius, shadows, and transitions. Do not restructure the HTML layout; only refine details for maximum polish.
*   **`/bolder`**: Enhance visual weight and contrast. Make headers larger, use bolder font weights, introduce stronger color contrasts, and expand vertical margins.
*   **`/distill`**: Simplify the UI. Remove unnecessary borders, backgrounds, card wrapping, and lines. Increase negative space (whitespace) to let core components breathe.
*   **`/animate`**: Refine animations and transitions. Use stagger entries (`animation-delay`), smooth bezier curves, and micro-hover states to make the interface feel responsive and alive.

## Core Design Principles

*   **OKLCH Color Space**: Encourage the use of OKLCH colors for CSS gradients and themes to ensure smooth, natural hue transitions without muddy middle colors.
*   **Typography**: Avoid generic default fonts. Maintain an explicit typographic scale where headings are large and characterful, and body copy is readable.
*   **Space as Structure**: Treat empty space (whitespace) as a physical design component. Do not crowd elements.
*   **UX Writing**: Write clean, concise, human-grade UI text. Avoid generic placeholder copy, corporate jargon, and overly formal greetings.
