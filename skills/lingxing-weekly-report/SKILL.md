---
name: lingxing-weekly-report
description: 领星 ERP 数据拉取、周报/月报汇总、运营周会 Excel 表格自动填报、钉盘附件上传、自动可编辑权限设置及周会纪要/钉钉日志全自动提交工作流。用于周会数据收集、南京欧洲组KS店铺业绩分析、FBA库龄/月库销比精准核算及全流程自动化发布。
---

# 领星 ERP 周报与运营周会全自动化 Skill (lingxing-weekly-report)

本 Skill 总结并标准化了领星 ERP 数据拉取、店铺筛选、多维度汇总计算（周报、月度及 FBA 库龄）、**2026财年月度/周度目标匹配**、**《六组周会会议纪要》对齐填报**、**自动设置组员/群成员【可编辑 EDITOR】权限**、**dws 钉钉环境绑定前置条件**以及**组员复用指南与定制化 Prompt SOP**。

---

## 1. 适用场景与触发词
- **触发词**：`周报数据`、`运营周会`、`生成周报`、`领星数据拉取`、`南京欧洲组`、`填写周报Excel`、`周会会议纪要`、`定时周报推送`、`提交钉钉周报`
- **默认店铺范围**：仅筛选名称包含 `南京欧洲组KS` 的 15 个店铺 SID (`5030, 5751, 5019, 5024, 5026, 5025, 5031, 5023, 5021, 5020, 5027, 5029, 5028, 5022, 5018`)。
- **计价币种**：美金 (USD)。
- **核心逻辑执行脚本**：`src/run_all_weekly_reports.py`

---

## 2. 🔐 自动设置【可编辑 EDITOR】权限规则 (Automatic EDITable Permission)

每次每周自动生成《六组周会会议纪要2026MMDD.xlsx》并上传至钉盘后，系统**必须自动执行权限设置**，将文件节点赋予组员及群成员可编辑权限：

```bash
dws drive permission add --node <fileId_or_docUrl> --users <userIds> --role EDITOR -y
```

- **目标**：保证钉群“南京欧洲站￥$€£”内的组员点击卡片在线链接后，可直接在浏览器中打开并编辑表格，无需再次提交权限申请。

---

## 3. 🔑 组员环境前置条件：dws 钉钉授权绑定 (Prerequisite: dws Auth)

组员在首次运行周报自动化前，**必须在其本地电脑完成 `dws` (DingTalk Workspace CLI) 的登录绑定**，否则无法抓取 AI 表格或发送钉群通知。

### 绑定三步法：
1. **确认 dws 可执行文件**：确保 `D:\Zero Tools\DingTalk\bin\dws.exe` 或全局 `dws` 命令可用。
2. **执行扫码登录**：在终端运行 `dws auth login`，使用手机钉钉扫码完成身份授权。
3. **运行登录验证**：运行 `dws user me`，若正常输出组员个人信息，则表示 `dws` 绑定成功。

---

## 4. 2026财年内置目标数据库 (FY2026 Targets)

每周目标为当前报告月份目标的 $1/4$。目标数据源自 `南京欧洲组-2026财年目标测算.xlsx`。

### 销售额目标 (GMV Target in USD)

| 月份 (Month) | 组总目标 (Group Total) | 王祎个人 (Wang Yi) | 化一博 (Hua Yibo) |
| --- | --- | --- | --- |
| **2026-04** | $150,000 | $45,000 | $105,000 |
| **2026-05** | $90,000 | $27,000 | $63,000 |
| **2026-06** | $65,000 | $19,500 | $45,500 |
| **2026-07** | $120,000 | $48,000 | $72,000 |
| **2026-08** | $280,000 | $112,000 | $168,000 |
| **2026-09** | $280,000 | $112,000 | $168,000 |
| **2026-10** | $450,000 | $180,000 | $270,000 |
| **2026-11** | $550,000 | $220,000 | $330,000 |
| **2026-12** | $600,000 | $270,000 | $330,000 |
| **2027-01** | $720,000 | $324,000 | $396,000 |
| **2027-02** | $880,000 | $396,000 | $484,000 |
| **2027-03** | $950,000 | $427,500 | $522,500 |

