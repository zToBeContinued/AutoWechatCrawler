import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Tuple

BEIJING_TZ = timezone(timedelta(hours=8))

class BackfillStageInfo:
    def __init__(self, lower_days: int, upper_days: int, index: int, total: int):
        self.lower_days = lower_days
        self.upper_days = upper_days
        self.index = index
        self.total = total

    def __repr__(self):
        return f"BackfillStage({self.index}/{self.total}: {self.lower_days}->{self.upper_days})"

class BackfillManager:
    """分段历史回填 + 自适应翻页管理"""

    def __init__(self, config: Dict):
        crawler_cfg = config or {}
        # 分段参数
        self.enabled = crawler_cfg.get('staged_backfill_enabled', False)
        self.stages: List[int] = crawler_cfg.get('staged_backfill_stages', [])
        self.min_threshold = crawler_cfg.get('staged_backfill_min_days_threshold', 8)
        self.state_file = crawler_cfg.get('staged_backfill_state_file', 'data/runtime/backfill_state.json')
        self.target_days = crawler_cfg.get('days_back', 0)
        # 自适应参数
        self.adaptive_enabled = crawler_cfg.get('adaptive_max_pages_enabled', False)
        self.adaptive_hard_cap = crawler_cfg.get('adaptive_max_pages_hard_cap', 150)
        self.adaptive_base_daily = crawler_cfg.get('adaptive_base_daily_posts', 2)
        self.adaptive_min_pages = crawler_cfg.get('adaptive_min_pages', 5)
        self.stats_file = 'data/runtime/max_pages_stats.json'

        # 状态容器
        self.state: Dict = {}
        self.stats: Dict = {}
        self._load_state()
        self._load_stats()

    # --------------- state persistence ---------------
    def _load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
            else:
                self.state = {}
        except Exception:
            self.state = {}

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 写入回填状态文件失败: {e}")

    def _load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {}
        except Exception:
            self.stats = {}

    def _save_stats(self):
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 写入自适应统计文件失败: {e}")

    # --------------- stage decision ---------------
    def decide_stage(self) -> Optional[BackfillStageInfo]:
        if not self.enabled:
            return None
        if self.target_days < self.min_threshold:
            return None
        if not self.stages:
            return None
        stages = sorted({int(s) for s in self.stages if isinstance(s, int) and s > 0})
        stages = [s for s in stages if s <= self.target_days]
        if not stages:
            return None
        if stages[-1] != self.target_days:
            stages.append(self.target_days)
        completed: List[int] = self.state.get('completed_stages', [])
        for idx, upper in enumerate(stages):
            if upper not in completed:
                lower = 0 if idx == 0 else stages[idx-1]
                return BackfillStageInfo(lower, upper, idx + 1, len(stages))
        return None

    def mark_completed(self, stage: BackfillStageInfo):
        completed: List[int] = self.state.get('completed_stages', [])
        if stage.upper_days not in completed:
            completed.append(stage.upper_days)
            completed = sorted(set(completed))
            self.state['completed_stages'] = completed
            self.state['target_days_back'] = self.target_days
            self.state['last_run_time'] = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            self._save_state()

    # --------------- adaptive max pages ---------------
    def decide_max_pages(self, account: str, stage: BackfillStageInfo, articles_per_page: int) -> int:
        if not self.adaptive_enabled or not stage:
            return 0
        span_days = stage.upper_days - stage.lower_days
        acc_stat = self.stats.get(account, {})
        daily_avg = acc_stat.get('recent_avg_daily', self.adaptive_base_daily)
        pages_est = int((daily_avg * span_days) / max(1, articles_per_page) + 0.999)
        pages_est = int(pages_est * 1.2) if pages_est > 0 else self.adaptive_min_pages
        last_ratio = acc_stat.get('last_page_effective_ratio')
        last_used = acc_stat.get('last_used_pages')
        last_est = acc_stat.get('last_est_pages')
        if last_ratio is not None and last_used and last_est:
            if last_ratio > 0.4 and last_used >= 0.8 * last_est:
                pages_est = int(pages_est * 1.3)
            elif last_ratio < 0.1:
                pages_est = int(pages_est * 0.7)
        pages_est = max(self.adaptive_min_pages, pages_est)
        pages_est = min(self.adaptive_hard_cap, pages_est)
        return pages_est

    def update_account_stats(self, account: str, stage: BackfillStageInfo, used_pages: int,
                              effective_articles: int, last_page_effective: int, last_page_total: int,
                              est_pages: int):
        if not self.adaptive_enabled or not stage:
            return
        span_days = stage.upper_days - stage.lower_days
        recent_avg = effective_articles / span_days if span_days > 0 else effective_articles
        last_ratio = (last_page_effective / last_page_total) if last_page_total > 0 else 0.0
        self.stats[account] = {
            'recent_avg_daily': round(recent_avg, 3),
            'last_page_effective_ratio': round(last_ratio, 3),
            'last_used_pages': used_pages,
            'last_est_pages': est_pages,
            'ts': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        }
        self._save_stats()

    # --------------- time bounds ---------------
    def compute_bounds(self, stage: BackfillStageInfo) -> Tuple[datetime, datetime]:
        now_bj = datetime.now(BEIJING_TZ)
        today_start = now_bj.replace(hour=0, minute=0, second=0, microsecond=0)
        upper_cutoff = today_start - timedelta(days=stage.lower_days) if stage.lower_days > 0 else now_bj
        lower_cutoff = today_start - timedelta(days=stage.upper_days)
        return lower_cutoff, upper_cutoff

    @staticmethod
    def within_bounds(ts: int, lower: datetime, upper: datetime) -> bool:
        dt = datetime.fromtimestamp(ts, BEIJING_TZ)
        return (dt >= lower) and (dt < upper)
