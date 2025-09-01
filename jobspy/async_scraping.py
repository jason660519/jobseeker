"""全面非同步化爬蟲架構

提供統一的非同步爬蟲基礎類和適配器，將現有的同步爬蟲轉換為非同步模式。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Callable, Union, Coroutine
from dataclasses import dataclass, field
from enum import Enum
import threading
from functools import wraps

from jobseeker.model import JobResponse, ScraperInput, Site, Scraper
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory, async_performance_logger
from jobseeker.error_handling import ScrapingError, retry_with_backoff, async_retry_with_backoff
from jobseeker.performance_monitoring import ScrapingMetrics, async_performance_monitor
from jobseeker.cache_system import JobCache, CacheStrategy
from jobseeker.data_quality import DataQualityProcessor, improve_job_data_quality


class AsyncMode(Enum):
    """非同步模式枚舉"""
    NATIVE = "native"  # 原生非同步
    THREADED = "threaded"  # 線程池非同步
    PROCESS = "process"  # 進程池非同步
    HYBRID = "hybrid"  # 混合模式


class ConcurrencyLevel(Enum):
    """並發級別枚舉"""
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    VERY_HIGH = 10


@dataclass
class AsyncConfig:
    """非同步配置"""
    mode: AsyncMode = AsyncMode.NATIVE
    max_concurrent_requests: int = 5
    request_delay: float = 1.0
    timeout: float = 30.0
    enable_caching: bool = True
    enable_quality_check: bool = True
    enable_monitoring: bool = True
    retry_attempts: int = 3
    backoff_factor: float = 2.0
    thread_pool_size: Optional[int] = None
    semaphore_limit: Optional[int] = None


@dataclass
class AsyncScrapingResult:
    """非同步爬取結果"""
    success: bool
    job_response: Optional[JobResponse] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cache_hit: bool = False
    quality_score: float = 0.0
    retry_count: int = 0
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AsyncScraper(ABC):
    """非同步爬蟲基礎類"""
    
    def __init__(self, site: Site, config: Optional[AsyncConfig] = None,
                 proxies: Optional[List[str]] = None, ca_cert: Optional[str] = None,
                 user_agent: Optional[str] = None):
        self.site = site
        self.config = config or AsyncConfig()
        self.proxies = proxies
        self.ca_cert = ca_cert
        self.user_agent = user_agent
        
        # 初始化組件
        self.logger = get_enhanced_logger(f"async_{site.value}")
        self.metrics = ScrapingMetrics() if self.config.enable_monitoring else None
        self.cache = JobCache(strategy=CacheStrategy.MEMORY) if self.config.enable_caching else None
        self.quality_processor = DataQualityProcessor() if self.config.enable_quality_check else None
        
        # 並發控制
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.rate_limiter = AsyncRateLimiter(self.config.request_delay)
        
        # 線程池（用於混合模式）
        if self.config.mode in [AsyncMode.THREADED, AsyncMode.HYBRID]:
            pool_size = self.config.thread_pool_size or self.config.max_concurrent_requests
            self.thread_pool = ThreadPoolExecutor(max_workers=pool_size)
        else:
            self.thread_pool = None
    
    @abstractmethod
    async def scrape_async(self, scraper_input: ScraperInput) -> AsyncScrapingResult:
        """非同步爬取方法 - 抽象方法"""
        pass
    
    async def scrape_multiple(self, scraper_inputs: List[ScraperInput]) -> List[AsyncScrapingResult]:
        """批量非同步爬取"""
        tasks = []
        for scraper_input in scraper_inputs:
            task = self.scrape_async(scraper_input)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = AsyncScrapingResult(
                    success=False,
                    error=str(result),
                    source=self.site.value
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def __aenter__(self):
        """非同步上下文管理器入口"""
        await self._setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步上下文管理器出口"""
        await self._cleanup()
    
    async def _setup(self):
        """設置資源"""
        self.logger.info(
            f"設置非同步爬蟲: {self.site.value}",
            category=LogCategory.GENERAL,
            metadata={'config': self.config.__dict__}
        )
    
    async def _cleanup(self):
        """清理資源"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        self.logger.info(
            f"清理非同步爬蟲: {self.site.value}",
            category=LogCategory.GENERAL
        )


class AsyncRateLimiter:
    """非同步速率限制器"""
    
    def __init__(self, delay: float):
        self.delay = delay
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """獲取速率限制許可"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()


