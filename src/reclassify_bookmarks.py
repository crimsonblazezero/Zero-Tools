import os
import re

# 文件路径
# File paths
CLEAN_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
ORIGINAL_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview.md"

# 定义细分归类规则字典 (名称/URL关键字 -> 目标次级分类)
# Sub-category mapping dict (Name/URL keyword -> Target sub-category)
CLASSIFICATION_RULES = {
    # 1. AIGC / 智能影音与视频生成 (AI Video & Audio)
    "OpenMontage": "AIGC / 智能影音与视频生成",
    "remotion": "AIGC / 智能影音与视频生成",
    "ViMax": "AIGC / 智能影音与视频生成",
    "Deep-Live-Cam": "AIGC / 智能影音与视频生成",
    "videocut-skills": "AIGC / 智能影音与视频生成",
    "clipsketch-ai": "AIGC / 智能影音与视频生成",
    "FullVideoProductionSkill": "AIGC / 智能影音与视频生成",
    "daily-bookcast": "AIGC / 智能影音与视频生成",
    "VibeVoice": "AIGC / 智能影音与视频生成",
    "VoxCPM": "AIGC / 智能影音与视频生成",
    "Qwen3-TTS": "AIGC / 智能影音与视频生成",
    "lossless-cut": "AIGC / 智能影音与视频生成",
    "Youtube-clipper-skill": "AIGC / 智能影音与视频生成",

    # 2. AIGC / AI 图像与提示词工程 (AI Image & Prompting)
    "Awesome-Nano-Banana-images": "AIGC / AI 图像与提示词工程",
    "awesome-nano-banana": "AIGC / AI 图像与提示词工程",
    "awesome-nanobanana-pro": "AIGC / AI 图像与提示词工程",
    "Snaplex": "AIGC / AI 图像与提示词工程",

    # 3. AIGC / 智能 Agent 与自动化 (AI Agents & Bots)
    "Agent-Reach": "AIGC / 智能 Agent 与自动化",
    "dexter": "AIGC / 智能 Agent 与自动化",
    "agency-agents": "AIGC / 智能 Agent 与自动化",
    "clawdbot-feishu": "AIGC / 智能 Agent 与自动化",
    "MemU": "AIGC / 智能 Agent 与自动化",
    "BSC-Amazon-OPC-Agent-OS": "AIGC / 智能 Agent 与自动化",
    "scope-recall-hermes": "AIGC / 智能 Agent 与自动化",
    "ChatLab": "AIGC / 智能 Agent 与自动化",
    "AIMedia": "AIGC / 智能 Agent 与自动化",

    # 4. AIGC / 智能 PPT 与办公辅助 (AI Office & PPT)
    "codex-ppt-skill": "AIGC / 智能 PPT 与办公辅助",
    "PPTAgent": "AIGC / 智能 PPT 与办公辅助",
    "dashi-ppt-skill": "AIGC / 智能 PPT 与办公辅助",
    "planners-ppt-hell": "AIGC / 智能 PPT 与办公辅助",
    "ian-handdrawn-ppt": "AIGC / 智能 PPT 与办公辅助",

    # 5. AI 开发 / 代理与工具生态 (AI Dev Tools & MCP)
    "codebase-memory-mcp": "AI 开发 / 代理与工具生态",
    "mcps.live": "AI 开发 / 代理与工具生态",
    "learn-claude-code": "AI 开发 / 代理与工具生态",
    "9router": "AI 开发 / 代理与工具生态",
    "antigravity-proxy": "AI 开发 / 代理与工具生态",
    "moonkite-skills": "AI 开发 / 代理与工具生态",
    "Antigravity-Manager": "AI 开发 / 代理与工具生态",
    "vibe-kanban": "AI 开发 / 代理与工具生态",
    "awesome-claude-skills": "AI 开发 / 代理与工具生态",
    "khazix-skills": "AI 开发 / 代理与工具生态",
    "beads": "AI 开发 / 代理与工具生态",
    "skill-from-masters": "AI 开发 / 代理与工具生态",
}

# 兜底分类
# Fallback sub-category
FALLBACK_CATEGORY = "技术 / 开发与实用工具"

