#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例優化器
自動改進和優化測試案例的質量、多樣性和有效性

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import re
import time
import random
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
from llm_test_case_validator import LLMTestCaseValidator, ValidationReport


class OptimizationStrategy(Enum):
    """優化策略"""
    QUALITY_IMPROVEMENT = "quality_improvement"  # 質量改進
    DIVERSITY_ENHANCEMENT = "diversity_enhancement"  # 多樣性增強
    COVERAGE_EXPANSION = "coverage_expansion"  # 覆蓋率擴展
    BALANCE_ADJUSTMENT = "balance_adjustment"  # 平衡調整
    EDGE_CASE_GENERATION = "edge_case_generation"  # 邊界案例生成
    LANGUAGE_ENRICHMENT = "language_enrichment"  # 語言豐富化
    COMPLEXITY_BALANCING = "complexity_balancing"  # 複雜度平衡
    INTENT_CLARIFICATION = "intent_clarification"  # 意圖澄清


class OptimizationAction(Enum):
    """優化動作"""
    ADD = "add"  # 添加
    MODIFY = "modify"  # 修改
    REMOVE = "remove"  # 移除
    MERGE = "merge"  # 合併
    SPLIT = "split"  # 分割
    ENHANCE = "enhance"  # 增強


@dataclass
class OptimizationRule:
    """優化規則"""
    strategy: OptimizationStrategy
    action: OptimizationAction
    condition: str
    description: str
    priority: int
    auto_apply: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """優化結果"""
    original_count: int
    optimized_count: int
    actions_applied: List[str]
    improvements: Dict[str, float]
    new_test_cases: List[Dict[str, Any]]
    modified_test_cases: List[Dict[str, Any]]
    removed_test_cases: List[str]
    optimization_time: float
    quality_score_improvement: float


