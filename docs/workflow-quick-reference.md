# 手动创建 Workflow 快速指南
# Quick Guide to Creating Workflows Manually

---

## 🎯 **3 种创建 Workflow 的方法**

### 方法 1：使用自动化脚本（最快）⭐⭐⭐

```powershell
# 快速创建新 workflow
.\scripts\create-workflow.ps1 -WorkflowName "frontend-design" -Description "Create beautiful frontend interfaces"

# 如果 skill 名称不同
.\scripts\create-workflow.ps1 -WorkflowName "design-ui" -Description "UI design tool" -SkillName "frontend-design"
```

**优点：**
- ✅ 最快速
- ✅ 自动填充模板
- ✅ 自动替换占位符
- ✅ 可选直接打开编辑

---

### 方法 2：复制现有 Workflow（推荐）⭐⭐

```powershell
# 复制一个相似的 workflow 作为起点
Copy-Item "D:\KovaScape Tools\.agent\workflows\canvas-design.md" "D:\KovaScape Tools\.agent\workflows\new-workflow.md"

# 编辑新文件
code "D:\KovaScape Tools\.agent\workflows\new-workflow.md"
```

**优点：**
- ✅ 有完整的参考示例
- ✅ 格式已经正确
- ✅ 只需修改内容

---

### 方法 3：从模板创建（手动）⭐

```powershell
# 复制模板
Copy-Item "D:\KovaScape Tools\.agent\workflows\_template.md" "D:\KovaScape Tools\.agent\workflows\new-workflow.md"

# 编辑文件
code "D:\KovaScape Tools\.agent\workflows\new-workflow.md"
```

**优点：**
- ✅ 完全控制
- ✅ 适合自定义需求

---

## 📝 **Workflow 文件的基本结构**

```markdown
---
description: 一句话描述
---

# workflow-name

详细说明

## When to Use
使用场景

## Prerequisites
前置条件

## How to Use This Workflow
使用步骤

## Example Workflow
实际示例

## Best Practices
最佳实践

## Tips for Better Results
使用技巧
```

---

## 🚀 **快速创建示例**

### 示例 1：为 frontend-design 创建 Workflow

```powershell
# 使用脚本创建
.\scripts\create-workflow.ps1 -WorkflowName "frontend-design" -Description "Create beautiful frontend interfaces"

# 然后编辑文件，添加：
# - 详细的使用步骤
# - KovaScape 专用示例
# - 设计最佳实践
```

### 示例 2：为 theme-factory 创建 Workflow

```powershell
# 使用脚本创建
.\scripts\create-workflow.ps1 -WorkflowName "theme-factory" -Description "Apply professional themes to artifacts"

# 编辑文件，添加：
# - 可用主题列表
# - 应用步骤
# - 自定义主题方法
```

---

## ✅ **必须遵守的规则**

### 1. 文件位置
```
必须放在：D:\KovaScape Tools\.agent\workflows\
```

### 2. 文件命名
```
✅ 正确：frontend-design.md
✅ 正确：theme-factory.md
❌ 错误：Frontend Design.md (有空格)
❌ 错误：frontendDesign.md (驼峰命名)
```

### 3. YAML Frontmatter
```markdown
---
description: 必须有这个描述
---
```

### 4. 文件扩展名
```
必须是 .md
```

---

## 🔍 **验证 Workflow 是否正确**

### 检查文件位置
```powershell
Get-ChildItem "D:\KovaScape Tools\.agent\workflows" -Filter "*.md"
```

### 测试 Workflow
```
在对话中输入：
/your-workflow-name

AI 应该会读取并执行这个 workflow
```

---

## 💡 **实用技巧**

### 技巧 1：查看现有 Workflows 学习

```powershell
# 列出所有 workflows
Get-ChildItem "D:\KovaScape Tools\.agent\workflows"

# 查看某个 workflow
code "D:\KovaScape Tools\.agent\workflows\ui-ux-pro-max.md"
```

### 技巧 2：为 KovaScape 添加专用配置

在 workflow 中添加：

```markdown
## KovaScape-Specific Guidelines

**品牌色彩：**
- 主色：海军蓝 (#1F3A60)
- 强调色：金色 (#D4AF37)
- 背景：奶油色 (#F5F5DC)

**设计风格：**
- 优雅而易接近
- 现代与经典结合
- 高端但不做作
```

### 技巧 3：引用 Skill 路径

```markdown
## Prerequisites

Skill 位置：
\`\`\`
C:\Users\china\.agent\skills\<skill-name>
\`\`\`

在 workflow 中指导 AI：
"使用 view_file 工具读取 SKILL.md 文件"
```

