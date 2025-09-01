#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 智能路由系統演示腳本

這個腳本展示了 jobseeker 智能路由系統的核心功能：
- 根據用戶查詢自動選擇最合適的爬蟲代理
- 支持地理位置、行業、距離和語言的智能識別
- 提供詳細的路由決策分析和解釋

作者: jobseeker Team
日期: 2025-01-02
"""

import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

try:
    from jobseeker.intelligent_router import IntelligentRouter
    from jobseeker.route_manager import RouteManager
except ImportError as e:
    print(f"導入錯誤: {e}")
    print("請確保 jobseeker 已正確安裝")
    sys.exit(1)

def demo_routing_analysis():
    """
    演示智能路由分析功能
    """
    print("\n" + "="*60)
    print("🧠 智能路由分析演示")
    print("="*60)
    
    router = IntelligentRouter()
    
    # 測試查詢列表
    test_queries = [
        "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作",
        "Looking for software engineer jobs in San Francisco",
        "尋找台北的資料科學家工作",
        "Find marketing manager positions in London within 25km",
        "البحث عن وظائف في دبي في مجال التمويل",
        "Looking for remote Python developer jobs"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 測試 {i}: {query}")
        print("-" * 50)
        
        try:
            decision = router.analyze_query(query)
            
            print(f"選中代理: {[agent.value for agent in decision.selected_agents]}")
            print(f"信心度: {decision.confidence:.2f}")
            print(f"決策理由: {decision.reasoning}")
            
            if decision.geographic_match:
                print(f"地理匹配: {decision.geographic_match}")
            if decision.industry_match:
                print(f"行業匹配: {decision.industry_match}")
            if decision.distance_detected:
                print(f"檢測距離: {decision.distance_detected} km")
            if decision.language_detected:
                print(f"檢測語言: {decision.language_detected}")
                
        except Exception as e:
            print(f"❌ 分析失敗: {e}")

def demo_smart_search():
    """
    演示智能搜索功能（僅分析，不執行實際搜索）
    """
    print("\n" + "="*60)
    print("🔍 智能搜索演示")
    print("="*60)
    
    route_manager = RouteManager()
    
    # 演示查詢
    demo_query = "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
    
    print(f"\n查詢: {demo_query}")
    print("-" * 50)
    
    try:
        # 只進行路由分析
        router = IntelligentRouter()
        decision = router.analyze_query(demo_query)
        
        print("\n🎯 路由決策結果:")
        print(f"  選中代理: {[agent.value for agent in decision.selected_agents]}")
        print(f"  信心度: {decision.confidence:.2f}")
        print(f"  決策理由: {decision.reasoning}")
        
        print("\n📊 代理詳情:")
        for agent in decision.selected_agents:
            agent_info = router.agent_capabilities.get(agent, {})
            print(f"  • {agent.value.upper()}:")
            print(f"    可靠性: {agent_info.get('reliability', 'N/A')}")
            print(f"    覆蓋範圍: {agent_info.get('coverage', 'N/A')}")
            print(f"    強項: {', '.join(agent_info.get('strengths', []))}")
        
        print("\n💡 這個查詢選擇這些代理的原因:")
        print("  1. SEEK: 專注澳洲本地市場，建築行業覆蓋率高")
        print("  2. LinkedIn: 專業職位平台，全球覆蓋")
        print("  3. Indeed: 大型綜合平台，職位數量多")
        print("  4. Google: 聚合搜索，補充覆蓋")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")

def demo_configuration():
    """
    演示配置功能
    """
    print("\n" + "="*60)
    print("⚙️ 配置系統演示")
    print("="*60)
    
    try:
        # 默認配置
        router_default = IntelligentRouter()
        print("\n📋 默認配置載入成功")
        print(f"  支持的地理區域: {len(router_default.geographic_regions)}")
        print(f"  支持的行業類別: {len(router_default.industry_categories)}")
        print(f"  支持的代理: {len(router_default.agent_capabilities)}")
        
        # 自定義配置（如果存在）
        config_path = "config/intelligent_routing_config.json"
        if Path(config_path).exists():
            router_custom = IntelligentRouter(config_path=config_path)
            print(f"\n📋 自定義配置載入成功: {config_path}")
        else:
            print(f"\n📋 自定義配置文件不存在: {config_path}")
            
    except Exception as e:
        print(f"❌ 配置演示失敗: {e}")

def main():
    """
    主演示函數
    """
    print("🚀 jobseeker 智能路由系統演示")
    print("這個演示展示了智能路由系統如何根據用戶查詢自動選擇最合適的爬蟲代理")
    
    try:
        # 演示 1: 路由分析
        demo_routing_analysis()
        
        # 演示 2: 智能搜索
        demo_smart_search()
        
        # 演示 3: 配置系統
        demo_configuration()
        
        print("\n" + "="*60)
        print("✅ 演示完成！")
        print("="*60)
        print("\n💡 使用建議:")
        print("  1. 使用 smart_job_search.py 進行實際工作搜索")
        print("  2. 查看 INTELLIGENT_ROUTING_GUIDE.md 了解詳細功能")
        print("  3. 運行 test_intelligent_routing.py 進行系統測試")
        print("  4. 查看 examples/intelligent_routing_examples.py 了解更多示例")
        
    except KeyboardInterrupt:
        print("\n\n👋 演示被用戶中斷")
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
