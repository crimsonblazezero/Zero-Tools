# -*- coding: utf-8 -*-
"""
验证相框产品规则脚本 (Verify Frame Product Rules)
"""
from keyword_analyzer import KeywordAnalyzer

analyzer = KeywordAnalyzer()

# 测试用例 (Test Cases)
test_cases = [
    # 1. 中文翻译 & 尺寸 (CN Name & Size)
    ("8x10 picture frame", "8x10", "8x10相框"),
    ("poster frames 24x36", "24x36", "24x36海报框架"),
    ("A4 certificate frame", "a4", "a4证书框"),
    ("picture frame", "other", "相框"),
    
    # 2. 颜色 (Color)
    ("gold picture frame", "gold"),
    ("rustic brown wood frame", "brown"),
    
    # 3. 产品类型 (Product Type)
    ("collage frames for wall", "组合/拼贴"),
    ("gallery wall set", "墙面装饰"),
    ("puzzle frame 1000 pieces", "拼图"),
    ("christmas picture ornament", "节日特定"),
    
    # 4. 搜索意图 (Search Intent)
    ("picture frame for living room", "装修决策期"),
    ("cheap bulk frames", "比价采购期"),
    ("how to hang frames", "安装使用期"),
    ("modern farmhouse decor", "风格搭配期"),
    
    # 5. 品牌 (Brand)
    ("IKEA picture frame", "【竞品品牌】"),
    ("KovaScape wall frame", "【自有品牌】"),
    ("generic photo frame", "【无品牌】"),
]

print("=== 规则验证开始 (Verification Start) ===\n")

for case in test_cases:
    keyword = case[0]
    result = analyzer.analyze_keyword(keyword)
    
    print(f"关键词: {keyword}")
    
    # 验证逻辑
    if len(case) == 3: # 验证中文名和尺寸
        expected_size = case[1]
        expected_cn = case[2]
        print(f"  尺寸: {result['size']} (预期: {expected_size}) -> {'✓' if result['size'] == expected_size else '❌'}")
        print(f"  中文: {result['cn_name']} (预期: {expected_cn}) -> {'✓' if result['cn_name'] == expected_cn else '❌'}")
        
    elif "gold" in case[0] or "brown" in case[0]: # 验证颜色
        expected_color = case[1]
        print(f"  颜色: {result['color']} (预期: {expected_color}) -> {'✓' if result['color'] == expected_color else '❌'}")
        
    elif "collage" in case[0] or "gallery" in case[0] or "puzzle" in case[0] or "christmas" in case[0]: # 验证类型
        expected_type = case[1]
        print(f"  类型: {result['product_type']} (预期: {expected_type}) -> {'✓' if result['product_type'] == expected_type else '❌'}")
        
    elif "living room" in case[0] or "cheap" in case[0] or "hang" in case[0] or "modern" in case[0]: # 验证意图
        expected_intent = case[1]
        print(f"  意图: {result['search_intent']} (预期: {expected_intent}) -> {'✓' if result['search_intent'] == expected_intent else '❌'}")
        
    elif "IKEA" in case[0] or "KovaScape" in case[0] or "generic" in case[0]: # 验证品牌
        expected_brand = case[1]
        print(f"  品牌: {result['brand_type']} (预期: {expected_brand}) -> {'✓' if result['brand_type'] == expected_brand else '❌'}")
    
    print("-" * 40)

print("\n=== 验证结束 (Verification End) ===")
