#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬蟲適配器
將現有的爬蟲適配到新的統一介面

Author: jobseeker Team
Date: 2025-01-27
"""

from typing import List, Optional
from .model import ScraperInput, JobResponse, Site, Country


class ScraperAdapter:
    """爬蟲適配器基類"""
    
    def __init__(self, scraper_instance):
        """
        初始化適配器
        
        Args:
            scraper_instance: 現有的爬蟲實例
        """
        self.scraper = scraper_instance
    
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        統一的搜尋介面
        
        Args:
            scraper_input: 搜尋輸入
            
        Returns:
            搜尋結果
        """
        return self.scraper.scrape(scraper_input)


class IndeedScraperAdapter(ScraperAdapter):
    """Indeed爬蟲適配器"""
    
    def __init__(self):
        from .indeed import Indeed
        super().__init__(Indeed())


class LinkedInScraperAdapter(ScraperAdapter):
    """LinkedIn爬蟲適配器"""
    
    def __init__(self):
        from .linkedin import LinkedIn
        super().__init__(LinkedIn())


class SeekScraperAdapter(ScraperAdapter):
    """Seek爬蟲適配器"""
    
    def __init__(self):
        from .seek import Seek
        super().__init__(Seek())


class TW104ScraperAdapter(ScraperAdapter):
    """104人力銀行爬蟲適配器"""
    
    def __init__(self):
        from .tw104.enhanced_tw104 import EnhancedTW104Scraper
        super().__init__(EnhancedTW104Scraper())
    
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        適配104爬蟲的搜尋介面
        
        Args:
            scraper_input: 搜尋輸入
            
        Returns:
            搜尋結果
        """
        # 104爬蟲使用不同的介面，需要適配
        try:
            # 使用異步搜尋
            import asyncio
            
            async def async_search():
                jobs = await self.scraper.search_jobs(
                    keyword=scraper_input.search_term,
                    location=scraper_input.location,
                    max_pages=3
                )
                return jobs
            
            # 運行異步搜尋
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                jobs_data = loop.run_until_complete(async_search())
            finally:
                loop.close()
            
            # 轉換為JobPost格式
            from .model import JobPost, Location
            job_posts = []
            
            for job_data in jobs_data:
                job_post = JobPost(
                    id=f"104-{job_data.get('id', '')}",
                    title=job_data.get('title', ''),
                    description=job_data.get('description', ''),
                    company_name=job_data.get('company', ''),
                    location=Location(
                        city=job_data.get('location', ''),
                        state=None,
                        country='TW'
                    ),
                    job_url=job_data.get('url', ''),
                    date_posted=job_data.get('date_posted', ''),
                    job_type=None,
                    compensation=None,
                    is_remote=False
                )
                job_posts.append(job_post)
            
            return JobResponse(jobs=job_posts)
            
        except Exception as e:
            print(f"104爬蟲適配失敗: {e}")
            return JobResponse(jobs=[])


class TW1111ScraperAdapter(ScraperAdapter):
    """1111人力銀行爬蟲適配器"""
    
    def __init__(self):
        from .tw1111 import Taiwan1111Scraper
        super().__init__(Taiwan1111Scraper())


class GoogleScraperAdapter(ScraperAdapter):
    """Google爬蟲適配器"""
    
    def __init__(self):
        from .google.enhanced_google import EnhancedGoogleScraper
        super().__init__(EnhancedGoogleScraper())


class ZipRecruiterScraperAdapter(ScraperAdapter):
    """ZipRecruiter爬蟲適配器"""
    
    def __init__(self):
        from .ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiterScraper
        super().__init__(EnhancedZipRecruiterScraper())


class GlassdoorScraperAdapter(ScraperAdapter):
    """Glassdoor爬蟲適配器"""
    
    def __init__(self):
        from .glassdoor import Glassdoor
        super().__init__(Glassdoor())


class NaukriScraperAdapter(ScraperAdapter):
    """Naukri爬蟲適配器"""
    
    def __init__(self):
        from .naukri import Naukri
        super().__init__(Naukri())


class BaytScraperAdapter(ScraperAdapter):
    """Bayt爬蟲適配器"""
    
    def __init__(self):
        from .bayt.enhanced_bayt import EnhancedBaytScraper
        super().__init__(EnhancedBaytScraper())


class BDJobsScraperAdapter(ScraperAdapter):
    """BDJobs爬蟲適配器"""
    
    def __init__(self):
        from .bdjobs import BDJobs
        super().__init__(BDJobs())


# 爬蟲適配器工廠
def create_scraper_adapter(platform_name: str) -> ScraperAdapter:
    """
    創建爬蟲適配器
    
    Args:
        platform_name: 平台名稱
        
    Returns:
        爬蟲適配器實例
    """
    adapters = {
        'indeed': IndeedScraperAdapter,
        'linkedin': LinkedInScraperAdapter,
        'seek': SeekScraperAdapter,
        '104': TW104ScraperAdapter,
        '1111': TW1111ScraperAdapter,
        'google': GoogleScraperAdapter,
        'ziprecruiter': ZipRecruiterScraperAdapter,
        'glassdoor': GlassdoorScraperAdapter,
        'naukri': NaukriScraperAdapter,
        'bayt': BaytScraperAdapter,
        'bdjobs': BDJobsScraperAdapter
    }
    
    adapter_class = adapters.get(platform_name)
    if not adapter_class:
        raise ValueError(f"不支援的平台: {platform_name}")
    
    return adapter_class()
