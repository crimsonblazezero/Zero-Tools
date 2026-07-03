---
name: agnes-imagegen
description: "Generate images using the Agnes Image 2.0 Flash model API. Use when the user asks to generate images via Agnes AI platform (apihub.agnes-ai.com). Triggers on: agnes image, agnes 图片, image gen, generate image, text to image, img2img, image editing, multi-image composition, 生图, 文生图, 图生图."
---

# Agnes Image Generation

Generate images using the Agnes Image 2.0 Flash API.

## Prerequisites

- An Agnes AI API key from [API Platform](https://platform.agnes-ai.com)
- Base URL: `https://apihub.agnes-ai.com/v1`

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
