# Session Example: Amazon Listing 批量生图 (2026-06-28)

## App Details

- **URL**: `http://47.99.165.14:3000/`
- **Title**: "Amazon Listing 批量生图" — "Listing & A+ 图片自动生成"
- **Purpose**: Bulk image generation for Amazon product listings (A+ content, main images, white background refinement)

## Discovery Process

### 1. Browser Tool Limitations

Clicked "✨ 开始生成" button and filled form fields (brand: "TestBrand", product: "Test Product"). The button click produced:
- No visible UI state change (still showed "等待生成" / "waiting to generate")
- Empty console output
- No DOM changes detectable via snapshot

This confirmed the browser tool cannot show Network tab data.

### 2. Curl Probing

**First attempt** — guessed endpoint `/api/generate`:
```bash
curl -X POST http://47.99.165.14:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"brandName":"Test","productName":"Test Product","targetMarket":"US","productType":"frame"}' \
  -v
```
Result: `400 Bad Request` — `{"error":"缺少 prompt 参数"}` (missing prompt parameter)

**Second attempt** — with prompt:
```bash
curl -X POST http://47.99.165.14:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Generate an Amazon product image for a wooden picture frame"}' \
  -v
```
Result: `500 Internal Server Error` — nested error from Google Generative Language API:
```json
{
  "error": {
    "code": 400,
    "message": "API key not valid. Please pass a valid API key.",
    "status": "INVALID_ARGUMENT",
    "details": [{
      "reason": "API_KEY_INVALID",
      "domain": "googleapis.com",
      "service": "generativelanguage.googleapis.com"
    }]
  }
}
```

## Findings

| Aspect | Detail |
|--------|--------|
| Backend framework | Express.js (`X-Powered-By: Express`) |
| API endpoint | `POST /api/generate` |
| Content type | `application/json` |
| Downstream AI service | Google Generative Language API (`generativelanguage.googleapis.com`) |
| Root cause | Invalid/missing Google API key on the server |
| Required param | `prompt` (string) |

## Key Takeaway

The frontend click produced no visible reaction because the backend API call was failing server-side (invalid API key). The browser console showed no errors because the failure happened server-side, not client-side. Using curl revealed the actual error chain: Express → Google API → INVALID_ARGUMENT.
