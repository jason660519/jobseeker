#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強型ETL編排器
整合視覺爬蟲、傳統爬蟲和ETL處理的統一調度系統

Author: JobSpy Team
Date: 2025-01-05
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

# 導入現有組件
from .etl_processor import SeekETLProcessor
from .seek_scraper_enhanced import SeekScraperEnhanced
from ..model import JobPost, JobType, Country
from ..enhanced_logging import get_enhanced_logger, LogCategory
from ..enhanced_error_handler import EnhancedErrorHandler, RecoveryAction

# 導入視覺爬蟲（需要調整路徑）
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent / "tests"))
    from comprehensive_seek_test import ComprehensiveSeekTest
except ImportError:
    ComprehensiveSeekTest = None
    logging.warning("視覺爬蟲模組未找到，將禁用視覺爬蟲功能")


class ScrapingStrategy(Enum):
    """爬蟲策略枚舉"""
    VISUAL_PRIMARY = "visual_primary"      # 視覺爬蟲為主
    TRADITIONAL_PRIMARY = "traditional_primary"  # 傳統爬蟲為主
    HYBRID = "hybrid"                      # 混合模式
    VISUAL_ONLY = "visual_only"            # 僅視覺爬蟲
    TRADITIONAL_ONLY = "traditional_only"  # 僅傳統爬蟲


@dataclass
class ScrapingJobConfig:
    """爬蟲任務配置"""
    search_term: str
    location: str = "Australia"
    job_type: str = "all"
    max_results: int = 50
    max_pages: int = 5
    
    # 策略配置
    strategy: ScrapingStrategy = ScrapingStrategy.HYBRID
    high_quality_required: bool = False
    large_volume_required: bool = False
    
    # 性能配置
    timeout: int = 300
    retry_attempts: int = 3
    enable_cross_validation: bool = True
    
    # 輸出配置
    output_formats: List[str] = None
    include_metadata: bool = True
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['json']


