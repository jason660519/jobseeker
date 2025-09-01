"""資料品質改善系統

此模組提供職位資料的清理、標準化、重複檢測和品質驗證功能。
"""

from __future__ import annotations

import re
import hashlib
import unicodedata
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
from difflib import SequenceMatcher

from jobseeker.model import JobPost, JobResponse, JobType, CompensationInterval, Location
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


class DataQualityIssue(Enum):
    """資料品質問題類型"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_URL = "invalid_url"
    INVALID_EMAIL = "invalid_email"
    INVALID_SALARY = "invalid_salary"
    INVALID_DATE = "invalid_date"
    DUPLICATE_CONTENT = "duplicate_content"
    SUSPICIOUS_CONTENT = "suspicious_content"
    ENCODING_ISSUE = "encoding_issue"
    FORMAT_INCONSISTENCY = "format_inconsistency"
    OUTLIER_VALUE = "outlier_value"


@dataclass
class QualityReport:
    """資料品質報告"""
    total_jobs: int
    valid_jobs: int
    issues_found: Dict[DataQualityIssue, int]
    duplicates_removed: int
    cleaned_fields: Dict[str, int]
    processing_time: float
    recommendations: List[str]
    
    @property
    def quality_score(self) -> float:
        """計算品質分數 (0-100)"""
        if self.total_jobs == 0:
            return 0.0
        return (self.valid_jobs / self.total_jobs) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'total_jobs': self.total_jobs,
            'valid_jobs': self.valid_jobs,
            'quality_score': self.quality_score,
            'issues_found': {issue.value: count for issue, count in self.issues_found.items()},
            'duplicates_removed': self.duplicates_removed,
            'cleaned_fields': self.cleaned_fields,
            'processing_time': self.processing_time,
            'recommendations': self.recommendations
        }


class TextCleaner:
    """文字清理工具"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("text_cleaner")
        
        # 常見的垃圾文字模式
        self.spam_patterns = [
            r'\b(?:click here|apply now|urgent|immediate start)\b',
            r'\$\$\$+',
            r'!!!+',
            r'\b(?:work from home|make money|easy money)\b',
            r'\b(?:no experience|no skills required)\b'
        ]
        
        # HTML 標籤模式
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # 多餘空白模式
        self.whitespace_pattern = re.compile(r'\s+')
        
        # 特殊字符模式
        self.special_chars_pattern = re.compile(r'[^\w\s\-.,!?()\[\]{}:;"\']')
    
    def clean_text(self, text: str, remove_html: bool = True, 
                  normalize_whitespace: bool = True, 
                  remove_special_chars: bool = False) -> str:
        """清理文字"""
        if not text or not isinstance(text, str):
            return ""
        
        # 移除 HTML 標籤
        if remove_html:
            text = self.html_pattern.sub(' ', text)
        
        # 正規化 Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # 移除特殊字符
        if remove_special_chars:
            text = self.special_chars_pattern.sub(' ', text)
        
        # 正規化空白
        if normalize_whitespace:
            text = self.whitespace_pattern.sub(' ', text)
        
        return text.strip()
    
    def detect_spam(self, text: str) -> bool:
        """檢測垃圾內容"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.spam_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # 檢查過多的大寫字母
        if len(text) > 20:
            upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if upper_ratio > 0.7:
                return True
        
        # 檢查重複字符
        if re.search(r'(.)\1{4,}', text):
            return True
        
        return False
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """提取關鍵詞"""
        if not text:
            return []
        
        # 清理文字
        cleaned = self.clean_text(text, remove_special_chars=True)
        
        # 分割單詞
        words = cleaned.lower().split()
        
        # 過濾短詞和常見停用詞
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words 
                   if len(word) >= min_length and word not in stop_words]
        
        return list(set(keywords))


class DataValidator:
    """資料驗證器"""
    
    def __init__(self):
        self.logger = get_enhanced_logger("data_validator")
        
        # URL 驗證模式
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # 電子郵件驗證模式
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # 薪資範圍
        self.salary_ranges = {
            CompensationInterval.HOURLY: (5, 200),
            CompensationInterval.DAILY: (50, 1000),
            CompensationInterval.WEEKLY: (200, 5000),
            CompensationInterval.MONTHLY: (1000, 20000),
            CompensationInterval.YEARLY: (15000, 500000)
        }
    
    def validate_url(self, url: str) -> bool:
        """驗證 URL 格式"""
        if not url or not isinstance(url, str):
            return False
        return bool(self.url_pattern.match(url))
    
    def validate_email(self, email: str) -> bool:
        """驗證電子郵件格式"""
        if not email or not isinstance(email, str):
            return False
        return bool(self.email_pattern.match(email))
    
    def validate_salary(self, min_amount: Optional[float], max_amount: Optional[float], 
                       interval: Optional[CompensationInterval]) -> bool:
        """驗證薪資範圍"""
        if not interval or interval not in self.salary_ranges:
            return min_amount is None and max_amount is None
        
        min_valid, max_valid = self.salary_ranges[interval]
        
        if min_amount is not None:
            if min_amount < min_valid or min_amount > max_valid:
                return False
        
        if max_amount is not None:
            if max_amount < min_valid or max_amount > max_valid:
                return False
        
        if min_amount is not None and max_amount is not None:
            if min_amount > max_amount:
                return False
        
        return True
    
    def validate_date(self, date_str: str) -> bool:
        """驗證日期格式"""
        if not date_str:
            return False
        
        try:
            # 嘗試解析常見的日期格式
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # 檢查日期是否合理（不能太久遠或太未來）
                    now = datetime.now()
                    if parsed_date > now + timedelta(days=365):  # 不能超過一年後
                        return False
                    if parsed_date < now - timedelta(days=365*5):  # 不能超過五年前
                        return False
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def validate_job_post(self, job: JobPost) -> List[DataQualityIssue]:
        """驗證職位資料"""
        issues = []
        
        # 檢查必填欄位
        if not job.title or not job.title.strip():
            issues.append(DataQualityIssue.MISSING_REQUIRED_FIELD)
        
        if not job.company or not job.company.strip():
            issues.append(DataQualityIssue.MISSING_REQUIRED_FIELD)
        
        # 驗證 URL
        if job.job_url and not self.validate_url(job.job_url):
            issues.append(DataQualityIssue.INVALID_URL)
        
        if job.job_url_direct and not self.validate_url(job.job_url_direct):
            issues.append(DataQualityIssue.INVALID_URL)
        
        if job.company_url and not self.validate_url(job.company_url):
            issues.append(DataQualityIssue.INVALID_URL)
        
        # 驗證電子郵件
        if job.emails:
            for email in job.emails:
                if not self.validate_email(email):
                    issues.append(DataQualityIssue.INVALID_EMAIL)
        
        # 驗證薪資
        if job.compensation:
            if not self.validate_salary(
                job.compensation.min_amount,
                job.compensation.max_amount,
                job.compensation.interval
            ):
                issues.append(DataQualityIssue.INVALID_SALARY)
        
        # 驗證日期
        if job.date_posted and not self.validate_date(str(job.date_posted)):
            issues.append(DataQualityIssue.INVALID_DATE)
        
        return issues


class DuplicateDetector:
    """重複檢測器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.logger = get_enhanced_logger("duplicate_detector")
        self.text_cleaner = TextCleaner()
    
    def generate_job_hash(self, job: JobPost) -> str:
        """生成職位雜湊值"""
        # 使用關鍵欄位生成雜湊
        key_fields = [
            job.title.lower().strip() if job.title else '',
            job.company.lower().strip() if job.company else '',
            str(job.location).lower().strip() if job.location else ''
        ]
        
        # 清理和正規化
        cleaned_fields = []
        for field in key_fields:
            cleaned = self.text_cleaner.clean_text(field, remove_special_chars=True)
            cleaned_fields.append(cleaned)
        
        combined = '|'.join(cleaned_fields)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def calculate_similarity(self, job1: JobPost, job2: JobPost) -> float:
        """計算兩個職位的相似度"""
        # 標題相似度
        title1 = self.text_cleaner.clean_text(job1.title or '', remove_special_chars=True)
        title2 = self.text_cleaner.clean_text(job2.title or '', remove_special_chars=True)
        title_sim = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        
        # 公司相似度
        company1 = self.text_cleaner.clean_text(job1.company or '', remove_special_chars=True)
        company2 = self.text_cleaner.clean_text(job2.company or '', remove_special_chars=True)
        company_sim = SequenceMatcher(None, company1.lower(), company2.lower()).ratio()
        
        # 地點相似度
        location1 = str(job1.location or '').lower()
        location2 = str(job2.location or '').lower()
        location_sim = SequenceMatcher(None, location1, location2).ratio()
        
        # 描述相似度（如果有的話）
        desc_sim = 0.0
        if job1.description and job2.description:
            desc1 = self.text_cleaner.clean_text(job1.description, remove_special_chars=True)[:500]
            desc2 = self.text_cleaner.clean_text(job2.description, remove_special_chars=True)[:500]
            desc_sim = SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
        
        # 加權平均
        weights = [0.4, 0.3, 0.2, 0.1]  # 標題、公司、地點、描述
        similarities = [title_sim, company_sim, location_sim, desc_sim]
        
        weighted_sim = sum(w * s for w, s in zip(weights, similarities))
        return weighted_sim
    
    def find_duplicates(self, jobs: List[JobPost]) -> List[Tuple[int, int, float]]:
        """找出重複的職位"""
        duplicates = []
        
        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                similarity = self.calculate_similarity(jobs[i], jobs[j])
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
        
        return duplicates
    
    def remove_duplicates(self, jobs: List[JobPost]) -> Tuple[List[JobPost], int]:
        """移除重複的職位"""
        if not jobs:
            return jobs, 0
        
        # 使用雜湊值快速檢測完全重複
        seen_hashes = set()
        hash_filtered = []
        
        for job in jobs:
            job_hash = self.generate_job_hash(job)
            if job_hash not in seen_hashes:
                seen_hashes.add(job_hash)
                hash_filtered.append(job)
        
        hash_removed = len(jobs) - len(hash_filtered)
        
        # 使用相似度檢測近似重複
        if len(hash_filtered) <= 1:
            return hash_filtered, hash_removed
        
        duplicates = self.find_duplicates(hash_filtered)
        
        # 標記要移除的索引
        to_remove = set()
        for i, j, similarity in duplicates:
            # 保留較完整的職位（有更多資訊的）
            job_i = hash_filtered[i]
            job_j = hash_filtered[j]
            
            score_i = self._calculate_completeness_score(job_i)
            score_j = self._calculate_completeness_score(job_j)
            
            if score_i >= score_j:
                to_remove.add(j)
            else:
                to_remove.add(i)
        
        # 移除重複項
        final_jobs = [job for idx, job in enumerate(hash_filtered) if idx not in to_remove]
        
        total_removed = hash_removed + len(to_remove)
        
        self.logger.info(
            f"重複檢測完成",
            category=LogCategory.GENERAL,
            metadata={
                'original_count': len(jobs),
                'final_count': len(final_jobs),
                'hash_duplicates_removed': hash_removed,
                'similarity_duplicates_removed': len(to_remove),
                'total_removed': total_removed
            }
        )
        
        return final_jobs, total_removed
    
    def _calculate_completeness_score(self, job: JobPost) -> int:
        """計算職位資料完整度分數"""
        score = 0
        
        # 基本資訊
        if job.title: score += 1
        if job.company: score += 1
        if job.location: score += 1
        if job.description: score += 2
        
        # 額外資訊
        if job.job_url: score += 1
        if job.compensation: score += 1
        if job.job_type: score += 1
        if job.date_posted: score += 1
        if job.emails: score += 1
        
        return score


