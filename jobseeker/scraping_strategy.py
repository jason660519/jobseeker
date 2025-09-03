"""統一爬蟲策略介面

此模組提供統一的爬蟲策略介面，允許不同的爬蟲實現使用一致的策略模式。
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable, Type
from urllib.parse import urljoin, urlparse

from jobseeker.model import JobPost, JobResponse, ScraperInput, Site
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory, performance_logger
from jobseeker.error_handling import ScrapingError, NetworkError, RateLimitError, retry_with_backoff
from jobseeker.cache_system import JobCache, CacheStrategy


class ScrapingMethod(Enum):
    """爬蟲方法類型"""
    REQUESTS = "requests"  # 使用 requests 庫
    SELENIUM = "selenium"  # 使用 Selenium
    PLAYWRIGHT = "playwright"  # 使用 Playwright
    API = "api"  # 直接 API 呼叫
    TLS_CLIENT = "tls_client"  # 使用 TLS 客戶端


class ScrapingMode(Enum):
    """爬蟲模式"""
    SYNC = "sync"  # 同步模式
    ASYNC = "async"  # 非同步模式
    BATCH = "batch"  # 批次模式
    STREAMING = "streaming"  # 串流模式


@dataclass
class ScrapingConfig:
    """爬蟲配置"""
    method: ScrapingMethod
    mode: ScrapingMode = ScrapingMode.SYNC
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    rate_limit: float = 1.0  # 每秒請求數
    concurrent_limit: int = 5
    use_cache: bool = True
    cache_ttl: int = 3600  # 快取存活時間（秒）
    user_agent: Optional[str] = None
    proxy_config: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapingResult:
    """爬蟲結果"""
    success: bool
    jobs: List[JobPost]
    total_found: int = 0
    pages_scraped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    cache_hit: bool = False
    
    def to_job_response(self) -> JobResponse:
        """轉換為 JobResponse"""
        return JobResponse(
            success=self.success,
            error=self.errors[0] if self.errors else None,
            jobs=self.jobs
        )


class BaseScrapingStrategy(ABC):
    """爬蟲策略基類"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.logger = get_enhanced_logger(f"strategy_{self.__class__.__name__.lower()}")
        self.cache = JobCache() if config.use_cache else None
        self._rate_limiter = RateLimiter(config.rate_limit)
        self._session = None
        self._last_request_time = 0.0
    
    @abstractmethod
    async def scrape_jobs(self, scraper_input: ScraperInput) -> ScrapingResult:
        """爬取職位 - 抽象方法"""
        pass
    
    @abstractmethod
    def get_supported_sites(self) -> List[Site]:
        """獲取支援的網站列表"""
        pass
    
    @abstractmethod
    def validate_input(self, scraper_input: ScraperInput) -> bool:
        """驗證輸入參數"""
        pass
    
    async def setup(self) -> None:
        """設置策略（在爬取前呼叫）"""
        self.logger.info(
            f"設置爬蟲策略: {self.__class__.__name__}",
            category=LogCategory.GENERAL,
            metadata={'config': self.config.__dict__}
        )
    
    async def cleanup(self) -> None:
        """清理資源（在爬取後呼叫）"""
        if self._session:
            try:
                if hasattr(self._session, 'close'):
                    await self._session.close()
                elif hasattr(self._session, 'quit'):
                    self._session.quit()
            except Exception as e:
                self.logger.warning(
                    f"清理會話時發生錯誤: {str(e)}",
                    category=LogCategory.ERROR
                )
    
    async def _apply_rate_limit(self) -> None:
        """應用速率限制"""
        await self._rate_limiter.acquire()
    
    def _generate_cache_key(self, scraper_input: ScraperInput) -> str:
        """生成快取鍵"""
        key_parts = [
            str(scraper_input.site_name),
            scraper_input.search_term or '',
            scraper_input.location or '',
            str(scraper_input.results_wanted or 0),
            str(scraper_input.job_type or ''),
            str(scraper_input.is_remote or False)
        ]
        return '|'.join(key_parts)
    
    async def _get_cached_result(self, scraper_input: ScraperInput) -> Optional[ScrapingResult]:
        """獲取快取結果"""
        if not self.cache:
            return None
        
        cache_key = self._generate_cache_key(scraper_input)
        cached_jobs = await self.cache.get_jobs(cache_key)
        
        if cached_jobs:
            self.logger.info(
                f"快取命中: {len(cached_jobs)} 個職位",
                category=LogCategory.GENERAL,
                metadata={'cache_key': cache_key}
            )
            
            return ScrapingResult(
                success=True,
                jobs=cached_jobs,
                total_found=len(cached_jobs),
                cache_hit=True
            )
        
        return None
    
    async def _cache_result(self, scraper_input: ScraperInput, result: ScrapingResult) -> None:
        """快取結果"""
        if not self.cache or not result.success or not result.jobs:
            return
        
        cache_key = self._generate_cache_key(scraper_input)
        await self.cache.cache_jobs(
            cache_key,
            result.jobs,
            ttl=self.config.cache_ttl
        )
        
        self.logger.info(
            f"結果已快取: {len(result.jobs)} 個職位",
            category=LogCategory.GENERAL,
            metadata={'cache_key': cache_key}
        )


