@echo off
chcp 65001 >nul
title make-jobs-ai 安装向导

echo ========================================
echo   make-jobs-ai 安装向导
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 16+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/5] 创建 Python 虚拟环境...
cd /d "%~dp0backend"
python -m venv venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo [2/5] 安装 Python 依赖...
call venv\Scripts\activate.bat
pip install -e .
if errorlevel 1 (
    echo [错误] 安装 Python 依赖失败
    pause
    exit /b 1
)

echo [3/5] 安装 Playwright 浏览器...
playwright install chromium
if errorlevel 1 (
    echo [警告] Playwright 浏览器安装失败，岗位爬取功能可能不可用
)

echo [4/5] 安装前端依赖...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo [错误] 安装前端依赖失败
    pause
    exit /b 1
)

echo [5/5] 创建配置文件...
cd /d "%~dp0"
if not exist .env (
    copy .env.example .env >nul
    echo 已创建 .env 配置文件，可在「API 设置」中配置密钥
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 双击 start.bat 启动应用
echo.
pause
