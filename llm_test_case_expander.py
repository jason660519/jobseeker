#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例擴充工具
自動生成大量多樣化的測試案例，用於比較不同LLM模型的輸出表現差異

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import random
import itertools
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import uuid
import re


class TestCaseType(Enum):
    """測試案例類型"""
    BASIC_SEARCH = "basic_search"  # 基礎搜尋
    ADVANCED_SEARCH = "advanced_search"  # 進階搜尋
    SKILL_FOCUSED = "skill_focused"  # 技能導向
    LOCATION_FOCUSED = "location_focused"  # 地點導向
    SALARY_FOCUSED = "salary_focused"  # 薪資導向
    CAREER_TRANSITION = "career_transition"  # 職涯轉換
    REMOTE_WORK = "remote_work"  # 遠程工作
    INDUSTRY_SPECIFIC = "industry_specific"  # 行業特定
    EXPERIENCE_LEVEL = "experience_level"  # 經驗等級
    COMPANY_SPECIFIC = "company_specific"  # 公司特定
    EDGE_CASE = "edge_case"  # 邊界案例
    MULTILINGUAL = "multilingual"  # 多語言
    AMBIGUOUS = "ambiguous"  # 模糊查詢
    COMPLEX_SCENARIO = "complex_scenario"  # 複雜場景
    ADVERSARIAL = "adversarial"  # 對抗性測試


class DifficultyLevel(Enum):
    """難度等級"""
    TRIVIAL = "trivial"  # 極簡單
    EASY = "easy"  # 簡單
    MEDIUM = "medium"  # 中等
    HARD = "hard"  # 困難
    EXPERT = "expert"  # 專家級
    EXTREME = "extreme"  # 極端


class ExpansionStrategy(Enum):
    """擴充策略"""
    TEMPLATE_VARIATION = "template_variation"  # 模板變化
    PARAMETER_COMBINATION = "parameter_combination"  # 參數組合
    SEMANTIC_EXPANSION = "semantic_expansion"  # 語義擴展
    SYNTACTIC_VARIATION = "syntactic_variation"  # 語法變化
    DOMAIN_TRANSFER = "domain_transfer"  # 領域遷移
    NOISE_INJECTION = "noise_injection"  # 噪聲注入
    COMPLEXITY_SCALING = "complexity_scaling"  # 複雜度縮放
    MULTILINGUAL_TRANSLATION = "multilingual_translation"  # 多語言翻譯


@dataclass
class TestCaseTemplate:
    """測試案例模板"""
    template_id: str
    category: TestCaseType
    difficulty: DifficultyLevel
    template_text: str
    parameters: List[str]
    expected_intent: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    variations: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpandedTestCase:
    """擴充的測試案例"""
    test_case_id: str
    original_template_id: str
    expansion_strategy: ExpansionStrategy
    category: TestCaseType
    difficulty: DifficultyLevel
    query: str
    expected_intent: str
    expected_entities: Dict[str, Any]
    metadata: Dict[str, Any]
    language: str = "zh-TW"
    complexity_score: float = 0.5
    uniqueness_score: float = 0.5


@dataclass
class ExpansionConfig:
    """擴充配置"""
    target_count: int = 1000
    difficulty_distribution: Dict[DifficultyLevel, float] = field(default_factory=lambda: {
        DifficultyLevel.EASY: 0.3,
        DifficultyLevel.MEDIUM: 0.4,
        DifficultyLevel.HARD: 0.2,
        DifficultyLevel.EXPERT: 0.08,
        DifficultyLevel.EXTREME: 0.02
    })
    category_distribution: Dict[TestCaseType, float] = field(default_factory=dict)
    language_distribution: Dict[str, float] = field(default_factory=lambda: {
        "zh-TW": 0.4,
        "zh-CN": 0.2,
        "en-US": 0.3,
        "ja-JP": 0.05,
        "ko-KR": 0.05
    })
    expansion_strategies: List[ExpansionStrategy] = field(default_factory=lambda: list(ExpansionStrategy))
    ensure_diversity: bool = True
    max_similarity_threshold: float = 0.8


