#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能決策引擎
根據意圖分析結果決定後續處理流程和模組選擇

Author: jobseeker Team
Date: 2025-01-27
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 避免循環導入，使用TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llm_intent_analyzer import LLMIntentResult, JobSearchIntent, IntentType
    from .model import Site, Country
else:
    # 運行時導入
    try:
        from .llm_intent_analyzer import LLMIntentResult, JobSearchIntent, IntentType
        from .model import Site, Country
    except ImportError:
        # 如果導入失敗，定義基本類型
        LLMIntentResult = Any
        JobSearchIntent = Any
        IntentType = Any
        Site = Any
        Country = Any

# 設置日誌
logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """處理策略枚舉"""
    STANDARD_SEARCH = "standard_search"  # 標準搜索
    ENHANCED_SEARCH = "enhanced_search"  # 增強搜索
    TARGETED_SEARCH = "targeted_search"  # 定向搜索
    BROAD_SEARCH = "broad_search"  # 廣泛搜索
    FALLBACK_SEARCH = "fallback_search"  # 備用搜索
    REJECT_QUERY = "reject_query"  # 拒絕查詢


class PlatformSelectionMode(Enum):
    """平台選擇模式"""
    AUTO_INTELLIGENT = "auto_intelligent"  # 智能自動選擇
    REGION_BASED = "region_based"  # 基於地區選擇
    SKILL_BASED = "skill_based"  # 基於技能選擇
    INDUSTRY_BASED = "industry_based"  # 基於行業選擇
    COMPREHENSIVE = "comprehensive"  # 全面搜索
    FALLBACK = "fallback"  # 備用選擇


@dataclass
class DecisionResult:
    """決策結果"""
    strategy: ProcessingStrategy
    platform_selection_mode: PlatformSelectionMode
    recommended_platforms: List[str]
    search_parameters: Dict[str, Any]
    priority_score: float  # 優先級分數 (0.0 - 1.0)
    confidence: float  # 決策置信度 (0.0 - 1.0)
    reasoning: str  # 決策推理過程
    fallback_options: List[Dict[str, Any]]  # 備用選項
    estimated_results: int  # 預估結果數量
    processing_hints: Dict[str, Any]  # 處理提示


