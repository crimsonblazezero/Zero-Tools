# -*- coding: utf-8 -*-
"""
KovaScape 领星周报自动填报与推送脚本
KovaScape LingXing Weekly Report Auto-filling and Push Script
"""

import os
import sys
import json
import datetime
import requests
import openpyxl
import subprocess

# 领星 MCP HTTP 接口配置
MCP_URL = "http://openmcp.lingxing.com/mcp-servers/lingxing-mcp"
MCP_HEADERS = {
    "X-Mcp-Key": "b7a40552c273e2757ada0bfd047d20a9"
}

# 南京欧洲组的 15 个店铺 ID
SIDS = [5030, 5024, 5026, 5031, 5025, 5023, 5021, 5027, 5029, 5028, 5022, 5751, 5019, 5020, 5018]

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
    response = requests.post(MCP_URL, json=payload, headers=MCP_HEADERS)
    response.raise_for_status()
    res_json = response.json()
    if "error" in res_json or res_json.get("result", {}).get("isError"):
        raise Exception(f"MCP Tool error: {res_json}")
    
    content_text = res_json["result"]["content"][0]["text"]
    return json.loads(content_text)

def get_weekly_profit_data(start_date, end_date):
    print(f"Fetching profit report from {start_date} to {end_date}...")
    data = call_mcp_tool("get_profit_report_msku", {
        "startDate": start_date,
        "endDate": end_date,
        "length": 1000
    })
    
    records = data.get("data", {}).get("data", {}).get("records", [])
    
    stats = {
        "化一博": {"sales": 0.0, "qty": 0, "profit": 0.0, "ads": 0.0},
        "王祎": {"sales": 0.0, "qty": 0, "profit": 0.0, "ads": 0.0}
    }
    
    for r in records:
        sid = int(r.get("sid") or 0)
        if sid not in SIDS:
            continue
        
        principal = r.get("principalRealname")
        if principal not in ["化一博", "王祎"]:
            continue
            
        sales = float(r.get("totalSalesAmount") or 0.0)
        qty = int(r.get("totalSalesQuantity") or 0)
        profit = float(r.get("grossProfit") or 0.0)
        ads = float(r.get("totalAdsCost") or 0.0)
        
        stats[principal]["sales"] += sales
        stats[principal]["qty"] += qty
        stats[principal]["profit"] += profit
        stats[principal]["ads"] += ads
        
    return stats

def get_fba_stock_data():
    print("Fetching FBA stock list for all 15 SIDs...")
    stock_stats = {
        "化一博": {"91-180": 0, "181-270": 0, "271-365": 0, "365+": 0},
        "王祎": {"91-180": 0, "181-270": 0, "271-365": 0, "365+": 0}
    }
    
    for sid in SIDS:
        try:
            data = call_mcp_tool("get_fba_stock_list", {
                "sid": sid,
                "length": 2000
            })
            records = data.get("data", {}).get("list", [])
            for item in records:
                principals = item.get("asin_principal_list") or []
                target_principal = "化一博"
                if "王祎" in principals:
                    target_principal = "王祎"
                
                stock_stats[target_principal]["91-180"] += int(item.get("inv_age_91_to_180_days") or 0)
                stock_stats[target_principal]["181-270"] += int(item.get("inv_age_181_to_270_days") or 0)
                stock_stats[target_principal]["271-365"] += int(item.get("inv_age_271_to_365_days") or 0)
                stock_stats[target_principal]["365+"] += int(item.get("inv_age_365_plus_days") or 0)
        except Exception as e:
            print(f"Error fetching stock for SID {sid}: {e}")
            
    return stock_stats