class ScrapingStrategySelector:
    """
    增強型爬蟲策略選擇器
    根據任務需求、網站狀態和動態性能智能選擇最佳策略
    """
    
    def __init__(self):
        self.logger = get_enhanced_logger(self.__class__.__name__)
        # 使用滑動窗口統計近期性能
        self.performance_window_size = 20
        self.strategy_performance = {
            ScrapingStrategy.VISUAL_PRIMARY: {
                'success_rate': 0.85, 'avg_time': 45, 'recent_results': [],
                'quality_score': 0.9, 'stability_score': 0.8
            },
            ScrapingStrategy.TRADITIONAL_PRIMARY: {
                'success_rate': 0.75, 'avg_time': 15, 'recent_results': [],
                'quality_score': 0.7, 'stability_score': 0.9
            },
            ScrapingStrategy.HYBRID: {
                'success_rate': 0.90, 'avg_time': 30, 'recent_results': [],
                'quality_score': 0.85, 'stability_score': 0.85
            }
        }
        # 網站狀態監控
        self.website_health = {
            'response_time': 1.0,
            'anti_bot_level': 0.3,
            'last_check': time.time()
        }
    
    def select_strategy(self, job_config: ScrapingJobConfig) -> ScrapingStrategy:
        """
        智能選擇最佳爬蟲策略
        
        Args:
            job_config: 任務配置
            
        Returns:
            ScrapingStrategy: 選定的策略
        """
        # 如果用戶指定了策略，直接使用
        if job_config.strategy != ScrapingStrategy.HYBRID:
            return job_config.strategy
        
        # 更新網站健康狀態
        self._update_website_health()
        
        # 計算各策略的綜合評分
        strategy_scores = self._calculate_strategy_scores(job_config)
        
        # 選擇評分最高的策略
        best_strategy = max(strategy_scores.keys(), key=lambda s: strategy_scores[s])
        
        self.logger.info(f"策略評分: {strategy_scores}")
        self.logger.info(f"選擇策略: {best_strategy} (評分: {strategy_scores[best_strategy]:.3f})")
        
        return best_strategy
    
    def _calculate_strategy_scores(self, job_config: ScrapingJobConfig) -> Dict[ScrapingStrategy, float]:
        """
        計算各策略的綜合評分
        
        Args:
            job_config: 任務配置
            
        Returns:
            Dict: 策略評分字典
        """
        scores = {}
        
        for strategy in [ScrapingStrategy.VISUAL_PRIMARY, 
                        ScrapingStrategy.TRADITIONAL_PRIMARY, 
                        ScrapingStrategy.HYBRID]:
            
            perf = self.strategy_performance[strategy]
            
            # 基礎性能評分 (40%)
            recent_success_rate = self._get_recent_success_rate(strategy)
            performance_score = recent_success_rate * 0.4
            
            # 質量評分 (30%)
            quality_weight = 0.5 if job_config.high_quality_required else 0.3
            quality_score = perf['quality_score'] * quality_weight
            
            # 速度評分 (20%)
            speed_weight = 0.3 if job_config.large_volume_required else 0.2
            # 時間越短評分越高
            speed_score = (1.0 / (perf['avg_time'] / 10)) * speed_weight
            
            # 穩定性評分 (10%)
            stability_score = perf['stability_score'] * 0.1
            
            # 網站狀態適應性評分
            adaptability_score = self._get_adaptability_score(strategy)
            
            # 綜合評分
            total_score = performance_score + quality_score + speed_score + stability_score + adaptability_score
            scores[strategy] = total_score
            
        return scores
    
    def _get_recent_success_rate(self, strategy: ScrapingStrategy) -> float:
        """
        獲取策略的近期成功率
        
        Args:
            strategy: 策略類型
            
        Returns:
            float: 近期成功率
        """
        recent_results = self.strategy_performance[strategy]['recent_results']
        
        if not recent_results:
            return self.strategy_performance[strategy]['success_rate']
        
        # 計算滑動窗口內的成功率
        recent_successes = sum(1 for result in recent_results if result['success'])
        return recent_successes / len(recent_results)
    
    def _get_adaptability_score(self, strategy: ScrapingStrategy) -> float:
        """
        根據網站狀態計算策略適應性評分
        
        Args:
            strategy: 策略類型
            
        Returns:
            float: 適應性評分
        """
        response_time = self.website_health['response_time']
        anti_bot_level = self.website_health['anti_bot_level']
        
        if strategy == ScrapingStrategy.VISUAL_PRIMARY:
            # 視覺爬蟲在反爬蟲強度高時表現更好
            return (anti_bot_level * 0.1) + (max(0, 2.0 - response_time) * 0.05)
        elif strategy == ScrapingStrategy.TRADITIONAL_PRIMARY:
            # 傳統爬蟲在響應快、反爬蟲弱時表現更好
            return (max(0, 1.0 - anti_bot_level) * 0.1) + (max(0, 2.0 - response_time) * 0.1)
        else:  # HYBRID
            # 混合模式適應性較為均衡
            return 0.08
    
    def _update_website_health(self):
        """
        更新網站健康狀態
        """
        current_time = time.time()
        
        # 每5分鐘更新一次
        if current_time - self.website_health['last_check'] > 300:
            # 這裡可以添加實際的網站健康檢查邏輯
            # 目前使用模擬數據
            import random
            self.website_health.update({
                'response_time': random.uniform(0.5, 3.0),
                'anti_bot_level': random.uniform(0.1, 0.8),
                'last_check': current_time
            })
            
            self.logger.debug(f"網站健康狀態更新: {self.website_health}")
    
    def update_strategy_performance(self, strategy: ScrapingStrategy, 
                                  success: bool, execution_time: float, 
                                  data_quality: float = 0.8, job_count: int = 0):
        """
        更新策略性能統計（支持滑動窗口）
        
        Args:
            strategy: 策略類型
            success: 是否成功
            execution_time: 執行時間
            data_quality: 數據質量評分 (0-1)
            job_count: 獲取的職位數量
        """
        if strategy not in self.strategy_performance:
            return
            
        perf = self.strategy_performance[strategy]
        
        # 添加到近期結果
        result_record = {
            'success': success,
            'execution_time': execution_time,
            'data_quality': data_quality,
            'job_count': job_count,
            'timestamp': time.time()
        }
        
        perf['recent_results'].append(result_record)
        
        # 維護滑動窗口大小
        if len(perf['recent_results']) > self.performance_window_size:
            perf['recent_results'].pop(0)
        
        # 更新平均指標
        self._update_average_metrics(strategy)
        
        self.logger.debug(f"策略 {strategy} 性能已更新: 成功={success}, 時間={execution_time:.2f}s, 質量={data_quality:.2f}")
    
    def _update_average_metrics(self, strategy: ScrapingStrategy):
        """
        更新策略的平均性能指標
        
        Args:
            strategy: 策略類型
        """
        perf = self.strategy_performance[strategy]
        recent_results = perf['recent_results']
        
        if not recent_results:
            return
        
        # 計算近期平均值
        successful_results = [r for r in recent_results if r['success']]
        
        if successful_results:
            perf['avg_time'] = sum(r['execution_time'] for r in successful_results) / len(successful_results)
            perf['quality_score'] = sum(r['data_quality'] for r in successful_results) / len(successful_results)
        
        # 計算穩定性評分（基於成功率的一致性）
        success_rates_by_time = []
        window_size = 5
        for i in range(0, len(recent_results), window_size):
            window = recent_results[i:i+window_size]
            if window:
                window_success_rate = sum(1 for r in window if r['success']) / len(window)
                success_rates_by_time.append(window_success_rate)
        
        if len(success_rates_by_time) > 1:
            # 穩定性 = 1 - 成功率的標準差
            import statistics
            std_dev = statistics.stdev(success_rates_by_time)
            perf['stability_score'] = max(0, 1.0 - std_dev)
        
        self.logger.debug(f"策略 {strategy} 平均指標已更新")


