---
name: lingxing-weekly-report
description: 领星 ERP 数据拉取、周报/月报汇总、运营周会 Excel 表格自动填报并交王祎审核确认后自动提交运营周复盘日志（附件以钉盘链接贴正文）、六组周会纪要自动生成与推送工作流。
---

# 领星 ERP 周报与运营周会全自动化 Skill

## 1. 适用场景与触发词

- **触发词**：`周报数据`、`运营周会`、`生成周报`、`领星数据拉取`、`南京欧洲组`、`填写周报Excel`、`周会会议纪要`、`提交钉钉周报`
- **默认店铺范围**：仅筛选名称包含 `南京欧洲组KS` 的 15 个店铺 SID (`5018, 5019, 5020, 5021, 5022, 5023, 5024, 5025, 5026, 5027, 5028, 5029, 5030, 5031, 5751`)
- **计价币种**：美金 (USD)
- **统一入口脚本**：`src/weekly_report_pipeline.py`

---

## 2. 数据维度说明 (Scope Codes)

| Code | 含义 | 说明 |
|------|------|------|
| **100** | 全组 (Group) | 六组 15 店铺全量汇总，周报日志提交使用此维度 |
| **200** | 王祎个人 (WY) | principal_names 含 "王祎" 的 ASIN |
| **300** | 化一博个人 (HYB) | principal_names 含 "化一博" 的 ASIN |

> **周报日志（运营周复盘）只提交 100 全组数据。**  
> 周会纪要 Excel 同时填入全组(D列) 与化一博个人(J列) 数据。

---

## 3. 核心工作流 (Master Pipeline)

```
[领星 ERP & AI表格] ──> [1. 填报 Excel] ──> [2. 导入在线表格+授权] ──> [3. 组装 payload（在线表格链接贴备注）]
                                                                                      │
                                                                                      ▼
[4. 展示 Excel 数据给王祎检查] ──确认/执行──> [5. 自动提交运营周复盘日志] ──> [6. 推送六组周会纪要(自动，无需确认)]
```

> **关键闸门（2026-08-08 王祎拍板）**：
> - **报表一（运营周复盘日志）**：Excel 生成后**必须等王祎检查确认数据**，确认后才自动提交；未经确认禁止 submit
> - **报表二（六组周会纪要）**：维持不变，生成后自动推送，无需确认
> - **附件**：⚠️ **日志附件 type=9 实际不可用**——`entry submit` dry-run（CLI 参数校验）能过，但**后端 create_report 真实提交会拒绝**（"请求未通过后端参数校验 / success=false"）。正确方案（2026-08-09 实测确认）：**在线表格链接（doc import 生成，已授权 EDITOR）以 Markdown 贴入正文文本字段**（如备注），文件本体在线可编辑。若需文件本体，用钉盘链接贴正文。

### CLI 用法

```bash
# 默认日期全自动推算（基于“今天”计算上周日~本周六等区间）
python src/weekly_report_pipeline.py --report1          # 仅报表一：运营周复盘
python src/weekly_report_pipeline.py --report2          # 仅报表二：六组周会纪要
python src/weekly_report_pipeline.py --all              # 依次执行 report1 → report2

# 可选覆盖日期
python src/weekly_report_pipeline.py --all --week-end 2026-08-01 --meeting-date 2026-08-03

# Dry-run 模式（仅验证数据，不写入文件/不发送消息）
python src/weekly_report_pipeline.py --all --dry-run
```

### 🔐 自动设置权限（在线表格可编辑）

> **2026-08-09 修正**：钉盘文件（`drive upload`）是二进制附件，**无法设置 EDITOR 角色权限**（`drive permission add` 报 "can't set role"，且 `drive publish set` 报"节点不支持互联网公开"）。正确做法是**导入为在线电子表格再授权**：
> 1. `dws doc import --file <xlsx> --workspace 27227639280` → 返回在线表格 `documentUrl`（导入到「我的文件」空间）
> 2. `dws doc +access-grant --node <documentUrl> --to 王祎,化一博 --role EDITOR -y` → 授予编辑权限
> ⚠️ **版本要求**：`doc +access-grant` 需 dws **≥ v1.0.57**（2026-08-06 发布，含 Drive/文档权限改进）。旧版（如 8/3 的 v1.0.54）报 unknown flag。升级命令：`dws upgrade -y`。pipeline 已封装 `grant_editor()`：优先 dws.exe（≥v1.0.57），失败自动回退新版 dws.js（`C:\Users\china\.workbuddy\binaries\node\cli-connector-packages\node_modules\dingtalk-workspace-cli\bin\dws.js`）。
> 权限验证：`dws drive permission list --node <docId>` → 化一博=EDITOR、创建者=OWNER、群=DOWNLOADER（可查看下载）。
> pipeline 已封装为 `import_excel_as_online()`（doc import + 授权一步完成），报表一/报表二自动调用。

