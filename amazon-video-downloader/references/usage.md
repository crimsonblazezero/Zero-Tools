# Amazon 视频下载器 - 详细使用指南

## 安装依赖

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 安装 Python 依赖

```bash
pip install playwright beautifulsoup4 lxml tqdm yt-dlp
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

## 准备 ASIN 列表

ASIN（Amazon Standard Identification Number）是 Amazon 商品的唯一标识符，10位字符。

### 获取 ASIN 的方法

1. **从商品 URL 获取**：
   - URL 格式：`https://www.amazon.com/dp/B0DPFZMPZT`
   - ASIN 就是：`B0DPFZMPZT`

2. **从商品页面获取**：
   - 滚动到商品详情页底部
   - 在 "Product information" 部分找到 ASIN

### 创建 ASIN 列表文件

创建 `asins.txt`，每行一个 ASIN：

```
# 竞品视频分析 - 2026年6月
B0DPFZMPZT  # 主竞品
B08F3XTW1G
B0BSF4C67F
B0CX23V2Z2

# 新款产品
B0D1F5JQKX
B0CJ8V3K7Y
```

**注意**：
- `#` 开头的行为注释，会被忽略
- 行内 `#` 后面的内容也会被忽略
- 空行会被自动跳过

## 运行示例

### 示例1：基础批量下载

```bash
python scripts/download_amazon_video.py \
  --asin-list asins.txt \
  --output ./downloaded_videos \
  --headless \
  --verbose
```

### 示例2：指定 Amazon 站点

```bash
# 美国站（默认）
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region com --headless

# 英国站
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region co.uk --headless

# 德国站
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region de --headless

# 日本站
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region co.jp --headless

# 加拿大站
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --region ca --headless
```

### 示例3：限制每个 ASIN 下载数量

```bash
# 每个 ASIN 最多下载 1 个视频
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --max-videos 1 --headless

# 每个 ASIN 最多下载 5 个视频
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --max-videos 5 --headless
```

### 示例4：增加延迟避免反爬

```bash
# 每个 ASIN 之间延迟 5 秒
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --delay 5 --headless

# 每个 ASIN 之间延迟 10 秒（更保守）
python scripts/download_amazon_video.py --asin-list asins.txt --output ./videos --delay 10 --headless
```

### 示例5：Dry Run 模式（只提取链接不下载）

```bash
python scripts/download_amazon_video.py \
  --asin-list asins.txt \
  --output ./videos \
  --dry-run \
  --headless \
  --verbose
```

### 示例6：非无头模式（调试用）

```bash
# 可以看到浏览器实际操作过程
python scripts/download_amazon_video.py \
  --asin-list asins.txt \
  --output ./videos \
  --verbose
```

## 输出说明

### 成功下载的文件结构

```
downloaded_videos/
├── B0DPFZMPZT_video_1.mp4       # 第1个视频
├── B0DPFZMPZT_video_2.mp4       # 第2个视频
├── B0DPFZMPZT_snapshot.html      # 页面HTML快照（用于调试）
├── B0BSF4C67F_video_1.mp4
├── B0BSF4C67F_snapshot.html
├── download_report.csv             # 下载报告
└── run_log.txt                    # 运行日志（如果重定向输出）
```

### download_report.csv 格式

| 列名 | 说明 |
|------|------|
| asin | ASIN 编号 |
| status | 状态（success/failed/not_found/error） |
| video_count | 下载成功的视频数量 |
| video_urls | 找到的视频URL列表（JSON格式） |
| error_message | 错误信息（如果有） |
| timestamp | 处理时间戳 |

### 读取 CSV 报告

```python
import pandas as pd

df = pd.read_csv('downloaded_videos/download_report.csv')
print(df)
print(f"成功: {len(df[df['status'] == 'success'])}")
print(f"失败: {len(df[df['status'] == 'failed'])}")
```

## 故障排除

### 问题1：所有 ASIN 都返回 404

**可能原因**：
- ASIN 不正确或已下架
- Amazon 站点区域不匹配

