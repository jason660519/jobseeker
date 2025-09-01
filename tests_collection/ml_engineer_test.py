#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Engineer 職位測試腳本
測試每個求職網站搜尋ML Engineer職位，每個網站15個，限制在近7日內的新增工作崗位
"""

import os
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from jobspy import scrape_jobs
from jobspy.model import Site


def create_output_directory() -> str:
    """
    創建輸出目錄
    
    Returns:
        str: 輸出目錄路徑
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"ml_engineer_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def scrape_site_jobs(site: Site, output_dir: str) -> Dict[str, Any]:
    """
    爬取指定網站的ML Engineer職位
    
    Args:
        site: 求職網站
        output_dir: 輸出目錄
        
    Returns:
        Dict: 包含網站名稱、職位數量、執行時間等資訊的字典
    """
    site_name = site.value
    print(f"\n開始測試 {site_name}...")
    
    start_time = datetime.now()
    
    try:
        # 計算7天前的日期
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # 爬取職位資料
        jobs_df = scrape_jobs(
            site_name=site,
            search_term="ML Engineer",
            location="Australia",  # 可以根據需要調整地區
            results_wanted=15,
            hours_old=168,  # 7天 = 168小時
            country_indeed="Australia"  # 針對Indeed的特殊參數
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if jobs_df is not None and not jobs_df.empty:
            # 保存為CSV
            csv_filename = os.path.join(output_dir, f"{site_name}_ml_engineer_jobs.csv")
            jobs_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            
            # 保存原始JSON數據
            json_filename = os.path.join(output_dir, f"{site_name}_ml_engineer_raw_data.json")
            jobs_data = jobs_df.to_dict('records')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2, default=str)
            
            job_count = len(jobs_df)
            print(f"✅ {site_name}: 成功獲取 {job_count} 個職位")
            
            return {
                'site': site_name,
                'status': 'success',
                'job_count': job_count,
                'execution_time': execution_time,
                'avg_time_per_job': execution_time / job_count if job_count > 0 else 0,
                'csv_file': csv_filename,
                'json_file': json_filename,
                'error': None
            }
        else:
            print(f"❌ {site_name}: 未找到職位")
            return {
                'site': site_name,
                'status': 'no_results',
                'job_count': 0,
                'execution_time': execution_time,
                'avg_time_per_job': 0,
                'csv_file': None,
                'json_file': None,
                'error': 'No jobs found'
            }
            
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        error_msg = str(e)
        print(f"❌ {site_name}: 錯誤 - {error_msg}")
        
        return {
            'site': site_name,
            'status': 'error',
            'job_count': 0,
            'execution_time': execution_time,
            'avg_time_per_job': 0,
            'csv_file': None,
            'json_file': None,
            'error': error_msg
        }


def combine_all_results(results: List[Dict], output_dir: str) -> None:
    """
    合併所有網站的結果
    
    Args:
        results: 所有網站的測試結果
        output_dir: 輸出目錄
    """
    # 合併所有成功的CSV文件
    all_jobs = []
    
    for result in results:
        if result['status'] == 'success' and result['csv_file']:
            try:
                df = pd.read_csv(result['csv_file'])
                df['source_site'] = result['site']
                all_jobs.append(df)
            except Exception as e:
                print(f"讀取 {result['site']} CSV文件時出錯: {e}")
    
    if all_jobs:
        combined_df = pd.concat(all_jobs, ignore_index=True)
        combined_csv = os.path.join(output_dir, "all_sites_ml_engineer_combined.csv")
        combined_df.to_csv(combined_csv, index=False, encoding='utf-8-sig')
        print(f"\n✅ 合併文件已保存: {combined_csv}")
        print(f"總計職位數量: {len(combined_df)}")


def generate_test_report(results: List[Dict], output_dir: str) -> None:
    """
    生成測試報告
    
    Args:
        results: 所有網站的測試結果
        output_dir: 輸出目錄
    """
    report_file = os.path.join(output_dir, "ml_engineer_test_report.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ML Engineer 職位測試報告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"搜尋關鍵字: ML Engineer\n")
        f.write(f"每個網站目標職位數: 15\n")
        f.write(f"時間範圍: 近7天內\n\n")
        
        # 統計資訊
        successful_sites = [r for r in results if r['status'] == 'success']
        total_jobs = sum(r['job_count'] for r in successful_sites)
        total_time = sum(r['execution_time'] for r in results)
        
        f.write("測試統計:\n")
        f.write("-" * 30 + "\n")
        f.write(f"測試網站總數: {len(results)}\n")
        f.write(f"成功網站數: {len(successful_sites)}\n")
        f.write(f"成功率: {len(successful_sites)/len(results)*100:.1f}%\n")
        f.write(f"總職位數: {total_jobs}\n")
        f.write(f"總執行時間: {total_time:.2f} 秒\n")
        f.write(f"平均每個網站耗時: {total_time/len(results):.2f} 秒\n\n")
        
        # 各網站詳細結果
        f.write("各網站詳細結果:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            f.write(f"\n網站: {result['site']}\n")
            f.write(f"  狀態: {result['status']}\n")
            f.write(f"  職位數量: {result['job_count']}\n")
            f.write(f"  執行時間: {result['execution_time']:.2f} 秒\n")
            
            if result['job_count'] > 0:
                f.write(f"  平均每個職位耗時: {result['avg_time_per_job']:.2f} 秒\n")
            
            if result['error']:
                f.write(f"  錯誤信息: {result['error']}\n")
            
            if result['csv_file']:
                f.write(f"  CSV文件: {os.path.basename(result['csv_file'])}\n")
            if result['json_file']:
                f.write(f"  JSON文件: {os.path.basename(result['json_file'])}\n")
        
        # 生成的文件列表
        f.write("\n\n生成的文件:\n")
        f.write("-" * 30 + "\n")
        for result in results:
            if result['csv_file']:
                f.write(f"- {os.path.basename(result['csv_file'])}\n")
            if result['json_file']:
                f.write(f"- {os.path.basename(result['json_file'])}\n")
        f.write("- all_sites_ml_engineer_combined.csv\n")
        f.write("- ml_engineer_test_report.txt\n")
    
    print(f"\n📊 測試報告已生成: {report_file}")


def main():
    """
    主函數：執行ML Engineer職位測試
    """
    print("🚀 開始ML Engineer職位測試")
    print("搜尋條件: ML Engineer, 每個網站15個職位, 近7天內")
    
    # 創建輸出目錄
    output_dir = create_output_directory()
    print(f"📁 輸出目錄: {output_dir}")
    
    # 支援的網站列表
    supported_sites = [
        Site.LINKEDIN,
        Site.INDEED, 
        Site.ZIP_RECRUITER,
        Site.GLASSDOOR,
        Site.GOOGLE,
        Site.BAYT,
        Site.NAUKRI,
        Site.BDJOBS,
        Site.SEEK
    ]
    
    results = []
    
    # 測試每個網站
    for site in supported_sites:
        result = scrape_site_jobs(site, output_dir)
        results.append(result)
    
    # 合併結果
    combine_all_results(results, output_dir)
    
    # 生成報告
    generate_test_report(results, output_dir)
    
    print("\n🎉 ML Engineer職位測試完成！")
    print(f"📁 所有結果已保存到: {output_dir}")


if __name__ == "__main__":
    main()