### 🔑 运行登录验证前置条件
终端验证绑定的正确命令是：
```bash
dws auth status
```

---

## 4. 报表一：《运营周会数据收集_王祎_v19_new.xlsx》与《运营周复盘》

### 步骤 1：最新单周数据覆盖填报 (Not Cumulative)

目标文件：`E:\#工作资料\月复盘\运营周会数据收集_王祎.xlsx`（公司电脑实际路径；pipeline 常量 `EXCEL_TEMPLATE_R1` 已适配，家中版用 `C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎_v19_new.xlsx`）

- **覆盖更新 `周报` Sheet**（最新单周数据直接覆盖，禁止 `+=` 累加）：

| 列 | 含义 | 数据来源 |
|----|------|----------|
| D | 本周实际销售额 | `amount`（上周日~本周六） |
| E | 本周目标销售额 | 月目标 / 4 |
| F | 本周 ACOAS | `spend / amount` |
| G | 周销售额达成率 | 公式 `=D2/E2` |
| H | 月目标销售额 | FY2026 目标表 |
| I | 月实际销售额 | `amount`（当月1号~本周六） |
| J | 本月 ACOAS | 月 `spend / amount` |
| K | 月销售额达成率 | 公式 `=I2/H2` |
| L | 月目标毛利额 | FY2026 目标表 |
| M | 月实际毛利额 | **结算毛利 `gross_profit`（利润报表 query_order_profit_list，南京组）× 0.6**（2026-08-09 用户确认：与领星前台一致；采购与头程未完全扣减仍需打折；接口为 USD 无汇率换算） |
| N | 毛利额达成率 | 公式 `=M2/L2` |
| O | 月库销比 | `(FBA在库可售 + 待调仓 + 调仓中) / (近7天平均日销) / 30` |

- **更新 `清货进度表` Sheet**：90-180天 / 181-270天 / 271-365天 / 365天以上 FBA 库龄分段数据
  - 目标存量系数：90-180天=`0.8` / 181-270天=`0.5` / 271-365天=`0.3` / 366天以上=`0.1`

### 步骤 2：上传钉盘与权限配置（在线表格可编辑）

- `dws drive upload` 上传 Excel → 提取 `spaceId`, `fileId`, `fileName`, `fileSize`, `docUrl`（钉盘文件供日志附件字段/本体使用）
- `dws doc import --file <excel> --workspace 27227639280` → 导入为**在线电子表格**（可编辑）→ `docUrl` 用在线版
- `dws doc +access-grant --node <documentUrl> --to 王祎,化一博,高应婷 --role EDITOR -y` → 授予编辑权限（pipeline 常量 `EDITOR_NAMES` 已含高应婷；须用新版 dws.js，见上）
- ❌ 不再使用 `drive publish set`（钉盘节点不支持互联网公开）

### 步骤 3：DWS 模版动态读取与 Payload 组装

- 模板名称：`运营周复盘（周一9:00前提交）`
- 模板 ID：`17a14a44cdee2e409b88ad14ca68d77b`
- Payload 输出路径：`d:\Zero Tools\data\report_payload.json`

