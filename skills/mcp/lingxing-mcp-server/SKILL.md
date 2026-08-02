---
name: lingxing-mcp-server
description: >
  领星MCP服务器配置指南。当用户需要配置、调试或调用领星ERP的MCP服务端点时触发。
  包含Streamable HTTP连接方式、鉴权Header、工具列表、权限边界和自动化用法。
tags: [mcp, lingxing, erp, sales, ad, report]
---

# 领星 MCP 服务器配置

## 基本信息

| 项目 | 值 |
|------|-----|
| 协议 | Streamable HTTP |
| URL | `https://openmcp.lingxing.com/mcp-servers/lingxing-mcp` |
| 鉴权Header | `X-Mcp-Key: <your-key>` |
| QPS限制 | 1次/秒 |
| 官方文档 | `https://www.lingxing.com/help/article/mcp` |

## Hermes Agent MCP 配置格式

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  lingxing-mcp:
    url: https://openmcp.lingxing.com/mcp-servers/lingxing-mcp
    transport: streamable-http
    headers:
      X-Mcp-Key: your_x_mcp_key_here
```

或 CLI:
```bash
hermes mcp add lingxing-mcp --url https://openmcp.lingxing.com/mcp-servers/lingxing-mcp --transport streamable-http --header "X-Mcp-Key:your_key"
```

> ⚠️ Header字段名是 `X-Mcp-Key`，不是 `Authorization`

## 已确认的工具清单（按类别）

### 店铺基础
| 工具名 | 功能 | 权限 |
|--------|------|------|
| `get_my_sids` | 获取用户绑定店铺 | ✅ 可用 |
| `get_multi_platform_shop_list` | 多平台店铺信息 | ✅ 可用 |
| `ad_auth_shops` | 广告授权店铺列表 | ✅ 可用 |
| `erp_listing` | Listing列表查询 | ✅ 可用 |

### 利润与报表
| 工具名 | 功能 | 权限 |
|--------|------|------|
| `get_profit_report_msku` | MSKU维度利润报表 | ⚠️ 见下方注意事项 |
| `query_order_profit_list_gross_profit` | 订单利润毛利报表（通用汇总） | ✅ 可用，但仅做总量校验 |
| `query_product_performance_asin_lists` | 产品表现ASIN列表 | ✅ 已确认可用 |

**⚠️ 毛利数据正确来源说明（2026-07-26 实测修正）**：

| 数据源 | 用途 | 可靠性 |
|--------|------|--------|
| Excel「订单毛利润」列 (col 38) | **月实际毛利额** | ✅ 最可靠，需手动下载 |
| MCP `gross_profit` | 结算毛利润，非订单毛利润 | ✅ 用于对比参考 |
| MCP `predict_gross_profit` ×0.6 | ~~估算订单毛利~~ | ❌ **不可靠**：月度偏差约65%，不可作为正式数据 |

> **关键决策**：月实际毛利额应以用户下载的 Excel 文件为准，不要依赖 MCP `predict_gross_profit ×0.6` 估算。详见 references/product_perf_gross_profit_fields.md。

### 利润与报表 — 接口选择决策树

> ⭐ **周报复盘优先用 `query_product_performance_asin_lists`**，其次才用其他两个。详见下方详情。

#### ⭐ `query_product_performance_asin_lists`（推荐主数据源）

**核心数据映射（2026-07-26 验证）**：

| MCP 字段 | Excel/ UI 列名 | 说明 |
|----------|---------------|------|
| `volume` | 销量 | int，完全对齐 |
| `amount` | 销售额 | CNY字符串，÷6.8109=USD |
| `net_amount` | 净销售额 | CNY字符串，÷6.8109=USD |
| `gross_profit` | **结算毛利润** | ❗不是订单毛利润！对应Excel「结算毛利润」列 |
| `predict_gross_profit` | 订单毛利（MCP预估口径） | ❌ **不能作为月度实际毛利额使用**；该字段是下单时估算值，通常偏高。月度数据与人工下载 Excel「订单毛利润」列差异显著（约差65%），详见下方【⚠️ 毛利数据不可用】 |
| `ad_sales_amount` | 广告销售额 | CNY字符串，÷6.8109=USD |
| `spend` + `ads_sp_cost` + `shared_ads_sb_cost` + `shared_ads_sbv_cost` + `ads_sd_cost` | 广告花费（SP+SB+SBV+SD） | 全CNY，分别÷汇率加总 |
| `currency_code` | 币种 | 本次调用内全部记录一致，固定为 `CNY` |

**⚠️ 两种毛利字段不可混用**：
- `gross_profit` → **结算毛利润**（采购成本、头程成本结完后才扣入），值可能远小于 `predict_gross_profit`，甚至为负
- `predict_gross_profit` → **订单毛利（MCP预估口径）**，不等于实际结算值，通常不等于人工下载的 Excel「订单毛利润」列。详见 references/product_perf_gross_profit_fields.md 的【毛利数据差异】章节。 | ✅ 用这个 |
- 周报复盘使用 `predict_gross_profit`
- Excel 中另有「结算毛利润」列（约$1,636 vs 订单毛利$14,836），是最终实际值

**关键坑 3（2026-07-26 新增）：所有金额字段全是CNY，统一汇率 6.8109**
- MCP `query_product_performance_asin_lists` 返回的所有金额字段（`amount`, `net_amount`, `gross_profit`, `predict_gross_profit`, `spend`, `ad_sales_amount`, `return_amount` 等）**统一为 CNY**
- 不管美站/英站/加站/德站，汇率都是 **6.8109**
- 转换方式：`usd_value = cny_value / 6.8109`
- ❌ 不要按各站点 `price_list[].source_rate` 转换（英站 source_rate=9.0145，会导致错误）
- ✅ 统一除以 6.8109 即可

**实测验证（2026-07-12~18，产品表现表全量）**：

```
          | 合计       | 王祎       | 化一博
