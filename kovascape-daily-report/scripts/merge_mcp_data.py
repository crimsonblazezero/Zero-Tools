"""
KovaScape Daily Report - MCP原始数据合并器 v2
=================================================

从 output/raw/ 目录读取 MCP 返回的原始 JSON 文件，
合并为 DailySnapshot 格式供规则引擎使用。

v2 改动：统一使用 query_product_performance_asin_lists 接口，
        该接口返回 sales/profit/ad/inventory/ranking 全部字段，
        且正确支持 sids 过滤 + 日期范围。

用法：
  python merge_mcp_data.py --date 2026-07-26 --output ../output/snapshot-2026-07-26.json
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_mcp_result(path: Path) -> Optional[Dict]:
    """加载 MCP 调用返回的原始 JSON，提取内层 data"""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        for key in ["data", "result", "response"]:
            if key in data and isinstance(data[key], dict):
                data = data[key]
        if "data" in data and isinstance(data["data"], dict) and "list" in data["data"]:
            return data["data"]
        if "list" in data:
            return data
        return data
    except Exception:
        return None


def extract_msku_from_key(msku_sid_str: str) -> str:
    """从 msku_sid_str 提取 MSKU

    格式：KSNE-PF-N12-AL0810GOL1P$|$5018$|$B0GZMLVX7G$|$null$|$...
    """
    if not msku_sid_str:
        return ""
    parts = msku_sid_str.split("$|$")
    return parts[0] if parts else ""


def extract_sid_from_response(items: List[Dict]) -> Optional[int]:
    """从响应中提取 sid（取第一条记录的 seller_store_countries）"""
    for item in items:
        sids = item.get("sids", [])
        if sids:
            return sids[0]
        stores = item.get("seller_store_countries", [])
        if stores:
            # Try to match sid from msku_sid_str
            msku_sid = item.get("msku_sid_str", "")
            match = re.search(r'\$|\$(\d+)\$|\$', msku_sid)
            if match:
                return int(match.group(1))
    return None


def parse_performance(items: List[Dict]) -> tuple[List[Dict], List[Dict], List[Dict]]:
    """从 query_product_performance_asin_lists 响应中解析：
    
    返回：(profit_rows, listing_rows, inventory_rows)
    """
    profit_rows = []
    listing_rows = []
    inventory_rows = []

    sid_country = {item["sid"]: item["country"] for item in SID_COUNTRY_LIST}

    for item in items:
        # 提取 sid
        sids = item.get("sids", [])
        sid = sids[0] if sids else 0
        country = sid_country.get(sid, "未知")

        # 提取 MSKU
        msku = extract_msku_from_key(item.get("msku_sid_str", ""))
        if not msku:
            msku = item.get("msku") or ""

        # 提取 ASIN
        asin = item.get("asin", "")
        parent_asin = None
        parent_asins = item.get("parent_asins", [])
        if parent_asins and isinstance(parent_asins, list) and len(parent_asins) > 0:
            parent_asin = parent_asins[0].get("parent_asin", "")

        # profit 行
        profit_rows.append({
            "sid": sid,
            "country": country,
            "msku": msku,
            "date": "",  # 由外部填入
            "orders": int(item.get("volume", 0) or 0),
            "units": int(item.get("volume", 0) or 0),
            "sales": float(item.get("amount", 0) or 0),
            "ad_spend": float(item.get("spend", 0) or 0),
            "gross_profit": float(item.get("gross_profit", 0) or 0),
            "gross_margin": float(item.get("gross_margin", 0) or 0),
            "acos": float(item.get("acos", 0) or 0) * 100,  # MCP 返回小数，转百分比
            "tacos": float(item.get("tacos", 0) or 0) * 100,
            "refund_rate": float(item.get("refund_rate", 0) or 0),
            "return_rate": float(item.get("return_rate", 0) or 0),
        })

        # listing 行
        cate_ranks = item.get("small_cate_rank", [])
        seller_rank = item.get("cate_rank", 0)
        reviews = int(item.get("reviews_count", 0) or 0)
        stars = float(item.get("avg_star", 0) or 0)
        buybox_pct = item.get("buy_box_percentage")

        listing_rows.append({
            "sid": sid,
            "country": country,
            "msku": msku,
            "asin": asin,
            "parent_asin": parent_asin,
            "title": item.get("item_name", ""),
            "brand": "KovaScape",
            "price": float(item.get("avg_custom_price", 0) or 0),
            "status": "在售",
            "buybox_owner": "KovaScape" if buybox_pct and buybox_pct > 0 else None,
            "is_hijacked": False,
            "seller_rank": seller_rank,
            "reviews": reviews,
            "stars": stars,
            "sales_30d": int(item.get("volume_30d", 0) or 0),
            "sales_7d": int(item.get("volume_7d", 0) or 0),
            "principal_uid": None,
            "principal_name": (item.get("principal_names", [""]) or [""])[0] if item.get("principal_names") else "",
        })

        # inventory（简版——从 available_inventory 提取）
        avail = item.get("available_inventory", {})
        inventory_rows.append({
            "sid": sid,
            "country": country,
            "msku": msku,
            "fnsku": None,
            "asin": asin,
            "available": int(avail.get("afn_fulfillable_quantity", 0) or 0),
            "inbound": int(avail.get("afn_inbound_working_quantity", 0) or 0),
            "reserved": int(avail.get("afn_reserved_quantity", 0) or 0),
            "age_0_90": 0,  # 此接口不返回库龄
            "age_90_180": 0,
            "age_180_plus": 0,
            "days_of_supply": None,
            "sales_velocity_7d": None,
        })

    return profit_rows, listing_rows, inventory_rows


# sid → country 映射
SID_COUNTRY = {
    5018: "美国", 5019: "加拿大", 5020: "墨西哥", 5021: "日本",
    5022: "英国", 5023: "意大利", 5024: "德国", 5025: "法国",
    5026: "西班牙", 5027: "荷兰", 5028: "瑞典", 5029: "波兰",
    5030: "比利时", 5031: "爱尔兰", 5751: "巴西",
}
SID_COUNTRY_LIST = [{"sid": k, "country": v} for k, v in SID_COUNTRY.items()]


def main():
    parser = argparse.ArgumentParser(description="合并 MCP 原始数据为 snapshot JSON v2")
    parser.add_argument("--date", required=True, help="美西日期 YYYY-MM-DD")
    parser.add_argument("--raw-dir", default=None, help="raw 目录路径")
    parser.add_argument("--output", required=True, help="输出文件路径")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else (
        Path(__file__).resolve().parent.parent / "output" / "raw"
    )
    output_path = Path(args.output)

    all_profit = []
    all_listings = []
    all_inventory = []

    for sid in SID_COUNTRY:
        # 新格式：performance 文件（推荐）
        perf_path = raw_dir / f"{sid}-performance.json"
        if perf_path.exists():
            data = load_mcp_result(perf_path)
            if data:
                items = data.get("list", data.get("data", []))
                if isinstance(items, dict):
                    items = items.get("list", [])
                profits, listings, inventory = parse_performance(items)
                all_profit.extend(profits)
                all_listings.extend(listings)
                all_inventory.extend(inventory)
                print(f"  ✅ {SID_COUNTRY[sid]} (sid={sid}) performance: {len(items)} 条")
                continue

        # 兼容旧格式：inventory.json + profit.json + listings.json
        found_any = False

        inv_path = raw_dir / f"{sid}-inventory.json"
        if inv_path.exists():
            found_any = True
            # 旧格式暂不深度处理，标记为已废弃
            print(f"  ⚠️ {SID_COUNTRY[sid]} (sid={sid}) 旧 inventory 格式，请改用 performance")

        profit_path = raw_dir / f"{sid}-profit.json"
        if profit_path.exists():
            found_any = True
            print(f"  ⚠️ {SID_COUNTRY[sid]} (sid={sid}) 旧 profit 格式，请改用 performance")

        listing_path = raw_dir / f"{sid}-listings.json"
        if listing_path.exists():
            found_any = True
            print(f"  ⚠️ {SID_COUNTRY[sid]} (sid={sid}) 旧 listings 格式，请改用 performance")

        if not found_any:
            print(f"  ⏭ {SID_COUNTRY[sid]} (sid={sid}) 无数据")

    # 注入日期到 profit rows
    for p in all_profit:
        p["date"] = args.date

    # 计算 inventory 派生字段（days_of_supply, sales_velocity_7d）
    for inv in all_inventory:
        msku = inv["msku"]
        # 找对应的 sales_7d
        for lh in all_listings:
            if lh["msku"] == msku and lh["sid"] == inv["sid"]:
                inv["sales_velocity_7d"] = lh.get("sales_7d", 0) / 7
                if inv["sales_velocity_7d"] and inv["sales_velocity_7d"] > 0:
                    inv["days_of_supply"] = inv["available"] / inv["sales_velocity_7d"]
                break

    snapshot = {
        "report_date": args.date,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "sids": [{"id": k, "country": v, "code": v} for k, v in SID_COUNTRY.items()],
        "inventory": all_inventory,
        "profit": all_profit,
        "listings": all_listings,
        "owners": [],
        "metadata": {"source": "mcp", "raw_files": str(raw_dir), "version": "v2"},
    }

    # 从 listing_owners.json 加载 owner 数据
    owners_path = raw_dir.parent / "listing_owners.json"
    if owners_path.exists():
        owners_data = json.loads(owners_path.read_text(encoding="utf-8"))
        owners_list = []
        seen = set()
        for sid_str, site_data in owners_data.items():
            for msku, info in site_data.get("msku", {}).items():
                key = f"{sid_str}|{msku}"
                if key not in seen:
                    owners_list.append({
                        "sid": int(sid_str),
                        "msku": msku,
                        "owner_key": info.get("owner", "wang_yi"),
                        "owner_name": info.get("name", ""),
                        "uid": info.get("uid"),
                    })
                    seen.add(key)
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