class LLMTestCaseOptimizer:
    """LLM測試案例優化器"""
    
    def __init__(self):
        """初始化優化器"""
        self.validator = LLMTestCaseValidator()
        self.optimization_rules = self._load_optimization_rules()
        self.templates = self._load_templates()
        self.enhancement_patterns = self._load_enhancement_patterns()
        
    def _load_optimization_rules(self) -> List[OptimizationRule]:
        """載入優化規則"""
        return [
            # 質量改進規則
            OptimizationRule(
                strategy=OptimizationStrategy.QUALITY_IMPROVEMENT,
                action=OptimizationAction.MODIFY,
                condition="query_too_short",
                description="擴展過短的查詢內容",
                priority=1
            ),
            OptimizationRule(
                strategy=OptimizationStrategy.QUALITY_IMPROVEMENT,
                action=OptimizationAction.MODIFY,
                condition="query_too_long",
                description="簡化過長的查詢內容",
                priority=2
            ),
            OptimizationRule(
                strategy=OptimizationStrategy.QUALITY_IMPROVEMENT,
                action=OptimizationAction.REMOVE,
                condition="empty_or_invalid",
                description="移除空白或無效的測試案例",
                priority=1
            ),
            
            # 多樣性增強規則
            OptimizationRule(
                strategy=OptimizationStrategy.DIVERSITY_ENHANCEMENT,
                action=OptimizationAction.ADD,
                condition="category_imbalance",
                description="添加缺少的類別測試案例",
                priority=3
            ),
            OptimizationRule(
                strategy=OptimizationStrategy.DIVERSITY_ENHANCEMENT,
                action=OptimizationAction.MODIFY,
                condition="duplicate_queries",
                description="修改重複的查詢內容",
                priority=2
            ),
            
            # 覆蓋率擴展規則
            OptimizationRule(
                strategy=OptimizationStrategy.COVERAGE_EXPANSION,
                action=OptimizationAction.ADD,
                condition="missing_edge_cases",
                description="添加邊界案例",
                priority=3
            ),
            OptimizationRule(
                strategy=OptimizationStrategy.COVERAGE_EXPANSION,
                action=OptimizationAction.ADD,
                condition="missing_languages",
                description="添加多語言測試案例",
                priority=4
            ),
            
            # 複雜度平衡規則
            OptimizationRule(
                strategy=OptimizationStrategy.COMPLEXITY_BALANCING,
                action=OptimizationAction.ADD,
                condition="complexity_imbalance",
                description="平衡複雜度分佈",
                priority=3
            ),
            
            # 意圖澄清規則
            OptimizationRule(
                strategy=OptimizationStrategy.INTENT_CLARIFICATION,
                action=OptimizationAction.MODIFY,
                condition="intent_mismatch",
                description="澄清意圖與查詢的匹配",
                priority=2
            )
        ]
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """載入測試案例模板"""
        return {
            "job_search": [
                "我想找{location}的{position}工作",
                "尋找{company}的{position}職位",
                "有沒有{skill}相關的工作機會",
                "Looking for {position} jobs in {location}",
                "Search for {skill} developer positions",
                "{location}で{position}の仕事を探しています",
                "{location}에서 {position} 일자리를 찾고 있습니다"
            ],
            "salary_query": [
                "{position}的薪資範圍是多少",
                "{location}{position}的平均薪水",
                "What's the salary range for {position}",
                "Average {position} salary in {location}",
                "{position}の給料はいくらですか",
                "{position}의 연봉은 얼마인가요"
            ],
            "career_advice": [
                "如何轉職到{field}領域",
                "想要成為{position}需要什麼技能",
                "How to transition to {field}",
                "Skills needed for {position} role",
                "{field}に転職するには",
                "{field}로 전직하려면"
            ],
            "edge_cases": [
                "我想找工作但不知道做什麼",
                "有沒有不用經驗的工作",
                "遠端工作機會",
                "part-time jobs for students",
                "work from home opportunities",
                "在宅勤務の仕事",
                "재택근무 가능한 일자리"
            ],
            "inappropriate": [
                "今天天氣如何",
                "推薦好吃的餐廳",
                "What's the weather like",
                "Best restaurants nearby",
                "今日の天気",
                "맛있는 식당 추천"
            ]
        }
    
    def _load_enhancement_patterns(self) -> Dict[str, List[str]]:
        """載入增強模式"""
        return {
            "locations": ["台北", "新竹", "台中", "高雄", "桃園", "台南", "New York", "San Francisco", "London", "Tokyo", "Seoul"],
            "positions": ["軟體工程師", "資料科學家", "產品經理", "設計師", "行銷專員", "software engineer", "data scientist", "product manager", "designer", "marketing specialist"],
            "skills": ["Python", "JavaScript", "React", "機器學習", "人工智慧", "UI/UX", "數據分析", "專案管理"],
            "companies": ["Google", "Microsoft", "Apple", "台積電", "聯發科", "鴻海", "TSMC", "MediaTek"],
            "fields": ["科技業", "金融業", "醫療業", "教育業", "製造業", "technology", "finance", "healthcare", "education"]
        }
    
    def optimize_test_cases(self, test_cases: List[Dict[str, Any]], 
                          strategies: List[OptimizationStrategy] = None,
                          target_count: int = None) -> OptimizationResult:
        """優化測試案例"""
        print(f"🔧 開始優化 {len(test_cases)} 個測試案例...")
        
        start_time = time.time()
        original_count = len(test_cases)
        
        if strategies is None:
            strategies = list(OptimizationStrategy)
        
        # 初始驗證
        initial_report = self.validator.validate_test_cases(test_cases)
        initial_quality_score = initial_report.metrics.overall_score
        
        # 複製測試案例以避免修改原始數據
        optimized_cases = [case.copy() for case in test_cases]
        actions_applied = []
        new_cases = []
        modified_cases = []
        removed_case_ids = []
        
        # 應用優化策略
        for strategy in strategies:
            print(f"   🎯 應用策略: {strategy.value}")
            
            if strategy == OptimizationStrategy.QUALITY_IMPROVEMENT:
                result = self._apply_quality_improvement(optimized_cases)
                actions_applied.extend(result["actions"])
                modified_cases.extend(result["modified"])
                removed_case_ids.extend(result["removed"])
                
            elif strategy == OptimizationStrategy.DIVERSITY_ENHANCEMENT:
                result = self._apply_diversity_enhancement(optimized_cases)
                actions_applied.extend(result["actions"])
                new_cases.extend(result["new"])
                modified_cases.extend(result["modified"])
                
            elif strategy == OptimizationStrategy.COVERAGE_EXPANSION:
                result = self._apply_coverage_expansion(optimized_cases)
                actions_applied.extend(result["actions"])
                new_cases.extend(result["new"])
                
            elif strategy == OptimizationStrategy.COMPLEXITY_BALANCING:
                result = self._apply_complexity_balancing(optimized_cases)
                actions_applied.extend(result["actions"])
                new_cases.extend(result["new"])
                
            elif strategy == OptimizationStrategy.INTENT_CLARIFICATION:
                result = self._apply_intent_clarification(optimized_cases)
                actions_applied.extend(result["actions"])
                modified_cases.extend(result["modified"])
        
        # 添加新案例
        optimized_cases.extend(new_cases)
        
        # 移除標記為刪除的案例
        optimized_cases = [case for case in optimized_cases if case.get("id") not in removed_case_ids]
        
        # 目標數量調整
        if target_count and len(optimized_cases) != target_count:
            optimized_cases = self._adjust_to_target_count(optimized_cases, target_count)
            actions_applied.append(f"調整到目標數量: {target_count}")
        
        # 最終驗證
        final_report = self.validator.validate_test_cases(optimized_cases)
        final_quality_score = final_report.metrics.overall_score
        
        # 計算改進指標
        improvements = {
            "quality_score": final_quality_score - initial_quality_score,
            "coverage_score": final_report.metrics.coverage_score - initial_report.metrics.coverage_score,
            "diversity_score": final_report.metrics.diversity_score - initial_report.metrics.diversity_score,
            "valid_cases": final_report.metrics.valid_cases - initial_report.metrics.valid_cases
        }
        
        optimization_time = time.time() - start_time
        
        result = OptimizationResult(
            original_count=original_count,
            optimized_count=len(optimized_cases),
            actions_applied=actions_applied,
            improvements=improvements,
            new_test_cases=new_cases,
            modified_test_cases=modified_cases,
            removed_test_cases=removed_case_ids,
            optimization_time=optimization_time,
            quality_score_improvement=improvements["quality_score"]
        )
        
        print(f"   ✅ 優化完成，耗時 {optimization_time:.2f} 秒")
        print(f"   📊 質量分數提升: {improvements['quality_score']:.3f}")
        
        return result, optimized_cases
    
    def _apply_quality_improvement(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List]:
        """應用質量改進"""
        actions = []
        modified = []
        removed = []
        
        for case in test_cases[:]:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            
            # 移除空白或無效案例
            if not query.strip() or len(query) < 3:
                removed.append(case_id)
                actions.append(f"移除無效案例: {case_id}")
                continue
            
            # 擴展過短查詢
            if len(query) < 10:
                enhanced_query = self._enhance_short_query(query, case)
                if enhanced_query != query:
                    case["query"] = enhanced_query
                    modified.append(case_id)
                    actions.append(f"擴展短查詢: {case_id}")
            
            # 簡化過長查詢
            elif len(query) > 200:
                simplified_query = self._simplify_long_query(query)
                if simplified_query != query:
                    case["query"] = simplified_query
                    modified.append(case_id)
                    actions.append(f"簡化長查詢: {case_id}")
            
            # 清理重複字符
            cleaned_query = re.sub(r"(.)\1{3,}", r"\1\1", query)
            if cleaned_query != query:
                case["query"] = cleaned_query
                modified.append(case_id)
                actions.append(f"清理重複字符: {case_id}")
        
        return {"actions": actions, "modified": modified, "removed": removed}
    
    def _apply_diversity_enhancement(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List]:
        """應用多樣性增強"""
        actions = []
        new_cases = []
        modified = []
        
        # 分析當前分佈
        category_counts = Counter(case.get("category", "") for case in test_cases)
        total_cases = len(test_cases)
        
        # 檢查類別不平衡
        target_categories = ["basic_job_search", "advanced_job_search", "salary_query", 
                           "location_query", "career_advice", "edge_case", "inappropriate_query"]
        
        for category in target_categories:
            current_count = category_counts.get(category, 0)
            target_count = max(1, total_cases // len(target_categories))
            
            if current_count < target_count:
                needed = target_count - current_count
                for _ in range(needed):
                    new_case = self._generate_case_for_category(category)
                    if new_case:
                        new_cases.append(new_case)
                        actions.append(f"添加 {category} 類別案例")
        
        # 處理重複查詢
        query_counts = Counter(case.get("query", "") for case in test_cases)
        duplicate_queries = [query for query, count in query_counts.items() if count > 1]
        
        for query in duplicate_queries:
            matching_cases = [case for case in test_cases if case.get("query") == query]
            for i, case in enumerate(matching_cases[1:], 1):  # 保留第一個，修改其他
                case_id = case.get("id", "unknown")
                varied_query = self._create_query_variation(query, case)
                if varied_query != query:
                    case["query"] = varied_query
                    modified.append(case_id)
                    actions.append(f"修改重複查詢: {case_id}")
        
        return {"actions": actions, "new": new_cases, "modified": modified}
    
    def _apply_coverage_expansion(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List]:
        """應用覆蓋率擴展"""
        actions = []
        new_cases = []
        
        # 檢查邊界案例覆蓋
        edge_case_count = sum(1 for case in test_cases if case.get("category") == "edge_case")
        if edge_case_count < len(test_cases) * 0.1:  # 少於10%
            needed_edge_cases = max(1, int(len(test_cases) * 0.1) - edge_case_count)
            for _ in range(needed_edge_cases):
                edge_case = self._generate_edge_case()
                if edge_case:
                    new_cases.append(edge_case)
                    actions.append("添加邊界案例")
        
        # 檢查多語言覆蓋
        languages = set(case.get("language", "zh-TW") for case in test_cases)
        target_languages = ["zh-TW", "en", "ja", "ko"]
        
        for lang in target_languages:
            if lang not in languages:
                lang_case = self._generate_multilingual_case(lang)
                if lang_case:
                    new_cases.append(lang_case)
                    actions.append(f"添加 {lang} 語言案例")
        
        return {"actions": actions, "new": new_cases}
    
    def _apply_complexity_balancing(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List]:
        """應用複雜度平衡"""
        actions = []
        new_cases = []
        
        # 分析複雜度分佈
        complexity_counts = Counter(case.get("complexity", "medium") for case in test_cases)
        total_cases = len(test_cases)
        
        target_complexities = ["simple", "medium", "complex", "extreme"]
        target_ratios = {"simple": 0.3, "medium": 0.4, "complex": 0.2, "extreme": 0.1}
        
        for complexity in target_complexities:
            current_count = complexity_counts.get(complexity, 0)
            target_count = int(total_cases * target_ratios[complexity])
            
            if current_count < target_count:
                needed = target_count - current_count
                for _ in range(needed):
                    complex_case = self._generate_case_with_complexity(complexity)
                    if complex_case:
                        new_cases.append(complex_case)
                        actions.append(f"添加 {complexity} 複雜度案例")
        
        return {"actions": actions, "new": new_cases}
    
    def _apply_intent_clarification(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List]:
        """應用意圖澄清"""
        actions = []
        modified = []
        
        intent_keywords = {
            "job_search": ["工作", "職缺", "job", "position", "仕事", "일자리"],
            "salary_query": ["薪資", "薪水", "salary", "wage", "給料", "급여"],
            "career_advice": ["轉職", "職涯", "career", "advice", "転職", "전직"],
            "location_query": ["地點", "位置", "location", "place", "場所", "위치"]
        }
        
        for case in test_cases:
            case_id = case.get("id", "unknown")
            query = case.get("query", "")
            expected_intent = case.get("expected_intent", "")
            
            if expected_intent in intent_keywords:
                keywords = intent_keywords[expected_intent]
                has_keyword = any(keyword.lower() in query.lower() for keyword in keywords)
                
                if not has_keyword:
                    # 添加相關關鍵詞
                    enhanced_query = self._add_intent_keywords(query, expected_intent)
                    if enhanced_query != query:
                        case["query"] = enhanced_query
                        modified.append(case_id)
                        actions.append(f"澄清意圖: {case_id}")
        
        return {"actions": actions, "modified": modified}
    
    def _enhance_short_query(self, query: str, case: Dict[str, Any]) -> str:
        """增強短查詢"""
        category = case.get("category", "")
        intent = case.get("expected_intent", "")
        
        enhancements = {
            "job_search": ["的工作機會", "相關職位", "工作"],
            "salary_query": ["的薪資範圍", "薪水多少", "待遇如何"],
            "career_advice": ["職涯建議", "發展方向", "轉職建議"]
        }
        
        if intent in enhancements:
            enhancement = random.choice(enhancements[intent])
            return f"{query}{enhancement}"
        
        return f"{query}相關信息"
    
    def _simplify_long_query(self, query: str) -> str:
        """簡化長查詢"""
        # 移除重複詞語
        words = query.split()
        unique_words = []
        seen = set()
        
        for word in words:
            if word.lower() not in seen:
                unique_words.append(word)
                seen.add(word.lower())
        
        simplified = " ".join(unique_words)
        
        # 如果還是太長，截取前150個字符
        if len(simplified) > 150:
            simplified = simplified[:147] + "..."
        
        return simplified
    
    def _generate_case_for_category(self, category: str) -> Optional[Dict[str, Any]]:
        """為特定類別生成測試案例"""
        templates = self.templates.get(category, [])
        if not templates:
            return None
        
        template = random.choice(templates)
        
        # 替換模板變量
        query = self._fill_template(template)
        
        case_id = f"opt_{category}_{int(time.time() * 1000) % 10000}"
        
        intent_mapping = {
            "basic_job_search": "job_search",
            "advanced_job_search": "job_search",
            "salary_query": "salary_query",
            "career_advice": "career_advice",
            "edge_case": "job_search",
            "inappropriate_query": "inappropriate_query"
        }
        
        return {
            "id": case_id,
            "query": query,
            "expected_intent": intent_mapping.get(category, "job_search"),
            "category": category,
            "complexity": "medium",
            "language": self._detect_query_language(query),
            "expected_confidence_range": [0.7, 0.9],
            "expected_entities": {},
            "metadata": {
                "generated_by": "optimizer",
                "generation_time": datetime.now().isoformat()
            }
        }
    
    def _create_query_variation(self, original_query: str, case: Dict[str, Any]) -> str:
        """創建查詢變體"""
        variations = [
            f"請問{original_query}",
            f"我想了解{original_query}",
            f"能否幫我{original_query}",
            f"關於{original_query}的問題",
            f"{original_query}的相關信息"
        ]
        
        # 根據語言選擇適當的變體
        language = case.get("language", "zh-TW")
        if language == "en":
            variations = [
                f"Can you help me with {original_query}",
                f"I'm looking for {original_query}",
                f"Please find {original_query}",
                f"Information about {original_query}",
                f"Help me understand {original_query}"
            ]
        
        return random.choice(variations)
    
    def _generate_edge_case(self) -> Dict[str, Any]:
        """生成邊界案例"""
        edge_cases = [
            "我想找工作但不知道自己適合什麼",
            "沒有工作經驗可以找到工作嗎",
            "50歲還能轉職嗎",
            "只想要遠端工作",
            "part-time job for students",
            "work from home opportunities",
            "jobs with no experience required",
            "career change at 40"
        ]
        
        query = random.choice(edge_cases)
        case_id = f"edge_{int(time.time() * 1000) % 10000}"
        
        return {
            "id": case_id,
            "query": query,
            "expected_intent": "job_search",
            "category": "edge_case",
            "complexity": "complex",
            "language": self._detect_query_language(query),
            "expected_confidence_range": [0.5, 0.8],
            "expected_entities": {},
            "metadata": {
                "generated_by": "optimizer",
                "generation_time": datetime.now().isoformat()
            }
        }
    
    def _generate_multilingual_case(self, language: str) -> Dict[str, Any]:
        """生成多語言案例"""
        queries = {
            "zh-TW": "我想在台北找軟體工程師的工作",
            "en": "Looking for software engineer jobs in New York",
            "ja": "東京でソフトウェアエンジニアの仕事を探しています",
            "ko": "서울에서 소프트웨어 엔지니어 일자리를 찾고 있습니다"
        }
        
        query = queries.get(language, queries["zh-TW"])
        case_id = f"lang_{language}_{int(time.time() * 1000) % 10000}"
        
        return {
            "id": case_id,
            "query": query,
            "expected_intent": "job_search",
            "category": "basic_job_search",
            "complexity": "medium",
            "language": language,
            "expected_confidence_range": [0.7, 0.9],
            "expected_entities": {},
            "metadata": {
                "generated_by": "optimizer",
                "generation_time": datetime.now().isoformat()
            }
        }
    
    def _generate_case_with_complexity(self, complexity: str) -> Dict[str, Any]:
        """生成指定複雜度的案例"""
        complexity_queries = {
            "simple": [
                "找工作",
                "job search",
                "仕事探し",
                "일자리 찾기"
            ],
            "medium": [
                "我想找台北的軟體工程師工作",
                "Looking for software engineer jobs in San Francisco",
                "東京でプログラマーの仕事を探しています",
                "서울에서 개발자 일자리를 찾고 있습니다"
            ],
            "complex": [
                "我是資深前端工程師，想轉職到大型科技公司做全端開發，希望薪資在150萬以上",
                "Senior frontend developer looking to transition to full-stack role at FAANG companies with 150k+ salary",
                "シニアフロントエンドエンジニアとして、大手テック企業でフルスタック開発に転職したい",
                "시니어 프론트엔드 개발자로서 대기업에서 풀스택 개발자로 전직하고 싶습니다"
            ],
            "extreme": [
                "我是45歲的傳統製造業經理，沒有程式背景，想轉職到AI/ML領域，但只考慮遠端工作，薪資不能低於現在的200萬，而且希望在6個月內完成轉職",
                "45-year-old manufacturing manager with no coding background wanting to transition to AI/ML field, remote only, salary must be 200k+, timeline 6 months",
                "45歳の製造業マネージャーで、プログラミング経験なし、AI/ML分野に転職したい、リモートワークのみ、年収2000万円以上、6ヶ月以内",
                "45세 제조업 매니저로 코딩 경험 없이 AI/ML 분야로 전직하고 싶은데, 재택근무만 가능하고 연봉 2억 이상, 6개월 내 전직 희망"
            ]
        }
        
        queries = complexity_queries.get(complexity, complexity_queries["medium"])
        query = random.choice(queries)
        case_id = f"comp_{complexity}_{int(time.time() * 1000) % 10000}"
        
        confidence_ranges = {
            "simple": [0.8, 0.95],
            "medium": [0.7, 0.9],
            "complex": [0.6, 0.8],
            "extreme": [0.4, 0.7]
        }
        
        return {
            "id": case_id,
            "query": query,
            "expected_intent": "job_search",
            "category": "basic_job_search",
            "complexity": complexity,
            "language": self._detect_query_language(query),
            "expected_confidence_range": confidence_ranges[complexity],
            "expected_entities": {},
            "metadata": {
                "generated_by": "optimizer",
                "generation_time": datetime.now().isoformat()
            }
        }
    
    def _add_intent_keywords(self, query: str, intent: str) -> str:
        """添加意圖關鍵詞"""
        keywords = {
            "job_search": ["工作", "職位", "job", "position"],
            "salary_query": ["薪資", "薪水", "salary", "wage"],
            "career_advice": ["職涯", "建議", "career", "advice"],
            "location_query": ["地點", "位置", "location", "place"]
        }
        
        if intent in keywords:
            keyword = random.choice(keywords[intent])
            if keyword not in query:
                return f"{query} {keyword}"
        
        return query
    
    def _fill_template(self, template: str) -> str:
        """填充模板"""
        patterns = self.enhancement_patterns
        
        # 替換模板變量
        for key, values in patterns.items():
            placeholder = f"{{{key[:-1]}}}"
            if placeholder in template:
                template = template.replace(placeholder, random.choice(values))
        
        return template
    
    def _detect_query_language(self, query: str) -> str:
        """檢測查詢語言"""
        if re.search(r"[\u4e00-\u9fff]", query):
            return "zh-TW"
        elif re.search(r"[\u3040-\u309f\u30a0-\u30ff]", query):
            return "ja"
        elif re.search(r"[\uac00-\ud7af]", query):
            return "ko"
        elif re.search(r"[a-zA-Z]", query):
            return "en"
        else:
            return "unknown"
    
    def _adjust_to_target_count(self, test_cases: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """調整到目標數量"""
        current_count = len(test_cases)
        
        if current_count > target_count:
            # 隨機移除多餘的案例，但保持類別平衡
            categories = list(set(case.get("category", "") for case in test_cases))
            cases_by_category = defaultdict(list)
            
            for case in test_cases:
                category = case.get("category", "")
                cases_by_category[category].append(case)
            
            # 按比例保留
            result = []
            for category in categories:
                category_cases = cases_by_category[category]
                keep_count = max(1, int(len(category_cases) * target_count / current_count))
                result.extend(random.sample(category_cases, min(keep_count, len(category_cases))))
            
            # 如果還是太多，隨機移除
            if len(result) > target_count:
                result = random.sample(result, target_count)
            
            return result
        
        elif current_count < target_count:
            # 生成額外案例
            needed = target_count - current_count
            categories = ["basic_job_search", "salary_query", "career_advice", "edge_case"]
            
            for _ in range(needed):
                category = random.choice(categories)
                new_case = self._generate_case_for_category(category)
                if new_case:
                    test_cases.append(new_case)
        
        return test_cases
    
    def export_optimized_cases(self, test_cases: List[Dict[str, Any]], 
                             result: OptimizationResult, 
                             output_file: str = None) -> str:
        """導出優化後的測試案例"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"optimized_test_cases_{timestamp}.json"
        
        print(f"💾 導出優化後的測試案例到 {output_file}...")
        
        export_data = {
            "optimization_info": {
                "optimization_time": datetime.now().isoformat(),
                "original_count": result.original_count,
                "optimized_count": result.optimized_count,
                "actions_applied": result.actions_applied,
                "improvements": result.improvements,
                "optimization_duration": result.optimization_time
            },
            "test_cases": test_cases,
            "statistics": {
                "category_distribution": dict(Counter(case.get("category", "") for case in test_cases)),
                "complexity_distribution": dict(Counter(case.get("complexity", "") for case in test_cases)),
                "language_distribution": dict(Counter(case.get("language", "") for case in test_cases)),
                "intent_distribution": dict(Counter(case.get("expected_intent", "") for case in test_cases))
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 優化後的測試案例已導出")
        return output_file
    
    def print_optimization_summary(self, result: OptimizationResult) -> None:
        """打印優化摘要"""
        print("\n" + "=" * 60)
        print("🔧 LLM測試案例優化報告")
        print("=" * 60)
        
        print(f"\n📊 優化統計:")
        print(f"   原始案例數: {result.original_count}")
        print(f"   優化後案例數: {result.optimized_count}")
        print(f"   優化時間: {result.optimization_time:.2f} 秒")
        
        print(f"\n🎯 執行的優化動作:")
        for i, action in enumerate(result.actions_applied, 1):
            print(f"   {i}. {action}")
        
        print(f"\n📈 改進指標:")
        for metric, improvement in result.improvements.items():
            improvement_emoji = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
            print(f"   {improvement_emoji} {metric}: {improvement:+.3f}")
        
        print(f"\n📋 變更摘要:")
        print(f"   新增案例: {len(result.new_test_cases)}")
        print(f"   修改案例: {len(result.modified_test_cases)}")
        print(f"   移除案例: {len(result.removed_test_cases)}")
        
        if result.quality_score_improvement > 0:
            print(f"\n✅ 優化成功！質量分數提升 {result.quality_score_improvement:.3f}")
        else:
            print(f"\n⚠️ 優化效果有限，質量分數變化 {result.quality_score_improvement:.3f}")
        
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
    """主函數 - 測試案例優化器入口點"""
    print("🔧 LLM測試案例優化器")
    print("=" * 60)
    
    optimizer = LLMTestCaseOptimizer()
    
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
        
        # 選擇優化策略
        print("\n🎯 選擇優化策略:")
        print("1. 全面優化 (所有策略)")
        print("2. 質量改進")
        print("3. 多樣性增強")
        print("4. 覆蓋率擴展")
        print("5. 複雜度平衡")
        print("6. 自定義")
        
        choice = input("請選擇 (1-6): ").strip()
        
        strategies = []
        if choice == "1":
            strategies = list(OptimizationStrategy)
        elif choice == "2":
            strategies = [OptimizationStrategy.QUALITY_IMPROVEMENT]
        elif choice == "3":
            strategies = [OptimizationStrategy.DIVERSITY_ENHANCEMENT]
        elif choice == "4":
            strategies = [OptimizationStrategy.COVERAGE_EXPANSION]
        elif choice == "5":
            strategies = [OptimizationStrategy.COMPLEXITY_BALANCING]
        elif choice == "6":
            print("\n可用策略:")
            for i, strategy in enumerate(OptimizationStrategy, 1):
                print(f"{i}. {strategy.value}")
            
            selected = input("請輸入策略編號 (用逗號分隔): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in selected.split(",")]
                strategies = [list(OptimizationStrategy)[i] for i in indices if 0 <= i < len(OptimizationStrategy)]
            except:
                print("無效的選擇，使用全面優化")
                strategies = list(OptimizationStrategy)
        else:
            strategies = list(OptimizationStrategy)
        
        # 目標數量
        target_count = None
        target_input = input(f"\n目標案例數量 (當前: {len(test_cases)}, 按Enter保持不變): ").strip()
        if target_input.isdigit():
            target_count = int(target_input)
        
        # 執行優化
        print(f"\n🔧 開始優化，使用策略: {[s.value for s in strategies]}")
        result, optimized_cases = optimizer.optimize_test_cases(test_cases, strategies, target_count)
        
        # 顯示結果
        optimizer.print_optimization_summary(result)
        
        # 導出結果
        export_result = input("\n是否導出優化後的測試案例？ (y/n): ").strip().lower()
        if export_result == 'y':
            output_file = optimizer.export_optimized_cases(optimized_cases, result)
            print(f"   📄 優化後文件: {output_file}")
        
        print("\n🎉 測試案例優化完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 優化過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 優化過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()