import asyncio
import re
import os
import random
import sys
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup

# 配置路径与参数
# Configuration paths and parameters
BOOKMARK_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview.md"
CLEAN_OUTPUT_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
REPORT_OUTPUT_PATH = r"C:\Users\Administrator\Desktop\bookmark-cleanup-report.md"

MAX_CONCURRENT_REQUESTS = 10  # 限制最大并发，防止触发平台反爬 (Limit concurrency to avoid anti-scraping)
TIMEOUT_SECONDS = 12          # HTTP 请求超时设置 (HTTP request timeout)

# 微信删帖/违规的特征词
# Signature keywords for deleted or blocked WeChat articles
WECHAT_DEAD_KEYWORDS = [
    "此内容因违规无法查看",
    "已被作者删除",
    "该内容已被发布者删除",
    "内容已被作者删除",
    "此内容因违"
]

# 亚马逊商品变狗或不可用的特征词与页面模式
# Signature patterns for suppressed/dog Amazon product pages
AMAZON_DEAD_PATTERNS = [
    "Sorry! We couldn't find that page",
    "The Web address you entered is not a functioning page",
    "d-landing-dog",
    "dog.html"
]

# 常见浏览器请求头，避免被识别为机器人
# Common browser User-Agents to prevent bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

class BookmarkCleaner:
    def __init__(self, filepath):
        self.filepath = filepath
        self.bookmarks = []      # 存储结构：[(title, url, category, line_no)] (Storage structure)
        self.categories = []     # 所有的分类 (All categories found)
        self.duplicates = []     # 重复的书签 (Duplicate bookmarks)
        self.dead_links = []     # 失效书签 (Dead bookmarks)
        self.valid_links = []    # 有效书签 (Valid bookmarks)
        self.seen_urls = set()   # 去重集合 (Set for de-duplication)

    def parse_markdown(self):
        """
        解析 Markdown 文件提取书签和对应的分类
        Parse the Markdown file to extract bookmarks and their categories
        """
        if not os.path.exists(self.filepath):
            print(f"[Error] File not found: {self.filepath}")
            sys.exit(1)

        current_category = "未分类 (Uncategorized)"
        
        # 匹配 Markdown 格式的链接: - [标题](链接)
        # Match Markdown links: - [Title](URL)
        link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
        
        # 匹配二级标题作为分类: ## 分类名
        # Match H2 titles as categories: ## Category Name
        category_pattern = re.compile(r'^##\s*(.*?)\s*$')

        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                cat_match = category_pattern.match(line)
                if cat_match:
                    current_category = cat_match.group(1).strip()
                    continue
                
                link_match = link_pattern.match(line)
                if link_match:
                    title = link_match.group(1).strip()
                    url = link_match.group(2).strip()
                    
                    # 检查是否重复
                    # Check for duplicates
                    normalized_url = url.split('?')[0].rstrip('/')  # 忽略查询参数进行基本去重
                    if normalized_url in self.seen_urls:
                        self.duplicates.append({
                            "title": title,
                            "url": url,
                            "category": current_category,
                            "line": line_no
                        })
                    else:
                        self.seen_urls.add(normalized_url)
                        self.bookmarks.append({
                            "title": title,
                            "url": url,
                            "category": current_category,
                            "line": line_no
                        })

        print(f"解析完成！共提取到 {len(self.bookmarks) + len(self.duplicates)} 个书签 (去重前)。")
        print(f"已过滤出 {len(self.duplicates)} 个重复书签，剩余 {len(self.bookmarks)} 个待检测网页。")

    async def check_single_url(self, session, semaphore, item):
        """
        检测单个 URL 的有效性
        Check the validity of a single URL
        """
        title = item["title"]
        url = item["url"]
        category = item["category"]
        
        # 随机延迟，防止高并发引起 IP 限制
        # Add random delay to mitigate rate limiting
        await asyncio.sleep(random.uniform(0.1, 0.4))
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Referer": "https://www.google.com/"
        }

        async with semaphore:
            try:
                # 使用 timeout 并允许重定向
                # Use timeout and allow redirects
                timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
                async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True) as response:
                    # 检查 HTTP 状态码
                    # Check HTTP status code
                    if response.status >= 400:
                        reason = f"HTTP {response.status}"
                        item["status"] = "dead"
                        item["reason"] = reason
                        self.dead_links.append(item)
                        print(f"[-] 失效 ({reason}): {title} -> {url}")
                        return

                    # 检查微信/亚马逊等特定网页的内容是否失效
                    # Check body content for platform-specific dead pages (WeChat/Amazon)
                    html_content = await response.text(errors='ignore')
                    
                    # 1. 微信链接判定
                    # 1. WeChat Link validation
                    if "mp.weixin.qq.com" in url:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        # 查找微信提示词
                        # Check for WeChat block keywords
                        text_content = soup.get_text()
                        for keyword in WECHAT_DEAD_KEYWORDS:
                            if keyword in text_content:
                                item["status"] = "dead"
                                item["reason"] = f"微信文章已删除 ({keyword})"
                                self.dead_links.append(item)
                                print(f"[-] 失效 (微信删帖): {title}")
                                return
                    
                    # 2. 亚马逊链接判定
                    # 2. Amazon Link validation
                    if any(domain in url for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
                        # 检查 URL 是否被重定向到 dog 页，或者内容包含变狗关键词
                        # Check redirection to dog page or presence of dead patterns
                        final_url = str(response.url)
                        if "dog.html" in final_url or any(pattern in html_content for pattern in AMAZON_DEAD_PATTERNS):
                            item["status"] = "dead"
                            item["reason"] = "亚马逊Listing变狗/失效 (Product Suppressed)"
                            self.dead_links.append(item)
                            print(f"[-] 失效 (亚马逊变狗): {title}")
                            return

                    # 3. 正常存活
                    # 3. Mark as valid
                    item["status"] = "valid"
                    self.valid_links.append(item)

            except asyncio.TimeoutError:
                item["status"] = "dead"
                item["reason"] = "连接超时 (Timeout)"
                self.dead_links.append(item)
                print(f"[-] 失效 (超时): {title}")
            except Exception as e:
                item["status"] = "dead"
                item["reason"] = f"请求错误 ({type(e).__name__})"
                self.dead_links.append(item)
                print(f"[-] 失效 (报错): {title} -> {type(e).__name__}")

    async def run_checker(self):
        """
        启动异步批量连接检测器
        Start asynchronous bulk connection checking
        """
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_single_url(session, semaphore, item) for item in self.bookmarks]
            await asyncio.gather(*tasks)

    def write_results(self):
        """
        将清洗后的有效书签和失效报告写入文件
        Write clean bookmarks and cleanup report to files
        """
        # 1. 整理有效书签，保持原有目录结构
        # 1. Structure valid bookmarks keeping original categories
        valid_by_category = {}
        for item in self.valid_links:
            cat = item["category"]
            if cat not in valid_by_category:
                valid_by_category[cat] = []
            valid_by_category[cat].append(item)

        # 写入干净的书签文件
        # Write clean bookmark file
        with open(CLEAN_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(f"# 书签总览 (已清洗)\n\n")
            f.write(f"共 {len(self.valid_links)} 个有效书签 (原 {len(self.bookmarks) + len(self.duplicates)} 个，已过滤失效与重复)\n\n")
            
            # 按原有分类输出
            # Output in original categories
            for cat, items in valid_by_category.items():
                f.write(f"## {cat} ({len(items)})\n\n")
                for item in items:
                    f.write(f"- [{item['title']}]({item['url']})\n")
                f.write("\n")

        # 2. 写入清理报告文件
        # 2. Write cleanup report file
        with open(REPORT_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write("# 📂 浏览器书签清洗整理报告\n\n")
            f.write("## 📊 统计看板 (Statistics)\n\n")
            f.write("| 指标 (Metric) | 数量 (Count) | 比例 (Ratio) |\n")
            f.write("| :--- | :--- | :--- |\n")
            total = len(self.bookmarks) + len(self.duplicates)
            f.write(f"| 原始书签总数 (Total Original) | {total} | 100% |\n")
            f.write(f"| **有效保留书签** (Valid Kept) | {len(self.valid_links)} | {len(self.valid_links)/total:.1%} |\n")
            f.write(f"| **失效直接删除** (Dead Links) | {len(self.dead_links)} | {len(self.dead_links)/total:.1%} |\n")
            f.write(f"| **重复合并书签** (Duplicates) | {len(self.duplicates)} | {len(self.duplicates)/total:.1%} |\n\n")
            
            f.write("---\n\n")
            f.write("## ❌ 建议删除的失效书签清单 (Dead Links - Safe to Delete)\n")
            f.write("可以直接在收藏夹里将以下链接批量剔除：\n\n")
            
            dead_by_reason = {}
            for item in self.dead_links:
                reason = item["reason"]
                if reason not in dead_by_reason:
                    dead_by_reason[reason] = []
                dead_by_reason[reason].append(item)
                
            for reason, items in dead_by_reason.items():
                f.write(f"### 📍 {reason} ({len(items)} 个)\n")
                for item in items:
                    f.write(f"- **[{item['category']}]** [{item['title']}]({item['url']})\n")
                f.write("\n")

            f.write("---\n\n")
            f.write("## 🌀 重复书签合并清单 (Duplicate Bookmarks)\n")
            f.write("以下书签已被去重过滤，如需要可人工核对：\n\n")
            for item in self.duplicates:
                f.write(f"- **[{item['category']}]** [{item['title']}]({item['url']})\n")

        print("\n==================================================")
        print(f"[Done] 清洗完成！")
        print(f"1. 干净的书签已写入: {CLEAN_OUTPUT_PATH}")
        print(f"2. 清洗统计报告已写入: {REPORT_OUTPUT_PATH}")
        print("==================================================")

def main():
    cleaner = BookmarkCleaner(BOOKMARK_PATH)
    cleaner.parse_markdown()
    
    print("\n开始并发检测连接有效性，请稍候...")
    asyncio.run(cleaner.run_checker())
    
    cleaner.write_results()

if __name__ == "__main__":
    main()
