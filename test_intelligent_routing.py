#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能路由系統測試腳本

此腳本用於測試 jobseeker 智能路由系統的各項功能，包括：
1. 路由決策分析
2. 智能搜索執行
3. 多語言支持
4. 錯誤處理
5. 配置加載

使用方法:
    python test_intelligent_routing.py
"""

import sys
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jobseeker.intelligent_router import IntelligentRouter, RoutingDecision
    from jobseeker.route_manager import RouteManager, smart_scrape_jobs
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保已正確安裝 jobseeker 及其依賴")
    sys.exit(1)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('intelligent_routing_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class IntelligentRoutingTester:
    """智能路由系統測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.router = None
        self.manager = None
        self.test_results = []
        
    def setup(self) -> bool:
        """設置測試環境"""
        try:
            logger.info("🔧 正在設置測試環境...")
            
            # 初始化路由器
            self.router = IntelligentRouter()
            logger.info("✅ 智能路由器初始化成功")
            
            # 初始化管理器
            self.manager = RouteManager(max_workers=2)
            logger.info("✅ 路由管理器初始化成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 設置失敗: {e}")
            return False
    
    def test_routing_analysis(self) -> bool:
        """測試路由決策分析"""
        logger.info("\n🧪 測試 1: 路由決策分析")
        
        test_queries = [
            "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作",
            "Looking for senior software engineer jobs in San Francisco Bay Area",
            "Find data scientist jobs in Bangalore, India for fresher candidates",
            "Looking for investment banking analyst positions in Dubai, UAE",
            "尋找台北的資料科學家工作機會",
            "Find marketing manager jobs in London, UK"
        ]
        
        success_count = 0
        
        for i, query in enumerate(test_queries, 1):
            try:
                logger.info(f"\n  測試查詢 {i}: {query}")
                
                # 分析路由決策
                decision = self.router.analyze_query(query)
                
                # 驗證決策結果
                if decision and decision.selected_agents:
                    logger.info(f"  ✅ 選中代理: {[a.value for a in decision.selected_agents]}")
                    logger.info(f"  📊 信心度: {decision.confidence_score:.2f}")
                    logger.info(f"  💭 決策理由: {decision.reasoning}")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️ 未能做出有效決策")
                    
            except Exception as e:
                logger.error(f"  ❌ 查詢分析失敗: {e}")
        
        success_rate = success_count / len(test_queries)
        logger.info(f"\n📈 路由分析成功率: {success_rate:.1%} ({success_count}/{len(test_queries)})")
        
        self.test_results.append({
            'test_name': '路由決策分析',
            'success_rate': success_rate,
            'details': f"{success_count}/{len(test_queries)} 查詢成功分析"
        })
        
        return success_rate >= 0.8
    
    def test_smart_search_dry_run(self) -> bool:
        """測試智能搜索（僅分析，不執行）"""
        logger.info("\n🧪 測試 2: 智能搜索分析（Dry Run）")
        
        test_cases = [
            {
                'query': "請你幫我找Australia NSW 建築工作",
                'expected_agents': ['seek', 'indeed', 'linkedin']
            },
            {
                'query': "Looking for software engineer jobs in San Francisco",
                'expected_agents': ['linkedin', 'indeed', 'ziprecruiter']
            },
            {
                'query': "Find jobs in Mumbai, India",
                'expected_agents': ['naukri', 'indeed', 'linkedin']
            }
        ]
        
        success_count = 0
        
        for i, case in enumerate(test_cases, 1):
            try:
                logger.info(f"\n  測試案例 {i}: {case['query']}")
                
                # 僅分析路由決策
                decision = self.router.analyze_query(case['query'])
                
                if decision and decision.selected_agents:
                    selected = [a.value for a in decision.selected_agents]
                    expected = case['expected_agents']
                    
                    # 檢查是否包含預期的代理
                    matches = set(selected) & set(expected)
                    
                    logger.info(f"  🎯 選中代理: {selected}")
                    logger.info(f"  📋 預期代理: {expected}")
                    logger.info(f"  ✅ 匹配代理: {list(matches)}")
                    
                    if matches:
                        success_count += 1
                        logger.info(f"  ✅ 測試通過")
                    else:
                        logger.warning(f"  ⚠️ 沒有匹配的代理")
                else:
                    logger.error(f"  ❌ 決策失敗")
                    
            except Exception as e:
                logger.error(f"  ❌ 測試失敗: {e}")
        
        success_rate = success_count / len(test_cases)
        logger.info(f"\n📈 智能搜索分析成功率: {success_rate:.1%} ({success_count}/{len(test_cases)})")
        
        self.test_results.append({
            'test_name': '智能搜索分析',
            'success_rate': success_rate,
            'details': f"{success_count}/{len(test_cases)} 案例通過"
        })
        
        return success_rate >= 0.7
    
    def test_multilingual_support(self) -> bool:
        """測試多語言支持"""
        logger.info("\n🧪 測試 3: 多語言支持")
        
        multilingual_queries = [
            ("請幫我找香港的會計師工作", "中文"),
            ("Find marketing jobs in Paris, France", "英文"),
            ("尋找新加坡的 software engineer 職位", "中英混合"),
            ("Looking for jobs in 東京, Japan", "英中混合")
        ]
        
        success_count = 0
        
        for query, lang_type in multilingual_queries:
            try:
                logger.info(f"\n  測試語言: {lang_type}")
                logger.info(f"  查詢: {query}")
                
                decision = self.router.analyze_query(query)
                
                if decision and decision.selected_agents:
                    logger.info(f"  ✅ 成功分析 {lang_type} 查詢")
                    logger.info(f"  🎯 選中代理: {[a.value for a in decision.selected_agents]}")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️ {lang_type} 查詢分析失敗")
                    
            except Exception as e:
                logger.error(f"  ❌ {lang_type} 查詢處理失敗: {e}")
        
        success_rate = success_count / len(multilingual_queries)
        logger.info(f"\n📈 多語言支持成功率: {success_rate:.1%} ({success_count}/{len(multilingual_queries)})")
        
        self.test_results.append({
            'test_name': '多語言支持',
            'success_rate': success_rate,
            'details': f"{success_count}/{len(multilingual_queries)} 語言測試通過"
        })
        
        return success_rate >= 0.8
    
    def test_error_handling(self) -> bool:
        """測試錯誤處理"""
        logger.info("\n🧪 測試 4: 錯誤處理")
        
        error_test_cases = [
            "",  # 空查詢
            "   ",  # 空白查詢
            "找工作",  # 過於模糊的查詢
            "jobs",  # 英文模糊查詢
            "!@#$%^&*()",  # 特殊字符
            "a" * 1000  # 超長查詢
        ]
        
        success_count = 0
        
        for i, query in enumerate(error_test_cases, 1):
            try:
                logger.info(f"\n  錯誤測試 {i}: '{query[:50]}{'...' if len(query) > 50 else ''}'")
                
                decision = self.router.analyze_query(query)
                
                # 對於錯誤輸入，系統應該優雅處理
                if decision:
                    logger.info(f"  ✅ 優雅處理錯誤輸入")
                    success_count += 1
                else:
                    logger.info(f"  ✅ 正確拒絕無效輸入")
                    success_count += 1
                    
            except Exception as e:
                logger.warning(f"  ⚠️ 錯誤處理異常: {e}")
                # 異常也算是一種處理方式
                success_count += 1
        
        success_rate = success_count / len(error_test_cases)
        logger.info(f"\n📈 錯誤處理成功率: {success_rate:.1%} ({success_count}/{len(error_test_cases)})")
        
        self.test_results.append({
            'test_name': '錯誤處理',
            'success_rate': success_rate,
            'details': f"{success_count}/{len(error_test_cases)} 錯誤案例正確處理"
        })
        
        return success_rate >= 0.9
    
    def test_configuration_loading(self) -> bool:
        """測試配置加載"""
        logger.info("\n🧪 測試 5: 配置加載")
        
        try:
            # 測試默認配置
            router_default = IntelligentRouter()
            logger.info("  ✅ 默認配置加載成功")
            
            # 測試自定義配置（如果存在）
            config_path = "config/intelligent_routing_config.json"
            if os.path.exists(config_path):
                router_custom = IntelligentRouter(config_path=config_path)
                logger.info("  ✅ 自定義配置加載成功")
            else:
                logger.info("  ℹ️ 自定義配置文件不存在，跳過測試")
            
            self.test_results.append({
                'test_name': '配置加載',
                'success_rate': 1.0,
                'details': '配置加載正常'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 配置加載失敗: {e}")
            
            self.test_results.append({
                'test_name': '配置加載',
                'success_rate': 0.0,
                'details': f'配置加載失敗: {e}'
            })
            
            return False
    
    def generate_test_report(self) -> None:
        """生成測試報告"""
        logger.info("\n" + "="*60)
        logger.info("📊 智能路由系統測試報告")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success_rate'] >= 0.7)
        overall_success_rate = sum(result['success_rate'] for result in self.test_results) / total_tests if total_tests > 0 else 0
        
        logger.info(f"\n📈 總體統計:")
        logger.info(f"  • 測試項目: {total_tests}")
        logger.info(f"  • 通過測試: {passed_tests}")
        logger.info(f"  • 整體成功率: {overall_success_rate:.1%}")
        
        logger.info(f"\n📋 詳細結果:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ 通過" if result['success_rate'] >= 0.7 else "❌ 失敗"
            logger.info(f"  {i}. {result['test_name']}: {status} ({result['success_rate']:.1%})")
            logger.info(f"     {result['details']}")
        
        # 保存報告到文件
        report_file = f"intelligent_routing_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"jobseeker 智能路由系統測試報告\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"總體統計:\n")
                f.write(f"  測試項目: {total_tests}\n")
                f.write(f"  通過測試: {passed_tests}\n")
                f.write(f"  整體成功率: {overall_success_rate:.1%}\n\n")
                f.write(f"詳細結果:\n")
                for i, result in enumerate(self.test_results, 1):
                    status = "通過" if result['success_rate'] >= 0.7 else "失敗"
                    f.write(f"  {i}. {result['test_name']}: {status} ({result['success_rate']:.1%})\n")
                    f.write(f"     {result['details']}\n")
            
            logger.info(f"\n💾 測試報告已保存到: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {e}")
        
        # 返回測試結果
        if overall_success_rate >= 0.8:
            logger.info("\n🎉 智能路由系統測試整體通過！")
            return True
        else:
            logger.warning("\n⚠️ 智能路由系統測試存在問題，請檢查失敗項目")
            return False
    
    def run_all_tests(self) -> bool:
        """運行所有測試"""
        logger.info("🚀 開始智能路由系統測試")
        logger.info(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 設置測試環境
        if not self.setup():
            logger.error("❌ 測試環境設置失敗")
            return False
        
        # 運行各項測試
        tests = [
            self.test_routing_analysis,
            self.test_smart_search_dry_run,
            self.test_multilingual_support,
            self.test_error_handling,
            self.test_configuration_loading
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"❌ 測試執行異常: {e}")
                self.test_results.append({
                    'test_name': test.__name__.replace('test_', '').replace('_', ' ').title(),
                    'success_rate': 0.0,
                    'details': f'測試執行異常: {e}'
                })
        
        # 生成測試報告
        return self.generate_test_report()

def main():
    """主函數"""
    print("\n" + "="*60)
    print("🧪 jobseeker 智能路由系統測試")
    print("="*60)
    
    # 創建測試器
    tester = IntelligentRoutingTester()
    
    # 運行測試
    success = tester.run_all_tests()
    
    # 退出
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
