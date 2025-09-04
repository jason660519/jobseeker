# -*- coding: utf-8 -*-
"""
Seek爬蟲引擎核心模組
整合Playwright瀏覽器自動化、Beautiful Soup HTML解析、PaddleOCR文字識別
實現智能化的求職網站數據抓取與ETL處理

Author: JobSpy Team
Date: 2024
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import aiofiles
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from bs4 import BeautifulSoup
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    logging.warning("PaddleOCR not installed. OCR functionality will be disabled.")

from ..model import JobPost
from ..util import extract_emails_from_text, extract_salary
from . import SeekScraper


class SeekCrawlerEngine:
    """
    Seek爬蟲引擎主類
    負責協調瀏覽器自動化、HTML解析、OCR處理和數據ETL流程
    """
    
    def __init__(self, 
                 headless: bool = True,
                 slow_mo: int = 100,
                 timeout: int = 30000,
                 enable_ocr: bool = True,
                 ocr_languages: List[str] = None,
                 storage_path: str = None):
        """
        初始化Seek爬蟲引擎
        
        Args:
            headless: 是否使用無頭瀏覽器模式
            slow_mo: 操作間延遲時間(毫秒)
            timeout: 頁面加載超時時間(毫秒)
            enable_ocr: 是否啟用OCR功能
            ocr_languages: OCR支持的語言列表
            storage_path: 數據存儲路徑
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.enable_ocr = enable_ocr
        self.ocr_languages = ocr_languages or ['en', 'ch_sim']
        
        # 設置存儲路徑
        self.storage_path = Path(storage_path) if storage_path else Path("./seek_data")
        self.storage_path.mkdir(exist_ok=True)
        
        # 初始化組件
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ocr_engine = None
        
        # 初始化OCR引擎
        if self.enable_ocr and PaddleOCR:
            try:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',  # 主要語言
                    use_gpu=False,
                    show_log=False
                )
                logging.info("PaddleOCR引擎初始化成功")
            except Exception as e:
                logging.error(f"PaddleOCR初始化失敗: {e}")
                self.enable_ocr = False
        
        # 設置日誌
        self._setup_logging()
        
        # 統計信息
        self.stats = {
            'pages_crawled': 0,
            'jobs_extracted': 0,
            'screenshots_taken': 0,
            'ocr_processed': 0,
            'errors': 0
        }
    
    def _setup_logging(self):
        """設置日誌配置"""
        log_path = self.storage_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        log_file = log_path / f"seek_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize_browser(self) -> bool:
        """
        初始化Playwright瀏覽器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.playwright = await async_playwright().start()
            
            # 啟動瀏覽器
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # 創建瀏覽器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 創建頁面
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            self.logger.info("瀏覽器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"瀏覽器初始化失敗: {e}")
            return False
    
    async def navigate_to_search(self, 
                               search_term: str, 
                               location: str = "",
                               job_type: str = "") -> bool:
        """
        導航到Seek搜索頁面並執行搜索
        
        Args:
            search_term: 搜索關鍵詞
            location: 工作地點
            job_type: 工作類型
            
        Returns:
            bool: 導航是否成功
        """
        try:
            # 構建搜索URL
            base_url = "https://www.seek.com.au/jobs"
            search_params = []
            
            if search_term:
                search_params.append(f"keywords={search_term}")
            if location:
                search_params.append(f"where={location}")
            if job_type:
                search_params.append(f"jobtype={job_type}")
            
            search_url = f"{base_url}?{'&'.join(search_params)}" if search_params else base_url
            
            self.logger.info(f"導航到搜索頁面: {search_url}")
            
            # 導航到頁面
            await self.page.goto(search_url, wait_until='networkidle')
            
            # 等待搜索結果加載
            await self.page.wait_for_selector('[data-automation="jobListing"]', timeout=10000)
            
            self.stats['pages_crawled'] += 1
            self.logger.info("成功導航到搜索頁面並加載結果")
            return True
            
        except Exception as e:
            self.logger.error(f"導航到搜索頁面失敗: {e}")
            self.stats['errors'] += 1
            return False
    
    async def take_intelligent_screenshot(self, 
                                        filename_prefix: str = "seek_page") -> Optional[str]:
        """
        智能截圖功能
        
        Args:
            filename_prefix: 文件名前綴
            
        Returns:
            Optional[str]: 截圖文件路徑
        """
        try:
            # 創建截圖目錄
            screenshot_dir = self.storage_path / "screenshots" / datetime.now().strftime('%Y%m%d')
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%H%M%S_%f')[:-3]
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            # 截取全頁面截圖
            await self.page.screenshot(
                path=str(filepath),
                full_page=True,
                type='png'
            )
            
            self.stats['screenshots_taken'] += 1
            self.logger.info(f"截圖已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"截圖失敗: {e}")
            self.stats['errors'] += 1
            return None
    
    async def extract_page_content(self) -> Tuple[str, BeautifulSoup]:
        """
        提取頁面HTML內容並創建BeautifulSoup對象
        
        Returns:
            Tuple[str, BeautifulSoup]: 原始HTML和解析對象
        """
        try:
            # 獲取頁面HTML
            html_content = await self.page.content()
            
            # 創建BeautifulSoup對象
            soup = BeautifulSoup(html_content, 'html.parser')
            
            self.logger.info("頁面內容提取成功")
            return html_content, soup
            
        except Exception as e:
            self.logger.error(f"頁面內容提取失敗: {e}")
            self.stats['errors'] += 1
            return "", BeautifulSoup("", 'html.parser')
    
    async def process_ocr_if_needed(self, screenshot_path: str) -> Dict[str, Any]:
        """
        如果啟用OCR，處理截圖進行文字識別
        
        Args:
            screenshot_path: 截圖文件路徑
            
        Returns:
            Dict[str, Any]: OCR識別結果
        """
        ocr_result = {'enabled': False, 'text': '', 'confidence': 0, 'details': []}
        
        if not self.enable_ocr or not self.ocr_engine or not screenshot_path:
            return ocr_result
        
        try:
            # 執行OCR識別
            result = self.ocr_engine.ocr(screenshot_path, cls=True)
            
            if result and result[0]:
                ocr_result['enabled'] = True
                extracted_texts = []
                total_confidence = 0
                
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                        confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.8
                        
                        extracted_texts.append(text)
                        total_confidence += confidence
                        
                        ocr_result['details'].append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': line[0] if len(line) > 0 else []
                        })
                
                ocr_result['text'] = ' '.join(extracted_texts)
                ocr_result['confidence'] = total_confidence / len(result[0]) if result[0] else 0
                
                self.stats['ocr_processed'] += 1
                self.logger.info(f"OCR處理完成，識別文字長度: {len(ocr_result['text'])}")
            
        except Exception as e:
            self.logger.error(f"OCR處理失敗: {e}")
            self.stats['errors'] += 1
        
        return ocr_result
    
    async def extract_job_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        從BeautifulSoup對象中提取職位列表
        
        Args:
            soup: BeautifulSoup解析對象
            
        Returns:
            List[Dict[str, Any]]: 提取的職位信息列表
        """
        jobs = []
        
        try:
            # 查找職位列表容器
            job_cards = soup.find_all('article', {'data-automation': 'jobListing'})
            
            for card in job_cards:
                job_data = self._extract_single_job(card)
                if job_data:
                    jobs.append(job_data)
            
            self.stats['jobs_extracted'] += len(jobs)
            self.logger.info(f"成功提取 {len(jobs)} 個職位信息")
            
        except Exception as e:
            self.logger.error(f"職位信息提取失敗: {e}")
            self.stats['errors'] += 1
        
        return jobs
    
    def _extract_single_job(self, job_card) -> Optional[Dict[str, Any]]:
        """
        從單個職位卡片中提取信息
        
        Args:
            job_card: BeautifulSoup職位卡片元素
            
        Returns:
            Optional[Dict[str, Any]]: 職位信息字典
        """
        try:
            # 提取基本信息
            title_elem = job_card.find('a', {'data-automation': 'jobTitle'})
            title = title_elem.get_text(strip=True) if title_elem else "未知職位"
            
            company_elem = job_card.find('a', {'data-automation': 'jobCompany'})
            company = company_elem.get_text(strip=True) if company_elem else "未知公司"
            
            location_elem = job_card.find('a', {'data-automation': 'jobLocation'})
            location = location_elem.get_text(strip=True) if location_elem else "未知地點"
            
            # 提取薪資信息
            salary_elem = job_card.find('span', {'data-automation': 'jobSalary'})
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # 提取職位鏈接
            job_url = title_elem.get('href') if title_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = f"https://www.seek.com.au{job_url}"
            
            # 提取描述
            desc_elem = job_card.find('span', {'data-automation': 'jobShortDescription'})
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'description': description,
                'url': job_url,
                'extracted_at': datetime.now().isoformat(),
                'source': 'seek.com.au'
            }
            
        except Exception as e:
            self.logger.error(f"單個職位信息提取失敗: {e}")
            return None
    
    async def save_raw_data(self, 
                          data: Dict[str, Any], 
                          data_type: str = "job_listings") -> str:
        """
        保存原始數據到文件
        
        Args:
            data: 要保存的數據
            data_type: 數據類型
            
        Returns:
            str: 保存的文件路徑
        """
        try:
            # 創建數據目錄
            data_dir = self.storage_path / "raw_data" / datetime.now().strftime('%Y%m%d')
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%H%M%S_%f')[:-3]
            filename = f"{data_type}_{timestamp}.json"
            filepath = data_dir / filename
            
            # 異步保存數據
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            self.logger.info(f"原始數據已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"數據保存失敗: {e}")
            self.stats['errors'] += 1
            return ""
    
    async def handle_pagination(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        處理分頁，抓取多頁數據
        
        Args:
            max_pages: 最大抓取頁數
            
        Returns:
            List[Dict[str, Any]]: 所有頁面的職位數據
        """
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            try:
                self.logger.info(f"處理第 {current_page} 頁")
                
                # 截圖
                screenshot_path = await self.take_intelligent_screenshot(
                    f"page_{current_page}"
                )
                
                # 提取頁面內容
                html_content, soup = await self.extract_page_content()
                
                # 提取職位信息
                page_jobs = await self.extract_job_listings(soup)
                
                # OCR處理（如果啟用）
                ocr_result = await self.process_ocr_if_needed(screenshot_path)
                
                # 保存頁面數據
                page_data = {
                    'page_number': current_page,
                    'jobs': page_jobs,
                    'html_content': html_content,
                    'ocr_result': ocr_result,
                    'screenshot_path': screenshot_path,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.save_raw_data(page_data, f"page_{current_page}")
                all_jobs.extend(page_jobs)
                
                # 檢查是否有下一頁
                next_button = await self.page.query_selector('a[aria-label="Next"]')
                if not next_button or current_page >= max_pages:
                    break
                
                # 點擊下一頁
                await next_button.click()
                await self.page.wait_for_load_state('networkidle')
                
                current_page += 1
                
                # 添加延遲避免被檢測
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"處理第 {current_page} 頁時出錯: {e}")
                self.stats['errors'] += 1
                break
        
        return all_jobs
    
    async def cleanup(self):
        """
        清理資源
        """
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.logger.info("資源清理完成")
            
        except Exception as e:
            self.logger.error(f"資源清理失敗: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取爬蟲統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        return {
            **self.stats,
            'storage_path': str(self.storage_path),
            'ocr_enabled': self.enable_ocr,
            'session_duration': time.time()
        }


# 使用示例
if __name__ == "__main__":
    async def main():
        # 創建爬蟲引擎實例
        crawler = SeekCrawlerEngine(
            headless=False,  # 顯示瀏覽器便於調試
            enable_ocr=True,
            storage_path="./seek_crawler_data"
        )
        
        try:
            # 初始化瀏覽器
            if await crawler.initialize_browser():
                # 執行搜索
                if await crawler.navigate_to_search("python developer", "Sydney"):
                    # 抓取多頁數據
                    all_jobs = await crawler.handle_pagination(max_pages=3)
                    
                    print(f"總共抓取到 {len(all_jobs)} 個職位")
                    print(f"爬蟲統計: {crawler.get_stats()}")
        
        finally:
            # 清理資源
            await crawler.cleanup()
    
    # 運行示例
    asyncio.run(main())