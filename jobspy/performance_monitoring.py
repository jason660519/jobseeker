"""效能監控模組

提供爬蟲效能監控、指標收集和分析功能。
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import statistics
from functools import wraps
import asyncio


class MetricType(Enum):
    """指標類型枚舉"""
    REQUEST_COUNT = "request_count"
    SUCCESS_COUNT = "success_count"
    ERROR_COUNT = "error_count"
    RESPONSE_TIME = "response_time"
    RATE_LIMIT_HIT = "rate_limit_hit"
    RETRY_COUNT = "retry_count"
    DATA_QUALITY_SCORE = "data_quality_score"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


class AlertLevel(Enum):
    """警報級別枚舉"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricEntry:
    """指標條目"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    source: str  # 爬蟲來源 (linkedin, indeed, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """效能警報"""
    timestamp: datetime
    level: AlertLevel
    message: str
    metric_type: MetricType
    current_value: float
    threshold: float
    source: str


@dataclass
class PerformanceStats:
    """效能統計"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    avg_data_quality_score: float = 0.0
    total_retries: int = 0
    rate_limit_hits: int = 0

    def calculate_rates(self):
        """計算各種比率"""
        if self.total_requests > 0:
            self.success_rate = self.successful_requests / self.total_requests
            self.error_rate = self.failed_requests / self.total_requests


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.metrics: deque = deque(maxlen=max_entries)
        self.alerts: List[PerformanceAlert] = []
        self.thresholds: Dict[MetricType, Dict[str, float]] = {
            MetricType.RESPONSE_TIME: {"warning": 5.0, "error": 10.0},
            MetricType.ERROR_COUNT: {"warning": 10, "error": 20},
            MetricType.SUCCESS_COUNT: {"warning": 0.8, "error": 0.6},  # 成功率閾值
        }
        self._lock = threading.Lock()
    
    def add_metric(self, metric_type: MetricType, value: float, source: str, 
                   metadata: Optional[Dict[str, Any]] = None):
        """添加指標"""
        with self._lock:
            entry = MetricEntry(
                timestamp=datetime.now(),
                metric_type=metric_type,
                value=value,
                source=source,
                metadata=metadata or {}
            )
            self.metrics.append(entry)
            self._check_thresholds(entry)
    
    def _check_thresholds(self, entry: MetricEntry):
        """檢查閾值並生成警報"""
        if entry.metric_type not in self.thresholds:
            return
        
        thresholds = self.thresholds[entry.metric_type]
        
        if entry.value >= thresholds.get("error", float('inf')):
            level = AlertLevel.ERROR
            threshold = thresholds["error"]
        elif entry.value >= thresholds.get("warning", float('inf')):
            level = AlertLevel.WARNING
            threshold = thresholds["warning"]
        else:
            return
        
        alert = PerformanceAlert(
            timestamp=entry.timestamp,
            level=level,
            message=f"{entry.metric_type.value} 超過閾值: {entry.value} >= {threshold}",
            metric_type=entry.metric_type,
            current_value=entry.value,
            threshold=threshold,
            source=entry.source
        )
        self.alerts.append(alert)
    
    def get_stats(self, source: Optional[str] = None, 
                  time_window: Optional[timedelta] = None) -> PerformanceStats:
        """獲取效能統計"""
        with self._lock:
            filtered_metrics = self._filter_metrics(source, time_window)
            return self._calculate_stats(filtered_metrics)
    
    def _filter_metrics(self, source: Optional[str], 
                       time_window: Optional[timedelta]) -> List[MetricEntry]:
        """過濾指標"""
        filtered = list(self.metrics)
        
        if source:
            filtered = [m for m in filtered if m.source == source]
        
        if time_window:
            cutoff = datetime.now() - time_window
            filtered = [m for m in filtered if m.timestamp >= cutoff]
        
        return filtered
    
    def _calculate_stats(self, metrics: List[MetricEntry]) -> PerformanceStats:
        """計算統計數據"""
        stats = PerformanceStats()
        
        if not metrics:
            return stats
        
        # 按類型分組指標
        by_type = defaultdict(list)
        for metric in metrics:
            by_type[metric.metric_type].append(metric.value)
        
        # 計算基本統計
        stats.total_requests = len(by_type.get(MetricType.REQUEST_COUNT, []))
        stats.successful_requests = len(by_type.get(MetricType.SUCCESS_COUNT, []))
        stats.failed_requests = len(by_type.get(MetricType.ERROR_COUNT, []))
        stats.total_retries = len(by_type.get(MetricType.RETRY_COUNT, []))
        stats.rate_limit_hits = len(by_type.get(MetricType.RATE_LIMIT_HIT, []))
        
        # 計算響應時間統計
        response_times = by_type.get(MetricType.RESPONSE_TIME, [])
        if response_times:
            stats.avg_response_time = statistics.mean(response_times)
            stats.min_response_time = min(response_times)
            stats.max_response_time = max(response_times)
        
        # 計算資料品質分數
        quality_scores = by_type.get(MetricType.DATA_QUALITY_SCORE, [])
        if quality_scores:
            stats.avg_data_quality_score = statistics.mean(quality_scores)
        
        # 計算快取命中率
        cache_hits = len(by_type.get(MetricType.CACHE_HIT, []))
        cache_misses = len(by_type.get(MetricType.CACHE_MISS, []))
        total_cache_requests = cache_hits + cache_misses
        if total_cache_requests > 0:
            stats.cache_hit_rate = cache_hits / total_cache_requests
        
        # 計算比率
        stats.calculate_rates()
        
        return stats
    
    def get_recent_alerts(self, count: int = 10) -> List[PerformanceAlert]:
        """獲取最近的警報"""
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:count]
    
    def export_metrics(self, filepath: str, source: Optional[str] = None,
                      time_window: Optional[timedelta] = None):
        """導出指標到文件"""
        with self._lock:
            filtered_metrics = self._filter_metrics(source, time_window)
            
            data = {
                "export_time": datetime.now().isoformat(),
                "source_filter": source,
                "time_window_hours": time_window.total_seconds() / 3600 if time_window else None,
                "metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "type": m.metric_type.value,
                        "value": m.value,
                        "source": m.source,
                        "metadata": m.metadata
                    }
                    for m in filtered_metrics
                ],
                "stats": self._stats_to_dict(self._calculate_stats(filtered_metrics))
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _stats_to_dict(self, stats: PerformanceStats) -> Dict[str, Any]:
        """將統計對象轉換為字典"""
        return {
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "avg_response_time": stats.avg_response_time,
            "min_response_time": stats.min_response_time if stats.min_response_time != float('inf') else 0,
            "max_response_time": stats.max_response_time,
            "success_rate": stats.success_rate,
            "error_rate": stats.error_rate,
            "cache_hit_rate": stats.cache_hit_rate,
            "avg_data_quality_score": stats.avg_data_quality_score,
            "total_retries": stats.total_retries,
            "rate_limit_hits": stats.rate_limit_hits
        }


