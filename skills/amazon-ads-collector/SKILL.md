---
name: amazon-ads-collector
description: KovaScape Amazon Ads and Inventory collection skill. Used to analyze, pull and merge store PPC data with ERP stock levels while respecting rate-limiting boundaries.
---

# Amazon Ads Collector

This skill is designed to prevent rate limiting (Throttling) while merging active ASINs, multiple MSKUs, and local ERP SKU stock levels.

## Core Matching Logic

1. **Variant to Entity Mapping**:
   - Active ASIN -> maps to multiple MSKUs -> points to a single local logic ERPSKU.
2. **Hybrid Data Stitching**:
   - Advertising campaigns fetch real-time Spend, Sales, Clicks, and ACOS.
   - LingXing listing mapping pulls local SKU stock levels.

## Workflow

- **1. Read amazon_ads.env credentials and mappings**
- **2. Enforce adaptive wait time**
- **3. Execute scripts/ads_flow_collector.py**
- **4. Export unified_report.csv**

### 1. Throttling Prevention Guide
To avoid "Server Busy (Gw 8002)" errors:
- Use local mapping cache where possible.
- Impose a 2.0s delay between LingXing calls and a 1.0s delay between Ads API calls.
- Enforce exponential backoff on retries.

### 2. Command Execution Syntax
`powershell
python "d:/Zero Tools/.agents/skills/amazon-ads-collector/scripts/ads_flow_collector.py"
`

## Resources

- **ads_flow_collector.py**: Core script that automates the collection mapping using environment credentials.