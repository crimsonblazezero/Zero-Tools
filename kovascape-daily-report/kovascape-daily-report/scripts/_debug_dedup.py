"""
Debug: 测试 dedup filter 查询为什么返回空
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 加载配置
config = yaml.safe_load(open(
    r"D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\config.yaml",
    encoding="utf-8"
))

node_path = config["aitable"]["invoker"]["node_path"]
dws_js = config["aitable"]["invoker"]["dws_js"]
base_id = config["aitable"]["base_id"]
table_id = config["aitable"]["table_id"]
field_ids = config["aitable"]["field_ids"]

print("=" * 60)
print("🔍 测试 1: 不加 filter 查全部记录")
print("=" * 60)

args = [
    node_path, dws_js,
    "aitable", "record", "query",
    "--base-id", base_id,
    "--table-id", table_id,
    "--limit", "20",
    "--format", "json",
]
result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", shell=False, timeout=30)
data = json.loads(result.stdout) if result.stdout else {}
records = data.get("data", {}).get("records", [])
print(f"总记录数: {len(records)}")
for r in records[:15]:
    cells = r.get("cells", {})
    print(f"  [{r['recordId']}] date={cells.get('EZwJUfQ','')} rule={cells.get('U4vyfOb','')} msku={cells.get('k5dL536','')} asin={cells.get('Bz1fDqU','N/A')}")

print()
print("=" * 60)
print("🔍 测试 2: filter = 纯日期 '2026-07-26' (当前代码)")
print("=" * 60)

filter1 = json.dumps({
    "operator": "and",
    "operands": [
        {"operator": "eq", "operands": [field_ids["date"], "2026-07-26"]},
        {"operator": "eq", "operands": [field_ids["rule"], "R04"]},
        {"operator": "eq", "operands": [field_ids["msku"], "KF-2024-09-BLACK-30"]},
    ]
}, ensure_ascii=False)

args1 = [
    node_path, dws_js,
    "aitable", "record", "query",
    "--base-id", base_id,
    "--table-id", table_id,
    "--filter", filter1,
    "--limit", "5",
    "--format", "json",
]
print(f"Filter: {filter1}")
result1 = subprocess.run(args1, capture_output=True, text=True, encoding="utf-8", shell=False, timeout=30)
try:
    data1 = json.loads(result1.stdout) if result1.stdout else {}
    records1 = data1.get("data", {}).get("records", [])
    print(f"命中记录: {len(records1)}")
    for r in records1:
        cells = r.get("cells", {})
        print(f"  [{r['recordId']}] date={cells.get('EZwJUfQ','')}")
    if result1.stderr:
        print(f"stderr: {result1.stderr[:500]}")
except json.JSONDecodeError as e:
    print(f"JSON解析失败: {e}")
    print(f"stdout: {result1.stdout[:1000]}")
    print(f"stderr: {result1.stderr[:500]}")

print()
print("=" * 60)
print("🔍 测试 3: filter = datetime '2026-07-26T00:00:00+08:00'")
print("=" * 60)

filter2 = json.dumps({
    "operator": "and",
    "operands": [
        {"operator": "eq", "operands": [field_ids["date"], "2026-07-26T00:00:00+08:00"]},
        {"operator": "eq", "operands": [field_ids["rule"], "R04"]},
        {"operator": "eq", "operands": [field_ids["msku"], "KF-2024-09-BLACK-30"]},
    ]
}, ensure_ascii=False)

args2 = [
    node_path, dws_js,
    "aitable", "record", "query",
    "--base-id", base_id,
    "--table-id", table_id,
    "--filter", filter2,
    "--limit", "5",
    "--format", "json",
]
print(f"Filter: {filter2}")
result2 = subprocess.run(args2, capture_output=True, text=True, encoding="utf-8", shell=False, timeout=30)
try:
    data2 = json.loads(result2.stdout) if result2.stdout else {}
    records2 = data2.get("data", {}).get("records", [])
    print(f"命中记录: {len(records2)}")
    for r in records2:
        cells = r.get("cells", {})
        print(f"  [{r['recordId']}] date={cells.get('EZwJUfQ','')}")
    if result2.stderr:
        print(f"stderr: {result2.stderr[:500]}")
except json.JSONDecodeError as e:
    print(f"JSON解析失败: {e}")
    print(f"stdout: {result2.stdout[:1000]}")
    print(f"stderr: {result2.stderr[:500]}")
