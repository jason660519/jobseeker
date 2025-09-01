#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各國首都智能路由測試腳本
測試智能路由器對世界主要首都的識別和路由能力

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.intelligent_router import IntelligentRouter

def test_capital_routing():
    """
    測試各國首都的智能路由能力
    """
    print("=" * 80)
    print("🏛️ 各國首都智能路由測試")
    print("=" * 80)
    
    # 初始化路由器
    router = IntelligentRouter()
    
    # 測試首都列表 (包含支援和不支援的)
    test_capitals = [
        # 亞洲 - 已支援
        ("🇯🇵 日本", "東京 AI Engineer 工作"),
        ("🇹🇼 台灣", "台北 軟體工程師 職位"),
        ("🇸🇬 新加坡", "新加坡首都 Data Scientist"),
        ("🇹🇭 泰國", "曼谷 Web Developer"),
        ("🇮🇳 印度", "新德里 Python 開發者"),
        
        # 中東 - 已支援
        ("🇦🇪 阿聯酋", "阿布達比 Software Engineer"),
        ("🇸🇦 沙烏地阿拉伯", "利雅德 DevOps Engineer"),
        ("🇶🇦 卡達", "多哈 Cloud Architect"),
        
        # 北美 - 已支援
        ("🇺🇸 美國", "華盛頓 Machine Learning Engineer"),
        ("🇨🇦 加拿大", "渥太華 Full Stack Developer"),
        
        # 大洋洲 - 已支援
        ("🇦🇺 澳洲", "坎培拉 Construction Manager"),
        ("🇳🇿 紐西蘭", "威靈頓 Software Developer"),
        
        # 歐洲 - 尚未支援
        ("🇬🇧 英國", "倫敦 Financial Analyst"),
        ("🇫🇷 法國", "巴黎 Data Scientist"),
        ("🇩🇪 德國", "柏林 Software Engineer"),
        
        # 亞洲 - 尚未支援
        ("🇨🇳 中國", "北京 AI Engineer"),
        ("🇰🇷 韓國", "首爾 Game Developer"),
        
        # 南美 - 尚未支援
        ("🇧🇷 巴西", "巴西利亞 Software Developer"),
        ("🇦🇷 阿根廷", "布宜諾斯艾利斯 Web Developer")
    ]
    
    supported_count = 0
    unsupported_count = 0
    
    print("\n🧪 測試結果:")
    print("-" * 80)
    
    for country_flag, query in test_capitals:
        print(f"\n{country_flag}")
        print(f"📝 查詢: '{query}'")
        
        try:
            decision = router.analyze_query(query)
            
            if decision.geographic_match:
                print(f"   ✅ 地理匹配: {decision.geographic_match}")
                print(f"   🏭 行業匹配: {decision.industry_match}")
                print(f"   🤖 選擇代理: {[agent.value for agent in decision.selected_agents]}")
                print(f"   📊 信心度: {decision.confidence_score:.2f}")
                print(f"   💭 決策理由: {decision.reasoning}")
                supported_count += 1
            else:
                print(f"   ❌ 地理匹配: 無法識別")
                print(f"   🏭 行業匹配: {decision.industry_match}")
                print(f"   🤖 選擇代理: {[agent.value for agent in decision.selected_agents]} (全球代理)")
                print(f"   📊 信心度: {decision.confidence_score:.2f}")
                print(f"   💭 決策理由: {decision.reasoning}")
                unsupported_count += 1
                
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")
            unsupported_count += 1
    
    # 統計結果
    total_tested = len(test_capitals)
    support_rate = (supported_count / total_tested) * 100
    
    print("\n" + "=" * 80)
    print("📊 測試統計結果")
    print("=" * 80)
    print(f"🧪 總測試數量: {total_tested}")
    print(f"✅ 成功識別: {supported_count}")
    print(f"❌ 無法識別: {unsupported_count}")
    print(f"📈 識別成功率: {support_rate:.1f}%")
    
    print("\n" + "=" * 80)
    print("🎯 路由器首都支援能力總結")
    print("=" * 80)
    
    if support_rate >= 70:
        print("🌟 優秀: 路由器具備強大的全球首都識別能力")
    elif support_rate >= 50:
        print("👍 良好: 路由器能識別大部分主要首都")
    elif support_rate >= 30:
        print("⚠️  一般: 路由器支援部分地區首都")
    else:
        print("🔧 需改進: 路由器首都識別能力有限")
    
    print("\n🚀 智能路由特色:")
    print("   ✅ 支援中英文混合查詢")
    print("   ✅ 自動行業分類識別")
    print("   ✅ 智能代理選擇機制")
    print("   ✅ 動態信心度評估")
    print("   ✅ 地理位置精確匹配")
    
    print("\n📋 建議:")
    if unsupported_count > 0:
        print("   🔧 考慮新增對歐洲、中國、韓國等地區的支援")
        print("   🌍 擴展地理配置以涵蓋更多國際市場")
        print("   🤖 整合更多本地化求職平台")
    else:
        print("   🎉 路由器已具備完整的全球首都識別能力!")

def main():
    """
    主函數
    """
    try:
        test_capital_routing()
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
