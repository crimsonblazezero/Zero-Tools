import os
import re
import time

# 配置输入输出路径
# Configuration paths
INPUT_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
OUTPUT_HTML_PATH = r"C:\Users\Administrator\Desktop\edge-bookmarks-import.html"

def md_to_netscape_html(md_path, html_path):
    """
    将带有文件夹目录结构的 Markdown 转换成标准的 Netscape HTML 书签导入文件
    Convert Markdown with category directories to standard Netscape HTML Bookmarks import file
    """
    if not os.path.exists(md_path):
        print(f"[Error] Markdown file not found: {md_path}")
        return

    # 正则表达式
    # Regular expressions
    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    h1_pattern = re.compile(r'^#\s*(.*?)\s*$')

    # 读取 MD 行数
    # Read MD lines
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
    in_folder = False

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # 匹配 H1 (作为根目录标题，跳过或记作主目录)
        # Match H1
        if h1_pattern.match(line_str):
            continue

        # 匹配二级标题作为文件夹分类: ## 文件夹名称
        # Match H2 titles as directory folders: ## Folder Name
        cat_match = category_pattern.match(line_str)
        if cat_match:
            folder_name = cat_match.group(1).strip()
            # 清洗掉后面的数量标识，例如 "其他 / 待确认 (321)" -> "其他 / 待确认"
            # Clean up trailing counts, e.g. "Folder (321)" -> "Folder"
            folder_name = re.sub(r'\s*\(\d+\)\s*$', '', folder_name)
            
            # 如果上一个文件夹没闭合，先闭合它
            # Close previous DL block if it exists
            if in_folder:
                html_lines.append(f"{indent}</DL><p>")
                in_folder = False
            
            # 创建文件夹节点
            # Create folder node
            html_lines.append(f'{indent}<DT><H3 ADD_DATE="{current_time}" LAST_MODIFIED="{current_time}">{folder_name}</H3>')
            html_lines.append(f"{indent}<DL><p>")
            in_folder = True
            continue

        # 匹配书签项: - [标题](链接)
        # Match link items: - [Title](URL)
        link_match = link_pattern.match(line_str)
        if link_match:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            
            # 逸出 HTML 敏感字符，防止导入失败
            # Escape HTML characters to prevent import errors
            title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            url_escaped = url.replace('&', '&amp;')
            
            # 若没在任何二级标题下，则作为顶级书签直接写入
            # Write as top-level bookmark if not inside an H2 folder
            cur_indent = indent * 2 if in_folder else indent
            html_lines.append(f'{cur_indent}<DT><A HREF="{url_escaped}" ADD_DATE="{current_time}">{title_escaped}</A>')

    # 循环结束后闭合未关闭的 DL 块
    # Close any open blocks at the end
    if in_folder:
        html_lines.append(f"{indent}</DL><p>")
    
    html_lines.append("</DL><p>")

    # 写入 HTML 文件
    # Write to HTML output file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_lines))

    print("\n==================================================")
    print(f"[Done] 转换完成！")
    print(f"生成的 Edge 导入文件: {html_path}")
    print("==================================================")

if __name__ == "__main__":
    md_to_netscape_html(INPUT_MD_PATH, OUTPUT_HTML_PATH)
