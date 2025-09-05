# -*- coding: utf-8 -*-
"""
快速測試案例生成器
用於快速生成多樣化的LLM測試案例，支援多種場景和複雜度
"""

import json
import random
import csv
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


class TestCategory(Enum):
    """測試案例類別"""
    JOB_SEARCH = "job_search"  # 求職搜尋
    SKILL_QUERY = "skill_query"  # 技能查詢
    LOCATION_BASED = "location_based"  # 地點導向
    SALARY_INQUIRY = "salary_inquiry"  # 薪資查詢
    CAREER_ADVICE = "career_advice"  # 職涯建議
    COMPANY_INFO = "company_info"  # 公司資訊
    EDGE_CASES = "edge_cases"  # 邊界案例
    MULTILINGUAL = "multilingual"  # 多語言
    AMBIGUOUS = "ambiguous"  # 模糊查詢
    COMPLEX_QUERY = "complex_query"  # 複雜查詢


class ComplexityLevel(Enum):
    """複雜度等級"""
    SIMPLE = "simple"  # 簡單
    MEDIUM = "medium"  # 中等
    COMPLEX = "complex"  # 複雜


class LanguageCode(Enum):
    """語言代碼"""
    ZH_TW = "zh-tw"  # 繁體中文
    ZH_CN = "zh-cn"  # 簡體中文
    EN_US = "en-us"  # 英文
    JA_JP = "ja-jp"  # 日文
    KO_KR = "ko-kr"  # 韓文


@dataclass
class TestCase:
    """測試案例數據結構"""
    id: str
    query: str
    category: str
    complexity: str
    language: str
    expected_intent: str
    expected_entities: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str


@dataclass
class GenerationConfig:
    """生成配置"""
    total_cases: int = 50
    language_distribution: Dict[str, float] = None
    complexity_distribution: Dict[str, float] = None
    category_weights: Dict[str, float] = None
    include_edge_cases: bool = True
    ensure_diversity: bool = True

    def __post_init__(self):
        if self.language_distribution is None:
            self.language_distribution = {
                "zh-tw": 0.4,
                "en-us": 0.3,
                "zh-cn": 0.2,
                "ja-jp": 0.05,
                "ko-kr": 0.05
            }
        
        if self.complexity_distribution is None:
            self.complexity_distribution = {
                "simple": 0.4,
                "medium": 0.4,
                "complex": 0.2
            }
        
        if self.category_weights is None:
            self.category_weights = {
                "job_search": 0.25,
                "skill_query": 0.15,
                "location_based": 0.15,
                "salary_inquiry": 0.1,
                "career_advice": 0.1,
                "company_info": 0.1,
                "edge_cases": 0.05,
                "multilingual": 0.05,
                "ambiguous": 0.03,
                "complex_query": 0.02
            }


