# 领星 MCP + 周报自动化 实测笔记 (2026-07-26)

## 连接信息

- URL: `https://openmcp.lingxing.com/mcp-servers/lingxing-mcp`
- Auth Header: `X-Mcp-Key: b7a40552c273e2757ada0bfd047d20a9`（凭据已脱敏，勿在此文件保留明文）
- QPS限制: ~1次/秒，并发调用会触发"服务器繁忙"错误码 42703
- 可用工具: 31个，大部分只读，自定义指标类接口无权限

## 实测接口状态

| 接口 | 状态 | 备注 |
|------|------|------|
| `ad_auth_shops` | ✅ 正常 | 返回店铺 profile_id、sid、alias，推荐用于广告查询 |
| `get_my_sids` | ✅ 正常 | 返回 33 个店铺 |
| `get_profit_report_msku` | ✅ 正常 | total=4453，每页约50条，需分页拉取 |
| `get_fba_stock_list` | ✅ 正常 | total=3972；卖家组名含多店逗号分隔列表 |
| `get_ad_campaign_report` | ⚠️ 服务器繁忙 | 并发调用时概率失败，需串行或降速重试 |
| `get_custom_indicator_list` | ❌ 暂无操作权限 | 自定义指标未开放 |
| `add_custom_indicator` | ❌ 暂无编辑权限 | 同上 |
| `update_custom_indicator` | ❌ 暂无编辑权限 | 同上 |
| `create_erp_*` 系列 | ❌ 预计无权限 | 写操作全部受限 |

## 关键字段名

### 利润报表 (`get_profit_report_msku`)

```json
{
  "totalSalesAmount": 1132.86,       // 销售额
  "totalSalesQuantity": 68,          // 销量（单位数）
  "grossProfit": 1132.86,            // 原始毛利额（未扣减全部成本）
  "adsSpCost": 0.0,                  // SP广告费
  "adsSbCost": 0.0,                  // SB广告费
  "adsSdCost": 0.0,                  // SD广告费
  "adsSbvCost": 0.0,                 // SBV广告费
  "currencyCode": "GBP",             // 币种
  "country": "英国",                  // 国家
  "reportDateMonth": "2026-08",      // 报告日期月份
  "principalRealname": "胡浩源",      // 负责人姓名
  "localName": "SKU显示名"            // 本地SKU名称
}
```

### FBA库存 (`get_fba_stock_list`)

```json
{
  "seller_group_name": "南京欧洲组KS-BE,南京欧洲组KS-DE,...",  // 多店逗号分隔
  "afn_fulfillable_quantity": 241,                            // FBA可售
  "inv_age_91_to_180_days": 0,                               // 91-180天库龄
  "inv_age_181_to_270_days": 0,                              // 181-270天库龄
  "inv_age_271_to_365_days": 0,                              // 271-365天库龄
  "inv_age_366_plus_days": 0                                 // 366天以上库龄
}
```

### 广告报表 (`ad_campaign_report`)

字段见 MCP 工具定义，通常包含：spend、sales、impressions、clicks、acos 等。
**注意**: ACoS 应直接从广告报表取，不手动用利润报表的 ads cost / sales 计算。

## 王祎月度目标

| 月份(财年) | GMV目标 | 毛利润目标 | 毛利率 |
|-----------|---------|-----------|--------|
| 11月      | 45,000  | 3,600     | 8.0%   |
| 12月      | 27,000  | 1,800     | 6.67%  |
| 1月       | 19,500  | 1,500     | 7.69%  |
| 2月       | 48,000  | 3,200     | 6.67%  |
| 3月       | 112,000 | 7,200     | 6.43%  |
| 4月       | 112,000 | 9,600     | 8.57%  |

> 当前是2026年7月，目标表可能需要更新7-10月数据。脚本中先用默认值。

## 业务计算规则（用户指定）

| 指标 | 公式 | 说明 |
|------|------|------|
| 毛利额 | 领星 grossProfit × **0.6** | 部分成本未扣减的修正系数 |
| ACoS % | 直接取领星广告报表 | 不从利润报表算 |
| 周目标销售额 | 月目标 ÷ 4 | 固定分配 |
| 90-180天库存目标 | 当前FBA库存 × **0.75** | 按当前存量推算 |
| 181-270天库存目标 | 当前FBA库存 × **0.8** | 按当前存量推算 |
| 近30天库销比 | FBA总库存件数 ÷ 日均销售件数 | **用件数不用金额** |
| 下期目标累加 | 本月未完成部分 → 下周目标 | 待确认是否启用 |

## 店铺筛选

### 南京欧洲组 KS（周报范围）

15个店铺，通过 `seller_group_name` 包含 `"南京欧洲组KS"` 来过滤 FBA 库存。
对应 alias 列表：`南京欧洲组KS-BE/BR/CA/DE/ES/FR/IE/IT/JP/MX/NL/PL/SE/UK/US`

### 排除项

- `深圳-雯选-EU-*` — 不属于周报范围
- `若驰家居-深圳组-LingFei-*` — 不属于周报范围

## 钉钉日志模板

- 模板名: "运营周复盘（周一9:00前提交）"
- 模板 ID: `17a14a44cdee2e409b88ad14ca68d77b`
- 类型:
  - type 1 = 文本/Markdown
  - type 2 = 数字
  - type 9 = 附件
  - type 13 = 富文本
  - type 16 = 复杂控件（组长销售数据/组长库存数据，需手动处理）

## 钉钉 AI 表格 — 周重点任务

- Base ID: `R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG`
- 链接: https://alidocs.dingtalk.com/i/nodes/R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG
- 用途: 提取最新一周任务，填入"下周重点工作及计划"字段
- 提取规则: 日报书写时间是 WK23 → 提取 WK24 数据；找到最新一周的记录
- MVP状态: 未实现，需先探索 `dws aitables` CLI 子命令

## 钉钉日志提交命令

```bash
dws report entry submit \
  --template-id <TEMPLATE_ID> \
  --contents-file <JSON_FILE> \
  --format json \
  [--profile <PROFILE_NAME>]
```

contents JSON 格式:
```json
[
  {"key": "字段名", "sort": "序号", "type": "1", "content": "内容", "contentType": "markdown"},
  {"key": "字段名", "sort": "序号", "type": "2", "content": "数值", "contentType": "origin"}
]
```

## 调度配置

- 首次执行: 每周五 16:00
- 失败重试: 同一天内每 2 小时最多重试一次
- 投递通知: 成功后**不群通知**
- 防重复: lock file 记录上次成功时间戳

## 已知坑

1. MCP 结果外层有嵌套 JSON: `{result: "{\"code\":0,..."}` → 需要 `json.loads` 二次解析
2. `ad_campaign_report` 并发调用容易触发限流，必须串行+短暂延迟
3. 利润报表一页只 50 条，total=4453 → 需要翻页或用更大的 page size（如果 API 支持）
4. `seller_group_name` 是逗号分隔的多店名 → 用 `in` 匹配即可
5. 字段可能为 `null`、空字符串 `""`、或数字 `0` → 统一 `float(val or 0)`
