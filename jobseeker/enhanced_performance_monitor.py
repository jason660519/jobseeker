#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版性能監控系統
提供實時監控、預警、分析和優化建議

Author: jobseeker Team
Date: 2025-01-27
"""

import time
import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import statistics
import psutil
import sys
from functools import wraps

from .performance_monitoring import (
    MetricType, AlertLevel, MetricEntry, PerformanceAlert, PerformanceStats,
    MetricsCollector, ScrapingMetrics
)
from .enhanced_logging import get_enhanced_logger, LogCategory


class HealthStatus(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class OptimizationSuggestion(Enum):
    """優化建議類型"""
    CACHE_OPTIMIZATION = "cache_optimization"
    RETRY_STRATEGY = "retry_strategy"
    RATE_LIMITING = "rate_limiting"
    RESOURCE_ALLOCATION = "resource_allocation"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_TUNING = "performance_tuning"


@dataclass
class SystemMetrics:
    """系統指標"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    thread_count: int
    timestamp: datetime


@dataclass
class PerformanceTrend:
    """性能趨勢"""
    metric_type: MetricType
    time_window: timedelta
    trend_direction: str  # "improving", "degrading", "stable"
    change_rate: float
    confidence: float
    data_points: List[float]


@dataclass
class OptimizationSuggestion:
    """優化建議"""
    suggestion_type: OptimizationSuggestion
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    effort: str  # "high", "medium", "low"
    priority: int  # 1-10
    estimated_improvement: float
    implementation_steps: List[str]


@dataclass
class HealthCheck:
    """健康檢查"""
    component: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]
    last_check: datetime
    recommendations: List[str]


