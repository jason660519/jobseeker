#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM驅動的智能意圖分析器
使用大語言模型分析用戶查詢意圖，提取結構化信息，並進行智能決策

Author: jobseeker Team
Date: 2025-01-27
"""

import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime

# 導入現有的意圖分析器作為備選方案
from .intent_analyzer import IntentAnalyzer as BasicIntentAnalyzer, IntentType, IntentAnalysisResult
from .llm_client import create_llm_client, LLMResponse
from .llm_config import LLMConfig
from .intelligent_decision_engine import (
    IntelligentDecisionEngine, 
    DecisionResult, 
    ProcessingStrategy, 
    PlatformSelectionMode,
    make_intelligent_decision
)


class LLMProvider(Enum):
    """LLM提供商枚舉"""
    OPENAI_GPT35 = "openai_gpt35"
    OPENAI_GPT4 = "openai_gpt4"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    LOCAL_LLAMA = "local_llama"
    AZURE_OPENAI = "azure_openai"


@dataclass
class JobSearchIntent:
    """結構化的求職意圖"""
    job_titles: List[str]  # 職位名稱
    skills: List[str]  # 技能關鍵詞
    locations: List[str]  # 地點
    salary_range: Optional[str] = None  # 薪資範圍
    work_mode: Optional[str] = None  # 工作模式（遠程/線下/混合）
    company_size: Optional[str] = None  # 公司規模
    industry: Optional[str] = None  # 行業
    experience_level: Optional[str] = None  # 經驗要求
    soft_preferences: List[str] = None  # 軟性偏好（如：不加班、團隊氛圍好）
    urgency: Optional[str] = None  # 緊急程度
    
    def __post_init__(self):
        if self.soft_preferences is None:
            self.soft_preferences = []


@dataclass
class LLMIntentResult:
    """LLM意圖分析結果"""
    intent_type: IntentType
    confidence: float  # 置信度 (0.0 - 1.0)
    is_job_related: bool
    structured_intent: Optional[JobSearchIntent] = None  # 結構化意圖
    search_query_suggestions: List[str] = None  # 搜索建議
    response_message: Optional[str] = None  # 回應訊息
    rejection_message: Optional[str] = None  # 拒絕訊息
    llm_reasoning: Optional[str] = None  # LLM推理過程
    fallback_used: bool = False  # 是否使用了備選方案
    llm_used: bool = True  # 是否使用了LLM
    processing_time: Optional[float] = None  # 處理時間
    
    def __post_init__(self):
        if self.search_query_suggestions is None:
            self.search_query_suggestions = []


class LLMIntentAnalyzer:
    """LLM驅動的智能意圖分析器，具備決策功能"""
    
    def __init__(self, 
                 provider: LLMProvider = LLMProvider.OPENAI_GPT35,
                 api_key: Optional[str] = None,
                 fallback_to_basic: bool = True,
                 cache_enabled: bool = True):
        """
        初始化LLM智能意圖分析器
        
        Args:
            provider: LLM提供商
            api_key: API密鑰
            fallback_to_basic: 是否在LLM失敗時回退到基礎分析器
            cache_enabled: 是否啟用緩存
        """
        self.provider = provider
        self.api_key = api_key
        self.fallback_to_basic = fallback_to_basic
        self.cache_enabled = cache_enabled
        
        # 初始化基礎分析器作為備選方案
        if fallback_to_basic:
            self.basic_analyzer = BasicIntentAnalyzer()
        
        # 初始化智能決策引擎
        self.decision_engine = IntelligentDecisionEngine()
        
        # 初始化緩存
        self.cache = {} if cache_enabled else None
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        
        # 初始化提示詞模板
        self._init_prompt_templates()
        
        # 初始化LLM客戶端
        self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化LLM客戶端"""
        self.llm_client = None
        
        if not self.api_key:
            self.logger.warning("未提供API密鑰，將使用模擬LLM客戶端")
            return
            
        try:
             config = LLMConfig(
                 provider=self.provider,
                 api_key=self.api_key,
                 model_name=self._get_default_model(),
                 temperature=0.1,
                 max_tokens=1000
             )
             self.llm_client = create_llm_client(config)
             self.logger.info(f"LLM客戶端初始化成功，提供商: {self.provider.value}")
            
        except Exception as e:
            self.logger.error(f"LLM客戶端初始化失敗: {e}")
            self.logger.warning("將使用基礎意圖分析器作為備選方案")
            self.llm_client = None
    
    def _init_prompt_templates(self):
        """初始化提示詞模板"""
        self.system_prompt = """
你是一個專業的求職意圖分析AI助手，專門分析用戶的工作搜索查詢並將其轉化為結構化的搜索條件。

核心能力：
1. 深度語義理解：理解自然語言中的隱含意圖和上下文
2. 智能意圖分類：準確判斷查詢是否與求職相關
3. 結構化提取：將複雜查詢轉化為可搜索的結構化數據
4. 智能推理：從描述中推斷用戶的深層需求和偏好

分析原則：
- 語義優先：重視語義理解而非關鍵詞匹配
- 上下文感知：考慮查詢的完整上下文
- 意圖推斷：從描述中推斷隱含的求職偏好
- 精準分類：嚴格區分求職相關和非求職查詢

輸出要求：
- 必須輸出有效的JSON格式
- 所有字段都必須包含
- confidence分數要準確反映分析確信度
- reasoning要提供清晰的分析邏輯

JSON輸出格式：
{
  "is_job_related": boolean,
  "intent_type": "job_search" | "non_job_related" | "unclear",
  "confidence": 0.0-1.0,
  "reasoning": "詳細的分析推理過程",
  "structured_intent": {
    "job_titles": ["識別的職位名稱"],
    "skills": ["相關技能和工具"],
    "locations": ["工作地點"],
    "salary_range": "薪資範圍或null",
    "work_mode": "遠程/線下/混合或null",
    "company_size": "公司規模或null",
    "industry": "目標行業或null",
    "experience_level": "經驗要求或null",
    "soft_preferences": ["工作偏好和文化要求"],
    "urgency": "求職緊急程度或null"
  },
  "search_suggestions": ["優化的搜索建議"],
  "response_message": "給用戶的友好回應"
}
"""
        
        self.analysis_prompt_template = """
請深度分析以下用戶查詢的求職意圖：

用戶查詢："{user_input}"

分析維度：

1. 意圖分類：
   - 明確求職：包含職位、技能、地點等求職元素
   - 職業諮詢：關於職業發展、技能學習的問題
   - 非求職相關：日常生活、娛樂、學術等話題
   - 模糊查詢：意圖不明確，需要進一步澄清

2. 深度語義提取（僅限求職相關）：
   - 職位意圖：直接提及的職位 + 從技能推斷的職位
   - 技能圖譜：技術技能、軟技能、工具、框架
   - 地理偏好：具體城市、國家、遠程工作偏好
   - 薪資期望：明確數字、範圍、相對描述（如"高薪"）
   - 工作模式：遠程、混合、現場，以及靈活性要求
   - 公司特徵：規模（初創/大企業）、行業、知名度
   - 職業階段：入門/中級/資深/管理層
   - 文化偏好：工作氛圍、價值觀、福利期望

3. 隱含意圖推理：
   - "不想加班" → 工作生活平衡、正常工時
   - "學習機會" → 培訓機會、技術成長
   - "團隊氛圍" → 協作文化、扁平管理
   - "穩定" → 大公司、傳統行業
   - "挑戰" → 初創公司、新技術

4. 搜索優化建議：
   - 基於提取的結構化數據生成精準搜索詞
   - 提供多個搜索角度和組合
   - 考慮同義詞和相關概念

請嚴格按照JSON格式輸出，確保所有字段完整且類型正確。
"""
    
    def analyze_intent_with_decision(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> tuple[LLMIntentResult, DecisionResult]:
        """
        分析用戶查詢意圖並進行智能決策
        
        Args:
            query: 用戶查詢字符串
            user_context: 用戶上下文信息
            
        Returns:
            tuple[LLMIntentResult, DecisionResult]: 意圖分析結果和決策結果
        """
        start_time = datetime.now()
        
        try:
            # 1. 進行意圖分析
            intent_result = self.analyze_intent(query)
            
            # 2. 基於意圖分析結果進行智能決策
            decision_result = self.decision_engine.make_decision(intent_result, user_context)
            
            return intent_result, decision_result
            
        except Exception as e:
            self.logger.error(f"意圖分析和決策過程中發生錯誤: {e}")
            
            # 返回錯誤備用結果
            error_intent = LLMIntentResult(
                intent_type=IntentType.UNCLEAR,
                confidence=0.1,
                is_job_related=True,
                structured_intent=None,
                search_query_suggestions=[query],
                response_message="分析過程中發生錯誤，將使用基礎搜索",
                rejection_message="",
                llm_reasoning="分析過程中發生錯誤",
                fallback_used=True,
                llm_used=False,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            error_decision = DecisionResult(
                strategy=ProcessingStrategy.BASIC_SEARCH,
                platform_selection=PlatformSelectionMode.ALL_PLATFORMS,
                confidence=0.1,
                reasoning="系統錯誤，使用基礎搜索策略",
                search_conditions={},
                response_message="系統暫時無法處理您的查詢，將使用基礎搜索"
            )
            
            return error_intent, error_decision
    
    def analyze_intent(self, query: str) -> LLMIntentResult:
        """
        使用LLM分析用戶意圖（保持向後兼容）
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            LLMIntentResult: LLM意圖分析結果
        """
        start_time = datetime.now()
        
        # 檢查緩存
        if self.cache_enabled and query in self.cache:
            cached_result = self.cache[query]
            cached_result.processing_time = 0.001  # 緩存命中時間
            return cached_result
        
        try:
            # 嘗試使用LLM分析
            llm_result = self._analyze_with_llm(query)
            processing_time = (datetime.now() - start_time).total_seconds()
            llm_result.processing_time = processing_time
            
            # 緩存結果
            if self.cache_enabled:
                self.cache[query] = llm_result
            
            return llm_result
            
        except Exception as e:
            self.logger.error(f"LLM分析失敗: {e}")
            
            # 回退到基礎分析器
            if self.fallback_to_basic:
                return self._fallback_to_basic_analyzer(query, start_time)
            else:
                # 返回錯誤結果
                return LLMIntentResult(
                    intent_type=IntentType.UNCLEAR,
                    confidence=0.0,
                    is_job_related=False,
                    response_message="抱歉，系統暫時無法處理您的查詢，請稍後再試。",
                    fallback_used=False,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
    
    def _analyze_with_llm(self, query: str) -> LLMIntentResult:
        """
        使用LLM進行意圖分析
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            LLMIntentResult: 分析結果
        """
        # 構建提示詞
        prompt = self.analysis_prompt_template.format(user_input=query)
        
        # 調用LLM API
        try:
            if self.llm_client:
                llm_response = self._call_llm_api(prompt)
            else:
                # 回退到模擬調用
                llm_response = self._mock_llm_call(query, prompt)
        except Exception as e:
            self.logger.error(f"LLM分析失敗: {e}")
            raise
        
        # 解析LLM響應
        return self._parse_llm_response(llm_response, query)
    
    def _get_default_model(self) -> str:
        """獲取默認模型名稱"""
        model_map = {
            LLMProvider.OPENAI_GPT35: "gpt-3.5-turbo",
            LLMProvider.OPENAI_GPT4: "gpt-4",
            LLMProvider.ANTHROPIC_CLAUDE: "claude-3-sonnet-20240229",
            LLMProvider.AZURE_OPENAI: "gpt-35-turbo",
            LLMProvider.LOCAL_LLAMA: "llama2-7b-chat"
        }
        return model_map.get(self.provider, "gpt-3.5-turbo")
    
    def _convert_basic_to_llm_result(self, basic_result: IntentAnalysisResult, query: str) -> LLMIntentResult:
        """將基礎分析器結果轉換為LLM格式結果"""
        structured_intent = JobSearchIntent(
            job_titles=[],
            skills=[],
            locations=[],
            salary_range=None,
            work_mode=None,
            company_size=None,
            industry=None,
            experience_level=None,
            soft_preferences=[],
            urgency=None
        )
        
        return LLMIntentResult(
            intent_type=basic_result.intent_type,
            confidence=basic_result.confidence,
            is_job_related=basic_result.is_job_related,
            structured_intent=structured_intent if basic_result.is_job_related else None,
            search_query_suggestions=[],
            response_message=basic_result.suggested_response,
            llm_reasoning="使用基礎關鍵詞匹配分析器（LLM不可用）",
            fallback_used=True
        )
    
    def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        調用LLM API進行意圖分析
        
        Args:
            prompt: 完整的提示詞
            
        Returns:
            Dict: LLM響應的結構化數據
        """
        try:
            # 準備消息
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 調用LLM API
            response: LLMResponse = self.llm_client.call(
                messages=messages,
                temperature=0.1,  # 低溫度確保輸出穩定
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            if not response.success:
                self.logger.error(f"LLM API調用失敗: {response.error_message}")
                raise Exception(response.error_message)
            
            # 解析LLM響應
            try:
                llm_result = json.loads(response.content)
                self.logger.info(f"LLM API調用成功，提供商: {self.provider.value}, 響應時間: {response.response_time:.2f}s")
                return llm_result
            except json.JSONDecodeError as e:
                self.logger.error(f"LLM響應JSON解析失敗: {e}")
                self.logger.debug(f"原始響應內容: {response.content}")
                raise Exception(f"JSON解析失敗: {e}")
            
        except Exception as e:
            self.logger.error(f"LLM API調用異常: {e}")
            raise
    
    def _mock_llm_call(self, query: str, prompt: str) -> Dict[str, Any]:
        """
        模擬LLM調用（用於演示，實際使用時應替換為真實的LLM API調用）
        
        Args:
            query: 用戶查詢
            prompt: 完整提示詞
            
        Returns:
            Dict: 模擬的LLM響應
        """
        # 這裡是模擬邏輯，實際實現時應該調用真實的LLM API
        query_lower = query.lower()
        
        # 模擬智能分析
        if any(keyword in query_lower for keyword in ['天氣', '電影', '音樂', '食譜', '烹飪']):
            return {
                "is_job_related": False,
                "intent_type": "non_job_related",
                "confidence": 0.9,
                "reasoning": "查詢內容與求職無關，涉及日常生活話題",
                "structured_intent": None,
                "search_suggestions": [],
                "response_message": "抱歉，我是AI助手，僅能協助您處理求職相關問題。您可以嘗試搜索：'軟體工程師 台北'、'產品經理 薪資'等求職相關內容。"
            }
        
        # 模擬求職相關分析
        job_titles = []
        skills = []
        locations = []
        soft_preferences = []
        
        # 智能提取職位
        if any(title in query_lower for title in ['工程師', 'engineer', '開發', 'developer']):
            if 'frontend' in query_lower or '前端' in query_lower:
                job_titles.append('前端工程師')
                skills.extend(['JavaScript', 'React', 'Vue'])
            elif 'backend' in query_lower or '後端' in query_lower:
                job_titles.append('後端工程師')
                skills.extend(['Python', 'Java', 'Node.js'])
            else:
                job_titles.append('軟體工程師')
        
        if '產品經理' in query or 'product manager' in query_lower:
            job_titles.append('產品經理')
        
        # 智能提取地點
        for location in ['台北', '新北', '台中', '高雄', 'sydney', 'melbourne']:
            if location in query_lower:
                locations.append(location)
        
        if '遠程' in query or 'remote' in query_lower or '在家工作' in query_lower:
            locations.append('遠程工作')
        
        # 智能提取軟性偏好
        if '不加班' in query or '不想加班' in query:
            soft_preferences.extend(['工作生活平衡', '正常工時', '不加班'])
        
        if '團隊氛圍' in query or '文化' in query:
            soft_preferences.extend(['團隊氛圍好', '企業文化佳'])
        
        # 提取薪資信息
        salary_match = re.search(r'(\d+)[-到]?(\d+)?[萬k]', query_lower)
        salary_range = None
        if salary_match:
            if salary_match.group(2):
                salary_range = f"{salary_match.group(1)}-{salary_match.group(2)}萬"
            else:
                salary_range = f"{salary_match.group(1)}萬以上"
        
        # 生成搜索建議
        search_suggestions = []
        if job_titles and locations:
            search_suggestions.append(f"{job_titles[0]} {locations[0]}")
        if job_titles and skills:
            search_suggestions.append(f"{job_titles[0]} {' '.join(skills[:2])}")
        
        return {
            "is_job_related": bool(job_titles or skills or locations or '工作' in query or 'job' in query_lower),
            "intent_type": "job_search",
            "confidence": 0.8 if job_titles else 0.6,
            "reasoning": "基於關鍵詞和語義分析，識別出求職相關意圖",
            "structured_intent": {
                "job_titles": job_titles,
                "skills": skills,
                "locations": locations,
                "salary_range": salary_range,
                "work_mode": "遠程" if '遠程' in query else None,
                "company_size": None,
                "industry": None,
                "experience_level": None,
                "soft_preferences": soft_preferences,
                "urgency": None
            },
            "search_suggestions": search_suggestions,
            "response_message": "已為您分析查詢意圖，正在搜索相關職位..."
        }
    
    def _parse_llm_response(self, llm_response: Dict[str, Any], original_query: str) -> LLMIntentResult:
        """
        解析LLM響應為結構化結果
        
        Args:
            llm_response: LLM原始響應
            original_query: 原始查詢
            
        Returns:
            LLMIntentResult: 解析後的結果
        """
        try:
            # 解析基本信息
            is_job_related = llm_response.get('is_job_related', False)
            intent_type_str = llm_response.get('intent_type', 'unclear')
            confidence = llm_response.get('confidence', 0.0)
            
            # 轉換意圖類型
            try:
                intent_type = IntentType(intent_type_str)
            except ValueError:
                intent_type = IntentType.UNCLEAR
            
            # 解析結構化意圖
            structured_intent = None
            if is_job_related and llm_response.get('structured_intent'):
                intent_data = llm_response['structured_intent']
                structured_intent = JobSearchIntent(
                    job_titles=intent_data.get('job_titles', []),
                    skills=intent_data.get('skills', []),
                    locations=intent_data.get('locations', []),
                    salary_range=intent_data.get('salary_range'),
                    work_mode=intent_data.get('work_mode'),
                    company_size=intent_data.get('company_size'),
                    industry=intent_data.get('industry'),
                    experience_level=intent_data.get('experience_level'),
                    soft_preferences=intent_data.get('soft_preferences', []),
                    urgency=intent_data.get('urgency')
                )
            
            return LLMIntentResult(
                intent_type=intent_type,
                confidence=confidence,
                is_job_related=is_job_related,
                structured_intent=structured_intent,
                search_query_suggestions=llm_response.get('search_suggestions', []),
                response_message=llm_response.get('response_message'),
                llm_reasoning=llm_response.get('reasoning'),
                fallback_used=False
            )
            
        except Exception as e:
            self.logger.error(f"解析LLM響應失敗: {e}")
            # 返回基本結果
            return LLMIntentResult(
                intent_type=IntentType.UNCLEAR,
                confidence=0.0,
                is_job_related=False,
                response_message="抱歉，無法理解您的查詢，請重新描述。",
                fallback_used=False
            )
    
    def _fallback_to_basic_analyzer(self, query: str, start_time: datetime) -> LLMIntentResult:
        """
        回退到基礎分析器
        
        Args:
            query: 用戶查詢
            start_time: 開始時間
            
        Returns:
            LLMIntentResult: 轉換後的結果
        """
        try:
            basic_result = self.basic_analyzer.analyze_intent(query)
            
            # 轉換為LLM結果格式
            return LLMIntentResult(
                intent_type=basic_result.intent_type,
                confidence=basic_result.confidence,
                is_job_related=basic_result.is_job_related,
                response_message=basic_result.suggested_response,
                fallback_used=True,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            self.logger.error(f"基礎分析器也失敗了: {e}")
            return LLMIntentResult(
                intent_type=IntentType.UNCLEAR,
                confidence=0.0,
                is_job_related=False,
                response_message="系統暫時無法處理您的查詢，請稍後再試。",
                fallback_used=True,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def generate_search_conditions(self, structured_intent: JobSearchIntent) -> Dict[str, Any]:
        """
        將結構化意圖轉換為搜索條件
        
        Args:
            structured_intent: 結構化意圖
            
        Returns:
            Dict: 搜索條件
        """
        conditions = {}
        
        if structured_intent.job_titles:
            conditions['job_titles'] = structured_intent.job_titles
        
        if structured_intent.skills:
            conditions['skills'] = structured_intent.skills
        
        if structured_intent.locations:
            conditions['locations'] = structured_intent.locations
        
        if structured_intent.salary_range:
            conditions['salary_range'] = structured_intent.salary_range
        
        if structured_intent.work_mode:
            conditions['work_mode'] = structured_intent.work_mode
        
        if structured_intent.company_size:
            conditions['company_size'] = structured_intent.company_size
        
        if structured_intent.industry:
            conditions['industry'] = structured_intent.industry
        
        if structured_intent.experience_level:
            conditions['experience_level'] = structured_intent.experience_level
        
        if structured_intent.soft_preferences:
            conditions['soft_preferences'] = structured_intent.soft_preferences
        
        return conditions
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        獲取緩存統計信息
        
        Returns:
            Dict: 緩存統計
        """
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        return {
            "cache_enabled": True,
            "cache_size": len(self.cache),
            "cached_queries": list(self.cache.keys())
        }
    
    def clear_cache(self):
        """清空緩存"""
        if self.cache_enabled:
            self.cache.clear()
            self.logger.info("緩存已清空")


# 全局實例
llm_intent_analyzer = LLMIntentAnalyzer()


def analyze_intent_with_llm(query: str) -> LLMIntentResult:
    """
    使用LLM分析意圖的便捷函數
    
    Args:
        query: 用戶查詢字符串
        
    Returns:
        LLMIntentResult: LLM意圖分析結果
    """
    return llm_intent_analyzer.analyze_intent(query)


def is_job_related_llm(query: str) -> bool:
    """
    使用LLM快速判斷查詢是否與求職相關
    
    Args:
        query: 用戶查詢字符串
        
    Returns:
        bool: 是否與求職相關
    """
    result = llm_intent_analyzer.analyze_intent(query)
    return result.is_job_related