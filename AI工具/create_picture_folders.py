import pandas as pd
import os
import re
from tkinter import filedialog, Tk

def clean_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', str(name))

def batch_create_folders():
    root = Tk()
    root.withdraw()
    # 强制置顶弹窗，防止它躲在后面
    root.attributes("-topmost", True)
    
    print("正在等待选择 Excel 文件...")
    excel_file = filedialog.askopenfilename(title="选择Excel文件", filetypes=[("Excel files", "*.xlsx *.xls")])
    
    if not excel_file:
        print("未选择文件，退出。")
        return

    print("正在等待选择保存位置...")
    base_output_path = filedialog.askdirectory(title="选择保存位置")
    
    if not base_output_path:
        print("未选择位置，退出。")
        return

    try:
        df = pd.read_excel(excel_file)
        spu_column = 'SPU品名'
        msku_column = 'MSKU'
        
        if spu_column not in df.columns or msku_column not in df.columns:
            print(f"错误：列名对不上！你的表头里必须有 '{spu_column}' 和 '{msku_column}'")
            return

        print(f"\n开始在: {base_output_path} 生成文件夹...")
        count = 0
        for _, row in df.iterrows():
            spu = clean_filename(row[spu_column]).strip()
            msku = clean_filename(row[msku_column]).strip()
            
            if spu == 'nan' or not spu: continue
            
            target_path = os.path.join(base_output_path, spu, msku)
            os.makedirs(target_path, exist_ok=True)
            count += 1
            print(f"[{count}] 已创建: {spu} / {msku}")
            
        print("\n--- 全部任务完成！ ---")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    batch_create_folders()
    input("\n按回车键关闭窗口...")
