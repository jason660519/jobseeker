"""Seek.com.au 職位爬蟲模塊

此模塊提供從 Seek.com.au 爬取職位信息的功能。
"""

import asyncio
import logging
import random
import re
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qs

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

from jobspy.model import (
    JobPost, JobResponse, JobType, Location, 
    Compensation, CompensationInterval, Site, Country,
    Scraper, ScraperInput
)
from .constant import (
    BASE_URL, USER_AGENTS, DEFAULT_HEADERS, 
    JOB_TYPE_MAPPING, STATE_MAPPING, SALARY_INTERVAL_MAPPING,
    SELECTORS, DELAYS, RETRY_CONFIG, TIMEOUT_CONFIG
)
from .util import (
    parse_location, parse_salary, get_job_type, 
    is_remote_job, clean_text, format_date, 
    generate_job_id, validate_url
)
from jobspy.util import create_logger


class SeekScraper(Scraper):
    """
    Seek.com.au 職位爬蟲類
    
    使用 Playwright 爬取 Seek.com.au 的職位信息
    """
    
    def __init__(self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None):
        """初始化爬蟲"""
        super().__init__(Site.SEEK, proxies=proxies, ca_cert=ca_cert, user_agent=user_agent)
        self.logger = create_logger("Seek")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.scraper_input: Optional[ScraperInput] = None
        self.playwright = None
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self._init_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self._close_browser()
        
    async def _init_browser(self):
        """初始化瀏覽器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # 創建新頁面
            self.page = await self.browser.new_page(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080}
            )
            
            # 設置額外的請求頭
            await self.page.set_extra_http_headers(DEFAULT_HEADERS)
            
            self.logger.info("瀏覽器初始化成功")
            
        except Exception as e:
            self.logger.error(f"瀏覽器初始化失敗: {e}")
            raise
            
    async def _close_browser(self):
        """關閉瀏覽器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self.logger.info("瀏覽器已關閉")
        except Exception as e:
            self.logger.error(f"關閉瀏覽器時出錯: {e}")
    
    def _build_search_url(self, search_term: str = "", location: str = "", 
                          job_type: str = "", distance: int = 0) -> str:
        """構建搜索 URL
        
        根據 Seek 網站的 URL 格式構建搜索 URL：
        - 基本格式: https://www.seek.com.au/jobs
        - 搜索詞: https://www.seek.com.au/ai-engineer-jobs
        - 搜索詞+分類: https://www.seek.com.au/aged-care-jobs-in-accounting
        - 搜索詞+分類+地點: https://www.seek.com.au/aged-care-jobs-in-accounting/in-All-Sydney-NSW
        - 加上距離參數: https://www.seek.com.au/aged-care-jobs-in-accounting/in-Gregory-Hills-NSW-2557?distance=25
        """
        url_parts = [BASE_URL]
        
        # 如果沒有任何搜索條件，返回基本 jobs 頁面
        if not search_term and not location:
            return f"{BASE_URL}/jobs"
        
        # 構建路徑部分
        path_parts = []
        
        # 添加搜索詞
        if search_term:
            # 將搜索詞轉換為 URL 友好格式
            search_slug = search_term.lower().replace(' ', '-').replace('/', '-')
            path_parts.append(f"{search_slug}-jobs")
        else:
            path_parts.append("jobs")
        
        # 添加職位類型（如果有）
        if job_type:
            job_type_slug = job_type.lower().replace(' ', '-')
            if path_parts and path_parts[-1] != "jobs":
                path_parts[-1] = f"{path_parts[-1]}-in-{job_type_slug}"
            else:
                path_parts.append(f"in-{job_type_slug}")
        
        # 添加地點
        if location:
            location_slug = location.replace(' ', '-').replace(',', '')
            path_parts.append(f"in-{location_slug}")
        
        # 組合 URL 路徑
        url = f"{BASE_URL}/{'/'.join(path_parts)}"
        
        # 添加查詢參數
        params = {}
        if distance > 0:
            params['distance'] = str(distance)
        
        if params:
            url += f"?{urlencode(params)}"
        
        return url
        
    async def _wait_and_scroll(self, delay_range: tuple = (2, 5)):
        """等待並滾動頁面"""
        # 隨機延遲
        delay = random.uniform(*delay_range)
        await asyncio.sleep(delay)
        
        # 滾動到頁面底部
        await self.page.evaluate("""
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        """)
        
        # 再次等待
        await asyncio.sleep(random.uniform(1, 3))
    
    async def _extract_job_data(self, job_element) -> Optional[Dict[str, Any]]:
        """從職位元素中提取數據"""
        try:
            # 提取職位標題和 URL
            title_element = await job_element.query_selector(SELECTORS['title'])
            if not title_element:
                return None
                
            title = await title_element.inner_text()
            job_url = await title_element.get_attribute('href')
            
            if job_url and not job_url.startswith('http'):
                job_url = f"https://www.seek.com.au{job_url}"
                
            # 提取公司名稱
            company_element = await job_element.query_selector(SELECTORS['company'])
            company = await company_element.inner_text() if company_element else ""
            
            # 提取地點
            location_element = await job_element.query_selector(SELECTORS['location'])
            location = await location_element.inner_text() if location_element else ""
            
            # 提取薪資
            salary_element = await job_element.query_selector(SELECTORS['salary'])
            salary = await salary_element.inner_text() if salary_element else ""
            
            # 提取工作類型
            job_type_element = await job_element.query_selector(SELECTORS['job_type'])
            job_type = await job_type_element.inner_text() if job_type_element else ""
            
            # 提取發布日期
            date_element = await job_element.query_selector(SELECTORS['date_posted'])
            date_posted = await date_element.inner_text() if date_element else ""
            
            # 提取職位描述（簡短版本）
            desc_element = await job_element.query_selector(SELECTORS['description'])
            description = await desc_element.inner_text() if desc_element else ""
            
            return {
                'title': clean_text(title),
                'company': clean_text(company),
                'location': clean_text(location),
                'salary': clean_text(salary),
                'job_type': clean_text(job_type),
                'date_posted': clean_text(date_posted),
                'description': clean_text(description),
                'job_url': job_url
            }
            
        except Exception as e:
            self.logger.error(f"提取職位數據時出錯: {e}")
            return None
    
    def _process_job_data(self, raw_data: Dict[str, Any]) -> Optional[JobPost]:
        """處理原始職位數據，轉換為 JobPost 對象"""
        try:
            # 解析地點
            city, state = parse_location(raw_data.get('location', ''))
            location = Location(city=city, state=state, country=Country.AUSTRALIA)
            
            # 解析薪資
            min_amount, max_amount, interval = parse_salary(raw_data.get('salary', ''))
            compensation = None
            if min_amount is not None or max_amount is not None:
                compensation = Compensation(
                    min_amount=min_amount,
                    max_amount=max_amount,
                    interval=interval
                )
            
            # 解析工作類型
            job_types = get_job_type(raw_data.get('job_type', ''))
            
            # 判斷是否為遠程工作
            is_remote = is_remote_job(
                raw_data.get('description', ''),
                raw_data.get('location', '')
            )
            
            # 生成職位 ID
            job_id = generate_job_id(
                raw_data.get('title', ''),
                raw_data.get('company', ''),
                raw_data.get('location', '')
            )
            
            # 創建 JobPost 對象
            job_post = JobPost(
                id=job_id,
                title=raw_data.get('title'),
                company_name=raw_data.get('company'),
                job_url=raw_data.get('job_url', ''),
                location=location,
                job_type=job_types if job_types else None,
                compensation=compensation,
                description=raw_data.get('description'),
                date_posted=format_date(raw_data.get('date_posted')),
                is_remote=is_remote
            )
            
            return job_post
            
        except Exception as e:
            self.logger.error(f"處理職位數據時出錯: {e}")
            return None
    
    async def _scrape_page(self, url: str) -> List[JobPost]:
        """爬取單個頁面的職位信息"""
        jobs = []
        
        try:
            # 訪問頁面
            self.logger.info(f"正在訪問 URL: {url}")
            response = await self.page.goto(
                url, 
                wait_until='domcontentloaded',
                timeout=TIMEOUT_CONFIG['page_load'] * 2000
            )
            
            if response.status != 200:
                self.logger.warning(f"頁面響應狀態碼: {response.status}")
                return jobs
                
            # 檢查頁面標題和內容
            page_title = await self.page.title()
            page_url = self.page.url
            self.logger.info(f"頁面標題: {page_title}")
            self.logger.info(f"當前 URL: {page_url}")
            
            # 檢查是否被重定向到錯誤頁面
            if 'error' in page_url.lower() or 'blocked' in page_url.lower():
                self.logger.error("頁面被重定向到錯誤頁面，可能被反爬蟲機制阻擋")
                return jobs
                
            # 等待頁面加載
            await self._wait_and_scroll()
            
            # 等待職位卡片加載
            try:
                # 首先等待主要內容區域
                await self.page.wait_for_selector('main', timeout=10000)
                
                # 然後等待職位卡片
                await self.page.wait_for_selector(
                    SELECTORS['job_item'],
                    timeout=TIMEOUT_CONFIG['element_wait'] * 2000
                )
                
                # 額外等待確保所有元素載入
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"未找到職位卡片元素: {e}")
                # 嘗試使用備用選擇器
                try:
                    await self.page.wait_for_selector('article[data-automation]', timeout=5000)
                    self.logger.info("使用備用選擇器找到職位元素")
                except Exception:
                     self.logger.error("所有選擇器都失敗")
                     # 保存截圖用於調試
                     try:
                         await self.page.screenshot(path='seek_error_debug.png')
                         self.logger.info("已保存錯誤截圖: seek_error_debug.png")
                     except Exception:
                         pass
                     return jobs
                
            # 獲取所有職位元素
            job_elements = await self.page.query_selector_all(SELECTORS['job_item'])
            
            # 如果主要選擇器沒有找到元素，嘗試備用選擇器
            if not job_elements:
                self.logger.info("主要選擇器未找到元素，嘗試備用選擇器")
                job_elements = await self.page.query_selector_all('article[data-automation]')
            
            self.logger.info(f"找到 {len(job_elements)} 個職位元素")
            
            # 提取每個職位的數據
            for job_element in job_elements:
                raw_data = await self._extract_job_data(job_element)
                if raw_data:
                    job_post = self._process_job_data(raw_data)
                    if job_post:
                        jobs.append(job_post)
                        
                # 隨機延遲
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
        except Exception as e:
            self.logger.error(f"爬取頁面時出錯: {e}")
            
        return jobs
    
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """爬取職位信息 - 實現 Scraper 基類的抽象方法"""
        self.scraper_input = scraper_input
        
        # 運行異步爬取
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self._async_scrape())
    
    async def _async_scrape(self) -> JobResponse:
        """異步爬取職位信息"""
        all_jobs = []
        
        try:
            # 初始化瀏覽器
            await self._init_browser()
            
            # 從 scraper_input 獲取參數
            search_term = self.scraper_input.search_term or ""
            location = self.scraper_input.location or ""
            job_type = self.scraper_input.job_type.value if self.scraper_input.job_type else ""
            distance = self.scraper_input.distance or 0
            
            # 計算需要爬取的頁數
            results_wanted = self.scraper_input.results_wanted or 15
            jobs_per_page = 20  # Seek 每頁大約 20 個職位
            max_pages = min(5, (results_wanted + jobs_per_page - 1) // jobs_per_page)
            
            # 構建搜索 URL
            base_url = self._build_search_url(search_term, location, job_type, distance)
            
            self.logger.info(f"開始爬取: {base_url}")
            
            # 爬取多個頁面
            for page_num in range(1, max_pages + 1):
                # 構建分頁 URL
                if page_num > 1:
                    separator = '&' if '?' in base_url else '?'
                    url = f"{base_url}{separator}page={page_num}"
                else:
                    url = base_url
                    
                self.logger.info(f"爬取第 {page_num} 頁: {url}")
                
                # 爬取當前頁面
                page_jobs = await self._scrape_page(url)
                
                if not page_jobs:
                    self.logger.info(f"第 {page_num} 頁沒有找到職位，停止爬取")
                    break
                    
                all_jobs.extend(page_jobs)
                self.logger.info(f"第 {page_num} 頁找到 {len(page_jobs)} 個職位")
                
                # 檢查是否已達到所需結果數量
                if len(all_jobs) >= results_wanted:
                    break
                
                # 頁面間延遲
                if page_num < max_pages:
                    delay = random.uniform(*DELAYS['between_pages'])
                    await asyncio.sleep(delay)
                    
        except Exception as e:
            self.logger.error(f"爬取過程中出錯: {e}")
        finally:
            # 關閉瀏覽器
            await self._close_browser()
            
        # 去重
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            if job.job_url and job.job_url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job.job_url)
                
        # 限制結果數量
        if self.scraper_input.results_wanted:
            unique_jobs = unique_jobs[:self.scraper_input.results_wanted]
                
        self.logger.info(f"總共找到 {len(unique_jobs)} 個唯一職位")
        
        return JobResponse(jobs=unique_jobs)
    
def scrape_jobs(search_term: str = "", location: str = "", 
               job_type: str = "", distance: int = 0, 
               max_pages: int = 5) -> JobResponse:
    """
    爬取 Seek.com.au 職位信息的主要函數
    
    Args:
        search_term: 搜索關鍵詞
        location: 工作地點
        job_type: 工作類型
        distance: 搜索距離（公里）
        max_pages: 最大爬取頁數
        
    Returns:
        JobResponse 對象，包含職位列表和總數
    """
    async def _async_scrape():
        async with SeekScraper() as scraper:
            return await scraper.scrape(
                search_term=search_term,
                location=location,
                job_type=job_type,
                distance=distance,
                max_pages=max_pages
            )
    
    # 運行異步函數
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(_async_scrape())


__all__ = ['SeekScraper', 'scrape_jobs']