class SyncToAsyncAdapter(AsyncScraper):
    """同步爬蟲到非同步爬蟲的適配器"""
    
    def __init__(self, sync_scraper_class: type, site: Site, 
                 config: Optional[AsyncConfig] = None, **kwargs):
        super().__init__(site, config, **kwargs)
        self.sync_scraper_class = sync_scraper_class
        self.sync_scraper_kwargs = kwargs
    
    @async_performance_monitor("adapter")
    @async_retry_with_backoff(max_retries=3)
    async def scrape_async(self, scraper_input: ScraperInput) -> AsyncScrapingResult:
        """將同步爬蟲適配為非同步"""
        start_time = time.time()
        
        # 檢查快取
        if self.cache:
            cached_result = await self._get_cached_result(scraper_input)
            if cached_result:
                return cached_result
        
        # 應用速率限制
        await self.rate_limiter.acquire()
        
        # 並發控制
        async with self.semaphore:
            try:
                # 在線程池中執行同步爬蟲
                loop = asyncio.get_event_loop()
                job_response = await loop.run_in_executor(
                    self.thread_pool,
                    self._run_sync_scraper,
                    scraper_input
                )
                
                execution_time = time.time() - start_time
                
                # 資料品質檢查
                quality_score = 0.0
                if self.quality_processor and job_response.jobs:
                    quality_report = self.quality_processor.process_jobs(job_response.jobs)
                    quality_score = quality_report.overall_score
                
                result = AsyncScrapingResult(
                    success=True,
                    job_response=job_response,
                    execution_time=execution_time,
                    quality_score=quality_score,
                    source=self.site.value
                )
                
                # 快取結果
                if self.cache:
                    await self._cache_result(scraper_input, result)
                
                # 記錄指標
                if self.metrics:
                    self.metrics.record_success(self.site.value, execution_time)
                    self.metrics.record_data_quality(self.site.value, quality_score)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # 記錄錯誤
                if self.metrics:
                    self.metrics.record_error(self.site.value, type(e).__name__)
                
                self.logger.error(
                    f"同步爬蟲適配失敗: {str(e)}",
                    category=LogCategory.ERROR,
                    metadata={'scraper_input': scraper_input.__dict__}
                )
                
                return AsyncScrapingResult(
                    success=False,
                    error=str(e),
                    execution_time=execution_time,
                    source=self.site.value
                )
    
    def _run_sync_scraper(self, scraper_input: ScraperInput) -> JobResponse:
        """在線程中運行同步爬蟲"""
        scraper = self.sync_scraper_class(**self.sync_scraper_kwargs)
        return scraper.scrape(scraper_input)
    
    async def _get_cached_result(self, scraper_input: ScraperInput) -> Optional[AsyncScrapingResult]:
        """獲取快取結果"""
        if not self.cache:
            return None
        
        cache_key = self.cache._generate_cache_key(scraper_input)
        cached_jobs = await asyncio.to_thread(self.cache.get, cache_key)
        
        if cached_jobs:
            job_response = JobResponse(jobs=cached_jobs)
            return AsyncScrapingResult(
                success=True,
                job_response=job_response,
                cache_hit=True,
                source=self.site.value
            )
        
        return None
    
    async def _cache_result(self, scraper_input: ScraperInput, result: AsyncScrapingResult):
        """快取結果"""
        if not self.cache or not result.success or not result.job_response:
            return
        
        cache_key = self.cache._generate_cache_key(scraper_input)
        await asyncio.to_thread(
            self.cache.set,
            cache_key,
            result.job_response.jobs,
            ttl=3600  # 1小時
        )


