---
name: lingxing-weekly-report-Kanban
description: >-
  Use when the user wants to pull Amazon sales/ad profit data from LingXing ERP (跨境电商ERP), build a weekly/monthly business dashboard (经营周报/月报/数据看板/排名环比/父ASIN), or send the report to a DingTalk group (钉钉群). Triggers: "拉上周数据/拉上个月数据", "父ASIN销售广告利润", "经营周报看板", "BSR排名环比", "发送到钉钉/欧洲群", "lingxing周报", "lingxing看板", "月报/月度复盘/全年完成表/退款率/退货率/仓储费/库销比". Pulls order-profit reports at parent-ASIN granularity, cross-validates ads spend, enriches Chinese product names, optionally fetches BSR rank trends, builds a self-contained Chart.js HTML dashboard (monthly variant adds fee-structure/rating/refund-rate/annual-target columns), and sends it to a specified DingTalk group via the dws CLI.
---

# LingXing 经营看板周报（数据拉取 → 看板 → 钉钉发送）

一键完成：**从 LingXing ERP 拉取父ASIN维度销售/广告/利润数据 → 制作 HTML 数据看板 → 发送到钉钉群**。支持周报与月报。

## 0. 前置条件（先确认）

| 项 | 要求 |
|---|---|
| LingXing MCP | 可用（`get_my_sids` 能返回店铺列表） |
| 币种 | 统一用 **USD**（`currency_type=USD`），与 ERP 美元口径一致 |
| dws CLI | 完整路径：`C:/Users/china/.workbuddy/binaries/node/cli-connector-packages/node_modules/dingtalk-workspace-cli/bin/dws.js`（shell 直接调 `dws` 会报 MODULE_NOT_FOUND） |
| 输出目录 | 当前工作目录（CSV/HTML/JSON 均写在此） |

**店铺筛选**：默认只保留「南京欧洲组KS」开头的店铺（sid: 5018 US / 5022 UK / 5024 DE / 5019 CA / 5021 JP / 5023 IT / 5029 PL / 5030 BE 等15个）。若需其他组织（深圳雯选 4748-4757、若驰家居 4131-4138），修改 Step 2 的 `nj_all` 集合。

## 1. 拉取利润数据（父ASIN维度）

**接口**：`mcp__LingXing-MCP__query_order_profit_list`（订单利润报表，字段最全）

参数（周报示例）：
```
start_date=YYYY-MM-DD  end_date=YYYY-MM-DD
currency_type=USD  summary_field=parent_asin  turn_on_summary="1"
date_summary_type=1  search_type=2  service_type=1
length="20"  offset="0..N"  sort_type=desc
source_service=mcp  external_service_mark=1
```

**分页拉取**：每页 20 条，`offset` 从 0 递增直到某页 `list` 长度 < 20 或累计条数 = 接口 total。响应超过 token 上限会自动存为 `tool-results/*.txt` 文件——**合并时 glob 匹配要覆盖全部时间戳段**（如周数据文件可能是 `*query_order_profit_list-1785*.txt`，缺一页数据就不全）。

**完成标准**：合并后记录数 = 各页 list 长度之和，且父ASIN无重复、无缺失。

## 2. 筛选店铺 + 补中文品名

1. **筛选**：记录按 `sids` 字段（字符串数组）归属店铺，只保留 `sids ⊆ 南京组sid集合` 且 `parent_asins` 非空非 `['-']` 的记录。
2. **中文品名**：调用 `mcp__LingXing-MCP__erp_listing`（`sids` 传目标店铺逗号分隔，`length=200` 分页，`offset=0,200,...` 直到 total），从返回的 `parent_asin` + `local_name` 建立映射。
   - 注意：部分新品的子ASIN挂在**不同父ASIN**下，需先建 `asin → local_name` 映射，再按子ASIN反查补齐。
   - 中文品名 = `local_name` 第一个逗号前部分，去掉 `(XX站)` 后缀。

