#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台智能路由系統 - 整合API

這個模塊提供了一個統一的API接口，整合了所有多平台路由系統的組件：
- 多平台調度器
- 任務追蹤服務
- 狀態同步協調器
- 錯誤處理管理器
- 數據完整性檢查器
- 異常通知服務

作者: Assistant
創建時間: 2024-01-15
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

# 導入所有組件
try:
    from multi_platform_config import MultiPlatformConfig
    from multi_platform_scheduler import MultiPlatformScheduler, JobRequest, JobResult
    from task_tracking_service import TaskTrackingService, TaskEvent, TaskEventType
    from sync_coordinator import SyncCoordinator, SyncRequest, SyncMode
    from error_handling_manager import ErrorHandlingManager, ErrorInfo, ErrorSeverity
    from enhanced_data_integrity_checker import EnhancedDataIntegrityChecker, IntegrityCheckConfig, AggregationStrategy
    from notification_service import NotificationService, NotificationChannel, NotificationPriority
except ImportError as e:
    logging.warning(f"某些組件導入失敗: {e}")
    # 提供基本的替代實現
    class JobRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class JobResult:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API狀態枚舉"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class JobStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class APIConfig:
    """API配置"""
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 線程池配置
    max_workers: int = 10
    
    # 超時配置
    job_timeout: int = 300  # 5分鐘
    health_check_interval: int = 30  # 30秒
    
    # 緩存配置
    cache_ttl: int = 3600  # 1小時
    max_cache_size: int = 1000
    
    # 通知配置
    enable_notifications: bool = True
    notification_channels: List[str] = None
    
    # 數據完整性配置
    enable_integrity_check: bool = True
    min_platform_coverage: float = 0.8
    max_duplicate_rate: float = 0.1
    min_overall_quality: float = 0.7
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ['email', 'webhook']


@dataclass
class JobSubmissionRequest:
    """任務提交請求"""
    job_id: str
    search_params: Dict[str, Any]
    target_region: str
    priority: str = "medium"
    timeout: Optional[int] = None
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # 數據完整性選項
    enable_integrity_check: bool = True
    aggregation_strategy: str = "deduplicate_smart"
    required_platforms: Optional[List[str]] = None


@dataclass
class JobStatusResponse:
    """任務狀態響應"""
    job_id: str
    status: str
    progress: float
    platforms: Dict[str, str]  # platform -> status
    results_count: int
    error_count: int
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None
    integrity_check_id: Optional[str] = None
    integrity_passed: Optional[bool] = None
    quality_score: Optional[float] = None


@dataclass
class SystemHealthResponse:
    """系統健康狀態響應"""
    status: str
    uptime: float
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    error_rate: float
    average_job_time: float
    platform_health: Dict[str, bool]
    redis_connected: bool
    memory_usage: Dict[str, float]
    last_health_check: datetime


