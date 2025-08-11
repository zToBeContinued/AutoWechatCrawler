# automated_crawler.py
"""
全新的全自动化爬虫控制器 - 支持多公众号
"""
import logging
import time
import os
import json
import pandas as pd

from src.proxy.read_cookie import ReadCookie
from src.crawler.batch_readnum_spider import BatchReadnumSpider
from src.ui.excel_auto_crawler import ExcelAutoCrawler
from src.database.database_manager import DatabaseManager
from src.database.database_config import get_database_config
from src.ui.wechat_browser_automation import WeChatBrowserAutomation, UI_AUTOMATION_AVAILABLE
from config.config_manager import get_crawler_config
from src.core.backfill_manager import BackfillManager, BackfillStageInfo

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
    def __init__(self, excel_path="target_articles.xlsx", save_to_db=True, db_config=None, crawler_config=None):
        self.logger = logging.getLogger()
        # 若未显式传入 excel_path 则使用配置中的 excel_file
        cfg_excel = (crawler_config or get_crawler_config()).get('excel_file', 'target_articles.xlsx')
        self.excel_path = excel_path if excel_path != "target_articles.xlsx" else cfg_excel
        # 配置
        self.crawler_config = crawler_config or get_crawler_config()
        self.cookie_wait_timeout = self.crawler_config.get('cookie_wait_timeout', 120)
        self.account_delay = self.crawler_config.get('account_delay', 15)
        self.days_back = self.crawler_config.get('days_back', 90)
        self.max_pages = self.crawler_config.get('max_pages', 200)
        self.articles_per_page = self.crawler_config.get('articles_per_page', 5)
        # 数据库
        self.save_to_db = save_to_db
        self.db_config = db_config or get_database_config()
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

        # 分段回填阶段决策
        backfill_mgr = BackfillManager(self.crawler_config)
        stage_info = backfill_mgr.decide_stage()
        lower_dt = upper_dt = None
        stage_label = None
        adaptive_est_pages = 0
        if stage_info:
            lower_dt, upper_dt = backfill_mgr.compute_bounds(stage_info)
            stage_label = f"{stage_info.index}/{stage_info.total} {stage_info.lower_days}->{stage_info.upper_days}d"
            self.logger.info(f"🧩 检测到分段回填阶段: {stage_label} 时间窗口 {lower_dt} -> {upper_dt}")
            adaptive_est_pages = backfill_mgr.decide_max_pages("__GLOBAL__", stage_info, self.articles_per_page)
            if adaptive_est_pages:
                self.logger.info(f"🧠 自适应估算 max_pages = {adaptive_est_pages} (全局配置 {self.max_pages})")
        else:
            self.logger.info("🧩 分段回填未启用或已完成，使用常规 days_back 窗口")
            if self.crawler_config.get('adaptive_max_pages_enabled'):
                try:
                    synthetic_stage = BackfillStageInfo(0, self.days_back, 1, 1)
                    adaptive_est_pages = backfill_mgr.decide_max_pages("__GLOBAL__", synthetic_stage, self.articles_per_page)
                    if adaptive_est_pages:
                        self.logger.info(f"🧠 非分段模式自适应估算 max_pages = {adaptive_est_pages} (全局配置 {self.max_pages})")
                except Exception as e:
                    self.logger.warning(f"⚠️ 非分段自适应估算失败: {e}")

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
                    if not cookie_reader.wait_for_new_cookie(timeout=self.cookie_wait_timeout):
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
                                    self.logger.warning("⚠️ Cookie验证失败（ret=-3），准备仅刷新文章页面以重新抓包...")

                                    # 重新抓取Cookie（仅启动抓取器，不重复粘贴点击）
                                    self.logger.info("🔄 重新启动Cookie抓取器...")
                                    fresh_cookie_reader = ReadCookie()
                                    if not fresh_cookie_reader.start_cookie_extractor():
                                        self.logger.error("❌ 重新启动Cookie抓取器失败")
                                        break

                                    # 仅刷新当前文章页面
                                    try:
                                        if not UI_AUTOMATION_AVAILABLE:
                                            self.logger.error("❌ UI自动化不可用，无法执行刷新")
                                        else:
                                            self.logger.info("🔁 不重新粘贴链接，直接刷新已打开的文章页面以触发新请求…")
                                            refresher = WeChatBrowserAutomation()
                                            # 刷新次数适当增加，提高触发概率
                                            refresher.auto_refresh_browser(refresh_count=self.crawler_config.get('refresh_count', 3),
                                                                           refresh_delay=self.crawler_config.get('refresh_delay', 3.0),
                                                                           cookie_reader=fresh_cookie_reader)
                                    except Exception as e:
                                        self.logger.warning(f"刷新文章页面时出错: {e}")

                                    # 等待新Cookie
                                    if not fresh_cookie_reader.wait_for_new_cookie(timeout=self.cookie_wait_timeout):
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

                                    self.logger.info("✅ 成功通过刷新重新获取Cookie，继续尝试...")
                                    continue
                                else:
                                    self.logger.error("❌ 多次尝试后Cookie仍然无效")
                                    break

                            # Cookie有效，开始正式爬取
                            self.logger.info("✅ Cookie验证成功，开始正式爬取...")
                            # 针对该账号的自适应估算（优先使用阶段/虚拟阶段窗口天数）
                            per_account_est = 0
                            if self.crawler_config.get('adaptive_max_pages_enabled'):
                                try:
                                    # 复用 stage_info 或构造虚拟阶段
                                    if stage_info:
                                        acct_stage = stage_info
                                    else:
                                        from src.core.backfill_manager import BackfillStageInfo
                                        acct_stage = BackfillStageInfo(0, self.days_back, 1, 1)
                                    per_account_est = BackfillManager(self.crawler_config).decide_max_pages(target['name'], acct_stage, self.articles_per_page)
                                    if per_account_est:
                                        self.logger.info(f"🧠 账号 {target['name']} 自适应估算 max_pages = {per_account_est}")
                                except Exception as e:
                                    self.logger.warning(f"⚠️ 账号级自适应估算失败: {e}")
                            effective_max_pages = per_account_est or adaptive_est_pages or self.max_pages
                            batch_spider.batch_crawl_readnum(
                                max_pages=effective_max_pages,
                                articles_per_page=self.articles_per_page,
                                days_back=self.days_back,
                                lower_bound_dt=lower_dt,
                                upper_bound_dt=upper_dt,
                                stage_label=stage_label
                            )
                            # 爬取后更新自适应统计
                            try:
                                if self.crawler_config.get('adaptive_max_pages_enabled') and hasattr(batch_spider, 'crawl_stats'):
                                    stats = batch_spider.crawl_stats
                                    if stage_info:
                                        update_stage = stage_info
                                    else:
                                        from src.core.backfill_manager import BackfillStageInfo
                                        update_stage = BackfillStageInfo(0, self.days_back, 1, 1)
                                    backfill_mgr.update_account_stats(
                                        account=target['name'],
                                        stage=update_stage,
                                        used_pages=stats.get('used_pages', 0),
                                        effective_articles=stats.get('effective_articles', 0),
                                        last_page_effective=stats.get('last_page_effective', 0),
                                        last_page_total=stats.get('last_page_total', 0),
                                        est_pages=effective_max_pages
                                    )
                                    # 漏抓预警：若未到下界且已用完估算页数
                                    if not stats.get('reached_lower_bound') and stats.get('used_pages') >= effective_max_pages:
                                        self.logger.warning(f"⚠️ 账号 {target['name']} 可能未触达时间下界，建议提升估算或增量翻页 (used_pages={stats.get('used_pages')}, est={effective_max_pages})")
                            except Exception as e:
                                self.logger.warning(f"⚠️ 更新自适应统计失败: {e}")
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
                        self.logger.info(f"⏳ 公众号间延迟 {self.account_delay} 秒...")
                        time.sleep(self.account_delay)

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

        # 若分段阶段成功且至少一个公众号有数据，则标记完成阶段
        if stage_info and successful_count > 0:
            # 粗略统计：使用的页数 = 最后一篇文章所在的页面估计（无法精确，后续可在 spider 内返回）
            backfill_mgr.mark_completed(stage_info)
            self.logger.info(f"🧩 已标记阶段完成: {stage_label}")

        # 汇总数据保存功能已移除

        self.logger.info("="*80)
        self.logger.info("✅ 多公众号全新自动化流程执行完毕 ✅")
        self.logger.info("="*80)

        return successful_count > 0  # 只要有一个成功就算成功
