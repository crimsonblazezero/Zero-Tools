# Workflows 快捷命令使用指南
# Workflows Quick Command Guide

---

## 🎯 **什么是 Workflows？**

Workflows 是快捷命令（slash commands），让你可以快速调用 skills 而无需记住复杂的路径和命令。

---

## 📋 **已创建的 Workflows**

现在你有 **4 个快捷命令**可用：

| 快捷命令         | Skill         | 用途                             | 创建时间 |
| ---------------- | ------------- | -------------------------------- | -------- |
| `/ui-ux-pro-max` | ui-ux-pro-max | UI/UX 设计智能系统               | 之前已有 |
| `/canvas-design` | canvas-design | 视觉设计创作（海报、营销素材）   | ✅ 刚创建 |
| `/xlsx`          | xlsx          | Excel 数据处理（库存、销售分析） | ✅ 刚创建 |
| `/pptx`          | pptx          | PowerPoint 演示文稿              | ✅ 刚创建 |

---

## 🚀 **如何使用 Workflows**

### 方法 1：直接输入快捷命令

在对话中直接输入 `/` 开头的命令：

```
/ui-ux-pro-max
/canvas-design
/xlsx
/pptx
```

Antigravity 会自动读取对应的 workflow 文件并按照指南执行。

---

### 方法 2：在请求中提及

你也可以在正常请求中提及 workflow：

```
"使用 /canvas-design 创建一个产品海报"
"用 /xlsx 分析销售数据"
"通过 /pptx 制作供应商演示文稿"
```

---

## 📚 **每个 Workflow 的详细说明**

### 1️⃣ `/ui-ux-pro-max` - UI/UX 设计智能系统

**用途：**
- 创建网站和移动应用界面
- 生成完整的设计系统
- 获取 50+ 设计风格、97 种配色方案
- 支持 9 种技术栈（React, Next.js, Vue, Svelte 等）

**示例：**
```
/ui-ux-pro-max

然后说：
"为 KovaScape 创建一个产品详情页，风格优雅现代"
```

**核心功能：**
- 自动生成设计系统（颜色、字体、风格）
- 提供 UX 最佳实践
- 支持响应式设计
- 包含可访问性指南

---

### 2️⃣ `/canvas-design` - 视觉设计创作

**用途：**
- 创建产品海报
- 设计营销素材
- 社交媒体图形
- 品牌视觉设计

**示例：**
```
/canvas-design

然后说：
"为新款相框设计一张产品海报，风格优雅，暖色调"
```

**核心功能：**
- 现代设计原则指导
- KovaScape 品牌色彩方案
- 排版和布局建议
- 输出 PNG/PDF 格式

**KovaScape 专用配色：**
- 优雅/高端：米色 + 金色 + 奶油色
- 现代/清新：白色 + 黑色 + 鼠尾草绿

---

### 3️⃣ `/xlsx` - Excel 数据处理

**用途：**
- 库存管理和分析
- 销售数据处理
- 创建业务报表
- 数据可视化

**示例：**
```
/xlsx

然后说：
"分析本月销售数据，计算库存可用天数和补货数量"
```

**核心功能：**
- 读取和分析 Excel 文件
- 创建带公式的报表
- 数据可视化（图表）
- 库存计算（可用天数、补货量）

**KovaScape 常用计算：**
```python
# 可用天数 = 总库存 / 日均销量
Days_Supply = Total_Inventory / Daily_Sales

# 补货数量 = (目标天数 × 日均销量) - 总库存
Replenish_Qty = (Target_Days * Daily_Sales) - Total_Inventory
```

---

### 4️⃣ `/pptx` - PowerPoint 演示文稿

**用途：**
- 产品展示演示
- 供应商沟通材料
- 业务报告
- 品牌指南演示

**示例：**
```
/pptx

然后说：
"创建一个产品展示PPT，给供应商看新款相框系列"
```

**核心功能：**
- 创建专业演示文稿
- 添加图表和表格
- KovaScape 品牌模板
- 多种演示模板（产品、报告、供应商）

