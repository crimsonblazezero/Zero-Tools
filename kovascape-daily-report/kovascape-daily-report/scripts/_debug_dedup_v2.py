"""
Debug v2: 直接调 dws 测试 filter 格式

目标：找出 aitable record query --filter 的正确语法
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

# Config paths
BASE = Path("D:/WorkBuddy/2026-07-25-08-51-51/kovascape-daily-report")
config = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))

NODE = config["aitable"]["invoker"]["node_path"]
DWS = config["aitable"]["invoker"]["dws_js"]
BASE_ID = config["aitable"]["base_id"]
TABLE_ID = config["aitable"]["table_id"]

def dws(args: list) -> dict:
    """调 dws 命令并返回解析结果"""
    full = [NODE, DWS] + args
    print(f"  ➜  {' '.join(str(a)[:80] for a in full)}")
    try:
        proc = subprocess.run(full, capture_output=True, text=True,
                            encoding="utf-8", shell=False, timeout=30)
        result = {}
        if proc.stdout.strip():
            result["stdout"] = proc.stdout
        if proc.stderr.strip():
            result["stderr"] = proc.stderr
        result["returncode"] = proc.returncode
        try:
            result["parsed"] = json.loads(proc.stdout) if proc.stdout.strip() else {}
        except json.JSONDecodeError:
            pass
        return result
    except Exception as e:
        return {"error": str(e)}


# === Test 1: 无 filter（基线）===
print("=" * 60)
print("📋 Test 1: 无 filter 查询全部")
print("=" * 60)
r = dws(["aitable", "record", "query",
         "--base-id", BASE_ID,
         "--table-id", TABLE_ID,
         "--limit", "5",
         "--format", "json"])
if "parsed" in r:
    recs = r["parsed"].get("data", {}).get("records", [])
    print(f"  ✅ 命中 {len(recs)} 条记录")
    for rec in recs:
        cells = rec.get("cells", {})
        print(f"    [{rec['recordId']}] date={cells.get('EZwJUfQ','')}")
else:
    print(f"  ❌ 失败: {r.get('stderr', '')[:300]}")
    print(f"  stdout: {r.get('stdout', '')[:300]}")

print()

# === Test 2: filter 格式 A — 嵌套 and/eq（当前 todo_dispatcher 的格式）===
print("=" * 60)
print("📋 Test 2: 嵌套 and/eq filter（当前代码格式）")
print("=" * 60)
filter_a = {"operator":"and","operands":[
    {"operator":"eq","operands":["EZwJUfQ","2026-07-26T00:00:00+08:00"]},
    {"operator":"eq","operands":["U4vyfOb","R04"]},
    {"operator":"eq","operands":["k5dL536","KF-2024-09-BLACK-30"]},
]}
r = dws(["aitable", "record", "query",
         "--base-id", BASE_ID,
         "--table-id", TABLE_ID,
         "--filter", json.dumps(filter_a, ensure_ascii=False),
         "--limit", "5",
         "--format", "json"])
stdout = r.get("stdout", "")
if "success" in stdout or "records" in stdout:
    parsed = json.loads(stdout)
    recs = parsed.get("data", {}).get("records", [])
    print(f"  ✅ 命中 {len(recs)} 条记录")
    for rec in recs:
        cells = rec.get("cells", {})
        print(f"    [{rec['recordId']}] date={cells.get('EZwJUfQ','')}")
elif r.get("returncode", 0) != 0:
    err = json.loads(stdout) if stdout else {}
    msg = err.get("error", {}).get("message", r.get("stderr", "unknown"))
    print(f"  ❌ 失败: {msg[:200]}")
else:
    print(f"  ❌ 无输出或格式异常")
    print(f"  stdout[:300]: {stdout[:300]}")
    print(f"  stderr[:300]: {r.get('stderr', '')[:300]}")

print()

# === Test 3: filter 格式 B — 尝试不同的 filter 结构 ===
# 也许需要 fieldFilterFormat 或 filterUp 格式？
print("=" * 60)
print("📋 Test 3: 可能 aitable 不支持 --filter JSON 格式")
print("   → 尝试用 dws 的等价参数或无 filter 直接查")
print("=" * 60)
r = dws(["aitable", "record", "query",
         "--base-id", BASE_ID,
         "--table-id", TABLE_ID,
         "--limit", "5",
         "--format", "json"])
print(f"  ✅ 无 filter 基准正常: {r.get('returncode')}")

print()

# === Test 4: filter 格式 C — 也许 filter 就是个 flat JSON 对象（MCP 原生格式）===
print("=" * 60)
print("📋 Test 4: flat JSON format {'fieldId': 'value'}")
print("=" * 60)
filter_c = {"EZwJUfQ": "2026-07-26T00:00:00+08:00", "U4vyfOb": "R04", "k5dL536": "KF-2024-09-BLACK-30"}
r = dws(["aitable", "record", "query",
         "--base-id", BASE_ID,
         "--table-id", TABLE_ID,
         "--filter", json.dumps(filter_c, ensure_ascii=False),
         "--limit", "5",
         "--format", "json"])
stdout = r.get("stdout", "")
if stdout.strip():
    parsed = json.loads(stdout)
    recs = parsed.get("data", {}).get("records", [])
    print(f"  ✅ 命中 {len(recs)} 条记录")
    for rec in recs:
        cells = rec.get("cells", {})
        print(f"    [{rec['recordId']}] date={cells.get('EZwJUfQ','')}")
elif r.get("returncode", 0) != 0:
    err = json.loads(stdout) if stdout else {}
    msg = err.get("error", {}).get("message", r.get("stderr", "unknown"))
    print(f"  ❌ 失败: {msg[:200]}")
else:
    print(f"  ⚪ 无结果（0 命中或格式不识别）")
