# 领星数据字段映射与数据口径

## 利润报表 `get_profit_report_msku`

### 核心返回字段

| 字段 | 类型 | 用途 | 注意 |
|------|------|------|------|
| `totalSalesAmount` | Number | 销售额（原始币种） | **必须先乘 exchangeRate 转 USD** |
| `totalSalesQuantity` | Int | 订单量 | |
| `grossProfit` | Number | 毛利额（未完全扣减成本） | 最终汇总后 ×0.6 |
| `totalAdsCost` | Number | 广告花费 | **负值**，汇总取 abs() |
| `totalAdsSales` | Number | 广告带动销售额 | 不用于 ACoAS 分母 |
| `currencyCode` | String | 币种 | USD / GBP / EUR / JPY / CAD / PLN |
| `exchangeRate` | Float | 汇率 | 多数为1.0；部分小币种可能也为1.0，需 fallback |
| `storeName` | String | 店铺名 | **主要筛选字段**：`南京欧洲组KS-US` 等 |
| `seller_group_name` | String | 卖家组名 | 备选筛选字段 |
| `principalRealname` | String | 负责人姓名 | 按人聚合用 |
| `country` | String | 国家 | 美国/英国/德国/日本/波兰/加拿大 |
| `msku` / `asin` | String | MSKU / ASIN | 维度标识 |

### storeName 匹配模式

```python
def is_ks_shop(store_name: str) -> bool:
    return any(kw in store_name for kw in [
        "南京欧洲组KS", "KS-US", "KS-UK", "KS-DE", "KS-JP", "KS-CA", "KS-PL"
    ])
```

### 分页拉取策略

```python
offset = 0; limit = 2000
while True:
    raw = client.call("get_profit_report_msku", {
        "startDate": start, "endDate": end,
        "searchField": "seller_sku", "length": limit, "offset": offset,
        "orderStatus": "All",
    })
    data = parse_response(raw)
    records = data["data"]["records"]
    if not records: break
    yield records
    if len(records) < limit: break
    offset += limit
```

实测 2026-07-12~18: total=2475, size=2000 → 需要2页。

## FBA 库存 `get_fba_stock_list`

### 关键字段

| 字段 | 用途 |
|------|------|
| `seller_group_name` | 筛选：包含 "南京欧洲组KS" |
| `sid` | 店铺ID，可用于精确匹配 |
| `afn_fulfillable_quantity` | 可售库存件数 |
| `inv_age_91_to_180_days` | 90-180天库龄件数 |
| `inv_age_181_to_270_days` | 181-270天库龄件数 |
| `inv_age_271_to_365_days` | 271-365天库龄件数 |
| `inv_age_366_plus_days` | 366天+库龄件数 |

实测 2026-07-12~18: total=3972, 每页500 → 需分页拉满。南京欧洲组KS约138条。

### ⚠️ 当前测试库存不完整

第一页只拿到500条，实际3972条。生产脚本必须循环分页拉取全量，否则库龄数据偏低。

## 指标计算规则

### ACoAS（正确口径）
```
ACoAS = sum(abs(totalAdsCost)) / sum(totalSalesAmount)
```
- 先统一货币为 USD（amount × exchangeRate），再求比值
- **不要用广告报表**，直接来自利润报表
- 不用 ACOS

### 毛利额修正
```
adjusted_profit = sum(grossProfit × exchangeRate) × 0.6
```
仅用于毛利额/完成率口径，**不用于 ACoAS 分母**。

### 周目标
```
week_target = month_goal_gmv / 4
next_week_target = week_target + max(month_goal - already_spent, 0)
```

### 库龄目标存量
```
target_90_180 = current_90_180 × 0.75
target_181_270 = current_181_270 × 0.80
```

### 库销比
```
stock_ratio = fulfillable_qty / (weekly_orders / 7)
```
分子是**件数**，分母是**日均件数**，不是美元金额。

## 已知坑

1. **Python requests 连领星MCP可能返回空body**：Hermes Agent 内置 MCP 工具正常，但 Python 脚本直连可能失败。优先用 Hermes 内置 MCP 调用，或读取已缓存结果文件。
2. **MCP QPS ≤1/秒**：连续调用间隔 ≥1.1s，触发"服务器繁忙"时等待30秒重试。
3. **分页遗漏导致严重低估**：第一页只拿50条时 ACoAS=3.2%，全量后=28.6%。这是致命bug。
4. **JPY 等小币种 exchangeRate=1.0 的陷阱**：领星对某些币种可能默认返回1.0，必须有 fallback rate 表。
5. **FBA 库存筛选**：有些记录 `seller_group_name=None`，需同时检查 `store_name` 和 `sid`。
6. **DWS aitables 子命令路径**暂未确认可用，周重点任务读取逻辑待开发。
