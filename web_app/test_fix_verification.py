#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證 Glassdoor WORLDWIDE 錯誤修復的測試腳本

測試目標:
1. 驗證智能路由器正確排除 Glassdoor 用於全球查詢
2. 驗證其他代理不再出現 Glassdoor 相關錯誤
3. 測試具體地理位置的查詢是否正常工作

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jobseeker.route_manager import smart_scrape_jobs
from jobseeker.intelligent_router import IntelligentRouter

def test_router_decision():
    """
    測試智能路由器的決策邏輯
    """
    print("\n" + "=" * 60)
    print("測試 1: 智能路由器決策邏輯")
    print("=" * 60)
    
    router = IntelligentRouter()
    
    # 測試全球查詢
    global_queries = [
        "data scientist worldwide",
        "software engineer global",
        "marketing manager international"
    ]
    
    for query in global_queries:
        print(f"\n🔍 測試查詢: {query}")
        decision = router.analyze_query(query)
        
        selected_agents = [agent.value for agent in decision.selected_agents]
        fallback_agents = [agent.value for agent in decision.fallback_agents]
        
        print(f"  選定代理: {selected_agents}")
        print(f"  後備代理: {fallback_agents}")
        print(f"  決策理由: {decision.reasoning}")
        
        # 驗證 Glassdoor 是否被正確排除
        glassdoor_in_selected = 'glassdoor' in selected_agents
        glassdoor_in_fallback = 'glassdoor' in fallback_agents
        
        if glassdoor_in_selected or glassdoor_in_fallback:
            print(f"  ❌ 錯誤: Glassdoor 未被正確排除")
            return False
        else:
            print(f"  ✅ 正確: Glassdoor 已被排除")
    
    return True

def test_specific_location_search():
    """
    測試具體地理位置的搜尋
    """
    print("\n" + "=" * 60)
    print("測試 2: 具體地理位置搜尋")
    print("=" * 60)
    
    test_cases = [
        {
            'query': 'software engineer',
            'location': 'San Francisco, CA',
            'description': '美國舊金山軟體工程師'
        },
        {
            'query': 'data scientist',
            'location': 'Sydney, Australia',
            'description': '澳洲雪梨資料科學家'
        },
        {
            'query': 'marketing manager',
            'location': 'London, UK',
            'description': '英國倫敦行銷經理'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 測試案例 {i}: {test_case['description']}")
        print(f"  查詢: {test_case['query']}")
        print(f"  地點: {test_case['location']}")
        
        start_time = time.time()
        
        try:
            result = smart_scrape_jobs(
                user_query=test_case['query'],
                location=test_case['location'],
                results_wanted=5  # 少量結果以加快測試
            )
            
            execution_time = time.time() - start_time
            
            print(f"  ✅ 搜尋完成: {execution_time:.2f}秒")
            print(f"  📊 總職位數: {result.total_jobs}")
            print(f"  🤖 成功代理: {[a.value for a in result.successful_agents]}")
            print(f"  🔄 路由理由: {result.routing_decision.reasoning}")
            
            # 檢查是否有錯誤
            failed_agents = []
            for exec_result in result.execution_results:
                if not exec_result.success:
                    failed_agents.append({
                        'agent': exec_result.agent.value,
                        'error': exec_result.error_message
                    })
            
            if failed_agents:
                print(f"  ⚠️  失敗代理:")
                for failed in failed_agents:
                    print(f"    - {failed['agent']}: {failed['error']}")
                    
                    # 檢查是否仍有 Glassdoor 錯誤
                    if 'Glassdoor is not available for' in failed['error']:
                        print(f"    ❌ 發現 Glassdoor 錯誤: {failed['error']}")
                        return False
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ 搜尋失敗: {execution_time:.2f}秒")
            print(f"  錯誤: {str(e)}")
            
            # 檢查是否是 Glassdoor 相關錯誤
            if 'Glassdoor is not available for' in str(e):
                print(f"  ❌ 發現 Glassdoor 錯誤: {str(e)}")
                return False
    
    return True

def test_global_query_handling():
    """
    測試全球查詢的處理
    """
    print("\n" + "=" * 60)
    print("測試 3: 全球查詢處理")
    print("=" * 60)
    
    global_query = "software engineer worldwide remote"
    print(f"🔍 測試查詢: {global_query}")
    
    start_time = time.time()
    
    try:
        result = smart_scrape_jobs(
            user_query=global_query,
            results_wanted=5
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ 搜尋完成: {execution_time:.2f}秒")
        print(f"📊 總職位數: {result.total_jobs}")
        print(f"🤖 成功代理: {[a.value for a in result.successful_agents]}")
        print(f"🔄 路由理由: {result.routing_decision.reasoning}")
        
        # 檢查選定的代理中是否包含 Glassdoor
        selected_agents = [a.value for a in result.routing_decision.selected_agents]
        if 'glassdoor' in selected_agents:
            print(f"❌ 錯誤: 全球查詢中仍選擇了 Glassdoor")
            return False
        else:
            print(f"✅ 正確: 全球查詢中已排除 Glassdoor")
        
        # 檢查執行結果中是否有 Glassdoor 錯誤
        for exec_result in result.execution_results:
            if not exec_result.success and 'Glassdoor is not available for' in exec_result.error_message:
                print(f"❌ 發現 Glassdoor 錯誤: {exec_result.error_message}")
                return False
        
        return True
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ 搜尋失敗: {execution_time:.2f}秒")
        print(f"錯誤: {str(e)}")
        
        if 'Glassdoor is not available for' in str(e):
            print(f"❌ 發現 Glassdoor 錯誤: {str(e)}")
            return False
        
        return False

def main():
    """
    主測試函數
    """
    print("🧪 Glassdoor WORLDWIDE 錯誤修復驗證測試")
    print("=" * 80)
    
    test_results = []
    
    # 執行測試
    test_results.append(("路由器決策邏輯", test_router_decision()))
    test_results.append(("具體地理位置搜尋", test_specific_location_search()))
    test_results.append(("全球查詢處理", test_global_query_handling()))
    
    # 總結結果
    print("\n" + "=" * 80)
    print("📋 測試結果總結")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有測試通過！Glassdoor WORLDWIDE 錯誤已成功修復。")
    else:
        print("⚠️  部分測試失敗，需要進一步檢查。")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)