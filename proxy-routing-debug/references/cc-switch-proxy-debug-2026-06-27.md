# CC Switch Proxy Debugging — Hermes + Codex Integration

Session-specific debugging notes for CC Switch proxy routing issues with Hermes Agent ↔ Codex.

## Session: 2026-06-27

### Problem
Hermes Agent connected to Codex via CC Switch local proxy (127.0.0.1:15721). Sending messages resulted in:
```
***.BadRequestError: OpenAIException - {"error":{"message":"Unexpected message role.","type":"BadRequestError","param":null,"code":400}}
```

### Investigation Steps Taken
1. Checked `cc-switch/logs/cc-switch.log` — showed proxy startup and DB migrations, no request-level logs
2. Queried CC Switch SQLite DB (`~/.cc-switch/cc-switch.db`):
   - `proxy_config`: codex proxy enabled on port 15721, logging enabled
   - `providers`: active provider `c1050a07...` (Agnes) with `"apiFormat":"openai_responses"`
3. Verified proxy is listening: `netstat -ano | findstr 15721` → LISTENING PID 4576
4. Checked Hermes config: `model.base_url` pointed to `https://apihub.agnes-ai.com/v1` directly

### Root Cause
The active CC Switch provider has `"apiFormat":"openai_responses"` which expects **OpenAI Responses API** format, not **Chat Completions** format. Hermes sends Chat Completions format messages. This format mismatch causes the `Unexpected message role` error.

Additionally, Hermes was NOT routing through CC Switch proxy — the `base_url` pointed directly at the upstream provider, bypassing the proxy entirely.

### Provider Details
- **Provider ID**: `c1050a07-c672-4f98-ac39-380e96a3ebaa`
- **Name**: Agnes
- **apiFormat**: `openai_responses`
- **Endpoint**: `https://apihub.agnes-ai.com/v1`

### Resolution Options
1. Point Hermes `model.base_url` to CC Switch proxy: `http://127.0.0.1:15721/v1`
2. Change CC Switch provider `apiFormat` to `openai_chat`
3. Use Hermes built-in proxy: `hermes proxy`

### Files Examined
- `~/.cc-switch/logs/cc-switch.log` — CC Switch application logs
- `~/.hermes/logs/errors.log` — Hermes error logs
- `~/.hermes/logs/agent.log` — Hermes agent logs
- `~/.cc-switch/settings.json` — CC Switch settings
- `~/.cc-switch/cc-switch.db` — CC Switch SQLite database
- `~/.hermes/config.yaml` — Hermes configuration