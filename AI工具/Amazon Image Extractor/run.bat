@echo off
cd /d "%~dp0"

:: Bypass VPN loopback proxy for CDP connection
set NO_PROXY=localhost,127.0.0.1,::1
set no_proxy=localhost,127.0.0.1,::1

echo ==================================================
echo   Amazon Image Extractor (亚马逊图片链接提取工具)
echo ==================================================
echo.

:: 1. Locate the Python script
set RUN_FILE=
if exist src\amazon_image_extractor.py set RUN_FILE=src\amazon_image_extractor.py
if exist amazon_image_extractor.py set RUN_FILE=amazon_image_extractor.py

if "%RUN_FILE%"=="" (
    echo [ERROR] 找不到主程序 amazon_image_extractor.py！
    goto end
)

:: 2. Auto detect Google Chrome
set CHROME_PATH=""
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if %CHROME_PATH%=="" (
    echo [ERROR] 未能在您的电脑上找到 Google Chrome 安装路径！
    echo 请确认您的电脑上是否安装了正版 Google Chrome 浏览器。
    goto end
)

:: 3. Select Chrome Launch Mode
echo ==================================================
echo 请选择 Chrome 启动模式 (Select Chrome Launch Mode):
echo ==================================================
echo [1] 模式一：接管日常 Chrome (推荐)
echo     - 自动强杀残留 Chrome，复用日常 Cookies，可能直接跳过验证码。
echo     - 运行前，请务必保存好日常浏览网页，脚本将自动关闭 Chrome！
echo.
echo [2] 模式二：免冲突独立调试模式 (免冲突隔离)
echo     - 不影响您当前打开的日常 Chrome，会拉起一个崭新的调试浏览器。
echo     - 首次运行或弹出验证码时，需要在此新窗口中登录亚马逊。
echo ==================================================
set CHOICE=1
set /p CHOICE="请输入数字 [1 或 2，回车默认 1]: "

if "%CHOICE%"=="2" (
    echo [INFO] 正在以【模式二：独立调试模式】启动 Chrome...
    start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data Debug" --restore-last-session
) else (
    echo [INFO] 正在以【模式一：接管日常 Chrome】启动...
    echo [INFO] 正在强行清理残留 Chrome 进程...
    taskkill /f /im chrome.exe >nul 2>&1
    timeout /t 2 /nobreak > nul
    start "" %CHROME_PATH% --remote-debugging-port=9222 --restore-last-session
)

:: Wait 4 seconds for Chrome to start
timeout /t 4 /nobreak > nul

:: 4. Try virtual environment Python first
if exist ".venv\Scripts\python.exe" (
    echo [INFO] 检测到本地虚拟环境，正在启动...
    ".venv\Scripts\python.exe" "%RUN_FILE%"
    goto end
)

:: 5. Try system Python
echo [INFO] 正在尝试通过系统 Python 启动...
python "%RUN_FILE%"
if errorlevel 1 (
    echo.
    echo [WARN] 启动失败，可能是由于缺少依赖库。正在尝试为您自动修复环境...
    echo [INFO] 正在安装库: pip install pandas openpyxl playwright playwright-stealth
    python -m pip install pandas openpyxl playwright playwright-stealth

    echo [INFO] 正在下载浏览器: python -m playwright install chromium
    python -m playwright install chromium

    echo.
    echo [INFO] 环境修复尝试完成，正在重新启动程序...
    python "%RUN_FILE%"
)

:end
echo.
echo ==================================================
pause
