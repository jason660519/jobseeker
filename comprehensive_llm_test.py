#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的LLM指令標準測試
包含更多測試案例來驗證LLM指令的穩定性和準確性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from datetime import datetime
import json

def run_comprehensive_test():
    """
    運行全面測試
    """
    print("🚀 開始全面LLM指令標準測試")
    print("=" * 50)
    
    # 初始化分析器
    analyzer = LLMIntentAnalyzer(provider=LLMProvider.OPENAI_GPT35)
    
    # 全面測試案例
    test_cases = [
        # 明確求職查詢
        {
            "category": "明確求職查詢",
            "description": "完整職位+地點",
            "query": "Python工程師 台北",
            "expected_job_related": True
        },
        {
            "category": "明確求職查詢",
            "description": "職位+技能+地點",
            "query": "前端工程師 React Vue 新竹",
            "expected_job_related": True
        },
        {
            "category": "明確求職查詢",
            "description": "職位+薪資+地點",
            "query": "資料科學家 60k 台中",
            "expected_job_related": True
        },
        
        # 技能導向查詢
        {
            "category": "技能導向查詢",
            "description": "單一技能+地點",
            "query": "React開發 遠程",
            "expected_job_related": True
        },
        {
            "category": "技能導向查詢",
            "description": "多個技能",
            "query": "Python Django PostgreSQL",
            "expected_job_related": True
        },
        {
            "category": "技能導向查詢",
            "description": "AI相關技能",
            "query": "機器學習 TensorFlow 深度學習",
            "expected_job_related": True
        },
        
        # 模糊求職查詢
        {
            "category": "模糊求職查詢",
            "description": "求職動詞",
            "query": "找工作 台北",
            "expected_job_related": True
        },
        {
            "category": "模糊求職查詢",
            "description": "職業諮詢",
            "query": "軟體工程師職涯發展",
            "expected_job_related": True
        },
        
        # 邊界案例
        {
            "category": "邊界案例",
            "description": "僅地點名稱",
            "query": "台北",
            "expected_job_related": False
        },
        {
            "category": "邊界案例",
            "description": "薪資關鍵詞但非求職",
            "query": "薪水",
            "expected_job_related": False
        },
        {
            "category": "邊界案例",
            "description": "技能學習查詢",
            "query": "學習Python的最佳方法",
            "expected_job_related": False
        },
        
        # 非求職相關
        {
            "category": "非求職相關",
            "description": "天氣查詢",
            "query": "今天天氣如何",
            "expected_job_related": False
        },
        {
            "category": "非求職相關",
            "description": "娛樂推薦",
            "query": "推薦一部好電影",
            "expected_job_related": False
        },
        {
            "category": "非求職相關",
            "description": "購物查詢",
            "query": "哪裡可以買到便宜的筆電",
            "expected_job_related": False
        },
        {
            "category": "非求職相關",
            "description": "旅遊查詢",
            "query": "台北有什麼好玩的景點",
            "expected_job_related": False
        },
        
        # 複雜查詢
        {
            "category": "複雜查詢",
            "description": "多條件求職",
            "query": "尋找台北的全端工程師職位，要求React和Node.js經驗，薪資50k以上",
            "expected_job_related": True
        },
        {
            "category": "複雜查詢",
            "description": "遠程工作查詢",
            "query": "遠程工作機會 軟體開發 彈性時間",
            "expected_job_related": True
        },
        {
            "category": "複雜查詢",
            "description": "職涯轉換",
            "query": "從傳統製造業轉入科技業的建議",
            "expected_job_related": True
        }
    ]
    
    # 執行測試
    results = []
    category_stats = {}
    total_passed = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        category = test_case['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'passed': 0}
        
        category_stats[category]['total'] += 1
        
        print(f"\n📋 測試 {i}/{total_tests}: {test_case['description']}")
        print(f"類別: {category}")
        print(f"查詢: {test_case['query']}")
        
        try:
            # 執行分析
            result = analyzer.analyze_intent(test_case['query'])
            
            # 檢查結果
            actual_job_related = result.is_job_related
            expected_job_related = test_case['expected_job_related']
            
            test_passed = actual_job_related == expected_job_related
            
            if test_passed:
                print("✅ PASS")
                total_passed += 1
                category_stats[category]['passed'] += 1
            else:
                print("❌ FAIL")
                print(f"   預期求職相關: {expected_job_related}, 實際: {actual_job_related}")
            
            # 顯示詳細信息
            print(f"   意圖類型: {result.intent_type.value}")
            print(f"   置信度: {result.confidence:.2f}")
            
            if result.structured_intent and result.is_job_related:
                intent = result.structured_intent
                if intent.job_titles:
                    print(f"   職位: {intent.job_titles}")
                if intent.skills:
                    print(f"   技能: {intent.skills}")
                if intent.locations:
                    print(f"   地點: {intent.locations}")
                if intent.salary_range:
                    print(f"   薪資: {intent.salary_range}")
            
            # 保存結果
            results.append({
                "test_id": i,
                "category": category,
                "description": test_case['description'],
                "query": test_case['query'],
                "expected_job_related": expected_job_related,
                "actual_job_related": actual_job_related,
                "passed": test_passed,
                "intent_type": result.intent_type.value,
                "confidence": result.confidence,
                "reasoning": result.llm_reasoning,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "test_id": i,
                "category": category,
                "description": test_case['description'],
                "query": test_case['query'],
                "error": str(e),
                "passed": False,
                "timestamp": datetime.now().isoformat()
            })
    
    # 計算統計數據
    overall_pass_rate = (total_passed / total_tests) * 100
    
    # 顯示分類統計
    print("\n📊 分類統計")
    print("=" * 50)
    for category, stats in category_stats.items():
        pass_rate = (stats['passed'] / stats['total']) * 100
        print(f"{category}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
    
    # 顯示總結
    print("\n📊 測試總結")
    print("=" * 50)
    print(f"總測試案例: {total_tests}")
    print(f"通過案例: {total_passed}")
    print(f"失敗案例: {total_tests - total_passed}")
    print(f"總通過率: {overall_pass_rate:.1f}%")
    
    # 評估結果
    print("\n🎯 標準規範遵循評估")
    print("=" * 30)
    
    if overall_pass_rate >= 90:
        print("✅ 優秀！LLM指令完全符合標準規範")
        evaluation = "優秀"
    elif overall_pass_rate >= 80:
        print("✅ 良好！LLM指令基本符合標準規範")
        evaluation = "良好"
    elif overall_pass_rate >= 70:
        print("⚠️ 一般！LLM指令部分符合標準規範，需要改進")
        evaluation = "一般"
    else:
        print("❌ 不佳！LLM指令不符合標準規範，需要重大修正")
        evaluation = "不佳"
    
    print(f"最終通過率: {overall_pass_rate:.1f}%")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comprehensive_llm_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_tests - total_passed,
                "pass_rate": overall_pass_rate,
                "evaluation": evaluation,
                "category_stats": category_stats,
                "timestamp": datetime.now().isoformat()
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 測試結果已保存至: {filename}")
    
    return overall_pass_rate >= 70

if __name__ == "__main__":
    run_comprehensive_test()