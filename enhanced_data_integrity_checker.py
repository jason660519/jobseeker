#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版數據完整性檢查器
專門處理多平台搜尋結果的完整性驗證、數據聚合和質量評估

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import uuid
import statistics
from collections import defaultdict, Counter

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory data integrity tracking")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Pandas not available, using basic data analysis")

from task_tracking_service import TaskTrackingService
from error_handling_manager import ErrorHandlingManager, ErrorInfo, ErrorSeverity, ErrorCategory
from notification_service import NotificationService, NotificationType, NotificationPriority


class DataQualityLevel(Enum):
    """數據質量等級"""
    EXCELLENT = "excellent"  # 95%+
    GOOD = "good"           # 85-94%
    FAIR = "fair"           # 70-84%
    POOR = "poor"           # 50-69%
    CRITICAL = "critical"   # <50%


class IntegrityCheckType(Enum):
    """完整性檢查類型"""
    PLATFORM_COVERAGE = "platform_coverage"      # 平台覆蓋率
    DATA_COMPLETENESS = "data_completeness"      # 數據完整性
    FIELD_CONSISTENCY = "field_consistency"      # 字段一致性
    DUPLICATE_DETECTION = "duplicate_detection"  # 重複檢測
    SCHEMA_VALIDATION = "schema_validation"      # 模式驗證
    CROSS_PLATFORM_CONSISTENCY = "cross_platform_consistency"  # 跨平台一致性
    TEMPORAL_CONSISTENCY = "temporal_consistency"  # 時間一致性
    GEOGRAPHIC_CONSISTENCY = "geographic_consistency"  # 地理一致性


class AggregationStrategy(Enum):
    """聚合策略"""
    MERGE_ALL = "merge_all"                    # 合併所有結果
    DEDUPLICATE_SMART = "deduplicate_smart"    # 智能去重
    PRIORITY_BASED = "priority_based"          # 基於優先級
    QUALITY_WEIGHTED = "quality_weighted"      # 質量加權
    CONSENSUS_BASED = "consensus_based"        # 基於共識
    PLATFORM_SPECIFIC = "platform_specific"   # 平台特定


class ValidationRule(Enum):
    """驗證規則"""
    REQUIRED_FIELDS = "required_fields"        # 必需字段
    FIELD_FORMATS = "field_formats"            # 字段格式
    VALUE_RANGES = "value_ranges"              # 值範圍
    BUSINESS_LOGIC = "business_logic"          # 業務邏輯
    CROSS_FIELD = "cross_field"                # 跨字段驗證
    EXTERNAL_REFERENCE = "external_reference"  # 外部參考


@dataclass
class DataQualityMetrics:
    """數據質量指標"""
    completeness_score: float = 0.0      # 完整性分數
    accuracy_score: float = 0.0          # 準確性分數
    consistency_score: float = 0.0       # 一致性分數
    uniqueness_score: float = 0.0        # 唯一性分數
    validity_score: float = 0.0          # 有效性分數
    timeliness_score: float = 0.0        # 及時性分數
    overall_score: float = 0.0           # 總體分數
    quality_level: DataQualityLevel = DataQualityLevel.FAIR
    
    # 詳細統計
    total_records: int = 0
    valid_records: int = 0
    duplicate_records: int = 0
    missing_fields: Dict[str, int] = field(default_factory=dict)
    invalid_fields: Dict[str, int] = field(default_factory=dict)
    
    # 時間戳
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlatformDataSummary:
    """平台數據摘要"""
    platform: str
    total_jobs: int = 0
    valid_jobs: int = 0
    duplicate_jobs: int = 0
    unique_jobs: int = 0
    data_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    collection_time: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 字段統計
    field_coverage: Dict[str, float] = field(default_factory=dict)
    field_quality: Dict[str, float] = field(default_factory=dict)


@dataclass
class IntegrityCheckResult:
    """完整性檢查結果"""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    check_type: IntegrityCheckType = IntegrityCheckType.DATA_COMPLETENESS
    status: str = "pending"  # pending, running, completed, failed
    
    # 檢查結果
    passed: bool = False
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 平台數據
    platform_summaries: Dict[str, PlatformDataSummary] = field(default_factory=dict)
    expected_platforms: Set[str] = field(default_factory=set)
    actual_platforms: Set[str] = field(default_factory=set)
    missing_platforms: Set[str] = field(default_factory=set)
    
    # 聚合結果
    aggregated_data: Optional[List[Dict[str, Any]]] = None
    aggregation_strategy: AggregationStrategy = AggregationStrategy.MERGE_ALL
    final_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    
    # 時間信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: float = 0.0
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityCheckConfig:
    """完整性檢查配置"""
    # 檢查設置
    enabled_checks: Set[IntegrityCheckType] = field(default_factory=lambda: {
        IntegrityCheckType.PLATFORM_COVERAGE,
        IntegrityCheckType.DATA_COMPLETENESS,
        IntegrityCheckType.DUPLICATE_DETECTION,
        IntegrityCheckType.SCHEMA_VALIDATION
    })
    
    # 質量閾值
    min_platform_coverage: float = 0.8      # 最小平台覆蓋率
    min_data_completeness: float = 0.7       # 最小數據完整性
    max_duplicate_rate: float = 0.1          # 最大重複率
    min_overall_quality: float = 0.6         # 最小總體質量
    
    # 聚合設置
    aggregation_strategy: AggregationStrategy = AggregationStrategy.DEDUPLICATE_SMART
    duplicate_threshold: float = 0.85        # 重複判定閾值
    quality_weight: float = 0.3              # 質量權重
    
    # 驗證規則
    required_fields: Set[str] = field(default_factory=lambda: {
        'title', 'company', 'location', 'date_posted'
    })
    
    field_formats: Dict[str, str] = field(default_factory=lambda: {
        'date_posted': r'\d{4}-\d{2}-\d{2}',
        'salary_min': r'\d+',
        'salary_max': r'\d+'
    })
    
    # 超時設置
    check_timeout: int = 300                 # 檢查超時（秒）
    aggregation_timeout: int = 180           # 聚合超時（秒）
    
    # 並發設置
    max_concurrent_checks: int = 5
    max_workers: int = 10


