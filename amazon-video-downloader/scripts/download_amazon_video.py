#!/usr/bin/env python3
"""
Amazon 竞品视频下载器 - Playwright 浏览器自动化版本 v3
=======================================================

修复内容 (v2 -> v3):
  - 修复 handle_response 过滤逻辑，去掉 vse-vms-transcoding 无用 URL
  - 修复 with open() 引号编码问题
  - 改进视频 URL 提取：优先用网络拦截的真实 MP4 URL
  - 自动点击视频缩略图触发播放，捕获真实视频流 URL
  - 对 blob URL 尝试通过 network interception 获取真实地址

用法：
  python download_browser.py --asin-list sample_asins.txt --output ./videos --headless
"""

import argparse
import asyncio
import csv
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse
import logging
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# 视频 URL 提取
# ─────────────────────────────────────────────────────────

async def extract_video_urls_from_page(page, asin: str) -> list:
    """从页面提取视频 URL（video 标签 + JS 变量扫描）"""
    videos = []

    # 方法 1: <video> 标签
    video_els = await page.query_selector_all("video source, video")
    for el in video_els:
        src = await el.get_attribute("src") or ""
        if src:
            videos.append({"video_url": src, "type": "video_tag", "selector": "video"})

    # 方法 2: JS 上下文扫描常见 Amazon 视频数据变量
    js_code = """
    () => {
        const results = [];
        const candidates = [
            'colorData', 'twisterData', 'imageData', 'mediaData',
            'dpVideoData', 'playbackUICoreData', 'vseData'
        ];
        for (const name of candidates) {
            try {
                const obj = window[name];
                if (obj) {
                    const urls = findUrls(obj);
                    results.push(...urls);
                }
            } catch(e) {}
        }
        // 扫描 window 下所有对象
        for (const key in window) {
            try {
                if (key.length > 30) continue;
                const val = window[key];
                if (val && typeof val === 'object' && !Array.isArray(val)) {
                    if (key.toLowerCase().includes('video') ||
                        key.toLowerCase().includes('media') ||
                        key.toLowerCase().includes('color')) {
                        const urls = findUrls(val);
                        results.push(...urls);
                    }
                }
            } catch(e) {}
        }
        return results;
    }

    function findUrls(obj, depth) {
        depth = depth || 0;
        const urls = [];
        if (depth > 4 || !obj || typeof obj !== 'object') return urls;
        for (const key in obj) {
            try {
                const val = obj[key];
                if (typeof val === 'string') {
                    if ((/video|m3u8|mp4|hls|streaming/i.test(key)) &&
                        (/^https?:\\/\\/[^\\s]+\\.(mp4|m3u8)/i.test(val) ||
                         /^https?:\\/\\/[^\\s]*(video|media)[^\\s]*/i.test(val))) {
                        urls.push({ key: key, url: val });
                    }
                } else if (typeof val === 'object') {
                    urls.push.apply(urls, findUrls(val, depth + 1));
                }
            } catch(e) {}
        }
        return urls;
    }
    """

    try:
        js_results = await page.evaluate(js_code)
        if js_results:
            for item in js_results:
                url = item.get("url", "")
                if url and not any(v["video_url"] == url for v in videos):
                    videos.append({
                        "video_url": url,
                        "type": "js_extracted",
                        "selector": "JS:" + str(item.get("key", "unknown")),
                    })
    except Exception as e:
        logger.debug("JS extraction failed: %s", e)

    # 方法 3: iframe
    iframes = await page.query_selector_all("iframe")
    for iframe in iframes:
        src = await iframe.get_attribute("src") or ""
        if src and ("video" in src.lower() or "prime" in src.lower() or "dpo" in src.lower()):
            videos.append({"video_url": src, "type": "iframe", "selector": "iframe"})

    # 方法 4: 直接从 HTML 中用正则提取完整视频 URL（最可靠）
    try:
        html = await page.content()
        # 匹配 media-amazon.com 的完整视频 URL
        pattern = r'https://m\.media-amazon\.com/images/S/[A-Za-z0-9\-]+/[A-Za-z0-9\-]+\.mp4/productVideoOptimized\.mp4'
        matches = re.findall(pattern, html)
        for url in matches:
            if not any(v["video_url"] == url for v in videos):
                videos.append({
                    "video_url": url,
                    "type": "html_regex",
                    "selector": "regex",
                })
    except Exception as e:
        logger.debug("HTML regex extraction failed: %s", e)

    return videos


# ─────────────────────────────────────────────────────────
# 视频下载
# ─────────────────────────────────────────────────────────

async def download_video(page, url: str, output_path: str, timeout: int = 120) -> bool:
    """下载单个视频，统一用 yt-dlp（支持 MP4/m3u8/HLS/DASH）"""
    if url.startswith("blob:"):
        logger.warning("  blob URL 无法直接下载: %s", url[:60])
        return False
    # 统一用 yt-dlp，稳定可靠
    return _download_with_ytdlp(url, output_path, timeout)


