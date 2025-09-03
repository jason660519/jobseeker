#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台適配器
統一各平台的搜尋介面，提供一致的API

Author: jobseeker Team
Date: 2025-01-27
"""

import asyncio
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .simple_config import SimpleConfig, PlatformConfig
from .model import JobPost, JobResponse, ScraperInput, Site

# 設置日誌
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜尋結果"""
    platform: str
    success: bool
    job_count: int
    execution_time: float
    jobs: List[JobPost]
    error_message: Optional[str] = None


class PlatformAdapter:
    """平台適配器 - 統一各平台的搜尋介面"""
    
    def __init__(self, platform_name: str):
        """
        初始化平台適配器
        
        Args:
            platform_name: 平台名稱
        """
        self.platform_name = platform_name
        self.config = SimpleConfig.get_platform_config(platform_name)
        self.scraper = self._get_scraper(platform_name)
        
        if not self.config:
            raise ValueError(f"不支援的平台: {platform_name}")
    
    def search(self, query: str, location: str = None, max_results: int = 25) -> SearchResult:
        """
        統一的搜尋介面
        
        Args:
            query: 搜尋關鍵詞
            location: 地點
            max_results: 最大結果數量
            
        Returns:
            搜尋結果
        """
        start_time = time.time()
        
        try:
            logger.info(f"開始搜尋 {self.platform_name}: {query}")
            
            # 創建搜尋輸入
            scraper_input = ScraperInput(
                search_term=query,
                location=location,
                results_wanted=max_results,
                site=Site.from_string(self.platform_name)
            )
            
            # 執行搜尋
            job_response = self.scraper.scrape(scraper_input)
            
            execution_time = time.time() - start_time
            
            if job_response and job_response.jobs:
                logger.info(f"{self.platform_name} 搜尋成功: {len(job_response.jobs)} 個職位")
                return SearchResult(
                    platform=self.platform_name,
                    success=True,
                    job_count=len(job_response.jobs),
                    execution_time=execution_time,
                    jobs=job_response.jobs
                )
            else:
                logger.warning(f"{self.platform_name} 未找到職位")
                return SearchResult(
                    platform=self.platform_name,
                    success=False,
                    job_count=0,
                    execution_time=execution_time,
                    jobs=[],
                    error_message="未找到職位"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{self.platform_name} 搜尋失敗: {str(e)}"
            logger.error(error_msg)
            
            return SearchResult(
                platform=self.platform_name,
                success=False,
                job_count=0,
                execution_time=execution_time,
                jobs=[],
                error_message=error_msg
            )
    
    def _get_scraper(self, platform_name: str):
        """
        獲取對應的爬蟲
        
        Args:
            platform_name: 平台名稱
            
        Returns:
            爬蟲實例
        """
        try:
            # 使用爬蟲適配器工廠
            from .scraper_adapter import create_scraper_adapter
            return create_scraper_adapter(platform_name)
                
        except Exception as e:
            logger.error(f"無法創建 {platform_name} 爬蟲適配器: {e}")
            raise ValueError(f"平台 {platform_name} 的爬蟲適配器創建失敗")


class MultiPlatformAdapter:
    """多平台適配器 - 管理多個平台的並發搜尋"""
    
    def __init__(self, max_workers: int = 3):
        """
        初始化多平台適配器
        
        Args:
            max_workers: 最大並發工作線程數
        """
        self.max_workers = max_workers
        self.config = SimpleConfig()
    
    def search_multiple_platforms(
        self, 
        platforms: List[str], 
        query: str, 
        location: str = None, 
        max_results: int = 25
    ) -> List[SearchResult]:
        """
        並發搜尋多個平台
        
        Args:
            platforms: 平台名稱列表
            query: 搜尋關鍵詞
            location: 地點
            max_results: 最大結果數量
            
        Returns:
            搜尋結果列表
        """
        # 驗證平台
        valid_platforms = self.config.validate_platforms(platforms)
        if not valid_platforms:
            logger.warning("沒有有效的平台")
            return []
        
        logger.info(f"開始並發搜尋 {len(valid_platforms)} 個平台: {valid_platforms}")
        
        results = []
        
        # 使用線程池並發執行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任務
            future_to_platform = {
                executor.submit(
                    self._search_single_platform, 
                    platform, 
                    query, 
                    location, 
                    max_results
                ): platform 
                for platform in valid_platforms
            }
            
            # 收集結果
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"平台 {platform} 搜尋異常: {e}")
                    results.append(SearchResult(
                        platform=platform,
                        success=False,
                        job_count=0,
                        execution_time=0,
                        jobs=[],
                        error_message=str(e)
                    ))
        
        # 按成功率和執行時間排序
        results.sort(key=lambda x: (x.success, -x.execution_time), reverse=True)
        
        successful_count = sum(1 for r in results if r.success)
        total_jobs = sum(r.job_count for r in results)
        
        logger.info(f"搜尋完成: {successful_count}/{len(results)} 個平台成功，總共 {total_jobs} 個職位")
        
        return results
    
    def _search_single_platform(
        self, 
        platform_name: str, 
        query: str, 
        location: str, 
        max_results: int
    ) -> SearchResult:
        """
        搜尋單個平台
        
        Args:
            platform_name: 平台名稱
            query: 搜尋關鍵詞
            location: 地點
            max_results: 最大結果數量
            
        Returns:
            搜尋結果
        """
        try:
            adapter = PlatformAdapter(platform_name)
            return adapter.search(query, location, max_results)
        except Exception as e:
            logger.error(f"創建 {platform_name} 適配器失敗: {e}")
            return SearchResult(
                platform=platform_name,
                success=False,
                job_count=0,
                execution_time=0,
                jobs=[],
                error_message=str(e)
            )
    
    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有平台的狀態
        
        Returns:
            平台狀態字典
        """
        status = {}
        
        for platform_name in self.config.get_enabled_platforms():
            try:
                adapter = PlatformAdapter(platform_name)
                config = self.config.get_platform_config(platform_name)
                
                status[platform_name] = {
                    'enabled': True,
                    'priority': config.priority,
                    'timeout': config.timeout,
                    'retry_count': config.retry_count,
                    'scraper_available': adapter.scraper is not None
                }
            except Exception as e:
                status[platform_name] = {
                    'enabled': False,
                    'error': str(e),
                    'scraper_available': False
                }
        
        return status
