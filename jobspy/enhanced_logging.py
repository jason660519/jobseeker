"""增強的日誌記錄系統

此模組提供結構化日誌記錄、效能監控和詳細的日誌功能。
"""

from __future__ import annotations

import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """日誌級別枚舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """日誌分類枚舉"""
    SCRAPING = "scraping"
    NETWORK = "network"
    PARSING = "parsing"
    PERFORMANCE = "performance"
    ERROR = "error"
    CACHE = "cache"
    GENERAL = "general"


@dataclass
class LogEntry:
    """結構化日誌條目"""
    timestamp: str
    level: str
    category: str
    site: Optional[str]
    message: str
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None
    function_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)
    
    def to_json(self) -> str:
        """轉換為 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class PerformanceMetrics:
    """效能指標收集器"""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_duration': 0.0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'site_metrics': {},
            'error_types': {},
            'hourly_stats': {}
        }
        self._lock = threading.Lock()
    
    def record_request(self, site: str, duration: float, success: bool, error_type: str = None):
        """記錄請求指標"""
        with self._lock:
            self.metrics['request_count'] += 1
            self.metrics['total_duration'] += duration
            
            if success:
                self.metrics['success_count'] += 1
            else:
                self.metrics['error_count'] += 1
                if error_type:
                    self.metrics['error_types'][error_type] = self.metrics['error_types'].get(error_type, 0) + 1
            
            # 更新響應時間統計
            self.metrics['avg_response_time'] = self.metrics['total_duration'] / self.metrics['request_count']
            self.metrics['min_response_time'] = min(self.metrics['min_response_time'], duration)
            self.metrics['max_response_time'] = max(self.metrics['max_response_time'], duration)
            
            # 網站特定指標
            if site not in self.metrics['site_metrics']:
                self.metrics['site_metrics'][site] = {
                    'requests': 0, 'successes': 0, 'errors': 0, 'total_time': 0.0
                }
            
            site_metrics = self.metrics['site_metrics'][site]
            site_metrics['requests'] += 1
            site_metrics['total_time'] += duration
            if success:
                site_metrics['successes'] += 1
            else:
                site_metrics['errors'] += 1
            
            # 每小時統計
            hour_key = datetime.now().strftime('%Y-%m-%d-%H')
            if hour_key not in self.metrics['hourly_stats']:
                self.metrics['hourly_stats'][hour_key] = {'requests': 0, 'successes': 0, 'errors': 0}
            
            hourly = self.metrics['hourly_stats'][hour_key]
            hourly['requests'] += 1
            if success:
                hourly['successes'] += 1
            else:
                hourly['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取當前指標"""
        with self._lock:
            # 計算成功率
            success_rate = (self.metrics['success_count'] / self.metrics['request_count'] * 100) if self.metrics['request_count'] > 0 else 0
            
            # 計算網站成功率
            for site, metrics in self.metrics['site_metrics'].items():
                if metrics['requests'] > 0:
                    metrics['success_rate'] = metrics['successes'] / metrics['requests'] * 100
                    metrics['avg_response_time'] = metrics['total_time'] / metrics['requests']
            
            return {
                **self.metrics,
                'success_rate': success_rate
            }
    
    def reset_metrics(self):
        """重置指標"""
        with self._lock:
            self.__init__()


class EnhancedLogger:
    """增強的日誌記錄器"""
    
    def __init__(self, name: str, log_file: Optional[str] = None, 
                 enable_console: bool = True, enable_json: bool = False):
        """
        初始化增強日誌記錄器
        
        Args:
            name: 日誌記錄器名稱
            log_file: 日誌檔案路徑
            enable_console: 是否啟用控制台輸出
            enable_json: 是否啟用 JSON 格式日誌
        """
        self.name = name
        self.logger = logging.getLogger(f"JobSpy.Enhanced.{name}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 效能指標
        self.metrics = PerformanceMetrics()
        
        # 日誌條目緩存
        self.log_entries: List[LogEntry] = []
        self._log_lock = threading.Lock()
        
        # 設置處理器
        self._setup_handlers(log_file, enable_console, enable_json)
    
    def _setup_handlers(self, log_file: Optional[str], enable_console: bool, enable_json: bool):
        """設置日誌處理器"""
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台處理器
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 檔案處理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # JSON 格式日誌檔案
            if enable_json:
                json_file = log_path.with_suffix('.json')
                json_handler = logging.FileHandler(json_file, encoding='utf-8')
                json_formatter = logging.Formatter('%(message)s')
                json_handler.setFormatter(json_formatter)
                self.logger.addHandler(json_handler)
    
    def _create_log_entry(self, level: LogLevel, category: LogCategory, 
                         message: str, site: Optional[str] = None, 
                         duration: Optional[float] = None, 
                         metadata: Optional[Dict[str, Any]] = None,
                         function_name: Optional[str] = None) -> LogEntry:
        """創建結構化日誌條目"""
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            site=site,
            message=message,
            duration=duration,
            metadata=metadata,
            thread_id=str(threading.current_thread().ident),
            function_name=function_name
        )
    
    def log(self, level: LogLevel, category: LogCategory, message: str, 
           site: Optional[str] = None, duration: Optional[float] = None,
           metadata: Optional[Dict[str, Any]] = None, 
           function_name: Optional[str] = None):
        """記錄結構化日誌"""
        entry = self._create_log_entry(level, category, message, site, duration, metadata, function_name)
        
        with self._log_lock:
            self.log_entries.append(entry)
            # 保持最近 1000 條日誌
            if len(self.log_entries) > 1000:
                self.log_entries = self.log_entries[-1000:]
        
        # 記錄到標準日誌
        log_message = f"[{category.value}] {message}"
        if site:
            log_message = f"[{site}] {log_message}"
        if duration:
            log_message += f" (耗時: {duration:.3f}s)"
        if metadata:
            log_message += f" | 元數據: {json.dumps(metadata, ensure_ascii=False)}"
        
        getattr(self.logger, level.value.lower())(log_message)
    
    def debug(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """記錄 DEBUG 級別日誌"""
        self.log(LogLevel.DEBUG, category, message, **kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """記錄 INFO 級別日誌"""
        self.log(LogLevel.INFO, category, message, **kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """記錄 WARNING 級別日誌"""
        self.log(LogLevel.WARNING, category, message, **kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
        """記錄 ERROR 級別日誌"""
        self.log(LogLevel.ERROR, category, message, **kwargs)
    
    def critical(self, message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
        """記錄 CRITICAL 級別日誌"""
        self.log(LogLevel.CRITICAL, category, message, **kwargs)
    
    def log_performance(self, site: str, duration: float, success: bool, 
                       operation: str, error_type: str = None, 
                       metadata: Optional[Dict[str, Any]] = None):
        """記錄效能日誌"""
        self.metrics.record_request(site, duration, success, error_type)
        
        status = "成功" if success else "失敗"
        message = f"{operation} {status}"
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        category = LogCategory.PERFORMANCE
        
        perf_metadata = {
            'operation': operation,
            'success': success,
            'error_type': error_type
        }
        if metadata:
            perf_metadata.update(metadata)
        
        self.log(level, category, message, site, duration, perf_metadata)
    
    def get_recent_logs(self, count: int = 100, 
                       level: Optional[LogLevel] = None,
                       category: Optional[LogCategory] = None,
                       site: Optional[str] = None) -> List[LogEntry]:
        """獲取最近的日誌條目"""
        with self._log_lock:
            logs = self.log_entries[-count:]
            
            # 過濾條件
            if level:
                logs = [log for log in logs if log.level == level.value]
            if category:
                logs = [log for log in logs if log.category == category.value]
            if site:
                logs = [log for log in logs if log.site == site]
            
            return logs
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取效能指標"""
        return self.metrics.get_metrics()
    
    def export_logs(self, file_path: str, format: str = 'json'):
        """匯出日誌到檔案"""
        with self._log_lock:
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([entry.to_dict() for entry in self.log_entries], 
                             f, ensure_ascii=False, indent=2)
            elif format.lower() == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if self.log_entries:
                        writer = csv.DictWriter(f, fieldnames=self.log_entries[0].to_dict().keys())
                        writer.writeheader()
                        for entry in self.log_entries:
                            writer.writerow(entry.to_dict())


def performance_logger(site: str = None, operation: str = None, 
                      logger: EnhancedLogger = None):
    """效能日誌裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__
            op_name = operation or func_name
            site_name = site or 'unknown'
            
            # 如果沒有提供 logger，嘗試從參數中獲取
            log_instance = logger
            if not log_instance:
                # 嘗試從 self 獲取 logger
                if args and hasattr(args[0], 'logger') and isinstance(args[0].logger, EnhancedLogger):
                    log_instance = args[0].logger
                else:
                    # 創建臨時 logger
                    log_instance = EnhancedLogger(f"temp_{func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_instance.log_performance(
                    site_name, duration, True, op_name,
                    metadata={'function': func_name}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_instance.log_performance(
                    site_name, duration, False, op_name, 
                    error_type=type(e).__name__,
                    metadata={'function': func_name, 'error': str(e)}
                )
                raise
        return wrapper
    return decorator


def async_performance_logger(site: str = None, operation: str = None, 
                             logger: EnhancedLogger = None):
    """非同步效能日誌裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__
            op_name = operation or func_name
            site_name = site or 'unknown'
            
            # 如果沒有提供 logger，嘗試從參數中獲取
            log_instance = logger
            if not log_instance:
                # 嘗試從 self 獲取 logger
                if args and hasattr(args[0], 'logger') and isinstance(args[0].logger, EnhancedLogger):
                    log_instance = args[0].logger
                else:
                    # 創建臨時 logger
                    log_instance = EnhancedLogger(f"temp_{func_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                log_instance.log_performance(
                    site_name, duration, True, op_name,
                    metadata={'function': func_name}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_instance.log_performance(
                    site_name, duration, False, op_name, 
                    error_type=type(e).__name__,
                    metadata={'function': func_name, 'error': str(e)}
                )
                raise
        return wrapper
    return decorator


# 全域日誌管理器
class LoggerManager:
    """全域日誌管理器"""
    
    _instance = None
    _loggers: Dict[str, EnhancedLogger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_logger(self, name: str, **kwargs) -> EnhancedLogger:
        """獲取或創建日誌記錄器"""
        if name not in self._loggers:
            self._loggers[name] = EnhancedLogger(name, **kwargs)
        return self._loggers[name]
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有日誌記錄器的指標"""
        return {name: logger.get_performance_metrics() 
                for name, logger in self._loggers.items()}
    
    def export_all_logs(self, directory: str):
        """匯出所有日誌"""
        log_dir = Path(directory)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        for name, logger in self._loggers.items():
            log_file = log_dir / f"{name}_logs.json"
            logger.export_logs(str(log_file))


# 全域實例
logger_manager = LoggerManager()


# 便利函數
def get_enhanced_logger(name: str, **kwargs) -> EnhancedLogger:
    """獲取增強日誌記錄器"""
    return logger_manager.get_logger(name, **kwargs)


def create_site_logger(site_name: str, log_dir: str = "logs") -> EnhancedLogger:
    """為特定網站創建日誌記錄器"""
    log_file = Path(log_dir) / f"{site_name}.log"
    return get_enhanced_logger(
        site_name,
        log_file=str(log_file),
        enable_console=True,
        enable_json=True
    )