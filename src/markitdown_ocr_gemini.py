"""
markitdown-ocr + Google AI Studio (Gemini) 使用示例
=====================================================
- Gemini API 完全兼容 OpenAI 接口格式
- 免费 Key 来自: https://aistudio.google.com/apikey
- 推荐模型: gemini-2.0-flash (免费额度最高，支持视觉)

用途: 从 PDF/Word/Excel/PPT 中提取图片内的文字 (OCR)
"""

import os
from openai import OpenAI
from markitdown import MarkItDown

# ============================================================
# 配置区：把你的 Google AI Studio Key 填在这里
# 获取地址: https://aistudio.google.com/apikey
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "在这里填入你的Key")

# 创建 OpenAI 兼容客户端（指向 Gemini 接口）
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 初始化 MarkItDown（启用 OCR 插件 + Gemini Vision）
md = MarkItDown(
    enable_plugins=True,          # 启用 markitdown-ocr 插件
    llm_client=client,            # 使用 Gemini 客户端
    llm_model="gemini-2.0-flash", # 免费额度大，支持图像识别
    # 可选: 自定义 OCR 提示词
    # llm_prompt="请提取图片中的所有文字，保留表格结构。",
)

# ============================================================
# 使用示例
# ============================================================

def convert_file(input_path: str, output_path: str = None):
    """将文件转换为 Markdown（含图片 OCR）"""
    print(f"正在转换: {input_path}")
    result = md.convert(input_path)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        print(f"已保存到: {output_path}")
    else:
        print(result.text_content)

    return result.text_content


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python markitdown_ocr_gemini.py <文件路径> [输出.md]")
        print("")
        print("示例:")
        print("  python markitdown_ocr_gemini.py 报告.pdf output.md")
        print("  python markitdown_ocr_gemini.py 含图片的合同.docx")
        print("  python markitdown_ocr_gemini.py 数据表.xlsx output.md")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        convert_file(input_file, output_file)