class DataQualityProcessor:
    """資料品質處理器"""
    
    def __init__(self, remove_duplicates: bool = True, 
                 clean_text: bool = True, validate_data: bool = True,
                 similarity_threshold: float = 0.85):
        self.remove_duplicates = remove_duplicates
        self.clean_text = clean_text
        self.validate_data = validate_data
        
        self.logger = get_enhanced_logger("data_quality")
        self.text_cleaner = TextCleaner()
        self.validator = DataValidator()
        self.duplicate_detector = DuplicateDetector(similarity_threshold)
    
    def process_job_response(self, job_response: JobResponse) -> Tuple[JobResponse, QualityReport]:
        """處理職位響應，改善資料品質"""
        start_time = datetime.now()
        
        if not job_response.success or not job_response.jobs:
            return job_response, QualityReport(
                total_jobs=0,
                valid_jobs=0,
                issues_found={},
                duplicates_removed=0,
                cleaned_fields={},
                processing_time=0.0,
                recommendations=[]
            )
        
        original_count = len(job_response.jobs)
        processed_jobs = job_response.jobs.copy()
        
        # 統計資訊
        issues_found = {issue: 0 for issue in DataQualityIssue}
        cleaned_fields = {}
        duplicates_removed = 0
        
        # 1. 資料清理
        if self.clean_text:
            processed_jobs, field_stats = self._clean_jobs(processed_jobs)
            cleaned_fields.update(field_stats)
        
        # 2. 資料驗證
        if self.validate_data:
            processed_jobs, validation_issues = self._validate_jobs(processed_jobs)
            for issue, count in validation_issues.items():
                issues_found[issue] += count
        
        # 3. 重複檢測和移除
        if self.remove_duplicates:
            processed_jobs, duplicates_removed = self.duplicate_detector.remove_duplicates(processed_jobs)
        
        # 4. 最終過濾
        valid_jobs = self._filter_valid_jobs(processed_jobs)
        
        # 生成報告
        processing_time = (datetime.now() - start_time).total_seconds()
        
        report = QualityReport(
            total_jobs=original_count,
            valid_jobs=len(valid_jobs),
            issues_found=issues_found,
            duplicates_removed=duplicates_removed,
            cleaned_fields=cleaned_fields,
            processing_time=processing_time,
            recommendations=self._generate_recommendations(issues_found, original_count)
        )
        
        # 創建新的響應
        new_response = JobResponse(
            success=True,
            error=None,
            jobs=valid_jobs
        )
        
        self.logger.info(
            f"資料品質處理完成",
            category=LogCategory.GENERAL,
            metadata={
                'original_jobs': original_count,
                'final_jobs': len(valid_jobs),
                'quality_score': report.quality_score,
                'processing_time': processing_time
            }
        )
        
        return new_response, report
    
    def _clean_jobs(self, jobs: List[JobPost]) -> Tuple[List[JobPost], Dict[str, int]]:
        """清理職位資料"""
        cleaned_fields = {}
        
        for job in jobs:
            # 清理標題
            if job.title:
                original = job.title
                job.title = self.text_cleaner.clean_text(job.title)
                if original != job.title:
                    cleaned_fields['title'] = cleaned_fields.get('title', 0) + 1
            
            # 清理公司名稱
            if job.company:
                original = job.company
                job.company = self.text_cleaner.clean_text(job.company)
                if original != job.company:
                    cleaned_fields['company'] = cleaned_fields.get('company', 0) + 1
            
            # 清理描述
            if job.description:
                original = job.description
                job.description = self.text_cleaner.clean_text(job.description)
                if original != job.description:
                    cleaned_fields['description'] = cleaned_fields.get('description', 0) + 1
            
            # 檢測垃圾內容
            if job.description and self.text_cleaner.detect_spam(job.description):
                job.description = "[內容已過濾：檢測到可疑內容]"
                cleaned_fields['spam_filtered'] = cleaned_fields.get('spam_filtered', 0) + 1
        
        return jobs, cleaned_fields
    
    def _validate_jobs(self, jobs: List[JobPost]) -> Tuple[List[JobPost], Dict[DataQualityIssue, int]]:
        """驗證職位資料"""
        validation_issues = {issue: 0 for issue in DataQualityIssue}
        
        for job in jobs:
            issues = self.validator.validate_job_post(job)
            for issue in issues:
                validation_issues[issue] += 1
        
        return jobs, validation_issues
    
    def _filter_valid_jobs(self, jobs: List[JobPost]) -> List[JobPost]:
        """過濾有效的職位"""
        valid_jobs = []
        
        for job in jobs:
            # 基本有效性檢查
            if (job.title and job.title.strip() and 
                job.company and job.company.strip()):
                valid_jobs.append(job)
        
        return valid_jobs
    
    def _generate_recommendations(self, issues: Dict[DataQualityIssue, int], 
                                total_jobs: int) -> List[str]:
        """生成改善建議"""
        recommendations = []
        
        if total_jobs == 0:
            return recommendations
        
        # 檢查各種問題的比例
        for issue, count in issues.items():
            if count == 0:
                continue
            
            percentage = (count / total_jobs) * 100
            
            if issue == DataQualityIssue.MISSING_REQUIRED_FIELD and percentage > 10:
                recommendations.append("建議改善爬蟲邏輯以獲取更完整的必填欄位")
            
            elif issue == DataQualityIssue.INVALID_URL and percentage > 5:
                recommendations.append("建議加強 URL 格式驗證和清理")
            
            elif issue == DataQualityIssue.INVALID_EMAIL and percentage > 5:
                recommendations.append("建議改善電子郵件提取和驗證邏輯")
            
            elif issue == DataQualityIssue.INVALID_SALARY and percentage > 15:
                recommendations.append("建議改善薪資資訊解析和驗證")
            
            elif issue == DataQualityIssue.DUPLICATE_CONTENT and percentage > 20:
                recommendations.append("建議加強重複檢測機制")
        
        if not recommendations:
            recommendations.append("資料品質良好，無需特別改善")
        
        return recommendations


# 便利函數
def improve_job_data_quality(job_response: JobResponse, 
                            remove_duplicates: bool = True,
                            clean_text: bool = True,
                            validate_data: bool = True,
                            similarity_threshold: float = 0.85) -> Tuple[JobResponse, QualityReport]:
    """改善職位資料品質"""
    processor = DataQualityProcessor(
        remove_duplicates=remove_duplicates,
        clean_text=clean_text,
        validate_data=validate_data,
        similarity_threshold=similarity_threshold
    )
    
    return processor.process_job_response(job_response)


def quality_check_decorator(remove_duplicates: bool = True, 
                          clean_text: bool = True,
                          validate_data: bool = True):
    """資料品質檢查裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if isinstance(result, JobResponse):
                improved_result, quality_report = improve_job_data_quality(
                    result, remove_duplicates, clean_text, validate_data
                )
                
                # 記錄品質報告
                logger = get_enhanced_logger("quality_decorator")
                logger.info(
                    f"資料品質檢查完成",
                    category=LogCategory.GENERAL,
                    metadata=quality_report.to_dict()
                )
                
                return improved_result
            
            return result
        
        return wrapper
    return decorator
