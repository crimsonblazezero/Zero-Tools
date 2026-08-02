import os
import re

# 配置路径
# Configuration paths
CLEAN_INPUT_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
PROMPT_OUTPUT_PATH = r"C:\Users\Administrator\Desktop\copy-me-ai-prompt.txt"

def export_titles_and_prompt():
    """
    提取干净书签的标题，并组装成即用的 AI 提示词文件
    Extract clean bookmark titles and assemble them into a ready-to-use AI prompt file
    """
    if not os.path.exists(CLEAN_INPUT_PATH):
        print(f"[Error] Clean bookmark file not found: {CLEAN_INPUT_PATH}")
        return

    # 匹配 Markdown 格式链接的标题: - [标题](链接)
    # Match markdown link titles: - [Title](URL)
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    titles = []
    
    with open(CLEAN_INPUT_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            match = link_pattern.match(line)
            if match:
                title = match.group(1).strip()
                # 剔除可能包含敏感信息的标题字符（如特定 Token、ID 提示等进行简单清洗）
                # Clean up any potential sensitive information in titles
                title_clean = re.sub(r'(token|pass|key|sessionid)[a-zA-Z0-9_\-\=\+]+', '[SENSITIVE]', title, flags=re.IGNORECASE)
                titles.append(title_clean)

    # 组装精心调教的 AI 提示词
    # Assemble the carefully tuned AI prompt
    prompt_content = f"""你是一个高效的“个人知识与第二大脑管理专家”（Second Brain Expert）。

以下是我浏览器收藏夹清洗去重后剩下的 {len(titles)} 个有效书签标题。很多时候我收藏了就再也没看过，导致收藏夹沦为“焦虑的临时仓库”。请根据我刚才发你的文章方法论，帮我完成两项分拣工作：

### 🎯 任务一：三档分类 [必读 / 可读 / 建议删]
根据标题判断，将其分为以下三档：
1. **必读**：你判断我未来 3 个月内极有可能会用到、需立即付诸行动或学习的干货（如核心SOP、高频工具、正在处理的任务）。
2. **可读**：有一定价值、有兴趣但目前不急迫，可以留作闲暇浏览的备用内容。
3. **建议删**：那些可能已经过时、阶段性任务已结束、或纯粹属于“收藏了就以为学会了”的低频内容。
*要求*：每条书签仅给出标题和档位，不要给任何理由，以极简格式输出（例如：`- 标题名称 [必读]`），节省 Token。

### 📊 任务二：前 10 大焦虑主题聚类
分析这 {len(titles)} 个标题，找出我收藏夹中最核心的 10 个主题（如：跨境电商广告优化、3D设计素材、日语学习、影视娱乐等），并统计出这 10 个主题占总书签的比例。这能帮我认清“我到底在焦虑什么”。

### 🛠️ 任务三：提取“今天就能做的 10 件事”
从你判定为“必读”的书签里，挖出 10 条今天或这周就能开始执行的具体动作。不要空话，要具体的微小行动（例如：收藏的日语学习，对应的动作是“今晚背完10个新单词”；收藏的亚马逊广告，对应的动作是“明天上午下载上周的广告报表并清洗”）。

---

以下是我的书签标题列表：

"""
    # 拼接标题列表
    # Append the title list
    for idx, t in enumerate(titles, 1):
        prompt_content += f"{idx}. {t}\n"

    # 写入输出文件
    # Write to output file
    with open(PROMPT_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(prompt_content)

    print("\n==================================================")
    print(f"[Done] AI 提示词组装完成！")
    print(f"提示词已写入桌面: {PROMPT_OUTPUT_PATH}")
    print(f"里面已打包 {len(titles)} 个书签标题，直接复制并发送给你常用的 AI 即可！")
    print("==================================================")

if __name__ == "__main__":
    export_titles_and_prompt()
