# -*- coding: utf-8 -*-
"""
KovaScape 领星周报自动填报与钉钉《运营周复盘》全自动准备脚本 (单周数据直接覆盖 + 原生附件挂载 + 预填预览)
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import openpyxl
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# 常量定义
DWS_BIN = r"D:\Zero Tools\DingTalk\bin\dws.exe"
MCP_CONFIG_PATH = r"C:\Users\Administrator\.gemini\config\mcp_config.json"
MCP_URL = "https://openmcp.lingxing.com/mcp-servers/lingxing-mcp"
REPORT_TEMPLATE_ID = "17a14a44cdee2e409b88ad14ca68d77b" # 运营周复盘（周一9:00前提交）
USER_ID_WY = "17566881508928543"

SIDS_STR = "5030,5751,5019,5024,5026,5025,5031,5023,5021,5020,5027,5029,5028,5022,5018"
SIDS_LIST = [5030, 5751, 5019, 5024, 5026, 5025, 5031, 5023, 5021, 5020, 5027, 5029, 5028, 5022, 5018]

# 2026 财年内置目标表 (按报告日期月份提取，周目标 = 月目标 / 4)
FY2026_TARGETS = {
    "2026-04": {"group_sales": 150000, "wy_sales": 45000, "group_profit": 10000, "wy_profit": 3000},
    "2026-05": {"group_sales": 90000,  "wy_sales": 27000, "group_profit": 6000,  "wy_profit": 1800},
    "2026-06": {"group_sales": 65000,  "wy_sales": 19500, "group_profit": 4000,  "wy_profit": 1200},
    "2026-07": {"group_sales": 120000, "wy_sales": 48000, "group_profit": 20000, "wy_profit": 8000},
    "2026-08": {"group_sales": 280000, "wy_sales": 112000, "group_profit": 40000, "wy_profit": 16000},
    "2026-09": {"group_sales": 280000, "wy_sales": 112000, "group_profit": 40000, "wy_profit": 16000},
    "2026-10": {"group_sales": 450000, "wy_sales": 180000, "group_profit": 70000, "wy_profit": 28000},
    "2026-11": {"group_sales": 550000, "wy_sales": 220000, "group_profit": 90000, "wy_profit": 36000},
    "2026-12": {"group_sales": 600000, "wy_sales": 270000, "group_profit": 100000, "wy_profit": 45000},
    "2027-01": {"group_sales": 720000, "wy_sales": 324000, "group_profit": 120000, "wy_profit": 54000},
    "2027-02": {"group_sales": 880000, "wy_sales": 396000, "group_profit": 150000, "wy_profit": 67500},
    "2027-03": {"group_sales": 950000, "wy_sales": 427500, "group_profit": 160000, "wy_profit": 72000},
}

def get_mcp_headers():
    key = "a12e733b81a539ab08cb05f0110c5624"
    if os.path.exists(MCP_CONFIG_PATH):
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                key = cfg.get("mcpServers", {}).get("LingXing-MCP", {}).get("headers", {}).get("X-Mcp-Key", key)
        except Exception:
            pass
    return {
        "Content-Type": "application/json",
        "X-Mcp-Key": key
    }

def call_mcp_tool(name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments
        },
        "id": 1
    }
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode('utf-8'), headers=get_mcp_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        res_json = json.loads(resp.read().decode('utf-8'))
        content_text = res_json["result"]["content"][0]["text"]
        return json.loads(content_text)

def run_dws(args):
    cmd = [DWS_BIN] + args + ["-f", "json"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"dws error: {res.stderr}")
        return None
    try:
        return json.loads(res.stdout)
    except Exception as e:
        print(f"JSON decode error: {e}")
        return None

# 1. 抓取业绩、广告、利润与库存
def pull_performance_and_stock(start_date="2026-07-26", end_date="2026-08-01"):
    print(f"📊 正在从领星 MCP 抓取单周业绩数据 ({start_date} ~ {end_date})...")
    
    # 抓取单周业绩
    perf_res = call_mcp_tool("query_product_performance_asin_lists", {
        "sids": SIDS_STR,
        "start_date": start_date,
        "end_date": end_date,
        "currency_code": "USD",
        "summary_field": "asin",
        "offset": 0,
        "length": 1000
    })
    
    # 按“王祎”筛选个人业绩
    res_data_obj = perf_res.get("data", {})
    if isinstance(res_data_obj, dict) and "data" in res_data_obj:
        res_data_obj = res_data_obj.get("data", {})
    items = res_data_obj.get("list", [])
    volume = 0.0
    amount = 0.0
    ad_spend = 0.0
    predict_gross_profit = 0.0
    
    for item in items:
        principals = item.get("principal_names") or []
        if "王祎" in principals:
            volume += float(item.get("volume") or 0)
            amount += float(item.get("amount") or 0.0)
            ad_spend += float(item.get("spend") or 0.0)
            predict_gross_profit += float(item.get("predict_gross_profit") or 0.0)

    actual_profit = predict_gross_profit * 0.6
    acoas = (ad_spend / amount * 100) if amount > 0 else 0.0

    # 抓取当月累计业绩 (用于月实际销售额与月实际毛利)
    dt_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    month_start = f"{dt_end.year:04d}-{dt_end.month:02d}-01"
    print(f"📅 正在从领星 MCP 抓取当月累计业绩 ({month_start} ~ {end_date})...")
    month_perf_res = call_mcp_tool("query_product_performance_asin_lists", {
        "sids": SIDS_STR,
        "start_date": month_start,
        "end_date": end_date,
        "currency_code": "USD",
        "summary_field": "asin",
        "offset": 0,
        "length": 1000
    })
    m_data_obj = month_perf_res.get("data", {})
    if isinstance(m_data_obj, dict) and "data" in m_data_obj:
        m_data_obj = m_data_obj.get("data", {})
    month_items = m_data_obj.get("list", [])
    month_amount = 0.0
    month_ad_spend = 0.0
    month_predict_profit = 0.0
    
    for item in month_items:
        principals = item.get("principal_names") or []
        if "王祎" in principals:
            month_amount += float(item.get("amount") or 0.0)
            month_ad_spend += float(item.get("spend") or 0.0)
            month_predict_profit += float(item.get("predict_gross_profit") or 0.0)

    month_actual_profit = month_predict_profit * 0.6
    month_acoas = (month_ad_spend / month_amount * 100) if month_amount > 0 else 0.0

    # 多线程抓取 15 店铺 FBA 库存与库龄
    print("📦 正在并发抓取 15 个店铺的 FBA 库存与库龄...")
    fba_stock_total = 0
    age_90_180 = 0
    age_181_270 = 0
    age_271_365 = 0
    age_365_plus = 0

    def fetch_sid_stock(sid):
        try:
            res = call_mcp_tool("get_fba_stock_list", {"sid": sid, "length": 2000})
            items = res.get("data", {}).get("list", [])
            s_fba = 0
            a90, a181, a271, a365 = 0, 0, 0, 0
            for item in items:
                fulfillable = int(item.get("afn_fulfillable_quantity") or 0)
                reserved_transfers = int(item.get("reserved_fc_transfers") or 0)
                reserved_other = int(item.get("afn_reserved_quantity") or 0)
                s_fba += (fulfillable + reserved_transfers + reserved_other)

                a90 += int(item.get("inv_age_91_to_180_days") or 0)
                a181 += int(item.get("inv_age_181_to_270_days") or 0)
                a271 += int(item.get("inv_age_271_to_365_days") or 0)
                a365 += int(item.get("inv_age_365_plus_days") or 0)
            return s_fba, a90, a181, a271, a365
        except Exception:
            return 0, 0, 0, 0, 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_sid_stock, sid) for sid in SIDS_LIST]
        for f in futures:
            s_fba, a90, a181, a271, a365 = f.result()
            fba_stock_total += s_fba
            age_90_180 += a90
            age_181_270 += a181
            age_271_365 += a271
            age_365_plus += a365

    # 库销比计算: (FBA在库总库存 / 近7天日均销) / 30
    daily_avg_7d = volume / 7.0 if volume > 0 else 1.0
    stock_to_sales_ratio = (fba_stock_total / daily_avg_7d) / 30.0

    return {
        "volume": volume,
        "amount": amount,
        "ad_spend": ad_spend,
        "acoas": acoas,
        "actual_profit": actual_profit,
        "month_amount": month_amount,
        "month_acoas": month_acoas,
        "month_actual_profit": month_actual_profit,
        "fba_stock_total": fba_stock_total,
        "stock_to_sales_ratio": stock_to_sales_ratio,
        "age_90_180": age_90_180,
        "age_181_270": age_181_270,
        "age_271_365": age_271_365,
        "age_365_plus": age_365_plus,
    }

# 2. 覆盖更新 Excel 文件
def update_excel_file(excel_path, data, month_key="2026-07"):
    print(f"📝 正在直接覆盖更新 Excel 文件: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, data_only=False)
    
    # 获取工作表
    sheet_weekly = wb["周报"] if "周报" in wb.sheetnames else wb.worksheets[0]
    sheet_clear = wb["清货进度表"] if "清货进度表" in wb.sheetnames else None

    # 获取月度目标
    targets = FY2026_TARGETS.get(month_key, FY2026_TARGETS["2026-07"])
    monthly_sales_target = targets["wy_sales"] # 王祎月目标销售额
    weekly_sales_target = monthly_sales_target / 4.0
    monthly_profit_target = targets["wy_profit"] # 王祎月目标毛利额

    # 针对周报 Sheet 直接覆盖填入最新单周数据（非累加！）
    # Row 2 是关键维度
    sheet_weekly["D2"] = data["amount"]                # 本周实际销售额
    sheet_weekly["E2"] = weekly_sales_target           # 本周目标销售额
    sheet_weekly["F2"] = data["acoas"] / 100.0          # 本周 ACOAS
    sheet_weekly["G2"] = "=D2/E2"                      # 周达成率公式

    sheet_weekly["H2"] = monthly_sales_target          # 月目标销售额
    sheet_weekly["I2"] = data["month_amount"]          # 月实际销售额
    sheet_weekly["J2"] = data["month_acoas"] / 100.0    # 月 ACOAS
    sheet_weekly["K2"] = "=I2/H2"                      # 月销售达成率公式

    sheet_weekly["L2"] = monthly_profit_target         # 月目标毛利额
    sheet_weekly["M2"] = data["month_actual_profit"]    # 月实际毛利额 (*0.6)
    sheet_weekly["N2"] = "=M2/L2"                      # 毛利达成率公式

    sheet_weekly["O2"] = round(data["stock_to_sales_ratio"], 2) # 最新月库销比

    # 清货进度表覆盖更新
    if sheet_clear:
        sheet_clear["D2"] = data["age_90_180"]
        sheet_clear["G2"] = data["age_181_270"]
        sheet_clear["J2"] = data["age_271_365"]
        sheet_clear["M2"] = data["age_365_plus"]

    try:
        wb.save(excel_path)
    except PermissionError:
        alt_path = os.path.join(os.path.dirname(excel_path), "运营周会数据收集_王祎_v19_new_latest.xlsx")
        wb.save(alt_path)
        excel_path = alt_path
        print(f"⚠️ 原文件被占用，已保存至备用路径: {excel_path}")
    wb.close()

    # 使用 win32com 重新计算所有公式
    try:
        import win32com.client
        abs_path = os.path.abspath(excel_path)
        excel = win32com.client.DispatchEx('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        wb_com = excel.Workbooks.Open(abs_path)
        excel.CalculateFull()
        wb_com.Save()
        wb_com.Close(SaveChanges=True)
        excel.Quit()
        print("✅ Excel 公式全量重算完成并保存！")
    except Exception as e:
        print(f"⚠️ COM 重算提示: {e}")

# 3. 从 AI 表格读取全量任务
def fetch_aitable_tasks(week_num=31):
    base_id = "R1zknDm0WRNmEDKZSBED3jE4WBQEx5rG"
    table_id = "dv19yqvsgs3oebp3pcjys"
    res = run_dws(["aitable", "record", "list", "--all", "--base-id", base_id, "--table-id", table_id])
    
    curr_tasks = []
    next_tasks = []
    
    if res and "records" in res:
        for r in res["records"]:
            cells = r.get("cells", {})
            task_name = cells.get("jxzfinmckxuusjowbz5ca", "")
            assignees = cells.get("sb82jyoeivzhh5is2guac", [])
            w_str = str(cells.get("8LkwFxC", ""))
            
            # 判断负责人包含王祎
            is_wy = any("王祎" in str(a) for a in assignees) if isinstance(assignees, list) else "王祎" in str(assignees)
            if is_wy and task_name:
                if f"第{week_num}周" in w_str or f"{week_num}周" in w_str:
                    curr_tasks.append(f"{len(curr_tasks)+1}. {task_name}")
                elif f"第{week_num+1}周" in w_str or f"{week_num+1}周" in w_str:
                    next_tasks.append(f"{len(next_tasks)+1}. {task_name}")

    curr_text = "\n".join(curr_tasks) if curr_tasks else "1. 本周重点任务清理与推进"
    next_text = "\n".join(next_tasks) if next_tasks else "1. 下周重点任务跟进"
    return curr_text, next_text

# 4. 上传钉盘 & 设置公开权限
def upload_to_drive(excel_path):
    print("☁️ 正在上传 Excel 到钉盘...")
    res = run_dws(["drive", "upload", "--file", excel_path])
    if not res or "result" not in res:
        print("❌ 上传钉盘失败")
        return None
    
    result = res["result"]
    space_id = str(result.get("spaceId"))
    file_id = str(result.get("fileId"))
    file_name = str(result.get("fileName"))
    file_size = int(result.get("fileSize", 9618))
    doc_url = str(result.get("docUrl"))

    # 设置企业内公开与复制下载权限
    print(f"🔐 正在设置文件权限 (ID: {file_id})...")
    run_dws(["drive", "publish", "set", "--node", file_id, "-y"])
    
    return {
        "spaceId": space_id,
        "fileId": file_id,
        "fileName": file_name,
        "fileSize": file_size,
        "fileType": "xlsx",
        "docUrl": doc_url
    }

# 5. 组装提交 JSON (挂载原生附件)
def build_report_payload(data, attach_info, curr_tasks, next_tasks, month_key="2026-07"):
    targets = FY2026_TARGETS.get(month_key, FY2026_TARGETS["2026-07"])
    monthly_sales_target = targets["wy_sales"]
    weekly_sales_target = monthly_sales_target / 4.0
    monthly_profit_target = targets["wy_profit"]

    actual_profit_val = round(data["month_actual_profit"], 2)
    profit_rate_val = round((actual_profit_val / monthly_profit_target * 100), 1) if monthly_profit_target > 0 else 0.0

    attachment_json_str = json.dumps([{
        "spaceId": attach_info["spaceId"],
        "fileId": attach_info["fileId"],
        "fileName": attach_info["fileName"],
        "fileSize": attach_info["fileSize"],
        "fileType": "xlsx"
    }], ensure_ascii=False)

    payload = [
        {"key": "附件", "sort": "56", "content": attachment_json_str, "contentType": "origin", "type": "9"},
        {"key": "周销量", "sort": "20", "content": str(int(data["volume"])), "contentType": "origin", "type": "2"},
        {"key": "本周实际销售额$", "sort": "21", "content": str(round(data["amount"], 2)), "contentType": "origin", "type": "2"},
        {"key": "AcoAs（%）", "sort": "22", "content": str(round(data["acoas"], 2)), "contentType": "origin", "type": "2"},
        {"key": "本周目标销售额$", "sort": "23", "content": str(round(weekly_sales_target, 2)), "contentType": "origin", "type": "2"},
        {"key": "下周目标销售额$", "sort": "24", "content": str(round(weekly_sales_target, 2)), "contentType": "origin", "type": "2"},
        {"key": "月目标销售额$", "sort": "25", "content": str(round(monthly_sales_target, 2)), "contentType": "origin", "type": "2"},
        {"key": "月实际销售额$", "sort": "26", "content": str(round(data["month_amount"], 2)), "contentType": "origin", "type": "2"},
        {"key": "月AcoAs（%）", "sort": "55", "content": str(round(data["month_acoas"], 2)), "contentType": "markdown", "type": "1"},
        {"key": "月目标毛利额$", "sort": "29", "content": str(round(monthly_profit_target, 2)), "contentType": "origin", "type": "2"},
        {"key": "月实际毛利额（未扣除工资、房租物业和财务成本等）$", "sort": "30", "content": str(actual_profit_val), "contentType": "origin", "type": "2"},
        {"key": "毛利额完成比率（%）", "sort": "31", "content": str(profit_rate_val), "contentType": "origin", "type": "2"},
        {"key": "近30天库销比（FBA在库库存）", "sort": "57", "content": str(round(data["stock_to_sales_ratio"], 2)), "contentType": "markdown", "type": "1"},
        {"key": "当前库存数量——90-180天库龄", "sort": "35", "content": str(data["age_90_180"]), "contentType": "origin", "type": "2"},
        {"key": "当前库存数量——181-270天库龄", "sort": "38", "content": str(data["age_181_270"]), "contentType": "origin", "type": "2"},
        {"key": "当前库存数量——271-365天库龄", "sort": "41", "content": str(data["age_271_365"]), "contentType": "origin", "type": "2"},
        {"key": "当前库存数量——366天以上库龄", "sort": "44", "content": str(data["age_365_plus"]), "contentType": "origin", "type": "2"},
        {"key": "本周重点工作及完成情况(事、量化、做到什么程度)", "sort": "17", "content": curr_tasks, "contentType": "markdown", "type": "1"},
        {"key": "下周重点工作及计划（事、量化、时间/不超3项）", "sort": "1", "content": next_tasks, "contentType": "markdown", "type": "1"}
    ]
    return payload

def main():
    excel_path = r"C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎_v19_new.xlsx"
    
    # 1. 抓取业绩与库存数据
    data = pull_performance_and_stock(start_date="2026-07-26", end_date="2026-08-01")

    # 2. 覆盖更新 Excel
    update_excel_file(excel_path, data, month_key="2026-07")

    # 3. 抓取 AI 表格重点任务
    curr_tasks, next_tasks = fetch_aitable_tasks(week_num=31)

    # 4. 上传钉盘
    attach_info = upload_to_drive(excel_path)
    if not attach_info:
        print("❌ 附件上传失败")
        return

    # 5. 组装预填 Payload
    payload = build_report_payload(data, attach_info, curr_tasks, next_tasks, month_key="2026-07")
    
    payload_file = r"d:\Zero Tools\skills\lingxing-weekly-report\report_payload.json"
    os.makedirs(os.path.dirname(payload_file), exist_ok=True)
    with open(payload_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("\n==================================================================")
    print("✅ 运营周报预填数据与【原生附件】已成功准备完毕！")
    print(f"📁 预填文件保存至: {payload_file}")
    print(f"📎 附带最新 Excel 钉盘链接: {attach_info['docUrl']}")
    print("⚠️ 注意：根据要求，系统不会自动提交日志，请审核下方数据并在聊天框回复“确认”后再行发送。")
    print("==================================================================\n")

if __name__ == "__main__":
    main()
