#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM意圖分析修復驗證測試
測試修復後的LLM意圖分析功能，特別關注之前失敗的案例
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer
from jobseeker.intelligent_decision_engine import IntelligentDecisionEngine

class LLMFixTester:
    """LLM意圖分析修復測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.analyzer = LLMIntentAnalyzer()
        self.decision_engine = IntelligentDecisionEngine()
        self.test_results = []
        
    def run_comprehensive_test(self):
        """運行全面測試"""
        print("🔧 LLM意圖分析修復驗證測試")
        print("=" * 50)
        
        # 測試案例分組
        test_groups = {
            "之前失敗的案例": [
                {"query": "資料科學家", "location": "高雄", "expected": True},
                {"query": "Data Analyst", "location": "Taichung", "expected": True},
                {"query": "UI/UX設計師", "location": "台中", "expected": True},
                {"query": "軟體工程師", "location": "台北", "expected": True},
                {"query": "前端工程師", "location": "新竹", "expected": True}
            ],
            "明確的求職查詢": [
                {"query": "Python工程師", "location": "台北", "expected": True},
                {"query": "機器學習工程師", "location": "遠程", "expected": True},
                {"query": "產品經理", "location": "台中", "expected": True},
                {"query": "DevOps工程師", "location": "高雄", "expected": True},
                {"query": "全端開發者", "location": "台南", "expected": True}
            ],
            "技能導向查詢": [
                {"query": "React開發", "location": "台北", "expected": True},
                {"query": "Python AI", "location": "新竹", "expected": True},
                {"query": "Java後端", "location": "台中", "expected": True},
                {"query": "Vue.js前端", "location": "高雄", "expected": True}
            ],
            "邊界案例": [
                {"query": "工作", "location": "台北", "expected": True},
                {"query": "職位", "location": "台中", "expected": True},
                {"query": "薪水", "location": "高雄", "expected": False},  # 可能被拒絕
                {"query": "台北", "location": "", "expected": False}  # 只有地點
            ],
            "應該拒絕的案例": [
                {"query": "今天天氣如何", "location": "", "expected": False},
                {"query": "推薦一部電影", "location": "", "expected": False},
                {"query": "晚餐吃什麼", "location": "", "expected": False},
                {"query": "音樂推薦", "location": "", "expected": False}
            ]
        }
        
        # 執行測試
        total_tests = 0
        passed_tests = 0
        
        for group_name, test_cases in test_groups.items():
            print(f"\n📋 測試組: {group_name}")
            print("-" * 30)
            
            group_passed = 0
            for i, test_case in enumerate(test_cases, 1):
                total_tests += 1
                result = self.test_single_case(test_case, f"{group_name}-{i}")
                
                if result['passed']:
                    passed_tests += 1
                    group_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                print(f"  {i}. {test_case['query']} @ {test_case['location']} - {status}")
                if not result['passed']:
                    print(f"     預期: {test_case['expected']}, 實際: {result['actual']}")
                    print(f"     原因: {result['reason']}")
            
            print(f"   組別通過率: {group_passed}/{len(test_cases)} ({group_passed/len(test_cases)*100:.1f}%)")
        
        # 總結
        print(f"\n📊 測試總結")
        print("=" * 50)
        print(f"總測試案例: {total_tests}")
        print(f"通過案例: {passed_tests}")
        print(f"失敗案例: {total_tests - passed_tests}")
        print(f"總通過率: {passed_tests/total_tests*100:.1f}%")
        
        # 保存詳細結果
        self.save_test_results()
        
        return passed_tests / total_tests
    
    def test_single_case(self, test_case: Dict[str, Any], test_id: str) -> Dict[str, Any]:
        """測試單個案例"""
        query = test_case['query']
        location = test_case['location']
        expected = test_case['expected']
        
        # 構建完整查詢
        full_query = f"{query} {location}".strip()
        
        try:
            # 1. 測試LLM意圖分析
            intent_result, decision_result = self.analyzer.analyze_intent_with_decision(full_query)
            
            # 2. 檢查結果
            actual_is_job_related = intent_result.is_job_related
            
            # 3. 判斷是否通過
            passed = (actual_is_job_related == expected)
            
            # 4. 記錄詳細信息
            test_result = {
                'test_id': test_id,
                'query': query,
                'location': location,
                'full_query': full_query,
                'expected': expected,
                'actual': actual_is_job_related,
                'passed': passed,
                'confidence': intent_result.confidence,
                'intent_type': intent_result.intent_type.value if hasattr(intent_result.intent_type, 'value') else str(intent_result.intent_type),
                'reasoning': getattr(intent_result, 'llm_reasoning', 'N/A'),
                'structured_intent': self._serialize_structured_intent(intent_result.structured_intent),
                'decision_strategy': decision_result.strategy.value if decision_result else None,
                'timestamp': datetime.now().isoformat()
            }
            
            if not passed:
                test_result['reason'] = f"預期{expected}但得到{actual_is_job_related}"
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            error_result = {
                'test_id': test_id,
                'query': query,
                'location': location,
                'full_query': full_query,
                'expected': expected,
                'actual': None,
                'passed': False,
                'error': str(e),
                'reason': f"測試執行錯誤: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            return error_result
    
    def test_scoring_mechanism(self):
        """測試評分機制"""
        print("\n🎯 測試評分機制")
        print("=" * 30)
        
        test_queries = [
            "資料科學家 高雄",  # 應該高分
            "Python工程師 台北",  # 應該高分
            "工作 台中",  # 應該中等分數
            "台北",  # 應該低分
            "天氣",  # 應該極低分
        ]
        
        for query in test_queries:
            try:
                # 直接調用內部方法測試評分
                query_lower = query.lower()
                
                # 模擬評分邏輯
                job_keywords = {
                    'job_titles_zh': ['工程師', '科學家', '開發者', '設計師'],
                    'job_titles_en': ['engineer', 'scientist', 'developer', 'designer'],
                    'skills': ['python', 'java', 'javascript', 'react'],
                    'job_verbs': ['工作', '找', '搜尋', 'find', 'search'],
                    'locations': ['台北', '台中', '高雄', 'taipei']
                }
                
                score = self._calculate_score(query_lower, job_keywords)
                print(f"  '{query}' -> 得分: {score:.2f}")
                
            except Exception as e:
                print(f"  '{query}' -> 錯誤: {str(e)}")
    
    def _calculate_score(self, query_lower: str, job_keywords: Dict[str, list]) -> float:
        """計算求職相關性得分 (模擬內部邏輯)"""
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
    
    def _serialize_structured_intent(self, structured_intent):
        """序列化結構化意圖對象為JSON可序列化的字典"""
        if not structured_intent:
            return None
        
        if hasattr(structured_intent, '__dict__'):
            result = {}
            for key, value in structured_intent.__dict__.items():
                if hasattr(value, 'value'):  # 枚舉類型
                    result[key] = value.value
                elif isinstance(value, (list, tuple)):
                    result[key] = list(value)
                else:
                    result[key] = value
            return result
        else:
            return str(structured_intent)
    
    def save_test_results(self):
        """保存測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_fix_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results if r['passed']),
                    'failed_tests': sum(1 for r in self.test_results if not r['passed']),
                    'pass_rate': sum(1 for r in self.test_results if r['passed']) / len(self.test_results) * 100,
                    'timestamp': datetime.now().isoformat()
                },
                'test_results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 測試結果已保存至: {filename}")

def main():
    """主函數"""
    tester = LLMFixTester()
    
    print("開始LLM意圖分析修復驗證測試...")
    
    # 運行全面測試
    pass_rate = tester.run_comprehensive_test()
    
    # 測試評分機制
    tester.test_scoring_mechanism()
    
    # 最終評估
    print(f"\n🎉 修復效果評估")
    print("=" * 30)
    if pass_rate >= 0.85:
        print("✅ 修復效果優秀！通過率達到85%以上")
    elif pass_rate >= 0.70:
        print("⚠️ 修復效果良好，但仍有改進空間")
    else:
        print("❌ 修復效果不佳，需要進一步調整")
    
    print(f"最終通過率: {pass_rate*100:.1f}%")
    
    return pass_rate

if __name__ == "__main__":
    main()