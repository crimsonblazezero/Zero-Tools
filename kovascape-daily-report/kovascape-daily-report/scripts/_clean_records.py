"""
清理 aitable 中的重复记录流程
1. 查询全部记录
2. 按 (date+rule+msku) 分组，每组保留第1条
3. 删除其余
"""
import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

import yaml

BASE = Path("D:/WorkBuddy/2026-07-25-08-51-51/kovascape-daily-report")
config = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))

NODE = config["aitable"]["invoker"]["node_path"]
DWS = config["aitable"]["invoker"]["dws_js"]
BASE_ID = config["aitable"]["base_id"]
TABLE_ID = config["aitable"]["table_id"]
F = config["aitable"]["field_ids"]

def dws(args: list) -> dict:
    full = [NODE, DWS] + args
    proc = subprocess.run(full, capture_output=True, text=True,
                         encoding="utf-8", shell=False, timeout=30)
    result = {"rc": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    if proc.stdout.strip():
        try:
            result["parsed"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return result

# Step 1: 查询全部记录（用 2 次分页，每页 100）
all_records = []
cursor = None
while True:
    args = ["aitable", "record", "query",
            "--base-id", BASE_ID,
            "--table-id", TABLE_ID,
            "--limit", "100",
            "--format", "json"]
    if cursor:
        args.extend(["--cursor", cursor])
    r = dws(args)
    recs = r.get("parsed", {}).get("data", {}).get("records", [])
    if not recs:
        break
    all_records.extend(recs)
    cursor = r.get("parsed", {}).get("data", {}).get("nextCursor", None)
    if not cursor:
        break

print(f"📊 总记录数: {len(all_records)}")

# Step 2: 按 (date+rule+msku) 分组
groups = defaultdict(list)
for rec in all_records:
    c = rec.get("cells", {})
    date = c.get(F["date"], "").split("T")[0]  # 取日期部分
    rule = c.get(F["rule"], "")
    msku = c.get(F["msku"], "") or c.get(F["asin"], "")
    key = f"{date}|{rule}|{msku}"
    groups[key].append(rec["recordId"])

print(f"📊 唯一组合数: {len(groups)}")
for key, ids in sorted(groups.items()):
    print(f"  {key}: {len(ids)}条 → 保留 {ids[0]}，删除 {ids[1:]}")

# Step 3: 删除重复
to_delete = []
kept = set()
for key, ids in groups.items():
    kept.add(ids[0])  # 保留第1条
    to_delete.extend(ids[1:])  # 删除其余

if not to_delete:
    print("\n✅ 无重复记录")
    sys.exit(0)

print(f"\n🗑️ 待删除 {len(to_delete)} 条: {to_delete}")

# 批量删除（ailtable record delete 可能一次只删一条，逐条删）
deleted = 0
for rid in to_delete:
    resp = dws(["aitable", "record", "delete",
                "--base-id", BASE_ID,
                "--table-id", TABLE_ID,
                "--record-ids", rid,
                "--yes",
                "--format", "json"])
    if resp.get("parsed", {}).get("success"):
        deleted += 1
        print(f"  ✅ 删除 {rid}")
    else:
        err = resp.get("parsed", {}).get("error", {})
        print(f"  ❌ 删除 {rid} 失败: {err}")

print(f"\n🎉 已删除 {deleted} 条重复记录")
print(f"📊 保留 {len(kept)} 条唯一记录")
