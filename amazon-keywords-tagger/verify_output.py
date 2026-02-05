# -*- coding: utf-8 -*-
"""验证输出结果"""
import pandas as pd

df = pd.read_excel(r'd:\Zero Tools\amazon-keywords-tagger\output_result.xlsx')

print('=== 关键词分析结果示例 ===\n')

examples = [0, 1, 2, 6, 11]
for i in examples:
    row = df.iloc[i]
    print(f'关键词: {row["关键词 (Keyword)"]}')
    print(f'  核心词根: {row["核心词根 (Core Root)"]}')
    print(f'  流量等级: {row["流量等级 (Traffic Level)"]}')
    print(f'  颜色: {row["颜色 (Color)"]}')
    print(f'  尺寸: {row["尺寸 (Size)"]}')
    print(f'  材质: {row["材质 (Material)"]}')
    print(f'  场景: {row["场景 (Scenario)"]}')
    print()
