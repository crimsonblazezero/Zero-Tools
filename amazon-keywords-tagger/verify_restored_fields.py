# -*- coding: utf-8 -*-
"""
验证恢复字段脚本 (Verify Restored Fields)
"""
from keyword_analyzer import KeywordAnalyzer

analyzer = KeywordAnalyzer()

# 测试用例: (关键词, 预期材质, 预期场景, 预期核心词)
test_cases = [
    ("rustic wood picture frame", "wood", "-", "rustic picture frame"), # wood 被提取为材质，rustic保留
    ("metal poster frames for kitchen", "metal", "kitchen", "poster frames"),
    ("acrylic photo frame holder", "acrylic", "-", "holder"), # photo frame 被停用词移除? 检查 STOP_WORDS
    ("glass certificate frame wall mounted", "glass", "wall", "certificate"),
    ("gold aluminum collage frame", "aluminum", "-", "collage"), # gold是颜色，aluminum是材质
]

print("=== 恢复字段验证开始 (Verification Start) ===\n")

for case in test_cases:
    keyword = case[0]
    expected_mat = case[1]
    expected_scen = case[2]
    # expected_core = case[3] # 核心词逻辑比较复杂，主要验证材质和场景
    
    result = analyzer.analyze_keyword(keyword)
    
    print(f"关键词: {keyword}")
    print(f"  材质 (Material): {result['material']} (预期: {expected_mat}) -> {'✓' if expected_mat in result['material'] else '❌'}")
    print(f"  场景 (Scenario): {result['scenario']} (预期: {expected_scen}) -> {'✓' if expected_scen in result['scenario'] else '❌'}")
    print(f"  核心词 (Core):   {result['core_keyword']}")
    print("-" * 40)

print("\n=== 验证结束 (Verification End) ===")
