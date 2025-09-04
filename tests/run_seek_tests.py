#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek爬蟲測試運行器
統一運行所有Seek相關的測試案例
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "jobseeker" / "seek"))

# 導入測試模組
try:
    import test_seek_crawler_user_behavior
    import test_seek_website_interaction
    TestSeekCrawlerUserBehavior = test_seek_crawler_user_behavior.TestSeekCrawlerUserBehavior
    TestSeekWebsiteRunner = test_seek_website_interaction.TestSeekWebsiteRunner
except ImportError as e:
    print(f"警告: 無法導入測試模組: {e}")
    print("請確保所有依賴都已安裝")
    TestSeekCrawlerUserBehavior = None
    TestSeekWebsiteRunner = None


class SeekTestRunner:
    """Seek測試運行器主類"""
    
    def __init__(self):
        self.results = []
        
    def run_unit_tests(self):
        """運行單元測試（用戶行為模擬）"""
        print("\n" + "="*60)
        print("開始運行Seek爬蟲用戶行為測試")
        print("="*60)
        
        try:
            # 創建測試實例
            behavior_tester = TestSeekCrawlerUserBehavior()
            
            # 運行各項測試
            tests = [
                ("基本職位搜索模擬", behavior_tester.test_basic_job_search_simulation),
                ("高級搜索過濾", behavior_tester.test_advanced_search_with_filters),
                ("多次搜索會話", behavior_tester.test_multiple_search_sessions),
                ("數據導出模擬", behavior_tester.test_data_export_simulation),
                ("錯誤處理模擬", behavior_tester.test_error_handling_simulation),
                ("性能監控", behavior_tester.test_performance_monitoring),
                ("並發搜索模擬", behavior_tester.test_concurrent_search_simulation)
            ]
            
            unit_results = []
            
            for test_name, test_func in tests:
                try:
                    print(f"\n--- 執行: {test_name} ---")
                    test_func()
                    unit_results.append((test_name, "通過", None))
                    print(f"✓ {test_name} 完成")
                    
                except Exception as e:
                    unit_results.append((test_name, "失敗", str(e)))
                    print(f"✗ {test_name} 失敗: {str(e)[:100]}...")
            
            self.results.extend(unit_results)
            return unit_results
            
        except Exception as e:
            print(f"單元測試運行失敗: {str(e)}")
            return [("單元測試", "失敗", str(e))]
    
    async def run_integration_tests(self):
        """運行集成測試（網站互動）"""
        print("\n" + "="*60)
        print("開始運行Seek網站互動測試")
        print("="*60)
        
        try:
            # 創建網站測試運行器
            website_runner = TestSeekWebsiteRunner()
            
            # 運行所有網站互動測試
            integration_results = await website_runner.run_all_tests()
            
            self.results.extend(integration_results)
            return integration_results
            
        except Exception as e:
            print(f"集成測試運行失敗: {str(e)}")
            return [("集成測試", "失敗", str(e))]
    
    def run_quick_validation(self):
        """運行快速驗證測試"""
        print("\n" + "="*60)
        print("開始運行快速驗證測試")
        print("="*60)
        
        validation_results = []
        
        # 1. 檢查模組導入
        try:
            import sys
            seek_path = str(project_root / "jobseeker" / "seek")
            if seek_path not in sys.path:
                sys.path.insert(0, seek_path)
            
            import seek_crawler_engine
            import seek_scraper_enhanced
            import config
            import etl_processor
            
            validation_results.append(("模組導入檢查", "通過", None))
            print("✓ 所有核心模組導入成功")
            
        except Exception as e:
            validation_results.append(("模組導入檢查", "失敗", str(e)))
            print(f"✗ 模組導入失敗: {str(e)}")
        
        # 2. 檢查配置初始化
        try:
            seek_config = config.SeekCrawlerConfig()
            validation_results.append(("配置初始化檢查", "通過", None))
            print("✓ 配置初始化成功")
            
        except Exception as e:
            validation_results.append(("配置初始化檢查", "失敗", str(e)))
            print(f"✗ 配置初始化失敗: {str(e)}")
        
        # 3. 檢查爬蟲引擎初始化
        try:
            seek_config = config.SeekCrawlerConfig()
            engine = seek_crawler_engine.SeekCrawlerEngine(seek_config)
            validation_results.append(("爬蟲引擎初始化檢查", "通過", None))
            print("✓ 爬蟲引擎初始化成功")
            
        except Exception as e:
            validation_results.append(("爬蟲引擎初始化檢查", "失敗", str(e)))
            print(f"✗ 爬蟲引擎初始化失敗: {str(e)}")
        
        # 4. 檢查依賴包
        dependencies = [
            'playwright',
            'bs4',  # beautifulsoup4的導入名稱是bs4
            'pandas',
            'requests',
            'asyncio'
        ]
        
        for package in dependencies:
            try:
                __import__(package)
                validation_results.append((f"依賴包檢查: {package}", "通過", None))
                print(f"✓ {package} 可用")
                
            except ImportError as e:
                validation_results.append((f"依賴包檢查: {package}", "失敗", str(e)))
                print(f"✗ {package} 不可用: {str(e)}")
        
        self.results.extend(validation_results)
        return validation_results
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "="*60)
        print("測試報告")
        print("="*60)
        
        if not self.results:
            print("沒有測試結果可報告")
            return
        
        # 統計結果
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r[1] == "通過"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        # 詳細結果
        print("\n詳細結果:")
        print("-" * 60)
        
        for test_name, status, error in self.results:
            status_icon = "✓" if status == "通過" else "✗"
            print(f"{status_icon} {test_name}: {status}")
            
            if error and status == "失敗":
                # 只顯示錯誤的前100個字符
                error_preview = error[:100] + "..." if len(error) > 100 else error
                print(f"  錯誤: {error_preview}")
        
        # 建議
        print("\n建議:")
        print("-" * 60)
        
        if failed_tests == 0:
            print("🎉 所有測試都通過了！Seek爬蟲引擎運行正常。")
        elif failed_tests < total_tests * 0.3:
            print("⚠ 大部分測試通過，但有一些問題需要注意。")
            print("建議檢查失敗的測試並修復相關問題。")
        else:
            print("❌ 多個測試失敗，建議進行以下檢查:")
            print("1. 確保所有依賴包都已正確安裝")
            print("2. 檢查網絡連接")
            print("3. 驗證Seek網站是否可訪問")
            print("4. 檢查配置文件設置")
    
    async def run_all_tests(self, test_types: List[str] = None):
        """運行所有測試"""
        if test_types is None:
            test_types = ['validation', 'unit', 'integration']
        
        print("開始Seek爬蟲引擎完整測試套件")
        print(f"測試類型: {', '.join(test_types)}")
        
        # 運行快速驗證
        if 'validation' in test_types:
            self.run_quick_validation()
        
        # 運行單元測試
        if 'unit' in test_types:
            self.run_unit_tests()
        
        # 運行集成測試
        if 'integration' in test_types:
            await self.run_integration_tests()
        
        # 生成報告
        self.generate_test_report()


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Seek爬蟲測試運行器')
    parser.add_argument(
        '--type', 
        choices=['validation', 'unit', 'integration', 'all'],
        default='all',
        help='要運行的測試類型'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='只運行快速驗證測試'
    )
    
    args = parser.parse_args()
    
    # 創建測試運行器
    runner = SeekTestRunner()
    
    async def run_tests():
        if args.quick:
            runner.run_quick_validation()
            runner.generate_test_report()
        elif args.type == 'all':
            await runner.run_all_tests()
        elif args.type == 'validation':
            await runner.run_all_tests(['validation'])
        elif args.type == 'unit':
            await runner.run_all_tests(['unit'])
        elif args.type == 'integration':
            await runner.run_all_tests(['integration'])
    
    # 運行測試
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
    except Exception as e:
        print(f"\n測試運行過程中發生錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()