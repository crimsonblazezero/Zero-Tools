---
description: Create and edit PowerPoint presentations with professional layouts, charts, and formatting
---

# pptx

Create, modify, and analyze PowerPoint presentations (.pptx) for business reports, product showcases, supplier communications, and brand presentations.

## When to Use

- Creating product presentations
- Supplier communication decks
- Business reports and analytics
- Brand guidelines presentations
- Training materials
- Sales presentations

## Prerequisites

The pptx skill is located at:
```
C:\Users\china\.agent\skills\pptx
```

Check if required Python library is installed:
```bash
python -c "import pptx; print('python-pptx installed')"
```

If not installed:
```bash
pip install python-pptx
```

## How to Use This Workflow

### Step 1: Read the Skill Documentation

```bash
# View the skill instructions
cat "C:\Users\china\.agent\skills\pptx\SKILL.md"
```

Or use the view_file tool to read the SKILL.md file.

### Step 2: Understand User Requirements

Determine the presentation type:
- **Product Showcase**: New products, features, benefits
- **Business Report**: Sales data, inventory analysis, performance
- **Supplier Communication**: Orders, requirements, specifications
- **Brand Guidelines**: Visual identity, usage rules
- **Training**: Process documentation, best practices

### Step 3: Common Operations

#### Creating a New Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# Create presentation
prs = Presentation()

# Set slide size (16:9)
prs.slide_width = Inches(10)
prs.slide_height = Inches(5.625)

# Add title slide
title_slide_layout = prs.slide_layouts[0]
slide = prs.slides.add_slide(title_slide_layout)
title = slide.shapes.title
subtitle = slide.placeholders[1]

title.text = "KovaScape Product Showcase"
subtitle.text = "Premium Home Decor Collection 2026"

# Save
prs.save('product_showcase.pptx')
```

#### Adding Content Slides

```python
# Add content slide
bullet_slide_layout = prs.slide_layouts[1]
slide = prs.slides.add_slide(bullet_slide_layout)

# Add title
title = slide.shapes.title
title.text = "Product Features"

# Add bullet points
body = slide.placeholders[1].text_frame
body.text = "Premium Materials"

p = body.add_paragraph()
p.text = "Solid Wood Construction"
p.level = 1

p = body.add_paragraph()
p.text = "Hand-Finished Details"
p.level = 1

p = body.add_paragraph()
p.text = "Eco-Friendly Coating"
p.level = 1
```

#### Adding Images

```python
from pptx.util import Inches

# Add blank slide
blank_slide_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_slide_layout)

# Add image
img_path = 'product_image.jpg'
left = Inches(1)
top = Inches(1.5)
width = Inches(8)

pic = slide.shapes.add_picture(img_path, left, top, width=width)
```

#### Adding Charts

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

# Add slide
slide = prs.slides.add_slide(prs.slide_layouts[5])

# Chart data
chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Sales', (150, 180, 210, 240))

# Add chart
x, y, cx, cy = Inches(2), Inches(2), Inches(6), Inches(4)
chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data
).chart

chart.has_legend = True
chart.chart_title.text_frame.text = 'Quarterly Sales Growth'
```

## Example Workflow for KovaScape

**User request:** "创建一个产品展示PPT，给供应商看新款相框"

### Step 1: Plan the Structure

```
Slide 1: Title - "New Frame Collection 2026"
Slide 2: Overview - Product line introduction
Slide 3: Product Details - Specifications and features
Slide 4: Materials - Quality and sourcing
Slide 5: Pricing - MOQ and pricing tiers
Slide 6: Timeline - Production and delivery schedule
Slide 7: Contact - Next steps
```

### Step 2: Create the Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Create presentation with KovaScape branding
prs = Presentation()

# Brand colors
NAVY = RGBColor(31, 58, 96)      # #1F3A60
GOLD = RGBColor(212, 175, 55)     # #D4AF37
CREAM = RGBColor(245, 245, 220)   # #F5F5DC

# Slide 1: Title
title_slide = prs.slides.add_slide(prs.slide_layouts[0])
title = title_slide.shapes.title
subtitle = title_slide.placeholders[1]

title.text = "New Frame Collection 2026"
subtitle.text = "Premium Picture Frames for European Market\nKovaScape Home Decor"

# Style title
title.text_frame.paragraphs[0].font.size = Pt(44)
title.text_frame.paragraphs[0].font.bold = True
title.text_frame.paragraphs[0].font.color.rgb = NAVY

# Slide 2: Product Overview
overview_slide = prs.slides.add_slide(prs.slide_layouts[1])
title = overview_slide.shapes.title
title.text = "Product Line Overview"

body = overview_slide.placeholders[1].text_frame
body.text = "Classic Collection"
p = body.add_paragraph()
p.text = "Traditional wooden frames in oak, walnut, and mahogany"
p.level = 1

p = body.add_paragraph()
p.text = "Modern Collection"
p.level = 0
p = body.add_paragraph()
p.text = "Minimalist metal and acrylic frames"
p.level = 1

p = body.add_paragraph()
p.text = "Luxury Collection"
p.level = 0
p = body.add_paragraph()
p.text = "Gold-leaf and hand-carved premium frames"
p.level = 1

# Slide 3: Specifications Table
spec_slide = prs.slides.add_slide(prs.slide_layouts[5])
title = spec_slide.shapes.title
title.text = "Product Specifications"

