---
name: kovascape-design-system
description: "Official KovaScape Brand Design System. Nordic Minimalist style with Deep Emerald Green (#064338) and Gold (#F3C546) accents. Focus on Real Wood (Oak, Walnut) harmony. Guidelines for A+ Content, Manuals, and Web Interface."
---

# KovaScape Design System - Nordic Premium

**Brand Philosophy**: "Warm Minimalism" — Combining the sleekness of Nordic design with the warmth of natural wood textures and premium dark greens.

## 1. Color Palette (The "Emerald & Gold" Standard)

### Primary Brand Colors
| Role           | Color            | Hex       | Usage                                               |
| -------------- | ---------------- | --------- | --------------------------------------------------- |
| **Core Brand** | **Deep Emerald** | `#064338` | Primary logos, strong headers, premium boxes.       |
| **Secondary**  | Forest Green     | `#0A5A47` | Hover states, secondary buttons.                    |
| **Darkest**    | Midnight Green   | `#1B3420` | Footers, dark mode backgrounds, high contrast text. |

### Metallic Accents (Luxury Indicators)
| Role          | Color          | Hex       | Usage                                        |
| ------------- | -------------- | --------- | -------------------------------------------- |
| **Highlight** | **Royal Gold** | `#F3C546` | CTA buttons, "Premium" badges, 5-star icons. |
| **Subtle**    | Muted Gold     | `#BCAD5B` | Borders, dividers, secondary icons.          |

### Backgrounds & Neutrals (Warmth)
| Role      | Color          | Hex       | Usage                                            |
| --------- | -------------- | --------- | ------------------------------------------------ |
| **Base**  | **Warm Beige** | `#F5DFC1` | Main backgrounds (web/print) to soften the look. |
| **Light** | Cream          | `#F2EEDD` | Content cards, inner sections.                   |
| **Text**  | Dark Charcoal  | `#2C2C2C` | Body text (Never pure black).                    |

---

## 2. Material Harmony (The "Wood First" Rule)

> [!IMPORTANT]
> **Conflict Warning**: Our products are **Oak and Walnut**.
> - **Do NOT** use large fields of Emerald Green behind Walnut wood—it kills the warmth.
> - **DO** use Beige (`#F5DFC1`) or Cream (`#F2EEDD`) backgrounds for product shots.
> - **DO** use Emerald Green (`#064338`) for *framing* elements: headers, footers, sidebars, and CTA buttons.

**Visual Hierarchy**:
1.  **Product Texture** (Real Wood) - *Hero*
2.  **Background** (Warm Beige/Cream) - *Stage*
3.  **Brand Color** (Emerald Green) - *Frame*
4.  **Accent** (Gold) - *Jewelry*

---

## 3. Typography

### Headings (Elegant & Classic)
*   **Font**: **Playfair Display**
*   **Weight**: 700 (Bold) for H1, 600 (SemiBold) for H2.
*   **Case**: Sentence case or Title Case. *Avoid all-caps for long titles.*

### Body Text (Clean & Modern)
*   **Font**: **Poppins**
*   **Alternative**: **Avenir Next Arabic** (for technical manuals/specs).
*   **Weight**: 400 (Regular). 300 (Light) for large captions.

---

## 4. Output Guidelines (Agent Instructions)

### A+ Content (Amazon)
*   **Modules**: Use clean, white/cream space. Don't overcrowding.
*   **Images**: Lifestyle shots must be "Nordic Home" style—bright, airy, indoor plants.
*   **Text Overlay**: Use Deep Emerald text on Beige backgrounds.

### Product Manuals
*   **Cover**: Deep Emerald `#064338` full bleed with Gold logo.
*   **Inside**: Cream `#F2EEDD` pages.
*   **Diagrams**: Black line art, Gold highlights for "Action" points (screws, hooks).

### Web Interface
*   **Buttons**: Solid Emerald Green (`#064338`) with Gold Text or Border.
    *   *Hover*: Lift shadow + brighten to `#0A5A47`.
*   **Cards**: White or Cream card on Beige background. `shadow-sm` (soft shadow).

---

## 5. Implementation Snippets

### CSS Variables
```css
:root {
  --color-primary: #064338;
  --color-primary-light: #0A5A47;
  --color-primary-dark: #1B3420;
  
  --color-accent: #F3C546;
  --color-accent-muted: #BCAD5B;
  
  --color-bg-base: #F5DFC1;
  --color-bg-card: #F2EEDD;
  
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Poppins', sans-serif;
}
```

### Tailwind Config Extension
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        emerald: {
          900: '#064338', // Brand Base
          800: '#0A5A47',
          950: '#1B3420',
        },
        gold: {
          400: '#F3C546', // Brand Accent
          500: '#BCAD5B',
        },
        beige: {
          100: '#F2EEDD',
          200: '#F5DFC1',
        }
      },
      fontFamily: {
        serif: ['Playfair Display', 'serif'],
        sans: ['Poppins', 'sans-serif'],
      }
    }
  }
}
```