----------|------------|------------|------------
销量      | 1,753 ✅   | 464        | 1,289
净销售额  | $74,279.03 ✅ | $16,532.53 | $57,746.49
订单毛利润| $14,836.49 ✅ | $1,397.45  | $13,439.04
广告花费  | $14,359.84 ✅ | $4,498.28  | $9,861.56
广告销售额| $56,258.66 ✅ | $14,539.39 | $41,719.27
```

每条记录的嵌套结构：
```python
data.list[i]
  principal_names[]           # ["王祎"] / ["化一博"] 负责人（用于拆分）
  parent_asins[0].sid         # "5018" → NS-KS筛选
  price_list[j].seller_name   # "南京欧洲组KS-US" → 店名筛选
  price_list[j].sid           # "5018"
  price_list[j].source_rate   # 站点汇率（用于识别站点，但金额换算统一用6.8109）
  volume                      # 销量（int）
  amount                      # 销售额（⚠️ 字符串！CNY，÷6.8109=USD）
  net_amount                  # 净销售额（⚠️ 字符串！CNY）
  gross_profit                # ❌ 结算毛利润（CNY）——周报复盘不要用它
  predict_gross_profit        # ✅ 订单毛利润（CNY，÷6.8109=USD）——周报复盘用这个
  ad_sales_amount             # 广告销售额（⚠️ 字符串！CNY）
  spend                       # 广告花费（⚠️ 字符串！CNY，SP部分）
  ads_sp_cost                 # SP广告费（⚠️ 字符串！CNY）
  shared_ads_sb_cost          # SB广告费（⚠️ 字符串！CNY）
  shared_ads_sbv_cost         # SBV广告费（⚠️ 字符串！CNY）
  ads_sd_cost                 # SD广告费（⚠️ 字符串！CNY）
  return_count                # 退货量
  return_amount               # 退款金额（⚠️ 字符串！CNY）
  currency_code               # 固定 "CNY"
```

**NS-KS筛选**：遍历 `parent_asins` 或 `price_list`，任一条目 `sid` 在 NS-KS SID 列表中即算。

**负责人拆分**：用 `principal_names[0]` 过滤。API 没有可靠的 `principal_uids` 参数可用，建议拉全后本地按 `principal_names` 拆分。

**⚠️ 分页注意**：
- 每页 `length=50`，产品表现API总记录可达270+
- 按 `sort_field=volume, sort_type=desc` 排序时，非零行通常集中在前50条
- 但仍需检查后续页是否有非零行（用 `if vol > 0 or amt > 0` 判断）
- 拉全后总量应与UI截图订单利润页面完全一致

#### ⚠️ `get_profit_report_msku`（不推荐用于周报复盘）

该接口返回的是**已结算/postedDate** 数据，以下单时间聚合的"预估利润"不包含未结算订单。导致：
- 销量仅为已结算部分（816单 vs UI 1753单）
- 币种混合且 `exchangeRate=1.0`，无法直接换算
- 与 UI「订单利润」页面口径不一致

> ⭐ 周报复盘优先用 `query_product_performance_asin_lists` + `predict_gross_profit`（周维度×0.6可行，月维度必须用下载Excel）

#### ⚠️ `query_order_profit_list_gross_profit`（备用，只做USD汇总校验）

该接口返回USD统一折算的汇总数据，但不支持按负责人拆分，适合做总量交叉校验。

### FBA `get_fba_stock_list` — 负责人字段、聚合与毛利修正

#### ⚠️ NS-KS 过滤：不要用 `group_by_seller_id`，用 `seller_group_name` + `seller_name`

`get_fba_stock_list` 返回的每条记录代表一个 ASIN/SKU，可能跨多个站点（卖家组）。很多 NS-KS 商品被跨站合并后，`group_by_seller_id` 是组合ID如 `A2A3VOMEFJC47N`，**不含任何 NS-KS 的站点SID**。如果按 SID 过滤会漏掉这些商品。

```python
def is_nsks_fba(item):
    sgn = item.get('seller_group_name', '') or ''
    sn = item.get('seller_name', '') or ''
    return '南京欧洲组KS' in sgn or '南京欧洲组KS' in sn