# Add table
rows, cols = 5, 4
left = Inches(1)
top = Inches(2)
width = Inches(8)
height = Inches(3)

table = spec_slide.shapes.add_table(rows, cols, left, top, width, height).table

# Set column widths
table.columns[0].width = Inches(2)
table.columns[1].width = Inches(2)
table.columns[2].width = Inches(2)
table.columns[3].width = Inches(2)

# Headers
headers = ['Model', 'Size', 'Material', 'MOQ']
for i, header in enumerate(headers):
    cell = table.cell(0, i)
    cell.text = header
    cell.fill.solid()
    cell.fill.fore_color.rgb = NAVY
    cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    cell.text_frame.paragraphs[0].font.bold = True

# Data
data = [
    ['FR-001', '8x10"', 'Oak Wood', '500'],
    ['FR-002', '11x14"', 'Walnut', '300'],
    ['FR-003', '16x20"', 'Metal', '200'],
    ['FR-004', '20x24"', 'Gold-leaf', '100'],
]

for i, row in enumerate(data, start=1):
    for j, value in enumerate(row):
        table.cell(i, j).text = value

# Save
prs.save('kovascape_frame_collection_2026.pptx')
print("Presentation created: kovascape_frame_collection_2026.pptx")
```

### Step 3: Add Visual Elements

```python
# Add product images (if available)
if os.path.exists('frame_classic.jpg'):
    img_slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Add title
    txBox = img_slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.5))
    tf = txBox.text_frame
    tf.text = "Classic Collection"
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = NAVY
    
    # Add image
    img_path = 'frame_classic.jpg'
    left = Inches(1.5)
    top = Inches(1.5)
    width = Inches(7)
    pic = img_slide.shapes.add_picture(img_path, left, top, width=width)
```

## KovaScape Presentation Templates

### Product Showcase Template

**Slide Structure:**
1. Title + Subtitle (Brand name, collection name)
2. Overview (Product categories)
3. Product Details (Specifications, features)
4. Materials & Quality (Sourcing, certifications)
5. Pricing (MOQ, pricing tiers, payment terms)
6. Timeline (Production, shipping, delivery)
7. Contact & Next Steps

### Business Report Template

**Slide Structure:**
1. Title + Date
2. Executive Summary
3. Sales Performance (Charts, trends)
4. Inventory Status (Stock levels, days supply)
5. Market Analysis (Competitors, opportunities)
6. Action Items
7. Appendix (Detailed data)

### Supplier Communication Template

**Slide Structure:**
1. Title + Order Number
2. Order Summary (Quantities, SKUs)
3. Specifications (Detailed requirements)
4. Quality Standards (Inspection criteria)
5. Timeline (Milestones, deadlines)
6. Logistics (Shipping, packaging)
7. Contact Information

## Best Practices

### Design Principles

- **Consistent branding**: Use KovaScape colors (Navy, Gold, Cream)
- **One idea per slide**: Don't overcrowd
- **Visual hierarchy**: Title → Key points → Details
- **High-quality images**: Minimum 1920x1080 for full-slide images
- **Readable fonts**: Minimum 18pt for body text, 32pt for titles

### Content Guidelines

- **6x6 rule**: Maximum 6 bullet points, 6 words per point
- **Data visualization**: Use charts instead of tables when possible
- **Consistent formatting**: Same fonts, colors, spacing throughout
- **Speaker notes**: Add notes for context and talking points
- **Slide numbers**: Add for easy reference

### KovaScape Brand Guidelines

**Colors:**
- Primary: Navy Blue (#1F3A60)
- Accent: Gold (#D4AF37)
- Background: Cream (#F5F5DC) or White
- Text: Dark Gray (#333333) or Navy

**Fonts:**
- Titles: Playfair Display or Georgia (serif)
- Body: Inter or Calibri (sans-serif)
- Size: 32-44pt titles, 18-24pt body

**Logo Placement:**
- Bottom right corner of each slide
- Or top left for title slides
- Consistent size across all slides

## Pre-Delivery Checklist

Before delivering presentations:

- [ ] All slides have titles
- [ ] Consistent fonts and colors throughout
- [ ] Images are high quality and properly sized
- [ ] Charts have clear labels and legends
- [ ] No spelling or grammar errors
- [ ] Slide numbers added
- [ ] Brand logo on each slide
- [ ] File name is descriptive (include date)
- [ ] Tested on different screen sizes
- [ ] Speaker notes added where needed

## Tips for Better Results

1. **Use templates**: Create reusable templates for common presentations
2. **Image quality**: Use high-resolution images (minimum 1920x1080)
3. **Consistent spacing**: Use guides and alignment tools
4. **Color contrast**: Ensure text is readable on backgrounds
5. **File size**: Compress images if file is too large
6. **Version control**: Save versions (v1, v2, final)

## Common Use Cases for KovaScape

### 1. Product Launch Presentation
- New product introduction
- Features and benefits
- Pricing and availability
- Marketing materials

### 2. Supplier Order Presentation
- Order details and specifications
- Quality requirements
- Timeline and milestones
- Payment terms

### 3. Monthly Business Review
- Sales performance
- Inventory status
- Market trends
- Action items

### 4. Brand Guidelines Presentation
- Logo usage
- Color palette
- Typography
- Visual examples

---

**Remember:** A great presentation tells a story, uses visuals effectively, and keeps the audience engaged. Keep it simple, professional, and on-brand.
