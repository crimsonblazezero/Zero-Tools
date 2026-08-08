---
name: lingxing-dws-weekly-report
description: >
  KovaScape / 南京欧洲组 周报自动化工作流。当需要生成运营周复盘、销售周报、
  从领星MCP拉取数据写入Excel、或提交钉钉日志（OA周报模板）时触发。
  支持周销量、周销售额、ACoS、毛利额、库龄库存、目标完成率等指标的自动计算与填报。
tags: [reporting, weekly, lingxing, dingtalk, dws, excel]
---

# 周报自动化工作流

从领星 ERP 拉取销售/利润/广告/库存数据，汇总后写入 Excel，再提交到钉钉日志「运营周复盘」模板。

## 何时触发

- 用户说：「周报自动化」「每周五跑数据」「自动生成运营周复盘」「生成Excel周报」
- 涉及跨三源数据合并：领星MCP + 本地Excel目标 + 钉钉日志模板提交

## 数据源清单

| 来源 | 工具/路径 | 用途 |
|------|-----------|------|
| 领星 MCP | `query_product_performance_asin_lists` | **主数据源**：销售额、净销售额、毛利润、广告费、销量（下单时间口径，与UI一致） |
| 领星 MCP | `get_fba_stock_list` | FBA库存、库龄段数据（按SKU/产品ID维度） |
| 本地Excel | 南京欧洲组-2026财年目标测算.xlsx →「人员」sheet | 王祎月目标销售额/毛利额/毛利率 |
| 领星账户权限 | 仅读，`create_*` 系列全部403 | 自定义指标未开放 |

## ⚠️ 数据聚合关键规则

### 🔴 周报复盘数据源选择规则（2026-07-26修正）

**核心原则：用 `query_product_performance_asin_lists`（下单时间口径）替代 `get_profit_report_msku`（结算时间口径）**

为什么之前对不上UI截图：
| 接口 | 时间口径 | 币种 | 数据范围 | 负责人拆分 |
|------|---------|------|---------|-----------|
| `query_product_performance_asin_lists` | 下单时间（purchase），含预估订单 | USD统一展示 | 全部订单，数量与UI一致 | ✅ `principal_names[]` |
| `get_profit_report_msku` | 结算时间（postedDate），仅已结算 | 原始混合币种，`exchangeRate=1.0` | 仅已结算MSKU，销量偏少约53% | ✅ `principalRealname` |
| `query_order_profit_list_gross_profit` | 汇总 | USD | 全店铺聚合，无负责人拆分 | ❌ 不支持 |

实测差异（2026-07-12~18，王祎+化一博）：UI销量1753 vs MCP利润报表816。这就是订单量差一半的原因。

**正确方案**：
1. **主数据源**：`query_product_performance_asin_lists`
   - 参数：`date_type="purchase"` + `query_order_profit=true` + `summary_field="parent_asin"`
   - 每条记录结构：
     ```python
     principal_names[]  # ["王祎"] / ["化一博"]
     parent_asins[0].sid  # "5018" → NS-KS筛选
     price_list[j].seller_name  # "南京欧洲组KS-US" → 店名筛选
     volume / amount / net_amount / gross_profit / ad_sales_amount
     ```
   - ⚠️ 必须分页拉取完整数据（每页50条，1753单≈35页）
   - NS-KS筛选用 `price_list` 遍历，匹配 `seller_name` 包含 `南京欧洲组KS`

2. **备用校验**：`query_order_profit_list_gross_profit` 拿USD毛利总额
   - 7天全店铺汇总毛利 $37,203（比UI $14,837大，因为它是所有店铺的粗毛，不是NS-KS精确拆分）

3. **避免用**：`get_profit_report_msku`
   - postedDate口径导致订单量严重偏少（816 vs 1753）
   - exchangeRate=1.0 的原始币种无法直接加总比较

### 利润报表必须全量拉取并分页
- 产品表现API每页50条，需分页循环取全量（length=50, offset=0,50,100...）
- 利润报表 get_profit_report_msku total 可达数千条（实际测试 2475~4453 条），同样必须分页
- `query_order_profit_list_gross_profit` 返回 `total` 字段可用于分页校验

