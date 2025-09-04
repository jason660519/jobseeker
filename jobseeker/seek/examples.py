#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek爬蟲引擎使用示例
展示各種使用場景和最佳實踐

Author: JobSpy Team
Date: 2024
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from .seek_scraper_enhanced import SeekScraperEnhanced
from .config import SeekCrawlerConfig, ConfigTemplates
from .models import JobPost


class SeekExamples:
    """
    Seek爬蟲引擎使用示例類
    """
    
    def __init__(self):
        self.scraper: SeekScraperEnhanced = None
        self.config: SeekCrawlerConfig = None
    
    async def example_basic_search(self):
        """
        示例1: 基本搜索功能
        演示最簡單的職位搜索
        """
        print("\n=== 示例1: 基本搜索 ===")
        
        # 創建基本配置
        config = ConfigTemplates.development()
        
        # 初始化爬蟲
        scraper = SeekScraperEnhanced(
            scraping_mode='traditional',
            headless=True,
            enable_ocr=False,
            storage_path=config.storage.base_path
        )
        
        try:
            # 初始化
            if await scraper.initialize():
                print("✅ 爬蟲初始化成功")
                
                # 搜索Python開發職位
                jobs = await scraper.scrape_jobs(
                    search_term="python developer",
                    location="Sydney",
                    max_pages=2,
                    results_wanted=20
                )
                
                print(f"🎯 找到 {len(jobs)} 個職位")
                
                # 顯示前3個職位
                for i, job in enumerate(jobs[:3], 1):
                    print(f"\n職位 {i}:")
                    print(f"  標題: {job.title}")
                    print(f"  公司: {job.company}")
                    print(f"  地點: {job.location}")
                    print(f"  薪資: {job.salary or '未提供'}")
                
                # 導出結果
                output_file = await scraper.export_results(jobs, 'json', 'basic_search_results.json')
                print(f"\n💾 結果已保存到: {output_file}")
            
        finally:
            await scraper.cleanup()
    
    async def example_enhanced_search_with_ocr(self):
        """
        示例2: 增強搜索與OCR功能
        演示使用OCR處理圖片內容
        """
        print("\n=== 示例2: 增強搜索與OCR ===")
        
        # 創建生產環境配置
        config = ConfigTemplates.production()
        config.ocr.enabled = True
        config.scraping.enable_screenshots = True
        
        scraper = SeekScraperEnhanced(
            scraping_mode='enhanced',
            headless=True,
            enable_ocr=True,
            enable_screenshots=True,
            storage_path=config.storage.base_path
        )
        
        try:
            if await scraper.initialize():
                print("✅ 增強爬蟲初始化成功")
                
                # 搜索數據科學職位
                jobs = await scraper.scrape_jobs(
                    search_term="data scientist",
                    location="Melbourne",
                    job_type="full-time",
                    max_pages=3,
                    results_wanted=30
                )
                
                print(f"🎯 找到 {len(jobs)} 個職位")
                
                # 分析薪資分布
                salary_jobs = [job for job in jobs if job.salary]
                print(f"💰 有薪資信息的職位: {len(salary_jobs)} 個")
                
                # 導出多種格式
                json_file = await scraper.export_results(jobs, 'json', 'enhanced_search_results.json')
                csv_file = await scraper.export_results(jobs, 'csv', 'enhanced_search_results.csv')
                
                print(f"\n💾 結果已保存:")
                print(f"  JSON: {json_file}")
                print(f"  CSV: {csv_file}")
                
                # 顯示性能報告
                performance = scraper.get_performance_report()
                print(f"\n📊 性能報告:")
                print(f"  成功率: {performance.get('success_rate', 0)}%")
                print(f"  平均響應時間: {performance.get('average_response_time', 0):.2f}秒")
        
        finally:
            await scraper.cleanup()
    
    async def example_hybrid_mode_batch_search(self):
        """
        示例3: 混合模式批量搜索
        演示批量搜索多個關鍵詞
        """
        print("\n=== 示例3: 混合模式批量搜索 ===")
        
        # 搜索關鍵詞列表
        search_terms = [
            "software engineer",
            "frontend developer",
            "backend developer",
            "devops engineer",
            "product manager"
        ]
        
        locations = ["Sydney", "Melbourne", "Brisbane"]
        
        config = ConfigTemplates.production()
        scraper = SeekScraperEnhanced(
            scraping_mode='hybrid',
            headless=True,
            enable_ocr=False,
            storage_path=config.storage.base_path,
            max_workers=5
        )
        
        all_jobs = []
        
        try:
            if await scraper.initialize():
                print("✅ 混合模式爬蟲初始化成功")
                
                # 批量搜索
                for term in search_terms:
                    for location in locations:
                        print(f"\n🔍 搜索: {term} @ {location}")
                        
                        jobs = await scraper.scrape_jobs(
                            search_term=term,
                            location=location,
                            max_pages=2,
                            results_wanted=15
                        )
                        
                        print(f"  找到 {len(jobs)} 個職位")
                        all_jobs.extend(jobs)
                        
                        # 添加搜索標籤
                        for job in jobs:
                            job.search_term = term
                            job.search_location = location
                
                print(f"\n🎯 總計找到 {len(all_jobs)} 個職位")
                
                # 去重處理
                unique_jobs = self._deduplicate_jobs(all_jobs)
                print(f"🔄 去重後: {len(unique_jobs)} 個唯一職位")
                
                # 按職位類型分組統計
                job_stats = self._analyze_job_distribution(unique_jobs)
                print(f"\n📊 職位分布統計:")
                for term, count in job_stats.items():
                    print(f"  {term}: {count} 個")
                
                # 導出結果
                output_file = await scraper.export_results(
                    unique_jobs, 'json', 'batch_search_results.json'
                )
                print(f"\n💾 批量搜索結果已保存到: {output_file}")
        
        finally:
            await scraper.cleanup()
    
    async def example_custom_configuration(self):
        """
        示例4: 自定義配置
        演示如何創建和使用自定義配置
        """
        print("\n=== 示例4: 自定義配置 ===")
        
        # 創建自定義配置
        config = SeekCrawlerConfig()
        
        # 自定義瀏覽器設置
        config.browser.headless = False  # 顯示瀏覽器
        config.browser.window_size = (1920, 1080)
        config.browser.user_agent = "Custom Seek Scraper 1.0"
        
        # 自定義爬蟲設置
        config.scraping.mode = 'enhanced'
        config.scraping.max_pages = 5
        config.scraping.results_wanted = 50
        config.scraping.enable_screenshots = True
        config.scraping.rate_limit_delay = 3.0
        
        # 自定義OCR設置
        config.ocr.enabled = True
        config.ocr.language = 'eng+chi_sim'  # 英文+簡體中文
        config.ocr.confidence_threshold = 0.8
        
        # 自定義存儲設置
        config.storage.base_path = "./custom_seek_data"
        config.storage.keep_raw_data = True
        config.storage.compress_data = True
        
        # 自定義性能設置
        config.performance.max_concurrent_requests = 2
        config.performance.max_memory_usage_mb = 2048
        config.performance.enable_caching = True
        
        # 保存配置
        config.save_to_file("custom_config.json")
        print("💾 自定義配置已保存到: custom_config.json")
        
        # 使用自定義配置創建爬蟲
        scraper = SeekScraperEnhanced(
            scraping_mode=config.scraping.mode,
            headless=config.browser.headless,
            enable_ocr=config.ocr.enabled,
            enable_screenshots=config.scraping.enable_screenshots,
            storage_path=config.storage.base_path,
            rate_limit_delay=config.scraping.rate_limit_delay
        )
        
        try:
            if await scraper.initialize():
                print("✅ 自定義配置爬蟲初始化成功")
                
                # 執行搜索
                jobs = await scraper.scrape_jobs(
                    search_term="machine learning engineer",
                    location="Sydney",
                    max_pages=config.scraping.max_pages,
                    results_wanted=config.scraping.results_wanted
                )
                
                print(f"🎯 找到 {len(jobs)} 個職位")
                
                # 顯示配置效果
                print(f"\n⚙️ 配置效果:")
                print(f"  瀏覽器可見: {'是' if not config.browser.headless else '否'}")
                print(f"  OCR語言: {config.ocr.language}")
                print(f"  存儲路徑: {config.storage.base_path}")
                print(f"  並發請求: {config.performance.max_concurrent_requests}")
        
        finally:
            await scraper.cleanup()
    
    async def example_error_handling_and_retry(self):
        """
        示例5: 錯誤處理與重試機制
        演示如何處理網絡錯誤和實現重試
        """
        print("\n=== 示例5: 錯誤處理與重試 ===")
        
        config = ConfigTemplates.testing()
        config.scraping.max_retries = 3
        config.scraping.retry_delay = 5.0
        
        scraper = SeekScraperEnhanced(
            scraping_mode='traditional',
            headless=True,
            storage_path=config.storage.base_path
        )
        
        try:
            if await scraper.initialize():
                print("✅ 錯誤處理示例爬蟲初始化成功")
                
                # 模擬可能失敗的搜索
                search_terms = [
                    "valid search term",
                    "",  # 空搜索詞，可能導致錯誤
                    "very specific rare job title that might not exist"
                ]
                
                successful_searches = 0
                failed_searches = 0
                
                for term in search_terms:
                    try:
                        print(f"\n🔍 嘗試搜索: '{term}'")
                        
                        if not term.strip():
                            print("⚠️ 跳過空搜索詞")
                            continue
                        
                        jobs = await scraper.scrape_jobs(
                            search_term=term,
                            location="Sydney",
                            max_pages=1,
                            results_wanted=10
                        )
                        
                        print(f"✅ 成功: 找到 {len(jobs)} 個職位")
                        successful_searches += 1
                        
                    except Exception as e:
                        print(f"❌ 搜索失敗: {e}")
                        failed_searches += 1
                        
                        # 記錄錯誤但繼續執行
                        continue
                
                print(f"\n📊 搜索結果統計:")
                print(f"  成功: {successful_searches}")
                print(f"  失敗: {failed_searches}")
                print(f"  成功率: {successful_searches/(successful_searches+failed_searches)*100:.1f}%")
        
        finally:
            await scraper.cleanup()
    
    def _deduplicate_jobs(self, jobs: List[JobPost]) -> List[JobPost]:
        """
        去除重複職位
        
        Args:
            jobs: 職位列表
            
        Returns:
            List[JobPost]: 去重後的職位列表
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # 使用標題+公司+地點作為唯一標識
            job_key = f"{job.title}|{job.company}|{job.location}"
            if job_key not in seen:
                seen.add(job_key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _analyze_job_distribution(self, jobs: List[JobPost]) -> Dict[str, int]:
        """
        分析職位分布
        
        Args:
            jobs: 職位列表
            
        Returns:
            Dict[str, int]: 職位類型分布統計
        """
        distribution = {}
        
        for job in jobs:
            search_term = getattr(job, 'search_term', 'unknown')
            distribution[search_term] = distribution.get(search_term, 0) + 1
        
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    async def run_all_examples(self):
        """
        運行所有示例
        """
        print("🚀 開始運行Seek爬蟲引擎示例")
        print("=" * 50)
        
        examples = [
            self.example_basic_search,
            self.example_enhanced_search_with_ocr,
            self.example_hybrid_mode_batch_search,
            self.example_custom_configuration,
            self.example_error_handling_and_retry
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                print(f"\n\n🔄 運行示例 {i}/{len(examples)}")
                await example()
                print(f"✅ 示例 {i} 完成")
            except Exception as e:
                print(f"❌ 示例 {i} 失敗: {e}")
                continue
        
        print("\n\n🎉 所有示例運行完成！")


async def main():
    """
    主函數
    """
    examples = SeekExamples()
    
    # 可以選擇運行單個示例或所有示例
    choice = input("\n選擇運行模式:\n1. 運行所有示例\n2. 基本搜索示例\n3. 增強搜索示例\n4. 批量搜索示例\n5. 自定義配置示例\n6. 錯誤處理示例\n請輸入選項 (1-6): ")
    
    try:
        if choice == '1':
            await examples.run_all_examples()
        elif choice == '2':
            await examples.example_basic_search()
        elif choice == '3':
            await examples.example_enhanced_search_with_ocr()
        elif choice == '4':
            await examples.example_hybrid_mode_batch_search()
        elif choice == '5':
            await examples.example_custom_configuration()
        elif choice == '6':
            await examples.example_error_handling_and_retry()
        else:
            print("❌ 無效選項")
            return
    
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷操作")
    except Exception as e:
        print(f"❌ 運行失敗: {e}")


if __name__ == '__main__':
    asyncio.run(main())