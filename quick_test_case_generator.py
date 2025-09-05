#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試案例生成器
專門用於快速生成多樣化的LLM測試案例，支援多種場景和複雜度

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import itertools


class TestCategory(Enum):
    """測試類別"""
    JOB_SEARCH = "job_search"  # 求職搜尋
    SKILL_QUERY = "skill_query"  # 技能查詢
    LOCATION_SEARCH = "location_search"  # 地點搜尋
    SALARY_INQUIRY = "salary_inquiry"  # 薪資查詢
    CAREER_ADVICE = "career_advice"  # 職涯建議
    COMPANY_INFO = "company_info"  # 公司資訊
    INTERVIEW_PREP = "interview_prep"  # 面試準備
    RESUME_HELP = "resume_help"  # 履歷協助
    GENERAL_CHAT = "general_chat"  # 一般對話
    EDGE_CASE = "edge_case"  # 邊界案例


class ComplexityLevel(Enum):
    """複雜度等級"""
    SIMPLE = "simple"  # 簡單
    MODERATE = "moderate"  # 中等
    COMPLEX = "complex"  # 複雜
    EXTREME = "extreme"  # 極端


class LanguageCode(Enum):
    """語言代碼"""
    ZH_TW = "zh-TW"  # 繁體中文
    ZH_CN = "zh-CN"  # 簡體中文
    EN_US = "en-US"  # 美式英文
    JA_JP = "ja-JP"  # 日文
    KO_KR = "ko-KR"  # 韓文


@dataclass
class TestCase:
    """測試案例"""
    test_id: str
    query: str
    category: TestCategory
    complexity: ComplexityLevel
    language: LanguageCode
    expected_intent: str
    expected_entities: Dict[str, Any]
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GenerationConfig:
    """生成配置"""
    total_cases: int = 1000
    category_distribution: Dict[TestCategory, float] = field(default_factory=dict)
    complexity_distribution: Dict[ComplexityLevel, float] = field(default_factory=dict)
    language_distribution: Dict[LanguageCode, float] = field(default_factory=dict)
    include_edge_cases: bool = True
    edge_case_ratio: float = 0.1
    ensure_diversity: bool = True
    max_similarity_threshold: float = 0.8


