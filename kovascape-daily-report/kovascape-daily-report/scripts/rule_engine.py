"""
KovaScape Daily Report - 规则引擎
=====================================

职责：
  1. 读取 data_layer 输出的 DailySnapshot
  2. 跑 8 条 P0 规则（与《KovaScape-预警模板配置手册-v1》完全对齐）
  3. 每条触发生成 Alert（含归属人、dws todo 字段、行动建议）
  4. 输出 JSON，供 html_renderer + todo_dispatcher 使用

阈值基线（来自 config.yaml）：
  - ACoS 盈亏线 50% / TACoS 25% / 毛利率红线 18% / 缺货 7 天 / 新品 30 天

作者：Zero/王祎 + AI
版本：v0.1 (W2)
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# 复用 data_layer 的 dataclass
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_layer import (
    DailySnapshot, InventoryRow, ProfitRow, ListingHealth,
    ListingOwner, load_config, setup_logger,
)


# ============================================
# Alert 数据模型
# ============================================

@dataclass
class Alert:
    """单条规则触发的报警"""
    rule_id: str                # "R01" ... "R08"
    level: str                  # "P0" / "P1" / "P2"
    msku: Optional[str] = None
    asin: Optional[str] = None
    parent_asin: Optional[str] = None
    sid: Optional[int] = None
    country: Optional[str] = None

    # 触发证据
    evidence: Dict[str, Any] = field(default_factory=dict)

    # 输出字段
    title: str = ""             # 完整 dws todo title（含详情）
    action: str = ""            # 建议动作
    priority: int = 40          # dws todo priority: 10/20/30/40
    due_hours: int = 8          # 距 due 时间

    # 归属人（关键！）
    owner_key: str = "wang_yi"  # wang_yi | hua_yibo
    owner_user_id: str = ""     # dws todo executors

    triggered_at: str = ""      # ISO 8601


# ============================================
# 归属人查询
# ============================================

class OwnerResolver:
    """MSKU/ASIN → 归属人

    查询优先级：
      1. listing_owners.json 缓存文件（从领星 MCP 实时拉取）
      2. config.lingxing.listing_owner_overrides（手工覆盖）
      3. 默认 config.lingxing.listing_owner_default
    """

    def __init__(self, config: Dict[str, Any]):
        self.overrides = config.get("lingxing", {}).get("listing_owner_overrides", {})
        self.default = config.get("lingxing", {}).get("listing_owner_default", "wang_yi")
        self.fallback = config.get("dingtalk", {}).get("todo_distribution", {}).get("fallback", "wang_yi")

        # owner_key → userId
        self.user_ids = config.get("dingtalk", {}).get("executors", {})
        if self.fallback not in self.user_ids:
            self.user_ids[self.fallback] = ""

        # 加载 listing_owners.json 缓存
        self._cache: Dict[str, Dict] = {}  # {sid: {msku: {...}, asin: {...}}}
        cache_path = Path(__file__).resolve().parent.parent / "output" / "listing_owners.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                log = logging.getLogger("kovascape")
                cached_sids = list(self._cache.keys())
                total_msku = sum(len(v.get("msku", {})) for v in self._cache.values())
                log.info(f"[OwnerResolver] 已加载 {len(cached_sids)} 站点的 listing_owners 缓存 ({total_msku} MSKUs)")
            except Exception as e:
                log = logging.getLogger("kovascape")
                log.warning(f"[OwnerResolver] 加载 listing_owners.json 失败: {e}")

    def resolve(self, sid: int, msku: Optional[str] = None, asin: Optional[str] = None) -> tuple[str, str]:
        """返回 (owner_key, owner_user_id)"""
        # 0. 从缓存查找
        sid_str = str(sid)
        cache_entry = None
        if sid_str in self._cache:
            # 按 MSKU → ASIN → Parent ASIN 优先级查找
            if msku:
                cache_entry = self._cache[sid_str].get("msku", {}).get(msku)
            if not cache_entry and asin:
                cache_entry = self._cache[sid_str].get("asin", {}).get(asin)
            if not cache_entry and asin:
                cache_entry = self._cache[sid_str].get("parent_asin", {}).get(asin)

        if cache_entry:
            owner_key = cache_entry.get("owner", self.default)
        else:
            # 1. overrides（旧式手工覆盖）
            sid_map = self.overrides.get(sid_str, {}) or self.overrides.get(sid, {})
            if msku and msku in sid_map:
                owner_key = sid_map[msku]
            elif asin and asin in sid_map:
                owner_key = sid_map[asin]
            else:
                owner_key = self.default

        # 2. userId 解析
        user_id = self.user_ids.get(owner_key, "")
        if not user_id:
            owner_key = self.fallback
            user_id = self.user_ids.get(self.fallback, "")

        return owner_key, user_id


# ============================================
# 8 条 P0 规则（独立函数，方便单测）
# ============================================

def rule_r01_stockout(inv: InventoryRow, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R01 缺货：可售天数 < 7 天

    排除：7 日销量 = 0 的死库存（不会被算缺货）
    """
    if inv.sales_velocity_7d is None or inv.sales_velocity_7d <= 0:
        return None
    if inv.days_of_supply is None or inv.days_of_supply >= thresholds["stockout_days"]:
        return None

    owner_key, owner_uid = owner
    days = inv.days_of_supply
    velocity = inv.sales_velocity_7d

    return Alert(
        rule_id="R01",
        level="P0",
        msku=inv.msku,
        asin=inv.asin,
        sid=inv.sid,
        country=inv.country,
        evidence={
            "available": inv.available,
            "sales_velocity_7d": velocity,
            "days_of_supply": days,
        },
        title=f"[日报 {report_date}] R01 缺货 {inv.msku}({inv.country}) 可售{inv.available}件/{velocity:.1f}件·天={days:.1f}天",
        action="立即提价 5-10% / 暂停广告 / 紧急补货评估",
        priority=40,
        due_hours=8,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


def rule_r02_negative_profit(p: ProfitRow, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R02 毛利润 < 0"""
    if p.gross_profit >= 0:
        return None

    owner_key, owner_uid = owner
    return Alert(
        rule_id="R02",
        level="P0",
        msku=p.msku,
        sid=p.sid,
        country=p.country,
        evidence={"gross_profit": p.gross_profit, "sales": p.sales, "ad_spend": p.ad_spend},
        title=f"[日报 {report_date}] R02 毛利润<0 {p.msku}({p.country}) 7日毛利${p.gross_profit:.0f}",
        action="立即止损：检查定价 / 广告占比 / 退货成本",
        priority=40,
        due_hours=8,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


def rule_r03_rank_drop(lh: ListingHealth, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R03 大类排名 3 日下滑 > 20%（数据字段未在 mock 中，跳过）"""
    # ⚠️ category_rank_trend 字段需要在 listing health 里有"3 日前"快照对比
    #   当前 MockDataSource 没生成 trend 字段，规则暂不触发
    # TODO: 接真实数据后启用
    return None


def rule_r04_buybox(lh: ListingHealth, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R04 Buybox 丢失

    触发条件（任一）：
      - buybox_owner 为 None（无主）
      - buybox_owner 不是我们自己（被抢）
    """
    our_brand_aliases = {"kovascape", "our_brand", "us", "self", "零"}
    is_ours = (
        lh.buybox_owner is not None and
        lh.buybox_owner.lower() in our_brand_aliases
    )
    if is_ours:
        return None

    # 触发：buybox_owner 为 None（无主） 或被抢
    owner_key, owner_uid = owner
    return Alert(
        rule_id="R04",
        level="P0",
        asin=lh.asin,
        msku=lh.msku,
        sid=lh.sid,
        country=lh.country,
        evidence={"buybox_owner": lh.buybox_owner or "(无人持有)", "is_hijacked": lh.is_hijacked},
        title=f"[日报 {report_date}] R04 Buybox丢失 {lh.asin}({lh.country}) 持有人:{lh.buybox_owner or '无人'}",
        action="查价格 / 查跟卖 / 品牌投诉 / 夺回 Buybox",
        priority=40,
        due_hours=4,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


def rule_r05_sales_drop(p: ProfitRow, prev_units: Optional[int], owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R05 销量骤降：环比下降 > 40%（7 日）"""
    # ⚠️ 需要昨日/上周数据对比，MockDataSource 没生成
    # TODO: 接真实数据后启用
    return None


def rule_r06_refund(p: ProfitRow, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R06 退款率 > 5%"""
    if p.refund_rate < 5.0:
        return None

    owner_key, owner_uid = owner
    return Alert(
        rule_id="R06",
        level="P0",
        msku=p.msku,
        sid=p.sid,
        country=p.country,
        evidence={"refund_rate": p.refund_rate},
        title=f"[日报 {report_date}] R06 退款率异常 {p.msku}({p.country}) {p.refund_rate:.1f}%",
        action="查退货原因 / 检查 Listing 描述 / 准备客服模板",
        priority=40,
        due_hours=8,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


def rule_r07_return(p: ProfitRow, owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R07 退货率 > 5%"""
    if p.return_rate < 5.0:
        return None

    owner_key, owner_uid = owner
    return Alert(
        rule_id="R07",
        level="P0",
        msku=p.msku,
        sid=p.sid,
        country=p.country,
        evidence={"return_rate": p.return_rate},
        title=f"[日报 {report_date}] R07 退货率异常 {p.msku}({p.country}) {p.return_rate:.1f}%",
        action="查退货原因 + 评估改款",
        priority=40,
        due_hours=8,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


def rule_r08_traffic_drop(lh: ListingHealth, prev_sessions: Optional[int], owner: tuple[str, str], thresholds: Dict, report_date: str) -> Optional[Alert]:
    """R08 Sessions 下滑 > 30%（需对比昨日）"""
    if prev_sessions is None or prev_sessions == 0:
        return None
    drop_pct = (prev_sessions - lh.sessions) / prev_sessions * 100
    if drop_pct < 30:
        return None

    owner_key, owner_uid = owner
    return Alert(
        rule_id="R08",
        level="P0",
        asin=lh.asin,
        msku=lh.msku,
        sid=lh.sid,
        country=lh.country,
        evidence={"sessions_today": lh.sessions, "sessions_prev": prev_sessions, "drop_pct": drop_pct},
        title=f"[日报 {report_date}] R08 流量下滑 {lh.asin}({lh.country}) Sessions↓{drop_pct:.0f}%",
        action="查关键词排名 / 检查广告结构 / 加预算抢流量",
        priority=40,
        due_hours=8,
        owner_key=owner_key,
        owner_user_id=owner_uid,
        triggered_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    )


# ============================================
# 规则引擎主入口
# ============================================

class RuleEngine:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.thresholds = config.get("thresholds", {})
        self.owner_resolver = OwnerResolver(config)

    def run(self, snapshot: DailySnapshot) -> List[Alert]:
        """跑全部 P0 规则，返回 alerts 列表"""
        alerts: List[Alert] = []
        report_date = snapshot.report_date

        # ---- R01 缺货 ----
        for inv in snapshot.inventory:
            owner = self.owner_resolver.resolve(inv.sid, inv.msku, inv.asin)
            alert = rule_r01_stockout(inv, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R02 毛利润 < 0 ----
        for p in snapshot.profit:
            owner = self.owner_resolver.resolve(p.sid, p.msku)
            alert = rule_r02_negative_profit(p, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R03 大类排名下滑 ----（待真实数据）
        for lh in snapshot.listings:
            owner = self.owner_resolver.resolve(lh.sid, lh.msku, lh.asin)
            alert = rule_r03_rank_drop(lh, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R04 Buybox ----
        for lh in snapshot.listings:
            owner = self.owner_resolver.resolve(lh.sid, lh.msku, lh.asin)
            alert = rule_r04_buybox(lh, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R05 销量骤降 ----（待对比数据）
        for p in snapshot.profit:
            owner = self.owner_resolver.resolve(p.sid, p.msku)
            alert = rule_r05_sales_drop(p, None, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R06 退款率 ----
        for p in snapshot.profit:
            owner = self.owner_resolver.resolve(p.sid, p.msku)
            alert = rule_r06_refund(p, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R07 退货率 ----
        for p in snapshot.profit:
            owner = self.owner_resolver.resolve(p.sid, p.msku)
            alert = rule_r07_return(p, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        # ---- R08 流量下滑 ----（待对比数据）
        for lh in snapshot.listings:
            owner = self.owner_resolver.resolve(lh.sid, lh.msku, lh.asin)
            alert = rule_r08_traffic_drop(lh, None, owner, self.thresholds, report_date)
            if alert:
                alerts.append(alert)

        self.logger.info(
            f"[RuleEngine] {len(alerts)} alerts triggered | "
            f"P0={sum(1 for a in alerts if a.level=='P0')} "
            f"P1={sum(1 for a in alerts if a.level=='P1')} "
            f"P2={sum(1 for a in alerts if a.level=='P2')}"
        )
        return alerts


# ============================================
# CLI / 测试入口
# ============================================

def main(snapshot_path: Optional[str] = None, output_path: Optional[str] = None) -> int:
    log = setup_logger()
    config = load_config()

    # 默认读 mock snapshot
    if snapshot_path is None:
        snapshot_path = str(
            Path(__file__).resolve().parent.parent / "output" / "snapshot-2026-07-26.json"
        )

    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_dict = json.load(f)

    # 反序列化为 DailySnapshot
    snapshot = DailySnapshot(
        report_date=snapshot_dict["report_date"],
        generated_at=snapshot_dict["generated_at"],
        sids=snapshot_dict["sids"],
        inventory=[InventoryRow(**r) for r in snapshot_dict["inventory"]],
        profit=[ProfitRow(**r) for r in snapshot_dict["profit"]],
        listings=[ListingHealth(**r) for r in snapshot_dict["listings"]],
        owners=[ListingOwner(**r) for r in snapshot_dict["owners"]],
        metadata=snapshot_dict.get("metadata", {}),
    )

    engine = RuleEngine(config, log)
    alerts = engine.run(snapshot)

    # 输出
    if output_path is None:
        output_path = str(
            Path(__file__).resolve().parent.parent / "output" / "alerts-2026-07-26.json"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(a) for a in alerts], f, ensure_ascii=False, indent=2)

    log.info(f"alerts saved: {output_path}")

    # 控制台打印前 3 条
    for a in alerts[:3]:
        log.info(f"  [{a.rule_id}|{a.level}|{a.owner_key}] {a.title}")
    return 0


if __name__ == "__main__":
    snap = sys.argv[1] if len(sys.argv) > 1 else None
    out = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(main(snap, out))