#!/usr/bin/env python3
"""
ads_analyze.py — KovaScape 广告一键分析入口
=============================================
用法:
    python ads_analyze.py --store KS-US --days 30 --analysis portfolio
    python ads_analyze.py --store KS-UK --days 7  --analysis all

支持的 --analysis 选项:
    portfolio     整体看板 (portfolio-dashboard)
    comparison    活动横向对比 (campaign-comparison)
    acos          保本 ACOS 计算 (break-even-acos)，需传 --price --cogs --fees
    wasted        浪费花费分析 (wasted-spend，需 search term 报告)
    all           全部运行
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from lingxing_pipeline import STORE_MAP, lingxing_to_campaign_csv

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── 从已缓存的领星 JSON 加载 ──────────────────────────────────
def load_lingxing_json(store_key, days=30):
    """
    返回本地已缓存的领星 JSON 路径。
    (实际使用时，领星数据由 MCP 工具拉取并写入此路径)
    """
    fname = f"lingxing_{store_key.replace('-','_').lower()}_{days}d.json"
    return os.path.join(DATA_DIR, fname)

# ── pp-amazon-ads CLI 执行封装 ────────────────────────────────
def run_pp(args_list):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        ["amazon-ads-pp-cli"] + args_list,
        capture_output=True, text=True, encoding="utf-8", env=env
    )
    if result.returncode != 0:
        print(f"[ERR] {result.stderr.strip()}")
        return None
    return json.loads(result.stdout) if result.stdout.strip().startswith("{") else result.stdout

# ── 分析函数 ─────────────────────────────────────────────────
def run_portfolio(csv_path):
    print("\n" + "="*60)
    print("  📊 Portfolio Dashboard")
    print("="*60)
    data = run_pp(["portfolio-dashboard", "--report", csv_path, "--agent"])
    if not data: return
    s = data.get("summary", {})
    acos_pct = round(s.get("acos", 0) * 100, 2)
    roas     = round(1 / s.get("acos", 1), 2) if s.get("acos") else 0
    print(f"  花费   ${s.get('spend', 0):>10,.2f}   | 销售额  ${s.get('sales', 0):>10,.2f}")
    print(f"  订单   {s.get('orders', 0):>10,}   | 点击数  {s.get('clicks', 0):>10,}")
    print(f"  ACOS   {acos_pct:>10.2f}%  | ROAS    {roas:>10.2f}x")
    print(f"  CPC    ${s.get('cpc', 0):>10.2f}   | CTR     {round(s.get('ctr',0)*100,2):>10.2f}%")
    print(f"  CVR    {round(s.get('cvr',0)*100,2):>10.2f}%")

def run_comparison(csv_path):
    print("\n" + "="*60)
    print("  📋 Campaign Comparison（Top 10 花费 + 高/低 ACOS）")
    print("="*60)
    data = run_pp(["campaign-comparison", "--report", csv_path, "--agent"])
    if not data: return

    campaigns = data.get("campaigns", [])
    print(f"\n  {'活动名称':<40s} {'花费':>8} {'ACOS':>7} {'ROAS':>6} {'CVR':>6}")
    print(f"  {'─'*40} {'─'*8} {'─'*7} {'─'*6} {'─'*6}")

    # 按花费排序
    top10 = sorted(campaigns, key=lambda x: x.get("spend", 0), reverse=True)[:10]
    for c in top10:
        name = c.get("campaign", "")[:38] + ".." if len(c.get("campaign","")) > 38 else c.get("campaign","")
        acos_val = c.get("acos", 0)
        acos_pct = round(acos_val * 100, 1) if acos_val else 0
        roas_val = round(1 / acos_val, 2) if acos_val and acos_val > 0 else 0
        cvr_pct  = round(c.get("cvr", 0) * 100, 1)
        flag = "🔴" if acos_pct > 45 else ("🚀" if acos_pct < 20 else "  ")
        print(f"  {flag}{name:<40s} ${c.get('spend',0):>7,.0f} {acos_pct:>6.1f}% {roas_val:>5.2f}x {cvr_pct:>5.1f}%")

    # 高 ACOS
    high = [c for c in campaigns if c.get("acos", 0) > 0.45 and c.get("spend", 0) > 50]
    if high:
        print(f"\n  🔴 高 ACOS 活动 (>45%, 花费>$50)：")
        for c in sorted(high, key=lambda x: x.get("acos",0), reverse=True):
            name = c.get("campaign", "")[:40]
            acos_pct = round(c.get("acos", 0) * 100, 1)
            print(f"     {name:<42s} ACOS {acos_pct:.1f}%  花费 ${c.get('spend',0):.0f}")

    # 低 ACOS 机会
    low = [c for c in campaigns if 0 < c.get("acos", 1) < 0.22 and c.get("spend", 0) > 100]
    if low:
        print(f"\n  🚀 扩量机会 (<22%, 花费>$100)：")
        for c in sorted(low, key=lambda x: x.get("acos", 1)):
            name = c.get("campaign", "")[:40]
            acos_pct = round(c.get("acos", 0) * 100, 1)
            print(f"     {name:<42s} ACOS {acos_pct:.1f}%  花费 ${c.get('spend',0):.0f}")

# ── 主入口 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="KovaScape 广告一键分析")
    parser.add_argument("--store",    default="KS-US", help="店铺代码，如 KS-US, KS-UK")
    parser.add_argument("--days",     default=30, type=int, help="分析天数")
    parser.add_argument("--analysis", default="all", help="分析类型：portfolio/comparison/all")
    parser.add_argument("--raw-json", default=None, help="指定领星 JSON 文件路径（默认自动查找缓存）")
    args = parser.parse_args()

    store_key = args.store.upper()
    if store_key not in STORE_MAP:
        print(f"[ERR] 未知店铺代码: {store_key}。可用: {list(STORE_MAP.keys())}")
        sys.exit(1)

    # 找到 JSON 数据
    raw_json = args.raw_json or load_lingxing_json(store_key, args.days)

    # 转换为 CSV
    csv_path = os.path.join(DATA_DIR, f"{store_key.replace('-','_').lower()}_campaigns.csv")

    if not os.path.exists(raw_json):
        print(f"[INFO] 未找到缓存数据 {raw_json}")
        print(f"[INFO] 请先通过 LingXing-MCP 拉取数据并保存到该路径")
        sys.exit(1)

    n = lingxing_to_campaign_csv(raw_json, csv_path, store_key=store_key)
    if n == 0:
        sys.exit(1)

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"  KovaScape {store_key} 广告分析报告")
    print(f"  时间范围：{start} → {end}（{args.days} 天）")
    print(f"{'='*60}")

    if args.analysis in ("portfolio", "all"):
        run_portfolio(csv_path)
    if args.analysis in ("comparison", "all"):
        run_comparison(csv_path)

    print("\n[DONE] 分析完成。如需执行优化操作，请告知'确认'。\n")

if __name__ == "__main__":
    main()
