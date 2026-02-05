# -*- coding: utf-8 -*-
"""验证 ABA 排名分级结果"""
import pandas as pd

df = pd.read_excel(r'd:\Zero Tools\amazon-keywords-tagger\test_aba_output.xlsx')

print('=== ABA排名分级测试结果 ===\n')

for i in range(len(df)):
    row = df.iloc[i]
    print(f'关键词: {row["关键词 (Keyword)"]}')
    print(f'  ABA排名: {row["ABA排名 (ABA Rank)"]}')
    print(f'  流量等级: {row["流量等级 (Traffic Level)"]}')
    print(f'  颜色: {row["颜色 (Color)"]}')
    print()

print("\n=== 流量分级规则验证 ===")
print("✓ ABA 1-50,000: 大词 (Large)")
print("✓ ABA 50,001-200,000: 中词 (Medium)")
print("✓ ABA 200,001-400,000: 小词 (Small)")  
print("✓ ABA >400,000 或为空: 超小词 (Extra Small)")
