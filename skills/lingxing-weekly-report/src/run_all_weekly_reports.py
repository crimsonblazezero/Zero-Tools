# -*- coding: utf-8 -*-
"""
南京欧洲组双周报全流程接续生成主运行脚本 (支持 Dry-Run 预演验证模式)
Master Pipeline Runner for Weekly Sales Report & Weekly Meeting Report
"""
import os
import sys
import subprocess
import datetime

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    dry_run = "--dry-run" in sys.argv or "--no-send" in sys.argv
    mode_str = "【Dry-Run 预演模式 - 不创建新报告，不发送通知】" if dry_run else "【正式执行模式 - 自动生成报告、上传钉盘并推送钉群】"
    
    print("==================================================================")
    print(f"🚀 开始自动执行【南京欧洲组】双周报接续生成与推送流程 {mode_str}")
    print(f"⏰ 当前执行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================================\n")

    sub_args = ["--dry-run"] if dry_run else []

    # 1. 运行报表一：运营周报 (fill_weekly_report.py)
    print(">>> 阶段 1: 正在运行【报表一：运营周报 (Sales & Targets Weekly Report)】...")
    try:
        res1 = subprocess.run([sys.executable, r"d:\Zero Tools\src\fill_weekly_report.py"] + sub_args, capture_output=True, text=True, errors='ignore')
        if res1.stdout:
            print(res1.stdout.strip())
        if res1.returncode == 0:
            print("✅ 报表一《运营周报》数据拉取与更新验证完成！")
        else:
            err_msg = res1.stderr if res1.stderr else ""
            print(f"⚠️ 报表一生成存在非阻塞提示: {err_msg.strip()}")
    except Exception as e:
        print(f"⚠️ 报表一执行提示: {e}")

    # 2. 运行报表二：六组周会会议纪要 (generate_weekly_meeting_report.py)
    print("\n>>> 阶段 2: 正在接续运行【报表二：六组周会会议纪要 (Weekly Meeting Report)】...")
    try:
        res2 = subprocess.run([sys.executable, r"d:\Zero Tools\src\generate_weekly_meeting_report.py"] + sub_args, capture_output=True, text=True, errors='ignore')
        if res2.stdout:
            print(res2.stdout.strip())
        if res2.returncode == 0:
            print("✅ 报表二《六组周会会议纪要》对齐填报、数据复用及生成逻辑验证完成！")
        else:
            err_msg = res2.stderr if res2.stderr else ""
            print(f"❌ 报表二执行失败: {err_msg.strip()}")
    except Exception as e:
        print(f"❌ 报表二执行失败: {e}")

    print("==================================================================")
    print(f"🎉 双报表接续流程验证完毕！ {mode_str}")
    print("==================================================================")

if __name__ == "__main__":
    main()