class TestCaseGenerator:
    """測試案例生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.templates = self._load_templates()
        self.entities = self._load_entities()
        self.generated_cases = []
        self.generation_stats = {}
    
    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """載入查詢模板"""
        return {
            "job_search": {
                "simple": [
                    "我想找{job_title}的工作",
                    "尋找{location}的{job_title}職位",
                    "Find {job_title} jobs",
                    "Looking for {job_title} position"
                ],
                "medium": [
                    "我想在{location}找{experience_level}{job_title}的工作，薪水{salary_range}",
                    "尋找{company_type}公司的{job_title}職位，要求{skills}",
                    "Find {experience_level} {job_title} jobs in {location} with {benefits}"
                ],
                "complex": [
                    "我是{background}背景，想轉職到{job_title}，希望在{location}找到薪水{salary_range}且有{benefits}的職位",
                    "尋找適合{experience_level}的{job_title}工作，公司規模{company_size}，地點{location}，技能要求包含{skills}"
                ]
            },
            "skill_query": {
                "simple": [
                    "{job_title}需要什麼技能？",
                    "What skills are needed for {job_title}?",
                    "{skill}技能的就業前景如何？"
                ],
                "medium": [
                    "想學習{skill}，有哪些相關的職位？",
                    "How to improve {skill} for {job_title} role?",
                    "{job_title}和{job_title2}哪個比較有前景？"
                ],
                "complex": [
                    "我有{current_skills}技能，想轉到{target_field}領域，需要學習哪些新技能？",
                    "Compare career paths: {job_title} vs {job_title2} in terms of skills, salary, and growth"
                ]
            },
            "edge_cases": {
                "simple": [
                    "",  # 空查詢
                    "？？？",  # 無意義符號
                    "aaaaaaaaa",  # 重複字符
                    "123456",  # 純數字
                ],
                "medium": [
                    "我想找工作但不知道找什麼",  # 模糊意圖
                    "幫我找個好工作",  # 過於籠統
                    "工作工作工作工作工作",  # 重複詞彙
                ],
                "complex": [
                    "我想找一個既能賺錢又輕鬆又有成就感還能學到東西的工作",  # 過多條件
                    "找工作但我什麼都不會也不想學新東西",  # 矛盾需求
                ]
            }
        }
    
    def _load_entities(self) -> Dict[str, List[str]]:
        """載入實體數據"""
        return {
            "job_title": [
                "軟體工程師", "資料科學家", "產品經理", "UI/UX設計師", "DevOps工程師",
                "Software Engineer", "Data Scientist", "Product Manager", "Designer",
                "プログラマー", "데이터 사이언티스트"
            ],
            "location": [
                "台北", "新竹", "台中", "高雄", "桃園",
                "San Francisco", "New York", "London", "Singapore",
                "東京", "서울"
            ],
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "AWS",
                "機器學習", "資料分析", "專案管理", "UI設計",
                "コミュニケーション", "팀워크"
            ],
            "salary_range": [
                "50-80萬", "80-120萬", "120萬以上",
                "$80k-120k", "$120k+",
                "500-800万円", "5000-8000만원"
            ],
            "experience_level": [
                "新鮮人", "1-3年經驗", "3-5年經驗", "資深",
                "Entry level", "Mid-level", "Senior",
                "新卒", "신입"
            ]
        }
    
    def generate_test_cases(self, config: GenerationConfig) -> List[TestCase]:
        """生成測試案例"""
        self.generated_cases = []
        self.generation_stats = {
            "total_generated": 0,
            "by_category": {},
            "by_complexity": {},
            "by_language": {},
            "generation_time": datetime.now().isoformat()
        }
        
        # 計算各類別案例數量
        category_counts = self._calculate_category_counts(config)
        
        # 生成各類別案例
        for category, count in category_counts.items():
            if count > 0:
                cases = self._generate_category_cases(category, count, config)
                self.generated_cases.extend(cases)
        
        # 確保多樣性
        if config.ensure_diversity:
            self._ensure_diversity()
        
        # 調整到目標數量
        self._adjust_to_target_count(config.total_cases)
        
        # 更新統計
        self._update_generation_stats()
        
        return self.generated_cases
    
    def _calculate_category_counts(self, config: GenerationConfig) -> Dict[str, int]:
        """計算各類別案例數量"""
        counts = {}
        for category, weight in config.category_weights.items():
            counts[category] = int(config.total_cases * weight)
        return counts
    
    def _generate_category_cases(self, category: str, count: int, config: GenerationConfig) -> List[TestCase]:
        """生成特定類別的案例"""
        cases = []
        
        for i in range(count):
            # 選擇複雜度
            complexity = self._select_complexity(config.complexity_distribution)
            
            # 選擇語言
            language = self._select_language(config.language_distribution)
            
            # 生成案例
            case = self._create_test_case(category, complexity, language)
            if case:
                cases.append(case)
        
        return cases
    
    def _select_complexity(self, distribution: Dict[str, float]) -> str:
        """根據分佈選擇複雜度"""
        rand = random.random()
        cumulative = 0
        for complexity, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return complexity
        return "simple"
    
    def _select_language(self, distribution: Dict[str, float]) -> str:
        """根據分佈選擇語言"""
        rand = random.random()
        cumulative = 0
        for language, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return language
        return "zh-tw"
    
    def _create_test_case(self, category: str, complexity: str, language: str) -> Optional[TestCase]:
        """創建單個測試案例"""
        try:
            # 獲取模板
            templates = self.templates.get(category, {}).get(complexity, [])
            if not templates:
                return None
            
            # 選擇模板
            template = random.choice(templates)
            
            # 填充模板
            query = self._fill_template(template, language)
            
            # 生成預期意圖
            expected_intent = self._generate_expected_intent(category, query)
            
            # 提取實體
            expected_entities = self._extract_entities(query, category)
            
            # 創建案例
            case = TestCase(
                id=f"{category}_{complexity}_{language}_{len(self.generated_cases) + 1}",
                query=query,
                category=category,
                complexity=complexity,
                language=language,
                expected_intent=expected_intent,
                expected_entities=expected_entities,
                metadata={
                    "template_used": template,
                    "generated_at": datetime.now().isoformat()
                },
                created_at=datetime.now().isoformat()
            )
            
            return case
            
        except Exception as e:
            print(f"生成案例時發生錯誤: {e}")
            return None
    
    def _fill_template(self, template: str, language: str) -> str:
        """填充模板變數"""
        query = template
        
        # 根據語言過濾實體
        filtered_entities = self._filter_entities_by_language(language)
        
        # 替換模板變數
        for entity_type, values in filtered_entities.items():
            placeholder = f"{{{entity_type}}}"
            if placeholder in query:
                value = random.choice(values)
                query = query.replace(placeholder, value)
        
        return query
    
    def _filter_entities_by_language(self, language: str) -> Dict[str, List[str]]:
        """根據語言過濾實體"""
        filtered = {}
        
        for entity_type, values in self.entities.items():
            filtered_values = []
            
            for value in values:
                # 簡單的語言檢測邏輯
                if language.startswith("zh"):
                    # 中文：包含中文字符
                    if any('\u4e00' <= char <= '\u9fff' for char in value):
                        filtered_values.append(value)
                elif language.startswith("en"):
                    # 英文：主要是ASCII字符
                    if value.isascii() and not any('\u4e00' <= char <= '\u9fff' for char in value):
                        filtered_values.append(value)
                elif language.startswith("ja"):
                    # 日文：包含平假名、片假名或漢字
                    if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9fff' for char in value):
                        filtered_values.append(value)
                elif language.startswith("ko"):
                    # 韓文：包含韓文字符
                    if any('\uac00' <= char <= '\ud7af' for char in value):
                        filtered_values.append(value)
            
            # 如果沒有符合語言的值，使用所有值
            if not filtered_values:
                filtered_values = values
            
            filtered[entity_type] = filtered_values
        
        return filtered
    
    def _generate_expected_intent(self, category: str, query: str) -> str:
        """生成預期意圖"""
        intent_mapping = {
            "job_search": "job_search",
            "skill_query": "skill_inquiry",
            "location_based": "location_search",
            "salary_inquiry": "salary_inquiry",
            "career_advice": "career_guidance",
            "company_info": "company_research",
            "edge_cases": "unclear_intent",
            "multilingual": "job_search",
            "ambiguous": "unclear_intent",
            "complex_query": "complex_job_search"
        }
        
        return intent_mapping.get(category, "unknown")
    
    def _extract_entities(self, query: str, category: str) -> Dict[str, Any]:
        """提取查詢中的實體"""
        entities = {}
        
        # 簡單的實體提取邏輯
        for entity_type, values in self.entities.items():
            for value in values:
                if value.lower() in query.lower():
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(value)
        
        return entities
    
    def _ensure_diversity(self):
        """確保案例多樣性"""
        # 移除重複的查詢
        seen_queries = set()
        unique_cases = []
        
        for case in self.generated_cases:
            if case.query not in seen_queries:
                seen_queries.add(case.query)
                unique_cases.append(case)
        
        self.generated_cases = unique_cases
    
    def _adjust_to_target_count(self, target_count: int):
        """調整到目標數量"""
        current_count = len(self.generated_cases)
        
        if current_count > target_count:
            # 隨機移除多餘案例
            self.generated_cases = random.sample(self.generated_cases, target_count)
        elif current_count < target_count:
            # 創建變體來補足數量
            needed = target_count - current_count
            variants = self._create_variants(needed)
            self.generated_cases.extend(variants)
    
    def _create_variants(self, count: int) -> List[TestCase]:
        """創建案例變體"""
        variants = []
        
        for i in range(count):
            if self.generated_cases:
                # 選擇一個現有案例作為基礎
                base_case = random.choice(self.generated_cases)
                
                # 創建變體
                variant = TestCase(
                    id=f"variant_{base_case.id}_{i}",
                    query=self._create_query_variant(base_case.query),
                    category=base_case.category,
                    complexity=base_case.complexity,
                    language=base_case.language,
                    expected_intent=base_case.expected_intent,
                    expected_entities=base_case.expected_entities.copy(),
                    metadata={
                        "variant_of": base_case.id,
                        "generated_at": datetime.now().isoformat()
                    },
                    created_at=datetime.now().isoformat()
                )
                
                variants.append(variant)
        
        return variants
    
    def _create_query_variant(self, original_query: str) -> str:
        """創建查詢變體"""
        # 簡單的變體生成邏輯
        variants = [
            original_query + "？",
            original_query + "，謝謝",
            "請幫我" + original_query,
            original_query + "，急需"
        ]
        
        return random.choice(variants)
    
    def _update_generation_stats(self):
        """更新生成統計"""
        self.generation_stats["total_generated"] = len(self.generated_cases)
        
        # 按類別統計
        for case in self.generated_cases:
            category = case.category
            if category not in self.generation_stats["by_category"]:
                self.generation_stats["by_category"][category] = 0
            self.generation_stats["by_category"][category] += 1
            
            # 按複雜度統計
            complexity = case.complexity
            if complexity not in self.generation_stats["by_complexity"]:
                self.generation_stats["by_complexity"][complexity] = 0
            self.generation_stats["by_complexity"][complexity] += 1
            
            # 按語言統計
            language = case.language
            if language not in self.generation_stats["by_language"]:
                self.generation_stats["by_language"][language] = 0
            self.generation_stats["by_language"][language] += 1
    
    def export_to_json(self, filepath: str) -> bool:
        """導出為JSON格式"""
        try:
            data = {
                "metadata": {
                    "total_cases": len(self.generated_cases),
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "1.0.0"
                },
                "statistics": self.generation_stats,
                "test_cases": [asdict(case) for case in self.generated_cases]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"導出JSON時發生錯誤: {e}")
            return False
    
    def export_to_csv(self, filepath: str) -> bool:
        """導出為CSV格式"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 寫入標題
                headers = ['id', 'query', 'category', 'complexity', 'language', 
                          'expected_intent', 'expected_entities', 'metadata', 'created_at']
                writer.writerow(headers)
                
                # 寫入數據
                for case in self.generated_cases:
                    row = [
                        case.id,
                        case.query,
                        case.category,
                        case.complexity,
                        case.language,
                        case.expected_intent,
                        json.dumps(case.expected_entities, ensure_ascii=False),
                        json.dumps(case.metadata, ensure_ascii=False),
                        case.created_at
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"導出CSV時發生錯誤: {e}")
            return False
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """獲取生成摘要"""
        return {
            "total_cases": len(self.generated_cases),
            "statistics": self.generation_stats,
            "sample_cases": [asdict(case) for case in self.generated_cases[:3]]  # 前3個案例作為樣本
        }
    
    def print_generation_summary(self):
        """打印生成摘要"""
        print("\n=== 測試案例生成摘要 ===")
        print(f"總共生成: {len(self.generated_cases)} 個測試案例")
        
        print("\n按類別分佈:")
        for category, count in self.generation_stats.get("by_category", {}).items():
            print(f"  {category}: {count}")
        
        print("\n按複雜度分佈:")
        for complexity, count in self.generation_stats.get("by_complexity", {}).items():
            print(f"  {complexity}: {count}")
        
        print("\n按語言分佈:")
        for language, count in self.generation_stats.get("by_language", {}).items():
            print(f"  {language}: {count}")
        
        print("\n樣本案例:")
        for i, case in enumerate(self.generated_cases[:3], 1):
            print(f"  {i}. [{case.category}] {case.query}")


