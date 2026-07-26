import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# 配置与路径
# ============================================================
DB_FILE = r"d:\Zero Tools\data\kovascape_ads.db"
DATA_DIR = r"d:\Zero Tools\data"

# ============================================================
# KovaScape 异常过滤器判定规则配置 (RPD Rule Layer)
# ============================================================
RULES_CONFIG = {
    "high_acos": {
        "threshold": 40.0,      # ACOS 阈值 (%)
        "min_spend": 50.0,       # 最低花费，过滤掉极小样本干扰
        "name": "广告烧钱无效/ACOS过高"
    },
    "zero_sales_high_clicks": {
        "min_clicks": 15,       # 产生点击但 0 订单
        "name": "广告不出单 (有点击无转化)"
    },
    "budget_drain": {
        "usage_pct": 0.95,      # 预算消耗率超过 95%
        "name": "预算提前超限/截流预警"
    },
    "sales_drop": {
        "drop_pct": 30.0,       # 近7天销量对比上一个7天环比降幅 (%)
        "name": "销量异常突降"
    }
}

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def detect_campaign_anomalies(target_date=None):
    """
    基于 SQLite 数据库执行日常异常过滤器 (Daily Loop - Campaign Level)
    利用 SQL 与 Pandas 极速计算并归纳问题，0 Token 消耗。
    """
    if target_date is None:
        # 默认检查最新的一天（以数据库里有数据的最后一天为准）
        conn = get_db_connection()
        res = conn.execute("SELECT MAX(date) FROM campaign_daily_performance").fetchone()
        conn.close()
        if res and res[0]:
            target_date = res[0]
        else:
            print("[WARN] Database is empty. Cannot detect anomalies.")
            return []

    print(f"\n🔍 Running anomaly detection for date: {target_date}...")
    
    conn = get_db_connection()
    
    # 1. 读取当前目标日期的全部活动表现
    query_today = """
    SELECT date, campaignId, campaignName, impressions, clicks, cost, sales, orders, acos, dailyBudget, store, portfolioId
    FROM campaign_daily_performance
    WHERE date = ?
    """
    df_today = pd.read_sql(query_today, conn, params=(target_date,))
    
    # 2. 读取前一周期的表现（用于计算环比突降）
    # 计算当前日期的 7 天前和 14 天前
    try:
        t_date = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"[ERR] Invalid date format in DB: {target_date}")
        return []
        
    date_7d_ago = (t_date - timedelta(days=7)).strftime("%Y-%m-%d")
    date_14d_ago = (t_date - timedelta(days=14)).strftime("%Y-%m-%d")
    
    query_history = """
    SELECT campaignId, SUM(sales) as hist_sales, SUM(orders) as hist_orders, SUM(cost) as hist_cost
    FROM campaign_daily_performance
    WHERE date >= ? AND date < ?
    GROUP BY campaignId
    """
    # 近 7 天累计 (Today - 7 -> Today)
    df_last_7d = pd.read_sql(query_history, conn, params=(date_7d_ago, target_date))
    # 上上周 7 天累计 (Today - 14 -> Today - 7)
    df_prev_7d = pd.read_sql(query_history, conn, params=(date_14d_ago, date_7d_ago))
    
    conn.close()
    
    if df_today.empty:
        print(f"[WARN] No records found for date {target_date}.")
        return []
        
    anomalies = []
    
    # 将历史数据转成字典以便快速 lookup
    last_7d_dict = df_last_7d.set_index('campaignId').to_dict('index')
    prev_7d_dict = df_prev_7d.set_index('campaignId').to_dict('index')
    
    for _, row in df_today.iterrows():
        cid = row['campaignId']
        cname = row['campaignName']
        cost = row['cost']
        sales = row['sales']
        orders = row['orders']
        clicks = row['clicks']
        acos = row['acos']
        budget = row['dailyBudget']
        store = row['store']
        
        issue_tags = []
        details = {}
        
        # ── 规则 1：ACOS 过高 ──
        if acos >= RULES_CONFIG["high_acos"]["threshold"] and cost >= RULES_CONFIG["high_acos"]["min_spend"]:
            issue_tags.append(RULES_CONFIG["high_acos"]["name"])
            details["acos"] = f"{acos:.1f}%"
            details["spend"] = f"${cost:.2f}"
            
        # ── 规则 2：有点击无转化 (烧钱无效) ──
        if clicks >= RULES_CONFIG["zero_sales_high_clicks"]["min_clicks"] and orders == 0:
            issue_tags.append(RULES_CONFIG["zero_sales_high_clicks"]["name"])
            details["clicks"] = clicks
            details["spend"] = f"${cost:.2f}"
            
        # ── 规则 3：预算提前超额 (消耗率 > 95%) ──
        # 日预算不为零且花费接近预算
        if budget > 0 and (cost / budget) >= RULES_CONFIG["budget_drain"]["usage_pct"]:
            issue_tags.append(RULES_CONFIG["budget_drain"]["name"])
            details["budget_usage"] = f"{((cost/budget)*100):.1f}%"
            details["current_budget"] = f"${budget:.2f}"
            details["suggested_budget"] = f"${budget * 1.5:.0f}"  # 预测扩幅
            
        # ── 规则 4：销量环比大幅突降 ──
        if cid in last_7d_dict and cid in prev_7d_dict:
            curr_sales = last_7d_dict[cid]['hist_sales']
            past_sales = prev_7d_dict[cid]['hist_sales']
            if past_sales > 100:  # 排除小基数扰动
                drop = ((past_sales - curr_sales) / past_sales) * 100
                if drop >= RULES_CONFIG["sales_drop"]["drop_pct"]:
                    issue_tags.append(RULES_CONFIG["sales_drop"]["name"])
                    details["sales_drop_pct"] = f"{drop:.1f}%"
                    details["last_7d_sales"] = f"${curr_sales:.2f}"
                    details["prev_7d_sales"] = f"${past_sales:.2f}"
                    
        # 归档异常
        if issue_tags:
            anomalies.append({
                "store": store,
                "campaignId": cid,
                "campaignName": cname,
                "issues": issue_tags,
                "details": details,
                "raw_metrics": {
                    "cost": cost,
                    "sales": sales,
                    "orders": orders,
                    "clicks": clicks,
                    "acos": acos,
                    "budget": budget
                }
            })
            
    print(f"[OK] Anomaly scan complete. Found {len(anomalies)} problematic campaigns.")
    return anomalies