**完成标准**：目标父ASIN 100% 有中文品名（无法匹配的标注缺失原因，如 PL/BE 新品）。

## 3. 交叉验证数据准确性（必做）

| 校验 | 方法 | 通过标准 |
|---|---|---|
| 内部一致性 | 接口 total_sum vs 明细求和 | 差异 < 0.1（浮点精度） |
| 跨接口勾稽 | 利润表 vs `query_product_performance_asin_lists` total_sum | spend/ad_sales_amount 绝对值一致 |
| 广告勾稽 | `ad_campaign_product_report` / `ad_campaign_report`（本币）折算 | 隐含汇率 6.5~7.2，广告订单数 ≈ 利润表 ad_volume |

**完成标准**：三项校验全部通过，否则在报告中标注口径差异。

## 4. 可选：排名趋势 + 环比（周报推荐）

- **销售环比**：拉取**上一统计周**利润表（统计周=周日~周六；如本期为 7-26~8-1，则上期=7-19~7-25），按父ASIN对比 `amount`，计算 `(本期-上期)/上期`。
- **整体KPI环比**：合并上期利润文件 → 筛选南京组 → 汇总上期 KPI（vol/amt/net/gross/spend/ads/advol/acos/gm/roas/ads_ratio/acoas），与本期对比，供 KPI 卡片显示「vs 上期」。
- **BSR排名趋势**：`mcp__xydc-mcp__get_asin_bsr_trends`（2 credits/次，按单ASIN查）。先从 `erp_listing` 选每个父ASIN的主力子ASIN（在售 + rank 最优）。**仅支持 US/CA/MX/BR/UK/DE/FR/ES/IT/JP**——PL/BE 站点查不了，标注"—"。
- 周环比口径：上期均值(前7天) vs 本期均值(后7天)；排名数值越小越靠前，负变化 = 排名上升。

**完成标准**：每父ASIN要么有排名环比，要么有明确缺失原因。

## 5. 生成 HTML 看板

自包含单文件（Chart.js 4.4.1 CDN + Google Fonts），建议瑞士国际主义编辑风（浅色）：
- 字体：Space Grotesk（数字）+ Noto Sans SC（中文）+ IBM Plex Mono（ASIN/标签），全站 `tabular-nums`
- 配色：暖纸底 `#f2f1ee`、墨黑 `#17150f`、靛蓝强调 `#3b4fd8`；语义色：蓝=销售、绿=毛利/排名上升、琥珀=广告、红=风险
- 布局：网格线驱动（1px细线+2px墨黑主框），KPI 金融终端式顶部色条，无阴影
- 数据以 JSON 内嵌于 `const DATA = ...`；明细表点击表头排序
- **榜单图表（01/02区）为 TOP10**，y 轴标签统一「中文品名 · 站点简称」（如 `195宽层板 · US`），**不加 ASIN**；若 TOP10 内出现同品名同站点重复，再追加父ASIN末4位兜底
- **KPI 卡片带整体环比**：每张卡底部显示「vs 上期」一行（↑/↓ + 百分比 + 上期值），语义色：销售额/毛利/销量/毛利率/广告销售额上升=绿（利好），ACOS/ROAS 方向**反转**（ACOS 升=红、ROAS 降=红），广告花费变动用蓝色（中性）
- **ACOAS 指标（必带）**：ACOAS = 广告花费 ÷ **总销售额**（区别于 ACOS = 广告花费 ÷ 广告销售额）。总览 KPI 的「综合 ACOS」卡同时显示 ACOS（主值）+ ACOAS（副值）；全量明细表在 ACOS 列后加 ACOAS 列，色块分级 绿 ≤15% / 黄 15–25% / 红 >25%
- 完成后用 Node `new Function(js)` 校验内嵌 JS 语法

**完成标准**：HTML 生成、JS 语法通过、关键数据（KPI/TOP榜）肉眼可读。

## 6. 发送到钉钉群

钉钉群消息**不支持 HTML 内联渲染**，两种方式（先问用户）：
- **文件附件**（推荐，保留完整图表）：`--msg-type file --file-path <html路径>`
- Markdown 摘要 + 文件附件