class EnhancedDataIntegrityChecker:
    """增強版數據完整性檢查器"""
    
    def __init__(self,
                 config: Optional[IntegrityCheckConfig] = None,
                 task_tracker: Optional[TaskTrackingService] = None,
                 error_handler: Optional[ErrorHandlingManager] = None,
                 notification_service: Optional[NotificationService] = None,
                 redis_url: str = "redis://localhost:6379/5"):
        """初始化數據完整性檢查器"""
        self.config = config or IntegrityCheckConfig()
        self.task_tracker = task_tracker
        self.error_handler = error_handler
        self.notification_service = notification_service
        self.redis_url = redis_url
        
        # Redis連接
        self.redis_client = None
        self._setup_redis()
        
        # 存儲
        self.check_results: Dict[str, IntegrityCheckResult] = {}
        self.platform_schemas: Dict[str, Dict[str, Any]] = {}
        self.quality_history: List[DataQualityMetrics] = []
        
        # 處理隊列
        self.check_queue: List[str] = []  # job_ids
        self.processing_jobs: Set[str] = set()
        self.queue_lock = threading.Lock()
        
        # 統計信息
        self.stats = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'average_quality': 0.0,
            'platform_stats': defaultdict(dict),
            'check_type_stats': defaultdict(dict),
            'start_time': datetime.now()
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="IntegrityChecker"
        )
        self.background_tasks: List[Future] = []
        self.shutdown_event = threading.Event()
        
        # 檢查器映射
        self.check_handlers = {
            IntegrityCheckType.PLATFORM_COVERAGE: self._check_platform_coverage,
            IntegrityCheckType.DATA_COMPLETENESS: self._check_data_completeness,
            IntegrityCheckType.FIELD_CONSISTENCY: self._check_field_consistency,
            IntegrityCheckType.DUPLICATE_DETECTION: self._check_duplicate_detection,
            IntegrityCheckType.SCHEMA_VALIDATION: self._check_schema_validation,
            IntegrityCheckType.CROSS_PLATFORM_CONSISTENCY: self._check_cross_platform_consistency,
            IntegrityCheckType.TEMPORAL_CONSISTENCY: self._check_temporal_consistency,
            IntegrityCheckType.GEOGRAPHIC_CONSISTENCY: self._check_geographic_consistency
        }
        
        # 聚合器映射
        self.aggregation_handlers = {
            AggregationStrategy.MERGE_ALL: self._aggregate_merge_all,
            AggregationStrategy.DEDUPLICATE_SMART: self._aggregate_deduplicate_smart,
            AggregationStrategy.PRIORITY_BASED: self._aggregate_priority_based,
            AggregationStrategy.QUALITY_WEIGHTED: self._aggregate_quality_weighted,
            AggregationStrategy.CONSENSUS_BASED: self._aggregate_consensus_based,
            AggregationStrategy.PLATFORM_SPECIFIC: self._aggregate_platform_specific
        }
        
        # 初始化平台模式
        self._setup_platform_schemas()
        
        # 啟動背景任務
        self._start_background_tasks()
        
        logging.info("增強版數據完整性檢查器已初始化")
    
    def _setup_redis(self):
        """設置Redis連接"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logging.info("Redis連接已建立（數據完整性檢查器）")
        except Exception as e:
            logging.warning(f"Redis連接失敗（數據完整性檢查器）: {e}")
            self.redis_client = None
    
    def _setup_platform_schemas(self):
        """設置平台數據模式"""
        # LinkedIn模式
        self.platform_schemas['linkedin'] = {
            'required_fields': {'title', 'company', 'location', 'date_posted', 'job_url'},
            'optional_fields': {'description', 'salary_min', 'salary_max', 'job_type', 'experience_level'},
            'field_types': {
                'title': str,
                'company': str,
                'location': str,
                'date_posted': str,
                'salary_min': (int, float, type(None)),
                'salary_max': (int, float, type(None))
            },
            'field_formats': {
                'date_posted': r'\d{4}-\d{2}-\d{2}',
                'job_url': r'https://.*linkedin.*'
            }
        }
        
        # Indeed模式
        self.platform_schemas['indeed'] = {
            'required_fields': {'title', 'company', 'location', 'date_posted', 'job_url'},
            'optional_fields': {'description', 'salary', 'job_type', 'remote'},
            'field_types': {
                'title': str,
                'company': str,
                'location': str,
                'date_posted': str,
                'salary': (str, type(None))
            },
            'field_formats': {
                'date_posted': r'\d{4}-\d{2}-\d{2}',
                'job_url': r'https://.*indeed.*'
            }
        }
        
        # Google Jobs模式
        self.platform_schemas['google'] = {
            'required_fields': {'title', 'company', 'location', 'date_posted'},
            'optional_fields': {'description', 'salary_range', 'job_type', 'source_url'},
            'field_types': {
                'title': str,
                'company': str,
                'location': str,
                'date_posted': str
            },
            'field_formats': {
                'date_posted': r'\d{4}-\d{2}-\d{2}'
            }
        }
        
        # 1111模式
        self.platform_schemas['1111'] = {
            'required_fields': {'title', 'company', 'location', 'date_posted', 'job_url'},
            'optional_fields': {'description', 'salary_min', 'salary_max', 'experience', 'education'},
            'field_types': {
                'title': str,
                'company': str,
                'location': str,
                'date_posted': str
            },
            'field_formats': {
                'date_posted': r'\d{4}-\d{2}-\d{2}',
                'job_url': r'https://.*1111.*'
            }
        }
        
        # 104模式
        self.platform_schemas['104'] = {
            'required_fields': {'title', 'company', 'location', 'date_posted', 'job_url'},
            'optional_fields': {'description', 'salary_min', 'salary_max', 'job_type', 'industry'},
            'field_types': {
                'title': str,
                'company': str,
                'location': str,
                'date_posted': str
            },
            'field_formats': {
                'date_posted': r'\d{4}-\d{2}-\d{2}',
                'job_url': r'https://.*104.*'
            }
        }
    
    def _start_background_tasks(self):
        """啟動背景任務"""
        # 檢查處理任務
        self.background_tasks.append(
            self.executor.submit(self._check_processing_loop)
        )
        
        # 質量監控任務
        self.background_tasks.append(
            self.executor.submit(self._quality_monitoring_loop)
        )
        
        # 統計更新任務
        self.background_tasks.append(
            self.executor.submit(self._stats_update_loop)
        )
        
        # 清理任務
        self.background_tasks.append(
            self.executor.submit(self._cleanup_loop)
        )
    
    def submit_integrity_check(self,
                              job_id: str,
                              platform_data: Dict[str, List[Dict[str, Any]]],
                              expected_platforms: Optional[Set[str]] = None,
                              check_types: Optional[Set[IntegrityCheckType]] = None,
                              aggregation_strategy: Optional[AggregationStrategy] = None) -> str:
        """提交完整性檢查"""
        try:
            # 創建檢查結果
            check_result = IntegrityCheckResult(
                job_id=job_id,
                expected_platforms=expected_platforms or set(platform_data.keys()),
                actual_platforms=set(platform_data.keys()),
                aggregation_strategy=aggregation_strategy or self.config.aggregation_strategy
            )
            
            # 計算缺失平台
            check_result.missing_platforms = check_result.expected_platforms - check_result.actual_platforms
            
            # 存儲檢查結果
            self.check_results[check_result.check_id] = check_result
            
            # 存儲平台數據到Redis
            if self.redis_client:
                self.redis_client.hset(
                    f"platform_data:{job_id}",
                    mapping={
                        platform: json.dumps(data)
                        for platform, data in platform_data.items()
                    }
                )
                self.redis_client.expire(f"platform_data:{job_id}", 86400)  # 24小時過期
            
            # 添加到處理隊列
            with self.queue_lock:
                if job_id not in self.check_queue and job_id not in self.processing_jobs:
                    self.check_queue.append(job_id)
            
            logging.info(f"已提交完整性檢查: {job_id} -> {check_result.check_id}")
            return check_result.check_id
            
        except Exception as e:
            logging.error(f"提交完整性檢查失敗: {e}")
            if self.error_handler:
                error_info = ErrorInfo(
                    job_id=job_id,
                    error_type="IntegrityCheckSubmissionError",
                    error_message=str(e),
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.SYSTEM
                )
                self.error_handler.handle_error(error_info)
            return ""
    
    def get_check_result(self, check_id: str) -> Optional[IntegrityCheckResult]:
        """獲取檢查結果"""
        return self.check_results.get(check_id)
    
    def get_job_check_results(self, job_id: str) -> List[IntegrityCheckResult]:
        """獲取任務的所有檢查結果"""
        return [
            result for result in self.check_results.values()
            if result.job_id == job_id
        ]
    
    def _check_processing_loop(self):
        """檢查處理循環"""
        while not self.shutdown_event.is_set():
            try:
                jobs_to_process = []
                
                # 獲取待處理任務
                with self.queue_lock:
                    available_slots = self.config.max_concurrent_checks - len(self.processing_jobs)
                    if available_slots > 0 and self.check_queue:
                        jobs_to_process = self.check_queue[:available_slots]
                        for job_id in jobs_to_process:
                            self.check_queue.remove(job_id)
                            self.processing_jobs.add(job_id)
                
                # 處理任務
                for job_id in jobs_to_process:
                    self.executor.submit(self._process_integrity_check, job_id)
                
                # 等待下一次處理
                if not jobs_to_process:
                    self.shutdown_event.wait(1)
                
            except Exception as e:
                logging.error(f"檢查處理循環錯誤: {e}")
                self.shutdown_event.wait(5)
    
    def _process_integrity_check(self, job_id: str):
        """處理完整性檢查"""
        try:
            # 找到對應的檢查結果
            check_result = None
            for result in self.check_results.values():
                if result.job_id == job_id and result.status == "pending":
                    check_result = result
                    break
            
            if not check_result:
                logging.warning(f"找不到待處理的檢查結果: {job_id}")
                return
            
            check_result.status = "running"
            
            # 獲取平台數據
            platform_data = self._load_platform_data(job_id)
            if not platform_data:
                check_result.status = "failed"
                check_result.issues.append("無法加載平台數據")
                return
            
            # 執行各種檢查
            self._execute_integrity_checks(check_result, platform_data)
            
            # 執行數據聚合
            self._execute_data_aggregation(check_result, platform_data)
            
            # 計算最終質量分數
            self._calculate_final_quality(check_result)
            
            # 完成檢查
            check_result.status = "completed"
            check_result.completed_at = datetime.now()
            check_result.duration = (check_result.completed_at - check_result.started_at).total_seconds()
            
            # 更新統計
            self._update_check_stats(check_result)
            
            # 發送通知
            self._send_check_notification(check_result)
            
            logging.info(f"完整性檢查完成: {job_id} -> {check_result.check_id}")
            
        except Exception as e:
            logging.error(f"處理完整性檢查失敗: {e}")
            if check_result:
                check_result.status = "failed"
                check_result.issues.append(f"處理錯誤: {str(e)}")
        
        finally:
            # 從處理集合中移除
            with self.queue_lock:
                self.processing_jobs.discard(job_id)
    
    def _load_platform_data(self, job_id: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """加載平台數據"""
        try:
            if self.redis_client:
                # 從Redis加載
                data_hash = self.redis_client.hgetall(f"platform_data:{job_id}")
                if data_hash:
                    return {
                        platform: json.loads(data_str)
                        for platform, data_str in data_hash.items()
                    }
            
            # 從任務追蹤服務加載
            if self.task_tracker:
                job_progress = self.task_tracker.get_job_progress(job_id)
                if job_progress and 'platform_results' in job_progress:
                    return job_progress['platform_results']
            
            return None
            
        except Exception as e:
            logging.error(f"加載平台數據失敗: {e}")
            return None
    
    def _execute_integrity_checks(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """執行完整性檢查"""
        try:
            # 為每個平台創建摘要
            for platform, jobs in platform_data.items():
                summary = PlatformDataSummary(platform=platform)
                summary.total_jobs = len(jobs)
                
                # 執行平台特定檢查
                self._analyze_platform_data(summary, jobs)
                
                check_result.platform_summaries[platform] = summary
            
            # 執行啟用的檢查
            for check_type in self.config.enabled_checks:
                if check_type in self.check_handlers:
                    try:
                        self.check_handlers[check_type](check_result, platform_data)
                    except Exception as e:
                        check_result.warnings.append(f"{check_type.value}檢查失敗: {str(e)}")
            
        except Exception as e:
            logging.error(f"執行完整性檢查失敗: {e}")
            check_result.issues.append(f"檢查執行錯誤: {str(e)}")
    
    def _analyze_platform_data(self, summary: PlatformDataSummary, jobs: List[Dict[str, Any]]):
        """分析平台數據"""
        try:
            start_time = time.time()
            
            # 獲取平台模式
            schema = self.platform_schemas.get(summary.platform, {})
            required_fields = schema.get('required_fields', set())
            field_types = schema.get('field_types', {})
            field_formats = schema.get('field_formats', {})
            
            valid_jobs = 0
            duplicate_jobs = 0
            field_coverage = defaultdict(int)
            field_quality = defaultdict(list)
            
            # 重複檢測
            job_signatures = set()
            
            for job in jobs:
                is_valid = True
                
                # 檢查必需字段
                for field in required_fields:
                    if field in job and job[field] is not None and str(job[field]).strip():
                        field_coverage[field] += 1
                        field_quality[field].append(1.0)
                    else:
                        field_quality[field].append(0.0)
                        is_valid = False
                
                # 檢查字段類型
                for field, expected_type in field_types.items():
                    if field in job and job[field] is not None:
                        if isinstance(job[field], expected_type):
                            field_quality[field].append(1.0)
                        else:
                            field_quality[field].append(0.5)
                            is_valid = False
                
                # 檢查字段格式
                import re
                for field, pattern in field_formats.items():
                    if field in job and job[field] is not None:
                        if re.match(pattern, str(job[field])):
                            field_quality[field].append(1.0)
                        else:
                            field_quality[field].append(0.5)
                            is_valid = False
                
                # 重複檢測
                job_signature = self._generate_job_signature(job)
                if job_signature in job_signatures:
                    duplicate_jobs += 1
                else:
                    job_signatures.add(job_signature)
                
                if is_valid:
                    valid_jobs += 1
            
            # 更新摘要
            summary.valid_jobs = valid_jobs
            summary.duplicate_jobs = duplicate_jobs
            summary.unique_jobs = len(job_signatures)
            summary.processing_time = time.time() - start_time
            
            # 計算字段覆蓋率和質量
            total_jobs = len(jobs)
            if total_jobs > 0:
                for field, count in field_coverage.items():
                    summary.field_coverage[field] = count / total_jobs
                
                for field, scores in field_quality.items():
                    if scores:
                        summary.field_quality[field] = statistics.mean(scores)
            
            # 計算數據質量指標
            summary.data_quality = self._calculate_data_quality_metrics(summary, jobs)
            
        except Exception as e:
            logging.error(f"分析平台數據失敗: {e}")
            summary.errors.append(str(e))
    
    def _generate_job_signature(self, job: Dict[str, Any]) -> str:
        """生成職位簽名用於重複檢測"""
        try:
            # 使用關鍵字段生成簽名
            key_fields = ['title', 'company', 'location']
            signature_parts = []
            
            for field in key_fields:
                value = job.get(field, '')
                if value:
                    # 標準化文本
                    normalized = str(value).lower().strip()
                    # 移除多餘空格
                    normalized = ' '.join(normalized.split())
                    signature_parts.append(normalized)
            
            signature_text = '|'.join(signature_parts)
            return hashlib.md5(signature_text.encode()).hexdigest()
            
        except Exception as e:
            logging.warning(f"生成職位簽名失敗: {e}")
            return str(uuid.uuid4())
    
    def _calculate_data_quality_metrics(self, summary: PlatformDataSummary, jobs: List[Dict[str, Any]]) -> DataQualityMetrics:
        """計算數據質量指標"""
        try:
            metrics = DataQualityMetrics()
            total_jobs = len(jobs)
            
            if total_jobs == 0:
                return metrics
            
            # 完整性分數
            if summary.field_coverage:
                metrics.completeness_score = statistics.mean(summary.field_coverage.values())
            
            # 準確性分數（基於字段質量）
            if summary.field_quality:
                metrics.accuracy_score = statistics.mean(summary.field_quality.values())
            
            # 唯一性分數
            metrics.uniqueness_score = summary.unique_jobs / total_jobs if total_jobs > 0 else 0
            
            # 有效性分數
            metrics.validity_score = summary.valid_jobs / total_jobs if total_jobs > 0 else 0
            
            # 一致性分數（基於模式匹配）
            schema = self.platform_schemas.get(summary.platform, {})
            if schema:
                consistency_scores = []
                for job in jobs:
                    job_score = self._calculate_job_consistency_score(job, schema)
                    consistency_scores.append(job_score)
                
                if consistency_scores:
                    metrics.consistency_score = statistics.mean(consistency_scores)
            
            # 及時性分數（基於數據新鮮度）
            metrics.timeliness_score = self._calculate_timeliness_score(jobs)
            
            # 總體分數
            scores = [
                metrics.completeness_score,
                metrics.accuracy_score,
                metrics.consistency_score,
                metrics.uniqueness_score,
                metrics.validity_score,
                metrics.timeliness_score
            ]
            metrics.overall_score = statistics.mean([s for s in scores if s > 0])
            
            # 確定質量等級
            if metrics.overall_score >= 0.95:
                metrics.quality_level = DataQualityLevel.EXCELLENT
            elif metrics.overall_score >= 0.85:
                metrics.quality_level = DataQualityLevel.GOOD
            elif metrics.overall_score >= 0.70:
                metrics.quality_level = DataQualityLevel.FAIR
            elif metrics.overall_score >= 0.50:
                metrics.quality_level = DataQualityLevel.POOR
            else:
                metrics.quality_level = DataQualityLevel.CRITICAL
            
            # 統計信息
            metrics.total_records = total_jobs
            metrics.valid_records = summary.valid_jobs
            metrics.duplicate_records = summary.duplicate_jobs
            
            return metrics
            
        except Exception as e:
            logging.error(f"計算數據質量指標失敗: {e}")
            return DataQualityMetrics()
    
    def _calculate_job_consistency_score(self, job: Dict[str, Any], schema: Dict[str, Any]) -> float:
        """計算單個職位的一致性分數"""
        try:
            score = 0.0
            total_checks = 0
            
            # 檢查必需字段
            required_fields = schema.get('required_fields', set())
            for field in required_fields:
                total_checks += 1
                if field in job and job[field] is not None and str(job[field]).strip():
                    score += 1.0
            
            # 檢查字段類型
            field_types = schema.get('field_types', {})
            for field, expected_type in field_types.items():
                if field in job and job[field] is not None:
                    total_checks += 1
                    if isinstance(job[field], expected_type):
                        score += 1.0
                    else:
                        score += 0.5
            
            # 檢查字段格式
            import re
            field_formats = schema.get('field_formats', {})
            for field, pattern in field_formats.items():
                if field in job and job[field] is not None:
                    total_checks += 1
                    if re.match(pattern, str(job[field])):
                        score += 1.0
                    else:
                        score += 0.5
            
            return score / total_checks if total_checks > 0 else 0.0
            
        except Exception as e:
            logging.warning(f"計算職位一致性分數失敗: {e}")
            return 0.0
    
    def _calculate_timeliness_score(self, jobs: List[Dict[str, Any]]) -> float:
        """計算及時性分數"""
        try:
            if not jobs:
                return 0.0
            
            current_date = datetime.now().date()
            timeliness_scores = []
            
            for job in jobs:
                date_posted = job.get('date_posted')
                if date_posted:
                    try:
                        # 解析日期
                        if isinstance(date_posted, str):
                            job_date = datetime.strptime(date_posted, '%Y-%m-%d').date()
                        else:
                            continue
                        
                        # 計算天數差異
                        days_diff = (current_date - job_date).days
                        
                        # 計算及時性分數（越新越好）
                        if days_diff <= 1:
                            score = 1.0
                        elif days_diff <= 7:
                            score = 0.8
                        elif days_diff <= 30:
                            score = 0.6
                        elif days_diff <= 90:
                            score = 0.4
                        else:
                            score = 0.2
                        
                        timeliness_scores.append(score)
                        
                    except Exception:
                        timeliness_scores.append(0.5)  # 無法解析的日期給中等分數
            
            return statistics.mean(timeliness_scores) if timeliness_scores else 0.0
            
        except Exception as e:
            logging.warning(f"計算及時性分數失敗: {e}")
            return 0.0
    
    # 檢查處理器實現
    def _check_platform_coverage(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查平台覆蓋率"""
        try:
            expected_count = len(check_result.expected_platforms)
            actual_count = len(check_result.actual_platforms)
            
            if expected_count == 0:
                coverage_rate = 1.0
            else:
                coverage_rate = actual_count / expected_count
            
            # 檢查是否通過
            passed = coverage_rate >= self.config.min_platform_coverage
            
            if not passed:
                check_result.issues.append(
                    f"平台覆蓋率不足: {coverage_rate:.2%} < {self.config.min_platform_coverage:.2%}"
                )
                
                if check_result.missing_platforms:
                    check_result.issues.append(
                        f"缺失平台: {', '.join(check_result.missing_platforms)}"
                    )
            
            # 添加建議
            if coverage_rate < 1.0:
                check_result.recommendations.append(
                    f"建議檢查缺失平台的爬蟲服務狀態: {', '.join(check_result.missing_platforms)}"
                )
            
            logging.info(f"平台覆蓋率檢查: {coverage_rate:.2%} ({'通過' if passed else '失敗'})")
            
        except Exception as e:
            logging.error(f"平台覆蓋率檢查失敗: {e}")
            check_result.warnings.append(f"平台覆蓋率檢查錯誤: {str(e)}")
    
    def _check_data_completeness(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查數據完整性"""
        try:
            total_completeness_scores = []
            
            for platform, summary in check_result.platform_summaries.items():
                completeness_score = summary.data_quality.completeness_score
                total_completeness_scores.append(completeness_score)
                
                if completeness_score < self.config.min_data_completeness:
                    check_result.issues.append(
                        f"{platform}平台數據完整性不足: {completeness_score:.2%} < {self.config.min_data_completeness:.2%}"
                    )
            
            # 計算總體完整性
            if total_completeness_scores:
                overall_completeness = statistics.mean(total_completeness_scores)
                passed = overall_completeness >= self.config.min_data_completeness
                
                if not passed:
                    check_result.issues.append(
                        f"總體數據完整性不足: {overall_completeness:.2%} < {self.config.min_data_completeness:.2%}"
                    )
                
                logging.info(f"數據完整性檢查: {overall_completeness:.2%} ({'通過' if passed else '失敗'})")
            
        except Exception as e:
            logging.error(f"數據完整性檢查失敗: {e}")
            check_result.warnings.append(f"數據完整性檢查錯誤: {str(e)}")
    
    def _check_field_consistency(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查字段一致性"""
        try:
            # 收集所有字段
            all_fields = set()
            platform_fields = {}
            
            for platform, jobs in platform_data.items():
                fields = set()
                for job in jobs:
                    fields.update(job.keys())
                platform_fields[platform] = fields
                all_fields.update(fields)
            
            # 檢查字段一致性
            inconsistent_fields = []
            for field in all_fields:
                platforms_with_field = [
                    platform for platform, fields in platform_fields.items()
                    if field in fields
                ]
                
                # 如果不是所有平台都有這個字段，記錄不一致
                if len(platforms_with_field) < len(platform_data) and len(platforms_with_field) > 0:
                    inconsistent_fields.append({
                        'field': field,
                        'platforms_with': platforms_with_field,
                        'platforms_without': [
                            platform for platform in platform_data.keys()
                            if platform not in platforms_with_field
                        ]
                    })
            
            # 報告不一致
            if inconsistent_fields:
                for inconsistency in inconsistent_fields:
                    check_result.warnings.append(
                        f"字段 '{inconsistency['field']}' 在平台間不一致: "
                        f"有: {', '.join(inconsistency['platforms_with'])}, "
                        f"無: {', '.join(inconsistency['platforms_without'])}"
                    )
                
                check_result.recommendations.append(
                    "建議標準化所有平台的字段結構以提高一致性"
                )
            
            logging.info(f"字段一致性檢查: 發現 {len(inconsistent_fields)} 個不一致字段")
            
        except Exception as e:
            logging.error(f"字段一致性檢查失敗: {e}")
            check_result.warnings.append(f"字段一致性檢查錯誤: {str(e)}")
    
    def _check_duplicate_detection(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查重複檢測"""
        try:
            total_jobs = 0
            total_duplicates = 0
            
            for platform, summary in check_result.platform_summaries.items():
                total_jobs += summary.total_jobs
                total_duplicates += summary.duplicate_jobs
                
                # 檢查平台內重複率
                if summary.total_jobs > 0:
                    duplicate_rate = summary.duplicate_jobs / summary.total_jobs
                    if duplicate_rate > self.config.max_duplicate_rate:
                        check_result.issues.append(
                            f"{platform}平台重複率過高: {duplicate_rate:.2%} > {self.config.max_duplicate_rate:.2%}"
                        )
            
            # 檢查跨平台重複
            cross_platform_duplicates = self._detect_cross_platform_duplicates(platform_data)
            
            if cross_platform_duplicates:
                check_result.warnings.append(
                    f"發現 {len(cross_platform_duplicates)} 個跨平台重複職位"
                )
                
                # 添加詳細信息到元數據
                check_result.metadata['cross_platform_duplicates'] = cross_platform_duplicates[:10]  # 只保存前10個
            
            # 計算總體重複率
            if total_jobs > 0:
                overall_duplicate_rate = total_duplicates / total_jobs
                passed = overall_duplicate_rate <= self.config.max_duplicate_rate
                
                if not passed:
                    check_result.issues.append(
                        f"總體重複率過高: {overall_duplicate_rate:.2%} > {self.config.max_duplicate_rate:.2%}"
                    )
                
                logging.info(f"重複檢測: {overall_duplicate_rate:.2%} ({'通過' if passed else '失敗'})")
            
        except Exception as e:
            logging.error(f"重複檢測失敗: {e}")
            check_result.warnings.append(f"重複檢測錯誤: {str(e)}")
    
    def _detect_cross_platform_duplicates(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """檢測跨平台重複"""
        try:
            job_signatures = {}
            duplicates = []
            
            # 為所有職位生成簽名
            for platform, jobs in platform_data.items():
                for i, job in enumerate(jobs):
                    signature = self._generate_job_signature(job)
                    
                    if signature in job_signatures:
                        # 發現重複
                        original = job_signatures[signature]
                        duplicate_info = {
                            'signature': signature,
                            'original_platform': original['platform'],
                            'original_index': original['index'],
                            'duplicate_platform': platform,
                            'duplicate_index': i,
                            'similarity_score': self._calculate_job_similarity(
                                original['job'], job
                            )
                        }
                        duplicates.append(duplicate_info)
                    else:
                        job_signatures[signature] = {
                            'platform': platform,
                            'index': i,
                            'job': job
                        }
            
            return duplicates
            
        except Exception as e:
            logging.error(f"檢測跨平台重複失敗: {e}")
            return []
    
    def _calculate_job_similarity(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> float:
        """計算職位相似度"""
        try:
            # 簡單的相似度計算
            key_fields = ['title', 'company', 'location', 'description']
            similarities = []
            
            for field in key_fields:
                value1 = str(job1.get(field, '')).lower().strip()
                value2 = str(job2.get(field, '')).lower().strip()
                
                if value1 and value2:
                    # 簡單的字符串相似度
                    if value1 == value2:
                        similarity = 1.0
                    elif value1 in value2 or value2 in value1:
                        similarity = 0.8
                    else:
                        # 計算詞彙重疊
                        words1 = set(value1.split())
                        words2 = set(value2.split())
                        if words1 and words2:
                            intersection = len(words1 & words2)
                            union = len(words1 | words2)
                            similarity = intersection / union
                        else:
                            similarity = 0.0
                    
                    similarities.append(similarity)
            
            return statistics.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logging.warning(f"計算職位相似度失敗: {e}")
            return 0.0
    
    def _check_schema_validation(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查模式驗證"""
        try:
            for platform, jobs in platform_data.items():
                schema = self.platform_schemas.get(platform)
                if not schema:
                    check_result.warnings.append(f"平台 {platform} 沒有定義模式")
                    continue
                
                validation_errors = []
                
                for i, job in enumerate(jobs):
                    job_errors = self._validate_job_against_schema(job, schema)
                    if job_errors:
                        validation_errors.extend([
                            f"職位 {i}: {error}" for error in job_errors
                        ])
                
                if validation_errors:
                    check_result.issues.extend([
                        f"{platform}平台模式驗證錯誤: {error}"
                        for error in validation_errors[:5]  # 只顯示前5個錯誤
                    ])
                    
                    if len(validation_errors) > 5:
                        check_result.warnings.append(
                            f"{platform}平台還有 {len(validation_errors) - 5} 個模式驗證錯誤"
                        )
            
            logging.info("模式驗證檢查完成")
            
        except Exception as e:
            logging.error(f"模式驗證失敗: {e}")
            check_result.warnings.append(f"模式驗證錯誤: {str(e)}")
    
    def _validate_job_against_schema(self, job: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """根據模式驗證職位"""
        errors = []
        
        try:
            # 檢查必需字段
            required_fields = schema.get('required_fields', set())
            for field in required_fields:
                if field not in job or job[field] is None or str(job[field]).strip() == '':
                    errors.append(f"缺少必需字段: {field}")
            
            # 檢查字段類型
            field_types = schema.get('field_types', {})
            for field, expected_type in field_types.items():
                if field in job and job[field] is not None:
                    if not isinstance(job[field], expected_type):
                        errors.append(f"字段 {field} 類型錯誤: 期望 {expected_type}, 實際 {type(job[field])}")
            
            # 檢查字段格式
            import re
            field_formats = schema.get('field_formats', {})
            for field, pattern in field_formats.items():
                if field in job and job[field] is not None:
                    if not re.match(pattern, str(job[field])):
                        errors.append(f"字段 {field} 格式錯誤: 不匹配模式 {pattern}")
            
        except Exception as e:
            errors.append(f"驗證過程錯誤: {str(e)}")
        
        return errors
    
    def _check_cross_platform_consistency(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查跨平台一致性"""
        try:
            # 檢查相同公司在不同平台的職位數量差異
            company_stats = defaultdict(lambda: defaultdict(int))
            
            for platform, jobs in platform_data.items():
                for job in jobs:
                    company = job.get('company', '').strip().lower()
                    if company:
                        company_stats[company][platform] += 1
            
            # 分析差異
            inconsistencies = []
            for company, platform_counts in company_stats.items():
                if len(platform_counts) > 1:  # 公司在多個平台出現
                    counts = list(platform_counts.values())
                    max_count = max(counts)
                    min_count = min(counts)
                    
                    # 如果差異過大，記錄不一致
                    if max_count > min_count * 2:  # 差異超過2倍
                        inconsistencies.append({
                            'company': company,
                            'platform_counts': dict(platform_counts),
                            'max_count': max_count,
                            'min_count': min_count
                        })
            
            if inconsistencies:
                check_result.warnings.extend([
                    f"公司 '{inc['company']}' 在不同平台的職位數量差異較大: {inc['platform_counts']}"
                    for inc in inconsistencies[:5]  # 只顯示前5個
                ])
                
                check_result.recommendations.append(
                    "建議檢查不同平台的搜尋參數和過濾條件是否一致"
                )
            
            logging.info(f"跨平台一致性檢查: 發現 {len(inconsistencies)} 個不一致")
            
        except Exception as e:
            logging.error(f"跨平台一致性檢查失敗: {e}")
            check_result.warnings.append(f"跨平台一致性檢查錯誤: {str(e)}")
    
    def _check_temporal_consistency(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查時間一致性"""
        try:
            # 檢查發布日期的分佈
            for platform, jobs in platform_data.items():
                dates = []
                for job in jobs:
                    date_posted = job.get('date_posted')
                    if date_posted:
                        try:
                            if isinstance(date_posted, str):
                                job_date = datetime.strptime(date_posted, '%Y-%m-%d')
                                dates.append(job_date)
                        except Exception:
                            continue
                
                if dates:
                    # 檢查日期範圍
                    min_date = min(dates)
                    max_date = max(dates)
                    date_range = (max_date - min_date).days
                    
                    # 檢查是否有異常舊的職位
                    current_date = datetime.now()
                    very_old_jobs = [
                        date for date in dates
                        if (current_date - date).days > 180  # 超過6個月
                    ]
                    
                    if very_old_jobs:
                        check_result.warnings.append(
                            f"{platform}平台有 {len(very_old_jobs)} 個超過6個月的舊職位"
                        )
                    
                    # 檢查日期分佈是否合理
                    if date_range > 365:  # 超過一年的範圍
                        check_result.warnings.append(
                            f"{platform}平台職位日期範圍過大: {date_range} 天"
                        )
            
            logging.info("時間一致性檢查完成")
            
        except Exception as e:
            logging.error(f"時間一致性檢查失敗: {e}")
            check_result.warnings.append(f"時間一致性檢查錯誤: {str(e)}")
    
    def _check_geographic_consistency(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """檢查地理一致性"""
        try:
            # 檢查地理位置的一致性
            location_stats = defaultdict(lambda: defaultdict(int))
            
            for platform, jobs in platform_data.items():
                for job in jobs:
                    location = job.get('location', '').strip().lower()
                    if location:
                        # 標準化地理位置
                        normalized_location = self._normalize_location(location)
                        location_stats[normalized_location][platform] += 1
            
            # 檢查地理分佈是否合理
            total_locations = len(location_stats)
            if total_locations == 0:
                check_result.warnings.append("沒有找到有效的地理位置信息")
                return
            
            # 檢查是否有異常的地理分佈
            platform_location_counts = defaultdict(int)
            for location, platform_counts in location_stats.items():
                for platform, count in platform_counts.items():
                    platform_location_counts[platform] += count
            
            # 檢查平台間地理分佈差異
            if len(platform_location_counts) > 1:
                counts = list(platform_location_counts.values())
                max_count = max(counts)
                min_count = min(counts)
                
                if max_count > min_count * 3:  # 差異超過3倍
                    check_result.warnings.append(
                        f"不同平台的地理分佈差異較大: {dict(platform_location_counts)}"
                    )
            
            logging.info(f"地理一致性檢查: 發現 {total_locations} 個不同位置")
            
        except Exception as e:
            logging.error(f"地理一致性檢查失敗: {e}")
            check_result.warnings.append(f"地理一致性檢查錯誤: {str(e)}")
    
    def _normalize_location(self, location: str) -> str:
        """標準化地理位置"""
        try:
            # 移除多餘空格和標點
            normalized = location.lower().strip()
            
            # 標準化常見地名
            location_mappings = {
                'taipei': '台北',
                'taichung': '台中',
                'kaohsiung': '高雄',
                'new york': 'new york',
                'san francisco': 'san francisco',
                'los angeles': 'los angeles'
            }
            
            for key, value in location_mappings.items():
                if key in normalized:
                    return value
            
            return normalized
            
        except Exception as e:
            logging.warning(f"標準化地理位置失敗: {e}")
            return location
    
    def _execute_data_aggregation(self, check_result: IntegrityCheckResult, platform_data: Dict[str, List[Dict[str, Any]]]):
        """執行數據聚合"""
        try:
            strategy = check_result.aggregation_strategy
            
            if strategy in self.aggregation_handlers:
                aggregated_data = self.aggregation_handlers[strategy](platform_data)
                check_result.aggregated_data = aggregated_data
                
                logging.info(f"數據聚合完成: {strategy.value}, 結果數量: {len(aggregated_data) if aggregated_data else 0}")
            else:
                check_result.warnings.append(f"不支持的聚合策略: {strategy.value}")
                
        except Exception as e:
            logging.error(f"數據聚合失敗: {e}")
            check_result.issues.append(f"聚合錯誤: {str(e)}")
    
    def _aggregate_merge_all(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """合併所有結果"""
        try:
            all_jobs = []
            
            for platform, jobs in platform_data.items():
                for job in jobs:
                    # 添加平台信息
                    job_copy = job.copy()
                    job_copy['source_platform'] = platform
                    job_copy['aggregation_id'] = str(uuid.uuid4())
                    all_jobs.append(job_copy)
            
            return all_jobs
            
        except Exception as e:
            logging.error(f"合併所有結果失敗: {e}")
            return []
    
    def _aggregate_deduplicate_smart(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """智能去重聚合"""
        try:
            unique_jobs = {}
            job_groups = defaultdict(list)
            
            # 按簽名分組
            for platform, jobs in platform_data.items():
                for job in jobs:
                    signature = self._generate_job_signature(job)
                    job_copy = job.copy()
                    job_copy['source_platform'] = platform
                    job_groups[signature].append(job_copy)
            
            # 為每組選擇最佳職位
            for signature, jobs in job_groups.items():
                if len(jobs) == 1:
                    # 唯一職位
                    best_job = jobs[0]
                else:
                    # 選擇質量最高的職位
                    best_job = self._select_best_job(jobs)
                    
                    # 添加重複信息
                    best_job['duplicate_count'] = len(jobs)
                    best_job['duplicate_platforms'] = [job['source_platform'] for job in jobs]
                
                best_job['aggregation_id'] = str(uuid.uuid4())
                unique_jobs[signature] = best_job
            
            return list(unique_jobs.values())
            
        except Exception as e:
            logging.error(f"智能去重聚合失敗: {e}")
            return []
    
    def _select_best_job(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """從重複職位中選擇最佳的"""
        try:
            if not jobs:
                return {}
            
            if len(jobs) == 1:
                return jobs[0]
            
            # 計算每個職位的質量分數
            job_scores = []
            for job in jobs:
                score = self._calculate_job_quality_score(job)
                job_scores.append((score, job))
            
            # 選擇分數最高的
            job_scores.sort(key=lambda x: x[0], reverse=True)
            return job_scores[0][1]
            
        except Exception as e:
            logging.warning(f"選擇最佳職位失敗: {e}")
            return jobs[0] if jobs else {}
    
    def _calculate_job_quality_score(self, job: Dict[str, Any]) -> float:
        """計算職位質量分數"""
        try:
            score = 0.0
            
            # 字段完整性
            required_fields = ['title', 'company', 'location', 'date_posted']
            for field in required_fields:
                if field in job and job[field] and str(job[field]).strip():
                    score += 1.0
            
            # 描述長度
            description = job.get('description', '')
            if description and len(str(description)) > 100:
                score += 0.5
            
            # 薪資信息
            if job.get('salary_min') or job.get('salary_max') or job.get('salary'):
                score += 0.5
            
            # URL有效性
            job_url = job.get('job_url', '')
            if job_url and job_url.startswith('http'):
                score += 0.5
            
            return score
            
        except Exception as e:
            logging.warning(f"計算職位質量分數失敗: {e}")
            return 0.0
    
    def _aggregate_priority_based(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """基於優先級的聚合"""
        try:
            # 平台優先級（可配置）
            platform_priority = {
                'linkedin': 1,
                'indeed': 2,
                'google': 3,
                '104': 4,
                '1111': 5
            }
            
            # 按優先級排序平台
            sorted_platforms = sorted(
                platform_data.keys(),
                key=lambda p: platform_priority.get(p, 999)
            )
            
            aggregated_jobs = []
            seen_signatures = set()
            
            # 按優先級處理平台
            for platform in sorted_platforms:
                jobs = platform_data[platform]
                for job in jobs:
                    signature = self._generate_job_signature(job)
                    
                    if signature not in seen_signatures:
                        job_copy = job.copy()
                        job_copy['source_platform'] = platform
                        job_copy['aggregation_id'] = str(uuid.uuid4())
                        aggregated_jobs.append(job_copy)
                        seen_signatures.add(signature)
            
            return aggregated_jobs
            
        except Exception as e:
            logging.error(f"基於優先級的聚合失敗: {e}")
            return []
    
    def _aggregate_quality_weighted(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """質量加權聚合"""
        try:
            job_groups = defaultdict(list)
            
            # 按簽名分組並計算質量分數
            for platform, jobs in platform_data.items():
                for job in jobs:
                    signature = self._generate_job_signature(job)
                    quality_score = self._calculate_job_quality_score(job)
                    
                    job_copy = job.copy()
                    job_copy['source_platform'] = platform
                    job_copy['quality_score'] = quality_score
                    
                    job_groups[signature].append(job_copy)
            
            # 為每組選擇質量最高的職位
            aggregated_jobs = []
            for signature, jobs in job_groups.items():
                # 按質量分數排序
                jobs.sort(key=lambda j: j.get('quality_score', 0), reverse=True)
                best_job = jobs[0]
                
                # 添加聚合信息
                best_job['aggregation_id'] = str(uuid.uuid4())
                if len(jobs) > 1:
                    best_job['alternative_sources'] = [
                        {'platform': job['source_platform'], 'quality_score': job.get('quality_score', 0)}
                        for job in jobs[1:]
                    ]
                
                aggregated_jobs.append(best_job)
            
            return aggregated_jobs
            
        except Exception as e:
            logging.error(f"質量加權聚合失敗: {e}")
            return []
    
    def _aggregate_consensus_based(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """基於共識的聚合"""
        try:
            job_groups = defaultdict(list)
            
            # 按簽名分組
            for platform, jobs in platform_data.items():
                for job in jobs:
                    signature = self._generate_job_signature(job)
                    job_copy = job.copy()
                    job_copy['source_platform'] = platform
                    job_groups[signature].append(job_copy)
            
            # 基於共識合併字段
            aggregated_jobs = []
            for signature, jobs in job_groups.items():
                if len(jobs) == 1:
                    # 單一來源
                    consensus_job = jobs[0]
                else:
                    # 多來源共識
                    consensus_job = self._build_consensus_job(jobs)
                
                consensus_job['aggregation_id'] = str(uuid.uuid4())
                aggregated_jobs.append(consensus_job)
            
            return aggregated_jobs
            
        except Exception as e:
            logging.error(f"基於共識的聚合失敗: {e}")
            return []
    
    def _build_consensus_job(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """構建共識職位"""
        try:
            if not jobs:
                return {}
            
            consensus_job = {}
            all_fields = set()
            
            # 收集所有字段
            for job in jobs:
                all_fields.update(job.keys())
            
            # 為每個字段建立共識
            for field in all_fields:
                if field == 'source_platform':
                    # 特殊處理平台字段
                    consensus_job['source_platforms'] = [job.get(field) for job in jobs if job.get(field)]
                    continue
                
                values = [job.get(field) for job in jobs if job.get(field) is not None]
                
                if not values:
                    continue
                
                # 根據字段類型選擇共識值
                if isinstance(values[0], str):
                    # 字符串字段：選擇最長的非空值
                    non_empty_values = [v for v in values if str(v).strip()]
                    if non_empty_values:
                        consensus_job[field] = max(non_empty_values, key=len)
                elif isinstance(values[0], (int, float)):
                    # 數值字段：取平均值
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    if numeric_values:
                        consensus_job[field] = statistics.mean(numeric_values)
                else:
                    # 其他類型：取第一個值
                    consensus_job[field] = values[0]
            
            # 添加共識元數據
            consensus_job['consensus_count'] = len(jobs)
            consensus_job['consensus_confidence'] = len(jobs) / len(all_fields) if all_fields else 0
            
            return consensus_job
            
        except Exception as e:
            logging.warning(f"構建共識職位失敗: {e}")
            return jobs[0] if jobs else {}
    
    def _aggregate_platform_specific(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """平台特定聚合"""
        try:
            aggregated_jobs = []
            
            # 為每個平台單獨處理
            for platform, jobs in platform_data.items():
                platform_jobs = []
                seen_signatures = set()
                
                for job in jobs:
                    signature = self._generate_job_signature(job)
                    
                    if signature not in seen_signatures:
                        job_copy = job.copy()
                        job_copy['source_platform'] = platform
                        job_copy['aggregation_id'] = str(uuid.uuid4())
                        platform_jobs.append(job_copy)
                        seen_signatures.add(signature)
                
                # 添加平台標識
                for job in platform_jobs:
                    job['platform_group'] = platform
                
                aggregated_jobs.extend(platform_jobs)
            
            return aggregated_jobs
            
        except Exception as e:
            logging.error(f"平台特定聚合失敗: {e}")
            return []
    
    def _calculate_final_quality(self, check_result: IntegrityCheckResult):
        """計算最終質量分數"""
        try:
            if not check_result.platform_summaries:
                return
            
            # 收集所有平台的質量指標
            quality_metrics = []
            for summary in check_result.platform_summaries.values():
                quality_metrics.append(summary.data_quality)
            
            if not quality_metrics:
                return
            
            # 計算加權平均質量
            total_jobs = sum(m.total_records for m in quality_metrics)
            if total_jobs == 0:
                return
            
            weighted_scores = {
                'completeness_score': 0.0,
                'accuracy_score': 0.0,
                'consistency_score': 0.0,
                'uniqueness_score': 0.0,
                'validity_score': 0.0,
                'timeliness_score': 0.0
            }
            
            for metrics in quality_metrics:
                weight = metrics.total_records / total_jobs
                weighted_scores['completeness_score'] += metrics.completeness_score * weight
                weighted_scores['accuracy_score'] += metrics.accuracy_score * weight
                weighted_scores['consistency_score'] += metrics.consistency_score * weight
                weighted_scores['uniqueness_score'] += metrics.uniqueness_score * weight
                weighted_scores['validity_score'] += metrics.validity_score * weight
                weighted_scores['timeliness_score'] += metrics.timeliness_score * weight
            
            # 創建最終質量指標
            final_quality = DataQualityMetrics(
                completeness_score=weighted_scores['completeness_score'],
                accuracy_score=weighted_scores['accuracy_score'],
                consistency_score=weighted_scores['consistency_score'],
                uniqueness_score=weighted_scores['uniqueness_score'],
                validity_score=weighted_scores['validity_score'],
                timeliness_score=weighted_scores['timeliness_score'],
                total_records=total_jobs,
                valid_records=sum(m.valid_records for m in quality_metrics),
                duplicate_records=sum(m.duplicate_records for m in quality_metrics)
            )
            
            # 計算總體分數
            scores = [
                final_quality.completeness_score,
                final_quality.accuracy_score,
                final_quality.consistency_score,
                final_quality.uniqueness_score,
                final_quality.validity_score,
                final_quality.timeliness_score
            ]
            final_quality.overall_score = statistics.mean([s for s in scores if s > 0])
            
            # 確定質量等級
            if final_quality.overall_score >= 0.95:
                final_quality.quality_level = DataQualityLevel.EXCELLENT
            elif final_quality.overall_score >= 0.85:
                final_quality.quality_level = DataQualityLevel.GOOD
            elif final_quality.overall_score >= 0.70:
                final_quality.quality_level = DataQualityLevel.FAIR
            elif final_quality.overall_score >= 0.50:
                final_quality.quality_level = DataQualityLevel.POOR
            else:
                final_quality.quality_level = DataQualityLevel.CRITICAL
            
            check_result.final_quality = final_quality
            
            # 檢查是否通過質量閾值
            if final_quality.overall_score < self.config.min_overall_quality:
                check_result.issues.append(
                    f"總體數據質量不足: {final_quality.overall_score:.2%} < {self.config.min_overall_quality:.2%}"
                )
                check_result.passed = False
            else:
                check_result.passed = True
            
            # 計算檢查分數
            check_result.score = final_quality.overall_score
            
            logging.info(f"最終質量計算完成: {final_quality.overall_score:.2%} ({final_quality.quality_level.value})")
            
        except Exception as e:
            logging.error(f"計算最終質量失敗: {e}")
            check_result.warnings.append(f"質量計算錯誤: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取檢查器統計信息"""
        try:
            return {
                'total_checks': self.stats['total_checks'],
                'successful_checks': self.stats['successful_checks'],
                'failed_checks': self.stats['failed_checks'],
                'average_check_time': self.stats['total_check_time'] / max(self.stats['total_checks'], 1),
                'total_jobs_processed': self.stats['total_jobs_processed'],
                'total_platforms_checked': self.stats['total_platforms_checked'],
                'average_quality_score': self.stats['total_quality_score'] / max(self.stats['successful_checks'], 1),
                'cache_hit_rate': self.stats['cache_hits'] / max(self.stats['cache_hits'] + self.stats['cache_misses'], 1),
                'uptime': time.time() - self.start_time,
                'memory_usage': self._get_memory_usage(),
                'redis_connected': self.redis_client is not None and self._check_redis_connection()
            }
        except Exception as e:
            logging.error(f"獲取統計信息失敗: {e}")
            return {}
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """獲取內存使用情況"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # 物理內存
                'vms_mb': memory_info.vms / 1024 / 1024,  # 虛擬內存
                'percent': process.memory_percent()        # 內存使用百分比
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _check_redis_connection(self) -> bool:
        """檢查Redis連接狀態"""
        try:
            if not self.redis_client:
                return False
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def export_results(self, check_id: str, file_path: str) -> bool:
        """導出檢查結果到文件"""
        try:
            result = self.get_check_result(check_id)
            if not result:
                logging.warning(f"檢查結果不存在: {check_id}")
                return False
            
            # 轉換為可序列化的格式
            export_data = {
                'check_id': result.check_id,
                'job_id': result.job_id,
                'timestamp': result.timestamp.isoformat(),
                'duration': result.duration,
                'passed': result.passed,
                'score': result.score,
                'aggregation_strategy': result.aggregation_strategy.value,
                'platform_summaries': {
                    platform: {
                        'platform': summary.platform,
                        'total_jobs': summary.total_jobs,
                        'valid_jobs': summary.valid_jobs,
                        'duplicate_jobs': summary.duplicate_jobs,
                        'missing_fields': summary.missing_fields,
                        'data_quality': {
                            'completeness_score': summary.data_quality.completeness_score,
                            'accuracy_score': summary.data_quality.accuracy_score,
                            'consistency_score': summary.data_quality.consistency_score,
                            'uniqueness_score': summary.data_quality.uniqueness_score,
                            'validity_score': summary.data_quality.validity_score,
                            'timeliness_score': summary.data_quality.timeliness_score,
                            'overall_score': summary.data_quality.overall_score,
                            'quality_level': summary.data_quality.quality_level.value,
                            'total_records': summary.data_quality.total_records,
                            'valid_records': summary.data_quality.valid_records,
                            'duplicate_records': summary.data_quality.duplicate_records
                        }
                    }
                    for platform, summary in result.platform_summaries.items()
                },
                'issues': result.issues,
                'warnings': result.warnings,
                'recommendations': result.recommendations,
                'final_quality': {
                    'completeness_score': result.final_quality.completeness_score,
                    'accuracy_score': result.final_quality.accuracy_score,
                    'consistency_score': result.final_quality.consistency_score,
                    'uniqueness_score': result.final_quality.uniqueness_score,
                    'validity_score': result.final_quality.validity_score,
                    'timeliness_score': result.final_quality.timeliness_score,
                    'overall_score': result.final_quality.overall_score,
                    'quality_level': result.final_quality.quality_level.value,
                    'total_records': result.final_quality.total_records,
                    'valid_records': result.final_quality.valid_records,
                    'duplicate_records': result.final_quality.duplicate_records
                } if result.final_quality else None,
                'aggregated_data_count': len(result.aggregated_data) if result.aggregated_data else 0
            }
            
            # 寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"檢查結果已導出到: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"導出檢查結果失敗: {e}")
            return False
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """清理舊的檢查結果"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            removed_count = 0
            
            # 清理內存緩存
            to_remove = []
            for check_id, result in self.results_cache.items():
                if result.timestamp < cutoff_time:
                    to_remove.append(check_id)
            
            for check_id in to_remove:
                del self.results_cache[check_id]
                removed_count += 1
            
            # 清理Redis緩存
            if self.redis_client:
                try:
                    pattern = f"{self.cache_prefix}:result:*"
                    keys = self.redis_client.keys(pattern)
                    
                    for key in keys:
                        try:
                            result_data = self.redis_client.get(key)
                            if result_data:
                                result_dict = json.loads(result_data)
                                timestamp = datetime.fromisoformat(result_dict.get('timestamp', ''))
                                
                                if timestamp < cutoff_time:
                                    self.redis_client.delete(key)
                                    removed_count += 1
                        except Exception as e:
                            logging.warning(f"清理Redis鍵失敗 {key}: {e}")
                            
                except Exception as e:
                    logging.warning(f"清理Redis緩存失敗: {e}")
            
            logging.info(f"清理完成: 移除了 {removed_count} 個舊結果")
            
        except Exception as e:
            logging.error(f"清理舊結果失敗: {e}")
    
    def shutdown(self):
        """關閉檢查器"""
        try:
            logging.info("正在關閉數據完整性檢查器...")
            
            # 停止背景任務
            self.running = False
            
            # 等待當前檢查完成
            if hasattr(self, 'current_checks'):
                while self.current_checks:
                    time.sleep(0.1)
            
            # 關閉線程池
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            # 關閉Redis連接
            if self.redis_client:
                try:
                    self.redis_client.close()
                except Exception as e:
                    logging.warning(f"關閉Redis連接失敗: {e}")
            
            # 清理緩存
            self.results_cache.clear()
            
            logging.info("數據完整性檢查器已關閉")
            
        except Exception as e:
            logging.error(f"關閉檢查器失敗: {e}")


# 測試用例
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_data_integrity_checker():
        """測試增強版數據完整性檢查器"""
        print("=== 增強版數據完整性檢查器測試 ===")
        
        # 創建檢查器
        config = IntegrityCheckConfig(
            required_platforms=['linkedin', 'indeed', 'google'],
            min_platform_coverage=0.8,
            max_duplicate_rate=0.1,
            min_overall_quality=0.7,
            enable_cross_platform_validation=True,
            enable_temporal_validation=True,
            enable_geographic_validation=True
        )
        
        checker = EnhancedDataIntegrityChecker(config)
        
        try:
            # 模擬平台數據
            test_data = {
                'linkedin': [
                    {
                        'title': 'Software Engineer',
                        'company': 'Tech Corp',
                        'location': 'San Francisco',
                        'date_posted': '2024-01-15',
                        'description': 'Great opportunity for software development',
                        'salary_min': 100000,
                        'salary_max': 150000,
                        'job_url': 'https://linkedin.com/jobs/123'
                    },
                    {
                        'title': 'Data Scientist',
                        'company': 'Data Inc',
                        'location': 'New York',
                        'date_posted': '2024-01-14',
                        'description': 'Exciting data science role',
                        'salary': 120000,
                        'job_url': 'https://linkedin.com/jobs/124'
                    }
                ],
                'indeed': [
                    {
                        'title': 'Software Engineer',
                        'company': 'Tech Corp',
                        'location': 'San Francisco',
                        'date_posted': '2024-01-15',
                        'description': 'Great opportunity for software development',
                        'salary_min': 95000,
                        'salary_max': 145000,
                        'job_url': 'https://indeed.com/jobs/456'
                    },
                    {
                        'title': 'Frontend Developer',
                        'company': 'Web Solutions',
                        'location': 'Los Angeles',
                        'date_posted': '2024-01-13',
                        'description': 'Frontend development position',
                        'job_url': 'https://indeed.com/jobs/457'
                    }
                ],
                'google': [
                    {
                        'title': 'Backend Developer',
                        'company': 'Cloud Services',
                        'location': 'Seattle',
                        'date_posted': '2024-01-12',
                        'description': 'Backend development role',
                        'salary': 110000,
                        'job_url': 'https://google.com/jobs/789'
                    }
                ]
            }
            
            # 提交完整性檢查
            print("\n1. 提交完整性檢查...")
            check_id = await checker.submit_integrity_check(
                job_id='test_job_001',
                platform_data=test_data,
                aggregation_strategy=AggregationStrategy.DEDUPLICATE_SMART
            )
            print(f"檢查ID: {check_id}")
            
            # 等待檢查完成
            print("\n2. 等待檢查完成...")
            await asyncio.sleep(2)
            
            # 獲取檢查結果
            print("\n3. 獲取檢查結果...")
            result = checker.get_check_result(check_id)
            
            if result:
                print(f"檢查通過: {result.passed}")
                print(f"總體分數: {result.score:.2%}")
                print(f"聚合策略: {result.aggregation_strategy.value}")
                print(f"處理時間: {result.duration:.2f}秒")
                
                if result.final_quality:
                    print(f"\n最終質量:")
                    print(f"  - 完整性: {result.final_quality.completeness_score:.2%}")
                    print(f"  - 準確性: {result.final_quality.accuracy_score:.2%}")
                    print(f"  - 一致性: {result.final_quality.consistency_score:.2%}")
                    print(f"  - 唯一性: {result.final_quality.uniqueness_score:.2%}")
                    print(f"  - 有效性: {result.final_quality.validity_score:.2%}")
                    print(f"  - 及時性: {result.final_quality.timeliness_score:.2%}")
                    print(f"  - 質量等級: {result.final_quality.quality_level.value}")
                
                print(f"\n平台摘要:")
                for platform, summary in result.platform_summaries.items():
                    print(f"  {platform}: {summary.total_jobs} 個職位, 質量分數: {summary.data_quality.overall_score:.2%}")
                
                if result.issues:
                    print(f"\n問題: {len(result.issues)} 個")
                    for issue in result.issues[:3]:  # 只顯示前3個
                        print(f"  - {issue}")
                
                if result.warnings:
                    print(f"\n警告: {len(result.warnings)} 個")
                    for warning in result.warnings[:3]:  # 只顯示前3個
                        print(f"  - {warning}")
                
                if result.aggregated_data:
                    print(f"\n聚合數據: {len(result.aggregated_data)} 個職位")
            
            # 獲取統計信息
            print("\n4. 獲取統計信息...")
            stats = checker.get_statistics()
            print(f"總檢查次數: {stats.get('total_checks', 0)}")
            print(f"成功檢查: {stats.get('successful_checks', 0)}")
            print(f"平均檢查時間: {stats.get('average_check_time', 0):.2f}秒")
            print(f"平均質量分數: {stats.get('average_quality_score', 0):.2%}")
            print(f"緩存命中率: {stats.get('cache_hit_rate', 0):.2%}")
            print(f"運行時間: {stats.get('uptime', 0):.1f}秒")
            
            # 導出結果
            print("\n5. 導出檢查結果...")
            export_path = f"integrity_check_result_{check_id}.json"
            if checker.export_results(check_id, export_path):
                print(f"結果已導出到: {export_path}")
            
            # 測試不同聚合策略
            print("\n6. 測試不同聚合策略...")
            strategies = [
                AggregationStrategy.MERGE_ALL,
                AggregationStrategy.PRIORITY_BASED,
                AggregationStrategy.QUALITY_WEIGHTED,
                AggregationStrategy.CONSENSUS_BASED
            ]
            
            for strategy in strategies:
                check_id = await checker.submit_integrity_check(
                    job_id=f'test_job_{strategy.value}',
                    platform_data=test_data,
                    aggregation_strategy=strategy
                )
                await asyncio.sleep(1)
                result = checker.get_check_result(check_id)
                if result and result.aggregated_data:
                    print(f"  {strategy.value}: {len(result.aggregated_data)} 個聚合職位")
            
            print("\n=== 測試完成 ===")
            
        except Exception as e:
            print(f"測試失敗: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理
            checker.shutdown()
    
    # 運行測試
    asyncio.run(test_enhanced_data_integrity_checker())