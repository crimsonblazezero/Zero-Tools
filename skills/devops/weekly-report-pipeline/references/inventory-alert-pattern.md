# 库存断货预警自动化模式

用于扫描 FBA 库存并推送预警到钉钉群。

## 架构

```
Cron (每天 9:00)
    ↓
inventory_alert.py (LingXing MCP)
    ├── 库存数据：get_fba_stock_list
    ├── 销量数据：query_product_performance_asin_lists
    └── 输出 → 钉钉群预警消息
```

## 数据源

| 数据 | MCP 工具 | 关键参数 |
|------|----------|----------|
| FBA 库存 | `get_fba_stock_list` | sid, length=2000, is_hide_zero_stock=0 |
| 近 30 天销量 | `query_product_performance_asin_lists` | sids, currency_code=USD, summary_field=asin |

## 预警阈值

| 级别 | 可售天数 | 颜色 | 说明 |
|------|----------|------|------|
| 🔴 断货风险 | < 7 天 | 红色 | 紧急补货 |
| 🟡 库存偏低 | < 14 天 | 黄色 | 关注 |
| 🟢 正常 | ≥ 14 天 | 绿色 | 无需处理 |

## 关键计算

```python
# 可售天数
days_remaining = afn_fulfillable_quantity / (30d_volume / 30)

# 合并多店铺同 ASIN
# 同一 ASIN 在多个店铺有库存时，合并显示店铺列表
```

## 输出格式

```
⚠️ 库存预警 2026-08-01
━━━━━━━━━━━━━━━
🔴 断货风险（<7天）：X个
  B0XXXX | SKU-XXX | 可售X天 | 日均销XX
🟡 库存偏低（<14天）：X个
  B0YYYY | SKU-YYY | 可售X天 | 日均销XX
━━━━━━━━━━━━━━━
合计：X个SKU需关注
```

## 边界处理

1. **日均销量为 0**：跳过（无历史数据，不算预警）
2. **库存为 0**：不显示（已断货）
3. **数据缺失**：记录日志，不阻塞其他数据

## 调试模式

```bash
python inventory_alert.py --dry-run
```

## 相关文件

- `inventory_alert.py`：主脚本
- `config.py`：阈值配置
