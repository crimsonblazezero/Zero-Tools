"""
KovaScape Daily Report - HTML 渲染器
=====================================

职责：
  1. 读取 snapshot JSON + alerts JSON
  2. 用 Jinja2 模板渲染为完整 HTML 日报
  3. 输出到 output/{date}.html，可部署到 CloudStudio

模板基于 W1 prototype（`outputs/daily-report-mock-2026-07-26.html`）
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jinja2 import Template

# ============================================
# 模板（内嵌，便于单文件分发）
# ============================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KovaScape 日报 · {{ report_date }}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f6f8; color: #1f2329; line-height: 1.5; padding: 16px; max-width: 1100px; margin: 0 auto; }
header { background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%); color: #fff; padding: 20px 24px; border-radius: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
header h1 { font-size: 22px; font-weight: 600; }
header .meta { font-size: 13px; opacity: 0.85; }
section { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
section h2 { font-size: 17px; font-weight: 600; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
.kpi { background: #f9fafb; border-radius: 8px; padding: 14px 16px; }
.kpi .label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.kpi .value { font-size: 22px; font-weight: 700; color: #1f2329; }
.kpi .delta { font-size: 12px; margin-top: 2px; }
.kpi .delta.up { color: #10b981; }
.kpi .delta.down { color: #ef4444; }
.kpi .delta.warn { color: #f59e0b; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
th { background: #f9fafb; font-weight: 600; color: #4b5563; }
.alert-list { display: grid; gap: 10px; }
.alert { border-left: 4px solid #e5e7eb; background: #f9fafb; padding: 12px 16px; border-radius: 6px; }
.alert.p0 { border-left-color: #ef4444; background: #fef2f2; }
.alert.p1 { border-left-color: #f59e0b; background: #fffbeb; }
.alert.p2 { border-left-color: #3b82f6; background: #eff6ff; }
.alert .rule { font-weight: 600; color: #1f2329; font-size: 14px; margin-bottom: 4px; }
.alert .title { color: #4b5563; font-size: 13px; margin-bottom: 4px; }
.alert .action { color: #6b7280; font-size: 12px; }
.alert .owner { display: inline-block; background: #e5e7eb; color: #374151; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-left: 8px; }
.empty { color: #9ca3af; font-size: 13px; padding: 24px; text-align: center; }
footer { text-align: center; font-size: 12px; color: #9ca3af; padding: 20px 0; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge.p0 { background: #fee2e2; color: #b91c1c; }
.badge.p1 { background: #fef3c7; color: #92400e; }
.badge.p2 { background: #dbeafe; color: #1e40af; }
</style>
</head>
<body>
<header>
  <div>
    <h1>📊 KovaScape 运营日报</h1>
    <div class="meta">报告日期：{{ report_date }}（美西） · 生成于 {{ generated_at }}（北京）</div>
  </div>
  <div class="meta">店铺范围：15 个 KS- 站点（US/UK/DE/CA/JP/MX/BR + BE/ES/FR/IE/IT/NL/PL/SE）</div>
</header>

<!-- ============ ① 业绩 ============ -->
<section>
  <h2>① 业绩摘要</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="label">总销售额</div><div class="value">${{ '%.0f' | format(kpi.total_sales) }}</div><div class="delta {{ 'up' if kpi.sales_delta > 0 else 'down' }}">{{ '%+.1f' | format(kpi.sales_delta) }}% vs 昨日</div></div>
    <div class="kpi"><div class="label">总订单</div><div class="value">{{ kpi.total_orders }}</div></div>
    <div class="kpi"><div class="label">毛利润</div><div class="value">${{ '%.0f' | format(kpi.total_profit) }}</div></div>
    <div class="kpi"><div class="label">毛利率</div><div class="value">{{ '%.1f' | format(kpi.gross_margin) }}%</div></div>
    <div class="kpi"><div class="label">TACoS</div><div class="value">{{ '%.1f' | format(kpi.tacos) }}%</div><div class="delta {{ 'warn' if kpi.tacos > 25 else '' }}">{{ '⚠ 超过目标线 25%' if kpi.tacos > 25 else '✅ 在目标内' }}</div></div>
    <div class="kpi"><div class="label">ACoS（加权）</div><div class="value">{{ '%.1f' | format(kpi.acos) }}%</div></div>
  </div>

  <h2 style="margin-top: 20px;">分站点表现</h2>
  <table>
    <thead><tr><th>站点</th><th>销售额</th><th>订单</th><th>毛利润</th><th>毛利率</th><th>ACoS</th></tr></thead>
    <tbody>
    {% for r in by_site %}
      <tr>
        <td>{{ r.country }} <small>({{ r.sid }})</small></td>
        <td>${{ '%.0f' | format(r.sales) }}</td>
        <td>{{ r.orders }}</td>
        <td>${{ '%.0f' | format(r.profit) }}</td>
        <td>{{ '%.1f' | format(r.margin) }}%</td>
        <td>{{ '%.1f' | format(r.acos) }}%</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</section>

<!-- ============ ② 异常 ============ -->
<section>
  <h2>② 异常清单 · {{ alerts | length }} 条</h2>
  {% if alerts %}
  <div class="alert-list">
    {% for a in alerts %}
    <div class="alert {{ a.level | lower }}" id="alert-{{ a.rule_id }}-{{ a.msku or a.asin or loop.index }}">
      <div class="rule">
        <span class="badge {{ a.level | lower }}">{{ a.level }}</span>
        {{ a.rule_id }} · {{ a.msku or a.asin or '?' }} ({{ a.country }})
        <span class="owner">归属：{{ a.owner_key }}{% if a.owner_user_id %} ({{ a.owner_user_id[:6] }}…){% endif %}</span>
      </div>
      <div class="title">{{ a.title }}</div>
      <div class="action">⚡ {{ a.action }} · 截止：{{ a.due_hours }}h 内</div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="empty">🎉 今天没有触发任何规则</div>
  {% endif %}
</section>

<!-- ============ ③ 展望 ============ -->
<section>
  <h2>③ 今日展望</h2>
  <ul style="padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.8;">
    <li>📦 补货：R01 触发 3 条 MSKU 需在 8h 内补货或提价</li>
    <li>💰 利润：R02 触发 1 条 MSKU 毛利润&lt;0，需立即止损</li>
    <li>🛒 Buybox：R04 触发 1 条 ASIN 丢失 Buybox，需立即夺回</li>
    <li>📈 退款：R06 触发 1 条 MSKU 退款率 6.5%，检查 Listing 描述</li>
    <li>📅 本周关键节点：周末前完成所有 P0 处置（按 dws 待办 SLA）</li>
  </ul>
</section>

<!-- ============ ④ 行动清单 ============ -->
<section>
  <h2>④ 行动清单（按归属人）</h2>
  {% if alerts %}
  {% set owners = alerts | map(attribute='owner_key') | unique | list %}
  {% for owner in owners %}
    {% set owner_alerts = alerts | selectattr('owner_key', 'equalto', owner) | list %}
    <h3 style="font-size: 14px; margin: 12px 0 8px; color: #4b5563;">👤 {{ owner }}（{{ owner_alerts | length }} 条）</h3>
    <div class="alert-list">
      {% for a in owner_alerts %}
      <div class="alert {{ a.level | lower }}">
        <div class="title"><span class="badge {{ a.level | lower }}">{{ a.level }}</span> <strong>{{ a.rule_id }}</strong> · {{ a.title }}</div>
        <div class="action">👉 {{ a.action }}</div>
      </div>
      {% endfor %}
    </div>
  {% endfor %}
  {% else %}
  <div class="empty">今天没有 actionable 项</div>
  {% endif %}
</section>

<footer>
  KovaScape Daily Report · 自动生成 · 数据源：领星 MCP（mock 数据） · 推送通道：钉钉
</footer>
</body>
</html>
"""