def reclassify_file(filepath):
    """
    解析指定 Markdown 文件，重构代码托管分类
    Parse markdown file and restructure the Code Hosting category
    """
    if not os.path.exists(filepath):
        return False

    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    new_sections = []
    
    current_category = ""
    in_code_hosting_section = False
    
    # 临时收集代码托管栏目里的链接
    # Temporarily collect links in the Code Hosting section
    code_hosting_links = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 第一次遍历：解析出普通部分与待拆分代码托管部分
    # First pass: parse general sections and code hosting section
    for line in lines:
        line_str = line.strip()
        cat_match = category_pattern.match(line_str)
        
        if cat_match:
            cat_name = cat_match.group(1).strip()
            # 过滤掉原先的数量标识，例如 "代码托管 (60)" -> "代码托管"
            cat_name_clean = re.sub(r'\s*\(\d+\)\s*$', '', cat_name)
            
            if "代码托管" in cat_name_clean:
                in_code_hosting_section = True
            else:
                in_code_hosting_section = False
                new_sections.append({"type": "category", "content": line})
            continue

        link_match = link_pattern.match(line_str)
        if link_match:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            if in_code_hosting_section:
                code_hosting_links.append({"title": title, "url": url})
            else:
                new_sections.append({"type": "link", "content": line})
        else:
            # 包含 H1 标题和空行等其他非书签行
            # Other non-bookmark lines like H1 titles and blank lines
            if not in_code_hosting_section:
                new_sections.append({"type": "other", "content": line})

    # 第二次遍历：将代码托管栏目的书签分配到细分子分类下
    # Second pass: allocate code hosting bookmarks to sub-categories
    sub_categories = {
        "AIGC / 智能影音与视频生成": [],
        "AIGC / AI 图像与提示词工程": [],
        "AIGC / 智能 Agent 与自动化": [],
        "AIGC / 智能 PPT 与办公辅助": [],
        "AI 开发 / 代理与工具生态": [],
        "技术 / 开发与实用工具": []
    }

    for link in code_hosting_links:
        title = link["title"]
        url = link["url"]
        
        matched_cat = None
        # 根据关键字进行匹配
        # Match using keywords
        for key, target_cat in CLASSIFICATION_RULES.items():
            if key.lower() in title.lower() or key.lower() in url.lower():
                matched_cat = target_cat
                break
        
        if not matched_cat:
            matched_cat = FALLBACK_CATEGORY
            
        sub_categories[matched_cat].append(link)

    # 组装输出文本内容
    # Reassemble markdown lines
    output_lines = []
    
    # 查找原代码托管栏目的替换位置并重构写入
    # Locate replacement index and inject reconstructed sub-categories
    for section in new_sections:
        if section["type"] == "other" and "# 书签总览" in section["content"]:
            # 在顶部附加新的指示
            output_lines.append(section["content"].rstrip())
            continue
        
        # 针对总数描述行进行正则修正
        if "个有效书签" in section["content"]:
            output_lines.append(section["content"].rstrip())
            # 在总数说明下面，把我们细化出的 6 个分类插进去
            for sub_cat, items in sub_categories.items():
                if not items:
                    continue
                output_lines.append(f"\n## {sub_cat} ({len(items)})\n")
                for item in items:
                    output_lines.append(f"- [{item['title']}]({item['url']})")
            continue
            
        output_lines.append(section["content"].rstrip('\r\n'))

    # 写回文件
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines) + "\n")
        
    print(f"成功重构并覆写文件: {filepath}")
    return True

def main():
    print("开始重分类 AIGC/Github 书签项目...")
    
    # 重构干净的书签文件
    success_clean = reclassify_file(CLEAN_MD_PATH)
    
    # 重构原始的书签文件 (如果存在)
    if os.path.exists(ORIGINAL_MD_PATH):
        reclassify_file(ORIGINAL_MD_PATH)
        
    if success_clean:
        print("\n分类写入成功！正在重新编译 Edge HTML 导入文件...")
        # 导入 md_to_edge_html.py 里的函数来同步生成 HTML
        # Import HTML conversion function to sync HTML outputs
        try:
            from md_to_edge_html import md_to_netscape_html
            md_to_netscape_html(CLEAN_MD_PATH, r"C:\Users\Administrator\Desktop\edge-bookmarks-import.html")
        except Exception as e:
            print(f"[Warning] Failed to generate HTML: {e}")
            
        print("\n==================================================")
        print("[Done] AIGC 书签次级分类重分类完成！")
        print("==================================================")
    else:
        print("[Error] 无法重分类，文件不存在。")

if __name__ == "__main__":
    main()