### 筛选规则
- 用 `storeName` 字段匹配店铺名称，不要只用 sid
- 南京欧洲组KS 的 storeName 格式：`南京欧洲组KS-US`, `南京欧洲组KS-UK`, `南京欧洲组KS-DE`, `南京欧洲组KS-JP`, `南京欧洲组KS-CA`, `南京欧洲组KS-PL`
- `seller_group_name` 也可能包含 "南京欧洲组KS"，两者都要检查
- `principalRealname` 字段用于区分负责人（王祎、化一博等）

### 多币种处理（2026-07-26 实测确认）

`query_product_performance_asin_lists` 返回的所有金额字段均为 **CNY**，不是各站点原始币种：
- 美站、英站、加站、德站、日站全部统一返回 CNY
- **固定汇率 6.8109**（所有站点相同）
- 换算方式：USD = CNY / 6.8109
- `price_list[0].source_rate` = 6.8109，可作为验证值

`get_profit_report_msku` 则是原始混合币种 + `exchangeRate=1.0`，无法直接使用。

### FBA库存匹配规则 ⚠️（不是只用 group_by_seller_id）

**绝对不要用 `group_by_seller_id` 做 NS-KS 过滤**，它不可靠：
- 很多 NS-KS 商品被跨站合并后，`group_by_seller_id` 变成组合ID如 `A2A3VOMEFJC47N`，不含任何NS-KS的SID
- **正确做法**：同时检查 `seller_group_name` 和 `seller_name` 是否包含 `"南京欧洲组KS"`
```python
def is_nsks_fba(item):
    sgn = item.get('seller_group_name', '') or ''
    sn = item.get('seller_name', '') or ''
    return '南京欧洲组KS' in sgn or '南京欧洲组KS' in sn
```
已验证：按 `group_by_seller_id` 只命中 125 条，按 `seller_name` 含"南京"能命中 137 条，差的12条正是跨站合并记录。

### FBA 完整拉取要求（2026-07-27 实测确认）

- `get_fba_stock_list` 单次 length=5000 可一次性拉全量（实测 total=3972 条）
- API 的 `length` 只接受 [20,50,100,200,500,1000,2000,5000]，传3000会报"页条数必须在范围内"错误
- NS-KS过滤必须用 `seller_group_name` 含"南京欧洲组KS"或 `seller_name` 含"南京欧洲组KS"

### Excel 行映射规则（2026-07-27 用户修正）

**"周报" Sheet 三行对应关系：**
| Excel行 | 姓名列 | 组内序号 | 数据口径 |
|---------|--------|---------|---------|
| Row 2 | 王祎 | **100** | **整组数据** = 王祎 + 化一博 |
| Row 3 | 王祎个人 | **200** | **负责人=王祎的所有数据** |
| Row 4 | 化一博 | **300** | **负责人=化一博的所有数据** |

**"清货进度表" Sheet 同样规则：**
| Excel行 | 姓名列 | 组内序号 | 数据口径 |
|---------|--------|---------|---------|
| Row 2 | 王祎 | **100** | **整组汇总库存** |
| Row 3 | 王祎个人 | **200** | **负责人=王祎的独有库存** |
| Row 4 | 化一博 | **300** | **负责人=化一博的独有库存** |

⚠️ 序号 100/200/300 硬编码写入，不可从其他字段计算。"王祎"显示整组，"王祎个人"显示仅该负责人。

### Excel 公式列处理（2026-07-27 用户修正）

⚠️ Excel G/J/K/N 列应为**硬编码数值**而非 Excel 公式字符串 `=D4/E4`。
脚本直接写入计算结果，不依赖 Excel 内部公式：
- G列=周达成率 → 硬编码 `wn/daily_tgt`
- J列=月ACoAS → 硬编码 `ad_spend/mn`  
- K列=月达成率 → 硬编码 `mn/mtgt_sales`
- N列=毛利额达成率 → 硬编码 `mg/mtgt_gp`