---

## 📚 **完整示例：创建一个新 Workflow**

### 场景：为 docx skill 创建 workflow

#### Step 1: 创建文件

```powershell
.\scripts\create-workflow.ps1 -WorkflowName "docx" -Description "Create and edit Word documents"
```

#### Step 2: 编辑内容

```markdown
---
description: Create and edit Word documents with formatting and styles
---

# docx

Create, modify, and analyze Word documents (.docx) for reports, documentation, and business documents.

## When to Use

- Creating business reports
- Writing documentation
- Generating contracts or agreements
- Formatting existing documents

## Prerequisites

Skill 位置：
\`\`\`
C:\Users\china\.agent\skills\docx
\`\`\`

检查依赖：
\`\`\`bash
python -c "import docx; print('python-docx installed')"
\`\`\`

## How to Use This Workflow

### Step 1: 读取 Skill 文档

\`\`\`bash
cat "C:\Users\china\.agent\skills\docx\SKILL.md"
\`\`\`

### Step 2: 理解用户需求

确定文档类型：
- 新建文档
- 修改现有文档
- 提取内容
- 格式化文档

### Step 3: 执行操作

根据 skill 文档执行相应操作。

## Example Workflow

**用户请求：** "创建一个产品说明文档"

### Step 1: 分析需求
- 文档类型：产品说明
- 包含内容：产品特性、规格、使用说明
- 格式要求：专业、清晰

### Step 2: 创建文档
使用 python-docx 创建文档，添加标题、段落、表格等。

## Best Practices

- 使用样式保持一致性
- 添加目录（如果文档较长）
- 使用表格展示数据
- 保持格式专业

## Tips for Better Results

1. 先规划文档结构
2. 使用内置样式
3. 添加页眉页脚
4. 检查拼写和格式
\`\`\`

#### Step 3: 保存并测试

```powershell
# 保存文件后，测试
# 在对话中输入：
/docx
```

---

## 🛠️ **已创建的工具**

### 1. 创建脚本
```powershell
.\scripts\create-workflow.ps1
```

### 2. 模板文件
```
.agent\workflows\_template.md
```

### 3. 详细教程
```
docs\create-workflow-guide.md
```

---

## 📋 **当前可用的 Workflows**

| Workflow         | 用途                | 状态     |
| ---------------- | ------------------- | -------- |
| `/ui-ux-pro-max` | UI/UX 设计智能系统  | ✅ 已有   |
| `/canvas-design` | 视觉设计创作        | ✅ 已创建 |
| `/xlsx`          | Excel 数据处理      | ✅ 已创建 |
| `/pptx`          | PowerPoint 演示文稿 | ✅ 已创建 |

---

## 🎯 **推荐创建的 Workflows**

基于 KovaScape 业务需求，推荐为以下 skills 创建 workflows：

### 高优先级
1. **frontend-design** - 创建产品详情页
2. **theme-factory** - 统一品牌视觉
3. **docx** - 创建业务文档

### 中优先级
4. **pdf** - PDF 处理
5. **web-artifacts-builder** - 复杂 Web 应用
6. **brand-guidelines** - 品牌规范应用

---

## ❓ **常见问题**

### Q1: Workflow 必须和 Skill 同名吗？
**A:** 不必须，但强烈推荐同名便于识别。

### Q2: 可以为一个 Skill 创建多个 Workflows 吗？
**A:** 可以，但通常一个 skill 一个 workflow 就够了。

### Q3: Workflow 文件可以放在其他地方吗？
**A:** 不可以，必须在 `.agent/workflows/` 文件夹。

### Q4: 如何删除不需要的 Workflow？
**A:** 直接删除对应的 `.md` 文件即可。

---

## 🎉 **总结**

### 创建 Workflow 的最快方法：

```powershell
# 1. 使用脚本创建
.\scripts\create-workflow.ps1 -WorkflowName "your-workflow" -Description "Your description"

# 2. 编辑内容
code "D:\KovaScape Tools\.agent\workflows\your-workflow.md"

# 3. 测试
# 在对话中输入：/your-workflow
```

### 记住：

- ✅ 使用脚本最快
- ✅ 复制现有 workflow 最安全
- ✅ 文件必须在 `.agent/workflows/`
- ✅ 文件名使用小写和连字符
- ✅ 必须包含 YAML frontmatter

---

**现在你可以轻松创建自己的 workflows 了！需要帮助创建某个特定的 workflow 吗？**

---

**相关文档：**
- 详细教程：`docs/create-workflow-guide.md`
- Workflows 使用指南：`docs/workflows-guide.md`
- 模板文件：`.agent/workflows/_template.md`
