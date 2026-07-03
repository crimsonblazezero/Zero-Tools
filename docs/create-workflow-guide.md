# 如何手动创建 Workflow 快捷命令
# How to Manually Create Workflow Shortcuts

---

## 🎯 **什么是 Workflow？**

Workflow 是一个 Markdown 文件，包含：
1. **YAML frontmatter** - 描述信息
2. **使用指南** - 如何使用这个 skill
3. **示例** - 实际使用案例
4. **最佳实践** - 注意事项

---

## 📁 **Workflow 文件位置**

所有 workflow 文件必须放在：
```
项目根目录/.agent/workflows/
```

例如：
```
D:/KovaScape Tools/.agent/workflows/
├── ui-ux-pro-max.md
├── canvas-design.md
├── xlsx.md
└── pptx.md
```

---

## 📝 **Workflow 文件格式**

### 基本结构

```markdown
---
description: 简短描述这个 workflow 的用途
---

# workflow-name

详细说明这个 workflow 是什么，什么时候使用。

## When to Use

列出使用场景

## Prerequisites

前置条件（如需要安装的库）

## How to Use This Workflow

### Step 1: 第一步
### Step 2: 第二步
...

## Example Workflow

实际使用示例

## Best Practices

最佳实践

## Tips for Better Results

使用技巧
```

---

## 🛠️ **创建步骤**

### 步骤 1：确定要创建的 Workflow

首先确定：
- **Skill 名称** - 你要调用哪个 skill？
- **快捷命令** - 你想用什么命令调用？（通常与 skill 同名）
- **用途** - 这个 skill 主要用来做什么？

**示例：**
- Skill: `frontend-design`
- 快捷命令: `/frontend-design`
- 用途: 创建前端界面设计

---

### 步骤 2：找到 Skill 的位置

Skill 通常在：
```
C:\Users\china\.agent\skills\<skill-name>\
```

查看 skill 的 SKILL.md 文件：
```powershell
code "C:\Users\china\.agent\skills\<skill-name>\SKILL.md"
```

---

### 步骤 3：创建 Workflow 文件

在项目的 `.agent/workflows/` 文件夹中创建新文件：

```powershell
# 创建新的 workflow 文件
New-Item -Path "D:\KovaScape Tools\.agent\workflows\<workflow-name>.md" -ItemType File
```

**文件命名规则：**
- 使用小写字母
- 单词之间用连字符 `-`
- 文件扩展名必须是 `.md`
- 通常与 skill 名称相同

**示例：**
```
frontend-design.md
theme-factory.md
docx.md
```

---

### 步骤 4：编写 Workflow 内容

#### 模板 1：简单 Workflow（推荐新手）

```markdown
---
description: 简短描述（一句话说明用途）
---

# workflow-name

这个 workflow 用于 [具体用途]。

## When to Use

- 场景 1
- 场景 2
- 场景 3

## Prerequisites

Skill 位置：
\`\`\`
C:\Users\china\.agent\skills\<skill-name>
\`\`\`

## How to Use This Workflow

### Step 1: 读取 Skill 文档

\`\`\`bash
cat "C:\Users\china\.agent\skills\<skill-name>\SKILL.md"
\`\`\`

或使用 view_file 工具读取 SKILL.md 文件。

### Step 2: 理解用户需求

确定用户想要什么：
- 需求 1
- 需求 2
- 需求 3

### Step 3: 执行操作

根据 skill 文档中的指南执行操作。

## Example Workflow

**用户请求：** "示例请求"

### 分析需求
- 关键点 1
- 关键点 2

### 执行步骤
1. 步骤 1
2. 步骤 2
3. 步骤 3

## Tips for Better Results

1. 技巧 1
2. 技巧 2
3. 技巧 3
```

---

#### 模板 2：完整 Workflow（适合复杂 skills）

