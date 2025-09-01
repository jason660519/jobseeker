#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歐洲地區 AI 工程師職位搜索測試
測試智能路由器對歐洲市場的支援能力

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import os
from datetime import datetime
import pandas as pd

# 添加 jobseeker 模組路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker import scrape_jobs
from jobseeker.intelligent_router import IntelligentRouter

def test_europe_ai_jobs():
    """
    測試歐洲地區 AI 工程師職位搜索
    
    Returns:
        dict: 測試結果統計
    """
    print("=" * 80)
    print("🇪🇺 歐洲地區 AI 工程師職位搜索測試")
    print("=" * 80)
    
    # 初始化智能路由器
    router = IntelligentRouter()
    
    # 測試查詢
    test_query = "請幫我生成 歐洲地區、AI工程師、目前有效的工作職缺列表"
    
    print(f"\n📝 測試查詢: {test_query}")
    print("-" * 60)
    
    # 分析路由決策
    decision = router.analyze_query(test_query)
    
    print(f"\n🎯 路由分析結果:")
    print(f"   地理匹配: {decision.geographic_match}")
    print(f"   行業匹配: {decision.industry_match}")
    print(f"   信心度: {decision.confidence_score:.2f}")
    print(f"   選定代理: {[agent.value for agent in decision.selected_agents]}")
    print(f"   備用代理: {[agent.value for agent in decision.fallback_agents]}")
    print(f"   決策理由: {decision.reasoning}")
    
    # 獲取路由說明
    explanation = router.get_routing_explanation(decision)
    print(f"\n📋 詳細說明:\n{explanation}")
    
    # 測試不同歐洲國家的查詢
    europe_test_queries = [
        "英國倫敦 AI工程師 職位",
        "法國巴黎 機器學習工程師",
        "德國柏林 深度學習 工作",
        "荷蘭阿姆斯特丹 人工智能 職缺",
        "瑞士蘇黎世 AI研發工程師"
    ]
    
    print("\n🌍 歐洲各國測試結果:")
    print("-" * 60)
    
    test_results = []
    
    for i, query in enumerate(europe_test_queries, 1):
        print(f"\n{i}. 測試查詢: {query}")
        
        try:
            # 分析查詢
            decision = router.analyze_query(query)
            
            result = {
                'query': query,
                'geographic_match': decision.geographic_match,
                'industry_match': decision.industry_match,
                'confidence_score': decision.confidence_score,
                'selected_agents': [agent.value for agent in decision.selected_agents],
                'status': 'success'
            }
            
            print(f"   ✅ 地理匹配: {decision.geographic_match}")
            print(f"   🎯 信心度: {decision.confidence_score:.2f}")
            print(f"   🤖 代理: {[agent.value for agent in decision.selected_agents]}")
            
        except Exception as e:
            result = {
                'query': query,
                'geographic_match': None,
                'industry_match': None,
                'confidence_score': 0.0,
                'selected_agents': [],
                'status': f'error: {str(e)}'
            }
            print(f"   ❌ 錯誤: {str(e)}")
        
        test_results.append(result)
    
    # 執行實際職位搜索（僅針對主要查詢）
    print("\n🔍 執行實際職位搜索...")
    print("-" * 60)
    
    try:
        # 搜索歐洲地區 AI 工程師職位
        jobs_df = scrape_jobs(
            site_name=decision.selected_agents,
            search_term="AI Engineer",
            location="Europe",
            results_wanted=20,
            hours_old=72,
            country_indeed="UK"  # 預設使用英國 Indeed
        )
        
        if jobs_df is not None and not jobs_df.empty:
            print(f"✅ 成功找到 {len(jobs_df)} 個職位")
            
            # 保存結果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"europe_ai_jobs_{timestamp}.csv"
            jobs_df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"📁 結果已保存至: {filename}")
            
            # 顯示前幾個職位
            print("\n📋 前5個職位預覽:")
            for i, row in jobs_df.head().iterrows():
                print(f"   {i+1}. {row.get('title', 'N/A')} - {row.get('company', 'N/A')}")
                print(f"      📍 {row.get('location', 'N/A')} | 💰 {row.get('salary', 'N/A')}")
        else:
            print("❌ 未找到職位")
            
    except Exception as e:
        print(f"❌ 搜索錯誤: {str(e)}")
    
    # 生成測試報告
    print("\n📊 測試統計:")
    print("-" * 60)
    
    successful_tests = sum(1 for r in test_results if r['status'] == 'success')
    total_tests = len(test_results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"總測試數: {total_tests}")
    print(f"成功測試: {successful_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    # 統計地理匹配
    europe_matches = sum(1 for r in test_results if r.get('geographic_match') == 'Europe')
    print(f"歐洲地理匹配: {europe_matches}/{total_tests}")
    
    # 統計平均信心度
    avg_confidence = sum(r.get('confidence_score', 0) for r in test_results) / total_tests if total_tests > 0 else 0
    print(f"平均信心度: {avg_confidence:.2f}")
    
    # 保存測試結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"europe_test_report_{timestamp}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"歐洲地區 AI 工程師職位搜索測試報告\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"="*80 + "\n\n")
        
        f.write(f"主要測試查詢: {test_query}\n")
        f.write(f"地理匹配: {decision.geographic_match}\n")
        f.write(f"行業匹配: {decision.industry_match}\n")
        f.write(f"信心度: {decision.confidence_score:.2f}\n")
        f.write(f"選定代理: {[agent.value for agent in decision.selected_agents]}\n")
        f.write(f"決策理由: {decision.reasoning}\n\n")
        
        f.write("各國測試結果:\n")
        f.write("-"*40 + "\n")
        for i, result in enumerate(test_results, 1):
            f.write(f"{i}. {result['query']}\n")
            f.write(f"   地理匹配: {result['geographic_match']}\n")
            f.write(f"   信心度: {result['confidence_score']:.2f}\n")
            f.write(f"   狀態: {result['status']}\n\n")
        
        f.write(f"測試統計:\n")
        f.write(f"總測試數: {total_tests}\n")
        f.write(f"成功測試: {successful_tests}\n")
        f.write(f"成功率: {success_rate:.1f}%\n")
        f.write(f"歐洲地理匹配: {europe_matches}/{total_tests}\n")
        f.write(f"平均信心度: {avg_confidence:.2f}\n")
    
    print(f"\n📄 測試報告已保存至: {report_filename}")
    
    return {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'success_rate': success_rate,
        'europe_matches': europe_matches,
        'avg_confidence': avg_confidence,
        'test_results': test_results
    }

def main():
    """
    主函數
    """
    try:
        results = test_europe_ai_jobs()
        
        print("\n" + "="*80)
        print("🎉 歐洲地區測試完成!")
        print("="*80)
        
        if results['success_rate'] >= 80:
            print("✅ 測試結果: 優秀")
        elif results['success_rate'] >= 60:
            print("⚠️  測試結果: 良好")
        else:
            print("❌ 測試結果: 需要改進")
            
    except Exception as e:
        print(f"❌ 測試執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
