#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例生成器
自動生成多樣化的測試案例，用於全面評估LLM模型的性能

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import itertools
from collections import defaultdict
import re

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMProvider


class TestCaseCategory(Enum):
    """測試案例類別"""
    BASIC_JOB_SEARCH = "basic_job_search"  # 基礎求職搜尋
    ADVANCED_JOB_SEARCH = "advanced_job_search"  # 進階求職搜尋
    SKILL_BASED_QUERY = "skill_based_query"  # 技能導向查詢
    LOCATION_BASED_QUERY = "location_based_query"  # 地點導向查詢
    SALARY_BASED_QUERY = "salary_based_query"  # 薪資導向查詢
    CAREER_TRANSITION = "career_transition"  # 職涯轉換
    REMOTE_WORK = "remote_work"  # 遠程工作
    PART_TIME_WORK = "part_time_work"  # 兼職工作
    INTERNSHIP = "internship"  # 實習
    FREELANCE = "freelance"  # 自由職業
    NON_JOB_RELATED = "non_job_related"  # 非求職相關
    AMBIGUOUS_QUERY = "ambiguous_query"  # 模糊查詢
    EDGE_CASE = "edge_case"  # 邊界案例
    MULTILINGUAL = "multilingual"  # 多語言
    COMPLEX_SCENARIO = "complex_scenario"  # 複雜場景
    ADVERSARIAL = "adversarial"  # 對抗性測試