def fill_excel_workbook(filepath, weekly_data, stock_data, date_str):
    print(f"Loading Excel file: {filepath}")
    wb = openpyxl.load_workbook(filepath, data_only=False)
    
    sheet_weekly = wb["202606周报"]
    
    total_sales = weekly_data["王祎"]["sales"] + weekly_data["化一博"]["sales"]
    total_ads = weekly_data["王祎"]["ads"] + weekly_data["化一博"]["ads"]
    total_acoas = -total_ads / total_sales if total_sales > 0 else 0.0
    
    wy_sales = weekly_data["王祎"]["sales"]
    wy_acoas = -weekly_data["王祎"]["ads"] / wy_sales if wy_sales > 0 else 0.0
    
    hyb_sales = weekly_data["化一博"]["sales"]
    hyb_acoas = -weekly_data["化一博"]["ads"] / hyb_sales if hyb_sales > 0 else 0.0
    
    sheet_weekly.cell(row=39, column=10, value=total_sales)
    sheet_weekly.cell(row=39, column=12, value=total_acoas)
    sheet_weekly.cell(row=40, column=10, value=wy_sales)
    sheet_weekly.cell(row=40, column=12, value=wy_acoas)
    sheet_weekly.cell(row=41, column=12, value=hyb_acoas)
    
    wb_read = openpyxl.load_workbook(filepath, data_only=True)
    sw_read = wb_read["202606周报"]
    
    old_p39 = float(sw_read.cell(row=39, column=16).value or 0.0)
    old_q39 = float(sw_read.cell(row=39, column=17).value or 0.0)
    old_u39 = float(sw_read.cell(row=39, column=21).value or 0.0)
    
    old_p40 = float(sw_read.cell(row=40, column=16).value or 0.0)
    old_q40 = float(sw_read.cell(row=40, column=17).value or 0.0)
    old_u40 = float(sw_read.cell(row=40, column=21).value or 0.0)
    
    old_p41 = float(sw_read.cell(row=41, column=16).value or 0.0)
    old_q41 = float(sw_read.cell(row=41, column=17).value or 0.0)
    
    wb_read.close()
    
    new_p39 = old_p39 + total_sales
    new_u39 = old_u39 + (weekly_data["王祎"]["profit"] + weekly_data["化一博"]["profit"])
    new_q39 = (old_p39 * old_q39 - total_ads) / new_p39 if new_p39 > 0 else 0.0
    
    new_p40 = old_p40 + wy_sales
    new_u40 = old_u40 + weekly_data["王祎"]["profit"]
    new_q40 = (old_p40 * old_q40 - weekly_data["王祎"]["ads"]) / new_p40 if new_p40 > 0 else 0.0
    
    new_q41 = (old_p41 * old_q41 - weekly_data["化一博"]["ads"]) / (old_p41 + hyb_sales) if (old_p41 + hyb_sales) > 0 else 0.0
    
    sheet_weekly.cell(row=39, column=16, value=new_p39)
    sheet_weekly.cell(row=39, column=17, value=new_q39)
    sheet_weekly.cell(row=39, column=21, value=new_u39)
    
    sheet_weekly.cell(row=40, column=16, value=new_p40)
    sheet_weekly.cell(row=40, column=17, value=new_q40)
    sheet_weekly.cell(row=40, column=21, value=new_u40)
    
    sheet_weekly.cell(row=41, column=17, value=new_q41)
    
    sheet_clear = wb["清货进度表"]
    
    tot_91 = stock_data["王祎"]["91-180"] + stock_data["化一博"]["91-180"]
    tot_181 = stock_data["王祎"]["181-270"] + stock_data["化一博"]["181-270"]
    tot_271 = stock_data["王祎"]["271-365"] + stock_data["化一博"]["271-365"]
    tot_365 = stock_data["王祎"]["365+"] + stock_data["化一博"]["365+"]
    
    sheet_clear.cell(row=41, column=3, value=tot_91)
    sheet_clear.cell(row=41, column=6, value=tot_181)
    sheet_clear.cell(row=41, column=9, value=tot_271)
    sheet_clear.cell(row=41, column=12, value=tot_365)
    
    sheet_clear.cell(row=42, column=3, value=stock_data["王祎"]["91-180"])
    sheet_clear.cell(row=42, column=6, value=stock_data["王祎"]["181-270"])
    sheet_clear.cell(row=42, column=9, value=stock_data["王祎"]["271-365"])
    sheet_clear.cell(row=42, column=12, value=stock_data["王祎"]["365+"])
    
    def fill_support_sheet(sheet_name, is_stock):
        sh = wb[sheet_name]
        if is_stock:
            sh.cell(row=31, column=2, value=stock_data["王祎"]["91-180"])
            sh.cell(row=31, column=4, value=stock_data["王祎"]["181-270"])
            sh.cell(row=31, column=6, value=stock_data["王祎"]["271-365"])
            sh.cell(row=31, column=8, value=stock_data["王祎"]["365+"])
            
            sh.cell(row=32, column=2, value=stock_data["化一博"]["91-180"])
            sh.cell(row=32, column=4, value=stock_data["化一博"]["181-270"])
            sh.cell(row=32, column=6, value=stock_data["化一博"]["271-365"])
            sh.cell(row=32, column=8, value=stock_data["化一博"]["365+"])
        else:
            sh.cell(row=31, column=1, value=date_str)
            sh.cell(row=31, column=4, value=total_sales)
            sh.cell(row=31, column=7, value=new_p39)
            sh.cell(row=31, column=10, value=new_u39)
            
            sh.cell(row=32, column=1, value=date_str)
            sh.cell(row=32, column=4, value=hyb_sales)
            sh.cell(row=32, column=7, value=new_p39 - new_p40)
            sh.cell(row=32, column=10, value=new_u39 - new_u40)
            
    fill_support_sheet("Sheet5", False)
    fill_support_sheet("Sheet3", False)
    fill_support_sheet("Sheet1", False)
    
    fill_support_sheet("Sheet6", True)
    fill_support_sheet("Sheet4", True)
    fill_support_sheet("Sheet2", True)
    
    wb.save(filepath)
    wb.close()
    print("Excel saved.")

