# Zero-Tools (KovaScape Tools)

> 专为 KovaScape 品牌打造的亚马逊运营与 AI 智能体技能工具集  
> AI Agents Skillset & Operations Toolkit for KovaScape Brand

---

## 📁 规范项目结构 / Project Structure

基于 KovaScape 品牌标准化结构目录：

```
Zero-Tools/
├── skills/             # 统一托管的 AI 技能目录 / Handled AI Skills
│   ├── ads-report-pipeline/    # 广告数据分析流水线
│   ├── dingtalk-unified/       # 钉钉 API 全能套件
│   ├── wechat-articles-crawler/# 微信文章抓取与语料库工具
│   └── ... (其他 70+ 核心技能)
├── src/                # Python 源代码 / Python Source Code
│   ├── fill_weekly_report.py   # 周报自动填报流水线
│   ├── bookmark_cleaner.py     # 书签清理与分类工具
│   └── delete_dead_wechat_links.py # 微信失效链接检测
├── data/               # 运营数据与数据库 / Operation Data & Databases
│   ├── kovascape_ads.db.backup # 备份的广告数据库
│   └── 六组周会会议纪要20260803.xlsx # 周会填报数据源
├── docs/               # 运营 SOP 与双语灵感库 / SOPs & Dual-language Guidelines
├── assets/             # 品牌设计素材与原图 / Branded Design Assets
├── config/             # 路径与环境配置 / Configuration
│   └── paths.json      # 系统路径设置
└── README.md           # 本说明文件 / Readme file
```

---

## 🚀 核心工具与自动化流水线 / Core Tools & Pipelines

### 1️⃣ 运营周报自动填报系统 (Weekly Report Auto-filler)
通过读取本地运营数据表，与钉钉 DWS API 及 AI 表格系统对接，实现周报数据自动同步。
* **主要文件**：`src/fill_weekly_report.py`
* **使用方式**：
  ```powershell
  # 运行周报自动同步流水线
  python src/fill_weekly_report.py
  ```

### 2️⃣ 广告数据与库存分析套件 (Amazon Ads & Inventory Collector)
利用 `ads-report-pipeline` 和 `amazon-ads-collector` 技能，一键拉取「南京欧洲组KS」店铺的 FBA 库存与广告花费，智能计算 Break-even ACOS。
* **核心命令**：`/xlsx` (Excel 数据处理)，`/pptx` (PPT 汇报生成)

### 3️⃣ 微信公众号抓取与语料库构建 (WeChat Articles Crawler)
自动化抓取微信公众号历史文章，输出 Markdown 格式的文稿，为品牌文案仿写和语料库提供输入。
* **路径**：`skills/wechat-articles-crawler`

---

## 🛠️ 环境配置与规范 / Environments & Guidelines

### 1. 路径配置文件 (`config/paths.json`)
当跨电脑或在不同环境下运行时，请务必更新该配置文件中的 `paths` 字段（如当前用户名为 `Administrator` 或 `china`），并运行验证脚本：
```powershell
# 验证配置路径的一致性
.\scripts\validate-paths.ps1
```

### 2. 广告 API 安全规则 (Amazon Ads CLI Guardrails)
* **写操作限制**：在未获得用户在聊天窗口中明确输入「确认」或「执行」指令之前，**禁止**调用任何修改亚马逊后台广告状态或预算的写操作命令。
* **前置预览**：所有调整必须先使用 `--dry-run` 并在本地向用户清晰展示调整前后的状态、数值与预算。

### 3. 数据拉取过滤规则 (Store Data Filtering)
* 所有的领星/亚马逊店铺数据拉取，必须**只筛选「南京欧洲组KS」的店铺数据**（对应店铺 sid 范围：`5018-5031`, `5751`）。

---

## 📝 贡献与维护 (Maintenance)

* **主分支**：`main`
* **代码规范**：所有生成的 Python 脚本必须包含**中英双语注释**，并在更新代码后使用 `rtk git status` / `rtk git diff` 进行 Token 优化的状态确认。

---
**Built with ❤️ for KovaScape**