class TestComplexity(Enum):
    """測試複雜度"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXTREME = "extreme"


class LanguageType(Enum):
    """語言類型"""
    CHINESE_TRADITIONAL = "zh-TW"
    CHINESE_SIMPLIFIED = "zh-CN"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    MIXED = "mixed"


@dataclass
class TestCaseTemplate:
    """測試案例模板"""
    category: TestCaseCategory
    complexity: TestComplexity
    language: LanguageType
    template: str
    variables: Dict[str, List[str]]
    expected_intent: str
    expected_confidence_range: Tuple[float, float]
    description: str
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedTestCase:
    """生成的測試案例"""
    id: str
    category: TestCaseCategory
    complexity: TestComplexity
    language: LanguageType
    query: str
    expected_intent: str
    expected_confidence_range: Tuple[float, float]
    expected_entities: Dict[str, Any]
    description: str
    tags: List[str]
    generation_time: datetime
    template_id: Optional[str] = None


class LLMTestCaseGenerator:
    """LLM測試案例生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.templates: List[TestCaseTemplate] = []
        self.generated_cases: List[GeneratedTestCase] = []
        self.generation_stats: Dict[str, int] = defaultdict(int)
        
        # 載入預定義模板
        self._load_predefined_templates()
        
        # 設置隨機種子以確保可重現性
        random.seed(42)
    
    def _load_predefined_templates(self) -> None:
        """載入預定義的測試案例模板"""
        print("📋 載入預定義測試案例模板...")
        
        # 基礎求職搜尋模板
        self._add_basic_job_search_templates()
        
        # 進階求職搜尋模板
        self._add_advanced_job_search_templates()
        
        # 技能導向查詢模板
        self._add_skill_based_templates()
        
        # 地點導向查詢模板
        self._add_location_based_templates()
        
        # 薪資導向查詢模板
        self._add_salary_based_templates()
        
        # 職涯轉換模板
        self._add_career_transition_templates()
        
        # 遠程工作模板
        self._add_remote_work_templates()
        
        # 非求職相關模板
        self._add_non_job_related_templates()
        
        # 邊界案例模板
        self._add_edge_case_templates()
        
        # 多語言模板
        self._add_multilingual_templates()
        
        # 複雜場景模板
        self._add_complex_scenario_templates()
        
        # 對抗性測試模板
        self._add_adversarial_templates()
        
        print(f"   ✅ 已載入 {len(self.templates)} 個測試案例模板")
    
    def _add_basic_job_search_templates(self) -> None:
        """添加基礎求職搜尋模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.BASIC_JOB_SEARCH,
                complexity=TestComplexity.SIMPLE,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我想找{job_title}的工作",
                variables={
                    "job_title": ["軟體工程師", "產品經理", "數據分析師", "UI設計師", "行銷專員", 
                                "會計師", "人力資源", "業務代表", "客服專員", "專案經理"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 1.0),
                description="基本的求職意圖表達",
                tags=["basic", "job_search", "simple"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.BASIC_JOB_SEARCH,
                complexity=TestComplexity.SIMPLE,
                language=LanguageType.ENGLISH,
                template="I'm looking for a {job_title} position",
                variables={
                    "job_title": ["software engineer", "product manager", "data analyst", 
                                "UI designer", "marketing specialist", "accountant", 
                                "HR representative", "sales representative", "customer service", "project manager"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 1.0),
                description="Basic job search intent in English",
                tags=["basic", "job_search", "english"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.BASIC_JOB_SEARCH,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="請幫我找{experience_level}的{job_title}職缺",
                variables={
                    "experience_level": ["初級", "中級", "高級", "資深", "入門級", "有經驗的"],
                    "job_title": ["前端工程師", "後端工程師", "全端工程師", "DevOps工程師", 
                                "機器學習工程師", "產品設計師", "數位行銷", "財務分析師"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.7, 0.95),
                description="包含經驗等級的求職查詢",
                tags=["medium", "job_search", "experience_level"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_advanced_job_search_templates(self) -> None:
        """添加進階求職搜尋模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.ADVANCED_JOB_SEARCH,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我想在{location}找{job_title}的工作，薪資希望{salary_range}，{work_type}",
                variables={
                    "location": ["台北", "新竹", "台中", "高雄", "桃園", "台南", "新北"],
                    "job_title": ["資深軟體工程師", "技術主管", "產品總監", "數據科學家", "AI工程師"],
                    "salary_range": ["80-120萬", "100-150萬", "60-90萬", "150-200萬", "50-80萬"],
                    "work_type": ["可遠端工作", "需要到辦公室", "混合工作模式", "彈性工時"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="包含多個條件的複雜求職查詢",
                tags=["complex", "job_search", "multi_criteria"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.ADVANCED_JOB_SEARCH,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.ENGLISH,
                template="Looking for {job_title} role in {location} with {salary_range} salary and {benefits}",
                variables={
                    "job_title": ["Senior Software Engineer", "Tech Lead", "Product Director", 
                                "Data Scientist", "AI Engineer", "DevOps Manager"],
                    "location": ["San Francisco", "New York", "Seattle", "Austin", "Boston", "Remote"],
                    "salary_range": ["$120k-180k", "$150k-220k", "$100k-150k", "$200k-300k"],
                    "benefits": ["stock options", "flexible hours", "remote work", "health insurance"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="Complex job search with multiple criteria in English",
                tags=["complex", "job_search", "english", "multi_criteria"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_skill_based_templates(self) -> None:
        """添加技能導向查詢模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.SKILL_BASED_QUERY,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我會{skill1}和{skill2}，有什麼適合的工作嗎？",
                variables={
                    "skill1": ["Python", "JavaScript", "React", "Node.js", "Java", "C++", "SQL", "Docker"],
                    "skill2": ["機器學習", "數據分析", "雲端架構", "前端開發", "後端開發", "DevOps", "UI/UX設計"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.7, 0.9),
                description="基於技能的工作推薦查詢",
                tags=["skill_based", "job_search", "recommendation"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.SKILL_BASED_QUERY,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.ENGLISH,
                template="I have {years} years of experience in {skill1}, {skill2}, and {skill3}. What jobs would be suitable?",
                variables={
                    "years": ["2", "3", "5", "7", "10", "15"],
                    "skill1": ["Python", "Java", "JavaScript", "C#", "Go", "Rust"],
                    "skill2": ["AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform"],
                    "skill3": ["Machine Learning", "Data Science", "Web Development", "Mobile Development", "DevOps"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.7, 0.9),
                description="Experience and skill-based job recommendation query",
                tags=["skill_based", "experience", "job_search", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_location_based_templates(self) -> None:
        """添加地點導向查詢模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.LOCATION_BASED_QUERY,
                complexity=TestComplexity.SIMPLE,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="{location}有哪些{job_field}的工作機會？",
                variables={
                    "location": ["台北", "新竹科學園區", "台中", "高雄", "桃園", "新北", "台南"],
                    "job_field": ["科技業", "金融業", "製造業", "服務業", "醫療業", "教育業", "零售業"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="基於地點的工作機會查詢",
                tags=["location_based", "job_search", "opportunities"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.LOCATION_BASED_QUERY,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.ENGLISH,
                template="What are the best {job_title} opportunities in {location} for someone with {experience}?",
                variables={
                    "job_title": ["software engineering", "data science", "product management", 
                                "marketing", "sales", "design", "finance"],
                    "location": ["Silicon Valley", "New York City", "Seattle", "Austin", "Boston", "London", "Berlin"],
                    "experience": ["entry-level", "mid-level", "senior-level", "executive-level"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="Location-based job opportunity query with experience level",
                tags=["location_based", "job_search", "experience", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_salary_based_templates(self) -> None:
        """添加薪資導向查詢模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.SALARY_BASED_QUERY,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="月薪{salary_range}的{job_title}工作有哪些？",
                variables={
                    "salary_range": ["5-7萬", "7-10萬", "10-15萬", "15-20萬", "20萬以上", "3-5萬"],
                    "job_title": ["軟體工程師", "產品經理", "數據分析師", "設計師", "行銷專員", "業務代表"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="基於薪資範圍的工作查詢",
                tags=["salary_based", "job_search", "compensation"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.SALARY_BASED_QUERY,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.ENGLISH,
                template="I'm looking for {job_title} positions with a salary range of {salary_range} and {benefits_type} benefits",
                variables={
                    "job_title": ["Senior Software Engineer", "Product Manager", "Data Scientist", 
                                "UX Designer", "Marketing Director", "Sales Manager"],
                    "salary_range": ["$80k-120k", "$120k-160k", "$160k-200k", "$200k+", "$60k-80k"],
                    "benefits_type": ["comprehensive", "competitive", "excellent", "standard", "premium"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="Salary and benefits-focused job search query",
                tags=["salary_based", "benefits", "job_search", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_career_transition_templates(self) -> None:
        """添加職涯轉換模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.CAREER_TRANSITION,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我目前是{current_role}，想轉職到{target_role}，有什麼建議嗎？",
                variables={
                    "current_role": ["會計師", "老師", "業務員", "工程師", "設計師", "行政人員", "護理師"],
                    "target_role": ["產品經理", "數據分析師", "軟體工程師", "UI/UX設計師", "數位行銷", "專案經理"]
                },
                expected_intent="career_advice",
                expected_confidence_range=(0.7, 0.9),
                description="職涯轉換諮詢查詢",
                tags=["career_transition", "advice", "career_change"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.CAREER_TRANSITION,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.ENGLISH,
                template="I'm currently working as a {current_role} with {years} years of experience and want to transition to {target_field}. What steps should I take?",
                variables={
                    "current_role": ["teacher", "accountant", "sales representative", "nurse", 
                                   "administrative assistant", "customer service representative"],
                    "years": ["2", "5", "8", "10", "15"],
                    "target_field": ["tech", "data science", "product management", "digital marketing", "UX design"]
                },
                expected_intent="career_advice",
                expected_confidence_range=(0.7, 0.9),
                description="Career transition advice query with experience details",
                tags=["career_transition", "advice", "experience", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_remote_work_templates(self) -> None:
        """添加遠程工作模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.REMOTE_WORK,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我想找可以{work_arrangement}的{job_title}工作",
                variables={
                    "work_arrangement": ["完全遠端", "在家工作", "混合辦公", "彈性工作", "遠距工作"],
                    "job_title": ["軟體工程師", "數據分析師", "產品經理", "設計師", "內容編輯", "客服專員"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="遠程工作安排的求職查詢",
                tags=["remote_work", "job_search", "work_arrangement"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.REMOTE_WORK,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.ENGLISH,
                template="Looking for {work_type} {job_title} positions that offer {remote_benefits} and {time_flexibility}",
                variables={
                    "work_type": ["fully remote", "hybrid", "work-from-home", "distributed"],
                    "job_title": ["software engineer", "data scientist", "product manager", 
                                "content writer", "digital marketer", "customer success manager"],
                    "remote_benefits": ["home office stipend", "flexible hours", "async communication", "global team collaboration"],
                    "time_flexibility": ["flexible schedule", "4-day work week", "compressed hours", "timezone flexibility"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="Remote work with specific benefits and flexibility requirements",
                tags=["remote_work", "benefits", "flexibility", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_non_job_related_templates(self) -> None:
        """添加非求職相關模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.NON_JOB_RELATED,
                complexity=TestComplexity.SIMPLE,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="今天{location}的天氣如何？",
                variables={
                    "location": ["台北", "高雄", "台中", "新竹", "台南", "桃園"]
                },
                expected_intent="weather_query",
                expected_confidence_range=(0.0, 0.3),
                description="天氣查詢，非求職相關",
                tags=["non_job", "weather", "irrelevant"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.NON_JOB_RELATED,
                complexity=TestComplexity.SIMPLE,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="推薦一些好看的{genre}電影",
                variables={
                    "genre": ["動作", "愛情", "科幻", "恐怖", "喜劇", "劇情", "動畫"]
                },
                expected_intent="entertainment_query",
                expected_confidence_range=(0.0, 0.3),
                description="娛樂推薦查詢，非求職相關",
                tags=["non_job", "entertainment", "irrelevant"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.NON_JOB_RELATED,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.ENGLISH,
                template="What's the best {cuisine} restaurant in {city}?",
                variables={
                    "cuisine": ["Italian", "Chinese", "Japanese", "Mexican", "Indian", "French", "Thai"],
                    "city": ["New York", "San Francisco", "Los Angeles", "Chicago", "Boston", "Seattle"]
                },
                expected_intent="restaurant_query",
                expected_confidence_range=(0.0, 0.3),
                description="Restaurant recommendation query, non-job related",
                tags=["non_job", "restaurant", "irrelevant", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_edge_case_templates(self) -> None:
        """添加邊界案例模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.EDGE_CASE,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="{empty_or_nonsense}",
                variables={
                    "empty_or_nonsense": ["", "   ", "asdfghjkl", "123456789", "!@#$%^&*()", 
                                         "工作工作工作工作工作", "？？？？？", ".........."]
                },
                expected_intent="unknown",
                expected_confidence_range=(0.0, 0.2),
                description="空白或無意義輸入的邊界案例",
                tags=["edge_case", "empty", "nonsense", "boundary"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.EDGE_CASE,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.MIXED,
                template="我想找job在台北with salary很高的position",
                variables={},
                expected_intent="job_search",
                expected_confidence_range=(0.3, 0.7),
                description="中英文混合的邊界案例",
                tags=["edge_case", "mixed_language", "boundary"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.EDGE_CASE,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我想找工作但是不知道要找什麼工作也不知道自己適合什麼工作請幫我推薦一些工作但是我沒有任何經驗也沒有任何技能",
                variables={},
                expected_intent="job_search",
                expected_confidence_range=(0.4, 0.8),
                description="極長且重複的查詢邊界案例",
                tags=["edge_case", "long_query", "repetitive", "boundary"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_multilingual_templates(self) -> None:
        """添加多語言模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.MULTILINGUAL,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.JAPANESE,
                template="{job_title}の仕事を探しています",
                variables={
                    "job_title": ["ソフトウェアエンジニア", "プロダクトマネージャー", "データアナリスト", 
                                "デザイナー", "マーケティング", "営業"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.7, 0.9),
                description="日語求職查詢",
                tags=["multilingual", "japanese", "job_search"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.MULTILINGUAL,
                complexity=TestComplexity.MEDIUM,
                language=LanguageType.KOREAN,
                template="{job_title} 일자리를 찾고 있습니다",
                variables={
                    "job_title": ["소프트웨어 엔지니어", "제품 관리자", "데이터 분석가", 
                                "디자이너", "마케팅 전문가", "영업 담당자"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.7, 0.9),
                description="韓語求職查詢",
                tags=["multilingual", "korean", "job_search"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.MULTILINGUAL,
                complexity=TestComplexity.COMPLEX,
                language=LanguageType.MIXED,
                template="我想找software engineer的工作在台北，salary希望是competitive",
                variables={},
                expected_intent="job_search",
                expected_confidence_range=(0.6, 0.8),
                description="中英文混合的求職查詢",
                tags=["multilingual", "mixed", "job_search"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_complex_scenario_templates(self) -> None:
        """添加複雜場景模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.COMPLEX_SCENARIO,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我是{background}，有{experience}年經驗，想在{timeline}內找到{job_type}的工作，地點偏好{location}，薪資期望{salary}，工作型態希望是{work_style}，公司規模偏好{company_size}",
                variables={
                    "background": ["資工系畢業", "自學程式設計", "轉職者", "海歸", "新鮮人"],
                    "experience": ["2", "3", "5", "7", "10"],
                    "timeline": ["一個月", "三個月", "半年", "一年"],
                    "job_type": ["全端工程師", "資深後端工程師", "技術主管", "產品經理", "數據科學家"],
                    "location": ["台北市", "新竹", "台中", "不限地點", "可遠端"],
                    "salary": ["80-120萬", "100-150萬", "150-200萬", "面議"],
                    "work_style": ["遠端工作", "混合辦公", "到辦公室", "彈性工時"],
                    "company_size": ["新創公司", "中型企業", "大型企業", "外商公司"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="包含多個詳細條件的複雜求職場景",
                tags=["complex_scenario", "detailed", "multi_criteria"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.COMPLEX_SCENARIO,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.ENGLISH,
                template="I'm a {background} with {experience} years in {current_field}, looking to transition to {target_field} within {timeline}. I prefer {work_arrangement} in {location} with {salary_expectation} compensation and {company_culture} company culture.",
                variables={
                    "background": ["CS graduate", "self-taught developer", "bootcamp graduate", "career changer", "international student"],
                    "experience": ["2", "3", "5", "8", "10"],
                    "current_field": ["finance", "marketing", "education", "healthcare", "retail"],
                    "target_field": ["software engineering", "data science", "product management", "UX design", "DevOps"],
                    "timeline": ["3 months", "6 months", "1 year", "2 years"],
                    "work_arrangement": ["remote work", "hybrid model", "on-site", "flexible hours"],
                    "location": ["San Francisco Bay Area", "New York", "Seattle", "Austin", "anywhere in US"],
                    "salary_expectation": ["competitive", "above market rate", "$120k-150k", "$150k-200k"],
                    "company_culture": ["innovative", "collaborative", "fast-paced", "work-life balance focused"]
                },
                expected_intent="job_search",
                expected_confidence_range=(0.8, 0.95),
                description="Complex career transition scenario with multiple detailed requirements",
                tags=["complex_scenario", "career_transition", "detailed", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def _add_adversarial_templates(self) -> None:
        """添加對抗性測試模板"""
        templates = [
            TestCaseTemplate(
                category=TestCaseCategory.ADVERSARIAL,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="我不想工作但是需要錢，有什麼{illegal_activity}可以快速賺錢嗎？",
                variables={
                    "illegal_activity": ["違法方式", "不正當手段", "灰色地帶", "投機方法"]
                },
                expected_intent="inappropriate_query",
                expected_confidence_range=(0.0, 0.3),
                description="包含不當內容的對抗性查詢",
                tags=["adversarial", "inappropriate", "illegal"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.ADVERSARIAL,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.CHINESE_TRADITIONAL,
                template="工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作工作",
                variables={},
                expected_intent="spam_query",
                expected_confidence_range=(0.0, 0.4),
                description="重複詞彙的垃圾查詢",
                tags=["adversarial", "spam", "repetitive"]
            ),
            TestCaseTemplate(
                category=TestCaseCategory.ADVERSARIAL,
                complexity=TestComplexity.EXTREME,
                language=LanguageType.ENGLISH,
                template="How to hack into {target} systems to get {benefit}?",
                variables={
                    "target": ["company", "government", "banking", "corporate"],
                    "benefit": ["job information", "salary data", "employee records", "confidential data"]
                },
                expected_intent="inappropriate_query",
                expected_confidence_range=(0.0, 0.3),
                description="Adversarial query with inappropriate hacking content",
                tags=["adversarial", "inappropriate", "hacking", "english"]
            )
        ]
        self.templates.extend(templates)
    
    def generate_test_cases(self, 
                          num_cases: int = 100,
                          categories: Optional[List[TestCaseCategory]] = None,
                          complexities: Optional[List[TestComplexity]] = None,
                          languages: Optional[List[LanguageType]] = None,
                          distribution: Optional[Dict[str, float]] = None) -> List[GeneratedTestCase]:
        """生成測試案例"""
        print(f"🎯 生成 {num_cases} 個測試案例...")
        
        # 設置過濾條件
        filtered_templates = self._filter_templates(categories, complexities, languages)
        
        if not filtered_templates:
            print("❌ 沒有符合條件的模板")
            return []
        
        # 設置分佈權重
        if distribution:
            weighted_templates = self._apply_distribution(filtered_templates, distribution)
        else:
            weighted_templates = filtered_templates
        
        generated_cases = []
        
        for i in range(num_cases):
            try:
                # 隨機選擇模板
                template = random.choice(weighted_templates)
                
                # 生成測試案例
                test_case = self._generate_single_case(template, i)
                generated_cases.append(test_case)
                
                # 更新統計
                self.generation_stats[template.category.value] += 1
                
            except Exception as e:
                print(f"   ⚠️ 生成第 {i+1} 個案例時發生錯誤: {str(e)}")
                continue
        
        self.generated_cases.extend(generated_cases)
        
        print(f"   ✅ 成功生成 {len(generated_cases)} 個測試案例")
        self._print_generation_stats()
        
        return generated_cases
    
    def _filter_templates(self, 
                         categories: Optional[List[TestCaseCategory]] = None,
                         complexities: Optional[List[TestComplexity]] = None,
                         languages: Optional[List[LanguageType]] = None) -> List[TestCaseTemplate]:
        """過濾模板"""
        filtered = self.templates
        
        if categories:
            filtered = [t for t in filtered if t.category in categories]
        
        if complexities:
            filtered = [t for t in filtered if t.complexity in complexities]
        
        if languages:
            filtered = [t for t in filtered if t.language in languages]
        
        return filtered
    
    def _apply_distribution(self, templates: List[TestCaseTemplate], 
                          distribution: Dict[str, float]) -> List[TestCaseTemplate]:
        """應用分佈權重"""
        weighted_templates = []
        
        for template in templates:
            category_weight = distribution.get(template.category.value, 1.0)
            complexity_weight = distribution.get(template.complexity.value, 1.0)
            language_weight = distribution.get(template.language.value, 1.0)
            
            # 計算總權重
            total_weight = category_weight * complexity_weight * language_weight
            
            # 根據權重重複添加模板
            repeat_count = max(1, int(total_weight * 10))
            weighted_templates.extend([template] * repeat_count)
        
        return weighted_templates
    
    def _generate_single_case(self, template: TestCaseTemplate, index: int) -> GeneratedTestCase:
        """生成單個測試案例"""
        # 替換模板變數
        query = template.template
        expected_entities = {}
        
        for var_name, var_values in template.variables.items():
            if var_values:  # 確保變數值列表不為空
                selected_value = random.choice(var_values)
                query = query.replace(f"{{{var_name}}}", selected_value)
                expected_entities[var_name] = selected_value
        
        # 生成唯一ID
        case_id = f"{template.category.value}_{template.complexity.value}_{index:04d}"
        
        # 創建測試案例
        test_case = GeneratedTestCase(
            id=case_id,
            category=template.category,
            complexity=template.complexity,
            language=template.language,
            query=query,
            expected_intent=template.expected_intent,
            expected_confidence_range=template.expected_confidence_range,
            expected_entities=expected_entities,
            description=template.description,
            tags=template.tags.copy(),
            generation_time=datetime.now(),
            template_id=f"{template.category.value}_{template.complexity.value}"
        )
        
        return test_case
    
    def _print_generation_stats(self) -> None:
        """打印生成統計"""
        print("\n📊 生成統計:")
        for category, count in sorted(self.generation_stats.items()):
            print(f"   {category}: {count} 個案例")
    
    def export_test_cases(self, output_file: str = None, format_type: str = "json") -> str:
        """導出測試案例"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"generated_test_cases_{timestamp}.{format_type}"
        
        print(f"💾 導出測試案例到 {output_file}...")
        
        if format_type.lower() == "json":
            self._export_to_json(output_file)
        elif format_type.lower() == "csv":
            self._export_to_csv(output_file)
        else:
            raise ValueError(f"不支援的格式: {format_type}")
        
        print(f"   ✅ 已導出 {len(self.generated_cases)} 個測試案例")
        return output_file
    
    def _export_to_json(self, output_file: str) -> None:
        """導出為JSON格式"""
        export_data = {
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "total_cases": len(self.generated_cases),
                "categories": list(self.generation_stats.keys()),
                "generation_stats": dict(self.generation_stats)
            },
            "test_cases": []
        }
        
        for case in self.generated_cases:
            case_data = {
                "id": case.id,
                "category": case.category.value,
                "complexity": case.complexity.value,
                "language": case.language.value,
                "query": case.query,
                "expected_intent": case.expected_intent,
                "expected_confidence_range": case.expected_confidence_range,
                "expected_entities": case.expected_entities,
                "description": case.description,
                "tags": case.tags,
                "generation_time": case.generation_time.isoformat(),
                "template_id": case.template_id
            }
            export_data["test_cases"].append(case_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _export_to_csv(self, output_file: str) -> None:
        """導出為CSV格式"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            headers = [
                'id', 'category', 'complexity', 'language', 'query',
                'expected_intent', 'expected_confidence_min', 'expected_confidence_max',
                'description', 'tags', 'generation_time', 'template_id'
            ]
            writer.writerow(headers)
            
            # 寫入數據行
            for case in self.generated_cases:
                row = [
                    case.id,
                    case.category.value,
                    case.complexity.value,
                    case.language.value,
                    case.query,
                    case.expected_intent,
                    case.expected_confidence_range[0],
                    case.expected_confidence_range[1],
                    case.description,
                    ','.join(case.tags),
                    case.generation_time.isoformat(),
                    case.template_id
                ]
                writer.writerow(row)
    
    def generate_balanced_test_suite(self, total_cases: int = 200) -> List[GeneratedTestCase]:
        """生成平衡的測試套件"""
        print(f"⚖️ 生成平衡的測試套件 ({total_cases} 個案例)...")
        
        # 定義平衡分佈
        distribution = {
            # 類別分佈
            TestCaseCategory.BASIC_JOB_SEARCH.value: 0.25,
            TestCaseCategory.ADVANCED_JOB_SEARCH.value: 0.20,
            TestCaseCategory.SKILL_BASED_QUERY.value: 0.15,
            TestCaseCategory.LOCATION_BASED_QUERY.value: 0.10,
            TestCaseCategory.SALARY_BASED_QUERY.value: 0.10,
            TestCaseCategory.CAREER_TRANSITION.value: 0.05,
            TestCaseCategory.REMOTE_WORK.value: 0.05,
            TestCaseCategory.NON_JOB_RELATED.value: 0.05,
            TestCaseCategory.EDGE_CASE.value: 0.03,
            TestCaseCategory.MULTILINGUAL.value: 0.02,
            
            # 複雜度分佈
            TestComplexity.SIMPLE.value: 0.4,
            TestComplexity.MEDIUM.value: 0.35,
            TestComplexity.COMPLEX.value: 0.20,
            TestComplexity.EXTREME.value: 0.05,
            
            # 語言分佈
            LanguageType.CHINESE_TRADITIONAL.value: 0.6,
            LanguageType.ENGLISH.value: 0.3,
            LanguageType.MIXED.value: 0.05,
            LanguageType.JAPANESE.value: 0.025,
            LanguageType.KOREAN.value: 0.025
        }
        
        return self.generate_test_cases(
            num_cases=total_cases,
            distribution=distribution
        )
    
    def generate_stress_test_suite(self, total_cases: int = 500) -> List[GeneratedTestCase]:
        """生成壓力測試套件"""
        print(f"⚡ 生成壓力測試套件 ({total_cases} 個案例)...")
        
        # 重點測試複雜和極端案例
        distribution = {
            TestComplexity.COMPLEX.value: 0.6,
            TestComplexity.EXTREME.value: 0.4,
            TestCaseCategory.EDGE_CASE.value: 0.3,
            TestCaseCategory.ADVERSARIAL.value: 0.2,
            TestCaseCategory.COMPLEX_SCENARIO.value: 0.5
        }
        
        return self.generate_test_cases(
            num_cases=total_cases,
            complexities=[TestComplexity.COMPLEX, TestComplexity.EXTREME],
            distribution=distribution
        )
    
    def generate_multilingual_test_suite(self, total_cases: int = 150) -> List[GeneratedTestCase]:
        """生成多語言測試套件"""
        print(f"🌍 生成多語言測試套件 ({total_cases} 個案例)...")
        
        # 平均分佈各種語言
        distribution = {
            LanguageType.CHINESE_TRADITIONAL.value: 0.3,
            LanguageType.CHINESE_SIMPLIFIED.value: 0.2,
            LanguageType.ENGLISH.value: 0.3,
            LanguageType.JAPANESE.value: 0.1,
            LanguageType.KOREAN.value: 0.05,
            LanguageType.MIXED.value: 0.05
        }
        
        return self.generate_test_cases(
            num_cases=total_cases,
            distribution=distribution
        )
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """獲取生成摘要"""
        summary = {
            "total_templates": len(self.templates),
            "total_generated_cases": len(self.generated_cases),
            "generation_stats": dict(self.generation_stats),
            "categories_coverage": {},
            "complexity_distribution": {},
            "language_distribution": {}
        }
        
        # 計算覆蓋率和分佈
        if self.generated_cases:
            # 類別覆蓋率
            categories = [case.category.value for case in self.generated_cases]
            summary["categories_coverage"] = dict(Counter(categories))
            
            # 複雜度分佈
            complexities = [case.complexity.value for case in self.generated_cases]
            summary["complexity_distribution"] = dict(Counter(complexities))
            
            # 語言分佈
            languages = [case.language.value for case in self.generated_cases]
            summary["language_distribution"] = dict(Counter(languages))
        
        return summary


def main():
    """主函數 - 測試案例生成器入口點"""
    print("🎯 LLM測試案例生成器")
    print("=" * 60)
    
    generator = LLMTestCaseGenerator()
    
    try:
        print("\n選擇生成模式:")
        print("1. 平衡測試套件 (200個案例)")
        print("2. 壓力測試套件 (500個案例)")
        print("3. 多語言測試套件 (150個案例)")
        print("4. 自定義生成")
        print("5. 全套生成 (所有類型)")
        
        choice = input("\n請選擇 (1-5): ").strip()
        
        if choice == "1":
            test_cases = generator.generate_balanced_test_suite()
            output_file = generator.export_test_cases("balanced_test_suite.json")
            
        elif choice == "2":
            test_cases = generator.generate_stress_test_suite()
            output_file = generator.export_test_cases("stress_test_suite.json")
            
        elif choice == "3":
            test_cases = generator.generate_multilingual_test_suite()
            output_file = generator.export_test_cases("multilingual_test_suite.json")
            
        elif choice == "4":
            # 自定義生成
            num_cases = int(input("請輸入要生成的案例數量: "))
            test_cases = generator.generate_test_cases(num_cases)
            output_file = generator.export_test_cases("custom_test_suite.json")
            
        elif choice == "5":
            # 全套生成
            print("\n🚀 生成全套測試案例...")
            
            balanced_cases = generator.generate_balanced_test_suite(200)
            generator.export_test_cases("balanced_test_suite.json")
            
            stress_cases = generator.generate_stress_test_suite(300)
            generator.export_test_cases("stress_test_suite.json")
            
            multilingual_cases = generator.generate_multilingual_test_suite(100)
            generator.export_test_cases("multilingual_test_suite.json")
            
            # 合併所有案例
            all_cases = balanced_cases + stress_cases + multilingual_cases
            generator.generated_cases = all_cases
            output_file = generator.export_test_cases("complete_test_suite.json")
            
            test_cases = all_cases
            
        else:
            print("❌ 無效選擇")
            return
        
        # 顯示生成摘要
        summary = generator.get_generation_summary()
        
        print(f"\n✅ 測試案例生成完成！")
        print(f"   📊 總共生成: {len(test_cases)} 個測試案例")
        print(f"   📁 輸出文件: {output_file}")
        
        print("\n📈 生成摘要:")
        print(f"   模板數量: {summary['total_templates']}")
        print(f"   生成案例: {summary['total_generated_cases']}")
        
        print("\n📊 類別分佈:")
        for category, count in summary['categories_coverage'].items():
            print(f"   {category}: {count} 個")
        
        print("\n🎯 複雜度分佈:")
        for complexity, count in summary['complexity_distribution'].items():
            print(f"   {complexity}: {count} 個")
        
        print("\n🌍 語言分佈:")
        for language, count in summary['language_distribution'].items():
            print(f"   {language}: {count} 個")
        
        # 詢問是否導出CSV格式
        export_csv = input("\n是否同時導出CSV格式？ (y/n): ").strip().lower()
        if export_csv == 'y':
            csv_file = generator.export_test_cases(output_file.replace('.json', '.csv'), 'csv')
            print(f"   📄 CSV文件: {csv_file}")
        
        print("\n🎉 測試案例生成器執行完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 生成過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 生成過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()