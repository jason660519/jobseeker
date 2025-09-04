#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據完整性管理器
負責多平台搜尋結果的完整性檢查、錯誤處理和數據驗證

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import aiofiles
import aioredis
from concurrent.futures import ThreadPoolExecutor

# 導入相關組件
from multi_platform_scheduler import (
    MultiPlatformJob, PlatformTask, TaskStatus, PlatformType, RegionType
)
from platform_sync_manager import SyncEvent, SyncEventType, PlatformSyncManager
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


class ValidationLevel(Enum):
    """驗證級別"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class DataQualityIssue(Enum):
    """數據質量問題類型"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    DUPLICATE_ENTRY = "duplicate_entry"
    INCONSISTENT_DATA = "inconsistent_data"
    INCOMPLETE_RESULT = "incomplete_result"
    PLATFORM_MISMATCH = "platform_mismatch"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    RATE_LIMIT_ERROR = "rate_limit_error"


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """驗證規則"""
    rule_id: str
    name: str
    description: str
    validation_func: str  # 函數名稱
    severity: ErrorSeverity
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    """數據質量報告"""
    job_id: str
    platform: str
    validation_level: ValidationLevel
    timestamp: datetime
    total_jobs: int
    valid_jobs: int
    invalid_jobs: int
    issues: List[Dict[str, Any]] = field(default_factory=list)
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    data_hash: str = ""


@dataclass
class IntegrityCheckResult:
    """完整性檢查結果"""
    job_id: str
    expected_platforms: List[str]
    completed_platforms: List[str]
    failed_platforms: List[str]
    missing_platforms: List[str]
    total_expected_jobs: int
    total_actual_jobs: int
    completeness_ratio: float
    consistency_score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    is_complete: bool = False
    is_consistent: bool = False


