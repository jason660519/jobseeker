#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版錯誤處理管理器
提供更智能的錯誤處理、恢復機制和監控功能

Author: jobseeker Team
Date: 2025-01-27
"""

import time
import json
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from pathlib import Path

from .error_handling import (
    ScrapingError, NetworkError, RateLimitError, ParsingError,
    AuthenticationError, TimeoutError, ErrorType, global_error_handler
)
from .enhanced_logging import get_enhanced_logger, LogCategory


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"           # 可忽略的錯誤
    MEDIUM = "medium"     # 需要關注的錯誤
    HIGH = "high"         # 嚴重錯誤
    CRITICAL = "critical" # 致命錯誤


class RecoveryAction(Enum):
    """恢復動作"""
    RETRY = "retry"                    # 重試
    FALLBACK = "fallback"              # 使用備用方案
    SKIP = "skip"                      # 跳過
    ABORT = "abort"                    # 中止
    NOTIFY = "notify"                  # 通知管理員


@dataclass
class ErrorContext:
    """錯誤上下文資訊"""
    site: str
    operation: str
    timestamp: datetime
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    request_url: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    retry_count: int = 0
    session_id: Optional[str] = None


@dataclass
class ErrorRecord:
    """錯誤記錄"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    original_exception: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_action: Optional[RecoveryAction] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class CircuitBreaker:
    """熔斷器 - 防止錯誤級聯"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        初始化熔斷器
        
        Args:
            failure_threshold: 失敗閾值
            recovery_timeout: 恢復超時時間（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = get_enhanced_logger("circuit_breaker")
    
    def can_execute(self) -> bool:
        """檢查是否可以執行操作"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info("熔斷器進入半開狀態", category=LogCategory.GENERAL)
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """記錄成功"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.logger.info("熔斷器重置為關閉狀態", category=LogCategory.GENERAL)
    
    def record_failure(self):
        """記錄失敗"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(
                f"熔斷器開啟，失敗次數: {self.failure_count}",
                category=LogCategory.ERROR,
                metadata={'failure_count': self.failure_count}
            )


