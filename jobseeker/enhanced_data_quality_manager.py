#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版數據品質管理器
提供智能品質分析、自動化改善和持續監控

Author: jobseeker Team
Date: 2025-01-27
"""

import time
import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import statistics
import re
from functools import wraps

from .data_quality import (
    DataQualityIssue, QualityReport, TextCleaner, DataValidator,
    DuplicateDetector, DataQualityProcessor, improve_job_data_quality
)
from .model import JobPost, JobResponse, Site
from .enhanced_logging import get_enhanced_logger, LogCategory


class QualityLevel(Enum):
    """品質等級"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 80-89
    FAIR = "fair"           # 70-79
    POOR = "poor"           # 60-69
    CRITICAL = "critical"   # <60


class QualityTrend(Enum):
    """品質趨勢"""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


@dataclass
class QualityMetrics:
    """品質指標"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    uniqueness_score: float
    freshness_score: float
    timestamp: datetime
    site: str
    sample_size: int


@dataclass
class QualityAlert:
    """品質警報"""
    alert_id: str
    level: QualityLevel
    message: str
    metric: str
    current_value: float
    threshold: float
    site: str
    timestamp: datetime
    recommendations: List[str]


@dataclass
class QualityImprovement:
    """品質改善建議"""
    improvement_id: str
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    effort: str  # "high", "medium", "low"
    priority: int  # 1-10
    estimated_improvement: float
    implementation_steps: List[str]
    affected_sites: List[str]


class QualityAnalyzer:
    """品質分析器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("quality_analyzer")
        self.quality_history = deque(maxlen=1000)
        self.site_quality_stats = defaultdict(list)
    
    def analyze_quality(self, job_response: JobResponse, site: str) -> QualityMetrics:
        """分析數據品質"""
        if not job_response.success or not job_response.jobs:
            return QualityMetrics(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                uniqueness_score=0.0,
                freshness_score=0.0,
                timestamp=datetime.now(),
                site=site,
                sample_size=0
            )
        
        jobs = job_response.jobs
        sample_size = len(jobs)
        
        # 計算各項品質指標
        completeness_score = self._calculate_completeness_score(jobs)
        accuracy_score = self._calculate_accuracy_score(jobs)
        consistency_score = self._calculate_consistency_score(jobs)
        uniqueness_score = self._calculate_uniqueness_score(jobs)
        freshness_score = self._calculate_freshness_score(jobs)
        
        # 計算總體品質分數
        weights = {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'uniqueness': 0.15,
            'freshness': 0.15
        }
        
        overall_score = (
            completeness_score * weights['completeness'] +
            accuracy_score * weights['accuracy'] +
            consistency_score * weights['consistency'] +
            uniqueness_score * weights['uniqueness'] +
            freshness_score * weights['freshness']
        )
        
        metrics = QualityMetrics(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            uniqueness_score=uniqueness_score,
            freshness_score=freshness_score,
            timestamp=datetime.now(),
            site=site,
            sample_size=sample_size
        )
        
        # 記錄品質歷史
        self.quality_history.append(metrics)
        self.site_quality_stats[site].append(metrics)
        
        return metrics
    
    def _calculate_completeness_score(self, jobs: List[JobPost]) -> float:
        """計算完整度分數"""
        if not jobs:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        required_fields = ['title', 'company', 'location']
        optional_fields = ['description', 'job_url', 'compensation', 'job_type', 'date_posted']
        
        for job in jobs:
            # 必填欄位
            for field in required_fields:
                total_fields += 1
                if getattr(job, field) and str(getattr(job, field)).strip():
                    filled_fields += 1
            
            # 可選欄位（權重較低）
            for field in optional_fields:
                total_fields += 0.5
                if getattr(job, field) and str(getattr(job, field)).strip():
                    filled_fields += 0.5
        
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0.0
    
    def _calculate_accuracy_score(self, jobs: List[JobPost]) -> float:
        """計算準確度分數"""
        if not jobs:
            return 0.0
        
        validator = DataValidator()
        total_checks = 0
        passed_checks = 0
        
        for job in jobs:
            # 檢查 URL 格式
            if job.job_url:
                total_checks += 1
                if validator.validate_url(job.job_url):
                    passed_checks += 1
            
            if job.company_url:
                total_checks += 1
                if validator.validate_url(job.company_url):
                    passed_checks += 1
            
            # 檢查電子郵件格式
            if job.emails:
                for email in job.emails:
                    total_checks += 1
                    if validator.validate_email(email):
                        passed_checks += 1
            
            # 檢查薪資範圍
            if job.compensation:
                total_checks += 1
                if validator.validate_salary(
                    job.compensation.min_amount,
                    job.compensation.max_amount,
                    job.compensation.interval
                ):
                    passed_checks += 1
            
            # 檢查日期格式
            if job.date_posted:
                total_checks += 1
                if validator.validate_date(str(job.date_posted)):
                    passed_checks += 1
        
        return (passed_checks / total_checks) * 100 if total_checks > 0 else 100.0
    
    def _calculate_consistency_score(self, jobs: List[JobPost]) -> float:
        """計算一致性分數"""
        if not jobs:
            return 0.0
        
        # 檢查格式一致性
        title_lengths = []
        company_lengths = []
        description_lengths = []
        
        for job in jobs:
            if job.title:
                title_lengths.append(len(job.title))
            if job.company:
                company_lengths.append(len(job.company))
            if job.description:
                description_lengths.append(len(job.description))
        
        # 計算變異係數（越小越一致）
        consistency_scores = []
        
        if title_lengths:
            cv = statistics.stdev(title_lengths) / statistics.mean(title_lengths) if len(title_lengths) > 1 else 0
            consistency_scores.append(max(0, 100 - cv * 100))
        
        if company_lengths:
            cv = statistics.stdev(company_lengths) / statistics.mean(company_lengths) if len(company_lengths) > 1 else 0
            consistency_scores.append(max(0, 100 - cv * 100))
        
        if description_lengths:
            cv = statistics.stdev(description_lengths) / statistics.mean(description_lengths) if len(description_lengths) > 1 else 0
            consistency_scores.append(max(0, 100 - cv * 100))
        
        return statistics.mean(consistency_scores) if consistency_scores else 100.0
    
    def _calculate_uniqueness_score(self, jobs: List[JobPost]) -> float:
        """計算唯一性分數"""
        if not jobs:
            return 0.0
        
        # 使用簡單的標題重複檢測
        titles = [job.title.lower().strip() for job in jobs if job.title]
        unique_titles = set(titles)
        
        if not titles:
            return 100.0
        
        uniqueness_ratio = len(unique_titles) / len(titles)
        return uniqueness_ratio * 100
    
    def _calculate_freshness_score(self, jobs: List[JobPost]) -> float:
        """計算新鮮度分數"""
        if not jobs:
            return 0.0
        
        current_time = datetime.now()
        freshness_scores = []
        
        for job in jobs:
            if job.date_posted:
                try:
                    # 嘗試解析日期
                    if isinstance(job.date_posted, str):
                        # 簡化的日期解析
                        posted_date = datetime.strptime(job.date_posted, '%Y-%m-%d')
                    else:
                        posted_date = job.date_posted
                    
                    # 計算天數差
                    days_old = (current_time - posted_date).days
                    
                    # 新鮮度分數（越新分數越高）
                    if days_old <= 1:
                        freshness_scores.append(100)
                    elif days_old <= 7:
                        freshness_scores.append(90)
                    elif days_old <= 30:
                        freshness_scores.append(70)
                    elif days_old <= 90:
                        freshness_scores.append(50)
                    else:
                        freshness_scores.append(20)
                        
                except Exception:
                    # 無法解析日期，給中等分數
                    freshness_scores.append(50)
            else:
                # 沒有日期資訊，給低分
                freshness_scores.append(30)
        
        return statistics.mean(freshness_scores) if freshness_scores else 50.0
    
    def get_quality_trend(self, site: str, days: int = 7) -> QualityTrend:
        """獲取品質趨勢"""
        cutoff_time = datetime.now() - timedelta(days=days)
        site_metrics = [
            m for m in self.site_quality_stats[site]
            if m.timestamp >= cutoff_time
        ]
        
        if len(site_metrics) < 3:
            return QualityTrend.STABLE
        
        # 計算趨勢
        scores = [m.overall_score for m in site_metrics]
        
        # 簡單線性回歸
        n = len(scores)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(scores) / n
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return QualityTrend.STABLE
        
        slope = numerator / denominator
        
        # 判斷趨勢
        if abs(slope) < 0.5:
            return QualityTrend.STABLE
        elif slope > 0:
            return QualityTrend.IMPROVING
        else:
            return QualityTrend.DEGRADING
    
    def get_quality_level(self, score: float) -> QualityLevel:
        """獲取品質等級"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.FAIR
        elif score >= 60:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL


class QualityMonitor:
    """品質監控器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("quality_monitor")
        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 90.0,
            QualityLevel.GOOD: 80.0,
            QualityLevel.FAIR: 70.0,
            QualityLevel.POOR: 60.0,
            QualityLevel.CRITICAL: 0.0
        }
        self.alerts = deque(maxlen=100)
        self._lock = threading.RLock()
    
    def check_quality_thresholds(self, metrics: QualityMetrics) -> List[QualityAlert]:
        """檢查品質閾值"""
        alerts = []
        
        # 檢查總體品質
        if metrics.overall_score < self.quality_thresholds[QualityLevel.GOOD]:
            alert = QualityAlert(
                alert_id=f"quality_{metrics.site}_{int(time.time())}",
                level=QualityLevel.POOR if metrics.overall_score >= 60 else QualityLevel.CRITICAL,
                message=f"{metrics.site} 數據品質過低: {metrics.overall_score:.1f}",
                metric="overall_score",
                current_value=metrics.overall_score,
                threshold=self.quality_thresholds[QualityLevel.GOOD],
                site=metrics.site,
                timestamp=datetime.now(),
                recommendations=self._generate_quality_recommendations(metrics)
            )
            alerts.append(alert)
        
        # 檢查各項指標
        for metric_name in ['completeness_score', 'accuracy_score', 'consistency_score', 'uniqueness_score', 'freshness_score']:
            score = getattr(metrics, metric_name)
            if score < 70:  # 低於70分發出警告
                alert = QualityAlert(
                    alert_id=f"{metric_name}_{metrics.site}_{int(time.time())}",
                    level=QualityLevel.POOR,
                    message=f"{metrics.site} {metric_name} 過低: {score:.1f}",
                    metric=metric_name,
                    current_value=score,
                    threshold=70.0,
                    site=metrics.site,
                    timestamp=datetime.now(),
                    recommendations=self._generate_metric_recommendations(metric_name, score)
                )
                alerts.append(alert)
        
        # 記錄警報
        with self._lock:
            self.alerts.extend(alerts)
        
        return alerts
    
    def _generate_quality_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """生成品質改善建議"""
        recommendations = []
        
        if metrics.completeness_score < 80:
            recommendations.append("改善數據完整度：檢查必填欄位提取邏輯")
        
        if metrics.accuracy_score < 80:
            recommendations.append("提升數據準確度：加強格式驗證和清理")
        
        if metrics.consistency_score < 80:
            recommendations.append("提高數據一致性：標準化數據格式")
        
        if metrics.uniqueness_score < 80:
            recommendations.append("減少重複數據：改善去重算法")
        
        if metrics.freshness_score < 80:
            recommendations.append("提升數據新鮮度：優化更新頻率")
        
        return recommendations
    
    def _generate_metric_recommendations(self, metric_name: str, score: float) -> List[str]:
        """生成特定指標的改善建議"""
        recommendations = {
            'completeness_score': [
                "檢查爬蟲是否正確提取所有必填欄位",
                "改善錯誤處理，避免數據丟失",
                "增加數據驗證步驟"
            ],
            'accuracy_score': [
                "加強 URL 和電子郵件格式驗證",
                "改善薪資數據解析邏輯",
                "優化日期格式處理"
            ],
            'consistency_score': [
                "標準化數據格式",
                "統一欄位長度和格式要求",
                "改善數據清理流程"
            ],
            'uniqueness_score': [
                "改善重複檢測算法",
                "增加相似度比較邏輯",
                "優化去重策略"
            ],
            'freshness_score': [
                "增加數據更新頻率",
                "改善日期解析邏輯",
                "實施數據過期機制"
            ]
        }
        
        return recommendations.get(metric_name, ["檢查相關配置和邏輯"])
    
    def get_recent_alerts(self, count: int = 10) -> List[QualityAlert]:
        """獲取最近的警報"""
        with self._lock:
            return list(self.alerts)[-count:]