class RequestsStrategy(BaseScrapingStrategy):
    """基於 Requests 的爬蟲策略"""
    
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self._requests_session = None
    
    async def setup(self) -> None:
        """設置 Requests 會話"""
        await super().setup()
        
        import requests
        self._requests_session = requests.Session()
        
        # 設置標頭
        if self.config.user_agent:
            self._requests_session.headers['User-Agent'] = self.config.user_agent
        
        self._requests_session.headers.update(self.config.headers)
        
        # 設置代理
        if self.config.proxy_config:
            self._requests_session.proxies.update(self.config.proxy_config)
        
        # 設置 cookies
        self._requests_session.cookies.update(self.config.cookies)
        
        self._session = self._requests_session
    
    @retry_with_backoff(max_retries=3)
    async def scrape_jobs(self, scraper_input: ScraperInput) -> ScrapingResult:
        """使用 Requests 爬取職位"""
        # 檢查快取
        cached_result = await self._get_cached_result(scraper_input)
        if cached_result:
            return cached_result
        
        start_time = time.time()
        result = ScrapingResult(success=False, jobs=[])
        
        try:
            await self._apply_rate_limit()
            
            # 這裡應該實現具體的爬取邏輯
            # 由於每個網站的實現不同，這裡提供一個框架
            jobs = await self._scrape_with_requests(scraper_input)
            
            result = ScrapingResult(
                success=True,
                jobs=jobs,
                total_found=len(jobs),
                pages_scraped=1,
                execution_time=time.time() - start_time
            )
            
            # 快取結果
            await self._cache_result(scraper_input, result)
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.execution_time = time.time() - start_time
            
            self.logger.error(
                f"Requests 爬取失敗: {str(e)}",
                category=LogCategory.ERROR,
                metadata={'scraper_input': scraper_input.__dict__}
            )
        
        return result
    
    async def _scrape_with_requests(self, scraper_input: ScraperInput) -> List[JobPost]:
        """使用 Requests 執行具體爬取邏輯"""
        try:
            # 根據網站類型選擇對應的爬蟲
            from .scraper_adapter import create_scraper_adapter
            
            # 將 ScraperInput 轉換為適合現有爬蟲的格式
            site_name = scraper_input.site_name.value if hasattr(scraper_input.site_name, 'value') else str(scraper_input.site_name)
            
            # 創建適配器
            adapter = create_scraper_adapter(site_name)
            
            # 執行爬取
            job_response = adapter.scrape(scraper_input)
            
            if job_response and job_response.jobs:
                self.logger.info(f"成功爬取 {len(job_response.jobs)} 個職位")
                return job_response.jobs
            else:
                self.logger.warning(f"未找到職位")
                return []
                
        except Exception as e:
            self.logger.error(f"爬取過程中發生錯誤: {str(e)}")
            return []
    
    def get_supported_sites(self) -> List[Site]:
        """獲取支援的網站"""
        return [
            Site.INDEED, Site.GLASSDOOR, Site.LINKEDIN, Site.SEEK,
            Site.ZIP_RECRUITER, Site.BAYT, Site.NAUKRI, Site.BDJOBS,
            Site.GOOGLE, Site.T104, Site.JOB_1111
        ]
    
    def validate_input(self, scraper_input: ScraperInput) -> bool:
        """驗證輸入"""
        return bool(scraper_input.search_term and scraper_input.site_name)


