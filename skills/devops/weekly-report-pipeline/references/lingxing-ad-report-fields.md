# 领星 MCP 广告报告字段说明

用于每日运营日报中的广告数据拉取。

## 工具

`mcp__LingXing_MCP__ad_campaign_report`

## 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `report_date` | 日期范围 | "2026-07-31 - 2026-07-31" |
| `profile_ids` | 广告店铺 ID 列表 | [12345, 67890] |
| `page` | 页码 | 1 |
| `length` | 每页条数 | 20 |
| `sort_field` | 排序字段 | "spends" |
| `sort_type` | 排序方向 | "desc" |

## 返回字段

| 字段 | 说明 | 用途 |
|------|------|------|
| `spends` | 广告花费 | 计算 ACoAS |
| `sales` | 广告销售额 | 计算 ACoAS |
| `direct_acos` | 直接 ACoS | 直接取用 |
| `clicks` | 点击数 | 计算 CPC |
| `impressions` | 曝光数 | 计算 CTR |
| `orders` | 广告订单数 | 计算转化率 |

## 使用示例

```python
# 拉取昨日广告汇总
result = ad_campaign_report(
    report_date="2026-07-31 - 2026-07-31",
    profile_ids=[12345, 67890],
    page=1,
    length=20,
    sort_field="spends",
    sort_type="desc"
)

# 汇总计算
total_spend = sum(r['spends'] for r in result['data']['records'])
total_sales = sum(r['sales'] for r in result['data']['records'])
acos = total_spend / total_sales if total_sales > 0 else 0
```

## 注意事项

1. **币种**：所有金额字段为 CNY，需转换为 USD（汇率 6.8109）
2. **延迟**：广告数据可能有 1 天延迟，昨日数据可能不完整
3. **限流**：并发调用可能触发"服务器繁忙"，需串行或降速
4. **空值**：字段可能为 null 或 0，需安全处理

## 相关文件

- `lingxing-mcp-notes.md`：领星 MCP 完整字段映射