class AsyncScrapingManager:
    """非同步爬蟲管理器"""
    
    def __init__(self, config: Optional[AsyncConfig] = None):
        self.config = config or AsyncConfig()
        self.scrapers: Dict[Site, AsyncScraper] = {}
        self.logger = get_enhanced_logger("async_manager")
        self.metrics = ScrapingMetrics()
    
    def register_scraper(self, site: Site, scraper: AsyncScraper):
        """註冊非同步爬蟲"""
        self.scrapers[site] = scraper
        self.logger.info(
            f"註冊非同步爬蟲: {site.value}",
            category=LogCategory.GENERAL
        )
    
    def register_sync_scraper(self, site: Site, sync_scraper_class: type, **kwargs):
        """註冊同步爬蟲（自動適配為非同步）"""
        adapter = SyncToAsyncAdapter(
            sync_scraper_class=sync_scraper_class,
            site=site,
            config=self.config,
            **kwargs
        )
        self.register_scraper(site, adapter)
    
    async def scrape_site(self, site: Site, scraper_input: ScraperInput) -> AsyncScrapingResult:
        """爬取單個網站"""
        if site not in self.scrapers:
            return AsyncScrapingResult(
                success=False,
                error=f"未找到 {site.value} 的爬蟲",
                source=site.value
            )
        
        scraper = self.scrapers[site]
        return await scraper.scrape_async(scraper_input)
    
    async def scrape_multiple_sites(self, 
                                   sites: List[Site], 
                                   scraper_input: ScraperInput) -> Dict[Site, AsyncScrapingResult]:
        """爬取多個網站"""
        tasks = {}
        for site in sites:
            if site in self.scrapers:
                task = self.scrape_site(site, scraper_input)
                tasks[site] = task
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 組織結果
        site_results = {}
        for site, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                site_results[site] = AsyncScrapingResult(
                    success=False,
                    error=str(result),
                    source=site.value
                )
            else:
                site_results[site] = result
        
        return site_results
    
    async def scrape_all_available(self, scraper_input: ScraperInput) -> Dict[Site, AsyncScrapingResult]:
        """爬取所有可用網站"""
        available_sites = list(self.scrapers.keys())
        return await self.scrape_multiple_sites(available_sites, scraper_input)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取效能摘要"""
        stats = self.metrics.get_stats()
        return {
            "total_requests": stats.total_requests,
            "success_rate": stats.success_rate,
            "avg_response_time": stats.avg_response_time,
            "cache_hit_rate": stats.cache_hit_rate,
            "avg_quality_score": stats.avg_data_quality_score
        }


# 便利函數
def create_async_scraping_manager(config: Optional[AsyncConfig] = None) -> AsyncScrapingManager:
    """創建非同步爬蟲管理器"""
    return AsyncScrapingManager(config)


def async_scrape_decorator(site: Site, config: Optional[AsyncConfig] = None):
    """非同步爬取裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = create_async_scraping_manager(config)
            
            # 如果函數返回 ScraperInput，則執行爬取
            result = await func(*args, **kwargs)
            if isinstance(result, ScraperInput):
                return await manager.scrape_site(site, result)
            return result
        
        return wrapper
    return decorator


# 全域非同步爬蟲管理器實例
_global_manager = None
_manager_lock = threading.Lock()


def get_global_async_manager() -> AsyncScrapingManager:
    """獲取全域非同步爬蟲管理器"""
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = create_async_scraping_manager()
    return _global_manager


# 高級非同步爬取函數
async def async_scrape_jobs(
    sites: Union[Site, List[Site]],
    search_term: str,
    location: Optional[str] = None,
    results_wanted: int = 15,
    job_type: Optional[str] = None,
    is_remote: bool = False,
    config: Optional[AsyncConfig] = None,
    **kwargs
) -> Dict[Site, AsyncScrapingResult]:
    """高級非同步職位爬取函數"""
    
    # 準備輸入
    scraper_input = ScraperInput(
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        job_type=job_type,
        is_remote=is_remote,
        **kwargs
    )
    
    # 準備網站列表
    if isinstance(sites, Site):
        sites = [sites]
    
    # 獲取管理器
    manager = get_global_async_manager()
    if config:
        manager.config = config
    
    # 執行爬取
    return await manager.scrape_multiple_sites(sites, scraper_input)


# 批量非同步爬取
async def batch_async_scrape(
    scrape_configs: List[Dict[str, Any]],
    global_config: Optional[AsyncConfig] = None
) -> List[Dict[Site, AsyncScrapingResult]]:
    """批量非同步爬取"""
    
    tasks = []
    for config in scrape_configs:
        sites = config.pop('sites', [])
        task = async_scrape_jobs(sites=sites, config=global_config, **config)
        tasks.append(task)
    
    return await asyncio.gather(*tasks, return_exceptions=True)
