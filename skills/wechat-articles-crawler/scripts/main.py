#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import html
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
from PIL import Image, ImageOps
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config.json"
PROFILE_DIR = Path(os.environ.get("WECHAT_FETCHER_PROFILE_DIR", APP_ROOT / ".playwright-profile"))
LOGIN_ARTIFACTS_DIR = Path(
    os.environ.get("WECHAT_FETCHER_LOGIN_ARTIFACTS_DIR", APP_ROOT / "login_artifacts")
)
DEFAULT_OUTPUT_FOLDER_NAME = "输出文章"
SEEN_MANIFEST = "seen_urls.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
MP_HOME_URL = "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN"
MP_LOGIN_URL = "https://mp.weixin.qq.com/"
ARTICLE_LIST_PAGE_SIZE = 20
KNOWN_COMMANDS = {"fetch", "increment", "status", "ensure-login", "login-status", "clear-login"}
ACTIVE_QR_VIEWER: Any | None = None

# 微信接口 create_time 为 UTC 秒级时间戳；中国公众号展示时间 = UTC+8，且中国不实行夏令时。
CN_OFFSET_HOURS = 8

DEFAULT_THROTTLE: dict[str, float] = {
    "api_min_delay": 2.0,     # 两次后台 API 调用之间的最小间隔（秒）
    "api_max_jitter": 1.5,    # API 调用额外随机抖动上限（秒）
    "dl_min_delay": 1.5,      # 两篇文章下载之间的最小间隔（秒）
    "dl_max_jitter": 1.2,     # 下载额外随机抖动上限（秒）
    "max_retries": 6,         # 单请求失败后的最大重试次数
    "backoff_base": 3.0,      # 退避基数（秒），第 n 次重试等待 ≈ backoff_base * 2^n
}

# 触发"需要重新登录"的 ret 码（微信后台约定，部分版本不同）
LOGIN_EXPIRED_RETS = {200002, 200003, 40001, 40014, 42001, -10001}


class WeChatRateLimit(Exception):
    """触发了微信的频率限制（频繁/429/5xx），应当退避后重试。"""


class LoginExpired(Exception):
    """登录态失效，需要重新扫码。"""


# --------------------------------------------------------------------------- #
# 限流器：在每次请求前插入「固定间隔 + 随机抖动」，避免请求节奏过于规律被识别为爬虫
# --------------------------------------------------------------------------- #
class RateLimiter:
    def __init__(self, min_delay: float, max_jitter: float) -> None:
        self.min_delay = max(0.0, float(min_delay))
        self.max_jitter = max(0.0, float(max_jitter))
        self._last = 0.0

    def wait(self) -> None:
        gap = self.min_delay + random.uniform(0, self.max_jitter)
        sleep_for = max(0.0, gap - (time.time() - self._last))
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last = time.time()

    async def wait_async(self) -> None:
        gap = self.min_delay + random.uniform(0, self.max_jitter)
        sleep_for = max(0.0, gap - (time.time() - self._last))
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)
        self._last = time.time()

    def reset(self) -> None:
        self._last = 0.0


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
@dataclass
class AppConfig:
    output_parent: str
    output_folder_name: str = DEFAULT_OUTPUT_FOLDER_NAME
    article_limit: int = 20
    concurrency: int = 3
    display_mode: str = "auto"
    tz: str = "Asia/Shanghai"
    write_html: bool = True
    throttle: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THROTTLE))

    @property
    def output_root(self) -> Path:
        return Path(self.output_parent).expanduser().resolve() / self.output_folder_name


def merge_throttle(raw: dict[str, Any]) -> dict[str, float]:
    out = dict(DEFAULT_THROTTLE)
    if isinstance(raw.get("throttle"), dict):
        for k, v in raw["throttle"].items():
            if k in DEFAULT_THROTTLE and isinstance(v, (int, float)):
                out[k] = float(v)
    return out


def main() -> int:
    # 强制 stdout/stderr 用 UTF-8，避免 Windows GBK 控制台打印含零宽字符(如 \u200b)的
    # 微信文章标题/内容时抛 UnicodeEncodeError（曾导致收尾 print 崩溃，但下载已完成）。
    # 同时开启行缓冲：后台运行重定向到日志文件时实时可见进度，
    # 不再出现"日志 0 字节干等"（等扫码/翻页阶段外部完全无感知）的问题。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

    args = parse_args()
    resolved_article_url = getattr(args, "url", None) or args.article_url
    quiet = bool(args.json)

    try:
        if args.command == "fetch":
            config = load_or_create_config(noninteractive=quiet or is_headless_environment())
            display_mode = args.display or config.display_mode
            payload = command_fetch(
                article_url=resolved_article_url,
                config=config,
                display_mode=display_mode,
                quiet=quiet,
                resume=args.resume,
                since=args.since,
                until=args.until,
                dry_run=args.dry_run,
                force_qr=args.force_qr,
                tz=args.tz or config.tz,
                login_timeout=args.login_timeout,
                qr_refresh=args.qr_refresh,
                safe_mode=args.safe,
                fast_mode=args.fast,
                min_delay=args.min_delay,
                max_jitter=args.max_jitter,
                md_only=args.md_only,
                limit=args.limit,
                stop_after_seen=args.stop_after_seen,
            )
        elif args.command == "ensure-login":
            config = load_or_create_config(noninteractive=quiet or is_headless_environment())
            display_mode = args.display or config.display_mode
            payload = command_ensure_login(
                display_mode=display_mode,
                quiet=quiet,
                force_qr=args.force_qr,
                login_timeout=args.login_timeout,
                qr_refresh=args.qr_refresh,
            )
        elif args.command == "login-status":
            payload = command_login_status()
        elif args.command == "clear-login":
            payload = command_clear_login()
        elif args.command == "increment":
            config = load_or_create_config(noninteractive=quiet or is_headless_environment())
            display_mode = args.display or config.display_mode
            payload = command_increment(
                article_url=resolved_article_url,
                config=config,
                display_mode=display_mode,
                quiet=quiet,
                since=args.since,
                dry_run=args.dry_run,
                force_qr=args.force_qr,
                tz=args.tz or config.tz,
                login_timeout=args.login_timeout,
                qr_refresh=args.qr_refresh,
                safe_mode=args.safe,
                fast_mode=args.fast,
                min_delay=args.min_delay,
                max_jitter=args.max_jitter,
                last_dir=args.last_dir,
                md_only=args.md_only,
                limit=args.limit,
                stop_after_seen=args.stop_after_seen,
            )
        elif args.command == "status":
            config = load_or_create_config(noninteractive=True)
            payload = command_status(config, quiet=quiet)
        else:
            raise RuntimeError(f"不支持的命令：{args.command}")
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(
                json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2)
            )
            return 1
        raise

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本地版微信公众号文章抓取工具（含限流/去重/本地时间窗）")
    parser.add_argument("primary", nargs="?", help="命令或文章链接")
    parser.add_argument("secondary", nargs="?", help="当命令需要时传入第二个位置参数")
    parser.add_argument(
        "--display",
        choices=["auto", "terminal", "image", "silent"],
        help="二维码展示模式，默认读取 config.json 的 display_mode",
    )
    parser.add_argument("--json", action="store_true", help="只输出 JSON，适合 agent / CLI 集成")
    parser.add_argument(
        "--resume",
        metavar="ARTICLES_JSON",
        default=None,
        help="续抓模式：传入上一轮的 articles.json 路径，自动跳过其中已抓文章，接着抓取后续文章并合并索引",
    )
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        default=None,
        help="时间窗下界：只保留发布时间 ≥ 该日期的文章（比这老的跳过，越过即停）。默认按中国时区(Asia/Shanghai)零点对齐",
    )
    parser.add_argument(
        "--until",
        metavar="YYYY-MM-DD",
        default=None,
        help="时间窗上界：只保留发布时间 ≤ 该日期的文章（含当天）。默认按中国时区零点对齐",
    )
    parser.add_argument(
        "--tz",
        metavar="Asia/Shanghai|UTC",
        default=None,
        help="时间窗对齐时区，默认 Asia/Shanghai（中国用户）。设 UTC 则按世界时零点对齐",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：登录并查询文章列表、应用时间窗与去重，但【不下载】任何文件，只返回将要抓取的清单",
    )
    parser.add_argument(
        "--force-qr",
        action="store_true",
        help="忽略本地已缓存的登录态，强制重新生成二维码扫码登录",
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        help="保守限流预设：加大请求间隔、降低并发，最大限度避免触发公众号限流（速度最慢）",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="激进预设：减小请求间隔、提高并发，速度最快但更易触发限流（风险自担）",
    )
    parser.add_argument(
        "--md-only",
        action="store_true",
        help="只输出 Markdown，不生成 HTML 文件（也可在 config.json 设 write_html:false 作为默认）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="本轮最多抓取 N 篇新文章（覆盖 config.article_limit）。如\"只要最新10篇\"直接 --limit 10",
    )
    parser.add_argument(
        "--stop-after-seen",
        type=int,
        default=None,
        metavar="N",
        help="增量提速：翻页时连续遇到 N 篇已抓文章即提前停止（列表新→旧，新增都在前面）。"
             "带 --resume/increment 时默认 30；设 0 禁用早停（全量扫描）",
    )
    parser.add_argument(
        "--min-delay", type=float, default=None, help="覆盖下载最小间隔（秒）",
    )
    parser.add_argument(
        "--max-jitter", type=float, default=None, help="覆盖下载随机抖动上限（秒）",
    )
    parser.add_argument(
        "--login-timeout", type=int, default=1800, help="登录二维码等待上限（秒），默认 1800",
    )
    parser.add_argument(
        "--qr-refresh", type=int, default=90, help="二维码自动刷新间隔（秒），默认 90",
    )
    parser.add_argument(
        "--url",
        metavar="ARTICLE_URL",
        default=None,
        help="种子文章链接（用于定位公众号）。可作为 fetch / increment 的替代写法，等价于位置参数中的链接",
    )
    parser.add_argument(
        "--last-dir",
        metavar="OUTPUT_DIR",
        default=None,
        help="increment 专用：显式指定上次的 output 目录（含 articles.json）。省略时自动在 output_root 下寻找最新的 run",
    )
    args = parser.parse_args()

    if args.primary in KNOWN_COMMANDS:
        args.command = args.primary
        args.article_url = args.secondary
    else:
        args.command = "fetch"
        args.article_url = args.primary

    if args.command in {"ensure-login", "login-status", "clear-login", "status"} and args.secondary:
        parser.error(f"{args.command} 不接受额外的位置参数。")
    if args.safe and args.fast:
        parser.error("--safe 与 --fast 不能同时指定。")
    return args


