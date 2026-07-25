# Debugging "Unexpected message role" Errors

## Pattern: CC Switch + Codex Integration

### Symptoms
- Codex connects to CC Switch proxy successfully
- Sending messages returns: `BadRequestError: OpenAIException - {"error":{"message":"Unexpected message role.",...}}`
- Or: `Invalid user message at index N. Please ensure all user messages are valid OpenAI chat completion messages`

### Root Cause Chain

1. **Codex uses Responses API format internally**:
   ```json
   {
     "role": "developer",
     "content": [{"type": "input_text", "text": "..."}]
   }
   ```

2. **CC Switch configured for `openai_chat`** but conversion logic doesn't handle:
   - `developer` → `system` role mapping
   - `content: [...]` → `content: "..."` array-to-string conversion

3. **Upstream API rejects the unconverted format**

### Debugging Steps

#### Step 1: Check CC Switch proxy is running
```bash
netstat -ano | findstr 15721
# Should show: TCP 127.0.0.1:15721 LISTENING <PID>
```

#### Step 2: Check current provider configuration
```python
import sqlite3, json

db_path = "~/.cc-switch/cc-switch.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, meta, settings_config 
    FROM providers WHERE app_type = 'codex' AND is_current = 1
""")
row = cursor.fetchone()
meta = json.loads(row[2])
settings = json.loads(row[3])

print(f"Provider: {row[1]}")
print(f"API Format: {meta.get('apiFormat')}")
print(f"wire_api: {settings.get('config', '')}")
```

#### Step 3: Check Codex session logs for actual message format
```python
import json

session_file = "~/.codex/sessions/2026/06/27/*.jsonl"
with open(session_file, 'r') as f:
    for line in f:
        data = json.loads(line.strip())
        if data.get('type') == 'response_item':
            role = data['payload'].get('role')
            print(f"Role: {role}")
```

#### Step 4: Test direct API call through proxy
```python
import urllib.request, json

test_request = {
    "model": "your-model",
    "messages": [
        {"role": "system", "content": "You are helpful."},
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

### Fixes

#### Fix A: Use Chat Completions mode (Recommended for most upstream APIs)
Change Codex's `wire_api` from `"responses"` to `"chat_completions"`:
```
wire_api = "chat_completions"
```

#### Fix B: Use Responses mode (If upstream supports it)
Set `apiFormat` to `"openai_responses"` in provider meta and ensure upstream accepts Responses API format.

#### Fix C: Ensure CC Switch is converting properly
- Verify `apiFormat: "openai_chat"` in provider meta
- Check that CC Switch version supports the conversion (may need update)

### Prevention Checklist

- [ ] CC Switch proxy is running on expected port
- [ ] Provider `apiFormat` matches upstream API capabilities
- [ ] Codex `wire_api` matches the intended format
- [ ] Test with a simple request before full integration
- [ ] Check `proxy_request_logs` table for error details
