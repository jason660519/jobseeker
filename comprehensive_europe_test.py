#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歐洲市場全面測試
測試智能路由器對歐洲各國的支援能力並執行實際職位搜索

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import os
from datetime import datetime
import pandas as pd
import time

# 添加 jobseeker 模組路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker import scrape_jobs
from jobseeker.intelligent_router import IntelligentRouter

def test_comprehensive_europe():
    """
    全面測試歐洲市場支援
    
    Returns:
        dict: 測試結果統計
    """
    print("=" * 80)
    print("🇪🇺 歐洲市場全面測試 - AI工程師職位搜索")
    print("=" * 80)
    
    # 初始化智能路由器
    router = IntelligentRouter()
    
    # 歐洲各國測試查詢
    europe_queries = [
        # 主要歐洲國家
        "英國倫敦 AI工程師 職位",
        "法國巴黎 機器學習工程師 工作",
        "德國柏林 深度學習工程師 職缺",
        "荷蘭阿姆斯特丹 人工智能工程師",
        "瑞士蘇黎世 AI研發工程師",
        "比利時布魯塞爾 機器學習 職位",
        "奧地利維也納 AI 工程師",
        "義大利米蘭 人工智能 工作",
        "西班牙馬德里 機器學習 職缺",
        "瑞典斯德哥爾摩 AI工程師",
        
        # 歐洲地區通用查詢
        "歐洲地區 AI工程師 職位",
        "Europe AI Engineer jobs",
        "歐盟 人工智能工程師 工作",
        "EU machine learning engineer",
        "European AI developer positions"
    ]
    
    print(f"\n📝 測試 {len(europe_queries)} 個歐洲查詢...")
    print("-" * 60)
    
    test_results = []
    
    for i, query in enumerate(europe_queries, 1):
        print(f"\n{i:2d}. 測試查詢: {query}")
        
        try:
            # 分析查詢
            decision = router.analyze_query(query)
            
            result = {
                'query': query,
                'geographic_match': decision.geographic_match,
                'industry_match': decision.industry_match,
                'confidence_score': decision.confidence_score,
                'selected_agents': [agent.value for agent in decision.selected_agents],
                'reasoning': decision.reasoning,
                'status': 'success'
            }
            
            print(f"    ✅ 地理匹配: {decision.geographic_match}")
            print(f"    🎯 行業匹配: {decision.industry_match}")
            print(f"    📊 信心度: {decision.confidence_score:.2f}")
            print(f"    🤖 代理: {[agent.value for agent in decision.selected_agents]}")
            
        except Exception as e:
            result = {
                'query': query,
                'geographic_match': None,
                'industry_match': None,
                'confidence_score': 0.0,
                'selected_agents': [],
                'reasoning': '',
                'status': f'error: {str(e)}'
            }
            print(f"    ❌ 錯誤: {str(e)}")
        
        test_results.append(result)
    
    # 執行實際職位搜索測試
    print("\n" + "=" * 80)
    print("🔍 執行實際職位搜索測試")
    print("=" * 80)
    
    search_tests = [
        {
            'name': '英國 AI 工程師',
            'search_term': 'AI Engineer',
            'location': 'London, UK',
            'country': 'UK'
        },
        {
            'name': '德國 機器學習工程師',
            'search_term': 'Machine Learning Engineer',
            'location': 'Berlin, Germany',
            'country': 'Germany'
        },
        {
            'name': '法國 人工智能工程師',
            'search_term': 'AI Engineer',
            'location': 'Paris, France',
            'country': 'France'
        }
    ]
    
    search_results = []
    
    for i, test in enumerate(search_tests, 1):
        print(f"\n{i}. 搜索測試: {test['name']}")
        print(f"   搜索詞: {test['search_term']}")
        print(f"   地點: {test['location']}")
        
        try:
            # 執行職位搜索
            jobs_df = scrape_jobs(
                site_name=['indeed', 'linkedin'],  # 使用字符串而非 AgentType
                search_term=test['search_term'],
                location=test['location'],
                results_wanted=10,
                hours_old=72,
                country_indeed=test['country']
            )
            
            if jobs_df is not None and not jobs_df.empty:
                job_count = len(jobs_df)
                print(f"   ✅ 找到 {job_count} 個職位")
                
                # 保存結果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"europe_{test['country'].lower()}_{timestamp}.csv"
                jobs_df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"   📁 結果已保存至: {filename}")
                
                # 顯示前幾個職位
                print(f"   📋 前3個職位:")
                for j, row in jobs_df.head(3).iterrows():
                    title = row.get('title', 'N/A')[:50]
                    company = row.get('company', 'N/A')[:30]
                    location = row.get('location', 'N/A')[:30]
                    print(f"      {j+1}. {title} - {company} ({location})")
                
                search_results.append({
                    'test_name': test['name'],
                    'job_count': job_count,
                    'status': 'success',
                    'filename': filename
                })
            else:
                print(f"   ⚠️  未找到職位")
                search_results.append({
                    'test_name': test['name'],
                    'job_count': 0,
                    'status': 'no_results',
                    'filename': None
                })
                
        except Exception as e:
            print(f"   ❌ 搜索錯誤: {str(e)}")
            search_results.append({
                'test_name': test['name'],
                'job_count': 0,
                'status': f'error: {str(e)}',
                'filename': None
            })
        
        # 避免過於頻繁的請求
        if i < len(search_tests):
            print(f"   ⏳ 等待 3 秒...")
            time.sleep(3)
    
    # 生成統計報告
    print("\n" + "=" * 80)
    print("📊 測試統計報告")
    print("=" * 80)
    
    # 路由測試統計
    successful_routes = sum(1 for r in test_results if r['status'] == 'success')
    total_routes = len(test_results)
    route_success_rate = (successful_routes / total_routes) * 100 if total_routes > 0 else 0
    
    europe_matches = sum(1 for r in test_results if r.get('geographic_match') == 'Europe')
    tech_matches = sum(1 for r in test_results if r.get('industry_match') == 'Technology')
    avg_confidence = sum(r.get('confidence_score', 0) for r in test_results) / total_routes if total_routes > 0 else 0
    
    print(f"\n🎯 路由測試結果:")
    print(f"   總測試數: {total_routes}")
    print(f"   成功測試: {successful_routes}")
    print(f"   成功率: {route_success_rate:.1f}%")
    print(f"   歐洲地理匹配: {europe_matches}/{total_routes} ({(europe_matches/total_routes)*100:.1f}%)")
    print(f"   技術行業匹配: {tech_matches}/{total_routes} ({(tech_matches/total_routes)*100:.1f}%)")
    print(f"   平均信心度: {avg_confidence:.2f}")
    
    # 搜索測試統計
    successful_searches = sum(1 for r in search_results if r['status'] == 'success')
    total_searches = len(search_results)
    search_success_rate = (successful_searches / total_searches) * 100 if total_searches > 0 else 0
    total_jobs_found = sum(r.get('job_count', 0) for r in search_results)
    
    print(f"\n🔍 職位搜索結果:")
    print(f"   總搜索測試: {total_searches}")
    print(f"   成功搜索: {successful_searches}")
    print(f"   搜索成功率: {search_success_rate:.1f}%")
    print(f"   總職位數: {total_jobs_found}")
    print(f"   平均每次搜索: {total_jobs_found/total_searches:.1f} 個職位")
    
    # 保存詳細報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"comprehensive_europe_test_report_{timestamp}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"歐洲市場全面測試報告\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"="*80 + "\n\n")
        
        f.write(f"路由測試結果:\n")
        f.write(f"總測試數: {total_routes}\n")
        f.write(f"成功測試: {successful_routes}\n")
        f.write(f"成功率: {route_success_rate:.1f}%\n")
        f.write(f"歐洲地理匹配: {europe_matches}/{total_routes}\n")
        f.write(f"技術行業匹配: {tech_matches}/{total_routes}\n")
        f.write(f"平均信心度: {avg_confidence:.2f}\n\n")
        
        f.write(f"詳細路由測試結果:\n")
        f.write("-"*60 + "\n")
        for i, result in enumerate(test_results, 1):
            f.write(f"{i:2d}. {result['query']}\n")
            f.write(f"    地理匹配: {result['geographic_match']}\n")
            f.write(f"    行業匹配: {result['industry_match']}\n")
            f.write(f"    信心度: {result['confidence_score']:.2f}\n")
            f.write(f"    代理: {result['selected_agents']}\n")
            f.write(f"    狀態: {result['status']}\n\n")
        
        f.write(f"職位搜索結果:\n")
        f.write(f"總搜索測試: {total_searches}\n")
        f.write(f"成功搜索: {successful_searches}\n")
        f.write(f"搜索成功率: {search_success_rate:.1f}%\n")
        f.write(f"總職位數: {total_jobs_found}\n\n")
        
        f.write(f"詳細搜索結果:\n")
        f.write("-"*40 + "\n")
        for i, result in enumerate(search_results, 1):
            f.write(f"{i}. {result['test_name']}\n")
            f.write(f"   職位數: {result['job_count']}\n")
            f.write(f"   狀態: {result['status']}\n")
            if result['filename']:
                f.write(f"   文件: {result['filename']}\n")
            f.write("\n")
    
    print(f"\n📄 詳細報告已保存至: {report_filename}")
    
    return {
        'route_tests': {
            'total': total_routes,
            'successful': successful_routes,
            'success_rate': route_success_rate,
            'europe_matches': europe_matches,
            'tech_matches': tech_matches,
            'avg_confidence': avg_confidence
        },
        'search_tests': {
            'total': total_searches,
            'successful': successful_searches,
            'success_rate': search_success_rate,
            'total_jobs': total_jobs_found
        },
        'test_results': test_results,
        'search_results': search_results
    }

def main():
    """
    主函數
    """
    try:
        results = test_comprehensive_europe()
        
        print("\n" + "="*80)
        print("🎉 歐洲市場全面測試完成!")
        print("="*80)
        
        route_success = results['route_tests']['success_rate']
        search_success = results['search_tests']['success_rate']
        
        if route_success >= 90 and search_success >= 70:
            print("✅ 測試結果: 優秀 - 歐洲市場支援完善")
        elif route_success >= 80 and search_success >= 50:
            print("⚠️  測試結果: 良好 - 歐洲市場支援基本完善")
        else:
            print("❌ 測試結果: 需要改進 - 歐洲市場支援有待加強")
        
        print(f"\n📈 關鍵指標:")
        print(f"   路由成功率: {route_success:.1f}%")
        print(f"   搜索成功率: {search_success:.1f}%")
        print(f"   歐洲地理匹配率: {(results['route_tests']['europe_matches']/results['route_tests']['total'])*100:.1f}%")
        print(f"   總職位數: {results['search_tests']['total_jobs']}")
            
    except Exception as e:
        print(f"❌ 測試執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
