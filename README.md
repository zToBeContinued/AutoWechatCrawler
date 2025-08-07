# 微信公众号爬虫

一个功能强大的微信公众号文章批量抓取工具，支持全自动化运行、多公众号处理、阅读量获取等功能。专为Windows环境设计，可配合任务计划程序实现定时自动抓取。

## 📚 文档导航

- **[快速开始](QUICK_START.md)** - 5分钟快速上手指南
- **[常见问题](FAQ.md)** - 详细的问题解答和故障排除
- **[更新日志](CHANGELOG.md)** - 版本更新历史和变更记录
- **[SSL绕过说明](SSL_BYPASS_README.md)** - SSL证书错误自动处理功能
- **[任务计划配置](Windows任务计划程序配置说明.md)** - Windows定时任务配置指南


## 🚀 快速开始

### ⚡ 三步快速部署

```bash
# 1. 下载项目
git clone https://github.com/RichardQt/AutoWechatCrawler.git
cd AutoWechatCrawler

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main_enhanced.py
```

### 📋 环境要求

- Windows 10/11 + Python 3.8+
- 微信PC版（已安装并登录）
- Chrome/Edge浏览器

### 📖 详细教程

**新手用户请查看**: [📚 快速开始指南](QUICK_START.md) - 包含详细的安装配置步骤

**遇到问题请查看**: [❓ 常见问题解答](FAQ.md) - 详细的故障排除指南

## 📋 使用方法

### 基本使用

1. **准备目标文章列表**
   - 打开 `target_articles.xlsx`
   - 在 `文章链接` 列填入微信公众号文章链接
   - 在 `公众号名称` 列填入对应的公众号名称

2. **运行自动化抓取**
```bash
python main_enhanced.py --auto
```

3. **查看结果**
   - 抓取结果保存在 `data/readnum_batch/` 目录
   - 日志文件保存在 `logs/` 目录

### 高级配置

#### 自定义Excel文件路径
```python
from automated_crawler import AutomatedCrawler

crawler = AutomatedCrawler(excel_path="custom_articles.xlsx")
crawler.run_full_automation()
```

## 🔧 Windows任务计划程序配置

为了实现定时自动抓取，可以配置Windows任务计划程序：

1. **打开任务计划程序**：`Win + R` → `taskschd.msc`

2. **创建基本任务**：
   - 任务名称：`微信公众号自动爬取`
   - 触发器：每天凌晨2:00执行
   - 操作：启动程序 `run_auto_crawler.bat`

3. **高级设置**：
   - ✅ 不管用户是否登录都要运行
   - ✅ 使用最高权限运行
   - ✅ 允许按需运行任务

详细配置说明请参考：[Windows任务计划程序配置说明.md](Windows任务计划程序配置说明.md)


## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

#### 环境变量配置

```bash
# 可选环境变量
WECHAT_SPIDER_LOG_LEVEL=INFO    # 日志级别
WECHAT_SPIDER_PROXY_PORT=8080   # 代理端口
WECHAT_SPIDER_TIMEOUT=30        # 请求超时时间
```


## 🚀 部署指南

### 开发环境部署

```bash
# 1. 克隆代码
略

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp config.example.py config.py
# 编辑config.py配置文件

# 5. 运行测试
python main_enhanced.py --test
```


## 🤝 贡献指南

### 贡献流程

1. **Fork项目**：在GitHub上Fork本项目
2. **创建分支**：`git checkout -b feature/your-feature`
3. **提交代码**：`git commit -m "Add your feature"`
4. **推送分支**：`git push origin feature/your-feature`
5. **创建PR**：在GitHub上创建Pull Request

### 代码规范

- **PEP 8**：遵循Python代码规范
- **类型注解**：使用类型注解提高代码可读性
- **文档字符串**：为函数和类添加详细文档
- **单元测试**：为新功能添加相应测试


## 📞 支持与反馈

### 获取帮助

- **GitHub Issues**：[提交Issue](https://github.com/RichardQt/AutoWechatCrawler.git/issues)
- **讨论区**：[GitHub Discussions](https://github.com/RichardQt/AutoWechatCrawler.git/discussions)
- **邮件支持**：`2837657164@qq.com`

### 常见问题

查看 [FAQ.md](docs/FAQ.md) 获取常见问题解答。

### 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本工具仅供学习和研究使用，使用者需自行承担使用风险。开发者不承担任何法律责任，请遵守相关法律法规和平台服务条款。

---

**如果这个项目对你有帮助，请给个⭐️支持一下！**
