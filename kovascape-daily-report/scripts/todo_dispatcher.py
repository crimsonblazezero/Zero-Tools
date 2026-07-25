"""
KovaScape Daily Report - 行动分发器
=====================================

职责：
  1. 读 alerts.json
  2. dedup 检查（已有不重复创建）
  3. 把 alert 写入 KovaScape 工作大表 → 9.0_日报行动项
  4. 对 P0 + due_hours <= 4 的 alert 创建 dws 待办（DING 强推）

⚠️ dws CLI 调用：直接调 node + dws.js（绕过 .cmd wrapper，避免 shell 转义损坏 JSON）

作者：Zero/王祎 + AI
版本：v0.1 (W2)
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# 复用 data_layer
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ============================================
# dws CLI 调用（核心：绕过 .cmd wrapper）
# ============================================

class DwsInvoker:
    """直接调 node + dws.js，避免 shell 转义损坏 JSON"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.logger = logger
        inv = config["aitable"]["invoker"]
        self.node_path = inv["node_path"]
        self.dws_js = inv["dws_js"]

    def run(self, args: List[str], json_args: Optional[Dict] = None) -> Dict:
        """调 dws 命令，json_args 自动注入到 --records/--fields

        args: 基础参数列表，如 ['aitable', 'record', 'query', '--base-id', 'X', '--table-id', 'Y']
        json_args: JSON 数据 dict（会被 JSON 序列化注入到 args 里）
        """
        full_args = [self.node_path, self.dws_js] + list(args)

        # 找到需要替换的 JSON flag（如 --records / --fields）
        # 实现：先转成命令行字符串，再注入 JSON
        if json_args is not None:
            for key, value in json_args.items():
                # 找到 --key 并替换下一个 arg（无论占位符是什么）
                flag = f"--{key}"
                if flag in full_args:
                    idx = full_args.index(flag)
                    # 总是替换 flag 后面的 arg
                    full_args[idx + 1] = json.dumps(value, ensure_ascii=False)

        self.logger.debug(f"[dws] cmd: {' '.join(full_args[:5])}...")
        if self.logger.level <= logging.DEBUG:
            # 调试：打印完整 args（特别是 records 的 JSON）
            for i, a in enumerate(full_args):
                if a.startswith("[{"):
                    self.logger.debug(f"  arg[{i}]: {a[:200]}...")
                elif "records" in a or "fields" in a:
                    self.logger.debug(f"  arg[{i}]={a}: <next arg>")

        try:
            proc = subprocess.run(
                full_args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                timeout=60,
            )
            stdout = proc.stdout.strip()
            if proc.returncode != 0:
                stderr = proc.stderr.strip()
                # dws 失败时 stdout 通常含 JSON error
                try:
                    return {"success": False, "error": json.loads(stdout), "stderr": stderr}
                except json.JSONDecodeError:
                    return {"success": False, "error": {"message": stderr or stdout}}
            try:
                return {"success": True, "data": json.loads(stdout)}
            except json.JSONDecodeError:
                return {"success": True, "raw": stdout}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": {"message": "timeout"}}
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}


# ============================================
# 行动剧本生成器
# ============================================

