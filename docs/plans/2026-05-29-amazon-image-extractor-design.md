# 亚马逊图片链接批量提取程序设计方案 (Amazon Image Link Extractor Design)

本设计方案旨在构建一个能够稳定、批量地从亚马逊各站点商品详情页提取主图 1-8 链接的程序。程序通过**模拟真实浏览器 (Browser Automation)** 以及**人机协同 (Human-in-the-loop)** 机制，彻底规避亚马逊严苛的反爬虫限制。

---

## 1. 业务背景与价值 (Business Context & Value)

*   **市场趋势 (Market Trends)**：欧美家居装饰市场极度依赖高质量场景图与细节图。通过批量分析竞品主图策略，有助于快速进行视觉策略规划。
*   **用户痛点 (User Pain Points)**：人工保存竞品图片效率低，且常规静态爬虫（如 `requests`）抓取极易触发亚马逊验证码。
*   **视觉差异化 (Visual Differentiation)**：利用提取的高清链接，设计团队可进行视觉拼图（Mood Board）对比，助力 KovaScape 的视觉差异化设计。

---

## 2. 系统架构与文件结构 (System Architecture & Workspace Structure)

程序严格遵循项目的目录规范进行组织：

```text
d:/KovaScape Tools/
├── src/
│   └── amazon_image_extractor.py     # 核心 Python 脚本
├── data/
│   ├── asin_list.xlsx                # 输入的 ASIN 与站点列表 Excel
│   └── amazon_images_result.xlsx     # 输出的图片链接结果 Excel
├── docs/
│   └── plans/
│       └── 2026-05-29-amazon-image-extractor-design.md  # 本设计方案
└── requirements.txt                  # 项目依赖文件
```

### 核心组件划分 (Core Components)

1.  **输入读取器 (Input Reader)**：读取 `data/asin_list.xlsx`，支持获取 `ASIN` 及其对应的 `Marketplace`（如 `US`, `UK`, `DE`, `JP` 等）。
2.  **浏览器控制器 (Browser Controller)**：利用 `Playwright` 启动 Headed (有头) 浏览器，使用 `playwright-stealth` 混淆自动化指纹。
3.  **图片链接解析器 (Image Parser)**：注入 JS 执行读取 `window.colorImages` 变量，提取高清图 URL，并通过正则表达式过滤和转换出无损原图。
4.  **数据导出器 (Data Exporter)**：将提取的数据整理为 DataFrame，通过 `pandas` 与 `openpyxl` 导出为美观的 Excel 报表。

---

## 3. 核心逻辑设计 (Core Logic Design)

### 3.1 域名与 URL 拼接映射 (Domain Mapping)
程序支持多站点，站点与域名的映射关系如下：
*   `US` -> `amazon.com`
*   `UK` -> `amazon.co.uk`
*   `DE` -> `amazon.de`
*   `FR` -> `amazon.fr`
*   `IT` -> `amazon.it`
*   `ES` -> `amazon.es`
*   `JP` -> `amazon.co.jp`
*   `CA` -> `amazon.ca`

### 3.2 亚马逊图片 JSON 解析算法 (Image JSON Parsing)
在详情页加载完成后，程序在浏览器上下文中执行：
```javascript
let data = window.colorImages || (window.ImageBlockATF && window.ImageBlockATF.colorImages);
if (!data) {
    // 降级匹配逻辑：寻找包含 colorImages 的 Script 标签并正则解析
    const scripts = Array.from(document.querySelectorAll('script'));
    for (let script of scripts) {
        if (script.textContent.includes('colorImages')) {
            // 正则提取 {} 内的 JSON 字符串
            const match = script.textContent.match(/'colorImages':\s*({.+?}),\n/);
            if (match) {
                data = JSON.parse(match[1]);
                break;
            }
        }
    }
}
return JSON.stringify(data);
```

### 3.3 图片 URL 规范化 (URL Normalization)
亚马逊图片 URL 包含尺寸配置（如 `https://images-na.ssl-images-amazon.com/images/I/71xyz%2B123L._AC_US40_.jpg`）。
程序使用正则表达式匹配 `._[A-Z0-9_]+_(?=\.[a-z]+$)` 并将其删除，还原为无损大图（例如：`https://images-na.ssl-images-amazon.com/images/I/71xyz%2B123L.jpg`）。

---

## 4. 容错与防反爬设计 (Error Handling & Anti-Scraping)

### 4.1 人机协同机制 (Human-in-the-Loop)
*   **触发条件**：页面标题为 `"Robot Check"` 或 URL 包含 `validateCaptcha`，或找不到核心页面元素且页面存在 `captcha` 关键字。
*   **处理逻辑**：脚本在终端输出显眼的红色高亮警报，程序进入 `time.sleep` 轮询等待（每秒检测一次页面是否已成功加载商品标题 `#productTitle`）。
*   **恢复逻辑**：用户在弹出的浏览器界面上手动完成验证码后，程序检测到商品标题出现，自动结束等待，继续运行。

### 4.2 变狗与下架处理 (Dog of Amazon / Product Unavailable)
*   **识别标识**：页面包含“变狗”的标志性元素（如 `id="d"`、`id="dogImage"` 或标题包含 `"Page Not Found"`）。
*   **处理逻辑**：在 Excel 的图片链接列写入 `"商品已下架/变狗 (Unavailable)"`，跳过该 ASIN，继续处理下一个。

---

## 5. 依赖包说明 (Dependencies)

在 `requirements.txt` 中需要确保包含以下包：
```text
playwright>=1.40.0
playwright-stealth>=0.1.6
pandas>=2.0.0
openpyxl>=3.1.0
```
*(注：首次运行程序前需要执行 `playwright install chromium` 安装 Playwright 自带的浏览器内核)*