**解决方法**：
```bash
# 1. 验证 ASIN 是否存在
# 在浏览器中访问：https://www.amazon.com/dp/B0DPFZMPZT

# 2. 尝试不同的区域
python scripts/download_amazon_video.py --asin B0DPFZMPZT --output ./videos --region com --headless
python scripts/download_amazon_video.py --asin B0DPFZMPZT --output ./videos --region co.uk --headless
```

### 问题2：找不到视频 URL

**可能原因**：
- 商品没有主图视频
- Amazon 返回了验证码页面
- 页面结构发生变化

**解决方法**：
```bash
# 1. 查看快照 HTML
cat downloaded_videos/B0DPFZMPZT_snapshot.html | grep -i "video"

# 2. 使用非无头模式观察
python scripts/download_amazon_video.py --asin B0DPFZMPZT --output ./videos

# 3. 检查是否被反爬
cat downloaded_videos/B0DPFZMPZT_snapshot.html | grep -i "robot\|captcha\|unusual traffic"
```

### 问题3：yt-dlp 下载失败

**可能原因**：
- yt-dlp 未正确安装
- 网络问题
- URL 格式不支持

**解决方法**：
```bash
# 1. 验证 yt-dlp 安装
yt-dlp --version

# 2. 手动测试下载
yt-dlp -o "test.mp4" "https://m.media-amazon.com/images/S/..."

# 3. 更新 yt-dlp
pip install --upgrade yt-dlp
```

### 问题4：Playwright 启动失败

**可能原因**：
- Playwright 浏览器未安装
- 系统依赖缺失（Linux）

**解决方法**：
```bash
# 1. 重新安装浏览器
playwright install chromium

# 2. Linux 上安装系统依赖
playwright install-deps chromium

# 3. 验证 Playwright 安装
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

## 性能优化

### 1. 使用 requests 版本（更快但不稳定）

```bash
# 对于少量 ASIN，可以尝试 requests 版本
python download.py --asin-list asins.txt --output ./videos --dry-run
```

### 2. 并发控制（高级）

修改脚本支持并发（需要修改代码）：

```python
# 在 download_browser.py 中添加并发逻辑
import asyncio
from asyncio import Semaphore

semaphore = Semaphore(3)  # 最多3个并发

async def process_asin_with_limit(asin):
    async with semaphore:
        await process_asin(asin)
```

## 合规建议

1. **遵守 robots.txt**：检查 Amazon 的 robots.txt 是否允许抓取
2. **控制请求频率**：使用 --delay 参数，建议 ≥ 2秒
3. **仅用于商业分析**：下载的视频仅用于竞品分析，不用于商业传播
4. **尊重版权**：Amazon 商品视频版权归原卖家所有
5. **使用代理（可选）**：对于大量下载，考虑使用代理IP

## 高级技巧

### 1. 定时批量下载（使用 cron/Launchd）

```bash
# Linux/Mac - 每天凌晨2点运行
# crontab -e
0 2 * * * cd /path/to/skill && python scripts/download_amazon_video.py --asin-list daily_asins.txt --output ./videos_$(date +\%Y\%m\%d) --headless
```

### 2. 与其他工具集成

```python
# 在 Python 中调用
import subprocess

result = subprocess.run([
    'python', 'scripts/download_amazon_video.py',
    '--asin-list', 'asins.txt',
    '--output', './videos',
    '--headless'
], capture_output=True, text=True)

print(result.stdout)
```

### 3. 解析下载报告生成摘要

```python
import pandas as pd
import json

df = pd.read_csv('downloaded_videos/download_report.csv')

print(f"总 ASIN 数: {len(df)}")
print(f"成功: {len(df[df['status'] == 'success'])}")
print(f"失败: {len(df[df['status'] == 'failed'])}")
print(f"未找到: {len(df[df['status'] == 'not_found'])}")

# 统计总视频数
total_videos = df['video_count'].sum()
print(f"总下载视频数: {total_videos}")
```
