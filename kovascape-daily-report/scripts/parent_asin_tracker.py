"""
KovaScape Daily Report - 父ASIN变更追踪器
============================================

检测 Amazon ASIN 的父体(parent_asin)是否被篡改。
Amazon 卖家可以通过合并/拆分变体系列改变子ASIN的父体，
这可能导致：
  - 品牌注册保护失效
  - 分类排名丢失
  - 广告活动断联
  - Listing 被恶意篡改

实现逻辑：
  1. 每天从 erp_listing MCP 数据中提取 ASIN → parent_asin 映射
  2. 保存到 output/parent_asin_history.json（保留7天）
  3. 第二天对比，发现的变更输出为 Alert
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_layer import ListingHealth
from rule_engine import Alert


HISTORY_FILE = Path(__file__).resolve().parent.parent / "output" / "parent_asin_history.json"
MAX_DAYS = 7  # 保留天数


# ============================================
# 历史快照读写
# ============================================

def load_history() -> Dict[str, Dict[str, str]]:
    """加载历史 parent_asin 映射

    返回: {"2026-07-25": {"B0XXXX": "B0YYYY", ...}, ...}
    """
    if not HISTORY_FILE.exists():
        return {}
    try:
        raw = HISTORY_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception:
        return {}


def save_snapshot(listings: List[Dict[str, Any]], report_date: str):
    """保存今天的 parent_asin 映射到历史文件

    listings: erp_listing 返回的原始 listing 列表
    """
    history = load_history()

    # 提取今天的映射
    today_map: Dict[str, str] = {}
    for item in listings:
        asin = item.get("asin", "")
        parent_asin = item.get("parent_asin", "")
        if asin and parent_asin:
            today_map[asin] = parent_asin

    # 写入今天的数据
    history[report_date] = today_map

    # 清理旧数据（保留 MAX_DAYS 天）
    dates = sorted(history.keys(), reverse=True)
    for d in dates[MAX_DAYS:]:
        del history[d]

    # 写回文件
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return today_map


# ============================================
# 变更检测
# ============================================

def detect_changes(
    listings: List[Dict[str, Any]],
    history: Dict[str, Dict[str, str]],
    report_date: str,
) -> List[Dict[str, Any]]:
    """检测 parent_asin 变更

    listings: 今天的 listing 数据
    history: 历史快照（load_history() 返回）
    report_date: 今天的日期

    返回: 变更列表 [{asin, old_parent, new_parent, old_parent_title?, new_parent_title?}]
    """
    # 找昨天的快照
    dates = sorted(history.keys())
    if len(dates) < 2:
        return []  # 只有一天数据，无法对比

    # 用最近的非今天快照作为基准
    yesterday_date = None
    for d in reversed(dates):
        if d != report_date:
            yesterday_date = d
            break

    if yesterday_date is None:
        return []

    yesterday_map = history.get(yesterday_date, {})
    if not yesterday_map:
        return []

    # 构建今天 ASIN → parent_asin 的快速索引
    today_map: Dict[str, str] = {}
    today_info: Dict[str, Dict] = {}  # asin → {msku, item_name, ...}
    for item in listings:
        asin = item.get("asin", "")
        parent_asin = item.get("parent_asin", "")
        if asin:
            if parent_asin:
                today_map[asin] = parent_asin
            today_info[asin] = {
                "msku": item.get("msku", ""),
                "item_name": item.get("item_name", ""),
                "country": "",  # 由调用方填充
            }

    # 对比
    changes = []
    for asin, old_parent in yesterday_map.items():
        new_parent = today_map.get(asin)
        if new_parent and new_parent != old_parent:
            changes.append({
                "asin": asin,
                "msku": today_info.get(asin, {}).get("msku", ""),
                "item_name": today_info.get(asin, {}).get("item_name", "")[:80],
                "old_parent_asin": old_parent,
                "new_parent_asin": new_parent,
            })

    return changes


# ============================================
# CLI 入口（测试用）
# ============================================

def main():
    """CLI 入口：读取 output/raw/ 下的 listing 数据，生成 snapshot"""
    import sys
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("kovascape")

    report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        report_date = sys.argv[1]

    # 从 output/raw/{sid}-listings.json 读取数据（如果存在）
    raw_dir = HISTORY_FILE.parent / "raw"
    all_listings = []
    if raw_dir.exists():
        for f in sorted(raw_dir.glob("*-listings.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                inner = data.get("data", {}).get("data", data)
                items = inner.get("list", [])
                all_listings.extend(items)
                log.info(f"  读取 {f.name}: {len(items)} 条")
            except Exception as e:
                log.warning(f"  跳过 {f.name}: {e}")

    if not all_listings:
        log.warning("未找到 listing 数据，尝试从 output/snapshot 读取")
        snap_path = HISTORY_FILE.parent / f"snapshot-{report_date}.json"
        if snap_path.exists():
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            for l in snap.get("listings", []):
                all_listings.append(l)

    if not all_listings:
        log.error("没有任何数据可处理")
        return 1

    # 保存今天快照
    today_map = save_snapshot(all_listings, report_date)
    log.info(f"已保存 {len(today_map)} 条 ASIN→parent_asin 映射到 {HISTORY_FILE}")

    # 检测变更
    history = load_history()
    changes = detect_changes(all_listings, history, report_date)
    if changes:
        log.warning(f"发现 {len(changes)} 条 parent_asin 变更:")
        for c in changes:
            log.warning(f"  {c['asin']}: {c['old_parent_asin']} → {c['new_parent_asin']}")
    else:
        log.info("未发现 parent_asin 变更")

    return 0


if __name__ == "__main__":
    exit(main())