ACTION_PLAYBOOKS = {
    "R01": """## R01 缺货处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：立即提价（5-10%）
- 进入 Seller Central → Inventory → Manage Inventory
- 找到该 MSKU → Edit → Price → 加 5-10%
- 目的：减缓消耗速度，避免 0 库存

### 步骤 2：暂停广告（如 ACoS > 25%）
- 进入 Advertising → Campaigns → 找到关联广告活动
- Pause 该广告活动
- 防止继续烧钱

### 步骤 3：紧急补货评估
- 联系供应链：能否调拨其他仓库/站点库存？
- 评估空运加急 vs 海运时间窗口
- 目标：48 小时内确认发货方案

### 步骤 4：在领星登记本次处置
- 记录提价幅度 / 暂停广告 ID / 补货计划
""",

    "R02": """## R02 毛利<0 处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：分析亏损原因
- 进入领星 → 商品分析 → 看利润明细
- 判断是 ad_spend 过高 / 售价过低 / 退货成本过高
- 7 日毛利 ${profit}，销售额 ${sales}，广告 ${ad_spend}

### 步骤 2：立即止损（任选）
- **A. 调整价格**：提价 5-10%，减少低毛利订单
- **B. 暂停广告**：ACoS ${acos}% 超目标线，立即暂停
- **C. 评估下架**：连续 7 天毛利<0 考虑下架

### 步骤 3：评估改款或换供应商
- 看退货率：如 >5%，可能是产品本身问题
- 联系供应链：能否降本 10%？
""",

    "R04": """## R04 Buybox 丢失处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：确认 Buybox 状态
- 在 Amazon 前台刷新 ASIN 页面
- 检查 Buybox 持有人：{buybox_owner}
- 判断是被跟卖还是其他卖家抢走

### 步骤 2：夺回 Buybox（4 小时窗口）
- **A. 调价**：用 Repricer 工具快速降价 1-2%
- **B. 库存确认**：确保 FBA 库存充足（>7 天）
- **C. 检查账户健康**：是否有政策违规警告

### 步骤 3：处理跟卖（如有）
- 进入 Brand Registry → Report a Violation
- 提交品牌侵权投诉
- 同时用 Test Buy 收集证据

### 步骤 4：监控恢复情况
- 设置每小时检查 Buybox 状态
- 24 小时未恢复 → 升级到 Brand Registry 团队
""",

    "R06": """## R06 退款率异常处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：分析退款原因
- 进入 Seller Central → Reports → Refunds
- 按 SKU 看退款原因分布
- 重点关注：产品质量不符 / 发错货 / 描述误导

### 步骤 2：紧急动作
- **A. 暂停广告**：退款率过高时投放是亏损
- **B. 检查 Listing 描述**：是否夸大或误导
- **C. 联系供应链**：批量退货是否同批次问题

### 步骤 3：联系买家挽留
- 在 Customer Feedback 主动联系高退款买家
- 提供部分退款或重发，争取改评

### 步骤 4：长期改进
- 如同款持续高退款：评估下架或改款
- 更新 Listing 描述，减少预期差距
""",

    "R07": """## R07 退货率异常处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：分析退货原因
- 与 R06 类似，专注"买家退货理由"
- 区分：产品质量 / 与描述不符 / 单纯不想要

### 步骤 2：评估改款
- 退货率 > 5% 持续 2 周：考虑改设计
- 联系供应链看是否做工问题

### 步骤 3：优化 Listing
- 增加多角度实拍图
- 明确尺寸/规格描述
- 减少买家预期差距

### 步骤 4：监控
- 每周跟踪退货率趋势
- 30 天未改善 → 升级到产品研发团队
""",

    "R08": """## R08 流量下滑处置

**紧急程度**：🔴 P0 · 截止 {due_hours} 小时内

### 步骤 1：诊断流量下滑原因
- 检查关键词排名变化（Helium 10 / Jungle Scout）
- 检查竞品新动作（价格 / 评论 / 新品）
- 检查 Listing 状态（Buybox / 主图是否被改）

### 步骤 2：紧急加流量
- **A. 广告加预算**：如 TACoS 未超 25%，可加 20-30%
- **B. 新增关键词**：搜索词报告找新词
- **C. Coupon / Deal**：短期刺激转化

### 步骤 3：监控
- 24h 后看 Sessions 是否回升
- 未回升 → 检查是否被算法降权（违规警告 / 评价下降）
""",
}


def build_action_playbook(alert: Dict) -> str:
    """根据 alert.rule_id 生成完整剧本 markdown"""
    template = ACTION_PLAYBOOKS.get(alert["rule_id"], "请参考 KovaScape SOP 文档处置。")
    # 填入实际数据
    evidence = alert.get("evidence", {})
    return template.format(
        due_hours=alert.get("due_hours", 8),
        profit=evidence.get("gross_profit", 0),
        sales=evidence.get("sales", 0),
        ad_spend=evidence.get("ad_spend", 0),
        acos=evidence.get("acos", 0),
        buybox_owner=evidence.get("buybox_owner", "未知"),
    )


def build_evidence_markdown(alert: Dict) -> str:
    """格式化触发证据为 markdown"""
    import json as _json
    return f"```json\n{_json.dumps(alert.get('evidence', {}), ensure_ascii=False, indent=2)}\n```"


# ============================================
# 字段映射构造器
# ============================================

