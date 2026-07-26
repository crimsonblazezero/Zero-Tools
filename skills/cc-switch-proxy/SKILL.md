---
name: cc-switch-proxy
description: "Configure and troubleshoot CC Switch proxy for Codex, Claude Code, and other AI coding agents. Covers provider setup, API format conversion, role mapping, and debugging proxy errors."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [proxy, cc-switch, codex, claude-code, routing, api-format]
    related_skills: [hermes-agent, claude-code, codex]
---

# CC Switch Proxy

CC Switch is a local proxy/router for AI coding agents (Codex, Claude Code, Gemini, etc.) that provides unified API routing, model mapping, failover, and usage tracking.

## When to Use

- Connecting Codex/Claude Code to custom API endpoints
- Routing through local proxy for usage tracking
- Managing multiple providers with model name mapping
- Debugging `BadRequestError: Unexpected message role` or similar API format errors

## Key Concepts

### API Format Modes

CC Switch supports two upstream API formats:

| Mode | Value | Behavior |
|------|-------|----------|
| Chat Completions | `openai_chat` | Converts Responses API format → Chat Completions format |
| Responses | `openai_responses` | Passes through Responses API format unchanged |

### Role Mapping (Critical Pitfall)

**Codex uses `developer` role** internally (Responses API format). When CC Switch converts to Chat Completions:
- `developer` → `system`
- `content: [{"type": "input_text", "text": "..."}]` → `content: "..."`

**If conversion fails**, you'll see:
- `BadRequestError: Unexpected message role`
- `Invalid user message at index N`
- HTTP 500 from upstream API

### wire_api Configuration

In Codex's `settings_config`, the `wire_api` field controls the API format:

```
wire_api = "responses"    # Uses OpenAI Responses API format (developer role)
wire_api = "chat_completions"  # Uses standard Chat Completions format (system role)
```

**If your upstream API doesn't support Responses API format**, set `wire_api = "chat_completions"`.

## Configuration

### Database Path

```
~/.cc-switch/cc-switch.db
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `providers` | Provider definitions, auth, config, meta |
| `proxy_config` | Proxy server settings per app_type |
| `proxy_request_logs` | Request/response tracking |
| `provider_endpoints` | Upstream API endpoint URLs |
| `settings` | Global CC Switch settings |

### Checking Provider Configuration

```python
import sqlite3, json

db_path = "~/.cc-switch/cc-switch.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get current provider
cursor.execute("""
    SELECT id, name, meta, settings_config 
    FROM providers 
    WHERE app_type = 'codex' AND is_current = 1
""")
row = cursor.fetchone()
meta = json.loads(row[2])
settings = json.loads(row[3])

print(f"API Format: {meta.get('apiFormat')}")
print(f"Config: {settings.get('config', '')[:500]}")
```

### Common Meta Fields

- `apiFormat`: `"openai_chat"` or `"openai_responses"`
- `endpointAutoSelect`: Auto-select endpoint from catalog
- `codexChatReasoning`: Codex-specific reasoning/thinking config

## Troubleshooting

### Error: `Unexpected message role`

**Cause**: CC Switch didn't convert `developer` → `system` role properly.

**Fix**:
1. Check `apiFormat` in provider meta
2. If upstream doesn't support Responses format, change Codex's `wire_api` to `"chat_completions"`
3. Or change `apiFormat` to `"openai_responses"` and ensure upstream supports it

### Error: `Invalid user message at index N`

**Cause**: Content array format not converted. Codex sends `content: [{"type": "input_text", "text": "..."}]` but upstream expects `content: "..."`.

**Fix**: Same as above — ensure proper format conversion or use Chat Completions mode.

### Error: `HTTP 500` from proxy

**Cause**: Proxy received request but upstream API rejected it.

**Fix**: Check `proxy_request_logs` in the CC Switch database for `error_message` field.

### Proxy Not Running

```bash
# Check if proxy is listening
netstat -ano | findstr 15721
# or on Linux/macOS
lsof -i :15721
```

### Test Proxy Connection

```python
import urllib.request, json

# Simple test request
test_request = {
    "model": "your-model",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 100,
    "stream": False
}

req = urllib.request.Request(
    "http://127.0.0.1:15721/v1/chat/completions",
    data=json.dumps(test_request).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer YOUR_KEY"}
)
response = urllib.request.urlopen(req, timeout=30)
print(response.read().decode())
```

## Session Log Locations

| Location | Content |
|----------|---------|
| `~/.cc-switch/logs/cc-switch.log` | Proxy server logs |
| `~/.codex/sessions/` | Codex session JSONL files |
| `~/.hermes/logs/agent.log` | Hermes agent logs |

## Related Skills

- `hermes-agent` — Hermes configuration
- `codex` — Codex CLI delegation
- `claude-code` — Claude Code CLI delegation

## Support Files

- `references/debugging-role-errors.md` — Step-by-step debugging guide for "Unexpected message role" errors
