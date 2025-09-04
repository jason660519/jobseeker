#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶意圖分析模組
用於判斷用戶查詢是否與求職相關，過濾非求職相關的查詢

Author: jobseeker Team
Date: 2025-01-27
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """意圖類型枚舉"""
    JOB_SEARCH = "job_search"  # 求職搜索
    CAREER_ADVICE = "career_advice"  # 職業建議
    SALARY_INQUIRY = "salary_inquiry"  # 薪資查詢
    COMPANY_INFO = "company_info"  # 公司信息
    SKILL_DEVELOPMENT = "skill_development"  # 技能發展
    INTERVIEW_PREP = "interview_prep"  # 面試準備
    RESUME_HELP = "resume_help"  # 履歷協助
    NON_JOB_RELATED = "non_job_related"  # 非求職相關
    UNCLEAR = "unclear"  # 意圖不明確


@dataclass
class IntentAnalysisResult:
    """意圖分析結果"""
    intent_type: IntentType
    confidence: float  # 置信度 (0.0 - 1.0)
    keywords_matched: List[str]  # 匹配的關鍵詞
    suggested_response: Optional[str] = None  # 建議回應
    is_job_related: bool = True  # 是否與求職相關


class IntentAnalyzer:
    """用戶意圖分析器"""
    
    def __init__(self):
        """初始化意圖分析器"""
        self._init_keywords()
        self._init_patterns()
    
    def _init_keywords(self):
        """初始化關鍵詞庫"""
        # 求職相關關鍵詞
        self.job_keywords = {
            'job_titles': [
                '工程師', '程式設計師', '軟體工程師', '資料科學家', '產品經理', 
                '設計師', '行銷', '業務', '會計', '人資', '護理師', '醫師',
                'engineer', 'developer', 'programmer', 'designer', 'manager',
                'analyst', 'consultant', 'specialist', 'coordinator', 'assistant',
                'director', 'supervisor', 'technician', 'administrator'
            ],
            'job_search_terms': [
                '工作', '職位', '職缺', '招聘', '求職', '應徵', '面試', '履歷',
                '薪水', '薪資', '待遇', '福利', '公司', '企業', '職業', '事業',
                'job', 'position', 'career', 'employment', 'work', 'hiring',
                'recruitment', 'interview', 'resume', 'cv', 'salary', 'wage',
                'company', 'corporation', 'firm', 'organization'
            ],
            'location_terms': [
                '台北', '新北', '桃園', '台中', '台南', '高雄', '新竹', '基隆',
                '遠端', '在家工作', 'remote', 'wfh', 'work from home',
                'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
                'singapore', 'hong kong', 'tokyo', 'seoul', 'bangkok'
            ],
            'skill_terms': [
                'python', 'java', 'javascript', 'react', 'vue', 'angular',
                'node.js', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
                'machine learning', 'ai', 'data science', 'blockchain'
            ]
        }
        
        # 非求職相關關鍵詞
        self.non_job_keywords = {
            'general_chat': [
                '你好', '哈囉', '嗨', '早安', '晚安', '謝謝', '再見',
                'hello', 'hi', 'hey', 'good morning', 'good night', 'thanks', 'bye'
            ],
            'weather': [
                '天氣', '氣溫', '下雨', '晴天', '陰天', '颱風',
                'weather', 'temperature', 'rain', 'sunny', 'cloudy', 'storm'
            ],
            'entertainment': [
                '電影', '音樂', '遊戲', '小說', '動漫', '運動', '旅遊',
                'movie', 'music', 'game', 'novel', 'anime', 'sport', 'travel'
            ],
            'food': [
                '食物', '餐廳', '料理', '食譜', '美食', '飲料',
                'food', 'restaurant', 'cooking', 'recipe', 'drink'
            ],
            'technology_general': [
                '手機', '電腦', '軟體', '硬體', '網路', '科技新聞',
                'phone', 'computer', 'software', 'hardware', 'internet', 'tech news'
            ]
        }
    
    def _init_patterns(self):
        """初始化正則表達式模式"""
        self.job_patterns = [
            r'找.*?工作',
            r'應徵.*?職位',
            r'.*?工程師.*?職缺',
            r'薪水.*?多少',
            r'.*?公司.*?怎麼樣',
            r'面試.*?準備',
            r'履歷.*?寫法',
            r'job.*?search',
            r'looking.*?for.*?job',
            r'salary.*?range',
            r'interview.*?tips',
            r'resume.*?help'
        ]
        
        self.non_job_patterns = [
            r'^(你好|哈囉|嗨|hello|hi)$',
            r'今天.*?天氣',
            r'推薦.*?(電影|音樂|遊戲)',
            r'.*?怎麼煮',
            r'.*?食譜',
            r'聊天.*?話題'
        ]
    
    def analyze_intent(self, query: str) -> IntentAnalysisResult:
        """
        分析用戶查詢的意圖
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            IntentAnalysisResult: 意圖分析結果
        """
        if not query or not query.strip():
            return IntentAnalysisResult(
                intent_type=IntentType.UNCLEAR,
                confidence=0.0,
                keywords_matched=[],
                is_job_related=False,
                suggested_response="請輸入您的查詢內容。"
            )
        
        query_lower = query.lower().strip()
        
        # 1. 檢查是否為明顯的非求職相關查詢
        non_job_result = self._check_non_job_intent(query_lower)
        if non_job_result:
            return non_job_result
        
        # 2. 檢查是否為求職相關查詢
        job_result = self._check_job_intent(query_lower)
        if job_result:
            return job_result
        
        # 3. 模糊匹配和上下文分析
        fuzzy_result = self._fuzzy_intent_analysis(query_lower)
        return fuzzy_result
    
    def _check_non_job_intent(self, query: str) -> Optional[IntentAnalysisResult]:
        """檢查非求職相關意圖"""
        matched_keywords = []
        confidence = 0.0
        
        # 檢查非求職關鍵詞
        for category, keywords in self.non_job_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    matched_keywords.append(keyword)
                    confidence += 0.3
        
        # 檢查非求職模式
        for pattern in self.non_job_patterns:
            if re.search(pattern, query):
                confidence += 0.4
                matched_keywords.append(f"pattern: {pattern}")
        
        if confidence >= 0.6:
            return IntentAnalysisResult(
                intent_type=IntentType.NON_JOB_RELATED,
                confidence=min(confidence, 1.0),
                keywords_matched=matched_keywords,
                is_job_related=False,
                suggested_response="抱歉，我是AI助手，僅能協助您處理求職相關問題，無法進行一般聊天。"
            )
        
        return None
    
    def _check_job_intent(self, query: str) -> Optional[IntentAnalysisResult]:
        """檢查求職相關意圖"""
        matched_keywords = []
        confidence = 0.0
        intent_type = IntentType.JOB_SEARCH
        
        # 檢查求職關鍵詞
        for category, keywords in self.job_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    matched_keywords.append(keyword)
                    if category == 'job_titles':
                        confidence += 0.4
                    elif category == 'job_search_terms':
                        confidence += 0.3
                    elif category == 'location_terms':
                        confidence += 0.2
                    elif category == 'skill_terms':
                        confidence += 0.2
        
        # 檢查求職模式
        for pattern in self.job_patterns:
            if re.search(pattern, query):
                confidence += 0.5
                matched_keywords.append(f"pattern: {pattern}")
        
        # 根據關鍵詞確定具體意圖類型
        if '薪水' in query or '薪資' in query or 'salary' in query:
            intent_type = IntentType.SALARY_INQUIRY
        elif '面試' in query or 'interview' in query:
            intent_type = IntentType.INTERVIEW_PREP
        elif '履歷' in query or 'resume' in query or 'cv' in query:
            intent_type = IntentType.RESUME_HELP
        elif '公司' in query or 'company' in query:
            intent_type = IntentType.COMPANY_INFO
        
        if confidence >= 0.4:
            return IntentAnalysisResult(
                intent_type=intent_type,
                confidence=min(confidence, 1.0),
                keywords_matched=matched_keywords,
                is_job_related=True
            )
        
        return None
    
    def _fuzzy_intent_analysis(self, query: str) -> IntentAnalysisResult:
        """模糊意圖分析"""
        # 簡單的長度和內容分析
        if len(query) < 3:
            return IntentAnalysisResult(
                intent_type=IntentType.UNCLEAR,
                confidence=0.1,
                keywords_matched=[],
                is_job_related=False,
                suggested_response="請提供更詳細的查詢內容。"
            )
        
        # 檢查是否包含數字（可能是薪資查詢）
        if re.search(r'\d+', query):
            return IntentAnalysisResult(
                intent_type=IntentType.JOB_SEARCH,
                confidence=0.3,
                keywords_matched=['contains_numbers'],
                is_job_related=True
            )
        
        # 默認為不明確意圖
        return IntentAnalysisResult(
            intent_type=IntentType.UNCLEAR,
            confidence=0.2,
            keywords_matched=[],
            is_job_related=False,
            suggested_response="抱歉，我無法理解您的查詢。請嘗試使用求職相關的關鍵詞，例如：'軟體工程師 台北'、'產品經理 薪資'等。"
        )
    
    def is_job_related_query(self, query: str) -> Tuple[bool, float]:
        """
        快速判斷查詢是否與求職相關
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            Tuple[bool, float]: (是否求職相關, 置信度)
        """
        result = self.analyze_intent(query)
        return result.is_job_related, result.confidence
    
    def get_rejection_message(self, query: str) -> str:
        """
        獲取拒絕非求職查詢的訊息
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            str: 拒絕訊息
        """
        result = self.analyze_intent(query)
        if not result.is_job_related and result.suggested_response:
            return result.suggested_response
        
        return "抱歉，我是AI助手，僅能協助您處理求職相關問題，無法進行一般聊天。"


# 全局實例
intent_analyzer = IntentAnalyzer()


def analyze_user_intent(query: str) -> IntentAnalysisResult:
    """
    分析用戶意圖的便捷函數
    
    Args:
        query: 用戶查詢字符串
        
    Returns:
        IntentAnalysisResult: 意圖分析結果
    """
    return intent_analyzer.analyze_intent(query)


def is_job_related(query: str) -> bool:
    """
    快速判斷查詢是否與求職相關的便捷函數
    
    Args:
        query: 用戶查詢字符串
        
    Returns:
        bool: 是否與求職相關
    """
    is_related, _ = intent_analyzer.is_job_related_query(query)
    return is_related