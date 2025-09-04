#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的LLM指令標準測試
測試修正後的LLM指令是否符合基本標準規範
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from datetime import datetime
import json

def test_basic_functionality():
    """
    測試基本功能
    """
    print("🚀 開始簡化LLM指令測試")
    print("=" * 40)
    
    # 初始化分析器
    analyzer = LLMIntentAnalyzer(provider=LLMProvider.OPENAI_GPT35)
    
    # 測試案例
    test_cases = [
        {
            "description": "明確求職查詢",
            "query": "Python工程師 台北",
            "expected_job_related": True
        },
        {
            "description": "技能查詢", 
            "query": "React開發 遠程",
            "expected_job_related": True
        },
        {
            "description": "非求職查詢",
            "query": "今天天氣如何",
            "expected_job_related": False
        },
        {
            "description": "娛樂查詢",
            "query": "推薦一部好電影",
            "expected_job_related": False
        },
        {
            "description": "邊界案例 - 僅地點",
            "query": "台北",
            "expected_job_related": False
        }
    ]
    
    results = []
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 測試 {i}: {test_case['description']}")
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
                passed += 1
            else:
                print("❌ FAIL")
                print(f"   預期求職相關: {expected_job_related}, 實際: {actual_job_related}")
            
            # 顯示詳細信息
            print(f"   意圖類型: {result.intent_type.value}")
            print(f"   置信度: {result.confidence:.2f}")
            print(f"   是否求職相關: {result.is_job_related}")
            
            if result.llm_reasoning:
                print(f"   推理過程: {result.llm_reasoning[:100]}...")
            
            if result.structured_intent and result.is_job_related:
                print(f"   職位: {result.structured_intent.job_titles}")
                print(f"   技能: {result.structured_intent.skills}")
                print(f"   地點: {result.structured_intent.locations}")
            
            # 保存結果
            results.append({
                "test_case": test_case['description'],
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
                "test_case": test_case['description'],
                "query": test_case['query'],
                "error": str(e),
                "passed": False,
                "timestamp": datetime.now().isoformat()
            })
    
    # 顯示總結
    print("\n📊 測試總結")
    print("=" * 40)
    print(f"總測試案例: {total}")
    print(f"通過案例: {passed}")
    print(f"失敗案例: {total - passed}")
    print(f"通過率: {(passed/total)*100:.1f}%")
    
    # 評估結果
    pass_rate = (passed/total)*100
    if pass_rate >= 80:
        print("\n✅ 良好！LLM指令基本符合標準規範")
    elif pass_rate >= 60:
        print("\n⚠️ 一般！LLM指令部分符合標準規範，需要改進")
    else:
        print("\n❌ 不佳！LLM指令不符合標準規範，需要重大修正")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_llm_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": pass_rate,
                "timestamp": datetime.now().isoformat()
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 測試結果已保存至: {filename}")
    
    return pass_rate >= 60

if __name__ == "__main__":
    test_basic_functionality()