# ============================================
# 计算层
# ============================================

def compute_kpis(snapshot: Dict, alerts: List[Dict]) -> Dict[str, Any]:
    """从 snapshot 计算 KPI"""
    profits = snapshot.get("profit", [])
    total_sales = sum(p.get("sales", 0) for p in profits)
    total_orders = sum(p.get("orders", 0) for p in profits)
    total_profit = sum(p.get("gross_profit", 0) for p in profits)
    total_ad_spend = sum(p.get("ad_spend", 0) for p in profits)
    gross_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    acos = (total_ad_spend / total_sales * 100) if total_sales > 0 else 0
    tacos = acos  # 简化为相同（同 ad_spend/sales）

    # 模拟昨日 delta（mock 数据无历史，固定 -3%）
    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_profit": total_profit,
        "gross_margin": gross_margin,
        "acos": acos,
        "tacos": tacos,
        "sales_delta": -3.0,  # mock 占位
    }


def aggregate_by_site(snapshot: Dict) -> List[Dict[str, Any]]:
    """按站点聚合利润数据"""
    by_sid = {}
    for p in snapshot.get("profit", []):
        sid = p.get("sid")
        if sid not in by_sid:
            by_sid[sid] = {
                "sid": sid,
                "country": p.get("country", ""),
                "sales": 0, "orders": 0, "profit": 0, "ad_spend": 0,
            }
        by_sid[sid]["sales"] += p.get("sales", 0)
        by_sid[sid]["orders"] += p.get("orders", 0)
        by_sid[sid]["profit"] += p.get("gross_profit", 0)
        by_sid[sid]["ad_spend"] += p.get("ad_spend", 0)

    rows = []
    for sid, r in by_sid.items():
        sales = r["sales"]
        rows.append({
            "sid": sid,
            "country": r["country"],
            "sales": sales,
            "orders": r["orders"],
            "profit": r["profit"],
            "margin": (r["profit"] / sales * 100) if sales > 0 else 0,
            "acos": (r["ad_spend"] / sales * 100) if sales > 0 else 0,
        })
    rows.sort(key=lambda r: r["sales"], reverse=True)
    return rows


# ============================================
# 渲染入口
# ============================================

def render(snapshot_path: str, alerts_path: str, output_path: str) -> str:
    """读 JSON → 渲染 HTML → 写文件"""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    with open(alerts_path, "r", encoding="utf-8") as f:
        alerts = json.load(f)

    kpi = compute_kpis(snapshot, alerts)
    by_site = aggregate_by_site(snapshot)

    template = Template(HTML_TEMPLATE)
    html = template.render(
        report_date=snapshot["report_date"],
        generated_at=snapshot["generated_at"],
        kpi=kpi,
        by_site=by_site,
        alerts=alerts,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def main(snapshot: str = None, alerts: str = None, output: str = None) -> int:
    base = Path(__file__).resolve().parent.parent / "output"
    snapshot = snapshot or str(base / "snapshot-2026-07-26.json")
    alerts = alerts or str(base / "alerts-2026-07-26.json")
    output = output or str(base / "2026-07-26.html")

    log = logging.getLogger("kovascape")
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = logging.StreamHandler()
        log.addHandler(h)

    out = render(snapshot, alerts, output)
    log.info(f"HTML rendered: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))