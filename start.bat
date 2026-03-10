@echo off
chcp 65001
echo ================================================
echo   面部表情检测系统 - 启动程序
echo ================================================
echo.

cd /d "%~dp0"

echo [1/2] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python 环境，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python 环境正常

echo.
echo [2/2] 启动应用...
python App\code\main.py

pause
