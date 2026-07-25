"""
KovaScape Daily Report - MCP原始数据合并器
============================================

从 output/raw/ 目录读取 MCP 返回的原始 JSON 文件，
合并为 DailySnapshot 格式供规则引擎使用。

用法：
  python merge_mcp_data.py --date 2026-07-26 --output ../output/snapshot-2026-07-26.json
"""

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_mcp_result(path: Path) -> Optional[Dict]:
    """加载 MCP 调用返回的原始 JSON，提取内层 data"""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        # 处理嵌套结构：data.data 或 data.result
        inner = data
        for key in ["data", "result", "response"]:
            if key in inner and isinstance(inner[key], dict):
                inner = inner[key]
        # 可能还有第二层 data
        if "data" in inner and isinstance(inner["data"], dict) and "list" in inner["data"]:
            return inner["data"]
        return inner
    except Exception:
        return None


def parse_inventory(items: List[Dict], sid: int, country: str) -> List[Dict]:
    """解析 FBA 库存列表"""
    rows = []
    for item in items:
        rows.append({
            "sid": sid,
            "country": country,
            "msku": item.get("msku", ""),
            "fnsku": item.get("fnsku"),
            "asin": item.get("asin"),
            "available": int(item.get("available", 0) or 0),
            "inbound": int(item.get("inbound", 0) or 0),
            "reserved": int(item.get("reserved", 0) or 0),
            "age_0_90": int(item.get("age_0_90", 0) or 0),
            "age_90_180": int(item.get("age_90_180", 0) or 0),
            "age_180_plus": int(item.get("age_180_plus", 0) or 0),
            "days_of_supply": None,
            "sales_velocity_7d": None,
        })
    return rows


def parse_profit(items: List[Dict], sid: int, country: str, date: str) -> List[Dict]:
    """解析利润列表"""
    rows = []
    for item in items:
        rows.append({
            "sid": sid,
            "country": country,
            "msku": item.get("msku", item.get("sku", "")),
            "date": date,
            "orders": int(item.get("orders", item.get("order_num", 0)) or 0),
            "units": int(item.get("units", item.get("unit_num", 0)) or 0),
            "sales": float(item.get("sales", item.get("sales_amount", 0)) or 0),
            "ad_spend": float(item.get("ad_spend", item.get("spend", 0)) or 0),
            "gross_profit": float(item.get("gross_profit", item.get("profit", 0)) or 0),
            "gross_margin": float(item.get("gross_margin", 0) or 0),
            "acos": float(item.get("acos", 0) or 0),
            "tacos": float(item.get("tacos", 0) or 0),
            "refund_rate": float(item.get("refund_rate", 0) or 0),
            "return_rate": float(item.get("return_rate", 0) or 0),
        })
    return rows


def parse_listings(items: List[Dict], sid: int, country: str) -> List[Dict]:
    """解析产品表现列表"""
    rows = []
    for item in items:
        rows.append({
            "sid": sid,
            "country": country,
            "msku": item.get("msku", ""),
            "asin": item.get("asin", ""),
            "parent_asin": item.get("parent_asin", ""),
            "title": item.get("item_name", ""),
            "brand": item.get("seller_brand", ""),
            "price": float(item.get("price", item.get("landed_price", 0)) or 0),
            "status": item.get("status_text", ""),
            "buybox_owner": item.get("principal_realname", ""),
            "seller_rank": int(item.get("seller_rank", 0) or 0),
            "reviews": int(item.get("reviews_num", 0) or 0),
            "stars": float(item.get("stars", 0) or 0),
            "sales_30d": int(item.get("thirty_volume", 0) or 0),
            "sales_7d": int(item.get("seven_volume", 0) or 0),
            "principal_uid": item.get("principal_uids", [None])[0] if item.get("principal_uids") else None,
            "principal_name": item.get("principal_realname", ""),
        })
    return rows


# sid → country 映射
SID_COUNTRY = {
    5018: "美国", 5019: "加拿大", 5020: "墨西哥", 5021: "日本",
    5022: "英国", 5023: "意大利", 5024: "德国", 5025: "法国",
    5026: "西班牙", 5027: "荷兰", 5028: "瑞典", 5029: "波兰",
    5030: "比利时", 5031: "爱尔兰", 5751: "巴西",
}


def main():
    parser = argparse.ArgumentParser(description="合并 MCP 原始数据为 snapshot JSON")
    parser.add_argument("--date", required=True, help="美西日期 YYYY-MM-DD")
    parser.add_argument("--raw-dir", default=None, help="raw 目录路径")
    parser.add_argument("--output", required=True, help="输出文件路径")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else (
        Path(__file__).resolve().parent.parent / "output" / "raw"
    )
    output_path = Path(args.output)

    all_inventory = []
    all_profit = []
    all_listings = []

    for sid, country in SID_COUNTRY.items():
        # 库存
        inv_path = raw_dir / f"{sid}-inventory.json"
        if inv_path.exists():
            data = load_mcp_result(inv_path)
            if data:
                items = data.get("list", data.get("data", []))
                if isinstance(items, dict):
                    items = items.get("list", [])
                all_inventory.extend(parse_inventory(items, sid, country))
                print(f"  ✅ {country} (sid={sid}) 库存: {len(items)} 条")

        # 利润
        profit_path = raw_dir / f"{sid}-profit.json"
        if profit_path.exists():
            data = load_mcp_result(profit_path)
            if data:
                items = data.get("list", data.get("data", []))
                if isinstance(items, dict):
                    items = items.get("list", [])
                all_profit.extend(parse_profit(items, sid, country, args.date))
                print(f"  ✅ {country} (sid={sid}) 利润: {len(items)} 条")

        # Listing
        listing_path = raw_dir / f"{sid}-listings.json"
        if listing_path.exists():
            data = load_mcp_result(listing_path)
            if data:
                items = data.get("list", data.get("data", []))
                if isinstance(items, dict):
                    items = items.get("list", [])
                all_listings.extend(parse_listings(items, sid, country))
                print(f"  ✅ {country} (sid={sid}) 产品表现: {len(items)} 条")

    snapshot = {
        "report_date": args.date,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "sids": [{"id": k, "country": v, "code": v} for k, v in SID_COUNTRY.items()],
        "inventory": all_inventory,
        "profit": all_profit,
        "listings": all_listings,
        "owners": [],  # 从 listing_owners.json 加载
        "metadata": {"source": "mcp", "raw_files": str(raw_dir)},
    }

    # 从 listing_owners.json 加载 owner 数据
    owners_path = raw_dir.parent / "listing_owners.json"
    if owners_path.exists():
        owners_data = json.loads(owners_path.read_text(encoding="utf-8"))
        owners_list = []
        for sid_str, site_data in owners_data.items():
            for msku, info in site_data.get("msku", {}).items():
                owners_list.append({
                    "sid": int(sid_str),
                    "msku": msku,
                    "owner_key": info.get("owner", "wang_yi"),
                    "owner_name": info.get("name", ""),
                    "uid": info.get("uid"),
                })
        snapshot["owners"] = owners_list

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ 合并完成: {output_path}")
    print(f"   库存 {len(all_inventory)} 条 | 利润 {len(all_profit)} 条 | Listing {len(all_listings)} 条")


if __name__ == "__main__":
    main()