```bash
DWS="C:/Users/china/.workbuddy/binaries/node/cli-connector-packages/node_modules/dingtalk-workspace-cli/bin/dws.js"

# 找群（list-my-groups 返回全部群，含 title + openConversationId）
node "$DWS" chat group list-my-groups --format json

# 预览（必做，真实发送前）
node "$DWS" chat message send --group "<openConversationId>" \
  --msg-type file --file-path "<html绝对路径>" --dry-run --format json

# 实际发送
node "$DWS" chat message send --group "<openConversationId>" \
  --msg-type file --file-path "<html绝对路径>" --format json

# 验证送达
node "$DWS" chat message list --group "<openConversationId>" --time "<发送时间>" --limit 5 --format json
```

**完成标准**：返回 `success:true` 且群消息列表能看到 `[文件] <报告名>`。

## 7. 月报扩展模板（月报必做，周报跳过）

月报在周报基础上增加**费用结构/质量/目标完成**维度。字段来源如下（全部 USD，`date_summary_type=3` 按月汇总，一次拉取即可）：

### 7.1 父ASIN月报字段（利润报表直接给或可算）

| 字段 | 计算/来源 | 说明 |
|---|---|---|
| 月销量 / 月销售额 / 月毛利润 / 月利润率 | `volume` / `amount` / `gross_profit` / `net_gross_margin` | 与周报同字段，整月汇总 |
| 月退款率 | `refund_amount_rate`（**数量口径**：退款数量÷销量） | ⚠️ 字段名含 amount 但实测是**数量/数量**；若要「退款金额÷销售额」需自算 `refund_amount/amount` |
| 月退货率 | `return_rate`（退货件数÷销量） | 接口已算好；`return_quantity`(全渠道) 比 `fba_return_goods_count`(仅FBA) 全 |
| 月广告费占比 | `spend_rate`（接口已算好） | 如 0.2264 = 22.64%（= 广告花费/销售额） |
| 月FBA仓储费占比 | `fba_storage_fee` ÷ `amount`（费用为负，取绝对值） | 不含长期仓储；若含长期用 `total_stock_fee` |
| 月产品成本占比 | `purchase_costs` ÷ `amount`（取绝对值） | |
| 月海运费占比 | `logistics_costs` ÷ `amount`（取绝对值） | ⚠️ 常见为 0：头程运费录入延迟（type=202 明细数量有值金额=0），不是真无海运成本 |
| 月库销比 | (FBA在库 + FBA在途 + 待调仓 + 调仓中) ÷ 月销量 | 库存来自 `get_fba_stock_list`，见 7.5 |

### 7.2 评分/评论数

- 来源：`erp_listing` 的 `stars`（评分，如 4.3）+ `reviews_num`（评论数，如 54）
- 月报运行时**重新拉取** listing（评分实时变化），构建 `parent_asin → stars/reviews_num` 映射，0销量新品标注"—"

### 7.3 全年销售额/利润完成表

- **目标数据源**：`E:\#工作资料\月复盘\汇报\<最新月份目录>\2026财年运营月复盘---运营六组 王祎-*.xlsx` **第一个sheet「全年完成总表」**
- 表结构：行=月目标销售额/实际销售额/目标毛利率/实际毛利率/目标毛利额/实际毛利额/毛利额完成率；列=财年12个月（2026-04 ~ 2027-03）+ 总计
- **口径（用户确认）**：南京欧洲组KS = 六组 = 王祎+化一博；币种 **USD**；财年 **2026-04-01 ~ 2027-03-27**；全年目标销售额 **5,135,000**、目标毛利额 **580,000**
- 月报做两件事：
  1. **当月完成率**：本月实际销售额 ÷ 本月目标销售额、本月实际毛利额 ÷ 本月目标毛利额
  2. **YTD累计**：财年至今（4月~本月）实际 vs 目标累计，进度条展示