class ScrapingMetrics:
    """爬蟲指標管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.collector = MetricsCollector()
            self.initialized = True
    
    def record_request(self, source: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄請求"""
        self.collector.add_metric(MetricType.REQUEST_COUNT, 1, source, metadata)
    
    def record_success(self, source: str, response_time: float, 
                      metadata: Optional[Dict[str, Any]] = None):
        """記錄成功請求"""
        self.collector.add_metric(MetricType.SUCCESS_COUNT, 1, source, metadata)
        self.collector.add_metric(MetricType.RESPONSE_TIME, response_time, source, metadata)
    
    def record_error(self, source: str, error_type: str, 
                    metadata: Optional[Dict[str, Any]] = None):
        """記錄錯誤"""
        metadata = metadata or {}
        metadata['error_type'] = error_type
        self.collector.add_metric(MetricType.ERROR_COUNT, 1, source, metadata)
    
    def record_retry(self, source: str, attempt: int, 
                    metadata: Optional[Dict[str, Any]] = None):
        """記錄重試"""
        metadata = metadata or {}
        metadata['attempt'] = attempt
        self.collector.add_metric(MetricType.RETRY_COUNT, 1, source, metadata)
    
    def record_rate_limit(self, source: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄速率限制"""
        self.collector.add_metric(MetricType.RATE_LIMIT_HIT, 1, source, metadata)
    
    def record_cache_hit(self, source: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄快取命中"""
        self.collector.add_metric(MetricType.CACHE_HIT, 1, source, metadata)
    
    def record_cache_miss(self, source: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄快取未命中"""
        self.collector.add_metric(MetricType.CACHE_MISS, 1, source, metadata)
    
    def record_data_quality(self, source: str, score: float, 
                           metadata: Optional[Dict[str, Any]] = None):
        """記錄資料品質分數"""
        self.collector.add_metric(MetricType.DATA_QUALITY_SCORE, score, source, metadata)
    
    def get_stats(self, source: Optional[str] = None, 
                  hours: Optional[int] = None) -> PerformanceStats:
        """獲取統計數據"""
        time_window = timedelta(hours=hours) if hours else None
        return self.collector.get_stats(source, time_window)
    
    def get_alerts(self, count: int = 10) -> List[PerformanceAlert]:
        """獲取警報"""
        return self.collector.get_recent_alerts(count)
    
    def export_report(self, filepath: str, source: Optional[str] = None, 
                     hours: Optional[int] = None):
        """導出效能報告"""
        time_window = timedelta(hours=hours) if hours else None
        self.collector.export_metrics(filepath, source, time_window)


def performance_monitor(source: str):
    """效能監控裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = ScrapingMetrics()
            start_time = time.time()
            
            try:
                metrics.record_request(source)
                result = func(*args, **kwargs)
                
                response_time = time.time() - start_time
                metrics.record_success(source, response_time)
                
                return result
            except Exception as e:
                metrics.record_error(source, type(e).__name__)
                raise
        
        return wrapper
    return decorator


def async_performance_monitor(source: str):
    """非同步效能監控裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = ScrapingMetrics()
            start_time = time.time()
            
            try:
                metrics.record_request(source)
                result = await func(*args, **kwargs)
                
                response_time = time.time() - start_time
                metrics.record_success(source, response_time)
                
                return result
            except Exception as e:
                metrics.record_error(source, type(e).__name__)
                raise
        
        return wrapper
    return decorator


class PerformanceDashboard:
    """效能儀表板"""
    
    def __init__(self, metrics: ScrapingMetrics):
        self.metrics = metrics
    
    def print_summary(self, source: Optional[str] = None, hours: Optional[int] = 24):
        """打印效能摘要"""
        stats = self.metrics.get_stats(source, hours)
        alerts = self.metrics.get_alerts(5)
        
        print("\n=== 爬蟲效能摘要 ===")
        if source:
            print(f"來源: {source}")
        if hours:
            print(f"時間範圍: 最近 {hours} 小時")
        
        print(f"\n📊 基本統計:")
        print(f"  總請求數: {stats.total_requests}")
        print(f"  成功請求: {stats.successful_requests}")
        print(f"  失敗請求: {stats.failed_requests}")
        print(f"  成功率: {stats.success_rate:.2%}")
        print(f"  錯誤率: {stats.error_rate:.2%}")
        
        print(f"\n⏱️ 響應時間:")
        print(f"  平均: {stats.avg_response_time:.2f}s")
        print(f"  最小: {stats.min_response_time:.2f}s")
        print(f"  最大: {stats.max_response_time:.2f}s")
        
        print(f"\n🔄 其他指標:")
        print(f"  重試次數: {stats.total_retries}")
        print(f"  速率限制: {stats.rate_limit_hits}")
        print(f"  快取命中率: {stats.cache_hit_rate:.2%}")
        print(f"  平均資料品質: {stats.avg_data_quality_score:.2f}")
        
        if alerts:
            print(f"\n🚨 最近警報:")
            for alert in alerts:
                emoji = {"warning": "⚠️", "error": "❌", "critical": "🔥"}.get(alert.level.value, "ℹ️")
                print(f"  {emoji} [{alert.timestamp.strftime('%H:%M:%S')}] {alert.message}")
        
        print("\n" + "="*50)


# 全域指標實例
metrics = ScrapingMetrics()


# 便利函數
def get_performance_stats(source: Optional[str] = None, hours: Optional[int] = None) -> PerformanceStats:
    """獲取效能統計的便利函數"""
    return metrics.get_stats(source, hours)


def show_performance_dashboard(source: Optional[str] = None, hours: Optional[int] = 24):
    """顯示效能儀表板的便利函數"""
    dashboard = PerformanceDashboard(metrics)
    dashboard.print_summary(source, hours)


def export_performance_report(filepath: str, source: Optional[str] = None, hours: Optional[int] = None):
    """導出效能報告的便利函數"""
    metrics.export_report(filepath, source, hours)
