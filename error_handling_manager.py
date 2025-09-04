#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
錯誤處理管理器
實現多平台任務的錯誤處理、重試機制、失敗回滾和異常通知功能

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory error tracking")

from task_tracking_service import TaskTrackingService, TaskEvent, EventType
from task_tracking_models import TaskStatus, PlatformStatus
from sync_coordinator import SyncCoordinator, SyncPriority


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"  # 輕微錯誤，可自動恢復
    MEDIUM = "medium"  # 中等錯誤，需要重試
    HIGH = "high"  # 嚴重錯誤，需要人工介入
    CRITICAL = "critical"  # 致命錯誤，系統停止


class ErrorCategory(Enum):
    """錯誤類別"""
    NETWORK = "network"  # 網路錯誤
    AUTHENTICATION = "authentication"  # 認證錯誤
    RATE_LIMIT = "rate_limit"  # 速率限制
    PARSING = "parsing"  # 解析錯誤
    VALIDATION = "validation"  # 驗證錯誤
    TIMEOUT = "timeout"  # 超時錯誤
    RESOURCE = "resource"  # 資源錯誤
    PLATFORM = "platform"  # 平台錯誤
    SYSTEM = "system"  # 系統錯誤
    UNKNOWN = "unknown"  # 未知錯誤


class RetryStrategy(Enum):
    """重試策略"""
    IMMEDIATE = "immediate"  # 立即重試
    LINEAR = "linear"  # 線性延遲
    EXPONENTIAL = "exponential"  # 指數退避
    FIXED = "fixed"  # 固定延遲
    CUSTOM = "custom"  # 自定義策略


class RecoveryAction(Enum):
    """恢復動作"""
    RETRY = "retry"  # 重試
    SKIP = "skip"  # 跳過
    FALLBACK = "fallback"  # 回退到備用方案
    ROLLBACK = "rollback"  # 回滾
    ESCALATE = "escalate"  # 升級處理
    ABORT = "abort"  # 中止任務


@dataclass
class ErrorInfo:
    """錯誤信息"""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    platform: Optional[str] = None
    error_type: str = ""
    error_message: str = ""
    error_code: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    last_retry: Optional[datetime] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_method: Optional[str] = None


