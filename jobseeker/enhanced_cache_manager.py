#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版快取管理器
提供智能快取策略、預測性快取和性能優化

Author: jobseeker Team
Date: 2025-01-27
"""

import time
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading
from collections import defaultdict, deque

from .cache_system import (
    JobCache, CacheType, CacheStrategy, MemoryCache, FileCache, RedisCache,
    get_job_cache, JobResponse
)
from .model import Site, JobPost, ScraperInput
from .enhanced_logging import get_enhanced_logger, LogCategory


class CacheIntelligence(Enum):
    """快取智能等級"""
    BASIC = "basic"           # 基本快取
    SMART = "smart"           # 智能快取
    PREDICTIVE = "predictive" # 預測性快取
    ADAPTIVE = "adaptive"     # 自適應快取


@dataclass
class CacheMetrics:
    """快取指標"""
    hit_rate: float
    miss_rate: float
    avg_response_time: float
    cache_size: int
    memory_usage: float
    disk_usage: float
    last_cleanup: datetime
    total_requests: int
    successful_requests: int


@dataclass
class CachePattern:
    """快取模式"""
    pattern_id: str
    site: str
    search_terms: List[str]
    locations: List[str]
    frequency: int
    success_rate: float
    avg_jobs_found: int
    last_used: datetime
    confidence: float


class PredictiveCache:
    """預測性快取"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.search_history = deque(maxlen=history_size)
        self.patterns: Dict[str, CachePattern] = {}
        self.logger = get_enhanced_logger("predictive_cache")
        self._lock = threading.RLock()
    
    def record_search(self, site: str, search_term: str, location: str, 
                     success: bool, jobs_found: int):
        """記錄搜尋歷史"""
        with self._lock:
            search_record = {
                'timestamp': datetime.now(),
                'site': site,
                'search_term': search_term.lower(),
                'location': location.lower(),
                'success': success,
                'jobs_found': jobs_found
            }
            self.search_history.append(search_record)
            self._update_patterns(search_record)
    
    def _update_patterns(self, search_record: dict):
        """更新搜尋模式"""
        site = search_record['site']
        search_term = search_record['search_term']
        location = search_record['location']
        
        # 創建模式鍵
        pattern_key = f"{site}:{self._extract_keywords(search_term)}:{location}"
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = CachePattern(
                pattern_id=pattern_key,
                site=site,
                search_terms=[search_term],
                locations=[location],
                frequency=0,
                success_rate=0.0,
                avg_jobs_found=0,
                last_used=datetime.now(),
                confidence=0.0
            )
        
        pattern = self.patterns[pattern_key]
        pattern.frequency += 1
        pattern.last_used = datetime.now()
        
        # 更新成功率
        total_searches = sum(1 for record in self.search_history 
                           if self._matches_pattern(record, pattern))
        successful_searches = sum(1 for record in self.search_history 
                                if self._matches_pattern(record, pattern) and record['success'])
        pattern.success_rate = successful_searches / total_searches if total_searches > 0 else 0.0
        
        # 更新平均職位數
        jobs_found = [record['jobs_found'] for record in self.search_history 
                     if self._matches_pattern(record, pattern)]
        pattern.avg_jobs_found = sum(jobs_found) / len(jobs_found) if jobs_found else 0
        
        # 計算信心度
        pattern.confidence = min(pattern.frequency / 10.0, 1.0) * pattern.success_rate
    
    def _extract_keywords(self, search_term: str) -> str:
        """提取關鍵詞"""
        # 簡單的關鍵詞提取，可以根據需要改進
        keywords = search_term.split()
        # 過濾掉常見的停用詞
        stop_words = {'the', 'and', 'or', 'in', 'at', 'for', 'with', 'of', 'to', 'a', 'an'}
        keywords = [kw for kw in keywords if kw.lower() not in stop_words]
        return ' '.join(keywords[:3])  # 只取前3個關鍵詞
    
    def _matches_pattern(self, record: dict, pattern: CachePattern) -> bool:
        """檢查記錄是否匹配模式"""
        return (record['site'] == pattern.site and
                self._extract_keywords(record['search_term']) == 
                self._extract_keywords(pattern.search_terms[0]) and
                record['location'].lower() == pattern.locations[0].lower())
    
    def get_recommended_searches(self, site: str, limit: int = 5) -> List[CachePattern]:
        """獲取推薦的搜尋模式"""
        with self._lock:
            site_patterns = [p for p in self.patterns.values() 
                           if p.site == site and p.confidence > 0.5]
            site_patterns.sort(key=lambda p: p.confidence * p.frequency, reverse=True)
            return site_patterns[:limit]
    
    def should_prefetch(self, site: str, search_term: str, location: str) -> bool:
        """判斷是否應該預取"""
        pattern_key = f"{site}:{self._extract_keywords(search_term)}:{location.lower()}"
        pattern = self.patterns.get(pattern_key)
        
        if not pattern:
            return False
        
        # 基於信心度和頻率決定是否預取
        return pattern.confidence > 0.7 and pattern.frequency > 5