class QuickTestCaseGenerator:
    """快速測試案例生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.templates = self._load_templates()
        self.entities = self._load_entities()
        self.generated_cases = []
        self.generation_stats = {}
    
    def _load_templates(self) -> Dict[TestCategory, Dict[ComplexityLevel, List[str]]]:
        """載入測試案例模板"""
        templates = {
            TestCategory.JOB_SEARCH: {
                ComplexityLevel.SIMPLE: [
                    "我想找{job_title}的工作",
                    "有{job_title}的職缺嗎",
                    "幫我搜尋{job_title}工作",
                    "找{location}的{job_title}工作",
                    "我要應徵{job_title}"
                ],
                ComplexityLevel.MODERATE: [
                    "我想在{location}找{job_title}的工作，薪水要{salary_range}",
                    "有沒有{company_type}公司的{job_title}職缺",
                    "我有{experience_years}年{skill}經驗，想找{job_title}工作",
                    "尋找{work_type}的{job_title}職位，地點在{location}",
                    "我想轉職到{job_title}，需要什麼條件"
                ],
                ComplexityLevel.COMPLEX: [
                    "我目前是{current_job}，想轉職到{target_job}，有{experience_years}年經驗，希望在{location}找到薪水{salary_range}的{work_type}工作",
                    "尋找{location}地區的{job_title}職位，要求{skill_list}技能，公司規模{company_size}，薪資範圍{salary_range}",
                    "我是{education_level}畢業，主修{major}，有{experience_years}年{industry}經驗，想在{location}找{job_title}工作",
                    "希望找到{company_type}的{job_title}職位，工作地點{location}，薪水{salary_range}，工作型態{work_type}"
                ],
                ComplexityLevel.EXTREME: [
                    "我是{education_level}{major}畢業，目前在{current_company}擔任{current_job}已{experience_years}年，專精{skill_list}，因為{reason}想轉職到{target_industry}的{target_job}，希望在{location}找到{company_type}公司，薪資{salary_range}，工作型態{work_type}，有{benefit_list}福利",
                    "尋找符合以下條件的工作：職位{job_title}，地點{location}，薪資{salary_range}，公司{company_type}，規模{company_size}，工作型態{work_type}，需要{skill_list}技能，{experience_years}年以上經驗，提供{benefit_list}福利"
                ]
            },
            TestCategory.SKILL_QUERY: {
                ComplexityLevel.SIMPLE: [
                    "{skill}是什麼",
                    "我需要學{skill}嗎",
                    "{skill}怎麼學",
                    "{skill}有用嗎",
                    "學{skill}要多久"
                ],
                ComplexityLevel.MODERATE: [
                    "學{skill}對{job_title}有幫助嗎",
                    "{skill}和{skill2}哪個比較重要",
                    "我想學{skill}，有推薦的課程嗎",
                    "{job_title}需要什麼技能",
                    "如何提升{skill}能力"
                ],
                ComplexityLevel.COMPLEX: [
                    "我想從{current_job}轉職到{target_job}，需要學習哪些{skill_category}技能",
                    "在{industry}工作，{skill_list}這些技能的重要性排序是什麼",
                    "我有{experience_years}年{current_skill}經驗，想學{target_skill}轉職到{target_job}"
                ],
                ComplexityLevel.EXTREME: [
                    "我目前掌握{current_skill_list}技能，在{current_industry}有{experience_years}年經驗，想轉入{target_industry}擔任{target_job}，請分析我需要補強哪些技能，學習順序和時間規劃",
                    "比較{skill_list}這些技能在{industry_list}不同產業中的應用和重要性，並給出學習建議"
                ]
            },
            TestCategory.LOCATION_SEARCH: {
                ComplexityLevel.SIMPLE: [
                    "{location}有工作嗎",
                    "我想在{location}工作",
                    "{location}的工作機會",
                    "搬到{location}工作好嗎",
                    "{location}工作環境如何"
                ],
                ComplexityLevel.MODERATE: [
                    "{location}的{job_title}工作多嗎",
                    "比較{location1}和{location2}的工作機會",
                    "{location}的{industry}發展如何",
                    "在{location}工作的生活成本",
                    "{location}適合{job_title}發展嗎"
                ],
                ComplexityLevel.COMPLEX: [
                    "我想在{location_list}中選一個地方發展{job_title}職涯，請比較各地的機會和生活品質",
                    "分析{location}的{industry}產業發展趨勢和{job_title}職位需求",
                    "考慮薪資、生活成本、發展機會，{location1}和{location2}哪個更適合{job_title}"
                ],
                ComplexityLevel.EXTREME: [
                    "我在考慮{location_list}這些城市發展{job_title}職涯，請從薪資水平、生活成本、產業發展、工作機會、生活品質等角度進行全面比較分析",
                    "分析{location}在未來{years}年內{industry}產業的發展潛力，以及對{job_title}職位的影響"
                ]
            },
            TestCategory.SALARY_INQUIRY: {
                ComplexityLevel.SIMPLE: [
                    "{job_title}薪水多少",
                    "我的薪水合理嗎",
                    "{location}薪水水平",
                    "如何談薪水",
                    "薪水太低怎麼辦"
                ],
                ComplexityLevel.MODERATE: [
                    "{location}的{job_title}平均薪資",
                    "有{experience_years}年經驗的{job_title}薪水",
                    "{company_type}的{job_title}薪資範圍",
                    "我的薪水{current_salary}在市場上如何",
                    "如何要求加薪到{target_salary}"
                ],
                ComplexityLevel.COMPLEX: [
                    "比較{location1}和{location2}的{job_title}薪資差異，考慮生活成本",
                    "我有{skill_list}技能，{experience_years}年經驗，在{location}做{job_title}應該拿多少薪水",
                    "分析{industry}中{job_title}的薪資成長趨勢"
                ],
                ComplexityLevel.EXTREME: [
                    "我目前{current_salary}，在{current_location}做{current_job}，想轉職到{target_location}的{target_job}，請分析薪資變化和談判策略",
                    "比較{job_list}這些職位在{location_list}不同城市的薪資水平，考慮技能要求、經驗需求、生活成本等因素"
                ]
            },
            TestCategory.EDGE_CASE: {
                ComplexityLevel.SIMPLE: [
                    "我想找工作但不知道做什麼",
                    "完全沒經驗可以找工作嗎",
                    "我50歲了還能找工作嗎",
                    "沒有學歷能工作嗎",
                    "我想在家工作"
                ],
                ComplexityLevel.MODERATE: [
                    "我被裁員了，現在該怎麼辦",
                    "懷孕期間可以找工作嗎",
                    "我有犯罪紀錄，能找到工作嗎",
                    "身體有殘疾，工作選擇有限嗎",
                    "我想創業但沒資金"
                ],
                ComplexityLevel.COMPLEX: [
                    "我已經失業一年了，履歷空白期怎麼解釋",
                    "我想轉行但完全沒相關經驗，該如何開始",
                    "因為家庭因素需要頻繁請假，什麼工作適合",
                    "我有社交恐懼症，適合什麼工作"
                ],
                ComplexityLevel.EXTREME: [
                    "我是單親媽媽，需要彈性工時，沒有高學歷，有什麼工作選擇",
                    "我有憂鬱症病史，工作經常中斷，現在想重新開始職涯",
                    "我因為照顧家人離開職場5年，現在想重返職場但技能已經落後"
                ]
            }
        }
        
        # 為其他類別添加基本模板
        for category in TestCategory:
            if category not in templates:
                templates[category] = {
                    ComplexityLevel.SIMPLE: [f"關於{category.value}的簡單問題"],
                    ComplexityLevel.MODERATE: [f"關於{category.value}的中等問題"],
                    ComplexityLevel.COMPLEX: [f"關於{category.value}的複雜問題"],
                    ComplexityLevel.EXTREME: [f"關於{category.value}的極端問題"]
                }
        
        return templates
    
    def _load_entities(self) -> Dict[str, List[str]]:
        """載入實體數據"""
        return {
            'job_title': [
                '軟體工程師', '資料科學家', '產品經理', '設計師', '行銷專員',
                '業務代表', '人資專員', '財務分析師', '專案經理', '客服專員',
                '前端工程師', '後端工程師', '全端工程師', 'DevOps工程師', 'QA工程師',
                'UI/UX設計師', '數位行銷專員', '社群媒體經理', '內容編輯', '翻譯員'
            ],
            'location': [
                '台北', '新北', '桃園', '台中', '台南', '高雄',
                '新竹', '基隆', '宜蘭', '花蓮', '台東', '屏東',
                '信義區', '大安區', '中山區', '松山區', '內湖區', '南港區',
                '美國', '日本', '新加坡', '香港', '上海', '深圳'
            ],
            'skill': [
                'Python', 'JavaScript', 'Java', 'C++', 'React', 'Vue.js',
                'Node.js', 'Django', 'Flask', 'Spring Boot', 'Docker', 'Kubernetes',
                'AWS', 'Azure', 'GCP', 'MySQL', 'PostgreSQL', 'MongoDB',
                'Git', 'Jenkins', 'Terraform', 'Ansible', '機器學習', '深度學習',
                '數據分析', 'Excel', 'PowerBI', 'Tableau', 'Photoshop', 'Illustrator',
                '專案管理', '溝通技巧', '領導能力', '問題解決', '創意思考'
            ],
            'company_type': [
                '新創公司', '中小企業', '大型企業', '外商公司', '本土企業',
                '科技公司', '金融業', '製造業', '服務業', '零售業',
                '非營利組織', '政府機關', '學術機構', '醫療機構', '媒體業'
            ],
            'industry': [
                '科技業', '金融業', '製造業', '服務業', '零售業', '醫療業',
                '教育業', '媒體業', '遊戲業', '電商業', '物流業', '房地產業',
                '能源業', '農業', '觀光業', '餐飲業', '時尚業', '汽車業'
            ],
            'work_type': [
                '全職', '兼職', '遠端工作', '混合辦公', '契約工作', '自由接案',
                '實習', '工讀', '臨時工', '顧問', '派遣', '輪班制'
            ],
            'salary_range': [
                '30-40K', '40-50K', '50-60K', '60-80K', '80-100K', '100-120K',
                '120-150K', '150-200K', '200K以上', '面議', '依經驗調整'
            ],
            'experience_years': [
                '0-1年', '1-3年', '3-5年', '5-8年', '8-10年', '10年以上',
                '應屆畢業', '有經驗', '資深', '專家級'
            ],
            'education_level': [
                '高中', '專科', '大學', '碩士', '博士', '技職', '自學'
            ],
            'major': [
                '資訊工程', '電機工程', '機械工程', '工業工程', '企業管理',
                '財務金融', '會計', '行銷', '心理學', '設計', '外語', '數學',
                '統計', '經濟', '法律', '醫學', '護理', '教育', '新聞傳播'
            ]
        }
    
    def generate_test_cases(self, config: GenerationConfig) -> List[TestCase]:
        """生成測試案例"""
        print(f"🚀 開始生成 {config.total_cases} 個測試案例")
        
        # 設置默認分佈
        if not config.category_distribution:
            config.category_distribution = self._get_default_category_distribution()
        
        if not config.complexity_distribution:
            config.complexity_distribution = self._get_default_complexity_distribution()
        
        if not config.language_distribution:
            config.language_distribution = self._get_default_language_distribution()
        
        # 計算各類別的案例數量
        category_counts = self._calculate_category_counts(config)
        
        # 生成案例
        generated_cases = []
        
        for category, count in category_counts.items():
            print(f"   生成 {category.value}: {count} 個案例")
            
            category_cases = self._generate_category_cases(
                category, count, config
            )
            generated_cases.extend(category_cases)
        
        # 確保多樣性
        if config.ensure_diversity:
            generated_cases = self._ensure_diversity(
                generated_cases, config.max_similarity_threshold
            )
        
        # 調整到目標數量
        if len(generated_cases) != config.total_cases:
            generated_cases = self._adjust_to_target_count(
                generated_cases, config.total_cases
            )
        
        # 隨機打亂
        random.shuffle(generated_cases)
        
        self.generated_cases = generated_cases
        self._calculate_generation_stats()
        
        print(f"✅ 成功生成 {len(generated_cases)} 個測試案例")
        
        return generated_cases
    
    def _get_default_category_distribution(self) -> Dict[TestCategory, float]:
        """獲取默認類別分佈"""
        return {
            TestCategory.JOB_SEARCH: 0.25,
            TestCategory.SKILL_QUERY: 0.15,
            TestCategory.LOCATION_SEARCH: 0.12,
            TestCategory.SALARY_INQUIRY: 0.12,
            TestCategory.CAREER_ADVICE: 0.10,
            TestCategory.COMPANY_INFO: 0.08,
            TestCategory.INTERVIEW_PREP: 0.08,
            TestCategory.RESUME_HELP: 0.05,
            TestCategory.GENERAL_CHAT: 0.03,
            TestCategory.EDGE_CASE: 0.02
        }
    
    def _get_default_complexity_distribution(self) -> Dict[ComplexityLevel, float]:
        """獲取默認複雜度分佈"""
        return {
            ComplexityLevel.SIMPLE: 0.3,
            ComplexityLevel.MODERATE: 0.4,
            ComplexityLevel.COMPLEX: 0.25,
            ComplexityLevel.EXTREME: 0.05
        }
    
    def _get_default_language_distribution(self) -> Dict[LanguageCode, float]:
        """獲取默認語言分佈"""
        return {
            LanguageCode.ZH_TW: 0.6,
            LanguageCode.EN_US: 0.25,
            LanguageCode.ZH_CN: 0.1,
            LanguageCode.JA_JP: 0.03,
            LanguageCode.KO_KR: 0.02
        }
    
    def _calculate_category_counts(self, config: GenerationConfig) -> Dict[TestCategory, int]:
        """計算各類別案例數量"""
        category_counts = {}
        remaining_cases = config.total_cases
        
        # 按分佈計算
        for category, ratio in config.category_distribution.items():
            count = int(config.total_cases * ratio)
            category_counts[category] = count
            remaining_cases -= count
        
        # 分配剩餘案例
        if remaining_cases > 0:
            categories = list(category_counts.keys())
            for i in range(remaining_cases):
                category = categories[i % len(categories)]
                category_counts[category] += 1
        
        return category_counts
    
    def _generate_category_cases(self, category: TestCategory, count: int, 
                               config: GenerationConfig) -> List[TestCase]:
        """生成特定類別的案例"""
        cases = []
        
        for _ in range(count):
            # 選擇複雜度
            complexity = self._choose_complexity(config.complexity_distribution)
            
            # 選擇語言
            language = self._choose_language(config.language_distribution)
            
            # 生成案例
            test_case = self._generate_single_case(category, complexity, language)
            
            if test_case:
                cases.append(test_case)
        
        return cases
    
    def _choose_complexity(self, distribution: Dict[ComplexityLevel, float]) -> ComplexityLevel:
        """選擇複雜度"""
        return random.choices(
            list(distribution.keys()),
            weights=list(distribution.values())
        )[0]
    
    def _choose_language(self, distribution: Dict[LanguageCode, float]) -> LanguageCode:
        """選擇語言"""
        return random.choices(
            list(distribution.keys()),
            weights=list(distribution.values())
        )[0]
    
    def _generate_single_case(self, category: TestCategory, 
                            complexity: ComplexityLevel, 
                            language: LanguageCode) -> Optional[TestCase]:
        """生成單個測試案例"""
        try:
            # 獲取模板
            templates = self.templates.get(category, {}).get(complexity, [])
            if not templates:
                return None
            
            template = random.choice(templates)
            
            # 填充模板
            query = self._fill_template(template, language)
            
            # 生成預期結果
            expected_intent = self._generate_expected_intent(category, complexity)
            expected_entities = self._extract_entities_from_query(query)
            
            # 創建測試案例
            test_case = TestCase(
                test_id=str(uuid.uuid4()),
                query=query,
                category=category,
                complexity=complexity,
                language=language,
                expected_intent=expected_intent,
                expected_entities=expected_entities,
                metadata={
                    'template': template,
                    'generated_at': datetime.now().isoformat()
                }
            )
            
            return test_case
            
        except Exception as e:
            print(f"⚠️ 生成案例失敗: {e}")
            return None
    
    def _fill_template(self, template: str, language: LanguageCode) -> str:
        """填充模板"""
        # 找出模板中的佔位符
        import re
        placeholders = re.findall(r'\{([^}]+)\}', template)
        
        filled_template = template
        
        for placeholder in placeholders:
            # 處理列表類型的佔位符
            if '_list' in placeholder:
                base_key = placeholder.replace('_list', '')
                if base_key in self.entities:
                    # 選擇2-4個實體
                    count = random.randint(2, 4)
                    selected = random.sample(self.entities[base_key], min(count, len(self.entities[base_key])))
                    value = '、'.join(selected)
                else:
                    value = placeholder
            else:
                # 單個實體
                if placeholder in self.entities:
                    value = random.choice(self.entities[placeholder])
                else:
                    value = placeholder
            
            filled_template = filled_template.replace(f'{{{placeholder}}}', value)
        
        # 根據語言調整
        if language != LanguageCode.ZH_TW:
            filled_template = self._translate_query(filled_template, language)
        
        return filled_template
    
    def _translate_query(self, query: str, target_language: LanguageCode) -> str:
        """翻譯查詢（簡化版）"""
        # 這裡是簡化的翻譯邏輯，實際應用中可以使用翻譯API
        translations = {
            LanguageCode.EN_US: {
                '我想找': 'I want to find',
                '工作': 'job',
                '的': '',
                '有': 'Are there any',
                '嗎': '?',
                '幫我搜尋': 'Help me search for',
                '薪水': 'salary',
                '多少': 'how much',
                '技能': 'skills',
                '學習': 'learn',
                '經驗': 'experience'
            },
            LanguageCode.ZH_CN: {
                '台北': '北京',
                '台中': '上海',
                '高雄': '深圳',
                '新台幣': '人民币',
                '職缺': '职位'
            }
        }
        
        if target_language in translations:
            for zh_word, translated in translations[target_language].items():
                query = query.replace(zh_word, translated)
        
        return query
    
    def _generate_expected_intent(self, category: TestCategory, 
                                complexity: ComplexityLevel) -> str:
        """生成預期意圖"""
        intent_mapping = {
            TestCategory.JOB_SEARCH: 'job_search',
            TestCategory.SKILL_QUERY: 'skill_inquiry',
            TestCategory.LOCATION_SEARCH: 'location_search',
            TestCategory.SALARY_INQUIRY: 'salary_inquiry',
            TestCategory.CAREER_ADVICE: 'career_advice',
            TestCategory.COMPANY_INFO: 'company_inquiry',
            TestCategory.INTERVIEW_PREP: 'interview_help',
            TestCategory.RESUME_HELP: 'resume_assistance',
            TestCategory.GENERAL_CHAT: 'general_conversation',
            TestCategory.EDGE_CASE: 'edge_case_handling'
        }
        
        base_intent = intent_mapping.get(category, 'unknown')
        
        # 根據複雜度調整
        if complexity == ComplexityLevel.COMPLEX:
            base_intent += '_complex'
        elif complexity == ComplexityLevel.EXTREME:
            base_intent += '_extreme'
        
        return base_intent
    
    def _extract_entities_from_query(self, query: str) -> Dict[str, Any]:
        """從查詢中提取實體"""
        entities = {}
        
        # 簡化的實體提取邏輯
        for entity_type, entity_list in self.entities.items():
            for entity in entity_list:
                if entity in query:
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(entity)
        
        return entities
    
    def _ensure_diversity(self, cases: List[TestCase], 
                        threshold: float) -> List[TestCase]:
        """確保多樣性"""
        # 簡化的多樣性檢查
        unique_cases = []
        seen_queries = set()
        
        for case in cases:
            # 簡化的相似度檢查
            query_words = set(case.query.split())
            
            is_similar = False
            for seen_query in seen_queries:
                seen_words = set(seen_query.split())
                
                if query_words and seen_words:
                    similarity = len(query_words & seen_words) / len(query_words | seen_words)
                    if similarity > threshold:
                        is_similar = True
                        break
            
            if not is_similar:
                unique_cases.append(case)
                seen_queries.add(case.query)
        
        return unique_cases
    
    def _adjust_to_target_count(self, cases: List[TestCase], 
                              target_count: int) -> List[TestCase]:
        """調整到目標數量"""
        if len(cases) == target_count:
            return cases
        elif len(cases) > target_count:
            # 隨機選擇
            return random.sample(cases, target_count)
        else:
            # 需要生成更多案例
            additional_needed = target_count - len(cases)
            
            # 複製現有案例並稍作修改
            additional_cases = []
            for i in range(additional_needed):
                base_case = random.choice(cases)
                
                # 創建變體
                variant = self._create_variant(base_case)
                additional_cases.append(variant)
            
            return cases + additional_cases
    
    def _create_variant(self, base_case: TestCase) -> TestCase:
        """創建案例變體"""
        # 簡單的變體生成
        variant_query = base_case.query
        
        # 隨機替換一些實體
        for entity_type, entity_list in self.entities.items():
            for entity in entity_list:
                if entity in variant_query:
                    # 有30%機率替換
                    if random.random() < 0.3:
                        new_entity = random.choice(entity_list)
                        variant_query = variant_query.replace(entity, new_entity, 1)
                        break
        
        variant = TestCase(
            test_id=str(uuid.uuid4()),
            query=variant_query,
            category=base_case.category,
            complexity=base_case.complexity,
            language=base_case.language,
            expected_intent=base_case.expected_intent,
            expected_entities=self._extract_entities_from_query(variant_query),
            metadata={
                'variant_of': base_case.test_id,
                'generated_at': datetime.now().isoformat()
            }
        )
        
        return variant
    
    def _calculate_generation_stats(self) -> None:
        """計算生成統計"""
        if not self.generated_cases:
            return
        
        # 類別統計
        category_stats = {}
        for category in TestCategory:
            count = sum(1 for case in self.generated_cases if case.category == category)
            category_stats[category.value] = count
        
        # 複雜度統計
        complexity_stats = {}
        for complexity in ComplexityLevel:
            count = sum(1 for case in self.generated_cases if case.complexity == complexity)
            complexity_stats[complexity.value] = count
        
        # 語言統計
        language_stats = {}
        for language in LanguageCode:
            count = sum(1 for case in self.generated_cases if case.language == language)
            language_stats[language.value] = count
        
        self.generation_stats = {
            'total_cases': len(self.generated_cases),
            'category_distribution': category_stats,
            'complexity_distribution': complexity_stats,
            'language_distribution': language_stats,
            'generation_time': datetime.now().isoformat()
        }
    
    def export_test_cases(self, file_path: str, format_type: str = 'json') -> None:
        """導出測試案例"""
        if not self.generated_cases:
            print("❌ 沒有可導出的測試案例")
            return
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type.lower() == 'json':
            self._export_json(file_path)
        elif format_type.lower() == 'csv':
            self._export_csv(file_path)
        else:
            print(f"❌ 不支援的格式: {format_type}")
            return
        
        print(f"✅ 測試案例已導出至: {file_path}")
    
    def _export_json(self, file_path: Path) -> None:
        """導出為JSON格式"""
        data = {
            'metadata': {
                'total_cases': len(self.generated_cases),
                'generation_time': datetime.now().isoformat(),
                'generator_version': '1.0.0'
            },
            'statistics': self.generation_stats,
            'test_cases': []
        }
        
        for case in self.generated_cases:
            case_data = {
                'test_id': case.test_id,
                'query': case.query,
                'category': case.category.value,
                'complexity': case.complexity.value,
                'language': case.language.value,
                'expected_intent': case.expected_intent,
                'expected_entities': case.expected_entities,
                'context': case.context,
                'metadata': case.metadata,
                'created_at': case.created_at.isoformat()
            }
            data['test_cases'].append(case_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_csv(self, file_path: Path) -> None:
        """導出為CSV格式"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 寫入標題
            headers = [
                'test_id', 'query', 'category', 'complexity', 'language',
                'expected_intent', 'expected_entities', 'context', 'created_at'
            ]
            writer.writerow(headers)
            
            # 寫入數據
            for case in self.generated_cases:
                row = [
                    case.test_id,
                    case.query,
                    case.category.value,
                    case.complexity.value,
                    case.language.value,
                    case.expected_intent,
                    json.dumps(case.expected_entities, ensure_ascii=False),
                    case.context or '',
                    case.created_at.isoformat()
                ]
                writer.writerow(row)
    
    def print_generation_summary(self) -> None:
        """打印生成摘要"""
        if not self.generation_stats:
            print("❌ 沒有生成統計數據")
            return
        
        print("\n" + "="*60)
        print("📊 測試案例生成摘要")
        print("="*60)
        
        print(f"\n📈 總體統計:")
        print(f"   總案例數: {self.generation_stats['total_cases']}")
        print(f"   生成時間: {self.generation_stats['generation_time']}")
        
        print(f"\n📂 類別分佈:")
        for category, count in self.generation_stats['category_distribution'].items():
            percentage = (count / self.generation_stats['total_cases']) * 100
            print(f"   {category}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 複雜度分佈:")
        for complexity, count in self.generation_stats['complexity_distribution'].items():
            percentage = (count / self.generation_stats['total_cases']) * 100
            print(f"   {complexity}: {count} ({percentage:.1f}%)")
        
        print(f"\n🌍 語言分佈:")
        for language, count in self.generation_stats['language_distribution'].items():
            percentage = (count / self.generation_stats['total_cases']) * 100
            print(f"   {language}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*60)


def main():
    """主函數"""
    print("🚀 快速測試案例生成器")
    print("專門用於快速生成多樣化的LLM測試案例\n")
    
    generator = QuickTestCaseGenerator()
    
    # 配置生成參數
    print("⚙️ 配置生成參數:")
    
    try:
        total_cases = int(input("測試案例總數 (預設1000): ") or "1000")
        total_cases = max(100, min(10000, total_cases))  # 限制範圍
    except ValueError:
        total_cases = 1000
        print("   使用預設值: 1000")
    
    # 選擇生成模式
    print("\n🎯 選擇生成模式:")
    print("   1. 平衡模式 (各類別平均分佈)")
    print("   2. 求職導向 (重點生成求職相關案例)")
    print("   3. 技能導向 (重點生成技能查詢案例)")
    print("   4. 多語言模式 (增加多語言案例)")
    print("   5. 邊界案例模式 (增加邊界案例)")
    print("   6. 自定義模式")
    
    try:
        mode_choice = int(input("請選擇模式 (預設1): ") or "1")
    except ValueError:
        mode_choice = 1
    
    # 創建配置
    config = GenerationConfig(total_cases=total_cases)
    
    if mode_choice == 2:  # 求職導向
        config.category_distribution = {
            TestCategory.JOB_SEARCH: 0.4,
            TestCategory.SKILL_QUERY: 0.2,
            TestCategory.SALARY_INQUIRY: 0.15,
            TestCategory.LOCATION_SEARCH: 0.1,
            TestCategory.CAREER_ADVICE: 0.1,
            TestCategory.INTERVIEW_PREP: 0.05
        }
    elif mode_choice == 3:  # 技能導向
        config.category_distribution = {
            TestCategory.SKILL_QUERY: 0.5,
            TestCategory.JOB_SEARCH: 0.2,
            TestCategory.CAREER_ADVICE: 0.15,
            TestCategory.INTERVIEW_PREP: 0.1,
            TestCategory.RESUME_HELP: 0.05
        }
    elif mode_choice == 4:  # 多語言模式
        config.language_distribution = {
            LanguageCode.ZH_TW: 0.3,
            LanguageCode.EN_US: 0.3,
            LanguageCode.ZH_CN: 0.2,
            LanguageCode.JA_JP: 0.1,
            LanguageCode.KO_KR: 0.1
        }
    elif mode_choice == 5:  # 邊界案例模式
        config.category_distribution = {
            TestCategory.EDGE_CASE: 0.3,
            TestCategory.JOB_SEARCH: 0.25,
            TestCategory.SKILL_QUERY: 0.15,
            TestCategory.CAREER_ADVICE: 0.15,
            TestCategory.SALARY_INQUIRY: 0.1,
            TestCategory.LOCATION_SEARCH: 0.05
        }
        config.complexity_distribution = {
            ComplexityLevel.COMPLEX: 0.4,
            ComplexityLevel.EXTREME: 0.3,
            ComplexityLevel.MODERATE: 0.2,
            ComplexityLevel.SIMPLE: 0.1
        }
    elif mode_choice == 6:  # 自定義模式
        print("\n⚙️ 自定義配置 (直接按Enter使用預設值):")
        
        try:
            edge_ratio = float(input("邊界案例比例 (0.0-1.0, 預設0.1): ") or "0.1")
            config.edge_case_ratio = max(0.0, min(1.0, edge_ratio))
            
            diversity_choice = input("確保多樣性? (Y/n): ").strip().lower()
            config.ensure_diversity = diversity_choice != 'n'
            
            if config.ensure_diversity:
                similarity_threshold = float(input("相似度閾值 (0.0-1.0, 預設0.8): ") or "0.8")
                config.max_similarity_threshold = max(0.0, min(1.0, similarity_threshold))
        
        except ValueError:
            print("   使用預設配置")
    
    # 生成測試案例
    print(f"\n🚀 開始生成測試案例...")
    test_cases = generator.generate_test_cases(config)
    
    # 打印摘要
    generator.print_generation_summary()
    
    # 導出選項
    print("\n💾 導出選項:")
    export_choice = input("是否導出測試案例? (Y/n): ").strip().lower()
    
    if export_choice != 'n':
        output_dir = input("輸出目錄 (預設: test_cases): ").strip() or "test_cases"
        
        format_choice = input("導出格式 (json/csv, 預設json): ").strip().lower() or "json"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_test_cases_{timestamp}.{format_choice}"
        file_path = Path(output_dir) / filename
        
        generator.export_test_cases(str(file_path), format_choice)
        
        # 生成統計報告
        stats_file = Path(output_dir) / f"generation_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(generator.generation_stats, f, ensure_ascii=False, indent=2)
        
        print(f"📊 統計報告已保存至: {stats_file}")
    
    print("\n🎉 測試案例生成完成!")
    print("\n💡 使用建議:")
    print("   • 可以將生成的測試案例用於LLM模型對比測試")
    print("   • 建議定期生成新的測試案例以保持測試的時效性")
    print("   • 可以根據實際需求調整類別和複雜度分佈")


if __name__ == "__main__":
    main()