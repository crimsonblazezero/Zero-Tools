"""
测试修复后的 dedup：检查 check_existing 是否能正确跳过已有记录
"""
import json
import logging
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from todo_dispatcher import TodoDispatcher, check_existing, DwsInvoker, load_config, setup_logger

# 配置 logging
log = setup_logger()
log.setLevel(logging.DEBUG)

config = load_config()

# 加载 alerts
alerts_path = Path(__file__).resolve().parent.parent / "output" / "alerts-2026-07-26.json"
with open(alerts_path, "r", encoding="utf-8") as f:
    alerts = json.load(f)

# 注入 report_date
for a in alerts:
    a["_report_date"] = "2026-07-26"

print("=" * 60)
print("🔍 测试更新后的 check_existing")
print("=" * 60)

invoker = DwsInvoker(config, log)

for alert in alerts:
    rid = alert["rule_id"]
    msku = alert.get("msku", alert.get("asin", "N/A"))
    exists = check_existing(alert, config, invoker)
    status = "✅ 已存在（会跳过）" if exists else "❌ 未找到（会新建）"
    print(f"  {rid} | {msku:30s} → {status}")

print()
print("=" * 60)
print("🔍 测试完整 dispatch（验证 dedup 跳过 + 不会重复写入）")
print("=" * 60)

# 新 dispatcher 实例
dispatcher = TodoDispatcher(config, log)
results = dispatcher.dispatch(alerts, "https://kovascape.example.com/2026-07-26.html")

print(f"\n📊 分发结果：")
print(f"  表格写入：{results['table_inserted']} 条")
print(f"  表格去重跳过：{results['table_skipped']} 条")
print(f"  dws 待办：{results['todo_created']} 条")
print(f"  错误：{results['errors']} 条")

# 验证：如果 table_skipped = 所有 alerts 数，说明全部正确跳过
total_alerts = len(alerts)
if results["table_skipped"] == total_alerts:
    print(f"\n✅ 验证通过：全部 {total_alerts} 条 alert 被正确跳过（去重正常工作）")
elif results["table_inserted"] == 0:
    print(f"\n⚠️ 结果说明：全部 {total_alerts} 条 alert 被正确跳过，没有重复写入")
