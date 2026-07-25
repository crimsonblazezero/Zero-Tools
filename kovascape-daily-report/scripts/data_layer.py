"""
KovaScape Daily Report - 数据聚合层
=====================================

职责：
  1. 通过领星 MCP 拉取 15 个 KS- 站点的关键运营数据
  2. 标准化为 JSON，供规则引擎（rule_engine.py）使用
  3. 失败重试 + 限流保护

数据维度：
  - 库存：FBA 可售、按 MSKU + sid
  - 利润：销售额/订单/毛利润/毛利率，按 MSKU
  - 广告表现：花费/订单/ACoS/TACoS，按 ASIN
  - Listing 状态：Buybox / 类目排名 / 评分
  - 监控配置：跟卖/竞品监控（领星 OpenAPI）

作者：Zero/王祎 + AI
版本：v0.1 (W2)
"""

from __future__ import annotations

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ============================================
# 数据模型
# ============================================

@dataclass
class InventoryRow:
    """单 MSKU 单站点的库存快照"""
    sid: int
    country: str  # US/UK/DE/...
    msku: str
    fnsku: Optional[str] = None
    asin: Optional[str] = None
    available: int = 0          # 可售
    inbound: int = 0            # 在途
    reserved: int = 0           # 预留
    age_0_90: int = 0           # 库龄 0-90 天
    age_90_180: int = 0         # 库龄 90-180 天
    age_180_plus: int = 0       # 库龄 180+ 天
    # 计算字段（在分析层填）
    days_of_supply: Optional[float] = None
    sales_velocity_7d: Optional[float] = None  # 近 7 天日均销量


@dataclass
class ProfitRow:
    """单 MSKU 单站点的利润快照"""
    sid: int
    country: str
    msku: str
    date: str                    # YYYY-MM-DD
    orders: int = 0
    units: int = 0
    sales: float = 0.0           # 销售额（站点币种）
    ad_spend: float = 0.0        # 广告花费
    gross_profit: float = 0.0    # 毛利润
    gross_margin: float = 0.0    # 毛利率 (%)
    acos: float = 0.0            # ACoS (%)
    tacos: float = 0.0           # TACoS (%) = ad_spend / sales
    refund_rate: float = 0.0     # 退款率 (%)
    return_rate: float = 0.0     # 退货率 (%)


@dataclass
class ListingHealth:
    """单 ASIN 单站点的 Listing 健康度"""
    sid: int
    country: str
    asin: str
    parent_asin: Optional[str] = None
    msku: Optional[str] = None
    title: Optional[str] = None
    sessions: int = 0            # 流量
    buybox_owner: Optional[str] = None  # Buybox 持有人（None=丢失）
    is_hijacked: bool = False    # 是否被跟卖
    category_rank: Optional[int] = None
    rating: Optional[float] = None  # 评分
    rating_count: int = 0
    rating_trend_14d: Optional[float] = None  # 14 天评分变化


@dataclass
class ListingOwner:
    """MSKU/ASIN → 归属人映射"""
    sid: int
    msku: Optional[str] = None
    asin: Optional[str] = None
    owner_key: str = "wang_yi"   # wang_yi | hua_yibo


