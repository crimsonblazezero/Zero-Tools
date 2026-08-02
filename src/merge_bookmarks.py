import os
import re
import time

# 输入输出路径
# Input and output paths
ORIGINAL_HTML_PATH = r"C:\Users\Administrator\Documents\favorites_2026_8_1.html"
CLEAN_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
MERGED_OUTPUT_HTML_PATH = r"C:\Users\Administrator\Desktop\favorites_merged.html"

# AIGC 相关的次级分类白名单
# Whitelist of sub-categories to export for AIGC only
AIGC_CATEGORIES = [
    "AIGC / 智能影音与视频生成",
    "AIGC / AI 图像与提示词工程",
    "AIGC / 智能 Agent 与自动化",
    "AIGC / 智能 PPT 与办公辅助",
    "AI 开发 / 代理与工具生态",
    "技术 / 开发与实用工具"
]

def generate_aigc_html_segment():
    """
    仅把 Markdown 中 AIGC 分类书签转换为 Netscape HTML 段落字符串
    Convert only AIGC category bookmarks in Markdown into a Netscape HTML segment string
    """
    if not os.path.exists(CLEAN_MD_PATH):
        print(f"[Error] Clean MD file not found: {CLEAN_MD_PATH}")
        return ""

    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    with open(CLEAN_MD_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_time = int(time.time())
    html_lines = []
    
    indent = "        "  # 保持与收藏夹栏下级目录一致的缩进 (Match indent of favorites bar subdirectories)
    in_target_folder = False

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        cat_match = category_pattern.match(line_str)
        if cat_match:
            folder_name = cat_match.group(1).strip()
            folder_name_clean = re.sub(r'\s*\(\d+\)\s*$', '', folder_name).strip()
            
            if folder_name_clean in AIGC_CATEGORIES:
                if in_target_folder:
                    html_lines.append(f"{indent}</DL><p>")
                
                # 创建 H3 文件夹，属于收藏夹栏的子文件夹
                # Create H3 folder node as child of favorites bar
                html_lines.append(f'{indent}<DT><H3 ADD_DATE="{current_time}" LAST_MODIFIED="{current_time}">{folder_name_clean}</H3>')
                html_lines.append(f"{indent}<DL><p>")
                in_target_folder = True
            else:
                if in_target_folder:
                    html_lines.append(f"{indent}</DL><p>")
                in_target_folder = False
            continue

        link_match = link_pattern.match(line_str)
        if link_match and in_target_folder:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            
            title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            url_escaped = url.replace('&', '&amp;')
            
            html_lines.append(f'{indent}    <DT><A HREF="{url_escaped}" ADD_DATE="{current_time}">{title_escaped}</A>')

    if in_target_folder:
        html_lines.append(f"{indent}</DL><p>")

    return "\n".join(html_lines)

def merge_bookmarks():
    """
    将生成的 AIGC 书签段落合并插入到用户原始备份 HTML 的“收藏夹栏”头部
    Merge and insert the generated AIGC bookmarks segment into the head of "收藏夹栏" in original backup HTML
    """
    if not os.path.exists(ORIGINAL_HTML_PATH):
        print(f"[Error] Original HTML backup file not found: {ORIGINAL_HTML_PATH}")
        return

    # 生成 AIGC 的 HTML 段落
    # Generate AIGC HTML segment
    aigc_segment = generate_aigc_html_segment()
    if not aigc_segment:
        print("[Error] Failed to generate AIGC HTML segment.")
        return

    # 读取原始备份 HTML
    # Read original HTML backup
    with open(ORIGINAL_HTML_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 定位“收藏夹栏”的起始 DL 标签
    # Locate the starting DL tag of "收藏夹栏" (PERSONAL_TOOLBAR_FOLDER="true")
    # 格式通常是: H3 ... PERSONAL_TOOLBAR_FOLDER="true">收藏夹栏</H3>\n    <DL><p>
    pattern = re.compile(r'(PERSONAL_TOOLBAR_FOLDER="true">.*?H3>\s*[\r\n]+\s*<DL><p>)', re.IGNORECASE)
    
    match = pattern.search(html_content)
    if not match:
        # 兜底匹配普通文件夹
        # Fallback to general DL match
        pattern = re.compile(r'(收藏夹栏.*?H3>\s*[\r\n]+\s*<DL><p>)', re.IGNORECASE)
        match = pattern.search(html_content)

    if match:
        insert_marker = match.group(1)
        # 在 <DL><p> 后面换行插入我们的 AIGC 分类段落
        # Insert the AIGC segments right after the <DL><p> tag
        new_content = html_content.replace(insert_marker, f"{insert_marker}\n{aigc_segment}")
        
        # 写入合并后的 HTML 文件
        # Write merged content to output file
        with open(MERGED_OUTPUT_HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("\n==================================================")
        print("[Done] 合并成功！")
        print(f"新合并的书签导入文件已生成在桌面: {MERGED_OUTPUT_HTML_PATH}")
        print("该文件保留了你原有的全部书签，同时在“收藏夹栏”最前部加入了整理后的 AIGC 次级分类。")
        print("==================================================")
    else:
        print("[Error] Could not locate the '收藏夹栏' folder inside the original HTML.")

if __name__ == "__main__":
    merge_bookmarks()
