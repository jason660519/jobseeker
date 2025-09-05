#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例驗證器
驗證生成的測試案例的質量、有效性和完整性

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, Counter
import statistics

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMProvider


class ValidationSeverity(Enum):
    """驗證問題嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """驗證類別"""
    CONTENT_QUALITY = "content_quality"  # 內容質量
    LANGUAGE_CONSISTENCY = "language_consistency"  # 語言一致性
    INTENT_CLARITY = "intent_clarity"  # 意圖清晰度
    ENTITY_EXTRACTION = "entity_extraction"  # 實體提取
    EDGE_CASE_COVERAGE = "edge_case_coverage"  # 邊界案例覆蓋
    DIVERSITY = "diversity"  # 多樣性
    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"  # 一致性
    BIAS_DETECTION = "bias_detection"  # 偏見檢測
    SECURITY = "security"  # 安全性


@dataclass
class ValidationIssue:
    """驗證問題"""
    category: ValidationCategory
    severity: ValidationSeverity
    test_case_id: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    auto_fixable: bool = False


@dataclass
class ValidationMetrics:
    """驗證指標"""
    total_cases: int
    valid_cases: int
    invalid_cases: int
    warning_cases: int
    error_cases: int
    critical_cases: int
    coverage_score: float
    diversity_score: float
    quality_score: float
    overall_score: float
    category_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """驗證報告"""
    validation_time: datetime
    metrics: ValidationMetrics
    issues: List[ValidationIssue]
    recommendations: List[str]
    summary: Dict[str, Any]
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)


class LLMTestCaseValidator:
    """LLM測試案例驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.validation_rules = self._load_validation_rules()
        self.language_patterns = self._load_language_patterns()
        self.intent_keywords = self._load_intent_keywords()
        self.security_patterns = self._load_security_patterns()
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """載入驗證規則"""
        return {
            "min_query_length": 3,
            "max_query_length": 500,
            "min_confidence": 0.0,
            "max_confidence": 1.0,
            "required_fields": ["id", "query", "expected_intent", "category"],
            "valid_intents": [
                "job_search", "career_advice", "skill_query", "salary_query",
                "location_query", "company_query", "unknown", "inappropriate_query",
                "weather_query", "entertainment_query", "restaurant_query", "spam_query"
            ],
            "language_codes": ["zh-TW", "zh-CN", "en", "ja", "ko", "mixed"],
            "complexity_levels": ["simple", "medium", "complex", "extreme"],
            "min_diversity_threshold": 0.7,
            "min_coverage_threshold": 0.8
        }
    
    def _load_language_patterns(self) -> Dict[str, List[str]]:
        """載入語言模式"""
        return {
            "zh-TW": [r"[\u4e00-\u9fff]+", r"[，。？！；：]"],
            "zh-CN": [r"[\u4e00-\u9fff]+", r"[，。？！；：]"],
            "en": [r"[a-zA-Z]+", r"[,.?!;:]"],
            "ja": [r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+"],
            "ko": [r"[\uac00-\ud7af]+"],
            "mixed": [r"[\u4e00-\u9fff]+.*[a-zA-Z]+|[a-zA-Z]+.*[\u4e00-\u9fff]+"]
        }
    
    def _load_intent_keywords(self) -> Dict[str, List[str]]:
        """載入意圖關鍵詞"""
        return {
            "job_search": [
                "工作", "職缺", "職位", "求職", "找工作", "應徵", "招聘",
                "job", "position", "career", "employment", "hiring", "work",
                "仕事", "就職", "채용", "일자리"
            ],
            "career_advice": [
                "轉職", "職涯", "建議", "發展", "規劃",
                "career change", "advice", "development", "planning",
                "転職", "キャリア", "전직", "경력"
            ],
            "salary_query": [
                "薪資", "薪水", "待遇", "收入", "年薪", "月薪",
                "salary", "wage", "compensation", "income", "pay",
                "給料", "年収", "급여", "연봉"
            ],
            "location_query": [
                "地點", "位置", "地區", "城市", "台北", "新竹",
                "location", "place", "city", "area", "remote",
                "場所", "地域", "위치", "지역"
            ]
        }
    
    def _load_security_patterns(self) -> List[str]:
        """載入安全模式"""
        return [
            r"hack|hacking|破解|入侵",
            r"illegal|違法|非法",
            r"steal|偷取|竊取",
            r"fraud|詐騙|欺詐",
            r"password|密碼|密码",
            r"credit card|信用卡|信用卡",
            r"social security|身分證|身份证",
            r"personal information|個人資料|个人信息"
        ]
    
    def validate_test_cases(self, test_cases: List[Dict[str, Any]]) -> ValidationReport:
        """驗證測試案例"""
        print(f"🔍 開始驗證 {len(test_cases)} 個測試案例...")
        
        start_time = time.time()
        issues = []
        
        # 執行各種驗證
        issues.extend(self._validate_content_quality(test_cases))
        issues.extend(self._validate_language_consistency(test_cases))
        issues.extend(self._validate_intent_clarity(test_cases))
        issues.extend(self._validate_entity_extraction(test_cases))
        issues.extend(self._validate_completeness(test_cases))
        issues.extend(self._validate_consistency(test_cases))
        issues.extend(self._validate_diversity(test_cases))
        issues.extend(self._validate_edge_case_coverage(test_cases))
        issues.extend(self._validate_bias_detection(test_cases))
        issues.extend(self._validate_security(test_cases))
        
        # 計算指標
        metrics = self._calculate_metrics(test_cases, issues)
        
        # 生成建議
        recommendations = self._generate_recommendations(issues, metrics)
        
        # 創建詳細分析
        detailed_analysis = self._create_detailed_analysis(test_cases, issues)
        
        # 創建摘要
        summary = self._create_summary(metrics, issues)
        
        validation_time = time.time() - start_time
        
        report = ValidationReport(
            validation_time=datetime.now(),
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            summary=summary,
            detailed_analysis=detailed_analysis
        )
        
        print(f"   ✅ 驗證完成，耗時 {validation_time:.2f} 秒")
        print(f"   📊 發現 {len(issues)} 個問題")
        
        return report
    
    def _validate_content_quality(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證內容質量"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            
            # 檢查查詢長度
            if len(query) < self.validation_rules["min_query_length"]:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.ERROR,
                    test_case_id=case_id,
                    message="查詢內容過短",
                    details={"query_length": len(query), "min_required": self.validation_rules["min_query_length"]},
                    suggestions=["增加查詢內容的長度和詳細程度"]
                ))
            
            if len(query) > self.validation_rules["max_query_length"]:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.WARNING,
                    test_case_id=case_id,
                    message="查詢內容過長",
                    details={"query_length": len(query), "max_allowed": self.validation_rules["max_query_length"]},
                    suggestions=["簡化查詢內容，保持簡潔明確"]
                ))
            
            # 檢查空白或無意義內容
            if not query.strip():
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.CRITICAL,
                    test_case_id=case_id,
                    message="查詢內容為空",
                    details={"query": query},
                    suggestions=["提供有意義的查詢內容"]
                ))
            
            # 檢查重複字符
            if re.search(r"(.)\1{5,}", query):
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.WARNING,
                    test_case_id=case_id,
                    message="查詢包含過多重複字符",
                    details={"query": query},
                    suggestions=["減少重複字符，提高內容質量"]
                ))
            
            # 檢查特殊字符過多
            special_char_ratio = len(re.findall(r"[^\w\s\u4e00-\u9fff]", query)) / max(len(query), 1)
            if special_char_ratio > 0.3:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.WARNING,
                    test_case_id=case_id,
                    message="查詢包含過多特殊字符",
                    details={"special_char_ratio": special_char_ratio, "query": query},
                    suggestions=["減少特殊字符的使用"]
                ))
        
        return issues
    
    def _validate_language_consistency(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證語言一致性"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            declared_language = case.get("language", "")
            
            # 檢測實際語言
            detected_language = self._detect_language(query)
            
            if detected_language != declared_language:
                issues.append(ValidationIssue(
                    category=ValidationCategory.LANGUAGE_CONSISTENCY,
                    severity=ValidationSeverity.WARNING,
                    test_case_id=case_id,
                    message="聲明語言與檢測語言不一致",
                    details={
                        "declared_language": declared_language,
                        "detected_language": detected_language,
                        "query": query
                    },
                    suggestions=[f"將語言標記更改為 {detected_language} 或調整查詢內容"]
                ))
        
        return issues
    
    def _validate_intent_clarity(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證意圖清晰度"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            expected_intent = case.get("expected_intent", "")
            
            # 檢查意圖是否有效
            if expected_intent not in self.validation_rules["valid_intents"]:
                issues.append(ValidationIssue(
                    category=ValidationCategory.INTENT_CLARITY,
                    severity=ValidationSeverity.ERROR,
                    test_case_id=case_id,
                    message="無效的期望意圖",
                    details={
                        "expected_intent": expected_intent,
                        "valid_intents": self.validation_rules["valid_intents"]
                    },
                    suggestions=["使用有效的意圖標籤"]
                ))
            
            # 檢查查詢與意圖的匹配度
            intent_keywords = self.intent_keywords.get(expected_intent, [])
            if intent_keywords:
                has_keyword = any(keyword.lower() in query.lower() for keyword in intent_keywords)
                if not has_keyword and expected_intent != "unknown":
                    issues.append(ValidationIssue(
                        category=ValidationCategory.INTENT_CLARITY,
                        severity=ValidationSeverity.WARNING,
                        test_case_id=case_id,
                        message="查詢內容與期望意圖不匹配",
                        details={
                            "query": query,
                            "expected_intent": expected_intent,
                            "missing_keywords": intent_keywords
                        },
                        suggestions=["在查詢中添加相關關鍵詞或調整期望意圖"]
                    ))
        
        return issues
    
    def _validate_entity_extraction(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證實體提取"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            expected_entities = case.get("expected_entities", {})
            
            # 檢查實體是否在查詢中存在
            for entity_type, entity_value in expected_entities.items():
                if isinstance(entity_value, str) and entity_value not in query:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.ENTITY_EXTRACTION,
                        severity=ValidationSeverity.WARNING,
                        test_case_id=case_id,
                        message="期望實體在查詢中未找到",
                        details={
                            "entity_type": entity_type,
                            "entity_value": entity_value,
                            "query": query
                        },
                        suggestions=["確保實體值確實出現在查詢中"]
                    ))
        
        return issues
    
    def _validate_completeness(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證完整性"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            
            # 檢查必需字段
            for field in self.validation_rules["required_fields"]:
                if field not in case or not case[field]:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.COMPLETENESS,
                        severity=ValidationSeverity.ERROR,
                        test_case_id=case_id,
                        message=f"缺少必需字段: {field}",
                        details={"missing_field": field},
                        suggestions=[f"添加 {field} 字段"]
                    ))
            
            # 檢查置信度範圍
            confidence_range = case.get("expected_confidence_range", [])
            if isinstance(confidence_range, list) and len(confidence_range) == 2:
                min_conf, max_conf = confidence_range
                if not (self.validation_rules["min_confidence"] <= min_conf <= max_conf <= self.validation_rules["max_confidence"]):
                    issues.append(ValidationIssue(
                        category=ValidationCategory.COMPLETENESS,
                        severity=ValidationSeverity.ERROR,
                        test_case_id=case_id,
                        message="無效的置信度範圍",
                        details={"confidence_range": confidence_range},
                        suggestions=["設置有效的置信度範圍 (0.0-1.0)"]
                    ))
        
        return issues
    
    def _validate_consistency(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證一致性"""
        issues = []
        
        # 檢查ID唯一性
        ids = [case.get("id", "") for case in test_cases]
        duplicate_ids = [id for id, count in Counter(ids).items() if count > 1]
        
        for dup_id in duplicate_ids:
            issues.append(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                test_case_id=dup_id,
                message="重複的測試案例ID",
                details={"duplicate_id": dup_id},
                suggestions=["確保每個測試案例都有唯一的ID"]
            ))
        
        # 檢查查詢重複
        queries = [case.get("query", "") for case in test_cases]
        duplicate_queries = [query for query, count in Counter(queries).items() if count > 1 and query.strip()]
        
        for dup_query in duplicate_queries:
            matching_cases = [case.get("id", "unknown") for case in test_cases if case.get("query") == dup_query]
            issues.append(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                test_case_id=",".join(matching_cases),
                message="重複的查詢內容",
                details={"duplicate_query": dup_query, "case_ids": matching_cases},
                suggestions=["增加查詢的多樣性，避免重複內容"]
            ))
        
        return issues
    
    def _validate_diversity(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證多樣性"""
        issues = []
        
        if not test_cases:
            return issues
        
        # 計算類別多樣性
        categories = [case.get("category", "") for case in test_cases]
        category_distribution = Counter(categories)
        total_cases = len(test_cases)
        
        # 檢查是否有類別過度集中
        for category, count in category_distribution.items():
            ratio = count / total_cases
            if ratio > 0.5:  # 超過50%集中在一個類別
                issues.append(ValidationIssue(
                    category=ValidationCategory.DIVERSITY,
                    severity=ValidationSeverity.WARNING,
                    test_case_id="global",
                    message=f"類別 {category} 過度集中",
                    details={"category": category, "ratio": ratio, "count": count},
                    suggestions=["增加其他類別的測試案例以提高多樣性"]
                ))
        
        # 計算複雜度多樣性
        complexities = [case.get("complexity", "") for case in test_cases]
        complexity_distribution = Counter(complexities)
        
        # 檢查是否缺少某些複雜度級別
        expected_complexities = set(self.validation_rules["complexity_levels"])
        actual_complexities = set(complexities)
        missing_complexities = expected_complexities - actual_complexities
        
        if missing_complexities:
            issues.append(ValidationIssue(
                category=ValidationCategory.DIVERSITY,
                severity=ValidationSeverity.INFO,
                test_case_id="global",
                message="缺少某些複雜度級別",
                details={"missing_complexities": list(missing_complexities)},
                suggestions=[f"添加 {', '.join(missing_complexities)} 複雜度的測試案例"]
            ))
        
        return issues
    
    def _validate_edge_case_coverage(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證邊界案例覆蓋"""
        issues = []
        
        edge_case_count = sum(1 for case in test_cases if case.get("category") == "edge_case")
        total_cases = len(test_cases)
        
        if total_cases > 0:
            edge_case_ratio = edge_case_count / total_cases
            if edge_case_ratio < 0.05:  # 少於5%的邊界案例
                issues.append(ValidationIssue(
                    category=ValidationCategory.EDGE_CASE_COVERAGE,
                    severity=ValidationSeverity.WARNING,
                    test_case_id="global",
                    message="邊界案例覆蓋不足",
                    details={"edge_case_ratio": edge_case_ratio, "edge_case_count": edge_case_count},
                    suggestions=["增加更多邊界案例以提高測試覆蓋率"]
                ))
        
        return issues
    
    def _validate_bias_detection(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證偏見檢測"""
        issues = []
        
        # 檢查性別偏見
        gender_bias_patterns = [r"男性", r"女性", r"male", r"female", r"man", r"woman"]
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            
            for pattern in gender_bias_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        category=ValidationCategory.BIAS_DETECTION,
                        severity=ValidationSeverity.INFO,
                        test_case_id=case_id,
                        message="檢測到可能的性別偏見",
                        details={"pattern": pattern, "query": query},
                        suggestions=["檢查是否存在性別偏見，確保測試案例的公平性"]
                    ))
        
        return issues
    
    def _validate_security(self, test_cases: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """驗證安全性"""
        issues = []
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            
            for pattern in self.security_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        category=ValidationCategory.SECURITY,
                        severity=ValidationSeverity.WARNING,
                        test_case_id=case_id,
                        message="檢測到潛在的安全風險內容",
                        details={"pattern": pattern, "query": query},
                        suggestions=["檢查查詢內容是否包含不當或危險信息"]
                    ))
        
        return issues
    
    def _detect_language(self, text: str) -> str:
        """檢測文本語言"""
        for lang, patterns in self.language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return lang
        return "unknown"
    
    def _calculate_metrics(self, test_cases: List[Dict[str, Any]], issues: List[ValidationIssue]) -> ValidationMetrics:
        """計算驗證指標"""
        total_cases = len(test_cases)
        
        # 按嚴重程度統計問題
        severity_counts = Counter(issue.severity for issue in issues)
        critical_cases = severity_counts[ValidationSeverity.CRITICAL]
        error_cases = severity_counts[ValidationSeverity.ERROR]
        warning_cases = severity_counts[ValidationSeverity.WARNING]
        
        # 計算有效案例數
        invalid_case_ids = set()
        for issue in issues:
            if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
                invalid_case_ids.add(issue.test_case_id)
        
        invalid_cases = len(invalid_case_ids)
        valid_cases = total_cases - invalid_cases
        
        # 計算覆蓋率分數
        categories = set(case.get("category", "") for case in test_cases)
        expected_categories = 10  # 預期的類別數量
        coverage_score = min(len(categories) / expected_categories, 1.0)
        
        # 計算多樣性分數
        if total_cases > 0:
            category_distribution = Counter(case.get("category", "") for case in test_cases)
            max_category_ratio = max(category_distribution.values()) / total_cases
            diversity_score = 1.0 - max_category_ratio
        else:
            diversity_score = 0.0
        
        # 計算質量分數
        if total_cases > 0:
            quality_score = valid_cases / total_cases
        else:
            quality_score = 0.0
        
        # 計算總體分數
        overall_score = (coverage_score + diversity_score + quality_score) / 3
        
        # 計算類別分數
        category_scores = {}
        for category in ValidationCategory:
            category_issues = [issue for issue in issues if issue.category == category]
            if category_issues:
                severity_weights = {
                    ValidationSeverity.INFO: 0.1,
                    ValidationSeverity.WARNING: 0.3,
                    ValidationSeverity.ERROR: 0.7,
                    ValidationSeverity.CRITICAL: 1.0
                }
                total_weight = sum(severity_weights[issue.severity] for issue in category_issues)
                category_scores[category.value] = max(0.0, 1.0 - (total_weight / total_cases))
            else:
                category_scores[category.value] = 1.0
        
        return ValidationMetrics(
            total_cases=total_cases,
            valid_cases=valid_cases,
            invalid_cases=invalid_cases,
            warning_cases=warning_cases,
            error_cases=error_cases,
            critical_cases=critical_cases,
            coverage_score=coverage_score,
            diversity_score=diversity_score,
            quality_score=quality_score,
            overall_score=overall_score,
            category_scores=category_scores
        )
    
    def _generate_recommendations(self, issues: List[ValidationIssue], metrics: ValidationMetrics) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 基於指標的建議
        if metrics.coverage_score < 0.8:
            recommendations.append("增加測試案例的類別覆蓋率，確保涵蓋所有重要場景")
        
        if metrics.diversity_score < 0.7:
            recommendations.append("提高測試案例的多樣性，避免過度集中在某些類別")
        
        if metrics.quality_score < 0.9:
            recommendations.append("改善測試案例的質量，修復發現的錯誤和問題")
        
        # 基於問題的建議
        issue_categories = Counter(issue.category for issue in issues)
        
        if issue_categories[ValidationCategory.CONTENT_QUALITY] > 0:
            recommendations.append("改善內容質量，確保查詢長度適中且有意義")
        
        if issue_categories[ValidationCategory.LANGUAGE_CONSISTENCY] > 0:
            recommendations.append("檢查語言標記的一致性，確保聲明語言與實際內容匹配")
        
        if issue_categories[ValidationCategory.INTENT_CLARITY] > 0:
            recommendations.append("提高意圖的清晰度，確保查詢內容與期望意圖匹配")
        
        if issue_categories[ValidationCategory.SECURITY] > 0:
            recommendations.append("檢查並移除可能的安全風險內容")
        
        return recommendations
    
    def _create_detailed_analysis(self, test_cases: List[Dict[str, Any]], issues: List[ValidationIssue]) -> Dict[str, Any]:
        """創建詳細分析"""
        analysis = {
            "category_distribution": Counter(case.get("category", "") for case in test_cases),
            "complexity_distribution": Counter(case.get("complexity", "") for case in test_cases),
            "language_distribution": Counter(case.get("language", "") for case in test_cases),
            "issue_distribution": Counter(issue.category.value for issue in issues),
            "severity_distribution": Counter(issue.severity.value for issue in issues),
            "query_length_stats": self._calculate_query_length_stats(test_cases),
            "confidence_range_stats": self._calculate_confidence_stats(test_cases)
        }
        
        return analysis
    
    def _calculate_query_length_stats(self, test_cases: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算查詢長度統計"""
        lengths = [len(case.get("query", "")) for case in test_cases]
        
        if lengths:
            return {
                "mean": statistics.mean(lengths),
                "median": statistics.median(lengths),
                "min": min(lengths),
                "max": max(lengths),
                "std": statistics.stdev(lengths) if len(lengths) > 1 else 0.0
            }
        else:
            return {"mean": 0, "median": 0, "min": 0, "max": 0, "std": 0}
    
    def _calculate_confidence_stats(self, test_cases: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算置信度統計"""
        confidence_ranges = []
        
        for case in test_cases:
            conf_range = case.get("expected_confidence_range", [])
            if isinstance(conf_range, list) and len(conf_range) == 2:
                confidence_ranges.extend(conf_range)
        
        if confidence_ranges:
            return {
                "mean": statistics.mean(confidence_ranges),
                "median": statistics.median(confidence_ranges),
                "min": min(confidence_ranges),
                "max": max(confidence_ranges),
                "std": statistics.stdev(confidence_ranges) if len(confidence_ranges) > 1 else 0.0
            }
        else:
            return {"mean": 0, "median": 0, "min": 0, "max": 0, "std": 0}
    
    def _create_summary(self, metrics: ValidationMetrics, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """創建摘要"""
        return {
            "total_cases": metrics.total_cases,
            "validation_status": "PASS" if metrics.overall_score >= 0.8 else "FAIL",
            "overall_score": metrics.overall_score,
            "key_metrics": {
                "coverage_score": metrics.coverage_score,
                "diversity_score": metrics.diversity_score,
                "quality_score": metrics.quality_score
            },
            "issue_summary": {
                "total_issues": len(issues),
                "critical": metrics.critical_cases,
                "error": metrics.error_cases,
                "warning": metrics.warning_cases
            }
        }
    
    def export_validation_report(self, report: ValidationReport, output_file: str = None) -> str:
        """導出驗證報告"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_report_{timestamp}.json"
        
        print(f"💾 導出驗證報告到 {output_file}...")
        
        report_data = {
            "validation_time": report.validation_time.isoformat(),
            "metrics": {
                "total_cases": report.metrics.total_cases,
                "valid_cases": report.metrics.valid_cases,
                "invalid_cases": report.metrics.invalid_cases,
                "warning_cases": report.metrics.warning_cases,
                "error_cases": report.metrics.error_cases,
                "critical_cases": report.metrics.critical_cases,
                "coverage_score": report.metrics.coverage_score,
                "diversity_score": report.metrics.diversity_score,
                "quality_score": report.metrics.quality_score,
                "overall_score": report.metrics.overall_score,
                "category_scores": report.metrics.category_scores
            },
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "test_case_id": issue.test_case_id,
                    "message": issue.message,
                    "details": issue.details,
                    "suggestions": issue.suggestions,
                    "auto_fixable": issue.auto_fixable
                }
                for issue in report.issues
            ],
            "recommendations": report.recommendations,
            "summary": report.summary,
            "detailed_analysis": report.detailed_analysis
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 驗證報告已導出")
        return output_file
    
    def print_validation_summary(self, report: ValidationReport) -> None:
        """打印驗證摘要"""
        print("\n" + "=" * 60)
        print("📋 LLM測試案例驗證報告")
        print("=" * 60)
        
        # 基本信息
        print(f"\n📊 基本信息:")
        print(f"   驗證時間: {report.validation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   總測試案例: {report.metrics.total_cases}")
        print(f"   有效案例: {report.metrics.valid_cases}")
        print(f"   無效案例: {report.metrics.invalid_cases}")
        
        # 驗證狀態
        status = report.summary["validation_status"]
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"\n{status_emoji} 驗證狀態: {status}")
        print(f"   總體分數: {report.metrics.overall_score:.3f}")
        
        # 關鍵指標
        print(f"\n📈 關鍵指標:")
        print(f"   覆蓋率分數: {report.metrics.coverage_score:.3f}")
        print(f"   多樣性分數: {report.metrics.diversity_score:.3f}")
        print(f"   質量分數: {report.metrics.quality_score:.3f}")
        
        # 問題統計
        print(f"\n⚠️ 問題統計:")
        print(f"   總問題數: {len(report.issues)}")
        print(f"   嚴重問題: {report.metrics.critical_cases}")
        print(f"   錯誤問題: {report.metrics.error_cases}")
        print(f"   警告問題: {report.metrics.warning_cases}")
        
        # 類別分數
        print(f"\n🎯 類別分數:")
        for category, score in sorted(report.metrics.category_scores.items()):
            score_emoji = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            print(f"   {score_emoji} {category}: {score:.3f}")
        
        # 建議
        if report.recommendations:
            print(f"\n💡 改進建議:")
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"   {i}. {recommendation}")
        
        # 詳細分析
        if report.detailed_analysis:
            print(f"\n📊 詳細分析:")
            
            # 類別分佈
            if "category_distribution" in report.detailed_analysis:
                print(f"   類別分佈:")
                for category, count in report.detailed_analysis["category_distribution"].most_common():
                    print(f"     {category}: {count}")
            
            # 查詢長度統計
            if "query_length_stats" in report.detailed_analysis:
                stats = report.detailed_analysis["query_length_stats"]
                print(f"   查詢長度統計:")
                print(f"     平均: {stats['mean']:.1f}, 中位數: {stats['median']:.1f}")
                print(f"     最小: {stats['min']}, 最大: {stats['max']}")
        
        print("\n" + "=" * 60)


def load_test_cases_from_file(file_path: str) -> List[Dict[str, Any]]:
    """從文件載入測試案例"""
    print(f"📂 載入測試案例從 {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "test_cases" in data:
            test_cases = data["test_cases"]
        elif isinstance(data, list):
            test_cases = data
        else:
            raise ValueError("無效的文件格式")
        
        print(f"   ✅ 成功載入 {len(test_cases)} 個測試案例")
        return test_cases
        
    except Exception as e:
        print(f"   ❌ 載入失敗: {str(e)}")
        return []


def main():
    """主函數 - 測試案例驗證器入口點"""
    print("🔍 LLM測試案例驗證器")
    print("=" * 60)
    
    validator = LLMTestCaseValidator()
    
    try:
        # 獲取輸入文件
        input_file = input("請輸入測試案例文件路徑 (或按Enter使用默認): ").strip()
        if not input_file:
            input_file = "generated_test_cases.json"
        
        # 載入測試案例
        test_cases = load_test_cases_from_file(input_file)
        
        if not test_cases:
            print("❌ 沒有找到有效的測試案例")
            return
        
        # 執行驗證
        print(f"\n🔍 開始驗證 {len(test_cases)} 個測試案例...")
        report = validator.validate_test_cases(test_cases)
        
        # 顯示摘要
        validator.print_validation_summary(report)
        
        # 導出報告
        export_report = input("\n是否導出詳細驗證報告？ (y/n): ").strip().lower()
        if export_report == 'y':
            output_file = validator.export_validation_report(report)
            print(f"   📄 報告文件: {output_file}")
        
        print("\n🎉 測試案例驗證完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 驗證過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 驗證過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()