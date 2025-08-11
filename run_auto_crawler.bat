@echo off
REM 微信公众号全自动爬取批处理脚本
REM 用于Windows任务计划程序调用

echo ========================================
echo 微信公众号全自动爬取程序启动
echo 启动时间: %date% %time%
echo ========================================

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH环境变量
    echo 请确保Python已正确安装并配置
    pause
    exit /b 1
)

REM 检查必要文件是否存在
if not exist "target_articles.xlsx" (
    echo 错误: 未找到target_articles.xlsx文件
    echo 请确保Excel文件存在并包含正确的公众号信息
    pause
    exit /b 1
)

REM 创建logs目录（如果不存在）
if not exist "logs" mkdir logs

echo 正在启动微信公众号全自动爬取程序...
echo.

REM 执行Python脚本
python main.py

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo ========================================
    echo 程序执行失败，请查看日志文件获取详细信息
    echo 日志文件位置: logs目录
    echo ========================================
    REM 在任务计划程序中运行时，不要暂停
    REM pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo 程序执行成功完成
    echo 结束时间: %date% %time%
    echo 请查看data目录获取爬取结果
    echo ========================================
    REM 在任务计划程序中运行时，不要暂停
    REM pause
    exit /b 0
)
