# -*- coding: utf-8 -*-
"""
Seek增強型爬蟲整合模組
整合爬蟲引擎、ETL處理器和現有的Seek爬蟲功能
提供統一的高級接口用於Seek網站數據抓取

Author: JobSpy Team
Date: 2024
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .seek_crawler_engine import SeekCrawlerEngine
from .etl_processor import SeekETLProcessor
from ..model import JobPost, JobType, Country
from . import SeekScraper
from .constant import *


class SeekScraperEnhanced:
    """
    Seek增強型爬蟲主類
    整合傳統爬蟲方法和新的智能爬蟲引擎
    提供多種抓取策略和數據處理選項
    """
    
    def __init__(self,
                 scraping_mode: str = "hybrid",  # "traditional", "enhanced", "hybrid"
                 headless: bool = True,
                 enable_ocr: bool = True,
                 enable_screenshots: bool = True,
                 storage_path: str = None,
                 max_workers: int = 3,
                 rate_limit_delay: float = 2.0):
        """
        初始化Seek增強型爬蟲
        
        Args:
            scraping_mode: 爬蟲模式 ("traditional", "enhanced", "hybrid")
            headless: 是否使用無頭瀏覽器
            enable_ocr: 是否啟用OCR功能
            enable_screenshots: 是否啟用截圖功能
            storage_path: 數據存儲路徑
            max_workers: 最大並發工作線程數
            rate_limit_delay: 請求間隔延遲(秒)
        """
        self.scraping_mode = scraping_mode
        self.headless = headless
        self.enable_ocr = enable_ocr
        self.enable_screenshots = enable_screenshots
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        
        # 設置存儲路徑
        self.storage_path = Path(storage_path) if storage_path else Path("./seek_enhanced_data")
        self.storage_path.mkdir(exist_ok=True)
        
        # 初始化組件
        self.crawler_engine = None
        self.etl_processor = None
        self.traditional_scraper = None
        
        # 設置日誌
        self._setup_logging()
        
        # 性能統計
        self.performance_stats = {
            'session_start_time': time.time(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_jobs_found': 0,
            'total_jobs_processed': 0,
            'average_response_time': 0,
            'mode_usage': {
                'traditional': 0,
                'enhanced': 0,
                'hybrid': 0
            }
        }
    
    def _setup_logging(self):
        """設置日誌配置"""
        log_path = self.storage_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        log_file = log_path / f"seek_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize(self) -> bool:
        """
        初始化所有組件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info(f"初始化Seek增強型爬蟲 - 模式: {self.scraping_mode}")
            
            # 初始化ETL處理器
            self.etl_processor = SeekETLProcessor(
                output_path=str(self.storage_path / "processed_data"),
                enable_data_validation=True,
                enable_deduplication=True
            )
            
            # 根據模式初始化相應組件
            if self.scraping_mode in ["enhanced", "hybrid"]:
                self.crawler_engine = SeekCrawlerEngine(
                    headless=self.headless,
                    enable_ocr=self.enable_ocr,
                    storage_path=str(self.storage_path / "crawler_data")
                )
                
                if not await self.crawler_engine.initialize_browser():
                    self.logger.error("爬蟲引擎初始化失敗")
                    return False
            
            if self.scraping_mode in ["traditional", "hybrid"]:
                self.traditional_scraper = SeekJobScraper()
            
            self.logger.info("所有組件初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失敗: {e}")
            return False
    
    async def scrape_jobs(self,
                         search_term: str,
                         location: str = "",
                         job_type: str = "",
                         max_pages: int = 5,
                         results_wanted: int = 100) -> List[JobPost]:
        """
        執行職位搜索和數據抓取
        
        Args:
            search_term: 搜索關鍵詞
            location: 工作地點
            job_type: 工作類型
            max_pages: 最大抓取頁數
            results_wanted: 期望結果數量
            
        Returns:
            List[JobPost]: 抓取到的職位列表
        """
        start_time = time.time()
        all_jobs = []
        
        try:
            self.logger.info(f"開始搜索: {search_term} @ {location} (模式: {self.scraping_mode})")
            
            if self.scraping_mode == "traditional":
                all_jobs = await self._scrape_traditional(search_term, location, job_type, results_wanted)
                self.performance_stats['mode_usage']['traditional'] += 1
                
            elif self.scraping_mode == "enhanced":
                all_jobs = await self._scrape_enhanced(search_term, location, job_type, max_pages)
                self.performance_stats['mode_usage']['enhanced'] += 1
                
            elif self.scraping_mode == "hybrid":
                all_jobs = await self._scrape_hybrid(search_term, location, job_type, max_pages, results_wanted)
                self.performance_stats['mode_usage']['hybrid'] += 1
            
            # 更新統計信息
            self.performance_stats['total_jobs_found'] += len(all_jobs)
            self.performance_stats['successful_requests'] += 1
            self.performance_stats['average_response_time'] = time.time() - start_time
            
            self.logger.info(f"搜索完成: 找到 {len(all_jobs)} 個職位")
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"搜索失敗: {e}")
            self.performance_stats['failed_requests'] += 1
            return []
        
        finally:
            self.performance_stats['total_requests'] += 1
    
    async def _scrape_traditional(self,
                                search_term: str,
                                location: str,
                                job_type: str,
                                results_wanted: int) -> List[JobPost]:
        """
        使用傳統方法抓取數據
        
        Args:
            search_term: 搜索關鍵詞
            location: 工作地點
            job_type: 工作類型
            results_wanted: 期望結果數量
            
        Returns:
            List[JobPost]: 職位列表
        """
        try:
            self.logger.info("使用傳統爬蟲方法")
            
            # 使用現有的傳統爬蟲
            jobs = self.traditional_scraper.scrape(
                site_name="seek",
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed=Country.AUSTRALIA
            )
            
            return jobs if jobs else []
            
        except Exception as e:
            self.logger.error(f"傳統爬蟲失敗: {e}")
            return []
    
    async def _scrape_enhanced(self,
                             search_term: str,
                             location: str,
                             job_type: str,
                             max_pages: int) -> List[JobPost]:
        """
        使用增強型爬蟲引擎抓取數據
        
        Args:
            search_term: 搜索關鍵詞
            location: 工作地點
            job_type: 工作類型
            max_pages: 最大頁數
            
        Returns:
            List[JobPost]: 職位列表
        """
        try:
            self.logger.info("使用增強型爬蟲引擎")
            
            # 導航到搜索頁面
            if not await self.crawler_engine.navigate_to_search(search_term, location, job_type):
                return []
            
            # 抓取多頁數據
            raw_jobs = await self.crawler_engine.handle_pagination(max_pages)
            
            # ETL處理
            processed_jobs = self.etl_processor.process_raw_data(raw_jobs)
            
            self.performance_stats['total_jobs_processed'] += len(processed_jobs)
            return processed_jobs
            
        except Exception as e:
            self.logger.error(f"增強型爬蟲失敗: {e}")
            return []
    
    async def _scrape_hybrid(self,
                           search_term: str,
                           location: str,
                           job_type: str,
                           max_pages: int,
                           results_wanted: int) -> List[JobPost]:
        """
        使用混合模式抓取數據
        結合傳統方法和增強型引擎的優勢
        
        Args:
            search_term: 搜索關鍵詞
            location: 工作地點
            job_type: 工作類型
            max_pages: 最大頁數
            results_wanted: 期望結果數量
            
        Returns:
            List[JobPost]: 職位列表
        """
        try:
            self.logger.info("使用混合模式爬蟲")
            
            # 首先嘗試傳統方法（快速獲取基本數據）
            traditional_jobs = await self._scrape_traditional(search_term, location, job_type, results_wanted // 2)
            
            # 然後使用增強型引擎（獲取詳細數據和截圖）
            enhanced_jobs = await self._scrape_enhanced(search_term, location, job_type, min(max_pages, 3))
            
            # 合併結果並去重
            all_jobs = traditional_jobs + enhanced_jobs
            unique_jobs = self._deduplicate_jobs(all_jobs)
            
            self.logger.info(f"混合模式完成: 傳統 {len(traditional_jobs)}, 增強 {len(enhanced_jobs)}, 去重後 {len(unique_jobs)}")
            return unique_jobs
            
        except Exception as e:
            self.logger.error(f"混合模式爬蟲失敗: {e}")
            return []
    
    def _deduplicate_jobs(self, jobs: List[JobPost]) -> List[JobPost]:
        """
        去除重複的職位
        
        Args:
            jobs: 職位列表
            
        Returns:
            List[JobPost]: 去重後的職位列表
        """
        seen_urls = set()
        seen_title_company = set()
        unique_jobs = []
        
        for job in jobs:
            # URL去重
            if job.job_url and job.job_url in seen_urls:
                continue
            
            # 標題+公司去重
            title_company_key = f"{job.title.lower()}_{job.company.lower()}"
            if title_company_key in seen_title_company:
                continue
            
            # 記錄並添加
            if job.job_url:
                seen_urls.add(job.job_url)
            seen_title_company.add(title_company_key)
            unique_jobs.append(job)
        
        return unique_jobs
    
    async def export_results(self,
                           jobs: List[JobPost],
                           export_format: str = "json",
                           filename: str = None) -> str:
        """
        導出搜索結果
        
        Args:
            jobs: 職位列表
            export_format: 導出格式 ("json", "csv", "excel")
            filename: 文件名
            
        Returns:
            str: 導出文件路徑
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"seek_results_{timestamp}"
            
            if export_format.lower() == "json":
                return self.etl_processor.export_to_json(jobs, f"{filename}.json")
            
            # TODO: 實現CSV和Excel導出
            elif export_format.lower() == "csv":
                return self._export_to_csv(jobs, f"{filename}.csv")
            
            elif export_format.lower() == "excel":
                return self._export_to_excel(jobs, f"{filename}.xlsx")
            
            else:
                self.logger.error(f"不支持的導出格式: {export_format}")
                return ""
                
        except Exception as e:
            self.logger.error(f"導出失敗: {e}")
            return ""
    
    def _export_to_csv(self, jobs: List[JobPost], filename: str) -> str:
        """
        導出為CSV格式
        
        Args:
            jobs: 職位列表
            filename: 文件名
            
        Returns:
            str: 文件路徑
        """
        # TODO: 實現CSV導出邏輯
        self.logger.info("CSV導出功能待實現")
        return ""
    
    def _export_to_excel(self, jobs: List[JobPost], filename: str) -> str:
        """
        導出為Excel格式
        
        Args:
            jobs: 職位列表
            filename: 文件名
            
        Returns:
            str: 文件路徑
        """
        # TODO: 實現Excel導出邏輯
        self.logger.info("Excel導出功能待實現")
        return ""
    
    async def get_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        獲取單個職位的詳細信息
        
        Args:
            job_url: 職位URL
            
        Returns:
            Optional[Dict[str, Any]]: 詳細職位信息
        """
        try:
            if not self.crawler_engine:
                self.logger.error("爬蟲引擎未初始化")
                return None
            
            # 導航到職位詳情頁
            await self.crawler_engine.page.goto(job_url, wait_until='networkidle')
            
            # 截圖
            if self.enable_screenshots:
                screenshot_path = await self.crawler_engine.take_intelligent_screenshot("job_detail")
            
            # 提取頁面內容
            html_content, soup = await self.crawler_engine.extract_page_content()
            
            # OCR處理
            ocr_result = None
            if self.enable_ocr and screenshot_path:
                ocr_result = await self.crawler_engine.process_ocr_if_needed(screenshot_path)
            
            # 提取詳細信息
            job_details = self._extract_job_details(soup, ocr_result)
            
            return job_details
            
        except Exception as e:
            self.logger.error(f"獲取職位詳情失敗: {e}")
            return None
    
    def _extract_job_details(self, soup, ocr_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        從頁面中提取詳細職位信息
        
        Args:
            soup: BeautifulSoup對象
            ocr_result: OCR識別結果
            
        Returns:
            Dict[str, Any]: 詳細職位信息
        """
        details = {
            'full_description': '',
            'requirements': [],
            'benefits': [],
            'company_info': '',
            'contact_info': {},
            'ocr_text': ocr_result.get('text', '') if ocr_result else ''
        }
        
        try:
            # 提取完整描述
            desc_elem = soup.find('div', {'data-automation': 'jobAdDetails'})
            if desc_elem:
                details['full_description'] = desc_elem.get_text(strip=True)
            
            # 提取公司信息
            company_elem = soup.find('div', {'data-automation': 'companyProfile'})
            if company_elem:
                details['company_info'] = company_elem.get_text(strip=True)
            
            # TODO: 添加更多詳細信息提取邏輯
            
        except Exception as e:
            self.logger.error(f"詳細信息提取失敗: {e}")
        
        return details
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        獲取性能報告
        
        Returns:
            Dict[str, Any]: 性能統計報告
        """
        session_duration = time.time() - self.performance_stats['session_start_time']
        
        report = {
            **self.performance_stats,
            'session_duration_seconds': round(session_duration, 2),
            'success_rate': round(
                self.performance_stats['successful_requests'] / max(self.performance_stats['total_requests'], 1) * 100, 2
            ),
            'jobs_per_minute': round(
                self.performance_stats['total_jobs_found'] / max(session_duration / 60, 1), 2
            )
        }
        
        # 添加ETL處理器統計
        if self.etl_processor:
            report['etl_quality_report'] = self.etl_processor.get_quality_report()
        
        # 添加爬蟲引擎統計
        if self.crawler_engine:
            report['crawler_engine_stats'] = self.crawler_engine.get_stats()
        
        return report
    
    async def cleanup(self):
        """
        清理所有資源
        """
        try:
            if self.crawler_engine:
                await self.crawler_engine.cleanup()
            
            self.logger.info("資源清理完成")
            
        except Exception as e:
            self.logger.error(f"資源清理失敗: {e}")


# 使用示例和測試函數
async def main():
    """
    主函數示例
    """
    # 創建增強型爬蟲實例
    scraper = SeekScraperEnhanced(
        scraping_mode="hybrid",  # 使用混合模式
        headless=False,  # 顯示瀏覽器便於調試
        enable_ocr=True,
        enable_screenshots=True,
        storage_path="./seek_enhanced_output"
    )
    
    try:
        # 初始化
        if await scraper.initialize():
            print("爬蟲初始化成功")
            
            # 執行搜索
            jobs = await scraper.scrape_jobs(
                search_term="python developer",
                location="Sydney",
                max_pages=3,
                results_wanted=50
            )
            
            print(f"找到 {len(jobs)} 個職位")
            
            # 導出結果
            if jobs:
                output_file = await scraper.export_results(jobs, "json")
                print(f"結果已導出到: {output_file}")
            
            # 獲取性能報告
            performance_report = scraper.get_performance_report()
            print(f"性能報告: {performance_report}")
        
        else:
            print("爬蟲初始化失敗")
    
    finally:
        # 清理資源
        await scraper.cleanup()


if __name__ == "__main__":
    # 運行示例
    asyncio.run(main())