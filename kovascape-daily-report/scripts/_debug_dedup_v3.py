"""
Debug v3: 逐一排除 filter 条件，找出哪个字段导致 INVALID_PARAM
"""
import json
import subprocess
import sys
from pathlib import Path

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
    print(f"  ➜  args={len(full)}个")
    try:
        proc = subprocess.run(full, capture_output=True, text=True,
                            encoding="utf-8", shell=False, timeout=30)
        out, err = proc.stdout.strip(), proc.stderr.strip()
        result = {"rc": proc.returncode, "stdout": out, "stderr": err}
        if out:
            try:
                result["parsed"] = json.loads(out)
            except json.JSONDecodeError:
                pass
        return result
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def test(desc: str, filter_obj: dict):
    print(f"\n--- {desc} ---")
    json_str = json.dumps(filter_obj, ensure_ascii=False)
    r = dws(["aitable", "record", "query",
             "--base-id", BASE_ID,
             "--table-id", TABLE_ID,
             "--filter", json_str,
             "--limit", "5",
             "--format", "json"])
    if "parsed" in r:
        p = r["parsed"]
        if "error" in p and p.get("error", {}).get("message", ""):
            emsg = p["error"]["message"]
            if "SCAN_RECORDS_FAILED" in emsg:
                print(f"  ❌ SCAN_RECORDS_FAILED: {emsg[:150]}")
            else:
                print(f"  ❌ {emsg[:150]}")
        else:
            recs = p.get("data", {}).get("records", [])
            status = p.get("status", "")
            print(f"  ✅ status={status}, 命中 {len(recs)} 条")
            for rec in recs:
                c = rec.get("cells", {})
                print(f"    [{rec['recordId']}] {c.get('EZwJUfQ','')} | {c.get('U4vyfOb','')} | {c.get('k5dL536','')}")
    else:
        err_msg = json.loads(r["stdout"]).get("error",{}).get("message","unknown") if r["stdout"] else r.get("stderr","")
        print(f"  ⚪ 结果: {err_msg[:150]}")


# Test A: 只有 rule 条件
test("A: 仅 rule eq R04",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["rule"], "R04"]}
     ]})

# Test B: rule + msku（无日期）
test("B: rule + msku",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["rule"], "R04"]},
         {"operator":"eq","operands":[F["msku"], "KF-2024-09-BLACK-30"]}
     ]})

# Test C: 仅日期（纯字符串 "2026-07-26"）
test("C: 仅日期 2026-07-26（纯字符串）",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["date"], "2026-07-26"]}
     ]})

# Test D: 仅日期（完整 datetime）
test("D: 仅日期 2026-07-26T00:00:00+08:00（完整 datetime）",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["date"], "2026-07-26T00:00:00+08:00"]}
     ]})

# Test E: 只查 MSKU
test("E: 仅 msku eq",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["msku"], "KF-2024-09-BLACK-30"]}
     ]})

# Test F: 不传 --filter, 用 URL query params 方式? 不支持的话会报错
print("\n\n--- F: 尝试 --fieldId/--value 参数（如存在）---")


# Test G: 确认 --filter 参数名称拼写（尝试 --filters 复数）
test("G: --filters（复数） 单条件 rule eq R04",
     {"operator":"and","operands":[
         {"operator":"eq","operands":[F["rule"], "R04"]}
     ]})
