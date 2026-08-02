---
name: ai-sync
description: "跨设备同步 Hermes/Antigravity 配置和记忆。当用户提到同步、跨电脑、两边配置一致时使用。"
---

# AI Tools Config Sync

同步 Hermes, Antigravity, WorkBuddy 的配置和记忆数据。

## 仓库

- 本地: `~/Desktop/ai-sync/`
- 远程: `git@github.com:crimsonblazezero/ai-sync.git`

## 结构

```
hermes/
├── config.yaml          # Hermes 配置
├── SOUL.md              # 系统提示词
└── memories/
    ├── MEMORY.md        # 长期记忆
    └── USER.md          # 用户信息
antigravity/
├── settings.json        # IDE 设置
└── app_storage.json     # 会话状态
```

## 使用

```bash
# 推送到 GitHub
bash ~/Desktop/ai-sync/ai-sync.sh push

# 从 GitHub 拉取
bash ~/Desktop/ai-sync/ai-sync.sh pull

# 查看状态
bash ~/Desktop/ai-sync/ai-sync.sh status
```

## 自动同步

```bash
# 每小时同步
0 * * * * bash ~/Desktop/ai-sync/ai-sync.sh pull >> ~/Desktop/ai-sync/sync.log 2>&1
```

## 注意事项

- WorkBuddy 无本地配置，无需同步
- memories 包含敏感信息，仅同步到私有仓库
- 冲突时以 GitHub 为准