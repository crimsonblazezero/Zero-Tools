---
name: dingtalk-weekly-report-automation
description: >-
  基于 Hermes Agent cron + dws CLI 的钉钉周报自动化工作流。
  定时从领星MCP拉取销售/库存/广告数据，生成Excel报表，提交钉钉OA日志模板。
  适用于每周五/周日下午自动执行运营周复盘、销售周报等周期性报表任务。
tags: [automation, dingtalk, dws, cron, lingxing-mcp, excel, weekly-report, oa-log]
metadata:
  author: agnes
  created: 2026-07-26
  updated: 2026-07-26
---

# DingTalk Weekly Report Automation

自动化钉钉OA周报生成与提交：定时调用领星MCP拉取业务数据 → 计算指标 → 更新Excel → 提交钉钉日志模板。

## 何时触发

- 用户说："配置周报自动化"、"每周五下午跑周报"、"设置cron周报任务"、"自动提交钉钉日志"
- 需要周期性（每天/每周）重复执行的跨系统数据同步任务

## 架构概览

```
Hermes Agent Cron Job
    ↓ (每周五 16:00 UTC+8)
Python 脚本：scripts/weekly_report.py
    ├── 领星MCP → 拉取利润报表 / FBA库存 / 广告报表
    ├── Python 计算 → 毛利×0.6、ACoS、库销比、目标达成率
    ├── openpyxl → 写入「运营周会数据收集_王祎.xlsx」
    ├── dws report entry submit → 填报钉钉日志模板
    └── （可选）上传Excel附件到钉盘
```

## 实现步骤

### Step 1: 编写数据处理脚本

核心功能（见参考文件 `references/python-script-structure.md`）：

1. **读取领星MCP数据** — 通过 `mcp__LingXing_MCP_*` 工具或直接HTTP调用
   - `get_profit_report_msku`: 销售额、毛利额、广告费
   - `get_fba_stock_list`: FBA库存及库龄分布
   - `ad_campaign_report`: ACoS（优先直取，fallback 到广告费/销售额）

2. **读取本地Excel目标** — 如「人员」sheet中的月目标数据

3. **计算业务指标** — 毛利修正×0.6、ACoS、目标完成率、库龄清货效率

4. **更新目标Excel** — openpyxl 写入对应sheet的行和列

5. **提交钉钉日志** — 调用 `dws report entry submit`，先 `template get` 获取字段定义，再构造JSON内容

### Step 2: 测试执行

在正式加入 cron 前，必须手动跑一次验证全流程：

```bash
# 方式A: Python脚本直接运行
python3 scripts/weekly_report.py --dry-run

# 方式B: 只测试数据拉取和Excel更新（跳过钉钉提交）
SKIP_DINGTALK=1 python3 scripts/weekly_report.py

# 方式C: 完整执行含钉钉提交
python3 scripts/weekly_report.py
```

验证清单：
- [ ] 领星数据是否按预期日期范围拉取？
- [ ] Excel中的每个字段值是否合理？（销售额是否过大/过小？）
- [ ] 毛利额是否已 ×0.6？
- [ ] 库存目标是否按 90-180天×0.8、181-270天×0.5、271-365天×0.3、366天以上×0.1 反推？
- [ ] 钉钉模板字段是否与 `template get` 返回一致？

### Step 3: 配置 Cron Job

使用 Hermes Agent cron 调度（推荐方式）：

```yaml
# 方案A: 直接执行 Python 脚本（推荐）
schedule: "0 16 * * 5"  # 每周五 16:00 UTC+8
prompt: |
  执行周报自动化脚本：
  python3 "C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\scripts\weekly_report.py"
  完成后报告执行结果，如果失败则记录错误。

# 方案B: 用 dws event + 自定义脚本
schedule: "every friday 16:00"
script: scripts/run_weekly_report.sh
```

⚠️ Cron 环境注意：
- Windows 路径用 `C:\...` 或 `/c/Users/...`
- Python 解释器路径可能需要完整路径：`C:\Python311\python.exe`
- 依赖包需确保环境中已安装：`openpyxl`, `requests`

### Step 4: 失败重试与防重复

脚本内部应包含：

```python
# Lock file 机制
if last_successful_run < today:
    should_run = True
elif elapsed_hours >= 2:
    should_run = True  # 2小时内最多重试一次
else:
    should_run = False

# 记录成功时间戳
record_success(now)
# 记录失败信息
record_error(error_msg, now)
```

**规则**：
- 当天首次失败后，允许每2小时重试一次
- 成功执行后记录时间戳，防止同一天重复提交
- 钉钉提交失败时，Excel 仍应更新保存；仅不记录为"成功"

## 关键业务规则速查

| 指标 | 公式 | 来源 |
|------|------|------|
| 毛利额 | predict_gross_profit × **0.6** ÷ 6.8109 | 领星产品表现表（原始值未扣全成本，周报/周会纪要统一口径） |
| ACoS % | **广告报表原始字段** | ad_campaign_report（非手算） |
| 周目标 | 月目标 ÷ 4 | 本地Excel |
| 90-180天库存目标 | 当前库存 × **0.8** | FBA库存 |
| 181-270天库存目标 | 当前库存 × **0.5** | FBA库存 |
| 271-365天库存目标 | 当前库存 × **0.3** | FBA库存 |
| 366天以上库存目标 | 当前库存 × **0.1** | FBA库存 |
| 库销比 | FBA总库存件数 ÷ 日均销售件数 | 件数÷件数，不是金额 |
| 日期范围 | 上周日 ~ 本周六 | 自然周定义 |

## 钉钉日志提交细节

### 铁律

1. **contents JSON 的 `key` 必须等于 `template get` 返回的 `field_name`**，一字不差
2. 长 JSON 必须写到临时文件，用 `--contents-file` 参数提交
3. `contentType`: type=1（文本）用 `markdown`，其他类型用 `origin`
4. 提交成功后返回中包含 `dingtalkOpenMarkdownLink`，必须返回给用户可点击链接

### 排查流程

遇到 `PARAM_ERROR` 时：
```bash
# 1. 重新拉取模板字段定义
dws report template get --name "运营周复盘（周一9:00前提交）" --format json

# 2. 对比实际字段名与预期是否有差异

# 3. 检查所有必填字段是否都有值（不要传空值给数字类型字段）
```

## 相关文件

- `references/python-script-structure.md` — Python脚本骨架与关键函数说明
- `references/dingtalk-report-template-fields.json` — 模板字段JSON示例
- `references/testing-checklist.md` — 测试执行清单
- `references/troubleshooting.md` — 常见故障排查