class MultiPlatformIntegrationAPI:
    """多平台智能路由系統整合API"""
    
    def __init__(self, config: APIConfig):
        """初始化API"""
        self.config = config
        self.status = APIStatus.INITIALIZING
        self.start_time = time.time()
        
        # 組件實例
        self.scheduler: Optional[MultiPlatformScheduler] = None
        self.task_tracker: Optional[TaskTrackingService] = None
        self.sync_coordinator: Optional[SyncCoordinator] = None
        self.error_manager: Optional[ErrorHandlingManager] = None
        self.integrity_checker: Optional[EnhancedDataIntegrityChecker] = None
        self.notification_service: Optional[NotificationService] = None
        
        # 內部狀態
        self.jobs: Dict[str, Dict[str, Any]] = {}  # job_id -> job_info
        self.job_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        
        # 統計信息
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_processing_time': 0.0,
            'error_count': 0,
            'last_error': None
        }
        
        # 健康檢查
        self.health_check_task: Optional[asyncio.Task] = None
        self.running = False
        
        logger.info("多平台整合API初始化完成")
    
    async def initialize(self) -> bool:
        """初始化所有組件"""
        try:
            logger.info("正在初始化多平台整合API...")
            
            # 初始化配置
            platform_config = MultiPlatformConfig()
            
            # 初始化調度器
            try:
                self.scheduler = MultiPlatformScheduler(platform_config)
                await self.scheduler.initialize()
                logger.info("多平台調度器初始化成功")
            except Exception as e:
                logger.error(f"調度器初始化失敗: {e}")
                return False
            
            # 初始化任務追蹤服務
            try:
                self.task_tracker = TaskTrackingService(
                    redis_host=self.config.redis_host,
                    redis_port=self.config.redis_port,
                    redis_db=self.config.redis_db
                )
                await self.task_tracker.initialize()
                logger.info("任務追蹤服務初始化成功")
            except Exception as e:
                logger.error(f"任務追蹤服務初始化失敗: {e}")
                return False
            
            # 初始化狀態同步協調器
            try:
                self.sync_coordinator = SyncCoordinator(
                    redis_host=self.config.redis_host,
                    redis_port=self.config.redis_port,
                    redis_db=self.config.redis_db
                )
                await self.sync_coordinator.start()
                logger.info("狀態同步協調器初始化成功")
            except Exception as e:
                logger.error(f"狀態同步協調器初始化失敗: {e}")
                return False
            
            # 初始化錯誤處理管理器
            try:
                self.error_manager = ErrorHandlingManager(
                    redis_host=self.config.redis_host,
                    redis_port=self.config.redis_port,
                    redis_db=self.config.redis_db
                )
                logger.info("錯誤處理管理器初始化成功")
            except Exception as e:
                logger.error(f"錯誤處理管理器初始化失敗: {e}")
                return False
            
            # 初始化數據完整性檢查器
            if self.config.enable_integrity_check:
                try:
                    integrity_config = IntegrityCheckConfig(
                        min_platform_coverage=self.config.min_platform_coverage,
                        max_duplicate_rate=self.config.max_duplicate_rate,
                        min_overall_quality=self.config.min_overall_quality
                    )
                    self.integrity_checker = EnhancedDataIntegrityChecker(integrity_config)
                    logger.info("數據完整性檢查器初始化成功")
                except Exception as e:
                    logger.error(f"數據完整性檢查器初始化失敗: {e}")
                    return False
            
            # 初始化通知服務
            if self.config.enable_notifications:
                try:
                    self.notification_service = NotificationService(
                        redis_host=self.config.redis_host,
                        redis_port=self.config.redis_port,
                        redis_db=self.config.redis_db
                    )
                    logger.info("通知服務初始化成功")
                except Exception as e:
                    logger.error(f"通知服務初始化失敗: {e}")
                    return False
            
            # 設置事件監聽器
            self._setup_event_listeners()
            
            # 啟動健康檢查
            self.running = True
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.status = APIStatus.RUNNING
            logger.info("多平台整合API初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"API初始化失敗: {e}")
            self.status = APIStatus.ERROR
            return False
    
    def _setup_event_listeners(self):
        """設置事件監聽器"""
        try:
            if self.task_tracker:
                # 監聽任務事件
                self.task_tracker.add_event_listener(
                    TaskEventType.TASK_COMPLETED,
                    self._on_task_completed
                )
                self.task_tracker.add_event_listener(
                    TaskEventType.TASK_FAILED,
                    self._on_task_failed
                )
                self.task_tracker.add_event_listener(
                    TaskEventType.PLATFORM_ERROR,
                    self._on_platform_error
                )
            
            logger.info("事件監聽器設置完成")
            
        except Exception as e:
            logger.error(f"設置事件監聽器失敗: {e}")
    
    async def _on_task_completed(self, event: TaskEvent):
        """任務完成事件處理"""
        try:
            job_id = event.job_id
            
            with self.job_lock:
                if job_id in self.jobs:
                    self.jobs[job_id]['status'] = JobStatus.COMPLETED.value
                    self.jobs[job_id]['updated_at'] = datetime.now()
                    self.stats['completed_jobs'] += 1
            
            # 發送完成通知
            if self.notification_service:
                await self.notification_service.send_task_completion_notification(
                    job_id=job_id,
                    status="completed",
                    results_count=event.data.get('results_count', 0)
                )
            
            logger.info(f"任務完成: {job_id}")
            
        except Exception as e:
            logger.error(f"處理任務完成事件失敗: {e}")
    
    async def _on_task_failed(self, event: TaskEvent):
        """任務失敗事件處理"""
        try:
            job_id = event.job_id
            error_message = event.data.get('error', 'Unknown error')
            
            with self.job_lock:
                if job_id in self.jobs:
                    self.jobs[job_id]['status'] = JobStatus.FAILED.value
                    self.jobs[job_id]['error'] = error_message
                    self.jobs[job_id]['updated_at'] = datetime.now()
                    self.stats['failed_jobs'] += 1
                    self.stats['error_count'] += 1
                    self.stats['last_error'] = error_message
            
            # 處理錯誤
            if self.error_manager:
                error_info = ErrorInfo(
                    error_id=str(uuid.uuid4()),
                    job_id=job_id,
                    platform="multi_platform",
                    error_type="task_failure",
                    severity=ErrorSeverity.HIGH,
                    message=error_message,
                    timestamp=datetime.now()
                )
                await self.error_manager.handle_error(error_info)
            
            # 發送錯誤通知
            if self.notification_service:
                await self.notification_service.send_error_notification(
                    error_type="task_failure",
                    message=error_message,
                    job_id=job_id,
                    severity="high"
                )
            
            logger.error(f"任務失敗: {job_id}, 錯誤: {error_message}")
            
        except Exception as e:
            logger.error(f"處理任務失敗事件失敗: {e}")
    
    async def _on_platform_error(self, event: TaskEvent):
        """平台錯誤事件處理"""
        try:
            platform = event.data.get('platform', 'unknown')
            error_message = event.data.get('error', 'Unknown platform error')
            
            # 處理平台錯誤
            if self.error_manager:
                error_info = ErrorInfo(
                    error_id=str(uuid.uuid4()),
                    job_id=event.job_id,
                    platform=platform,
                    error_type="platform_error",
                    severity=ErrorSeverity.MEDIUM,
                    message=error_message,
                    timestamp=datetime.now()
                )
                await self.error_manager.handle_error(error_info)
            
            logger.warning(f"平台錯誤: {platform}, 錯誤: {error_message}")
            
        except Exception as e:
            logger.error(f"處理平台錯誤事件失敗: {e}")
    
    async def submit_job(self, request: JobSubmissionRequest) -> Dict[str, Any]:
        """提交任務"""
        try:
            if self.status != APIStatus.RUNNING:
                raise Exception(f"API狀態不正確: {self.status.value}")
            
            job_id = request.job_id
            
            # 記錄任務信息
            with self.job_lock:
                self.jobs[job_id] = {
                    'job_id': job_id,
                    'status': JobStatus.PENDING.value,
                    'search_params': request.search_params,
                    'target_region': request.target_region,
                    'priority': request.priority,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'platforms': {},
                    'results_count': 0,
                    'error_count': 0,
                    'integrity_check_id': None,
                    'metadata': request.metadata or {}
                }
                self.stats['total_jobs'] += 1
            
            # 創建任務追蹤
            if self.task_tracker:
                await self.task_tracker.create_task(
                    job_id=job_id,
                    platforms=request.required_platforms or [],
                    metadata=request.metadata or {}
                )
            
            # 提交到調度器
            if self.scheduler:
                job_request = JobRequest(
                    job_id=job_id,
                    search_params=request.search_params,
                    target_region=request.target_region,
                    priority=request.priority,
                    timeout=request.timeout or self.config.job_timeout,
                    callback_url=request.callback_url,
                    metadata=request.metadata
                )
                
                # 異步提交任務
                asyncio.create_task(self._process_job(job_request, request))
            
            logger.info(f"任務已提交: {job_id}")
            
            return {
                'job_id': job_id,
                'status': 'submitted',
                'message': '任務已成功提交',
                'estimated_completion': datetime.now() + timedelta(minutes=5)
            }
            
        except Exception as e:
            logger.error(f"提交任務失敗: {e}")
            raise
    
    async def _process_job(self, job_request: JobRequest, submission_request: JobSubmissionRequest):
        """處理任務"""
        job_id = job_request.job_id
        start_time = time.time()
        
        try:
            # 更新任務狀態
            with self.job_lock:
                if job_id in self.jobs:
                    self.jobs[job_id]['status'] = JobStatus.RUNNING.value
                    self.jobs[job_id]['updated_at'] = datetime.now()
            
            # 啟動任務追蹤
            if self.task_tracker:
                await self.task_tracker.start_task(job_id)
            
            # 執行調度
            if self.scheduler:
                result = await self.scheduler.schedule_job(job_request)
                
                # 收集結果
                platform_data = {}
                total_results = 0
                
                if result and result.platform_results:
                    for platform, platform_result in result.platform_results.items():
                        if platform_result.success and platform_result.data:
                            platform_data[platform] = platform_result.data
                            total_results += len(platform_result.data)
                        
                        # 更新平台狀態
                        with self.job_lock:
                            if job_id in self.jobs:
                                self.jobs[job_id]['platforms'][platform] = (
                                    'completed' if platform_result.success else 'failed'
                                )
                
                # 執行數據完整性檢查
                integrity_check_id = None
                integrity_passed = None
                quality_score = None
                
                if (self.integrity_checker and 
                    submission_request.enable_integrity_check and 
                    platform_data):
                    
                    try:
                        # 確定聚合策略
                        strategy_map = {
                            'merge_all': AggregationStrategy.MERGE_ALL,
                            'deduplicate_smart': AggregationStrategy.DEDUPLICATE_SMART,
                            'priority_based': AggregationStrategy.PRIORITY_BASED,
                            'quality_weighted': AggregationStrategy.QUALITY_WEIGHTED,
                            'consensus_based': AggregationStrategy.CONSENSUS_BASED
                        }
                        
                        aggregation_strategy = strategy_map.get(
                            submission_request.aggregation_strategy,
                            AggregationStrategy.DEDUPLICATE_SMART
                        )
                        
                        integrity_check_id = await self.integrity_checker.submit_integrity_check(
                            job_id=job_id,
                            platform_data=platform_data,
                            aggregation_strategy=aggregation_strategy
                        )
                        
                        # 等待檢查完成
                        await asyncio.sleep(1)
                        
                        check_result = self.integrity_checker.get_check_result(integrity_check_id)
                        if check_result:
                            integrity_passed = check_result.passed
                            quality_score = check_result.score
                        
                    except Exception as e:
                        logger.warning(f"數據完整性檢查失敗: {e}")
                
                # 更新任務結果
                with self.job_lock:
                    if job_id in self.jobs:
                        self.jobs[job_id]['status'] = JobStatus.COMPLETED.value
                        self.jobs[job_id]['results_count'] = total_results
                        self.jobs[job_id]['integrity_check_id'] = integrity_check_id
                        self.jobs[job_id]['integrity_passed'] = integrity_passed
                        self.jobs[job_id]['quality_score'] = quality_score
                        self.jobs[job_id]['updated_at'] = datetime.now()
                
                # 完成任務追蹤
                if self.task_tracker:
                    await self.task_tracker.complete_task(
                        job_id=job_id,
                        results={'total_results': total_results, 'platforms': len(platform_data)}
                    )
                
                # 更新統計
                processing_time = time.time() - start_time
                self.stats['total_processing_time'] += processing_time
                
                logger.info(f"任務處理完成: {job_id}, 結果數量: {total_results}, 處理時間: {processing_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"處理任務失敗 {job_id}: {e}")
            
            # 更新失敗狀態
            with self.job_lock:
                if job_id in self.jobs:
                    self.jobs[job_id]['status'] = JobStatus.FAILED.value
                    self.jobs[job_id]['error'] = str(e)
                    self.jobs[job_id]['updated_at'] = datetime.now()
            
            # 失敗任務追蹤
            if self.task_tracker:
                await self.task_tracker.fail_task(job_id, str(e))
            
            # 處理錯誤
            if self.error_manager:
                error_info = ErrorInfo(
                    error_id=str(uuid.uuid4()),
                    job_id=job_id,
                    platform="scheduler",
                    error_type="job_processing_error",
                    severity=ErrorSeverity.HIGH,
                    message=str(e),
                    timestamp=datetime.now()
                )
                await self.error_manager.handle_error(error_info)
    
    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """獲取任務狀態"""
        try:
            with self.job_lock:
                if job_id not in self.jobs:
                    return None
                
                job_info = self.jobs[job_id]
                
                return JobStatusResponse(
                    job_id=job_id,
                    status=job_info['status'],
                    progress=self._calculate_job_progress(job_info),
                    platforms=job_info.get('platforms', {}),
                    results_count=job_info.get('results_count', 0),
                    error_count=job_info.get('error_count', 0),
                    created_at=job_info['created_at'],
                    updated_at=job_info['updated_at'],
                    estimated_completion=self._estimate_completion_time(job_info),
                    integrity_check_id=job_info.get('integrity_check_id'),
                    integrity_passed=job_info.get('integrity_passed'),
                    quality_score=job_info.get('quality_score')
                )
                
        except Exception as e:
            logger.error(f"獲取任務狀態失敗: {e}")
            return None
    
    def _calculate_job_progress(self, job_info: Dict[str, Any]) -> float:
        """計算任務進度"""
        try:
            status = job_info['status']
            
            if status == JobStatus.PENDING.value:
                return 0.0
            elif status == JobStatus.RUNNING.value:
                # 基於平台完成情況計算進度
                platforms = job_info.get('platforms', {})
                if not platforms:
                    return 0.1  # 剛開始
                
                completed_platforms = sum(1 for status in platforms.values() 
                                         if status in ['completed', 'failed'])
                return min(0.9, completed_platforms / len(platforms) * 0.8 + 0.1)
            elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                return 1.0
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _estimate_completion_time(self, job_info: Dict[str, Any]) -> Optional[datetime]:
        """估算完成時間"""
        try:
            status = job_info['status']
            
            if status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                return job_info['updated_at']
            
            # 基於歷史數據估算
            if self.stats['completed_jobs'] > 0:
                avg_time = self.stats['total_processing_time'] / self.stats['completed_jobs']
                elapsed = (datetime.now() - job_info['created_at']).total_seconds()
                remaining = max(0, avg_time - elapsed)
                return datetime.now() + timedelta(seconds=remaining)
            
            # 默認估算
            return datetime.now() + timedelta(minutes=5)
            
        except Exception:
            return None
    
    def list_jobs(self, status_filter: Optional[str] = None, limit: int = 100) -> List[JobStatusResponse]:
        """列出任務"""
        try:
            with self.job_lock:
                jobs = []
                
                for job_id, job_info in list(self.jobs.items())[-limit:]:
                    if status_filter and job_info['status'] != status_filter:
                        continue
                    
                    job_status = JobStatusResponse(
                        job_id=job_id,
                        status=job_info['status'],
                        progress=self._calculate_job_progress(job_info),
                        platforms=job_info.get('platforms', {}),
                        results_count=job_info.get('results_count', 0),
                        error_count=job_info.get('error_count', 0),
                        created_at=job_info['created_at'],
                        updated_at=job_info['updated_at'],
                        estimated_completion=self._estimate_completion_time(job_info),
                        integrity_check_id=job_info.get('integrity_check_id'),
                        integrity_passed=job_info.get('integrity_passed'),
                        quality_score=job_info.get('quality_score')
                    )
                    jobs.append(job_status)
                
                return sorted(jobs, key=lambda x: x.created_at, reverse=True)
                
        except Exception as e:
            logger.error(f"列出任務失敗: {e}")
            return []
    
    async def cancel_job(self, job_id: str) -> bool:
        """取消任務"""
        try:
            with self.job_lock:
                if job_id not in self.jobs:
                    return False
                
                job_info = self.jobs[job_id]
                if job_info['status'] not in [JobStatus.PENDING.value, JobStatus.RUNNING.value]:
                    return False
                
                job_info['status'] = JobStatus.CANCELLED.value
                job_info['updated_at'] = datetime.now()
            
            # 取消任務追蹤
            if self.task_tracker:
                await self.task_tracker.cancel_task(job_id)
            
            # 取消調度器中的任務
            if self.scheduler:
                await self.scheduler.cancel_job(job_id)
            
            logger.info(f"任務已取消: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任務失敗: {e}")
            return False
    
    async def get_system_health(self) -> SystemHealthResponse:
        """獲取系統健康狀態"""
        try:
            uptime = time.time() - self.start_time
            
            # 計算錯誤率
            total_jobs = self.stats['total_jobs']
            error_rate = (self.stats['failed_jobs'] / total_jobs) if total_jobs > 0 else 0.0
            
            # 計算平均任務時間
            completed_jobs = self.stats['completed_jobs']
            avg_job_time = (self.stats['total_processing_time'] / completed_jobs) if completed_jobs > 0 else 0.0
            
            # 檢查平台健康狀態
            platform_health = {}
            if self.scheduler:
                # 這裡應該從調度器獲取平台健康狀態
                platform_health = {
                    'linkedin': True,
                    'indeed': True,
                    'google': True,
                    '104': True,
                    '1111': True
                }
            
            # 檢查Redis連接
            redis_connected = False
            if self.task_tracker:
                redis_connected = await self._check_redis_connection()
            
            # 獲取內存使用情況
            memory_usage = self._get_memory_usage()
            
            # 統計活躍任務
            active_jobs = 0
            with self.job_lock:
                active_jobs = sum(1 for job in self.jobs.values() 
                                if job['status'] in [JobStatus.PENDING.value, JobStatus.RUNNING.value])
            
            return SystemHealthResponse(
                status=self.status.value,
                uptime=uptime,
                active_jobs=active_jobs,
                completed_jobs=self.stats['completed_jobs'],
                failed_jobs=self.stats['failed_jobs'],
                error_rate=error_rate,
                average_job_time=avg_job_time,
                platform_health=platform_health,
                redis_connected=redis_connected,
                memory_usage=memory_usage,
                last_health_check=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"獲取系統健康狀態失敗: {e}")
            return SystemHealthResponse(
                status=APIStatus.ERROR.value,
                uptime=0,
                active_jobs=0,
                completed_jobs=0,
                failed_jobs=0,
                error_rate=1.0,
                average_job_time=0,
                platform_health={},
                redis_connected=False,
                memory_usage={},
                last_health_check=datetime.now()
            )
    
    async def _check_redis_connection(self) -> bool:
        """檢查Redis連接"""
        try:
            if self.task_tracker and hasattr(self.task_tracker, 'redis_client'):
                await self.task_tracker.redis_client.ping()
                return True
        except Exception:
            pass
        return False
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """獲取內存使用情況"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while self.running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # 執行健康檢查
                health = await self.get_system_health()
                
                # 檢查是否需要發送健康警報
                if health.error_rate > 0.1:  # 錯誤率超過10%
                    if self.notification_service:
                        await self.notification_service.send_health_alert(
                            alert_type="high_error_rate",
                            message=f"系統錯誤率過高: {health.error_rate:.2%}",
                            severity="high",
                            metrics=asdict(health)
                        )
                
                if not health.redis_connected:
                    if self.notification_service:
                        await self.notification_service.send_health_alert(
                            alert_type="redis_disconnected",
                            message="Redis連接已斷開",
                            severity="critical",
                            metrics=asdict(health)
                        )
                
                logger.debug(f"健康檢查完成: 狀態={health.status}, 活躍任務={health.active_jobs}")
                
            except Exception as e:
                logger.error(f"健康檢查失敗: {e}")
    
    async def shutdown(self):
        """關閉API"""
        try:
            logger.info("正在關閉多平台整合API...")
            
            self.status = APIStatus.STOPPING
            self.running = False
            
            # 停止健康檢查
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 等待所有任務完成
            with self.job_lock:
                active_jobs = [job_id for job_id, job_info in self.jobs.items() 
                             if job_info['status'] in [JobStatus.PENDING.value, JobStatus.RUNNING.value]]
            
            if active_jobs:
                logger.info(f"等待 {len(active_jobs)} 個活躍任務完成...")
                # 等待最多30秒
                for _ in range(30):
                    with self.job_lock:
                        remaining = [job_id for job_id, job_info in self.jobs.items() 
                                   if job_info['status'] in [JobStatus.PENDING.value, JobStatus.RUNNING.value]]
                    if not remaining:
                        break
                    await asyncio.sleep(1)
            
            # 關閉所有組件
            if self.scheduler:
                await self.scheduler.shutdown()
            
            if self.task_tracker:
                await self.task_tracker.shutdown()
            
            if self.sync_coordinator:
                await self.sync_coordinator.shutdown()
            
            if self.error_manager:
                self.error_manager.shutdown()
            
            if self.integrity_checker:
                self.integrity_checker.shutdown()
            
            if self.notification_service:
                await self.notification_service.shutdown()
            
            # 關閉線程池
            self.executor.shutdown(wait=True)
            
            self.status = APIStatus.STOPPED
            logger.info("多平台整合API已關閉")
            
        except Exception as e:
            logger.error(f"關閉API失敗: {e}")
            self.status = APIStatus.ERROR


# 測試用例
if __name__ == "__main__":
    import asyncio
    
    async def test_integration_api():
        """測試整合API"""
        print("=== 多平台整合API測試 ===")
        
        # 創建API配置
        config = APIConfig(
            redis_host="localhost",
            redis_port=6379,
            max_workers=5,
            enable_notifications=True,
            enable_integrity_check=True
        )
        
        # 創建API實例
        api = MultiPlatformIntegrationAPI(config)
        
        try:
            # 初始化API
            print("\n1. 初始化API...")
            if await api.initialize():
                print("API初始化成功")
            else:
                print("API初始化失敗")
                return
            
            # 提交測試任務
            print("\n2. 提交測試任務...")
            job_request = JobSubmissionRequest(
                job_id="test_job_001",
                search_params={
                    "keywords": "software engineer",
                    "location": "San Francisco",
                    "experience_level": "mid"
                },
                target_region="US",
                priority="high",
                enable_integrity_check=True,
                aggregation_strategy="deduplicate_smart",
                required_platforms=["linkedin", "indeed", "google"]
            )
            
            result = await api.submit_job(job_request)
            print(f"任務提交結果: {result}")
            
            # 等待任務處理
            print("\n3. 等待任務處理...")
            await asyncio.sleep(5)
            
            # 檢查任務狀態
            print("\n4. 檢查任務狀態...")
            status = api.get_job_status("test_job_001")
            if status:
                print(f"任務狀態: {status.status}")
                print(f"進度: {status.progress:.1%}")
                print(f"結果數量: {status.results_count}")
                print(f"平台狀態: {status.platforms}")
                if status.integrity_passed is not None:
                    print(f"完整性檢查: {'通過' if status.integrity_passed else '未通過'}")
                if status.quality_score is not None:
                    print(f"質量分數: {status.quality_score:.2%}")
            
            # 列出所有任務
            print("\n5. 列出所有任務...")
            jobs = api.list_jobs(limit=10)
            print(f"總任務數: {len(jobs)}")
            for job in jobs:
                print(f"  {job.job_id}: {job.status} ({job.progress:.1%})")
            
            # 獲取系統健康狀態
            print("\n6. 獲取系統健康狀態...")
            health = await api.get_system_health()
            print(f"系統狀態: {health.status}")
            print(f"運行時間: {health.uptime:.1f}秒")
            print(f"活躍任務: {health.active_jobs}")
            print(f"完成任務: {health.completed_jobs}")
            print(f"失敗任務: {health.failed_jobs}")
            print(f"錯誤率: {health.error_rate:.2%}")
            print(f"平均任務時間: {health.average_job_time:.2f}秒")
            print(f"Redis連接: {'正常' if health.redis_connected else '異常'}")
            
            # 提交更多測試任務
            print("\n7. 提交更多測試任務...")
            test_jobs = [
                ("test_job_002", "TW", "data scientist", "Taipei"),
                ("test_job_003", "AU", "frontend developer", "Sydney"),
                ("test_job_004", "US", "backend engineer", "New York")
            ]
            
            for job_id, region, keywords, location in test_jobs:
                request = JobSubmissionRequest(
                    job_id=job_id,
                    search_params={
                        "keywords": keywords,
                        "location": location,
                        "experience_level": "senior"
                    },
                    target_region=region,
                    priority="medium"
                )
                
                result = await api.submit_job(request)
                print(f"  {job_id}: {result['status']}")
            
            # 等待所有任務處理
            print("\n8. 等待所有任務處理...")
            await asyncio.sleep(10)
            
            # 最終狀態檢查
            print("\n9. 最終狀態檢查...")
            final_jobs = api.list_jobs()
            for job in final_jobs:
                print(f"  {job.job_id}: {job.status} - 結果: {job.results_count}")
            
            final_health = await api.get_system_health()
            print(f"\n最終系統狀態:")
            print(f"  完成任務: {final_health.completed_jobs}")
            print(f"  失敗任務: {final_health.failed_jobs}")
            print(f"  錯誤率: {final_health.error_rate:.2%}")
            
            print("\n=== 測試完成 ===")
            
        except Exception as e:
            print(f"測試失敗: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 關閉API
            await api.shutdown()
    
    # 運行測試
    asyncio.run(test_integration_api())