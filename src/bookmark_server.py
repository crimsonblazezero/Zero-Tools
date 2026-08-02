import os
import re
import json
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# 配置路径
# Configuration paths
CLEAN_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview-clean.md"
ORIGINAL_MD_PATH = r"C:\Users\Administrator\Desktop\bookmark-overview.md"

PORT = 8000

# 默认分流分类
# Default routing categories
DEFAULT_CATEGORIES = [
    "跨境运营 (Cross-border Ops)",
    "AI开发 (AI & Dev)",
    "设计素材 (Design Assets)",
    "个人生活 (Personal Life)"
]

def load_bookmarks_from_md():
    """
    从干净的 MD 文件中解析出“待确认”分类的书签
    Parse the bookmarks under the "待确认" category from the clean MD file
    """
    if not os.path.exists(CLEAN_MD_PATH):
        print(f"[Error] Clean MD file not found: {CLEAN_MD_PATH}")
        return [], []

    # 匹配分类和链接的正则
    # Regex to match categories and links
    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    all_categories = []
    to_verify_bookmarks = []
    
    current_category = ""
    
    with open(CLEAN_MD_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            cat_match = category_pattern.match(line.strip())
            if cat_match:
                current_category = cat_match.group(1).strip()
                # 剔除数量后缀，例如 "其他 / 待确认 (321)" -> "其他 / 待确认"
                current_category_clean = re.sub(r'\s*\(\d+\)\s*$', '', current_category)
                if current_category_clean not in all_categories:
                    all_categories.append(current_category_clean)
                continue
                
            link_match = link_pattern.match(line.strip())
            if link_match:
                title = link_match.group(1).strip()
                url = link_match.group(2).strip()
                
                # 如果是“待确认”分类下的书签，将其收集为待分拣列表
                # Collect as to-verify list if under the "待确认" category
                if "待确认" in current_category or "Other" in current_category:
                    to_verify_bookmarks.append({
                        "title": title,
                        "url": url,
                        "original_category": current_category
                    })

    # 合并预设的分类和原有的分类
    # Merge preset categories with parsed categories
    merged_categories = list(DEFAULT_CATEGORIES)
    for cat in all_categories:
        if "待确认" not in cat and cat not in merged_categories:
            merged_categories.append(cat)

    return to_verify_bookmarks, merged_categories

def save_bookmarks_to_md(sorted_data):
    """
    接收分拣结果，重构并覆写 Markdown 文件
    Receive sorting results, reconstruct and overwrite the Markdown file
    """
    # sorted_data 格式:
    # {
    #   "saved": [{"title": "xx", "url": "xx", "category": "分类"}, ...],
    #   "deleted": [{"title": "xx", "url": "xx"}, ...]
    # }
    
    if not os.path.exists(CLEAN_MD_PATH):
        return False

    # 1. 解析出除了“待确认”以外的其他书签
    # 1. Parse all bookmarks except the "待确认" category
    category_pattern = re.compile(r'^##\s*(.*?)\s*$')
    link_pattern = re.compile(r'^\s*-\s*\[(.*?)\]\((https?://.*?)\)')
    
    existing_bookmarks_by_cat = {}
    current_category = ""
    
    with open(CLEAN_MD_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            cat_match = category_pattern.match(line.strip())
            if cat_match:
                current_category = cat_match.group(1).strip()
                current_category_clean = re.sub(r'\s*\(\d+\)\s*$', '', current_category)
                if "待确认" not in current_category_clean:
                    existing_bookmarks_by_cat[current_category_clean] = []
                continue
                
            link_match = link_pattern.match(line.strip())
            if link_match:
                title = link_match.group(1).strip()
                url = link_match.group(2).strip()
                
                current_category_clean = re.sub(r'\s*\(\d+\)\s*$', '', current_category)
                if "待确认" not in current_category_clean:
                    existing_bookmarks_by_cat[current_category_clean].append({
                        "title": title,
                        "url": url
                    })

    # 2. 将用户刚归类好的书签并入对应的分类中
    # 2. Merge newly sorted bookmarks into their corresponding categories
    for item in sorted_data["saved"]:
        title = item["title"]
        url = item["url"]
        new_cat = item["category"]
        
        # 移出可能的数量后缀
        new_cat_clean = re.sub(r'\s*\(\d+\)\s*$', '', new_cat).strip()
        
        if new_cat_clean not in existing_bookmarks_by_cat:
            existing_bookmarks_by_cat[new_cat_clean] = []
        
        # 避免重复并入
        if not any(x["url"] == url for x in existing_bookmarks_by_cat[new_cat_clean]):
            existing_bookmarks_by_cat[new_cat_clean].append({
                "title": title,
                "url": url
            })

    # 3. 重新输出干净的 Markdown 文件
    # 3. Output the updated clean Markdown file
    total_valid = sum(len(items) for items in existing_bookmarks_by_cat.values())
    
    markdown_lines = [
        f"# 书签总览 (已清洗)\n",
        f"共 {total_valid} 个有效书签 (已过滤失效与重复，并完成分拣)\n"
    ]
    
    for cat, items in existing_bookmarks_by_cat.items():
        if not items:  # 跳过空文件夹 (Skip empty folders)
            continue
        markdown_lines.append(f"## {cat} ({len(items)})\n")
        for item in items:
            markdown_lines.append(f"- [{item['title']}]({item['url']})")
        markdown_lines.append("")

    with open(CLEAN_MD_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_lines))

    # 4. 同步更新原始的桌面文件，剔除已被用户标记删除的链接
    # 4. Sync updates to the original desktop file, removing URLs marked as deleted
    if os.path.exists(ORIGINAL_MD_PATH):
        deleted_urls = {item["url"] for item in sorted_data["deleted"]}
        with open(ORIGINAL_MD_PATH, 'r', encoding='utf-8') as f:
            orig_lines = f.readlines()
            
        new_orig_lines = []
        for line in orig_lines:
            # 检查是否有包含被删 URL 的行
            has_deleted_url = False
            for url in deleted_urls:
                if url in line:
                    has_deleted_url = True
                    break
            if not has_deleted_url:
                new_orig_lines.append(line)
                
        with open(ORIGINAL_MD_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_orig_lines)

    return True

class BookmarkRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 抑制请求日志，使终端控制台干净 (Suppress logs for clean console)
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/bookmarks':
            bookmarks, categories = load_bookmarks_from_md()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "bookmarks": bookmarks,
                "categories": categories
            }).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            sorted_data = json.loads(post_data.decode('utf-8'))
            
            success = save_bookmarks_to_md(sorted_data)
            
            self.send_response(200 if success else 500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

# 高端、富流动性微动美学的 HTML 单页确认看板模版
# Premium high-end web app template for bookmark verification
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KovaScape 书签确认看板 (Bookmark Verification Board)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@300;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #03120e;
            --emerald-deep: #062f27;
            --emerald-light: #0d4d40;
            --gold: #F3C546;
            --text-main: #f0f4f3;
            --text-muted: #8fa8a3;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 50% 50%, var(--emerald-deep) 0%, var(--bg-color) 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            overflow: hidden;
        }

        header {
            width: 100%;
            max-width: 1200px;
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 0%, var(--gold) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stats-badge {
            background: rgba(243, 197, 70, 0.1);
            border: 1px solid rgba(243, 197, 70, 0.2);
            padding: 8px 16px;
            border-radius: 99px;
            font-size: 14px;
            color: var(--gold);
            font-weight: 600;
        }

        /* 闪卡主容器 */
        .deck-container {
            position: relative;
            width: 550px;
            height: 380px;
            perspective: 1000px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* 闪卡基本样式 */
        .card {
            position: absolute;
            width: 100%;
            height: 100%;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(20px);
            border-radius: 28px;
            padding: 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
            transform-style: preserve-3d;
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease;
            cursor: pointer;
        }

        .card:hover {
            border-color: rgba(243, 197, 70, 0.3);
            box-shadow: 0 35px 70px rgba(0,0,0,0.7), 0 0 20px rgba(243,197,70,0.1), inset 0 1px 0 rgba(255,255,255,0.15);
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .category-tag {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .domain-tag {
            font-size: 13px;
            color: var(--gold);
            background: rgba(243, 197, 70, 0.08);
            padding: 4px 10px;
            border-radius: 6px;
        }

        .card-body {
            margin: 20px 0;
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 26px;
            line-height: 1.4;
            font-weight: 600;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .card-footer {
            font-size: 13px;
            color: var(--text-muted);
            border-top: 1px solid rgba(255,255,255,0.05);
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .hint-text {
            color: var(--gold);
            font-weight: 600;
        }

        /* 动画状态 */
        .card.swipe-left {
            transform: translate3d(-150%, 0, 0) rotate(-20deg);
            opacity: 0;
        }

        .card.swipe-right {
            transform: translate3d(150%, 0, 0) rotate(20deg);
            opacity: 0;
        }

        /* 控制区与操作提示 */
        .controls-wrapper {
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 24px;
            padding: 32px;
        }

        .keyhints {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
        }

        .keyhint {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 8px 14px;
            border-radius: 12px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .keyhint kbd {
            background: #fff;
            color: #000;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 800;
            font-size: 11px;
            box-shadow: 0 2px 0 rgba(0,0,0,0.2);
        }

        .action-btns {
            display: flex;
            gap: 16px;
        }

        .btn {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--text-main);
            padding: 12px 24px;
            border-radius: 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.2);
        }

        .btn-gold {
            background: var(--gold);
            color: #000;
            border: none;
        }

        .btn-gold:hover {
            background: #ffd966;
            box-shadow: 0 0 15px rgba(243, 197, 70, 0.4);
        }

        /* 进度条 */
        .progress-container {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.05);
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--gold) 0%, #fff 100%);
            width: 0%;
            transition: width 0.3s ease;
        }

        /* 完成提示 */
        .done-message {
            display: none;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            text-align: center;
        }

        .done-title {
            font-family: 'Outfit', sans-serif;
            font-size: 40px;
            font-weight: 800;
            color: var(--gold);
        }
    </style>
</head>
<body>
    <header>
        <h1>KovaScape 书签筛选 (Verification Board)</h1>
        <div id="stats" class="stats-badge">剩余: -- / --</div>
    </header>

    <!-- 闪卡主场景 -->
    <div id="deck" class="deck-container">
        <!-- 卡片动态渲染 -->
    </div>

    <!-- 完成屏幕 -->
    <div id="done-screen" class="done-message">
        <div class="done-title">🎉 分拣全部完成！</div>
        <p>你已经处理完这批所有的待确认书签，干得漂亮！</p>
        <div class="action-btns">
            <button class="btn btn-gold" onclick="saveData()">💾 立即同步保存至本地</button>
        </div>
    </div>

    <!-- 操控面板 -->
    <div class="controls-wrapper">
        <div class="keyhints">
            <div class="keyhint"><kbd>Space</kbd> <span>在新窗口中打开链接</span></div>
            <div class="keyhint" style="border-color: rgba(255,75,75,0.2)"><kbd>D</kbd> <span>标记删除</span></div>
            <div class="keyhint" style="border-color: rgba(253,197,70,0.2)"><kbd>Z</kbd> <span>撤销上一步</span></div>
        </div>
        <div id="cat-hints" class="keyhints">
            <!-- 类别键盘提示 -->
        </div>
        <div class="action-btns">
            <button class="btn" onclick="undo()"><kbd style="margin-right:4px;">Z</kbd> 撤销</button>
            <button class="btn btn-gold" onclick="saveData()">💾 保存同步</button>
        </div>
    </div>

    <div class="progress-container">
        <div id="progress" class="progress-bar"></div>
    </div>

    <script>
        let bookmarks = [];
        let categories = [];
        
        let currentIndex = 0;
        let savedItems = [];    // 已保存/分类的项
        let deletedItems = [];  // 标记删除的项
        
        let history = [];       // 操作历史，用于撤销 (Undo history)

        // 初始化加载数据
        async function loadData() {
            const res = await fetch('/api/bookmarks');
            const data = await res.json();
            bookmarks = data.bookmarks;
            categories = data.categories;
            
            renderCatHints();
            updateStats();
            renderCard();
        }

        // 渲染分类键盘映射提示
        function renderCatHints() {
            const container = document.getElementById('cat-hints');
            container.innerHTML = '';
            
            // 绑定前 9 个分类到快捷键 1-9
            categories.slice(0, 9).forEach((cat, index) => {
                const cleanName = cat.split(' ')[0];
                const hint = document.createElement('div');
                hint.className = 'keyhint';
                hint.innerHTML = `<kbd>${index + 1}</kbd> <span>归入 ${cleanName}</span>`;
                container.appendChild(hint);
            });
        }

        // 更新进度及统计
        function updateStats() {
            const stats = document.getElementById('stats');
            const total = bookmarks.length;
            const remaining = total - currentIndex;
            stats.innerText = `剩余: ${remaining} / 总数: ${total}`;
            
            const progress = document.getElementById('progress');
            const percent = total > 0 ? (currentIndex / total) * 100 : 0;
            progress.style.width = `${percent}%`;
        }

        // 渲染当前闪卡
        function renderCard() {
            const deck = document.getElementById('deck');
            deck.innerHTML = '';
            
            if (currentIndex >= bookmarks.length) {
                // 全部处理完毕，显示保存界面
                document.getElementById('deck').style.display = 'none';
                document.getElementById('done-screen').style.display = 'flex';
                return;
            }

            document.getElementById('deck').style.display = 'flex';
            document.getElementById('done-screen').style.display = 'none';

            const item = bookmarks[currentIndex];
            const urlObj = new URL(item.url);
            const domain = urlObj.hostname;

            const card = document.createElement('div');
            card.className = 'card';
            card.id = `card-${currentIndex}`;
            
            card.innerHTML = `
                <div class="card-top">
                    <span class="category-tag">待确认书签</span>
                    <span class="domain-tag">${domain}</span>
                </div>
                <div class="card-body">
                    <h2 class="card-title">${item.title}</h2>
                </div>
                <div class="card-footer">
                    <span>按 <span class="hint-text">Space</span> 打开网页</span>
                    <span>双击卡片也可直接打开</span>
                </div>
            `;

            // 双击打开链接
            card.addEventListener('dblclick', () => {
                window.open(item.url, '_blank');
            });

            deck.appendChild(card);
        }

        // 分类操作 (Category sort)
        function classify(catIndex) {
            if (currentIndex >= bookmarks.length) return;
            const category = categories[catIndex];
            const item = bookmarks[currentIndex];
            
            // 记录历史用于撤销
            history.push({
                index: currentIndex,
                action: 'save',
                item: { ...item, category: category }
            });
            
            savedItems.push({
                title: item.title,
                url: item.url,
                category: category
            });
            
            animateSwipe('swipe-right');
        }

        // 删除操作 (Delete item)
        function markDelete() {
            if (currentIndex >= bookmarks.length) return;
            const item = bookmarks[currentIndex];
            
            history.push({
                index: currentIndex,
                action: 'delete',
                item: item
            });
            
            deletedItems.push(item);
            animateSwipe('swipe-left');
        }

        // 撤销上一步操作 (Undo)
        function undo() {
            if (history.length === 0) return;
            
            const lastOp = history.pop();
            currentIndex = lastOp.index;
            
            if (lastOp.action === 'save') {
                savedItems = savedItems.filter(x => x.url !== lastOp.item.url);
            } else if (lastOp.action === 'delete') {
                deletedItems = deletedItems.filter(x => x.url !== lastOp.item.url);
            }
            
            updateStats();
            renderCard();
        }

        // 滑动卡片动画
        function animateSwipe(className) {
            const card = document.getElementById(`card-${currentIndex}`);
            if (card) {
                card.classList.add(className);
                setTimeout(() => {
                    currentIndex++;
                    updateStats();
                    renderCard();
                }, 300);
            } else {
                currentIndex++;
                updateStats();
                renderCard();
            }
        }

        // 保存同步到本地文件系统
        async function saveData() {
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    saved: savedItems,
                    deleted: deletedItems
                })
            });
            const result = await response.json();
            if (result.success) {
                alert('💾 书签已成功同步并写入你桌面的原始文件与清洗后的文件中！');
            } else {
                alert('❌ 保存失败，请检查终端报错。');
            }
        }

        // 键盘监听事件 (Keyboard shortcuts)
        window.addEventListener('keydown', (e) => {
            if (currentIndex >= bookmarks.length) return;
            
            const key = e.key.toLowerCase();
            
            if (e.code === 'Space' || key === ' ') {
                e.preventDefault();
                window.open(bookmarks[currentIndex].url, '_blank');
            } else if (key === 'd' || e.code === 'Delete') {
                markDelete();
            } else if (key === 'z') {
                undo();
            } else if (key >= '1' && key <= '9') {
                const idx = parseInt(key) - 1;
                if (idx < categories.length) {
                    classify(idx);
                }
            }
        });

        // 页面初始化
        loadData();
    </script>
</body>
</html>
"""

def main():
    print("==================================================")
    print("   KovaScape Bookmarks Verification Server")
    print("==================================================")
    
    # 预加载数据验证
    to_verify, cats = load_bookmarks_from_md()
    print(f"检测到“待确认”书签数量: {len(to_verify)} 个")
    print(f"可用分类目录: {', '.join(cats)}")
    
    if not to_verify:
        print("[Notice] 没有检测到“待确认”分类的书签，请检查 Desktop/bookmark-overview-clean.md")
        sys.exit(0)

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, BookmarkRequestHandler)
    
    # 自动打开浏览器
    url = f"http://localhost:{PORT}"
    print(f"\n正在本地启动确认看板: {url}")
    print("按下 Ctrl + C 可以随时关闭本地服务器并退出。")
    
    webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭本地确认服务器。退出成功！")
        sys.exit(0)

if __name__ == "__main__":
    main()
