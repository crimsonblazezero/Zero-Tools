# 每日运营日报自动化模式

用于每天早上自动推送昨日运营数据到钉钉群。

## 架构

```
Cron (每天 9:00)
    ↓
daily_report.py (LingXing MCP)
    ├── 销售数据：query_order_profit_list_gross_profit
    ├── 广告数据：ad_campaign_report
    └── 输出 → 钉钉群消息
```

## 数据源

| 数据 | MCP 工具 | 关键参数 |
|------|----------|----------|
| 销售额/毛利 | `query_order_profit_list_gross_profit` | start_date, end_date, search_type=1, currency_type=0 |
| 订单量 | 同上 | summary_field=country 或 seller |
| 广告花费 | `ad_campaign_report` | report_date, profile_ids |
| 环比 | 同上日期范围 [-1d, 0d] | 分两组对比 |

## 关键计算

```python
# ACoAS 计算
ACoAS = abs(ad_spend) / net_sales

# 环比百分比
change_pct = (today - yesterday) / yesterday * 100

# 库存可售天数
days_remaining = fulfillable_qty / (30d_volume / 30)
```

## 输出格式

纯文本，支持 emoji：

```
📊 运营日报 2026-08-01（环比 vs 07-31）
━━━━━━━━━━━━━━━
💰 销售额：$XX,XXX (+X.X%)
📈 毛利：$X,XXX (+X.X%)
🛒 订单量：XXX单 (+X)
📉 ACoAS：X.X%（vs 昨日X.X%）
━━━━━━━━━━━━━━━
📢 广告：花费 $XXX | ROAS X.X
```

## 配置要点

1. **店铺范围**：固定 15 个 KS 店铺 SID（5030,5751,5019...）
2. **币种**：CNY → USD 汇率 6.8109
3. **毛利修正**：`predict_gross_profit × 0.6`
4. **空值处理**：无数据时显示"暂无数据"而非 0

## 调试模式

```bash
python daily_report.py --date 2026-07-31 --dry-run
```

## 相关文件

- `daily_report.py`：主脚本
- `config.py`：配置（店铺列表、阈值等）
- `DAILY_REPORT_SPEC.md`：详细字段规格
