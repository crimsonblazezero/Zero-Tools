---
name: lmx_mcp_integration
description: >-
  领星 ERP 官方 Streamable HTTP MCP Server 配置与使用指南。
  当用户需要拉取亚马逊 ERP 数据（销售、利润、库存、广告）时触发。
tags: [lingxing, mcp, amazon-erp, ads, inventory, sales]
metadata:
  author: agnes
  created: 2026-07-26
  updated: 2026-07-26
---

# LingXing ERP MCP Integration

领星 ERP 官方提供的 Streamable HTTP MCP Server，用于从 Amazon 运营数据中自动拉取销售、利润、库存和广告报表。

## Connection Info

- **URL**: `https://openmcp.lingxing.com/mcp-servers/lingxing-mcp`
- **Auth Header**: `X-Mcp-Key`（由领星后台 AI助手 → 管理MCP 生成）
- **Rate Limit**: ~1次/秒，并发调用容易触发「服务器繁忙」错误码 42703
- **Tool Count**: 31 tools，以只读为主

## Tool Capability Map

### ✅ Read-only (Confirmed Working)

| Tool | Purpose | Key Notes |
|------|---------|-----------|
| `get_my_sids` | List all accessible shops | Returns sid, alias, seller_id |
| `ad_auth_shops` | List ad-authenticated shops | More structured, includes profile_id; recommended |
| `get_profit_report_msku` | MSKU profit detail | total can be thousands; 50/pagelimit |
| `query_order_profit_list_gross_profit` | Aggregated gross profit | Supports filters/sorting |
| `get_fba_stock_list` | FBA inventory with aging | seller_group_name is comma-separated multi-store |
| `query_erp_competitive_monitor` | Competitor monitoring list | Read-only view of existing monitors |
| `query_erp_follow_sale_monitor` | Follow-sale monitor list | Read-only view |
| `query_erp_keyword_ranking_*` | Keyword rank monitoring | Read-only |
| `ad_campaign_report` | Ad campaign-level report | ⚠️ Susceptible to rate-limit errors |
| `ad_campaign_keyword_report` | Keyword search term report | |
| `ad_campaign_product_report` | Sponsored product target report | |
| `ad_campaign_search_term_report` | Search term report | |
| `ad_campaign_targeting_report` | Targeting/bidding report | |
| `ad_campaign_group_report` | Campaign group report | |

### ❌ Denied / Not Available

| Tool | Reason |
|------|--------|
| `add_custom_indicator` / `update_custom_indicator` | No permission: "暂无操作权限" |
| `get_custom_indicator_list` | No permission |
| `get_custom_indicator_field` | Related to disabled feature |
| `create_erp_competitive_monitor` | Write operation not permitted |
| `create_erp_follow_sale_monitor` | Write operation not permitted |
| `create_erp_new_monitor` | Write operation not permitted |
| `create_erp_keyword` | Write operation not permitted |

## Field Mapping Reference

### `get_profit_report_msku`

Key fields in each record:
- `totalSalesAmount` — sales amount per SKU
- `totalSalesQuantity` — unit count sold
- `grossProfit` — raw gross profit before full cost deduction
- `adsSpCost`, `adsSbCost`, `adsSdCost`, `adsSbvCost`, `adsSarCost` — ad spend by type
- `currencyCode` — USD/EUR/GBP/CAD/JPY/etc.
- `country` — Chinese locale name like "美国", "英国", "德国"
- `reportDateMonth` — YYYY-MM format
- `principalRealname` — responsible person name

### `get_fba_stock_list`

Key fields:
- `afn_fulfillable_quantity` — FBA available sellable stock
- `seller_group_name` — comma-separated store group names (e.g., "南京欧洲组KS-BE,南京欧洲组KS-DE,...")
- Age bucket fields: `inv_age_91_to_180_days`, `inv_age_181_to_270_days`, `inv_age_271_to_365_days`, `inv_age_366_plus_days`
- Note: Some listings use different naming like `age_X_to_Y` — verify actual keys before aggregating

## Common Pitfalls

1. **Nested JSON**: MCP result may wrap inner data as stringified JSON: `{result: "{\"code\":0,..."}` → always do `json.loads(result)` twice when needed
2. **Rate limits**: `ad_campaign_report` in particular fails under concurrency; serialize calls with small delays
3. **Pagination**: Many reports return 50 items/page even when total is thousands — check `total` field and paginate
4. **Multi-store grouping**: FBA stock `seller_group_name` can contain comma-separated values across multiple stores; filter by substring match
5. **Empty/null handling**: Fields may be `null`, `""`, or numeric `0`; always use `float(val or 0)` or equivalent
6. **Currency mismatch**: Sales/profit records may span multiple currencies — normalize to USD if needed for reporting
7. **ACoS calculation**: Take directly from ad report tools when possible; don't manually compute from `adsSpCost / totalSalesAmount` as primary source

## Configuration Pattern (Hermes config.yaml)

```yaml
mcp_servers:
  LingXing-MCP:
    url: https://openmcp.lingxing.com/mcp-servers/lingxing-mcp
    headers:
      X-Mcp-Key: <your-key>
    transport: streamable_http
```

## References

See `references/weekly-report-pipeline-notes.md` for business rule mappings used in weekly report automation.
