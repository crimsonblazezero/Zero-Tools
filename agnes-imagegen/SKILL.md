---
name: agnes-imagegen
description: "Generate images using the Agnes Image 2.0 Flash model API. Use when the user asks to generate images via Agnes AI platform (apihub.agnes-ai.com). Triggers on: agnes image, agnes 图片, image gen, generate image, text to image, img2img, image editing, multi-image composition, 生图, 文生图, 图生图."
---

# Agnes Image Generation

Generate images using the Agnes Image 2.0 Flash API.

## Prerequisites

- An Agnes AI API key stored as `OPENAI_API_KEY` in `$HOME/AppData/Local/hermes/.env` (NOT a separate `AGNES_API_KEY` — the key is aliased under the OpenAI variable name because the provider is configured as `openai-api` with Agnes base URL)
- Base URL: `https://apihub.agnes-ai.com/v1`

### API Key Extraction Pattern

```bash
KEY=$(grep '^OPENAI_API_KEY=' "$HOME/AppData/Local/hermes/.env" | head -1 | cut -d= -f2-)
curl -X POST "https://apihub.agnes-ai.com/v1/images/generations" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"agnes-image-2.0-flash","prompt":"...","size":"1024x1024","extra_body":{"response_format":"url"}}'
```

## API Details

**Endpoint:** `POST https://apihub.agnes-ai.com/v1/images/generations`

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`
- `Content-Type: application/json`

**Model Name:** `agnes-image-2.0-flash`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Fixed as `agnes-image-2.0-flash` |
| prompt | string | Yes | Text prompt describing the target image or editing instruction |
| size | string | Yes | Output image size: `1024x768`, `1024x1024`, or `768x1024` |
| image | string[] | Image-to-Image only | Input image array. Supports public URLs or Data URI Base64 |
| return_base64 | boolean | No | Return Base64 output for text-to-image |
| extra_body.response_format | string | No | Output format: `url` or `b64_json` |

## Workflows

### 1. Text-to-Image (URL output)

```bash
curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "A clean product photo of a glass cube on a white studio background, soft shadows, high detail",
    "size": "1024x768",
    "extra_body": { "response_format": "url" }
  }'
```

Result: `data[0].url`

### 2. Text-to-Image (Base64 output)

```bash
curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "A clean product photo of a glass cube on a white studio background, soft shadows, high detail",
    "size": "1024x768",
    "return_base64": true
  }'
```

Result: `data[0].b64_json`

### 3. Image-to-Image (URL input, URL output)

```bash
curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "Transform this image into a cinematic cyberpunk style while preserving the main subject and composition",
    "size": "1024x768",
    "extra_body": {
      "image": ["https://example.com/input-image.png"],
      "response_format": "url"
    }
  }'
```

### 4. Multi-Image Composition

```bash
curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "Combine the two characters into an intense fantasy battle scene, dynamic lighting, detailed background, cinematic composition",
    "size": "1024x768",
    "extra_body": {
      "image": [
        "https://example.com/character-1.png",
        "https://example.com/character-2.png"
      ],
      "response_format": "url"
    }
  }'
```

## Response Format

URL output:
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

Base64 output:
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": null,
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA...",
      "revised_prompt": null
    }
  ]
}
```

## Important Notes

- Text-to-image does not require the `image` parameter
- Image-to-image requires `image` array (public URLs or Data URI Base64)
- Image-to-image does NOT require `tags: ["img2img"]`
- Do NOT place `response_format` at the top level — use `extra_body.response_format`
- Client timeout recommended: 60s–360s
- Pricing: Currently free during beta

## Prompt Best Practices

**Text-to-Image structure:**
`[Main subject] + [Scene/background] + [Style] + [Lighting] + [Composition] + [Quality requirements]`

Example:
```
A young explorer standing in an ancient temple, cinematic fantasy style, warm dramatic lighting, wide-angle composition, ultra detailed, high quality
```

**Image-to-Image structure:**
`[Editing instruction] + [Elements to preserve] + [Target style/scene] + [Lighting] + [Composition] + [Quality requirements]`

Example:
```
Change the background into a cinematic fantasy temple while preserving the person's face, outfit, and pose, warm dramatic lighting, wide-angle composition, ultra detailed, high quality
```

## Post-Generation: Compositing into Frames / Artifacts

When the user wants a generated image placed into an existing frame, matting, or other container image:

1. **Analyze the target image** with `vision_analyze` to determine matting opening position, size ratios, and frame characteristics.
2. **Generate the content image** using the workflows above.
3. **Download both images** via `requests.get()` (generated) and local file path (target frame).
4. **Calculate matting geometry**: open the target image with `PIL.Image`, read its size, compute the matting opening region (usually centered, proportional to frame size — e.g., 10×12 frame matted to 8×10 → ~80% width, ~83% height, centered).
5. **Resize content** to fit the matting opening using `Image.LANCZOS`.
6. **Composite** using `frame.convert("RGBA")` then `frame_rgba.paste(resized_content, (mat_x, mat_y))` — pure PIL, no numpy dependency (numpy is often not installed).
7. **Save and verify** with `vision_analyze` to confirm correct placement.

**Pitfalls:**
- `numpy` is frequently unavailable — use pure PIL for compositing.
- Browser tools may time out on image URLs — use `requests` + local file download instead.
- Always preserve the original frame造型 (shape/profile); only replace the inner matting/opening area.