- 读取失败时（文件改名/目录不存在）：标注"目标数据缺失"，完成率列留空，不阻断发送

### 7.4 月度环比（月报）

- 上期对比 = **上个月**（自然月），同样 `currency_type=USD` + `date_summary_type=3` 拉整月，按父ASIN对比 `amount/gross_profit`
- 注意：不要用周报的"周日~周六"口径，月报按自然月

### 7.5 月库销比与库龄段库存（用户口径）

**库存范围**：仅「南京欧洲组KS」名下 5 个仓（各仓对应 sid，需**分仓调用** `get_fba_stock_list`）：
| 仓库 | sid | fulfillment_channel |
|---|---|---|
| KS-US 美国仓 | 5018 | AMAZON_NA |
| KS-CA 加拿大仓 | 5019 | AMAZON_NA |
| KS-UK 英国仓 | 5022 | AMAZON_EU |
| KS-EU 欧洲仓 | 5024（返回 group_by_sid=EU-5） | AMAZON_EU |
| KS-JP 日本仓 | 5021 | AMAZON_JP |

**调用参数**：`is_parant_asin_merge="1"`（父ASIN合并）、`is_cost_page="0"`、`is_hide_zero_stock=0`、`sort_field=total_volume`、`sort_type=desc`、`length=100`。**响应可能 >3MB 落盘到 tool-results**，需从文件解析；`total > length` 时按 offset 翻页拉全（每仓 total 通常 <100，1 页够）。

**字段映射（已验证，用户口径）**：
| 用户口径 | 接口字段 |
|---|---|
| FBA在库 | `afn_fulfillable_quantity` |
| FBA在途 | `afn_inbound_shipped_quantity`（已发运在途；**勿用** `afn_inbound_working_quantity`，那是处理中总量） |
| 待调仓 | `reserved_fc_transfers` |
| 调仓中 | `reserved_fc_processing` |
| 库龄 91-180 | `inv_age_91_to_180_days` |
| 库龄 180-270 | `inv_age_181_to_270_days` |
| 库龄 270-365 | `inv_age_271_to_330_days` + `inv_age_331_to_365_days` |
| 库龄 365+ | `inv_age_365_plus_days` |

**计算**：按 `parent_asin_arr[0]` 跨仓汇总 → 库销比 = (在库+在途shipped+待调仓+调仓中) ÷ 月销量；总览额外展示 4 个库龄段合计。参考样例：2026-08 实测 78 个父ASIN、分子合计 58,296（在库33,519/在途shipped21,130/待调仓3,135/调仓中512）。

### 7.6 月报看板布局与交互规范（用户确认版）

数据多 → **Tab 三页签**（单 HTML 文件内分页，钉钉附件体验不变）：

**① 总览**
- KPI 卡：销售额/毛利润/广告花费/退款率(额)/月销量/库存合计/库龄≥91天/广告销售额
- **广告花费卡 ext 只显示 `ACOS x% · ACOAS y%`**（勿加"占销售%"——与 ACOAS 重复）
- **退款率卡**：主值=金额口径(退款金额÷销售额)，ext 注明数量口径(退款数量÷销量 N件)
- 01 销售/毛利 TOP10（标签「中文品名 · 站点」）
- 02 费用结构占比条形 + 「退款与退货」块（退款金额/退款数量/退货数量）
- 03 全年目标：进度条(7月+YTD两行) + **Chart.js 柱状图**（目标灰柱 vs 实际蓝/绿柱，7月+YTD两组）
- 04 库存与库销比：在库/在途/待调仓/调仓中条形 + **库龄四段独立条形**（91-180/180-270/270-365/365+）

**② 全量明细**
- **隐藏全 0 父ASIN**（销量=0 且销售额=0），表头标注"显示 X/Y，已隐藏 Z 个"
- **去掉父ASIN列**；**冻结中文品名列**（`position:sticky;left:0`，横向滚动固定）；表格容器 `max-height:640px` 纵向滚动
- **库龄四段分四列**（库龄91-180/180-270/270-365/365+）
- 列含环比：销量环比/销售环比/毛利环比（▲绿/▼红）
- **「⛶ 全屏」按钮**：Fullscreen API 切换（`detailSec.requestFullscreen()` / `exitFullscreen()`），CSS `#detailSec:fullscreen{...}` 拉高表格 `calc(100vh-140px)`，含 webkit 兼容

