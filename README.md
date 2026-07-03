# KovaScape Tools

> 专为 KovaScape 品牌打造的亚马逊运营工具集  
> Amazon Operations Toolkit for KovaScape Brand

---

## 📁 项目结构 / Project Structure

```
KovaScape Tools/
├── config/              # 配置文件 / Configuration files
│   └── paths.json      # 路径配置 / Path configuration
├── scripts/            # 脚本工具 / Script utilities
│   ├── open-skills.ps1      # Skills 管理器 / Skills manager
│   └── validate-paths.ps1   # 路径验证器 / Path validator
├── src/                # 源代码 / Source code
├── data/               # 数据文件 / Data files
├── assets/             # 资源文件 / Asset files
├── docs/               # 文档 / Documentation
└── README.md           # 项目说明 / Project documentation
```

---

## 🚀 快速开始 / Quick Start

### 1️⃣ 打开 Skills 管理器 / Open Skills Manager

```powershell
# 在 PowerShell 中运行 / Run in PowerShell
.\scripts\open-skills.ps1
```

**功能 / Features:**
- 📂 打开全局 Skills 文件夹
- 📚 列出所有已安装的 Skills
- 🔍 搜索特定 Skill
- 📖 查看 Skill 详细信息
- 💻 在 VS Code 中打开

---

### 1️⃣-B 使用 Workflows 快捷命令 / Use Workflow Shortcuts ⭐

**什么是 Workflows？**  
Workflows 是快捷命令（slash commands），让你快速调用 skills。

**可用的快捷命令：**

```
/ui-ux-pro-max    - UI/UX 设计智能系统
/canvas-design    - 视觉设计创作（海报、营销素材）
/xlsx             - Excel 数据处理（库存、销售分析）
/pptx             - PowerPoint 演示文稿
```

**使用方法：**
```
直接在对话中输入：
/canvas-design

然后说明你的需求：
"为新款相框设计一张产品海报"
```

**查看详细指南：**
```powershell
code .\docs\workflows-guide.md
```

---

### 2️⃣ 验证路径配置 / Validate Path Configuration

```powershell
# 检查所有路径是否有效 / Check if all paths are valid
.\scripts\validate-paths.ps1
```

**验证内容 / Validation includes:**
- ✅ 全局 Skills 路径
- ✅ 项目目录结构
- ✅ Skills 配置一致性

---

## 🛠️ 配置管理 / Configuration Management

### 路径配置文件 / Path Configuration File

位置 / Location: `config/paths.json`

```json
{
  "paths": {
    "global_skills": "C:\\Users\\china\\.agent\\skills",
    "project_root": "D:\\KovaScape Tools",
    ...
  }
}
```

### 更换环境时 / When Changing Environment

如果你在不同电脑或环境工作，请：  
If working on different computers or environments:

1. 运行路径验证器 / Run path validator
   ```powershell
   .\scripts\validate-paths.ps1
   ```

2. 根据提示更新 `config/paths.json`  
   Update `config/paths.json` based on prompts

3. 重新验证 / Re-validate
   ```powershell
   .\scripts\validate-paths.ps1
   ```

---

## 📚 已安装的 Skills / Installed Skills

### 🎯 KovaScape 高优先级 / High Priority for KovaScape

- **ui-ux-pro-max** - UI/UX 设计智能系统
- **canvas-design** - 视觉艺术创作
- **xlsx** - Excel 数据处理
- **pptx** - PowerPoint 演示文稿
- **frontend-design** - 前端界面设计
- **theme-factory** - 主题样式工具

### 📋 完整列表 / Full List

查看 `config/paths.json` 中的 `skills.installed` 部分  
See `skills.installed` section in `config/paths.json`

---

## 💡 使用技巧 / Tips

### 快速访问 Skills / Quick Access to Skills

```powershell
# 方法 1：使用脚本 / Method 1: Use script
.\scripts\open-skills.ps1

# 方法 2：直接打开 / Method 2: Direct access
explorer C:\Users\china\.agent\skills

# 方法 3：VS Code / Method 3: VS Code
code C:\Users\china\.agent\skills
```

### 添加新 Skill / Add New Skill

```powershell
cd C:\Users\china\.agent\skills
git clone <skill-repo-url>

# 然后更新配置 / Then update config
# 编辑 config/paths.json，添加到 skills.installed 数组
# Edit config/paths.json, add to skills.installed array
```

---

## 🔧 故障排除 / Troubleshooting

### ❌ 路径不存在 / Path Does Not Exist

**问题 / Problem:** 运行脚本时提示路径不存在  
**解决 / Solution:**

1. 检查当前用户名
   ```powershell
   echo $env:USERNAME
   ```

2. 更新 `config/paths.json` 中的路径

3. 重新运行验证脚本

### ❌ Skills 配置不一致 / Skills Configuration Mismatch

**问题 / Problem:** 验证器提示 Skills 配置与实际不一致  
**解决 / Solution:**

1. 运行 `.\scripts\validate-paths.ps1` 查看详情
2. 手动更新 `config/paths.json` 中的 `skills.installed` 数组
3. 或删除不需要的 Skill 文件夹

---

## 📦 工具集 / Toolkits

### Inventory Intelligence Tool
库存智能分析工具，用于计算库存健康度、可用天数和补货需求。

**使用方法 / Usage:**
```bash
pip install -r requirements.txt
python app.py
```

访问 `http://127.0.0.1:5000` 使用工具。

---

## 📞 联系与支持 / Contact & Support

- **品牌 / Brand:** KovaScape
- **定位 / Focus:** 欧美市场家居装饰（相框、置物架）
- **市场 / Market:** Amazon FBA

---

## 📝 更新日志 / Changelog

### 2026-01-22
- ✅ 创建项目配置文件 `config/paths.json`
- ✅ 添加 Skills 管理器脚本 `scripts/open-skills.ps1`
- ✅ 添加路径验证脚本 `scripts/validate-paths.ps1`
- ✅ 记录全局 Skills 路径：`C:\Users\china\.agent\skills`

---

**Built with ❤️ for KovaScape**
