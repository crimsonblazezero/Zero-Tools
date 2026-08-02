---
name: ai-routing-gateways
description: AI路由网关对比与选型指南。当用户需要配置备用token方案、降低成本、避免rate limit时使用。涵盖OmniRoute、9Router、LiteLLM等主流方案对比。
---

# AI Routing Gateways Skill

当用户遇到以下场景时触发：
- 需要备用AI token方案
- 想避免API配额耗尽
- 想降低成本（免费/低价提供商）
- 需要自动降级路由
- Hermes Agent token超限时找替代方案

## 主流方案对比

| 方案 | Stars | 提供商数 | 免费数 | Token压缩 | MCP支持 | Hermes支持 | 推荐度 |
|------|-------|---------|--------|-----------|---------|------------|--------|
| **OmniRoute** | 36.7k | 290+ | 90+ | 15-95% | ✅ 104工具 | ✅ 官方 | ⭐⭐⭐⭐⭐ |
| **9Router** | 24.3k | 40+ | 少量 | 20-40% | ❌ | ❌ | ⭐⭐⭐ |
| **LiteLLM** | 15k+ | 100+ | 视配置 | 无 | ❌ | ❌ | ⭐⭐⭐ |
| **OpenRouter** | 商业 | 100+ | 无 | 无 | ❌ | ❌ | ⭐⭐ |

## 推荐：OmniRoute

### 核心优势
- **Hermes Agent 官方支持** — 文档明确列出
- **4层自动降级** — 订阅 → API → 低价 → 免费
- **19种路由策略** — cheapest, offline, smart, fusion等
- **RTK + Caveman双引擎压缩** — 平均节省89% token
- **104个MCP工具** — 内置代理能力
- **500+贡献者** — 活跃维护

### 快速上手

```bash
# 安装
npm install -g omniroute

# 启动（零配置，免费提供商预配置）
omniroute

# 配置 Hermes Agent
# Endpoint: http://localhost:20128/v1
# Model: auto
```

### Hermes 集成配置

在 `~/.hermes/config.yaml` 中添加：

```yaml
model:
  custom:
    - name: omniroute
      base_url: http://localhost:20128/v1
      api_key: [从dashboard复制]
```

或会话内切换：
```
/model custom:omniroute
```

## 决策树

```
需要备用token方案？
├── 是，需要Hermes深度集成 → OmniRoute
├── 是，只需要简单降级 → 9Router
├── 是，已有API key → LiteLLM
└── 否，想省钱 → 查看免费提供商列表
```

## 何时使用

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| Hermes token超限 | OmniRoute | 官方支持，零配置 |
| 多工具并行开发 | OmniRoute | 19路由策略，104MCP工具 |
| 简单备用 | 9Router | 更轻量，配置简单 |
| 已有付费订阅 | LiteLLM | 管理多key，成本透明 |
| 不想自建 | OpenRouter | 现成服务，但收费 |

## 关键指标解读

- **RTK (Real-Time Knowledge)**: 智能工具输出过滤，压缩git diff/grep结果
- **Caveman**: 压缩算法，牺牲少量质量换取大幅token节省
- **Auto-Combo**: 自动组合多个提供商，按配额/成本/延迟动态选择
- **Circuit Breaker**: 故障自动切换，避免单个提供商失败

## 参考资料

- [OmniRoute GitHub](https://github.com/diegosouzapw/OmniRoute)
- [9Router GitHub](https://github.com/decolua/9router)
- [详细对比报告](references/omniroute-vs-9router.md)