class AdaptiveCacheStrategy:
    """自適應快取策略"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("adaptive_cache")
        self.performance_history = deque(maxlen=100)
        self.current_strategy = CacheStrategy.LRU
        self.adaptation_threshold = 0.1  # 10% 的性能變化觸發適應
    
    def record_performance(self, strategy: CacheStrategy, hit_rate: float, 
                          response_time: float):
        """記錄性能指標"""
        self.performance_history.append({
            'strategy': strategy,
            'hit_rate': hit_rate,
            'response_time': response_time,
            'timestamp': datetime.now()
        })
        
        # 檢查是否需要適應
        if len(self.performance_history) >= 10:
            self._adapt_strategy()
    
    def _adapt_strategy(self):
        """適應快取策略"""
        recent_performance = list(self.performance_history)[-10:]
        
        # 計算每種策略的平均性能
        strategy_performance = defaultdict(list)
        for record in recent_performance:
            strategy_performance[record['strategy']].append(record['hit_rate'])
        
        # 找到最佳策略
        best_strategy = None
        best_score = 0
        
        for strategy, hit_rates in strategy_performance.items():
            avg_hit_rate = sum(hit_rates) / len(hit_rates)
            if avg_hit_rate > best_score:
                best_score = avg_hit_rate
                best_strategy = strategy
        
        # 如果性能提升超過閾值，切換策略
        if (best_strategy and best_strategy != self.current_strategy and 
            best_score - self._get_current_performance() > self.adaptation_threshold):
            
            self.logger.info(
                f"切換快取策略: {self.current_strategy.value} -> {best_strategy.value}",
                category=LogCategory.CACHE,
                metadata={
                    'old_strategy': self.current_strategy.value,
                    'new_strategy': best_strategy.value,
                    'performance_improvement': best_score - self._get_current_performance()
                }
            )
            self.current_strategy = best_strategy
    
    def _get_current_performance(self) -> float:
        """獲取當前策略的性能"""
        recent_records = [r for r in self.performance_history 
                         if r['strategy'] == self.current_strategy]
        if not recent_records:
            return 0.0
        return sum(r['hit_rate'] for r in recent_records) / len(recent_records)
    
    def get_optimal_strategy(self) -> CacheStrategy:
        """獲取最佳策略"""
        return self.current_strategy


class EnhancedCacheManager:
    """增強版快取管理器"""
    
    def __init__(self, 
                 cache_type: CacheType = CacheType.HYBRID,
                 intelligence_level: CacheIntelligence = CacheIntelligence.SMART,
                 enable_predictive: bool = True,
                 enable_adaptive: bool = True,
                 **kwargs):
        """
        初始化增強版快取管理器
        
        Args:
            cache_type: 快取類型
            intelligence_level: 智能等級
            enable_predictive: 是否啟用預測性快取
            enable_adaptive: 是否啟用自適應策略
        """
        self.cache_type = cache_type
        self.intelligence_level = intelligence_level
        self.enable_predictive = enable_predictive
        self.enable_adaptive = enable_adaptive
        
        self.logger = get_enhanced_logger("enhanced_cache_manager")
        
        # 初始化基礎快取
        self.job_cache = get_job_cache(cache_type, **kwargs)
        
        # 初始化智能組件
        if enable_predictive:
            self.predictive_cache = PredictiveCache()
        else:
            self.predictive_cache = None
        
        if enable_adaptive:
            self.adaptive_strategy = AdaptiveCacheStrategy()
        else:
            self.adaptive_strategy = None
        
        # 性能監控
        self.metrics = CacheMetrics(
            hit_rate=0.0,
            miss_rate=0.0,
            avg_response_time=0.0,
            cache_size=0,
            memory_usage=0.0,
            disk_usage=0.0,
            last_cleanup=datetime.now(),
            total_requests=0,
            successful_requests=0
        )
        
        # 快取預熱任務
        self._prefetch_tasks = set()
        
        self.logger.info(
            f"增強版快取管理器初始化完成",
            category=LogCategory.CACHE,
            metadata={
                'cache_type': cache_type.value,
                'intelligence_level': intelligence_level.value,
                'predictive_enabled': enable_predictive,
                'adaptive_enabled': enable_adaptive
            }
        )
    
    async def get_jobs(self, scraper_input: ScraperInput) -> Optional[JobResponse]:
        """獲取快取的職位搜尋結果"""
        start_time = time.time()
        
        try:
            # 生成快取鍵
            cache_key = self._generate_cache_key(scraper_input)
            
            # 嘗試從快取獲取
            cached_result = self.job_cache.get_jobs(
                scraper_input.site_name,
                scraper_input.search_term or '',
                scraper_input.location or '',
                results_wanted=scraper_input.results_wanted,
                hours_old=scraper_input.hours_old
            )
            
            response_time = time.time() - start_time
            
            if cached_result is not None:
                # 快取命中
                self._update_metrics(hit=True, response_time=response_time)
                
                # 記錄搜尋歷史（用於預測）
                if self.predictive_cache:
                    self.predictive_cache.record_search(
                        scraper_input.site_name.value,
                        scraper_input.search_term or '',
                        scraper_input.location or '',
                        True,
                        len(cached_result.jobs) if cached_result.jobs else 0
                    )
                
                self.logger.debug(
                    f"快取命中: {cache_key}",
                    category=LogCategory.CACHE,
                    metadata={
                        'site': scraper_input.site_name.value,
                        'search_term': scraper_input.search_term,
                        'response_time': response_time
                    }
                )
                
                return cached_result
            else:
                # 快取未命中
                self._update_metrics(hit=False, response_time=response_time)
                
                # 觸發預取（如果啟用）
                if self.enable_predictive and self.predictive_cache:
                    asyncio.create_task(self._trigger_prefetch(scraper_input))
                
                return None
                
        except Exception as e:
            self.logger.error(
                f"獲取快取失敗: {str(e)}",
                category=LogCategory.CACHE,
                metadata={'scraper_input': asdict(scraper_input)}
            )
            return None
    
    async def set_jobs(self, scraper_input: ScraperInput, job_response: JobResponse,
                      ttl: Optional[int] = None) -> bool:
        """快取職位搜尋結果"""
        try:
            success = self.job_cache.set_jobs(
                scraper_input.site_name,
                scraper_input.search_term or '',
                job_response,
                scraper_input.location or '',
                ttl,
                results_wanted=scraper_input.results_wanted,
                hours_old=scraper_input.hours_old
            )
            
            if success and self.predictive_cache:
                # 記錄搜尋結果
                self.predictive_cache.record_search(
                    scraper_input.site_name.value,
                    scraper_input.search_term or '',
                    scraper_input.location or '',
                    job_response.success,
                    len(job_response.jobs) if job_response.jobs else 0
                )
            
            return success
            
        except Exception as e:
            self.logger.error(
                f"設置快取失敗: {str(e)}",
                category=LogCategory.CACHE,
                metadata={'scraper_input': asdict(scraper_input)}
            )
            return False
    
    async def _trigger_prefetch(self, scraper_input: ScraperInput):
        """觸發預取"""
        if not self.predictive_cache:
            return
        
        try:
            # 獲取推薦的搜尋模式
            recommended_patterns = self.predictive_cache.get_recommended_searches(
                scraper_input.site_name.value, limit=3
            )
            
            for pattern in recommended_patterns:
                if pattern.confidence > 0.8:  # 高信心度的模式
                    # 創建預取任務
                    prefetch_input = ScraperInput(
                        site_name=scraper_input.site_name,
                        search_term=pattern.search_terms[0],
                        location=pattern.locations[0],
                        results_wanted=scraper_input.results_wanted
                    )
                    
                    # 檢查是否已經快取
                    if not await self.get_jobs(prefetch_input):
                        # 創建預取任務（這裡可以調用實際的爬蟲）
                        task = asyncio.create_task(self._prefetch_jobs(prefetch_input))
                        self._prefetch_tasks.add(task)
                        task.add_done_callback(self._prefetch_tasks.discard)
                        
                        self.logger.info(
                            f"觸發預取: {pattern.pattern_id}",
                            category=LogCategory.CACHE,
                            metadata={
                                'pattern_id': pattern.pattern_id,
                                'confidence': pattern.confidence,
                                'frequency': pattern.frequency
                            }
                        )
        
        except Exception as e:
            self.logger.error(f"預取觸發失敗: {str(e)}", category=LogCategory.CACHE)
    
    async def _prefetch_jobs(self, scraper_input: ScraperInput):
        """預取職位數據"""
        try:
            # 這裡可以調用實際的爬蟲來預取數據
            # 為了避免循環導入，我們使用一個簡單的模擬
            self.logger.debug(
                f"預取職位數據: {scraper_input.site_name.value}",
                category=LogCategory.CACHE,
                metadata={
                    'search_term': scraper_input.search_term,
                    'location': scraper_input.location
                }
            )
            
            # 實際實現中，這裡會調用爬蟲
            # from .scraper_adapter import create_scraper_adapter
            # adapter = create_scraper_adapter(scraper_input.site_name.value)
            # job_response = adapter.scrape(scraper_input)
            # await self.set_jobs(scraper_input, job_response)
            
        except Exception as e:
            self.logger.error(f"預取失敗: {str(e)}", category=LogCategory.CACHE)
    
    def _generate_cache_key(self, scraper_input: ScraperInput) -> str:
        """生成快取鍵"""
        return self.job_cache.generate_search_key(
            scraper_input.site_name,
            scraper_input.search_term or '',
            scraper_input.location or '',
            results_wanted=scraper_input.results_wanted,
            hours_old=scraper_input.hours_old
        )
    
    def _update_metrics(self, hit: bool, response_time: float):
        """更新性能指標"""
        self.metrics.total_requests += 1
        if hit:
            self.metrics.successful_requests += 1
        
        # 更新命中率
        self.metrics.hit_rate = self.metrics.successful_requests / self.metrics.total_requests
        self.metrics.miss_rate = 1.0 - self.metrics.hit_rate
        
        # 更新平均響應時間
        if self.metrics.avg_response_time == 0:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (
                self.metrics.avg_response_time * 0.9 + response_time * 0.1
            )
        
        # 更新快取大小
        self.metrics.cache_size = self.job_cache.get_cache_stats()
        
        # 記錄性能（用於自適應策略）
        if self.adaptive_strategy:
            self.adaptive_strategy.record_performance(
                CacheStrategy.LRU,  # 這裡應該從實際快取獲取策略
                self.metrics.hit_rate,
                self.metrics.avg_response_time
            )
    
    def get_cache_metrics(self) -> CacheMetrics:
        """獲取快取指標"""
        return self.metrics
    
    def get_cache_patterns(self) -> List[CachePattern]:
        """獲取快取模式"""
        if not self.predictive_cache:
            return []
        
        return list(self.predictive_cache.patterns.values())
    
    def get_recommendations(self, site: str, limit: int = 5) -> List[CachePattern]:
        """獲取搜尋推薦"""
        if not self.predictive_cache:
            return []
        
        return self.predictive_cache.get_recommended_searches(site, limit)
    
    async def cleanup_expired(self):
        """清理過期快取"""
        try:
            self.job_cache.cleanup_expired()
            self.metrics.last_cleanup = datetime.now()
            
            self.logger.info("過期快取清理完成", category=LogCategory.CACHE)
            
        except Exception as e:
            self.logger.error(f"快取清理失敗: {str(e)}", category=LogCategory.CACHE)
    
    async def warmup_cache(self, common_searches: List[Dict[str, Any]]):
        """快取預熱"""
        self.logger.info(f"開始快取預熱，共 {len(common_searches)} 個搜尋", 
                        category=LogCategory.CACHE)
        
        tasks = []
        for search_config in common_searches:
            scraper_input = ScraperInput(
                site_name=Site(search_config['site']),
                search_term=search_config.get('search_term'),
                location=search_config.get('location'),
                results_wanted=search_config.get('results_wanted', 20)
            )
            
            task = asyncio.create_task(self._prefetch_jobs(scraper_input))
            tasks.append(task)
        
        # 等待所有預熱任務完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("快取預熱完成", category=LogCategory.CACHE)
    
    def get_optimization_suggestions(self) -> List[str]:
        """獲取優化建議"""
        suggestions = []
        
        # 基於命中率的建議
        if self.metrics.hit_rate < 0.5:
            suggestions.append("快取命中率較低，建議增加快取大小或調整TTL")
        
        # 基於響應時間的建議
        if self.metrics.avg_response_time > 1.0:
            suggestions.append("平均響應時間較長，建議啟用預測性快取")
        
        # 基於模式的建議
        if self.predictive_cache:
            high_confidence_patterns = [
                p for p in self.predictive_cache.patterns.values() 
                if p.confidence > 0.8
            ]
            if len(high_confidence_patterns) > 10:
                suggestions.append("發現多個高信心度搜尋模式，建議啟用預取")
        
        return suggestions


# 全域增強快取管理器實例
_global_enhanced_cache: Optional[EnhancedCacheManager] = None


def get_enhanced_cache_manager(**kwargs) -> EnhancedCacheManager:
    """獲取全域增強快取管理器實例"""
    global _global_enhanced_cache
    
    if _global_enhanced_cache is None:
        _global_enhanced_cache = EnhancedCacheManager(**kwargs)
    
    return _global_enhanced_cache


def with_enhanced_caching(
    cache_type: CacheType = CacheType.HYBRID,
    ttl: int = 3600,
    enable_predictive: bool = True
):
    """增強版快取裝飾器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # 提取搜尋參數
            scraper_input = None
            for arg in args:
                if isinstance(arg, ScraperInput):
                    scraper_input = arg
                    break
            
            if not scraper_input:
                return await func(*args, **kwargs)
            
            # 獲取增強快取管理器
            cache_manager = get_enhanced_cache_manager(
                cache_type=cache_type,
                enable_predictive=enable_predictive
            )
            
            # 嘗試從快取獲取
            cached_result = await cache_manager.get_jobs(scraper_input)
            if cached_result is not None:
                return cached_result
            
            # 執行函數並快取結果
            result = await func(*args, **kwargs)
            if isinstance(result, JobResponse) and result.success:
                await cache_manager.set_jobs(scraper_input, result, ttl)
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # 同步版本的處理
            scraper_input = None
            for arg in args:
                if isinstance(arg, ScraperInput):
                    scraper_input = arg
                    break
            
            if not scraper_input:
                return func(*args, **kwargs)
            
            # 獲取增強快取管理器
            cache_manager = get_enhanced_cache_manager(
                cache_type=cache_type,
                enable_predictive=enable_predictive
            )
            
            # 嘗試從快取獲取
            cached_result = asyncio.run(cache_manager.get_jobs(scraper_input))
            if cached_result is not None:
                return cached_result
            
            # 執行函數並快取結果
            result = func(*args, **kwargs)
            if isinstance(result, JobResponse) and result.success:
                asyncio.run(cache_manager.set_jobs(scraper_input, result, ttl))
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