class MultiSourceDataCollector:
    """
    多源數據收集器
    協調視覺爬蟲和傳統爬蟲的數據收集
    """
    
    def __init__(self):
        self.logger = get_enhanced_logger(self.__class__.__name__)
        self.visual_scraper = None
        self.traditional_scraper = None
        
        # 初始化爬蟲組件
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """初始化爬蟲組件"""
        try:
            # 初始化視覺爬蟲
            if ComprehensiveSeekTest:
                self.visual_scraper = ComprehensiveSeekTest()
                self.logger.info("視覺爬蟲初始化成功")
            else:
                self.logger.warning("視覺爬蟲不可用")
            
            # 初始化傳統爬蟲
            self.traditional_scraper = SeekScraperEnhanced()
            self.logger.info("傳統爬蟲初始化成功")
            
        except Exception as e:
            self.logger.error(f"爬蟲初始化失敗: {e}")
    
    async def collect_visual_data(self, job_config: ScrapingJobConfig) -> Dict[str, Any]:
        """
        使用視覺爬蟲收集數據
        
        Args:
            job_config: 任務配置
            
        Returns:
            Dict: 包含數據和元數據的字典
        """
        if not self.visual_scraper:
            raise RuntimeError("視覺爬蟲不可用")
        
        start_time = time.time()
        
        try:
            self.logger.info(f"開始視覺爬蟲數據收集: {job_config.search_term}")
            
            # 執行視覺測試和數據抓取
            await self.visual_scraper.test_job_search_and_scraping()
            
            execution_time = time.time() - start_time
            
            return {
                'source': 'visual_scraper',
                'data': self.visual_scraper.scraped_data,
                'metadata': {
                    'performance_metrics': getattr(self.visual_scraper, 'performance_metrics', {}),
                    'test_results': getattr(self.visual_scraper, 'test_results', []),
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat(),
                    'config': asdict(job_config)
                },
                'success': True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"視覺爬蟲數據收集失敗: {e}")
            
            return {
                'source': 'visual_scraper',
                'data': [],
                'metadata': {
                    'error': str(e),
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat(),
                    'config': asdict(job_config)
                },
                'success': False
            }
    
    async def collect_traditional_data(self, job_config: ScrapingJobConfig) -> Dict[str, Any]:
        """
        使用傳統爬蟲收集數據
        
        Args:
            job_config: 任務配置
            
        Returns:
            Dict: 包含數據和元數據的字典
        """
        if not self.traditional_scraper:
            raise RuntimeError("傳統爬蟲不可用")
        
        start_time = time.time()
        
        try:
            self.logger.info(f"開始傳統爬蟲數據收集: {job_config.search_term}")
            
            # 使用增強型Seek爬蟲
            jobs = await self.traditional_scraper.scrape_jobs(
                search_term=job_config.search_term,
                location=job_config.location,
                job_type=job_config.job_type,
                max_pages=job_config.max_pages
            )
            
            execution_time = time.time() - start_time
            
            # 轉換JobPost對象為字典
            jobs_data = []
            for job in jobs:
                if isinstance(job, JobPost):
                    job_dict = asdict(job)
                else:
                    job_dict = job
                jobs_data.append(job_dict)
            
            return {
                'source': 'traditional_scraper',
                'data': jobs_data,
                'metadata': {
                    'scraping_method': 'requests_bs4',
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat(),
                    'config': asdict(job_config)
                },
                'success': True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"傳統爬蟲數據收集失敗: {e}")
            
            return {
                'source': 'traditional_scraper',
                'data': [],
                'metadata': {
                    'error': str(e),
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat(),
                    'config': asdict(job_config)
                },
                'success': False
            }