```markdown
---
description: 详细描述这个 workflow 的功能和用途
---

# workflow-name

完整的功能说明，包括这个 skill 能做什么，适用场景等。

## When to Use

详细列出使用场景：
- 场景 1：具体说明
- 场景 2：具体说明
- 场景 3：具体说明

## Prerequisites

### Skill 位置
\`\`\`
C:\Users\china\.agent\skills\<skill-name>
\`\`\`

### 依赖检查
\`\`\`bash
# 检查是否安装了必要的库
python -c "import library_name; print('Installed')"
\`\`\`

### 安装依赖（如需要）
\`\`\`bash
pip install library_name
\`\`\`

## How to Use This Workflow

### Step 1: 读取 Skill 文档

\`\`\`bash
cat "C:\Users\china\.agent\skills\<skill-name>\SKILL.md"
\`\`\`

### Step 2: 分析用户需求

提取关键信息：
- **需求类型**：[类型]
- **关键参数**：[参数]
- **期望输出**：[输出]

### Step 3: 准备数据/环境

如果需要准备数据或环境，在这里说明。

### Step 4: 执行核心操作

详细的执行步骤，包括代码示例。

### Step 5: 验证和优化

检查结果，必要时进行优化。

## Example Workflow

### 示例 1：[场景名称]

**用户请求：** "具体请求内容"

#### Step 1: 分析需求
- 分析点 1
- 分析点 2

#### Step 2: 执行操作
\`\`\`python
# 示例代码
\`\`\`

#### Step 3: 输出结果
说明预期结果

### 示例 2：[另一个场景]

...

## Best Practices

### 最佳实践 1
说明和示例

### 最佳实践 2
说明和示例

## Common Use Cases for KovaScape

### 用例 1：[业务场景]
具体说明如何应用到 KovaScape 业务

### 用例 2：[业务场景]
具体说明如何应用到 KovaScape 业务

## Pre-Delivery Checklist

交付前检查清单：
- [ ] 检查项 1
- [ ] 检查项 2
- [ ] 检查项 3

## Tips for Better Results

1. **技巧 1**：详细说明
2. **技巧 2**：详细说明
3. **技巧 3**：详细说明

## Troubleshooting

### 常见问题 1
**问题：** 描述问题
**解决：** 解决方法

### 常见问题 2
**问题：** 描述问题
**解决：** 解决方法

---

**Remember:** 总结性的提醒或建议
```

---

## 📚 **实际示例：创建 frontend-design Workflow**

### 完整代码示例

```markdown
---
description: Create distinctive, production-grade frontend interfaces with high design quality
---

# frontend-design

Create beautiful, professional frontend interfaces for web applications. This skill helps you build components, pages, and complete web applications with modern design principles.

## When to Use

- Building web pages or applications
- Creating React/Vue/HTML components
- Designing landing pages
- Developing dashboards or admin panels
- Styling existing interfaces

## Prerequisites

The frontend-design skill is located at:
\`\`\`
C:\Users\china\.agent\skills\frontend-design
\`\`\`

## How to Use This Workflow

### Step 1: Read the Skill Documentation

\`\`\`bash
cat "C:\Users\china\.agent\skills\frontend-design\SKILL.md"
\`\`\`

Or use the view_file tool to read the SKILL.md file.

### Step 2: Understand User Requirements

Extract key information:
- **Project type**: Landing page, dashboard, e-commerce, etc.
- **Tech stack**: React, Vue, HTML/CSS, etc.
- **Design style**: Modern, minimal, elegant, etc.
- **Features needed**: Forms, charts, navigation, etc.

### Step 3: Apply Design Principles

Follow the skill's design guidelines:
- Use modern color palettes
- Implement responsive layouts
- Add smooth animations
- Ensure accessibility

### Step 4: Generate Code

Create the frontend code following best practices from the skill.

## Example Workflow

**User request:** "创建一个产品展示页面，用于 KovaScape 相框"

### Step 1: Analyze Requirements
- Project type: Product showcase page
- Tech stack: HTML/CSS (or React if specified)
- Design style: Elegant, modern, premium
- Features: Product gallery, specifications, CTA

### Step 2: Design Strategy
- Color scheme: Warm neutrals (beige, gold, cream)
- Layout: Hero section + product grid + details
- Typography: Elegant serif for headings, clean sans-serif for body
- Interactions: Smooth hover effects, image zoom

### Step 3: Implementation
Create the page following the skill's guidelines.

## Best Practices

- **Mobile-first**: Design for mobile, then scale up
- **Performance**: Optimize images and code
- **Accessibility**: Use semantic HTML, ARIA labels
- **Consistency**: Follow design system throughout

## Tips for Better Results

1. **Reference the skill documentation**: Always check SKILL.md for latest guidelines
2. **Use modern frameworks**: React, Vue, or Tailwind CSS
3. **Test responsiveness**: Check on multiple screen sizes
4. **Validate code**: Ensure HTML/CSS/JS is valid

---

**Remember:** Great frontend design combines aesthetics with functionality and performance.
```

---

## 🎯 **快速创建 Workflow 的方法**

### 方法 1：复制现有 Workflow 并修改

```powershell
# 复制现有的 workflow 作为模板
Copy-Item "D:\KovaScape Tools\.agent\workflows\canvas-design.md" "D:\KovaScape Tools\.agent\workflows\new-workflow.md"

# 然后编辑新文件
code "D:\KovaScape Tools\.agent\workflows\new-workflow.md"
```

### 方法 2：使用模板快速创建

我可以为你创建一个通用模板文件：

```powershell
# 创建模板文件
New-Item -Path "D:\KovaScape Tools\.agent\workflows\_template.md" -ItemType File
```

---

## ✅ **验证 Workflow 是否生效**

### 检查文件是否在正确位置

```powershell
# 列出所有 workflows
Get-ChildItem "D:\KovaScape Tools\.agent\workflows" -Filter "*.md"
```

### 测试 Workflow

在对话中输入：
```
/your-workflow-name
```

Antigravity 应该会读取并执行这个 workflow。

---