class IntelligentDecisionEngine:
    """智能決策引擎"""
    
    def __init__(self):
        """
        初始化智能決策引擎
        """
        self.logger = logging.getLogger(__name__)
        self.decision_history = []
        self.platform_performance = {}  # 平台性能統計
        self.region_platform_mapping = self._init_region_platform_mapping()
        self.skill_platform_mapping = self._init_skill_platform_mapping()
        self.industry_platform_mapping = self._init_industry_platform_mapping()
        
    def _init_region_platform_mapping(self) -> Dict[str, List[str]]:
        """初始化地區-平台映射"""
        return {
            'australia': ['seek', 'indeed'],
            'taiwan': ['104', '1111', 'indeed'],
            'hong_kong': ['indeed', 'linkedin'],
            'singapore': ['indeed', 'linkedin'],
            'usa': ['indeed', 'linkedin', 'ziprecruiter'],
            'uk': ['indeed', 'linkedin'],
            'global': ['indeed', 'linkedin'],
            'asia': ['indeed', 'linkedin', 'naukri'],
            'middle_east': ['bayt', 'indeed'],
            'bangladesh': ['bdjobs', 'indeed']
        }
    
    def _init_skill_platform_mapping(self) -> Dict[str, List[str]]:
        """初始化技能-平台映射"""
        return {
            'tech': ['linkedin', 'indeed', 'seek'],
            'finance': ['linkedin', 'indeed'],
            'healthcare': ['indeed', 'seek'],
            'education': ['indeed', 'seek'],
            'marketing': ['linkedin', 'indeed'],
            'sales': ['indeed', 'linkedin'],
            'engineering': ['linkedin', 'indeed', 'seek'],
            'design': ['linkedin', 'indeed'],
            'management': ['linkedin', 'indeed'],
            'customer_service': ['indeed', 'seek']
        }
    
    def _init_industry_platform_mapping(self) -> Dict[str, List[str]]:
        """初始化行業-平台映射"""
        return {
            'technology': ['linkedin', 'indeed', 'seek'],
            'finance': ['linkedin', 'indeed'],
            'healthcare': ['indeed', 'seek'],
            'education': ['indeed', 'seek'],
            'retail': ['indeed', 'seek'],
            'manufacturing': ['indeed', 'seek'],
            'consulting': ['linkedin', 'indeed'],
            'startup': ['linkedin', 'indeed'],
            'government': ['indeed', 'seek'],
            'nonprofit': ['indeed', 'seek']
        }
    
    def make_decision(self, intent_result: Any, 
                     user_context: Optional[Dict[str, Any]] = None) -> DecisionResult:
        """
        根據意圖分析結果做出智能決策
        
        Args:
            intent_result: LLM意圖分析結果
            user_context: 用戶上下文信息
            
        Returns:
            DecisionResult: 決策結果
        """
        start_time = datetime.now()
        
        try:
            # 1. 檢查是否為求職相關查詢
            if not intent_result.is_job_related:
                return self._create_rejection_decision(intent_result)
            
            # 2. 分析查詢複雜度和特異性
            complexity_score = self._analyze_query_complexity(intent_result)
            specificity_score = self._analyze_query_specificity(intent_result)
            
            # 3. 確定處理策略
            strategy = self._determine_processing_strategy(
                intent_result, complexity_score, specificity_score
            )
            
            # 4. 選擇平台選擇模式
            platform_mode = self._determine_platform_selection_mode(
                intent_result, strategy
            )
            
            # 5. 推薦具體平台
            recommended_platforms = self._recommend_platforms(
                intent_result, platform_mode, user_context
            )
            
            # 6. 生成搜索參數
            search_parameters = self._generate_search_parameters(
                intent_result, strategy
            )
            
            # 7. 計算優先級和置信度
            priority_score = self._calculate_priority_score(
                intent_result, complexity_score, specificity_score
            )
            confidence = self._calculate_decision_confidence(
                intent_result, strategy, recommended_platforms
            )
            
            # 8. 生成決策推理
            reasoning = self._generate_reasoning(
                intent_result, strategy, platform_mode, recommended_platforms
            )
            
            # 9. 準備備用選項
            fallback_options = self._prepare_fallback_options(
                intent_result, recommended_platforms
            )
            
            # 10. 預估結果數量
            estimated_results = self._estimate_result_count(
                intent_result, recommended_platforms
            )
            
            # 11. 生成處理提示
            processing_hints = self._generate_processing_hints(
                intent_result, strategy, platform_mode
            )
            
            decision = DecisionResult(
                strategy=strategy,
                platform_selection_mode=platform_mode,
                recommended_platforms=recommended_platforms,
                search_parameters=search_parameters,
                priority_score=priority_score,
                confidence=confidence,
                reasoning=reasoning,
                fallback_options=fallback_options,
                estimated_results=estimated_results,
                processing_hints=processing_hints
            )
            
            # 記錄決策歷史
            self._record_decision(decision, intent_result, start_time)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"決策過程中發生錯誤: {e}")
            return self._create_fallback_decision(intent_result)
    
    def _create_rejection_decision(self, intent_result: Any) -> DecisionResult:
        """創建拒絕決策"""
        return DecisionResult(
            strategy=ProcessingStrategy.REJECT_QUERY,
            platform_selection_mode=PlatformSelectionMode.FALLBACK,
            recommended_platforms=[],
            search_parameters={},
            priority_score=0.0,
            confidence=1.0,
            reasoning="查詢不是求職相關，拒絕處理",
            fallback_options=[],
            estimated_results=0,
            processing_hints={'rejection_message': intent_result.rejection_message}
        )
    
    def _analyze_query_complexity(self, intent_result: Any) -> float:
        """分析查詢複雜度"""
        if not intent_result.structured_intent:
            return 0.3  # 低複雜度
        
        intent = intent_result.structured_intent
        complexity_factors = 0
        
        # 檢查各種複雜度因素
        if intent.job_titles and len(intent.job_titles) > 1:
            complexity_factors += 0.2
        if intent.skills and len(intent.skills) > 2:
            complexity_factors += 0.2
        if intent.locations and len(intent.locations) > 1:
            complexity_factors += 0.15
        if intent.salary_range:
            complexity_factors += 0.1
        if intent.work_mode:
            complexity_factors += 0.1
        if intent.company_size:
            complexity_factors += 0.1
        if intent.industry:
            complexity_factors += 0.1
        if intent.soft_preferences and len(intent.soft_preferences) > 0:
            complexity_factors += 0.15
        
        return min(complexity_factors, 1.0)
    
    def _analyze_query_specificity(self, intent_result: Any) -> float:
        """分析查詢特異性"""
        if not intent_result.structured_intent:
            return 0.2  # 低特異性
        
        intent = intent_result.structured_intent
        specificity_score = 0
        
        # 職位標題特異性
        if intent.job_titles:
            if any(len(title.split()) > 2 for title in intent.job_titles):
                specificity_score += 0.3  # 具體職位名稱
            else:
                specificity_score += 0.15  # 一般職位名稱
        
        # 技能特異性
        if intent.skills:
            if len(intent.skills) >= 3:
                specificity_score += 0.25  # 多個具體技能
            else:
                specificity_score += 0.1
        
        # 地點特異性
        if intent.locations:
            specificity_score += 0.2
        
        # 其他特異性因素
        if intent.salary_range:
            specificity_score += 0.15
        if intent.company_size:
            specificity_score += 0.1
        if intent.industry:
            specificity_score += 0.1
        
        return min(specificity_score, 1.0)
    
    def _determine_processing_strategy(self, intent_result: Any, 
                                     complexity_score: float, 
                                     specificity_score: float) -> ProcessingStrategy:
        """確定處理策略"""
        # 高複雜度 + 高特異性 = 定向搜索
        if complexity_score > 0.7 and specificity_score > 0.7:
            return ProcessingStrategy.TARGETED_SEARCH
        
        # 高複雜度 + 中等特異性 = 增強搜索
        elif complexity_score > 0.6 and specificity_score > 0.4:
            return ProcessingStrategy.ENHANCED_SEARCH
        
        # 低複雜度 + 低特異性 = 廣泛搜索
        elif complexity_score < 0.4 and specificity_score < 0.4:
            return ProcessingStrategy.BROAD_SEARCH
        
        # 其他情況 = 標準搜索
        else:
            return ProcessingStrategy.STANDARD_SEARCH
    
    def _determine_platform_selection_mode(self, intent_result: Any, 
                                         strategy: ProcessingStrategy) -> PlatformSelectionMode:
        """確定平台選擇模式"""
        if not intent_result.structured_intent:
            return PlatformSelectionMode.AUTO_INTELLIGENT
        
        intent = intent_result.structured_intent
        
        # 基於地區選擇
        if intent.locations:
            return PlatformSelectionMode.REGION_BASED
        
        # 基於行業選擇
        elif intent.industry:
            return PlatformSelectionMode.INDUSTRY_BASED
        
        # 基於技能選擇
        elif intent.skills and len(intent.skills) >= 2:
            return PlatformSelectionMode.SKILL_BASED
        
        # 定向搜索使用全面模式
        elif strategy == ProcessingStrategy.TARGETED_SEARCH:
            return PlatformSelectionMode.COMPREHENSIVE
        
        # 默認智能選擇
        else:
            return PlatformSelectionMode.AUTO_INTELLIGENT
    
    def _recommend_platforms(self, intent_result: Any, 
                           platform_mode: PlatformSelectionMode,
                           user_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """推薦具體平台"""
        platforms = set()
        
        if platform_mode == PlatformSelectionMode.REGION_BASED:
            platforms.update(self._get_platforms_by_region(intent_result))
        
        elif platform_mode == PlatformSelectionMode.SKILL_BASED:
            platforms.update(self._get_platforms_by_skills(intent_result))
        
        elif platform_mode == PlatformSelectionMode.INDUSTRY_BASED:
            platforms.update(self._get_platforms_by_industry(intent_result))
        
        elif platform_mode == PlatformSelectionMode.COMPREHENSIVE:
            platforms.update(['indeed', 'linkedin', 'seek', '104'])
        
        else:  # AUTO_INTELLIGENT
            platforms.update(self._get_intelligent_platform_selection(intent_result))
        
        # 確保至少有一個平台
        if not platforms:
            platforms = {'indeed', 'linkedin'}
        
        return list(platforms)
    
    def _get_platforms_by_region(self, intent_result: Any) -> List[str]:
        """根據地區獲取平台"""
        if not intent_result.structured_intent or not intent_result.structured_intent.locations:
            return ['indeed', 'linkedin']
        
        platforms = set()
        for location in intent_result.structured_intent.locations:
            location_lower = location.lower()
            
            # 檢查地區映射
            for region, region_platforms in self.region_platform_mapping.items():
                if region in location_lower or any(keyword in location_lower for keyword in [region]):
                    platforms.update(region_platforms)
        
        return list(platforms) if platforms else ['indeed', 'linkedin']
    
    def _get_platforms_by_skills(self, intent_result: Any) -> List[str]:
        """根據技能獲取平台"""
        if not intent_result.structured_intent or not intent_result.structured_intent.skills:
            return ['indeed', 'linkedin']
        
        platforms = set()
        for skill in intent_result.structured_intent.skills:
            skill_lower = skill.lower()
            
            # 檢查技能映射
            for skill_category, skill_platforms in self.skill_platform_mapping.items():
                if skill_category in skill_lower or any(keyword in skill_lower for keyword in [skill_category]):
                    platforms.update(skill_platforms)
        
        return list(platforms) if platforms else ['indeed', 'linkedin']
    
    def _get_platforms_by_industry(self, intent_result: Any) -> List[str]:
        """根據行業獲取平台"""
        if not intent_result.structured_intent or not intent_result.structured_intent.industry:
            return ['indeed', 'linkedin']
        
        industry = intent_result.structured_intent.industry.lower()
        
        # 檢查行業映射
        for industry_category, industry_platforms in self.industry_platform_mapping.items():
            if industry_category in industry or any(keyword in industry for keyword in [industry_category]):
                return industry_platforms
        
        return ['indeed', 'linkedin']
    
    def _get_intelligent_platform_selection(self, intent_result: Any) -> List[str]:
        """智能平台選擇"""
        platforms = set(['indeed', 'linkedin'])  # 基礎平台
        
        if intent_result.structured_intent:
            intent = intent_result.structured_intent
            
            # 根據多個因素智能選擇
            if intent.locations:
                platforms.update(self._get_platforms_by_region(intent_result))
            
            if intent.skills:
                platforms.update(self._get_platforms_by_skills(intent_result))
            
            if intent.industry:
                platforms.update(self._get_platforms_by_industry(intent_result))
        
        return list(platforms)
    
    def _generate_search_parameters(self, intent_result: Any, 
                                  strategy: ProcessingStrategy) -> Dict[str, Any]:
        """生成搜索參數"""
        params = {
            'strategy': strategy.value,
            'max_results': self._determine_max_results(strategy),
            'timeout': self._determine_timeout(strategy),
            'retry_attempts': self._determine_retry_attempts(strategy)
        }
        
        if intent_result.structured_intent:
            intent = intent_result.structured_intent
            
            if intent.job_titles:
                params['job_titles'] = intent.job_titles
            if intent.skills:
                params['skills'] = intent.skills
            if intent.locations:
                params['locations'] = intent.locations
            if intent.salary_range:
                params['salary_range'] = intent.salary_range
            if intent.work_mode:
                params['work_mode'] = intent.work_mode
            if intent.company_size:
                params['company_size'] = intent.company_size
            if intent.industry:
                params['industry'] = intent.industry
            if intent.soft_preferences:
                params['soft_preferences'] = intent.soft_preferences
        
        return params
    
    def _determine_max_results(self, strategy: ProcessingStrategy) -> int:
        """確定最大結果數量"""
        strategy_limits = {
            ProcessingStrategy.TARGETED_SEARCH: 50,
            ProcessingStrategy.ENHANCED_SEARCH: 75,
            ProcessingStrategy.STANDARD_SEARCH: 25,
            ProcessingStrategy.BROAD_SEARCH: 100,
            ProcessingStrategy.FALLBACK_SEARCH: 20
        }
        return strategy_limits.get(strategy, 25)
    
    def _determine_timeout(self, strategy: ProcessingStrategy) -> int:
        """確定超時時間（秒）"""
        strategy_timeouts = {
            ProcessingStrategy.TARGETED_SEARCH: 60,
            ProcessingStrategy.ENHANCED_SEARCH: 45,
            ProcessingStrategy.STANDARD_SEARCH: 30,
            ProcessingStrategy.BROAD_SEARCH: 90,
            ProcessingStrategy.FALLBACK_SEARCH: 20
        }
        return strategy_timeouts.get(strategy, 30)
    
    def _determine_retry_attempts(self, strategy: ProcessingStrategy) -> int:
        """確定重試次數"""
        strategy_retries = {
            ProcessingStrategy.TARGETED_SEARCH: 3,
            ProcessingStrategy.ENHANCED_SEARCH: 2,
            ProcessingStrategy.STANDARD_SEARCH: 1,
            ProcessingStrategy.BROAD_SEARCH: 2,
            ProcessingStrategy.FALLBACK_SEARCH: 1
        }
        return strategy_retries.get(strategy, 1)
    
    def _calculate_priority_score(self, intent_result: Any, 
                                complexity_score: float, 
                                specificity_score: float) -> float:
        """計算優先級分數"""
        base_score = intent_result.confidence
        complexity_bonus = complexity_score * 0.2
        specificity_bonus = specificity_score * 0.3
        
        # 緊急程度加成
        urgency_bonus = 0.0
        if (intent_result.structured_intent and 
            intent_result.structured_intent.urgency and 
            'urgent' in intent_result.structured_intent.urgency.lower()):
            urgency_bonus = 0.2
        
        return min(base_score + complexity_bonus + specificity_bonus + urgency_bonus, 1.0)
    
    def _calculate_decision_confidence(self, intent_result: Any, 
                                     strategy: ProcessingStrategy, 
                                     platforms: List[str]) -> float:
        """計算決策置信度"""
        base_confidence = intent_result.confidence
        
        # 策略置信度調整
        strategy_confidence = {
            ProcessingStrategy.TARGETED_SEARCH: 0.9,
            ProcessingStrategy.ENHANCED_SEARCH: 0.8,
            ProcessingStrategy.STANDARD_SEARCH: 0.7,
            ProcessingStrategy.BROAD_SEARCH: 0.6,
            ProcessingStrategy.FALLBACK_SEARCH: 0.4
        }
        
        # 平台數量調整
        platform_confidence = min(len(platforms) * 0.1 + 0.5, 1.0)
        
        return min((base_confidence + strategy_confidence.get(strategy, 0.7) + platform_confidence) / 3, 1.0)
    
    def _generate_reasoning(self, intent_result: Any, 
                          strategy: ProcessingStrategy, 
                          platform_mode: PlatformSelectionMode, 
                          platforms: List[str]) -> str:
        """生成決策推理"""
        reasoning_parts = []
        
        # 意圖分析結果
        reasoning_parts.append(f"意圖分析置信度: {intent_result.confidence:.2f}")
        
        # 策略選擇原因
        strategy_reasons = {
            ProcessingStrategy.TARGETED_SEARCH: "查詢具有高複雜度和特異性，採用定向搜索策略",
            ProcessingStrategy.ENHANCED_SEARCH: "查詢複雜度較高，採用增強搜索策略",
            ProcessingStrategy.STANDARD_SEARCH: "查詢複雜度適中，採用標準搜索策略",
            ProcessingStrategy.BROAD_SEARCH: "查詢較為廣泛，採用廣泛搜索策略",
            ProcessingStrategy.FALLBACK_SEARCH: "採用備用搜索策略"
        }
        reasoning_parts.append(strategy_reasons.get(strategy, "採用標準策略"))
        
        # 平台選擇原因
        platform_reasons = {
            PlatformSelectionMode.REGION_BASED: "基於地區信息選擇平台",
            PlatformSelectionMode.SKILL_BASED: "基於技能要求選擇平台",
            PlatformSelectionMode.INDUSTRY_BASED: "基於行業信息選擇平台",
            PlatformSelectionMode.COMPREHENSIVE: "採用全面搜索模式",
            PlatformSelectionMode.AUTO_INTELLIGENT: "智能自動選擇平台"
        }
        reasoning_parts.append(platform_reasons.get(platform_mode, "智能選擇平台"))
        
        # 選擇的平台
        reasoning_parts.append(f"推薦平台: {', '.join(platforms)}")
        
        return "; ".join(reasoning_parts)
    
    def _prepare_fallback_options(self, intent_result: Any, 
                                primary_platforms: List[str]) -> List[Dict[str, Any]]:
        """準備備用選項"""
        fallback_options = []
        
        # 備用平台組合
        all_platforms = ['indeed', 'linkedin', 'seek', '104', 'ziprecruiter']
        backup_platforms = [p for p in all_platforms if p not in primary_platforms]
        
        if backup_platforms:
            fallback_options.append({
                'type': 'alternative_platforms',
                'platforms': backup_platforms[:3],
                'reason': '主要平台失敗時的備用選擇'
            })
        
        # 簡化搜索選項
        if intent_result.structured_intent and intent_result.structured_intent.job_titles:
            fallback_options.append({
                'type': 'simplified_search',
                'search_term': intent_result.structured_intent.job_titles[0],
                'reason': '使用簡化的搜索詞進行備用搜索'
            })
        
        return fallback_options
    
    def _estimate_result_count(self, intent_result: Any, 
                             platforms: List[str]) -> int:
        """預估結果數量"""
        base_estimate = len(platforms) * 10  # 每個平台預估10個結果
        
        # 根據查詢特異性調整
        if intent_result.structured_intent:
            intent = intent_result.structured_intent
            
            # 特異性越高，結果越少
            specificity_factors = 0
            if intent.job_titles:
                specificity_factors += len(intent.job_titles) * 0.1
            if intent.skills:
                specificity_factors += len(intent.skills) * 0.05
            if intent.locations:
                specificity_factors += len(intent.locations) * 0.1
            if intent.salary_range:
                specificity_factors += 0.2
            
            # 調整預估
            adjustment = max(0.3, 1.0 - specificity_factors)
            base_estimate = int(base_estimate * adjustment)
        
        return max(base_estimate, 5)  # 至少預估5個結果
    
    def _generate_processing_hints(self, intent_result: Any, 
                                 strategy: ProcessingStrategy, 
                                 platform_mode: PlatformSelectionMode) -> Dict[str, Any]:
        """生成處理提示"""
        hints = {
            'strategy': strategy.value,
            'platform_mode': platform_mode.value,
            'use_cache': strategy != ProcessingStrategy.TARGETED_SEARCH,
            'parallel_processing': len(intent_result.structured_intent.locations) > 1 if intent_result.structured_intent and intent_result.structured_intent.locations else False,
            'result_filtering': strategy in [ProcessingStrategy.TARGETED_SEARCH, ProcessingStrategy.ENHANCED_SEARCH],
            'quality_threshold': 0.8 if strategy == ProcessingStrategy.TARGETED_SEARCH else 0.6
        }
        
        # 特殊處理提示
        if intent_result.structured_intent:
            intent = intent_result.structured_intent
            
            if intent.soft_preferences:
                hints['apply_soft_filters'] = True
                hints['soft_preferences'] = intent.soft_preferences
            
            if intent.urgency and 'urgent' in intent.urgency.lower():
                hints['priority_processing'] = True
            
            if intent.salary_range:
                hints['salary_filtering'] = True
        
        return hints
    
    def _create_fallback_decision(self, intent_result: Any) -> DecisionResult:
        """創建備用決策"""
        return DecisionResult(
            strategy=ProcessingStrategy.FALLBACK_SEARCH,
            platform_selection_mode=PlatformSelectionMode.FALLBACK,
            recommended_platforms=['indeed', 'linkedin'],
            search_parameters={'max_results': 20, 'timeout': 20, 'retry_attempts': 1},
            priority_score=0.3,
            confidence=0.5,
            reasoning="決策過程中發生錯誤，使用備用決策",
            fallback_options=[],
            estimated_results=10,
            processing_hints={'use_cache': True, 'quality_threshold': 0.5}
        )
    
    def _record_decision(self, decision: DecisionResult, 
                        intent_result: Any, 
                        start_time: datetime):
        """記錄決策歷史"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        decision_record = {
            'timestamp': start_time,
            'processing_time': processing_time,
            'strategy': decision.strategy.value,
            'platforms': decision.recommended_platforms,
            'confidence': decision.confidence,
            'priority_score': decision.priority_score,
            'intent_confidence': intent_result.confidence,
            'estimated_results': decision.estimated_results
        }
        
        self.decision_history.append(decision_record)
        
        # 保持歷史記錄在合理範圍內
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """獲取決策統計信息"""
        if not self.decision_history:
            return {'total_decisions': 0}
        
        total_decisions = len(self.decision_history)
        avg_confidence = sum(d['confidence'] for d in self.decision_history) / total_decisions
        avg_processing_time = sum(d['processing_time'] for d in self.decision_history) / total_decisions
        
        strategy_counts = {}
        for decision in self.decision_history:
            strategy = decision['strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_decisions': total_decisions,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time,
            'strategy_distribution': strategy_counts,
            'recent_decisions': self.decision_history[-10:]
        }


# 創建全局決策引擎實例
intelligent_decision_engine = IntelligentDecisionEngine()


def make_intelligent_decision(intent_result: Any, 
                            user_context: Optional[Dict[str, Any]] = None) -> DecisionResult:
    """
    便捷函數：進行智能決策
    
    Args:
        intent_result: LLM意圖分析結果
        user_context: 用戶上下文信息
        
    Returns:
        DecisionResult: 決策結果
    """
    return intelligent_decision_engine.make_decision(intent_result, user_context)