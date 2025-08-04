# 微信公众号全自动爬取PowerShell脚本
# 用于Windows任务计划程序调用

param(
    [switch]$Interactive = $false
)

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Green
Write-Host "微信公众号全自动爬取程序启动" -ForegroundColor Green
Write-Host "启动时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "工作目录: $ScriptDir" -ForegroundColor Yellow

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: Python未安装或未添加到PATH环境变量" -ForegroundColor Red
    Write-Host "请确保Python已正确安装并配置" -ForegroundColor Red
    exit 1
}

# 检查必要文件是否存在
$requiredFiles = @("main_enhanced.py", "target_articles.xlsx")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "错误: 未找到文件 $file" -ForegroundColor Red
        Write-Host "请确保所有必要文件都存在" -ForegroundColor Red
        exit 1
    }
}

# 创建logs目录（如果不存在）
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "已创建logs目录" -ForegroundColor Yellow
}

Write-Host "正在启动微信公众号全自动爬取程序..." -ForegroundColor Yellow
Write-Host ""

# 执行Python脚本
try {
    if ($Interactive) {
        $result = python main_enhanced.py --interactive
    } else {
        $result = python main_enhanced.py --auto
    }
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "程序执行成功完成" -ForegroundColor Green
        Write-Host "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
        Write-Host "请查看data目录获取爬取结果" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        exit 0
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "程序执行失败，退出代码: $exitCode" -ForegroundColor Red
        Write-Host "请查看日志文件获取详细信息" -ForegroundColor Red
        Write-Host "日志文件位置: logs目录" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        exit $exitCode
    }
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "程序执行过程中发生异常: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
