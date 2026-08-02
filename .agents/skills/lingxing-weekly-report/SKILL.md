---
name: lingxing-weekly-report
description: 领星 ERP 数据拉取、周报/月报汇总、运营周会 Excel 表格自动填报、钉盘附件上传、DWS 模板动态校验、保存预填卡片与通知王祎确认后提交，以及六组周会纪要全自动化工作流。
---

# 领星 ERP 周报与运营周会全自动化 Skill (lingxing-weekly-report)

本 Skill 总结并标准化了领星 ERP 数据拉取、店铺筛选、多维度汇总计算（周报、月度及 FBA 库龄）、**2026财年月度/周度目标匹配**、**《运营周会数据收集_王祎_v19_new.xlsx》最新覆盖填报**、**DWS 动态模版读取与参数组装**、**保存预览/通知王祎确认后提交**，以及**《六组周会会议纪要》自动推送**的标准 SOP。

---

## 1. 适用场景与触发词
- **触发词**：`周报数据`、`运营周会`、`生成周报`、`领星数据拉取`、`南京欧洲组`、`填写周报Excel`、`周会会议纪要`、`提交钉钉周报`
- **默认店铺范围**：仅筛选名称包含 `南京欧洲组KS` 的 15 个店铺 SID (`5030, 5751, 5019, 5024, 5026, 5025, 5031, 5023, 5021, 5020, 5027, 5029, 5028, 5022, 5018`)。
- **计价币种**：美金 (USD)。
- **核心逻辑执行脚本**：`src/run_all_weekly_reports.py`

---

## 2. 核心工作流与双报表接续机制 (Master Pipeline)

```
[领星 ERP & AI表格] ──> [1. 填报个人 Excel] ──> [2. 上传钉盘并设公开权限] ──> [3. 生成预填周报卡片并通知王祎]
                                                                                      │ (王祎回复“确认/执行”)
                                                                                      ▼
[4. 推送六组周会纪要到钉群] <── [自动执行 dws report entry submit 提交发布]
```

---

## 3. 报表一：《运营周会数据收集_王祎_v19_new.xlsx》更新与《运营周复盘》工作流

### 步骤 1：最新单周数据覆盖填报 (Not Cumulative)
目标文件：`C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎_v19_new.xlsx`
- **覆盖更新 `周报` Sheet**：
  - **最新单周数据直接覆盖**，不得直接在旧数据上做累加 (`+=`)。
  - **D列 (本周实际销售额)**：填入上周日到本周六的 `amount`
  - **F列 (本周ACOAS)**：填入 `spend / amount`
  - **G列 (周销售额达成率)**：填入公式 `=D2/E2`
  - **I列 (月实际销售额)**：填入当月1号至本周六的 `amount`
  - **J列 (本月ACOAS)**：填入当月1号至本周六的 `spend / amount`
  - **K列 (月实际销售额达成率)**：填入公式 `=I2/H2`
  - **M列 (月实际毛利额)**：填入 `predict_gross_profit * 0.6`
  - **N列 (毛利额达成率)**：填入公式 `=M2/L2`
  - **O列 (月库销比)**：填入最新计算值 $\frac{\frac{\text{FBA在库可售}+\text{待调仓}+\text{调仓中}}{\text{近7天平均日销}}}{30}$
- **更新 `清货进度表` Sheet**：
  - 更新 90-180天、181-270天、271-365天、365天以上的 FBA 库龄分段数据。

### 步骤 2：自动上传钉盘与权限配置
- 使用 `dws drive upload` 上传更新后的 `运营周会数据收集_王祎_v19_new.xlsx`。
- 自动提取 `spaceId`, `fileId`, `fileName`, `fileSize`, `docUrl`。
- 自动执行 `dws drive publish set --file-id <fileId> -y` 设置企业内公开与复制下载权限。

### 步骤 3：DWS 模版动态读取与参数组装
- 调用 `dws report template get --name "运营周复盘（周一9:00前提交）"` (ID: `17a14a44cdee2e409b88ad14ca68d77b`) 动态读取必填项。
- 必填项自动映射：
  - `周销量` (type: 2, contentType: origin)
  - `本周实际销售额$` (type: 2, contentType: origin)
  - `AcoAs（%）` (type: 2, contentType: origin)
  - `本周目标销售额$` (type: 2, contentType: origin)
  - `下周目标销售额$` (type: 2, contentType: origin)
  - `月目标销售额$` (type: 2, contentType: origin)
  - `月实际销售额$` (type: 2, contentType: origin)
  - `月AcoAs（%）` (type: 1, contentType: markdown)
  - `月目标毛利额$` (type: 2, contentType: origin)
  - `月实际毛利额（未扣除工资...）$` (type: 2, contentType: origin)
  - `毛利额完成比率（%）` (type: 2, contentType: origin)
  - `近30天库销比（FBA在库库存）` (type: 1, contentType: markdown)
  - `本周重点工作及完成情况` (type: 1, contentType: markdown, 从 AI 表格读取全量任务)
  - `下周重点工作及计划` (type: 1, contentType: markdown, 从 AI 表格读取全量计划)
  - **`附件` (type: 9, contentType: origin)**：结构化填入 `[{"spaceId":"...","fileId":"...","fileName":"运营周会数据收集_王祎_v19_new.xlsx","fileSize":...,"fileType":"xlsx"}]`

### 🔒 步骤 4：暂停自动提交，发送预填预览给王祎确认
- **原则**：**禁止自动直接调用 `dws report entry submit` 提交发布日志！**
- 生成 `report_payload.json` 后，先将完整提交预览卡片发送给王祎（可以通过钉钉单聊或对话框展示）。
- **必须等待王祎在聊天框中回复“确认”或“执行”指令后**，Agent 才可以执行最后的 `dws report entry submit` 进行正式提交！

---

## 4. 报表二：《六组周会会议纪要2026MMDD.xlsx》与钉群卡片

1. **自动生成与日期平移**：
   - 复制模板，表头 `C2`/`I2` 更新为上周日期（如 `7.19-7.25`），`D2`/`J2` 更新为最新周日期（如 `7.26-8.1`）。
   - 下方数据平移后，填充最新周的六组与化一博个人业绩及库存。
2. **钉盘上传与 `EDITOR` 权限赋权**：
   - 上传至钉盘，调用 `dws drive permission add` 赋予组员 `EDITOR`（可编辑）权限。
3. **推送钉群**：
   - 发送带有最新例会日期与指标速览的卡片消息到钉群【南京欧洲站￥$€£】。

---

## 5. 2026财年内置目标数据库 (FY2026 Targets)

每周目标为当前报告月份目标的 $1/4$。目标数据源自 `南京欧洲组-2026财年目标测算.xlsx`。

| 月份 (Month) | 组总目标 (Group Total) | 王祎个人 (Wang Yi) | 化一博 (Hua Yibo) |
| --- | --- | --- | --- |
| **2026-07** | $120,000 | $48,000 | $72,000 |
| **2026-08** | $280,000 | $112,000 | $168,000 |
| **2026-09** | $280,000 | $112,000 | $168,000 |