如果用户要求保留公式，改为写 `=D4/E4` 等，但**当前策略是直接覆盖值**。

### ⚠️ 库销比公式（2026-07-27 用户修正）

正确公式：**现有FBA总库存 / 日均销量 / 30**

不是 `FBA总库存 / 日均销量`（那是天数），也不是 `FBA总库存 / 近30天总销量`。
示例：32222 / 314 / 30 ≈ 3.41

### ⚠️ 王祎个人周目标销售额必须写入（2026-07-27）

- 王祎个人周目标 = 月目标 ÷ 4 = $48,000 / 4 = **$12,000**
- 化一博周目标 = 月目标 ÷ 4 = $84,000 / 4 = **$21,000**
- 整组周目标 = $30,000（$12,000 + $21,000）
- Excel中 Row2（序号100=整组）E列填$30,000；Row3（王祎个人）E列填$12,000；Row4（化一博）E列填$21,000

## ⚠️ write_file 对大文件会截断

当脚本超过 ~400 行时，**绝对不要使用 `write_file` 直接覆盖**。该工具在长文件覆盖时容易截断或混入旧内容，导致编译通过但运行崩溃。

正确的修复策略：
1. 优先用 `patch` 修改具体代码段
2. 如果必须重写，先备份，然后分段写入临时文件再合并
3. 或者从另一个小脚本 import 已有函数来生成输出（避免覆盖主文件）

## Excel 打开锁文件

`.xlsx` 文件被 Excel 占用时 openpyxl 保存会报 `PermissionError`。
解决：写入新文件名如 `xxx_v19_new.xlsx`，不要在原文件上覆盖。

## Excel 输出格式

目标文件：`运营周会数据收集_王祎.xlsx`
脚本路径：`scripts/weekly_report.py`（v18，直接覆盖旧值，不用管原始Excel公式）

**"清货进度表" Sheet 同样规则：**
| Excel行 | 姓名列 | 组内序号 | 数据口径 |
|---------|--------|---------|---------|
| Row 2 | 王祎 | **100** | **整组汇总库存** |
| Row 3 | 王祎个人 | **200** | **负责人=王祎的独有库存** |
| Row 4 | 化一博 | **300** | **负责人=化一博的独有库存** |

⚠️ 序号 100/200/300 硬编码写入，不可从其他字段计算。"王祎"显示整组，"王祎个人"显示仅该负责人。

### DWS 容器型字段处理

sort=52 "组长销售数据" 和 sort=53 "组长库存数据" 在模板中是 **type=16**，但钉钉 API 不接受 type=16 → PARAM_ERROR。
**必须转换为 type=1 + contentType=origin**，content 放长文本表格内容。

| sort | field_name | 模板 type | 提交 type | contentType |
|------|------------|-----------|-----------|-------------|
| 52 | 组长销售数据 | 16(复杂) | **1** | **origin** |
| 53 | 组长库存数据 | 16(复杂) | **1** | **origin** |

**DWS contentType 正确写法**：
- type=1 文本 → `contentType: "origin"`（不是 markdown）
- type=2 数字 → `contentType: "origin"`
- type=9 附件 → `contentType: "origin"`（当前阶段跳过）
- type=16 必须转 type=1 → `contentType: "origin"`

- **组整体**：所有`asin_principal_list`中包含该负责人的NS-KS商品都计入
- **个人行**（Excel中的"王祎个人"）：仅统计 `asin_principal_list == ['王祎']` 的独有ASIN
- 两个维度可能差异较大，不要混用

## ⚠️ 硬编码修复（2026-07-27 用户指出问题后修正）

### 库销比公式修正
❌ 错误：`FBA总库存 / 日均销量`
✅ 正确：**`FBA总库存 / 日均销量 / 30`**

示例：32222件 / 314件/天 / 30 = **3.41**

### 周目标销售额修正
❌ 错误：王祎个人 `daily_tgt: None`
✅ 正确：**王祎个人周目标 = $12,000**（月目标$48,000 ÷ 4）
✅ **化一博周目标 = $21,000**（月目标$84,000 ÷ 4）

