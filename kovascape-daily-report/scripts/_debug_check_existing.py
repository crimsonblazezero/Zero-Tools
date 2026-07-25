"""
深入调试 check_existing：逐步检查 filter 查询结果
"""
import json
import logging
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from todo_dispatcher import DwsInvoker, load_config, setup_logger

log = setup_logger()
log.setLevel(logging.DEBUG)

config = load_config()
invoker = DwsInvoker(config, log)

F = config["aitable"]["field_ids"]
BASE_ID = config["aitable"]["base_id"]
TABLE_ID = config["aitable"]["table_id"]

# 构造和 check_existing 一样的 filter
alert = {
    "rule_id": "R01",
    "msku": "KF-2024-09-BLACK-30",
    "_report_date": "2026-07-26",
}

# 手动构造 filter（不带日期条件）
filter_obj = {
    "operator": "and",
    "operands": [
        {"operator": "eq", "operands": [F["rule"], alert["rule_id"]]},
        {"operator": "eq", "operands": [F["msku"], alert["msku"]]},
    ]
}

print(f"Filter: {json.dumps(filter_obj, ensure_ascii=False)}")
print()

result = invoker.run([
    "aitable", "record", "query",
    "--base-id", BASE_ID,
    "--table-id", TABLE_ID,
    "--filter", json.dumps(filter_obj, ensure_ascii=False),
    "--limit", "20",
    "--format", "json",
])

print(f"Success: {result.get('success')}")
if result.get("success"):
    records = result.get("data", {}).get("records") or []
    print(f"命中: {len(records)} 条")
    
    for rec in records:
        cells = rec.get("cells", {})
        date_val = cells.get(F["date"], "")
        rule_val = cells.get(F["rule"], "")
        msku_val = cells.get(F["msku"], "")
        date_startswith = date_val.startswith(alert["_report_date"]) if isinstance(date_val, str) else False
        print(f"  [{rec['recordId']}] date='{date_val}' (type={type(date_val).__name__}) | rule='{rule_val}' | msku='{msku_val}'")
        print(f"    startswith('{alert['_report_date']}') = {date_startswith}")
        print(f"    recordId={rec['recordId']}, full cells keys={list(cells.keys())}")
else:
    print(f"Error: {result.get('error')}")
    print(f"Raw: {result}")