class QualityImprovementEngine:
    """品質改善引擎"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("quality_improvement_engine")
        self.improvement_history = deque(maxlen=100)
    
    def generate_improvements(self, metrics: QualityMetrics, 
                            trend: QualityTrend) -> List[QualityImprovement]:
        """生成改善建議"""
        improvements = []
        
        # 基於品質分數生成改善建議
        if metrics.overall_score < 80:
            improvements.append(self._create_completeness_improvement(metrics))
        
        if metrics.accuracy_score < 80:
            improvements.append(self._create_accuracy_improvement(metrics))
        
        if metrics.consistency_score < 80:
            improvements.append(self._create_consistency_improvement(metrics))
        
        if metrics.uniqueness_score < 80:
            improvements.append(self._create_uniqueness_improvement(metrics))
        
        if metrics.freshness_score < 80:
            improvements.append(self._create_freshness_improvement(metrics))
        
        # 基於趨勢生成改善建議
        if trend == QualityTrend.DEGRADING:
            improvements.append(self._create_trend_improvement(metrics, trend))
        
        # 按優先級排序
        improvements.sort(key=lambda x: x.priority, reverse=True)
        
        return improvements
    
    def _create_completeness_improvement(self, metrics: QualityMetrics) -> QualityImprovement:
        """創建完整度改善建議"""
        return QualityImprovement(
            improvement_id=f"completeness_{metrics.site}_{int(time.time())}",
            title="提升數據完整度",
            description=f"改善 {metrics.site} 的數據完整度，當前分數: {metrics.completeness_score:.1f}",
            impact="high",
            effort="medium",
            priority=8,
            estimated_improvement=15.0,
            implementation_steps=[
                "檢查爬蟲選擇器是否正確",
                "增加必填欄位驗證",
                "改善錯誤處理邏輯",
                "實施數據補全機制"
            ],
            affected_sites=[metrics.site]
        )
    
    def _create_accuracy_improvement(self, metrics: QualityMetrics) -> QualityImprovement:
        """創建準確度改善建議"""
        return QualityImprovement(
            improvement_id=f"accuracy_{metrics.site}_{int(time.time())}",
            title="提升數據準確度",
            description=f"改善 {metrics.site} 的數據準確度，當前分數: {metrics.accuracy_score:.1f}",
            impact="high",
            effort="low",
            priority=9,
            estimated_improvement=20.0,
            implementation_steps=[
                "加強格式驗證",
                "改善數據清理邏輯",
                "優化正則表達式",
                "增加數據校驗步驟"
            ],
            affected_sites=[metrics.site]
        )
    
    def _create_consistency_improvement(self, metrics: QualityMetrics) -> QualityImprovement:
        """創建一致性改善建議"""
        return QualityImprovement(
            improvement_id=f"consistency_{metrics.site}_{int(time.time())}",
            title="提升數據一致性",
            description=f"改善 {metrics.site} 的數據一致性，當前分數: {metrics.consistency_score:.1f}",
            impact="medium",
            effort="medium",
            priority=6,
            estimated_improvement=12.0,
            implementation_steps=[
                "標準化數據格式",
                "統一欄位處理邏輯",
                "實施數據模板",
                "增加格式檢查"
            ],
            affected_sites=[metrics.site]
        )
    
    def _create_uniqueness_improvement(self, metrics: QualityMetrics) -> QualityImprovement:
        """創建唯一性改善建議"""
        return QualityImprovement(
            improvement_id=f"uniqueness_{metrics.site}_{int(time.time())}",
            title="提升數據唯一性",
            description=f"改善 {metrics.site} 的數據唯一性，當前分數: {metrics.uniqueness_score:.1f}",
            impact="medium",
            effort="high",
            priority=7,
            estimated_improvement=18.0,
            implementation_steps=[
                "改善重複檢測算法",
                "增加相似度比較",
                "優化去重策略",
                "實施智能合併"
            ],
            affected_sites=[metrics.site]
        )
    
    def _create_freshness_improvement(self, metrics: QualityMetrics) -> QualityImprovement:
        """創建新鮮度改善建議"""
        return QualityImprovement(
            improvement_id=f"freshness_{metrics.site}_{int(time.time())}",
            title="提升數據新鮮度",
            description=f"改善 {metrics.site} 的數據新鮮度，當前分數: {metrics.freshness_score:.1f}",
            impact="medium",
            effort="low",
            priority=5,
            estimated_improvement=10.0,
            implementation_steps=[
                "增加更新頻率",
                "改善日期解析",
                "實施過期機制",
                "優化快取策略"
            ],
            affected_sites=[metrics.site]
        )
    
    def _create_trend_improvement(self, metrics: QualityMetrics, trend: QualityTrend) -> QualityImprovement:
        """創建趨勢改善建議"""
        return QualityImprovement(
            improvement_id=f"trend_{metrics.site}_{int(time.time())}",
            title="改善品質下降趨勢",
            description=f"{metrics.site} 數據品質呈下降趨勢，需要立即改善",
            impact="high",
            effort="high",
            priority=10,
            estimated_improvement=25.0,
            implementation_steps=[
                "分析品質下降原因",
                "檢查爬蟲穩定性",
                "改善錯誤處理",
                "實施品質監控",
                "優化數據處理流程"
            ],
            affected_sites=[metrics.site]
        )


class EnhancedDataQualityManager:
    """增強版數據品質管理器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("enhanced_data_quality_manager")
        self.quality_analyzer = QualityAnalyzer()
        self.quality_monitor = QualityMonitor()
        self.improvement_engine = QualityImprovementEngine()
        
        # 品質處理器
        self.quality_processor = DataQualityProcessor(
            remove_duplicates=True,
            clean_text=True,
            validate_data=True,
            similarity_threshold=0.85
        )
        
        # 品質歷史
        self.quality_history = deque(maxlen=1000)
        self.site_quality_trends = {}
    
    async def process_job_response(self, job_response: JobResponse, site: str) -> Tuple[JobResponse, QualityReport, QualityMetrics]:
        """處理職位響應並分析品質"""
        try:
            # 1. 執行品質處理
            processed_response, quality_report = self.quality_processor.process_job_response(job_response)
            
            # 2. 分析品質指標
            quality_metrics = self.quality_analyzer.analyze_quality(processed_response, site)
            
            # 3. 檢查品質警報
            alerts = self.quality_monitor.check_quality_thresholds(quality_metrics)
            
            # 4. 記錄品質歷史
            self.quality_history.append({
                'timestamp': datetime.now(),
                'site': site,
                'metrics': quality_metrics,
                'report': quality_report,
                'alerts': alerts
            })
            
            # 5. 記錄日誌
            self.logger.info(
                f"數據品質處理完成: {site}",
                category=LogCategory.GENERAL,
                metadata={
                    'site': site,
                    'original_jobs': len(job_response.jobs) if job_response.jobs else 0,
                    'processed_jobs': len(processed_response.jobs) if processed_response.jobs else 0,
                    'quality_score': quality_metrics.overall_score,
                    'alerts_count': len(alerts)
                }
            )
            
            return processed_response, quality_report, quality_metrics
            
        except Exception as e:
            self.logger.error(
                f"數據品質處理失敗: {str(e)}",
                category=LogCategory.ERROR,
                metadata={'site': site}
            )
            return job_response, QualityReport(
                total_jobs=0, valid_jobs=0, issues_found={},
                duplicates_removed=0, cleaned_fields={},
                processing_time=0.0, recommendations=[]
            ), QualityMetrics(
                overall_score=0.0, completeness_score=0.0, accuracy_score=0.0,
                consistency_score=0.0, uniqueness_score=0.0, freshness_score=0.0,
                timestamp=datetime.now(), site=site, sample_size=0
            )
    
    def get_quality_dashboard(self, site: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """獲取品質儀表板數據"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 過濾歷史數據
            filtered_history = [
                entry for entry in self.quality_history
                if entry['timestamp'] >= cutoff_time and (site is None or entry['site'] == site)
            ]
            
            if not filtered_history:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'site': site,
                    'message': '沒有足夠的歷史數據'
                }
            
            # 計算統計數據
            sites = list(set(entry['site'] for entry in filtered_history))
            total_entries = len(filtered_history)
            
            # 按網站分組
            site_metrics = defaultdict(list)
            for entry in filtered_history:
                site_metrics[entry['site']].append(entry['metrics'])
            
            # 計算平均品質分數
            avg_scores = {}
            for site_name, metrics_list in site_metrics.items():
                if metrics_list:
                    avg_scores[site_name] = {
                        'overall': statistics.mean([m.overall_score for m in metrics_list]),
                        'completeness': statistics.mean([m.completeness_score for m in metrics_list]),
                        'accuracy': statistics.mean([m.accuracy_score for m in metrics_list]),
                        'consistency': statistics.mean([m.consistency_score for m in metrics_list]),
                        'uniqueness': statistics.mean([m.uniqueness_score for m in metrics_list]),
                        'freshness': statistics.mean([m.freshness_score for m in metrics_list])
                    }
            
            # 獲取最近的警報
            recent_alerts = self.quality_monitor.get_recent_alerts(10)
            
            # 獲取品質趨勢
            trends = {}
            for site_name in sites:
                trend = self.quality_analyzer.get_quality_trend(site_name, days)
                trends[site_name] = trend.value
            
            # 生成改善建議
            improvements = []
            for site_name, metrics_list in site_metrics.items():
                if metrics_list:
                    latest_metrics = metrics_list[-1]
                    trend = self.quality_analyzer.get_quality_trend(site_name, days)
                    site_improvements = self.improvement_engine.generate_improvements(latest_metrics, trend)
                    improvements.extend(site_improvements[:3])  # 每個網站最多3個建議
            
            return {
                'timestamp': datetime.now().isoformat(),
                'site': site,
                'time_range_days': days,
                'total_entries': total_entries,
                'sites': sites,
                'average_scores': avg_scores,
                'trends': trends,
                'recent_alerts': [asdict(alert) for alert in recent_alerts],
                'improvements': [asdict(improvement) for improvement in improvements[:10]],
                'quality_levels': {
                    site_name: self.quality_analyzer.get_quality_level(avg_scores[site_name]['overall']).value
                    for site_name in avg_scores
                }
            }
            
        except Exception as e:
            self.logger.error(f"獲取品質儀表板失敗: {str(e)}", category=LogCategory.ERROR)
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_quality_trends(self, site: str, days: int = 30) -> Dict[str, Any]:
        """獲取品質趨勢分析"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            site_entries = [
                entry for entry in self.quality_history
                if entry['site'] == site and entry['timestamp'] >= cutoff_time
            ]
            
            if not site_entries:
                return {
                    'site': site,
                    'message': '沒有足夠的歷史數據',
                    'days': days
                }
            
            # 按日期分組
            daily_metrics = defaultdict(list)
            for entry in site_entries:
                date_key = entry['timestamp'].date()
                daily_metrics[date_key].append(entry['metrics'])
            
            # 計算每日平均
            daily_averages = {}
            for date, metrics_list in daily_metrics.items():
                daily_averages[date.isoformat()] = {
                    'overall': statistics.mean([m.overall_score for m in metrics_list]),
                    'completeness': statistics.mean([m.completeness_score for m in metrics_list]),
                    'accuracy': statistics.mean([m.accuracy_score for m in metrics_list]),
                    'consistency': statistics.mean([m.consistency_score for m in metrics_list]),
                    'uniqueness': statistics.mean([m.uniqueness_score for m in metrics_list]),
                    'freshness': statistics.mean([m.freshness_score for m in metrics_list]),
                    'sample_size': len(metrics_list)
                }
            
            # 計算趨勢
            trend = self.quality_analyzer.get_quality_trend(site, days)
            
            return {
                'site': site,
                'days': days,
                'trend': trend.value,
                'daily_averages': daily_averages,
                'total_samples': len(site_entries)
            }
            
        except Exception as e:
            self.logger.error(f"獲取品質趨勢失敗: {str(e)}", category=LogCategory.ERROR)
            return {
                'error': str(e),
                'site': site,
                'days': days
            }
    
    async def export_quality_report(self, filepath: str, site: Optional[str] = None, days: int = 30):
        """導出品質報告"""
        try:
            dashboard_data = self.get_quality_dashboard(site, days)
            trends_data = {}
            
            if site:
                trends_data[site] = self.get_quality_trends(site, days)
            else:
                # 為所有網站生成趨勢數據
                sites = dashboard_data.get('sites', [])
                for site_name in sites:
                    trends_data[site_name] = self.get_quality_trends(site_name, days)
            
            report_data = {
                'report_info': {
                    'generated_at': datetime.now().isoformat(),
                    'site': site,
                    'time_range_days': days,
                    'report_type': 'enhanced_quality_report'
                },
                'dashboard': dashboard_data,
                'trends': trends_data,
                'summary': {
                    'total_sites': len(dashboard_data.get('sites', [])),
                    'average_quality': statistics.mean([
                        scores['overall'] for scores in dashboard_data.get('average_scores', {}).values()
                    ]) if dashboard_data.get('average_scores') else 0,
                    'total_alerts': len(dashboard_data.get('recent_alerts', [])),
                    'total_improvements': len(dashboard_data.get('improvements', []))
                }
            }
            
            # 保存到檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"品質報告已導出: {filepath}", category=LogCategory.GENERAL)
            
        except Exception as e:
            self.logger.error(f"導出品質報告失敗: {str(e)}", category=LogCategory.ERROR)


# 全域增強數據品質管理器實例
_global_enhanced_quality_manager: Optional[EnhancedDataQualityManager] = None


def get_enhanced_data_quality_manager() -> EnhancedDataQualityManager:
    """獲取全域增強數據品質管理器實例"""
    global _global_enhanced_quality_manager
    
    if _global_enhanced_quality_manager is None:
        _global_enhanced_quality_manager = EnhancedDataQualityManager()
    
    return _global_enhanced_quality_manager


def with_enhanced_quality_management(site: str):
    """增強版數據品質管理裝飾器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            quality_manager = get_enhanced_data_quality_manager()
            
            # 執行原始函數
            result = await func(*args, **kwargs)
            
            # 如果是 JobResponse，進行品質處理
            if isinstance(result, JobResponse):
                processed_result, quality_report, quality_metrics = await quality_manager.process_job_response(result, site)
                return processed_result
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            quality_manager = get_enhanced_data_quality_manager()
            
            # 執行原始函數
            result = func(*args, **kwargs)
            
            # 如果是 JobResponse，進行品質處理
            if isinstance(result, JobResponse):
                processed_result, quality_report, quality_metrics = asyncio.run(
                    quality_manager.process_job_response(result, site)
                )
                return processed_result
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
