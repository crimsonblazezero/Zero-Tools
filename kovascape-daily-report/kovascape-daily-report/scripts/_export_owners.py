"""
批量拉取所有 KovaScape 站点的 Listing 负责人映射

输出：output/listing_owners.json
  { sid: { msku: {"uid": ..., "name": ...}, asin: {"uid": ..., "name": ...} } }
"""
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import yaml

BASE = Path("D:/WorkBuddy/2026-07-25-08-51-51/kovascape-daily-report")
config = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))

# 领星 MCP 的 tool 名称
TOOL = "mcp__LingXing-MCP__erp_listing"

# 15 个 KS- sid
SIDS = config["lingxing"]["sids"]  # [{id: 5018, country: "美国", code: "US"}, ...]

# 领星 UID → 内部 owner_key 映射
UID_TO_OWNER = {
    10896311: "wang_yi",   # 王祎
    10923094: "hua_yibo",  # 化一博
}

# 输出
OUT_PATH = BASE / "output" / "listing_owners.json"

def call_mcp(sid: int, offset: int = 0) -> dict:
    """调 erp_listing 拉一页（模拟 MCP 调用，走 dws invoke）"""
    # 这里用 Python 直接调 dws invoke 命令
    node = config["aitable"]["invoker"]["node_path"]
    dws_js = config["aitable"]["invoker"]["dws_js"]

    payload = json.dumps({
        "offset": offset,
        "length": 200,  # 每页 200 条
        "pvi_ids": "",
        "sids": str(sid),
        "sort_field": "msku",
        "sort_type": "asc",
    }, ensure_ascii=False)

    args = [node, dws_js, "mcp", "tool", "invoke",
            "--tool", TOOL,
            "--payload", payload,
            "--format", "json"]

    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", shell=False, timeout=60)

    try:
        result = json.loads(proc.stdout)
        # 解析 MCP 返回
        # response 结构可能有嵌套，要看 dws 的输出格式
        data_obj = result
        # 尝试取 data
        for key in ["data", "result", "response"]:
            if key in data_obj and isinstance(data_obj[key], dict):
                data_obj = data_obj[key]
                break
        # 取内层 data
        inner = data_obj.get("data", {})
        if isinstance(inner, dict) and inner.get("list"):
            return inner
        elif isinstance(inner, dict) and inner.get("data", {}).get("list"):
            return inner["data"]
        # 直接返回
        return inner or data_obj
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ⚠️ 解析失败: {e}")
        print(f"  stdout[:300]: {proc.stdout[:300]}")
        return {}


def extract_owners_from_response(data: dict) -> dict:
    """从 erp_listing 响应提取 MSKU/ASIN → 负责人"""
    result = {"msku": {}, "asin": {}, "parent_asin": {}}
    listings = data.get("list", data.get("data", []))
    if isinstance(listings, dict) and "list" in listings:
        listings = listings["list"]
    if not isinstance(listings, list):
        return result

    for item in listings:
        msku = item.get("msku", "")
        asin = item.get("asin", "")
        parent_asin = item.get("parent_asin", "")
        principal_list = item.get("principal_list", [])
        principal_uids = item.get("principal_uids", [])
        principal_name = item.get("principal_realname", "")

        uid = principal_uids[0] if principal_uids else None
        owner_key = UID_TO_OWNER.get(uid, "wang_yi") if uid else "wang_yi"

        if msku:
            result["msku"][msku] = {"uid": uid, "name": principal_name, "owner": owner_key}
        if asin:
            result["asin"][asin] = {"uid": uid, "name": principal_name, "owner": owner_key}
        if parent_asin:
            result["parent_asin"][parent_asin] = {"uid": uid, "name": principal_name, "owner": owner_key}

    return result


def main():
    all_owners = {}

    for s in SIDS:
        sid = s["id"]
        country = s["country"]
        code = s["code"]
        print(f"\n📦 {country} ({code}) sid={sid}")

        page_owners = {"msku": {}, "asin": {}, "parent_asin": {}}
        offset = 0
        total = 0

        while True:
            print(f"  拉取 offset={offset}...", end=" ", flush=True)
            data = call_mcp(sid, offset)
            listings = data.get("list") or data.get("data") or []
            if isinstance(listings, dict):
                listings = listings.get("list") or []

            if not listings:
                print("无更多数据")
                break

            page = extract_owners_from_response({"list": listings})
            for k in page_owners:
                page_owners[k].update(page[k])

            offset += len(listings)
            total += len(listings)
            print(f"累计 {total} 条")

            # 如果返回不足 200 条，已到最后一页
            if len(listings) < 200:
                break

            time.sleep(1)  # 限流

        print(f"  ✅ {country} 完成: {total} listings, {len(page_owners['msku'])} MSKUs")
        all_owners[str(sid)] = page_owners

    # 保存
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_owners, f, ensure_ascii=False, indent=2)

    # 统计汇总
    total_msku = sum(len(v["msku"]) for v in all_owners.values())
    total_asin = sum(len(v["asin"]) for v in all_owners.values())
    owner_counts = defaultdict(int)
    for v in all_owners.values():
        for msku_data in v["msku"].values():
            owner_counts[msku_data["owner"]] += 1
    print(f"\n{'='*60}")
    print(f"✅ 导出完成")
    print(f"   总 MSKU 数: {total_msku}")
    print(f"   总 ASIN 数: {total_asin}")
    print(f"   归属分布:")
    for owner, cnt in sorted(owner_counts.items()):
        print(f"     {owner}: {cnt}")
    print(f"   文件: {OUT_PATH}")


if __name__ == "__main__":
    main()
