---
name: dws-cli-troubleshooting
description: |
  钉钉 DWS CLI 故障排查与升级指南。当 dws upgrade 失败、命令识别异常、版本不一致或网络调用报错时使用。
tags: [dws, dingtalk, cli, troubleshooting]
requires:
  - commands: [dws, curl, npm]
  - env_vars: []
version: "1.0.0"
created_at: "2026-07-26"
last_tested_at: "2026-07-26"
---

# DWS CLI 故障排查与升级

## 升级失败处理

### 症状
`dws upgrade -y` 报 `下载二进制失败`、`connection attempt failed` 或 `read tcp ... timeout`。

### 诊断顺序

1. **确认代理环境变量是否干扰**
   ```bash
   echo $HTTPS_PROXY; echo $HTTP_PROXY; echo $ALL_PROXY
   ```
   若代理端口拒绝连接（如 9872），先 unset 再重试，或直接绕过。

2. **测试 GitHub 直连**
   ```bash
   curl --noproxy "*" -sI "https://api.github.com/repos/DingTalk-Real-AI/dingtalk-workspace-cli/releases/latest"
   ```
   - 返回 200 → 直连通，可能只是临时波动
   - 返回非 200 → 网络确实不通，见下方回退方案

3. **确认安装方式**
   ```bash
   where dws    # Windows cmd/powershell
   which dws    # bash/msys
   ```
   输出路径包含 `node_modules/dingtalk-workspace-cli/bin/dws.js` → **npm 安装**
   独立 zip/binary → 标准 CLI 安装

### 推荐回退方案（npm 安装时）— 首选

当 `dws upgrade -y` 因 GitHub Release 下载失败、`connectex: No connection could be made`、`read tcp ... timeout` 时：

```bash
# 0. 清除代理环境变量干扰（必须！）
unset HTTPS_PROXY HTTP_PROXY ALL_PROXY

# 1. 通过 npm registry 升级（比 GitHub 下载稳定得多）
npm update dingtalk-workspace-cli -g

# 2. 确认新版本并验证
dws --version
dws doctor
```

> 原理：`dws upgrade` 内部依赖 GitHub Release 二进制下载，Windows 环境下极不稳定；`npm update` 走 npm registry，穿透力强。

## 已验证版本信息

| 版本 | 日期 | 备注 |
|------|------|------|
| v1.0.41 | — | 初版，用户环境 |
| v1.0.54 | 2026-07-21 | 最新稳定版（npm 安装），包含 `dws dev/audit/event/profile/skill/pat/agoal` 等新命令 |

## 新命令速查（v1.0.41→v1.0.54）


## 命令识别异常

### 现象
`dws <product> <subcommand> --help` 显示的是旧版 help 或报 `unknown command`。

### 原因
本地 `dws` skill 文档可能落后于 npm 发布的 CLI 版本。新版增加了 `agoal`、`audit`、`event`、`profile`、`skill`、`dev`、`pat` 等命令，但本地 skill 索引未同步。

### 处理
- **以 `dws --help` 和 `dws <cmd> --help` 为准**，不要硬编码 product 列表
- `dws schema` 可动态拉取当前 MCP 注册的工具清单
- npm registry 显示的最新版本号（`npm view dingtalk-workspace-cli version`）是事实源

## 常见网络问题

| 场景 | 症状 | 处理 |
|------|------|------|
| VPN 代理端口断开 | `connectex: No connection could be made` | `unset HTTP_PROXY HTTPS_PROXY; npm update ... -g` |
| GitHub DNS 污染 | `curl --noproxy *` 连 API 200，但 release 下载超时 | 用 npm 升级替代 GitHub 下载 |
| macOS keychain 认证 | `dws auth login` 卡在浏览器或报错 | `dws auth reset && dws auth login` |

## 快速健康检查流程

```bash
dws --version          # 确认版本
dws doctor             # 环境健康检查
dws contact user me --format json  # 端到端调用测试
```

## 相关资源
- 官方 changelog: `https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/releases`（可用 `curl` 拉取）
- `dws --help` / `dws schema` — 以运行时实际注册的能力为准