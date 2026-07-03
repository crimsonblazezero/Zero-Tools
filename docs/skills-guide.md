# Skills 管理快速指南
# Quick Guide for Skills Management

---

## 🎯 全局 Skills 路径 / Global Skills Path

```
C:\Users\china\.agent\skills
```

**这是你的全局 Skills 文件夹，所有 Skills 都存放在这里。**  
**This is your global Skills folder where all skills are stored.**

---

## 🚀 快速使用 / Quick Usage

### 方法 1：使用管理脚本 / Method 1: Use Management Script

```powershell
# 在项目根目录运行 / Run in project root
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
```

**功能菜单 / Feature Menu:**
- `[1]` 打开 Skills 文件夹 / Open Skills Folder
- `[2]` 列出所有 Skills / List All Skills  
- `[3]` 在 VS Code 中打开 / Open in VS Code
- `[4]` 验证路径 / Validate Paths

---

### 方法 2：直接访问 / Method 2: Direct Access

```powershell
# 打开文件夹 / Open folder
explorer C:\Users\china\.agent\skills

# 在 VS Code 中打开 / Open in VS Code
code C:\Users\china\.agent\skills

# 列出所有 Skills / List all skills
Get-ChildItem C:\Users\china\.agent\skills -Directory
```

---

## 📚 已安装的 Skills / Installed Skills (18)

### 🎨 设计类 / Design
- `algorithmic-art` - 算法艺术生成
- `canvas-design` - 视觉设计创作
- `frontend-design` - 前端界面设计
- `ui-ux-pro-max` ⭐ - UI/UX 设计智能系统
- `theme-factory` - 主题样式工具
- `slack-gif-creator` - GIF 动画创建

### 📄 文档类 / Documents
- `docx` - Word 文档处理
- `pptx` - PowerPoint 处理
- `pdf` - PDF 处理
- `xlsx` - Excel 处理
- `doc-coauthoring` - 文档协作

### 🛠️ 开发类 / Development
- `web-artifacts-builder` - Web 应用构建
- `webapp-testing` - Web 应用测试
- `mcp-builder` - MCP 服务器构建

### 📝 其他 / Others
- `brand-guidelines` - 品牌规范
- `internal-comms` - 内部沟通
- `skill-creator` - Skill 创建工具
- `superpower` - Superpowers 功能

---

## 🎯 KovaScape 推荐 Skills / Recommended for KovaScape

### 高优先级 / High Priority
1. **ui-ux-pro-max** - 创建产品详情页、品牌网站
2. **canvas-design** - 设计产品海报、营销素材
3. **xlsx** - 处理销售数据、库存报表
4. **pptx** - 创建品牌展示、供应商沟通材料

### 中优先级 / Medium Priority
5. **frontend-design** - 构建内部工具界面
6. **theme-factory** - 统一品牌视觉风格

---

## 🔧 常见操作 / Common Operations

### 查看 Skill 详情 / View Skill Details

```powershell
# 查看 SKILL.md 文件 / View SKILL.md file
Get-Content "C:\Users\china\.agent\skills\ui-ux-pro-max\SKILL.md" -Head 20
```

### 添加新 Skill / Add New Skill

```powershell
# 克隆到全局文件夹 / Clone to global folder
cd C:\Users\china\.agent\skills
git clone <skill-repo-url>

# 更新配置文件 / Update config file
# 编辑 D:\KovaScape Tools\config\paths.json
# 在 skills.installed 数组中添加新 skill 名称
```

### 删除 Skill / Remove Skill

```powershell
# 删除文件夹 / Delete folder
Remove-Item "C:\Users\china\.agent\skills\<skill-name>" -Recurse -Force

# 更新配置文件 / Update config file
# 从 config/paths.json 的 skills.installed 中移除
```

---

## 💡 使用技巧 / Tips

### 1. 快速搜索 Skill / Quick Search

```powershell
Get-ChildItem C:\Users\china\.agent\skills -Directory | Where-Object { $_.Name -like "*design*" }
```

### 2. 查看 Skill 文件结构 / View Skill Structure

```powershell
Get-ChildItem "C:\Users\china\.agent\skills\ui-ux-pro-max" -Recurse
```

### 3. 批量查看所有 Skill 描述 / View All Skill Descriptions

```powershell
Get-ChildItem C:\Users\china\.agent\skills -Directory | ForEach-Object {
    $skillMd = Join-Path $_.FullName "SKILL.md"
    if (Test-Path $skillMd) {
        Write-Host "=== $($_.Name) ===" -ForegroundColor Green
        Get-Content $skillMd -Head 5 | Select-String "description:"
        Write-Host ""
    }
}
```

---

## 🔄 环境切换 / Environment Switching

如果你在不同电脑工作（公司/家里），需要更新路径：  
If working on different computers (company/home), update paths:

### 1. 检查当前用户 / Check Current User

```powershell
echo $env:USERNAME
```

### 2. 更新配置文件 / Update Config File

编辑 `D:\KovaScape Tools\config\paths.json`：

```json
{
  "paths": {
    "global_skills": "C:\\Users\\<YOUR_USERNAME>\\.agent\\skills",
    ...
  },
  "environment": {
    "current_location": "home",  // 或 "company"
    "user": "<YOUR_USERNAME>",
    ...
  }
}
```

### 3. 验证路径 / Validate Paths

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
# 选择选项 4 验证路径
```

---

## ❓ 故障排除 / Troubleshooting

### 问题 1：脚本无法运行 / Script Cannot Run

**错误信息 / Error:** "禁止运行脚本" / "Script execution is disabled"

**解决方案 / Solution:**
```powershell
# 使用 -ExecutionPolicy Bypass 参数
powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1
```

### 问题 2：路径不存在 / Path Does Not Exist

**错误信息 / Error:** "Global skills folder not found"

**解决方案 / Solution:**
1. 检查用户名是否正确
2. 检查 Antigravity 是否已安装
3. 手动创建文件夹：
   ```powershell
   mkdir C:\Users\china\.agent\skills
   ```

### 问题 3：找不到某个 Skill / Cannot Find a Skill

**解决方案 / Solution:**
```powershell
# 搜索 Skill
Get-ChildItem C:\Users\china\.agent\skills -Directory | Where-Object { $_.Name -like "*<keyword>*" }

# 如果确实不存在，可以安装
cd C:\Users\china\.agent\skills
git clone <skill-repo-url>
```

---

## 📞 需要帮助？/ Need Help?

如果遇到问题，可以：  
If you encounter issues:

1. 运行路径验证 / Run path validation
2. 检查配置文件 / Check config file: `config/paths.json`
3. 查看 README / View README: `README.md`
4. 询问 Antigravity AI 助手 / Ask Antigravity AI assistant

---

**最后更新 / Last Updated:** 2026-01-22  
**项目 / Project:** KovaScape Tools