### DWS 提交失败根因修正
❌ 错误：模板 sort=52/53 为 type=16（容器型），钉钉 API 不接受
✅ 正确：**type=16 → type=1 + contentType=origin**，content放长文本

## 关键字段映射规则

### 🔴 产品表现表字段币种与关键差异（2026-07-26 实测确认）

`query_product_performance_asin_lists` 返回的**所有金额字段均为 CNY**，不是 USD：
- 美站、英站、加站、德站、日站全部返回 CNY
- **统一汇率固定为 6.8109**（所有站点相同，非各站点独立汇率）
- 换算方式：USD = CNY / 6.8109
- `price_list[0].source_rate` = 6.8109（可作为验证）

### 🔴 predict_gross_profit vs gross_profit 区别

| 字段 | 含义 | 对应Excel列 |
|------|------|-------------|
| `predict_gross_profit` | **预测毛利润（下单时预估）** | 产品表现表的「订单毛利润」 |
| `gross_profit` | **结算毛利润（已结算后更新）** | 产品表现表的「结算毛利润」 |

周报必须使用 `predict_gross_profit`，不要用 `gross_profit`！两者相差巨大。

### 🔴 毛利润修正规则（2026-07-26 最终确认）

**使用 `predict_gross_profit`（下单时间预估），不做 `gross_profit`（结算口径）：**

```python
修正毛利额USD = sum(predict_gross_profit_cny) * 0.6 / 6.8109
```

原因：`predict_gross_profit` 未扣全采购/头程等成本，需 ×0.6 修正系数。  
**ACoAS 口径不变**：`|sum(广告费)| / sum(net_amount)`，广告费字段来自产品表现表的 ads 相关支出。

⚠️ 不要使用 `gross_profit`（结算利润）或 `get_profit_report_msku`，前者遗漏未结算预估订单，后者仅覆盖已结算MSKU。

#### 历史参考
详细API差异审计见 `references/LingXing_profit_report_api_audit.md`，其中记录的旧版`×0.6`经验公式已被官方文档表面否定，但**实际上因成本项缺失，保留×0.6仍是当前可靠方案**。

### ACoAS 口径 ⚠️ 数据来源与计算

**原则：优先从 `query_product_performance_asin_lists` 一次性拿全量数据。**
- 广告报表数据太大且容易触发"服务器繁忙"限流
- 产品表现接口已包含各支出和收入 + 销售数据，按负责人聚合即可
- 关键字段在 `data.list[i]` 中：
  - `volume` → 销量
  - `amount` → 销售额
  - `net_amount` → 净销售额
  - `gross_profit` → 毛利润（领星订单利润公式：销售额+退款额+买家运费+促销折扣+平台费+FBA发货费+其他费用+广告费+采购成本+头程成本+其他成本）
  - `shared_cost_of_advertising` / `ad_sales_amount` → 广告费/广告销售额
- **ACoAS = |sum(shared_cost_of_advertising)| / sum(amount)**
- ❌ 不要单独拉广告报表
- ⚠️ **不要对 `gross_profit` 做 ×0.6 修正**——这是错误的业务假设，应直接使用API返回的真实毛利字段

### 周目标计算
```
周目标 = 月目标 ÷ 4
```
如本月未完成目标，下周目标自动加上未完成情况。

### 清货目标存量 ⚠️ 由当前库存反推
- **90-180天库龄目标存量 = 当前该段FBA库存数量 × 0.75**
- **181-270天库龄目标存量 = 当前该段FBA库存数量 × 0.8**
- 不是固定值，不是人工录入值，是用当前库存按比例反算

### 日期范围
- **周数据**: 上周日 ~ 本周六
- **月数据**: 当月1号 ~ 本周六

### Aitable URL → Base ID 提取
钉钉AI表格链接格式：
```
https://alidocs.dingtalk.com/i/nodes/{baseId}/{tableId}...
```
URL预检必须先识别类型（见 dws skill 的 url-patterns.md）。多维表格用 `dws aitables base list` / `record list` 读取。

### DWS 提交钉钉日志