class JobDataValidator:
    """職位數據驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        
        # 必需字段定義
        self.required_fields = {
            ValidationLevel.BASIC: ['title', 'company'],
            ValidationLevel.STANDARD: ['title', 'company', 'location', 'description'],
            ValidationLevel.STRICT: ['title', 'company', 'location', 'description', 'date_posted'],
            ValidationLevel.COMPREHENSIVE: [
                'title', 'company', 'location', 'description', 'date_posted',
                'job_url', 'salary', 'job_type'
            ]
        }
        
        # 驗證規則
        self.validation_rules = {
            'title_length': ValidationRule(
                rule_id='title_length',
                name='職位標題長度檢查',
                description='檢查職位標題長度是否合理',
                validation_func='_validate_title_length',
                severity=ErrorSeverity.MEDIUM,
                parameters={'min_length': 3, 'max_length': 200}
            ),
            'company_format': ValidationRule(
                rule_id='company_format',
                name='公司名稱格式檢查',
                description='檢查公司名稱格式是否正確',
                validation_func='_validate_company_format',
                severity=ErrorSeverity.LOW,
                parameters={'min_length': 1, 'max_length': 100}
            ),
            'url_format': ValidationRule(
                rule_id='url_format',
                name='URL格式檢查',
                description='檢查職位URL格式是否正確',
                validation_func='_validate_url_format',
                severity=ErrorSeverity.MEDIUM
            ),
            'date_format': ValidationRule(
                rule_id='date_format',
                name='日期格式檢查',
                description='檢查發布日期格式是否正確',
                validation_func='_validate_date_format',
                severity=ErrorSeverity.HIGH
            ),
            'salary_format': ValidationRule(
                rule_id='salary_format',
                name='薪資格式檢查',
                description='檢查薪資信息格式是否正確',
                validation_func='_validate_salary_format',
                severity=ErrorSeverity.LOW
            )
        }
    
    def validate_job_data(self, job_data: Dict[str, Any], 
                         validation_level: ValidationLevel = ValidationLevel.STANDARD) -> DataQualityReport:
        """驗證職位數據"""
        report = DataQualityReport(
            job_id=job_data.get('id', 'unknown'),
            platform=job_data.get('platform', 'unknown'),
            validation_level=validation_level,
            timestamp=datetime.now(),
            total_jobs=1,
            valid_jobs=0,
            invalid_jobs=0
        )
        
        issues = []
        
        # 檢查必需字段
        required_fields = self.required_fields.get(validation_level, [])
        for field in required_fields:
            if field not in job_data or not job_data[field]:
                issues.append({
                    'type': DataQualityIssue.MISSING_REQUIRED_FIELD.value,
                    'field': field,
                    'severity': ErrorSeverity.HIGH.value,
                    'message': f'缺少必需字段: {field}'
                })
        
        # 執行驗證規則
        for rule_id, rule in self.validation_rules.items():
            if not rule.enabled:
                continue
            
            try:
                validation_func = getattr(self, rule.validation_func)
                is_valid, error_message = validation_func(job_data, rule.parameters)
                
                if not is_valid:
                    issues.append({
                        'type': DataQualityIssue.INVALID_FORMAT.value,
                        'rule_id': rule_id,
                        'severity': rule.severity.value,
                        'message': error_message
                    })
            except Exception as e:
                self.logger.error(f"驗證規則 {rule_id} 執行失敗: {e}")
        
        # 計算質量分數
        total_checks = len(required_fields) + len([r for r in self.validation_rules.values() if r.enabled])
        failed_checks = len(issues)
        quality_score = max(0, (total_checks - failed_checks) / total_checks) if total_checks > 0 else 0
        
        report.issues = issues
        report.quality_score = quality_score
        report.valid_jobs = 1 if quality_score > 0.7 else 0
        report.invalid_jobs = 1 - report.valid_jobs
        
        # 生成數據哈希
        report.data_hash = self._generate_data_hash(job_data)
        
        # 生成建議
        report.recommendations = self._generate_recommendations(issues)
        
        return report
    
    def validate_job_list(self, jobs_data: List[Dict[str, Any]], 
                         platform: str,
                         validation_level: ValidationLevel = ValidationLevel.STANDARD) -> DataQualityReport:
        """驗證職位列表數據"""
        report = DataQualityReport(
            job_id='batch_validation',
            platform=platform,
            validation_level=validation_level,
            timestamp=datetime.now(),
            total_jobs=len(jobs_data),
            valid_jobs=0,
            invalid_jobs=0
        )
        
        all_issues = []
        valid_count = 0
        job_hashes = set()
        
        for i, job_data in enumerate(jobs_data):
            job_report = self.validate_job_data(job_data, validation_level)
            
            # 檢查重複
            if job_report.data_hash in job_hashes:
                all_issues.append({
                    'type': DataQualityIssue.DUPLICATE_ENTRY.value,
                    'job_index': i,
                    'severity': ErrorSeverity.MEDIUM.value,
                    'message': f'發現重複職位 (索引: {i})'
                })
            else:
                job_hashes.add(job_report.data_hash)
            
            # 合併問題
            for issue in job_report.issues:
                issue['job_index'] = i
                all_issues.append(issue)
            
            if job_report.quality_score > 0.7:
                valid_count += 1
        
        # 計算整體質量分數
        total_quality = sum(self.validate_job_data(job).quality_score for job in jobs_data)
        average_quality = total_quality / len(jobs_data) if jobs_data else 0
        
        report.issues = all_issues
        report.quality_score = average_quality
        report.valid_jobs = valid_count
        report.invalid_jobs = len(jobs_data) - valid_count
        report.recommendations = self._generate_batch_recommendations(all_issues, len(jobs_data))
        
        return report
    
    def _validate_title_length(self, job_data: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證職位標題長度"""
        title = job_data.get('title', '')
        min_length = params.get('min_length', 3)
        max_length = params.get('max_length', 200)
        
        if len(title) < min_length:
            return False, f'職位標題過短 (最少 {min_length} 字符)'
        if len(title) > max_length:
            return False, f'職位標題過長 (最多 {max_length} 字符)'
        
        return True, ''
    
    def _validate_company_format(self, job_data: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證公司名稱格式"""
        company = job_data.get('company', '')
        min_length = params.get('min_length', 1)
        max_length = params.get('max_length', 100)
        
        if not company or len(company.strip()) < min_length:
            return False, '公司名稱不能為空'
        if len(company) > max_length:
            return False, f'公司名稱過長 (最多 {max_length} 字符)'
        
        return True, ''
    
    def _validate_url_format(self, job_data: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證URL格式"""
        url = job_data.get('job_url', '')
        if not url:
            return True, ''  # URL可選
        
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False, 'URL格式無效'
        
        return True, ''
    
    def _validate_date_format(self, job_data: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證日期格式"""
        date_posted = job_data.get('date_posted', '')
        if not date_posted:
            return True, ''  # 日期可選
        
        try:
            # 嘗試解析日期
            if isinstance(date_posted, str):
                from dateutil import parser
                parser.parse(date_posted)
            elif isinstance(date_posted, datetime):
                pass  # 已經是datetime對象
            else:
                return False, '日期格式無效'
        except Exception:
            return False, '無法解析日期格式'
        
        return True, ''
    
    def _validate_salary_format(self, job_data: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證薪資格式"""
        salary = job_data.get('salary', '')
        if not salary:
            return True, ''  # 薪資可選
        
        # 簡單的薪資格式檢查
        import re
        salary_pattern = re.compile(r'[\d,]+(?:\s*-\s*[\d,]+)?(?:\s*(?:USD|TWD|AUD|元|美元|澳元))?', re.IGNORECASE)
        
        if not salary_pattern.search(str(salary)):
            return False, '薪資格式無效'
        
        return True, ''
    
    def _generate_data_hash(self, job_data: Dict[str, Any]) -> str:
        """生成數據哈希"""
        # 使用關鍵字段生成哈希
        key_fields = ['title', 'company', 'location', 'job_url']
        hash_data = ''.join(str(job_data.get(field, '')) for field in key_fields)
        return hashlib.md5(hash_data.encode()).hexdigest()
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        issue_types = [issue['type'] for issue in issues]
        
        if DataQualityIssue.MISSING_REQUIRED_FIELD.value in issue_types:
            recommendations.append('確保所有必需字段都有值')
        
        if DataQualityIssue.INVALID_FORMAT.value in issue_types:
            recommendations.append('檢查數據格式是否符合規範')
        
        if DataQualityIssue.DUPLICATE_ENTRY.value in issue_types:
            recommendations.append('實施去重機制避免重複數據')
        
        return recommendations
    
    def _generate_batch_recommendations(self, issues: List[Dict[str, Any]], total_jobs: int) -> List[str]:
        """生成批量改進建議"""
        recommendations = self._generate_recommendations(issues)
        
        # 添加批量特定建議
        error_rate = len(issues) / total_jobs if total_jobs > 0 else 0
        
        if error_rate > 0.3:
            recommendations.append('錯誤率過高，建議檢查數據源質量')
        
        if error_rate > 0.1:
            recommendations.append('考慮增加數據預處理步驟')
        
        return recommendations


class DataIntegrityManager:
    """數據完整性管理器"""
    
    def __init__(self, redis_url: str = None):
        """初始化完整性管理器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.redis_url = redis_url
        self.redis_client = None
        
        # 初始化組件
        self.validator = JobDataValidator()
        
        # 完整性檢查配置
        self.integrity_checks: Dict[str, IntegrityCheckResult] = {}
        self.validation_reports: Dict[str, List[DataQualityReport]] = {}
        
        # 錯誤處理配置
        self.error_thresholds = {
            ErrorSeverity.LOW: 0.1,      # 10%
            ErrorSeverity.MEDIUM: 0.05,  # 5%
            ErrorSeverity.HIGH: 0.02,    # 2%
            ErrorSeverity.CRITICAL: 0.01 # 1%
        }
    
    async def initialize(self):
        """初始化完整性管理器"""
        if self.redis_url:
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.logger.info("Redis連接成功")
            except Exception as e:
                self.logger.error(f"Redis連接失敗: {e}")
                self.redis_client = None
        
        self.logger.info("數據完整性管理器初始化完成")
    
    async def check_job_integrity(self, job: MultiPlatformJob) -> IntegrityCheckResult:
        """檢查多平台任務的完整性"""
        expected_platforms = [p.value for p in job.target_platforms]
        completed_platforms = []
        failed_platforms = []
        missing_platforms = []
        
        total_expected_jobs = 0
        total_actual_jobs = 0
        
        issues = []
        
        # 檢查每個平台的狀態
        for platform_name, platform_task in job.platform_tasks.items():
            if platform_task.status == TaskStatus.COMPLETED:
                completed_platforms.append(platform_name)
                total_actual_jobs += platform_task.job_count
            elif platform_task.status == TaskStatus.FAILED:
                failed_platforms.append(platform_name)
                issues.append({
                    'type': 'platform_failure',
                    'platform': platform_name,
                    'severity': ErrorSeverity.HIGH.value,
                    'message': f'平台 {platform_name} 執行失敗: {platform_task.error_message}'
                })
            elif platform_task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                missing_platforms.append(platform_name)
                issues.append({
                    'type': 'platform_incomplete',
                    'platform': platform_name,
                    'severity': ErrorSeverity.MEDIUM.value,
                    'message': f'平台 {platform_name} 尚未完成'
                })
        
        # 計算完整性比率
        completeness_ratio = len(completed_platforms) / len(expected_platforms) if expected_platforms else 0
        
        # 計算一致性分數（基於成功平台的數據質量）
        consistency_score = await self._calculate_consistency_score(job)
        
        # 檢查是否完整和一致
        is_complete = len(missing_platforms) == 0 and len(failed_platforms) == 0
        is_consistent = consistency_score > 0.8
        
        result = IntegrityCheckResult(
            job_id=job.job_id,
            expected_platforms=expected_platforms,
            completed_platforms=completed_platforms,
            failed_platforms=failed_platforms,
            missing_platforms=missing_platforms,
            total_expected_jobs=total_expected_jobs,
            total_actual_jobs=total_actual_jobs,
            completeness_ratio=completeness_ratio,
            consistency_score=consistency_score,
            issues=issues,
            is_complete=is_complete,
            is_consistent=is_consistent
        )
        
        # 保存檢查結果
        self.integrity_checks[job.job_id] = result
        
        # 保存到Redis
        if self.redis_client:
            await self.redis_client.hset(
                "integrity_checks",
                job.job_id,
                json.dumps(asdict(result), default=str)
            )
        
        self.logger.info(f"完整性檢查完成: {job.job_id}, 完整性: {completeness_ratio:.2f}, 一致性: {consistency_score:.2f}")
        
        return result
    
    async def validate_platform_results(self, job_id: str, platform: str, 
                                      results_data: Dict[str, Any],
                                      validation_level: ValidationLevel = ValidationLevel.STANDARD) -> DataQualityReport:
        """驗證平台搜尋結果"""
        jobs_data = results_data.get('jobs', [])
        
        # 執行數據驗證
        report = self.validator.validate_job_list(jobs_data, platform, validation_level)
        report.job_id = job_id
        
        # 保存驗證報告
        if job_id not in self.validation_reports:
            self.validation_reports[job_id] = []
        self.validation_reports[job_id].append(report)
        
        # 保存到Redis
        if self.redis_client:
            await self.redis_client.lpush(
                f"validation_reports:{job_id}",
                json.dumps(asdict(report), default=str)
            )
        
        # 檢查是否超過錯誤閾值
        await self._check_error_thresholds(report)
        
        self.logger.info(f"平台結果驗證完成: {job_id}_{platform}, 質量分數: {report.quality_score:.2f}")
        
        return report
    
    async def _calculate_consistency_score(self, job: MultiPlatformJob) -> float:
        """計算數據一致性分數"""
        # 獲取所有成功平台的驗證報告
        reports = self.validation_reports.get(job.job_id, [])
        
        if not reports:
            return 1.0  # 沒有報告時假設一致
        
        # 計算平均質量分數
        total_score = sum(report.quality_score for report in reports)
        average_score = total_score / len(reports)
        
        # 計算分數方差（一致性指標）
        variance = sum((report.quality_score - average_score) ** 2 for report in reports) / len(reports)
        consistency_score = max(0, 1 - variance)  # 方差越小，一致性越高
        
        return consistency_score
    
    async def _check_error_thresholds(self, report: DataQualityReport):
        """檢查錯誤閾值"""
        if report.total_jobs == 0:
            return
        
        # 按嚴重程度統計錯誤
        severity_counts = {severity: 0 for severity in ErrorSeverity}
        
        for issue in report.issues:
            severity = ErrorSeverity(issue.get('severity', ErrorSeverity.LOW.value))
            severity_counts[severity] += 1
        
        # 檢查是否超過閾值
        for severity, count in severity_counts.items():
            error_rate = count / report.total_jobs
            threshold = self.error_thresholds.get(severity, 0.1)
            
            if error_rate > threshold:
                self.logger.warning(
                    f"錯誤率超過閾值: {report.job_id}_{report.platform}, "
                    f"嚴重程度: {severity.value}, 錯誤率: {error_rate:.2%}, 閾值: {threshold:.2%}"
                )
                
                # 可以在這裡觸發告警或自動處理
    
    def get_integrity_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取完整性狀態"""
        integrity_result = self.integrity_checks.get(job_id)
        validation_reports = self.validation_reports.get(job_id, [])
        
        if not integrity_result:
            return None
        
        return {
            'integrity_check': asdict(integrity_result),
            'validation_reports': [asdict(report) for report in validation_reports],
            'overall_quality_score': sum(r.quality_score for r in validation_reports) / len(validation_reports) if validation_reports else 0,
            'total_issues': sum(len(r.issues) for r in validation_reports)
        }
    
    def get_global_integrity_summary(self) -> Dict[str, Any]:
        """獲取全局完整性摘要"""
        total_jobs = len(self.integrity_checks)
        complete_jobs = sum(1 for result in self.integrity_checks.values() if result.is_complete)
        consistent_jobs = sum(1 for result in self.integrity_checks.values() if result.is_consistent)
        
        total_reports = sum(len(reports) for reports in self.validation_reports.values())
        total_quality_score = sum(
            sum(report.quality_score for report in reports)
            for reports in self.validation_reports.values()
        )
        average_quality = total_quality_score / total_reports if total_reports > 0 else 0
        
        return {
            'total_jobs': total_jobs,
            'complete_jobs': complete_jobs,
            'consistent_jobs': consistent_jobs,
            'completeness_rate': complete_jobs / total_jobs if total_jobs > 0 else 0,
            'consistency_rate': consistent_jobs / total_jobs if total_jobs > 0 else 0,
            'average_quality_score': average_quality,
            'total_validation_reports': total_reports
        }


# 全局數據完整性管理器實例
data_integrity_manager = DataIntegrityManager()


if __name__ == "__main__":
    async def main():
        """測試數據完整性管理器"""
        integrity_manager = DataIntegrityManager()
        await integrity_manager.initialize()
        
        # 模擬職位數據
        sample_jobs = [
            {
                'id': '1',
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'San Francisco',
                'description': 'Great Python job',
                'date_posted': '2025-01-27',
                'job_url': 'https://example.com/job1',
                'platform': 'linkedin'
            },
            {
                'id': '2',
                'title': '',  # 缺少標題
                'company': 'Another Corp',
                'location': 'New York',
                'description': 'Job description',
                'platform': 'indeed'
            }
        ]
        
        # 驗證數據質量
        report = integrity_manager.validator.validate_job_list(
            sample_jobs, 'test_platform', ValidationLevel.STANDARD
        )
        
        print(f"驗證報告:")
        print(f"總職位: {report.total_jobs}")
        print(f"有效職位: {report.valid_jobs}")
        print(f"無效職位: {report.invalid_jobs}")
        print(f"質量分數: {report.quality_score:.2f}")
        print(f"問題數量: {len(report.issues)}")
        
        for issue in report.issues:
            print(f"  - {issue['message']} (嚴重程度: {issue['severity']})")
        
        print(f"建議: {report.recommendations}")
    
    asyncio.run(main())