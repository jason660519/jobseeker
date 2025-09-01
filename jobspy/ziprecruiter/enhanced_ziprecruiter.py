from __future__ import annotations

import json
import math
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Tuple, List

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser

from .constant import headers, get_cookie_data
from ..anti_detection import AntiDetectionScraper
from ..util import (
    extract_emails_from_text,
    create_session,
    markdown_converter,
    remove_attributes,
    create_logger,
)
from ..model import (
    JobPost,
    Compensation,
    Location,
    JobResponse,
    Country,
    DescriptionFormat,
    Scraper,
    ScraperInput,
    Site,
)
from .util import get_job_type_enum, add_params

log = create_logger("EnhancedZipRecruiter")


class EnhancedZipRecruiter(Scraper):
    """
    增強版 ZipRecruiter 爬蟲，使用 Playwright 和反檢測技術解決 429 錯誤
    """
    base_url = "https://www.ziprecruiter.com"
    api_url = "https://api.ziprecruiter.com"

    def __init__(
        self, 
        proxies: list[str] | str | None = None, 
        ca_cert: str | None = None, 
        user_agent: str | None = None
    ):
        """
        初始化增強版 ZipRecruiter 爬蟲
        """
        super().__init__(Site.ZIP_RECRUITER, proxies=proxies)
        
        self.scraper_input = None
        self.anti_detection = AntiDetectionScraper()
        
        # 智能請求調度參數
        self.base_delay = 3  # 基礎延遲
        self.max_delay = 15  # 最大延遲
        self.retry_count = 3  # 重試次數
        self.jobs_per_page = 20
        self.seen_urls = set()
        
        # Playwright 相關
        self.playwright = None
        self.browser = None
        self.page = None
        
        # 傳統 session 作為備用
        self.session = create_session(proxies=proxies, ca_cert=ca_cert)
        self.session.headers.update(headers)

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
        使用增強策略爬取 ZipRecruiter 職位
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        continue_token = None
        
        # 嘗試使用 Playwright
        playwright_success = self._init_playwright()
        
        try:
            max_pages = math.ceil(scraper_input.results_wanted / self.jobs_per_page)
            
            for page in range(1, max_pages + 1):
                if len(job_list) >= scraper_input.results_wanted:
                    break
                    
                # 智能延遲
                if page > 1:
                    delay = self._calculate_smart_delay(page)
                    log.info(f"智能延遲 {delay} 秒")
                    time.sleep(delay)
                
                log.info(f"搜尋頁面: {page} / {max_pages}")
                
                # 嘗試多種方法獲取職位
                jobs_on_page, continue_token = self._find_jobs_with_fallback(
                    scraper_input, continue_token, playwright_success
                )
                
                if jobs_on_page:
                    job_list.extend(jobs_on_page)
                    log.info(f"頁面 {page} 找到 {len(jobs_on_page)} 個職位")
                else:
                    log.warning(f"頁面 {page} 未找到職位")
                    break
                    
                if not continue_token:
                    break
                    
        finally:
            self._cleanup_playwright()
            
        return JobResponse(jobs=job_list[: scraper_input.results_wanted])

    def _calculate_smart_delay(self, page: int) -> float:
        """
        計算智能延遲時間
        """
        # 基於頁面數量和隨機因子計算延遲
        base = self.base_delay + (page * 0.5)
        random_factor = random.uniform(0.5, 1.5)
        delay = min(base * random_factor, self.max_delay)
        return delay

    def _find_jobs_with_fallback(
        self, 
        scraper_input: ScraperInput, 
        continue_token: str | None, 
        use_playwright: bool
    ) -> tuple[list[JobPost], str | None]:
        """
        使用多種方法嘗試獲取職位，包含容錯機制
        """
        for attempt in range(self.retry_count):
            try:
                if use_playwright and self.page:
                    # 嘗試使用 Playwright
                    jobs, token = self._find_jobs_playwright(scraper_input, continue_token)
                    if jobs:
                        return jobs, token
                
                # 回退到傳統方法
                jobs, token = self._find_jobs_traditional(scraper_input, continue_token)
                if jobs:
                    return jobs, token
                    
            except Exception as e:
                log.warning(f"嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.retry_count - 1:
                    delay = (attempt + 1) * 2
                    log.info(f"等待 {delay} 秒後重試")
                    time.sleep(delay)
                    
        return [], None

    def _find_jobs_playwright(
        self, 
        scraper_input: ScraperInput, 
        continue_token: str | None
    ) -> tuple[list[JobPost], str | None]:
        """
        使用 Playwright 獲取職位
        """
        params = add_params(scraper_input)
        if continue_token:
            params["continue_from"] = continue_token
            
        # 構建 URL
        url = f"{self.api_url}/jobs-app/jobs"
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_string}"
        
        # 模擬人類行為
        self.anti_detection.simulate_human_behavior(self.page)
        
        # 訪問 API
        response = self.page.goto(full_url, wait_until="networkidle")
        
        if response.status == 429:
            log.warning("遇到 429 錯誤，切換策略")
            raise Exception("429 Too Many Requests")
            
        if response.status not in range(200, 400):
            raise Exception(f"HTTP {response.status}")
            
        # 解析 JSON 響應
        content = self.page.content()
        # 從頁面中提取 JSON（如果是 JSON 響應）
        try:
            res_data = json.loads(content)
        except:
            # 如果不是純 JSON，嘗試從 pre 標籤中提取
            soup = BeautifulSoup(content, 'html.parser')
            pre_tag = soup.find('pre')
            if pre_tag:
                res_data = json.loads(pre_tag.text)
            else:
                raise Exception("無法解析 JSON 響應")
        
        jobs_list = res_data.get("jobs", [])
        next_continue_token = res_data.get("continue", None)
        
        # 處理職位
        with ThreadPoolExecutor(max_workers=self.jobs_per_page) as executor:
            job_results = [executor.submit(self._process_job, job) for job in jobs_list]
        
        job_list = list(filter(None, (result.result() for result in job_results)))
        return job_list, next_continue_token

    def _find_jobs_traditional(
        self, 
        scraper_input: ScraperInput, 
        continue_token: str | None
    ) -> tuple[list[JobPost], str | None]:
        """
        使用傳統 requests 方法獲取職位（帶增強頭部）
        """
        jobs_list = []
        params = add_params(scraper_input)
        if continue_token:
            params["continue_from"] = continue_token
            
        # 使用反檢測管理器的頭部
        enhanced_headers = self.anti_detection.get_random_headers()
        self.session.headers.update(enhanced_headers)
        
        try:
            res = self.session.get(f"{self.api_url}/jobs-app/jobs", params=params)
            
            if res.status_code == 429:
                log.warning("傳統方法也遇到 429 錯誤")
                return jobs_list, ""
                
            if res.status_code not in range(200, 400):
                err = f"ZipRecruiter 響應狀態碼 {res.status_code}"
                if res.status_code != 429:
                    err += f" 響應內容: {res.text}"
                log.error(err)
                return jobs_list, ""
                
        except Exception as e:
            log.error(f"請求異常: {str(e)}")
            return jobs_list, ""
        
        res_data = res.json()
        jobs_list = res_data.get("jobs", [])
        next_continue_token = res_data.get("continue", None)
        
        with ThreadPoolExecutor(max_workers=self.jobs_per_page) as executor:
            job_results = [executor.submit(self._process_job, job) for job in jobs_list]
        
        job_list = list(filter(None, (result.result() for result in job_results)))
        return job_list, next_continue_token

    def _process_job(self, job: dict) -> JobPost | None:
        """
        處理單個職位數據
        """
        title = job.get("name")
        job_url = f"{self.base_url}/jobs//j?lvk={job['listing_key']}"
        if job_url in self.seen_urls:
            return
        self.seen_urls.add(job_url)

        description = job.get("job_description", "").strip()
        listing_type = job.get("buyer_type", "")
        description = (
            markdown_converter(description)
            if self.scraper_input.description_format == DescriptionFormat.MARKDOWN
            else description
        )
        company = job.get("hiring_company", {}).get("name")
        country_value = "usa" if job.get("job_country") == "US" else "canada"
        country_enum = Country.from_string(country_value)

        location = Location(
            city=job.get("job_city"), state=job.get("job_state"), country=country_enum
        )
        job_type = get_job_type_enum(
            job.get("employment_type", "").replace("_", "").lower()
        )
        date_posted = datetime.fromisoformat(job["posted_time"].rstrip("Z")).date()
        comp_interval = job.get("compensation_interval")
        comp_interval = "yearly" if comp_interval == "annual" else comp_interval
        comp_min = int(job["compensation_min"]) if "compensation_min" in job else None
        comp_max = int(job["compensation_max"]) if "compensation_max" in job else None
        comp_currency = job.get("compensation_currency")
        description_full, job_url_direct = self._get_descr(job_url)

        return JobPost(
            id=f'zr-{job["listing_key"]}',
            title=title,
            company_name=company,
            location=location,
            job_type=job_type,
            compensation=Compensation(
                interval=comp_interval,
                min_amount=comp_min,
                max_amount=comp_max,
                currency=comp_currency,
            ),
            date_posted=date_posted,
            job_url=job_url,
            description=description_full if description_full else description,
            emails=extract_emails_from_text(description) if description else None,
            job_url_direct=job_url_direct,
            listing_type=listing_type,
        )

    def _get_descr(self, job_url):
        """
        獲取職位詳細描述
        """
        # 使用增強的頭部
        enhanced_headers = self.anti_detection.get_random_headers()
        temp_session = create_session()
        temp_session.headers.update(enhanced_headers)
        
        res = temp_session.get(job_url, allow_redirects=True)
        description_full = job_url_direct = None
        
        if res.ok:
            soup = BeautifulSoup(res.text, "html.parser")
            job_descr_div = soup.find("div", class_="job_description")
            company_descr_section = soup.find("section", class_="company_description")
            job_description_clean = (
                remove_attributes(job_descr_div).prettify(formatter="html")
                if job_descr_div
                else ""
            )
            company_description_clean = (
                remove_attributes(company_descr_section).prettify(formatter="html")
                if company_descr_section
                else ""
            )
            description_full = job_description_clean + company_description_clean

            try:
                script_tag = soup.find("script", type="application/json")
                if script_tag:
                    job_json = json.loads(script_tag.string)
                    job_url_val = job_json["model"].get("saveJobURL", "")
                    m = re.search(r"job_url=(.+)", job_url_val)
                    if m:
                        job_url_direct = m.group(1)
            except:
                job_url_direct = None

            if self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
                description_full = markdown_converter(description_full)

        return description_full, job_url_direct
