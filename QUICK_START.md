# 快速开始指南

## 🎯 5分钟快速上手

### 第一步：环境准备

1. **确认系统要求**
   - Windows 10/11 系统
   - Python 3.8+ 已安装
   - 微信PC版已安装并登录

2. **下载项目**
```bash
git clone https://github.com/your-repo/wechat_spider2.git
cd wechat_spider2
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

### 第二步：配置目标文章

1. **打开Excel文件**
   - 找到项目根目录下的 `target_articles.xlsx`
   - 用Excel或WPS打开

2. **填入目标数据**
   
   | 文章链接 | 公众号名称 | 备注 |
   |----------|------------|------|
   | https://mp.weixin.qq.com/s/abc123... | 科技前沿 | 重点关注 |
   | https://mp.weixin.qq.com/s/def456... | 财经观察 | 每日更新 |

   > 💡 **提示**：文章链接必须是完整的微信公众号文章URL

### 第三步：运行程序

**最简单的方式**：双击 `run_auto_crawler.bat` 文件

**或者使用命令行**：
```bash
python main_enhanced.py --auto
```

### 第四步：查看结果

程序运行完成后，结果文件会保存在：
- **Excel格式**：`data/readnum_batch/` 目录
- **日志文件**：`logs/` 目录

## 🔧 常见问题

### Q1: 程序运行失败怎么办？

**A1**: 按以下步骤排查：

1. **检查微信状态**
   - 确认微信PC版已登录
   - 确认可以正常访问文件传输助手

2. **检查Excel文件**
   - 确认文章链接格式正确
   - 确认文件没有被其他程序占用

3. **查看日志**
   - 打开 `logs/` 目录下最新的日志文件
   - 查找错误信息

### Q2: Cookie获取失败？

**A2**: 这通常是代理设置问题：

1. **手动检查代理**
   - 打开微信 → 设置 → 通用设置 → 网络代理
   - 确认代理设置为 `127.0.0.1:8080`

2. **重启程序**
   - 关闭所有相关程序
   - 重新运行 `run_auto_crawler.bat`

### Q3: UI自动化失败？

**A3**: 检查以下几点：

1. **微信窗口状态**
   - 确认微信窗口没有被最小化
   - 确认没有弹窗遮挡

2. **系统权限**
   - 以管理员身份运行程序
   - 关闭杀毒软件的实时保护

## 📊 输出文件说明

### Excel文件结构

| 列名 | 说明 | 示例 |
|------|------|------|
| title | 文章标题 | "人工智能的未来发展" |
| publish_time | 发布时间 | "2024-01-01 12:00:00" |
| read_num | 阅读量 | 1000 |
| like_num | 点赞数 | 50 |
| share_num | 分享数 | 20 |
| url | 文章链接 | "https://mp.weixin.qq.com/s/..." |
| account_name | 公众号名称 | "科技前沿" |

### 日志文件说明

日志文件包含详细的运行信息：
- **INFO**: 正常运行信息
- **WARNING**: 警告信息（不影响运行）
- **ERROR**: 错误信息（需要处理）

## 🚀 进阶使用

### 定时自动运行

1. **配置Windows任务计划程序**
   - 参考 `Windows任务计划程序配置说明.md`
   - 设置每日自动运行

2. **批量处理多个Excel文件**
```bash
# 处理自定义Excel文件
python main_enhanced.py --excel custom_articles.xlsx --auto
```

### 自定义配置

1. **修改抓取间隔**
   - 编辑 `batch_readnum_spider.py`
   - 调整 `delay_range` 参数

2. **修改输出格式**
   - 编辑 `utils.py`
   - 自定义数据导出格式

## 📞 获取帮助

如果遇到问题：

1. **查看完整文档**：阅读 `README.md`
2. **检查日志文件**：查看 `logs/` 目录
3. **提交Issue**：在GitHub上提交问题报告

---

**祝你使用愉快！** 🎉