class LLMTestCaseExpander:
    """LLM測試案例擴充器"""
    
    def __init__(self):
        """初始化擴充器"""
        self.templates = []
        self.expanded_cases = []
        self.entity_pools = self._load_entity_pools()
        self.language_patterns = self._load_language_patterns()
        self.complexity_factors = self._load_complexity_factors()
        self.generated_queries = set()  # 用於去重
        
    def _load_entity_pools(self) -> Dict[str, List[str]]:
        """載入實體池"""
        return {
            "job_titles": [
                "軟體工程師", "資料科學家", "產品經理", "UI/UX設計師", "DevOps工程師",
                "前端工程師", "後端工程師", "全端工程師", "機器學習工程師", "雲端架構師",
                "網路安全專家", "數據分析師", "專案經理", "技術主管", "系統管理員",
                "品質保證工程師", "移動應用開發者", "區塊鏈開發者", "AI研究員", "技術寫手",
                "業務分析師", "數位行銷專員", "客戶成功經理", "銷售代表", "人力資源專員",
                "財務分析師", "會計師", "法務專員", "營運經理", "供應鏈管理師"
            ],
            "skills": [
                "Python", "JavaScript", "Java", "C++", "React", "Vue.js", "Angular",
                "Node.js", "Django", "Flask", "Spring Boot", "Docker", "Kubernetes",
                "AWS", "Azure", "GCP", "TensorFlow", "PyTorch", "Scikit-learn",
                "SQL", "MongoDB", "PostgreSQL", "Redis", "Elasticsearch",
                "Git", "Jenkins", "CI/CD", "Agile", "Scrum", "機器學習", "深度學習",
                "自然語言處理", "計算機視覺", "數據挖掘", "統計分析", "A/B測試"
            ],
            "locations": [
                "台北", "新北", "桃園", "台中", "台南", "高雄", "新竹", "基隆",
                "遠端工作", "混合辦公", "彈性地點", "全台灣", "大台北地區",
                "竹科", "南科", "中科", "內湖科技園區", "信義區", "松山區",
                "板橋", "林口", "淡水", "中壢", "新竹市", "新竹縣"
            ],
            "companies": [
                "台積電", "聯發科", "鴻海", "廣達", "華碩", "宏碁", "研華",
                "聯電", "日月光", "緯創", "仁寶", "和碩", "英業達", "神達",
                "趨勢科技", "雷虎科技", "創意電子", "聯詠科技", "瑞昱半導體",
                "Google", "Microsoft", "Apple", "Amazon", "Meta", "Netflix",
                "Uber", "Airbnb", "Spotify", "Tesla", "NVIDIA", "Intel"
            ],
            "industries": [
                "科技業", "金融業", "製造業", "零售業", "醫療保健", "教育",
                "媒體娛樂", "電商", "遊戲", "新創", "顧問", "政府機關",
                "非營利組織", "生技醫藥", "能源", "交通運輸", "房地產",
                "食品飲料", "時尚服飾", "旅遊觀光", "電信", "半導體"
            ],
            "salary_ranges": [
                "30-50萬", "50-80萬", "80-120萬", "120-200萬", "200萬以上",
                "面議", "依經驗面議", "具競爭力", "優於市場行情", "股票選擇權"
            ],
            "experience_levels": [
                "新鮮人", "1-3年", "3-5年", "5-8年", "8年以上", "資深",
                "主管級", "總監級", "VP級", "C-level", "實習生", "兼職"
            ]
        }
    
    def _load_language_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """載入語言模式"""
        return {
            "zh-TW": {
                "question_starters": ["我想找", "請幫我找", "有沒有", "哪裡有", "推薦", "尋找"],
                "connectors": ["的", "在", "於", "位於", "關於", "相關的"],
                "modifiers": ["優秀的", "資深的", "有經驗的", "專業的", "頂尖的", "新手"],
                "endings": ["工作", "職位", "機會", "職缺", "崗位", "工作機會"]
            },
            "zh-CN": {
                "question_starters": ["我想找", "请帮我找", "有没有", "哪里有", "推荐", "寻找"],
                "connectors": ["的", "在", "于", "位于", "关于", "相关的"],
                "modifiers": ["优秀的", "资深的", "有经验的", "专业的", "顶尖的", "新手"],
                "endings": ["工作", "职位", "机会", "职缺", "岗位", "工作机会"]
            },
            "en-US": {
                "question_starters": ["I'm looking for", "Find me", "Are there any", "Where can I find", "Recommend", "Search for"],
                "connectors": ["in", "at", "for", "with", "related to", "involving"],
                "modifiers": ["excellent", "senior", "experienced", "professional", "top", "junior"],
                "endings": ["jobs", "positions", "opportunities", "roles", "careers", "openings"]
            },
            "ja-JP": {
                "question_starters": ["探しています", "見つけて", "ありますか", "どこで", "おすすめ", "検索"],
                "connectors": ["の", "で", "に", "における", "関連の", "に関する"],
                "modifiers": ["優秀な", "シニア", "経験豊富な", "プロの", "トップ", "ジュニア"],
                "endings": ["仕事", "ポジション", "機会", "役職", "キャリア", "求人"]
            },
            "ko-KR": {
                "question_starters": ["찾고 있습니다", "찾아주세요", "있나요", "어디서", "추천", "검색"],
                "connectors": ["의", "에서", "에", "관련", "에 대한", "와 관련된"],
                "modifiers": ["우수한", "시니어", "경험있는", "전문", "최고의", "주니어"],
                "endings": ["일자리", "포지션", "기회", "역할", "커리어", "채용"]
            }
        }
    
    def _load_complexity_factors(self) -> Dict[str, float]:
        """載入複雜度因子"""
        return {
            "multiple_skills": 1.2,
            "multiple_locations": 1.1,
            "salary_negotiation": 1.3,
            "remote_hybrid": 1.2,
            "career_change": 1.4,
            "industry_specific": 1.1,
            "company_culture": 1.2,
            "work_life_balance": 1.1,
            "growth_opportunity": 1.2,
            "team_size": 1.1,
            "technology_stack": 1.3,
            "certification_required": 1.2,
            "language_requirement": 1.1,
            "travel_requirement": 1.1,
            "security_clearance": 1.4
        }
    
    def load_base_templates(self, templates_file: str = None) -> None:
        """載入基礎模板"""
        if templates_file and Path(templates_file).exists():
            with open(templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.templates = [TestCaseTemplate(**template) for template in data]
        else:
            # 創建預設模板
            self._create_default_templates()
        
        print(f"📚 載入了 {len(self.templates)} 個基礎模板")
    
    def _create_default_templates(self) -> None:
        """創建預設模板"""
        default_templates = [
            # 基礎搜尋模板
            TestCaseTemplate(
                template_id="basic_001",
                category=TestCaseType.BASIC_SEARCH,
                difficulty=DifficultyLevel.EASY,
                template_text="我想找{job_title}的工作",
                parameters=["job_title"],
                expected_intent="job_search",
                metadata={"requires_entities": ["job_title"]}
            ),
            TestCaseTemplate(
                template_id="basic_002",
                category=TestCaseType.BASIC_SEARCH,
                difficulty=DifficultyLevel.EASY,
                template_text="{location}有什麼{job_title}職缺",
                parameters=["location", "job_title"],
                expected_intent="job_search",
                metadata={"requires_entities": ["location", "job_title"]}
            ),
            
            # 技能導向模板
            TestCaseTemplate(
                template_id="skill_001",
                category=TestCaseType.SKILL_FOCUSED,
                difficulty=DifficultyLevel.MEDIUM,
                template_text="需要{skill1}和{skill2}技能的{job_title}工作",
                parameters=["skill1", "skill2", "job_title"],
                expected_intent="job_search",
                metadata={"requires_entities": ["skills", "job_title"]}
            ),
            
            # 薪資導向模板
            TestCaseTemplate(
                template_id="salary_001",
                category=TestCaseType.SALARY_FOCUSED,
                difficulty=DifficultyLevel.MEDIUM,
                template_text="年薪{salary_range}的{job_title}職位",
                parameters=["salary_range", "job_title"],
                expected_intent="job_search",
                metadata={"requires_entities": ["salary", "job_title"]}
            ),
            
            # 遠程工作模板
            TestCaseTemplate(
                template_id="remote_001",
                category=TestCaseType.REMOTE_WORK,
                difficulty=DifficultyLevel.MEDIUM,
                template_text="遠端工作的{job_title}機會",
                parameters=["job_title"],
                expected_intent="job_search",
                metadata={"requires_entities": ["job_title", "work_type"]}
            ),
            
            # 複雜場景模板
            TestCaseTemplate(
                template_id="complex_001",
                category=TestCaseType.COMPLEX_SCENARIO,
                difficulty=DifficultyLevel.HARD,
                template_text="我是{experience_level}，想在{location}找{job_title}工作，要求{skill1}、{skill2}技能，年薪{salary_range}",
                parameters=["experience_level", "location", "job_title", "skill1", "skill2", "salary_range"],
                expected_intent="job_search",
                metadata={"requires_entities": ["experience", "location", "job_title", "skills", "salary"]}
            ),
            
            # 邊界案例模板
            TestCaseTemplate(
                template_id="edge_001",
                category=TestCaseType.EDGE_CASE,
                difficulty=DifficultyLevel.EXPERT,
                template_text="找一個不存在的職位",
                parameters=[],
                expected_intent="invalid_query",
                metadata={"is_negative_case": True}
            ),
            
            # 模糊查詢模板
            TestCaseTemplate(
                template_id="ambiguous_001",
                category=TestCaseType.AMBIGUOUS,
                difficulty=DifficultyLevel.HARD,
                template_text="我想要一個好工作",
                parameters=[],
                expected_intent="job_search",
                metadata={"ambiguity_level": "high"}
            )
        ]
        
        self.templates = default_templates
    
    def expand_test_cases(self, config: ExpansionConfig) -> List[ExpandedTestCase]:
        """擴充測試案例"""
        print(f"🚀 開始擴充測試案例，目標數量: {config.target_count}")
        
        self.expanded_cases = []
        self.generated_queries = set()
        
        # 計算每個類別和難度的目標數量
        category_targets = self._calculate_category_targets(config)
        difficulty_targets = self._calculate_difficulty_targets(config)
        
        # 按策略擴充
        for strategy in config.expansion_strategies:
            strategy_cases = self._expand_by_strategy(strategy, config, category_targets, difficulty_targets)
            self.expanded_cases.extend(strategy_cases)
            
            print(f"   ✅ {strategy.value} 策略生成了 {len(strategy_cases)} 個案例")
        
        # 去重和質量控制
        if config.ensure_diversity:
            self._ensure_diversity(config.max_similarity_threshold)
        
        # 調整到目標數量
        self._adjust_to_target_count(config.target_count)
        
        print(f"   🎯 最終生成了 {len(self.expanded_cases)} 個測試案例")
        return self.expanded_cases
    
    def _calculate_category_targets(self, config: ExpansionConfig) -> Dict[TestCaseType, int]:
        """計算類別目標數量"""
        if not config.category_distribution:
            # 均勻分佈
            categories = list(TestCaseType)
            target_per_category = config.target_count // len(categories)
            return {cat: target_per_category for cat in categories}
        
        targets = {}
        for category, ratio in config.category_distribution.items():
            targets[category] = int(config.target_count * ratio)
        
        return targets
    
    def _calculate_difficulty_targets(self, config: ExpansionConfig) -> Dict[DifficultyLevel, int]:
        """計算難度目標數量"""
        targets = {}
        for difficulty, ratio in config.difficulty_distribution.items():
            targets[difficulty] = int(config.target_count * ratio)
        
        return targets
    
    def _expand_by_strategy(self, strategy: ExpansionStrategy, config: ExpansionConfig,
                          category_targets: Dict[TestCaseType, int],
                          difficulty_targets: Dict[DifficultyLevel, int]) -> List[ExpandedTestCase]:
        """按策略擴充"""
        cases = []
        
        if strategy == ExpansionStrategy.TEMPLATE_VARIATION:
            cases = self._expand_template_variation(config, category_targets)
        elif strategy == ExpansionStrategy.PARAMETER_COMBINATION:
            cases = self._expand_parameter_combination(config, category_targets)
        elif strategy == ExpansionStrategy.SEMANTIC_EXPANSION:
            cases = self._expand_semantic_expansion(config, category_targets)
        elif strategy == ExpansionStrategy.SYNTACTIC_VARIATION:
            cases = self._expand_syntactic_variation(config, category_targets)
        elif strategy == ExpansionStrategy.DOMAIN_TRANSFER:
            cases = self._expand_domain_transfer(config, category_targets)
        elif strategy == ExpansionStrategy.NOISE_INJECTION:
            cases = self._expand_noise_injection(config, category_targets)
        elif strategy == ExpansionStrategy.COMPLEXITY_SCALING:
            cases = self._expand_complexity_scaling(config, difficulty_targets)
        elif strategy == ExpansionStrategy.MULTILINGUAL_TRANSLATION:
            cases = self._expand_multilingual_translation(config)
        
        return cases
    
    def _expand_template_variation(self, config: ExpansionConfig,
                                 category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """模板變化擴充"""
        cases = []
        
        for template in self.templates:
            target_count = category_targets.get(template.category, 10)
            
            for i in range(target_count):
                # 填充參數
                filled_template = self._fill_template_parameters(template)
                
                if filled_template and filled_template not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.TEMPLATE_VARIATION,
                        category=template.category,
                        difficulty=template.difficulty,
                        query=filled_template,
                        expected_intent=template.expected_intent,
                        expected_entities=self._extract_expected_entities(filled_template, template),
                        metadata=template.metadata.copy(),
                        complexity_score=self._calculate_complexity_score(filled_template, template)
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(filled_template)
        
        return cases
    
    def _expand_parameter_combination(self, config: ExpansionConfig,
                                    category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """參數組合擴充"""
        cases = []
        
        for template in self.templates:
            if len(template.parameters) < 2:
                continue
            
            target_count = min(category_targets.get(template.category, 10), 50)
            
            # 生成參數組合
            param_combinations = self._generate_parameter_combinations(template, target_count)
            
            for combination in param_combinations:
                filled_template = self._fill_template_with_combination(template, combination)
                
                if filled_template and filled_template not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.PARAMETER_COMBINATION,
                        category=template.category,
                        difficulty=template.difficulty,
                        query=filled_template,
                        expected_intent=template.expected_intent,
                        expected_entities=combination,
                        metadata=template.metadata.copy(),
                        complexity_score=self._calculate_complexity_score(filled_template, template)
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(filled_template)
        
        return cases
    
    def _expand_semantic_expansion(self, config: ExpansionConfig,
                                 category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """語義擴展"""
        cases = []
        
        # 創建語義相似的變體
        semantic_variations = {
            "工作": ["職位", "職缺", "機會", "崗位", "工作機會", "職業"],
            "找": ["尋找", "搜尋", "查找", "物色", "尋求", "探索"],
            "需要": ["要求", "必須", "希望", "期望", "想要", "渴望"],
            "經驗": ["資歷", "背景", "履歷", "工作經驗", "專業經驗", "實務經驗"]
        }
        
        for template in self.templates:
            target_count = category_targets.get(template.category, 5)
            
            for i in range(target_count):
                # 應用語義變化
                varied_template = self._apply_semantic_variations(template.template_text, semantic_variations)
                filled_template = self._fill_template_parameters_from_text(varied_template, template)
                
                if filled_template and filled_template not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.SEMANTIC_EXPANSION,
                        category=template.category,
                        difficulty=template.difficulty,
                        query=filled_template,
                        expected_intent=template.expected_intent,
                        expected_entities=self._extract_expected_entities(filled_template, template),
                        metadata=template.metadata.copy(),
                        complexity_score=self._calculate_complexity_score(filled_template, template)
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(filled_template)
        
        return cases
    
    def _expand_syntactic_variation(self, config: ExpansionConfig,
                                  category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """語法變化擴充"""
        cases = []
        
        syntactic_patterns = [
            lambda x: f"請幫我{x}",
            lambda x: f"我想要{x}",
            lambda x: f"能否推薦{x}",
            lambda x: f"有沒有{x}",
            lambda x: f"哪裡可以找到{x}",
            lambda x: f"我正在尋找{x}"
        ]
        
        for template in self.templates:
            target_count = category_targets.get(template.category, 3)
            
            for pattern in syntactic_patterns[:target_count]:
                # 提取核心內容
                core_content = self._extract_core_content(template.template_text)
                varied_query = pattern(core_content)
                filled_template = self._fill_template_parameters_from_text(varied_query, template)
                
                if filled_template and filled_template not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.SYNTACTIC_VARIATION,
                        category=template.category,
                        difficulty=template.difficulty,
                        query=filled_template,
                        expected_intent=template.expected_intent,
                        expected_entities=self._extract_expected_entities(filled_template, template),
                        metadata=template.metadata.copy(),
                        complexity_score=self._calculate_complexity_score(filled_template, template)
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(filled_template)
        
        return cases
    
    def _expand_domain_transfer(self, config: ExpansionConfig,
                              category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """領域遷移擴充"""
        cases = []
        
        # 跨行業遷移
        industry_mappings = {
            "軟體工程師": ["遊戲開發者", "區塊鏈開發者", "AI工程師"],
            "產品經理": ["專案經理", "營運經理", "策略經理"],
            "設計師": ["UI設計師", "UX設計師", "視覺設計師"]
        }
        
        for template in self.templates:
            if template.category in [TestCaseType.BASIC_SEARCH, TestCaseType.SKILL_FOCUSED]:
                target_count = category_targets.get(TestCaseType.INDUSTRY_SPECIFIC, 5)
                
                for i in range(target_count):
                    # 應用領域遷移
                    transferred_template = self._apply_domain_transfer(template, industry_mappings)
                    
                    if transferred_template and transferred_template not in self.generated_queries:
                        case = ExpandedTestCase(
                            test_case_id=str(uuid.uuid4()),
                            original_template_id=template.template_id,
                            expansion_strategy=ExpansionStrategy.DOMAIN_TRANSFER,
                            category=TestCaseType.INDUSTRY_SPECIFIC,
                            difficulty=template.difficulty,
                            query=transferred_template,
                            expected_intent=template.expected_intent,
                            expected_entities=self._extract_expected_entities(transferred_template, template),
                            metadata=template.metadata.copy(),
                            complexity_score=self._calculate_complexity_score(transferred_template, template)
                        )
                        
                        cases.append(case)
                        self.generated_queries.add(transferred_template)
        
        return cases
    
    def _expand_noise_injection(self, config: ExpansionConfig,
                              category_targets: Dict[TestCaseType, int]) -> List[ExpandedTestCase]:
        """噪聲注入擴充"""
        cases = []
        
        noise_types = [
            "typos",  # 拼寫錯誤
            "extra_words",  # 多餘詞語
            "informal_language",  # 非正式語言
            "abbreviations",  # 縮寫
            "punctuation_errors"  # 標點錯誤
        ]
        
        for template in self.templates:
            target_count = category_targets.get(TestCaseType.EDGE_CASE, 2)
            
            for noise_type in noise_types[:target_count]:
                noisy_template = self._inject_noise(template, noise_type)
                
                if noisy_template and noisy_template not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.NOISE_INJECTION,
                        category=TestCaseType.EDGE_CASE,
                        difficulty=DifficultyLevel.HARD,
                        query=noisy_template,
                        expected_intent=template.expected_intent,
                        expected_entities=self._extract_expected_entities(noisy_template, template),
                        metadata={**template.metadata, "noise_type": noise_type},
                        complexity_score=self._calculate_complexity_score(noisy_template, template) * 1.3
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(noisy_template)
        
        return cases
    
    def _expand_complexity_scaling(self, config: ExpansionConfig,
                                 difficulty_targets: Dict[DifficultyLevel, int]) -> List[ExpandedTestCase]:
        """複雜度縮放擴充"""
        cases = []
        
        for target_difficulty, target_count in difficulty_targets.items():
            if target_difficulty in [DifficultyLevel.EXPERT, DifficultyLevel.EXTREME]:
                # 生成高複雜度案例
                complex_cases = self._generate_complex_cases(target_difficulty, target_count)
                cases.extend(complex_cases)
        
        return cases
    
    def _expand_multilingual_translation(self, config: ExpansionConfig) -> List[ExpandedTestCase]:
        """多語言翻譯擴充"""
        cases = []
        
        for language, ratio in config.language_distribution.items():
            if language == "zh-TW":
                continue  # 跳過原始語言
            
            target_count = int(config.target_count * ratio * 0.1)  # 限制多語言案例數量
            
            for template in self.templates[:target_count]:
                translated_query = self._translate_template(template, language)
                
                if translated_query and translated_query not in self.generated_queries:
                    case = ExpandedTestCase(
                        test_case_id=str(uuid.uuid4()),
                        original_template_id=template.template_id,
                        expansion_strategy=ExpansionStrategy.MULTILINGUAL_TRANSLATION,
                        category=TestCaseType.MULTILINGUAL,
                        difficulty=template.difficulty,
                        query=translated_query,
                        expected_intent=template.expected_intent,
                        expected_entities=self._extract_expected_entities(translated_query, template),
                        metadata={**template.metadata, "original_language": "zh-TW"},
                        language=language,
                        complexity_score=self._calculate_complexity_score(translated_query, template)
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(translated_query)
        
        return cases
    
    def _fill_template_parameters(self, template: TestCaseTemplate) -> str:
        """填充模板參數"""
        text = template.template_text
        
        for param in template.parameters:
            if param in self.entity_pools:
                value = random.choice(self.entity_pools[param])
                text = text.replace(f"{{{param}}}", value)
            elif param.endswith("1") or param.endswith("2"):
                # 處理編號參數
                base_param = param[:-1]
                if base_param in self.entity_pools:
                    value = random.choice(self.entity_pools[base_param])
                    text = text.replace(f"{{{param}}}", value)
        
        return text if "{" not in text else None
    
    def _generate_parameter_combinations(self, template: TestCaseTemplate, count: int) -> List[Dict[str, str]]:
        """生成參數組合"""
        combinations = []
        
        for _ in range(count):
            combination = {}
            for param in template.parameters:
                if param in self.entity_pools:
                    combination[param] = random.choice(self.entity_pools[param])
                elif param.endswith("1") or param.endswith("2"):
                    base_param = param[:-1]
                    if base_param in self.entity_pools:
                        combination[param] = random.choice(self.entity_pools[base_param])
            
            if combination:
                combinations.append(combination)
        
        return combinations
    
    def _fill_template_with_combination(self, template: TestCaseTemplate, combination: Dict[str, str]) -> str:
        """用組合填充模板"""
        text = template.template_text
        
        for param, value in combination.items():
            text = text.replace(f"{{{param}}}", value)
        
        return text if "{" not in text else None
    
    def _apply_semantic_variations(self, text: str, variations: Dict[str, List[str]]) -> str:
        """應用語義變化"""
        for original, alternatives in variations.items():
            if original in text:
                alternative = random.choice(alternatives)
                text = text.replace(original, alternative, 1)
        
        return text
    
    def _fill_template_parameters_from_text(self, text: str, template: TestCaseTemplate) -> str:
        """從文本填充模板參數"""
        for param in template.parameters:
            if f"{{{param}}}" in text:
                if param in self.entity_pools:
                    value = random.choice(self.entity_pools[param])
                    text = text.replace(f"{{{param}}}", value)
        
        return text if "{" not in text else text
    
    def _extract_core_content(self, template_text: str) -> str:
        """提取核心內容"""
        # 移除常見的起始詞
        core = template_text
        prefixes = ["我想找", "請幫我找", "有沒有", "哪裡有"]
        
        for prefix in prefixes:
            if core.startswith(prefix):
                core = core[len(prefix):]
                break
        
        return core.strip()
    
    def _apply_domain_transfer(self, template: TestCaseTemplate, mappings: Dict[str, List[str]]) -> str:
        """應用領域遷移"""
        text = self._fill_template_parameters(template)
        
        if not text:
            return None
        
        # 替換職位名稱
        for original, alternatives in mappings.items():
            if original in text:
                alternative = random.choice(alternatives)
                text = text.replace(original, alternative)
                break
        
        return text
    
    def _inject_noise(self, template: TestCaseTemplate, noise_type: str) -> str:
        """注入噪聲"""
        text = self._fill_template_parameters(template)
        
        if not text:
            return None
        
        if noise_type == "typos":
            # 隨機替換字符
            if len(text) > 5:
                pos = random.randint(1, len(text) - 2)
                text = text[:pos] + random.choice("abcdefg") + text[pos + 1:]
        
        elif noise_type == "extra_words":
            # 添加多餘詞語
            extra_words = ["呃", "嗯", "那個", "就是", "然後"]
            word = random.choice(extra_words)
            pos = random.randint(0, len(text))
            text = text[:pos] + word + text[pos:]
        
        elif noise_type == "informal_language":
            # 非正式語言
            text = text.replace("工作", "打工")
            text = text.replace("職位", "位子")
        
        elif noise_type == "abbreviations":
            # 縮寫
            text = text.replace("軟體工程師", "軟工")
            text = text.replace("產品經理", "PM")
        
        elif noise_type == "punctuation_errors":
            # 標點錯誤
            text = text.replace("，", "")
            text = text.replace("。", "")
        
        return text
    
    def _generate_complex_cases(self, difficulty: DifficultyLevel, count: int) -> List[ExpandedTestCase]:
        """生成複雜案例"""
        cases = []
        
        complex_templates = [
            "我是{experience_level}的{job_title}，想轉職到{industry}，需要學習{skill1}和{skill2}，希望在{location}找到年薪{salary_range}的{work_type}工作",
            "尋找{company}或類似公司的{job_title}職位，要求{skill1}、{skill2}、{skill3}技能，{experience_level}經驗，可接受{location}或遠端工作",
            "我想找一個結合{skill1}和{skill2}的創新職位，最好是在{industry}領域的新創公司，地點不限但希望有彈性工作時間"
        ]
        
        for i in range(count):
            template_text = random.choice(complex_templates)
            
            # 填充所有參數
            filled_text = template_text
            for param_type, values in self.entity_pools.items():
                pattern = f"{{{param_type}}}"
                if pattern in filled_text:
                    filled_text = filled_text.replace(pattern, random.choice(values))
                
                # 處理編號參數
                for i in range(1, 4):
                    pattern = f"{{{param_type}{i}}}"
                    if pattern in filled_text:
                        filled_text = filled_text.replace(pattern, random.choice(values))
            
            if filled_text and "{" not in filled_text and filled_text not in self.generated_queries:
                case = ExpandedTestCase(
                    test_case_id=str(uuid.uuid4()),
                    original_template_id="complex_generated",
                    expansion_strategy=ExpansionStrategy.COMPLEXITY_SCALING,
                    category=TestCaseType.COMPLEX_SCENARIO,
                    difficulty=difficulty,
                    query=filled_text,
                    expected_intent="job_search",
                    expected_entities=self._extract_entities_from_text(filled_text),
                    metadata={"complexity_level": difficulty.value},
                    complexity_score=0.8 if difficulty == DifficultyLevel.EXPERT else 0.9
                )
                
                cases.append(case)
                self.generated_queries.add(filled_text)
        
        return cases
    
    def _translate_template(self, template: TestCaseTemplate, target_language: str) -> str:
        """翻譯模板"""
        if target_language not in self.language_patterns:
            return None
        
        patterns = self.language_patterns[target_language]
        
        # 簡化的翻譯邏輯
        if target_language == "en-US":
            # 英文翻譯
            starter = random.choice(patterns["question_starters"])
            job_title = random.choice(self.entity_pools["job_titles"])
            # 簡化翻譯
            return f"{starter} {job_title} {random.choice(patterns['endings'])}"
        
        elif target_language == "ja-JP":
            # 日文翻譯
            starter = random.choice(patterns["question_starters"])
            job_title = random.choice(self.entity_pools["job_titles"])
            return f"{job_title}{random.choice(patterns['connectors'])}{random.choice(patterns['endings'])}{starter}"
        
        else:
            # 其他語言使用相似結構
            filled_template = self._fill_template_parameters(template)
            return filled_template
    
    def _extract_expected_entities(self, query: str, template: TestCaseTemplate) -> Dict[str, Any]:
        """提取預期實體"""
        entities = {}
        
        # 基於模板元數據提取實體
        if "requires_entities" in template.metadata:
            for entity_type in template.metadata["requires_entities"]:
                entities[entity_type] = self._extract_entity_from_query(query, entity_type)
        
        return entities
    
    def _extract_entity_from_query(self, query: str, entity_type: str) -> List[str]:
        """從查詢中提取實體"""
        entities = []
        
        if entity_type in self.entity_pools:
            for entity in self.entity_pools[entity_type]:
                if entity in query:
                    entities.append(entity)
        
        return entities
    
    def _extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """從文本中提取實體"""
        entities = {}
        
        for entity_type, entity_list in self.entity_pools.items():
            found_entities = []
            for entity in entity_list:
                if entity in text:
                    found_entities.append(entity)
            
            if found_entities:
                entities[entity_type] = found_entities
        
        return entities
    
    def _calculate_complexity_score(self, query: str, template: TestCaseTemplate) -> float:
        """計算複雜度分數"""
        base_score = 0.5
        
        # 基於難度等級
        difficulty_scores = {
            DifficultyLevel.TRIVIAL: 0.1,
            DifficultyLevel.EASY: 0.3,
            DifficultyLevel.MEDIUM: 0.5,
            DifficultyLevel.HARD: 0.7,
            DifficultyLevel.EXPERT: 0.9,
            DifficultyLevel.EXTREME: 1.0
        }
        
        base_score = difficulty_scores.get(template.difficulty, 0.5)
        
        # 基於查詢長度
        length_factor = min(len(query) / 100, 0.3)
        
        # 基於實體數量
        entity_count = len(self._extract_entities_from_text(query))
        entity_factor = min(entity_count * 0.1, 0.2)
        
        # 基於複雜度因子
        complexity_factor = 0
        for factor, weight in self.complexity_factors.items():
            if any(keyword in query for keyword in factor.split("_")):
                complexity_factor += weight * 0.1
        
        total_score = base_score + length_factor + entity_factor + complexity_factor
        return min(total_score, 1.0)
    
    def _ensure_diversity(self, similarity_threshold: float) -> None:
        """確保多樣性"""
        print("🔍 確保測試案例多樣性...")
        
        # 簡化的相似度檢查
        unique_cases = []
        seen_queries = set()
        
        for case in self.expanded_cases:
            # 基本去重
            if case.query not in seen_queries:
                unique_cases.append(case)
                seen_queries.add(case.query)
        
        removed_count = len(self.expanded_cases) - len(unique_cases)
        self.expanded_cases = unique_cases
        
        if removed_count > 0:
            print(f"   🗑️ 移除了 {removed_count} 個重複案例")
    
    def _adjust_to_target_count(self, target_count: int) -> None:
        """調整到目標數量"""
        current_count = len(self.expanded_cases)
        
        if current_count > target_count:
            # 隨機採樣到目標數量
            self.expanded_cases = random.sample(self.expanded_cases, target_count)
            print(f"   ✂️ 隨機採樣到目標數量 {target_count}")
        
        elif current_count < target_count:
            # 需要生成更多案例
            needed = target_count - current_count
            additional_cases = self._generate_additional_cases(needed)
            self.expanded_cases.extend(additional_cases)
            print(f"   ➕ 額外生成了 {len(additional_cases)} 個案例")
    
    def _generate_additional_cases(self, count: int) -> List[ExpandedTestCase]:
        """生成額外案例"""
        additional_cases = []
        
        # 使用簡單模板快速生成
        simple_templates = [
            "找{job_title}工作",
            "{location}的{job_title}職位",
            "需要{skill1}技能的工作",
            "年薪{salary_range}的職位"
        ]
        
        for i in range(count):
            template_text = random.choice(simple_templates)
            
            # 填充參數
            filled_text = template_text
            for param_type, values in self.entity_pools.items():
                pattern = f"{{{param_type}}}"
                if pattern in filled_text:
                    filled_text = filled_text.replace(pattern, random.choice(values))
                
                # 處理編號參數
                for j in range(1, 4):
                    pattern = f"{{{param_type}{j}}}"
                    if pattern in filled_text:
                        filled_text = filled_text.replace(pattern, random.choice(values))
            
            if filled_text and "{" not in filled_text and filled_text not in self.generated_queries:
                case = ExpandedTestCase(
                    test_case_id=str(uuid.uuid4()),
                    original_template_id="additional_generated",
                    expansion_strategy=ExpansionStrategy.TEMPLATE_VARIATION,
                    category=TestCaseType.BASIC_SEARCH,
                    difficulty=DifficultyLevel.EASY,
                    query=filled_text,
                    expected_intent="job_search",
                    expected_entities=self._extract_entities_from_text(filled_text),
                    metadata={"generated_type": "additional"},
                    complexity_score=0.3
                )
                
                additional_cases.append(case)
                self.generated_queries.add(filled_text)
        
        return additional_cases
    
    def export_test_cases(self, output_file: str, format_type: str = "json") -> None:
        """導出測試案例"""
        print(f"💾 導出測試案例到 {output_file}...")
        
        if format_type == "json":
            self._export_json(output_file)
        elif format_type == "csv":
            self._export_csv(output_file)
        else:
            raise ValueError(f"不支持的格式: {format_type}")
        
        print(f"   ✅ 成功導出 {len(self.expanded_cases)} 個測試案例")
    
    def _export_json(self, output_file: str) -> None:
        """導出JSON格式"""
        data = {
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "total_cases": len(self.expanded_cases),
                "expansion_strategies": list(set(case.expansion_strategy.value for case in self.expanded_cases)),
                "categories": list(set(case.category.value for case in self.expanded_cases)),
                "difficulties": list(set(case.difficulty.value for case in self.expanded_cases)),
                "languages": list(set(case.language for case in self.expanded_cases))
            },
            "test_cases": [
                {
                    "test_case_id": case.test_case_id,
                    "original_template_id": case.original_template_id,
                    "expansion_strategy": case.expansion_strategy.value,
                    "category": case.category.value,
                    "difficulty": case.difficulty.value,
                    "query": case.query,
                    "expected_intent": case.expected_intent,
                    "expected_entities": case.expected_entities,
                    "metadata": case.metadata,
                    "language": case.language,
                    "complexity_score": case.complexity_score,
                    "uniqueness_score": case.uniqueness_score
                }
                for case in self.expanded_cases
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_csv(self, output_file: str) -> None:
        """導出CSV格式"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 寫入標題
            writer.writerow([
                'test_case_id', 'original_template_id', 'expansion_strategy',
                'category', 'difficulty', 'query', 'expected_intent',
                'language', 'complexity_score', 'uniqueness_score'
            ])
            
            # 寫入數據
            for case in self.expanded_cases:
                writer.writerow([
                    case.test_case_id,
                    case.original_template_id,
                    case.expansion_strategy.value,
                    case.category.value,
                    case.difficulty.value,
                    case.query,
                    case.expected_intent,
                    case.language,
                    case.complexity_score,
                    case.uniqueness_score
                ])
    
    def get_expansion_statistics(self) -> Dict[str, Any]:
        """獲取擴充統計"""
        if not self.expanded_cases:
            return {}
        
        stats = {
            "total_cases": len(self.expanded_cases),
            "strategy_distribution": {},
            "category_distribution": {},
            "difficulty_distribution": {},
            "language_distribution": {},
            "complexity_stats": {
                "mean": sum(case.complexity_score for case in self.expanded_cases) / len(self.expanded_cases),
                "min": min(case.complexity_score for case in self.expanded_cases),
                "max": max(case.complexity_score for case in self.expanded_cases)
            }
        }
        
        # 策略分佈
        for case in self.expanded_cases:
            strategy = case.expansion_strategy.value
            stats["strategy_distribution"][strategy] = stats["strategy_distribution"].get(strategy, 0) + 1
        
        # 類別分佈
        for case in self.expanded_cases:
            category = case.category.value
            stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
        
        # 難度分佈
        for case in self.expanded_cases:
            difficulty = case.difficulty.value
            stats["difficulty_distribution"][difficulty] = stats["difficulty_distribution"].get(difficulty, 0) + 1
        
        # 語言分佈
        for case in self.expanded_cases:
            language = case.language
            stats["language_distribution"][language] = stats["language_distribution"].get(language, 0) + 1
        
        return stats
    
    def print_expansion_summary(self) -> None:
        """打印擴充摘要"""
        if not self.expanded_cases:
            print("❌ 沒有生成任何測試案例")
            return
        
        stats = self.get_expansion_statistics()
        
        print("\n" + "="*60)
        print("📊 LLM測試案例擴充摘要")
        print("="*60)
        
        print(f"\n📈 總體統計:")
        print(f"   總案例數: {stats['total_cases']}")
        print(f"   平均複雜度: {stats['complexity_stats']['mean']:.2f}")
        print(f"   複雜度範圍: {stats['complexity_stats']['min']:.2f} - {stats['complexity_stats']['max']:.2f}")
        
        print(f"\n🔧 擴充策略分佈:")
        for strategy, count in stats['strategy_distribution'].items():
            percentage = (count / stats['total_cases']) * 100
            print(f"   {strategy}: {count} ({percentage:.1f}%)")
        
        print(f"\n📂 類別分佈:")
        for category, count in stats['category_distribution'].items():
            percentage = (count / stats['total_cases']) * 100
            print(f"   {category}: {count} ({percentage:.1f}%)")
        
        print(f"\n⚡ 難度分佈:")
        for difficulty, count in stats['difficulty_distribution'].items():
            percentage = (count / stats['total_cases']) * 100
            print(f"   {difficulty}: {count} ({percentage:.1f}%)")
        
        print(f"\n🌍 語言分佈:")
        for language, count in stats['language_distribution'].items():
            percentage = (count / stats['total_cases']) * 100
            print(f"   {language}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*60)


def main():
    """主函數"""
    print("🚀 LLM測試案例擴充工具")
    print("自動生成大量多樣化的測試案例，用於比較不同LLM模型的輸出表現差異\n")
    
    # 創建擴充器
    expander = LLMTestCaseExpander()
    
    # 載入基礎模板
    print("📚 載入基礎模板...")
    expander.load_base_templates()
    
    # 配置選項
    print("\n⚙️ 配置擴充參數:")
    
    # 目標數量
    while True:
        try:
            target_count = int(input("請輸入目標測試案例數量 (建議1000-5000): ") or "2000")
            if target_count > 0:
                break
            else:
                print("❌ 請輸入正數")
        except ValueError:
            print("❌ 請輸入有效數字")
    
    # 擴充策略選擇
    print("\n🔧 選擇擴充策略 (多選，用逗號分隔):")
    strategies = list(ExpansionStrategy)
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy.value}")
    
    strategy_input = input("請選擇策略編號 (預設全選): ") or ",".join(str(i) for i in range(1, len(strategies) + 1))
    
    try:
        selected_indices = [int(x.strip()) - 1 for x in strategy_input.split(",")]
        selected_strategies = [strategies[i] for i in selected_indices if 0 <= i < len(strategies)]
    except:
        selected_strategies = strategies
    
    # 語言分佈
    print("\n🌍 語言分佈配置:")
    print("1. 以中文為主 (中文70%, 英文20%, 其他10%)")
    print("2. 多語言平衡 (中文40%, 英文30%, 其他30%)")
    print("3. 英文為主 (英文60%, 中文30%, 其他10%)")
    
    lang_choice = input("請選擇語言分佈 (預設1): ") or "1"
    
    if lang_choice == "2":
        language_distribution = {
            "zh-TW": 0.4, "en-US": 0.3, "zh-CN": 0.15, "ja-JP": 0.1, "ko-KR": 0.05
        }
    elif lang_choice == "3":
        language_distribution = {
            "en-US": 0.6, "zh-TW": 0.3, "zh-CN": 0.05, "ja-JP": 0.03, "ko-KR": 0.02
        }
    else:
        language_distribution = {
            "zh-TW": 0.7, "en-US": 0.2, "zh-CN": 0.05, "ja-JP": 0.03, "ko-KR": 0.02
        }
    
    # 創建配置
    config = ExpansionConfig(
        target_count=target_count,
        expansion_strategies=selected_strategies,
        language_distribution=language_distribution,
        ensure_diversity=True,
        max_similarity_threshold=0.8
    )
    
    # 執行擴充
    print(f"\n🔄 開始擴充測試案例...")
    expanded_cases = expander.expand_test_cases(config)
    
    # 顯示摘要
    expander.print_expansion_summary()
    
    # 導出選項
    print("\n💾 導出選項:")
    export_choice = input("是否導出測試案例? (y/n, 預設y): ") or "y"
    
    if export_choice.lower() == 'y':
        # 選擇格式
        print("\n📄 選擇導出格式:")
        print("1. JSON (推薦)")
        print("2. CSV")
        
        format_choice = input("請選擇格式 (預設1): ") or "1"
        format_type = "json" if format_choice == "1" else "csv"
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"expanded_test_cases_{timestamp}.{format_type}"
        
        # 導出
        expander.export_test_cases(output_file, format_type)
        
        print(f"\n✅ 測試案例已導出到: {output_file}")
    
    # 生成對比報告選項
    print("\n📊 生成對比分析報告:")
    report_choice = input("是否生成測試案例分析報告? (y/n, 預設n): ") or "n"
    
    if report_choice.lower() == 'y':
        # 生成分析報告
        analysis_report = {
            "generation_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_cases": len(expanded_cases),
                "target_count": target_count,
                "success_rate": len(expanded_cases) / target_count if target_count > 0 else 0
            },
            "statistics": expander.get_expansion_statistics(),
            "recommendations": {
                "model_comparison_focus": [
                    "重點測試複雜度較高的案例 (complexity_score > 0.7)",
                    "比較不同語言下的模型表現差異",
                    "關注邊界案例和對抗性測試的處理能力",
                    "評估模型在多技能組合查詢上的理解能力"
                ],
                "testing_strategy": [
                    "按難度等級分批測試，從簡單到複雜",
                    "使用相同查詢的不同語言版本進行跨語言對比",
                    "重點關注意圖識別和實體提取的準確性",
                    "記錄模型在處理模糊查詢時的表現差異"
                ]
            }
        }
        
        report_file = f"test_case_analysis_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_report, f, ensure_ascii=False, indent=2)
        
        print(f"   📋 分析報告已生成: {report_file}")
    
    print("\n🎉 測試案例擴充完成!")
    print("\n💡 使用建議:")
    print("   1. 將生成的測試案例導入到LLM測試執行引擎")
    print("   2. 使用不同的LLM模型運行相同的測試案例")
    print("   3. 比較各模型在不同類別和難度上的表現")
    print("   4. 重點關注複雜度高和邊界案例的處理差異")
    print("   5. 分析多語言測試案例的跨語言理解能力")


if __name__ == "__main__":
    main()