#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Engineer 職位測試腳本 (修正版)
修正了失敗網站的問題：
- ZipRecruiter: 添加延遲避免429錯誤
- Google: 調整搜尋參數和地區設定
- Bayt: 添加重試機制和錯誤處理
- BDJobs: 修正user_agent參數問題
"""

import os
import json
import csv
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from jobseeker import scrape_jobs
from jobseeker.model import Site


def create_output_directory() -> str:
    """
    創建輸出目錄
    
    Returns:
        str: 輸出目錄路徑
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"ml_engineer_test_fixed_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def add_random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """
    添加隨機延遲以避免被網站阻擋
    
    Args:
        min_seconds: 最小延遲秒數
        max_seconds: 最大延遲秒數
    """
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏳ 等待 {delay:.1f} 秒以避免被阻擋...")
    time.sleep(delay)


def scrape_site_jobs_with_retry(site: Site, output_dir: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    帶重試機制的職位爬取函數
    
    Args:
        site: 求職網站
        output_dir: 輸出目錄
        max_retries: 最大重試次數
        
    Returns:
        Dict: 包含網站名稱、職位數量、執行時間等資訊的字典
    """
    site_name = site.value
    print(f"\n開始測試 {site_name}...")
    
    # 針對不同網站添加延遲
    if site in [Site.ZIP_RECRUITER, Site.BAYT]:
        add_random_delay(3.0, 6.0)  # 較長延遲
    else:
        add_random_delay(1.0, 3.0)  # 標準延遲
    
    start_time = datetime.now()
    
    for attempt in range(max_retries):
        try:
            # 根據不同網站調整參數
            scrape_params = {
                'site_name': site,
                'search_term': "ML Engineer",
                'results_wanted': 15,
                'hours_old': 168,  # 7天 = 168小時
            }
            
            # 針對特定網站的參數調整
            if site == Site.GOOGLE:
                # Google 需要更具體的搜尋詞和地區
                scrape_params.update({
                    'search_term': "Machine Learning Engineer",
                    'location': "Sydney, Australia",
                    'country_indeed': "Australia"
                })
            elif site == Site.BAYT:
                # Bayt 主要服務中東地區
                scrape_params.update({
                    'location': "Dubai, UAE",
                    'search_term': "Machine Learning Engineer"
                })
            elif site == Site.BDJOBS:
                # BDJobs 服務孟加拉，移除可能導致錯誤的參數
                scrape_params.update({
                    'location': "Dhaka, Bangladesh",
                    'search_term': "ML Engineer"
                })
                # 不傳遞 user_agent 參數給 BDJobs
            elif site == Site.ZIP_RECRUITER:
                # ZipRecruiter 需要美國地區
                scrape_params.update({
                    'location': "United States",
                    'country_indeed': "USA"
                })
            else:
                # 其他網站使用澳洲作為預設地區
                scrape_params.update({
                    'location': "Australia",
                    'country_indeed': "Australia"
                })
            
            print(f"🔄 嘗試 {attempt + 1}/{max_retries}: {site_name}")
            
            # 爬取職位資料
            jobs_df = scrape_jobs(**scrape_params)
            
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
                    'error': None,
                    'attempts': attempt + 1
                }
            else:
                if attempt < max_retries - 1:
                    print(f"⚠️ {site_name}: 第 {attempt + 1} 次嘗試未找到職位，準備重試...")
                    add_random_delay(5.0, 10.0)  # 重試前較長延遲
                    continue
                else:
                    print(f"❌ {site_name}: 所有嘗試後仍未找到職位")
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                    return {
                        'site': site_name,
                        'status': 'no_results',
                        'job_count': 0,
                        'execution_time': execution_time,
                        'avg_time_per_job': 0,
                        'csv_file': None,
                        'json_file': None,
                        'error': 'No jobs found after all attempts',
                        'attempts': max_retries
                    }
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {site_name}: 第 {attempt + 1} 次嘗試錯誤 - {error_msg}")
            
            if attempt < max_retries - 1:
                print(f"🔄 準備重試 {site_name}...")
                add_random_delay(5.0, 10.0)  # 錯誤後較長延遲
                continue
            else:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                return {
                    'site': site_name,
                    'status': 'error',
                    'job_count': 0,
                    'execution_time': execution_time,
                    'avg_time_per_job': 0,
                    'csv_file': None,
                    'json_file': None,
                    'error': error_msg,
                    'attempts': max_retries
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
    report_file = os.path.join(output_dir, "ml_engineer_test_report_fixed.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ML Engineer 職位測試報告 (修正版)\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"搜尋關鍵字: ML Engineer\n")
        f.write(f"每個網站目標職位數: 15\n")
        f.write(f"時間範圍: 近7天內\n")
        f.write(f"修正內容: 添加延遲、重試機制、參數調整\n\n")
        
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
            f.write(f"  嘗試次數: {result.get('attempts', 1)}\n")
            
            if result['job_count'] > 0:
                f.write(f"  平均每個職位耗時: {result['avg_time_per_job']:.2f} 秒\n")
            
            if result['error']:
                f.write(f"  錯誤信息: {result['error']}\n")
            
            if result['csv_file']:
                f.write(f"  CSV文件: {os.path.basename(result['csv_file'])}\n")
            if result['json_file']:
                f.write(f"  JSON文件: {os.path.basename(result['json_file'])}\n")
        
        # 修正說明
        f.write("\n\n修正措施說明:\n")
        f.write("-" * 30 + "\n")
        f.write("- ZipRecruiter: 添加3-6秒隨機延遲，使用美國地區\n")
        f.write("- Google: 調整搜尋詞為'Machine Learning Engineer'，指定悉尼地區\n")
        f.write("- Bayt: 添加重試機制，使用杜拜地區，增加延遲\n")
        f.write("- BDJobs: 移除user_agent參數，使用達卡地區\n")
        f.write("- 所有網站: 添加隨機延遲和重試機制\n")
        
        # 生成的文件列表
        f.write("\n\n生成的文件:\n")
        f.write("-" * 30 + "\n")
        for result in results:
            if result['csv_file']:
                f.write(f"- {os.path.basename(result['csv_file'])}\n")
            if result['json_file']:
                f.write(f"- {os.path.basename(result['json_file'])}\n")
        f.write("- all_sites_ml_engineer_combined.csv\n")
        f.write("- ml_engineer_test_report_fixed.txt\n")
    
    print(f"\n📊 測試報告已生成: {report_file}")


def main():
    """
    主函數：執行ML Engineer職位測試 (修正版)
    """
    print("🚀 開始ML Engineer職位測試 (修正版)")
    print("搜尋條件: ML Engineer, 每個網站15個職位, 近7天內")
    print("修正內容: 添加延遲、重試機制、參數調整")
    
    # 創建輸出目錄
    output_dir = create_output_directory()
    print(f"📁 輸出目錄: {output_dir}")
    
    # 支援的網站列表 (重點測試之前失敗的網站)
    supported_sites = [
        Site.LINKEDIN,      # 參考基準
        Site.INDEED,        # 參考基準
        Site.ZIP_RECRUITER, # 修正: 添加延遲
        Site.GLASSDOOR,     # 參考基準
        Site.GOOGLE,        # 修正: 調整搜尋參數
        Site.BAYT,          # 修正: 重試機制
        Site.NAUKRI,        # 參考基準
        Site.BDJOBS,        # 修正: 移除user_agent
        Site.SEEK           # 參考基準
    ]
    
    results = []
    
    # 測試每個網站
    for i, site in enumerate(supported_sites):
        print(f"\n進度: {i+1}/{len(supported_sites)}")
        result = scrape_site_jobs_with_retry(site, output_dir)
        results.append(result)
        
        # 在網站之間添加延遲
        if i < len(supported_sites) - 1:
            add_random_delay(2.0, 4.0)
    
    # 合併結果
    combine_all_results(results, output_dir)
    
    # 生成報告
    generate_test_report(results, output_dir)
    
    # 顯示修正結果摘要
    successful_sites = [r for r in results if r['status'] == 'success']
    failed_sites = [r for r in results if r['status'] != 'success']
    
    print(f"\n🎉 ML Engineer職位測試完成 (修正版)！")
    print(f"📁 所有結果已保存到: {output_dir}")
    print(f"\n📊 修正結果摘要:")
    print(f"✅ 成功網站: {len(successful_sites)}/{len(supported_sites)}")
    if failed_sites:
        print(f"❌ 仍然失敗的網站:")
        for site in failed_sites:
            print(f"   - {site['site']}: {site['error']}")


if __name__ == "__main__":
    main()
