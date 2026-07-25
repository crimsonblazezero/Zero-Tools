#!/usr/bin/env python3
"""
KovaScape Daily Report - 主编排器
===================================

全流程：数据聚合 → 规则引擎 → HTML 渲染 → 待办分发 → 钉钉推送

使用方式：
  python main.py                         # mock 数据（开发测试）
  python main.py --mode real             # 领星 MCP 真实数据
  python main.py --date 2026-07-26       # 指定日期
  python main.py --skip-webhook          # 跳过钉钉推送
  python main.py --skip-dispatcher       # 跳过待办分发

依赖：
  pip install pyyaml requests jinja2
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# ============================================
# 日志
# ============================================

logger = logging.getLogger("kovascape")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(h)

# ============================================
# 路径
# ============================================

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_report_date() -> str:
    """美西昨天（夏令时 PDT=UTC-7, 冬令时 PST=UTC-8）"""
    now = datetime.now(timezone.utc)
    # PST = UTC-8, PDT = UTC-7（3月第2周日~11月第1周日）
    # 简化：4月-10月用PDT(-7)，11月-3月用PST(-8)
    month = now.month
    offset = -7 if 4 <= month <= 10 else -8
    us_pacific = now + timedelta(hours=offset)
    return (us_pacific - timedelta(days=1)).strftime("%Y-%m-%d")


def run_step(step_name: str, cmd: list, timeout: int = 300) -> bool:
    """运行一个步骤并记录"""
    logger.info(f"[{step_name}] 开始: {' '.join(str(a)[:60] for a in cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", shell=False, timeout=timeout)
    if proc.returncode == 0:
        logger.info(f"[{step_name}] ✅ 完成")
        return True
    else:
        logger.error(f"[{step_name}] ❌ 失败 (rc={proc.returncode})")
        if proc.stderr.strip():
            logger.error(f"  stderr: {proc.stderr[:500]}")
        if proc.stdout.strip():
            logger.error(f"  stdout: {proc.stdout[:500]}")
        return False


# ============================================
# 步骤 1: 数据聚合 (data_layer)
# ============================================

def step_data_layer(mode: str, date: str) -> bool:
    python = sys.executable
    script = SCRIPTS_DIR / "data_layer.py"
    return run_step("数据聚合", [python, str(script), mode, date])


# ============================================
# 步骤 2: 规则引擎 (rule_engine)
# ============================================

def step_rule_engine(date: str) -> bool:
    python = sys.executable
    script = SCRIPTS_DIR / "rule_engine.py"
    snapshot = OUTPUT_DIR / f"snapshot-{date}.json"
    return run_step("规则引擎", [python, str(script), str(snapshot)])


# ============================================
# 步骤 3: HTML 渲染 (html_renderer)
# ============================================

def step_html_renderer(date: str) -> Optional[str]:
    """渲染 HTML 并返回输出路径"""
    python = sys.executable
    script = SCRIPTS_DIR / "html_renderer.py"
    snapshot = OUTPUT_DIR / f"snapshot-{date}.json"
    alerts = OUTPUT_DIR / f"alerts-{date}.json"
    html = OUTPUT_DIR / f"{date}.html"

    args = [python, str(script), str(snapshot), str(alerts), str(html)]
    ok = run_step("HTML渲染", args)
    if ok:
        return str(html)
    return None


# ============================================
# 步骤 4: 待办分发 (todo_dispatcher)
# ============================================

def step_todo_dispatcher(date: str, deploy_url: str) -> bool:
    python = sys.executable
    script = SCRIPTS_DIR / "todo_dispatcher.py"
    alerts = OUTPUT_DIR / f"alerts-{date}.json"
    report_url = f"{deploy_url}/{date}.html"
    return run_step("待办分发", [python, str(script), str(alerts), report_url])


# ============================================
# 步骤 5: 钉钉推送 (webhook_pusher)
# ============================================

def step_webhook_push(date: str, deploy_url: str, config: Dict) -> bool:
    """推送 Action Card 到钉钉群"""
    sys.path.insert(0, str(SCRIPTS_DIR))
    from webhook_pusher import push_daily_report

    alerts = str(OUTPUT_DIR / f"alerts-{date}.json")
    snapshot = str(OUTPUT_DIR / f"snapshot-{date}.json")
    report_url = f"{deploy_url}/{date}.html"

    return push_daily_report(alerts, snapshot, report_url, config, logger)


# ============================================
# 步骤 6: 清理旧报告（保留 retain_days 天）
# ============================================

def step_cleanup(config: Dict):
    retain = config.get("output", {}).get("retain_days", 30)
    cutoff = datetime.now() - timedelta(days=retain)
    deleted = 0
    for f in OUTPUT_DIR.glob("*.html"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                deleted += 1
        except Exception:
            pass
    if deleted:
        logger.info(f"[清理] 删除 {deleted} 份旧报告")


# ============================================
# 主流程
# ============================================

def main():
    parser = argparse.ArgumentParser(description="KovaScape Daily Report")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock",
                        help="数据源模式 (默认 mock)")
    parser.add_argument("--date", type=str, default=None,
                        help="报告日期 YYYY-MM-DD (默认美西昨天)")
    parser.add_argument("--skip-dispatcher", action="store_true",
                        help="跳过待办分发")
    parser.add_argument("--skip-webhook", action="store_true",
                        help="跳过钉钉推送")
    parser.add_argument("--deploy-url", type=str, default=None,
                        help="部署 URL 覆盖 config.yaml 中的值")
    args = parser.parse_args()

    config = load_config()
    date = args.date or config.get("_report_date") or get_report_date()
    deploy_url = args.deploy_url or config.get("output", {}).get("deploy_url",
                        "https://d70f70b3d5174e90a35cc59ddab837cc.app.codebuddy.work")
    # 解析 {date} 占位符
    deploy_url_resolved = deploy_url.replace("{date}", date)
    # deploy_url_base = 部署根目录（不含文件名，用于构造页面内锚点链接）
    deploy_url_base = deploy_url_resolved.rsplit("/", 1)[0] if "/" in deploy_url_resolved else deploy_url_resolved

    logger.info(f"\n{'='*60}")
    logger.info(f"📋 KovaScape 日报 {date}")
    logger.info(f"   模式: {args.mode}")
    logger.info(f"   部署: {deploy_url_resolved}")
    logger.info(f"{'='*60}\n")

    # 确保 output 目录存在
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Step 1: 数据聚合
    if not step_data_layer(args.mode, date):
        logger.error("❌ 数据聚合失败，终止流程")
        return 1

    # Step 2: 规则引擎
    if not step_rule_engine(date):
        logger.error("❌ 规则引擎失败，终止流程")
        return 1

    # Step 3: HTML 渲染
    html_path = step_html_renderer(date)
    if not html_path:
        logger.error("❌ HTML 渲染失败，终止流程")
        return 1

    # Step 4: 待办分发（可选）
    if not args.skip_dispatcher:
        logger.info(f"[待办分发] report_url={deploy_url_resolved}")
        step_todo_dispatcher(date, deploy_url_resolved)
    else:
        logger.info("[待办分发] ⏭ 跳过")

    # Step 5: 钉钉推送（可选）
    if not args.skip_webhook:
        step_webhook_push(date, deploy_url_resolved, config)
    else:
        logger.info("[钉钉推送] ⏭ 跳过")

    # Step 6: 清理
    step_cleanup(config)

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ KovaScape 日报 {date} 完成")
    logger.info(f"   HTML: {html_path}")
    logger.info(f"   Alerts: {OUTPUT_DIR / f'alerts-{date}.json'}")
    logger.info(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