## 📋 **Workflow 命名规范**

### ✅ 正确的命名

- `frontend-design.md`
- `theme-factory.md`
- `web-testing.md`
- `data-analysis.md`

### ❌ 错误的命名

- `Frontend Design.md` (有空格)
- `frontendDesign.md` (驼峰命名)
- `frontend_design.md` (下划线，虽然可以但不推荐)
- `FRONTEND-DESIGN.md` (全大写)

---

## 🔧 **常见问题解决**

### Q1: Workflow 不生效怎么办？

**检查清单：**
1. 文件是否在 `.agent/workflows/` 文件夹中？
2. 文件扩展名是否是 `.md`？
3. YAML frontmatter 格式是否正确？
4. 文件名是否使用了正确的命名规范？

### Q2: 如何引用 Skill 路径？

**推荐方式：**
```markdown
Skill 位置：
\`\`\`
C:\Users\china\.agent\skills\<skill-name>
\`\`\`

然后在 workflow 中指导 AI：
"使用 view_file 工具读取 SKILL.md 文件"
```

### Q3: Workflow 和 Skill 必须同名吗？

**不必须**，但强烈推荐同名以便识别。

**示例：**
- Skill: `canvas-design`
- Workflow: `canvas-design.md` ✅ 推荐
- Workflow: `design-poster.md` ⚠️ 可以但不推荐

---

## 💡 **高级技巧**

### 技巧 1：在 Workflow 中引用其他 Workflows

```markdown
## Related Workflows

This workflow works well with:
- `/ui-ux-pro-max` - For design system generation
- `/canvas-design` - For creating visual assets
```

### 技巧 2：添加 KovaScape 专用配置

```markdown
## KovaScape-Specific Guidelines

**Brand Colors:**
- Primary: Navy Blue (#1F3A60)
- Accent: Gold (#D4AF37)
- Background: Cream (#F5F5DC)

**Typography:**
- Headings: Playfair Display
- Body: Inter

**Design Style:**
- Elegant yet accessible
- Modern with classic touches
- Premium but not pretentious
```

### 技巧 3：使用 Turbo 模式自动执行

如果某个步骤可以安全自动执行，添加 `// turbo` 注释：

```markdown
### Step 2: Install Dependencies

// turbo
\`\`\`bash
pip install required-library
\`\`\`
```

---

## 📝 **创建 Workflow 的完整流程**

### 1. 确定目标
- 我要为哪个 skill 创建 workflow？
- 这个 skill 的主要用途是什么？

### 2. 研究 Skill
```powershell
# 查看 skill 文档
code "C:\Users\china\.agent\skills\<skill-name>\SKILL.md"

# 查看 skill 结构
Get-ChildItem "C:\Users\china\.agent\skills\<skill-name>" -Recurse
```

### 3. 创建文件
```powershell
# 创建 workflow 文件
New-Item -Path "D:\KovaScape Tools\.agent\workflows\<workflow-name>.md" -ItemType File

# 或者复制模板
Copy-Item "D:\KovaScape Tools\.agent\workflows\canvas-design.md" "D:\KovaScape Tools\.agent\workflows\<workflow-name>.md"
```

### 4. 编写内容
- 添加 YAML frontmatter
- 写清楚使用场景
- 提供详细步骤
- 添加实际示例
- 包含 KovaScape 专用指南（如适用）

### 5. 测试
```
在对话中输入：
/<workflow-name>

验证 AI 是否正确读取和执行
```

### 6. 优化
- 根据使用情况调整内容
- 添加更多示例
- 完善最佳实践

---

## 🎓 **学习资源**

### 查看现有 Workflows

```powershell
# 列出所有 workflows
Get-ChildItem "D:\KovaScape Tools\.agent\workflows"

# 查看某个 workflow
code "D:\KovaScape Tools\.agent\workflows\ui-ux-pro-max.md"
```

### 参考最佳实践

现有的 workflows 是很好的学习材料：
- `ui-ux-pro-max.md` - 复杂 workflow 的示例
- `canvas-design.md` - 包含品牌指南的示例
- `xlsx.md` - 技术性 workflow 的示例
- `pptx.md` - 业务场景 workflow 的示例

---

## 🎉 **总结**

### 创建 Workflow 的核心步骤：

1. **创建文件** - 在 `.agent/workflows/` 中创建 `.md` 文件
2. **添加 frontmatter** - 包含 `description`
3. **编写指南** - 详细的使用步骤和示例
4. **测试** - 使用 `/<workflow-name>` 测试
5. **优化** - 根据使用情况改进

### 记住：

- ✅ 文件必须在 `.agent/workflows/` 文件夹
- ✅ 文件名使用小写和连字符
- ✅ 必须包含 YAML frontmatter
- ✅ 提供清晰的步骤和示例
- ✅ 添加 KovaScape 专用指南（如适用）

---

**现在你知道如何手动创建 workflow 了！需要我帮你创建某个特定的 workflow 吗？**