**③ 同款多站点对比**
- 按中文品名分组，≥2站点有销售才展示
- 每款一张卡片，列：站点/月销量/月销售额/销售环比/月毛利润/毛利环比/毛利率/ACOS/ACOAS/退款率/评分/评论数
- ACOAS 色块阈值 绿≤15% / 黄15-25% / 红>25%（分母含自然销售，比 ACOS 阈值低）

**环比口径（重要）**：
- 环比基期 = 上个月（自然月）
- **6月销售额 < $2,000 视为低基数 → 环比标「新」**；无6月数据 → 标「—」
- 整体环比只统计可比父ASIN（上月≥$2,000），并在报告注明可比数量

**评分/评论环比不可行**（xydc `get_asin_info_trends` 实测 ratings/stars 全 null，无历史数据源）→ 只展示当前绝对值，环比位标"—"；建议月报运行时保存评分快照供次月环比

**JS 规范**：百分比拼接**必须 `.toFixed(1)`**（裸用 `*100` 会暴露 IEEE754 浮点，如 19.434639334654342%）；接口比例字段值本身是小数（0.0630=6.3%），显示时 `*100`，勿误读为 0.063%

### 7.7 月度 YTD（财年累计）计算

- 财年 = 2026-04 ~ 2027-03（用户口径）
- YTD 实际 = 财年初(4月) ~ 本月各月南京组销售额/毛利**累计**：需**逐月拉取** 4月/5月/6月…（`date_summary_type=3`，全部分页），筛选南京组后按月汇总
- 参考样例（2026-08 拉 7 月月报时）：4月$83,975 / 5月$69,246 / 6月$93,257 / 7月$312,105 → YTD(4-7月) $558,582；目标 $425,000 → 完成率 131%
- **口径校验**：拉取的 4/5 月实际与目标表「全年完成总表」月实际值几乎一致 → 验证口径吻合，若差异大需排查
- 完成表展示：当月完成率 + YTD 累计完成率（进度条 + 目标 vs 实际柱状图）

**完成标准**：月报 HTML 含全部 7.1 字段列 + 评分/评论 + 完成表 + 库销比（5仓全量）与 4 库龄段总览；库存拉取失败才标注"未获取"。

## 参考

- 目标群「南京欧洲站￥$€£」openConversationId：`cidCtsmbs4Sk6ajOZQDMQl32w==`
- 南京欧洲组主力店铺 sid：5018(US) 5022(UK) 5024(DE) 5019(CA) 5021(JP) 5023(IT) 5029(PL) 5030(BE)
- 上期文件 glob 匹配 `1785746*.txt` 这类时间戳段时，需覆盖全部页（9页=180条），否则环比偏差
- 月报：`date_summary_type=3`（按月汇总），上期对比取上个月；月度环比按自然月（勿用周日~周六口径）
- 年度目标文件：`E:\#工作资料\月复盘\汇报\<最新月份目录>\2026财年运营月复盘---运营六组 王祎-*.xlsx` sheet1「全年完成总表」；口径=南京欧洲组KS（六组=王祎+化一博）、USD、财年2026-04~2027-03、全年目标销售额5,135,000/毛利额580,000
- **踩坑**：① refund_amount_rate 是数量口径(退款数/销量)非金额——金额口径自算；② 海运费=0 多为录入延迟非真实0；③ xydc 评分趋势接口无数据，评分环比做不了；④ 环比爆表因新品起量——设 $2,000 低基数门槛标"新"；⑤ Python 生成 JS 时三引号内嵌 `'"'"'` 转义会残留——直接写字符串；⑥ JS 百分比必须 `.toFixed(1)`
