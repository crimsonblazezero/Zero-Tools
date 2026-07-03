# Skills 文件夹清理指南
# Skills Folders Cleanup Guide

---

## 📊 当前状态分析 / Current Status Analysis

### 发现的 Skills 文件夹 / Found Skills Folders

| 路径 / Path                                 | 数量 / Count | 类型 / Type   | 建议 / Recommendation |
| ------------------------------------------- | ------------ | ------------- | --------------------- |
| `C:\Users\china\.agent\skills`              | 18           | 功能性 Skills | ✅ **保留（主要）**    |
| `C:\Users\china\.gemini\antigravity\skills` | 18           | 重复备份      | ❌ **删除**            |
| `C:\Users\china\superpowers\skills`         | 14           | 工作流 Skills | ⚠️ **建议保留**        |

---

## 🎯 清理建议 / Cleanup Recommendations

### ✅ **保留的文件夹 / Keep These**

#### 1. `C:\Users\china\.agent\skills` - **主要 Skills 库**
- **原因：** 这是 Antigravity 的标准全局 Skills 位置
- **内容：** 18 个功能性 Skills（设计、文档、开发等）
- **用途：** 日常工作中使用的所有 Skills

#### 2. `C:\Users\china\superpowers\` - **Superpowers 完整项目** ⭐
- **⚠️ 重要：** 这是一个**完整的 Git 项目**，不只是 skills 文件夹！
- **原因：** 包含完整的开发工作流系统
- **项目作者：** obra (Jesse)
- **完整结构：**
  - `skills/` - 14 个工作流 Skills
  - `commands/` - 命令定义
  - `lib/` - 核心库文件 (skills-core.js)
  - `hooks/` - 钩子脚本
  - `tests/` - 测试文件
  - `agents/` - Agent 配置
  - `.claude-plugin/` - Claude 插件配置
  - 其他项目文件
- **Skills 包含：**
  - `brainstorming` - 头脑风暴方法
  - `systematic-debugging` - 系统化调试
  - `test-driven-development` - TDD 开发
  - `executing-plans` - 执行计划
  - `subagent-driven-development` - 子代理开发
  - `code-review` - 代码审查流程
  - 等等...
- **用途：** 指导 AI 如何更好地工作（工作流方法论）
- **类型：** 工作流指导（教 AI 如何工作）
- **❌ 不要拆分：** 必须保留整个项目，skills 依赖其他文件
- **✅ 可以更新：** 通过 `git pull` 更新整个项目

---

### ❌ **删除的文件夹 / Delete This**

#### `C:\Users\china\.gemini\antigravity\skills` - **重复备份**
- **原因：** 与 `.agent\skills` 完全相同（100% 重复）
- **大小：** 约 0.2 MB
- **状态：** 可以安全删除

---

## 🗑️ 删除方法 / Deletion Methods

### 方法 1：使用删除脚本（推荐）⭐

```powershell
# 运行删除脚本
powershell -ExecutionPolicy Bypass -File .\scripts\delete-duplicate-skills.ps1
```

**脚本会：**
1. 显示文件夹大小
2. 要求你输入 'YES' 确认
3. 尝试解锁并删除文件
4. 显示删除结果

**如果失败：**
- 脚本会提示具体错误
- 提供解决方案

---

### 方法 2：手动删除（最安全）⭐⭐⭐

#### 步骤：

1. **关闭 Antigravity**
   - 完全退出应用程序
   - 确保所有进程都已关闭

2. **打开文件夹**
   ```powershell
   explorer C:\Users\china\.gemini\antigravity
   ```

3. **删除 `skills` 文件夹**
   - 右键点击 `skills` 文件夹
   - 选择"删除"
   - 确认删除

4. **重新启动 Antigravity**
   - 正常启动应用
   - 验证功能正常

---

### 方法 3：命令行强制删除

```powershell
# 如果 Antigravity 已关闭，可以直接运行
Remove-Item "C:\Users\china\.gemini\antigravity\skills" -Recurse -Force
```

**注意：** 如果文件被占用，这个命令会失败。

---

## ⚠️ 重要提示 / Important Notes

### 为什么文件被占用？
- Antigravity 可能正在读取这些文件
- `superpowers-main.zip` 可能被某个进程锁定
- 系统索引服务可能正在扫描

