# -*- coding: utf-8 -*-
"""
純英文轉換器模組
用於將中英文混雜的測試案例轉換為純英文版本
"""

import json
import re
from typing import Dict, List, Any

class EnglishTranslator:
    """
    純英文轉換器類別
    負責將中英文混雜的測試案例轉換為純英文版本
    """
    
    def __init__(self):
        """
        初始化轉換器，設定翻譯映射表
        """
        # 類別翻譯映射
        self.category_mapping = {
            '工作搜尋': 'job_search',
            '簡歷優化': 'resume_optimization', 
            '面試準備': 'interview_preparation',
            '職業發展': 'career_development',
            '薪資談判': 'salary_negotiation',
            '技能提升': 'skill_enhancement',
            '網絡建設': 'networking',
            '行業分析': 'industry_analysis'
        }
        
        # 複雜度翻譯映射
        self.complexity_mapping = {
            '簡單': 'simple',
            '中等': 'medium', 
            '複雜': 'complex'
        }
        
        # 語言代碼映射
        self.language_mapping = {
            'zh': 'en',
            'zh-TW': 'en',
            'zh-CN': 'en'
        }
        
        # 意圖翻譯映射
        self.intent_mapping = {
            '搜尋工作': 'search_jobs',
            '尋找職位': 'find_positions',
            '查詢薪資': 'query_salary',
            '了解公司': 'learn_about_company',
            '準備面試': 'prepare_interview',
            '優化簡歷': 'optimize_resume',
            '技能學習': 'learn_skills',
            '職業規劃': 'career_planning',
            '行業趨勢': 'industry_trends',
            '網絡拓展': 'expand_network'
        }
        
        # 常見中文詞彙翻譯映射
        self.common_translations = {
            # 職位相關
            '軟體工程師': 'software engineer',
            '資料科學家': 'data scientist', 
            '產品經理': 'product manager',
            '設計師': 'designer',
            '行銷專員': 'marketing specialist',
            '業務代表': 'sales representative',
            '人力資源': 'human resources',
            '財務分析師': 'financial analyst',
            
            # 技能相關
            'Python程式設計': 'Python programming',
            '機器學習': 'machine learning',
            '人工智慧': 'artificial intelligence',
            '資料分析': 'data analysis',
            '網頁開發': 'web development',
            '行動應用開發': 'mobile app development',
            '雲端運算': 'cloud computing',
            '網路安全': 'cybersecurity',
            
            # 公司相關
            '科技公司': 'technology company',
            '新創公司': 'startup company',
            '跨國企業': 'multinational corporation',
            '金融機構': 'financial institution',
            '諮詢公司': 'consulting firm',
            
            # 地點相關
            '台北': 'Taipei',
            '台灣': 'Taiwan',
            '美國': 'United States',
            '矽谷': 'Silicon Valley',
            '紐約': 'New York',
            '舊金山': 'San Francisco',
            
            # 其他常見詞彙
            '遠端工作': 'remote work',
            '全職': 'full-time',
            '兼職': 'part-time',
            '實習': 'internship',
            '合約工作': 'contract work',
            '薪資範圍': 'salary range',
            '工作經驗': 'work experience',
            '學歷要求': 'education requirements'
        }
    
    def translate_query(self, query: str) -> str:
        """
        翻譯查詢字串為英文
        
        Args:
            query: 原始查詢字串（可能包含中文）
            
        Returns:
            翻譯後的英文查詢字串
        """
        translated_query = query
        
        # 使用常見翻譯映射進行替換
        for chinese, english in self.common_translations.items():
            translated_query = translated_query.replace(chinese, english)
        
        # 移除或替換常見的中文字符
        # 這裡可以添加更複雜的翻譯邏輯
        chinese_patterns = {
            r'在(.+?)工作': r'work at \1',
            r'(.+?)的薪資': r'salary of \1',
            r'如何成為(.+?)': r'how to become \1',
            r'(.+?)面試技巧': r'\1 interview tips',
            r'(.+?)職業發展': r'\1 career development'
        }
        
        for pattern, replacement in chinese_patterns.items():
            translated_query = re.sub(pattern, replacement, translated_query)
        
        return translated_query
    
    def translate_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻譯實體字典為英文
        
        Args:
            entities: 原始實體字典
            
        Returns:
            翻譯後的英文實體字典
        """
        translated_entities = {}
        
        for key, value in entities.items():
            # 翻譯鍵名
            translated_key = key
            if key in self.common_translations:
                translated_key = self.common_translations[key]
            
            # 翻譯值
            if isinstance(value, str):
                translated_value = value
                for chinese, english in self.common_translations.items():
                    translated_value = translated_value.replace(chinese, english)
                translated_entities[translated_key] = translated_value
            elif isinstance(value, list):
                translated_list = []
                for item in value:
                    if isinstance(item, str):
                        translated_item = item
                        for chinese, english in self.common_translations.items():
                            translated_item = translated_item.replace(chinese, english)
                        translated_list.append(translated_item)
                    else:
                        translated_list.append(item)
                translated_entities[translated_key] = translated_list
            else:
                translated_entities[translated_key] = value
        
        return translated_entities
    
    def translate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻譯元數據字典為英文
        
        Args:
            metadata: 原始元數據字典
            
        Returns:
            翻譯後的英文元數據字典
        """
        translated_metadata = {}
        
        for key, value in metadata.items():
            # 翻譯鍵名
            translated_key = key
            key_translations = {
                '創建時間': 'created_time',
                '更新時間': 'updated_time',
                '標籤': 'tags',
                '優先級': 'priority',
                '來源': 'source',
                '版本': 'version'
            }
            if key in key_translations:
                translated_key = key_translations[key]
            
            # 翻譯值
            if isinstance(value, str):
                translated_value = value
                for chinese, english in self.common_translations.items():
                    translated_value = translated_value.replace(chinese, english)
                translated_metadata[translated_key] = translated_value
            elif isinstance(value, list):
                translated_list = []
                for item in value:
                    if isinstance(item, str):
                        translated_item = item
                        for chinese, english in self.common_translations.items():
                            translated_item = translated_item.replace(chinese, english)
                        translated_list.append(translated_item)
                    else:
                        translated_list.append(item)
                translated_metadata[translated_key] = translated_list
            else:
                translated_metadata[translated_key] = value
        
        return translated_metadata
    
    def translate_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻譯單個測試案例為純英文版本
        
        Args:
            test_case: 原始測試案例字典
            
        Returns:
            翻譯後的純英文測試案例字典
        """
        translated_case = {
            'id': test_case.get('id', ''),
            'query': self.translate_query(test_case.get('query', '')),
            'category': self.category_mapping.get(test_case.get('category', ''), test_case.get('category', '')),
            'complexity': self.complexity_mapping.get(test_case.get('complexity', ''), test_case.get('complexity', '')),
            'language': self.language_mapping.get(test_case.get('language', 'zh'), 'en'),
            'expected_intent': self.intent_mapping.get(test_case.get('expected_intent', ''), test_case.get('expected_intent', '')),
            'expected_entities': self.translate_entities(test_case.get('expected_entities', {})),
            'metadata': self.translate_metadata(test_case.get('metadata', {}))
        }
        
        return translated_case
    
    def translate_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        翻譯測試案例列表為純英文版本
        
        Args:
            test_cases: 原始測試案例列表
            
        Returns:
            翻譯後的純英文測試案例列表
        """
        return [self.translate_test_case(case) for case in test_cases]