# coding:utf-8
# main_enhanced.py
"""
微信公众号爬虫工具集 v3.0 - 全自动化版本
专为Windows任务计划程序设计，无需任何用户交互，直接执行Excel全自动爬取流程。
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from automated_crawler import AutomatedCrawler

# 配置日志系统
def setup_logging():
    """设置日志系统，同时输出到控制台和文件"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = os.path.join(log_dir, f"wechat_spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



def main():
    """主程序入口 - 专注于全自动化爬取"""
    logger = setup_logging()

    logger.info("="*80)
    logger.info("🚀 微信公众号全自动爬取流程启动 🚀")
    logger.info("="*80)
    logger.info("版本: v3.0 - 全自动化版本")
    logger.info("设计用途: Windows任务计划程序自动执行")
    logger.info("执行时间: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("="*80)

    # 检查Excel文件是否存在
    excel_file = "target_articles.xlsx"
    if not os.path.exists(excel_file):
        logger.error("❌ 未找到Excel文件: %s", excel_file)
        logger.error("请确保在项目根目录下存在包含公众号信息的Excel文件。")
        sys.exit(1)

    try:
        # 启动全自动化爬取流程
        logger.info("启动全新自动化爬取流程...")
        crawler = AutomatedCrawler(excel_file)
        success = crawler.run()

        if success:
            logger.info("="*80)
            logger.info("✅ 全自动化爬取流程执行完毕")
            logger.info("详细结果请查看上方的日志输出")
            logger.info("="*80)
            sys.exit(0)
        else:
            logger.error("❌ 自动化爬取流程执行失败")
            sys.exit(1)

    except ImportError as e:
        logger.error("❌ 关键依赖库缺失: %s", str(e))
        logger.error("请确保已安装所有必要的依赖库:")
        logger.error("  pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        logger.error("❌ 自动化流程启动失败: %s", str(e))
        logger.error("详细错误信息:")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()