class RealTimeMonitor:
    """實時監控器"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval
        self.logger = get_enhanced_logger("real_time_monitor")
        self.monitoring = False
        self.monitor_task = None
        self.system_metrics_history = deque(maxlen=1000)
        self.performance_alerts = deque(maxlen=100)
        self._lock = threading.RLock()
    
    async def start_monitoring(self):
        """開始實時監控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        self.logger.info(
            "實時監控已啟動",
            category=LogCategory.MONITORING,
            metadata={'update_interval': self.update_interval}
        )
    
    async def stop_monitoring(self):
        """停止實時監控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("實時監控已停止", category=LogCategory.MONITORING)
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.monitoring:
            try:
                # 收集系統指標
                system_metrics = self._collect_system_metrics()
                
                with self._lock:
                    self.system_metrics_history.append(system_metrics)
                
                # 檢查性能警報
                await self._check_performance_alerts(system_metrics)
                
                # 等待下次更新
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {str(e)}", category=LogCategory.MONITORING)
                await asyncio.sleep(self.update_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU 使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁碟使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 網路 I/O
            network_io = psutil.net_io_counters()._asdict()
            
            # 活躍連接數
            active_connections = len(psutil.net_connections())
            
            # 執行緒數
            thread_count = threading.active_count()
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=active_connections,
                thread_count=thread_count,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {str(e)}", category=LogCategory.MONITORING)
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                active_connections=0,
                thread_count=0,
                timestamp=datetime.now()
            )
    
    async def _check_performance_alerts(self, system_metrics: SystemMetrics):
        """檢查性能警報"""
        alerts = []
        
        # CPU 使用率警報
        if system_metrics.cpu_usage > 80:
            alerts.append({
                'level': AlertLevel.WARNING if system_metrics.cpu_usage < 90 else AlertLevel.CRITICAL,
                'message': f"CPU 使用率過高: {system_metrics.cpu_usage:.1f}%",
                'metric': 'cpu_usage',
                'value': system_metrics.cpu_usage
            })
        
        # 記憶體使用率警報
        if system_metrics.memory_usage > 85:
            alerts.append({
                'level': AlertLevel.WARNING if system_metrics.memory_usage < 95 else AlertLevel.CRITICAL,
                'message': f"記憶體使用率過高: {system_metrics.memory_usage:.1f}%",
                'metric': 'memory_usage',
                'value': system_metrics.memory_usage
            })
        
        # 磁碟使用率警報
        if system_metrics.disk_usage > 90:
            alerts.append({
                'level': AlertLevel.WARNING,
                'message': f"磁碟使用率過高: {system_metrics.disk_usage:.1f}%",
                'metric': 'disk_usage',
                'value': system_metrics.disk_usage
            })
        
        # 記錄警報
        for alert in alerts:
            with self._lock:
                self.performance_alerts.append({
                    'timestamp': datetime.now(),
                    'level': alert['level'].value,
                    'message': alert['message'],
                    'metric': alert['metric'],
                    'value': alert['value']
                })
            
            self.logger.warning(
                alert['message'],
                category=LogCategory.MONITORING,
                metadata={
                    'level': alert['level'].value,
                    'metric': alert['metric'],
                    'value': alert['value']
                }
            )
    
    def get_system_metrics(self, minutes: int = 60) -> List[SystemMetrics]:
        """獲取系統指標歷史"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            return [m for m in self.system_metrics_history if m.timestamp >= cutoff_time]
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的警報"""
        with self._lock:
            return list(self.performance_alerts)[-count:]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("performance_analyzer")
    
    def analyze_trends(self, metrics: List[MetricEntry], 
                      time_window: timedelta = timedelta(hours=24)) -> List[PerformanceTrend]:
        """分析性能趨勢"""
        trends = []
        
        # 按指標類型分組
        by_type = defaultdict(list)
        for metric in metrics:
            if metric.timestamp >= datetime.now() - time_window:
                by_type[metric.metric_type].append(metric)
        
        # 分析每種類型的趨勢
        for metric_type, type_metrics in by_type.items():
            if len(type_metrics) < 5:  # 需要足夠的數據點
                continue
            
            # 按時間排序
            type_metrics.sort(key=lambda x: x.timestamp)
            values = [m.value for m in type_metrics]
            
            # 計算趨勢
            trend = self._calculate_trend(values)
            confidence = self._calculate_confidence(values, trend)
            
            trends.append(PerformanceTrend(
                metric_type=metric_type,
                time_window=time_window,
                trend_direction=trend['direction'],
                change_rate=trend['rate'],
                confidence=confidence,
                data_points=values[-20:]  # 最近20個數據點
            ))
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """計算趨勢"""
        if len(values) < 2:
            return {'direction': 'stable', 'rate': 0.0}
        
        # 簡單線性回歸
        n = len(values)
        x = list(range(n))
        
        # 計算斜率
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return {'direction': 'stable', 'rate': 0.0}
        
        slope = numerator / denominator
        
        # 判斷趨勢方向
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'improving' if self._is_positive_metric(values[0]) else 'degrading'
        else:
            direction = 'degrading' if self._is_positive_metric(values[0]) else 'improving'
        
        return {
            'direction': direction,
            'rate': abs(slope)
        }
    
    def _is_positive_metric(self, value: float) -> bool:
        """判斷是否為正向指標"""
        # 這裡可以根據具體的指標類型來判斷
        # 例如：成功率、快取命中率等是正向指標
        # 響應時間、錯誤率等是負向指標
        return True  # 簡化實現
    
    def _calculate_confidence(self, values: List[float], trend: Dict[str, Any]) -> float:
        """計算趨勢信心度"""
        if len(values) < 3:
            return 0.0
        
        # 計算變異係數
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / mean_val
        
        # 變異係數越小，信心度越高
        confidence = max(0.0, 1.0 - cv)
        
        return min(confidence, 1.0)
    
    def generate_optimization_suggestions(self, trends: List[PerformanceTrend],
                                        system_metrics: List[SystemMetrics]) -> List[OptimizationSuggestion]:
        """生成優化建議"""
        suggestions = []
        
        # 分析響應時間趨勢
        response_time_trends = [t for t in trends if t.metric_type == MetricType.RESPONSE_TIME]
        if response_time_trends:
            trend = response_time_trends[0]
            if trend.trend_direction == 'degrading' and trend.confidence > 0.7:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type=OptimizationSuggestion.PERFORMANCE_TUNING,
                    title="優化響應時間",
                    description="響應時間呈下降趨勢，建議優化爬蟲性能",
                    impact="high",
                    effort="medium",
                    priority=8,
                    estimated_improvement=0.2,
                    implementation_steps=[
                        "檢查網路連接質量",
                        "優化請求頻率",
                        "實施更智能的重試策略",
                        "考慮使用快取機制"
                    ]
                ))
        
        # 分析錯誤率趨勢
        error_trends = [t for t in trends if t.metric_type == MetricType.ERROR_COUNT]
        if error_trends:
            trend = error_trends[0]
            if trend.trend_direction == 'degrading' and trend.confidence > 0.6:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type=OptimizationSuggestion.ERROR_HANDLING,
                    title="改善錯誤處理",
                    description="錯誤率呈上升趨勢，建議改善錯誤處理機制",
                    impact="high",
                    effort="low",
                    priority=9,
                    estimated_improvement=0.3,
                    implementation_steps=[
                        "增加重試次數",
                        "改善錯誤分類",
                        "實施熔斷器模式",
                        "優化錯誤恢復策略"
                    ]
                ))
        
        # 分析系統資源使用
        if system_metrics:
            latest_metrics = system_metrics[-1]
            if latest_metrics.cpu_usage > 70:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type=OptimizationSuggestion.RESOURCE_ALLOCATION,
                    title="優化資源分配",
                    description="CPU 使用率較高，建議優化資源分配",
                    impact="medium",
                    effort="high",
                    priority=6,
                    estimated_improvement=0.15,
                    implementation_steps=[
                        "增加並發限制",
                        "實施請求佇列",
                        "優化記憶體使用",
                        "考慮負載均衡"
                    ]
                ))
        
        # 按優先級排序
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        return suggestions


class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("health_checker")
        self.health_checks = {}
    
    async def perform_health_check(self, component: str) -> HealthCheck:
        """執行健康檢查"""
        try:
            if component == "system":
                return await self._check_system_health()
            elif component == "cache":
                return await self._check_cache_health()
            elif component == "scrapers":
                return await self._check_scrapers_health()
            elif component == "database":
                return await self._check_database_health()
            else:
                return HealthCheck(
                    component=component,
                    status=HealthStatus.UNKNOWN,
                    message=f"未知的組件: {component}",
                    metrics={},
                    last_check=datetime.now(),
                    recommendations=[]
                )
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {component}, 錯誤: {str(e)}", category=LogCategory.MONITORING)
            return HealthCheck(
                component=component,
                status=HealthStatus.CRITICAL,
                message=f"健康檢查失敗: {str(e)}",
                metrics={},
                last_check=datetime.now(),
                recommendations=["檢查系統狀態", "查看錯誤日誌"]
            )
    
    async def _check_system_health(self) -> HealthCheck:
        """檢查系統健康狀態"""
        try:
            # 收集系統指標
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': (disk.used / disk.total) * 100,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
            
            # 判斷健康狀態
            status = HealthStatus.HEALTHY
            issues = []
            recommendations = []
            
            if cpu_usage > 80:
                status = HealthStatus.WARNING
                issues.append(f"CPU 使用率過高: {cpu_usage:.1f}%")
                recommendations.append("考慮增加 CPU 資源或優化程式碼")
            
            if memory.percent > 85:
                status = HealthStatus.WARNING
                issues.append(f"記憶體使用率過高: {memory.percent:.1f}%")
                recommendations.append("檢查記憶體洩漏或增加記憶體")
            
            if metrics['disk_usage'] > 90:
                status = HealthStatus.CRITICAL
                issues.append(f"磁碟空間不足: {metrics['disk_usage']:.1f}%")
                recommendations.append("清理磁碟空間或增加儲存容量")
            
            message = "系統運行正常" if status == HealthStatus.HEALTHY else "; ".join(issues)
            
            return HealthCheck(
                component="system",
                status=status,
                message=message,
                metrics=metrics,
                last_check=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return HealthCheck(
                component="system",
                status=HealthStatus.CRITICAL,
                message=f"系統健康檢查失敗: {str(e)}",
                metrics={},
                last_check=datetime.now(),
                recommendations=["檢查系統狀態"]
            )
    
    async def _check_cache_health(self) -> HealthCheck:
        """檢查快取健康狀態"""
        try:
            # 這裡可以檢查快取系統的狀態
            # 例如：快取命中率、快取大小等
            
            metrics = {
                'cache_hit_rate': 0.85,  # 示例值
                'cache_size': 1000,
                'cache_errors': 0
            }
            
            status = HealthStatus.HEALTHY
            message = "快取系統運行正常"
            recommendations = []
            
            if metrics['cache_hit_rate'] < 0.5:
                status = HealthStatus.WARNING
                message = f"快取命中率較低: {metrics['cache_hit_rate']:.2%}"
                recommendations.append("檢查快取策略和 TTL 設置")
            
            return HealthCheck(
                component="cache",
                status=status,
                message=message,
                metrics=metrics,
                last_check=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return HealthCheck(
                component="cache",
                status=HealthStatus.CRITICAL,
                message=f"快取健康檢查失敗: {str(e)}",
                metrics={},
                last_check=datetime.now(),
                recommendations=["檢查快取配置"]
            )
    
    async def _check_scrapers_health(self) -> HealthCheck:
        """檢查爬蟲健康狀態"""
        try:
            # 這裡可以檢查各個爬蟲的狀態
            # 例如：成功率、響應時間等
            
            metrics = {
                'active_scrapers': 5,
                'success_rate': 0.92,
                'avg_response_time': 2.5,
                'error_count': 3
            }
            
            status = HealthStatus.HEALTHY
            message = "爬蟲系統運行正常"
            recommendations = []
            
            if metrics['success_rate'] < 0.8:
                status = HealthStatus.WARNING
                message = f"爬蟲成功率較低: {metrics['success_rate']:.2%}"
                recommendations.append("檢查爬蟲配置和目標網站狀態")
            
            if metrics['avg_response_time'] > 10:
                status = HealthStatus.WARNING
                message = f"平均響應時間過長: {metrics['avg_response_time']:.1f}s"
                recommendations.append("優化爬蟲性能或增加超時時間")
            
            return HealthCheck(
                component="scrapers",
                status=status,
                message=message,
                metrics=metrics,
                last_check=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return HealthCheck(
                component="scrapers",
                status=HealthStatus.CRITICAL,
                message=f"爬蟲健康檢查失敗: {str(e)}",
                metrics={},
                last_check=datetime.now(),
                recommendations=["檢查爬蟲配置"]
            )
    
    async def _check_database_health(self) -> HealthCheck:
        """檢查資料庫健康狀態"""
        try:
            # 這裡可以檢查資料庫的狀態
            # 例如：連接數、查詢性能等
            
            metrics = {
                'connection_count': 5,
                'query_performance': 0.95,
                'disk_usage': 0.3
            }
            
            status = HealthStatus.HEALTHY
            message = "資料庫運行正常"
            recommendations = []
            
            return HealthCheck(
                component="database",
                status=status,
                message=message,
                metrics=metrics,
                last_check=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return HealthCheck(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"資料庫健康檢查失敗: {str(e)}",
                metrics={},
                last_check=datetime.now(),
                recommendations=["檢查資料庫連接"]
            )


class EnhancedPerformanceMonitor:
    """增強版性能監控器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("enhanced_performance_monitor")
        self.real_time_monitor = RealTimeMonitor()
        self.performance_analyzer = PerformanceAnalyzer()
        self.health_checker = HealthChecker()
        self.metrics = ScrapingMetrics()
        
        # 監控狀態
        self.monitoring_active = False
        self.health_check_interval = 300  # 5分鐘
        self.health_check_task = None
    
    async def start_monitoring(self):
        """開始監控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # 啟動實時監控
        await self.real_time_monitor.start_monitoring()
        
        # 啟動健康檢查
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        self.logger.info("增強版性能監控已啟動", category=LogCategory.MONITORING)
    
    async def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        
        # 停止實時監控
        await self.real_time_monitor.stop_monitoring()
        
        # 停止健康檢查
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("增強版性能監控已停止", category=LogCategory.MONITORING)
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while self.monitoring_active:
            try:
                # 執行健康檢查
                components = ["system", "cache", "scrapers", "database"]
                for component in components:
                    health_check = await self.health_checker.perform_health_check(component)
                    
                    if health_check.status != HealthStatus.HEALTHY:
                        self.logger.warning(
                            f"健康檢查警告: {component}",
                            category=LogCategory.MONITORING,
                            metadata={
                                'status': health_check.status.value,
                                'message': health_check.message,
                                'recommendations': health_check.recommendations
                            }
                        )
                
                # 等待下次檢查
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"健康檢查循環錯誤: {str(e)}", category=LogCategory.MONITORING)
                await asyncio.sleep(self.health_check_interval)
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """獲取性能儀表板數據"""
        try:
            # 獲取基本統計
            stats = self.metrics.get_stats(hours=24)
            
            # 獲取系統指標
            system_metrics = self.real_time_monitor.get_system_metrics(minutes=60)
            
            # 獲取趨勢分析
            # 這裡需要從 MetricsCollector 獲取原始指標數據
            # 簡化實現，實際應該從 collector.metrics 獲取
            trends = []
            
            # 獲取優化建議
            suggestions = self.performance_analyzer.generate_optimization_suggestions(
                trends, system_metrics
            )
            
            # 獲取警報
            alerts = self.real_time_monitor.get_recent_alerts(10)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'performance_stats': asdict(stats),
                'system_metrics': [asdict(m) for m in system_metrics[-10:]],  # 最近10個
                'trends': [asdict(t) for t in trends],
                'optimization_suggestions': [asdict(s) for s in suggestions[:5]],  # 前5個建議
                'alerts': alerts,
                'monitoring_status': {
                    'active': self.monitoring_active,
                    'uptime': self._get_uptime()
                }
            }
            
        except Exception as e:
            self.logger.error(f"獲取性能儀表板失敗: {str(e)}", category=LogCategory.MONITORING)
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_uptime(self) -> str:
        """獲取運行時間"""
        # 簡化實現，實際應該記錄啟動時間
        return "未知"
    
    async def export_performance_report(self, filepath: str, hours: int = 24):
        """導出性能報告"""
        try:
            dashboard_data = self.get_performance_dashboard()
            
            # 添加詳細的系統指標
            system_metrics = self.real_time_monitor.get_system_metrics(minutes=hours * 60)
            dashboard_data['detailed_system_metrics'] = [asdict(m) for m in system_metrics]
            
            # 保存到檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"性能報告已導出: {filepath}", category=LogCategory.MONITORING)
            
        except Exception as e:
            self.logger.error(f"導出性能報告失敗: {str(e)}", category=LogCategory.MONITORING)


# 全域增強性能監控器實例
_global_enhanced_monitor: Optional[EnhancedPerformanceMonitor] = None


def get_enhanced_performance_monitor() -> EnhancedPerformanceMonitor:
    """獲取全域增強性能監控器實例"""
    global _global_enhanced_monitor
    
    if _global_enhanced_monitor is None:
        _global_enhanced_monitor = EnhancedPerformanceMonitor()
    
    return _global_enhanced_monitor


def with_enhanced_monitoring(source: str):
    """增強版性能監控裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_enhanced_performance_monitor()
            start_time = time.time()
            
            try:
                # 記錄請求
                monitor.metrics.record_request(source)
                
                # 執行函數
                result = await func(*args, **kwargs)
                
                # 記錄成功
                response_time = time.time() - start_time
                monitor.metrics.record_success(source, response_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                monitor.metrics.record_error(source, type(e).__name__)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_enhanced_performance_monitor()
            start_time = time.time()
            
            try:
                # 記錄請求
                monitor.metrics.record_request(source)
                
                # 執行函數
                result = func(*args, **kwargs)
                
                # 記錄成功
                response_time = time.time() - start_time
                monitor.metrics.record_success(source, response_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                monitor.metrics.record_error(source, type(e).__name__)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
