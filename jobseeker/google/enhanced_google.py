from __future__ import annotations

import math
import re
import json
import time
import random
from typing import Tuple, Optional
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup

from .constant import headers_jobs, headers_initial, async_param
from ..anti_detection import AntiDetectionScraper
from ..model import (
    Scraper,
    ScraperInput,
    Site,
    JobPost,
    JobResponse,
    Location,
    JobType,
)
from ..util import extract_emails_from_text, extract_job_type, create_session, create_logger
from .util import find_job_info_initial_page, find_job_info

log = create_logger("EnhancedGoogle")


class EnhancedGoogle(Scraper):
    """
    增強版 Google Jobs 爬蟲，使用 Playwright 解決動態內容載入和初始游標問題
    """
    
    def __init__(
        self, 
        proxies: list[str] | str | None = None, 
        ca_cert: str | None = None, 
        user_agent: str | None = None
    ):
        """
        初始化增強版 Google Jobs 爬蟲
        """
        site = Site(Site.GOOGLE)
        super().__init__(site, proxies=proxies, ca_cert=ca_cert)

        self.country = None
        self.session = None
        self.scraper_input = None
        self.jobs_per_page = 10
        self.seen_urls = set()
        self.url = "https://www.google.com/search"
        self.jobs_url = "https://www.google.com/async/callback:550"
        
        # 反檢測管理器
        self.anti_detection = AntiDetectionScraper()
        
        # Playwright 相關
        self.playwright = None
        self.browser = None
        self.page = None
        
        # 智能重試參數
        self.max_retries = 3
        self.base_delay = 2
        self.max_delay = 10

    def _init_playwright(self) -> bool:
        """
        初始化 Playwright 瀏覽器
        """
        try:
            self.playwright = sync_playwright().start()
            browser_config = self.anti_detection.get_browser_config()
            
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=browser_config['args']
            )
            
            context = self.browser.new_context(
                user_agent=browser_config['user_agent'],
                viewport=browser_config['viewport'],
                extra_http_headers=browser_config['headers']
            )
            
            self.page = context.new_page()
            
            # 注入反檢測腳本
            self.anti_detection.inject_stealth_scripts(self.page)
            
            log.info("Playwright 瀏覽器初始化成功")
            return True
            
        except Exception as e:
            log.error(f"Playwright 初始化失敗: {e}")
            return False

    def _cleanup_playwright(self):
        """
        清理 Playwright 資源
        """
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            log.warning(f"清理 Playwright 資源時出錯: {e}")

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        使用增強策略爬取 Google Jobs
        """
        self.scraper_input = scraper_input
        self.scraper_input.results_wanted = min(900, scraper_input.results_wanted)
        
        # 初始化 Playwright
        playwright_success = self._init_playwright()
        
        try:
            # 嘗試獲取初始游標和職位
            forward_cursor, job_list = self._get_initial_cursor_and_jobs_enhanced(playwright_success)
            
            if forward_cursor is None:
                log.warning("初始游標未找到，嘗試使用備用策略")
                # 如果 Playwright 失敗，嘗試傳統方法
                if playwright_success:
                    forward_cursor, job_list = self._get_initial_cursor_fallback()
                
                if forward_cursor is None:
                    log.warning("所有方法都無法獲取初始游標，返回已找到的職位")
                    return JobResponse(jobs=job_list)

            page = 1
            max_pages = math.ceil(scraper_input.results_wanted / self.jobs_per_page)
            
            # 分頁爬取
            while (
                len(self.seen_urls) < scraper_input.results_wanted + scraper_input.offset
                and forward_cursor
                and page <= max_pages
            ):
                log.info(f"搜尋頁面: {page} / {max_pages}")
                
                try:
                    jobs, forward_cursor = self._get_jobs_next_page_enhanced(
                        forward_cursor, playwright_success
                    )
                    
                    if not jobs:
                        log.info(f"頁面 {page} 未找到職位")
                        break
                        
                    job_list += jobs
                    log.info(f"頁面 {page} 找到 {len(jobs)} 個職位")
                    
                    # 智能延遲
                    if page < max_pages:
                        delay = self._calculate_smart_delay(page)
                        time.sleep(delay)
                        
                except Exception as e:
                    log.error(f"頁面 {page} 爬取失敗: {e}")
                    break
                    
                page += 1
                
        finally:
            self._cleanup_playwright()
            
        return JobResponse(
            jobs=job_list[
                scraper_input.offset : scraper_input.offset + scraper_input.results_wanted
            ]
        )

    def _calculate_smart_delay(self, page: int) -> float:
        """
        計算智能延遲時間
        """
        base = self.base_delay + (page * 0.3)
        random_factor = random.uniform(0.8, 1.5)
        delay = min(base * random_factor, self.max_delay)
        return delay

    def _get_initial_cursor_and_jobs_enhanced(
        self, use_playwright: bool
    ) -> Tuple[Optional[str], list[JobPost]]:
        """
        使用增強策略獲取初始游標和職位
        """
        if use_playwright and self.page:
            try:
                return self._get_initial_cursor_playwright()
            except Exception as e:
                log.warning(f"Playwright 方法失敗: {e}，回退到傳統方法")
                
        return self._get_initial_cursor_fallback()

    def _get_initial_cursor_playwright(self) -> Tuple[Optional[str], list[JobPost]]:
        """
        使用 Playwright 獲取初始游標
        """
        query = self._build_search_query()
        params = {"q": query, "udm": "8"}
        
        # 構建 URL
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{self.url}?{param_string}"
        
        # 模擬人類行為
        self.anti_detection.simulate_human_behavior(self.page)
        
        # 訪問搜索頁面
        response = self.page.goto(full_url, wait_until="networkidle")
        
        if response.status not in range(200, 400):
            raise Exception(f"HTTP {response.status}")
            
        # 等待動態內容載入
        try:
            self.page.wait_for_selector('[jsname="Yust4d"]', timeout=10000)
        except:
            log.warning("等待動態內容載入超時")
            
        # 獲取頁面內容
        content = self.page.content()
        
        # 解析游標
        pattern_fc = r'<div jsname="Yust4d"[^>]+data-async-fc="([^"]+)"'
        match_fc = re.search(pattern_fc, content)
        data_async_fc = match_fc.group(1) if match_fc else None
        
        # 解析職位
        jobs_raw = find_job_info_initial_page(content)
        jobs = []
        for job_raw in jobs_raw:
            job_post = self._parse_job(job_raw)
            if job_post:
                jobs.append(job_post)
                
        log.info(f"Playwright 方法找到初始游標: {data_async_fc is not None}，職位數: {len(jobs)}")
        return data_async_fc, jobs

    def _get_initial_cursor_fallback(self) -> Tuple[Optional[str], list[JobPost]]:
        """
        傳統方法獲取初始游標（備用）
        """
        query = self._build_search_query()
        params = {"q": query, "udm": "8"}
        
        # 創建增強的 session
        self.session = create_session(
            proxies=self.proxies, ca_cert=self.ca_cert, is_tls=False, has_retry=True
        )
        
        # 使用反檢測頭部
        enhanced_headers = self.anti_detection.get_random_headers()
        enhanced_headers.update(headers_initial)
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(self.url, headers=enhanced_headers, params=params)
                
                if response.status_code not in range(200, 400):
                    raise Exception(f"HTTP {response.status_code}")
                    
                pattern_fc = r'<div jsname="Yust4d"[^>]+data-async-fc="([^"]+)"'
                match_fc = re.search(pattern_fc, response.text)
                data_async_fc = match_fc.group(1) if match_fc else None
                
                jobs_raw = find_job_info_initial_page(response.text)
                jobs = []
                for job_raw in jobs_raw:
                    job_post = self._parse_job(job_raw)
                    if job_post:
                        jobs.append(job_post)
                        
                log.info(f"傳統方法找到初始游標: {data_async_fc is not None}，職位數: {len(jobs)}")
                return data_async_fc, jobs
                
            except Exception as e:
                log.warning(f"嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.max_retries - 1:
                    delay = (attempt + 1) * 2
                    time.sleep(delay)
                    
        return None, []

    def _build_search_query(self) -> str:
        """
        構建搜索查詢字符串
        """
        query = f"{self.scraper_input.search_term} jobs"

        def get_time_range(hours_old):
            if hours_old <= 24:
                return "since yesterday"
            elif hours_old <= 72:
                return "in the last 3 days"
            elif hours_old <= 168:
                return "in the last week"
            else:
                return "in the last month"

        job_type_mapping = {
            JobType.FULL_TIME: "Full time",
            JobType.PART_TIME: "Part time",
            JobType.INTERNSHIP: "Internship",
            JobType.CONTRACT: "Contract",
        }

        if self.scraper_input.job_type in job_type_mapping:
            query += f" {job_type_mapping[self.scraper_input.job_type]}"

        if self.scraper_input.location:
            query += f" near {self.scraper_input.location}"

        if self.scraper_input.hours_old:
            time_filter = get_time_range(self.scraper_input.hours_old)
            query += f" {time_filter}"

        if self.scraper_input.is_remote:
            query += " remote"

        if self.scraper_input.google_search_term:
            query = self.scraper_input.google_search_term
            
        return query

    def _get_jobs_next_page_enhanced(
        self, forward_cursor: str, use_playwright: bool
    ) -> Tuple[list[JobPost], Optional[str]]:
        """
        使用增強策略獲取下一頁職位
        """
        if use_playwright and self.page:
            try:
                return self._get_jobs_next_page_playwright(forward_cursor)
            except Exception as e:
                log.warning(f"Playwright 分頁失敗: {e}，回退到傳統方法")
                
        return self._get_jobs_next_page_traditional(forward_cursor)

    def _get_jobs_next_page_playwright(
        self, forward_cursor: str
    ) -> Tuple[list[JobPost], Optional[str]]:
        """
        使用 Playwright 獲取下一頁
        """
        params = {"fc": [forward_cursor], "fcv": ["3"], "async": [async_param]}
        param_string = "&".join([f"{k}={v[0]}" for k, v in params.items()])
        full_url = f"{self.jobs_url}?{param_string}"
        
        # 模擬人類行為
        self.anti_detection.simulate_human_behavior(self.page)
        
        response = self.page.goto(full_url, wait_until="networkidle")
        
        if response.status not in range(200, 400):
            raise Exception(f"HTTP {response.status}")
            
        content = self.page.content()
        return self._parse_jobs(content)

    def _get_jobs_next_page_traditional(
        self, forward_cursor: str
    ) -> Tuple[list[JobPost], Optional[str]]:
        """
        使用傳統方法獲取下一頁
        """
        params = {"fc": [forward_cursor], "fcv": ["3"], "async": [async_param]}
        
        # 使用增強頭部
        enhanced_headers = self.anti_detection.get_random_headers()
        enhanced_headers.update(headers_jobs)
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(self.jobs_url, headers=enhanced_headers, params=params)
                
                if response.status_code not in range(200, 400):
                    raise Exception(f"HTTP {response.status_code}")
                    
                return self._parse_jobs(response.text)
                
            except Exception as e:
                log.warning(f"分頁嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 1.5)
                    
        return [], None

    def _parse_jobs(self, job_data: str) -> Tuple[list[JobPost], Optional[str]]:
        """
        解析職位數據和下一頁游標
        """
        try:
            start_idx = job_data.find("[[[")
            end_idx = job_data.rindex("]]]")
            
            if start_idx == -1 or end_idx == -1:
                log.warning("無法找到有效的 JSON 數據")
                return [], None
                
            end_idx += 3
            s = job_data[start_idx:end_idx]
            parsed = json.loads(s)[0]

            pattern_fc = r'data-async-fc="([^"]+)"'
            match_fc = re.search(pattern_fc, job_data)
            data_async_fc = match_fc.group(1) if match_fc else None
            
            jobs_on_page = []
            for array in parsed:
                _, job_data_inner = array
                if not job_data_inner.startswith("[[["):
                    continue
                    
                job_d = json.loads(job_data_inner)
                job_info = find_job_info(job_d)
                job_post = self._parse_job(job_info)
                if job_post:
                    jobs_on_page.append(job_post)
                    
            return jobs_on_page, data_async_fc
            
        except Exception as e:
            log.error(f"解析職位數據失敗: {e}")
            return [], None

    def _parse_job(self, job_info: list) -> Optional[JobPost]:
        """
        解析單個職位信息
        """
        try:
            job_url = job_info[3][0][0] if job_info[3] and job_info[3][0] else None
            if job_url in self.seen_urls:
                return None
            self.seen_urls.add(job_url)

            title = job_info[0]
            company_name = job_info[1]
            location = city = job_info[2]
            state = country = date_posted = None
            
            if location and "," in location:
                city, state, *country = [*map(lambda x: x.strip(), location.split(","))]

            days_ago_str = job_info[12]
            if type(days_ago_str) == str:
                match = re.search(r"\d+", days_ago_str)
                days_ago = int(match.group()) if match else None
                date_posted = (datetime.now() - timedelta(days=days_ago)).date()

            description = job_info[19]

            job_post = JobPost(
                id=f"go-{job_info[28]}",
                title=title,
                company_name=company_name,
                location=Location(
                    city=city, state=state, country=country[0] if country else None
                ),
                job_url=job_url,
                date_posted=date_posted,
                is_remote="remote" in description.lower() or "wfh" in description.lower(),
                description=description,
                emails=extract_emails_from_text(description),
                job_type=extract_job_type(description),
            )
            return job_post
            
        except Exception as e:
            log.warning(f"解析職位失敗: {e}")
            return None