def build_record(alert: Dict, config: Dict, report_url: str) -> Dict[str, Any]:
    """alert → aitable record (含 cells key)"""
    field_ids = config["aitable"]["field_ids"]
    report_date = alert.get("_report_date", "2026-07-26")
    fired_at = alert.get("triggered_at", "2026-07-26T20:52:47+08:00")

    # 截止时间 = 触发时间 + due_hours
    try:
        ft = datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        due_dt = ft + timedelta(hours=alert.get("due_hours", 8))
        due_str = due_dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    except Exception:
        due_str = "2026-07-26T18:00:00+08:00"

    fired_str = fired_at if "T" in fired_at else fired_at + "T00:00:00+08:00"

    cells = {
        field_ids["date"]:     report_date,
        field_ids["rule"]:     alert["rule_id"],
        field_ids["level"]:    alert["level"],   # singleSelect P0/P1/P2
        field_ids["status"]:   "待处理",          # singleSelect 初始值
        field_ids["fired_at"]: fired_str,
        field_ids["due"]:      due_str,
        field_ids["action"]:   {"markdown": build_action_playbook(alert)},
        field_ids["evidence"]: {"markdown": build_evidence_markdown(alert)},
    }

    # MSKU / ASIN（可空）
    msku_or_asin = alert.get("msku") or alert.get("asin") or ""
    if alert.get("msku"):
        cells[field_ids["msku"]] = alert["msku"]
    if alert.get("asin"):
        cells[field_ids["asin"]] = alert["asin"]
    if alert.get("country"):
        cells[field_ids["site"]] = alert["country"]

    # 日报链接：使用锚点指向具体 alert
    if msku_or_asin:
        anchor = f"#alert-{alert['rule_id']}-{msku_or_asin}"
        report_link = report_url + anchor
    else:
        report_link = report_url
    cells[field_ids["report"]] = {"text": "查看日报", "link": report_link}

    # 归属人：user 字段格式 [{"userId": "xxx"}]
    owner_uid = alert.get("owner_user_id", "")
    if owner_uid:
        cells[field_ids["owner"]] = [{"userId": owner_uid}]

    # ⚠️ aitable API 要求 [{"cells": {...}}]
    return {"cells": cells}


# ============================================
# dedup 检查
# ============================================

def check_existing(alert: Dict, config: Dict, invoker: DwsInvoker) -> bool:
    """检查同 (日期+规则+MSKU/ASIN) 是否已存在记录

    ⚠️ 日期字段 (EZwJUfQ) 是 datetime 类型，不支持 eq 运算符。
    因此 filter 只查 (rule + msku/asin)，日期过滤在 Python 端做。
    """
    field_ids = config["aitable"]["field_ids"]
    base_id = config["aitable"]["base_id"]
    table_id = config["aitable"]["table_id"]
    report_date = alert.get("_report_date", "")

    # 构造 filter：只查 rule + msku/asin（日期字段不支持 eq）
    operands = [
        {"operator": "eq", "operands": [field_ids["rule"], alert["rule_id"]]},
    ]
    if alert.get("msku"):
        operands.append({"operator": "eq", "operands": [field_ids["msku"], alert["msku"]]})
    elif alert.get("asin"):
        operands.append({"operator": "eq", "operands": [field_ids["asin"], alert["asin"]]})

    filter_obj = {"operator": "and", "operands": operands}

    result = invoker.run([
        "aitable", "record", "query",
        "--base-id", base_id,
        "--table-id", table_id,
        "--filter", json.dumps(filter_obj, ensure_ascii=False),
        "--limit", "20",
        "--format", "json",
    ])

    if not result.get("success"):
        return False

    # ⚠️ invoker.run() 返回 data = 完整 API 响应
    #   result = {"success": True, "data": {"data": {"records": [...]}, ...}}
    #   所以 records 在 result["data"]["data"]["records"]
    api_data = result.get("data", {})
    inner = api_data.get("data", {})
    records = inner.get("records") or []
    log = logging.getLogger("kovascape")
    log.debug(f"[DEDUP] filter 命中 {len(records)} 条 (rule={alert['rule_id']}, msku={alert.get('msku','N/A')})")

    # 在 Python 端过滤日期匹配的记录
    # 日期字段 EZwJUfQ 存的是 "2026-07-26T00:00:00+08:00" 格式
    for rec in records:
        cells = rec.get("cells", {})
        date_val = cells.get(field_ids["date"], "")
        # 检查日期是否以 report_date 开头（如 "2026-07-26T..." 匹配 "2026-07-26"）
        if isinstance(date_val, str) and date_val.startswith(report_date):
            log.info(f"[DEDUP] 找到已有记录 {rec.get('recordId','')} date={date_val}")
            return True  # 找到同日期+规则+SKU 的已有记录

    return False


