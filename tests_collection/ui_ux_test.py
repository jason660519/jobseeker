#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/UX 職位測試腳本
測試各個求職網站搜尋 UI/UX 相關職位的功能
目標：每個網站至少獲取 6 筆職位資料
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加 jobspy 模組路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from jobspy import scrape_jobs
except ImportError as e:
    print(f"導入 jobspy 失敗: {e}")
    sys.exit(1)

def create_output_directory():
    """
    創建輸出目錄
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"ui_ux_test_{timestamp}"
    Path(output_dir).mkdir(exist_ok=True)
    return output_dir

def test_site_ui_ux_jobs(site_name, search_terms, output_dir, min_jobs=6):
    """
    測試單個網站的 UI/UX 職位搜尋功能
    
    Args:
        site_name (str): 網站名稱
        search_terms (list): 搜尋關鍵字列表
        output_dir (str): 輸出目錄
        min_jobs (int): 最少職位數量
    
    Returns:
        dict: 測試結果
    """
    print(f"\n=== 測試 {site_name} - UI/UX 職位搜尋 ===")
    
    all_jobs = []
    
    for term in search_terms:
        try:
            print(f"搜尋關鍵字: {term}")
            
            # 執行職位搜尋
            jobs = scrape_jobs(
                site_name=site_name,
                search_term=term,
                location="Remote",  # 遠端工作
                results_wanted=10,  # 每個關鍵字搜尋10個職位
                hours_old=72,  # 72小時內的職位
                country_indeed="worldwide",  # 全球範圍
                is_remote=True  # 遠端工作
            )
            
            if jobs is not None and not jobs.empty:
                print(f"找到 {len(jobs)} 個職位")
                all_jobs.append(jobs)
            else:
                print("未找到職位")
                
        except Exception as e:
            print(f"搜尋 {term} 時發生錯誤: {str(e)}")
            continue
    
    # 合併所有職位資料
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        # 去除重複職位（基於標題和公司）
        combined_jobs = combined_jobs.drop_duplicates(subset=['title', 'company'], keep='first')
        
        # 保存資料
        csv_file = os.path.join(output_dir, f"{site_name}_ui_ux_jobs.csv")
        json_file = os.path.join(output_dir, f"{site_name}_ui_ux_raw_data.json")
        
        combined_jobs.to_csv(csv_file, index=False, encoding='utf-8-sig')
        combined_jobs.to_json(json_file, orient='records', indent=2)
        
        job_count = len(combined_jobs)
        success = job_count >= min_jobs
        
        print(f"總共獲取 {job_count} 個 UI/UX 職位")
        print(f"目標達成: {'是' if success else '否'} (目標: {min_jobs}+)")
        
        return {
            'site': site_name,
            'job_count': job_count,
            'success': success,
            'csv_file': csv_file,
            'json_file': json_file,
            'sample_jobs': combined_jobs.head(3).to_dict('records') if not combined_jobs.empty else []
        }
    else:
        print("未獲取到任何職位")
        return {
            'site': site_name,
            'job_count': 0,
            'success': False,
            'csv_file': None,
            'json_file': None,
            'sample_jobs': []
        }

def main():
    """
    主函數 - 執行 UI/UX 職位測試
    """
    print("開始 UI/UX 職位搜尋測試")
    print("目標：每個網站至少 6 筆 UI/UX 相關職位")
    print("地區：任何國家，遠端工作")
    
    # 創建輸出目錄
    output_dir = create_output_directory()
    print(f"輸出目錄: {output_dir}")
    
    # UI/UX 相關搜尋關鍵字
    ui_ux_terms = [
        "UI Designer",
        "UX Designer", 
        "UI/UX Designer",
        "User Experience Designer",
        "User Interface Designer",
        "Product Designer"
    ]
    
    # 測試的求職網站
    sites_to_test = [
        'indeed',
        'linkedin', 
        'glassdoor',
        'seek',
        'naukri'
    ]
    
    results = []
    all_jobs_combined = []
    
    # 測試每個網站
    for site in sites_to_test:
        try:
            result = test_site_ui_ux_jobs(site, ui_ux_terms, output_dir)
            results.append(result)
            
            # 如果有職位資料，讀取並加入合併列表
            if result['csv_file'] and os.path.exists(result['csv_file']):
                site_jobs = pd.read_csv(result['csv_file'])
                site_jobs['source_site'] = site
                all_jobs_combined.append(site_jobs)
                
        except Exception as e:
            print(f"測試 {site} 時發生錯誤: {str(e)}")
            results.append({
                'site': site,
                'job_count': 0,
                'success': False,
                'error': str(e)
            })
    
    # 生成合併報告
    if all_jobs_combined:
        combined_df = pd.concat(all_jobs_combined, ignore_index=True)
        combined_file = os.path.join(output_dir, "all_sites_ui_ux_combined.csv")
        combined_df.to_csv(combined_file, index=False, encoding='utf-8-sig')
        print(f"\n合併檔案已保存: {combined_file}")
    
    # 生成測試報告
    report_file = os.path.join(output_dir, "ui_ux_test_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("UI/UX 職位搜尋測試報告\n")
        f.write("=" * 50 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"測試目標: 每個網站至少 6 筆 UI/UX 職位\n")
        f.write(f"搜尋條件: 遠端工作，任何國家\n\n")
        
        total_jobs = 0
        successful_sites = 0
        
        for result in results:
            f.write(f"網站: {result['site']}\n")
            f.write(f"職位數量: {result['job_count']}\n")
            f.write(f"目標達成: {'是' if result['success'] else '否'}\n")
            if 'error' in result:
                f.write(f"錯誤: {result['error']}\n")
            f.write("-" * 30 + "\n")
            
            total_jobs += result['job_count']
            if result['success']:
                successful_sites += 1
        
        f.write(f"\n總結:\n")
        f.write(f"總職位數: {total_jobs}\n")
        f.write(f"成功網站數: {successful_sites}/{len(sites_to_test)}\n")
        f.write(f"整體成功率: {(successful_sites/len(sites_to_test)*100):.1f}%\n")
    
    # 顯示最終結果
    print("\n" + "=" * 60)
    print("UI/UX 職位搜尋測試完成")
    print(f"總職位數: {total_jobs}")
    print(f"成功網站數: {successful_sites}/{len(sites_to_test)}")
    print(f"整體成功率: {(successful_sites/len(sites_to_test)*100):.1f}%")
    print(f"詳細報告: {report_file}")
    
    # 顯示每個網站的結果摘要
    print("\n各網站結果摘要:")
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['site']}: {result['job_count']} 個職位")

if __name__ == "__main__":
    main()