```bash
# 查模板字段定义
dws report template get --name "运营周复盘（周一9:00前提交）" --format json
```

## ⚠️ 组长提交策略

**王祎作为组长（运营六组）的提交方式：一份日志，不是两人各一份。**

- **DWS日志**: WY一份，数值字段填**组整体**数据，文本字段含个人明细（用 markdown 格式在说明框中列出 WY 个人和化一博个人数据）
- **Excel附件**: 三行全覆盖（row2=王祎组整体、row3=王祎个人、row4=化一博）
- **不要为化一博单独提交一份日志**（之前尝试每人一个JSON被API因重复key拒绝）

#### ⚠️ 模板内容格式（DWS提交）— 2026-07-27 修正

contents JSON 的 key 必须等于 template get 返回的 field_name 原值，sort 必须等于 field_sort 字符串。

| 模板 field_type | contents JSON `type` | 推荐 `contentType` | 说明 |
|-----------|---------------------|-------------|------|
| 1(文本) | `1` | `origin`（不用 markdown） | 文本字段；不要传 `type=16` |
| 2(数字) | `2` | `origin` | 数值字段；必填项无数据时填 `"0"` |
| 9(附件) | `9` | `origin` | 附件字段；若跳过附件则不写此项 |
| **16(容器型)** | **⚠️ 必须转为 `1`** | **`origin`** | **API不接受 type=16，会导致 PARAM_ERROR。** 用 type=1+origin 替代；长文本放 content |

🔴 **type=16 = PARAM_ERROR 根因之一**。钉钉日志 API 实际只接受 1/2/5/7 等类型。当 template get 返回 type=16 时（如 sort=52 "组长销售数据"、sort=53 "组长库存数据"），改为 type=1，content 放纯文本/Markdown 长文本。

⚠️ **contentType 不要用 markdown** — 实测用 `origin` 更稳定。即使是 type=1 文本字段也用 origin。

⚠️ **必填项处理**：模板要求的必填字段如果没有数据，填 `"0"` 占位（数字）或空字符串 `""`（文本），不能缺失整个字段。sort=0 "周未达成重要目标/存在问题/原因/办法" 按用户偏好不自动写入数据，留空给人工更新，但 JSON 中仍需保留该字段（内容为空字符串）。
```bash
# 优先：不加 --format json
dws report entry submit --template-id <id> --contents-file <file.json> --yes

# 如果仍需format，再试 --format json
dws report entry submit --template-id <id> --contents-file <file.json> --yes --format json
```

#### 附件上传流程（可选）

模板 sort=56 "附件"（type=9）。不能直接传文件路径，需要两步：
1. `dws drive upload <local_excel_path>` → 获取 UUID
2. contents JSON 加：`{"key":"附件","sort":"56","content":"<UUID>","contentType":"origin","type":"9"}`
3. `dws report entry submit --template-id <模板ID> --contents-file <file.json> --yes`

**用户偏好**：当前阶段跳过附件自动上传。DWS提交后手动上传Excel到日志中。脚本内 `build_dws()` 中附件字段设为空字符串即可。

#### ⚠️ contents JSON 去重规则

每个 key+sort 组合在数组中必须唯一，出现重复会被 API 静默拒绝（PARAM_ERROR，不告诉你哪个）。提交前用 Python 校验：
```python
seen = set()
for c in dws_contents:
    k = (c['key'], c['sort'])
    assert k not in seen, f"Duplicate: {k}"
    seen.add(k)
```

#### 提交失败排查顺序
1. `dws report template list` → 确认template ID正确
2. `dws report template get --name "..." --format json` → 提取完整字段定义
3. 按字段映射重写 contents JSON（禁止凭记忆编 key）
4. `--contents-file` 而非 `--contents` 长JSON，避免shell引号破坏
5. contents大小 ≤ 10MB，不支持分批
| 2 | `"2"` | `"text"` | 数字 |
| 9 | `"9"` | `"file"` | 附件（需先 upload 获 fileId） |
| 16 | `"16"` | `"text"` | 长文本/表格 |

contents JSON 的 `key` 必须等于 `field_name` 原值，`sort` 必须等于 `field_sort` 字符串。