class PlaywrightStrategy(BaseScrapingStrategy):
    """基於 Playwright 的爬蟲策略"""
    
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self._playwright = None
        self._browser = None
        self._context = None
    
    async def setup(self) -> None:
        """設置 Playwright"""
        await super().setup()
        
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            # 啟動瀏覽器
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # 創建上下文
            context_options = {
                'user_agent': self.config.user_agent,
                'viewport': {'width': 1920, 'height': 1080}
            }
            
            if self.config.proxy_config:
                context_options['proxy'] = self.config.proxy_config
            
            self._context = await self._browser.new_context(**context_options)
            
            # 設置額外標頭
            if self.config.headers:
                await self._context.set_extra_http_headers(self.config.headers)
            
            self._session = self._context
            
        except ImportError:
            raise ScrapingError("Playwright 未安裝，請執行: pip install playwright")
    
    async def cleanup(self) -> None:
        """清理 Playwright 資源"""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            self.logger.warning(
                f"清理 Playwright 資源時發生錯誤: {str(e)}",
                category=LogCategory.ERROR
            )
        
        await super().cleanup()
    
    @retry_with_backoff(max_retries=3)
    async def scrape_jobs(self, scraper_input: ScraperInput) -> ScrapingResult:
        """使用 Playwright 爬取職位"""
        # 檢查快取
        cached_result = await self._get_cached_result(scraper_input)
        if cached_result:
            return cached_result
        
        start_time = time.time()
        result = ScrapingResult(success=False, jobs=[])
        
        try:
            await self._apply_rate_limit()
            
            # 創建新頁面
            page = await self._context.new_page()
            
            try:
                # 這裡應該實現具體的爬取邏輯
                jobs = await self._scrape_with_playwright(page, scraper_input)
                
                result = ScrapingResult(
                    success=True,
                    jobs=jobs,
                    total_found=len(jobs),
                    pages_scraped=1,
                    execution_time=time.time() - start_time
                )
                
                # 快取結果
                await self._cache_result(scraper_input, result)
                
            finally:
                await page.close()
        
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.execution_time = time.time() - start_time
            
            self.logger.error(
                f"Playwright 爬取失敗: {str(e)}",
                category=LogCategory.ERROR,
                metadata={'scraper_input': scraper_input.__dict__}
            )
        
        return result
    
    async def _scrape_with_playwright(self, page, scraper_input: ScraperInput) -> List[JobPost]:
        """使用 Playwright 執行具體爬取邏輯"""
        try:
            # 對於需要 JavaScript 的網站，使用 Playwright
            from .scraper_adapter import create_scraper_adapter
            
            site_name = scraper_input.site_name.value if hasattr(scraper_input.site_name, 'value') else str(scraper_input.site_name)
            
            # 創建適配器
            adapter = create_scraper_adapter(site_name)
            
            # 執行爬取
            job_response = adapter.scrape(scraper_input)
            
            if job_response and job_response.jobs:
                self.logger.info(f"成功爬取 {len(job_response.jobs)} 個職位")
                return job_response.jobs
            else:
                self.logger.warning(f"未找到職位")
                return []
                
        except Exception as e:
            self.logger.error(f"Playwright 爬取過程中發生錯誤: {str(e)}")
            return []
    
    def get_supported_sites(self) -> List[Site]:
        """獲取支援的網站"""
        return [
            Site.INDEED, Site.GLASSDOOR, Site.LINKEDIN, Site.SEEK,
            Site.ZIP_RECRUITER, Site.BAYT, Site.NAUKRI, Site.BDJOBS,
            Site.GOOGLE, Site.T104, Site.JOB_1111
        ]
    
    def validate_input(self, scraper_input: ScraperInput) -> bool:
        """驗證輸入"""
        return bool(scraper_input.search_term and scraper_input.site_name)


