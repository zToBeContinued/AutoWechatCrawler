# automated_crawler.py
"""
全新的全自动化爬虫控制器 - 支持多公众号
"""
import logging
import time
import os
import json
import pandas as pd
from read_cookie import ReadCookie
from batch_readnum_spider import BatchReadnumSpider
from excel_auto_crawler import ExcelAutoCrawler
from database_manager import DatabaseManager
from database_config import get_database_config

class AutomatedCrawler:
    """
    协调整个自动化流程的控制器 - 支持多公众号:
    1. 从Excel读取所有公众号链接
    2. 对每个公众号执行完整的抓取流程:
       - 启动 mitmproxy 抓取器 (会自动设置代理)
       - 运行 UI 自动化打开微信文章以触发抓取
       - 等待并验证 Cookie 是否成功抓取
       - 停止 mitmproxy 抓取器 (会自动关闭代理)
       - 使用获取到的 Cookie 运行批量爬虫
    3. 汇总所有公众号的抓取结果
    """
    def __init__(self, excel_path="target_articles.xlsx", save_to_db=True, db_config=None):
        self.logger = logging.getLogger()
        self.excel_path = excel_path
        # 不在初始化时创建cookie_reader，每个公众号单独创建

        # 数据库相关配置
        self.save_to_db = save_to_db
        self.db_config = db_config or get_database_config()

        # 测试数据库连接
        if self.save_to_db:
            try:
                with DatabaseManager(**self.db_config) as db:
                    count = db.get_articles_count()
                    self.logger.info(f"✅ 数据库连接成功！当前有 {count} 篇文章")
            except Exception as e:
                self.logger.error(f"❌ 数据库连接失败: {e}")
                self.logger.warning("⚠️ 将只保存到文件，不保存到数据库")
                self.save_to_db = False

    def _get_all_target_urls_from_excel(self) -> list:
        """
        从Excel文件中读取所有有效的公众号链接
        :return: 包含所有有效链接和公众号名称的列表
        """
        self.logger.info(f"正在从 {self.excel_path} 读取所有目标URL...")
        if not os.path.exists(self.excel_path):
            self.logger.error(f"Excel文件未找到: {self.excel_path}")
            return []

        try:
            df = pd.read_excel(self.excel_path)
            url_column = '文章链接' if '文章链接' in df.columns else 'url'
            name_column = '公众号名称' if '公众号名称' in df.columns else 'name'

            if url_column not in df.columns:
                self.logger.error("Excel中未找到 '文章链接' 或 'url' 列。")
                return []

            valid_targets = []
            for index, row in df.iterrows():
                url = row[url_column]
                name = row.get(name_column, f"公众号_{index+1}") if name_column in df.columns else f"公众号_{index+1}"

                if pd.notna(url) and 'mp.weixin.qq.com' in str(url):
                    valid_targets.append({
                        'name': str(name),
                        'url': str(url),
                        'index': index + 1
                    })
                    self.logger.info(f"找到有效目标 {index+1}: {name} - {str(url)[:50]}...")

            self.logger.info(f"共找到 {len(valid_targets)} 个有效的公众号目标")
            return valid_targets

        except Exception as e:
            self.logger.error(f"读取Excel文件失败: {e}")
            return []

    def run(self):
        """执行完整的多公众号自动化流程"""
        self.logger.info("="*80)
        self.logger.info("🚀 多公众号全新自动化流程启动 🚀")
        self.logger.info("="*80)

        # 获取所有目标公众号
        all_targets = self._get_all_target_urls_from_excel()
        if not all_targets:
            self.logger.error("❌ 未找到任何有效的公众号链接，流程中止。")
            return False

        self.logger.info(f"📋 共找到 {len(all_targets)} 个公众号，开始逐个处理...")

        # 用于存储所有公众号的抓取结果
        all_results = []
        successful_count = 0
        failed_count = 0

        try:
            for i, target in enumerate(all_targets, 1):
                self.logger.info("="*60)
                self.logger.info(f"📍 处理第 {i}/{len(all_targets)} 个公众号: {target['name']}")
                self.logger.info("="*60)

                # 为每个公众号创建独立的Cookie抓取器
                cookie_reader = None
                try:
                    # 步骤1: 为每个公众号创建独立的Cookie抓取器
                    self.logger.info(f"[步骤 1/5] 为 '{target['name']}' 创建独立的 Cookie 抓取器...")
                    cookie_reader = ReadCookie()  # 每个公众号独立创建，会删除旧文件

                    if not cookie_reader.start_cookie_extractor():
                        self.logger.error(f"❌ 公众号 '{target['name']}' Cookie 抓取器启动失败，跳过此公众号")
                        failed_count += 1
                        continue
                    self.logger.info("✅ Cookie 抓取器已在后台运行。")

                    # 步骤2: 运行 UI 自动化触发抓取
                    self.logger.info(f"[步骤 2/5] 为 '{target['name']}' 启动 UI 自动化...")
                    try:
                        ui_crawler = ExcelAutoCrawler()
                        # 直接传递当前公众号的URL，并传递cookie_reader以启用智能刷新停止
                        success = ui_crawler.automation.send_and_open_latest_link(target['url'], cookie_reader=cookie_reader)
                        if not success:
                            self.logger.error(f"❌ 公众号 '{target['name']}' UI 自动化触发失败，跳过此公众号")
                            cookie_reader.stop_cookie_extractor()
                            failed_count += 1
                            continue
                    except Exception as e:
                        self.logger.error(f"❌ 公众号 '{target['name']}' UI 自动化过程中发生错误: {e}")
                        cookie_reader.stop_cookie_extractor()
                        failed_count += 1
                        continue
                    self.logger.info("✅ UI 自动化已成功触发链接打开。")

                    # 步骤3: 等待并验证 Cookie
                    self.logger.info(f"[步骤 3/5] 等待 '{target['name']}' 的 Cookie 数据...")
                    if not cookie_reader.wait_for_new_cookie(timeout=120):
                        self.logger.error(f"❌ 公众号 '{target['name']}' 等待 Cookie 超时，跳过此公众号")
                        cookie_reader.stop_cookie_extractor()
                        failed_count += 1
                        continue

                    # 验证cookie是否有效
                    auth_info = cookie_reader.get_latest_cookies()
                    if not auth_info:
                        self.logger.error(f"❌ 公众号 '{target['name']}' Cookie 解析失败")
                        self.logger.error("💡 可能的原因:")
                        self.logger.error("   1. mitmproxy 没有成功抓取到微信请求")
                        self.logger.error("   2. 微信内置浏览器没有正确打开链接")
                        self.logger.error("   3. 网络连接问题或代理设置问题")
                        self.logger.error("💡 建议:")
                        self.logger.error("   1. 检查微信是否正常打开了文章链接")
                        self.logger.error("   2. 手动在微信中刷新文章页面")
                        self.logger.error("   3. 确保网络连接正常")
                        cookie_reader.stop_cookie_extractor()
                        failed_count += 1
                        continue
                    self.logger.info("✅ 成功获取并验证了新的 Cookie。")

                    # 步骤4: 停止 mitmproxy 抓取器
                    self.logger.info(f"[步骤 4/5] 停止 '{target['name']}' 的 Cookie 抓取器...")
                    cookie_reader.stop_cookie_extractor()
                    time.sleep(3)  # 等待代理完全关闭
                    self.logger.info("✅ Cookie 抓取器已停止，系统代理已恢复。")

                    # 步骤5: 运行批量爬虫（带Cookie重新抓取机制）
                    self.logger.info(f"[步骤 5/5] 开始爬取 '{target['name']}' 的文章...")

                    max_attempts = 2  # 最多尝试2次（第一次失败后重新抓取Cookie再试一次）
                    batch_spider = None

                    for attempt in range(max_attempts):
                        try:
                            self.logger.info(f"🔄 第 {attempt + 1}/{max_attempts} 次尝试爬取...")
                            batch_spider = BatchReadnumSpider(
                                auth_info=auth_info,
                                save_to_db=self.save_to_db,
                                db_config=self.db_config,
                                unit_name=target['name']
                            )

                            # 先验证Cookie
                            if not batch_spider.validate_cookie():
                                if attempt < max_attempts - 1:
                                    self.logger.warning("⚠️ Cookie验证失败（ret=-3），准备重新抓取Cookie...")

                                    # 重新抓取Cookie
                                    self.logger.info("🔄 重新启动Cookie抓取器...")
                                    fresh_cookie_reader = ReadCookie()
                                    if not fresh_cookie_reader.start_cookie_extractor():
                                        self.logger.error("❌ 重新启动Cookie抓取器失败")
                                        break

                                    # 重新触发UI自动化
                                    self.logger.info("🔄 重新触发UI自动化...")
                                    ui_crawler = ExcelAutoCrawler()
                                    success = ui_crawler.automation.send_and_open_latest_link(target['url'], cookie_reader=fresh_cookie_reader)
                                    if not success:
                                        self.logger.error("❌ 重新触发UI自动化失败")
                                        fresh_cookie_reader.stop_cookie_extractor()
                                        break

                                    # 等待新Cookie
                                    if not fresh_cookie_reader.wait_for_new_cookie(timeout=120):
                                        self.logger.error("❌ 重新等待Cookie超时")
                                        fresh_cookie_reader.stop_cookie_extractor()
                                        break

                                    # 获取新的认证信息
                                    auth_info = fresh_cookie_reader.get_latest_cookies()
                                    fresh_cookie_reader.stop_cookie_extractor()
                                    time.sleep(3)

                                    if not auth_info:
                                        self.logger.error("❌ 重新获取Cookie失败")
                                        break

                                    self.logger.info("✅ 成功重新获取Cookie，继续尝试...")
                                    continue
                                else:
                                    self.logger.error("❌ 多次尝试后Cookie仍然无效")
                                    break

                            # Cookie有效，开始正式爬取
                            self.logger.info("✅ Cookie验证成功，开始正式爬取...")
                            batch_spider.batch_crawl_readnum()
                            break  # 成功完成，跳出重试循环

                        except Exception as e:
                            self.logger.error(f"❌ 第 {attempt + 1} 次尝试时发生异常: {e}")
                            if attempt < max_attempts - 1:
                                self.logger.info("🔄 准备重试...")
                                time.sleep(5)
                            else:
                                self.logger.error("❌ 所有尝试都失败了")

                    if not batch_spider or not batch_spider.articles_data:
                        self.logger.error(f"❌ 公众号 '{target['name']}' 爬取失败")
                        failed_count += 1
                        continue

                    if batch_spider.articles_data:
                        # 为每篇文章添加公众号信息
                        for article in batch_spider.articles_data:
                            article['公众号名称'] = target['name']
                            article['公众号序号'] = i

                        all_results.extend(batch_spider.articles_data)

                        # 保存当前公众号的数据
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        excel_file = batch_spider.save_to_excel(f"./data/readnum_batch/readnum_{target['name']}_{timestamp}.xlsx")
                        json_file = batch_spider.save_to_json(f"./data/readnum_batch/readnum_{target['name']}_{timestamp}.json")

                        self.logger.info(f"✅ 公众号 '{target['name']}' 爬取完成！获取 {len(batch_spider.articles_data)} 篇文章")
                        self.logger.info(f"📊 数据已保存到: {excel_file}")
                        successful_count += 1
                    else:
                        self.logger.warning(f"⚠️ 公众号 '{target['name']}' 未获取到任何文章数据")
                        failed_count += 1

                    # 公众号间延迟，避免频繁请求
                    if i < len(all_targets):
                        delay_time = 15
                        self.logger.info(f"⏳ 公众号间延迟 {delay_time} 秒...")
                        time.sleep(delay_time)

                except Exception as e:
                    self.logger.error(f"❌ 处理公众号 '{target['name']}' 时发生错误: {e}")
                    # 确保停止抓取器
                    if cookie_reader:
                        try:
                            cookie_reader.stop_cookie_extractor()
                        except:
                            pass
                    failed_count += 1
                    continue

        except Exception as e:
            self.logger.error(f"❌ 自动化流程发生未知严重错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

        # 汇总结果
        self.logger.info("="*80)
        self.logger.info("📊 多公众号爬取汇总结果")
        self.logger.info("="*80)
        self.logger.info(f"✅ 成功处理: {successful_count} 个公众号")
        self.logger.info(f"❌ 失败处理: {failed_count} 个公众号")
        self.logger.info(f"📄 总计文章: {len(all_results)} 篇")

        # 汇总数据保存功能已移除

        self.logger.info("="*80)
        self.logger.info("✅ 多公众号全新自动化流程执行完毕 ✅")
        self.logger.info("="*80)

        return successful_count > 0  # 只要有一个成功就算成功
