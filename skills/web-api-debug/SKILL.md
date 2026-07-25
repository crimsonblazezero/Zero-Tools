---
name: web-api-debug
description: "Debug and inspect web application backend APIs — discover endpoints, probe request/response formats, diagnose server errors. Use when the browser tool can't show you the Network tab and you need to inspect actual API calls, or when testing backend endpoints directly via curl."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, web, api, curl, backend, network, qa]
---

# Web API Debugging

## When to Use

- The browser tool gives you DOM snapshots and console output, but NOT the DevTools Network tab
- You need to discover what API endpoints a web app calls
- You need to inspect actual request/response formats, headers, or bodies
- You want to verify the server is reachable and responding correctly
- You're doing QA on a web app and need backend evidence for frontend bugs

## Core Technique: curl as Network Tab Replacement

### Step 1: Infer the API endpoint

Common patterns to look for:
- `/api/*` — most REST apps
- `/graphql` — GraphQL endpoints  
- `/rpc/*` or `/services/*` — RPC-style APIs
- Check page source for hardcoded URLs: `browser_console(expression: "document.documentElement.outerHTML")`
- Look for `fetch()` or `axios` calls in the JS bundle

### Step 2: Probe with curl

```bash
# Basic connectivity test
curl -v http://<host>:<port>/

# POST to an API endpoint
curl -X POST http://<host>:<port>/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}' \
  -v
```

Use `-v` (verbose) to see headers, HTTP version, and full request/response.

### Step 3: Interpret HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success — check response body for data format |
| 400 | Bad Request — check error message for missing/invalid params |
| 401/403 | Auth issue — API key, token, or permissions |
| 404 | Endpoint not found — wrong URL path |
| 405 | Method not allowed — wrong HTTP verb |
| 429 | Rate limited |
| 500 | Server error — backend crashed or downstream dependency failed |
| 502/503 | Gateway/upstream error |

### Step 4: Read Response Headers for Tech Stack Clues

- `X-Powered-By: Express` → Node.js/Express backend
- `Content-Type: application/json` → JSON API
- `Server: nginx` → Reverse proxy in front
- `Set-Cookie` → Session/auth mechanism
- `Access-Control-Allow-Origin` → CORS configuration

### Step 5: Diagnose Common Issues

**Backend returns 400 with missing param:**
- Try minimal valid payload first, then expand
- Check error message for exact field names

**Backend returns 500 with downstream API error:**
- The 500 often wraps a third-party API error (e.g., invalid API key, quota exceeded)
- Read the inner error message — the root cause is usually in the nested JSON

**Multi-service app (ports differ from frontend):**
- Modern platforms split services across ports (auth:4000, sessions:4001, scheduler:4002, etc.)
- The frontend URL may not be the API URL. Check `/config.js`, `/api/server-config`, or JS bundles for service topology.
- Example: `curl -s http://hawork.shulie.io/config.js` → reveals `chatApiUrl: 'http://hawork.shulie.io:3000'`
- Then: `curl -s http://hawork.shulie.io:3000/api/server-config` → reveals full microservice map

**Browser shows no response but curl works:**
- CORS misconfiguration
- Frontend JS error (check `browser_console()`)
- Frontend expects different response format than backend sends

**curl works but browser doesn't:**
- CORS issue (curl bypasses CORS)
- Frontend bug in request construction
- Missing auth headers from browser context

## Multi-Service Architecture Discovery

Some platforms split services across multiple ports (auth, sessions, scheduler, etc.). The frontend URL may differ from API endpoints.

### Step 1: Find the config

```bash
# Check for runtime config files
curl -s http://TARGET_URL/config.js
curl -s http://TARGET_URL/api/server-config
```

### Step 2: Map the service topology

```bash
# Server config often reveals all service URLs
curl -s http://TARGET_URL:PORT/api/server-config
# Look for authServiceUrl, sessionServiceUrl, etc.
```

### Step 3: Extract API routes from JS bundles

```bash
# Get the JS bundle URL from HTML
curl -s http://TARGET_URL/ | grep -o 'src="[^"]*\.js"'

# Search for API routes in the bundle
curl -s http://TARGET_URL/assets/bundle.js | grep -o '/api/[^"\x27]*' | sort -u
```

### Step 4: Handle token-based auth

```bash
# Login and extract token
TOKEN=$(curl -s http://AUTH_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# Use token for authenticated calls
curl -s http://SESSION_URL/api/sessions \
  -H "Authorization: Bearer $TOKEN"
```

## Pitfalls

- **Browser tools don't capture Network traffic** — the browser tool gives you DOM snapshots and console output, but NOT the DevTools Network tab. Always use curl as a complement when you need to see actual HTTP requests/responses.
- **Don't assume the frontend is sending correct data** — the UI may be constructing requests incorrectly. Use curl to test the backend independently.
- **CORS errors are frontend problems, not backend** — if curl works but the browser doesn't, the issue is CORS configuration or frontend request construction.
- **Try minimal payloads first** — complex request bodies hide missing-required-field errors. Start with the smallest valid request.
- **Multi-service apps split across ports** — modern platforms (auth, sessions, scheduler, share) run on different ports. The frontend URL ≠ API URL. Always check `/config.js`, `/api/server-config`, or JS bundles for the full topology.
- **JWT tokens get truncated in CLI output** — when extracting tokens from JSON, use `python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['token'])"` to avoid shell quoting issues.
- **Empty model config is a valid finding** — some platforms are scaffolds awaiting configuration. Report this explicitly rather than assuming the app is broken.
- **"model-config empty" ≠ no AI working** — platforms may have built-in default models that work without user configuration. The `get_config` tool may return empty for *custom* config while the platform still has a default model running. Always send a test message to verify actual AI functionality before concluding the platform lacks AI.
- **Use Python `requests` for authenticated API calls** — on Windows+bash, shell quoting breaks easily with complex curl chains. Use Python for extracting tokens and making authenticated calls.

## Related Skills

- `dogfood` — exploratory QA of web apps (broader testing workflow)
- `systematic-debugging` — 4-phase root cause debugging methodology
- `proxy-routing-debug` — LLM API proxy debugging (specific to LLM routing)

## Support Files

- `references/session-amazon-listing-gen-2026-06-28.md` — Amazon Listing 批量生图 app: curl probing, Google API key error discovery
- `references/session-hawork-multi-service-2026-06-28.md` — Hawork AI work platform: multi-service architecture discovery, token auth flow, model config query
