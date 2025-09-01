#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版爬蟲測試腳本
專門測試 ZipRecruiter、Google Jobs 和 Bayt 的修復效果
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobseeker import scrape_jobs
from jobseeker.model import Site


def setup_enhanced_environment():
    """
    設置增強版爬蟲環境變數
    """
    os.environ['ENABLE_ALL_ENHANCED'] = 'true'
    os.environ['ENABLE_ENHANCED_ZIPRECRUITER'] = 'true'
    os.environ['ENABLE_ENHANCED_GOOGLE'] = 'true'
    os.environ['ENABLE_ENHANCED_BAYT'] = 'true'
    print("✅ 已啟用所有增強版爬蟲")


def add_random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """
    添加隨機延遲
    """
    import random
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏳ 延遲 {delay:.1f} 秒...")
    time.sleep(delay)


def test_enhanced_scraper(site: Site, site_name: str, output_dir: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    測試單個增強版爬蟲
    
    Args:
        site: 求職網站枚舉
        site_name: 網站名稱
        output_dir: 輸出目錄
        max_retries: 最大重試次數
        
    Returns:
        Dict: 測試結果
    """
    print(f"\n🚀 開始測試增強版 {site_name}...")
    
    # 針對不同網站添加延遲
    if site in [Site.ZIP_RECRUITER, Site.BAYT]:
        add_random_delay(3.0, 6.0)  # 較長延遲
    else:
        add_random_delay(1.0, 3.0)  # 標準延遲
    
    start_time = datetime.now()
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 嘗試 {attempt + 1}/{max_retries}: {site_name}")
            
            # 根據不同網站調整參數
            scrape_params = {
                'site_name': site,
                'search_term': "ML Engineer",
                'results_wanted': 10,  # 減少數量以加快測試
                'hours_old': 168,  # 7天
                'verbose': 1
            }
            
            # 針對特定網站的參數調整
            if site == Site.GOOGLE:
                scrape_params.update({
                    'search_term': "Machine Learning Engineer",
                    'location': "Sydney, Australia",
                    'country_indeed': "Australia"
                })
            elif site == Site.BAYT:
                scrape_params.update({
                    'location': "Dubai, UAE",
                    'search_term': "Machine Learning Engineer"
                })
            elif site == Site.ZIP_RECRUITER:
                scrape_params.update({
                    'location': "United States",
                    'country_indeed': "USA"
                })
            
            # 爬取職位資料
            jobs_df = scrape_jobs(**scrape_params)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if jobs_df is not None and not jobs_df.empty:
                # 保存為 CSV
                csv_filename = os.path.join(output_dir, f"enhanced_{site_name}_ml_engineer_jobs.csv")
                jobs_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                
                # 保存為 JSON
                json_filename = os.path.join(output_dir, f"enhanced_{site_name}_ml_engineer_raw_data.json")
                jobs_df.to_json(json_filename, orient='records', indent=2, force_ascii=False)
                
                print(f"✅ {site_name} 成功找到 {len(jobs_df)} 個職位")
                print(f"📁 CSV 檔案: {csv_filename}")
                print(f"📁 JSON 檔案: {json_filename}")
                
                return {
                    'site': site_name,
                    'status': 'success',
                    'job_count': len(jobs_df),
                    'execution_time': execution_time,
                    'attempts': attempt + 1,
                    'avg_time_per_job': execution_time / len(jobs_df),
                    'csv_file': csv_filename,
                    'json_file': json_filename,
                    'sample_jobs': jobs_df.head(3).to_dict('records') if len(jobs_df) > 0 else []
                }
            else:
                print(f"⚠️ {site_name} 第 {attempt + 1} 次嘗試未找到職位")
                if attempt < max_retries - 1:
                    add_random_delay(5.0, 10.0)  # 重試前等待更長時間
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {site_name} 第 {attempt + 1} 次嘗試失敗: {error_msg}")
            
            if attempt < max_retries - 1:
                add_random_delay(5.0, 10.0)  # 重試前等待更長時間
            else:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                return {
                    'site': site_name,
                    'status': 'error',
                    'job_count': 0,
                    'execution_time': execution_time,
                    'attempts': max_retries,
                    'error_message': error_msg
                }
    
    # 所有嘗試都失敗
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    return {
        'site': site_name,
        'status': 'no_results',
        'job_count': 0,
        'execution_time': execution_time,
        'attempts': max_retries,
        'error_message': 'No jobs found after all attempts'
    }


def generate_enhanced_test_report(results: List[Dict[str, Any]], output_dir: str):
    """
    生成增強版測試報告
    """
    report_filename = os.path.join(output_dir, "enhanced_scrapers_test_report.txt")
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("增強版爬蟲測試報告\n")
        f.write("=" * 50 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"測試網站: ZipRecruiter, Google Jobs, Bayt\n")
        f.write("\n")
        
        # 統計摘要
        successful_sites = [r for r in results if r['status'] == 'success']
        failed_sites = [r for r in results if r['status'] in ['error', 'no_results']]
        total_jobs = sum(r['job_count'] for r in successful_sites)
        
        f.write("測試摘要:\n")
        f.write("-" * 30 + "\n")
        f.write(f"成功網站數: {len(successful_sites)}/3\n")
        f.write(f"失敗網站數: {len(failed_sites)}/3\n")
        f.write(f"總職位數: {total_jobs}\n")
        f.write(f"平均成功率: {len(successful_sites)/3*100:.1f}%\n")
        f.write("\n")
        
        # 詳細結果
        f.write("詳細測試結果:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            f.write(f"\n網站: {result['site']}\n")
            f.write(f"  狀態: {result['status']}\n")
            f.write(f"  職位數量: {result['job_count']}\n")
            f.write(f"  執行時間: {result['execution_time']:.2f} 秒\n")
            f.write(f"  嘗試次數: {result['attempts']}\n")
            
            if result['status'] == 'success':
                f.write(f"  平均每個職位耗時: {result['avg_time_per_job']:.2f} 秒\n")
                f.write(f"  CSV文件: {os.path.basename(result['csv_file'])}\n")
                f.write(f"  JSON文件: {os.path.basename(result['json_file'])}\n")
                
                # 顯示樣本職位
                if result['sample_jobs']:
                    f.write("  樣本職位:\n")
                    for i, job in enumerate(result['sample_jobs'][:2], 1):
                        f.write(f"    {i}. {job.get('title', 'N/A')} - {job.get('company_name', 'N/A')}\n")
            else:
                f.write(f"  錯誤信息: {result.get('error_message', 'Unknown error')}\n")
        
        # 修復效果分析
        f.write("\n\n修復效果分析:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            site_name = result['site']
            if result['status'] == 'success':
                f.write(f"✅ {site_name}: 修復成功，找到 {result['job_count']} 個職位\n")
            elif result['status'] == 'no_results':
                f.write(f"⚠️ {site_name}: 修復部分成功，無錯誤但未找到職位\n")
            else:
                f.write(f"❌ {site_name}: 修復失敗，錯誤: {result.get('error_message', 'Unknown')}\n")
        
        # 生成的文件列表
        f.write("\n\n生成的文件:\n")
        f.write("-" * 30 + "\n")
        for result in results:
            if result['status'] == 'success':
                f.write(f"- {os.path.basename(result['csv_file'])}\n")
                f.write(f"- {os.path.basename(result['json_file'])}\n")
    
    print(f"\n📊 測試報告已生成: {report_filename}")
    return report_filename


def main():
    """
    主測試函數
    """
    print("🔧 增強版爬蟲測試開始")
    print("=" * 50)
    
    # 設置增強版環境
    setup_enhanced_environment()
    
    # 創建輸出目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"enhanced_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 輸出目錄: {output_dir}")
    
    # 要測試的網站
    test_sites = [
        (Site.ZIP_RECRUITER, "ziprecruiter"),
        (Site.GOOGLE, "google"),
        (Site.BAYT, "bayt")
    ]
    
    results = []
    
    # 逐一測試每個網站
    for site, site_name in test_sites:
        try:
            result = test_enhanced_scraper(site, site_name, output_dir)
            results.append(result)
        except Exception as e:
            print(f"❌ 測試 {site_name} 時發生未預期錯誤: {str(e)}")
            results.append({
                'site': site_name,
                'status': 'error',
                'job_count': 0,
                'execution_time': 0,
                'attempts': 0,
                'error_message': f'Unexpected error: {str(e)}'
            })
        
        # 網站間延遲
        if site != test_sites[-1][0]:  # 不是最後一個網站
            add_random_delay(3.0, 8.0)
    
    # 生成測試報告
    report_file = generate_enhanced_test_report(results, output_dir)
    
    # 顯示測試摘要
    print("\n" + "=" * 50)
    print("🎯 增強版爬蟲測試完成")
    print("=" * 50)
    
    successful_sites = [r for r in results if r['status'] == 'success']
    total_jobs = sum(r['job_count'] for r in successful_sites)
    
    print(f"✅ 成功網站: {len(successful_sites)}/3")
    print(f"📊 總職位數: {total_jobs}")
    print(f"📁 輸出目錄: {output_dir}")
    print(f"📋 測試報告: {os.path.basename(report_file)}")
    
    # 顯示各網站結果
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_emoji} {result['site']}: {result['job_count']} 個職位")
    
    return results


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
