
import pandas as pd
import os

files = [
    "d:\\Zero Tools\\Test\\全仓明细详情信息-878063387337490432.xlsx",
    "d:\\Zero Tools\\Test\\若驰家居-深圳组-LingFei-DE-DE等2个店铺的广告活动报告-汇总-878062778654949376.xlsx"
]

output_file = "d:\\Zero Tools\\test_file_analysis.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for f in files:
        out.write(f"\n{'='*50}\n")
        out.write(f"ANALYZING: {os.path.basename(f)}\n")
        out.write(f"{'='*50}\n")
        
        try:
            # Check file extension to decide engine
            if f.endswith('.csv'):
                df = pd.read_csv(f)
                out.write("\n[CSV File] Info:\n")
                out.write(f"Shape: {df.shape}\n")
                out.write("Columns:\n")
                for col in df.columns:
                    out.write(f"  - {col}\n")
            else:
                xl = pd.ExcelFile(f)
                out.write(f"Sheet Names: {xl.sheet_names}\n")
                
                for sheet in xl.sheet_names:
                    df = xl.parse(sheet)
                    out.write(f"\n[Sheet: {sheet}] Info:\n")
                    out.write(f"Shape: {df.shape}\n")
                    out.write("Columns:\n")
                    for col in df.columns:
                        out.write(f"  - {col}\n")
                    
                    # Preview first row keys/values to identify specific inventory columns
                    if not df.empty:
                        out.write("\nFirst row sample:\n")
                        first_row = df.iloc[0].to_dict()
                        for k, v in first_row.items():
                            out.write(f"  {k}: {v}\n")
        
        except Exception as e:
            out.write(f"ERROR reading {f}: {e}\n")