#### 附件上传流程

模板 sort=56 "附件"（type=9）。不能直接传文件路径，需要两步：
1. `dws drive upload <local_excel_path>` → 获取 UUID
2. contents JSON 加：`{"key":"附件","sort":"56","content":"<UUID>","contentType":"file","type":"9"}`
3. submit 必须带 `--format json` 才能解析 file_id

```bash
# 构造 contents JSON 到文件
cat > /tmp/report_contents.json << 'EOF'
[{...}]
EOF

# 提交
dws report entry submit \
  --template-id <模板ID> \
  --contents-file /tmp/report_contents.json \
  --yes --format json
```

### ⚠️ 必守铁律

1. **contents key 必须完全等于 template get 返回的 field_name**，一个字不能改
2. **contentType 用 `origin`**（type=1 文本也用 origin，不用 markdown；type=9 附件用 origin）
3. **长内容永远走 `--contents-file`**，禁止 `--contents '<json>'` 带中文引号换行
4. **提交失败后的排查顺序**：template list → template get → 重新写 contents → submit
5. **提交成功后用 `dingtalkOpenMarkdownLink`** 给用户点击跳转，禁止裸放 `dingtalk://` 链接
6. **不要走 dws doc 写文档**，如果用户明确说"OA周报/日志/模板"就走 dws report
7. **出参确认**：submit 成功会在返回中追加 `dingtalkOpenMarkdownLink`；如果缺少就再调一次 `entry get` 补取
8. **当前阶段跳过附件上传**，Excel仅做本地备份（脚本内 build_dws() 不含附件字段）
9. **`weekly_report.py` 是主脚本**，路径 `C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\scripts\weekly_report.py`

### 📋 运营周复盘模板字段表

| sort | field_name | type | 是否自动填充 |
|------|------------|------|-------------|
| 20 | 周销量 | 2(数字) | ✅ |
| 21 | 本周实际销售额$ | 2(数字) | ✅ |
| 22 | AcoAs（%） | 2(数字) | ✅ |
| 23 | 本周目标销售额$ | 2(数字) | ✅ (月目标÷4) |
| 24 | 下周目标销售额$ | 2(数字) | ✅ (未完成自动累加) |
| 25 | 月目标销售额$ | 2(数字) | ✅ (本地Excel) |
| 26 | 月实际销售额$ | 2(数字) | ✅ |
| 27 | 月目标毛利率（%） | 2(数字) | ✅ (本地Excel) |
| 28 | 月实际毛利率（%） | 2(数字) | ✅ |
| 29 | 月目标毛利额$ | 2(数字) | ✅ (本地Excel) |
| 30 | 月实际毛利额$ | 2(数字) | ✅ (API真实毛利，不做修正) |
| 31 | 毛利额完成比率（%） | 2(数字) | ✅ (自动计算) |
| 35~50 | 各库龄段库存/目标 | 2(数字) | 部分✅部分⚠️ |
| 57 | 近30天库销比（FBA在库库存） | 1(文本) | ✅ (自动计算) |
| 52 | 组长销售数据 | 16(复杂) | ❌ 手动填写 |
| 53 | 组长库存数据 | 16(复杂) | ❌ 手动填写 |
| 17 | 本周重点工作及完成情况 | 1(文本) | ⚠️ 复制上期「本周工作」 |
| 0 | 周未达成重要目标/问题/办法 | 1(文本) | ⚠️ AI草稿 |
| 1 | 下周重点工作及计划 | 1(文本) | ⚠️ AI草稿 |
| 12 | 周销量/销售额$/AcoAs/下周目标 | 1(文本) | ✅ |
| 16 | 月目标/实际/毛利率/毛利额 | 1(文本) | ✅ |
| 56 | 附件 | 9(附件) | ✅ Excel上传 |

## Excel 输出格式

目标文件：`运营周会数据收集_王祎.xlsx`

两个 Sheet 需同步更新：
### Excel 「周报」Sheet 列映射（2026-07-27 修正）