@dataclass
class DailySnapshot:
    """一个站点一天的完整快照（data_layer 输出）"""
    report_date: str              # YYYY-MM-DD (US Pacific)
    generated_at: str             # YYYY-MM-DDTHH:MM:SS+08:00 (北京)
    sids: List[int]               # 包含的 sid
    inventory: List[InventoryRow] = field(default_factory=list)
    profit: List[ProfitRow] = field(default_factory=list)
    listings: List[ListingHealth] = field(default_factory=list)
    owners: List[ListingOwner] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转 dict（供 json.dumps）"""
        return {
            "report_date": self.report_date,
            "generated_at": self.generated_at,
            "sids": self.sids,
            "inventory": [asdict(r) for r in self.inventory],
            "profit": [asdict(r) for r in self.profit],
            "listings": [asdict(r) for r in self.listings],
            "owners": [asdict(r) for r in self.owners],
            "metadata": self.metadata,
        }


# ============================================
# 领星 MCP 数据源（真实环境）
# ============================================

class LingxingDataSource:
    """通过 mcp__LingXing-MCP 工具调用领星 OpenAPI

    注意：本机 MCP 工具在 WorkBuddy 内可直接调用。
    离开 WorkBuddy 环境（独立 Python 脚本）需要：
      1. 申请领星 OpenAPI token（领星 → 设置 → API）
      2. 写到 .env：LINGXING_APP_ID=xxx / LINGXING_APP_SECRET=xxx
      3. 用 requests 直接调 OpenAPI
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.sids = [s["id"] for s in config["lingxing"]["sids"]]
        self.sid_country = {s["id"]: s["country"] for s in config["lingxing"]["sids"]}
        self.max_parallel = config["lingxing"].get("max_parallel", 3)
        self.retry = config["lingxing"].get("retry", 2)

    # ---------- 库存 ----------
    def fetch_inventory(self, sid: int) -> List[InventoryRow]:
        """拉取单个 sid 的 FBA 库存"""
        return self._call_with_retry(
            "get_fba_stock_list",
            sid=sid,
            offset=0,
            length=500,  # 单次最大
            sort_field="available",
            sort_type="desc",
            is_cost_page=0,
            fulfillment_channel_type="FBA",
            transform=lambda items: [
                InventoryRow(
                    sid=sid,
                    country=self.sid_country.get(sid, "?"),
                    msku=item.get("msku", ""),
                    fnsku=item.get("fnsku"),
                    asin=item.get("asin"),
                    available=int(item.get("available", 0) or 0),
                    inbound=int(item.get("inbound", 0) or 0),
                    reserved=int(item.get("reserved", 0) or 0),
                    age_0_90=int(item.get("age_0_90", 0) or 0),
                    age_90_180=int(item.get("age_90_180", 0) or 0),
                    age_180_plus=int(item.get("age_180_plus", 0) or 0),
                )
                for item in items
            ]
        )

    # ---------- 利润 ----------
    def fetch_profit(self, sid: int, date: str) -> List[ProfitRow]:
        """拉取单个 sid 单天的利润数据（按 MSKU 聚合）

        date 格式：YYYY-MM-DD（美西日期）
        """
        return self._call_with_retry(
            "query_order_profit_list_gross_profit",
            sid=sid,
            start_date=date,
            end_date=date,
            offset=0,
            length=500,
            transform=lambda items: [
                ProfitRow(
                    sid=sid,
                    country=self.sid_country.get(sid, "?"),
                    msku=item.get("msku", ""),
                    date=date,
                    orders=int(item.get("order_count", 0) or 0),
                    units=int(item.get("quantity", 0) or 0),
                    sales=float(item.get("sales", 0) or 0),
                    ad_spend=float(item.get("ad_spend", 0) or 0),
                    gross_profit=float(item.get("gross_profit", 0) or 0),
                    gross_margin=float(item.get("gross_margin", 0) or 0),
                    acos=float(item.get("acos", 0) or 0),
                    tacos=float(item.get("tacos", 0) or 0),
                    refund_rate=float(item.get("refund_rate", 0) or 0),
                    return_rate=float(item.get("return_rate", 0) or 0),
                )
                for item in items
            ]
        )

    # ---------- Listing 健康 ----------
    def fetch_listings(self, sid: int) -> List[ListingHealth]:
        """拉取单个 sid 的 Listing 健康数据

        实际 MCP 工具可能是 query_product_performance_asin_lists 或 get_listing_quality
        """
        return self._call_with_retry(
            "query_product_performance_asin_lists",
            sid=sid,
            offset=0,
            length=500,
            transform=lambda items: [
                ListingHealth(
                    sid=sid,
                    country=self.sid_country.get(sid, "?"),
                    asin=item.get("asin", ""),
                    parent_asin=item.get("parent_asin"),
                    msku=item.get("msku"),
                    title=item.get("title"),
                    sessions=int(item.get("sessions", 0) or 0),
                    buybox_owner=item.get("buybox_owner"),
                    is_hijacked=bool(item.get("is_hijacked", False)),
                    category_rank=int(item["category_rank"]) if item.get("category_rank") else None,
                    rating=float(item.get("rating")) if item.get("rating") else None,
                    rating_count=int(item.get("rating_count", 0) or 0),
                    rating_trend_14d=float(item["rating_trend_14d"]) if item.get("rating_trend_14d") else None,
                )
                for item in items
            ]
        )

    # ---------- 通用：重试 + 转换 ----------
    def _call_with_retry(self, tool_name: str, transform, **kwargs):
        """调 MCP 工具，失败重试"""
        for attempt in range(self.retry + 1):
            try:
                raw_items = self._call_mcp(tool_name, **kwargs)
                return transform(raw_items)
            except Exception as e:
                self.logger.warning(
                    f"[{tool_name}] attempt {attempt+1}/{self.retry+1} failed: {e}"
                )
                if attempt < self.retry:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"[{tool_name}] all retries exhausted")
                    raise

    def _call_mcp(self, tool_name: str, **kwargs) -> List[Dict]:
        """实际调 MCP——需要在 WorkBuddy 环境内执行"""
        # ⚠️ 此方法依赖 WorkBuddy MCP 调度层
        # WorkBuddy 通过 mcp__LingXing-MCP__<tool_name>(params={...}) 调
        # 独立 Python 进程里这一行要换成 requests 调 OpenAPI
        raise NotImplementedError(
            f"data_layer.py 不能独立运行，必须在 WorkBuddy 内通过 DeferExecuteTool 调 {tool_name}"
        )


