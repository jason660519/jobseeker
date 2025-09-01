#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 智能路由系統使用示例
展示如何使用智能路由功能進行工作搜索

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
from pathlib import Path

# 添加 jobspy 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from jobspy.route_manager import RouteManager, smart_scrape_jobs
from jobspy.intelligent_router import IntelligentRouter

def example_1_australia_construction():
    """
    示例 1: 澳洲建築行業工作搜索
    """
    print("\n" + "=" * 60)
    print("示例 1: 澳洲建築行業工作搜索")
    print("=" * 60)
    
    query = "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
    print(f"查詢: {query}")
    
    # 使用便利函數
    result = smart_scrape_jobs(
        user_query=query,
        results_wanted=10
    )
    
    print(f"\n結果: 找到 {result.total_jobs} 個職位")
    print(f"使用的代理: {[a.value for a in result.successful_agents]}")
    print(f"路由理由: {result.routing_decision.reasoning}")
    
    if result.combined_jobs_data is not None and not result.combined_jobs_data.empty:
        print("\n前3個職位:")
        for i, (_, job) in enumerate(result.combined_jobs_data.head(3).iterrows()):
            print(f"  {i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")

def example_2_us_tech_jobs():
    """
    示例 2: 美國科技行業工作搜索
    """
    print("\n" + "=" * 60)
    print("示例 2: 美國科技行業工作搜索")
    print("=" * 60)
    
    query = "Looking for senior software engineer jobs in San Francisco Bay Area with Python experience"
    print(f"查詢: {query}")
    
    # 使用路由管理器
    manager = RouteManager()
    result = manager.smart_scrape_jobs(
        user_query=query,
        results_wanted=15,
        hours_old=72  # 最近3天的職位
    )
    
    print(f"\n結果: 找到 {result.total_jobs} 個職位")
    print(f"使用的代理: {[a.value for a in result.successful_agents]}")
    print(f"執行時間: {result.total_execution_time:.2f} 秒")
    
    # 顯示各代理的表現
    print("\n各代理表現:")
    for exec_result in result.execution_results:
        status = "✓" if exec_result.success else "✗"
        print(f"  {status} {exec_result.agent.value}: {exec_result.job_count} 職位")

def example_3_india_tech_jobs():
    """
    示例 3: 印度科技行業工作搜索
    """
    print("\n" + "=" * 60)
    print("示例 3: 印度科技行業工作搜索")
    print("=" * 60)
    
    query = "Find data scientist jobs in Bangalore, India for fresher candidates"
    print(f"查詢: {query}")
    
    result = smart_scrape_jobs(
        user_query=query,
        location="Bangalore, Karnataka, India",
        results_wanted=20
    )
    
    print(f"\n結果: 找到 {result.total_jobs} 個職位")
    print(f"地理匹配: {result.routing_decision.geographic_match}")
    print(f"行業匹配: {result.routing_decision.industry_match}")
    print(f"信心度: {result.routing_decision.confidence_score:.2f}")

def example_4_middle_east_finance():
    """
    示例 4: 中東金融行業工作搜索
    """
    print("\n" + "=" * 60)
    print("示例 4: 中東金融行業工作搜索")
    print("=" * 60)
    
    query = "Looking for investment banking analyst positions in Dubai, UAE"
    print(f"查詢: {query}")
    
    result = smart_scrape_jobs(
        user_query=query,
        results_wanted=12
    )
    
    print(f"\n結果: 找到 {result.total_jobs} 個職位")
    print(f"選中的代理: {[a.value for a in result.routing_decision.selected_agents]}")
    
    if result.failed_agents:
        print(f"失敗的代理: {[a.value for a in result.failed_agents]}")