```

实测差异：按 `group_by_seller_id` 只命中 125 条，按 `seller_name` 含 "南京" 能命中 137 条。差值来自跨站合并的库龄为0的空壳商品。

#### ⚠️ 分页拉取：必须用大 `length` + offset 循环 + item.id 去重

- API 的 `length` 参数只接受以下值之一：**20, 50, 100, 200, 500, 1000, 2000, 5000**；传其他值会报错 "页条数必须在范围内"
- 每次调用必须检查 `data.total` 字段，用 offset=500, 1000... 循环拉取
- **同一条商品可能跨多次 API 调用重复出现**：每次按 `item.id` 去重
- 旧缓存只拿 500 条会导致库龄数据严重偏低（王祎 91-180天从 145 变成 85）
- 2026-07-26 实测：total=2894，每页 500，至少需 6 页

#### ⚠️ FBA 负责人拆分：`principal_names` 为空，必须用 `asin_principal_list`

**真实 API 行为**：FBA 库存返回的 `principal_names` 字段**始终为空**（即使有负责人）。负责人数据只存在于 `asin_principal_list` 中。

```python
# ✅ 正确
p_list = item.get('asin_principal_list', [])

# ❌ 错误：FBA 接口 `principal_names` 始终为 []
p_list = item.get('principal_names', [])
```

**聚合维度区分**：
- **组整体**：所有 `asin_principal_list` 包含该负责人的商品都计入（含多人共管共享商品）
- **个人行**（如 Excel "王祎个人"）：仅统计 `asin_principal_list == ['王祎']` 的独有 ASIN（`len == 1`）
- 两种维度的库龄/库存数量差异可能很大，不可混用

#### ⚠️ `predict_gross_profit` 毛利额需要 ×0.6 修正

MCP `query_product_performance_asin_lists` 返回的 `predict_gross_profit` 是订单预估毛利，但采购和头程成本没有完全扣光。最终输出时需要：

```python
actual_gp_usd = predict_gross_profit * 0.6 / RATE
```

对应毛利率也需要用修正后的毛利额重新计算，不能直接用原始 `predict_gross_profit / net_amount`。

> 这是 2026-07-26 用户确认的业务规则，适用于周报毛利额/毛利率输出。

#### ⚠️ NS-KS 过滤：不要用 `group_by_seller_id`，用 `seller_group_name` + `seller_name`

`get_fba_stock_list` 返回的每条记录代表一个 ASIN/SKU，可能跨多个站点（卖家组）。很多 NS-KS 商品被跨站合并后，`group_by_seller_id` 是组合ID如 `A2A3VOMEFJC47N`，**不含任何 NS-KS 的站点SID**。如果按 SID 过滤会漏掉这些商品。

```python
def is_nsks_fba(item):
    sgn = item.get('seller_group_name', '') or ''
    sn = item.get('seller_name', '') or ''
    return '南京欧洲组KS' in sgn or '南京欧洲组KS' in sn
```

实测差异：按 `group_by_seller_id` 只命中 125 条，按 `seller_name` 含 "南京" 能命中 137 条。差值来自跨站合并的库龄为0的空壳商品。

#### ⚠️ 分页拉取：必须用大 `length` + offset 循环 + item.id 去重

- API 的 `length` 参数只接受以下值之一：**20, 50, 100, 200, 500, 1000, 2000, 5000**；传其他值会报错 "页条数必须在范围内"
- 每次调用必须检查 `data.total` 字段，用 offset=500, 1000... 循环拉取
- **同一条商品可能跨多次 API 调用重复出现**：每次按 `item.id` 去重
- 旧缓存只拿 500 条会导致库龄数据严重偏低（王祎 91-180天从 145 变成 85）
- 2026-07-26 实测：total=2894，每页 500，至少需 6 页

#### ⚠️ FBA 负责人拆分：`principal_names` 为空，必须用 `asin_principal_list`

**真实 API 行为**：FBA 库存返回的 `principal_names` 字段**始终为空**（即使有负责人）。负责人数据只存在于 `asin_principal_list` 中。

```python
# ✅ 正确
p_list = item.get('asin_principal_list', [])

