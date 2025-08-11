#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主流程封装（自动化版本）

职责：
1. 初始化日志
2. 读取配置（包含 Excel 路径等）
3. 测试数据库连接（可选）
4. 启动 AutomatedCrawler
"""

import os
import sys
import logging
from datetime import datetime
import traceback

from config import get_crawler_config, get_database_config
from src.database.database_manager import DatabaseManager
from src.core.automated_crawler import AutomatedCrawler


def setup_logging() -> logging.Logger:
    """初始化日志（同时输出到控制台与文件）"""
    logger = logging.getLogger("wechat_spider_main")
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"wechat_spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def main():
    """主程序入口 - 全自动化爬取"""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("🚀 微信公众号全自动爬取流程启动 🚀")
    logger.info("版本: v3.0 - 全自动化版本")
    logger.info("执行时间: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("=" * 80)

    # 读取爬虫配置
    crawler_cfg = get_crawler_config()
    excel_file = crawler_cfg.get('excel_file', 'target_articles.xlsx')
    if not os.path.exists(excel_file):
        logger.error("❌ 未找到 Excel 文件: %s", excel_file)
        logger.error("请在项目根目录放置目标公众号 Excel 文件 (默认: target_articles.xlsx)")
        sys.exit(1)

    # 测试数据库连接
    db_config = get_database_config()
    logger.info("🔍 测试数据库连接...")
    try:
        with DatabaseManager(**db_config) as db:
            count = db.get_articles_count()
            logger.info(f"✅ 数据库连接成功！当前已有 {count} 篇文章")
            save_to_db = True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        logger.warning("⚠️ 将仅保存到本地文件，不写入数据库")
        save_to_db = False

    try:
        logger.info("启动全自动化爬取流程...")
        crawler = AutomatedCrawler(
            excel_path=excel_file,
            save_to_db=save_to_db,
            db_config=db_config,
            crawler_config=crawler_cfg,
        )
        success = crawler.run()
        if success:
            logger.info("✅ 爬取流程完成，程序正常结束")
            sys.exit(0)
        else:
            logger.error("❌ 爬取流程失败")
            sys.exit(1)
    except ImportError as e:
        logger.error("❌ 依赖库缺失: %s", e)
        logger.error("请先安装依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error("❌ 主流程异常: %s", e)
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()