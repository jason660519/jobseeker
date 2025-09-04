#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
視覺爬蟲與傳統爬蟲協調機制測試腳本

此腳本專門測試優化後的協調機制，包括：
1. 智能策略選擇
2. 動態性能評估
3. 混合模式執行
4. 性能監控與反饋
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

from jobseeker.seek.enhanced_etl_orchestrator import (
    EnhancedETLOrchestrator,
    ScrapingJobConfig,
    ScrapingStrategy
)
from jobseeker.enhanced_logging import get_enhanced_logger

class CoordinationTester:
    """
    協調機制測試器
    """
    
    def __init__(self):
        self.logger = get_enhanced_logger(self.__class__.__name__)
        self.orchestrator = EnhancedETLOrchestrator("coordination_test_output")
        self.test_results = []
    
    async def test_strategy_selection(self):
        """
        測試智能策略選擇功能
        """
        self.logger.info("開始測試智能策略選擇...")
        
        test_configs = [
            # 小數據量測試
            ScrapingJobConfig(
                search_term="python developer",
                max_results=10,
                high_quality_required=True
            ),
            # 大數據量測試
            ScrapingJobConfig(
                search_term="data scientist",
                max_results=100,
                large_volume_required=True
            ),
            # 平衡測試
            ScrapingJobConfig(
                search_term="software engineer",
                max_results=50
            )
        ]
        
        for i, config in enumerate(test_configs, 1):
            self.logger.info(f"測試配置 {i}: {config.search_term}")
            
            # 獲取策略選擇器推薦的策略
            selected_strategy = self.orchestrator.strategy_selector.select_strategy(config)
            self.logger.info(f"選擇的策略: {selected_strategy.value}")
            
            # 記錄策略選擇結果
            self.test_results.append({
                'test_type': 'strategy_selection',
                'config': config.search_term,
                'selected_strategy': selected_strategy.value,
                'max_results': config.max_results,
                'high_quality': config.high_quality_required,
                'large_volume': config.large_volume_required
            })
    
    async def test_performance_tracking(self):
        """
        測試性能追蹤功能
        """
        self.logger.info("開始測試性能追蹤...")
        
        # 模擬不同策略的性能數據
        performance_data = [
            (ScrapingStrategy.VISUAL_ONLY, True, 15.5, 0.9, 25),
            (ScrapingStrategy.TRADITIONAL_ONLY, True, 8.2, 0.7, 15),
            (ScrapingStrategy.HYBRID, True, 22.1, 0.85, 40),
            (ScrapingStrategy.VISUAL_PRIMARY, False, 30.0, 0.6, 5),
            (ScrapingStrategy.TRADITIONAL_PRIMARY, True, 12.3, 0.8, 20)
        ]
        
        for strategy, success, exec_time, quality, job_count in performance_data:
            self.orchestrator.strategy_selector.update_strategy_performance(
                strategy, success, exec_time, quality, job_count
            )
            self.logger.info(f"更新策略 {strategy.value} 性能: 成功={success}, 時間={exec_time}s, 質量={quality}")
        
        # 檢查性能統計
        for strategy in ScrapingStrategy:
            stats = self.orchestrator.strategy_selector.strategy_performance.get(strategy, {})
            if stats:
                self.logger.info(f"策略 {strategy.value} 統計: {stats}")
    
    async def test_hybrid_execution(self):
        """
        測試混合模式執行
        """
        self.logger.info("開始測試混合模式執行...")
        
        # 創建混合模式配置
        hybrid_config = ScrapingJobConfig(
            search_term="machine learning",
            strategy=ScrapingStrategy.HYBRID,
            max_results=30,
            timeout=60
        )
        
        start_time = time.time()
        
        try:
            # 執行混合模式任務
            result = await self.orchestrator.execute_scraping_job(hybrid_config)
            execution_time = time.time() - start_time
            
            self.logger.info(f"混合模式執行完成: {execution_time:.2f}秒")
            self.logger.info(f"結果摘要: {result.get('summary', {})}")
            
            # 記錄測試結果
            self.test_results.append({
                'test_type': 'hybrid_execution',
                'execution_time': execution_time,
                'job_count': result.get('summary', {}).get('total_jobs', 0),
                'data_sources': len(result.get('data_sources', [])),
                'success': result.get('success', False)
            })
            
        except Exception as e:
            self.logger.error(f"混合模式執行失敗: {e}")
            self.test_results.append({
                'test_type': 'hybrid_execution',
                'error': str(e),
                'success': False
            })
    
    async def test_adaptive_coordination(self):
        """
        測試自適應協調功能
        """
        self.logger.info("開始測試自適應協調...")
        
        # 測試不同場景下的策略適應
        scenarios = [
            {
                'name': '高質量需求場景',
                'config': ScrapingJobConfig(
                    search_term="senior developer",
                    high_quality_required=True,
                    max_results=20
                )
            },
            {
                'name': '大數據量場景',
                'config': ScrapingJobConfig(
                    search_term="developer",
                    large_volume_required=True,
                    max_results=200
                )
            },
            {
                'name': '平衡場景',
                'config': ScrapingJobConfig(
                    search_term="python",
                    max_results=50
                )
            }
        ]
        
        for scenario in scenarios:
            self.logger.info(f"測試場景: {scenario['name']}")
            
            # 獲取推薦策略
            strategy = self.orchestrator.strategy_selector.select_strategy(scenario['config'])
            self.logger.info(f"推薦策略: {strategy.value}")
            
            # 計算策略評分
            scores = self.orchestrator.strategy_selector._calculate_strategy_scores(scenario['config'])
            self.logger.info(f"策略評分: {scores}")
            
            # 記錄結果
            self.test_results.append({
                'test_type': 'adaptive_coordination',
                'scenario': scenario['name'],
                'recommended_strategy': strategy.value,
                'strategy_scores': {k.value: v for k, v in scores.items()}
            })
    
    def generate_test_report(self) -> Dict[str, Any]:
        """
        生成測試報告
        """
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'test_types': list(set(result['test_type'] for result in self.test_results)),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'strategy_selection_tests': [],
            'performance_tracking_tests': [],
            'hybrid_execution_tests': [],
            'adaptive_coordination_tests': [],
            'orchestrator_stats': self.orchestrator.get_performance_report()
        }
        
        # 分類測試結果
        for result in self.test_results:
            test_type = result['test_type']
            if test_type == 'strategy_selection':
                report['strategy_selection_tests'].append(result)
            elif test_type == 'performance_tracking':
                report['performance_tracking_tests'].append(result)
            elif test_type == 'hybrid_execution':
                report['hybrid_execution_tests'].append(result)
            elif test_type == 'adaptive_coordination':
                report['adaptive_coordination_tests'].append(result)
        
        return report
    
    async def run_all_tests(self):
        """
        運行所有測試
        """
        self.logger.info("開始協調機制綜合測試...")
        
        try:
            # 運行各項測試
            await self.test_strategy_selection()
            await self.test_performance_tracking()
            await self.test_adaptive_coordination()
            await self.test_hybrid_execution()
            
            # 生成報告
            report = self.generate_test_report()
            
            # 輸出測試結果
            self.print_test_results(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"測試執行失敗: {e}")
            raise
    
    def print_test_results(self, report: Dict[str, Any]):
        """
        打印測試結果
        """
        print("\n" + "="*80)
        print("協調機制測試報告")
        print("="*80)
        
        # 測試摘要
        summary = report['test_summary']
        print(f"\n📊 測試摘要:")
        print(f"  總測試數: {summary['total_tests']}")
        print(f"  測試類型: {', '.join(summary['test_types'])}")
        print(f"  測試時間: {summary['timestamp']}")
        
        # 策略選擇測試
        if report['strategy_selection_tests']:
            print(f"\n🎯 策略選擇測試:")
            for test in report['strategy_selection_tests']:
                print(f"  {test['config']}: {test['selected_strategy']} (最大結果: {test['max_results']})")
        
        # 自適應協調測試
        if report['adaptive_coordination_tests']:
            print(f"\n🔄 自適應協調測試:")
            for test in report['adaptive_coordination_tests']:
                print(f"  {test['scenario']}: {test['recommended_strategy']}")
                scores = test['strategy_scores']
                top_strategies = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"    前三策略評分: {', '.join([f'{k}({v:.2f})' for k, v in top_strategies])}")
        
        # 混合執行測試
        if report['hybrid_execution_tests']:
            print(f"\n🔀 混合執行測試:")
            for test in report['hybrid_execution_tests']:
                if test.get('success'):
                    print(f"  執行時間: {test.get('execution_time', 0):.2f}秒")
                    print(f"  職位數量: {test.get('job_count', 0)}")
                    print(f"  數據源數: {test.get('data_sources', 0)}")
                else:
                    print(f"  執行失敗: {test.get('error', '未知錯誤')}")
        
        # 性能統計
        stats = report['orchestrator_stats']
        print(f"\n📈 性能統計:")
        print(f"  平均執行時間: {stats.get('average_execution_time', 0):.2f}秒")
        print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
        print(f"  總處理職位: {stats.get('total_jobs_collected', 0)}")
        
        print("\n" + "="*80)
        print("✅ 協調機制測試完成!")
        print("="*80)

async def main():
    """
    主函數
    """
    tester = CoordinationTester()
    
    try:
        await tester.run_all_tests()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)