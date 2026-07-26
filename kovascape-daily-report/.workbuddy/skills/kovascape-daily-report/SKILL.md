---
name: kovascape-daily-report
description: 从领星 MCP 拉取 15 个亚马逊站点（KovaScape 品牌）的真实库存和利润数据，运行规则引擎检测异常，生成 HTML 日报，分发钉钉待办，推送 Action Card。当用户要求"执行日报"、"生成 KovaScape 日报"、"跑日报流程"或自动化定时器触发日报任务时使用。
---

# KovaScape 日报执行流程

## 项目路径

```
D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\
├── config.yaml          # 15站点sid、阈值、webhook、dws配置
├── main.py              # 编排器
├── output/              # 输出目录
│   ├── listing_owners.json  # 负责人缓存（已预拉取）
│   └── snapshot-{date}.json
├── scripts/
│   ├── data_layer.py    # 数据模型 + MockDataSource
│   ├── rule_engine.py   # 8条P0规则 + OwnerResolver
│   ├── html_renderer.py # Jinja2 HTML模板
│   ├── todo_dispatcher.py # aitable写入 + dws待办
│   └── webhook_pusher.py  # Action Card推送
└── .workbuddy/skills/kovascape-daily-report/
    ├── SKILL.md          # 本文件
    └── scripts/
        └── merge_mcp_data.py  # MCP原始数据 → snapshot JSON
```

## 执行步骤（顺序执行）

### 0. 准备工作

```bash
cd /d/WorkBuddy/2026-07-25-08-51-51/kovascape-daily-report
mkdir -p output
```

确定美西日期（夏令时 PDT=UTC-7, 冬令时 PST=UTC-8）：
```bash
# 美西昨天 = 日报日期
# 2026年7月：夏令时 PDT = UTC-7
# 15:00 北京 = 00:00 美西当天
# 日报日期 = 昨天美西日期
```

### 1. 通过 MCP 拉取真实数据

**核心接口**：`query_product_performance_asin_lists` —— 一个接口包含 sales/profit/ad/inventory/ranking 全部数据。

对每个 KS- 站点，调一次 MCP：
```
{"sids": "5018", "offset": 0, "length": 500, "start_date": "昨天", "end_date": "昨天", "date_type": "purchase", "query_order_profit": true}
```

保存到 `output/raw/{sid}-performance.json`。

⚠️ 关键参数：
- `sids`：必须指定单个站点ID（不要拼多个，也不要漏掉——否则会拉全站！）
- `start_date` / `end_date`：都填美西昨天日期（一个站点一天的数据）
- `query_order_profit: true`：获取利润数据

15 个站点串行拉取，每站约 200-600 条记录。

### 1d. 合并原始数据为 snapshot JSON

```bash
python scripts/merge_mcp_data.py --date {美西日期} --output output/snapshot-{date}.json
```

此脚本读取 `output/raw/` 下所有 `{sid}-inventory.json` / `{sid}-profit.json` / `{sid}-listings.json`，合并为 `DailySnapshot` 格式。

### 2. 运行规则引擎

```bash
python scripts/rule_engine.py output/snapshot-{date}.json output/alerts-{date}.json
```

输出：`output/alerts-{date}.json`（包含6-8条P0异常）

### 3. 渲染 HTML 日报

```bash
python scripts/html_renderer.py output/snapshot-{date}.json output/alerts-{date}.json output/{date}.html
```

输出：`output/{date}.html`

### 4. 分发待办（写入 aitable + 创建 dws 待办）

```bash
python scripts/todo_dispatcher.py output/alerts-{date}.json "https://d70f70b3d5174e90a35cc59ddab837cc.app.codebuddy.work/{date}.html"
```

- 写入钉钉多维表格 `KovaScape工作大表 → 9.0_日报行动项`
- P0 + due≤4h 的 alert 创建 dws 待办（DING 强推）
- 自动去重：同日期+规则+MSKU 的记录会跳过

### 5. 推送钉钉 Action Card

```bash
python scripts/webhook_pusher.py --date {date} --url "https://d70f70b3d5174e90a35cc59ddab837cc.app.codebuddy.work/{date}.html"
```

### 6. 汇报结果

最终输出格式：
```
✅ KovaScape 日报 {date} 完成
   业绩：销售额 $X | 订单 Y | 毛利 $Z | TACoS W%
   异常：P0 × N 条
   待办分发：写入 A 条 | 去重跳过 B 条 | dws待办 C 条
   钉钉推送：成功
```

## 关键数据

### 领星 UID → 归属人

| 领星 UID | 姓名 | 系统key | dws userId |
|---------|------|---------|-----------|
| 10896311 | 王祎 | wang_yi | 17566881508928543 |
| 10923094 | 化一博 | hua_yibo | 17597998065506150 |

### 钉钉配置

- Webhook：`https://oapi.dingtalk.com/robot/send?access_token=ba74877458660cee8526c367981821c5493aa0ae0493d205574bc82e8fe620d7`
- 关键词：`广告`（Action Card 的 title 和 text 都必须含关键词）
- 加签 secret：无（仅关键词模式）

### dws 路径

```
node: C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2/node.exe
dws_js: C:/Users/Administrator/.workbuddy/binaries/node/cli-connector-packages/node_modules/dingtalk-workspace-cli/bin/dws.js
```

### 阈值基线

| 指标 | 值 | 说明 |
|------|-----|------|
| ACoS 盈亏线 | 50% | 硬线 |
| TACoS 当前目标 | 25% | 广告占总销售比 |
| 毛利率红线 | 18% | |
| 缺货阈值 | 7 days of supply | |
| 新品排除期 | 30天 | |
