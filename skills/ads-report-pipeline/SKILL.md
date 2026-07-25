---
name: ads-report-pipeline
description: >
  KovaScape 广告数据解读标准工作流。当用户请求广告报告分析、数据解读、portfolio-dashboard、bid-optimizer、
  ACOS分析、关键词分析等任何广告数据类任务时触发。
  默认数据源为领星 MCP (LingXing-MCP)，通过 lingxing_pipeline.py 转换为 pp-amazon-ads 标准格式后，
  用 pp-amazon-ads CLI 进行深度解读。
  触发词：广告报告、广告数据、看一下广告、ACOS分析、关键词分析、portfolio-dashboard、bid-optimizer、
  花费分析、广告表现、广告健康、哪个活动亏钱、扩量建议、否定词建议。
---

# 广告报告数据解读 Skill

## 核心原则
1. **默认数据源 = 领星 MCP**：无需用户手动导出 CSV，直接调 `LingXing-MCP` 的工具拉取。
2. **数据转换层 = lingxing_pipeline.py**：将领星 JSON 转为 pp-amazon-ads 标准 CSV。
3. **分析引擎 = pp-amazon-ads CLI**：用 CLI 命令进行标准化分析，保证输出格式一致。
4. **安全边界**：所有分析为只读操作，任何优化建议需用户"确认"后才执行写操作。

## 标准执行流程 (Standard Execution Flow)

### Step 1：确认店铺和时间范围
```
用户指定：KS-US / KS-UK / KS-DE ...（默认最近 30 天）
```
店铺 SID 映射表见 `d:\Zero Tools\src\lingxing_pipeline.py` 中的 `STORE_MAP`。

### Step 2：从领星 MCP 拉取数据

**广告活动报告** (Campaign Report)：
```python
# 调用 LingXing-MCP.ad_campaign_report
{
  "profile_ids": [<store_profile_id>],
  "report_date": "<start_date> - <end_date>",
  "page": 1,
  "length": 100,   # 尽量拉全量
  "sort_field": "spends",
  "sort_type": "desc"
}
```

**关键词报告** (Keyword Report)：
```python
# 调用 LingXing-MCP.ad_campaign_keyword_report
{
  "profile_ids": [<store_profile_id>],
  "report_date": "<start_date> - <end_date>",
  "page": 1,
  "length": 100,
  "sort_field": "spends",
  "sort_type": "desc"
}
```

**搜索词报告** (Search Term Report)（如需挖掘否定词/新词）：
```python
# 调用 LingXing-MCP.ad_campaign_search_term_report
```

### Step 3：转换数据格式

将领星返回的 JSON 保存到临时文件，然后运行：

```bash
python "d:\Zero Tools\src\lingxing_pipeline.py"
# 输出到 d:\Zero Tools\data\<store>_campaigns.csv
# 输出到 d:\Zero Tools\data\<store>_keywords.csv
```

### Step 4：pp-amazon-ads CLI 分析

根据用户需求选择对应命令：

| 用户需求 | pp-amazon-ads 命令 | 数据源 |
|:---|:---|:---|
| 看整体广告表现 | `portfolio-dashboard --report campaigns.csv` | campaign CSV |
| 活动横向对比 | `campaign-comparison --report campaigns.csv` | campaign CSV |
| ACOS 对比 TACOS | `acos-vs-tacos --report campaigns.csv` | campaign CSV |
| 保本 ACOS 计算 | `break-even-acos --price X --cogs Y --fees Z` | 无需报告 |
| 真实利润 | `true-profit --price X --cogs Y --fees Z --ad-spend A` | 无需报告 |
| 竞价优化建议 | `bid-optimizer --report keywords.csv --target-acos X` | keyword CSV |
| 否定词建议 | `negative-keyword-generator --report search_terms.csv` | search term CSV |
| 浪费花费 | `wasted-spend --report search_terms.csv --threshold 10` | search term CSV |
| 广告位分析 | `placement-analysis --report placement.csv` | placement CSV |
| 预算分配建议 | `budget-rebalance --report campaigns.csv --total-budget X` | campaign CSV |

**所有命令加 `--agent` 标志以获取 JSON 输出**：
```bash
$env:PYTHONIOENCODING="utf-8"
amazon-ads-pp-cli portfolio-dashboard --report "d:\Zero Tools\data\ks_us_campaigns.csv" --agent
```

### Step 5：解读并输出结论

按以下结构输出分析结论：

```
## 📊 <店铺> 广告报告解读 | <时间范围>

### 🔑 汇总健康度
[整体 ACOS / ROAS / 花费 / 销售额 / 超预算情况]

### 🔴 问题活动（需干预）
[高 ACOS 活动列表 + 原因分析]

### 🚀 扩量机会（效率好的活动）
[低 ACOS + 高 ROAS 活动 + 建议预算增幅]

### 💡 优化建议（待您确认后执行）
[具体调整清单：活动ID + 操作 + 调前/调后对比]
```

## 数据文件约定 (Data File Conventions)

```
d:\Zero Tools\data\
├── ks_us_campaigns.csv       # KS-US 活动级报告
├── ks_uk_campaigns.csv       # KS-UK 活动级报告
├── ks_de_campaigns.csv       # KS-DE 活动级报告
├── ks_us_keywords.csv        # KS-US 关键词报告
├── ks_us_search_terms.csv    # KS-US 搜索词报告
└── amazon_ads_profiles.json  # 全站 Profile ID 映射表
```

## 关键文件引用

- **数据转换脚本**：[lingxing_pipeline.py](file:///d:/Zero%20Tools/src/lingxing_pipeline.py)
- **店铺 Profile 映射**：[amazon_ads_profiles.json](file:///d:/Zero%20Tools/data/amazon_ads_profiles.json)
- **架构蓝图**：[ops_integration_blueprint.md](file:///C:/Users/Administrator/.gemini/antigravity/brain/a5de039d-ae22-41fc-b73a-5581686025f9/ops_integration_blueprint.md)

## 常用 Profile ID 快查

| 店铺 | Profile ID |
|:---|:---|
| KS-US | 341152603067627 |
| KS-UK | 562422498717821 |
| KS-DE | 1520887297341187 |
| KS-FR | 914553890503512 |
| KS-IT | 980893527404192 |
| KS-ES | 1848045335441540 |
| KS-JP | 3704664040321826 |
| KS-CA | 102143003061298 |

## 注意事项

1. **分页**：领星 MCP 每次最多返回 100 条，若活动数 > 100，需多次调用并合并。
2. **编码**：Windows PowerShell 需设置 `$env:PYTHONIOENCODING="utf-8"` 再运行 pp-cli。
3. **缓存**：同一天的数据不重复拉取，复用 `data/` 目录下的 CSV 文件。
4. **写操作安全边界**：任何 `--apply` 操作必须经用户在聊天中明确输入"确认"后才能执行。