def recalculate_formulas(filepath):
    import win32com.client
    abs_path = os.path.abspath(filepath)
    print(f"Recalculating formulas in {abs_path} via Excel COM...")
    excel = None
    try:
        excel = win32com.client.DispatchEx('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(abs_path)
        excel.CalculateFull()
        wb.Save()
        wb.Close(SaveChanges=True)
        print("Recalculation successful.")
    except Exception as e:
        print(f"Error recalculating Excel formulas: {e}")
        raise e
    finally:
        if excel:
            excel.Quit()

def generate_weekly_report_markdown(weekly_data, stock_data, date_str, doc_url):
    wy_sales = weekly_data["王祎"]["sales"]
    hyb_sales = weekly_data["化一博"]["sales"]
    tot_sales = wy_sales + hyb_sales
    
    wy_profit = weekly_data["王祎"]["profit"]
    hyb_profit = weekly_data["化一博"]["profit"]
    tot_profit = wy_profit + hyb_profit
    
    wy_acoas = -weekly_data["王祎"]["ads"] / wy_sales if wy_sales > 0 else 0.0
    hyb_acoas = -weekly_data["化一博"]["ads"] / hyb_sales if hyb_sales > 0 else 0.0
    tot_acoas = -(weekly_data["王祎"]["ads"] + weekly_data["化一博"]["ads"]) / tot_sales if tot_sales > 0 else 0.0

    tot_91 = stock_data["王祎"]["91-180"] + stock_data["化一博"]["91-180"]
    tot_181 = stock_data["王祎"]["181-270"] + stock_data["化一博"]["181-270"]
    tot_271 = stock_data["王祎"]["271-365"] + stock_data["化一博"]["271-365"]
    tot_365 = stock_data["王祎"]["365+"] + stock_data["化一博"]["365+"]

    md = f"""# 运营周会数据统计 - 南京欧洲站周报
**填报周期**：{date_str}

## 一、销售及广告数据 (Sales & Ads Data)
| 负责人 | 本周销售额 (Sales) | 本周利润 (Profit) | 本周 ACOAS |
| --- | --- | --- | --- |
| **王祎个人** | ${wy_sales:,.2f} | ${wy_profit:,.2f} | {wy_acoas*100:.2f}% |
| **化一博** | ${hyb_sales:,.2f} | ${hyb_profit:,.2f} | {hyb_acoas*100:.2f}% |
| **全组总计** | **${tot_sales:,.2f}** | **${tot_profit:,.2f}** | **{tot_acoas*100:.2f}%** |

## 二、FBA 库存库龄分布 (FBA Stock Age Distribution)
| 负责人 | 91-180天库龄 | 181-270天库龄 | 271-365天库龄 | 365天以上库龄 |
| --- | --- | --- | --- | --- |
| **王祎个人** | {stock_data["王祎"]["91-180"]} | {stock_data["王祎"]["181-270"]} | {stock_data["王祎"]["271-365"]} | {stock_data["王祎"]["365+"]} |
| **化一博** | {stock_data["化一博"]["91-180"]} | {stock_data["化一博"]["181-270"]} | {stock_data["化一博"]["271-365"]} | {stock_data["化一博"]["365+"]} |
| **全组总计** | **{tot_91}** | **{tot_181}** | **{tot_271}** | **{tot_365}** |

## 三、周会汇报材料附件 (Weekly Meeting Attachment)
📎 **[点此在线打开并下载最新周报 Excel]({doc_url})**
"""
    return md

def upload_and_send_dingtalk(filepath, target_user=None, target_group=None, date_str=""):
    print(f"Uploading file {filepath} to DingTalk drive...")
    cmd_upload = [r"d:\Zero Tools\DingTalk\bin\dws.exe", "drive", "upload", "-y", "--file", filepath]
    r = subprocess.run(cmd_upload, capture_output=True, check=True)
    res = json.loads(r.stdout.decode('utf-8'))
    doc_url = res["result"]["docUrl"]
    
    # 模拟生成漂亮的周报 Markdown 并附上链接
    # We will generate report using doc_url
    return doc_url

def main():
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    date_str = f"{start_date}至{end_date}"
    
    possible_paths = [
        r"d:\Zero Tools\data\运营周会数据统计-王祎-2026.6.29.xlsx",
        r"d:\Zero Tools\data\运营周会数据收集_王祎_v19_new.xlsx",
        r"C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据统计-王祎-2026.6.29.xlsx"
    ]
    
    excel_path = None
    for p in possible_paths:
        if os.path.exists(p):
            excel_path = p
            break
            
    dry_run = "--dry-run" in sys.argv or "--no-send" in sys.argv
    target_group = None
    target_user = None
    
    if len(sys.argv) > 1:
        if "--group" in sys.argv:
            target_group = "cidCtsmbs4Sk6ajOZQDMQl32w==" # 南京欧洲站￥$€£
            print("Mode: Group chat send")
        elif "--test" in sys.argv:
            target_user = "17566881508928543" # 王祎 User ID
            print("Mode: Test (Direct to Wang Yi)")
            
    # 1. 抓取数据
    weekly_profit = get_weekly_profit_data(start_date, end_date)
    fba_stock = get_fba_stock_data()
    
    # 2. 写入 Excel (如果模版文件存在)
    if excel_path and os.path.exists(excel_path):
        fill_excel_workbook(excel_path, weekly_profit, fba_stock, date_str)
        recalculate_formulas(excel_path)
    else:
        print("[INFO] 报表一模板文件暂未找到，已完成领星 MCP 数据抓取与逻辑验证。")

        
    if dry_run:
        print("[SUCCESS] [Dry-Run] 报表一《运营周报》数据拉取与计算逻辑验证成功（已跳过钉盘上传与消息发送）。")
        return


    # 3. 上传文件与发送消息
    if excel_path and os.path.exists(excel_path):
        doc_url = upload_and_send_dingtalk(excel_path)
        report_md = generate_weekly_report_markdown(weekly_profit, fba_stock, date_str, doc_url)
        
        dest_flag = []
        if target_user:
            dest_flag = ["--user", target_user]
        elif target_group:
            dest_flag = ["--group", target_group]
        else:
            dest_flag = ["--user", "17566881508928543"]
            
        cmd_send_msg = [r"d:\Zero Tools\DingTalk\bin\dws.exe", "chat", "message", "send", "-y"] + dest_flag + [
            "--title", "南京欧洲站运营周报",
            "--text", report_md
        ]
        subprocess.run(cmd_send_msg, check=True)
        print("Weekly report message sent successfully!")

if __name__ == "__main__":
    main()