def generate_daily_markdown_report(anomalies, target_date):
    """
    将扫描到的异常格式化为高可读性的操作总表 Markdown 文件，
    为第二天早上 9:30 的推送做数据准备。
    """
    report_path = os.path.join(DATA_DIR, f"daily_anomaly_report_{target_date}.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 🔍 KovaScape 每日广告异动巡检报告\n")
        f.write(f"> **巡检日期**：{target_date} | **扫描范围**：全站点活动 | **异常总数**：{len(anomalies)} 个\n\n")
        f.write("---\n\n")
        
        if not anomalies:
            f.write("### 🎉 今日无异常活动，全站点健康度极佳！\n")
            return report_path
            
        # 按站点归类展示
        stores = set([x['store'] for x in anomalies])
        for st in stores:
            f.write(f"## 🌐 站点：{st}\n")
            f.write(f"| 活动名称 | 诊断出的问题 | 关键指标数据 | 建议操作 |\n")
            f.write(f"| :--- | :--- | :--- | :--- |\n")
            
            st_anoms = [x for x in anomalies if x['store'] == st]
            for a in st_anoms:
                issues_str = "、".join([f"⚠️ **{i}**" for i in a['issues']])
                
                # 组装细节字符串
                details_parts = []
                for k, v in a['details'].items():
                    details_parts.append(f"{k}: {v}")
                details_str = "<br/>".join(details_parts)
                
                # AI 生成的简单建议操作 (用于 ActionCard 中继)
                action_suggestion = "建议下调出价"
                if "预算提前超限/截流预警" in a['issues']:
                    if a['raw_metrics']['acos'] < 30:
                        action_suggestion = f"建议提高预算至 {a['details'].get('suggested_budget', '$20')}"
                    else:
                        action_suggestion = "表现一般，建议维持原状"
                elif "广告不出单 (有点击无转化)" in a['issues']:
                    action_suggestion = "建议暂停或检查排词"
                    
                f.write(f"| {a['campaignName']} | {issues_str} | {details_str} | {action_suggestion} |\n")
            f.write("\n")
            
        f.write("---\n")
        f.write(f"*以上报告由本地 Daily Loop 脚本于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 自动计算生成。*\n")
        
    print(f"[OK] Markdown anomaly report generated at: {report_path}")
    return report_path

if __name__ == "__main__":
    # 测试扫描我们刚刚导入的 2026-07-12（或 11 号）的数据
    anoms = detect_campaign_anomalies("2026-07-12")
    if not anoms:
        # 如果没有 12 号的，检查 11 号
        anoms = detect_campaign_anomalies("2026-07-11")
        
    if anoms:
        generate_daily_markdown_report(anoms, anoms[0]['raw_metrics'].get('date', '2026-07-12'))