def example_5_routing_analysis_only():
    """
    示例 5: 僅進行路由分析（不執行搜索）
    """
    print("\n" + "=" * 60)
    print("示例 5: 路由分析演示")
    print("=" * 60)
    
    router = IntelligentRouter()
    
    test_queries = [
        "請你幫我找台北的軟體工程師工作",
        "Find nursing jobs in Toronto, Canada within 30 miles",
        "Looking for marketing manager positions in London, UK",
        "尋找新加坡的金融分析師職位",
        "Search for construction project manager jobs in Sydney, Australia"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n查詢 {i}: {query}")
        print("-" * 50)
        
        decision = router.analyze_query(query)
        
        print(f"選中代理: {[a.value for a in decision.selected_agents]}")
        print(f"信心度: {decision.confidence_score:.2f}")
        print(f"決策理由: {decision.reasoning}")
        
        if decision.geographic_match:
            print(f"地理匹配: {decision.geographic_match}")
        
        if decision.industry_match:
            print(f"行業匹配: {decision.industry_match}")

def example_6_custom_parameters():
    """
    示例 6: 自定義參數使用
    """
    print("\n" + "=" * 60)
    print("示例 6: 自定義參數使用")
    print("=" * 60)
    
    query = "Find remote software developer jobs with React and Node.js experience"
    print(f"查詢: {query}")
    
    # 使用自定義參數
    manager = RouteManager(max_workers=2)  # 限制並發數
    
    result = manager.smart_scrape_jobs(
        user_query=query,
        location="Remote",
        results_wanted=25,
        hours_old=48,  # 最近2天
        country_indeed="worldwide"
    )
    
    print(f"\n結果: 找到 {result.total_jobs} 個職位")
    print(f"執行時間: {result.total_execution_time:.2f} 秒")
    
    # 顯示統計信息
    stats = manager.get_routing_statistics()
    print(f"\n統計信息:")
    print(f"總執行次數: {stats['total_executions']}")
    print(f"平均執行時間: {stats['average_execution_time']:.2f} 秒")

def example_7_error_handling():
    """
    示例 7: 錯誤處理和後備機制
    """
    print("\n" + "=" * 60)
    print("示例 7: 錯誤處理演示")
    print("=" * 60)
    
    # 使用可能導致某些代理失敗的查詢
    query = "Find jobs in a very specific niche market that might not exist"
    print(f"查詢: {query}")
    
    try:
        result = smart_scrape_jobs(
            user_query=query,
            results_wanted=5
        )
        
        print(f"\n結果: 找到 {result.total_jobs} 個職位")
        
        if result.failed_agents:
            print(f"失敗的代理: {[a.value for a in result.failed_agents]}")
            print("系統自動使用了後備代理")
        
        print("\n各代理執行詳情:")
        for exec_result in result.execution_results:
            status = "成功" if exec_result.success else "失敗"
            print(f"  {exec_result.agent.value}: {status}")
            if exec_result.error_message:
                print(f"    錯誤信息: {exec_result.error_message}")
                
    except Exception as e:
        print(f"搜索過程中出現錯誤: {e}")
        print("這展示了系統的錯誤處理機制")

def example_8_multilingual_support():
    """
    示例 8: 多語言支持演示
    """
    print("\n" + "=" * 60)
    print("示例 8: 多語言支持演示")
    print("=" * 60)
    
    multilingual_queries = [
        "請幫我找香港的會計師工作",  # 中文
        "Find marketing jobs in Paris, France",  # 英文
        "尋找新加坡的數據分析師職位",  # 中文
        "Looking for nurse positions in Vancouver, Canada"  # 英文
    ]
    
    router = IntelligentRouter()
    
    for query in multilingual_queries:
        print(f"\n查詢: {query}")
        print("-" * 40)
        
        decision = router.analyze_query(query)
        print(f"選中代理: {[a.value for a in decision.selected_agents]}")
        print(f"決策理由: {decision.reasoning}")

def run_all_examples():
    """
    運行所有示例
    """
    print("JobSpy 智能路由系統示例集")
    print("=" * 60)
    
    examples = [
        ("澳洲建築行業搜索", example_1_australia_construction),
        ("美國科技行業搜索", example_2_us_tech_jobs),
        ("印度科技行業搜索", example_3_india_tech_jobs),
        ("中東金融行業搜索", example_4_middle_east_finance),
        ("路由分析演示", example_5_routing_analysis_only),
        ("自定義參數使用", example_6_custom_parameters),
        ("錯誤處理演示", example_7_error_handling),
        ("多語言支持演示", example_8_multilingual_support)
    ]
    
    for name, example_func in examples:
        try:
            print(f"\n正在運行: {name}")
            example_func()
        except Exception as e:
            print(f"示例 '{name}' 執行失敗: {e}")
        
        input("\n按 Enter 繼續下一個示例...")

def interactive_demo():
    """
    互動式演示
    """
    print("\n" + "=" * 60)
    print("JobSpy 智能路由系統 - 互動式演示")
    print("=" * 60)
    print("輸入您的工作搜索查詢，系統將智能選擇最適合的代理")
    print("輸入 'quit' 退出")
    
    router = IntelligentRouter()
    
    while True:
        try:
            query = input("\n請輸入您的查詢: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出', 'q']:
                print("感謝使用 JobSpy 智能路由系統！")
                break
            
            if not query:
                continue
            
            print("\n分析中...")
            decision = router.analyze_query(query)
            
            print(f"\n路由決策結果:")
            print(f"選中代理: {[a.value for a in decision.selected_agents]}")
            print(f"信心度: {decision.confidence_score:.2f}")
            print(f"決策理由: {decision.reasoning}")
            
            if decision.geographic_match:
                print(f"地理匹配: {decision.geographic_match}")
            
            if decision.industry_match:
                print(f"行業匹配: {decision.industry_match}")
            
            # 詢問是否執行實際搜索
            execute = input("\n是否執行實際搜索？(y/n): ").strip().lower()
            if execute in ['y', 'yes', '是', 'Y']:
                print("執行搜索中...")
                result = smart_scrape_jobs(user_query=query, results_wanted=5)
                print(f"找到 {result.total_jobs} 個職位")
                
                if result.combined_jobs_data is not None and not result.combined_jobs_data.empty:
                    print("\n前3個職位:")
                    for i, (_, job) in enumerate(result.combined_jobs_data.head(3).iterrows()):
                        print(f"  {i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
            
        except KeyboardInterrupt:
            print("\n\n感謝使用 JobSpy 智能路由系統！")
            break
        except Exception as e:
            print(f"\n錯誤: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="JobSpy 智能路由系統示例")
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true", 
        help="運行互動式演示"
    )
    parser.add_argument(
        "--example", "-e", 
        type=int, 
        choices=range(1, 9), 
        help="運行特定示例 (1-8)"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_demo()
    elif args.example:
        examples = {
            1: example_1_australia_construction,
            2: example_2_us_tech_jobs,
            3: example_3_india_tech_jobs,
            4: example_4_middle_east_finance,
            5: example_5_routing_analysis_only,
            6: example_6_custom_parameters,
            7: example_7_error_handling,
            8: example_8_multilingual_support
        }
        examples[args.example]()
    else:
        run_all_examples()