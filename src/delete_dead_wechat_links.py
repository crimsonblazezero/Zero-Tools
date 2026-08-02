import os

# 目标文件路径
# Target file path
BOOKMARK_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview.md"

# 已经确认为死亡的微信链接
# WeChat URLs confirmed as deleted or blocked
DEAD_WECHAT_URLS = [
    "https://mp.weixin.qq.com/s/APyVIof7mYAvbEgZ6rGuLA",
    "https://mp.weixin.qq.com/s/7Ip0z6miGV_7BgJ-_1SPQA",
    "https://mp.weixin.qq.com/s/Zv9utRyEyAc0n1AGyfa_Ng",
    "https://mp.weixin.qq.com/s/awmS3PKPkX23AuV30nu5LA",
    "https://mp.weixin.qq.com/s/bAjBBN1hxXUpCH9xzspv-w",
    "https://mp.weixin.qq.com/s/5ZpobSQCfT3JW6G5lA7E9A"
]

def delete_dead_wechat_links():
    """
    从源 bookmark-overview.md 文件中直接剔除已被微信作者删除的文章链接
    Directly delete blocked/deleted WeChat links from the source bookmark-overview.md file
    """
    if not os.path.exists(BOOKMARK_PATH):
        print(f"[Error] File not found: {BOOKMARK_PATH}")
        return

    # 读取旧内容
    # Read old contents
    with open(BOOKMARK_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed_count = 0

    # 逐行过滤
    # Filter line by line
    for line in lines:
        should_keep = True
        for url in DEAD_WECHAT_URLS:
            if url in line:
                should_keep = False
                removed_count += 1
                print(f"[Removed] {line.strip()}")
                break
        if should_keep:
            new_lines.append(line)

    # 写入新内容覆盖原文件
    # Write back new contents to overwrite original file
    with open(BOOKMARK_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("\n==================================================")
    print(f"[Done] 处理完成！已从源文件中剔除 {removed_count} 个失效微信书签。")
    print(f"源文件已更新: {BOOKMARK_PATH}")
    print("==================================================")

if __name__ == "__main__":
    delete_dead_wechat_links()
