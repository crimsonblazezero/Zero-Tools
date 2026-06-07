import os
import re
import traceback
import pandas as pd
from pypdf import PdfReader
import tkinter as tk
from tkinter import filedialog

def select_folder():
    """唤起系统弹窗选择文件夹"""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="第一步：请选择存放 PDF 标签的文件夹")
    return folder_path

def select_mapping_file():
    """唤起系统弹窗选择Excel或CSV文件"""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="第二步：请选择 SKU 映射表 (Excel/CSV)",
        filetypes=[("表格文件", "*.xlsx *.xls *.csv")]
    )
    return file_path

def main():
    try:
        print("====================================")
        print("  FNSKU 自动重命名工具 (精准匹配版)")
        print("====================================\n")

        # 1. 交互式选择路径
        print("正在唤起文件夹选择窗口...")
        pdf_folder = select_folder()
        if not pdf_folder:
            print("[操作取消] 你没有选择存放PDF的文件夹。")
            return

        print("正在唤起表格选择窗口...")
        excel_path = select_mapping_file()
        if not excel_path:
            print("[操作取消] 你没有选择SKU映射表。")
            return

        print(f"\n[设定完成]")
        print(f"PDF 目录: {pdf_folder}")
        print(f"映射表格: {excel_path}\n")

        # 2. 兼容读取 CSV 和 Excel
        try:
            if excel_path.lower().endswith('.csv'):
                try:
                    df = pd.read_csv(excel_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(excel_path, encoding='gbk')
            else:
                df = pd.read_excel(excel_path)
                
            mapping = dict(zip(df['FNSKU'].astype(str).str.strip(), df['SKU'].astype(str).str.strip()))
            print(f"成功加载映射表，共读取到 {len(mapping)} 条匹配规则。\n")
        except Exception as e:
            print(f"[读取表格失败] 请检查表头是否包含 FNSKU 和 SKU 两个英文字母列名。")
            print(f"详细报错: {e}")
            return

        # 3. 执行核心重命名逻辑
        success_count = 0
        for filename in os.listdir(pdf_folder):
            if not filename.lower().endswith('.pdf'):
                continue
                
            pdf_path = os.path.join(pdf_folder, filename)
            extracted_text = ""
            
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    # 提取文本并清除可能存在的多余换行符
                    extracted_text += page.extract_text().replace('\n', '') + " "
            except Exception as e:
                print(f"[跳过] 无法读取 {filename}，文件可能损坏。")
                continue
                
            # 【修复核心】: 去掉 {7,} 的逗号，强制精准抓取 10 位 (X00 + 7位大写字母/数字)
            match = re.search(r'(X00[A-Z0-9]{7})', extracted_text)
            if not match:
                print(f"❌ [跳过] {filename} : 未检测到标准的10位 FNSKU。抓取到的原始文本片段：{extracted_text[:30]}...")
                continue
                
            fnsku = match.group(1)
            
            if fnsku in mapping:
                sku = mapping[fnsku]
                new_filename = f"{sku}.pdf"
                new_pdf_path = os.path.join(pdf_folder, new_filename)
                
                if os.path.exists(new_pdf_path):
                    print(f"⚠️ [冲突] {new_filename} 已存在，跳过覆盖。")
                    continue
                    
                os.rename(pdf_path, new_pdf_path)
                print(f"✅ {filename} -> {new_filename} (提取到: {fnsku})")
                success_count += 1
            else:
                print(f"❌ {filename} (精准提取到: {fnsku}): 表格中未找到匹配项。")
                
        print(f"\n====================================")
        print(f"运行结束！共成功重命名 {success_count} 个文件。")
        print(f"====================================")

    except Exception as e:
        print("\n" + "!"*40)
        print("[程序崩溃] 发生未知错误，详情如下：")
        traceback.print_exc()
        print("!"*40)

    finally:
        input("\n请按回车键 (Enter) 退出程序...")

if __name__ == "__main__":
    main()