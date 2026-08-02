# PPT Tool Comparison — Session Notes

**Date**: 2026-08-01
**Tools Compared**: planners-ppt-hell, codex-ppt-skill, dashi-ppt-skill

## Quick Comparison Table

| Dimension | planners-ppt-hell | codex-ppt-skill | dashi-ppt-skill |
|-----------|-------------------|-----------------|-----------------|
| **Author** | 阿祖不看 TVC | ningzimu | chuspeeism |
| **Stars** | 217 | 4,397 | 4,479 |
| **License** | AGPL-3.0 | MIT | AGPL-3.0 |
| **Core Approach** | Review-gated production line | Image-based generation | Browser-editable web PPT |
| **Tech Stack** | Python + SVG | Python + gpt-image-2 | JavaScript + HTML |
| **Input** | Markdown, proposals, strategy drafts | Markdown, PDF, Word, outlines, papers, notes | Any document |
| **Output** | Editable PPTX | Image-based PPTX | HTML + PPTX + PDF |
| **Post-Generation Editing** | ❌ Locked after review | ❌ Image is final | ✅ Full editor in browser |
| **Speech Notes** | ❌ | ✅ speech.md | ❌ |
| **Animations** | ❌ | ❌ | ✅ 9 transition types |

## Decision Matrix

| If you need... | Choose |
|----------------|--------|
| Human review at every step | planners-ppt-hell |
| Academic/technical presentation | codex-ppt-skill |
| Quick business PPT with editing | dashi-ppt-skill |
| Fully editable PPTX output | planners-ppt-hell or dashi-ppt-skill |
| Image-based visual quality | codex-ppt-skill |
| Post-generation editing | dashi-ppt-skill |
| Chinese platform content (Douyin, etc.) | dashi-ppt-skill |
| Speech notes自动生成 | codex-ppt-skill |

## Important Note on E-Book Conversion

None of these tools accept `.epub` or `.mobi` files directly. Workaround:
1. Convert e-book to PDF or Word first
2. Use codex-ppt-skill or dashi-ppt-skill (both accept PDF/Word input)
3. For dashi-ppt-skill, you can also edit the generated HTML version in-browser