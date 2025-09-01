from __future__ import annotations

import asyncio
import random
import time
import math
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..model import (
    Scraper,
    ScraperInput,
    Site,
    JobPost,
    JobResponse,
    Location,
    Country,
)
from ..util import create_logger, create_session
from ..anti_detection import AntiDetectionScraper

log = create_logger("EnhancedBayt")


class EnhancedBaytScraper(Scraper):
    """
    增強版 Bayt 爬蟲，使用 Playwright 和反檢測技術
    專門解決 403 錯誤和地理位置限制問題
    """
    
    base_url = "https://www.bayt.com"
    delay = 2
    band_delay = 3
    jobs_per_page = 20
    
    def __init__(
        self, 
        proxies: list[str] | str | None = None, 
        ca_cert: str | None = None, 
        user_agent: str | None = None
    ):
        super().__init__(Site.BAYT, proxies=proxies, ca_cert=ca_cert)
        self.scraper_input = None
        self.session = None
        self.country = "worldwide"
        
        # Playwright 相關
        self.playwright = None
        self.browser = None
        self.context = None
        self.anti_detection = AntiDetectionScraper()
        
        # 中東地區特定配置
        self.middle_east_locations = [
            "Dubai, UAE", "Riyadh, Saudi Arabia", "Kuwait City, Kuwait",
            "Doha, Qatar", "Abu Dhabi, UAE", "Manama, Bahrain"
        ]
        
    def _init_playwright(self) -> bool:
        """
        初始化 Playwright 瀏覽器
        """
        try:
            # 獲取反檢測配置
            browser_config = self.anti_detection.get_browser_config()
            
            # 啟動 Playwright
            self.playwright = asyncio.new_event_loop()
            asyncio.set_event_loop(self.playwright)
            
            async def setup_browser():
                playwright = await async_playwright().start()
                
                # 使用 Chrome 瀏覽器（更好的中東地區支援）
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--lang=ar-AE,ar,en-US,en',  # 阿拉伯語和英語支援
                        '--accept-lang=ar-AE,ar,en-US,en',
                        '--timezone-id=Asia/Dubai',  # 中東時區
                    ]
                )
                
                # 創建上下文，模擬中東地區用戶
                self.context = await self.browser.new_context(
                    user_agent=browser_config['user_agent'],
                    viewport={'width': 1920, 'height': 1080},
                    locale='ar-AE',  # 阿聯酋阿拉伯語
                    timezone_id='Asia/Dubai',
                    geolocation={'latitude': 25.2048, 'longitude': 55.2708},  # 杜拜座標
                    permissions=['geolocation'],
                    extra_http_headers={
                        'Accept-Language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                
                # 注入反檢測腳本
                await self.context.add_init_script("""
                    // 移除 webdriver 標識
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // 偽裝 Chrome 插件
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // 偽裝語言設置
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ar-AE', 'ar', 'en-US', 'en'],
                    });
                """)
                
            self.playwright.run_until_complete(setup_browser())
            log.info("Playwright 初始化成功，已配置中東地區環境")
            return True
            
        except Exception as e:
            log.error(f"Playwright 初始化失敗: {str(e)}")
            return False
    
    def _cleanup_playwright(self):
        """
        清理 Playwright 資源
        """
        try:
            if self.context:
                self.playwright.run_until_complete(self.context.close())
            if self.browser:
                self.playwright.run_until_complete(self.browser.close())
            if self.playwright:
                self.playwright.close()
            log.info("Playwright 資源已清理")
        except Exception as e:
            log.error(f"清理 Playwright 資源時出錯: {str(e)}")
    
    def _calculate_smart_delay(self, page: int) -> float:
        """
        計算智能延遲時間
        """
        base_delay = 3.0  # 基礎延遲
        page_factor = min(page * 0.5, 5.0)  # 頁面因子
        random_factor = random.uniform(0.5, 2.0)  # 隨機因子
        return base_delay + page_factor + random_factor
    
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        使用增強策略爬取 Bayt 職位
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        
        # 初始化 Playwright
        playwright_success = self._init_playwright()
        
        try:
            results_wanted = scraper_input.results_wanted if scraper_input.results_wanted else 10
            max_pages = math.ceil(results_wanted / self.jobs_per_page)
            
            for page in range(1, max_pages + 1):
                if len(job_list) >= results_wanted:
                    break
                    
                # 智能延遲
                if page > 1:
                    delay = self._calculate_smart_delay(page)
                    log.info(f"智能延遲 {delay:.1f} 秒")
                    time.sleep(delay)
                
                log.info(f"搜尋頁面: {page} / {max_pages}")
                
                # 嘗試多種方法獲取職位
                jobs_on_page = self._fetch_jobs_with_fallback(
                    scraper_input.search_term, page, playwright_success
                )
                
                if jobs_on_page:
                    initial_count = len(job_list)
                    for job in jobs_on_page:
                        try:
                            job_post = self._extract_job_info(job)
                            if job_post:
                                job_list.append(job_post)
                                if len(job_list) >= results_wanted:
                                    break
                        except Exception as e:
                            log.error(f"提取職位信息時出錯: {str(e)}")
                            continue
                    
                    new_jobs = len(job_list) - initial_count
                    log.info(f"頁面 {page} 找到 {new_jobs} 個職位")
                    
                    if new_jobs == 0:
                        log.warning(f"頁面 {page} 未找到新職位，停止搜尋")
                        break
                else:
                    log.warning(f"頁面 {page} 未找到職位")
                    break
                    
        finally:
            self._cleanup_playwright()
            
        return JobResponse(jobs=job_list[:results_wanted])
    
    def _fetch_jobs_with_fallback(
        self, query: str, page: int, playwright_available: bool
    ) -> List[BeautifulSoup] | None:
        """
        使用多種方法獲取職位，包含備用方案
        """
        # 方法 1: 使用 Playwright（推薦）
        if playwright_available:
            try:
                return self._fetch_jobs_playwright(query, page)
            except Exception as e:
                log.warning(f"Playwright 方法失敗: {str(e)}，嘗試備用方法")
        
        # 方法 2: 使用增強的 requests（備用）
        try:
            return self._fetch_jobs_enhanced_requests(query, page)
        except Exception as e:
            log.error(f"增強 requests 方法失敗: {str(e)}")
        
        # 方法 3: 使用原始 requests（最後備用）
        try:
            return self._fetch_jobs_original(query, page)
        except Exception as e:
            log.error(f"原始 requests 方法失敗: {str(e)}")
        
        return None
    
    def _fetch_jobs_playwright(self, query: str, page: int) -> List[BeautifulSoup] | None:
        """
        使用 Playwright 獲取職位
        """
        async def fetch_page():
            page_obj = await self.context.new_page()
            try:
                # 構建 URL
                url = f"{self.base_url}/en/international/jobs/{query}-jobs/?page={page}"
                log.info(f"使用 Playwright 訪問: {url}")
                
                # 模擬人類行為：先訪問首頁
                if page == 1:
                    await page_obj.goto(self.base_url, wait_until='networkidle')
                    await page_obj.wait_for_timeout(random.randint(2000, 4000))
                
                # 訪問目標頁面
                response = await page_obj.goto(url, wait_until='networkidle')
                
                if response.status == 403:
                    log.warning("收到 403 錯誤，嘗試更換 User-Agent")
                    # 更換 User-Agent 並重試
                    new_config = self.anti_detection.get_browser_config()
                    await page_obj.set_extra_http_headers({
                        'User-Agent': new_config['user_agent']
                    })
                    await page_obj.wait_for_timeout(5000)
                    response = await page_obj.goto(url, wait_until='networkidle')
                
                if response.status != 200:
                    log.error(f"HTTP 狀態碼: {response.status}")
                    return None
                
                # 等待頁面載入
                await page_obj.wait_for_timeout(random.randint(3000, 6000))
                
                # 模擬滾動行為
                await page_obj.evaluate("""
                    window.scrollTo(0, document.body.scrollHeight / 3);
                """)
                await page_obj.wait_for_timeout(1000)
                
                await page_obj.evaluate("""
                    window.scrollTo(0, document.body.scrollHeight / 2);
                """)
                await page_obj.wait_for_timeout(1000)
                
                # 獲取頁面內容
                content = await page_obj.content()
                soup = BeautifulSoup(content, "html.parser")
                job_listings = soup.find_all("li", attrs={"data-js-job": ""})
                
                log.info(f"Playwright 找到 {len(job_listings)} 個職位元素")
                return job_listings
                
            finally:
                await page_obj.close()
        
        return self.playwright.run_until_complete(fetch_page())
    
    def _fetch_jobs_enhanced_requests(self, query: str, page: int) -> List[BeautifulSoup] | None:
        """
        使用增強的 requests 獲取職位
        """
        try:
            # 創建增強的 session
            if not self.session:
                self.session = create_session(
                    proxies=self.proxies, 
                    ca_cert=self.ca_cert, 
                    is_tls=False, 
                    has_retry=True
                )
            
            # 獲取反檢測配置
            config = self.anti_detection.get_browser_config()
            
            # 設置增強的請求頭
            headers = {
                'User-Agent': config['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # 如果是第一頁，先訪問首頁建立 session
            if page == 1:
                self.session.get(self.base_url, headers=headers)
                time.sleep(random.uniform(2, 4))
            
            url = f"{self.base_url}/en/international/jobs/{query}-jobs/?page={page}"
            log.info(f"使用增強 requests 訪問: {url}")
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            job_listings = soup.find_all("li", attrs={"data-js-job": ""})
            
            log.info(f"增強 requests 找到 {len(job_listings)} 個職位元素")
            return job_listings
            
        except Exception as e:
            log.error(f"增強 requests 方法出錯: {str(e)}")
            return None
    
    def _fetch_jobs_original(self, query: str, page: int) -> List[BeautifulSoup] | None:
        """
        使用原始方法獲取職位（最後備用）
        """
        try:
            if not self.session:
                self.session = create_session(
                    proxies=self.proxies, 
                    ca_cert=self.ca_cert, 
                    is_tls=False, 
                    has_retry=True
                )
            
            url = f"{self.base_url}/en/international/jobs/{query}-jobs/?page={page}"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            job_listings = soup.find_all("li", attrs={"data-js-job": ""})
            
            log.info(f"原始方法找到 {len(job_listings)} 個職位元素")
            return job_listings
            
        except Exception as e:
            log.error(f"原始方法出錯: {str(e)}")
            return None
    
    def _extract_job_info(self, job: BeautifulSoup) -> JobPost | None:
        """
        從職位元素中提取職位信息
        """
        try:
            # 查找標題和連結
            job_general_information = job.find("h2")
            if not job_general_information:
                return None

            job_title = job_general_information.get_text(strip=True)
            job_url = self._extract_job_url(job_general_information)
            if not job_url:
                return None

            # 提取公司名稱
            company_tag = job.find("div", class_="t-nowrap p10l")
            company_name = (
                company_tag.find("span").get_text(strip=True)
                if company_tag and company_tag.find("span")
                else None
            )

            # 提取地點
            location_tag = job.find("div", class_="t-mute t-small")
            location = location_tag.get_text(strip=True) if location_tag else None

            job_id = f"bayt-{abs(hash(job_url))}"
            location_obj = Location(
                city=location,
                country=Country.from_string(self.country),
            )
            
            return JobPost(
                id=job_id,
                title=job_title,
                company_name=company_name,
                location=location_obj,
                job_url=job_url,
            )
            
        except Exception as e:
            log.error(f"提取職位信息時出錯: {str(e)}")
            return None
    
    def _extract_job_url(self, job_general_information: BeautifulSoup) -> str | None:
        """
        從 h2 元素中提取職位 URL
        """
        try:
            a_tag = job_general_information.find("a")
            if a_tag and a_tag.has_attr("href"):
                return self.base_url + a_tag["href"].strip()
            return None
        except Exception as e:
            log.error(f"提取職位 URL 時出錯: {str(e)}")
            return None