def _download_with_ytdlp(url: str, output_path: str, timeout: int = 120) -> bool:
    """调用 yt-dlp 下载（支持 HLS/m3u8/DASH）"""
    try:
        if not output_path.endswith(".mp4"):
            output_path = output_path.rsplit(".", 1)[0] + ".mp4"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-warnings", "--no-progress",
            "--socket-timeout", str(timeout),
            "-o", output_path,
            url,
        ]
        logger.info("  yt-dlp: %s", url[:80])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
        if result.returncode == 0 and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            logger.info("  yt-dlp ok: %.1f MB", size / 1024 / 1024)
            return True
        else:
            logger.warning("  yt-dlp failed (rc=%d): %s", result.returncode, result.stderr[:200])
            return False
    except Exception as e:
        logger.warning("  yt-dlp exception: %s", e)
        return False


# ─────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────

async def run(
    asin_list_path: str,
    output_dir: str,
    region: str = "com",
    delay: float = 3.0,
    max_videos_per_product: int = 3,
    profile_dir: str = None,
    headless: bool = False,
):
    from playwright.async_api import async_playwright

    # 读取 ASIN 列表
    asins = []
    seen = set()
    with open(asin_list_path, "r", encoding="utf-8") as f:
        for line in f:
            asin = line.strip().upper()
            if re.match(r"^[A-Z0-9]{10}$", asin) and asin not in seen:
                asins.append(asin)
                seen.add(asin)
    if not asins:
        raise ValueError("未找到有效 ASIN: %s" % asin_list_path)
    logger.info("共读取 %d 个 ASIN", len(asins))

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []

    async with async_playwright() as p:
        launch_args = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        }
        if profile_dir:
            launch_args["user_data_dir"] = profile_dir
            logger.info("使用浏览器 Profile: %s", profile_dir)
        else:
            logger.info("未指定 Profile，使用临时环境")

        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        await context.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        for i, asin in enumerate(asins, 1):
            logger.info("[%d/%d] ASIN: %s", i, len(asins), asin)
            page = await context.new_page()

            # ---- 网络拦截：捕获视频 URL ----
            captured_urls = []

            async def handle_response(response):
                url = response.url
                # 过滤无用 URL
                if "vse-vms-transcoding-artifact" in url:
                    return
                # 只保留真正的视频文件
                if ".mp4" in url or ".m3u8" in url:
                    if url not in captured_urls:
                        captured_urls.append(url)
                        logger.info("  [network]捕获: %s", url[:90])
                elif "media-amazon.com" in url and "/images/S/" in url:
                    # Amazon 视频 CDN 地址
                    ct = response.headers.get("content-type", "")
                    if "video" in ct or "mp4" in ct or url.rstrip("/").endswith((".mp4", ".m3u8")):
                        if url not in captured_urls:
                            captured_urls.append(url)
                            logger.info("  [network]捕获: %s", url[:90])

            page.on("response", handle_response)
            # ----------------------------------------

            url = "https://www.amazon.%s/dp/%s" % (region, asin)

            try:
                logger.info("  加载: %s", url)
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                # 尝试点击视频缩略图，触发视频加载
                for sel in [
                    "img[data-a-image-name*='video']",
                    ".video-thumbnail",
                    "[data-action='a-popover']",
                    "a[id*='video']",
                    ".dp-video-thumbnail",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            await el.click()
                            await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        pass

                # 检查验证码
                is_captcha = await page.evaluate("""() => !!(
                    document.querySelector('[data-captcha="true"]') ||
                    document.title.includes('Robot') ||
                    document.body.innerText.includes('robot check')
                )""")
                if is_captcha:
                    logger.error("  %s 触发验证码！", asin)
                    snap = os.path.join(output_dir, "%s_captcha.html" % asin)
                    with open(snap, "w", encoding="utf-8") as f:
                        f.write(await page.content())
                    results.append({
                        "asin": asin, "url": url,
                        "status": "CAPTCHA", "video_count": 0,
                        "successful_count": 0, "local_files": "",
                        "error": "验证码拦截",
                    })
                    await page.close()
                    continue

                # 保存快照
                snap = os.path.join(output_dir, "%s_snapshot.html" % asin)
                with open(snap, "w", encoding="utf-8") as f:
                    f.write(await page.content())

                # 提取视频 URL
                # 先从快照 HTML 中直接正则提取（最可靠）
                page_videos = []
                try:
                    with open(snap, "r", encoding="utf-8") as f:
                        html = f.read()
                    pattern = r'https://m\.media-amazon\.com/images/S/[A-Za-z0-9\-]+/[A-Za-z0-9\-]+\.mp4/productVideoOptimized\.mp4'
                    matches = re.findall(pattern, html)
                    seen = set()
                    for url in matches:
                        if url not in seen:
                            seen.add(url)
                            page_videos.append({
                                "video_url": url,
                                "type": "snapshot_regex",
                                "selector": "snapshot",
                            })
                    logger.info("  快照正则提取: %d 个 URL", len(matches))
                except Exception as e:
                    logger.debug("快照正则提取失败: %s", e)

                # 再用 extract_video_urls_from_page 作补充（去重）
                extra = await extract_video_urls_from_page(page, asin)
                for v in extra:
                    if not any(ev["video_url"] == v["video_url"] for ev in page_videos):
                        page_videos.append(v)

                # 合并网络拦截的 URL（去重）
                for u in captured_urls:
                    if not any(v["video_url"] == u for v in page_videos):
                        page_videos.append({
                            "video_url": u,
                            "type": "network_intercept",
                            "selector": "response",
                        })

                if not page_videos:
                    logger.warning("  %s 未找到视频", asin)
                    results.append({
                        "asin": asin, "url": url,
                        "status": "NO_VIDEO", "video_count": 0,
                        "successful_count": 0, "local_files": "",
                        "error": "未找到视频",
                    })
                    await page.close()
                    time.sleep(delay)
                    continue

                logger.info("  找到 %d 个视频（+%d 拦截）", len(page_videos), len(captured_urls))
                for idx, v in enumerate(page_videos):
                    logger.debug("    [%d] %s | %s", idx + 1, v["type"], v["video_url"][:80])

                page_videos = page_videos[:max_videos_per_product]

                downloaded = 0
                local_files = []

                for j, vid in enumerate(page_videos, 1):
                    vurl = vid["video_url"]
                    parsed = urlparse(vurl)
                    ext = (parsed.path.rsplit(".", 1)[-1] or "mp4").split("?")[0][:10]
                    if ext not in ("mp4", "m3u8", "mov", "webm"):
                        ext = "mp4"
                    out_file = os.path.join(output_dir, "%s_video_%d.%s" % (asin, j, ext))

                    logger.info("  [%d/%d] %s | %s...", j, len(page_videos), vid["type"], vurl[:60])

                    if vurl.startswith("blob:"):
                        logger.warning("  跳过 blob URL（需手动处理）")
                        local_files.append("[blob] " + vurl)
                        continue

                    ok = await download_video(page, vurl, out_file)
                    if ok:
                        sz = os.path.getsize(out_file)
                        downloaded += 1
                        local_files.append("%s (%.0f KB)" % (os.path.basename(out_file), sz / 1024))
                    else:
                        logger.warning("  下载失败，记录 URL")
                        local_files.append("[failed] " + vurl)

                status = "SUCCESS" if downloaded > 0 else "FAILED"
                results.append({
                    "asin": asin, "url": url,
                    "status": status,
                    "video_count": len(page_videos),
                    "successful_count": downloaded,
                    "local_files": "; ".join(local_files),
                })
                logger.info("  %s 完成: %d/%d 下载成功", asin, downloaded, len(page_videos))

            except Exception as e:
                logger.error("  %s 处理出错: %s", asin, e)
                traceback.print_exc()
                results.append({
                    "asin": asin, "url": url,
                    "status": "FAILED", "video_count": 0,
                    "successful_count": 0, "local_files": "",
                    "error": str(e),
                })

            await page.close()
            if i < len(asins):
                time.sleep(delay)

        await browser.close()

    # 写 CSV 报告
    report_path = os.path.join(output_dir, "download_report.csv")
    write_report(results, report_path)

    # 摘要
    print("\n" + "=" * 60)
    print("下载完成摘要")
    print("=" * 60)
    total_v = sum(r.get("video_count", 0) for r in results)
    total_ok = sum(r.get("successful_count", 0) for r in results)
    sc = {}
    for r in results:
        s = r.get("status", "UNKNOWN")
        sc[s] = sc.get(s, 0) + 1
    print("  ASIN 总数:   %d" % len(results))
    print("  找到视频:   %d" % total_v)
    print("  下载成功:   %d" % total_ok)
    print("  状态分布:   %s" % dict(sc))
    print("  报告:       %s" % report_path)
    print("=" * 60)


def write_report(results, report_path):
    fieldnames = ["asin", "product_url", "status", "video_count",
                  "successful_count", "local_files", "error"]
    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in fieldnames}
            row["product_url"] = r.get("url", "")
            writer.writerow(row)
    logger.info("报告已写入: %s", report_path)


def main():
    parser = argparse.ArgumentParser(
        description="Amazon 竞品视频批量下载器 (浏览器自动化 v3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python download_browser.py -a sample_asins.txt -o ./videos --headless
  python download_browser.py -a sample_asins.txt -o ./videos --region co.uk
        """,
    )
    parser.add_argument("--asin-list", "-a", required=True, help="ASIN 列表文件")
    parser.add_argument("--output", "-o", default="./amazon_videos", help="输出目录")
    parser.add_argument("--region", "-r", default="com", help="Amazon 区域后缀")
    parser.add_argument("--delay", "-d", type=float, default=3.0, help="请求间隔（秒）")
    parser.add_argument("--max-videos", "-m", type=int, default=3, help="每商品最多下载数")
    parser.add_argument("--profile-dir", "-p", help="浏览器 Profile 目录")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if not os.path.isfile(args.asin_list):
        logger.error("文件不存在: %s", args.asin_list)
        sys.exit(1)

    asyncio.run(run(
        asin_list_path=args.asin_list,
        output_dir=args.output,
        region=args.region,
        delay=args.delay,
        max_videos_per_product=args.max_videos,
        profile_dir=args.profile_dir,
        headless=args.headless,
    ))


if __name__ == "__main__":
    main()
