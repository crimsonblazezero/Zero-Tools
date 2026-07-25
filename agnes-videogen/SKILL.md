---
name: agnes-videogen
description: "Generate videos using the Agnes Video V2.0 model API. Use when the user asks to generate videos via Agnes AI platform (apihub.agnes-ai.com). Triggers on: agnes video, agnes 视频, video gen, generate video, text to video, image to video, keyframe interpolation, 生视频, 文生视频, 图生视频."
---

# Agnes Video Generation

Generate videos using the Agnes Video V2.0 API.

## Prerequisites

- An Agnes AI API key from [API Platform](https://platform.agnes-ai.com)
- Base URL: `https://apihub.agnes-ai.com/v1`

## API Architecture

Agnes Video V2.0 uses an **asynchronous two-step workflow**:
1. **Create Video Task** — submit the request, get a `video_id`
2. **Retrieve Video Result** — poll the `video_id` to get the final video

## API Endpoints

### Step 1: Create Video Task

**Endpoint:** `POST https://apihub.agnes-ai.com/v1/videos`

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`
- `Content-Type: application/json`

### Step 2: Retrieve Video Result

**Endpoint:** `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>`

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`

**Optional parameter:** `model_name` — specify model explicitly (e.g., `agnes-video-v2.0`)

**Legacy method (compatibility):** `GET https://apihub.agnes-ai.com/v1/videos/<TASK_ID>`

## Model Name

`agnes-video-v2.0`

## Request Parameters (Create Task)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Use `agnes-video-v2.0` |
| prompt | string | Yes | Text description of the video content |
| image | string / array | No | Image URL or image URL array (for image-to-video) |
| mode | string | No | Generation mode: `ti2vid` (text-to-video) or `keyframes` |
| height | integer | No | Video height. Default: `768` |
| width | integer | No | Video width. Default: `1152` |
| num_frames | integer | No | Number of frames. Must be ≤ 441, follows `8n + 1` rule |
| frame_rate | number | No | Video FPS. Range: 1–60 |
| num_inference_steps | integer | No | Number of inference steps |
| seed | integer | No | Random seed for reproducible results |
| negative_prompt | string | No | Content to avoid |
| extra_body.image | array | No | Input image URLs for multi-image or keyframe mode |
| extra_body.mode | string | No | Additional mode setting, e.g., `keyframes` |

## Workflows

### 1. Text-to-Video

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "A cinematic shot of a cat walking on the beach at sunset, soft ocean waves, warm golden lighting, realistic motion",
    "height": 768,
    "width": 1152,
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**Response:**
```json
{
  "id": "task_YOUR_TASK_ID",
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "object": "video",
  "model": "agnes-video-v2.0",
  "status": "queued",
  "progress": 0,
  "created_at": 1780457477,
  "seconds": "10.0",
  "size": "1280x768"
}
```

### 2. Image-to-Video (single image)

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "The woman slowly turns around and looks back at the camera, natural facial expression, cinematic camera movement",
    "image": "https://example.com/image.png",
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### 3. Multi-Image Video

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Create a smooth transformation scene between the two reference images, cinematic lighting, consistent character identity, natural motion",
    "extra_body": {
      "image": [
        "https://example.com/image1.png",
        "https://example.com/image2.png"
      ]
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### 4. Keyframe Interpolation

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Generate a smooth cinematic transition between the keyframes, maintaining visual consistency and natural camera movement",
    "extra_body": {
      "image": [
        "https://example.com/keyframe1.png",
        "https://example.com/keyframe2.png"
      ],
      "mode": "keyframes"
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### Retrieve Video Result

Poll until `status` is `"completed"` and `progress` is `100`:

```bash
curl --location --request GET \
  'https://apihub.agnes-ai.com/agnesapi?video_id=video_xxxxxx' \
  --header 'Authorization: Bearer YOUR_API_KEY'
```

**Completed response:**
```json
{
  "id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "model": "agnes-video-v2.0",
  "object": "video",
  "status": "completed",
  "progress": 100,
  "seconds": "10.0",
  "size": "1280x768",
  "remixed_from_video_id": "https://storage.googleapis.com/agnes-aigc/aigc/videos/2026/06/03/video_xxxxxx.mp4",
  "error": null
}
```

Final video URL: `remixed_from_video_id`

## Result Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Task ID |
| video_id | string | Video ID |
| model | string | Model used |
| object | string | Always `"video"` |
| status | string | Task status (`queued`, `processing`, `completed`, `failed`) |
| progress | integer | Progress percentage (0–100) |
| seconds | string | Video duration |
| size | string | Video resolution (e.g., `"1280x768"`) |
| remixed_from_video_id | string | Final video URL (only when completed) |
| error | string / null | Error message if failed |

## Important Notes

- **Asynchronous workflow**: Submit → get `video_id` → poll for result
- `num_frames` must follow `8n + 1` rule and be ≤ 441
- `frame_rate` range: 1–60
- Default resolution: 1152×768
- Recommended polling interval: 30 seconds (to avoid hitting API rate limits or spamming)
- Timeout recommended: 60s–360s for create request
- Pricing: Currently free during beta
- **Image Input**: Must be a publicly accessible image URL. Base64 is not recommended for video generation and might fail.

## Troubleshooting & Best Practices

### 1. Proxy Connection Errors (ProxyError)
When uploading large payloads or making requests through local proxies (such as Clash/VPN clients), the proxy might close the connection unexpectedly, causing `ProxyError` or `RemoteDisconnected`.
**Solution**: Bypass the proxy for Agnes API calls. In Python `requests`, pass `proxies={"http": None, "https": None}`.

### 2. Request Timeout and Hanging
If the network connection drops or the server has a temporary hiccup, Python `requests` calls without a timeout can block indefinitely, freezing your agent.
**Solution**: Always specify a reasonable timeout (e.g., `timeout=15`) in your requests.

### 3. Log Buffering in Background Tasks
When running Python scripts as background tasks, stdout is buffered by default. This makes the log file appear empty until the process exits.
**Solution**: Use `print(..., flush=True)` or launch Python with the `-u` flag (`python -u script.py`) to force immediate log writes.

## Supported Capabilities

- Text-to-Video generation
- Image-to-Video generation (requires public URL)
- Multi-image video composition
- Keyframe interpolation
- Custom resolution, frame rate, and duration
- Reproducible results via seed
