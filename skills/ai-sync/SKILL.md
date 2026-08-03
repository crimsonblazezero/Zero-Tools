---
name: ai-sync
description: AI Tools 端到端同步工作流，同步 Hermes 配置、记忆、技能和 Python 文件到 GitHub。
category: devops
---

# AI Tools 端到端同步工作流

## 触发条件
- 用户需要同步配置和技能到 GitHub
- 用户切换设备后需要同步 Hermes/Antigravity 配置
- 用户需要备份或恢复技能
- 用户想推送本地更改到远程仓库

## 同步架构

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub (远程仓库)                         │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ ai-sync         │    │ Zero-Tools      │                │
│  │ (配置 + 记忆)    │    │ (技能 + 脚本)    │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
          ▲                        ▲
          │                        │
     ~/Desktop/ai-sync/    D:/Zero Tools/
          │                        │
          └────────┬───────────────┘
                   │
          symlink  │
                   │
      ~/AppData/Local/hermes/skills/
```

## 仓库结构

### 1. ai-sync 仓库
- **路径**: `~/Desktop/ai-sync/`
- **远程**: `crimsonblazezero/ai-sync`
- **用途**: 同步 Hermes 配置和记忆数据
- **内容**:
  - `hermes/config.yaml` - Hermes 配置
  - `hermes/SOUL.md` - Hermes 人格定义
  - `MEMORY.md` - 持久记忆
  - `USER.md` - 用户信息
  - `sync-config.sh` - 配置同步脚本
  - `sync-skills.sh` - 技能同步脚本
  - `sync-all.sh` - 一键同步脚本

### 2. Zero-Tools 仓库
- **路径**: `D:/Zero Tools/`
- **远程**: `crimsonblazezero/Zero-Tools`
- **用途**: 同步技能和 Python 脚本
- **内容**:
  - `skills/` - 126 个 Hermes 技能
  - `src/` - Python 脚本
  - `docs/` - 文档
  - symlink: `~/AppData/Local/hermes/skills/` → `D:/Zero Tools/skills/`

### 3. workbuddy-config 仓库
- **路径**: `/d/AgentSystem/workbuddy-config/`
- **远程**: 无（本地使用）
- **用途**: WorkBuddy 配置源
- **symlink**: `.workbuddy/` → `workbuddy-config/`

## 使用方法

### 快速开始

```bash
# 查看同步状态
bash ~/Desktop/ai-sync/sync-all.sh status

# 拉取配置和记忆（从 GitHub 同步到本地）
bash ~/Desktop/ai-sync/sync-config.sh pull

# 推送配置和记忆（从本地同步到 GitHub）
bash ~/Desktop/ai-sync/sync-config.sh push

# 拉取技能（从 GitHub 同步到 Zero-Tools）
bash ~/Desktop/ai-sync/sync-skills.sh pull

# 推送技能（从本地同步到 GitHub）
bash ~/Desktop/ai-sync/sync-skills.sh push

# 一键同步所有（配置 + 技能）
bash ~/Desktop/ai-sync/sync-all.sh pull
bash ~/Desktop/ai-sync/sync-all.sh push
```

### 详细操作

#### 1. 同步配置和记忆

```bash
cd ~/Desktop/ai-sync

# 拉取（远程 → 本地）
bash sync-config.sh pull

# 推送（本地 → 远程）
bash sync-config.sh push
```

**覆盖范围**:
- `~/AppData/Local/hermes/config.yaml`
- `~/AppData/Local/hermes/SOUL.md`
- `MEMORY.md`
- `USER.md`

#### 2. 同步技能

```bash
cd ~/Desktop/ai-sync

# 拉取（远程 → Zero-Tools）
bash sync-skills.sh pull

# 推送（Zero-Tools → 远程）
bash sync-skills.sh push
```

**覆盖范围**:
- `D:/Zero Tools/skills/`
- `D:/Zero Tools/src/`
- `D:/Zero Tools/docs/`

#### 3. 一键同步

```bash
# 一键拉取（配置 + 技能）
bash ~/Desktop/ai-sync/sync-all.sh pull

# 一键推送（配置 + 技能）
bash ~/Desktop/ai-sync/sync-all.sh push

# 查看状态
bash ~/Desktop/ai-sync/sync-all.sh status
```

## 注意事项

### 路径兼容
脚本已适配 Windows/MSYS2 环境，使用 `cygpath` 转换路径。

### 冲突处理
- 推送前会检查本地是否有未提交的更改
- 如果有本地更改，会先 commit 再 push
- 拉取前会检查是否有本地未提交的更改

### 备份策略
- 每次推送前会自动创建备份
- 备份保存在 `backups/` 目录
- 备份命名格式: `backup-YYYYMMDD-HHMMSS`

### 权限要求
- 需要 SSH 访问 GitHub 的权限
- 需要写入 `~/AppData/Local/hermes/` 的权限
- 需要写入 `D:/Zero Tools/` 的权限

## 故障排查

### 问题 1: SSH 连接失败
```bash
# 检查 SSH 状态
gh auth status

# 重新认证
gh auth login
```

### 问题 2: 路径转换错误
脚本已内置 `cygpath` 转换，如果仍有问题，检查：
- Git Bash 是否安装
- MSYS2 路径是否正确

### 问题 3: 权限不足
```bash
# 检查 Hermes 目录权限
ls -la ~/AppData/Local/hermes/

# 检查 Zero-Tools 目录权限
ls -la "D:/Zero Tools/"
```

### 问题 4: 技能数不一致
```bash
# 检查本地技能数
ls ~/AppData/Local/hermes/skills/ | wc -l

# 检查远程技能数
cd ~/Desktop/ai-sync && bash sync-skills.sh status
```

## 相关命令

### 手动同步
```bash
# 只同步配置
cd ~/Desktop/ai-sync && git pull && bash sync-config.sh pull

# 只同步技能
cd "D:/Zero Tools" && git pull

# 只推送配置
cd ~/Desktop/ai-sync && bash sync-config.sh push && git push

# 只推送技能
cd "D:/Zero Tools" && git add -A && git commit -m "sync skills" && git push
```

### 查看日志
```bash
# 查看同步日志
cat ~/Desktop/ai-sync/logs/sync-$(date +%Y%m%d).log

# 查看 Git 日志
cd ~/Desktop/ai-sync && git log --oneline -5
cd "D:/Zero Tools" && git log --oneline -5
```

## 更新记录

- 2026-08-02: 初始版本，创建同步脚本
- 2026-08-02: 修复 Windows/MSYS2 路径问题