**完整字段映射与参考说明（详见 [field-mapping.md](file:///d:/Zero%20Tools/skills/data-science/lingxing-dws-weekly-report/references/field-mapping.md)）**

| # | key | sort | type | contentType | 数据来源说明 |
|---|-----|------|------|-------------|-------------|
| 1 | ~~附件~~（**payload 已移除**） | 56 | 9 | origin | ⚠️ 后端 create_report 拒绝 type=9（dry-run 能过、真实提交 PARAM_ERROR），**不再提交**；Excel 以**在线表格链接贴入「备注」**（2026-08-09 实测） |
| 2 | 周销量 | 20 | 2 | origin | 全组单周销量 `int(volume)` |
| 3 | 本周实际销售额$ | 21 | 2 | origin | 全组单周 `amount` |
| 4 | AcoAs（%） | 22 | 2 | origin | 全组单周 `spend / amount * 100` |
| 5 | 本周目标销售额$ | 23 | 2 | origin | 月目标 / 4 |
| 6 | 下周目标销售额$ | 24 | 2 | origin | 月目标 / 4 |
| 7 | 月目标销售额$ | 25 | 2 | origin | FY2026 目标表 |
| 8 | 月实际销售额$ | 26 | 2 | origin | 全组当月 `amount` |
| 9 | 月AcoAs（%） | 55 | 1 | markdown | 全组当月 `spend / amount * 100` |
| 10 | 月目标毛利额$ | 29 | 2 | origin | FY2026 目标表 |
| 11 | 月实际毛利额（未扣除工资、房租物业和财务成本等）$ | 30 | 2 | origin | 全组当月**结算毛利 `gross_profit`（利润报表筛南京组）× 0.6**（USD 无汇率换算） |
| 12 | 毛利额完成比率（%） | 31 | 2 | origin | `月实际毛利额 / 月目标毛利额 * 100` |
| 13 | 近30天库销比（FBA在库库存） | 57 | 1 | markdown | `(FBA总库存 / 近7天平均日销) / 30` |
| 14 | 当前库存数量——90-180天库龄 | 35 | 2 | origin | FBA 库龄 91-180 天 |
| 15 | 目标存量——90-180天库龄 | 47 | 2 | origin | `当前量 * 0.8` |
| 16 | 当前库存数量——181-270天库龄 | 38 | 2 | origin | FBA 库龄 181-270 天 |
| 17 | 目标存量——181-270天库龄 | 48 | 2 | origin | `当前量 * 0.5` |
| 18 | 当前库存数量——271-365天库龄 | 41 | 2 | origin | FBA 库龄 271-365 天 |
| 19 | 目标存量——271-365天库龄 | 49 | 2 | origin | `当前量 * 0.3` |
| 20 | 当前库存数量——366天以上库龄 | 44 | 2 | origin | FBA 库龄 365+ 天 |
| 21 | 目标存量——366天以上库龄 | 50 | 2 | origin | `当前量 * 0.1` |
| 22 | 本周清货计划是否符合预期？如否，写明原因 | 51 | 1 | markdown | 默认 "符合预期" |
| 23 | 周未达成重要目标/存在问题/原因/办法 | 0 | 1 | markdown | 留空 |
| 24 | 老品月库销比超过2个月的产品名称/降低库销比方案/预期需要多久完成 | 18 | 1 | markdown | **暂不统计**（当前均为新品/全新品，待有老品后启用；2026-08-09 用户确认） |
| 25 | 超过180天的SKU数量/以及对应的货量总和/预期多久清理完毕 | 19 | 1 | markdown | 动态：SKU数/货量总和/明细（**品名取第一个逗号前基础名**+MSKU，**≤20条**）+预期60天清完 |
| 26 | 本周重点工作及完成情况(事、量化、做到什么程度) | 17 | 1 | markdown | 从 AI 表格读取上周 WK 任务 |
| 27 | 下周重点工作及计划（事、量化、时间/不超3项） | 1 | 1 | markdown | 从 AI 表格读取本周 WK 任务 |

### 步骤 4：王祎检查确认（强制闸门，2026-08-08）

- **展示 Excel 关键数据给王祎**：本周/本月销售额、ACOAS、毛利额、达成率、库龄库存（可截图或摘要展示）
- **必须等王祎回复"确认/执行"后**，才可执行下一步自动提交
- 若王祎指出数据异常 → 先排查修正，再重新展示，直到确认

### 步骤 5：自动提交运营周复盘日志

**⚠️ 平台硬限制：钉钉日志 `report create` API 只支持文本组件（type=1），附件字段（sort=56, type=9）不支持接口提交**（官方文档原文："对应日志模板中的每个组件只允许是文本类型，其他类型组件暂不支持接口调用"）。实测 `contents` 中带附件字段一律返回 `PARAM_ERROR`。

**附件方案（钉盘链接贴正文）**：
1. `dws doc import <excel>` 导入为在线表格（已授权 EDITOR）→ 返回 `documentUrl`（推荐，可在线编辑）
2. **正文贴链接（type=9 附件后端不支持，2026-08-09 实测）**：在备注/汇总等文本字段贴在线表格链接：
   ```markdown
   [运营周会数据收集_王祎.xlsx（在线可编辑）](https://alidocs.dingtalk.com/i/nodes/<docId>)
   ```
3. 执行提交（王祎已确认后）：
   ```bash
   dws report entry submit --template-id 17a14a44cdee2e409b88ad14ca68d77b --contents '<json>' --yes
   ```
   （注意：`--contents-file` 有 cwd 解析 bug，用 `--contents` 单行 JSON 或 `--contents -` stdin）
4. 提交成功后用返回的 `dingtalkOpenLink`/`dingtalkOpenMarkdownLink` 给王祎跳转查看
5. **转发给高应婷（2026-08-09 用户要求，pipeline 已固化）**：报表一在线表格生成后自动 `chat message send --open-dingtalk-id DT2AUV82nT7PZbqyiPfiPSdOwuyiPmR29xgn` 发送链接（高应婷已授权 EDITOR）。手动等价命令：
   ```bash
   dws chat message send --open-dingtalk-id DT2AUV82nT7PZbqyiPfiPSdOwuyiPmR29xgn \
     --title "运营周复盘在线表格" --text "<周区间> 运营周复盘在线表格（已授权可编辑）：<docUrl>" -y
   ```

### 步骤 6：六组周会纪要（维持不变，自动推送）

- 生成《六组周会会议纪要2026MMDD.xlsx》→ 导入在线表格 + 授予 EDITOR 权限 → 自动推送钉群（卡片带可编辑链接）
- 此报表**无需王祎确认**，全自动执行
- **利润口径（2026-08-09 用户确认，报表一/报表二完全一致）**：
  - **订单利润额(*0.6, 结算·月口径) = 利润报表 `query_order_profit_list` 结算 `gross_profit`（南京组）× 0.6**（月口径 8-1~8-8，与报表一月实际毛利同一数值，数据环比 **D8/J8**）
  - **结算利润额 = 产品表现 `query_product_performance_asin_lists` purchase（下单时间）口径 Σ `gross_profit`**（月口径，**未×0.6**，数据环比 **D10/J10**；2026-08 实测全组 ≈ 6,814.38）
  - 产品表现 `predict_gross_profit`（预估）不再用于周会纪要利润行（已弃用）

---

## 5. AI 表格字段映射 (DingTalk AI Table)

| 常量 | 值 | 说明 |
|------|-----|------|
| `BASE_ID` | `R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG` | AI 表格 Base：周重点任务 |
| `TABLE_ID` | `dv19yqvsgs3oebp3pcjys` | 数据表：1.任务管理表 |

### 字段 ID 映射

| cellId | 字段名称 | 说明 |
|--------|----------|------|
| `jxzfinmckxuusjowbz5ca` | 任务名称 | 任务标题文本 |
| `sb82jyoeivzhh5is2guac` | 执行人 | 人员数组，含 userId |
| `y5s8sqzoulb4pdafd1mlo` | 截止日期 | ISO 日期字符串 |
| `8LkwFxC` | 周数 (WK) | 年度第几周，公式字段 |

---

## 6. FY2026 财年目标数据库

目标数据源自 `南京欧洲组-2026财年目标测算.xlsx`。每周目标 = 当月目标 / 4。

### 销售额目标 (GMV Target in USD)

| 月份 | 全组 (Group) | 王祎 (WY) | 化一博 (HYB) |
|------|-------------|-----------|-------------|
| 2026-04 | $150,000 | $45,000 | $105,000 |
| 2026-05 | $90,000 | $27,000 | $63,000 |
| 2026-06 | $65,000 | $19,500 | $45,500 |
| 2026-07 | $120,000 | $48,000 | $72,000 |
| 2026-08 | $280,000 | $112,000 | $168,000 |
| 2026-09 | $280,000 | $112,000 | $168,000 |
| 2026-10 | $450,000 | $180,000 | $270,000 |
| 2026-11 | $550,000 | $220,000 | $330,000 |
| 2026-12 | $600,000 | $270,000 | $330,000 |
| 2027-01 | $720,000 | $324,000 | $396,000 |
| 2027-02 | $880,000 | $396,000 | $484,000 |
| 2027-03 | $950,000 | $427,500 | $522,500 |

### 毛利额目标 (Profit Target in USD)

| 月份 | 全组 (Group) | 王祎 (WY) | 化一博 (HYB) |
|------|-------------|-----------|-------------|
| 2026-04 | $12,000 | $3,600 | $8,400 |
| 2026-05 | $6,000 | $1,800 | $4,200 |
| 2026-06 | $5,000 | $1,500 | $3,500 |
| 2026-07 | $8,000 | $3,600 | $6,400 |
| 2026-08 | $40,000 | $16,000 | $24,000 |
| 2026-09 | $40,000 | $16,000 | $24,000 |
| 2026-10 | $36,000 | $14,400 | $21,600 |
| 2026-11 | $60,000 | $24,000 | $36,000 |
| 2026-12 | $70,000 | $31,500 | $38,500 |
| 2027-01 | $100,000 | $45,000 | $55,000 |
| 2027-02 | $115,000 | $51,750 | $63,250 |
| 2027-03 | $126,000 | $56,700 | $69,300 |
