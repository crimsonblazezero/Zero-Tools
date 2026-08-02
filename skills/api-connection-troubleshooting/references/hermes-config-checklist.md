# Hermes 配置检查清单

## 基础配置

```bash
# 1. 检查模型配置
hermes config get model

# 期望输出：
# default: <model_name>
# provider: <provider_name>
# base_url: https://...
# api_mode: chat_completions  # 显式设置，非默认
# skip_provider_detection: true
```

## 认证检查

```bash
# 2. 检查 API key 是否设置
hermes config show | grep -A 5 "API Keys"

# 3. 测试认证
curl -H "Authorization: Bearer <key>" https://api.example.com/v1/models
```

## MCP 连接检查

```bash
# 4. 检查 MCP 服务器状态
hermes mcp list

# 5. 测试连接
hermes mcp test <server_name>
```

## 会话数据检查

```bash
# 6. 查看最近会话
hermes sessions list

# 7. 检查是否有异常消息格式（需要自定义脚本）
```

## 日志检查

```bash
# 8. 查看最近错误
hermes logs | grep -i "error\|failed\|timeout" | tail -20

# 9. 查看 API 调用延迟
hermes logs | grep "latency=" | tail -10
```

## 快速修复命令

```bash
# 重启 gateway（配置变更后）
hermes gateway restart

# 清除会话缓存
hermes sessions prune

# 重新加载 MCP
hermes mcp reload
```