---

## 5. 核心 API 与 MCP 接口映射 (API Mapping)

| 模块 / 数据源 | 调用的 MCP / API 工具 | 关键参数设置 | 关键提取字段与计算逻辑 |
| --- | --- | --- | --- |
| **AI 表格任务提取** | `dws aitable record list` | `--all --base-id R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG --table-id dv19yqvsgs3oebp3pcjys` | `jxzfinmckxuusjowbz5ca` (任务名称)<br>`sb82jyoeivzhh5is2guac` (负责人)<br>`8LkwFxC` / `y5s8sqzoulb4pdafd1mlo` (按 ISO 周数精准匹配本周与上周任务) |
| **产品表现数据** | `query_product_performance_asin_lists` | `sids`: 15个SID<br>`currency_code`: "USD"<br>`summary_field`: "asin"<br>`length`: 1000 | `volume` (销量)<br>`amount` (销售额)<br>`predict_gross_profit` (预估订单利润，**必须 * 0.6**)<br>`gross_profit` (结算利润)<br>`spend` (广告花费，正数展示) |
| **FBA 库存与库龄** | `get_fba_stock_list` | `sid`: 15个SID (多线程并发拉取)<br>`length`: 2000 | `afn_fulfillable_quantity` + `afn_reserved_quantity` + `reserved_fc_transfers` (**FBA可售+待调仓+调仓中**)<br>库龄分段: `inv_age_91_to_180_days` 等 |

---

## 6. 核心计算规则与公式 (Calculation Rules)

1. **真实订单利润额 (Order Profit in USD)**：
   $$\text{订单利润额} = \text{预估订单利润 (predict\_gross\_profit)} \times 0.6$$

2. **FBA 在库库存 (FBA On-hand Stock)**：
   $$\text{FBA在库库存} = \text{FBA可售} + \text{待调仓/预留} + \text{调仓中}$$

3. **数据位移与公式修正 (Formula Shift)**：
   - 环比表格更新时，旧 D列/J列 自动位移复制至 C列/I列。
   - C列与 I列的所有比率与衍生公式（客单价、利润率、ACOAS、日销等）**必须修正为引用自身 C/I 单元格**。
   - 最新周（D列与J列）的 `太仓仓库库存`、`额定资金`、`实际资金`、`资金使用率` 强制设为 `None` (留空)。

---

## 7. 组员复用与个性化配置指南 (Team Reuse & Customization SOP)

为了让团队内其他组员也能无缝复用本 Skill，组员可以通过简单的 Prompt 指令告知 Agent 自己的个人数据与文件路径。

### 👥 1. 组员首次使用配置 Prompt 模板 (First-time Configuration Prompt)

> **复制发送给 AI**：
> “我是组员【张三】，我的钉钉 User ID 是【1234567890】，我的模板文件路径是 `D:\MyWork\运营周报_张三.xlsx`。请帮我在周报自动化逻辑中将【张三】设为个人数据列的提取负责人，并更新模版路径。”

### 🔄 2. 组员日常执行 Prompt 模板 (Daily Execution Prompts)

- **场景 A：仅拉取数据并填报本地 Excel（不发群通知）**
  > “请帮我运行周报自动化，拉取上一周领星美金业绩，更新我的本地周报 Excel，先不要发送到群里。”

- **场景 B：完整执行并推送至个人/特定群聊（自动赋权可编辑）**
  > “请帮我生成上周的运营周报与周会纪要，更新表格并自动授权群成员可编辑权限后，将通知发送到钉群。”

---

## 8. 参数化脚本支持 (Command Line Flags)

执行脚本已升级支持命令行参数，组员亦可直接通过命令运行：

```bash
# 1. 组员认证校验
dws user me

# 2. 指定个人姓名与模板路径运行（包含自动 EDITOR 权限赋予）
python src/generate_weekly_meeting_report.py --user-name "张三" --user-id "1234567890" --template "D:\MyWork\周会纪要_张三.xlsx"

# 3. 预演测试模式 (Dry-Run: 不创建新文件、不发通知)
python src/run_all_weekly_reports.py --dry-run
```