class DataFusionProcessor:
    """
    數據融合處理器
    負責合併多源數據並進行交叉驗證
    """
    
    def __init__(self):
        self.logger = get_enhanced_logger(self.__class__.__name__)
    
    def merge_multi_source_data(self, data_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合併多個數據源
        
        Args:
            data_sources: 數據源列表
            
        Returns:
            List[Dict]: 合併後的職位數據
        """
        merged_jobs = []
        
        for source_data in data_sources:
            if not source_data.get('success', False):
                self.logger.warning(f"跳過失敗的數據源: {source_data['source']}")
                continue
            
            source_type = source_data['source']
            jobs = source_data['data']
            metadata = source_data['metadata']
            
            self.logger.info(f"處理數據源 {source_type}: {len(jobs)} 個職位")
            
            for job in jobs:
                # 標準化職位數據
                standardized_job = self._standardize_job_data(job)
                
                # 添加數據源信息
                standardized_job['data_source'] = source_type
                standardized_job['source_metadata'] = metadata
                
                merged_jobs.append(standardized_job)
        
        self.logger.info(f"合併完成，總計 {len(merged_jobs)} 個職位")
        
        # 去重處理
        deduplicated_jobs = self._deduplicate_jobs(merged_jobs)
        
        # 交叉驗證
        validated_jobs = self._cross_validate_jobs(deduplicated_jobs)
        
        return validated_jobs
    
    def _standardize_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        標準化職位數據格式
        
        Args:
            job: 原始職位數據
            
        Returns:
            Dict: 標準化後的職位數據
        """
        # 定義標準字段映射
        field_mapping = {
            'title': ['title', 'job_title', 'position'],
            'company': ['company', 'company_name', 'employer'],
            'location': ['location', 'job_location', 'address'],
            'description': ['description', 'job_description', 'summary'],
            'salary': ['salary', 'salary_info', 'compensation'],
            'url': ['url', 'job_url', 'link'],
            'date_posted': ['date_posted', 'posted_date', 'scraped_at']
        }
        
        standardized = {}
        
        for standard_field, possible_fields in field_mapping.items():
            value = None
            for field in possible_fields:
                if field in job and job[field]:
                    value = job[field]
                    break
            
            standardized[standard_field] = value or ""
        
        # 保留其他字段
        for key, value in job.items():
            if key not in [field for fields in field_mapping.values() for field in fields]:
                standardized[key] = value
        
        return standardized
    
    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重處理
        
        Args:
            jobs: 職位列表
            
        Returns:
            List[Dict]: 去重後的職位列表
        """
        seen_urls = set()
        seen_title_company = set()
        deduplicated = []
        
        for job in jobs:
            # URL去重
            url = job.get('url', '')
            if url and url in seen_urls:
                continue
            
            # 標題+公司去重
            title = job.get('title', '').strip().lower()
            company = job.get('company', '').strip().lower()
            title_company_key = f"{title}|{company}"
            
            if title_company_key in seen_title_company:
                continue
            
            # 記錄已見過的標識
            if url:
                seen_urls.add(url)
            if title and company:
                seen_title_company.add(title_company_key)
            
            deduplicated.append(job)
        
        removed_count = len(jobs) - len(deduplicated)
        if removed_count > 0:
            self.logger.info(f"去重完成，移除 {removed_count} 個重複職位")
        
        return deduplicated
    
    def _cross_validate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        交叉驗證職位數據
        
        Args:
            jobs: 職位列表
            
        Returns:
            List[Dict]: 驗證後的職位列表
        """
        # 按相似性分組
        job_groups = self._group_similar_jobs(jobs)
        validated_jobs = []
        
        for group in job_groups:
            if len(group) > 1:
                # 多源數據，進行交叉驗證
                validated_job = self._validate_multi_source_job(group)
            else:
                # 單源數據，進行基本驗證
                validated_job = self._validate_single_source_job(group[0])
            
            if validated_job:
                validated_jobs.append(validated_job)
        
        return validated_jobs
    
    def _group_similar_jobs(self, jobs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        將相似的職位分組
        
        Args:
            jobs: 職位列表
            
        Returns:
            List[List[Dict]]: 分組後的職位列表
        """
        groups = []
        processed = set()
        
        for i, job in enumerate(jobs):
            if i in processed:
                continue
            
            group = [job]
            processed.add(i)
            
            # 查找相似職位
            for j, other_job in enumerate(jobs[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_jobs_similar(job, other_job):
                    group.append(other_job)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_jobs_similar(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> bool:
        """
        判斷兩個職位是否相似
        
        Args:
            job1: 職位1
            job2: 職位2
            
        Returns:
            bool: 是否相似
        """
        # 簡單的相似性判斷
        title1 = job1.get('title', '').strip().lower()
        title2 = job2.get('title', '').strip().lower()
        company1 = job1.get('company', '').strip().lower()
        company2 = job2.get('company', '').strip().lower()
        
        # 標題和公司都相同則認為相似
        return title1 == title2 and company1 == company2
    
    def _validate_multi_source_job(self, job_group: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        驗證多源職位數據
        
        Args:
            job_group: 相似職位組
            
        Returns:
            Optional[Dict]: 驗證後的職位數據
        """
        # 選擇最完整的數據作為基礎
        base_job = max(job_group, key=lambda j: len([v for v in j.values() if v]))
        
        # 添加多源驗證標記
        base_job['multi_source_verified'] = True
        base_job['source_count'] = len(job_group)
        base_job['all_sources'] = [job.get('data_source') for job in job_group]
        
        return base_job
    
    def _validate_single_source_job(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        驗證單源職位數據
        
        Args:
            job: 職位數據
            
        Returns:
            Optional[Dict]: 驗證後的職位數據
        """
        # 基本字段檢查
        required_fields = ['title', 'company']
        
        for field in required_fields:
            if not job.get(field, '').strip():
                self.logger.warning(f"職位缺少必要字段 {field}，跳過")
                return None
        
        job['multi_source_verified'] = False
        job['source_count'] = 1
        
        return job


class EnhancedETLOrchestrator:
    """
    增強型ETL編排器
    統一調度視覺爬蟲、傳統爬蟲和ETL處理
    """
    
    def __init__(self, output_path: str = None):
        """
        初始化編排器
        
        Args:
            output_path: 輸出路徑
        """
        self.output_path = Path(output_path) if output_path else Path("./enhanced_etl_output")
        self.output_path.mkdir(exist_ok=True)
        
        self.logger = get_enhanced_logger(self.__class__.__name__)
        
        # 初始化組件
        self.strategy_selector = ScrapingStrategySelector()
        self.data_collector = MultiSourceDataCollector()
        self.data_fusion_processor = DataFusionProcessor()
        self.etl_processor = SeekETLProcessor(
            output_path=str(self.output_path / "processed_data"),
            enable_data_validation=True,
            enable_deduplication=True
        )
        
        # 性能統計
        self.execution_stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'execution_times': [],
            'strategy_usage': {}
        }
    
    async def execute_scraping_job(self, job_config: ScrapingJobConfig) -> Dict[str, Any]:
        """
        執行爬蟲任務
        
        Args:
            job_config: 任務配置
            
        Returns:
            Dict: 執行結果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"開始執行爬蟲任務: {job_config.search_term}")
            
            # 1. 策略選擇
            strategy = self.strategy_selector.select_strategy(job_config)
            self.logger.info(f"選定策略: {strategy}")
            
            # 2. 執行抓取
            raw_data_sources = await self._execute_with_strategy(strategy, job_config)
            
            # 3. 數據融合
            merged_data = self.data_fusion_processor.merge_multi_source_data(raw_data_sources)
            
            # 4. ETL處理
            processed_jobs = self.etl_processor.process_raw_data(merged_data)
            
            # 5. 生成結果
            execution_time = time.time() - start_time
            result = self._generate_execution_result(
                job_config, strategy, processed_jobs, raw_data_sources, execution_time
            )
            
            # 6. 更新統計
            self._update_execution_stats(strategy, True, execution_time, len(processed_jobs))
            
            self.logger.info(f"任務執行成功，處理 {len(processed_jobs)} 個職位")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"任務執行失敗: {e}")
            
            # 更新失敗統計
            self._update_execution_stats(strategy, False, execution_time, 0)
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'config': asdict(job_config)
            }
    
    async def _execute_with_strategy(self, strategy: ScrapingStrategy, 
                                   job_config: ScrapingJobConfig) -> List[Dict[str, Any]]:
        """
        根據策略執行數據抓取
        
        Args:
            strategy: 爬蟲策略
            job_config: 任務配置
            
        Returns:
            List[Dict]: 原始數據源列表
        """
        data_sources = []
        
        if strategy == ScrapingStrategy.VISUAL_ONLY:
            # 僅視覺爬蟲
            visual_data = await self.data_collector.collect_visual_data(job_config)
            data_sources.append(visual_data)
            
        elif strategy == ScrapingStrategy.TRADITIONAL_ONLY:
            # 僅傳統爬蟲
            traditional_data = await self.data_collector.collect_traditional_data(job_config)
            data_sources.append(traditional_data)
            
        elif strategy == ScrapingStrategy.VISUAL_PRIMARY:
            # 視覺爬蟲為主，傳統爬蟲為輔
            visual_data = await self.data_collector.collect_visual_data(job_config)
            data_sources.append(visual_data)
            
            if not visual_data.get('success', False):
                self.logger.info("視覺爬蟲失敗，啟用傳統爬蟲備份")
                traditional_data = await self.data_collector.collect_traditional_data(job_config)
                data_sources.append(traditional_data)
                
        elif strategy == ScrapingStrategy.TRADITIONAL_PRIMARY:
            # 傳統爬蟲為主，視覺爬蟲為輔
            traditional_data = await self.data_collector.collect_traditional_data(job_config)
            data_sources.append(traditional_data)
            
            if not traditional_data.get('success', False):
                self.logger.info("傳統爬蟲失敗，啟用視覺爬蟲備份")
                visual_data = await self.data_collector.collect_visual_data(job_config)
                data_sources.append(visual_data)
                
        elif strategy == ScrapingStrategy.HYBRID:
            # 智能混合模式，根據任務特性選擇執行方式
            data_sources = await self._execute_smart_hybrid(job_config)
        
        return data_sources
    
    async def _execute_smart_hybrid(self, job_config: ScrapingJobConfig) -> List[Dict[str, Any]]:
        """
        智能混合模式執行
        根據任務特性和資源狀況選擇最佳執行方式
        
        Args:
            job_config: 任務配置
            
        Returns:
            List[Dict]: 數據源列表
        """
        data_sources = []
        
        # 根據任務特性決定執行策略
        if job_config.max_results <= 20:
            # 小量數據：漸進式執行，先快後慢
            self.logger.info("小量數據任務，採用漸進式執行")
            data_sources = await self._execute_progressive(job_config)
        elif job_config.large_volume_required:
            # 大量數據：並行執行，最大化效率
            self.logger.info("大量數據任務，採用並行執行")
            data_sources = await self._execute_parallel(job_config)
        else:
            # 中等數據：智能選擇
            self.logger.info("中等數據任務，採用智能選擇")
            data_sources = await self._execute_adaptive(job_config)
        
        return data_sources
    
    async def _execute_progressive(self, job_config: ScrapingJobConfig) -> List[Dict[str, Any]]:
        """
        漸進式執行：先執行快速策略，根據結果決定是否執行慢速策略
        
        Args:
            job_config: 任務配置
            
        Returns:
            List[Dict]: 數據源列表
        """
        data_sources = []
        
        # 第一階段：執行傳統爬蟲（快速）
        self.logger.info("漸進式執行 - 第一階段：傳統爬蟲")
        traditional_data = await self.data_collector.collect_traditional_data(job_config)
        data_sources.append(traditional_data)
        
        # 評估第一階段結果
        if traditional_data.get('success', False):
            job_count = len(traditional_data.get('data', []))
            data_quality = self._estimate_data_quality(traditional_data)
            
            # 如果結果足夠好，可能不需要第二階段
            if job_count >= job_config.max_results * 0.8 and data_quality >= 0.7:
                self.logger.info(f"第一階段結果良好 (數量: {job_count}, 質量: {data_quality:.2f})，跳過第二階段")
                return data_sources
        
        # 第二階段：執行視覺爬蟲（慢速但高質量）
        self.logger.info("漸進式執行 - 第二階段：視覺爬蟲")
        visual_data = await self.data_collector.collect_visual_data(job_config)
        data_sources.append(visual_data)
        
        return data_sources
    
    async def _execute_parallel(self, job_config: ScrapingJobConfig) -> List[Dict[str, Any]]:
        """
        並行執行：同時執行兩種策略，最大化數據收集效率
        
        Args:
            job_config: 任務配置
            
        Returns:
            List[Dict]: 數據源列表
        """
        self.logger.info("並行執行兩種爬蟲策略")
        
        # 並行執行
        tasks = [
            self.data_collector.collect_visual_data(job_config),
            self.data_collector.collect_traditional_data(job_config)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data_sources = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                strategy_name = "視覺爬蟲" if i == 0 else "傳統爬蟲"
                self.logger.error(f"{strategy_name}執行出錯: {result}")
            else:
                data_sources.append(result)
        
        return data_sources
    
    async def _execute_adaptive(self, job_config: ScrapingJobConfig) -> List[Dict[str, Any]]:
        """
        自適應執行：根據實時性能動態調整執行策略
        
        Args:
            job_config: 任務配置
            
        Returns:
            List[Dict]: 數據源列表
        """
        data_sources = []
        
        # 獲取策略性能評估
        visual_perf = self.strategy_selector.strategy_performance[ScrapingStrategy.VISUAL_PRIMARY]
        traditional_perf = self.strategy_selector.strategy_performance[ScrapingStrategy.TRADITIONAL_PRIMARY]
        
        visual_score = visual_perf['success_rate'] * visual_perf['quality_score']
        traditional_score = traditional_perf['success_rate'] * (1.0 / (traditional_perf['avg_time'] / 10))
        
        # 根據評分決定執行順序
        if visual_score > traditional_score * 1.2:
            # 視覺爬蟲明顯更優，優先執行
            self.logger.info("自適應執行：視覺爬蟲優先")
            visual_data = await self.data_collector.collect_visual_data(job_config)
            data_sources.append(visual_data)
            
            if not visual_data.get('success', False):
                traditional_data = await self.data_collector.collect_traditional_data(job_config)
                data_sources.append(traditional_data)
        elif traditional_score > visual_score * 1.2:
            # 傳統爬蟲明顯更優，優先執行
            self.logger.info("自適應執行：傳統爬蟲優先")
            traditional_data = await self.data_collector.collect_traditional_data(job_config)
            data_sources.append(traditional_data)
            
            if not traditional_data.get('success', False):
                visual_data = await self.data_collector.collect_visual_data(job_config)
                data_sources.append(visual_data)
        else:
            # 性能相近，並行執行
            self.logger.info("自適應執行：並行執行")
            data_sources = await self._execute_parallel(job_config)
        
        return data_sources
    
    def _estimate_data_quality(self, data_source: Dict[str, Any]) -> float:
        """
        估算數據源的質量評分
        
        Args:
            data_source: 數據源
            
        Returns:
            float: 質量評分 (0-1)
        """
        if not data_source.get('success', False):
            return 0.0
        
        jobs = data_source.get('data', [])
        if not jobs:
            return 0.0
        
        # 基於數據完整性評估質量
        total_score = 0
        for job in jobs:
            score = 0
            # 檢查關鍵字段
            if job.get('title'):
                score += 0.3
            if job.get('company'):
                score += 0.2
            if job.get('location'):
                score += 0.2
            if job.get('description'):
                score += 0.2
            if job.get('salary'):
                score += 0.1
            
            total_score += score
        
        return total_score / len(jobs) if jobs else 0.0
    
    def _generate_execution_result(self, job_config: ScrapingJobConfig, 
                                 strategy: ScrapingStrategy,
                                 processed_jobs: List[JobPost],
                                 raw_data_sources: List[Dict[str, Any]],
                                 execution_time: float) -> Dict[str, Any]:
        """
        生成執行結果
        
        Args:
            job_config: 任務配置
            strategy: 使用的策略
            processed_jobs: 處理後的職位列表
            raw_data_sources: 原始數據源
            execution_time: 執行時間
            
        Returns:
            Dict: 執行結果
        """
        # 轉換JobPost對象為字典
        jobs_data = []
        for job in processed_jobs:
            if isinstance(job, JobPost):
                job_dict = asdict(job)
            else:
                job_dict = job
            jobs_data.append(job_dict)
        
        return {
            'success': True,
            'strategy_used': strategy.value,
            'total_jobs': len(jobs_data),
            'jobs': jobs_data,
            'execution_time': execution_time,
            'data_sources_summary': {
                source['source']: {
                    'success': source.get('success', False),
                    'job_count': len(source.get('data', [])),
                    'execution_time': source.get('metadata', {}).get('execution_time', 0)
                }
                for source in raw_data_sources
            },
            'quality_report': self.etl_processor.get_quality_report(),
            'config': asdict(job_config),
            'timestamp': datetime.now().isoformat()
        }
    
    def _update_execution_stats(self, strategy: ScrapingStrategy, success: bool, 
                              execution_time: float, job_count: int):
        """
        更新執行統計
        
        Args:
            strategy: 使用的策略
            success: 是否成功
            execution_time: 執行時間
            job_count: 職位數量
        """
        self.execution_stats['total_jobs'] += job_count
        
        if success:
            self.execution_stats['successful_jobs'] += job_count
        else:
            self.execution_stats['failed_jobs'] += job_count
        
        self.execution_stats['execution_times'].append(execution_time)
        
        strategy_key = strategy.value
        if strategy_key not in self.execution_stats['strategy_usage']:
            self.execution_stats['strategy_usage'][strategy_key] = 0
        self.execution_stats['strategy_usage'][strategy_key] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        獲取性能報告
        
        Returns:
            Dict: 性能報告
        """
        stats = self.execution_stats
        
        avg_execution_time = (
            sum(stats['execution_times']) / len(stats['execution_times'])
            if stats['execution_times'] else 0
        )
        
        success_rate = (
            stats['successful_jobs'] / (stats['successful_jobs'] + stats['failed_jobs'])
            if (stats['successful_jobs'] + stats['failed_jobs']) > 0 else 0
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_jobs_processed': stats['total_jobs'],
            'successful_jobs': stats['successful_jobs'],
            'failed_jobs': stats['failed_jobs'],
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'strategy_usage': stats['strategy_usage'],
            'etl_quality_stats': self.etl_processor.quality_stats
        }
    
    async def export_results(self, result: Dict[str, Any], 
                           formats: List[str] = None) -> List[str]:
        """
        導出結果到文件
        
        Args:
            result: 執行結果
            formats: 導出格式列表
            
        Returns:
            List[str]: 導出文件路徑列表
        """
        if formats is None:
            formats = ['json']
        
        exported_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for format_type in formats:
            if format_type == 'json':
                filename = f"enhanced_etl_result_{timestamp}.json"
                filepath = self.output_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                
                exported_files.append(str(filepath))
                
            elif format_type == 'csv':
                filename = f"enhanced_etl_result_{timestamp}.csv"
                filepath = self.output_path / filename
                
                # 將職位數據轉換為CSV
                if result.get('jobs'):
                    import pandas as pd
                    df = pd.DataFrame(result['jobs'])
                    df.to_csv(filepath, index=False, encoding='utf-8')
                    exported_files.append(str(filepath))
        
        self.logger.info(f"結果已導出到: {exported_files}")
        return exported_files


# 使用示例
if __name__ == "__main__":
    async def main():
        # 創建編排器
        orchestrator = EnhancedETLOrchestrator(output_path="./enhanced_etl_output")
        
        # 配置任務
        job_config = ScrapingJobConfig(
            search_term="python developer",
            location="Sydney NSW",
            max_results=20,
            strategy=ScrapingStrategy.HYBRID,
            high_quality_required=True
        )
        
        # 執行任務
        result = await orchestrator.execute_scraping_job(job_config)
        
        if result['success']:
            print(f"任務執行成功，處理了 {result['total_jobs']} 個職位")
            
            # 導出結果
            exported_files = await orchestrator.export_results(result, ['json', 'csv'])
            print(f"結果已導出到: {exported_files}")
            
            # 顯示性能報告
            performance_report = orchestrator.get_performance_report()
            print(f"性能報告: {performance_report}")
        else:
            print(f"任務執行失敗: {result.get('error')}")
    
    # 運行示例
    asyncio.run(main())