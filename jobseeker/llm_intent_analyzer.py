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
import os
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
            # 映射到正確的LLMConfig提供商
            from .llm_config import LLMProvider as ConfigLLMProvider
            
            provider_mapping = {
                LLMProvider.OPENAI_GPT35: ConfigLLMProvider.OPENAI,
                LLMProvider.OPENAI_GPT4: ConfigLLMProvider.OPENAI,
                LLMProvider.ANTHROPIC_CLAUDE: ConfigLLMProvider.ANTHROPIC,
                LLMProvider.AZURE_OPENAI: ConfigLLMProvider.AZURE_OPENAI,
                LLMProvider.LOCAL_LLAMA: ConfigLLMProvider.LOCAL_LLAMA
            }
            
            config_provider = provider_mapping.get(self.provider, ConfigLLMProvider.OPENAI)
            
            config = LLMConfig(
                provider=config_provider,
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
        """初始化提示詞模板 - 從配置文件加載英文標準化提示"""
        try:
            # 嘗試從配置文件加載標準化提示
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'llm_system_prompts.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    prompts_config = json.load(f)
                    
                self.system_prompt = prompts_config['intent_analyzer']['system_prompt']
                self.analysis_prompt_template = prompts_config['intent_analyzer']['analysis_prompt_template']
                logging.info("Successfully loaded standardized English prompts from config file")
            else:
                # 如果配置文件不存在，使用默認英文提示
                self._init_default_english_prompts()
                logging.warning("Config file not found, using default English prompts")
        except Exception as e:
            logging.error(f"Error loading prompt config: {e}, falling back to default English prompts")
            self._init_default_english_prompts()
    
    def _init_default_english_prompts(self):
        """初始化默認英文提示模板"""
        self.system_prompt = """You are a professional job search intent analyzer. Your task is to accurately determine if user queries are job-related and extract structured information.

Core Judgment Principles:
1. Job-related queries must satisfy the following conditions:
   - Contains explicit job titles or job search verbs (e.g., 'find job', 'apply for', 'job search')
   - Or contains job title + location combination (e.g., 'software engineer Sydney')
   - Or contains clear career development intent (e.g., 'career planning', 'career change')

2. Non-job-related queries:
   - Only contains location names (e.g., 'Sydney', 'Melbourne')
   - Only contains skill learning queries (e.g., 'learn Python', 'how to learn')
   - Daily life queries (weather, entertainment, shopping, travel, etc.)
   - Pure technical questions or academic discussions

3. Confidence scoring standards:
   - 0.9-1.0: Clearly contains job title + location/skills
   - 0.7-0.8: Contains job search verbs or career development keywords
   - 0.5-0.6: Ambiguous job-related queries
   - 0.3-0.4: Boundary cases, leaning towards non-job
   - 0.0-0.2: Clearly non-job-related

Output JSON format (must strictly follow):
{
  "is_job_related": boolean,
  "intent_type": "job_search" | "non_job_related" | "unclear",
  "confidence": 0.0-1.0,
  "reasoning": "analysis reasoning process",
  "job_titles": ["job title list"],
  "skills": ["skill list"],
  "locations": ["location list"],
  "search_suggestions": ["search suggestions"],
  "response_message": "user response message"
}

Important: Queries containing only location or skill keywords but lacking clear job search intent should be classified as non-job-related."""
        
        self.analysis_prompt_template = """I am a career analyst. I will analyze the user's prompt, extract key parameters (such as location, job categories, etc.), and output structured JSON format for downstream databases and crawler engines.

User Query: "{user_input}"

Analysis Dimensions:

1. Intent Classification:
   - Clear job search: Contains job titles, skills, locations and other job search elements
   - Career consultation: Questions about career development and skill learning
   - Non-job-related: Daily life, entertainment, academic topics
   - Ambiguous query: Unclear intent, requires further clarification

2. Deep Semantic Extraction (job-related only):
   - Job Intent: Directly mentioned positions + positions inferred from skills
   - Skill Map: Technical skills, soft skills, tools, frameworks
   - Geographic Preferences: Specific cities, countries, remote work preferences
   - Salary Expectations: Specific numbers, ranges, relative descriptions (e.g., "high salary")
   - Work Mode: Remote, hybrid, on-site, and flexibility requirements
   - Company Characteristics: Size (startup/enterprise), industry, reputation
   - Career Stage: Entry/mid-level/senior/management
   - Cultural Preferences: Work atmosphere, values, benefit expectations

3. Implicit Intent Reasoning:
   - "No overtime" → Work-life balance, normal working hours
   - "Learning opportunities" → Training opportunities, technical growth
   - "Team atmosphere" → Collaborative culture, flat management
   - "Stability" → Large companies, traditional industries
   - "Challenge" → Startups, new technologies

4. Search Optimization Suggestions:
   - Generate precise search terms based on extracted structured data
   - Provide multiple search angles and combinations
   - Consider synonyms and related concepts

Output must be standard JSON structure containing all necessary parameters so that the router can distribute to appropriate crawler programs (such as LinkedIn, Indeed, Google, etc.) for subsequent search operations. Please strictly output in JSON format, ensuring all fields are complete and types are correct."""
    
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
            
        Raises:
            Exception: 當LLM服務不可用時
        """
        # 檢查LLM客戶端是否可用
        if not self.llm_client:
            raise Exception("目前LLM服務暫時不可用，請使用主頁的智能職位搜尋功能，這將幫助您更精準地找到理想工作。")
        
        # 構建提示詞
        prompt = self.analysis_prompt_template.format(user_input=query)
        
        # 調用LLM API
        try:
            llm_response = self._call_llm_api(prompt)
        except Exception as e:
            self.logger.error(f"LLM分析失敗: {e}")
            raise Exception("目前LLM服務暫時不可用，請使用主頁的智能職位搜尋功能，這將幫助您更精準地找到理想工作。")
        
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
    
    # 模擬LLM相關方法已移除 - 不再支持模擬功能
    
    def _calculate_job_relevance_score(self, query_lower: str, job_keywords: Dict[str, list]) -> float:
        """
        計算求職相關性得分 (0.0 - 1.0)
        """
        score = 0.0
        
        # 職位名稱匹配 (權重: 0.4)
        for title in job_keywords['job_titles_zh'] + job_keywords['job_titles_en']:
            if title.lower() in query_lower:
                score += 0.4
                break
        
        # 技能關鍵字匹配 (權重: 0.3)
        skill_matches = sum(1 for skill in job_keywords['skills'] 
                           if skill.lower() in query_lower)
        if skill_matches > 0:
            score += min(0.3, skill_matches * 0.1)
        
        # 求職動詞匹配 (權重: 0.2)
        for verb in job_keywords['job_verbs']:
            if verb.lower() in query_lower:
                score += 0.2
                break
        
        # 地點關鍵字匹配 (權重: 0.1)
        for location in job_keywords['locations']:
            if location.lower() in query_lower:
                score += 0.1
                break
        
        return min(score, 1.0)
    
    def _is_boundary_case_non_job(self, query_lower: str, job_score: float) -> bool:
        """
        檢查是否為邊界案例中的非求職查詢
        主要針對單純的地點、薪資關鍵詞等
        """
        # 如果得分太高，不是邊界案例
        if job_score >= 0.2:
            return False
            
        # 定義邊界案例關鍵詞
        location_only_keywords = [
            '台北', '新北', '桃園', '台中', '台南', '高雄', '新竹', '基隆',
            'taipei', 'taichung', 'kaohsiung', 'sydney', 'melbourne', 'singapore'
        ]
        
        salary_only_keywords = ['薪水', '薪資', '工資', 'salary', 'wage', 'pay']
        
        general_keywords = ['工作', 'job', 'work', '職位', 'position']
        
        # 移除空格並分割查詢
        query_words = query_lower.replace(' ', '').split()
        
        # 檢查是否只包含單一地點
        if len(query_words) <= 2 and any(loc in query_lower for loc in location_only_keywords):
            # 檢查是否沒有其他求職相關詞彙
            has_job_context = any(word in query_lower for word in 
                                ['工程師', '開發', '設計師', '經理', '分析師', 'engineer', 'developer', 'manager', 'analyst'])
            if not has_job_context:
                return True
        
        # 檢查是否只包含薪資關鍵詞
        if len(query_words) <= 2 and any(sal in query_lower for sal in salary_only_keywords):
            # 檢查是否沒有職位上下文
            has_job_context = any(word in query_lower for word in 
                                ['工程師', '開發', '設計師', '經理', '分析師', 'engineer', 'developer', 'manager', 'analyst'])
            if not has_job_context:
                return True
        
        # 檢查是否只包含過於泛泛的關鍵詞
        if len(query_words) <= 2 and any(gen in query_lower for gen in general_keywords):
            # 如果只有「工作」或「職位」這樣的詞，且沒有其他具體信息
            has_specific_context = any(word in query_lower for word in 
                                     ['工程師', '開發', '設計師', '經理', '分析師', 'python', 'java', 'react', 
                                      'engineer', 'developer', 'manager', 'analyst'])
            if not has_specific_context and job_score <= 0.15:
                return True
        
        return False
    
    def _create_job_related_response(self, query: str, score: float, confidence_level: str) -> Dict[str, Any]:
        """
        創建求職相關的響應
        """
        # 提取結構化信息
        structured_intent = self._extract_structured_intent(query)
        
        # 根據置信度調整confidence值
        confidence_map = {"高": 0.9, "中": 0.7, "低": 0.5}
        confidence = confidence_map.get(confidence_level, 0.7)
        
        # 生成搜索建議
        search_suggestions = []
        if structured_intent['job_titles'] and structured_intent['locations']:
            search_suggestions.append(f"{structured_intent['job_titles'][0]} {structured_intent['locations'][0]}")
        if structured_intent['job_titles'] and structured_intent['skills']:
            search_suggestions.append(f"{structured_intent['job_titles'][0]} {' '.join(structured_intent['skills'][:2])}")
        
        return {
            "is_job_related": True,
            "intent_type": "job_search",
            "confidence": confidence,
            "reasoning": f"求職相關性得分{score:.2f}，置信度{confidence_level}",
            "structured_intent": structured_intent,
            "search_suggestions": search_suggestions,
            "response_message": "已為您分析查詢意圖，正在搜索相關職位..."
        }
    
    def _extract_structured_intent(self, query: str) -> Dict[str, Any]:
        """
        從查詢中提取結構化的求職意圖
        增強版本，支援更多職位和技能識別
        """
        query_lower = query.lower()
        
        # 提取職位名稱 (擴展版)
        job_titles = []
        job_keywords = [
            '工程師', '開發者', '程式設計師', '設計師', '經理', '分析師', '科學家',
            'engineer', 'developer', 'programmer', 'designer', 'manager', 'analyst', 'scientist'
        ]
        for keyword in job_keywords:
            if keyword in query_lower:
                job_titles.append(keyword)
        
        # 智能提取職位
        if any(title in query_lower for title in ['工程師', 'engineer', '開發', 'developer']):
            if 'ai' in query_lower or '人工智慧' in query_lower or '機器學習' in query_lower:
                if 'AI工程師' not in job_titles:
                    job_titles.append('AI工程師')
            elif 'frontend' in query_lower or '前端' in query_lower:
                if '前端工程師' not in job_titles:
                    job_titles.append('前端工程師')
            elif 'backend' in query_lower or '後端' in query_lower:
                if '後端工程師' not in job_titles:
                    job_titles.append('後端工程師')
        
        # 提取技能 (擴展版)
        skills = []
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'sql', 'mysql', 'postgresql', 'machine learning', 'ai', 'ml',
            'docker', 'kubernetes', 'aws', 'azure', 'git'
        ]
        for skill in skill_keywords:
            if skill in query_lower:
                skills.append(skill)
        
        # 智能技能推斷
        if 'ai' in query_lower or '人工智慧' in query_lower or '機器學習' in query_lower:
            skills.extend(['Python', 'TensorFlow', 'PyTorch', 'Machine Learning'])
        elif 'frontend' in query_lower or '前端' in query_lower:
            skills.extend(['JavaScript', 'React', 'Vue'])
        elif 'backend' in query_lower or '後端' in query_lower:
            skills.extend(['Python', 'Java', 'Node.js'])
        
        # 去重
        skills = list(set(skills))
        
        # 提取地點 (擴展版)
        locations = []
        location_keywords = [
            '台北', '新北', '桃園', '台中', '台南', '高雄', '新竹', '基隆',
            'taipei', 'taichung', 'kaohsiung', 'sydney', 'melbourne', 'singapore',
            'remote', '遠程', '遠端'
        ]
        for location in location_keywords:
            if location in query_lower:
                locations.append(location)
        
        if '在家工作' in query_lower or 'wfh' in query_lower:
            locations.append('遠程工作')
        
        # 提取經驗要求
        experience_level = None
        if any(word in query_lower for word in ['新手', '初級', 'junior', 'entry']):
            experience_level = 'junior'
        elif any(word in query_lower for word in ['資深', '高級', 'senior']):
            experience_level = 'senior'
        elif any(word in query_lower for word in ['中級', 'mid', 'middle']):
            experience_level = 'mid'
        
        # 提取軟性偏好
        soft_preferences = []
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
        
        return {
            "job_titles": job_titles,
            "skills": skills,
            "locations": locations,
            "salary_range": salary_range,
            "work_mode": "遠程" if any(remote in query_lower for remote in ['遠程', '遠端', 'remote']) else None,
            "company_size": None,
            "industry": None,
            "experience_level": experience_level,
            "soft_preferences": soft_preferences,
            "urgency": None
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


# 全局實例（用於向後兼容）
# 自動檢測API密鑰並初始化
def _create_global_analyzer():
    """創建全局分析器實例，自動檢測可用的API密鑰"""
    import os
    
    # 檢查可用的API密鑰
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if openai_key:
        # 使用OpenAI
        return LLMIntentAnalyzer(
            provider=LLMProvider.OPENAI_GPT35,
            api_key=openai_key,
            fallback_to_basic=True
        )
    elif anthropic_key:
        # 使用Anthropic
        return LLMIntentAnalyzer(
            provider=LLMProvider.ANTHROPIC_CLAUDE,
            api_key=anthropic_key,
            fallback_to_basic=True
        )
    else:
        # 沒有API密鑰，使用Mock模式
        return LLMIntentAnalyzer()

llm_intent_analyzer = _create_global_analyzer()


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