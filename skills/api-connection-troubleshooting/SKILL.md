---
name: api-connection-troubleshooting
description: "Diagnose slow or failing API calls after Hermes upgrades."
tags: [troubleshooting, api, connectivity, hermes]
version: "1.0.0"
created_at: "2026-08-01"
---

# API 连接故障排查指南

当 Hermes Agent 出现 API 调用缓慢、超时或连接失败时，使用本 Skill 进行系统性诊断。

## 核心原则

**不要假设是客户端配置问题**。大多数"升级后变慢"的案例实际上是服务端延迟，而非客户端配置错误。

## 诊断流程

### 1. 验证配置是否正确

```bash
# 检查当前模型配置
hermes config get model

# 确认 api_mode 已显式设置（不应依赖默认值）
hermes config get model.api_mode
```

**关键检查点**：
- `api_mode` 应为 `chat_completions`（除非明确需要 Responses API）
- `base_url` 指向正确的网关
- `skip_provider_detection: true` 防止自动切换

### 2. 测试基础连通性

```bash
# 直接测试 API 端点（绕过 Hermes）
python3 -c "
import urllib.request, json
key = '<YOUR_API_KEY>'
req = urllib.request.Request('https://api.example.com/v1/models')
req.add_header('Authorization', f'Bearer {key}')
import time
start = time.time()
r = urllib.request.urlopen(req, timeout=10)
print(f'连通时间: {time.time()-start:.2f}s')
print(json.loads(r.read()))
"
```

**判断标准**：
- < 1s：服务端正常
- 1-5s：轻微延迟，可能正常
- > 5s：服务端有问题

### 3. 检查 Hermes 日志

```bash
# 查看最近 API 调用延迟
hermes logs | grep "latency="

# 查看超时错误
hermes logs | grep -i "timeout\|timed out"
```

**日志模式识别**：
- `latency=15s cache=...` → 服务端响应慢
- `APITimeoutError` → 请求超时（服务端无响应）
- `HTTP Error 400` → 客户端请求格式问题
- `HTTP Error 401` → 认证问题

### 4. Ping 测试（Windows）

```bash
ping apihub.agnes-ai.com
```

**注意**：ICMP 被拦截不代表 API 不通，但 100% 丢包值得记录。

## 常见误判案例

### 误判 1：认为 api_mode 自动切换

**症状**：升级后 API 调用变慢或失败
**错误归因**：认为客户端自动切换到 `codex_responses` 模式
**实际情况**：
- `api_mode` 已在 config.yaml 显式设置为 `chat_completions`
- OpenAI SDK 2.x 的 `client.beta.responses` 可能不存在
- 检查实际配置而非假设

### 误判 2：认为是 Session 脏数据

**症状**：第二句消息失败，第一句正常
**错误归因**：认为历史消息格式不兼容
**实际情况**：
- 检查 session 数据格式，确认是否有 `output_text` 类型
- 多数情况是服务端间歇性延迟

### 误判 3：忽略服务端延迟

**症状**：API 调用耗时 15-30s
**错误归因**：尝试各种客户端配置调整
**实际情况**：
- 直接测试 API 端点，测量实际延迟
- 检查服务端状态或联系服务商

## 快速诊断脚本

```python
import urllib.request, json, time, os

# 读取 API key
key = ''
with open(r'C:/Users/Administrator/AppData/Local/hermes/.env') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            key = line.strip().split('=',1)[1].strip('"').strip("'")
            break

# 测试连通性
url = 'https://apihub.agnes-ai.com/v1/models'
results = []
for i in range(3):
    start = time.time()
    try:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {key}')
        r = urllib.request.urlopen(req, timeout=30)
        elapsed = time.time() - start
        data = json.loads(r.read())
        results.append(elapsed)
        print(f"Attempt {i+1}: {elapsed:.2f}s - OK ({len(data.get('data', []))} models)")
    except Exception as e:
        elapsed = time.time() - start
        results.append(elapsed)
        print(f"Attempt {i+1}: {elapsed:.2f}s - FAILED: {e}")

if results:
    print(f"\nMin: {min(results):.2f}s, Avg: {sum(results)/len(results):.2f}s, Max: {max(results):.2f}s")
```

## 参考资源

- `references/api-latency-patterns.md` — 常见 API 延迟模式与解决方案
- `references/hermes-config-checklist.md` — Hermes 配置检查清单
