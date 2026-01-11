@echo off
chcp 65001 >nul
title TiCNet 肺结节检测系统

echo.
echo ============================================================
echo                TiCNet 肺结节检测系统
echo    Transformer in Convolutional Neural Network
echo    for Pulmonary Nodule Detection on CT Images
echo ============================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查是否在正确目录
if not exist "config.py" (
    echo ❌ 错误: 请在TiCNet项目根目录运行此脚本
    pause
    exit /b 1
)

:: 检查虚拟环境（可选）
if exist "venv\Scripts\activate.bat" (
    echo 🔧 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
)

:: 启动系统
echo 🚀 正在启动TiCNet系统...
echo.
echo 选择启动方式:
echo 1. 简化启动 (推荐)
echo 2. 完整检查启动
echo.
set /p choice=请输入选择 (1 或 2, 默认为 1): 

if "%choice%"=="2" (
    python run_system.py
) else (
    python run_system_simple.py
)

:: 如果出错，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo ❌ 系统启动失败，请检查上述错误信息
    pause
) 