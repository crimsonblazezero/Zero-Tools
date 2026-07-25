"""Debug: 直接调 dws aitable record create 看请求结构"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 加载 config + alerts
config = yaml.safe_load(open(r"D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\config.yaml", encoding="utf-8"))
with open(r"D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\output\alerts-2026-07-26.json", encoding="utf-8") as f:
    alerts = json.load(f)

alert = alerts[0]
print("First alert:", json.dumps(alert, ensure_ascii=False, indent=2))

# 构造 record
field_ids = config["aitable"]["field_ids"]
report_date = "2026-07-26"

record_cells = {
    field_ids["date"]: report_date,
    field_ids["rule"]: alert["rule_id"],
    field_ids["level"]: alert["level"],
    field_ids["status"]: "待处理",
    field_ids["msku"]: alert.get("msku", ""),
    field_ids["site"]: alert.get("country", ""),
    field_ids["owner"]: [{"userId": alert.get("owner_user_id", "")}],
}

records = [{"cells": record_cells}]
print("\nRecord to send:", json.dumps(records, ensure_ascii=False, indent=2))

# 直接调 dws
node_path = config["aitable"]["invoker"]["node_path"]
dws_js = config["aitable"]["invoker"]["dws_js"]
base_id = config["aitable"]["base_id"]
table_id = config["aitable"]["table_id"]

args = [
    node_path, dws_js,
    "aitable", "record", "create",
    "--base-id", base_id,
    "--table-id", table_id,
    "--records", json.dumps(records, ensure_ascii=False),
    "--yes",
    "--format", "json",
]

print("\nArgs:", args)

result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", shell=False, timeout=60)
print("\nstdout:", result.stdout[:2000])
print("\nstderr:", result.stderr[:500])