### 安全性确认
- ✅ 删除 `.gemini\antigravity\skills` **不会影响**主要 Skills
- ✅ 主要 Skills 在 `C:\Users\china\.agent\skills`
- ✅ 删除后 Antigravity 仍然正常工作

---

## 🔍 删除前验证 / Pre-Deletion Verification

### 确认两个文件夹内容相同

```powershell
# 比较两个文件夹
$folder1 = Get-ChildItem "C:\Users\china\.agent\skills" -Directory | Select-Object -ExpandProperty Name | Sort-Object
$folder2 = Get-ChildItem "C:\Users\china\.gemini\antigravity\skills" -Directory | Select-Object -ExpandProperty Name | Sort-Object

Compare-Object $folder1 $folder2
```

**如果没有输出** = 两个文件夹完全相同 ✅

---

## ✅ 删除后验证 / Post-Deletion Verification

### 1. 检查主要 Skills 是否完整

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
# 选择选项 2 - 应该显示 18 个 Skills
```

### 2. 验证路径配置

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
# 选择选项 4 - 验证路径
```

### 3. 测试 Antigravity

- 重新启动 Antigravity
- 尝试使用任意 Skill
- 确认功能正常

---

## 📋 清理后的文件夹结构 / Final Structure

```
C:\Users\china\
├── .agent\
│   └── skills\                    ← 主要 Skills（18 个）✅
│       ├── algorithmic-art\
│       ├── canvas-design\
│       ├── ui-ux-pro-max\
│       └── ... (15 more)
│
├── .gemini\
│   └── antigravity\
│       └── (skills 文件夹已删除)  ← 已清理 ✅
│
└── superpowers\
    └── skills\                    ← 工作流 Skills（14 个）✅
        ├── brainstorming\
        ├── systematic-debugging\
        └── ... (12 more)
```

---

## 💾 空间节省 / Space Saved

删除重复的 skills 文件夹后：
- **节省空间：** 约 0.2 MB
- **减少混淆：** 只保留必要的文件夹
- **提高清晰度：** 明确的 Skills 管理结构

---

## 🚀 推荐操作流程 / Recommended Workflow

### 步骤 1：备份（可选）
```powershell
# 如果你想要额外的安全保障
Copy-Item "C:\Users\china\.gemini\antigravity\skills" "D:\Backup\skills-backup" -Recurse
```

### 步骤 2：关闭 Antigravity
- 完全退出应用程序

### 步骤 3：删除重复文件夹
```powershell
# 方法 A：使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\delete-duplicate-skills.ps1

# 方法 B：手动删除
explorer C:\Users\china\.gemini\antigravity
# 然后手动删除 skills 文件夹
```

### 步骤 4：验证
```powershell
# 重新启动 Antigravity
# 运行验证脚本
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
```

---

## ❓ 常见问题 / FAQ

### Q1: 删除后 Antigravity 会出问题吗？
**A:** 不会。`.gemini\antigravity\skills` 只是缓存/备份，主要 Skills 在 `.agent\skills`。

### Q2: Superpowers 项目可以删除或拆分吗？
**A:** 
- **不建议删除：** 这些工作流 Skills 与功能 Skills 互补，用于指导 AI 的工作方式
- **❌ 不要拆分：** `superpowers` 是一个完整的 Git 项目，不只是 skills 文件夹
- **原因：** skills 依赖项目中的其他文件（lib/、commands/、hooks/ 等）
- **建议：** 保留整个 `C:\Users\china\superpowers\` 项目

### Q3: 如果删除错了怎么办？
**A:** 如果你删除了主要的 `.agent\skills`，可以从 `.gemini\antigravity\skills` 恢复（如果还没删除）。或者重新安装 Skills。

### Q4: 文件被占用无法删除怎么办？
**A:** 
1. 关闭 Antigravity
2. 重启电脑
3. 使用手动删除方法

---

## 📞 需要帮助？/ Need Help?

如果遇到问题：
1. 查看错误信息
2. 尝试重启电脑
3. 使用手动删除方法
4. 询问 AI 助手

---

**最后更新 / Last Updated:** 2026-01-22  
**状态 / Status:** 待清理 / Pending Cleanup
