# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 2025-08-04

### 🎉 新增功能

- **全自动化运行**: 实现零人工干预的完全自动化流程
- **多公众号批量处理**: 支持从Excel文件读取多个公众号并批量处理
- **SSL错误自动绕过**: 智能检测并自动处理SSL证书错误页面
- **增强代理管理**: 全新的代理管理器，确保代理正确开关
- **智能Cookie获取**: 基于mitmproxy的自动Cookie抓取机制
- **UI自动化增强**: 改进的微信PC版UI自动化操作
- **Windows任务计划程序支持**: 专为定时任务设计的运行模式

### 🔧 改进优化

- **错误处理机制**: 完善的错误恢复和重试机制
- **日志系统**: 详细的分级日志记录系统
- **性能优化**: 优化请求频率和资源使用
- **代码重构**: 模块化设计，提高代码可维护性
- **文档完善**: 详细的使用文档和配置说明

### 🐛 问题修复

- 修复代理设置无法完全关闭的问题
- 修复Cookie获取失败时的异常处理
- 修复UI自动化在某些情况下失效的问题
- 修复Excel文件读取时的编码问题
- 修复网络异常时的程序崩溃问题

### 📁 文件结构变更

```
新增文件:
├── main_enhanced.py              # 全自动化主程序入口
├── automated_crawler.py          # 自动化爬虫控制器
├── enhanced_proxy_manager.py     # 增强代理管理器
├── wechat_browser_automation.py  # 微信浏览器自动化
├── run_auto_crawler.bat          # Windows批处理启动脚本
├── run_auto_crawler.ps1          # PowerShell启动脚本
├── SSL_BYPASS_README.md          # SSL绕过功能说明
├── Windows任务计划程序配置说明.md  # 任务计划配置文档
└── QUICK_START.md                # 快速开始指南

重构文件:
├── batch_readnum_spider.py       # 重构批量抓取器
├── cookie_extractor.py           # 重构Cookie抓取器
├── proxy_manager.py              # 重构代理管理器
└── utils.py                      # 增强工具函数
```

