---
name: browser-inspection
description: "Inspect web applications: API endpoints, network traffic, frontend code, backend routes, and debugging techniques using browser tools and terminal."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, inspection, debugging, api, network, web-qa]
---

# Browser Inspection

Techniques for inspecting web applications: discovering API endpoints, reading frontend source, debugging network traffic, and analyzing backend behavior.

## What This Skill Covers

- Discovering API endpoints from frontend JavaScript
- Reading and parsing frontend source code to understand request formats
- Using terminal-based `curl` to test API endpoints directly
- Understanding browser tool limitations for network inspection
- Analyzing server responses and error messages

## Workflow

### Step 1: Discover the Application Structure

First, understand what the application is and what it does:

```bash
# Get the HTML to find script sources
curl -s http://TARGET_URL/ | grep -o 'src="[^"]*\.js"' | head -20
curl -s http://TARGET_URL/ | grep -o 'href="[^"]*"' | head -20
```

Look for:
- JavaScript files in `<script src="...">` tags
- CSS files for style clues
- Meta tags for description
- Page title and structure

### Step 2: Find API Endpoints

API endpoints are typically called from JavaScript. Search the frontend source:

```bash
# Search for fetch/axios calls in JS files
curl -s http://TARGET_URL/js/main.js | grep -oE '(fetch|axios)\([^)]*\)' | head -20

# Search for API route patterns
curl -s http://TARGET_URL/js/main.js | grep -oE '["\x27]/api/[^"\x27]+["\x27]' | sort -u

# Search for specific HTTP methods
curl -s http://TARGET_URL/js/main.js | grep -E '(POST|GET|PUT|DELETE|PATCH)' | head -20
```

Common patterns:
- `fetch('/api/endpoint', { method: 'POST', ... })`
- `axios.post('/api/endpoint', data)`
- `$.ajax({ url: '/api/endpoint', ... })`

### Step 3: Understand Request Format

Once you find API calls, extract the full request body structure:

```bash
# Get the full function that makes the API call
curl -s http://TARGET_URL/js/main.js | grep -B 5 -A 30 'fetch.*\/api\/generate'
```

Look for:
- Request body structure (JSON fields)
- Headers being set
- Error handling patterns
- Response parsing

### Step 4: Test with curl

Use `curl` to test discovered endpoints directly:

```bash
# Basic test
curl -X POST http://TARGET_URL/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}' \
  -v

# With verbose output to see headers
curl -v http://TARGET_URL/api/endpoint

# Capture response headers for tech stack clues
curl -sI http://TARGET_URL/api/endpoint
```

### Step 5: Analyze Responses

Common response patterns:

**Success (200 OK):**
```json
{"imageBase64": "...", "mimeType": "image/png"}
```

**Validation error (400 Bad Request):**
```json
{"error": "Missing required field: prompt"}
```

**Server error (500 Internal Server Error):**
```json
{"error": "{\"error\":{\"code\":400,\"message\":\"API key not valid...\"}}"}
```

**Backend service error:** Often the 500 wraps an upstream error (e.g., Google AI API key invalid). Parse the nested JSON.

## Browser Tool Limitations

### What `browser_console()` CAN do:
- Show JavaScript console output (`console.log`, `console.error`, etc.)
- Detect uncaught exceptions and JS errors
- Execute JavaScript expressions in the page context
- Inject fetch/XHR interceptors (but output may not be captured reliably)

### What `browser_console()` CANNOT do:
- **Show Network tab data** — no passive HTTP request logging
- **Record all API calls** — you must inject interception code
- **Show response bodies** for requests you didn't intercept

### Reliable approach for API inspection:
1. **Terminal-first:** Use `curl` to directly test suspected endpoints
2. **Frontend analysis:** Read JS source to understand request formats
3. **Browser as supplement:** Use `browser_console()` for JS errors and DOM state, not for network traffic

## Common Pitfalls

- **Empty page snapshots after interaction** — the browser tool sometimes returns `(empty page)` after clicks or type. Re-navigate or use `browser_snapshot(full=true)`.
- **Disabled buttons block API calls** — many apps have validation guards. Check for `disabled` attributes or alert dialogs before assuming the API is broken.
- **Nested error responses** — a 500 from the app server often wraps an upstream service error. Always parse the inner JSON to find the real issue.
- **API key errors masquerading as 500** — an internal server error with a message about "API key not valid" means the backend's third-party API key is expired/invalid, not that your request is wrong.
- **CORS issues** — if testing from `curl`, CORS headers won't block the request (curl isn't a browser). But the app's frontend may still fail due to CORS. Check `Access-Control-Allow-Origin` headers.

## Tech Stack Detection

Identify the backend framework from response headers:

| Header | Framework |
|--------|-----------|
| `X-Powered-By: Express` | Node.js / Express |
| `X-Powered-By: Next.js` | Next.js |
| `Server: nginx` | Nginx reverse proxy |
| `X-AspNet-Version` | ASP.NET |
| `X-Generator` | Various CMS/frameworks |

## Reference Files

See `references/api-inspection-checklist.md` for a condensed quick-reference checklist.
