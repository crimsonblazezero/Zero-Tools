"""
KovaScape Daily Report - 钉钉 Action Card 推送器
=================================================

职责：
  1. 读 alerts.json 统计异常概览
  2. 从 snapshot.json 提取业绩 KPI
  3. 构造 Action Card 推送到钉钉群
  4. 关键词模式需在 title + text 中同时含关键词

基于 dingtalk-webhook skill 的封装
"""

from __future__ import annotations

import json
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
import requests


# ============================================
# DingTalk Webhook 客户端
# ============================================

class DingTalkWebhook:
    """钉钉群机器人 webhook 客户端（支持加签 + 关键词模式）"""

    def __init__(self, webhook_url: str, secret: str = "", keyword: str = ""):
        self.base_url = webhook_url
        self.secret = secret
        self.keyword = keyword

    def _signed_url(self) -> str:
        if not self.secret:
            return self.base_url
        ts = str(round(time.time() * 1000))
        s = f"{ts}\n{self.secret}"
        h = hmac.new(self.secret.encode(), s.encode(), hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(h))
        return f"{self.base_url}&timestamp={ts}&sign={sign}"

    def _prepend_keyword(self, payload: dict) -> dict:
        """关键词模式：在 title 和 text 中都注入关键词"""
        if not self.keyword:
            return payload
        mt = payload.get("msgtype")
        if mt == "text":
            payload["text"]["content"] = f"{self.keyword} {payload['text']['content']}"
        elif mt == "markdown":
            payload["markdown"]["title"] = f"{self.keyword} · {payload['markdown']['title']}"
            payload["markdown"]["text"] = f"**{self.keyword}**\n{payload['markdown']['text']}"
        elif mt == "actionCard":
            # ⚠️ title 和 text 都必须含关键词
            if self.keyword not in payload["actionCard"].get("title", ""):
                payload["actionCard"]["title"] = f"{self.keyword} · {payload['actionCard']['title']}"
            payload["actionCard"]["text"] = f"**{self.keyword}**\n{payload['actionCard']['text']}"
        return payload

    def send(self, payload: dict) -> dict:
        payload = self._prepend_keyword(payload)
        url = self._signed_url()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        resp = requests.post(url, data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
        return resp.json()


# ============================================
# Action Card 构造器
# ============================================

def build_action_card(
    kpi: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    report_url: str,
    report_date: str,
) -> dict:
    """基于业绩 KPI + 异常概览构造 Action Card"""

    # 业绩摘要
    sales = kpi.get("total_sales", 0)
    orders = kpi.get("total_orders", 0)
    profit = kpi.get("total_gross_profit", 0)
    margin = kpi.get("gross_margin", 0)
    tacos = kpi.get("tacos", 0)

    # 异常统计
    p0_count = sum(1 for a in alerts if a.get("level") == "P0")
    p1_count = sum(1 for a in alerts if a.get("level") == "P1")

    # 按规则分组
    rule_counts: Dict[str, int] = {}
    for a in alerts:
        rid = a.get("rule_id", "未知")
        rule_counts[rid] = rule_counts.get(rid, 0) + 1

    rule_lines = "\n".join([f"- {rid} × {cnt}" for rid, cnt in sorted(rule_counts.items())])

    # 构造 text
    text = f"""📊 **KovaScape 日报 · {report_date}**

━━━ 业绩概览 ━━━
销售额 ${sales:,.0f}
订单 {orders:,}
毛利 ${profit:,.0f}（毛利率 {margin:.1f}%）
TACoS {tacos:.1f}%

━━━ 异常概览 ━━━
**P0 待办 {p0_count} 条**

{rule_lines}

👉 点击下方按钮查看完整日报及行动清单"""

    # 构造 Action Card
    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": f"KovaScape 日报 {report_date} | {p0_count} 条 P0 待办",
            "text": text,
            "singleTitle": "📋 查看完整日报及行动项",
            "singleURL": report_url,
            "btnOrientation": "0",
        },
    }
    return payload


# ============================================
# 主入口
# ============================================

def push_daily_report(
    alerts_path: str,
    snapshot_path: str,
    report_url: str,
    config: Dict[str, Any],
    logger: logging.Logger,
) -> bool:
    """推送日报 Action Card 到钉钉群"""

    # 加载 alerts
    with open(alerts_path, "r", encoding="utf-8") as f:
        alerts = json.load(f)
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    report_date = snapshot.get("report_date", "未知")

    # 从 snapshot 提取 KPI
    kpi = _compute_kpi(snapshot)

    # 构造 Action Card
    card = build_action_card(kpi, alerts, report_url, report_date)

    # 推送
    dk_cfg = config.get("dingtalk", {})
    webhook_url = dk_cfg.get("webhook_url", "")
    secret = dk_cfg.get("secret", "")
    keyword = dk_cfg.get("keyword", "广告")

    if not webhook_url:
        logger.error("[WEBHOOK] webhook_url 未配置，跳过推送")
        return False

    client = DingTalkWebhook(webhook_url, secret, keyword)
    result = client.send(card)

    if result.get("errcode") == 0:
        logger.info(f"[WEBHOOK] Action Card 推送成功 → 群")
        return True
    else:
        logger.error(f"[WEBHOOK] 推送失败: {result}")
        return False


def _compute_kpi(snapshot: dict) -> dict:
    """从 snapshot JSON 提取业绩 KPI"""
    profit_rows = snapshot.get("profit", [])
    total_sales = sum(r.get("sales", 0) for r in profit_rows)
    total_orders = sum(r.get("orders", 0) for r in profit_rows)
    total_ad = sum(r.get("ad_spend", 0) for r in profit_rows)
    total_profit = sum(r.get("gross_profit", 0) for r in profit_rows)

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_ad_spend": total_ad,
        "total_gross_profit": total_profit,
        "gross_margin": (total_profit / total_sales * 100) if total_sales > 0 else 0,
        "tacos": (total_ad / total_sales * 100) if total_sales > 0 else 0,
    }


def main(
    alerts_path: str = None,
    snapshot_path: str = None,
    report_url: str = "",
    config: Dict = None,
) -> int:
    """CLI 入口"""
    log = logging.getLogger("kovascape")
    if config is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import data_layer
        config = data_layer.load_config()

    base = Path(__file__).resolve().parent.parent / "output"
    alerts_path = alerts_path or str(base / "alerts-2026-07-26.json")
    snapshot_path = snapshot_path or str(base / "snapshot-2026-07-26.json")

    ok = push_daily_report(alerts_path, snapshot_path, report_url, config, log)
    return 0 if ok else 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