class EnhancedErrorHandler:
    """增強版錯誤處理器"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        初始化增強版錯誤處理器
        
        Args:
            log_file: 錯誤日誌檔案路徑
        """
        self.logger = get_enhanced_logger("enhanced_error_handler")
        self.error_records: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_patterns: Dict[str, int] = {}
        self.log_file = log_file or "error_log.json"
        self.recovery_strategies: Dict[ErrorType, Callable] = {}
        
        # 初始化恢復策略
        self._init_recovery_strategies()
    
    def _init_recovery_strategies(self):
        """初始化恢復策略"""
        self.recovery_strategies = {
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.RATE_LIMIT: self._handle_rate_limit_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorType.AUTHENTICATION_ERROR: self._handle_auth_error,
            ErrorType.PARSING_ERROR: self._handle_parsing_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error
        }
    
    def handle_error(
        self, 
        error: Exception, 
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorRecord:
        """
        處理錯誤並創建錯誤記錄
        
        Args:
            error: 原始異常
            context: 錯誤上下文
            severity: 錯誤嚴重程度
            
        Returns:
            錯誤記錄
        """
        # 生成錯誤ID
        error_id = f"{context.site}_{int(time.time())}_{hash(str(error))}"
        
        # 轉換為統一異常類型
        scraping_error = global_error_handler.handle_error(error, asdict(context))
        
        # 創建錯誤記錄
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=scraping_error.error_type,
            severity=severity,
            message=str(scraping_error),
            context=context,
            original_exception=str(error),
            stack_trace=traceback.format_exc()
        )
        
        # 記錄錯誤
        self.error_records.append(error_record)
        
        # 更新錯誤模式統計
        pattern_key = f"{context.site}:{scraping_error.error_type.value}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # 更新熔斷器
        circuit_breaker = self._get_circuit_breaker(context.site)
        circuit_breaker.record_failure()
        
        # 記錄日誌
        self.logger.error(
            f"錯誤處理: {error_record.error_id}",
            category=LogCategory.ERROR,
            metadata={
                'error_type': scraping_error.error_type.value,
                'severity': severity.value,
                'site': context.site,
                'operation': context.operation
            }
        )
        
        # 保存到檔案
        self._save_error_record(error_record)
        
        return error_record
    
    def get_recovery_action(
        self, 
        error_record: ErrorRecord
    ) -> RecoveryAction:
        """
        獲取恢復動作
        
        Args:
            error_record: 錯誤記錄
            
        Returns:
            恢復動作
        """
        # 檢查熔斷器狀態
        circuit_breaker = self._get_circuit_breaker(error_record.context.site)
        if not circuit_breaker.can_execute():
            return RecoveryAction.ABORT
        
        # 根據錯誤類型和嚴重程度決定恢復動作
        if error_record.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.ABORT
        elif error_record.severity == ErrorSeverity.HIGH:
            if error_record.context.retry_count >= 3:
                return RecoveryAction.FALLBACK
            return RecoveryAction.RETRY
        elif error_record.severity == ErrorSeverity.MEDIUM:
            if error_record.context.retry_count >= 2:
                return RecoveryAction.SKIP
            return RecoveryAction.RETRY
        else:  # LOW
            return RecoveryAction.SKIP
    
    def execute_recovery(
        self, 
        error_record: ErrorRecord,
        recovery_action: RecoveryAction
    ) -> bool:
        """
        執行恢復動作
        
        Args:
            error_record: 錯誤記錄
            recovery_action: 恢復動作
            
        Returns:
            是否成功恢復
        """
        try:
            recovery_strategy = self.recovery_strategies.get(error_record.error_type)
            if recovery_strategy:
                success = recovery_strategy(error_record, recovery_action)
                if success:
                    error_record.resolved = True
                    error_record.resolved_at = datetime.now()
                    error_record.recovery_action = recovery_action
                    
                    # 更新熔斷器
                    circuit_breaker = self._get_circuit_breaker(error_record.context.site)
                    circuit_breaker.record_success()
                    
                    self.logger.info(
                        f"錯誤恢復成功: {error_record.error_id}",
                        category=LogCategory.GENERAL,
                        metadata={'recovery_action': recovery_action.value}
                    )
                
                return success
            else:
                self.logger.warning(
                    f"沒有找到恢復策略: {error_record.error_type.value}",
                    category=LogCategory.ERROR
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"恢復動作執行失敗: {str(e)}",
                category=LogCategory.ERROR,
                metadata={'error_id': error_record.error_id}
            )
            return False
    
    def _get_circuit_breaker(self, site: str) -> CircuitBreaker:
        """獲取或創建熔斷器"""
        if site not in self.circuit_breakers:
            self.circuit_breakers[site] = CircuitBreaker()
        return self.circuit_breakers[site]
    
    def _handle_network_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理網路錯誤"""
        if action == RecoveryAction.RETRY:
            # 等待一段時間後重試
            time.sleep(min(2 ** error_record.context.retry_count, 30))
            return True
        elif action == RecoveryAction.FALLBACK:
            # 使用備用代理或不同的請求方式
            return True
        return False
    
    def _handle_rate_limit_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理速率限制錯誤"""
        if action == RecoveryAction.RETRY:
            # 等待更長時間
            wait_time = min(60 * (2 ** error_record.context.retry_count), 300)
            time.sleep(wait_time)
            return True
        return False
    
    def _handle_timeout_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理超時錯誤"""
        if action == RecoveryAction.RETRY:
            # 增加超時時間
            time.sleep(5)
            return True
        return False
    
    def _handle_auth_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理認證錯誤"""
        if action == RecoveryAction.FALLBACK:
            # 嘗試不同的認證方式
            return True
        return False
    
    def _handle_parsing_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理解析錯誤"""
        if action == RecoveryAction.SKIP:
            # 跳過這個項目
            return True
        return False
    
    def _handle_unknown_error(
        self, 
        error_record: ErrorRecord, 
        action: RecoveryAction
    ) -> bool:
        """處理未知錯誤"""
        if action == RecoveryAction.RETRY:
            time.sleep(5)
            return True
        return False
    
    def _save_error_record(self, error_record: ErrorRecord):
        """保存錯誤記錄到檔案"""
        try:
            # 轉換為可序列化的格式
            record_dict = asdict(error_record)
            record_dict['context']['timestamp'] = record_dict['context']['timestamp'].isoformat()
            if record_dict['resolved_at']:
                record_dict['resolved_at'] = record_dict['resolved_at'].isoformat()
            
            # 保存到檔案
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record_dict, ensure_ascii=False) + '\n')
                
        except Exception as e:
            self.logger.error(f"保存錯誤記錄失敗: {str(e)}", category=LogCategory.ERROR)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計資訊"""
        total_errors = len(self.error_records)
        resolved_errors = sum(1 for r in self.error_records if r.resolved)
        
        # 按錯誤類型統計
        error_type_stats = {}
        for record in self.error_records:
            error_type = record.error_type.value
            error_type_stats[error_type] = error_type_stats.get(error_type, 0) + 1
        
        # 按網站統計
        site_stats = {}
        for record in self.error_records:
            site = record.context.site
            site_stats[site] = site_stats.get(site, 0) + 1
        
        # 按嚴重程度統計
        severity_stats = {}
        for record in self.error_records:
            severity = record.severity.value
            severity_stats[severity] = severity_stats.get(severity, 0) + 1
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'resolution_rate': resolved_errors / total_errors if total_errors > 0 else 0,
            'error_type_distribution': error_type_stats,
            'site_distribution': site_stats,
            'severity_distribution': severity_stats,
            'error_patterns': self.error_patterns,
            'circuit_breaker_status': {
                site: {
                    'state': cb.state,
                    'failure_count': cb.failure_count
                }
                for site, cb in self.circuit_breakers.items()
            }
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[ErrorRecord]:
        """獲取最近的錯誤"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            record for record in self.error_records
            if record.context.timestamp >= cutoff_time
        ]
    
    def cleanup_old_errors(self, days: int = 7):
        """清理舊的錯誤記錄"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.error_records = [
            record for record in self.error_records
            if record.context.timestamp >= cutoff_time
        ]
        self.logger.info(f"清理了 {days} 天前的錯誤記錄", category=LogCategory.GENERAL)


