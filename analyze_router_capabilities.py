#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能路由器能力分析工具
分析路由器能識別的國家、城市數量以及首都支援情況

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobspy.intelligent_router import IntelligentRouter
from collections import defaultdict
import json

def analyze_router_capabilities():
    """
    分析智能路由器的地理識別能力
    
    Returns:
        分析結果字典
    """
    print("=" * 80)
    print("智能路由器地理識別能力分析")
    print("=" * 80)
    
    # 初始化路由器
    router = IntelligentRouter()
    
    # 統計數據
    total_countries = set()
    total_cities = set()
    total_states_provinces = set()
    total_keywords = set()
    
    # 各區域統計
    region_stats = {}
    
    # 世界主要國家首都列表（用於檢測首都支援）
    world_capitals = {
        # 亞洲
        "中國": "北京",
        "日本": "東京",
        "韓國": "首爾",
        "台灣": "台北",
        "新加坡": "新加坡",
        "泰國": "曼谷",
        "越南": "河內",
        "馬來西亞": "吉隆坡",
        "印尼": "雅加達",
        "菲律賓": "馬尼拉",
        "印度": "新德里",
        "孟加拉": "達卡",
        
        # 中東
        "阿聯酋": "阿布達比",
        "沙烏地阿拉伯": "利雅德",
        "卡達": "多哈",
        "科威特": "科威特城",
        "巴林": "麥納麥",
        "阿曼": "馬斯喀特",
        
        # 歐洲
        "英國": "倫敦",
        "法國": "巴黎",
        "德國": "柏林",
        "義大利": "羅馬",
        "西班牙": "馬德里",
        "荷蘭": "阿姆斯特丹",
        "瑞士": "伯恩",
        "瑞典": "斯德哥爾摩",
        "挪威": "奧斯陸",
        "丹麥": "哥本哈根",
        
        # 北美
        "美國": "華盛頓",
        "加拿大": "渥太華",
        "墨西哥": "墨西哥城",
        
        # 大洋洲
        "澳洲": "坎培拉",
        "紐西蘭": "威靈頓",
        
        # 南美
        "巴西": "巴西利亞",
        "阿根廷": "布宜諾斯艾利斯",
        "智利": "聖地亞哥",
        "秘魯": "利馬",
        
        # 非洲
        "南非": "開普敦",
        "埃及": "開羅",
        "奈及利亞": "阿布賈",
        "肯亞": "奈洛比"
    }
    
    print("\n📊 各地理區域詳細分析:")
    print("-" * 60)
    
    for region in router.geographic_regions:
        print(f"\n🌍 區域: {region.name}")
        
        # 統計當前區域
        region_countries = set(region.countries)
        region_cities = set(region.cities)
        region_states = set(region.states_provinces)
        region_keywords = set(region.keywords)
        
        # 加入總統計
        total_countries.update(region_countries)
        total_cities.update(region_cities)
        total_states_provinces.update(region_states)
        total_keywords.update(region_keywords)
        
        # 區域統計
        region_stats[region.name] = {
            "countries": len(region_countries),
            "cities": len(region_cities),
            "states_provinces": len(region_states),
            "keywords": len(region_keywords),
            "primary_agents": [agent.value for agent in region.primary_agents],
            "secondary_agents": [agent.value for agent in region.secondary_agents]
        }
        
        print(f"   📍 國家數量: {len(region_countries)}")
        print(f"   🏙️  城市數量: {len(region_cities)}")
        print(f"   🗺️  州省數量: {len(region_states)}")
        print(f"   🔑 關鍵詞數量: {len(region_keywords)}")
        print(f"   🎯 主要代理: {[agent.value for agent in region.primary_agents]}")
        print(f"   🔄 次要代理: {[agent.value for agent in region.secondary_agents]}")
        
        # 顯示具體內容（限制顯示數量）
        print(f"   📋 國家列表: {list(region_countries)[:10]}{'...' if len(region_countries) > 10 else ''}")
        print(f"   📋 主要城市: {list(region_cities)[:10]}{'...' if len(region_cities) > 10 else ''}")
    
    print("\n" + "=" * 80)
    print("📈 總體統計摘要")
    print("=" * 80)
    print(f"🌍 總支援國家數量: {len(total_countries)}")
    print(f"🏙️  總支援城市數量: {len(total_cities)}")
    print(f"🗺️  總支援州省數量: {len(total_states_provinces)}")
    print(f"🔑 總關鍵詞數量: {len(total_keywords)}")
    print(f"📊 地理區域數量: {len(router.geographic_regions)}")
    
    print("\n" + "=" * 80)
    print("🏛️ 世界主要首都支援情況分析")
    print("=" * 80)
    
    supported_capitals = []
    unsupported_capitals = []
    
    for country, capital in world_capitals.items():
        # 測試首都查詢
        test_queries = [
            f"{capital} {country} software engineer",
            f"{country} {capital} 工程師",
            f"{capital} 首都 AI engineer"
        ]
        
        capital_supported = False
        for query in test_queries:
            try:
                decision = router.analyze_query(query)
                if decision.geographic_match:
                    capital_supported = True
                    break
            except Exception as e:
                continue
        
        if capital_supported:
            supported_capitals.append((country, capital))
        else:
            unsupported_capitals.append((country, capital))
    
    print(f"\n✅ 支援的首都 ({len(supported_capitals)}/{len(world_capitals)}):")
    for country, capital in supported_capitals:
        print(f"   🏛️ {country} - {capital}")
    
    print(f"\n❌ 尚未支援的首都 ({len(unsupported_capitals)}/{len(world_capitals)}):")
    for country, capital in unsupported_capitals:
        print(f"   🏛️ {country} - {capital}")
    
    # 首都支援率
    capital_support_rate = len(supported_capitals) / len(world_capitals) * 100
    print(f"\n📊 首都支援率: {capital_support_rate:.1f}%")
    
    print("\n" + "=" * 80)
    print("🎯 智能路由能力測試")
    print("=" * 80)
    
    # 測試各種查詢類型
    test_queries = [
        "新加坡首都50公里內AI Engineer工作",
        "台北軟體工程師職位",
        "東京 AI 工程師",
        "杜拜 Software Developer",
        "紐約 Data Scientist",
        "雪梨建築工程師",
        "倫敦金融分析師",
        "多倫多護士工作"
    ]
    
    print("\n🧪 測試查詢結果:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查詢: '{query}'")
        try:
            decision = router.analyze_query(query)
            print(f"   🎯 地理匹配: {decision.geographic_match}")
            print(f"   🏭 行業匹配: {decision.industry_match}")
            print(f"   🤖 選擇代理: {[agent.value for agent in decision.selected_agents]}")
            print(f"   📊 信心度: {decision.confidence_score:.2f}")
            print(f"   💭 決策理由: {decision.reasoning}")
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")
    
    print("\n" + "=" * 80)
    print("📋 結論與建議")
    print("=" * 80)
    
    print(f"\n✨ 智能路由器目前具備以下能力:")
    print(f"   🌍 支援 {len(router.geographic_regions)} 個主要地理區域")
    print(f"   🏳️ 識別 {len(total_countries)} 個國家/地區")
    print(f"   🏙️ 識別 {len(total_cities)} 個城市")
    print(f"   🗺️ 識別 {len(total_states_provinces)} 個州省")
    print(f"   🏛️ 支援 {len(supported_capitals)} 個世界主要首都 ({capital_support_rate:.1f}%)")
    print(f"   🤖 整合 {len(router.agent_capabilities)} 個求職代理")
    
    print(f"\n🎯 智能路由特色:")
    print(f"   ✅ 多語言支援 (中文/英文混合查詢)")
    print(f"   ✅ 地理位置智能識別")
    print(f"   ✅ 行業分類自動匹配")
    print(f"   ✅ 距離範圍檢測")
    print(f"   ✅ 代理可靠性排序")
    print(f"   ✅ 動態信心度評估")
    
    if unsupported_capitals:
        print(f"\n🔧 改進建議:")
        print(f"   📈 可考慮新增對以下地區的支援:")
        for country, capital in unsupported_capitals[:5]:  # 顯示前5個
            print(f"      - {country} ({capital})")
    
    # 返回統計結果
    return {
        "total_countries": len(total_countries),
        "total_cities": len(total_cities),
        "total_states_provinces": len(total_states_provinces),
        "total_keywords": len(total_keywords),
        "geographic_regions": len(router.geographic_regions),
        "supported_capitals": len(supported_capitals),
        "total_capitals_tested": len(world_capitals),
        "capital_support_rate": capital_support_rate,
        "region_stats": region_stats,
        "supported_capitals_list": supported_capitals,
        "unsupported_capitals_list": unsupported_capitals
    }

def main():
    """
    主函數
    """
    try:
        stats = analyze_router_capabilities()
        
        # 保存詳細統計到JSON文件
        output_file = "router_capabilities_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細分析結果已保存至: {output_file}")
        
    except Exception as e:
        print(f"❌ 分析過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()