# --------------------------------------------------------------------------- #
# 时间处理（修复：使用中国时区零点，避免与 UTC 差一天）
# --------------------------------------------------------------------------- #
def date_to_ts(date_str: str | None, tz: str = "Asia/Shanghai") -> int | None:
    """把 'YYYY-MM-DD' 解析为某时区当天零点的 UTC 时间戳；空或非法返回 None。"""
    if not date_str:
        return None
    s = date_str.strip()
    try:
        naive = datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        try:
            naive = datetime.strptime(s, "%Y/%m/%d")
        except ValueError:
            return None
    if tz == "UTC":
        dt = naive.replace(tzinfo=timezone.utc)
    else:
        # 中国（Asia/Shanghai）全年 UTC+8，无夏令时，直接偏移避免依赖 tzdata
        dt = (naive - timedelta(hours=CN_OFFSET_HOURS)).replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def ts_to_cn_str(ts: Any) -> str | None:
    """把 UTC 秒级时间戳转换为中国展示时间字符串（UTC+8）。"""
    if not isinstance(ts, (int, float)):
        return None
    try:
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc) + timedelta(hours=CN_OFFSET_HOURS)
    except (ValueError, OverflowError, OSError):
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# 命令：increment（增量续抓）
# --------------------------------------------------------------------------- #
def find_latest_run(output_root: Path) -> Path | None:
    """在 output_root 下找出最新的、含 articles.json 的抓取目录（按 articles.json 的 mtime 排序）。"""
    if not output_root.exists():
        return None
    candidates: list[tuple[float, Path]] = []
    for d in output_root.iterdir():
        if not d.is_dir():
            continue
        aj = d / "articles.json"
        md = d / "markdown"
        if aj.exists() and md.exists():
            try:
                candidates.append((aj.stat().st_mtime, d))
            except OSError:
                continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def latest_publish_date_from_articles(articles_json: Path, tz: str = "Asia/Shanghai") -> str | None:
    """从 articles.json 推断增量起点的 since 日期（YYYY-MM-DD）。

    优先取已抓文章中最大的 create_time（发布时间）；若该字段缺失（旧数据），
    回退到目录名中的抓取时间戳（如 ..._20260708_214608 -> 2026-07-08），保证兼容。
    """
    try:
        data = json.loads(articles_json.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        data = None
    if isinstance(data, list):
        max_ts: int | float | None = None
        for item in data:
            if not isinstance(item, dict):
                continue
            ct = item.get("create_time")
            if isinstance(ct, (int, float)) and (max_ts is None or ct > max_ts):
                max_ts = ct
        if max_ts is not None:
            try:
                dt = datetime.fromtimestamp(max_ts, tz=ZoneInfo(tz))
            except Exception:  # noqa: BLE001
                dt = datetime.fromtimestamp(max_ts)
            return dt.strftime("%Y-%m-%d")
    # 回退1：目录名时间戳（如 ..._20260708_214608）
    m = re.search(r"_(\d{8})(?:_\d{6})?$", articles_json.parent.name)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001
            pass
    # 回退2：索引文件最后修改时间的本地日期（≈ 上次抓取日）
    try:
        ts = articles_json.stat().st_mtime
        try:
            dt = datetime.fromtimestamp(ts, tz=ZoneInfo(tz))
        except Exception:  # noqa: BLE001  # 环境缺时区数据则退回系统时区
            dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        pass
    return None


def command_increment(
    *,
    article_url: str | None,
    config: AppConfig,
    display_mode: str,
    quiet: bool,
    since: str | None = None,
    dry_run: bool = False,
    force_qr: bool = False,
    tz: str = "Asia/Shanghai",
    login_timeout: int = 1800,
    qr_refresh: int = 90,
    safe_mode: bool = False,
    fast_mode: bool = False,
    min_delay: float | None = None,
    max_jitter: float | None = None,
    last_dir: str | None = None,
    md_only: bool = False,
    limit: int | None = None,
    stop_after_seen: int | None = None,
) -> dict[str, Any]:
    """增量续抓：复用上次 output 目录，自动推断 since（上次最新文章日期），只抓更新的文章。

    等价于手动 `fetch --resume <上次>/articles.json --since <日期>`，但省去记忆路径与日期。
    若上次之后无新文章，返回 status=up_to_date 而非抛错。
    """
    if not article_url:
        raise RuntimeError(
            "increment 需要种子文章链接来定位公众号，请在命令后附加链接，或用 --url 指定。"
        )
    tz = tz or config.tz
    run_dir = Path(last_dir).expanduser().resolve() if last_dir else find_latest_run(config.output_root)
    if run_dir is None or not (run_dir / "articles.json").exists():
        raise RuntimeError(
            "找不到历史抓取记录（output_root 下无含 articles.json 的目录）。"
            "请先完整抓取一次，或用 --last-dir 显式指定上次的 output 目录。"
        )
    articles_json = run_dir / "articles.json"
    # 默认不早停（since=None）：仅靠 resume 的 seen_links 去重，翻页时跳过全部已抓文章，
    # 新文章必然不在 seen 中而被抓取 —— 最稳，绝不漏抓，也不依赖 articles.json 是否含 create_time。
    # 用户可显式 --since 做早停提速（需保证不晚于已抓最新文章发布日，否则可能早停漏抓）。
    last_update = latest_publish_date_from_articles(articles_json, tz)
    mode_note = (
        f"时间窗 since={since}({tz}) 早停" if since
        else "不早停，全量扫描 + seen 去重（最稳，绝不漏抓）"
    )
    log(
        f"增量模式：基于上次目录 {run_dir.name}"
        + (f"，上次索引更新于 {last_update}" if last_update else "")
        + f"，{mode_note}，并复用同一目录。",
        quiet=quiet,
    )
    try:
        return command_fetch(
            article_url=article_url,
            config=config,
            display_mode=display_mode,
            quiet=quiet,
            resume=str(articles_json),
            since=since,
            until=None,
            dry_run=dry_run,
            force_qr=force_qr,
            tz=tz,
            login_timeout=login_timeout,
            qr_refresh=qr_refresh,
            safe_mode=safe_mode,
            fast_mode=fast_mode,
            min_delay=min_delay,
            max_jitter=max_jitter,
            md_only=md_only,
            limit=limit,
            stop_after_seen=stop_after_seen,
        )
    except RuntimeError as exc:
        if "没有可下载的新文章" in str(exc):
            return {
                "status": "up_to_date",
                "message": "没有比上次更新的文章，无需抓取。",
                "since": since,
                "last_dir": str(run_dir),
            }
        raise


# --------------------------------------------------------------------------- #
# 命令：status（抓取前速览：各账号上次抓到哪天 + 登录态）
# --------------------------------------------------------------------------- #
def command_status(config: AppConfig, *, quiet: bool = False) -> dict[str, Any]:
    """速览历史抓取状态：output_root 下每个账号目录的文章数、最新发布日期，以及登录态。

    落实"抓取前先看上一轮日期、避免重复抓"的习惯，一条命令替代手写脚本解析 articles.json。
    """
    runs: list[dict[str, Any]] = []
    root = config.output_root
    if root.exists():
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            aj = d / "articles.json"
            if not aj.exists():
                continue
            total = ok = 0
            latest: int | float | None = None
            try:
                data = json.loads(aj.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    total = len(data)
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        if item.get("status") == "ok":
                            ok += 1
                        ct = item.get("create_time")
                        if isinstance(ct, (int, float)) and (latest is None or ct > latest):
                            latest = ct
            except Exception:  # noqa: BLE001
                pass
            runs.append({
                "dir": d.name,
                "path": str(d),
                "total": total,
                "ok": ok,
                "latest_publish": ts_to_cn_str(latest) if latest else None,
                "note": None if latest else "旧数据无 create_time 字段，最新日期未知（去重仍可靠）",
            })
    login = command_login_status()
    if not quiet:
        log(f"输出根目录：{root}", quiet=quiet)
        log(f"登录态：{login.get('status', 'unknown')}"
            + (f"（更新于 {login.get('updated_at')}）" if login.get("updated_at") else ""), quiet=quiet)
        if not runs:
            log("暂无历史抓取记录。", quiet=quiet)
        for r in runs:
            log(f"  • {r['dir']}: 共 {r['total']} 篇（成功 {r['ok']}），最新发布 "
                + (r["latest_publish"] or "未知(老数据)"), quiet=quiet)
    return {"status": "ok", "output_root": str(root), "login": login, "runs": runs}


# --------------------------------------------------------------------------- #
# 命令：fetch
# --------------------------------------------------------------------------- #
def command_fetch(
    *,
    article_url: str | None,
    config: AppConfig,
    display_mode: str,
    quiet: bool,
    resume: str | None = None,
    since: str | None = None,
    until: str | None = None,
    dry_run: bool = False,
    force_qr: bool = False,
    tz: str = "Asia/Shanghai",
    login_timeout: int = 1800,
    qr_refresh: int = 90,
    safe_mode: bool = False,
    fast_mode: bool = False,
    min_delay: float | None = None,
    max_jitter: float | None = None,
    md_only: bool = False,
    limit: int | None = None,
    stop_after_seen: int | None = None,
) -> dict[str, Any]:
    article_url = get_article_url(article_url)

    # 本轮抓取上限：--limit 优先于 config.article_limit（如"只要最新10篇"）
    effective_limit = limit if (limit is not None and limit > 0) else config.article_limit

    thr = apply_speed_preset(config.throttle, safe_mode, fast_mode)
    if min_delay is not None:
        thr["dl_min_delay"] = max(0.0, min_delay)
    if max_jitter is not None:
        thr["dl_max_jitter"] = max(0.0, max_jitter)
    concurrency = max(1, min(int(config.concurrency), 6))
    if safe_mode:
        concurrency = min(concurrency, 2)          # 保守：最多 2 路并发
    elif fast_mode:
        concurrency = max(concurrency, 5)           # 激进：拉到 5 路（仍有抖动护体）

    # --- 续抓 / 去重清单：来自上一轮 articles.json（仅成功的）、本地产物清单、已有 seen 清单 ---
    seen_links: set[str] = set()
    resume_dir: Path | None = None
    if resume:
        rp = Path(resume).expanduser().resolve()
        if rp.exists():
            seen_links |= load_ok_links(rp)
            resume_dir = rp.parent
        else:
            raise RuntimeError(f"--resume 指定的文件不存在：{rp}")
    if resume_dir is not None:
        seen_links |= load_ok_links(resume_dir / "articles.json")
        seen_links |= load_manifest(resume_dir / SEEN_MANIFEST)

    # 增量早停：续抓时列表新→旧，新增文章必然在最前面；连续命中 N 篇已抓文章
    # 即说明已进入"老区"，直接停止翻页（避免为找增量翻完全部历史，600 篇号从 ~6 分钟降到几十秒）。
    # 未显式指定时：带 resume 默认 30，全新抓取默认 0（不早停）。设 --stop-after-seen 0 可强制全量扫描。
    if stop_after_seen is None:
        stop_after_seen = 30 if seen_links else 0
    if stop_after_seen > 0:
        log(f"增量早停已启用：连续 {stop_after_seen} 篇命中已抓清单即停止翻页（--stop-after-seen 0 可禁用）。",
            quiet=quiet)

    since_ts = date_to_ts(since, tz)
    until_ts = date_to_ts(until, tz)
    if since and since_ts is None:
        raise RuntimeError(f"--since 日期无法解析：{since}（应为 YYYY-MM-DD）")
    if until and until_ts is None:
        raise RuntimeError(f"--until 日期无法解析：{until}（应为 YYYY-MM-DD）")
    if until_ts is not None:
        until_ts += 86400  # --until 视为含当天，截止点推到次日 0 点
    if since_ts is not None and until_ts is not None and since_ts > until_ts:
        raise RuntimeError(f"--since({since}) 不能晚于 --until({until})")

    win_bits = []
    if since_ts is not None:
        win_bits.append(f"since={since}({tz})")
    if until_ts is not None:
        win_bits.append(f"until={until}({tz})")
    if win_bits:
        log(f"时间窗已启用：{', '.join(win_bits)}（更老的文章将跳过/停止）", quiet=quiet)

    log(f"限流配置：API 间隔≈{thr['api_min_delay']:.1f}+{thr['api_max_jitter']:.1f}s，"
        f"下载间隔≈{thr['dl_min_delay']:.1f}+{thr['dl_max_jitter']:.1f}s，并发={concurrency}", quiet=quiet)

    # 首次登录 + 解析 + 抓取列表（若中途登录失效则强制重登一次后重试）
    try:
        articles, skipped = run_fetch_once(
            article_url=article_url,
            config=config,
            display_mode=display_mode,
            quiet=quiet,
            since_ts=since_ts,
            until_ts=until_ts,
            seen_links=seen_links,
            force_qr=force_qr,
            tz=tz,
            login_timeout=login_timeout,
            qr_refresh=qr_refresh,
            thr=thr,
            limit_override=effective_limit,
            stop_after_seen=stop_after_seen,
        )
    except LoginExpired:
        log("登录态已失效，正在强制重新扫码登录后重试一次...", quiet=quiet)
        articles, skipped = run_fetch_once(
            article_url=article_url,
            config=config,
            display_mode=display_mode,
            quiet=quiet,
            since_ts=since_ts,
            until_ts=until_ts,
            seen_links=seen_links,
            force_qr=True,
            tz=tz,
            login_timeout=login_timeout,
            qr_refresh=qr_refresh,
            thr=thr,
            limit_override=effective_limit,
            stop_after_seen=stop_after_seen,
        )

    if not articles:
        note = "没有可下载的新文章（可能该号历史已全部抓取完毕，或落在时间窗之外）。"
        if dry_run:
            return {"status": "preview_empty", "message": note, "already_have": len(seen_links)}
        raise RuntimeError(note)

    if dry_run:
        would = [
            {
                "index": i + 1,
                "title": a["title"],
                "link": a["link"],
                "publish_time": ts_to_cn_str(a.get("create_time")),
                "create_time": a.get("create_time"),
            }
            for i, a in enumerate(articles)
        ]
        return {
            "status": "preview",
            "timezone": tz,
            "since": since,
            "until": until,
            "already_have": skipped,
            "would_download_count": len(would),
            "would_download": would,
            "note": "仅预览，未下载任何文件。去掉 --dry-run 才会真正抓取到本地。",
        }

    # 是否生成 HTML：默认跟随 config.write_html，--md-only 可强制只出 Markdown
    want_html = bool(config.write_html) and (not md_only)

    output_dir = prepare_output_dir(config, articles[0]["account_name"], resume_dir=resume_dir, want_html=want_html)
    start_index = 1
    existing_results: list[dict[str, Any]] = []
    if resume_dir is not None:
        start_index = len(list((output_dir / "markdown").glob("*.md"))) + 1
        index_path_existing = output_dir / "articles.json"
        if index_path_existing.exists():
            try:
                existing_results = json.loads(index_path_existing.read_text(encoding="utf-8"))
                if not isinstance(existing_results, list):
                    existing_results = []
            except Exception:  # noqa: BLE001
                existing_results = []

    log(f"准备下载 {len(articles)} 篇文章到：{output_dir}", quiet=quiet)
    dl_limiter = RateLimiter(thr["dl_min_delay"], thr["dl_max_jitter"])
    cookies = load_cookies_from_profile()  # 由 run_fetch_once 内已写入 profile；这里兜底取
    results = asyncio.run(
        download_articles(
            cookies=cookies,
            articles=articles[:effective_limit],
            output_dir=output_dir,
            account=articles[0]["account"],
            concurrency=concurrency,
            start_index=start_index,
            write_html=(resume_dir is None) and want_html,
            limiter=dl_limiter,
            max_retries=int(thr["max_retries"]),
            backoff_base=thr["backoff_base"],
        )
    )

    # 把文章发布时间注入本轮索引，便于未来 increment 精确推断 since
    ct_map = {
        normalize_article_url(a.get("link", "")): a.get("create_time")
        for a in articles
    }
    for item in results:
        if item.get("create_time") is None:
            item["create_time"] = ct_map.get(normalize_article_url(item.get("url", "")))

    # 合并索引 + 更新去重清单（仅把成功的链接写进 manifest，失败的留待下次重试）
    all_results = existing_results + results
    index_path = output_dir / "articles.json"
    index_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    for item in results:
        if item.get("status") == "ok" and item.get("url"):
            seen_links.add(normalize_article_url(item["url"]))
    write_manifest(output_dir / SEEN_MANIFEST, sorted(seen_links))

    new_success = sum(1 for item in results if item.get("status") == "ok")
    total_success = sum(1 for item in all_results if item.get("status") == "ok")
    log(f"完成：本轮成功 {new_success}/{len(results)} 篇"
        + (f"，累计 {total_success} 篇" if resume_dir is not None else "") + "。", quiet=quiet)
    log(f"输出目录：{output_dir}", quiet=quiet)
    log(f"索引文件：{index_path}", quiet=quiet)

    return {
        "status": "completed",
        "account_name": articles[0]["account_name"],
        "account_alias": articles[0]["account"].get("alias") or "",
        "requested_limit": effective_limit,
        "downloaded": new_success,
        "failed": len(results) - new_success,
        "output_dir": str(output_dir),
        "index_file": str(index_path),
        "profile_dir": str(PROFILE_DIR),
        "login_artifacts_dir": str(LOGIN_ARTIFACTS_DIR),
        "results": results,
    }


def run_fetch_once(
    *,
    article_url: str,
    config: AppConfig,
    display_mode: str,
    quiet: bool,
    since_ts: int | None,
    until_ts: int | None,
    seen_links: set[str],
    force_qr: bool,
    tz: str,
    login_timeout: int,
    qr_refresh: int,
    thr: dict[str, float],
    limit_override: int | None = None,
    stop_after_seen: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    log("正在检查公众号后台登录状态...", quiet=quiet)
    token, cookies = ensure_login(
        display_mode=display_mode,
        quiet=quiet,
        force_qr=force_qr,
        login_timeout=login_timeout,
        qr_refresh=qr_refresh,
    )
    log("登录状态可用，开始解析文章来源...", quiet=quiet)

    seed = fetch_seed_article_info(article_url)
    if not seed.get("nickname") and not seed.get("alias"):
        raise RuntimeError("无法从这篇文章里识别公众号名称，换一篇该号文章再试。")

    api_limiter = RateLimiter(thr["api_min_delay"], thr["api_max_jitter"])
    with build_sync_client(cookies) as client:
        account, _preview = resolve_account(
            client, token, seed, config.article_limit, api_limiter, thr
        )
        log(
            f"已锁定公众号：{account['nickname']}"
            + (f"（{account['alias']}）" if account.get("alias") else ""),
            quiet=quiet,
        )
        articles, skipped = fetch_account_articles(
            client=client,
            token=token,
            fakeid=account["fakeid"],
            limit=limit_override or config.article_limit,
            seen_links=seen_links,
            since_ts=since_ts,
            until_ts=until_ts,
            limiter=api_limiter,
            max_retries=int(thr["max_retries"]),
            backoff_base=thr["backoff_base"],
            stop_after_seen=stop_after_seen,
        )

    if not articles:
        return [], skipped

    # 把 account 信息挂到每篇上，方便后续落盘
    for a in articles:
        a["account"] = account
        a["account_name"] = account["nickname"]
    return articles, skipped


# --------------------------------------------------------------------------- #
# 命令：登录相关
# --------------------------------------------------------------------------- #
def command_ensure_login(
    *, display_mode: str, quiet: bool, force_qr: bool = False,
    login_timeout: int = 1800, qr_refresh: int = 90,
) -> dict[str, Any]:
    log("正在检查公众号后台登录状态...", quiet=quiet)
    ensure_login(
        display_mode=display_mode, quiet=quiet,
        force_qr=force_qr, login_timeout=login_timeout, qr_refresh=qr_refresh,
    )
    payload = command_login_status()
    payload.update({"status": "authenticated", "token_present": True})
    return payload


def command_login_status() -> dict[str, Any]:
    status_path = LOGIN_ARTIFACTS_DIR / "login_status.json"
    payload: dict[str, Any] = {
        "status": "missing",
        "status_file": str(status_path),
        "profile_dir": str(PROFILE_DIR),
        "profile_exists": PROFILE_DIR.exists(),
        "login_artifacts_dir": str(LOGIN_ARTIFACTS_DIR),
        "login_artifacts_exists": LOGIN_ARTIFACTS_DIR.exists(),
    }
    if status_path.exists():
        payload.update(json.loads(status_path.read_text(encoding="utf-8")))
        payload["status_file"] = str(status_path)
        payload["profile_dir"] = str(PROFILE_DIR)
        payload["profile_exists"] = PROFILE_DIR.exists()
        payload["login_artifacts_dir"] = str(LOGIN_ARTIFACTS_DIR)
        payload["login_artifacts_exists"] = LOGIN_ARTIFACTS_DIR.exists()
    return payload


def command_clear_login() -> dict[str, Any]:
    removed_paths: list[str] = []
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR)
        removed_paths.append(str(PROFILE_DIR))
    if LOGIN_ARTIFACTS_DIR.exists():
        shutil.rmtree(LOGIN_ARTIFACTS_DIR)
        removed_paths.append(str(LOGIN_ARTIFACTS_DIR))
    return {
        "status": "cleared",
        "removed_paths": removed_paths,
        "profile_dir": str(PROFILE_DIR),
        "login_artifacts_dir": str(LOGIN_ARTIFACTS_DIR),
    }


# --------------------------------------------------------------------------- #
# 日志
# --------------------------------------------------------------------------- #
def log(message: str, *, quiet: bool) -> None:
    if not quiet:
        print(message)


def log_err(message: str) -> None:
    """进度/告警信息走 stderr，避免污染 --json 的 stdout。"""
    print(message, file=sys.stderr)


# --------------------------------------------------------------------------- #
# 配置加载
# --------------------------------------------------------------------------- #
def load_or_create_config(*, noninteractive: bool) -> AppConfig:
    if CONFIG_PATH.exists():
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["throttle"] = merge_throttle(raw)
        raw.setdefault("article_limit", 20)
        raw.setdefault("concurrency", 3)
        raw.setdefault("display_mode", "auto")
        raw.setdefault("tz", "Asia/Shanghai")
        raw.setdefault("output_folder_name", DEFAULT_OUTPUT_FOLDER_NAME)
        return AppConfig(**raw)

    if noninteractive:
        config = build_default_config()
        CONFIG_PATH.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
        return config

    output_parent, article_limit = prompt_first_run_config()
    config = AppConfig(output_parent=output_parent, article_limit=article_limit)
    CONFIG_PATH.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    return config


def build_default_config() -> AppConfig:
    return AppConfig(
        output_parent=str(default_output_parent()),
        article_limit=20,
        concurrency=3,
        display_mode="silent" if is_headless_environment() else "auto",
        tz="Asia/Shanghai",
        throttle=dict(DEFAULT_THROTTLE),
    )


def apply_speed_preset(thr: dict[str, float], safe: bool, fast: bool) -> dict[str, float]:
    out = dict(thr)
    if safe:
        out.update({
            "api_min_delay": 4.0, "api_max_jitter": 3.0,
            "dl_min_delay": 3.0, "dl_max_jitter": 2.0,
        })
    elif fast:
        out.update({
            "api_min_delay": 0.6, "api_max_jitter": 0.4,
            "dl_min_delay": 0.4, "dl_max_jitter": 0.3,
        })
    out["max_retries"] = max(1, int(out.get("max_retries", 6)))
    return out


def default_output_parent() -> Path:
    skill_root = APP_ROOT.parent
    if (skill_root / "SKILL.md").exists():
        return skill_root
    desktop_path = Path.home() / "Desktop"
    if desktop_path.exists():
        return desktop_path
    return Path.home()


def is_headless_environment() -> bool:
    if sys.platform == "darwin":
        return not sys.stdout.isatty()
    return not bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def prompt_first_run_config() -> tuple[str, int]:
    selected_dir = choose_directory_with_dialog()
    if not selected_dir:
        fallback = input("请输入输出父目录绝对路径：").strip()
        selected_dir = fallback
    if not selected_dir:
        raise SystemExit("未选择输出目录，程序已退出。")

    raw_limit = ask_text_with_dialog(message="请输入单次批量提取文章数：", default="20")
    if not raw_limit:
        raw_limit = input("请输入单次批量提取文章数：").strip()
    try:
        article_limit = int(raw_limit)
    except ValueError as exc:
        raise SystemExit("单次抓取篇数不是有效数字。") from exc
    if article_limit < 1 or article_limit > 200:
        raise SystemExit("单次抓取篇数必须在 1 到 200 之间。")
    return selected_dir, article_limit


def choose_directory_with_dialog() -> str | None:
    script = """
    set chosenFolder to choose folder with prompt "请选择文章输出的父目录，程序会在里面自动新建“输出文章”文件夹"
    POSIX path of chosenFolder
    """
    return run_osascript(script)


def ask_text_with_dialog(*, message: str, default: str) -> str | None:
    escaped_message = message.replace('"', '\\"')
    escaped_default = default.replace('"', '\\"')
    script = f'''
    text returned of (display dialog "{escaped_message}" default answer "{escaped_default}" buttons {{"取消", "确定"}} default button "确定")
    '''
    return run_osascript(script)


def run_osascript(script: str) -> str | None:
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def get_article_url(article_url: str | None) -> str:
    if article_url and article_url.strip():
        return article_url.strip()
    article_url = input("请输入任意一篇公众号文章链接：").strip()
    if not article_url:
        raise SystemExit("未输入文章链接。")
    return article_url


# --------------------------------------------------------------------------- #
# 登录实现
# --------------------------------------------------------------------------- #
def ensure_login(
    *, display_mode: str, quiet: bool, force_qr: bool = False,
    login_timeout: int = 1800, qr_refresh: int = 90,
) -> tuple[str, dict[str, str]]:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    LOGIN_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if not force_qr:
        with sync_playwright() as playwright:
            token, cookies = try_get_session(playwright, headless=True, interactive=False)
            if token:
                write_login_status(status="authenticated", display_mode=display_mode,
                                    message="已复用本地登录态。")
                save_cookies_to_profile(cookies)
                return token, cookies

    log("常规会话检查未命中，正在进入登录页；如有需要会生成登录二维码...", quiet=quiet)
    with sync_playwright() as playwright:
        token, cookies = login_with_qr(
            playwright, display_mode=display_mode, quiet=quiet,
            login_timeout=login_timeout, qr_refresh=qr_refresh,
        )
        if token:
            save_cookies_to_profile(cookies)
            return token, cookies

    write_login_status(status="timeout", display_mode=display_mode,
                       message="登录超时，未拿到公众号后台 token。")
    raise SystemExit("登录失败，未拿到公众号后台 token。")


def try_get_session(playwright: Any, *, headless: bool, interactive: bool) -> tuple[str | None, dict[str, str]]:
    context = launch_browser_context(playwright, headless=headless, user_data_dir=PROFILE_DIR)
    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(MP_HOME_URL, wait_until="domcontentloaded", timeout=45000)
        token = wait_for_token(page, interactive=interactive)
        cookies = {item["name"]: item["value"] for item in context.cookies("https://mp.weixin.qq.com")}
        return token, cookies
    finally:
        context.close()


def launch_browser_context(playwright: Any, *, headless: bool, user_data_dir: Path) -> Any:
    browser_args = {
        "user_data_dir": str(user_data_dir),
        "headless": headless,
        "viewport": {"width": 1440, "height": 960},
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-default-browser-check",
        ],
    }
    last_error: Exception | None = None
    for channel in ("chrome", "msedge", None):
        try:
            if channel:
                return playwright.chromium.launch_persistent_context(channel=channel, **browser_args)
            return playwright.chromium.launch_persistent_context(**browser_args)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError("无法启动浏览器。")


def login_with_qr(
    playwright: Any, *, display_mode: str, quiet: bool,
    login_timeout: int = 1800, qr_refresh: int = 90,
) -> tuple[str | None, dict[str, str]]:
    context = launch_browser_context(playwright, headless=True, user_data_dir=PROFILE_DIR)
    qr_selector = "img.login__type__container__scan__qrcode"
    last_qr_signature: str | None = None
    last_refresh_at = time.time()

    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(MP_LOGIN_URL, wait_until="domcontentloaded", timeout=45000)

        token = extract_token_from_url(page.url)
        if token:
            cookies = {item["name"]: item["value"] for item in context.cookies("https://mp.weixin.qq.com")}
            write_login_status(status="authenticated", display_mode=display_mode, message="已通过登录页复用本地登录态。")
            return token, cookies

        wait_for_login_qr(page, qr_selector)

        deadline = time.time() + max(120, login_timeout)
        while time.time() < deadline:
            token = extract_token_from_url(page.url)
            if token:
                cookies = {item["name"]: item["value"] for item in context.cookies("https://mp.weixin.qq.com")}
                write_login_status(status="authenticated", display_mode=display_mode, message="扫码登录成功。")
                return token, cookies

            last_qr_signature = maybe_refresh_qr_artifacts(
                page=page, qr_selector=qr_selector, display_mode=display_mode,
                last_qr_signature=last_qr_signature, quiet=quiet,
            )

            # 按设定间隔刷新二维码（单码有效期约 90–120s，务必提示用户只扫当前活码）
            if time.time() - last_refresh_at > max(30, qr_refresh):
                page.reload(wait_until="domcontentloaded", timeout=45000)
                token = extract_token_from_url(page.url)
                if token:
                    cookies = {item["name"]: item["value"] for item in context.cookies("https://mp.weixin.qq.com")}
                    write_login_status(status="authenticated", display_mode=display_mode,
                                       message="二维码刷新期间已复用本地登录态。")
                    return token, cookies
                wait_for_login_qr(page, qr_selector)
                last_refresh_at = time.time()

            try:
                page.wait_for_timeout(1000)
            except PlaywrightTimeoutError:
                pass
    finally:
        close_qr_viewer()
        context.close()

    return None, {}


def wait_for_login_qr(page: Any, qr_selector: str) -> None:
    locator = page.locator(qr_selector).first
    locator.wait_for(state="visible", timeout=45000)
    deadline = time.time() + 45
    while time.time() < deadline:
        info = locator.evaluate(
            "el => ({complete: el.complete, naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight})"
        )
        if info["complete"] and info["naturalWidth"] > 0 and info["naturalHeight"] > 0:
            return
        page.wait_for_timeout(250)
    raise RuntimeError("二维码图片未能在限定时间内加载完成。")


def maybe_refresh_qr_artifacts(
    *, page: Any, qr_selector: str, display_mode: str, last_qr_signature: str | None, quiet: bool,
) -> str | None:
    qr_image = page.locator(qr_selector).first
    try:
        qr_src = qr_image.get_attribute("src", timeout=3000) or ""
    except PlaywrightTimeoutError:
        return last_qr_signature

    try:
        body_text = page.locator("body").inner_text(timeout=3000)
    except PlaywrightTimeoutError:
        body_text = ""

    if body_text and ("二维码已失效" in body_text or "请重新扫描" in body_text or "已过期" in body_text):
        page.reload(wait_until="domcontentloaded", timeout=45000)
        wait_for_login_qr(page, qr_selector)
        qr_image = page.locator(qr_selector).first
        qr_src = qr_image.get_attribute("src") or ""

    if qr_src and qr_src != last_qr_signature:
        wait_for_login_qr(page, qr_selector)
        qr_image = page.locator(qr_selector).first
        png_bytes = qr_image.screenshot()
        return write_login_qr_artifacts(
            png_bytes=png_bytes, qr_signature=qr_src, display_mode=display_mode, quiet=quiet,
        )
    return last_qr_signature


def write_login_qr_artifacts(*, png_bytes: bytes, qr_signature: str, display_mode: str, quiet: bool) -> str:
    png_path = LOGIN_ARTIFACTS_DIR / "login_qr.png"
    txt_path = LOGIN_ARTIFACTS_DIR / "login_qr.txt"
    png_path.write_bytes(png_bytes)

    ascii_qr = render_qr_ascii(png_bytes)
    txt_path.write_text(ascii_qr + "\n", encoding="utf-8")

    write_login_status(
        status="waiting_scan", display_mode=display_mode, qr_signature=qr_signature,
        qr_png_path=str(png_path), qr_text_path=str(txt_path),
        qr_valid_seconds=120,
        message="请使用微信扫码登录公众号后台。务必只扫当前弹出的最新活码（旧码 90–120s 即失效）。",
    )

    log("登录二维码已生成：", quiet=quiet)
    log(f"- PNG：{png_path}", quiet=quiet)
    log(f"- 文本：{txt_path}", quiet=quiet)

    if should_print_qr_to_terminal(display_mode) and not quiet:
        print(ascii_qr)
    if should_open_qr_image(display_mode):
        open_file_in_viewer(png_path)
    return qr_signature


def render_qr_ascii(png_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(png_bytes)).convert("L")
    image = ImageOps.autocontrast(image)
    binary = image.point(lambda value: 255 if value > 180 else 0, mode="1")
    bbox = ImageOps.invert(binary.convert("L")).getbbox()
    if bbox:
        binary = binary.crop(bbox)
    padded = ImageOps.expand(binary, border=4, fill=1)
    max_side = 48
    padded = padded.resize((max_side, max_side), resample=Image.Resampling.NEAREST)
    lines = []
    for y in range(padded.height):
        row = []
        for x in range(padded.width):
            pixel = padded.getpixel((x, y))
            row.append("  " if pixel else "██")
        lines.append("".join(row).rstrip())
    return "\n".join(lines)


def should_print_qr_to_terminal(display_mode: str) -> bool:
    return display_mode in {"auto", "terminal"} and sys.stdout.isatty()


def should_open_qr_image(display_mode: str) -> bool:
    if display_mode not in {"auto", "image"}:
        return False
    if sys.platform == "darwin":
        return shutil.which("qlmanage") is not None
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) and shutil.which("xdg-open") is not None


