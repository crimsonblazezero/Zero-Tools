---
name: amazon-video-downloader
description: "从 Amazon 下载竞品主图视频。当用户需要批量下载 Amazon 商品页面的主图视频、通过 ASIN 列表批量处理、或采集竞品视频内容时使用此技能。支持美国、英国、德国等多站点，使用 Playwright 浏览器自动化和 yt-dlp 下载视频。"
---

# Amazon 视频下载器技能

从 Amazon 商品页面批量下载主图视频的工具。

## 快速开始

### 前置要求

- Python 3.8+
- Playwright（`pip install playwright`，然后运行 `playwright install chromium`）
- yt-dlp（`pip install yt-dlp`）
- requests、beautifulsoup4、lxml、tqdm（`pip install requests beautifulsoup4 lxml tqdm`）

### 基本用法

```bash
# 从 ASIN 列表文件批量下载（推荐）
python scripts/download_amazon_video.py --asin-list sample_asins.txt --output ./videos --headless --verbose

# 单个 ASIN 下载
python scripts/download_amazon_video.py --asin B0DPFZMPZT --output ./videos --headless

# 指定 Amazon 站点（默认是美国站）
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region com --headless
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region co.uk --headless  # 英国站
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region de --headless   # 德国站
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-a, --asin-list FILE` | ASIN 列表文件（每行一个 ASIN） | 无 |
| `-o, --output DIR` | 视频输出目录 | `./videos` |
| `-r, --region REGION` | Amazon 站点区域 | `com`（美国站） |
| `--max-videos N` | 每个 ASIN 最多下载 N 个视频 | 3 |
| `--delay N` | 每个 ASIN 之间的延迟（秒） | 2 |
| `--headless` | 无头模式运行浏览器 | False |
| `--verbose` | 详细日志输出 | False |
| `--dry-run` | 只提取视频链接，不下载 | False |

## ASIN 列表文件格式

每行一个 ASIN（Amazon 标准识别号码），支持 # 开头的注释行：

```
# 这是注释行
B0DPFZMPZT  # 可以带注释
B08F3XTW1G
B0BSF4C67F
```

## 输出文件

运行后会在输出目录生成：

```
videos/
├── B0DPFZMPZT_video_1.mp4   # 下载的视频文件
├── B0DPFZMPZT_video_2.mp4
├── B0DPFZMPZT_snapshot.html  # 页面 HTML 快照（用于调试）
└── download_report.csv          # 下载报告（CSV 格式）
```

## 工作原理

1. **读取 ASIN 列表** → 解析文件，跳过注释和空行
2. **访问 Amazon 商品页面** → 使用 Playwright 无头浏览器加载页面
3. **提取视频 URL** → 从页面 HTML 快照中用正则提取 `https://m.media-amazon.com/images/S/.../productVideoOptimized.mp4` 格式的视频 URL
4. **下载视频** → 使用 yt-dlp 下载视频文件到本地
5. **生成报告** → 输出 CSV 报告记录每个 ASIN 的处理结果

## 常见问题

### 问题1：没有找到视频

- 确认 ASIN 是否正确（10位字符）
- 确认 Amazon 站点区域是否匹配（美国站的 ASIN 在英国站可能不存在）
- 检查 `snapshot.html` 文件，看是否页面加载成功
- 有些商品可能没有主图视频

### 问题2：下载失败

- 检查网络连接
- 尝试增加 `--delay` 参数值，避免被 Amazon 反爬
- 检查 yt-dlp 是否安装正确：`yt-dlp --version`

### 问题3：页面返回 404

- ASIN 可能已下架或不存在
- 尝试更换 `--region` 参数（可能不是美国站的 ASIN）

## 进阶用法

### 使用 requests 版本（更快但可能被反爬）

```bash
python download.py --asin-list asins.txt --output ./videos --dry-run
```

### 只提取视频链接，不下载

```bash
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --dry-run --headless
```

## 注意事项

1. **尊重 robots.txt** - 请遵守 Amazon 的 robots.txt 和使用条款
2. **避免频繁请求** - 使用 `--delay` 参数控制请求频率，避免 IP 被封
3. **仅用于合规用途** - 仅用于竞品分析、市场调研等合规商业用途
4. **视频版权** - 下载的视频仅供个人分析使用，请勿用于商业传播

## 故障排除

如果脚本运行出错，可以：

1. 查看 `download_report.csv` 了解每个 ASIN 的处理结果
2. 查看 `snapshot.html` 了解页面加载情况
3. 使用 `--verbose` 参数查看详细日志
4. 尝试不使用 `--headless` 参数，观察浏览器实际运行情况

## 相关文件

- `scripts/download_amazon_video.py` - Playwright 浏览器自动化版本（推荐）
- `references/usage.md` - 更详细的使用指南
