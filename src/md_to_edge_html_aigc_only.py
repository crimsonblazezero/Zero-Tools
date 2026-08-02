import os
import re
import time

# 配置输入输出路径
# Configuration paths
INPUT_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
OUTPUT_HTML_PATH = r"C:\Users\Administrator\Desktop\edge-aigc-bookmarks-only.html"

# 仅导入 AIGC 相关的次级分类白名单
# Whitelist of sub-categories to export for AIGC only
AIGC_CATEGORIES = [
    "AIGC / 智能影音与视频生成",
    "AIGC / AI 图像与提示词工程",
    "AIGC / 智能 Agent 与自动化",
    "AIGC / 智能 PPT 与办公辅助",
    "AI 开发 / 代理与工具生态",
    "技术 / 开发与实用工具"
]

def md_to_netscape_html_aigc_only(md_path, html_path):
    """
    仅提取 Markdown 中的 AIGC 文件夹，转换成标准的 Netscape HTML 书签导入文件
    Extract only the AIGC folders from the Markdown file and convert them to Netscape HTML format
    """
    if not os.path.exists(md_path):
        print(f"[Error] Markdown file not found: {md_path}")
        return

    # 正则表达式
    # Regular expressions
    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_time = int(time.time())

    # HTML 标头声明 (Netscape Bookmark File 1 标准)
    # Netscape Bookmark Header declaration
    html_lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "<!-- This is an automatically generated file.",
        "     It will be read and written.",
        "     DO NOT EDIT! -->",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>"
    ]

    indent = "    "
    in_target_folder = False

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # 匹配二级标题作为文件夹分类: ## 文件夹名称
        # Match H2 titles as directory folders: ## Folder Name
        cat_match = category_pattern.match(line_str)
        if cat_match:
            folder_name = cat_match.group(1).strip()
            # 过滤数量后缀，例如 "AIGC / 智能影音与视频生成 (13)" -> "AIGC / 智能影音与视频生成"
            # Strip trailing count, e.g. "Folder (13)" -> "Folder"
            folder_name_clean = re.sub(r'\s*\(\d+\)\s*$', '', folder_name).strip()
            
            # 检查是否属于我们白名单的 AIGC 类别
            # Check if this category is in the AIGC whitelist
            if folder_name_clean in AIGC_CATEGORIES:
                # 如果前一个文件夹没闭合，先闭合它
                if in_target_folder:
                    html_lines.append(f"{indent}</DL><p>")
                
                # 创建新文件夹
                # Create folder node
                html_lines.append(f'{indent}<DT><H3 ADD_DATE="{current_time}" LAST_MODIFIED="{current_time}">{folder_name_clean}</H3>')
                html_lines.append(f"{indent}<DL><p>")
                in_target_folder = True
            else:
                # 遇到非白名单文件夹，闭合之前的文件夹，并设置状态为 False
                # If non-whitelisted, close previous folder and set state to False
                if in_target_folder:
                    html_lines.append(f"{indent}</DL><p>")
                in_target_folder = False
            continue

        # 匹配书签项: - [标题](链接)
        # Match link items: - [Title](URL)
        link_match = link_pattern.match(line_str)
        if link_match and in_target_folder:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            
            title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            url_escaped = url.replace('&', '&amp;')
            
            html_lines.append(f'{indent * 2}<DT><A HREF="{url_escaped}" ADD_DATE="{current_time}">{title_escaped}</A>')

    # 闭合未关闭的 DL 块
    # Close any open blocks
    if in_target_folder:
        html_lines.append(f"{indent}</DL><p>")
    
    html_lines.append("</DL><p>")

    # 写入 HTML 文件
    # Write to HTML output file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_lines))

    print("\n==================================================")
    print(f"[Done] 仅 AIGC 的 HTML 转换完成！")
    print(f"生成的 Edge 导入文件: {html_path}")
    print("==================================================")

if __name__ == "__main__":
    md_to_netscape_html_aigc_only(INPUT_MD_PATH, OUTPUT_HTML_PATH)
