#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Engineer 職位測試腳本 - 最終修正版
修正所有失敗網站的問題
"""

import os
import time
import random
from datetime import datetime
from jobspy import scrape_jobs
from jobspy.model import Site
import pandas as pd

def create_output_directory():
    """創建輸出目錄"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"ml_engineer_test_final_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def scrape_site_jobs_with_retry(site, site_name, output_dir, max_retries=3):
    """帶重試機制的職位爬取函數"""
    for attempt in range(max_retries):
        try:
            start_time = datetime.now()
            
            # 基本參數
            scrape_params = {
                'site_name': site,
                'search_term': "ML Engineer",
                'results_wanted': 15,
                'country_indeed': "Australia",
                'description_format': "markdown",
                'verbose': 1
            }
            
            # 針對不同網站的特殊配置
            if site == Site.GOOGLE:
                # Google 需要更具體的搜尋詞和地區
                scrape_params.update({
                    'search_term': "Machine Learning Engineer",
                    'location': "Sydney, Australia",
                    'google_search_term': "Machine Learning Engineer jobs Sydney"
                })
            elif site == Site.BAYT:
                # Bayt 服務中東地區
                scrape_params.update({
                    'location': "Dubai, UAE",
                    'search_term': "Machine Learning Engineer"
                })
            elif site == Site.BDJOBS:
                # BDJobs 服務孟加拉，不傳遞 user_agent 參數
                scrape_params.update({
                    'location': "Dhaka, Bangladesh",
                    'search_term': "ML Engineer"
                })
                # 重要：不為 BDJobs 設置 user_agent
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
            
            # 只為支援 user_agent 的網站添加該參數
            if site != Site.BDJOBS:
                scrape_params['user_agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            
            print(f"🔄 嘗試 {attempt + 1}/{max_retries}: {site_name}")
            
            # 添加隨機延遲以避免被阻擋
            if site in [Site.ZIP_RECRUITER, Site.BAYT]:
                delay = random.uniform(3, 6)
                print(f"   ⏳ 延遲 {delay:.1f} 秒...")
                time.sleep(delay)
            else:
                time.sleep(2)  # 基本延遲
            
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
                jobs_df.to_json(json_filename, orient='records', indent=2, force_ascii=False)
                
                print(f"✅ {site_name}: 找到 {len(jobs_df)} 個職位 (耗時: {execution_time:.2f}秒)")
                return {
                    'site': site_name,
                    'status': 'success',
                    'jobs_count': len(jobs_df),
                    'execution_time': execution_time,
                    'attempts': attempt + 1,
                    'csv_file': csv_filename,
                    'json_file': json_filename,
                    'jobs_df': jobs_df
                }
            else:
                print(f"⚠️ {site_name}: 未找到職位 (嘗試 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"   ⏳ 等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {site_name}: 錯誤 - {error_msg} (嘗試 {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"   ⏳ 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                return {
                    'site': site_name,
                    'status': 'error',
                    'jobs_count': 0,
                    'execution_time': execution_time,
                    'attempts': max_retries,
                    'error': error_msg
                }
    
    # 所有嘗試都失敗
    return {
        'site': site_name,
        'status': 'no_results',
        'jobs_count': 0,
        'execution_time': 0,
        'attempts': max_retries,
        'error': 'No jobs found after all attempts'
    }

def combine_all_results(results, output_dir):
    """合併所有網站的結果"""
    all_jobs = []
    
    for result in results:
        if result['status'] == 'success' and 'jobs_df' in result:
            jobs_df = result['jobs_df']
            all_jobs.append(jobs_df)
    
    if all_jobs:
        combined_df = pd.concat(all_jobs, ignore_index=True)
        combined_filename = os.path.join(output_dir, "all_sites_ml_engineer_combined.csv")
        combined_df.to_csv(combined_filename, index=False, encoding='utf-8-sig')
        print(f"\n📊 合併文件已保存: {combined_filename}")
        print(f"📊 總計職位數量: {len(combined_df)}")
        return combined_filename, len(combined_df)
    
    return None, 0

def generate_test_report(results, output_dir, total_jobs, total_time):
    """生成測試報告"""
    report_filename = os.path.join(output_dir, "ml_engineer_test_report_final.txt")
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("ML Engineer 職位測試報告 - 最終修正版\n")
        f.write("=" * 50 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"總執行時間: {total_time:.2f} 秒\n")
        f.write(f"測試網站數量: {len(results)}\n")
        
        successful_sites = [r for r in results if r['status'] == 'success']
        f.write(f"成功網站數量: {len(successful_sites)}\n")
        f.write(f"總職位數量: {total_jobs}\n\n")
        
        f.write("詳細結果:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            f.write(f"網站: {result['site']}\n")
            f.write(f"  狀態: {result['status']}\n")
            f.write(f"  職位數量: {result['jobs_count']}\n")
            f.write(f"  執行時間: {result['execution_time']:.2f} 秒\n")
            f.write(f"  嘗試次數: {result['attempts']}\n")
            
            if result['status'] == 'success':
                avg_time = result['execution_time'] / result['jobs_count'] if result['jobs_count'] > 0 else 0
                f.write(f"  平均每個職位耗時: {avg_time:.2f} 秒\n")
                f.write(f"  CSV文件: {os.path.basename(result['csv_file'])}\n")
                f.write(f"  JSON文件: {os.path.basename(result['json_file'])}\n")
            elif 'error' in result:
                f.write(f"  錯誤信息: {result['error']}\n")
            
            f.write("\n")
        
        f.write("最終修正措施說明:\n")
        f.write("-" * 30 + "\n")
        f.write("- ZipRecruiter: 添加3-6秒隨機延遲，使用美國地區\n")
        f.write("- Google: 調整搜尋詞為'Machine Learning Engineer'，指定悉尼地區\n")
        f.write("- Bayt: 添加重試機制，使用杜拜地區，增加延遲\n")
        f.write("- BDJobs: 完全移除user_agent參數，使用達卡地區\n")
        f.write("- 所有網站: 添加隨機延遲和重試機制\n\n")
        
        f.write("生成的文件:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            if result['status'] == 'success':
                f.write(f"- {os.path.basename(result['csv_file'])}\n")
                f.write(f"- {os.path.basename(result['json_file'])}\n")
        
        f.write("- all_sites_ml_engineer_combined.csv\n")
        f.write("- ml_engineer_test_report_final.txt\n")
    
    print(f"\n📋 測試報告已保存: {report_filename}")
    return report_filename

def main():
    """主函數"""
    print("🚀 開始 ML Engineer 職位測試 - 最終修正版")
    print("=" * 50)
    
    # 創建輸出目錄
    output_dir = create_output_directory()
    print(f"📁 輸出目錄: {output_dir}")
    
    # 支援的網站列表
    sites_to_test = [
        (Site.LINKEDIN, "linkedin"),
        (Site.INDEED, "indeed"),
        (Site.ZIP_RECRUITER, "ziprecruiter"),
        (Site.GLASSDOOR, "glassdoor"),
        (Site.GOOGLE, "google"),
        (Site.BAYT, "bayt"),
        (Site.NAUKRI, "naukri"),
        (Site.BDJOBS, "bdjobs"),
        (Site.SEEK, "seek")
    ]
    
    results = []
    start_time = datetime.now()
    
    # 測試每個網站
    for site, site_name in sites_to_test:
        print(f"\n🔍 測試網站: {site_name.upper()}")
        result = scrape_site_jobs_with_retry(site, site_name, output_dir)
        results.append(result)
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    # 合併結果
    print("\n" + "=" * 50)
    print("📊 合併所有結果...")
    combined_file, total_jobs = combine_all_results(results, output_dir)
    
    # 生成報告
    print("\n📋 生成測試報告...")
    report_file = generate_test_report(results, output_dir, total_jobs, total_time)
    
    # 總結
    print("\n" + "=" * 50)
    print("🎯 測試完成！")
    print(f"📁 所有文件已保存到: {output_dir}")
    print(f"⏱️ 總執行時間: {total_time:.2f} 秒")
    print(f"📊 總職位數量: {total_jobs}")
    
    successful_sites = [r for r in results if r['status'] == 'success']
    print(f"✅ 成功網站: {len(successful_sites)}/{len(sites_to_test)}")
    
    if successful_sites:
        print("\n成功的網站:")
        for result in successful_sites:
            print(f"  - {result['site']}: {result['jobs_count']} 個職位")
    
    failed_sites = [r for r in results if r['status'] != 'success']
    if failed_sites:
        print("\n仍然失敗的網站:")
        for result in failed_sites:
            print(f"  - {result['site']}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()