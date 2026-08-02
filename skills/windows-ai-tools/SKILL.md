---
name: windows-ai-tools
description: "管理 Hermes/Antigravity/WorkBuddy 配置和目录结构，Windows 环境。"
---

# Windows AI Tools Configuration

管理 Windows 环境下的 AI 工具配置和目录结构。

## 核心目录

### 共享基准目录
```
D:/AgentSystem/
├── shared_skills/        # 技能副本（473MB，可能冗余）
├── workbuddy-config/     # WorkBuddy 配置源（被 .workbuddy/ 引用）
├── AppData_Local_hermes/ # Hermes 备份
└── AppData_Roaming_Hermes/
```

### 用户目录
```
~/AppData/Local/hermes/    # Hermes 实际数据
├── config.yaml
├── memories/
└── skills/ -> /d/Zero Tools/skills  # symlink

~/.hermes/                 # Hermes 独立配置
~/.gemini/                 # Gemini/Antigravity 配置
~/.workbuddy/              # WorkBuddy 配置（symlink）
```

### 主要仓库
- `D:/Zero Tools/` - 主要技能仓库（220MB）
- `~/Desktop/ai-sync/` - 配置同步仓库

## Symlink 管理

```bash
# 检查 symlink
readlink ~/.hermes/skills
readlink ~/.workbuddy

# 创建 symlink
ln -s /d/Zero\ Tools/skills ~/AppData/Local/hermes/skills
```

## 配置同步

使用 `ai-sync` skill 同步配置。

## 冗余清理

可安全清理：
- `/d/AgentSystem/shared_skills/` (473MB)
- `/d/AgentSystem/.codex/.tmp/plugins/`
- `/d/AgentSystem/AppData_Local_hermes/hermes-agent/`