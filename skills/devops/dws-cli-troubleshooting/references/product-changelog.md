# v1.0.41 → v1.0.54 新增能力速查

此文件记录 2026-06-24（v1.0.41）至 2026-07-21（v1.0.54 稳定版）之间的主要变更，供排查「命令不存在」或升级相关问题时快速查阅。

## v1.0.42（2026-06-25）— devapp / connect / pat

- **`devapp`（后续更名为 `dev`）** — 开放平台开发者工具集初版
  - `robot connect` — 机器人桥接/连接配置
  - AI-card 回复、模板自定义、会话记忆
  - Digital employee / twin 确认策略、角色权限、后台执行
  - Opencode / Qoder 会话持久化
- **`pat`** — 行为授权管理基础命令
  - `pat chmod` 批量授权、agent-code 支持、chmod 输出摘要
- **Windows 安装** — `install-devapp.sh` 适配 Windows (ps1)
- Gitee 镜像自动降级（GitHub 不可达时）

## v1.0.43（2026-06-26）— 发现与文档

- 对齐 Open CLI 与 Wukong（通过 discovery version code）
- `devdoc article search` 游标分页
- 删除 devapp fork，指向官方仓库

## v1.0.44（2026-06-29）

- **Phantom guard** — 隐藏不存在的 override 命令
- **`@file` / `--contents-file`** — 结构化 JSON flag 的本地文件输入
- **Sheet parity** — range read/update 与 Wukong 对齐
- 日志 `report create --contents-file` 支持

## v1.0.45（2026-06-29）

- **多 profile 登录** — `dws auth login` 支持多个组织/账号
- **Chat AI badge** — 默认 `--ai-tag`，AI 发送的消息带 AI 标识

## v1.0.46（2026-07-01）— PAT 修复

- `pat chmod` agent code grant 对齐修复

## v1.0.47（2026-07-05）— Connector + Bot @mention

- Connector supervision
- Bot-to-bot `@` mention

## v1.0.48–49（2026-07-07）— QA + Release 修复

- Schema-on-main 发布流程验证
- 6 产品 QA 优化：CLI、脚本、技能文档全量修正

## v1.0.50（2026-07-08）— JQ / 导出合并

- 全局 `--jq` / `--fields` 覆盖产品命令
- `dws api` export 合并 helper
- Round-2 QA 修复

## v1.0.51（2026-07-10）— Connect 稳定性

- Agent mid-turn blocking 修复
- PAT chmod grants permanent default
- macOS keychain 诊断与修复

## v1.0.52（2026-07-15）⭐ 重要版本

- **`event` 产品** 🆕 — 个人级 IM 事件订阅（@我、单聊、群聊）
  - `event list/schema/consume/status/stop`
  - 消息已读、撤回、表情回应事件
  - 个人订阅 vs 企业订阅
- **Personal audit log** 🆕 — `audit` 产品操作审计日志查询
- **Open product commands** 🆕
  - Sheet: pivot-table / gridline
  - Chat: `me` / group 相关增强
- **macOS credentials** 安全加固
- Agent command catalog 确定性：22 个产品

## v1.0.53-beta 系列（2026-07-16~21）— Shortcut / IM 扩展

- **Shortcut 功能** — AI 快捷指令
- **IM 扩展事件订阅** (#651)
  - 一对一/群消息已读、撤回、表情回应
  - 指定发送者接收事件
  - 可订阅 staff `--user` 或 `--open-dingtalk-id`
- **Personal event 输出结构化** (#651)
  - `event consume` 输出扁平化为事件级 DTO
- **Guarded release** 流程加速
- npm dist-tag eventual consistency 容错

## v1.0.54（2026-07-21）稳定版 ⭐

### Changed
- **Personal event output compatibility** (#743)
  - `event consume` 恢复默认保留 transport envelope
  - `--flatten` opt-in 开启事件级顶层 DTO
  - 与 `-f raw` / `--debug-raw-events` 互斥

### Fixed
- **Schema CLI path compatibility** (#738)
  - Space、dot、slash 分隔的 CLI 路径都能正确解析
- **Plugin CLI overlays** (#701)
  - 安装的插件能正确注册 overlay 命令

---

> 当前最新版本可能已超出本文档范围。始终用 `npm view dingtalk-workspace-cli version` 和 `dws --version` 核对实际版本。完整历史见官方 releases：
> https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/releases
