@echo off
chcp 65001 >nul
title 微信公众号爬虫数据库版本

echo.
echo ========================================
echo   微信公众号爬虫数据库版本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

REM 检查是否在正确的目录
if not exist "run_database_crawler.py" (
    echo ❌ 未找到 run_database_crawler.py 文件
    echo 请确保在正确的项目目录中运行此脚本
    pause
    exit /b 1
)

echo ✅ 项目文件检查通过

REM 运行主程序
echo.
echo 🚀 启动微信公众号爬虫数据库版本...
echo.

python run_database_crawler.py

echo.
echo 程序已结束
pause
