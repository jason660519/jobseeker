#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 原始資料 vs 統一格式對比展示

這個腳本展示各家網站的原始資料檔案和統一格式CSV檔案的差異，
回應使用者關於「各家網站agent的raw檔長怎樣，統一格式的csv檔長怎樣」的問題。

作者: JobSpy Team
日期: 2025
"""

import json
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any

def find_test_result_directories() -> List[str]:
    """
    尋找測試結果目錄
    
    Returns:
        測試結果目錄列表
    """
    test_results_path = Path('tests_collection/test_results')
    directories = []
    
    if test_results_path.exists():
        for category_dir in test_results_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                for test_dir in category_dir.iterdir():
                    if test_dir.is_dir():
                        directories.append(str(test_dir))
    
    return directories

def analyze_raw_data_file(raw_file_path: str) -> Dict[str, Any]:
    """
    分析原始資料檔案
    
    Args:
        raw_file_path: 原始資料檔案路徑
        
    Returns:
        分析結果字典
    """
    try:
        # 嘗試不同的編碼方式
        encodings = ['utf-8-sig', 'utf-8', 'latin-1']
        raw_data = None
        
        for encoding in encodings:
            try:
                with open(raw_file_path, 'r', encoding=encoding) as f:
                    raw_data = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        
        if raw_data is None:
            return {'error': '無法讀取檔案，編碼問題'}
        
        if not raw_data:
            return {'error': '檔案為空'}
        
        first_record = raw_data[0] if isinstance(raw_data, list) else raw_data
        
        return {
            'total_records': len(raw_data) if isinstance(raw_data, list) else 1,
            'fields': list(first_record.keys()) if isinstance(first_record, dict) else [],
            'sample_data': first_record if isinstance(first_record, dict) else {},
            'data_structure': type(raw_data).__name__
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_csv_file(csv_file_path: str) -> Dict[str, Any]:
    """
    分析CSV檔案
    
    Args:
        csv_file_path: CSV檔案路徑
        
    Returns:
        分析結果字典
    """
    try:
        df = pd.read_csv(csv_file_path)
        
        return {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'sample_data': df.iloc[0].to_dict() if len(df) > 0 else {},
            'data_types': df.dtypes.to_dict()
        }
    except Exception as e:
        return {'error': str(e)}

def compare_site_data(test_dir: str, site: str) -> Dict[str, Any]:
    """
    對比特定網站的原始資料和CSV資料
    
    Args:
        test_dir: 測試目錄路徑
        site: 網站名稱
        
    Returns:
        對比結果字典
    """
    raw_file = os.path.join(test_dir, f'{site}_ml_engineer_raw_data.json')
    csv_file = os.path.join(test_dir, f'{site}_ml_engineer_jobs.csv')
    
    result = {
        'site': site,
        'raw_file_exists': os.path.exists(raw_file),
        'csv_file_exists': os.path.exists(csv_file),
        'raw_analysis': {},
        'csv_analysis': {}
    }
    
    if result['raw_file_exists']:
        result['raw_analysis'] = analyze_raw_data_file(raw_file)
    
    if result['csv_file_exists']:
        result['csv_analysis'] = analyze_csv_file(csv_file)
    
    return result

def display_raw_data_structure(site: str, raw_analysis: Dict[str, Any]) -> None:
    """
    顯示原始資料結構
    
    Args:
        site: 網站名稱
        raw_analysis: 原始資料分析結果
    """
    print(f"\n🌐 {site.upper()} 原始資料結構:")
    print("-" * 40)
    
    if 'error' in raw_analysis:
        print(f"   ❌ 錯誤: {raw_analysis['error']}")
        return
    
    print(f"   📊 資料筆數: {raw_analysis.get('total_records', 'N/A')}")
    print(f"   📋 資料結構: {raw_analysis.get('data_structure', 'N/A')}")
    print(f"   🔑 欄位數量: {len(raw_analysis.get('fields', []))}")
    
    fields = raw_analysis.get('fields', [])
    if fields:
        print(f"   📝 主要欄位: {', '.join(fields[:10])}")
        if len(fields) > 10:
            print(f"              ... 還有 {len(fields) - 10} 個欄位")
    
    # 顯示樣本資料的關鍵欄位
    sample = raw_analysis.get('sample_data', {})
    if sample:
        print(f"   📄 樣本資料:")
        key_fields = ['id', 'title', 'company', 'location', 'salary', 'date_posted']
        for field in key_fields:
            if field in sample:
                value = str(sample[field])[:50] + '...' if len(str(sample[field])) > 50 else sample[field]
                print(f"      {field}: {value}")

def display_csv_structure(site: str, csv_analysis: Dict[str, Any]) -> None:
    """
    顯示CSV資料結構
    
    Args:
        site: 網站名稱
        csv_analysis: CSV分析結果
    """
    print(f"\n📊 {site.upper()} 統一CSV格式:")
    print("-" * 40)
    
    if 'error' in csv_analysis:
        print(f"   ❌ 錯誤: {csv_analysis['error']}")
        return
    
    print(f"   📊 資料筆數: {csv_analysis.get('total_records', 'N/A')}")
    print(f"   📋 欄位數量: {csv_analysis.get('total_columns', 'N/A')}")
    
    columns = csv_analysis.get('columns', [])
    if columns:
        # 顯示標準欄位
        standard_fields = ['id', 'site', 'job_url', 'title', 'company', 'location', 
                          'date_posted', 'job_type', 'salary_source', 'interval', 
                          'min_amount', 'max_amount', 'currency', 'is_remote']
        
        print(f"   🔑 標準欄位: {', '.join(standard_fields[:7])}")
        print(f"              {', '.join(standard_fields[7:])}")
        
        # 顯示樣本資料
        sample = csv_analysis.get('sample_data', {})
        if sample:
            print(f"   📄 樣本資料:")
            for field in standard_fields[:6]:
                if field in sample:
                    value = str(sample[field])[:50] + '...' if len(str(sample[field])) > 50 else sample[field]
                    print(f"      {field}: {value}")

def demonstrate_format_differences():
    """
    展示格式差異
    """
    print("\n" + "="*80)
    print("🔍 JobSpy 原始資料 vs 統一格式對比展示")
    print("="*80)
    print("展示各家網站的原始資料檔案和統一格式CSV檔案的差異")
    
    # 尋找測試結果目錄
    test_dirs = find_test_result_directories()
    
    if not test_dirs:
        print("\n⚠️  未找到測試結果目錄")
        return
    
    # 選擇最新的ML工程師測試結果
    ml_test_dirs = [d for d in test_dirs if 'ml_engineer' in d]
    
    if not ml_test_dirs:
        print("\n⚠️  未找到ML工程師測試結果")
        return
    
    # 使用最新的測試目錄
    latest_test_dir = sorted(ml_test_dirs)[-1]
    print(f"\n📁 使用測試目錄: {os.path.basename(latest_test_dir)}")
    
    # 分析各網站資料
    sites = ['indeed', 'linkedin', 'glassdoor', 'naukri', 'seek']
    
    for site in sites:
        comparison = compare_site_data(latest_test_dir, site)
        
        if not comparison['raw_file_exists'] and not comparison['csv_file_exists']:
            continue
        
        print(f"\n" + "="*60)
        print(f"🌐 {site.upper()} 網站資料對比")
        print("="*60)
        
        if comparison['raw_file_exists']:
            display_raw_data_structure(site, comparison['raw_analysis'])
        else:
            print(f"\n⚠️  {site.upper()} 原始資料檔案不存在")
        
        if comparison['csv_file_exists']:
            display_csv_structure(site, comparison['csv_analysis'])
        else:
            print(f"\n⚠️  {site.upper()} CSV檔案不存在")
        
        # 對比分析
        if comparison['raw_file_exists'] and comparison['csv_file_exists']:
            raw_count = comparison['raw_analysis'].get('total_records', 0)
            csv_count = comparison['csv_analysis'].get('total_records', 0)
            
            print(f"\n🔄 轉換對比:")
            print(f"   原始資料 → 統一CSV: {raw_count} → {csv_count} 筆")
            
            if raw_count != csv_count:
                print(f"   ⚠️  資料筆數不一致，可能有資料過濾或處理")
            else:
                print(f"   ✅ 資料筆數一致")

def show_file_locations():
    """
    顯示檔案位置資訊
    """
    print("\n" + "="*80)
    print("📁 JobSpy 檔案結構說明")
    print("="*80)
    
    print("\n🗂️  原始資料檔案位置:")
    print("   tests_collection/test_results/[測試類型]/[測試時間]/")
    print("   ├── indeed_[job_type]_raw_data.json     # Indeed原始JSON資料")
    print("   ├── linkedin_[job_type]_raw_data.json   # LinkedIn原始JSON資料")
    print("   ├── glassdoor_[job_type]_raw_data.json  # Glassdoor原始JSON資料")
    print("   ├── naukri_[job_type]_raw_data.json     # Naukri原始JSON資料")
    print("   └── seek_[job_type]_raw_data.json       # Seek原始JSON資料")
    
    print("\n📊 統一格式CSV檔案位置:")
    print("   tests_collection/test_results/[測試類型]/[測試時間]/")
    print("   ├── indeed_[job_type]_jobs.csv          # Indeed統一格式CSV")
    print("   ├── linkedin_[job_type]_jobs.csv        # LinkedIn統一格式CSV")
    print("   ├── glassdoor_[job_type]_jobs.csv       # Glassdoor統一格式CSV")
    print("   ├── naukri_[job_type]_jobs.csv          # Naukri統一格式CSV")
    print("   ├── seek_[job_type]_jobs.csv            # Seek統一格式CSV")
    print("   └── all_sites_[job_type]_combined.csv   # 所有網站合併CSV")
    
    print("\n🔍 範例測試目錄:")
    test_dirs = find_test_result_directories()
    for i, test_dir in enumerate(test_dirs[:5], 1):
        print(f"   {i}. {test_dir}")
    
    if len(test_dirs) > 5:
        print(f"   ... 還有 {len(test_dirs) - 5} 個測試目錄")

def main():
    """
    主函數
    """
    print("🚀 JobSpy 原始資料 vs 統一格式對比工具")
    print("回應使用者問題：'各家網站agent的raw檔長怎樣，統一格式的csv檔長怎樣'")
    
    # 顯示檔案位置
    show_file_locations()
    
    # 展示格式差異
    demonstrate_format_differences()
    
    print("\n" + "="*80)
    print("📋 總結")
    print("="*80)
    print("\n🔹 原始資料檔案特點:")
    print("   • 各網站格式完全不同")
    print("   • JSON格式，包含網站特有欄位")
    print("   • 欄位名稱、資料結構各異")
    print("   • 包含原始爬取的所有資訊")
    
    print("\n🔹 統一格式CSV特點:")
    print("   • 所有網站使用相同的34欄位格式")
    print("   • 固定的欄位順序和命名")
    print("   • 標準化的資料類型")
    print("   • 便於分析和處理")
    
    print("\n🔄 轉換過程:")
    print("   原始JSON → JobPost模型 → 統一CSV格式")
    print("   確保不同網站的資料能夠無縫合併和分析")

if __name__ == "__main__":
    main()