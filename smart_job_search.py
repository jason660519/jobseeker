#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 智能工作搜索 CLI 工具
使用智能路由系統進行工作搜索

使用方法:
    python smart_job_search.py "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
    python smart_job_search.py "Looking for software engineer jobs in San Francisco" --results 20
    python smart_job_search.py "Find marketing jobs in Mumbai" --location "Mumbai, India" --hours 24

Author: jobseeker Team
Date: 2025-01-27
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Optional

# 添加 jobseeker 到路徑
sys.path.insert(0, str(Path(__file__).parent))

try:
    from jobseeker.route_manager import RouteManager, smart_scrape_jobs
    from jobseeker.intelligent_router import IntelligentRouter
except ImportError as e:
    print(f"導入錯誤: {e}")
    print("請確保 jobseeker 已正確安裝")
    sys.exit(1)

def parse_arguments():
    """
    解析命令行參數
    
    Returns:
        解析後的參數
    """
    parser = argparse.ArgumentParser(
        description="jobseeker 智能工作搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
  %(prog)s "Looking for software engineer jobs in San Francisco" --results 20
  %(prog)s "Find marketing jobs in Mumbai" --location "Mumbai, India" --hours 24
  %(prog)s "尋找台北的資料科學家工作" --output jobs.csv
        """
    )
    
    # 必需參數
    parser.add_argument(
        "query",
        help="工作搜索查詢（支持中文和英文）"
    )
    
    # 可選參數
    parser.add_argument(
        "-l", "--location",
        help="額外的位置信息（會與查詢結合分析）"
    )
    
    parser.add_argument(
        "-r", "--results",
        type=int,
        default=15,
        help="期望的結果數量（默認: 15）"
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        help="職位發布時間限制（小時）"
    )
    
    parser.add_argument(
        "-c", "--country",
        default="worldwide",
        help="Indeed 國家設置（默認: worldwide）"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="輸出文件路徑（支持 .csv, .json, .xlsx）"
    )
    
    parser.add_argument(
        "--explain",
        action="store_true",
        help="顯示詳細的路由決策解釋"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只顯示路由決策，不執行實際搜索"
    )
    
    parser.add_argument(
        "--config",
        help="自定義配置文件路徑"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細輸出"
    )
    
    return parser.parse_args()

def setup_logging(verbose: bool):
    """
    設置日誌級別
    
    Args:
        verbose: 是否顯示詳細輸出
    """
    import logging
    
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def print_routing_decision(router: IntelligentRouter, query: str, explain: bool = False):
    """
    打印路由決策信息
    
    Args:
        router: 智能路由器
        query: 查詢字符串
        explain: 是否顯示詳細解釋
    """
    decision = router.analyze_query(query)
    
    print("\n" + "=" * 60)
    print("智能路由決策")
    print("=" * 60)
    print(f"查詢: {query}")
    print(f"選中的代理: {[agent.value for agent in decision.selected_agents]}")
    print(f"信心度: {decision.confidence_score:.2f}")
    print(f"決策理由: {decision.reasoning}")
    
    if decision.geographic_match:
        print(f"地理匹配: {decision.geographic_match}")
    
    if decision.industry_match:
        print(f"行業匹配: {decision.industry_match}")
    
    if decision.fallback_agents:
        print(f"後備代理: {[agent.value for agent in decision.fallback_agents]}")
    
    if explain:
        print("\n" + router.get_routing_explanation(decision))
    
    print("=" * 60)

def save_results(jobs_data, output_path: str):
    """
    保存搜索結果到文件
    
    Args:
        jobs_data: 工作數據
        output_path: 輸出文件路徑
    """
    if jobs_data is None or jobs_data.empty:
        print("沒有數據可保存")
        return
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if output_path.suffix.lower() == '.csv':
            jobs_data.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif output_path.suffix.lower() == '.json':
            jobs_data.to_json(output_path, orient='records', indent=2, force_ascii=False)
        elif output_path.suffix.lower() in ['.xlsx', '.xls']:
            jobs_data.to_excel(output_path, index=False)
        else:
            # 默認保存為 CSV
            output_path = output_path.with_suffix('.csv')
            jobs_data.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n結果已保存到: {output_path}")
        print(f"保存了 {len(jobs_data)} 個職位")
        
    except Exception as e:
        print(f"保存文件時出錯: {e}")

def display_results_summary(result):
    """
    顯示搜索結果摘要
    
    Args:
        result: 聚合結果
    """
    print("\n" + "=" * 60)
    print("搜索結果摘要")
    print("=" * 60)
    print(f"總執行時間: {result.total_execution_time:.2f} 秒")
    print(f"總職位數量: {result.total_jobs}")
    print(f"成功的代理: {[a.value for a in result.successful_agents]}")
    
    if result.failed_agents:
        print(f"失敗的代理: {[a.value for a in result.failed_agents]}")
    
    print(f"\n各代理詳細結果:")
    for exec_result in result.execution_results:
        status = "✓" if exec_result.success else "✗"
        print(f"  {status} {exec_result.agent.value}: {exec_result.job_count} 職位 ({exec_result.execution_time:.2f}s)")
        if exec_result.error_message:
            print(f"    錯誤: {exec_result.error_message}")
    
    # 顯示前幾個職位
    if result.combined_jobs_data is not None and not result.combined_jobs_data.empty:
        print(f"\n前 5 個職位:")
        print("-" * 60)
        
        for i, (_, job) in enumerate(result.combined_jobs_data.head().iterrows()):
            print(f"{i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
            if 'location' in job:
                print(f"   位置: {job['location']}")
            if 'source_agent' in job:
                print(f"   來源: {job['source_agent']}")
            print()
    
    print("=" * 60)

def main():
    """
    主函數
    """
    args = parse_arguments()
    
    # 設置日誌
    setup_logging(args.verbose)
    
    print("jobseeker 智能工作搜索工具")
    print("=" * 40)
    
    try:
        # 創建路由管理器
        manager = RouteManager(config_path=args.config)
        
        # 如果是 dry-run，只顯示路由決策
        if args.dry_run:
            print_routing_decision(manager.router, args.query, args.explain)
            return
        
        # 顯示路由決策（如果需要）
        if args.explain:
            print_routing_decision(manager.router, args.query, True)
        
        # 執行智能搜索
        print(f"\n開始搜索: {args.query}")
        if args.location:
            print(f"額外位置: {args.location}")
        
        start_time = time.time()
        
        result = manager.smart_scrape_jobs(
            user_query=args.query,
            location=args.location,
            results_wanted=args.results,
            hours_old=args.hours,
            country_indeed=args.country
        )
        
        # 顯示結果
        display_results_summary(result)
        
        # 保存結果（如果指定了輸出文件）
        if args.output:
            save_results(result.combined_jobs_data, args.output)
        
        # 成功完成
        print(f"\n搜索完成！總共找到 {result.total_jobs} 個職位")
        
    except KeyboardInterrupt:
        print("\n搜索被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n搜索過程中出現錯誤: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