class APIStrategy(BaseScrapingStrategy):
    """基於 API 的爬蟲策略"""
    
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self._api_client = None
    
    async def setup(self) -> None:
        """設置 API 客戶端"""
        await super().setup()
        
        import aiohttp
        
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_limit,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        headers = {
            'User-Agent': self.config.user_agent or 'jobseeker/1.0',
            **self.config.headers
        }
        
        self._api_client = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            cookies=self.config.cookies
        )
        
        self._session = self._api_client
    
    @retry_with_backoff(max_retries=3)
    async def scrape_jobs(self, scraper_input: ScraperInput) -> ScrapingResult:
        """使用 API 爬取職位"""
        # 檢查快取
        cached_result = await self._get_cached_result(scraper_input)
        if cached_result:
            return cached_result
        
        start_time = time.time()
        result = ScrapingResult(success=False, jobs=[])
        
        try:
            await self._apply_rate_limit()
            
            # 這裡應該實現具體的 API 呼叫邏輯
            jobs = await self._scrape_with_api(scraper_input)
            
            result = ScrapingResult(
                success=True,
                jobs=jobs,
                total_found=len(jobs),
                pages_scraped=1,
                execution_time=time.time() - start_time
            )
            
            # 快取結果
            await self._cache_result(scraper_input, result)
        
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.execution_time = time.time() - start_time
            
            self.logger.error(
                f"API 爬取失敗: {str(e)}",
                category=LogCategory.ERROR,
                metadata={'scraper_input': scraper_input.__dict__}
            )
        
        return result
    
    async def _scrape_with_api(self, scraper_input: ScraperInput) -> List[JobPost]:
        """使用 API 執行具體爬取邏輯"""
        try:
            # 對於有 API 的網站，使用 API 策略
            from .scraper_adapter import create_scraper_adapter
            
            site_name = scraper_input.site_name.value if hasattr(scraper_input.site_name, 'value') else str(scraper_input.site_name)
            
            # 創建適配器
            adapter = create_scraper_adapter(site_name)
            
            # 執行爬取
            job_response = adapter.scrape(scraper_input)
            
            if job_response and job_response.jobs:
                self.logger.info(f"成功爬取 {len(job_response.jobs)} 個職位")
                return job_response.jobs
            else:
                self.logger.warning(f"未找到職位")
                return []
                
        except Exception as e:
            self.logger.error(f"API 爬取過程中發生錯誤: {str(e)}")
            return []
    
    def get_supported_sites(self) -> List[Site]:
        """獲取支援的網站"""
        return [
            Site.INDEED, Site.GLASSDOOR, Site.LINKEDIN, Site.SEEK,
            Site.ZIP_RECRUITER, Site.BAYT, Site.NAUKRI, Site.BDJOBS,
            Site.GOOGLE, Site.T104, Site.JOB_1111
        ]
    
    def validate_input(self, scraper_input: ScraperInput) -> bool:
        """驗證輸入"""
        return bool(scraper_input.search_term and scraper_input.site_name)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, rate: float):
        self.rate = rate  # 每秒請求數
        self.interval = 1.0 / rate if rate > 0 else 0
        self.last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """獲取請求許可"""
        if self.rate <= 0:
            return
        
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_request
            
            if time_since_last < self.interval:
                sleep_time = self.interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request = time.time()


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[ScrapingMethod, Type[BaseScrapingStrategy]] = {
            ScrapingMethod.REQUESTS: RequestsStrategy,
            ScrapingMethod.PLAYWRIGHT: PlaywrightStrategy,
            ScrapingMethod.API: APIStrategy
        }
        self.logger = get_enhanced_logger("strategy_manager")
    
    def register_strategy(self, method: ScrapingMethod, 
                         strategy_class: Type[BaseScrapingStrategy]) -> None:
        """註冊新策略"""
        self.strategies[method] = strategy_class
        self.logger.info(
            f"註冊策略: {method.value} -> {strategy_class.__name__}",
            category=LogCategory.GENERAL
        )
    
    def get_strategy(self, config: ScrapingConfig) -> BaseScrapingStrategy:
        """獲取策略實例"""
        strategy_class = self.strategies.get(config.method)
        if not strategy_class:
            raise ValueError(f"不支援的爬蟲方法: {config.method}")
        
        return strategy_class(config)
    
    def get_available_methods(self) -> List[ScrapingMethod]:
        """獲取可用的爬蟲方法"""
        return list(self.strategies.keys())
    
    def get_strategy_for_site(self, site: Site) -> Optional[ScrapingMethod]:
        """為特定網站推薦策略"""
        # 根據網站特性推薦最適合的策略
        site_recommendations = {
            Site.LINKEDIN: ScrapingMethod.REQUESTS,    # 使用現有爬蟲
            Site.INDEED: ScrapingMethod.REQUESTS,      # 使用現有爬蟲
            Site.GLASSDOOR: ScrapingMethod.REQUESTS,   # 使用現有爬蟲
            Site.SEEK: ScrapingMethod.REQUESTS,        # 使用現有爬蟲
            Site.ZIP_RECRUITER: ScrapingMethod.REQUESTS,  # 使用現有爬蟲
            Site.BAYT: ScrapingMethod.REQUESTS,        # 使用現有爬蟲
            Site.NAUKRI: ScrapingMethod.REQUESTS,      # 使用現有爬蟲
            Site.BDJOBS: ScrapingMethod.REQUESTS,      # 使用現有爬蟲
            Site.GOOGLE: ScrapingMethod.REQUESTS,      # 使用現有爬蟲
            Site.T104: ScrapingMethod.REQUESTS,        # 使用現有爬蟲
            Site.JOB_1111: ScrapingMethod.REQUESTS     # 使用現有爬蟲
        }
        
        return site_recommendations.get(site)