@dataclass
class RetryConfig:
    """重試配置"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = 3
    base_delay: float = 1.0  # 基礎延遲（秒）
    max_delay: float = 300.0  # 最大延遲（秒）
    backoff_factor: float = 2.0  # 退避因子
    jitter: bool = True  # 添加隨機抖動
    timeout: float = 30.0  # 單次重試超時
    conditions: List[str] = field(default_factory=list)  # 重試條件
    excluded_errors: List[str] = field(default_factory=list)  # 不重試的錯誤


@dataclass
class RollbackConfig:
    """回滾配置"""
    enabled: bool = True
    auto_rollback: bool = False  # 自動回滾
    rollback_timeout: float = 60.0  # 回滾超時
    preserve_partial_results: bool = True  # 保留部分結果
    rollback_actions: List[str] = field(default_factory=list)  # 回滾動作
    notification_required: bool = True  # 需要通知


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = True
    email_enabled: bool = False
    webhook_enabled: bool = False
    slack_enabled: bool = False
    
    # 郵件配置
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    to_emails: List[str] = field(default_factory=list)
    
    # Webhook配置
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    # Slack配置
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # 通知條件
    severity_threshold: ErrorSeverity = ErrorSeverity.HIGH
    rate_limit: int = 10  # 每小時最大通知數
    cooldown: int = 300  # 冷卻時間（秒）


class ErrorHandlingManager:
    """錯誤處理管理器"""
    
    def __init__(self,
                 task_service: Optional[TaskTrackingService] = None,
                 sync_coordinator: Optional[SyncCoordinator] = None,
                 redis_url: str = "redis://localhost:6379/3",
                 retry_config: Optional[RetryConfig] = None,
                 rollback_config: Optional[RollbackConfig] = None,
                 notification_config: Optional[NotificationConfig] = None):
        """初始化錯誤處理管理器"""
        self.task_service = task_service
        self.sync_coordinator = sync_coordinator
        self.redis_url = redis_url
        
        # 配置
        self.retry_config = retry_config or RetryConfig()
        self.rollback_config = rollback_config or RollbackConfig()
        self.notification_config = notification_config or NotificationConfig()
        
        # 錯誤存儲
        self.errors: Dict[str, ErrorInfo] = {}
        self.error_patterns: Dict[str, Dict[str, Any]] = {}  # 錯誤模式分析
        self.recovery_history: List[Dict[str, Any]] = []
        
        # Redis連接
        self.redis_client = None
        self._setup_redis()
        
        # 重試隊列
        self.retry_queue: List[Tuple[str, datetime]] = []  # (error_id, retry_time)
        self.retry_lock = threading.Lock()
        
        # 通知限制
        self.notification_history: Dict[str, List[datetime]] = {}  # 通知歷史
        self.notification_lock = threading.Lock()
        
        # 統計信息
        self.stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'failed_retries': 0,
            'successful_retries': 0,
            'rollbacks_performed': 0,
            'notifications_sent': 0,
            'start_time': datetime.now()
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ErrorHandler")
        self.background_tasks: List[Future] = []
        self.shutdown_event = threading.Event()
        
        # 錯誤處理器映射
        self.error_handlers: Dict[ErrorCategory, Callable] = {
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.AUTHENTICATION: self._handle_auth_error,
            ErrorCategory.RATE_LIMIT: self._handle_rate_limit_error,
            ErrorCategory.PARSING: self._handle_parsing_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.TIMEOUT: self._handle_timeout_error,
            ErrorCategory.RESOURCE: self._handle_resource_error,
            ErrorCategory.PLATFORM: self._handle_platform_error,
            ErrorCategory.SYSTEM: self._handle_system_error,
            ErrorCategory.UNKNOWN: self._handle_unknown_error
        }
        
        # 啟動背景任務
        self._start_background_tasks()
        
        logging.info("錯誤處理管理器已初始化")
    
    def _setup_redis(self):
        """設置Redis連接"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logging.info("Redis連接已建立（錯誤處理）")
        except Exception as e:
            logging.warning(f"Redis連接失敗（錯誤處理）: {e}")
            self.redis_client = None
    
    def _start_background_tasks(self):
        """啟動背景任務"""
        # 重試處理任務
        self.background_tasks.append(
            self.executor.submit(self._retry_processing_loop)
        )
        
        # 錯誤模式分析任務
        self.background_tasks.append(
            self.executor.submit(self._pattern_analysis_loop)
        )
        
        # 清理任務
        self.background_tasks.append(
            self.executor.submit(self._cleanup_loop)
        )
        
        # 健康檢查任務
        self.background_tasks.append(
            self.executor.submit(self._health_check_loop)
        )
    
    def handle_error(self,
                    job_id: str,
                    platform: Optional[str],
                    error: Exception,
                    context: Optional[Dict[str, Any]] = None) -> str:
        """處理錯誤"""
        try:
            # 創建錯誤信息
            error_info = ErrorInfo(
                job_id=job_id,
                platform=platform,
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                context=context or {},
                timestamp=datetime.now()
            )
            
            # 分析錯誤
            self._analyze_error(error_info)
            
            # 存儲錯誤
            self.errors[error_info.error_id] = error_info
            self.stats['total_errors'] += 1
            
            # 持久化錯誤
            self._persist_error(error_info)
            
            # 確定處理策略
            recovery_action = self._determine_recovery_action(error_info)
            
            # 執行恢復動作
            self._execute_recovery_action(error_info, recovery_action)
            
            # 同步錯誤狀態
            if self.sync_coordinator:
                self.sync_coordinator.sync_error_notification(
                    job_id=job_id,
                    error=error_info.error_message,
                    platform=platform,
                    error_code=error_info.error_code,
                    data={
                        'error_id': error_info.error_id,
                        'severity': error_info.severity.value,
                        'category': error_info.category.value,
                        'recovery_action': recovery_action.value
                    },
                    priority=self._get_sync_priority(error_info.severity)
                )
            
            logging.error(f"錯誤已處理: {error_info.error_id} - {error_info.error_message}")
            return error_info.error_id
            
        except Exception as e:
            logging.critical(f"錯誤處理器本身發生錯誤: {e}")
            return ""
    
    def _analyze_error(self, error_info: ErrorInfo):
        """分析錯誤"""
        try:
            # 確定錯誤類別
            error_info.category = self._categorize_error(error_info)
            
            # 確定錯誤嚴重程度
            error_info.severity = self._assess_severity(error_info)
            
            # 提取錯誤代碼
            error_info.error_code = self._extract_error_code(error_info)
            
            # 設置重試配置
            error_info.max_retries = self._get_max_retries(error_info)
            
        except Exception as e:
            logging.warning(f"錯誤分析失敗: {e}")
    
    def _categorize_error(self, error_info: ErrorInfo) -> ErrorCategory:
        """分類錯誤"""
        error_message = error_info.error_message.lower()
        error_type = error_info.error_type.lower()
        
        # 網路錯誤
        if any(keyword in error_message for keyword in [
            'connection', 'network', 'timeout', 'unreachable', 'dns'
        ]):
            return ErrorCategory.NETWORK
        
        # 認證錯誤
        if any(keyword in error_message for keyword in [
            'authentication', 'unauthorized', 'forbidden', 'login', 'credential'
        ]):
            return ErrorCategory.AUTHENTICATION
        
        # 速率限制
        if any(keyword in error_message for keyword in [
            'rate limit', 'too many requests', 'quota exceeded', 'throttle'
        ]):
            return ErrorCategory.RATE_LIMIT
        
        # 解析錯誤
        if any(keyword in error_message for keyword in [
            'parse', 'json', 'xml', 'html', 'format', 'decode'
        ]):
            return ErrorCategory.PARSING
        
        # 驗證錯誤
        if any(keyword in error_message for keyword in [
            'validation', 'invalid', 'missing', 'required', 'format'
        ]):
            return ErrorCategory.VALIDATION
        
        # 超時錯誤
        if any(keyword in error_message for keyword in [
            'timeout', 'timed out', 'deadline exceeded'
        ]):
            return ErrorCategory.TIMEOUT
        
        # 資源錯誤
        if any(keyword in error_message for keyword in [
            'memory', 'disk', 'space', 'resource', 'limit'
        ]):
            return ErrorCategory.RESOURCE
        
        # 平台錯誤
        if any(keyword in error_message for keyword in [
            'platform', 'service unavailable', 'maintenance', 'blocked'
        ]):
            return ErrorCategory.PLATFORM
        
        # 系統錯誤
        if any(keyword in error_type for keyword in [
            'system', 'os', 'file', 'permission', 'io'
        ]):
            return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error_info: ErrorInfo) -> ErrorSeverity:
        """評估錯誤嚴重程度"""
        # 根據錯誤類別確定基礎嚴重程度
        base_severity = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
            ErrorCategory.RATE_LIMIT: ErrorSeverity.LOW,
            ErrorCategory.PARSING: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.RESOURCE: ErrorSeverity.HIGH,
            ErrorCategory.PLATFORM: ErrorSeverity.MEDIUM,
            ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM
        }.get(error_info.category, ErrorSeverity.MEDIUM)
        
        # 根據上下文調整嚴重程度
        if error_info.context.get('critical_job', False):
            if base_severity.value == 'low':
                return ErrorSeverity.MEDIUM
            elif base_severity.value == 'medium':
                return ErrorSeverity.HIGH
        
        # 根據重試次數調整
        if error_info.retry_count >= 2:
            if base_severity == ErrorSeverity.LOW:
                return ErrorSeverity.MEDIUM
            elif base_severity == ErrorSeverity.MEDIUM:
                return ErrorSeverity.HIGH
        
        return base_severity
    
    def _extract_error_code(self, error_info: ErrorInfo) -> Optional[str]:
        """提取錯誤代碼"""
        # 從錯誤消息中提取HTTP狀態碼
        import re
        
        # HTTP狀態碼
        http_pattern = r'\b(\d{3})\b'
        match = re.search(http_pattern, error_info.error_message)
        if match:
            return f"HTTP_{match.group(1)}"
        
        # 自定義錯誤代碼
        code_pattern = r'error[_\s]?code[:\s]+(\w+)'
        match = re.search(code_pattern, error_info.error_message, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _get_max_retries(self, error_info: ErrorInfo) -> int:
        """獲取最大重試次數"""
        # 根據錯誤類別確定重試次數
        retry_limits = {
            ErrorCategory.NETWORK: 3,
            ErrorCategory.AUTHENTICATION: 1,
            ErrorCategory.RATE_LIMIT: 5,
            ErrorCategory.PARSING: 2,
            ErrorCategory.VALIDATION: 1,
            ErrorCategory.TIMEOUT: 3,
            ErrorCategory.RESOURCE: 2,
            ErrorCategory.PLATFORM: 3,
            ErrorCategory.SYSTEM: 1,
            ErrorCategory.UNKNOWN: 2
        }
        
        return retry_limits.get(error_info.category, self.retry_config.max_attempts)
    
    def _determine_recovery_action(self, error_info: ErrorInfo) -> RecoveryAction:
        """確定恢復動作"""
        # 檢查是否應該重試
        if self._should_retry(error_info):
            return RecoveryAction.RETRY
        
        # 檢查是否需要回滾
        if self._should_rollback(error_info):
            return RecoveryAction.ROLLBACK
        
        # 檢查是否有備用方案
        if self._has_fallback(error_info):
            return RecoveryAction.FALLBACK
        
        # 根據嚴重程度確定動作
        if error_info.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.ABORT
        elif error_info.severity == ErrorSeverity.HIGH:
            return RecoveryAction.ESCALATE
        elif error_info.severity == ErrorSeverity.MEDIUM:
            return RecoveryAction.SKIP
        else:
            return RecoveryAction.SKIP
    
    def _should_retry(self, error_info: ErrorInfo) -> bool:
        """判斷是否應該重試"""
        # 檢查重試次數
        if error_info.retry_count >= error_info.max_retries:
            return False
        
        # 檢查錯誤類別
        non_retryable_categories = {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.VALIDATION
        }
        
        if error_info.category in non_retryable_categories:
            return False
        
        # 檢查排除的錯誤
        for excluded_error in self.retry_config.excluded_errors:
            if excluded_error.lower() in error_info.error_message.lower():
                return False
        
        return True
    
    def _should_rollback(self, error_info: ErrorInfo) -> bool:
        """判斷是否應該回滾"""
        if not self.rollback_config.enabled:
            return False
        
        # 自動回滾條件
        if self.rollback_config.auto_rollback:
            return error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        
        return False
    
    def _has_fallback(self, error_info: ErrorInfo) -> bool:
        """檢查是否有備用方案"""
        # 檢查上下文中是否有備用平台
        fallback_platforms = error_info.context.get('fallback_platforms', [])
        return len(fallback_platforms) > 0
    
    def _execute_recovery_action(self, error_info: ErrorInfo, action: RecoveryAction):
        """執行恢復動作"""
        try:
            if action == RecoveryAction.RETRY:
                self._schedule_retry(error_info)
            elif action == RecoveryAction.ROLLBACK:
                self._perform_rollback(error_info)
            elif action == RecoveryAction.FALLBACK:
                self._execute_fallback(error_info)
            elif action == RecoveryAction.ESCALATE:
                self._escalate_error(error_info)
            elif action == RecoveryAction.ABORT:
                self._abort_job(error_info)
            elif action == RecoveryAction.SKIP:
                self._skip_task(error_info)
            
            # 記錄恢復歷史
            self.recovery_history.append({
                'error_id': error_info.error_id,
                'action': action.value,
                'timestamp': datetime.now(),
                'success': True
            })
            
        except Exception as e:
            logging.error(f"執行恢復動作失敗 {action.value}: {e}")
            
            # 記錄失敗
            self.recovery_history.append({
                'error_id': error_info.error_id,
                'action': action.value,
                'timestamp': datetime.now(),
                'success': False,
                'error': str(e)
            })
    
    def _schedule_retry(self, error_info: ErrorInfo):
        """安排重試"""
        try:
            # 計算重試延遲
            delay = self._calculate_retry_delay(error_info)
            retry_time = datetime.now() + timedelta(seconds=delay)
            
            # 添加到重試隊列
            with self.retry_lock:
                self.retry_queue.append((error_info.error_id, retry_time))
                self.retry_queue.sort(key=lambda x: x[1])  # 按時間排序
            
            # 更新錯誤信息
            error_info.retry_count += 1
            error_info.last_retry = retry_time
            
            logging.info(f"已安排重試: {error_info.error_id}, 延遲 {delay:.2f} 秒")
            
        except Exception as e:
            logging.error(f"安排重試失敗: {e}")
    
    def _calculate_retry_delay(self, error_info: ErrorInfo) -> float:
        """計算重試延遲"""
        strategy = self.retry_config.strategy
        base_delay = self.retry_config.base_delay
        max_delay = self.retry_config.max_delay
        backoff_factor = self.retry_config.backoff_factor
        
        if strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif strategy == RetryStrategy.LINEAR:
            delay = base_delay * error_info.retry_count
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (backoff_factor ** error_info.retry_count)
        elif strategy == RetryStrategy.FIXED:
            delay = base_delay
        else:  # CUSTOM
            delay = self._custom_retry_delay(error_info)
        
        # 限制最大延遲
        delay = min(delay, max_delay)
        
        # 添加隨機抖動
        if self.retry_config.jitter:
            import random
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter
        
        return delay
    
    def _custom_retry_delay(self, error_info: ErrorInfo) -> float:
        """自定義重試延遲"""
        # 根據錯誤類別自定義延遲
        category_delays = {
            ErrorCategory.RATE_LIMIT: 60.0,  # 速率限制等待更長時間
            ErrorCategory.NETWORK: 5.0,
            ErrorCategory.TIMEOUT: 10.0,
            ErrorCategory.PLATFORM: 30.0
        }
        
        base_delay = category_delays.get(error_info.category, self.retry_config.base_delay)
        return base_delay * (1.5 ** error_info.retry_count)
    
    def _perform_rollback(self, error_info: ErrorInfo):
        """執行回滾"""
        try:
            logging.info(f"開始回滾任務: {error_info.job_id}")
            
            # 更新任務狀態為回滾中
            if self.task_service:
                self.task_service.update_job_status(
                    error_info.job_id,
                    TaskStatus.ROLLING_BACK,
                    message=f"因錯誤回滾: {error_info.error_message}"
                )
            
            # 執行回滾動作
            for action in self.rollback_config.rollback_actions:
                self._execute_rollback_action(error_info, action)
            
            # 更新統計
            self.stats['rollbacks_performed'] += 1
            
            # 發送通知
            if self.rollback_config.notification_required:
                self._send_notification(
                    error_info,
                    f"任務 {error_info.job_id} 已回滾",
                    "rollback"
                )
            
            logging.info(f"回滾完成: {error_info.job_id}")
            
        except Exception as e:
            logging.error(f"回滾失敗: {e}")
            raise
    
    def _execute_rollback_action(self, error_info: ErrorInfo, action: str):
        """執行具體的回滾動作"""
        if action == "clear_partial_results":
            # 清理部分結果
            if self.task_service:
                self.task_service.clear_job_results(error_info.job_id)
        
        elif action == "reset_platform_status":
            # 重置平台狀態
            if self.task_service:
                self.task_service.reset_platform_status(
                    error_info.job_id,
                    error_info.platform
                )
        
        elif action == "cleanup_resources":
            # 清理資源
            self._cleanup_job_resources(error_info.job_id)
        
        # 可以添加更多回滾動作
    
    def _execute_fallback(self, error_info: ErrorInfo):
        """執行備用方案"""
        try:
            fallback_platforms = error_info.context.get('fallback_platforms', [])
            
            if not fallback_platforms:
                logging.warning(f"沒有可用的備用平台: {error_info.job_id}")
                return
            
            # 選擇備用平台
            fallback_platform = fallback_platforms[0]
            
            logging.info(f"切換到備用平台: {fallback_platform}")
            
            # 更新任務配置
            if self.task_service:
                self.task_service.update_job_platform(
                    error_info.job_id,
                    fallback_platform,
                    reason=f"原平台 {error_info.platform} 失敗"
                )
            
            # 重新提交任務
            # 這裡需要與調度器集成
            
        except Exception as e:
            logging.error(f"執行備用方案失敗: {e}")
    
    def _escalate_error(self, error_info: ErrorInfo):
        """升級錯誤處理"""
        try:
            logging.warning(f"升級錯誤處理: {error_info.error_id}")
            
            # 發送高優先級通知
            self._send_notification(
                error_info,
                f"嚴重錯誤需要人工介入: {error_info.error_message}",
                "escalation",
                priority="high"
            )
            
            # 標記為需要人工介入
            error_info.context['requires_manual_intervention'] = True
            
            # 暫停相關任務
            if self.task_service:
                self.task_service.pause_related_jobs(
                    error_info.job_id,
                    reason="錯誤升級，需要人工介入"
                )
            
        except Exception as e:
            logging.error(f"升級錯誤處理失敗: {e}")
    
    def _abort_job(self, error_info: ErrorInfo):
        """中止任務"""
        try:
            logging.error(f"中止任務: {error_info.job_id}")
            
            # 更新任務狀態
            if self.task_service:
                self.task_service.update_job_status(
                    error_info.job_id,
                    TaskStatus.FAILED,
                    message=f"因致命錯誤中止: {error_info.error_message}"
                )
            
            # 清理資源
            self._cleanup_job_resources(error_info.job_id)
            
            # 發送通知
            self._send_notification(
                error_info,
                f"任務 {error_info.job_id} 因致命錯誤已中止",
                "abort",
                priority="critical"
            )
            
        except Exception as e:
            logging.error(f"中止任務失敗: {e}")
    
    def _skip_task(self, error_info: ErrorInfo):
        """跳過任務"""
        try:
            logging.info(f"跳過任務: {error_info.job_id}")
            
            # 更新任務狀態
            if self.task_service:
                self.task_service.update_job_status(
                    error_info.job_id,
                    TaskStatus.SKIPPED,
                    message=f"因錯誤跳過: {error_info.error_message}"
                )
            
            # 標記錯誤為已解決
            error_info.resolved = True
            error_info.resolution_time = datetime.now()
            error_info.resolution_method = "skipped"
            
        except Exception as e:
            logging.error(f"跳過任務失敗: {e}")
    
    def _cleanup_job_resources(self, job_id: str):
        """清理任務資源"""
        try:
            # 清理臨時文件
            temp_dir = Path(f"/tmp/job_{job_id}")
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
            
            # 清理緩存
            if self.redis_client:
                pattern = f"job:{job_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logging.info(f"已清理任務資源: {job_id}")
            
        except Exception as e:
            logging.warning(f"清理任務資源失敗: {e}")
    
    def _send_notification(self,
                          error_info: ErrorInfo,
                          message: str,
                          notification_type: str,
                          priority: str = "medium"):
        """發送通知"""
        try:
            # 檢查通知配置
            if not self.notification_config.enabled:
                return
            
            # 檢查嚴重程度閾值
            if error_info.severity.value < self.notification_config.severity_threshold.value:
                return
            
            # 檢查速率限制
            if not self._check_notification_rate_limit(error_info):
                return
            
            # 發送郵件通知
            if self.notification_config.email_enabled:
                self._send_email_notification(error_info, message, notification_type)
            
            # 發送Webhook通知
            if self.notification_config.webhook_enabled:
                self._send_webhook_notification(error_info, message, notification_type)
            
            # 發送Slack通知
            if self.notification_config.slack_enabled:
                self._send_slack_notification(error_info, message, notification_type)
            
            # 更新統計
            self.stats['notifications_sent'] += 1
            
            # 記錄通知歷史
            with self.notification_lock:
                key = f"{error_info.job_id}_{notification_type}"
                if key not in self.notification_history:
                    self.notification_history[key] = []
                self.notification_history[key].append(datetime.now())
            
        except Exception as e:
            logging.error(f"發送通知失敗: {e}")
    
    def _check_notification_rate_limit(self, error_info: ErrorInfo) -> bool:
        """檢查通知速率限制"""
        try:
            with self.notification_lock:
                key = f"{error_info.job_id}_rate_limit"
                now = datetime.now()
                hour_ago = now - timedelta(hours=1)
                
                # 清理舊記錄
                if key in self.notification_history:
                    self.notification_history[key] = [
                        ts for ts in self.notification_history[key]
                        if ts > hour_ago
                    ]
                else:
                    self.notification_history[key] = []
                
                # 檢查是否超過限制
                if len(self.notification_history[key]) >= self.notification_config.rate_limit:
                    return False
                
                # 檢查冷卻時間
                if self.notification_history[key]:
                    last_notification = max(self.notification_history[key])
                    cooldown_end = last_notification + timedelta(seconds=self.notification_config.cooldown)
                    if now < cooldown_end:
                        return False
                
                return True
        
        except Exception as e:
            logging.warning(f"檢查通知速率限制失敗: {e}")
            return True
    
    def _send_email_notification(self, error_info: ErrorInfo, message: str, notification_type: str):
        """發送郵件通知"""
        try:
            if not self.notification_config.to_emails:
                return
            
            # 創建郵件
            msg = MIMEMultipart()
            msg['From'] = self.notification_config.from_email
            msg['To'] = ', '.join(self.notification_config.to_emails)
            msg['Subject'] = f"[JobSpy Alert] {notification_type.title()}: {error_info.job_id}"
            
            # 郵件內容
            body = f"""
            錯誤通知
            
            任務ID: {error_info.job_id}
            平台: {error_info.platform or 'N/A'}
            錯誤類型: {error_info.error_type}
            錯誤消息: {error_info.error_message}
            嚴重程度: {error_info.severity.value}
            類別: {error_info.category.value}
            時間: {error_info.timestamp.isoformat()}
            重試次數: {error_info.retry_count}
            
            詳細信息:
            {message}
            
            錯誤ID: {error_info.error_id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 發送郵件
            server = smtplib.SMTP(self.notification_config.smtp_server, self.notification_config.smtp_port)
            server.starttls()
            server.login(self.notification_config.smtp_username, self.notification_config.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"郵件通知已發送: {error_info.error_id}")
            
        except Exception as e:
            logging.error(f"發送郵件通知失敗: {e}")
    
    def _send_webhook_notification(self, error_info: ErrorInfo, message: str, notification_type: str):
        """發送Webhook通知"""
        try:
            import requests
            
            payload = {
                'type': notification_type,
                'error_id': error_info.error_id,
                'job_id': error_info.job_id,
                'platform': error_info.platform,
                'error_type': error_info.error_type,
                'error_message': error_info.error_message,
                'severity': error_info.severity.value,
                'category': error_info.category.value,
                'timestamp': error_info.timestamp.isoformat(),
                'retry_count': error_info.retry_count,
                'message': message
            }
            
            response = requests.post(
                self.notification_config.webhook_url,
                json=payload,
                headers=self.notification_config.webhook_headers,
                timeout=10
            )
            
            response.raise_for_status()
            logging.info(f"Webhook通知已發送: {error_info.error_id}")
            
        except Exception as e:
            logging.error(f"發送Webhook通知失敗: {e}")
    
    def _send_slack_notification(self, error_info: ErrorInfo, message: str, notification_type: str):
        """發送Slack通知"""
        try:
            import requests
            
            # Slack消息格式
            color = {
                'low': 'good',
                'medium': 'warning',
                'high': 'danger',
                'critical': 'danger'
            }.get(error_info.severity.value, 'warning')
            
            payload = {
                'channel': self.notification_config.slack_channel,
                'username': 'JobSpy Error Handler',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': f'{notification_type.title()}: {error_info.job_id}',
                    'text': message,
                    'fields': [
                        {'title': '平台', 'value': error_info.platform or 'N/A', 'short': True},
                        {'title': '嚴重程度', 'value': error_info.severity.value, 'short': True},
                        {'title': '錯誤類型', 'value': error_info.error_type, 'short': True},
                        {'title': '重試次數', 'value': str(error_info.retry_count), 'short': True}
                    ],
                    'timestamp': int(error_info.timestamp.timestamp())
                }]
            }
            
            response = requests.post(
                self.notification_config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            logging.info(f"Slack通知已發送: {error_info.error_id}")
            
        except Exception as e:
            logging.error(f"發送Slack通知失敗: {e}")
    
    def _get_sync_priority(self, severity: ErrorSeverity) -> SyncPriority:
        """根據錯誤嚴重程度獲取同步優先級"""
        mapping = {
            ErrorSeverity.LOW: SyncPriority.LOW,
            ErrorSeverity.MEDIUM: SyncPriority.MEDIUM,
            ErrorSeverity.HIGH: SyncPriority.HIGH,
            ErrorSeverity.CRITICAL: SyncPriority.CRITICAL
        }
        return mapping.get(severity, SyncPriority.MEDIUM)
    
    def _persist_error(self, error_info: ErrorInfo):
        """持久化錯誤信息"""
        if not self.redis_client:
            return
        
        try:
            # 存儲錯誤信息
            self.redis_client.hset(
                'errors',
                error_info.error_id,
                json.dumps(asdict(error_info), default=str)
            )
            
            # 添加到任務錯誤列表
            self.redis_client.lpush(
                f'job_errors:{error_info.job_id}',
                error_info.error_id
            )
            
            # 設置過期時間（30天）
            self.redis_client.expire(f'job_errors:{error_info.job_id}', 30 * 24 * 3600)
            
        except Exception as e:
            logging.warning(f"持久化錯誤信息失敗: {e}")
    
    def _retry_processing_loop(self):
        """重試處理循環"""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()
                ready_retries = []
                
                # 檢查準備重試的錯誤
                with self.retry_lock:
                    while self.retry_queue and self.retry_queue[0][1] <= current_time:
                        error_id, _ = self.retry_queue.pop(0)
                        ready_retries.append(error_id)
                
                # 處理重試
                for error_id in ready_retries:
                    self._process_retry(error_id)
                
                # 等待下一次檢查
                self.shutdown_event.wait(1)
                
            except Exception as e:
                logging.error(f"重試處理循環錯誤: {e}")
                self.shutdown_event.wait(5)
    
    def _process_retry(self, error_id: str):
        """處理重試"""
        try:
            error_info = self.errors.get(error_id)
            if not error_info:
                logging.warning(f"找不到錯誤信息: {error_id}")
                return
            
            logging.info(f"開始重試: {error_id} (第 {error_info.retry_count} 次)")
            
            # 執行重試邏輯
            success = self._execute_retry(error_info)
            
            if success:
                # 重試成功
                error_info.resolved = True
                error_info.resolution_time = datetime.now()
                error_info.resolution_method = "retry"
                self.stats['successful_retries'] += 1
                self.stats['resolved_errors'] += 1
                
                logging.info(f"重試成功: {error_id}")
                
                # 同步狀態
                if self.sync_coordinator:
                    self.sync_coordinator.sync_job_status(
                        job_id=error_info.job_id,
                        status=TaskStatus.PROCESSING,
                        platform=error_info.platform,
                        data={'retry_success': True, 'error_id': error_id},
                        priority=SyncPriority.MEDIUM
                    )
            else:
                # 重試失敗
                self.stats['failed_retries'] += 1
                
                # 檢查是否還能重試
                if error_info.retry_count < error_info.max_retries:
                    # 重新安排重試
                    self._schedule_retry(error_info)
                else:
                    # 重試次數用盡，執行其他恢復動作
                    logging.warning(f"重試次數用盡: {error_id}")
                    recovery_action = self._determine_recovery_action(error_info)
                    if recovery_action != RecoveryAction.RETRY:
                        self._execute_recovery_action(error_info, recovery_action)
        
        except Exception as e:
            logging.error(f"處理重試失敗: {e}")
    
    def _execute_retry(self, error_info: ErrorInfo) -> bool:
        """執行重試邏輯"""
        try:
            # 這裡需要根據具體的錯誤類型執行相應的重試邏輯
            handler = self.error_handlers.get(error_info.category)
            if handler:
                return handler(error_info, is_retry=True)
            else:
                # 默認重試邏輯
                return self._default_retry_logic(error_info)
        
        except Exception as e:
            logging.error(f"執行重試邏輯失敗: {e}")
            return False
    
    def _default_retry_logic(self, error_info: ErrorInfo) -> bool:
        """默認重試邏輯"""
        # 這裡實現默認的重試邏輯
        # 實際實現需要根據具體的業務邏輯
        logging.info(f"執行默認重試邏輯: {error_info.error_id}")
        
        # 模擬重試成功率
        import random
        return random.random() > 0.3  # 70%成功率
    
    # 錯誤處理器實現
    def _handle_network_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理網路錯誤"""
        logging.info(f"處理網路錯誤: {error_info.error_id}")
        # 實現網路錯誤的具體處理邏輯
        return True
    
    def _handle_auth_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理認證錯誤"""
        logging.info(f"處理認證錯誤: {error_info.error_id}")
        # 實現認證錯誤的具體處理邏輯
        return False  # 認證錯誤通常不能通過重試解決
    
    def _handle_rate_limit_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理速率限制錯誤"""
        logging.info(f"處理速率限制錯誤: {error_info.error_id}")
        # 實現速率限制錯誤的具體處理邏輯
        return True
    
    def _handle_parsing_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理解析錯誤"""
        logging.info(f"處理解析錯誤: {error_info.error_id}")
        # 實現解析錯誤的具體處理邏輯
        return True
    
    def _handle_validation_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理驗證錯誤"""
        logging.info(f"處理驗證錯誤: {error_info.error_id}")
        # 實現驗證錯誤的具體處理邏輯
        return False  # 驗證錯誤通常需要修復數據
    
    def _handle_timeout_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理超時錯誤"""
        logging.info(f"處理超時錯誤: {error_info.error_id}")
        # 實現超時錯誤的具體處理邏輯
        return True
    
    def _handle_resource_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理資源錯誤"""
        logging.info(f"處理資源錯誤: {error_info.error_id}")
        # 實現資源錯誤的具體處理邏輯
        return False  # 資源錯誤通常需要清理或等待
    
    def _handle_platform_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理平台錯誤"""
        logging.info(f"處理平台錯誤: {error_info.error_id}")
        # 實現平台錯誤的具體處理邏輯
        return True
    
    def _handle_system_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理系統錯誤"""
        logging.info(f"處理系統錯誤: {error_info.error_id}")
        # 實現系統錯誤的具體處理邏輯
        return False  # 系統錯誤通常需要人工介入
    
    def _handle_unknown_error(self, error_info: ErrorInfo, is_retry: bool = False) -> bool:
        """處理未知錯誤"""
        logging.info(f"處理未知錯誤: {error_info.error_id}")
        # 實現未知錯誤的具體處理邏輯
        return True
    
    def _pattern_analysis_loop(self):
        """錯誤模式分析循環"""
        while not self.shutdown_event.is_set():
            try:
                # 分析錯誤模式
                self._analyze_error_patterns()
                
                # 等待下一次分析
                self.shutdown_event.wait(3600)  # 每小時分析一次
                
            except Exception as e:
                logging.error(f"錯誤模式分析循環錯誤: {e}")
                self.shutdown_event.wait(300)
    
    def _analyze_error_patterns(self):
        """分析錯誤模式"""
        try:
            # 統計錯誤類型
            error_counts = {}
            for error in self.errors.values():
                key = f"{error.category.value}_{error.error_type}"
                error_counts[key] = error_counts.get(key, 0) + 1
            
            # 識別高頻錯誤
            high_frequency_errors = {
                k: v for k, v in error_counts.items() if v >= 5
            }
            
            if high_frequency_errors:
                logging.info(f"發現高頻錯誤模式: {high_frequency_errors}")
                
                # 更新錯誤模式
                self.error_patterns.update({
                    'high_frequency': high_frequency_errors,
                    'last_analysis': datetime.now().isoformat()
                })
        
        except Exception as e:
            logging.error(f"分析錯誤模式失敗: {e}")
    
    def _cleanup_loop(self):
        """清理循環"""
        while not self.shutdown_event.is_set():
            try:
                # 清理已解決的舊錯誤
                cutoff_time = datetime.now() - timedelta(days=7)
                
                resolved_errors = [
                    error_id for error_id, error in self.errors.items()
                    if error.resolved and error.resolution_time and error.resolution_time < cutoff_time
                ]
                
                for error_id in resolved_errors:
                    del self.errors[error_id]
                
                # 清理通知歷史
                hour_ago = datetime.now() - timedelta(hours=1)
                for key in list(self.notification_history.keys()):
                    self.notification_history[key] = [
                        ts for ts in self.notification_history[key]
                        if ts > hour_ago
                    ]
                    if not self.notification_history[key]:
                        del self.notification_history[key]
                
                logging.info(f"清理完成: 移除了 {len(resolved_errors)} 個已解決錯誤")
                
                # 等待下一次清理
                self.shutdown_event.wait(3600)  # 每小時清理一次
                
            except Exception as e:
                logging.error(f"清理循環錯誤: {e}")
                self.shutdown_event.wait(300)
    
    def _health_check_loop(self):
        """健康檢查循環"""
        while not self.shutdown_event.is_set():
            try:
                # 檢查系統健康狀態
                health_status = self._check_system_health()
                
                if not health_status['healthy']:
                    logging.warning(f"系統健康檢查失敗: {health_status['issues']}")
                    
                    # 發送健康警報
                    self._send_health_alert(health_status)
                
                # 等待下一次檢查
                self.shutdown_event.wait(300)  # 每5分鐘檢查一次
                
            except Exception as e:
                logging.error(f"健康檢查循環錯誤: {e}")
                self.shutdown_event.wait(60)
    
    def _check_system_health(self) -> Dict[str, Any]:
        """檢查系統健康狀態"""
        issues = []
        
        # 檢查錯誤率
        total_errors = self.stats['total_errors']
        if total_errors > 0:
            error_rate = self.stats['failed_retries'] / total_errors
            if error_rate > 0.5:  # 錯誤率超過50%
                issues.append(f"高錯誤率: {error_rate:.2%}")
        
        # 檢查重試隊列
        retry_queue_size = len(self.retry_queue)
        if retry_queue_size > 100:  # 重試隊列過長
            issues.append(f"重試隊列過長: {retry_queue_size}")
        
        # 檢查Redis連接
        if self.redis_client:
            try:
                self.redis_client.ping()
            except Exception:
                issues.append("Redis連接失敗")
        
        # 檢查線程池
        if hasattr(self.executor, '_threads'):
            active_threads = len([t for t in self.executor._threads if t.is_alive()])
            if active_threads == 0:
                issues.append("沒有活躍的工作線程")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'stats': self.stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_health_alert(self, health_status: Dict[str, Any]):
        """發送健康警報"""
        try:
            # 創建虛擬錯誤信息用於發送警報
            alert_error = ErrorInfo(
                job_id="SYSTEM_HEALTH",
                platform="system",
                error_type="HealthCheck",
                error_message=f"系統健康檢查失敗: {', '.join(health_status['issues'])}",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM
            )
            
            self._send_notification(
                alert_error,
                f"系統健康警報: {health_status['issues']}",
                "health_alert",
                priority="high"
            )
            
        except Exception as e:
            logging.error(f"發送健康警報失敗: {e}")
    
    def get_error_info(self, error_id: str) -> Optional[ErrorInfo]:
        """獲取錯誤信息"""
        return self.errors.get(error_id)
    
    def get_job_errors(self, job_id: str) -> List[ErrorInfo]:
        """獲取任務的所有錯誤"""
        return [error for error in self.errors.values() if error.job_id == job_id]
    
    def resolve_error(self, error_id: str, resolution_method: str = "manual") -> bool:
        """手動解決錯誤"""
        try:
            error_info = self.errors.get(error_id)
            if not error_info:
                return False
            
            error_info.resolved = True
            error_info.resolution_time = datetime.now()
            error_info.resolution_method = resolution_method
            
            self.stats['resolved_errors'] += 1
            
            # 從重試隊列中移除
            with self.retry_lock:
                self.retry_queue = [
                    (eid, time) for eid, time in self.retry_queue
                    if eid != error_id
                ]
            
            logging.info(f"錯誤已手動解決: {error_id}")
            return True
            
        except Exception as e:
            logging.error(f"解決錯誤失敗: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        current_time = datetime.now()
        uptime = current_time - self.stats['start_time']
        
        # 計算錯誤率
        total_errors = self.stats['total_errors']
        error_rate = 0
        if total_errors > 0:
            error_rate = (total_errors - self.stats['resolved_errors']) / total_errors
        
        # 計算重試成功率
        total_retries = self.stats['successful_retries'] + self.stats['failed_retries']
        retry_success_rate = 0
        if total_retries > 0:
            retry_success_rate = self.stats['successful_retries'] / total_retries
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_errors': total_errors,
            'resolved_errors': self.stats['resolved_errors'],
            'pending_errors': total_errors - self.stats['resolved_errors'],
            'error_rate': error_rate,
            'successful_retries': self.stats['successful_retries'],
            'failed_retries': self.stats['failed_retries'],
            'retry_success_rate': retry_success_rate,
            'rollbacks_performed': self.stats['rollbacks_performed'],
            'notifications_sent': self.stats['notifications_sent'],
            'retry_queue_size': len(self.retry_queue),
            'error_patterns': self.error_patterns,
            'timestamp': current_time.isoformat()
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """獲取錯誤摘要"""
        # 按類別統計
        category_stats = {}
        severity_stats = {}
        platform_stats = {}
        
        for error in self.errors.values():
            # 類別統計
            category = error.category.value
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'resolved': 0}
            category_stats[category]['total'] += 1
            if error.resolved:
                category_stats[category]['resolved'] += 1
            
            # 嚴重程度統計
            severity = error.severity.value
            if severity not in severity_stats:
                severity_stats[severity] = {'total': 0, 'resolved': 0}
            severity_stats[severity]['total'] += 1
            if error.resolved:
                severity_stats[severity]['resolved'] += 1
            
            # 平台統計
            platform = error.platform or 'unknown'
            if platform not in platform_stats:
                platform_stats[platform] = {'total': 0, 'resolved': 0}
            platform_stats[platform]['total'] += 1
            if error.resolved:
                platform_stats[platform]['resolved'] += 1
        
        return {
            'by_category': category_stats,
            'by_severity': severity_stats,
            'by_platform': platform_stats,
            'total_errors': len(self.errors),
            'timestamp': datetime.now().isoformat()
        }
    
    def export_errors(self, output_file: str, include_resolved: bool = True) -> bool:
        """導出錯誤信息"""
        try:
            errors_to_export = []
            
            for error in self.errors.values():
                if not include_resolved and error.resolved:
                    continue
                
                error_dict = asdict(error)
                # 轉換datetime為字符串
                for key, value in error_dict.items():
                    if isinstance(value, datetime):
                        error_dict[key] = value.isoformat()
                    elif hasattr(value, 'value'):  # Enum
                        error_dict[key] = value.value
                
                errors_to_export.append(error_dict)
            
            # 寫入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'errors': errors_to_export,
                    'statistics': self.get_statistics(),
                    'summary': self.get_error_summary(),
                    'export_time': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            logging.info(f"錯誤信息已導出到: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"導出錯誤信息失敗: {e}")
            return False
    
    def shutdown(self):
        """關閉錯誤處理管理器"""
        try:
            logging.info("正在關閉錯誤處理管理器...")
            
            # 設置關閉事件
            self.shutdown_event.set()
            
            # 等待背景任務完成
            for future in self.background_tasks:
                try:
                    future.result(timeout=5)
                except Exception as e:
                    logging.warning(f"背景任務關閉異常: {e}")
            
            # 關閉線程池
            self.executor.shutdown(wait=True, timeout=10)
            
            # 關閉Redis連接
            if self.redis_client:
                self.redis_client.close()
            
            logging.info("錯誤處理管理器已關閉")
            
        except Exception as e:
            logging.error(f"關閉錯誤處理管理器失敗: {e}")


if __name__ == "__main__":
    # 測試錯誤處理管理器
    import time
    
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建錯誤處理管理器
    error_manager = ErrorHandlingManager(
        retry_config=RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=3,
            base_delay=1.0
        ),
        notification_config=NotificationConfig(
            enabled=True,
            email_enabled=False,  # 測試時關閉郵件
            severity_threshold=ErrorSeverity.MEDIUM
        )
    )
    
    try:
        # 模擬一些錯誤
        print("\n=== 測試錯誤處理管理器 ===")
        
        # 測試網路錯誤
        network_error = ConnectionError("Connection timeout")
        error_id1 = error_manager.handle_error(
            job_id="test_job_1",
            platform="linkedin",
            error=network_error,
            context={'critical_job': True}
        )
        print(f"處理網路錯誤: {error_id1}")
        
        # 測試認證錯誤
        auth_error = PermissionError("Authentication failed")
        error_id2 = error_manager.handle_error(
            job_id="test_job_2",
            platform="indeed",
            error=auth_error
        )
        print(f"處理認證錯誤: {error_id2}")
        
        # 測試解析錯誤
        parse_error = ValueError("Invalid JSON format")
        error_id3 = error_manager.handle_error(
            job_id="test_job_3",
            platform="google",
            error=parse_error
        )
        print(f"處理解析錯誤: {error_id3}")
        
        # 等待一段時間讓重試處理
        print("\n等待重試處理...")
        time.sleep(5)
        
        # 顯示統計信息
        print("\n=== 統計信息 ===")
        stats = error_manager.get_statistics()
        for key, value in stats.items():
            if key != 'error_patterns':
                print(f"{key}: {value}")
        
        # 顯示錯誤摘要
        print("\n=== 錯誤摘要 ===")
        summary = error_manager.get_error_summary()
        print(f"按類別: {summary['by_category']}")
        print(f"按嚴重程度: {summary['by_severity']}")
        print(f"按平台: {summary['by_platform']}")
        
        # 手動解決一個錯誤
        print(f"\n手動解決錯誤: {error_id2}")
        error_manager.resolve_error(error_id2, "manual_fix")
        
        # 導出錯誤信息
        export_file = "error_export_test.json"
        if error_manager.export_errors(export_file):
            print(f"錯誤信息已導出到: {export_file}")
        
        print("\n測試完成")
        
    except KeyboardInterrupt:
        print("\n收到中斷信號")
    finally:
        # 關閉管理器
        error_manager.shutdown()
        print("錯誤處理管理器已關閉")