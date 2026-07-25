#!/usr/bin/env bash
# 跨平台启动脚本：自动探测并准备好 venv，再转发参数给 main.py
set -e
cd "$(dirname "$0")"

# 1) 选 python 解释器：Windows 用 Scripts/python.exe，Linux/macOS 用 bin/python
if [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  # 没有 venv：用系统 python 创建并安装依赖
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  else
    PYTHON_BIN=python
  fi
  "$PYTHON_BIN" -m venv .venv
  if [ -x ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"
  else
    PY=".venv/bin/python"
  fi
  "$PY" -m pip install -r requirements.txt
  # 浏览器内核（Windows 走系统 Chrome；其余装 chromium）
  "$PY" -m playwright install chromium || true
fi

exec "$PY" main.py "$@"
