---
name: nanobanana-2
description: "Generate images using Antigravity's native Google Gemini Image generation tool. Triggers on: nanobanana, nanobanana 2, nanobanana-2, generate nanobanana image, 蕉蕉图, 香蕉生图."
---

# NanoBanana-2 (Google AI Pro Native Image Generation)

This skill guides the AI to use its native image generation capability to satisfy image requests.

## Workflow

1. When the user requests an image generation using "nanobanana 2", "nanobanana-2", "蕉蕉图", or "香蕉生图", the agent MUST immediately invoke the native `generate_image` tool.
2. Use the following parameters for `generate_image`:
   - **`Prompt`**: The prompt provided by the user (optimized for Gemini's image generation model).
   - **`ImageName`**: A clean, snake_case filename describing the content.
   - **`AspectRatio`**: Default to '1:1' unless the user specifies otherwise.
3. **CRITICAL WORKSPACE SYNC**:
   - Immediately after generation, the agent MUST copy the generated image from the sandbox brain directory to the user's workspace root directory (`d:/Zero Tools/`).
   - Use a clear filename such as `nanobanana_out.jpg` or a descriptive name related to the prompt.
   - Run a powershell command to copy it, e.g.:
     ```powershell
     Copy-Item "C:/path/to/generated/image.jpg" "d:/Zero Tools/filename.jpg"
     ```
4. Present the resulting image to the user and **always provide a clickable file:// link** to the copied image in the workspace root so the user can download and view it easily.