class UnifiedScraper:
    """統一爬蟲介面"""
    
    def __init__(self, strategy_manager: Optional[StrategyManager] = None):
        self.strategy_manager = strategy_manager or StrategyManager()
        self.logger = get_enhanced_logger("unified_scraper")
    
    @performance_logger
    async def scrape_jobs(self, scraper_input: ScraperInput, 
                         config: Optional[ScrapingConfig] = None) -> ScrapingResult:
        """統一的職位爬取介面"""
        # 如果沒有提供配置，使用預設配置
        if not config:
            # 根據網站推薦策略
            recommended_method = self.strategy_manager.get_strategy_for_site(scraper_input.site_name)
            if not recommended_method:
                recommended_method = ScrapingMethod.REQUESTS  # 預設策略
            
            config = ScrapingConfig(
                method=recommended_method,
                mode=ScrapingMode.ASYNC
            )
        
        # 獲取策略
        strategy = self.strategy_manager.get_strategy(config)
        
        # 驗證輸入
        if not strategy.validate_input(scraper_input):
            return ScrapingResult(
                success=False,
                jobs=[],
                errors=["輸入參數驗證失敗"]
            )
        
        self.logger.info(
            f"開始爬取: {scraper_input.site_name.value} - {scraper_input.search_term}",
            category=LogCategory.SCRAPING,
            metadata={
                'strategy': strategy.__class__.__name__,
                'method': config.method.value,
                'location': scraper_input.location,
                'results_wanted': scraper_input.results_wanted
            }
        )
        
        try:
            # 設置策略
            await strategy.setup()
            
            # 執行爬取
            result = await strategy.scrape_jobs(scraper_input)
            
            self.logger.info(
                f"爬取完成: {len(result.jobs)} 個職位",
                category=LogCategory.SCRAPING,
                metadata={
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'cache_hit': result.cache_hit,
                    'errors': len(result.errors)
                }
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                f"爬取過程發生錯誤: {str(e)}",
                category=LogCategory.ERROR,
                metadata={
                    'strategy': strategy.__class__.__name__,
                    'error_type': type(e).__name__
                }
            )
            
            return ScrapingResult(
                success=False,
                jobs=[],
                errors=[str(e)]
            )
        
        finally:
            # 清理資源
            await strategy.cleanup()
    
    async def scrape_multiple_sites(self, scraper_inputs: List[ScraperInput],
                                   configs: Optional[List[ScrapingConfig]] = None) -> List[ScrapingResult]:
        """爬取多個網站"""
        if configs and len(configs) != len(scraper_inputs):
            raise ValueError("配置數量必須與輸入數量相同")
        
        tasks = []
        for i, scraper_input in enumerate(scraper_inputs):
            config = configs[i] if configs else None
            task = self.scrape_jobs(scraper_input, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(ScrapingResult(
                    success=False,
                    jobs=[],
                    errors=[str(result)]
                ))
            else:
                final_results.append(result)
        
        return final_results


# 全域策略管理器實例
_global_strategy_manager = StrategyManager()


def get_strategy_manager() -> StrategyManager:
    """獲取全域策略管理器"""
    return _global_strategy_manager


def create_unified_scraper(strategy_manager: Optional[StrategyManager] = None) -> UnifiedScraper:
    """創建統一爬蟲實例"""
    return UnifiedScraper(strategy_manager or get_strategy_manager())