def open_file_in_viewer(path: Path) -> None:
    global ACTIVE_QR_VIEWER
    close_qr_viewer()
    try:
        if sys.platform == "darwin":
            ACTIVE_QR_VIEWER = subprocess.Popen(["qlmanage", "-p", str(path)],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if shutil.which("xdg-open"):
            ACTIVE_QR_VIEWER = subprocess.Popen(["xdg-open", str(path)],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        ACTIVE_QR_VIEWER = None


def close_qr_viewer() -> None:
    global ACTIVE_QR_VIEWER
    if ACTIVE_QR_VIEWER is None:
        return
    try:
        if ACTIVE_QR_VIEWER.poll() is None:
            ACTIVE_QR_VIEWER.terminate()
            try:
                ACTIVE_QR_VIEWER.wait(timeout=3)
            except subprocess.TimeoutExpired:
                ACTIVE_QR_VIEWER.kill()
    except Exception:  # noqa: BLE001
        pass
    ACTIVE_QR_VIEWER = None


def write_login_status(status: str, display_mode: str, **payload: Any) -> None:
    status_path = LOGIN_ARTIFACTS_DIR / "login_status.json"
    data = {
        "status": status,
        "display_mode": display_mode,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def wait_for_token(page: Any, *, interactive: bool) -> str | None:
    deadline = time.time() + (300 if interactive else 5)
    if interactive:
        print("浏览器已打开。请在微信公众平台页面扫码并完成确认。")
    while time.time() < deadline:
        token = extract_token_from_url(page.url)
        if token:
            return token
        try:
            page.wait_for_timeout(1000)
        except PlaywrightTimeoutError:
            pass
    return None


def extract_token_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("token")
    return values[0] if values else None


# cookies 持久化：登录成功后把 cookie 单独存一份，供下载阶段与续抓阶段复用，
# 避免每次都重新走浏览器拿 token。
_COOKIE_CACHE = LOGIN_ARTIFACTS_DIR / "cookies.json"


def save_cookies_to_profile(cookies: dict[str, str]) -> None:
    try:
        _COOKIE_CACHE.write_text(json.dumps(cookies, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def load_cookies_from_profile() -> dict[str, str]:
    try:
        if _COOKIE_CACHE.exists():
            return json.loads(_COOKIE_CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {}


# --------------------------------------------------------------------------- #
# HTTP 客户端 + 限流封装
# --------------------------------------------------------------------------- #
def build_sync_client(cookies: dict[str, str]) -> httpx.Client:
    return httpx.Client(
        headers=base_headers(),
        cookies=cookies,
        follow_redirects=True,
        timeout=httpx.Timeout(30.0, connect=30.0),
    )


def build_async_client(cookies: dict[str, str]) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=base_headers(),
        cookies=cookies,
        follow_redirects=True,
        timeout=httpx.Timeout(30.0, connect=30.0),
    )


def base_headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Referer": "https://mp.weixin.qq.com/",
        "Origin": "https://mp.weixin.qq.com",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "identity",
    }


def check_base_resp(data: Any) -> None:
    """解析后台 base_resp，遇限流抛 WeChatRateLimit，遇登录失效抛 LoginExpired。"""
    if not isinstance(data, dict):
        return
    br = data.get("base_resp") or {}
    ret = br.get("ret")
    if ret in (None, 0):
        return
    msg = " ".join(str(br.get(k, "")) for k in ("err_msg", "err_msg_cn", "msg"))
    msg = msg or str(data.get("err_msg", ""))
    if ret in LOGIN_EXPIRED_RETS or any(p in msg for p in ("登录已过期", "请重新登录", "未登录", "请先登录", "帐号登录")):
        raise LoginExpired(f"ret={ret} {msg}")
    if any(p in msg for p in ("频繁", "频率", "太频繁", "操作过于", "请稍后", "frequency", "try again", "busy", "访问过于")):
        raise WeChatRateLimit(f"ret={ret} {msg}")
    raise RuntimeError(f"公众号后台接口报错：{data}")


def api_get_json(
    client: httpx.Client, url: str, params: dict[str, Any],
    *, limiter: RateLimiter, max_retries: int, backoff_base: float,
) -> dict[str, Any]:
    """带限流 + 指数退避的后台 API 调用。"""
    limiter.wait()
    last_exc: Exception | None = None
    for attempt in range(max(1, max_retries)):
        try:
            resp = client.get(url, params=params)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise WeChatRateLimit(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            check_base_resp(data)
            return data
        except (WeChatRateLimit, httpx.TransportError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt >= max(1, max_retries) - 1:
                break
            wait = backoff_base * (2 ** attempt) + random.uniform(0, 1.5)
            log_err(f"[限流/重试] 第{attempt + 1}次失败：{exc}；{wait:.1f}s 后重试")
            time.sleep(wait)
            limiter.reset()
    assert last_exc is not None
    raise last_exc


# --------------------------------------------------------------------------- #
# 文章解析 / 账号解析
# --------------------------------------------------------------------------- #
def fetch_seed_article_info(article_url: str) -> dict[str, Any]:
    response = httpx.get(
        article_url,
        headers={"User-Agent": USER_AGENT, "Referer": "https://mp.weixin.qq.com/"},
        follow_redirects=True,
        timeout=httpx.Timeout(30.0, connect=30.0),
    )
    response.raise_for_status()
    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")
    parsed = urlparse(str(response.url))
    query = parse_qs(parsed.query)

    title = ""
    title_node = soup.select_one("#activity-name")
    if title_node:
        title = title_node.get_text(" ", strip=True)
    if not title:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title:
            title = og_title.get("content", "").strip()

    seed = {
        "article_url": str(response.url),
        "title": title,
        "nickname": first_match(html_text, [
            r'var\s+nickname\s*=\s*htmlDecode\("([^"]+)"\);',
            r'window\.__INITIAL_STATE__.*?"nickname":"([^"]+)"',
        ]),
        "alias": first_match(html_text, [
            r'var\s+user_name\s*=\s*"([^"]*)";',
            r'"user_name":"([^"]+)"',
        ]),
        "biz": query.get("__biz", [None])[0] or first_match(html_text, [r'var\s+biz\s*=\s*"([^"]+)";']),
        "mid": query.get("mid", [None])[0],
        "idx": query.get("idx", [None])[0],
        "sn": query.get("sn", [None])[0],
    }
    return seed


def first_match(content: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return decode_js_string(match.group(1))
    return None


def decode_js_string(value: str) -> str:
    candidate = value.strip()
    try:
        candidate = json.loads(f'"{candidate}"')
    except json.JSONDecodeError:
        candidate = candidate.replace('\\"', '"').replace("\\/", "/")
    return html.unescape(candidate).strip()


def resolve_account(
    client: httpx.Client, token: str, seed: dict[str, Any], limit: int,
    limiter: RateLimiter, thr: dict[str, float],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    queries = [seed.get("alias"), seed.get("nickname")]
    candidates: list[dict[str, Any]] = []
    seen_fakeids: set[str] = set()

    for query in queries:
        if not query:
            continue
        for account in search_accounts(client, token, query, limiter, thr):
            fakeid = str(account.get("fakeid") or "")
            if fakeid and fakeid not in seen_fakeids:
                seen_fakeids.add(fakeid)
                candidates.append(account)

    if not candidates:
        raise SystemExit("没有找到公众号候选结果。该账号可能关闭了后台搜索。")

    ranked = sorted(candidates, key=lambda item: score_account(item, seed), reverse=True)
    preview_cache: dict[str, list[dict[str, Any]]] = {}

    # 只预览前 3 个候选以匹配 seed，减少无谓的 API 调用（限流友好）
    for account in ranked[:3]:
        preview, _ = fetch_account_articles(
            client=client, token=token, fakeid=account["fakeid"],
            limit=min(max(limit, 10), 20), seen_links=set(),
            limiter=limiter, max_retries=int(thr["max_retries"]), backoff_base=thr["backoff_base"],
        )
        preview_cache[str(account["fakeid"])] = preview
        if any(is_same_article(article["link"], seed["article_url"]) for article in preview):
            return account, preview

    best = ranked[0]
    return best, preview_cache.get(str(best["fakeid"]), [])


def search_accounts(client: httpx.Client, token: str, query: str, limiter: RateLimiter, thr: dict[str, float]) -> list[dict[str, Any]]:
    data = api_get_json(
        client, "https://mp.weixin.qq.com/cgi-bin/searchbiz",
        {"action": "search_biz", "query": query, "begin": 0, "count": 5, "token": token,
         "lang": "zh_CN", "f": "json", "ajax": 1},
        limiter=limiter, max_retries=int(thr["max_retries"]), backoff_base=thr["backoff_base"],
    )
    return data.get("list") or []


def fetch_account_articles(
    *, client: httpx.Client, token: str, fakeid: str, limit: int,
    seen_links: set[str] | None = None,
    since_ts: int | None = None, until_ts: int | None = None,
    limiter: RateLimiter | None = None, max_retries: int = 6, backoff_base: float = 3.0,
    stop_after_seen: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    limiter = limiter or RateLimiter(DEFAULT_THROTTLE["api_min_delay"], DEFAULT_THROTTLE["api_max_jitter"])
    articles: list[dict[str, Any]] = []
    seen_links = seen_links or set()
    begin = 0
    skipped_already = 0
    consecutive_seen = 0  # 连续命中已抓文章的计数（stop_after_seen>0 时用于增量早停）

    while len(articles) < limit:
        data = api_get_json(
            client, "https://mp.weixin.qq.com/cgi-bin/appmsgpublish",
            {"sub": "list", "begin": begin, "count": ARTICLE_LIST_PAGE_SIZE, "fakeid": fakeid,
             "type": "101_1", "free_publish_type": 1, "sub_action": "list_ex", "token": token,
             "lang": "zh_CN", "f": "json", "ajax": 1},
            limiter=limiter, max_retries=max_retries, backoff_base=backoff_base,
        )
        page_raw = data.get("publish_page")
        if not page_raw:
            break
        page_data = json.loads(page_raw) if isinstance(page_raw, str) else page_raw
        publish_list = page_data.get("publish_list") or []
        if not publish_list:
            break

        past_window = False
        for item in publish_list:
            publish_info = item.get("publish_info")
            if isinstance(publish_info, str) and publish_info.strip():
                try:
                    publish_data = json.loads(publish_info)
                except json.JSONDecodeError:
                    publish_data = {}
            else:
                publish_data = publish_info if isinstance(publish_info, dict) else {}
            for appmsg in (publish_data or {}).get("appmsgex", []):
                link = normalize_article_url(appmsg.get("link") or "")
                if not link:
                    continue
                if link in seen_links:
                    skipped_already += 1
                    consecutive_seen += 1
                    if stop_after_seen > 0 and consecutive_seen >= stop_after_seen:
                        # 列表新→旧：连续命中已抓文章说明已进入"老区"，后面全是抓过的，提前收工
                        return articles, skipped_already
                    continue
                consecutive_seen = 0
                ct = appmsg.get("create_time")
                if until_ts is not None and isinstance(ct, (int, float)) and ct > until_ts:
                    continue
                if since_ts is not None and isinstance(ct, (int, float)) and ct < since_ts:
                    past_window = True
                    break
                seen_links.add(link)
                articles.append({
                    "title": appmsg.get("title") or "",
                    "digest": appmsg.get("digest") or "",
                    "link": link,
                    "cover": appmsg.get("cover") or "",
                    "update_time": appmsg.get("update_time"),
                    "create_time": appmsg.get("create_time"),
                })
                if len(articles) >= limit:
                    return articles, skipped_already
            if past_window:
                break
        if past_window:
            break
        begin += ARTICLE_LIST_PAGE_SIZE
        if len(publish_list) < ARTICLE_LIST_PAGE_SIZE:
            break

    return articles, skipped_already


def score_account(account: dict[str, Any], seed: dict[str, Any]) -> int:
    nickname = normalize_text(account.get("nickname"))
    alias = normalize_text(account.get("alias"))
    seed_nickname = normalize_text(seed.get("nickname"))
    seed_alias = normalize_text(seed.get("alias"))
    score = 0
    if seed_alias and alias == seed_alias:
        score += 100
    if seed_nickname and nickname == seed_nickname:
        score += 80
    if seed_alias and seed_alias in alias:
        score += 30
    if seed_nickname and seed_nickname in nickname:
        score += 20
    return score


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def normalize_article_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    important = []
    for key in ("__biz", "mid", "idx", "sn"):
        value = query.get(key, [None])[0]
        if value:
            important.append(f"{key}={value}")
    if important:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{'&'.join(important)}"
    return url


def is_same_article(left: str, right: str) -> bool:
    return bool(left and right and normalize_article_url(left) == normalize_article_url(right))


# --------------------------------------------------------------------------- #
# 去重清单持久化
# --------------------------------------------------------------------------- #
def load_ok_links(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.exists():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return out
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("status") == "ok" and item.get("url"):
                out.add(normalize_article_url(item["url"]))
    return out


def load_manifest(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.exists():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return out
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item:
                out.add(normalize_article_url(item))
    return out


def write_manifest(path: Path, links: list[str]) -> None:
    try:
        path.write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- #
# 输出目录
# --------------------------------------------------------------------------- #
def prepare_output_dir(config: AppConfig, account_name: str, resume_dir: Path | None = None, want_html: bool = True) -> Path:
    if resume_dir is not None:
        output_dir = Path(resume_dir).resolve()
        (output_dir / "markdown").mkdir(parents=True, exist_ok=True)
        return output_dir
    config.output_root.mkdir(parents=True, exist_ok=True)
    run_name = f"{safe_name(account_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = config.output_root / run_name
    (output_dir / "markdown").mkdir(parents=True, exist_ok=True)
    if want_html:
        (output_dir / "html").mkdir(parents=True, exist_ok=True)
    return output_dir


async def download_articles(
    *, cookies: dict[str, str], articles: list[dict[str, Any]], output_dir: Path,
    account: dict[str, Any], concurrency: int, start_index: int = 1, write_html: bool = True,
    limiter: RateLimiter | None = None, max_retries: int = 6, backoff_base: float = 3.0,
) -> list[dict[str, Any]]:
    limiter = limiter or RateLimiter(DEFAULT_THROTTLE["dl_min_delay"], DEFAULT_THROTTLE["dl_max_jitter"])
    semaphore = asyncio.Semaphore(max(concurrency, 1))
    async with build_async_client(cookies) as client:
        tasks = [
            download_single_article(
                client=client, semaphore=semaphore, index=index, article=article,
                output_dir=output_dir, account=account, write_html=write_html,
                limiter=limiter, max_retries=max_retries, backoff_base=backoff_base,
            )
            for index, article in enumerate(articles, start=start_index)
        ]
        return await asyncio.gather(*tasks)


async def download_single_article(
    *, client: httpx.AsyncClient, semaphore: asyncio.Semaphore, index: int,
    article: dict[str, Any], output_dir: Path, account: dict[str, Any],
    write_html: bool = True, limiter: RateLimiter | None = None,
    max_retries: int = 6, backoff_base: float = 3.0,
) -> dict[str, Any]:
    limiter = limiter or RateLimiter(DEFAULT_THROTTLE["dl_min_delay"], DEFAULT_THROTTLE["dl_max_jitter"])
    base_name = f"{index:03d}_{safe_name(article.get('title') or '未命名文章')}"
    markdown_path = output_dir / "markdown" / f"{base_name}.md"
    html_path = output_dir / "html" / f"{base_name}.html"

    # 幂等：已存在且非空的 Markdown 直接复用，不再下载
    if markdown_path.exists() and markdown_path.stat().st_size > 0:
        return {
            "status": "ok", "index": index, "title": article.get("title"),
            "url": article["link"], "markdown_file": str(markdown_path),
            "html_file": str(html_path), "publish_time": None, "cached": True,
        }

    async with semaphore:
        await limiter.wait_async()
        last_err: Exception | None = None
        for attempt in range(max(1, max_retries)):
            try:
                response = await client.get(article["link"])
                response.raise_for_status()
                parsed = parse_article_content(response.text, article)
                markdown_path.write_text(build_markdown_document(parsed, article, account), encoding="utf-8")
                if write_html:
                    html_path.write_text(response.text, encoding="utf-8")
                return {
                    "status": "ok", "index": index,
                    "title": parsed["title"] or article["title"],
                    "url": article["link"], "markdown_file": str(markdown_path),
                    "html_file": str(html_path), "publish_time": parsed.get("publish_time"),
                }
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_err = exc
                if attempt >= max(1, max_retries) - 1:
                    break
                wait = backoff_base * (2 ** attempt) + random.uniform(0, 1.0)
                log_err(f"[下载重试] #{index} 第{attempt + 1}次失败：{exc}；{wait:.1f}s 后重试")
                await asyncio.sleep(wait)
    return {
        "status": "error", "index": index, "title": article.get("title"),
        "url": article.get("link"), "error": str(last_err),
    }


def parse_article_content(html_text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser")
    content_node = soup.select_one("#js_content") or soup.body
    title_node = soup.select_one("#activity-name")
    account_node = soup.select_one("#js_name")

    if content_node:
        for selector in [
            "script", "style", "#js_pc_qr_code", ".qr_code_pc_outer",
            ".original_primary_card", ".wx_profile_card_inner", ".discuss_container", "iframe",
        ]:
            for tag in content_node.select(selector):
                tag.decompose()
        for image in content_node.select("img"):
            data_src = image.get("data-src")
            if data_src:
                image["src"] = data_src

    title = title_node.get_text(" ", strip=True) if title_node else fallback.get("title") or ""
    account_name = account_node.get_text(" ", strip=True) if account_node else ""
    publish_time = parse_publish_time(html_text)
    content_html = str(content_node) if content_node else ""
    markdown = clean_markdown(html_to_markdown(content_html, heading_style="ATX"))

    return {
        "title": title,
        "account_name": account_name,
        "publish_time": publish_time,
        "markdown": markdown,
    }


def parse_publish_time(html_text: str) -> str | None:
    # 优先取中国展示时间（ct 为 UTC 秒，转 UTC+8），与过滤窗口一致
    match = re.search(r'var\s+ct\s*=\s*"(\d+)";', html_text)
    if not match:
        match = re.search(r'"ct":(\d+)', html_text)
    if not match:
        return None
    return ts_to_cn_str(int(match.group(1)))


def clean_markdown(content: str) -> str:
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def build_markdown_document(parsed: dict[str, Any], article: dict[str, Any], account: dict[str, Any]) -> str:
    lines = [
        f"# {parsed['title'] or article.get('title') or '未命名文章'}",
        "",
        f"- 公众号：{parsed.get('account_name') or account.get('nickname') or ''}",
        f"- 账号别名：{account.get('alias') or ''}",
        f"- 发布时间：{parsed.get('publish_time') or ''}",
        f"- 原文链接：{article.get('link') or ''}",
        "",
        "---",
        "",
        parsed.get("markdown") or "",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def safe_name(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:80] or "未命名"


def safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"接口返回不是 JSON：{response.text[:200]}") from exc
    check_base_resp(data)
    return data


if __name__ == "__main__":
    raise SystemExit(main())
