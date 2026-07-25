---
name: proxy-routing-debug
description: "Debugging guide for LLM API proxy routing issues — message format mismatches, role errors, base_url misconfigurations, and provider API format conflicts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, proxy, routing, api-format, cc-switch, openai]
---

# Proxy Routing Debugging

## When to Use

When an LLM client (Hermes Agent, Codex, Claude Code, etc.) routed through a local proxy or gateway returns HTTP 400 errors like:
- `Unexpected message role`
- `BadRequestError`
- `Invalid message format`
- Role-related 400 errors from OpenAI-compatible APIs

## Common Root Causes

### 1. API Format Mismatch
The proxy may be configured for a different API format than the client sends:
- **Chat Completions** (`/v1/chat/completions`): standard OpenAI format with `role`/`content`
- **Responses** (`/v1/responses`): newer OpenAI format with different message structure
- **Function Calling** vs **Tool Use**: different parameter naming

**Check**: Look for `apiFormat` in proxy provider config. `openai_responses` ≠ Chat Completions.

### 2. Invalid Role Values
Only these role values are valid for OpenAI Chat Completions:
- `system`, `user`, `assistant`, `tool`

Any other value (`ai`, `bot`, `function`, `model`, empty string, `User`, `Assistant`) causes 400.

### 3. Base URL Misconfiguration
The client may be pointing directly at the upstream provider instead of the proxy:
- Client `base_url` should point to proxy address (e.g., `http://127.0.0.1:15721/v1`)
- Not the upstream provider (e.g., `https://api.upstream.com/v1`)

### 4. Middleware Transform Errors
Proxies that transform messages (role mapping, system prompt injection, tool format conversion) may introduce invalid structures.

## Debugging Checklist

1. **Verify proxy is running**: Check port is LISTENING (`netstat`, `ss`, `lsof`)
2. **Check client config**: Verify `base_url`, `provider`, `model` settings
3. **Read error logs**: Look for `BadRequestError`, `Unexpected message role` in client logs
4. **Inspect proxy config**: Check `apiFormat`, message transformation settings
5. **Compare formats**: Client sends Chat Completions format → proxy should expect same
6. **Test direct connection**: Bypass proxy temporarily to confirm upstream works
7. **Enable proxy logging**: Turn on request/response logging in proxy config

## Provider-Specific Notes

### CC Switch (Codex/Claude/Hermes proxy)
- Config stored in `~/.cc-switch/cc-switch.db` (SQLite)
- Providers table: check `app_type`, `meta.apiFormat`, `is_current`
- Proxy config: check `enabled`, `enable_logging`, `listen_port`
- Settings: `~/.cc-switch/settings.json`
- Logs: `~/.cc-switch/logs/cc-switch.log`

### Hermes Agent
- Config: `~/.hermes/config.yaml` — check `model.base_url`, `model.provider`
- Logs: `~/.hermes/logs/errors.log`, `~/.hermes/logs/agent.log`
- Auth: `~/.hermes/auth.json` for OAuth providers

### Windows Netstat Encoding
`netstat` output may not be UTF-8. Use: `chcp 65001 > nul && netstat -ano`

## Session-Specific References

See `references/` for detailed session debugging transcripts and provider configurations.

## Quick Fix Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Unexpected message role` | API format mismatch | Change `apiFormat` to `openai_chat` or point client to proxy |
| HTTP 404 | Wrong base_url / endpoint | Verify proxy is running on configured port |
| HTTP 401/403 | Auth token expired/wrong | Re-authenticate with upstream provider |
| HTTP 429 | Rate limit | Check provider limits, enable failover |
| Silent failure | Proxy not intercepting traffic | Verify base_url points to proxy, not upstream |