# ============================================
# 主入口
# ============================================

class TodoDispatcher:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.invoker = DwsInvoker(config, logger)

    def dispatch(self, alerts: List[Dict], report_url: str) -> Dict[str, int]:
        """把 alerts 写入表格 + 创建紧急 dws 待办"""
        results = {"table_inserted": 0, "table_skipped": 0, "todo_created": 0, "errors": 0}

        for alert in alerts:
            # 1. dedup
            try:
                if self.config["aitable"].get("dedup", True):
                    if check_existing(alert, self.config, self.invoker):
                        self.logger.info(f"[DEDUP] {alert['rule_id']} {alert.get('msku', alert.get('asin', ''))} 已存在，跳过")
                        results["table_skipped"] += 1
                        continue
            except Exception as e:
                self.logger.warning(f"[DEDUP] 检查失败（{e}），继续创建")

            # 2. 写入表格
            record = build_record(alert, self.config, report_url)
            res = self.invoker.run(
                ["aitable", "record", "create",
                 "--base-id", self.config["aitable"]["base_id"],
                 "--table-id", self.config["aitable"]["table_id"],
                 "--records", "[]",  # 占位，invoker 会替换
                 "--yes",
                 "--format", "json"],
                json_args={"records": [record]},
            )
            if res.get("success"):
                results["table_inserted"] += 1
                self.logger.info(f"[TABLE] {alert['rule_id']} {alert.get('msku', alert.get('asin', ''))} 写入成功")
            else:
                results["errors"] += 1
                self.logger.error(f"[TABLE] 写入失败: {res.get('error')}")

            # 3. P0 + due<=4h → dws todo
            if alert.get("level") == "P0" and alert.get("due_hours", 8) <= 4:
                if alert.get("owner_user_id"):
                    todo_res = self.invoker.run([
                        "todo", "task", "create",
                        "--title", alert["title"],
                        "--executors", alert["owner_user_id"],
                        "--priority", str(alert.get("priority", 40)),
                        "--yes",
                        "--format", "json",
                    ])
                    if todo_res.get("success"):
                        results["todo_created"] += 1
                        self.logger.info(f"[TODO] {alert['rule_id']} → DING 待办创建")
                    else:
                        self.logger.error(f"[TODO] 创建失败: {todo_res.get('error')}")

        return results


# ============================================
# CLI 入口
# ============================================

def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    cfg_path = Path(__file__).resolve().parent.parent / path
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logger(name: str = "kovascape") -> logging.Logger:
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log


def main(alerts_path: str = None, report_url: str = "") -> int:
    log = setup_logger()
    config = load_config()

    if alerts_path is None:
        alerts_path = str(
            Path(__file__).resolve().parent.parent / "output" / "alerts-2026-07-26.json"
        )

    with open(alerts_path, "r", encoding="utf-8") as f:
        alerts = json.load(f)

    # 给每条 alert 注入 report_date（来自 snapshot）
    snapshot_path = alerts_path.replace("alerts-", "snapshot-")
    if Path(snapshot_path).exists():
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snap = json.load(f)
        report_date = snap["report_date"]
    else:
        report_date = "2026-07-26"

    for a in alerts:
        a["_report_date"] = report_date

    dispatcher = TodoDispatcher(config, log)
    results = dispatcher.dispatch(alerts, report_url)

    log.info(f"\n📊 分发结果：")
    log.info(f"  表格写入：{results['table_inserted']} 条")
    log.info(f"  表格去重跳过：{results['table_skipped']} 条")
    log.info(f"  dws 待办（DING 强推）：{results['todo_created']} 条")
    log.info(f"  错误：{results['errors']} 条")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    alerts_path = args[0] if len(args) > 0 else None
    report_url = args[1] if len(args) > 1 else "https://kovascape.example.com/daily/2026-07-26.html"
    sys.exit(main(alerts_path, report_url))