def main():
    """主函數 - 工具入口點"""
    print("🚀 快速測試案例生成器")
    print("=" * 50)
    
    generator = TestCaseGenerator()
    
    # 提供預設配置選項
    config_options = {
        "1": ("平衡模式", GenerationConfig(total_cases=50)),
        "2": ("求職導向", GenerationConfig(
            total_cases=100,
            category_weights={
                "job_search": 0.5,
                "skill_query": 0.2,
                "location_based": 0.15,
                "salary_inquiry": 0.1,
                "career_advice": 0.05
            }
        )),
        "3": ("技能導向", GenerationConfig(
            total_cases=75,
            category_weights={
                "skill_query": 0.4,
                "job_search": 0.3,
                "career_advice": 0.2,
                "company_info": 0.1
            }
        )),
        "4": ("多語言", GenerationConfig(
            total_cases=60,
            language_distribution={
                "zh-tw": 0.25,
                "en-us": 0.25,
                "zh-cn": 0.25,
                "ja-jp": 0.125,
                "ko-kr": 0.125
            }
        )),
        "5": ("邊界案例", GenerationConfig(
            total_cases=30,
            category_weights={
                "edge_cases": 0.4,
                "ambiguous": 0.3,
                "complex_query": 0.2,
                "job_search": 0.1
            }
        )),
        "6": ("自定義", None)
    }
    
    print("\n選擇生成模式:")
    for key, (name, _) in config_options.items():
        print(f"  {key}. {name}")
    
    choice = input("\n請選擇 (1-6): ").strip()
    
    if choice in config_options:
        name, config = config_options[choice]
        
        if choice == "6":  # 自定義模式
            total_cases = int(input("請輸入總案例數 (預設50): ") or "50")
            config = GenerationConfig(total_cases=total_cases)
        
        print(f"\n使用 {name} 生成 {config.total_cases} 個測試案例...")
        
        # 生成測試案例
        test_cases = generator.generate_test_cases(config)
        
        # 顯示摘要
        generator.print_generation_summary()
        
        # 詢問是否導出
        export_choice = input("\n是否要導出結果？(y/n): ").strip().lower()
        if export_choice == 'y':
            format_choice = input("選擇格式 (json/csv): ").strip().lower()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_choice == 'json':
                filename = f"test_cases_{timestamp}.json"
                if generator.export_to_json(filename):
                    print(f"✅ 已導出到: {filename}")
                else:
                    print("❌ 導出失敗")
            elif format_choice == 'csv':
                filename = f"test_cases_{timestamp}.csv"
                if generator.export_to_csv(filename):
                    print(f"✅ 已導出到: {filename}")
                else:
                    print("❌ 導出失敗")
    else:
        print("無效選擇")


if __name__ == "__main__":
    main()