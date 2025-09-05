#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例數據集生成器
生成大量多樣化的測試案例，用於全面評估LLM模型性能

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import random
import itertools
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import string
import re


class DatasetType(Enum):
    """數據集類型"""
    TRAINING = "training"  # 訓練集
    VALIDATION = "validation"  # 驗證集
    TESTING = "testing"  # 測試集
    BENCHMARK = "benchmark"  # 基準測試集
    STRESS = "stress"  # 壓力測試集
    ADVERSARIAL = "adversarial"  # 對抗測試集


class GenerationStrategy(Enum):
    """生成策略"""
    TEMPLATE_BASED = "template_based"  # 基於模板
    COMBINATORIAL = "combinatorial"  # 組合式
    RULE_BASED = "rule_based"  # 基於規則
    SYNTHETIC = "synthetic"  # 合成式
    AUGMENTATION = "augmentation"  # 數據增強
    ADVERSARIAL = "adversarial"  # 對抗式


@dataclass
class DatasetConfig:
    """數據集配置"""
    dataset_type: DatasetType
    target_size: int
    generation_strategies: List[GenerationStrategy]
    complexity_distribution: Dict[str, float] = field(default_factory=lambda: {
        "simple": 0.3, "medium": 0.4, "complex": 0.2, "extreme": 0.1
    })
    language_distribution: Dict[str, float] = field(default_factory=lambda: {
        "chinese": 0.6, "english": 0.3, "mixed": 0.1
    })
    category_distribution: Dict[str, float] = field(default_factory=lambda: {
        "job_search": 0.4, "skill_query": 0.2, "location_query": 0.15,
        "salary_query": 0.1, "career_transition": 0.05, "remote_work": 0.05,
        "non_job_related": 0.05
    })
    quality_threshold: float = 0.8
    diversity_threshold: float = 0.7
    enable_validation: bool = True
    enable_augmentation: bool = True


@dataclass
class GeneratedDataset:
    """生成的數據集"""
    dataset_id: str
    dataset_type: DatasetType
    test_cases: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    generation_time: Optional[datetime] = None
    quality_score: float = 0.0
    diversity_score: float = 0.0