M列「月实际毛利额」数据源为 `predict_gross_profit × 0.6 / RATE`（已修正，非API原始值）。

| 列 | 含义 | 计算方式 |
|---|---|---|
| D 本周销售额完成 | 周实际销售额 | 领星数据汇总 CNY÷RATE |
| E 本周目标销售额 | 周目标 | 整组$30000; 个人=月目标÷4 |
| F 本周ACOAS | 周ACoAS | 周广告费÷周净销售额 |
| G 周销售额达成率 | 周目标完成率 | =D/E |
| H 月目标销售额 | 月度目标 | 本地Excel读取 |
| I 月实际销售额 | 月净销售额 | 领星数据 CNY÷RATE |
| J 本月ACOAS | 月ACoAS | 月广告费÷月净销售额 |
| K 月实际销售额达成率 | 月度销售完成率 | =I/H |
| L 月目标毛利额 | 毛利额目标 | 本地Excel读取 |
| M 月实际毛利额 | **修正后毛利额** | **predict_gross_profit × 0.6 ÷ 6.8109** |
| N 毛利额达成率 | 毛利额完成率 | =M/L |
| O 月库销比 | 库存销售比 | FBA可售 ÷ (周销量/7) |

### 「清货进度表」Sheet
| 库龄段 | 当前存量 | 目标存量 | 清货效率 |
|--------|---------|---------|---------|
| 91-180天 | FBA库存汇总 | 人工/系统 | 目标/当前 |
| 181-270天 | FBA库存汇总 | 人工/系统 | 目标/当前 |
| 271-365天 | FBA库存汇总 | 人工/系统 | 目标/当前 |
| 366天以上 | FBA库存汇总 | 人工/系统 | 目标/当前 |

## 调度配置

- cron: `0 16 * * 5`（UTC+8 周五 16:00，注意 cron 时间要换算）
- 或 cron: `0 8 * * 6`（UTC 周六 8:00 = UTC+8 周日 16:00）

### ⏱️ 调度重试逻辑
- 每天最多跑一次
- 若首次失败 → 每2小时检查一次同一天的锁文件
- 使用 lockfile 防止重复执行

## 领星 MCP 权限边界

| 接口类型 | 状态 | 备注 |
|----------|------|------|
| `query_order_profit_list_gross_profit` | ✅ 可用 | MSKU利润报表 |
| `get_fba_stock_list` | ✅ 可用 | FBA库存（length 需 ≥20） |
| `ad_campaign_report` | ✅ 可用 | SP/SD/SB广告，QPS≤1/s |
| `create_*` 系列 | ❌ 403 | 无写入权限 |
| `add_custom_indicator` / `update_custom_indicator` | ❌ 无权限 | 自定义指标未开放 |
| `get_custom_indicator_list` | ❌ 无权限 | 同上 |
| `query_product_performance_asin_lists` | ✅ 已确认可用 | 主数据源，按下单时间（purchase） |
| `get_my_sids` | ✅ 可用 | 33个店铺 |

## ⚠️ 陷阱 & 调试经验

### LingXing MCP 调用格式
HTTP Streamable HTTP，每次请求 QPS ≤ 1。多数据源并行采集时必须串行调用，不能并发冲 QPS。

### outbox list 默认只查最近20天
超过20天窗口必须滚动 `--start/--end`，每次跨度≤20天。

### contents key 错误 → PARAM_ERROR 静默失败
服务端不告诉你哪个字段错了。遇到 PARAM_ERROR 必须从 template get 重新开始，禁止凭记忆编 key。

### dingtalk:// 链接裸粘贴不可点击
必须包成 markdown link：`[查看日志](dingtalk://...)`。

## 相关文件

- `references/field-mapping.md` — 字段名→Excel列映射速查表
- `references/LingXing_profit_report_api_audit.md` — 🔴 两个利润API口径差异审计（含截图基准数据、实测对比）
- 本地文件：
  - `C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\南京欧洲组-2026财年目标测算.xlsx`
  - `C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎.xlsx`
- MVP脚本：`C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\scripts\weekly_report.py`（已暂停，待修正后继续）
