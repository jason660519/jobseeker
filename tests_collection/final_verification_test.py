#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終驗證測試 - 確認所有修正都有效
"""

import os
import time
from datetime import datetime
from jobseeker import scrape_jobs
from jobseeker.model import Site
import pandas as pd

def create_output_directory():
    """創建輸出目錄"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"final_verification_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def test_single_site(site, site_name, output_dir):
    """測試單個網站"""
    try:
        start_time = datetime.now()
        
        # 基本參數
        scrape_params = {
            'site_name': site,
            'search_term': "Software Engineer",
            'results_wanted': 5,
            'country_indeed': "Australia",
            'description_format': "markdown",
            'verbose': 1
        }
        
        # 針對不同網站的特殊配置
        if site == Site.GOOGLE:
            scrape_params.update({
                'search_term': "Software Engineer",
                'location': "Sydney, Australia",
                'google_search_term': "Software Engineer jobs Sydney"
            })
        elif site == Site.BAYT:
            scrape_params.update({
                'location': "Dubai, UAE",
                'search_term': "Software Engineer"
            })
        elif site == Site.BDJOBS:
            scrape_params.update({
                'location': "Dhaka, Bangladesh",
                'search_term': "Software Engineer"
            })
        elif site == Site.ZIP_RECRUITER:
            scrape_params.update({
                'location': "United States",
                'country_indeed': "USA"
            })
        else:
            scrape_params.update({
                'location': "Australia",
                'country_indeed': "Australia"
            })
        
        print(f"🔍 測試 {site_name}...")
        
        # 爬取職位資料
        jobs_df = scrape_jobs(**scrape_params)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if jobs_df is not None and not jobs_df.empty:
            print(f"✅ {site_name}: 找到 {len(jobs_df)} 個職位 (耗時: {execution_time:.2f}秒)")
            return {
                'site': site_name,
                'status': 'success',
                'jobs_count': len(jobs_df),
                'execution_time': execution_time,
                'error': None
            }
        else:
            print(f"⚠️ {site_name}: 未找到職位")
            return {
                'site': site_name,
                'status': 'no_results',
                'jobs_count': 0,
                'execution_time': execution_time,
                'error': 'No jobs found'
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ {site_name}: 錯誤 - {error_msg}")
        return {
            'site': site_name,
            'status': 'error',
            'jobs_count': 0,
            'execution_time': 0,
            'error': error_msg
        }

def main():
    """主函數"""
    print("🚀 最終驗證測試 - 確認所有修正")
    print("=" * 50)
    
    # 創建輸出目錄
    output_dir = create_output_directory()
    print(f"📁 輸出目錄: {output_dir}")
    
    # 重點測試之前失敗的網站
    sites_to_test = [
        (Site.BDJOBS, "bdjobs"),  # 主要測試 user_agent 修正
        (Site.ZIP_RECRUITER, "ziprecruiter"),  # 測試 429 錯誤
        (Site.GOOGLE, "google"),  # 測試搜尋參數
        (Site.BAYT, "bayt"),  # 測試 403 錯誤
    ]
    
    results = []
    start_time = datetime.now()
    
    # 測試每個網站
    for site, site_name in sites_to_test:
        result = test_single_site(site, site_name, output_dir)
        results.append(result)
        time.sleep(3)  # 避免請求過快
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    # 總結
    print("\n" + "=" * 50)
    print("🎯 驗證測試完成！")
    print(f"⏱️ 總執行時間: {total_time:.2f} 秒")
    
    # 分析結果
    fixed_sites = []
    still_failing = []
    
    for result in results:
        if result['status'] == 'success':
            fixed_sites.append(result['site'])
        elif result['status'] == 'error':
            if 'user_agent' in result['error']:
                still_failing.append(f"{result['site']}: user_agent 問題仍存在")
            else:
                still_failing.append(f"{result['site']}: {result['error']}")
        else:
            # no_results 不算錯誤，可能是正常情況
            print(f"ℹ️ {result['site']}: 未找到職位（可能是正常情況）")
    
    if fixed_sites:
        print(f"\n✅ 已修正的網站: {', '.join(fixed_sites)}")
    
    if still_failing:
        print(f"\n❌ 仍然失敗的網站:")
        for failure in still_failing:
            print(f"   - {failure}")
    else:
        print("\n🎉 所有網站都已修正或正常運行！")
    
    # 特別檢查 BDJobs
    bdjobs_result = next((r for r in results if r['site'] == 'bdjobs'), None)
    if bdjobs_result:
        if bdjobs_result['status'] == 'success':
            print("\n🎉 BDJobs user_agent 問題已完全修正！")
        elif 'user_agent' in bdjobs_result.get('error', ''):
            print("\n❌ BDJobs user_agent 問題仍然存在")
        else:
            print("\n✅ BDJobs user_agent 問題已修正（雖然可能有其他問題）")

if __name__ == "__main__":
    main()
