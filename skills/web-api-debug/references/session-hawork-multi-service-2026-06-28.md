# Session Example: Hawork AI Work Platform (2026-06-28)

## App Details

- **URL**: `http://hawork.shulie.io/`
- **Title**: "Hawork" — AI-powered work platform
- **Purpose**: Task-based AI assistant platform (similar to Claude Code / Codex interface)

## Architecture Discovery

### Multi-Service Pattern

Unlike single-server apps, Hawork splits services across ports:

```bash
# Frontend HTML reveals /config.js
curl -s http://hawork.shulie.io/config.js
# Returns: window.__HAWK_CONFIG__ = { chatApiUrl: 'http://hawork.shulie.io:3000' }

# Server config reveals full microservice topology:
curl -s http://hawork.shulie.io:3000/api/server-config
# Returns:
{
  "serverDeploy": true,
  "authServiceUrl": "http://hawork.shulie.io:4000",
  "sessionServiceUrl": "http://hawork.shulie.io:4001",
  "schedulerServiceUrl": "http://hawork.shulie.io:4002",
  "shareServiceUrl": "http://hawork.shulie.io:4003"
}
```

**Ports**: 3000 (frontend/chat), 4000 (auth), 4001 (sessions), 4002 (scheduler), 4003 (share)

### Auth Flow

1. Login via `/api/auth/login` POST with `{"email":"...", "password":"..."}`
2. Response includes JWT token: `{"success":true,"data":{"token":"eyJhbG..."}}`
3. Use token for subsequent API calls: `-H "Authorization: Bearer <token>"`

**Token extraction from CLI**: `python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['token'])"`

### API Endpoint Discovery

From frontend JS bundle:
```bash
# Extract API routes from minified JS
curl -s "http://hawork.shulie.io/assets/index-D8FDWail.js" | grep -o '/api/[^"\x27]*' | sort -u
# Found: /api/auth, /api/paas/v4, /api/scheduler, /api/server-config, /api/sessions, /api/share, /api/skill-file, /api/v3
```

### Model Configuration Query

Asked the in-app AI assistant "查询当前使用的AI模型信息" (query current AI model info).
Response: **"目前系统中尚未配置具体的 AI 模型信息（配置为空）"** — No *custom* AI models configured.

**CORRECTED FINDING**: Despite the "empty config" response, the AI assistant **was actively responding** to messages. This means:
- The platform has a **built-in default model** that works without user configuration
- The `get_config` tool query for `model-config` returns empty because *custom* user config is absent
- The platform is operational out-of-the-box with a default model
- Users can optionally add custom models (OpenAI, Anthropic, Gemini) via settings

**How to detect this**: Send a test message and observe if the AI responds. If it does, a model IS configured — possibly at the platform/system level, not the user level.

**Frontend model support**: The platform supports OpenAI, Anthropic, Google Gemini, and regional models (found in JS strings: "Supports OpenAI, Anthropic, Google Gemini and various domestic models").

**API endpoints for model management** (from frontend JS):
- `GET /api/assigned-models` — assigned models
- `POST /api/assigned-models` — save assigned models
- `GET /api/user-models` — user model config
- `GET /api/oauth/config` — OAuth configuration
- `POST /api/oauth/login` — OAuth login
- Events: `hawk:model_config_updated`, `hawk:config_updated`

### Full API Endpoints Discovered

| Endpoint | Method | Service |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth (4000) |
| `/api/sessions` | GET | Sessions (4001) |
| `/api/sessions/:id/messages` | GET | Sessions (4001) |
| `/api/sessions/:id` | GET | Sessions (4001) |
| `/api/server-config` | GET | Chat (3000) |
| `/api/assigned-models` | GET/POST | Auth (4000) |
| `/api/oauth/config` | GET | Auth (4000) |
| `/api/oauth/login` | POST | Auth (4000) |
| `/api/skill-file` | GET | Chat (3000) |
| `/api/share` | ? | Share (4003) |
| `/api/scheduler` | ? | Scheduler (4002) |
| `/api/paas/v4` | ? | ? |
| `/api/v3` | ? | ? |

## Key Takeaways

1. **Multi-service apps need port-specific curl calls** — the frontend URL may differ from API endpoints. Always check `/config.js`, `/api/server-config`, or JS bundles for service topology.
2. **Token-based auth requires extracting the JWT** — use `python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['token'])"` to extract tokens from JSON responses.
3. **Empty model config ≠ no AI working** — "model-config is empty" means no *custom* user config, not that the platform lacks AI. The platform may have a built-in default model. Always send a test message to verify actual functionality.
4. **Python `requests` beats complex curl chains** — on Windows+bash, shell quoting breaks easily. Use Python for authenticated API calls instead of chaining curl with variable extraction.
5. **Session messages reveal tool usage** — examine `blocks[].tool.name` and `blocks[].tool.output` in message responses to understand what capabilities/tools the platform exposes.
