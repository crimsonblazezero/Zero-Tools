"""Test: 直接用 todo_dispatcher 的 build_record 看 cells"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from todo_dispatcher import build_record

config = yaml.safe_load(open(r"D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\config.yaml", encoding="utf-8"))

with open(r"D:\WorkBuddy\2026-07-25-08-51-51\kovascape-daily-report\output\alerts-2026-07-26.json", encoding="utf-8") as f:
    alerts = json.load(f)

# 注入 report_date
for a in alerts:
    a["_report_date"] = "2026-07-26"

alert = alerts[0]
record = build_record(alert, config, "https://kovascape.example.com/2026-07-26.html")
print("Record cells:")
print(json.dumps(record, ensure_ascii=False, indent=2))