class LLMTestDatasetGenerator:
    """LLM測試數據集生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.templates = self._load_templates()
        self.entities = self._load_entities()
        self.patterns = self._load_patterns()
        self.augmentation_rules = self._load_augmentation_rules()
        self.generated_queries = set()  # 避免重複
        
    def _load_templates(self) -> Dict[str, List[str]]:
        """載入查詢模板"""
        return {
            "job_search": [
                "我想找{job_title}的工作",
                "請幫我搜尋{location}的{job_title}職位",
                "有沒有{company}的{job_title}空缺",
                "尋找{experience_level}{job_title}工作機會",
                "我要應徵{industry}行業的{job_title}",
                "Find {job_title} jobs in {location}",
                "Looking for {job_title} position at {company}",
                "Search for {experience_level} {job_title} roles",
                "I want to work as a {job_title} in {industry}",
                "Show me {job_title} openings with {salary_range} salary"
            ],
            "skill_query": [
                "我需要學習什麼技能才能成為{job_title}",
                "{job_title}需要具備哪些技能",
                "如何提升{skill_name}技能",
                "What skills are required for {job_title}",
                "How to improve {skill_name} skills",
                "Best way to learn {technology} for {job_title}",
                "我想轉職到{job_title}，需要什麼技能",
                "{industry}行業最重要的技能是什麼"
            ],
            "location_query": [
                "{location}有哪些{job_title}工作",
                "我想在{location}工作",
                "搬到{location}後如何找工作",
                "Jobs in {location} for {job_title}",
                "Best cities for {job_title} career",
                "Remote {job_title} jobs available",
                "比較{location1}和{location2}的工作機會"
            ],
            "salary_query": [
                "{job_title}的薪水大概多少",
                "我想要薪水{salary_range}的工作",
                "如何談判更高的薪水",
                "What is the average salary for {job_title}",
                "High paying {job_title} jobs",
                "Salary negotiation tips for {job_title}",
                "{location}的{job_title}薪資水平"
            ],
            "career_transition": [
                "我想從{current_job}轉職到{target_job}",
                "如何轉換職業跑道",
                "Career change from {industry1} to {industry2}",
                "轉職需要注意什麼",
                "我{age}歲了還能轉職嗎",
                "How to switch from {current_job} to {target_job}"
            ],
            "remote_work": [
                "我想找遠端工作",
                "有哪些{job_title}可以在家工作",
                "Remote {job_title} opportunities",
                "Work from home {job_title} jobs",
                "如何申請國外的遠端工作",
                "Best remote work platforms for {job_title}"
            ],
            "non_job_related": [
                "今天天氣如何",
                "推薦一些好吃的餐廳",
                "What is the capital of France",
                "如何煮咖啡",
                "最新的電影推薦",
                "How to lose weight",
                "股票投資建議"
            ],
            "boundary_cases": [
                "",  # 空查詢
                "   ",  # 只有空格
                "a",  # 單字符
                "工作" * 100,  # 超長重複
                "!@#$%^&*()",  # 特殊字符
                "SELECT * FROM jobs WHERE salary > 100000",  # SQL注入
                "<script>alert('xss')</script>",  # XSS攻擊
                "工作工作工作工作工作",  # 重複詞彙
                "我我我我我想想想找找工工作作",  # 字符重複
            ],
            "multilingual": [
                "我想找software engineer的工作",  # 中英混合
                "Looking for 軟體工程師 position",  # 英中混合
                "在台北找developer工作",  # 地名+英文職位
                "I want to work in 台灣",  # 英文+中文地名
                "尋找remote work機會",  # 中文+英文概念
            ]
        }
    
    def _load_entities(self) -> Dict[str, List[str]]:
        """載入實體詞典"""
        return {
            "job_title": [
                "軟體工程師", "資料科學家", "產品經理", "設計師", "行銷專員",
                "業務代表", "會計師", "人資專員", "專案經理", "系統管理員",
                "software engineer", "data scientist", "product manager", 
                "designer", "marketing specialist", "sales representative",
                "accountant", "hr specialist", "project manager", "system administrator",
                "前端工程師", "後端工程師", "全端工程師", "DevOps工程師", "QA工程師",
                "UI/UX設計師", "數位行銷專員", "客服專員", "財務分析師", "法務專員"
            ],
            "location": [
                "台北", "新北", "桃園", "台中", "台南", "高雄", "新竹", "基隆",
                "台灣", "中國", "美國", "日本", "新加坡", "香港", "澳洲", "加拿大",
                "Taipei", "New Taipei", "Taoyuan", "Taichung", "Tainan", "Kaohsiung",
                "Taiwan", "China", "USA", "Japan", "Singapore", "Hong Kong",
                "信義區", "大安區", "中山區", "松山區", "內湖區", "南港區",
                "竹北", "竹東", "苗栗", "彰化", "雲林", "嘉義", "屏東", "宜蘭"
            ],
            "company": [
                "台積電", "鴻海", "聯發科", "華碩", "宏碁", "廣達", "仁寶", "和碩",
                "Google", "Microsoft", "Apple", "Amazon", "Facebook", "Netflix",
                "Tesla", "Uber", "Airbnb", "Spotify", "Adobe", "Oracle",
                "阿里巴巴", "騰訊", "百度", "字節跳動", "美團", "滴滴", "小米", "華為",
                "LINE", "Yahoo", "IBM", "Intel", "NVIDIA", "AMD", "Qualcomm"
            ],
            "industry": [
                "科技業", "金融業", "製造業", "服務業", "零售業", "醫療業", "教育業",
                "technology", "finance", "manufacturing", "service", "retail", 
                "healthcare", "education", "entertainment", "automotive", "aerospace",
                "半導體", "電子業", "軟體業", "遊戲業", "電商", "物流業", "房地產",
                "生技業", "能源業", "農業", "觀光業", "媒體業", "廣告業", "顧問業"
            ],
            "experience_level": [
                "新鮮人", "1-3年經驗", "3-5年經驗", "5-10年經驗", "10年以上經驗",
                "junior", "mid-level", "senior", "lead", "principal", "director",
                "實習生", "初級", "中級", "高級", "資深", "首席", "總監", "VP"
            ],
            "skill_name": [
                "Python", "Java", "JavaScript", "React", "Vue.js", "Angular",
                "Node.js", "Django", "Flask", "Spring", "Docker", "Kubernetes",
                "AWS", "Azure", "GCP", "MySQL", "PostgreSQL", "MongoDB",
                "機器學習", "深度學習", "資料分析", "專案管理", "溝通技巧", "領導能力",
                "英文", "日文", "韓文", "德文", "法文", "西班牙文"
            ],
            "technology": [
                "React", "Vue", "Angular", "Python", "Java", "C++", "Go", "Rust",
                "Docker", "Kubernetes", "Terraform", "Jenkins", "GitLab CI",
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
                "區塊鏈", "人工智慧", "物聯網", "雲端運算", "大數據", "DevOps"
            ],
            "salary_range": [
                "30-50萬", "50-80萬", "80-120萬", "120-200萬", "200萬以上",
                "$30k-50k", "$50k-80k", "$80k-120k", "$120k-200k", "$200k+",
                "月薪3-5萬", "月薪5-8萬", "月薪8-12萬", "月薪12-20萬", "月薪20萬以上"
            ],
            "age": ["25", "30", "35", "40", "45", "50", "55"]
        }
    
    def _load_patterns(self) -> Dict[str, List[str]]:
        """載入查詢模式"""
        return {
            "question_patterns": [
                "什麼是{}", "如何{}", "為什麼{}", "哪裡可以{}", "誰能{}",
                "What is {}", "How to {}", "Why {}", "Where can {}", "Who can {}"
            ],
            "request_patterns": [
                "我想要{}", "我需要{}", "請幫我{}", "可以給我{}", "我要找{}",
                "I want {}", "I need {}", "Please help me {}", "Can you give me {}", "I'm looking for {}"
            ],
            "comparison_patterns": [
                "{}和{}哪個比較好", "比較{}與{}", "{}vs{}",
                "Which is better {} or {}", "Compare {} and {}", "{} vs {}"
            ],
            "conditional_patterns": [
                "如果{}的話", "假設{}", "當{}時", "在{}情況下",
                "If {}", "Suppose {}", "When {}", "In case of {}"
            ]
        }
    
    def _load_augmentation_rules(self) -> Dict[str, List[Tuple[str, str]]]:
        """載入數據增強規則"""
        return {
            "synonym_replacement": [
                ("工作", "職位"), ("工作", "職缺"), ("工作", "就業機會"),
                ("找", "搜尋"), ("找", "尋找"), ("找", "查找"),
                ("薪水", "薪資"), ("薪水", "待遇"), ("薪水", "收入"),
                ("公司", "企業"), ("公司", "組織"), ("公司", "機構"),
                ("job", "position"), ("job", "role"), ("job", "career"),
                ("find", "search"), ("find", "look for"), ("find", "seek")
            ],
            "insertion": [
                ("請", "麻煩"), ("可以", "能夠"), ("想要", "希望"),
                ("please", "kindly"), ("can", "could"), ("want", "would like")
            ],
            "deletion": [
                "請", "麻煩", "可以", "能夠", "的話", "一下",
                "please", "kindly", "just", "really", "actually"
            ],
            "reordering": [
                # 詞序調整規則
                (r"我想找(.+)的工作", r"找(.+)工作"),
                (r"I want to find (.+) job", r"Looking for (.+) job")
            ]
        }
    
    def generate_dataset(self, config: DatasetConfig) -> GeneratedDataset:
        """生成數據集"""
        print(f"🎯 開始生成 {config.dataset_type.value} 數據集...")
        print(f"   目標大小: {config.target_size}")
        print(f"   生成策略: {[s.value for s in config.generation_strategies]}")
        
        start_time = datetime.now()
        
        # 初始化數據集
        dataset = GeneratedDataset(
            dataset_id=f"{config.dataset_type.value}_{int(start_time.timestamp())}",
            dataset_type=config.dataset_type,
            test_cases=[],
            generation_time=start_time
        )
        
        # 計算各類別目標數量
        category_targets = self._calculate_category_targets(config)
        
        # 按策略生成測試案例
        for strategy in config.generation_strategies:
            print(f"   🔄 使用策略: {strategy.value}")
            
            if strategy == GenerationStrategy.TEMPLATE_BASED:
                cases = self._generate_template_based(category_targets, config)
            elif strategy == GenerationStrategy.COMBINATORIAL:
                cases = self._generate_combinatorial(category_targets, config)
            elif strategy == GenerationStrategy.RULE_BASED:
                cases = self._generate_rule_based(category_targets, config)
            elif strategy == GenerationStrategy.SYNTHETIC:
                cases = self._generate_synthetic(category_targets, config)
            elif strategy == GenerationStrategy.AUGMENTATION:
                cases = self._generate_augmentation(dataset.test_cases, config)
            elif strategy == GenerationStrategy.ADVERSARIAL:
                cases = self._generate_adversarial(category_targets, config)
            else:
                cases = []
            
            dataset.test_cases.extend(cases)
            print(f"     ✅ 生成 {len(cases)} 個案例")
        
        # 去重和過濾
        dataset.test_cases = self._deduplicate_and_filter(dataset.test_cases, config)
        
        # 調整到目標大小
        dataset.test_cases = self._adjust_to_target_size(dataset.test_cases, config.target_size)
        
        # 計算統計信息
        dataset.statistics = self._calculate_statistics(dataset.test_cases)
        
        # 計算質量和多樣性分數
        dataset.quality_score = self._calculate_quality_score(dataset.test_cases)
        dataset.diversity_score = self._calculate_diversity_score(dataset.test_cases)
        
        # 添加元數據
        dataset.metadata = {
            "config": {
                "dataset_type": config.dataset_type.value,
                "target_size": config.target_size,
                "strategies": [s.value for s in config.generation_strategies],
                "complexity_distribution": config.complexity_distribution,
                "language_distribution": config.language_distribution,
                "category_distribution": config.category_distribution
            },
            "generation_info": {
                "generation_time": start_time.isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "actual_size": len(dataset.test_cases)
            }
        }
        
        print(f"   ✅ 數據集生成完成: {len(dataset.test_cases)} 個案例")
        print(f"   📊 質量分數: {dataset.quality_score:.3f}")
        print(f"   🎨 多樣性分數: {dataset.diversity_score:.3f}")
        
        return dataset
    
    def _calculate_category_targets(self, config: DatasetConfig) -> Dict[str, int]:
        """計算各類別目標數量"""
        targets = {}
        for category, ratio in config.category_distribution.items():
            targets[category] = int(config.target_size * ratio)
        return targets
    
    def _generate_template_based(self, category_targets: Dict[str, int], 
                               config: DatasetConfig) -> List[Dict[str, Any]]:
        """基於模板生成"""
        cases = []
        
        for category, target_count in category_targets.items():
            if category not in self.templates:
                continue
                
            templates = self.templates[category]
            generated_count = 0
            
            while generated_count < target_count:
                template = random.choice(templates)
                
                # 填充模板
                filled_query = self._fill_template(template)
                
                if filled_query and filled_query not in self.generated_queries:
                    case = self._create_test_case(
                        query=filled_query,
                        category=category,
                        complexity=self._sample_complexity(config.complexity_distribution),
                        language=self._detect_language(filled_query),
                        generation_method="template_based",
                        template=template
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(filled_query)
                    generated_count += 1
        
        return cases
    
    def _generate_combinatorial(self, category_targets: Dict[str, int], 
                              config: DatasetConfig) -> List[Dict[str, Any]]:
        """組合式生成"""
        cases = []
        
        # 生成實體組合
        entity_combinations = self._generate_entity_combinations()
        
        for category, target_count in category_targets.items():
            if category not in self.templates:
                continue
                
            generated_count = 0
            templates = self.templates[category]
            
            for template in templates:
                if generated_count >= target_count:
                    break
                    
                # 為每個模板生成多個組合
                combinations_per_template = min(10, target_count - generated_count)
                
                for _ in range(combinations_per_template):
                    combination = random.choice(entity_combinations)
                    filled_query = self._fill_template_with_combination(template, combination)
                    
                    if filled_query and filled_query not in self.generated_queries:
                        case = self._create_test_case(
                            query=filled_query,
                            category=category,
                            complexity=self._sample_complexity(config.complexity_distribution),
                            language=self._detect_language(filled_query),
                            generation_method="combinatorial",
                            template=template,
                            entities=combination
                        )
                        
                        cases.append(case)
                        self.generated_queries.add(filled_query)
                        generated_count += 1
        
        return cases
    
    def _generate_rule_based(self, category_targets: Dict[str, int], 
                           config: DatasetConfig) -> List[Dict[str, Any]]:
        """基於規則生成"""
        cases = []
        
        # 定義生成規則
        rules = {
            "job_search": [
                lambda: f"我想找{random.choice(self.entities['job_title'])}工作在{random.choice(self.entities['location'])}",
                lambda: f"尋找{random.choice(self.entities['experience_level'])}的{random.choice(self.entities['job_title'])}職位",
                lambda: f"{random.choice(self.entities['company'])}有{random.choice(self.entities['job_title'])}的空缺嗎"
            ],
            "skill_query": [
                lambda: f"學習{random.choice(self.entities['technology'])}需要多久時間",
                lambda: f"{random.choice(self.entities['job_title'])}需要會{random.choice(self.entities['skill_name'])}嗎",
                lambda: f"如何快速掌握{random.choice(self.entities['technology'])}技術"
            ],
            "salary_query": [
                lambda: f"{random.choice(self.entities['location'])}的{random.choice(self.entities['job_title'])}薪水多少",
                lambda: f"我想要{random.choice(self.entities['salary_range'])}的工作",
                lambda: f"{random.choice(self.entities['experience_level'])}的薪資範圍是多少"
            ]
        }
        
        for category, target_count in category_targets.items():
            if category not in rules:
                continue
                
            category_rules = rules[category]
            generated_count = 0
            
            while generated_count < target_count:
                rule = random.choice(category_rules)
                query = rule()
                
                if query and query not in self.generated_queries:
                    case = self._create_test_case(
                        query=query,
                        category=category,
                        complexity=self._sample_complexity(config.complexity_distribution),
                        language=self._detect_language(query),
                        generation_method="rule_based"
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(query)
                    generated_count += 1
        
        return cases
    
    def _generate_synthetic(self, category_targets: Dict[str, int], 
                          config: DatasetConfig) -> List[Dict[str, Any]]:
        """合成式生成"""
        cases = []
        
        # 生成合成查詢
        for category, target_count in category_targets.items():
            generated_count = 0
            
            while generated_count < target_count:
                # 隨機組合詞彙生成新查詢
                query = self._generate_synthetic_query(category)
                
                if query and query not in self.generated_queries:
                    case = self._create_test_case(
                        query=query,
                        category=category,
                        complexity=self._sample_complexity(config.complexity_distribution),
                        language=self._detect_language(query),
                        generation_method="synthetic"
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(query)
                    generated_count += 1
        
        return cases
    
    def _generate_augmentation(self, existing_cases: List[Dict[str, Any]], 
                             config: DatasetConfig) -> List[Dict[str, Any]]:
        """數據增強生成"""
        if not existing_cases:
            return []
        
        cases = []
        augmentation_count = min(len(existing_cases), config.target_size // 4)  # 增強25%
        
        for _ in range(augmentation_count):
            base_case = random.choice(existing_cases)
            base_query = base_case["query"]
            
            # 應用增強技術
            augmented_queries = []
            
            # 同義詞替換
            augmented_queries.append(self._apply_synonym_replacement(base_query))
            
            # 插入詞彙
            augmented_queries.append(self._apply_insertion(base_query))
            
            # 刪除詞彙
            augmented_queries.append(self._apply_deletion(base_query))
            
            # 詞序調整
            augmented_queries.append(self._apply_reordering(base_query))
            
            for aug_query in augmented_queries:
                if aug_query and aug_query != base_query and aug_query not in self.generated_queries:
                    case = self._create_test_case(
                        query=aug_query,
                        category=base_case["category"],
                        complexity=base_case["complexity"],
                        language=self._detect_language(aug_query),
                        generation_method="augmentation",
                        base_case_id=base_case["id"]
                    )
                    
                    cases.append(case)
                    self.generated_queries.add(aug_query)
        
        return cases
    
    def _generate_adversarial(self, category_targets: Dict[str, int], 
                            config: DatasetConfig) -> List[Dict[str, Any]]:
        """對抗式生成"""
        cases = []
        
        # 生成對抗性測試案例
        adversarial_patterns = [
            # 邊界案例
            "",  # 空查詢
            "   ",  # 只有空格
            "a" * 1000,  # 超長查詢
            "工作" * 50,  # 重複詞彙
            
            # 特殊字符
            "!@#$%^&*()",
            "<script>alert('test')</script>",
            "SELECT * FROM jobs",
            "../../../etc/passwd",
            
            # 混淆查詢
            "我我我想想找找工工作作",
            "工作找我想",
            "JOB job Job jOb",
            
            # 多語言混合
            "我want找job在台北",
            "Looking for工作in台灣",
            "仕事を探している",
            "찾고 있는 직업",
        ]
        
        for pattern in adversarial_patterns:
            case = self._create_test_case(
                query=pattern,
                category="boundary_cases",
                complexity="extreme",
                language="mixed" if self._is_multilingual(pattern) else self._detect_language(pattern),
                generation_method="adversarial",
                is_adversarial=True
            )
            
            cases.append(case)
            self.generated_queries.add(pattern)
        
        return cases
    
    def _fill_template(self, template: str) -> str:
        """填充模板"""
        filled = template
        
        # 查找所有佔位符
        placeholders = re.findall(r'\{([^}]+)\}', template)
        
        for placeholder in placeholders:
            if placeholder in self.entities:
                replacement = random.choice(self.entities[placeholder])
                filled = filled.replace(f"{{{placeholder}}}", replacement)
        
        return filled
    
    def _fill_template_with_combination(self, template: str, combination: Dict[str, str]) -> str:
        """使用組合填充模板"""
        filled = template
        
        for placeholder, value in combination.items():
            filled = filled.replace(f"{{{placeholder}}}", value)
        
        return filled
    
    def _generate_entity_combinations(self) -> List[Dict[str, str]]:
        """生成實體組合"""
        combinations = []
        
        # 生成常見組合
        for _ in range(100):
            combination = {}
            
            # 隨機選擇實體
            for entity_type, values in self.entities.items():
                if random.random() < 0.3:  # 30%機率包含此實體
                    combination[entity_type] = random.choice(values)
            
            if combination:
                combinations.append(combination)
        
        return combinations
    
    def _generate_synthetic_query(self, category: str) -> str:
        """生成合成查詢"""
        # 根據類別生成合成查詢
        if category == "job_search":
            parts = [
                random.choice(["我想", "我要", "尋找", "找", "搜尋"]),
                random.choice(self.entities["job_title"]),
                random.choice(["工作", "職位", "職缺", "機會"]),
                random.choice(["在", "於", "位於"]) if random.random() < 0.5 else "",
                random.choice(self.entities["location"]) if random.random() < 0.5 else ""
            ]
        elif category == "skill_query":
            parts = [
                random.choice(["如何", "怎麼", "怎樣"]),
                random.choice(["學習", "掌握", "提升"]),
                random.choice(self.entities["skill_name"]),
                random.choice(["技能", "能力", "技術"])
            ]
        else:
            # 默認生成
            parts = [
                random.choice(["我想", "請問", "如何"]),
                random.choice(self.entities["job_title"]),
                random.choice(["相關", "有關", "關於"]),
                random.choice(["問題", "資訊", "資料"])
            ]
        
        return " ".join([part for part in parts if part])
    
    def _apply_synonym_replacement(self, query: str) -> str:
        """應用同義詞替換"""
        result = query
        
        for original, replacement in self.augmentation_rules["synonym_replacement"]:
            if original in result:
                result = result.replace(original, replacement)
                break  # 只替換一次
        
        return result
    
    def _apply_insertion(self, query: str) -> str:
        """應用插入"""
        insertions = self.augmentation_rules["insertion"]
        
        if insertions and random.random() < 0.5:
            insertion, _ = random.choice(insertions)
            words = query.split()
            if words:
                pos = random.randint(0, len(words))
                words.insert(pos, insertion)
                return " ".join(words)
        
        return query
    
    def _apply_deletion(self, query: str) -> str:
        """應用刪除"""
        deletions = self.augmentation_rules["deletion"]
        
        result = query
        for deletion in deletions:
            if deletion in result:
                result = result.replace(deletion, "", 1)  # 只刪除一次
                break
        
        return result.strip()
    
    def _apply_reordering(self, query: str) -> str:
        """應用詞序調整"""
        words = query.split()
        
        if len(words) > 2 and random.random() < 0.3:
            # 隨機交換兩個詞的位置
            i, j = random.sample(range(len(words)), 2)
            words[i], words[j] = words[j], words[i]
        
        return " ".join(words)
    
    def _create_test_case(self, query: str, category: str, complexity: str, 
                         language: str, generation_method: str, **kwargs) -> Dict[str, Any]:
        """創建測試案例"""
        case_id = f"{category}_{len(self.generated_queries)}_{int(datetime.now().timestamp())}"
        
        case = {
            "id": case_id,
            "query": query,
            "category": category,
            "complexity": complexity,
            "language": language,
            "generation_method": generation_method,
            "expected_intent": self._infer_expected_intent(query, category),
            "metadata": {
                "query_length": len(query),
                "word_count": len(query.split()),
                "has_special_chars": bool(re.search(r'[^\w\s\u4e00-\u9fff]', query)),
                "is_question": query.strip().endswith('?') or any(q in query for q in ['什麼', '如何', '為什麼', 'what', 'how', 'why']),
                "generation_time": datetime.now().isoformat()
            }
        }
        
        # 添加額外元數據
        case["metadata"].update(kwargs)
        
        return case
    
    def _sample_complexity(self, distribution: Dict[str, float]) -> str:
        """根據分佈採樣複雜度"""
        rand = random.random()
        cumulative = 0
        
        for complexity, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return complexity
        
        return "medium"  # 默認
    
    def _detect_language(self, query: str) -> str:
        """檢測查詢語言"""
        if not query:
            return "unknown"
        
        # 簡單的語言檢測
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', query))
        english_chars = len(re.findall(r'[a-zA-Z]', query))
        total_chars = len(query.replace(' ', ''))
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.5:
            return "chinese"
        elif english_ratio > 0.5:
            return "english"
        elif chinese_ratio > 0.1 and english_ratio > 0.1:
            return "mixed"
        else:
            return "other"
    
    def _is_multilingual(self, query: str) -> bool:
        """檢查是否為多語言查詢"""
        return self._detect_language(query) == "mixed"
    
    def _infer_expected_intent(self, query: str, category: str) -> str:
        """推斷期望意圖"""
        # 基於類別和查詢內容推斷意圖
        intent_mapping = {
            "job_search": "job_search",
            "skill_query": "skill_inquiry",
            "location_query": "location_search",
            "salary_query": "salary_inquiry",
            "career_transition": "career_advice",
            "remote_work": "remote_job_search",
            "non_job_related": "non_job_related",
            "boundary_cases": "unclear",
            "multilingual": "job_search"  # 大多數多語言查詢是求職相關
        }
        
        return intent_mapping.get(category, "unknown")
    
    def _deduplicate_and_filter(self, test_cases: List[Dict[str, Any]], 
                               config: DatasetConfig) -> List[Dict[str, Any]]:
        """去重和過濾"""
        print("   🔄 去重和過濾測試案例...")
        
        # 去重
        seen_queries = set()
        unique_cases = []
        
        for case in test_cases:
            query = case["query"]
            if query not in seen_queries:
                seen_queries.add(query)
                unique_cases.append(case)
        
        print(f"     去重後: {len(unique_cases)} 個案例")
        
        # 質量過濾
        if config.enable_validation:
            filtered_cases = []
            
            for case in unique_cases:
                quality_score = self._calculate_case_quality(case)
                if quality_score >= config.quality_threshold:
                    filtered_cases.append(case)
            
            print(f"     質量過濾後: {len(filtered_cases)} 個案例")
            return filtered_cases
        
        return unique_cases
    
    def _calculate_case_quality(self, case: Dict[str, Any]) -> float:
        """計算案例質量分數"""
        query = case["query"]
        
        if not query or not query.strip():
            return 0.0
        
        score = 1.0
        
        # 長度檢查
        if len(query) < 2:
            score -= 0.3
        elif len(query) > 500:
            score -= 0.2
        
        # 重複字符檢查
        if len(set(query)) / len(query) < 0.3:
            score -= 0.3
        
        # 特殊字符比例
        special_char_ratio = len(re.findall(r'[^\w\s\u4e00-\u9fff]', query)) / len(query)
        if special_char_ratio > 0.5:
            score -= 0.4
        
        # 語言一致性
        if case["language"] == "unknown":
            score -= 0.2
        
        return max(0.0, score)
    
    def _adjust_to_target_size(self, test_cases: List[Dict[str, Any]], 
                              target_size: int) -> List[Dict[str, Any]]:
        """調整到目標大小"""
        if len(test_cases) > target_size:
            # 隨機採樣
            return random.sample(test_cases, target_size)
        elif len(test_cases) < target_size:
            # 如果不足，重複一些案例（添加變體）
            additional_needed = target_size - len(test_cases)
            additional_cases = []
            
            for _ in range(additional_needed):
                base_case = random.choice(test_cases)
                # 創建變體
                variant = base_case.copy()
                variant["id"] = f"{base_case['id']}_variant_{len(additional_cases)}"
                variant["query"] = self._create_query_variant(base_case["query"])
                additional_cases.append(variant)
            
            return test_cases + additional_cases
        
        return test_cases
    
    def _create_query_variant(self, original_query: str) -> str:
        """創建查詢變體"""
        # 簡單的變體生成
        variants = [
            self._apply_synonym_replacement(original_query),
            self._apply_insertion(original_query),
            self._apply_deletion(original_query)
        ]
        
        # 選擇與原查詢不同的變體
        for variant in variants:
            if variant != original_query:
                return variant
        
        return original_query
    
    def _calculate_statistics(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算統計信息"""
        if not test_cases:
            return {}
        
        # 類別分佈
        category_counts = defaultdict(int)
        complexity_counts = defaultdict(int)
        language_counts = defaultdict(int)
        generation_method_counts = defaultdict(int)
        
        query_lengths = []
        word_counts = []
        
        for case in test_cases:
            category_counts[case["category"]] += 1
            complexity_counts[case["complexity"]] += 1
            language_counts[case["language"]] += 1
            generation_method_counts[case["generation_method"]] += 1
            
            query_lengths.append(len(case["query"]))
            word_counts.append(len(case["query"].split()))
        
        return {
            "total_cases": len(test_cases),
            "category_distribution": dict(category_counts),
            "complexity_distribution": dict(complexity_counts),
            "language_distribution": dict(language_counts),
            "generation_method_distribution": dict(generation_method_counts),
            "query_length_stats": {
                "min": min(query_lengths) if query_lengths else 0,
                "max": max(query_lengths) if query_lengths else 0,
                "avg": sum(query_lengths) / len(query_lengths) if query_lengths else 0
            },
            "word_count_stats": {
                "min": min(word_counts) if word_counts else 0,
                "max": max(word_counts) if word_counts else 0,
                "avg": sum(word_counts) / len(word_counts) if word_counts else 0
            }
        }
    
    def _calculate_quality_score(self, test_cases: List[Dict[str, Any]]) -> float:
        """計算整體質量分數"""
        if not test_cases:
            return 0.0
        
        total_score = 0.0
        
        for case in test_cases:
            case_score = self._calculate_case_quality(case)
            total_score += case_score
        
        return total_score / len(test_cases)
    
    def _calculate_diversity_score(self, test_cases: List[Dict[str, Any]]) -> float:
        """計算多樣性分數"""
        if not test_cases:
            return 0.0
        
        # 計算各維度的多樣性
        categories = set(case["category"] for case in test_cases)
        complexities = set(case["complexity"] for case in test_cases)
        languages = set(case["language"] for case in test_cases)
        
        # 查詢相似性
        unique_queries = set(case["query"] for case in test_cases)
        query_diversity = len(unique_queries) / len(test_cases)
        
        # 綜合多樣性分數
        diversity_score = (
            len(categories) / 10 * 0.3 +  # 類別多樣性
            len(complexities) / 4 * 0.2 +  # 複雜度多樣性
            len(languages) / 5 * 0.2 +  # 語言多樣性
            query_diversity * 0.3  # 查詢多樣性
        )
        
        return min(1.0, diversity_score)
    
    def export_dataset(self, dataset: GeneratedDataset, output_file: str = None) -> str:
        """導出數據集"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dataset_{dataset.dataset_type.value}_{timestamp}.json"
        
        print(f"💾 導出數據集到 {output_file}...")
        
        export_data = {
            "dataset_info": {
                "dataset_id": dataset.dataset_id,
                "dataset_type": dataset.dataset_type.value,
                "generation_time": dataset.generation_time.isoformat() if dataset.generation_time else None,
                "quality_score": dataset.quality_score,
                "diversity_score": dataset.diversity_score
            },
            "metadata": dataset.metadata,
            "statistics": dataset.statistics,
            "test_cases": dataset.test_cases
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 數據集已導出: {len(dataset.test_cases)} 個案例")
        return output_file
    
    def print_dataset_summary(self, dataset: GeneratedDataset) -> None:
        """打印數據集摘要"""
        print("\n" + "=" * 60)
        print(f"📊 數據集摘要: {dataset.dataset_type.value}")
        print("=" * 60)
        
        print(f"\n📈 基本信息:")
        print(f"   數據集ID: {dataset.dataset_id}")
        print(f"   案例數量: {len(dataset.test_cases)}")
        print(f"   質量分數: {dataset.quality_score:.3f}")
        print(f"   多樣性分數: {dataset.diversity_score:.3f}")
        
        if dataset.statistics:
            stats = dataset.statistics
            
            print(f"\n📊 分佈統計:")
            
            # 類別分佈
            if "category_distribution" in stats:
                print(f"   類別分佈:")
                for category, count in stats["category_distribution"].items():
                    percentage = count / stats["total_cases"] * 100
                    print(f"     {category}: {count} ({percentage:.1f}%)")
            
            # 複雜度分佈
            if "complexity_distribution" in stats:
                print(f"   複雜度分佈:")
                for complexity, count in stats["complexity_distribution"].items():
                    percentage = count / stats["total_cases"] * 100
                    print(f"     {complexity}: {count} ({percentage:.1f}%)")
            
            # 語言分佈
            if "language_distribution" in stats:
                print(f"   語言分佈:")
                for language, count in stats["language_distribution"].items():
                    percentage = count / stats["total_cases"] * 100
                    print(f"     {language}: {count} ({percentage:.1f}%)")
            
            # 查詢長度統計
            if "query_length_stats" in stats:
                length_stats = stats["query_length_stats"]
                print(f"   查詢長度統計:")
                print(f"     最短: {length_stats['min']} 字符")
                print(f"     最長: {length_stats['max']} 字符")
                print(f"     平均: {length_stats['avg']:.1f} 字符")
        
        print("\n" + "=" * 60)


def main():
    """主函數 - 數據集生成器入口點"""
    print("🎯 LLM測試數據集生成器")
    print("=" * 60)
    
    try:
        # 選擇數據集類型
        print("\n📊 選擇數據集類型:")
        dataset_types = list(DatasetType)
        for i, dtype in enumerate(dataset_types, 1):
            print(f"{i}. {dtype.value}")
        
        type_choice = input("請選擇數據集類型 (1-6): ").strip()
        try:
            dataset_type = dataset_types[int(type_choice) - 1]
        except:
            print("無效選擇，使用默認類型: testing")
            dataset_type = DatasetType.TESTING
        
        # 設置目標大小
        size_input = input("請輸入目標數據集大小 (默認1000): ").strip()
        target_size = int(size_input) if size_input.isdigit() else 1000
        
        # 選擇生成策略
        print("\n🔧 選擇生成策略:")
        strategies = list(GenerationStrategy)
        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. {strategy.value}")
        
        strategy_input = input("請選擇策略 (用逗號分隔編號，或按Enter選擇所有): ").strip()
        
        if strategy_input:
            try:
                indices = [int(x.strip()) - 1 for x in strategy_input.split(",")]
                selected_strategies = [strategies[i] for i in indices if 0 <= i < len(strategies)]
            except:
                print("無效選擇，使用所有策略")
                selected_strategies = strategies
        else:
            selected_strategies = strategies
        
        # 創建配置
        config = DatasetConfig(
            dataset_type=dataset_type,
            target_size=target_size,
            generation_strategies=selected_strategies
        )
        
        # 創建生成器
        generator = LLMTestDatasetGenerator()
        
        # 生成數據集
        print(f"\n🚀 開始生成數據集...")
        dataset = generator.generate_dataset(config)
        
        # 顯示摘要
        generator.print_dataset_summary(dataset)
        
        # 導出數據集
        export_choice = input("\n是否導出數據集？ (y/n): ").strip().lower()
        if export_choice == 'y':
            output_file = generator.export_dataset(dataset)
            print(f"   📄 數據集文件: {output_file}")
        
        print("\n🎉 數據集生成完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 生成過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 生成過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()