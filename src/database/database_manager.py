# coding:utf-8
# database_manager.py
"""
数据库管理模块
用于将微信公众号文章数据实时插入到MySQL数据库中
"""

import pymysql
import logging
import random
import string
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

from src.database.database_config import get_table_config

class DatabaseManager:
    """数据库管理器，负责微信公众号文章数据的数据库操作"""
    
    def __init__(self, host='127.0.0.1', port=3306, user='root', password='root', database='faxuan', table_name: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.logger = logging.getLogger(__name__)

        # 读取表配置
        table_cfg = get_table_config()
        self.table_name = table_name or table_cfg.get('table_name', 'fx_article_records')
        self.crawl_channel_default = table_cfg.get('crawl_channel_default', '微信公众号')

        # 初始化数据库连接
        self.connect()
    
    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                autocommit=True,  # 自动提交
                cursorclass=pymysql.cursors.DictCursor
            )
            self.logger.info(f"✅ 数据库连接成功: {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")
    
    def is_connected(self) -> bool:
        """检查数据库连接状态"""
        try:
            if self.connection:
                self.connection.ping(reconnect=True)
                return True
        except:
            return False
        return False
    
    def reconnect(self) -> bool:
        """重新连接数据库"""
        self.logger.info("尝试重新连接数据库...")
        self.disconnect()
        return self.connect()
    
    def generate_article_id(self, crawl_time: datetime) -> str:
        """
        生成文章ID
        格式：前12位为crawl_time时间(YYYYMMDDHHMM)，后4位为随机数
        
        Args:
            crawl_time: 爬取时间
            
        Returns:
            生成的文章ID
        """
        # 前12位：年月日时分
        time_part = crawl_time.strftime('%Y%m%d%H%M')
        
        # 后4位：随机数
        random_part = ''.join(random.choices(string.digits, k=4))
        
        return time_part + random_part
    
    def insert_article(self, article_data: Dict[str, Any]) -> bool:
        """
        插入单篇文章数据到数据库
        
        Args:
            article_data: 文章数据字典，包含以下字段：
                - title: 文章标题 (必填)
                - content: 文章内容 (可选)
                - url: 文章链接 (可选)
                - pub_time: 发布时间 (可选)
                - crawl_time: 爬取时间 (必填)
                - unit_name: 单位名称 (必填)
                - view_count: 阅读量 (可选)
                - like_count: 点赞数 (可选) -> 映射到数据库的 likes 字段
                - share_count: 分享数 (可选) -> 映射到数据库的 comments 字段
                
        Returns:
            插入成功返回True，失败返回False
        """
        if not self.is_connected():
            if not self.reconnect():
                return False

        # 检查标题是否已存在（去重）
        article_title = article_data.get('title', '').strip()
        if article_title and self.check_article_title_exists(article_title):
            self.logger.info(f"⚠️ 文章标题已存在，跳过插入: {article_title}")
            return False

        try:
            # 准备数据
            current_time = datetime.now()
            crawl_time = article_data.get('crawl_time')
            
            # 如果crawl_time是字符串，转换为datetime对象
            if isinstance(crawl_time, str):
                try:
                    crawl_time = datetime.strptime(crawl_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    crawl_time = current_time
            elif not isinstance(crawl_time, datetime):
                crawl_time = current_time
            
            # 处理发布时间
            publish_time = article_data.get('pub_time')
            if isinstance(publish_time, str):
                try:
                    publish_time = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    publish_time = None
            elif not isinstance(publish_time, datetime):
                publish_time = None
            
            # 生成文章ID
            article_id = self.generate_article_id(crawl_time)
            
            # 准备插入数据
            insert_data = {
                'crawl_time': crawl_time,
                'crawl_channel': self.crawl_channel_default,  # 从配置读取默认值
                'unit_name': article_data.get('unit_name', ''),
                'article_title': article_data.get('title', ''),
                'article_content': article_data.get('content', ''),
                'publish_time': publish_time,
                'view_count': article_data.get('view_count'),
                'likes': article_data.get('like_count'),  # 映射 like_count 到 likes 字段
                'comments': article_data.get('share_count'),  # 映射 share_count 到 comments 字段
                'article_url': article_data.get('url', ''),
                'article_id': article_id,
                'create_time': current_time,
                'update_time': current_time
            }
            
            # 构建SQL语句
            sql = f"""
            INSERT INTO {self.table_name}
            (crawl_time, crawl_channel, unit_name, article_title, article_content,
             publish_time, view_count, likes, comments, article_url, article_id, create_time, update_time)
            VALUES
            (%(crawl_time)s, %(crawl_channel)s, %(unit_name)s, %(article_title)s, %(article_content)s,
             %(publish_time)s, %(view_count)s, %(likes)s, %(comments)s, %(article_url)s, %(article_id)s, %(create_time)s, %(update_time)s)
            """
            
            # 执行插入
            with self.connection.cursor() as cursor:
                cursor.execute(sql, insert_data)
            
            self.logger.info(f"✅ 文章插入成功: {article_data.get('title', 'Unknown')} (ID: {article_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 文章插入失败: {e}")
            self.logger.error(f"文章数据: {article_data}")
            return False
    
    def batch_insert_articles(self, articles_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量插入文章数据

        Args:
            articles_data: 文章数据列表

        Returns:
            包含统计信息的字典: {'success': 成功数量, 'duplicate': 重复数量, 'failed': 失败数量}
        """
        if not articles_data:
            self.logger.warning("没有文章数据需要插入")
            return {'success': 0, 'duplicate': 0, 'failed': 0}

        success_count = 0
        duplicate_count = 0
        failed_count = 0
        total_count = len(articles_data)

        self.logger.info(f"开始批量插入 {total_count} 篇文章...")

        for i, article_data in enumerate(articles_data, 1):
            try:
                article_title = article_data.get('title', 'Unknown')

                # 检查标题是否重复
                if article_data.get('title', '').strip() and self.check_article_title_exists(article_data.get('title', '').strip()):
                    duplicate_count += 1
                    self.logger.info(f"进度: {i}/{total_count} - 标题重复，跳过: {article_title}")
                    continue

                if self.insert_article(article_data):
                    success_count += 1
                    self.logger.info(f"进度: {i}/{total_count} - 成功插入文章: {article_title}")
                else:
                    failed_count += 1
                    self.logger.error(f"进度: {i}/{total_count} - 插入失败: {article_title}")

                # 添加小延迟避免数据库压力过大
                time.sleep(0.1)

            except Exception as e:
                failed_count += 1
                self.logger.error(f"批量插入第 {i} 篇文章时出错: {e}")

        result = {'success': success_count, 'duplicate': duplicate_count, 'failed': failed_count}
        self.logger.info(f"批量插入完成: 成功 {success_count} 篇，重复 {duplicate_count} 篇，失败 {failed_count} 篇")
        return result
    
    def check_article_exists(self, article_url: str) -> bool:
        """
        检查文章是否已存在（根据URL判断）

        Args:
            article_url: 文章URL

        Returns:
            存在返回True，不存在返回False
        """
        if not self.is_connected():
            if not self.reconnect():
                return False

        try:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE article_url = %s"
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (article_url,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            self.logger.error(f"检查文章是否存在时出错: {e}")
            return False

    def check_article_title_exists(self, article_title: str) -> bool:
        """
        检查文章标题是否已存在（用于去重）

        Args:
            article_title: 文章标题

        Returns:
            存在返回True，不存在返回False
        """
        if not self.is_connected():
            if not self.reconnect():
                return False

        try:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE article_title = %s"
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (article_title,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            self.logger.error(f"检查文章标题是否存在时出错: {e}")
            return False
    
    def get_articles_count(self) -> int:
        """
        获取数据库中文章总数
        
        Returns:
            文章总数
        """
        if not self.is_connected():
            if not self.reconnect():
                return 0
        
        try:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name}"
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                return result['count']
        except Exception as e:
            self.logger.error(f"获取文章总数时出错: {e}")
            return 0
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
