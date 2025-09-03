#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能職位搜尋路由器
一站式解決方案，簡化複雜的路由邏輯

Author: jobseeker Team
Date: 2025-01-27
"""

import time
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass

from .simple_config import SimpleConfig
from .platform_adapter import MultiPlatformAdapter, SearchResult
from .model import JobPost

# 設置日誌
logger = logging.getLogger(__name__)


@dataclass
class SmartSearchResult:
    """智能搜尋結果"""
    total_jobs: int
    successful_platforms: List[str]
    failed_platforms: List[str]
    total_execution_time: float
    jobs: List[JobPost]
    search_metadata: Dict[str, Any]
    platform_results: List[SearchResult]


class SmartJobRouter:
    """智能職位搜尋路由器 - 一站式解決方案"""
    
    def __init__(self, max_workers: int = 3):
        """
        初始化智能路由器
        
        Args:
            max_workers: 最大並發工作線程數
        """
        self.config = SimpleConfig()
        self.multi_adapter = MultiPlatformAdapter(max_workers)
        self.search_history = []
    
    def search_jobs(
        self, 
        query: str, 
        location: str = None, 
        max_results: int = 25,
        platforms: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> SmartSearchResult:
        """
        一站式搜尋職位
        
        Args:
            query: 搜尋關鍵詞
            location: 地點
            max_results: 最大結果數量
            platforms: 指定平台列表（可選）
            region: 指定地區（可選）
            
        Returns:
            智能搜尋結果
        """
        start_time = time.time()
        
        logger.info(f"開始智能搜尋: '{query}' 在 '{location or '全球'}'")
        
        # 1. 智能選擇平台
        selected_platforms = self._select_platforms(query, location, platforms, region)
        logger.info(f"選擇的平台: {selected_platforms}")
        
        # 2. 並發搜尋
        platform_results = self.multi_adapter.search_multiple_platforms(
            selected_platforms, query, location, max_results
        )
        
        # 3. 聚合結果
        result = self._aggregate_results(platform_results, query, location, start_time)
        
        # 4. 記錄搜尋歷史
        self._record_search_history(result)
        
        logger.info(f"搜尋完成: {result.total_jobs} 個職位，{len(result.successful_platforms)} 個平台成功")
        
        return result
    
    def _select_platforms(
        self, 
        query: str, 
        location: str = None, 
        platforms: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> List[str]:
        """
        智能選擇搜尋平台
        
        Args:
            query: 搜尋關鍵詞
            location: 地點
            platforms: 指定平台列表
            region: 指定地區
            
        Returns:
            選擇的平台列表
        """
        # 如果指定了平台，直接使用
        if platforms:
            valid_platforms = self.config.validate_platforms(platforms)
            if valid_platforms:
                return self.config.sort_platforms_by_priority(valid_platforms)
            else:
                logger.warning("指定的平台無效，使用智能選擇")
        
        # 如果指定了地區，使用地區對應的平台
        if region:
            region_platforms = self.config.get_platforms_for_region(region)
            if region_platforms:
                return self.config.sort_platforms_by_priority(region_platforms)
        
        # 智能檢測地區
        text = f"{query} {location or ''}"
        detected_region = self.config.detect_region(text)
        
        if detected_region:
            logger.info(f"檢測到地區: {detected_region}")
            region_platforms = self.config.get_platforms_for_region(detected_region)
            return self.config.sort_platforms_by_priority(region_platforms)
        
        # 默認使用全球平台
        logger.info("使用默認全球平台")
        return self.config.sort_platforms_by_priority(self.config.DEFAULT_PLATFORMS)
    
    def _aggregate_results(
        self, 
        platform_results: List[SearchResult], 
        query: str, 
        location: str, 
        start_time: float
    ) -> SmartSearchResult:
        """
        聚合搜尋結果
        
        Args:
            platform_results: 平台搜尋結果列表
            query: 搜尋關鍵詞
            location: 地點
            start_time: 開始時間
            
        Returns:
            聚合後的搜尋結果
        """
        total_execution_time = time.time() - start_time
        
        # 分類成功和失敗的平台
        successful_platforms = [r.platform for r in platform_results if r.success]
        failed_platforms = [r.platform for r in platform_results if not r.success]
        
        # 聚合所有職位
        all_jobs = []
        for result in platform_results:
            if result.success and result.jobs:
                all_jobs.extend(result.jobs)
        
        # 去重（基於職位URL）
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        # 創建搜尋元數據
        search_metadata = {
            'query': query,
            'location': location,
            'total_platforms': len(platform_results),
            'successful_platforms_count': len(successful_platforms),
            'failed_platforms_count': len(failed_platforms),
            'execution_time': total_execution_time,
            'timestamp': time.time()
        }
        
        return SmartSearchResult(
            total_jobs=len(unique_jobs),
            successful_platforms=successful_platforms,
            failed_platforms=failed_platforms,
            total_execution_time=total_execution_time,
            jobs=unique_jobs,
            search_metadata=search_metadata,
            platform_results=platform_results
        )
    
    def _deduplicate_jobs(self, jobs: List[JobPost]) -> List[JobPost]:
        """
        去重職位（基於URL）
        
        Args:
            jobs: 職位列表
            
        Returns:
            去重後的職位列表
        """
        seen_urls = set()
        unique_jobs = []
        
        for job in jobs:
            if job.job_url and job.job_url not in seen_urls:
                seen_urls.add(job.job_url)
                unique_jobs.append(job)
            elif not job.job_url:
                # 如果沒有URL，基於標題和公司去重
                key = f"{job.title}_{job.company}"
                if key not in seen_urls:
                    seen_urls.add(key)
                    unique_jobs.append(job)
        
        return unique_jobs
    
    def _record_search_history(self, result: SmartSearchResult):
        """
        記錄搜尋歷史
        
        Args:
            result: 搜尋結果
        """
        history_entry = {
            'timestamp': result.search_metadata['timestamp'],
            'query': result.search_metadata['query'],
            'location': result.search_metadata['location'],
            'total_jobs': result.total_jobs,
            'successful_platforms': result.successful_platforms,
            'execution_time': result.total_execution_time
        }
        
        self.search_history.append(history_entry)
        
        # 只保留最近100次搜尋記錄
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        獲取搜尋統計信息
        
        Returns:
            統計信息字典
        """
        if not self.search_history:
            return {'message': '暫無搜尋歷史'}
        
        total_searches = len(self.search_history)
        total_jobs_found = sum(h['total_jobs'] for h in self.search_history)
        avg_execution_time = sum(h['execution_time'] for h in self.search_history) / total_searches
        
        # 平台成功率統計
        platform_success_count = {}
        for history in self.search_history:
            for platform in history['successful_platforms']:
                platform_success_count[platform] = platform_success_count.get(platform, 0) + 1
        
        platform_success_rate = {
            platform: count / total_searches 
            for platform, count in platform_success_count.items()
        }
        
        return {
            'total_searches': total_searches,
            'total_jobs_found': total_jobs_found,
            'average_execution_time': avg_execution_time,
            'platform_success_rate': platform_success_rate,
            'recent_searches': self.search_history[-5:]  # 最近5次搜尋
        }
    
    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有平台的狀態
        
        Returns:
            平台狀態字典
        """
        return self.multi_adapter.get_platform_status()
    
    def search_with_fallback(
        self, 
        query: str, 
        location: str = None, 
        max_results: int = 25,
        primary_platforms: Optional[List[str]] = None
    ) -> SmartSearchResult:
        """
        帶後備機制的搜尋
        
        Args:
            query: 搜尋關鍵詞
            location: 地點
            max_results: 最大結果數量
            primary_platforms: 主要平台列表
            
        Returns:
            搜尋結果
        """
        # 首先嘗試主要平台
        result = self.search_jobs(query, location, max_results, primary_platforms)
        
        # 如果主要平台沒有找到足夠的結果，使用後備平台
        if result.total_jobs < max_results // 2:  # 如果結果少於期望的一半
            logger.info("主要平台結果不足，嘗試後備平台")
            
            # 排除已使用的平台
            used_platforms = set(result.successful_platforms + result.failed_platforms)
            available_platforms = [
                p for p in self.config.get_enabled_platforms() 
                if p not in used_platforms
            ]
            
            if available_platforms:
                fallback_result = self.search_jobs(
                    query, location, max_results - result.total_jobs, available_platforms
                )
                
                # 合併結果
                result.jobs.extend(fallback_result.jobs)
                result.total_jobs = len(result.jobs)
                result.successful_platforms.extend(fallback_result.successful_platforms)
                result.failed_platforms.extend(fallback_result.failed_platforms)
                result.total_execution_time += fallback_result.total_execution_time
                result.platform_results.extend(fallback_result.platform_results)
        
        return result


# 全局路由器實例
smart_router = SmartJobRouter()
