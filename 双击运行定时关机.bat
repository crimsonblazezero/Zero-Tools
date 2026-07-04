@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

:: Start the app using pythonw.exe (windowless mode)
start "" ".venv\Scripts\pythonw.exe" "shutdown_app.py"
exit /b 0
