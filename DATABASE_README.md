# 微信公众号爬虫数据库功能说明

## 概述

本项目现已支持将微信公众号文章数据实时保存到MySQL数据库中。数据会按照指定的表结构自动插入，包括自动生成文章ID、设置爬取渠道等功能。

## 功能特点

- ✅ **实时保存**: 爬取到的文章数据立即保存到数据库
- ✅ **自动生成ID**: 按照指定格式自动生成文章ID (前12位时间+后4位随机数)
- ✅ **数据完整性**: 自动设置创建时间、更新时间等字段
- ✅ **错误处理**: 完善的数据库连接和错误处理机制
- ✅ **配置灵活**: 支持自定义数据库连接参数
- ✅ **兼容性**: 保持原有文件保存功能，可同时使用

## 数据库配置

### 数据库信息
- **地址**: 127.0.0.1:3306
- **用户名**: root
- **密码**: root
- **数据库名**: xuanfa
- **表名**: fx_article_records

### 表结构
数据库表结构定义在 `fx_article_records.sql` 文件中，主要字段包括：

| 字段名 | 类型 | 说明 | 数据来源 |
|--------|------|------|----------|
| `id` | bigint | 自增主键 | 自动生成 |
| `crawl_time` | datetime | 爬取时间 | 爬虫运行时间 |
| `crawl_channel` | varchar(50) | 爬取渠道 | 固定值"微信公众号" |
| `unit_name` | varchar(100) | 单位名称 | 公众号名称 |
| `article_title` | varchar(255) | 文章标题 | 从微信API获取 |
| `article_content` | text | 文章内容 | 从文章页面解析 |
| `publish_time` | datetime | 文章发布时间 | 从微信API获取 |
| `view_count` | int | 浏览次数/阅读量 | 从微信API获取 |
| `article_url` | varchar(500) | 文章链接 | 从微信API获取 |
| `article_id` | varchar(100) | 文章ID | 自动生成(格式:YYYYMMDDHHMM+4位随机数) |
| `create_time` | datetime | 记录创建时间 | 保存到数据库的时间 |
| `update_time` | datetime | 记录更新时间 | 保存到数据库的时间 |

## 安装和配置

### 1. 安装依赖

运行安装脚本自动安装数据库相关依赖：

```bash
python install_database_dependencies.py
```

或手动安装：

```bash
pip install pymysql>=1.0.0
```

### 2. 数据库准备

1. 确保MySQL服务已启动
2. 创建数据库 `xuanfa`
3. 执行 `fx_article_records.sql` 创建表结构

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS xuanfa CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- 使用数据库
USE xuanfa;

-- 执行fx_article_records.sql中的建表语句
```

### 3. 配置数据库连接

编辑 `database_config.py` 文件，修改数据库连接参数：

```python
DATABASE_CONFIG = {
    'host': '127.0.0.1',      # 数据库地址
    'port': 3306,             # 数据库端口
    'user': 'root',           # 用户名
    'password': 'root',       # 密码
    'database': 'xuanfa'      # 数据库名
}
```

## 使用方法

### 方法1: 使用示例脚本

运行带数据库功能的示例脚本：

```bash
python database_crawler_example.py
```

按提示输入：
- appmsg_token
- biz
- cookie
- 公众号名称
- 页数范围
- 是否获取文章内容

### 方法2: 在代码中使用

```python
from enhanced_wx_crawler import EnhancedWxCrawler

# 数据库配置
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'xuanfa'
}

# 创建爬虫实例
crawler = EnhancedWxCrawler(
    appmsg_token="your_token",
    biz="your_biz",
    cookie="your_cookie",
    begin_page_index=0,
    end_page_index=5,
    save_to_file=True,        # 同时保存到文件
    get_content=True,         # 获取文章内容
    unit_name="公众号名称",    # 必填：公众号名称
    save_to_db=True,          # 启用数据库保存
    db_config=db_config       # 数据库配置
)

# 开始爬取
articles = crawler.run()
```

### 方法3: 直接使用数据库管理器

```python
from database_manager import DatabaseManager

# 创建数据库管理器
with DatabaseManager() as db:
    # 插入单篇文章
    article_data = {
        'title': '文章标题',
        'content': '文章内容',
        'url': 'https://mp.weixin.qq.com/s/xxx',
        'pub_time': '2025-08-05 20:00:00',
        'crawl_time': '2025-08-05 22:00:00',
        'unit_name': '公众号名称',
        'view_count': 1000
    }
    
    success = db.insert_article(article_data)
    print(f"插入结果: {success}")
    
    # 获取文章总数
    count = db.get_articles_count()
    print(f"数据库中共有 {count} 篇文章")
```

## 文章ID生成规则

文章ID按以下格式自动生成：
- **格式**: `YYYYMMDDHHMM` + `XXXX`
- **前12位**: 爬取时间 (年月日时分)
- **后4位**: 随机数字

**示例**: `2025080522300001`
- `202508052230`: 2025年8月5日22点30分
- `0001`: 随机生成的4位数字

## 数据流程

1. **爬取文章列表**: 从微信公众号API获取文章基本信息
2. **获取文章内容**: 访问文章页面解析内容 (可选)
3. **数据处理**: 
   - 添加公众号名称 (`unit_name`)
   - 设置爬取渠道为"微信公众号"
   - 生成唯一文章ID
   - 设置创建和更新时间
4. **实时保存**: 每获取一篇文章立即保存到数据库
5. **文件备份**: 同时保存到Excel和JSON文件 (可选)

## 错误处理

- **数据库连接失败**: 自动重试连接，失败时只保存到文件
- **插入失败**: 记录错误日志，继续处理下一篇文章
- **数据验证**: 自动验证必填字段，缺失时使用默认值

## 监控和日志

- 实时显示保存状态
- 详细的错误日志记录
- 爬取完成后显示统计信息

## 注意事项

1. **数据库权限**: 确保数据库用户有INSERT权限
2. **字符编码**: 使用utf8mb4编码支持emoji等特殊字符
3. **网络稳定**: 数据库连接需要稳定的网络环境
4. **存储空间**: 文章内容可能较大，注意数据库存储空间
5. **并发控制**: 避免多个爬虫实例同时写入相同数据

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置是否正确
   - 确认数据库和表是否存在

2. **插入数据失败**
   - 检查表结构是否正确
   - 验证数据类型是否匹配
   - 查看错误日志获取详细信息

3. **中文乱码**
   - 确保数据库使用utf8mb4编码
   - 检查连接字符集设置

### 测试数据库功能

运行测试脚本：

```bash
python database_crawler_example.py
# 选择选项 2: 测试数据库操作
```

## 更新日志

- **v1.0**: 初始版本，支持基本的数据库保存功能
- **v1.1**: 添加自动重连和错误处理
- **v1.2**: 优化文章ID生成算法
- **v1.3**: 增加配置文件和安装脚本
