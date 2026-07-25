"""
Print the FULL raw response from invoker.run() with filter to see structure
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

filter_obj = {
    "operator": "and",
    "operands": [
        {"operator": "eq", "operands": [F["rule"], "R01"]},
        {"operator": "eq", "operands": [F["msku"], "KF-2024-09-BLACK-30"]},
    ]
}

result = invoker.run([
    "aitable", "record", "query",
    "--base-id", BASE_ID,
    "--table-id", TABLE_ID,
    "--filter", json.dumps(filter_obj, ensure_ascii=False),
    "--limit", "20",
    "--format", "json",
])

print("=== RAW RESULT ===")
print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
