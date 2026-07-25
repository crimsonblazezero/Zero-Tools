# API Inspection Quick Checklist

## When inspecting an unknown web app:

- [ ] Fetch HTML → find JS files (`grep -o 'src="[^"]*\.js"'`)
- [ ] Read JS files → find API endpoints (`grep -oE '/api/[^"]+'`)
- [ ] Read JS functions → understand request/response format (`grep -B5 -A30 'fetch.*api'`)
- [ ] Test with `curl -v` → verify endpoint exists and get headers
- [ ] Parse response → identify errors (400, 500, nested upstream errors)
- [ ] Check `X-Powered-By` header → identify backend framework
- [ ] Check console for JS errors → `browser_console(clear=true)`
- [ ] Note: browser tools CANNOT passively log network traffic — use curl

## Common API error patterns:

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Bad request / missing fields | Check required parameters in request body |
| 401/403 | Auth failure | Check API keys, tokens, cookies |
| 404 | Endpoint not found | Check URL path, maybe renamed/removed |
| 429 | Rate limited | Wait and retry, check rate limits |
| 500 | Server error | Check nested error JSON for upstream issues |
| 502/503 | Upstream down | Backend service unavailable, not your fault |

## Nested error pattern:

A 500 from the app server wrapping an upstream error:
```json
{"error": "{\"error\":{\"code\":400,\"message\":\"API key not valid\",\"status\":\"INVALID_ARGUMENT\"}}"}
```
→ The real issue is the upstream service (Google AI, OpenAI, etc.), not the app itself.
