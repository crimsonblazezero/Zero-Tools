---
name: weekly-report-pipeline
description: >-
  自动化周运营报告生成管道：从领星ERP、钉钉AI表格、本地Excel拉取数据，
  计算销售/毛利/库存指标，写入Excel并自动填报钉钉日志。
tags: [report, automation, lingxing, dingtalk, excel, pipeline]
metadata:
  author: agnes
  created: 2026-07-26
  updated: 2026-07-26
---

# Weekly Report Pipeline

自动化周运营报告生成，用于团队周报填报和数据收集。

## 适用场景

- 每周日下午自动生成员工/主管周报
- 从多个数据源汇总业务指标
- 自动填写钉钉日志报表模板
- Excel 数据收集表更新

## 核心数据源

| 数据源 | 用途 | 访问方式 |
|--------|------|---------|
| 领星 ERP MCP | 销售额、毛利额、广告费、A科S、FBA库存 | `LingXing-MCP` 工具集 |
| 钉钉 AI 表格 | 周重点任务、工作计划 | `dws aitables` CLI / API |
| 本地 Excel | 月度目标、历史数据对比 | 文件读写 |
| 钉钉云盘 | 模板文件、附件上传 | `dws drive` CLI |

## 关键业务规则

### 计算逻辑

| 指标 | 公式/来源 | 备注 |
|------|----------|------|
| **毛利润** | 领星 grossProfit × **0.6** | 因部分成本未扣减，需用此系数修正 |
| **ACoS%** | 直接取领星广告报表数据 | ⚠️ 不要手动算 ads_cost/sales |
| **周目标** | 月目标 ÷ 4 | 固定分配 |
| **90-180天库存目标** | 当前库存 × **0.75** | 库龄清货目标 |
| **181-270天库存目标** | 当前库存 × **0.8** | 库龄清货目标 |
| **库销比** | FBA总库存件数 ÷ 日均销售件数 | 用件数，不用金额 |
| **下期目标累加** | 本月未完成部分可加到下周日目标 | 需确认是否启用 |

### 店铺筛选规则

**南京欧洲组 KS 店铺列表**（固定）:
- BE、BR、CA、DE、ES、FR、IE、IT、JP、MX、NL、PL、SE、UK、US
- 共 15 个站点
- 通过 `ad_auth_shops` 或 `get_my_sids` 获取 sid 和 profile_id

**过滤条件**:
- `seller_group_name` 包含 `"南京欧洲组KS"`
- `alias` 以 `"南京欧洲组KS"` 开头
- 排除深圳雯选EU组和若驰家居深圳组

## 调度配置

```yaml
schedule: "every Friday 16:00"
retry_policy: "2h interval if failed same day"
notification: "success -> no group message"
```

**防重复执行**:
- 当天首次失败后，每 2 小时允许重试一次
- 同一天内最多执行 1 次成功 + 1 次重试
- 不同日期自动恢复运行
- 用 lock file 记录时间戳

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 周报Excel | `运营周会数据收集_王祎.xlsx` | 现有模板，直接更新行 |
| 基础数据Excel | `周报数据_王祎.xlsx` | 汇总表 + 明细表 |
| 钉钉日志 | 模板 "运营周复盘（周一9:00前提交）" | 自动生成草稿，人工审核后提交 |

## 字段映射

### 周报 Excel 列映射

| Excel列 | 数据项 | 来源 |
|---------|--------|------|
| D: 本周销售额完成 | total_sales | 利润报表合计 |
| E: 本周目标销售额 | week_target = month_target / 4 | 计算公式 |
| F: 周ACOAS | ACoS % | 广告报表或直接计算 |
| G: 周销售额达成率 | sales / week_target | 自动计算 |
| H: 月目标销售额 | month_gmv_target | 目标表 |
| I: 月实际销售额 | month_actual_sales | 利润报表合计 |
| J: 本月ACOAS | ACoS % | 广告报表或利润报表 |
| L: 月目标毛利额 | month_profit_target | 目标表 |
| M: 月实际毛利额 | gross_profit × 0.6 | 利润报表×修正系数 |
| N: 毛利额达成率 | adjusted / target | 自动计算 |
| O: 月库销比 | stock_units / daily_units | 自动计算 |

### 清货进度表列映射

| Excel列 | 数据项 | 计算公式 |
|---------|--------|----------|
| D: 90-180天当前存量 | inv_90_180 | FBA库存聚合 |
| E: 90-180天目标存量 | target_90_180 | current × 0.75 |
| F: 清货效率 | target / current | 自动计算 |
| G: 181-270天当前存量 | inv_181_270 | FBA库存聚合 |
| H: 181-270天目标存量 | target_181_270 | current × 0.8 |
| I: 清货效率 | target / current | 自动计算 |
| J: 271-365天当前存量 | inv_271_365 | FBA库存聚合 |
| K: 271-365天目标存量 | 0 | 暂无目标 |
| L: 清货效率 | - | 无 |
| M: 366天以上当前存量 | inv_366_plus | FBA库存聚合 |
| N: 366天以上目标存量 | 0 | 暂无目标 |

## 钉钉日志字段类型

| Type | 说明 | 使用场景 |
|------|------|----------|
| `1` (文本/Markdown) | 长文本字段 | 心得、问题、备注 |
| `2` (数字) | 数值字段 | 销售额、毛利额、ACoS |
| `9` (附件) | 文件上传 | Excel附件 |
| `13` (富文本) | 复杂控件 | 销售指标图表 |
| `16` (复杂控件) | 组长数据区域 | 可能需手动 |

## DingTalk Aitable 任务

- Base ID: `R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG`
- 链接: https://alidocs.dingtalk.com/i/nodes/R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG
- 用途: 提取"下周重点工作及计划"
- 规则: 最新一周的任务作为下周计划；上期完成工作可自动复制

## API 调用注意事项

### 领星 MCP 限制

1. **QPS 限制**: ~1次/秒，并发调用会触发"服务器繁忙"
2. **分页**: `get_profit_report_msku` total=4453，一页约50条，需翻页
3. **嵌套JSON**: MCP结果可能是 `{result: "{\"code\":0,...}"}` → 需要二次 `json.loads`
4. **空值处理**: 字段可能是 `null`, `""`, `0`, 或数字 → 统一安全转换

### 推荐调用顺序

```
1. get_my_sids / ad_auth_shops  # 获取店铺信息（一次性）
2. get_profit_report_msku       # 拉取利润报表（按日期范围，分页）
3. get_fba_stock_list           # 拉取库存（按店铺过滤）
4. ad_campaign_report           # 拉取广告数据（注意限流）
5. dingtalk report entry submit # 最后提交日志
```

## 错误处理

- 领星接口返回"服务器繁忙" → 降速重试 1次
- 钉钉提交失败 → 记录错误日志，不中断Excel生成
- AI表格暂不可用 → 标记"待人工填写"，不阻塞流程

## Reference Files

- `references/lingxing-mcp-notes.md` - 领星MCP字段映射和实测结果
- `references/dingtalk-report-template.md` - 日志模板字段清单
