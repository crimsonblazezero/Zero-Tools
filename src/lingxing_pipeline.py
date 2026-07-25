"""
KovaScape 广告数据管道 (Ad Data Pipeline)
-----------------------------------------
默认数据源：领星 MCP (LingXing-MCP)
用途：将领星广告报告数据转换为 pp-amazon-ads CLI 可读的标准 CSV 格式

店铺 SID 映射表 (Store SID Map)
"""

import json
import csv
import os
import sys
from datetime import datetime, timedelta

# ============================================================
# 店铺 SID 配置 (Store Configuration)
# ============================================================
STORE_MAP = {
    "KS-US": {"sid": 5018, "profile_id": 341152603067627, "currency": "USD", "endpoint": "advertising-api.amazon.com"},
    "KS-UK": {"sid": 5022, "profile_id": 562422498717821, "currency": "GBP", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-DE": {"sid": 5024, "profile_id": 1520887297341187, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-FR": {"sid": 5025, "profile_id": 914553890503512, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-IT": {"sid": 5023, "profile_id": 980893527404192, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-ES": {"sid": 5026, "profile_id": 1848045335441540, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-JP": {"sid": 5021, "profile_id": 3704664040321826, "currency": "JPY", "endpoint": "advertising-api-fe.amazon.com"},
    "KS-CA": {"sid": 5019, "profile_id": 102143003061298, "currency": "CAD", "endpoint": "advertising-api.amazon.com"},
    "KS-NL": {"sid": 5027, "profile_id": 3223742056527340, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-SE": {"sid": 5028, "profile_id": 3150136719983076, "currency": "SEK", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-PL": {"sid": 5029, "profile_id": 679162377114364, "currency": "PLN", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-BE": {"sid": 5030, "profile_id": 3889972646403992, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
    "KS-MX": {"sid": 5020, "profile_id": 504098149927584, "currency": "MXN", "endpoint": "advertising-api.amazon.com"},
    "KS-IE": {"sid": 5031, "profile_id": 2985188199950324, "currency": "EUR", "endpoint": "advertising-api-eu.amazon.com"},
}

def get_date_range(days=30):
    """生成最近 N 天的日期范围 (Generate date range for last N days)"""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def lingxing_to_campaign_csv(raw_json_path, output_csv_path, store_key="KS-US"):
    """
    将领星 MCP 广告活动报告 JSON 转换为 pp-amazon-ads 标准 CSV
    (Convert LingXing MCP campaign report JSON to pp-amazon-ads standard CSV)

    pp-amazon-ads portfolio-dashboard 需要的字段:
    campaignId, campaignName, impressions, clicks, cost, sales, orders, acos, dailyBudget
    """
    store = STORE_MAP.get(store_key, STORE_MAP["KS-US"])

    with open(raw_json_path, encoding="utf-8") as f:
        data = json.load(f)

    campaigns = data.get("data", {}).get("data", [])
    rows = []
    for c in campaigns:
        cid = c.get("campaign_id")
        if not cid:
            continue
        rows.append({
            "campaignId":    str(cid),
            "campaignName":  c.get("name", ""),
            "impressions":   int(c.get("impressions") or 0),
            "clicks":        int(c.get("clicks") or 0),
            "cost":          float(c.get("spends") or 0),
            "sales":         float(c.get("sales") or 0),
            "orders":        int(c.get("orders") or 0),
            "acos":          float(c.get("acos") or 0),
            "dailyBudget":   float(c.get("daily_budget") or 0),
            # 扩展字段 (Extended fields)
            "roas":          float(c.get("roas") or 0),
            "cpc":           float(c.get("cpc") or 0),
            "ctr":           float(c.get("ctr") or 0),
            "cvr":           float(c.get("cvr") or 0),
            "state":         c.get("state") or "",
            "targetingType": c.get("targeting_type") or "",
            "portfolioName": c.get("portfolio_name") or "",
            "currency":      store["currency"],
            "store":         store_key,
        })

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        if not rows:
            print(f"[WARN] No campaign data found in {raw_json_path}")
            return 0
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Exported {len(rows)} campaigns to {output_csv_path}")
    return len(rows)

def lingxing_to_keyword_csv(raw_json_path, output_csv_path):
    """
    将领星关键词报告 JSON 转换为 pp-amazon-ads 标准 CSV
    (Convert LingXing keyword report JSON to pp-amazon-ads keyword CSV)

    pp-amazon-ads bid-optimizer / search-term-mining 需要的字段:
    keywordId, keywordText, matchType, bid, clicks, cost, sales, orders, acos
    """
    with open(raw_json_path, encoding="utf-8") as f:
        data = json.load(f)

    keywords = data.get("data", {}).get("data", [])
    rows = []
    for k in keywords:
        rows.append({
            "keywordId":    str(k.get("keyword_id") or k.get("id") or ""),
            "keywordText":  k.get("keyword_text") or k.get("keyword") or "",
            "matchType":    k.get("match_type") or "",
            "bid":          float(k.get("bid") or 0),
            "impressions":  int(k.get("impressions") or 0),
            "clicks":       int(k.get("clicks") or 0),
            "cost":         float(k.get("spends") or k.get("cost") or 0),
            "sales":        float(k.get("sales") or 0),
            "orders":       int(k.get("orders") or 0),
            "acos":         float(k.get("acos") or 0),
            "cpc":          float(k.get("cpc") or 0),
            "cvr":          float(k.get("cvr") or 0),
            "campaignName": k.get("campaign_name") or "",
            "adGroupName":  k.get("ad_group_name") or "",
        })

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        if not rows:
            print(f"[WARN] No keyword data found in {raw_json_path}")
            return 0
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Exported {len(rows)} keywords to {output_csv_path}")
    return len(rows)


if __name__ == "__main__":
    # 示例：直接转换上一步拉取的 KS-US 报告
    raw = r"C:\Users\Administrator\.gemini\antigravity\brain\a5de039d-ae22-41fc-b73a-5581686025f9\.system_generated\steps\1161\output.txt"
    out_campaign = r"d:\Zero Tools\data\ks_us_campaigns.csv"
    n = lingxing_to_campaign_csv(raw, out_campaign, store_key="KS-US")
    print(f"Done: {n} rows -> {out_campaign}")