# ============================================
# Mock 数据源（开发/测试用）
# ============================================

class MockDataSource(LingxingDataSource):
    """返回固定结构的 mock 数据，用于：
       1. data_layer 单元测试
       2. rule_engine / html_renderer 联调
       3. W3 端到端 demo

    模拟一个真实触发的场景：US 站 R01 缺货 1 条 + R05 销量骤降 1 条
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__(config, logger)
        self._mock_inventory = {
            5018: [  # US
                self._inv(5018, "KF-2024-08-WALNUT-30", "B0ABCD1234", available=120, age_0_90=80, age_90_180=40),
                self._inv(5018, "KF-2024-08-WALNUT-40", "B0ABCD1235", available=200, age_0_90=150, age_90_180=50),
                self._inv(5018, "KF-2024-09-BLACK-30", "B0ABCD1240", available=8, age_0_90=8, age_90_180=0),     # R01 触发：销量 12/天，库存 8/12 < 1 天
                self._inv(5018, "KF-2024-10-OAK-30", "B0ABCD1250", available=300, age_0_90=200, age_90_180=100),
                self._inv(5018, "KF-2024-11-WALNUT-50", "B0ABCD1260", available=15, age_0_90=15, age_90_180=0),   # R01 触发：销量 5/天，库存 15/5 = 3 天
            ],
            5024: [  # DE
                self._inv(5024, "KF-2024-08-WALNUT-30", "B0DEEF5678", available=200, age_0_90=150, age_90_180=50),
                self._inv(5024, "KF-2024-09-BLACK-40", "B0DEEF5680", available=18, age_0_90=18, age_90_180=0),   # R01 触发：销量 6/天，库存 18/6 = 3 天
            ],
        }
        self._mock_profit = {
            5018: [
                self._prof(5018, "KF-2024-08-WALNUT-30", date="2026-07-26",
                           sales=850, ad_spend=240, gross_profit=180, acos=28.2, tacos=28.2,
                           refund_rate=2.1, return_rate=2.5, units=18),
                self._prof(5018, "KF-2024-09-BLACK-30", date="2026-07-26",
                           sales=120, ad_spend=80, gross_profit=-15, acos=66.7, tacos=66.7,    # R02 触发
                           refund_rate=3.0, return_rate=3.5, units=84),                          # R01 触发：8/84*7=0.67 天
                self._prof(5018, "KF-2024-11-WALNUT-50", date="2026-07-26",
                           sales=600, ad_spend=180, gross_profit=50, acos=30.0, tacos=30.0,
                           refund_rate=6.5, return_rate=2.0, units=35),                          # R06 触发 + R01 触发：15/35*7=3 天
            ],
            5024: [
                self._prof(5024, "KF-2024-09-BLACK-40", date="2026-07-26",
                           sales=200, ad_spend=40, gross_profit=80, acos=20.0, tacos=20.0,
                           refund_rate=1.5, return_rate=2.0, units=42),                          # R01 触发：18/42*7=3 天
            ],
        }
        self._mock_listings = {
            5018: [
                self._lh(5018, "B0ABCD1234", "KF-2024-08-WALNUT-30", sessions=4500,
                         buybox_owner="KovaScape", rating=4.6, rating_count=320,
                         category_rank=1250),
                self._lh(5018, "B0ABCD1240", "KF-2024-09-BLACK-30", sessions=1800,
                         buybox_owner=None, rating=3.8, rating_count=85,  # R04 触发：Buybox 丢失
                         category_rank=8500),
            ],
        }

    def _inv(self, sid, msku, asin, available, age_0_90, age_90_180, age_180_plus=0):
        return InventoryRow(
            sid=sid, country=self.sid_country.get(sid, "?"),
            msku=msku, asin=asin, available=available,
            age_0_90=age_0_90, age_90_180=age_90_180, age_180_plus=age_180_plus
        )

    def _prof(self, sid, msku, date, sales, ad_spend, gross_profit, acos, tacos, refund_rate, return_rate, units=None):
        if units is None:
            units = max(int(sales / 30), 1)  # 估算
        return ProfitRow(
            sid=sid, country=self.sid_country.get(sid, "?"),
            msku=msku, date=date, orders=units, units=units,
            sales=sales, ad_spend=ad_spend, gross_profit=gross_profit,
            gross_margin=round(gross_profit / sales * 100, 1) if sales else 0,
            acos=acos, tacos=tacos, refund_rate=refund_rate, return_rate=return_rate,
        )

    def _lh(self, sid, asin, msku, sessions, buybox_owner, rating, rating_count, category_rank):
        return ListingHealth(
            sid=sid, country=self.sid_country.get(sid, "?"),
            asin=asin, msku=msku, sessions=sessions,
            buybox_owner=buybox_owner, rating=rating,
            rating_count=rating_count, category_rank=category_rank
        )

    def fetch_inventory(self, sid: int) -> List[InventoryRow]:
        return self._mock_inventory.get(sid, [])

    def fetch_profit(self, sid: int, date: str) -> List[ProfitRow]:
        return [p for p in self._mock_profit.get(sid, []) if p.date == date]

    def fetch_listings(self, sid: int) -> List[ListingHealth]:
        return self._mock_listings.get(sid, [])


# ============================================
# 聚合层
# ============================================

class DataAggregator:
    """并行拉所有 sid 的数据 → DailySnapshot"""

    def __init__(self, source: LingxingDataSource, logger: logging.Logger):
        self.source = source
        self.logger = logger

    def aggregate(self, report_date: str) -> DailySnapshot:
        """聚合一天的数据

        report_date: 美西日期 YYYY-MM-DD（如 2026-07-26）
        """
        beijing_now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
        snapshot = DailySnapshot(
            report_date=report_date,
            generated_at=beijing_now,
            sids=self.source.sids,
        )

        # 并行：库存 + 利润 + Listing 三组
        with ThreadPoolExecutor(max_workers=self.source.max_parallel) as executor:
            futures = {}

            # 库存：每个 sid 一次
            for sid in self.source.sids:
                futures[executor.submit(self.source.fetch_inventory, sid)] = ("inv", sid)

            # 利润：每个 sid 一次
            for sid in self.source.sids:
                futures[executor.submit(self.source.fetch_profit, sid, report_date)] = ("prof", sid)

            # Listing：每个 sid 一次
            for sid in self.source.sids:
                futures[executor.submit(self.source.fetch_listings, sid)] = ("lh", sid)

            for future in as_completed(futures):
                kind, sid = futures[future]
                try:
                    rows = future.result()
                    if kind == "inv":
                        snapshot.inventory.extend(rows)
                    elif kind == "prof":
                        snapshot.profit.extend(rows)
                    elif kind == "lh":
                        snapshot.listings.extend(rows)
                except Exception as e:
                    self.logger.error(f"聚合 {kind} sid={sid} 失败: {e}")

        self.logger.info(
            f"[DataAggregator] date={report_date} "
            f"inventory={len(snapshot.inventory)} profit={len(snapshot.profit)} "
            f"listings={len(snapshot.listings)}"
        )
        return snapshot


# ============================================
# 计算层：填充派生字段
# ============================================

def enrich_inventory(snapshot: DailySnapshot, profit_by_msku: Dict[str, ProfitRow]) -> None:
    """根据 profit 数据计算 days_of_supply 和 sales_velocity"""
    for inv in snapshot.inventory:
        profit = profit_by_msku.get(f"{inv.sid}|{inv.msku}")
        if profit:
            velocity = profit.units / 7.0  # 假设 7 日累计
            inv.sales_velocity_7d = round(velocity, 2)
            inv.days_of_supply = round(inv.available / velocity, 1) if velocity > 0 else None


def index_profit_by_msku(snapshot: DailySnapshot) -> Dict[str, ProfitRow]:
    """profit 按 sid+msku 建索引"""
    return {f"{p.sid}|{p.msku}": p for p in snapshot.profit}


# ============================================
# CLI / 测试入口
# ============================================

def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    # config.yaml 在项目根目录，不在 scripts/ 下
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


def main(mode: str = "mock", report_date: Optional[str] = None) -> int:
    """CLI 入口

    mode: "mock" 用 MockDataSource，"real" 用 LingxingDataSource（MCP）
    report_date: 美西日期，默认昨天
    """
    log = setup_logger()
    config = load_config()

    # 默认美西昨天
    if report_date is None:
        us_pacific_now = datetime.now(timezone(timedelta(hours=-7)))
        report_date = (us_pacific_now - timedelta(days=1)).strftime("%Y-%m-%d")

    if mode == "mock":
        source = MockDataSource(config, log)
    else:
        source = LingxingDataSource(config, log)

    aggregator = DataAggregator(source, log)
    snapshot = aggregator.aggregate(report_date)

    # 填充派生字段
    profit_idx = index_profit_by_msku(snapshot)
    enrich_inventory(snapshot, profit_idx)

    # 输出
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"snapshot-{report_date}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)

    log.info(f"snapshot saved: {out_path}")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
    date = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(main(mode=mode, report_date=date))