# 全域增強錯誤處理器實例
enhanced_error_handler = EnhancedErrorHandler()


def with_error_handling(
    site: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
):
    """
    錯誤處理裝飾器
    
    Args:
        site: 網站名稱
        operation: 操作名稱
        severity: 錯誤嚴重程度
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            context = ErrorContext(
                site=site,
                operation=operation,
                timestamp=datetime.now(),
                retry_count=kwargs.get('retry_count', 0)
            )
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_record = enhanced_error_handler.handle_error(e, context, severity)
                recovery_action = enhanced_error_handler.get_recovery_action(error_record)
                
                if recovery_action == RecoveryAction.RETRY:
                    kwargs['retry_count'] = context.retry_count + 1
                    return await async_wrapper(*args, **kwargs)
                elif recovery_action == RecoveryAction.ABORT:
                    raise
                else:
                    return None
        
        def sync_wrapper(*args, **kwargs):
            context = ErrorContext(
                site=site,
                operation=operation,
                timestamp=datetime.now(),
                retry_count=kwargs.get('retry_count', 0)
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_record = enhanced_error_handler.handle_error(e, context, severity)
                recovery_action = enhanced_error_handler.get_recovery_action(error_record)
                
                if recovery_action == RecoveryAction.RETRY:
                    kwargs['retry_count'] = context.retry_count + 1
                    return sync_wrapper(*args, **kwargs)
                elif recovery_action == RecoveryAction.ABORT:
                    raise
                else:
                    return None
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
