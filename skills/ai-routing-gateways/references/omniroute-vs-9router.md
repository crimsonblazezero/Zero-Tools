# OmniRoute vs 9Router 详细对比

## 基础信息

| 维度 | OmniRoute | 9Router |
|------|-----------|---------|
| GitHub | diegosouzapw/OmniRoute | decolua/9router |
| Stars | 36,700 | 24,300 |
| Forks | 4,700 | 4,200 |
| 贡献者 | 500+ | 少量 |
| 语言 | TypeScript | JavaScript |
| 最新提交 | 2026-08-01 (8分钟前) | 2026-07-30 (3天前) |
| 总提交数 | 5,941 | 1,020 |
| 版本标签 | 313 | 78 |
| 当前版本 | v3.8.50 | v0.5.45 |
| 许可证 | MIT | MIT |

## 功能对比

### 提供商与模型

| 功能 | OmniRoute | 9Router |
|------|-----------|---------|
| 总提供商数 | 290+ | 40+ |
| 免费提供商 | 90+ | 少量 |
| 模型总数 | 500+ | 100+ |
| 免费月Token | ~1.53B | 未公开 |
| 提供商池 | 43个 | 未明确 |

**OmniRoute 独家提供商**: Kimi (K2/K3), Z.AI GLM-Flash, Kilo, OpenCode Zen, Baidu, DeepSeek (免费层), xAI Grok

**9Router 独家提供商**: Poolside (OpenAI兼容)

### Token压缩

| 功能 | OmniRoute | 9Router |
|------|-----------|---------|
| RTK | ✅ | ✅ |
| Caveman | ✅ | ❌ |
| 压缩率 | 15-95% (平均89%) | 20-40% |
| 压缩引擎数 | 12 | 1 |
| 多语言支持 | DE/FR/JA/中文(文言) | 无 |
| 格式感知 | 代码/URL/JSON保真 | 基础 |

**OmniRoute 额外压缩引擎**:
- LLMLingua-2
- Ultra (两阶段)
- OmniGlyph
- GCF v3.2
- Session-Dedup
- CCR (Cross-Context Redundancy)
- Lite
- Responses Tool Output
- Headroom
- Relevance
- Aggressive

### 路由策略

| 策略 | OmniRoute | 9Router |
|------|-----------|---------|
| 总策略数 | 19 | 3 |
| auto | ✅ | ✅ |
| auto/cheap | ✅ | ❌ |
| auto/offline | ✅ | ❌ |
| auto/smart | ✅ | ❌ |
| Fusion (多模型+裁判) | ✅ | ❌ |
| Quota-Share (配额共享) | ✅ | ❌ |
| Round-Robin (多账户) | ✅ | ✅ |

### 高级功能

| 功能 | OmniRoute | 9Router |
|------|-----------|---------|
| MCP Server | ✅ 104工具 | ❌ |
| A2A协议 | ✅ | ❌ |
| 持久记忆 | ✅ | ❌ |
| Guardrails | ✅ 注入防护 | ❌ |
| TLS隐身 | ✅ | ❌ |
| MITM解密 | ✅ TPROXY模式 | ❌ |
| Dashboard | ✅ 实时分析 | ✅ 基础 |
| 成本遥测 | ✅ $0订阅显示 | ✅ 估算 |
| 多云部署 | ✅ Desktop/PWA/Termux | ❌ |

### 安全特性

| 特性 | OmniRoute | 9Router |
|------|-----------|---------|
| 凭证掩码 | ✅ | ❌ |
| Prompt注入防护 | ✅ | ❌ |
| OIDC登录门 | ✅ (可选) | ❌ |
| AES-256-GCM密钥加密 | ✅ | ❌ |
| 本地优先 | ✅ | ❌ |

## Hermes Agent 集成

### OmniRoute 支持

- ✅ 官方文档明确列出 Hermes Agent
- ✅ 预配置 `setup-hermes` 命令
- ✅ 零配置启动即可用
- ✅ 支持 `/goal` 模式下的 token 路由

### 9Router 支持

- ❌ 未明确提及 Hermes
- ⚠️ 兼容任何 OpenAI 兼容端点
- ⚠️ 需手动配置 endpoint

## 部署方式

| 方式 | OmniRoute | 9Router |
|------|-----------|---------|
| npm全局 | ✅ | ✅ |
| Docker | ✅ | ✅ |
| Electron Desktop | ✅ | ❌ |
| PWA | ✅ | ❌ |
| Termux (Android) | ✅ | ❌ |
| Cloudflare Workers | ✅ | ❌ |
| Deno Deploy | ✅ | ❌ |

## 社区与维护

| 指标 | OmniRoute | 9Router |
|------|-----------|---------|
| Discord | ✅ 活跃 | ✅ |
| Telegram | ✅ | ✅ |
| WhatsApp | ✅ 全球+巴西 | ❌ |
| 网站 | ✅ omniroute.online | ✅ 9router.com |
| 更新频率 | 每日 | 每周 |
| PR响应 | 快 (500+贡献者) | 中等 |

## 适用场景

### 选择 OmniRoute 当：

1. 使用 Hermes Agent — 官方支持，零配置
2. 需要 MCP/A2A 集成 — 104工具内置
3. 重度工具调用场景 — 15-95% token压缩
4. 多提供商容错 — 290+提供商，19种路由
5. 生产环境 — Circuit breaker, guardrails, TLS隐身

### 选择 9Router 当：

1. 只需要简单降级 — 更轻量
2. 不想管理复杂配置 — 更简单
3. 已有固定提供商组合 — 40+够用
4. 资源受限环境 — 无Desktop/PWA依赖

## 关键数字

- **OmniRoute 免费Token**: ~1.53B/月 (43池/516模型)
- **OmniRoute 压缩节省**: 平均89%, 最高95%
- **OmniRoute 提供商**: 290+, 90+免费
- **9Router 压缩节省**: 20-40%
- **9Router 提供商**: 40+

## 配置示例

### OmniRoute (推荐)

```bash
# 安装
npm install -g omniroute

# 启动
omniroute

# 访问 Dashboard
http://localhost:20128/dashboard

# 配置 Hermes
/model custom:omniroute
```

### 9Router

```bash
# 安装
npm install -g 9router

# 启动
9router

# 访问 Dashboard
http://localhost:20128/dashboard

# 配置工具
Endpoint: http://localhost:20128/v1
Model: kr/claude-sonnet-4.5
```

## 总结

| 维度 | OmniRoute | 9Router | 建议 |
|------|-----------|---------|------|
| 功能丰富度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | OmniRoute |
| 易用性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 平手 |
| Hermes集成 | ⭐⭐⭐⭐⭐ | ⭐⭐ | OmniRoute |
| Token压缩 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | OmniRoute |
| 社区活跃 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | OmniRoute |
| 轻量级 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 9Router |
| 生产就绪 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | OmniRoute |

**最终建议**: 优先 OmniRoute，9Router 作为轻量备用。
