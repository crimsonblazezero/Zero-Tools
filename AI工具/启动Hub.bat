@echo off
chcp 65001 > nul 2>&1
setlocal

:: 切换到 bat 文件所在目录（即工具文件夹）
cd /d "%~dp0"

:: 检查 Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python 未安装，请先安装 Python 3
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 端口配置
set HUB_PORT=8765
set LAUNCHER_PORT=8766

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║        KovaScape Ops Hub                 ║
echo  ║  Hub: %HUB_PORT%   Launcher: %LAUNCHER_PORT%          ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  正在启动服务，请稍候...
echo.

:: 启动 Launcher Service（后台独立窗口）
start "KovaScape Launcher" /min python launcher_service.py

:: 等待 Launcher 就绪（约 1.5 秒）
ping 127.0.0.1 -n 3 > nul

:: 延迟打开浏览器
start "" cmd /c "ping 127.0.0.1 -n 2 > nul && start http://localhost:%HUB_PORT%/kovascape-hub.html"

:: 启动 Hub 静态服务器（主窗口，关闭即停止）
echo  Hub 地址: http://localhost:%HUB_PORT%/kovascape-hub.html
echo  关闭此窗口 = 停止 Hub 服务器
echo  （Launcher 服务在独立窗口运行，可单独关闭）
echo.
python -m http.server %HUB_PORT% --bind 127.0.0.1

endlocal
