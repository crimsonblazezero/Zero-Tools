
import pandas as pd
import os

files = [
    "d:\\Zero Tools\\VC-SC 库存表-2025.8.4.xlsx",
    "d:\\Zero Tools\\欧洲广告分析表8.3.xlsx"
]

output_file = "d:\\Zero Tools\\report_analysis.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for f in files:
        out.write(f"\n{'='*50}\n")
        out.write(f"ANALYZING: {os.path.basename(f)}\n")
        out.write(f"{'='*50}\n")
        
        try:
            xl = pd.ExcelFile(f)
            out.write(f"Sheet Names: {xl.sheet_names}\n")
            
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                out.write(f"\n[Sheet: {sheet}] Info:\n")
                out.write(f"Shape: {df.shape}\n")
                out.write("Columns:\n")
                for col in df.columns:
                    out.write(f"  - {col}\n")
                
                out.write("\nFirst row sample:\n")
                # Write first row as dict to see values
                if not df.empty:
                    first_row = df.iloc[0].to_dict()
                    for k, v in first_row.items():
                        out.write(f"  {k}: {v}\n")
        
        except Exception as e:
            out.write(f"ERROR reading {f}: {e}\n")
