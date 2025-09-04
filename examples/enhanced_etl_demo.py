#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強型ETL流程演示腳本
展示如何使用新的整合架構進行智能化數據抓取和處理

Author: JobSpy Team
Date: 2025-01-05
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from jobseeker.seek.enhanced_etl_orchestrator import (
    EnhancedETLOrchestrator,
    ScrapingJobConfig,
    ScrapingStrategy
)


class EnhancedETLDemo:
    """
    增強型ETL演示類
    展示各種使用場景和功能
    """
    
    def __init__(self):
        self.orchestrator = EnhancedETLOrchestrator(
            output_path="./demo_output"
        )
    
    async def demo_basic_usage(self):
        """
        演示基本使用方法
        """
        print("\n" + "="*80)
        print("演示1: 基本使用 - 混合模式爬蟲")
        print("="*80)
        
        # 基本配置
        job_config = ScrapingJobConfig(
            search_term="data scientist",
            location="Melbourne VIC",
            max_results=10,
            strategy=ScrapingStrategy.HYBRID
        )
        
        print(f"搜索配置: {job_config.search_term} @ {job_config.location}")
        print(f"策略: {job_config.strategy.value}")
        
        # 執行任務
        result = await self.orchestrator.execute_scraping_job(job_config)
        
        # 顯示結果
        self._display_result(result, "基本使用")
        
        return result
    
    async def demo_visual_primary(self):
        """
        演示視覺爬蟲為主的高質量抓取
        """
        print("\n" + "="*80)
        print("演示2: 視覺爬蟲為主 - 高質量數據抓取")
        print("="*80)
        
        # 高質量配置
        job_config = ScrapingJobConfig(
            search_term="senior software engineer",
            location="Sydney NSW",
            max_results=5,
            strategy=ScrapingStrategy.VISUAL_PRIMARY,
            high_quality_required=True,
            enable_cross_validation=True
        )
        
        print(f"搜索配置: {job_config.search_term} @ {job_config.location}")
        print(f"策略: {job_config.strategy.value}")
        print(f"高質量模式: {job_config.high_quality_required}")
        
        # 執行任務
        result = await self.orchestrator.execute_scraping_job(job_config)
        
        # 顯示結果
        self._display_result(result, "視覺爬蟲為主")
        
        return result
    
    async def demo_traditional_primary(self):
        """
        演示傳統爬蟲為主的大量數據抓取
        """
        print("\n" + "="*80)
        print("演示3: 傳統爬蟲為主 - 大量數據抓取")
        print("="*80)
        
        # 大量數據配置
        job_config = ScrapingJobConfig(
            search_term="python",
            location="Australia",
            max_results=50,
            max_pages=3,
            strategy=ScrapingStrategy.TRADITIONAL_PRIMARY,
            large_volume_required=True
        )
        
        print(f"搜索配置: {job_config.search_term} @ {job_config.location}")
        print(f"策略: {job_config.strategy.value}")
        print(f"大量數據模式: {job_config.large_volume_required}")
        print(f"最大頁數: {job_config.max_pages}")
        
        # 執行任務
        result = await self.orchestrator.execute_scraping_job(job_config)
        
        # 顯示結果
        self._display_result(result, "傳統爬蟲為主")
        
        return result
    
    async def demo_strategy_comparison(self):
        """
        演示不同策略的性能比較
        """
        print("\n" + "="*80)
        print("演示4: 策略性能比較")
        print("="*80)
        
        strategies = [
            ScrapingStrategy.VISUAL_ONLY,
            ScrapingStrategy.TRADITIONAL_ONLY,
            ScrapingStrategy.HYBRID
        ]
        
        results = {}
        
        for strategy in strategies:
            print(f"\n測試策略: {strategy.value}")
            print("-" * 40)
            
            job_config = ScrapingJobConfig(
                search_term="web developer",
                location="Brisbane QLD",
                max_results=5,
                strategy=strategy
            )
            
            result = await self.orchestrator.execute_scraping_job(job_config)
            results[strategy.value] = result
            
            if result['success']:
                print(f"✓ 成功: {result['total_jobs']} 個職位")
                print(f"  執行時間: {result['execution_time']:.2f}秒")
                
                # 顯示數據源摘要
                for source, summary in result['data_sources_summary'].items():
                    print(f"  {source}: {summary['job_count']} 個職位 ({summary['execution_time']:.2f}秒)")
            else:
                print(f"✗ 失敗: {result.get('error')}")
        
        # 性能比較
        print("\n" + "="*40)
        print("性能比較摘要")
        print("="*40)
        
        for strategy_name, result in results.items():
            if result['success']:
                efficiency = result['total_jobs'] / result['execution_time'] if result['execution_time'] > 0 else 0
                print(f"{strategy_name:20}: {result['total_jobs']:3d} 職位, {result['execution_time']:6.2f}秒, {efficiency:5.2f} 職位/秒")
        
        return results
    
    async def demo_data_export(self):
        """
        演示數據導出功能
        """
        print("\n" + "="*80)
        print("演示5: 數據導出功能")
        print("="*80)
        
        # 執行一個基本任務
        job_config = ScrapingJobConfig(
            search_term="machine learning",
            location="Perth WA",
            max_results=8,
            strategy=ScrapingStrategy.HYBRID
        )
        
        result = await self.orchestrator.execute_scraping_job(job_config)
        
        if result['success']:
            print(f"成功抓取 {result['total_jobs']} 個職位")
            
            # 導出多種格式
            exported_files = await self.orchestrator.export_results(
                result, 
                formats=['json', 'csv']
            )
            
            print("\n導出文件:")
            for file_path in exported_files:
                file_size = Path(file_path).stat().st_size
                print(f"  {file_path} ({file_size:,} bytes)")
        
        return result
    
    def demo_performance_monitoring(self):
        """
        演示性能監控功能
        """
        print("\n" + "="*80)
        print("演示6: 性能監控報告")
        print("="*80)
        
        # 獲取性能報告
        performance_report = self.orchestrator.get_performance_report()
        
        print("整體性能統計:")
        print(f"  總處理職位數: {performance_report['total_jobs_processed']}")
        print(f"  成功職位數: {performance_report['successful_jobs']}")
        print(f"  失敗職位數: {performance_report['failed_jobs']}")
        print(f"  成功率: {performance_report['success_rate']:.2%}")
        print(f"  平均執行時間: {performance_report['average_execution_time']:.2f}秒")
        
        print("\n策略使用統計:")
        for strategy, count in performance_report['strategy_usage'].items():
            print(f"  {strategy}: {count} 次")
        
        print("\nETL質量統計:")
        etl_stats = performance_report['etl_quality_stats']
        for metric, value in etl_stats.items():
            print(f"  {metric}: {value}")
        
        return performance_report
    
    def _display_result(self, result: dict, demo_name: str):
        """
        顯示執行結果
        
        Args:
            result: 執行結果
            demo_name: 演示名稱
        """
        print(f"\n{demo_name} - 執行結果:")
        print("-" * 40)
        
        if result['success']:
            print(f"✓ 執行成功")
            print(f"  策略: {result['strategy_used']}")
            print(f"  職位數量: {result['total_jobs']}")
            print(f"  執行時間: {result['execution_time']:.2f}秒")
            
            # 顯示數據源摘要
            print("  數據源摘要:")
            for source, summary in result['data_sources_summary'].items():
                status = "✓" if summary['success'] else "✗"
                print(f"    {status} {source}: {summary['job_count']} 個職位 ({summary['execution_time']:.2f}秒)")
            
            # 顯示質量報告
            quality_report = result.get('quality_report', {})
            if quality_report:
                print("  數據質量:")
                print(f"    有效職位: {quality_report.get('valid_jobs', 0)}")
                print(f"    無效職位: {quality_report.get('invalid_jobs', 0)}")
                print(f"    去重移除: {quality_report.get('duplicates_removed', 0)}")
            
            # 顯示前3個職位
            if result['jobs']:
                print("  前3個職位:")
                for i, job in enumerate(result['jobs'][:3], 1):
                    title = job.get('title', '未知職位')
                    company = job.get('company', '未知公司')
                    location = job.get('location', '未知地點')
                    print(f"    {i}. {title} - {company} ({location})")
        else:
            print(f"✗ 執行失敗: {result.get('error')}")
    
    async def run_all_demos(self):
        """
        運行所有演示
        """
        print("🚀 增強型ETL流程演示開始")
        print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 運行各個演示
            await self.demo_basic_usage()
            await self.demo_visual_primary()
            await self.demo_traditional_primary()
            await self.demo_strategy_comparison()
            await self.demo_data_export()
            self.demo_performance_monitoring()
            
            print("\n" + "="*80)
            print("🎉 所有演示完成!")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ 演示過程中出錯: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """
    主函數
    """
    demo = EnhancedETLDemo()
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        demo_name = sys.argv[1].lower()
        
        if demo_name == "basic":
            await demo.demo_basic_usage()
        elif demo_name == "visual":
            await demo.demo_visual_primary()
        elif demo_name == "traditional":
            await demo.demo_traditional_primary()
        elif demo_name == "comparison":
            await demo.demo_strategy_comparison()
        elif demo_name == "export":
            await demo.demo_data_export()
        elif demo_name == "performance":
            demo.demo_performance_monitoring()
        elif demo_name == "all":
            await demo.run_all_demos()
        else:
            print(f"未知的演示名稱: {demo_name}")
            print("可用的演示: basic, visual, traditional, comparison, export, performance, all")
    else:
        # 默認運行所有演示
        await demo.run_all_demos()


if __name__ == "__main__":
    print("""
    增強型ETL流程演示腳本
    
    使用方法:
        python enhanced_etl_demo.py [演示名稱]
    
    可用演示:
        basic       - 基本使用演示
        visual      - 視覺爬蟲為主演示
        traditional - 傳統爬蟲為主演示
        comparison  - 策略性能比較
        export      - 數據導出功能
        performance - 性能監控報告
        all         - 運行所有演示 (默認)
    
    示例:
        python enhanced_etl_demo.py basic
        python enhanced_etl_demo.py comparison
        python enhanced_etl_demo.py all
    """)
    
    asyncio.run(main())