# ❌ 错误：FBA 接口 `principal_names` 始终为 []
p_list = item.get('principal_names', [])
```

**聚合维度区分**：
- **组整体**：所有 `asin_principal_list` 包含该负责人的商品都计入（含多人共管共享商品）
- **个人行**（如 Excel "王祎个人"）：仅统计 `asin_principal_list == ['王祎']` 的独有 ASIN（`len == 1`）
- 两种维度的库龄/库存数量差异可能很大，不可混用

#### ⚠️ `predict_gross_profit` 毛利额需要 ×0.6 修正

MCP `query_product_performance_asin_lists` 返回的 `predict_gross_profit` 是订单预估毛利，但采购和头程成本没有完全扣光。最终输出时需要：

```python
actual_gp_usd = predict_gross_profit * 0.6 / RATE
```

对应毛利率也需要用修正后的毛利额重新计算，不能直接用原始 `predict_gross_profit / net_amount`。

> 这是 2026-07-26 用户确认的业务规则，适用于周报毛利额/毛利率输出。

### 广告系统
| 工具名 | 功能 | 权限 |
|--------|------|------|
| `ad_campaign_report` | 广告活动报告 | ✅ 可用 |
| `ad_campaign_keyword_report` | 关键词投放报告 | ✅ 可用 |
| `ad_campaign_product_report` | 广告商品报告 | ✅ 可用 |
| `ad_campaign_search_term_report` | 搜索词报告 | ✅ 可用 |
| `ad_campaign_group_report` | 广告组报告 | ✅ 可用 |
| `ad_portfolio_report_shop` | 广告组合报告（店铺维度） | ✅ 可用 |
| `ad_campaign_targeting_report` | 自动投放/商品投放报告 | ✅ 可用 |

### ERP监控
| 工具名 | 功能 | 权限 |
|--------|------|------|
| `query_erp_competitive_monitor` | 竞品监控列表（只读） | ✅ 可用 |
| `query_erp_follow_sale_monitor` | ASIN跟卖监控列表（只读） | ✅ 可用 |
| `query_erp_keyword_ranking_*` | 关键词排名监控（只读） | ✅ 可用 |
| `query_erp_new_monitor` | 店铺监控列表（只读） | ✅ 可用 |

### ❌ 不可用（需权限开放）
| 工具名 | 说明 |
|--------|------|
| `add_custom_indicator` | 「暂无操作权限」 |
| `update_custom_indicator` | 「暂无操作权限」 |
| `get_custom_indicator_list` | 「暂无查看权限」 |
| `create_erp_*` 系列 | 预计也返回无权限 |

> ⚠️ 自定义指标报表相关功能目前未开放，需要通过领星后台申请权限或等待开通

## QPS限制处理

QPS = 1次/秒。并行数据拉取时必须串行调用。如果批量请求多个维度数据，建议：
- 单个任务内请求间隔 ≥ 1秒
- 使用 `time.sleep(1)` 在循环中
- 或使用 async with rate limiter

## MCP 配置验证

```bash
# 1. 检查服务是否可达
curl -sI https://openmcp.lingxing.com/mcp-servers/lingxing-mcp

# 2. 列出当前MCP服务
hermes mcp list

# 3. 测试连接
hermes mcp test lingxing-mcp

# 4. 读取tools schema
hermes mcp schema lingxing-mcp <tool_name>
```

## 注意事项

1. `get_fba_stock_list` 返回的总记录数较大，默认 `length=20` 不够，需显式设到 2000+
2. 所有 `create_*`、`add_*`、`update_*` 相关工具都需要额外权限
3. Streamable HTTP是**标准HTTP请求**，不是SSE，不要用 `http` transport
4. **不要直接调领星HTTP端点绕过Hermes MCP**：领星端点（`http://openmcp.lingxing.com/mcp-servers/lingxing-mcp`）会返回 308 Permanent Redirect，正常做法是通过 `mcp__LingXing_MCP__*` 工具调用。如果确实需要从Python直接调，需要在config里拿到 `X-Mcp-Key` 并使用 `https://` 重定向后的实际URL
5. **分页拉取时检查每页item数**：如果返回的 item 数量 < length，说明已经到最后一页。产品表现API单页50条，总记录可达270+
