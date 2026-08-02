# 产品表现表毛利字段对比（2026-07-26 验证）

## MCP 两种毛利字段

| MCP 字段 | Excel/ UI 列名 | 含义 | 周报复盘用？ |
|----------|---------------|------|-------------|
| `gross_profit` | 结算毛利润 | 采购成本、头程成本结完后才扣入；值可能远小于或为负 | ❌ 不用 |
| `predict_gross_profit` | **订单毛利（MCP预估口径）** | 下单时间口径含预估，与UI「订单利润」页面**部分**对齐，但月度偏差大 | ⚠️ 见下方【关键修正】 |

## ⚠️ 关键修正：月度毛利不能用 `predict_gross_profit ×0.6`

### 实测差异（NS-KS 2026-07-01~25 月度）

| 口径 | 王祎+化一博合计 (USD) | 对应关系 |
|------|----------------------|----------|
| MCP `predict_gross_profit` / 6.8109（原始） | $125,490.88 | 偏高，只是初步预估 |
| `predict_gross_profit ×0.6` / 6.8109 | $75,294.53 | ❌ **偏差约65%** |
| **用户下载 Excel「订单毛利润」列 (col 38)** | **$45,607.11** | ✅ **正确值，Antigravity 拉取完全对得上** |
| MCP `gross_profit` / 6.8109 | $4,679.69 | 结算毛利润，不是订单毛利 |

### 反推分析

每条 ASIN 记录的 `predict_gross_profit - net_amount` 差额占净销售额比例从 **32%~70%** 不等，说明该字段不是按固定比率扣除成本的。不同 ASIN 的成本结构差异很大，不存在一个统一的固定修正系数。

### 周度数据参考（2026-07-12~18，产品表现表全量）

| 负责人 | 订单毛利润 ($GP) | 结算毛利润 ($SGP) | 差额 |
|--------|------------------|-------------------|------|
| 王祎 | $1,397.45 | -$2,416.30 | -$3,813.75 |
| 化一博 | $13,439.04 | $4,039.82 | -$9,399.22 |
| **合计** | **$14,836.49** | **$1,636.01** | **-$13,200.48** |

周度数据与 Excel 一致（因为周期短、波动小），但**月维度必须用 Excel 下载的「订单毛利润」列**。

## 币种规则

MCP 返回所有金额字段均为 CNY，统一除以 **6.8109** 转 USD。
不管美站/英站/加站/德站/日站，汇率都是 6.8109。
❌ 不要按 `price_list[].source_rate` 分别转换（英站 source_rate=9.0145，会导致错误）。

## 金额字段类型

以下字段全是**字符串**：`amount`, `net_amount`, `gross_profit`, `predict_gross_profit`, `spend`, `ad_sales_amount`, `ads_sp_cost`, `shared_ads_sb_cost`, `shared_ads_sbv_cost`, `ads_sd_cost`, `return_amount`
以下字段是 **int**：`volume`, `order_items`, `return_count`

转换函数：
```python
RATE_CNY_TO_USD = 6.8109

def to_usd(val_str):
    return float(str(val_str or '0').replace(',', '').replace('$', '').strip()) / RATE_CNY_TO_USD

def to_int(val_str):
    return int(str(val_str or '0').replace(',', '').strip() or '0')
```

## 正确的数据源决策树

```
需要毛利额时：
├── 月实际毛利额 → 必须用人工下载 Excel 的「订单毛利润」列 (col 38)
├── 周报复盘 → 可用 MCP predict_gross_profit × 0.6（短期相对准确）
└── 交叉校验 → 可用 query_order_profit_list_gross_profit（仅总量校验，不支持负责人拆分）
```

## `query_order_profit_list_gross_profit` 接口说明

- 功能：查询订单利润毛利报表，支持按 MSKU/ASIN/SKU 等维度汇总，支持按日期、币种筛选
- 在本 MCP 通道中该接口返回的全是 `$0.00`，可能是权限或参数问题
- 官方文档描述：查询订单利润毛利报表，支持按MSKU/ASIN/SKU等维度汇总，支持按日期、币种筛选
- 只能做总量校验，不支持按负责人拆分
