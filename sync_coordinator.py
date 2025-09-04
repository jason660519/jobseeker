#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
狀態同步協調器
整合即時同步管理器和任務追蹤服務，提供統一的狀態同步接口

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import weakref

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory coordination")

from task_tracking_service import TaskTrackingService, TaskEvent, EventType
from task_tracking_models import TaskStatus, PlatformStatus, MultiPlatformJob, PlatformTask
from real_time_sync_manager import RealTimeSyncManager, SyncEvent, SyncEventType, ClientType
from multi_platform_scheduler import MultiPlatformScheduler, PlatformTask as SchedulerPlatformTask
from platform_sync_manager import PlatformSyncManager, SyncEventType as PlatformSyncEventType


class SyncCoordinationMode(Enum):
    """同步協調模式"""
    REAL_TIME = "real_time"  # 即時同步
    BATCH = "batch"  # 批量同步
    HYBRID = "hybrid"  # 混合模式
    POLLING = "polling"  # 輪詢模式


class SyncPriority(Enum):
    """同步優先級"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SyncConfiguration:
    """同步配置"""
    mode: SyncCoordinationMode = SyncCoordinationMode.HYBRID
    real_time_enabled: bool = True
    batch_enabled: bool = True
    polling_enabled: bool = False
    
    # 即時同步配置
    websocket_host: str = "localhost"
    websocket_port: int = 8765
    heartbeat_interval: int = 30
    client_timeout: int = 120
    
    # 批量同步配置
    batch_size: int = 50
    batch_timeout: float = 5.0
    batch_interval: int = 10
    
    # 輪詢配置
    polling_interval: int = 60
    polling_timeout: int = 30
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/2"
    redis_enabled: bool = True
    
    # 性能配置
    max_concurrent_syncs: int = 100
    sync_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # 過濾配置
    sync_filters: List[str] = field(default_factory=list)
    priority_threshold: SyncPriority = SyncPriority.LOW
    
    # 存儲配置
    enable_persistence: bool = True
    max_history_size: int = 10000
    cleanup_interval: int = 3600  # 1小時


@dataclass
class SyncRequest:
    """同步請求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    platform: Optional[str] = None
    sync_type: str = "status_update"
    data: Dict[str, Any] = field(default_factory=dict)
    priority: SyncPriority = SyncPriority.MEDIUM
    target_clients: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """同步結果"""
    request_id: str
    success: bool
    message: str = ""
    clients_notified: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SyncCoordinator:
    """狀態同步協調器"""
    
    def __init__(self,
                 config: Optional[SyncConfiguration] = None,
                 task_service: Optional[TaskTrackingService] = None,
                 scheduler: Optional[MultiPlatformScheduler] = None,
                 platform_sync_manager: Optional[PlatformSyncManager] = None):
        """初始化同步協調器"""
        self.config = config or SyncConfiguration()
        self.task_service = task_service
        self.scheduler = scheduler
        self.platform_sync_manager = platform_sync_manager
        
        # 核心組件
        self.real_time_manager: Optional[RealTimeSyncManager] = None
        self.redis_client: Optional[Any] = None
        
        # 同步狀態
        self.is_running = False
        self.sync_requests: Dict[str, SyncRequest] = {}
        self.sync_results: Dict[str, SyncResult] = {}
        self.active_syncs: Set[str] = set()
        
        # 統計信息
        self.stats = {
            'total_requests': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'clients_notified': 0,
            'average_processing_time': 0.0,
            'start_time': datetime.now()
        }
        
        # 線程和任務管理
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_syncs,
            thread_name_prefix="SyncCoordinator"
        )
        self.background_tasks: List[Future] = []
        self.shutdown_event = threading.Event()
        
        # 事件監聽器
        self.event_listeners: Dict[str, List[Callable]] = {
            'sync_started': [],
            'sync_completed': [],
            'sync_failed': [],
            'client_connected': [],
            'client_disconnected': []
        }
        
        # 初始化組件
        self._setup_redis()
        self._setup_real_time_manager()
        self._setup_event_listeners()
        
        logging.info("狀態同步協調器已初始化")
    
    def _setup_redis(self):
        """設置Redis連接"""
        if not self.config.redis_enabled or not REDIS_AVAILABLE:
            return
        
        try:
            self.redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
            self.redis_client.ping()
            logging.info("Redis連接已建立")
        except Exception as e:
            logging.warning(f"Redis連接失敗: {e}")
            self.redis_client = None
    
    def _setup_real_time_manager(self):
        """設置即時同步管理器"""
        if not self.config.real_time_enabled:
            return
        
        try:
            self.real_time_manager = RealTimeSyncManager(
                task_service=self.task_service,
                websocket_host=self.config.websocket_host,
                websocket_port=self.config.websocket_port,
                redis_url=self.config.redis_url,
                enable_websockets=True,
                enable_redis_pubsub=self.config.redis_enabled
            )
            
            # 配置即時管理器
            self.real_time_manager.config.update({
                'heartbeat_interval': self.config.heartbeat_interval,
                'client_timeout': self.config.client_timeout,
                'event_batch_size': self.config.batch_size,
                'event_batch_timeout': self.config.batch_timeout
            })
            
            logging.info("即時同步管理器已設置")
            
        except Exception as e:
            logging.error(f"設置即時同步管理器失敗: {e}")
            self.real_time_manager = None
    
    def _setup_event_listeners(self):
        """設置事件監聽器"""
        # 監聽任務服務事件
        if self.task_service:
            self.task_service.add_event_listener(self._handle_task_event)
        
        # 監聽平台同步管理器事件
        if self.platform_sync_manager:
            self.platform_sync_manager.add_event_listener(self._handle_platform_sync_event)
    
    def start(self):
        """啟動同步協調器"""
        if self.is_running:
            logging.warning("同步協調器已在運行")
            return
        
        try:
            self.is_running = True
            self.shutdown_event.clear()
            
            # 啟動即時同步管理器
            if self.real_time_manager:
                self.real_time_manager.start_websocket_server_threaded()
            
            # 啟動背景任務
            self._start_background_tasks()
            
            logging.info("狀態同步協調器已啟動")
            
        except Exception as e:
            logging.error(f"啟動同步協調器失敗: {e}")
            self.is_running = False
            raise
    
    def _start_background_tasks(self):
        """啟動背景任務"""
        # 批量同步任務
        if self.config.batch_enabled:
            self.background_tasks.append(
                self.executor.submit(self._batch_sync_loop)
            )
        
        # 輪詢同步任務
        if self.config.polling_enabled:
            self.background_tasks.append(
                self.executor.submit(self._polling_sync_loop)
            )
        
        # 清理任務
        self.background_tasks.append(
            self.executor.submit(self._cleanup_loop)
        )
        
        # 統計更新任務
        self.background_tasks.append(
            self.executor.submit(self._stats_update_loop)
        )
    
    def sync_job_status(self,
                       job_id: str,
                       status: TaskStatus,
                       platform: Optional[str] = None,
                       data: Optional[Dict[str, Any]] = None,
                       priority: SyncPriority = SyncPriority.MEDIUM,
                       target_clients: Optional[List[str]] = None) -> str:
        """同步任務狀態"""
        sync_data = {
            'job_id': job_id,
            'status': status.value if isinstance(status, TaskStatus) else status,
            'platform': platform,
            'timestamp': datetime.now().isoformat(),
            **(data or {})
        }
        
        request = SyncRequest(
            job_id=job_id,
            platform=platform,
            sync_type='status_update',
            data=sync_data,
            priority=priority,
            target_clients=target_clients
        )
        
        return self._submit_sync_request(request)
    
    def sync_platform_status(self,
                           job_id: str,
                           platform: str,
                           status: PlatformStatus,
                           data: Optional[Dict[str, Any]] = None,
                           priority: SyncPriority = SyncPriority.MEDIUM) -> str:
        """同步平台狀態"""
        sync_data = {
            'job_id': job_id,
            'platform': platform,
            'platform_status': status.value if isinstance(status, PlatformStatus) else status,
            'timestamp': datetime.now().isoformat(),
            **(data or {})
        }
        
        request = SyncRequest(
            job_id=job_id,
            platform=platform,
            sync_type='platform_status',
            data=sync_data,
            priority=priority
        )
        
        return self._submit_sync_request(request)
    
    def sync_progress_update(self,
                           job_id: str,
                           progress: float,
                           platform: Optional[str] = None,
                           message: Optional[str] = None,
                           data: Optional[Dict[str, Any]] = None,
                           priority: SyncPriority = SyncPriority.LOW) -> str:
        """同步進度更新"""
        sync_data = {
            'job_id': job_id,
            'progress': progress,
            'platform': platform,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            **(data or {})
        }
        
        request = SyncRequest(
            job_id=job_id,
            platform=platform,
            sync_type='progress_update',
            data=sync_data,
            priority=priority
        )
        
        return self._submit_sync_request(request)
    
    def sync_error_notification(self,
                              job_id: str,
                              error: str,
                              platform: Optional[str] = None,
                              error_code: Optional[str] = None,
                              data: Optional[Dict[str, Any]] = None,
                              priority: SyncPriority = SyncPriority.HIGH) -> str:
        """同步錯誤通知"""
        sync_data = {
            'job_id': job_id,
            'error': error,
            'error_code': error_code,
            'platform': platform,
            'timestamp': datetime.now().isoformat(),
            **(data or {})
        }
        
        request = SyncRequest(
            job_id=job_id,
            platform=platform,
            sync_type='error_notification',
            data=sync_data,
            priority=priority
        )
        
        return self._submit_sync_request(request)
    
    def sync_system_alert(self,
                         alert_type: str,
                         message: str,
                         severity: str = "info",
                         data: Optional[Dict[str, Any]] = None,
                         priority: SyncPriority = SyncPriority.HIGH) -> str:
        """同步系統警報"""
        sync_data = {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            **(data or {})
        }
        
        request = SyncRequest(
            sync_type='system_alert',
            data=sync_data,
            priority=priority
        )
        
        return self._submit_sync_request(request)
    
    def _submit_sync_request(self, request: SyncRequest) -> str:
        """提交同步請求"""
        try:
            # 檢查優先級閾值
            if request.priority.value < self.config.priority_threshold.value:
                logging.debug(f"同步請求優先級過低，已跳過: {request.request_id}")
                return request.request_id
            
            # 應用過濾器
            if not self._apply_filters(request):
                logging.debug(f"同步請求被過濾器拒絕: {request.request_id}")
                return request.request_id
            
            # 存儲請求
            self.sync_requests[request.request_id] = request
            self.stats['total_requests'] += 1
            
            # 觸發事件
            self._trigger_event('sync_started', request)
            
            # 根據模式處理請求
            if self.config.mode == SyncCoordinationMode.REAL_TIME:
                self._process_real_time_sync(request)
            elif self.config.mode == SyncCoordinationMode.BATCH:
                # 批量模式會在背景任務中處理
                pass
            elif self.config.mode == SyncCoordinationMode.HYBRID:
                # 高優先級即時處理，其他批量處理
                if request.priority.value >= SyncPriority.HIGH.value:
                    self._process_real_time_sync(request)
            elif self.config.mode == SyncCoordinationMode.POLLING:
                # 輪詢模式會在背景任務中處理
                pass
            
            return request.request_id
            
        except Exception as e:
            logging.error(f"提交同步請求失敗: {e}")
            return request.request_id
    
    def _apply_filters(self, request: SyncRequest) -> bool:
        """應用同步過濾器"""
        if not self.config.sync_filters:
            return True
        
        for filter_rule in self.config.sync_filters:
            # 簡單的過濾器實現
            if filter_rule.startswith('job_id:'):
                pattern = filter_rule[7:]
                if pattern not in request.job_id:
                    return False
            elif filter_rule.startswith('platform:'):
                pattern = filter_rule[9:]
                if request.platform != pattern:
                    return False
            elif filter_rule.startswith('type:'):
                pattern = filter_rule[5:]
                if request.sync_type != pattern:
                    return False
        
        return True
    
    def _process_real_time_sync(self, request: SyncRequest):
        """處理即時同步"""
        if not self.real_time_manager:
            logging.warning("即時同步管理器不可用")
            return
        
        try:
            start_time = time.time()
            
            # 轉換為同步事件
            sync_event = self._convert_to_sync_event(request)
            
            # 發送事件
            success = self.real_time_manager.send_custom_event(
                event_type=sync_event.event_type,
                data=sync_event.data,
                job_id=sync_event.job_id,
                platform=sync_event.platform,
                target_clients=request.target_clients,
                priority=request.priority.value
            )
            
            processing_time = time.time() - start_time
            
            # 記錄結果
            result = SyncResult(
                request_id=request.request_id,
                success=success,
                processing_time=processing_time,
                clients_notified=len(self.real_time_manager.connected_clients) if success else 0
            )
            
            self._record_sync_result(result)
            
        except Exception as e:
            logging.error(f"即時同步處理失敗: {e}")
            result = SyncResult(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
            self._record_sync_result(result)
    
    def _convert_to_sync_event(self, request: SyncRequest) -> SyncEvent:
        """轉換同步請求為同步事件"""
        event_type_mapping = {
            'status_update': SyncEventType.STATUS_UPDATE,
            'progress_update': SyncEventType.PROGRESS_UPDATE,
            'platform_status': SyncEventType.PLATFORM_HEALTH,
            'error_notification': SyncEventType.ERROR_NOTIFICATION,
            'system_alert': SyncEventType.SYSTEM_ALERT
        }
        
        event_type = event_type_mapping.get(request.sync_type, SyncEventType.STATUS_UPDATE)
        
        return SyncEvent(
            event_id=request.request_id,
            event_type=event_type,
            job_id=request.job_id,
            platform=request.platform,
            data=request.data,
            timestamp=request.created_at,
            source='coordinator',
            target_clients=request.target_clients,
            priority=request.priority.value
        )
    
    def _record_sync_result(self, result: SyncResult):
        """記錄同步結果"""
        self.sync_results[result.request_id] = result
        
        if result.success:
            self.stats['successful_syncs'] += 1
            self.stats['clients_notified'] += result.clients_notified
            self._trigger_event('sync_completed', result)
        else:
            self.stats['failed_syncs'] += 1
            self._trigger_event('sync_failed', result)
        
        # 更新平均處理時間
        total_syncs = self.stats['successful_syncs'] + self.stats['failed_syncs']
        if total_syncs > 0:
            current_avg = self.stats['average_processing_time']
            self.stats['average_processing_time'] = (
                (current_avg * (total_syncs - 1) + result.processing_time) / total_syncs
            )
        
        # 從活躍同步中移除
        self.active_syncs.discard(result.request_id)
        
        # 持久化結果
        if self.config.enable_persistence and self.redis_client:
            try:
                self.redis_client.hset(
                    'sync_results',
                    result.request_id,
                    json.dumps(asdict(result), default=str)
                )
            except Exception as e:
                logging.warning(f"持久化同步結果失敗: {e}")
    
    def _batch_sync_loop(self):
        """批量同步循環"""
        while not self.shutdown_event.is_set():
            try:
                # 收集待處理的請求
                pending_requests = [
                    req for req in self.sync_requests.values()
                    if req.request_id not in self.active_syncs and
                    req.request_id not in self.sync_results
                ]
                
                if pending_requests:
                    # 按優先級排序
                    pending_requests.sort(key=lambda r: r.priority.value, reverse=True)
                    
                    # 處理批量請求
                    batch = pending_requests[:self.config.batch_size]
                    self._process_batch_sync(batch)
                
                # 等待下一個批量間隔
                self.shutdown_event.wait(self.config.batch_interval)
                
            except Exception as e:
                logging.error(f"批量同步循環錯誤: {e}")
                self.shutdown_event.wait(5)
    
    def _process_batch_sync(self, requests: List[SyncRequest]):
        """處理批量同步"""
        if not requests:
            return
        
        try:
            start_time = time.time()
            
            # 標記為活躍
            for request in requests:
                self.active_syncs.add(request.request_id)
            
            # 批量發送事件
            if self.real_time_manager:
                for request in requests:
                    sync_event = self._convert_to_sync_event(request)
                    self.real_time_manager.send_custom_event(
                        event_type=sync_event.event_type,
                        data=sync_event.data,
                        job_id=sync_event.job_id,
                        platform=sync_event.platform,
                        target_clients=request.target_clients,
                        priority=request.priority.value
                    )
            
            processing_time = time.time() - start_time
            
            # 記錄批量結果
            for request in requests:
                result = SyncResult(
                    request_id=request.request_id,
                    success=True,
                    processing_time=processing_time / len(requests),
                    clients_notified=len(self.real_time_manager.connected_clients) if self.real_time_manager else 0
                )
                self._record_sync_result(result)
            
            logging.info(f"批量同步完成: {len(requests)} 個請求")
            
        except Exception as e:
            logging.error(f"批量同步處理失敗: {e}")
            
            # 記錄失敗結果
            for request in requests:
                result = SyncResult(
                    request_id=request.request_id,
                    success=False,
                    error=str(e)
                )
                self._record_sync_result(result)
    
    def _polling_sync_loop(self):
        """輪詢同步循環"""
        while not self.shutdown_event.is_set():
            try:
                # 輪詢任務狀態
                if self.task_service:
                    self._poll_task_statuses()
                
                # 輪詢平台狀態
                if self.scheduler:
                    self._poll_platform_statuses()
                
                # 等待下一個輪詢間隔
                self.shutdown_event.wait(self.config.polling_interval)
                
            except Exception as e:
                logging.error(f"輪詢同步循環錯誤: {e}")
                self.shutdown_event.wait(10)
    
    def _poll_task_statuses(self):
        """輪詢任務狀態"""
        try:
            # 獲取活躍任務
            active_jobs = self.task_service.get_active_jobs()
            
            for job in active_jobs:
                # 檢查狀態變化
                current_status = self.task_service.get_job_status(job.job_id)
                if current_status:
                    self.sync_job_status(
                        job_id=job.job_id,
                        status=current_status.get('status', TaskStatus.PENDING),
                        data=current_status,
                        priority=SyncPriority.LOW
                    )
        
        except Exception as e:
            logging.error(f"輪詢任務狀態失敗: {e}")
    
    def _poll_platform_statuses(self):
        """輪詢平台狀態"""
        try:
            # 獲取平台健康狀態
            if hasattr(self.scheduler, 'get_platform_health'):
                health_status = self.scheduler.get_platform_health()
                
                for platform, status in health_status.items():
                    self.sync_platform_status(
                        job_id="system",
                        platform=platform,
                        status=status.get('status', PlatformStatus.UNKNOWN),
                        data=status,
                        priority=SyncPriority.LOW
                    )
        
        except Exception as e:
            logging.error(f"輪詢平台狀態失敗: {e}")
    
    def _cleanup_loop(self):
        """清理循環"""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()
                
                # 清理過期的同步請求
                expired_requests = [
                    req_id for req_id, req in self.sync_requests.items()
                    if req.expires_at and current_time > req.expires_at
                ]
                
                for req_id in expired_requests:
                    del self.sync_requests[req_id]
                
                # 清理舊的同步結果
                if len(self.sync_results) > self.config.max_history_size:
                    # 保留最新的結果
                    sorted_results = sorted(
                        self.sync_results.items(),
                        key=lambda x: x[1].timestamp,
                        reverse=True
                    )
                    
                    keep_results = dict(sorted_results[:self.config.max_history_size//2])
                    self.sync_results = keep_results
                
                logging.info(f"清理完成: 移除了 {len(expired_requests)} 個過期請求")
                
                # 等待下一個清理間隔
                self.shutdown_event.wait(self.config.cleanup_interval)
                
            except Exception as e:
                logging.error(f"清理循環錯誤: {e}")
                self.shutdown_event.wait(60)
    
    def _stats_update_loop(self):
        """統計更新循環"""
        while not self.shutdown_event.is_set():
            try:
                # 更新統計信息
                if self.real_time_manager:
                    rtm_stats = self.real_time_manager.get_statistics()
                    self.stats.update({
                        'connected_clients': rtm_stats.get('connected_clients', 0),
                        'websocket_enabled': rtm_stats.get('websocket_enabled', False),
                        'redis_enabled': rtm_stats.get('redis_enabled', False)
                    })
                
                # 等待下一個更新間隔
                self.shutdown_event.wait(60)
                
            except Exception as e:
                logging.error(f"統計更新循環錯誤: {e}")
                self.shutdown_event.wait(60)
    
    def _handle_task_event(self, task_event: TaskEvent):
        """處理任務事件"""
        try:
            # 根據事件類型確定優先級
            priority = SyncPriority.MEDIUM
            if task_event.event_type in [EventType.JOB_FAILED, EventType.ERROR_OCCURRED]:
                priority = SyncPriority.HIGH
            elif task_event.event_type == EventType.JOB_COMPLETED:
                priority = SyncPriority.MEDIUM
            
            # 同步任務狀態
            if task_event.new_status:
                self.sync_job_status(
                    job_id=task_event.job_id,
                    status=task_event.new_status,
                    platform=task_event.platform,
                    data={
                        'event_type': task_event.event_type.value,
                        'message': task_event.message,
                        'old_status': task_event.old_status.value if task_event.old_status else None,
                        **task_event.data
                    },
                    priority=priority
                )
        
        except Exception as e:
            logging.error(f"處理任務事件失敗: {e}")
    
    def _handle_platform_sync_event(self, event_data: Dict[str, Any]):
        """處理平台同步事件"""
        try:
            event_type = event_data.get('event_type')
            
            if event_type == PlatformSyncEventType.STATUS_CHANGED.value:
                self.sync_platform_status(
                    job_id=event_data.get('job_id', ''),
                    platform=event_data.get('platform', ''),
                    status=PlatformStatus(event_data.get('new_status', 'unknown')),
                    data=event_data,
                    priority=SyncPriority.MEDIUM
                )
            
            elif event_type == PlatformSyncEventType.ERROR_OCCURRED.value:
                self.sync_error_notification(
                    job_id=event_data.get('job_id', ''),
                    error=event_data.get('error', ''),
                    platform=event_data.get('platform'),
                    data=event_data,
                    priority=SyncPriority.HIGH
                )
        
        except Exception as e:
            logging.error(f"處理平台同步事件失敗: {e}")
    
    def _trigger_event(self, event_name: str, data: Any):
        """觸發事件"""
        try:
            listeners = self.event_listeners.get(event_name, [])
            for listener in listeners:
                try:
                    listener(data)
                except Exception as e:
                    logging.warning(f"事件監聽器執行失敗 {event_name}: {e}")
        except Exception as e:
            logging.error(f"觸發事件失敗 {event_name}: {e}")
    
    def add_event_listener(self, event_name: str, listener: Callable):
        """添加事件監聽器"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        self.event_listeners[event_name].append(listener)
    
    def remove_event_listener(self, event_name: str, listener: Callable):
        """移除事件監聽器"""
        if event_name in self.event_listeners:
            try:
                self.event_listeners[event_name].remove(listener)
            except ValueError:
                pass
    
    def get_sync_status(self, request_id: str) -> Optional[SyncResult]:
        """獲取同步狀態"""
        return self.sync_results.get(request_id)
    
    def get_connected_clients(self) -> Dict[str, Any]:
        """獲取連接的客戶端"""
        if self.real_time_manager:
            return self.real_time_manager.get_connected_clients()
        return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        uptime = datetime.now() - self.stats['start_time']
        
        stats = {
            **self.stats,
            'active_syncs': len(self.active_syncs),
            'pending_requests': len(self.sync_requests) - len(self.sync_results),
            'total_results': len(self.sync_results),
            'uptime_seconds': uptime.total_seconds(),
            'is_running': self.is_running
        }
        
        # 添加即時管理器統計
        if self.real_time_manager:
            rtm_stats = self.real_time_manager.get_statistics()
            stats.update({
                'real_time_manager': rtm_stats
            })
        
        return stats
    
    def shutdown(self):
        """關閉同步協調器"""
        try:
            logging.info("正在關閉狀態同步協調器...")
            
            self.is_running = False
            self.shutdown_event.set()
            
            # 關閉即時同步管理器
            if self.real_time_manager:
                self.real_time_manager.shutdown()
            
            # 等待背景任務完成
            for task in self.background_tasks:
                try:
                    task.result(timeout=5)
                except Exception as e:
                    logging.warning(f"背景任務關閉失敗: {e}")
            
            # 關閉線程池
            self.executor.shutdown(wait=True)
            
            # 關閉Redis連接
            if self.redis_client:
                self.redis_client.close()
            
            logging.info("狀態同步協調器已關閉")
            
        except Exception as e:
            logging.error(f"關閉同步協調器時出錯: {e}")


# 全局協調器實例
coordinator = None


def get_sync_coordinator(config: Optional[SyncConfiguration] = None,
                        task_service: Optional[TaskTrackingService] = None,
                        scheduler: Optional[MultiPlatformScheduler] = None,
                        platform_sync_manager: Optional[PlatformSyncManager] = None) -> SyncCoordinator:
    """獲取同步協調器實例"""
    global coordinator
    if coordinator is None:
        coordinator = SyncCoordinator(
            config=config,
            task_service=task_service,
            scheduler=scheduler,
            platform_sync_manager=platform_sync_manager
        )
    return coordinator


if __name__ == "__main__":
    # 測試同步協調器
    import time
    
    # 創建配置
    config = SyncConfiguration(
        mode=SyncCoordinationMode.HYBRID,
        websocket_port=8766,
        batch_interval=5
    )
    
    # 創建協調器
    sync_coord = SyncCoordinator(config=config)
    
    # 啟動協調器
    sync_coord.start()
    
    # 等待啟動
    time.sleep(2)
    
    # 發送測試同步請求
    request_id = sync_coord.sync_job_status(
        job_id="test-job-456",
        status=TaskStatus.PROCESSING,
        platform="linkedin",
        data={'message': '測試同步協調器'},
        priority=SyncPriority.HIGH
    )
    
    print(f"同步請求已提交: {request_id}")
    
    # 等待處理
    time.sleep(3)
    
    # 檢查結果
    result = sync_coord.get_sync_status(request_id)
    if result:
        print(f"同步結果: {result.success}, 通知客戶端: {result.clients_notified}")
    
    # 獲取統計信息
    stats = sync_coord.get_statistics()
    print(f"協調器統計: {stats}")
    
    # 保持運行
    try:
        while True:
            time.sleep(10)
            print(f"活躍同步: {len(sync_coord.active_syncs)}")
    except KeyboardInterrupt:
        print("正在關閉...")
        sync_coord.shutdown()