**KovaScape 品牌色：**
- 主色：海军蓝 (#1F3A60)
- 强调色：金色 (#D4AF37)
- 背景：奶油色 (#F5F5DC) 或白色

---

## 💡 **实际使用示例**

### 场景 1：新产品上市

```
1. /canvas-design
   "为新款金色相框设计产品海报"
   
2. /ui-ux-pro-max
   "创建产品详情页，展示相框特点"
   
3. /pptx
   "制作产品发布演示文稿"
```

### 场景 2：月度业务分析

```
1. /xlsx
   "分析本月销售数据，生成库存报告"
   
2. /pptx
   "创建月度业务回顾演示文稿，包含销售图表"
```

### 场景 3：供应商沟通

```
1. /xlsx
   "整理订单数据和规格要求"
   
2. /pptx
   "创建供应商订单演示文稿，包含产品规格和时间表"
```

---

## 📁 **Workflow 文件位置**

所有 workflow 文件存放在：
```
D:\KovaScape Tools\.agent\workflows\
├── ui-ux-pro-max.md      ← UI/UX 设计
├── canvas-design.md       ← 视觉设计（新）
├── xlsx.md                ← Excel 处理（新）
└── pptx.md                ← PowerPoint（新）
```

---

## 🔧 **如何查看 Workflow 详情**

### 方法 1：使用命令
```powershell
# 查看特定 workflow
code "D:\KovaScape Tools\.agent\workflows\canvas-design.md"
```

### 方法 2：列出所有 workflows
```powershell
Get-ChildItem "D:\KovaScape Tools\.agent\workflows" -Filter "*.md"
```

---

## ✨ **Workflow vs Skill 的区别**

| 特性     | Workflow                 | Skill                |
| -------- | ------------------------ | -------------------- |
| **位置** | `.agent\workflows\`      | `.agent\skills\`     |
| **用途** | 快捷命令和使用指南       | 实际功能实现         |
| **调用** | `/command`               | 直接引用 skill 路径  |
| **内容** | 使用说明、示例、最佳实践 | 详细的功能代码和文档 |
| **关系** | 指向 Skill               | 被 Workflow 引用     |

**简单理解：**
- **Skill** = 工具本身（锤子）
- **Workflow** = 使用说明书（如何用锤子）

---

## 🎯 **为什么创建这些 Workflows？**

### 问题
你发现只有 `/ui-ux-pro-max` 有快捷命令，其他重要的 skills 没有。

### 解决方案
为 KovaScape 最常用的 3 个 skills 创建了 workflows：
1. `/canvas-design` - 设计营销素材
2. `/xlsx` - 处理业务数据
3. `/pptx` - 创建演示文稿

### 好处
- ✅ 快速调用，无需记住复杂路径
- ✅ 包含 KovaScape 专用指南和示例
- ✅ 统一的使用体验
- ✅ 降低学习成本

---

## 📝 **下一步可以做什么？**

### 选项 1：测试新的 Workflows
```
试试：
/canvas-design
"为春季新品设计一张海报"
```

### 选项 2：创建更多 Workflows

如果你还想为其他 skills 创建快捷命令，可以告诉我，比如：
- `/frontend-design` - 前端界面设计
- `/theme-factory` - 主题样式工具
- `/docx` - Word 文档处理

### 选项 3：自定义现有 Workflows

如果你想调整某个 workflow 的内容或示例，随时告诉我。

---

## ❓ **常见问题**

### Q1: Workflow 和 Skill 有什么区别？
**A:** Skill 是功能本身，Workflow 是使用指南。Workflow 告诉 AI 如何使用 Skill。

### Q2: 我可以自己创建 Workflow 吗？
**A:** 可以！在 `.agent\workflows\` 文件夹中创建 `.md` 文件，按照现有格式编写即可。

### Q3: Workflow 必须和 Skill 同名吗？
**A:** 不必须，但建议同名以便识别。

### Q4: 如何删除不需要的 Workflow？
**A:** 直接删除 `.agent\workflows\` 中对应的 `.md` 文件即可。

---

## 🎉 **总结**

### ✅ **现在你有了：**

1. **4 个快捷 Workflows**
   - `/ui-ux-pro-max` - UI/UX 设计
   - `/canvas-design` - 视觉设计
   - `/xlsx` - Excel 处理
   - `/pptx` - PowerPoint

2. **每个 Workflow 包含：**
   - 详细使用指南
   - KovaScape 专用示例
   - 最佳实践
   - 常见问题解决

3. **快速访问方式：**
   - 直接输入 `/command`
   - 在请求中提及
   - 查看文件获取详情

---

**开始使用吧！试试输入 `/canvas-design` 或 `/xlsx` 看看效果！** 🚀

---

**最后更新 / Last Updated:** 2026-01-22  
**项目 / Project:** KovaScape Tools  
**状态 / Status:** ✅ 4 个 Workflows 已创建
