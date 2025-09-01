#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy CSV格式驗證工具

這個腳本用於驗證JobSpy專案中的CSV檔案是否符合統一的格式標準，
並展示不同網站爬蟲輸出的格式標準化過程。

作者: JobSpy Team
日期: 2025
"""

import pandas as pd
import os
from typing import List, Dict, Any
from pathlib import Path

# JobSpy標準CSV欄位順序
DESIRED_ORDER = [
    "id",
    "site",
    "job_url",
    "job_url_direct",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "salary_source",
    "interval",
    "min_amount",
    "max_amount",
    "currency",
    "is_remote",
    "job_level",
    "job_function",
    "listing_type",
    "emails",
    "description",
    "company_industry",
    "company_url",
    "company_logo",
    "company_url_direct",
    "company_addresses",
    "company_num_employees",
    "company_revenue",
    "company_description",
    # naukri-specific fields
    "skills",
    "experience_range",
    "company_rating",
    "company_reviews_count",
    "vacancy_count",
    "work_from_home_type",
]

def validate_csv_format(csv_file_path: str) -> Dict[str, Any]:
    """
    驗證CSV檔案格式是否符合JobSpy標準
    
    Args:
        csv_file_path: CSV檔案路徑
        
    Returns:
        包含驗證結果的字典
    """
    try:
        # 讀取CSV檔案
        df = pd.read_csv(csv_file_path)
        
        # 基本資訊
        result = {
            'file_path': csv_file_path,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'missing_standard_columns': [],
            'extra_columns': [],
            'column_order_correct': False,
            'format_compliant': False,
            'sites_found': [],
            'sample_data': {}
        }
        
        # 檢查缺失的標準欄位
        for col in DESIRED_ORDER:
            if col not in df.columns:
                result['missing_standard_columns'].append(col)
        
        # 檢查額外的欄位
        for col in df.columns:
            if col not in DESIRED_ORDER:
                result['extra_columns'].append(col)
        
        # 檢查欄位順序
        existing_standard_cols = [col for col in DESIRED_ORDER if col in df.columns]
        actual_order = [col for col in df.columns if col in DESIRED_ORDER]
        result['column_order_correct'] = existing_standard_cols == actual_order
        
        # 檢查是否完全符合格式
        result['format_compliant'] = (
            len(result['missing_standard_columns']) == 0 and
            len(result['extra_columns']) == 0 and
            result['column_order_correct']
        )
        
        # 獲取網站資訊
        if 'site' in df.columns:
            result['sites_found'] = df['site'].unique().tolist()
        
        # 獲取樣本資料
        if len(df) > 0:
            sample_row = df.iloc[0].to_dict()
            # 只顯示前10個欄位的樣本資料
            result['sample_data'] = {k: v for i, (k, v) in enumerate(sample_row.items()) if i < 10}
        
        return result
        
    except Exception as e:
        return {
            'file_path': csv_file_path,
            'error': str(e),
            'format_compliant': False
        }

def standardize_csv_format(input_csv: str, output_csv: str = None) -> bool:
    """
    將CSV檔案標準化為JobSpy格式
    
    Args:
        input_csv: 輸入CSV檔案路徑
        output_csv: 輸出CSV檔案路徑（如果為None，則覆蓋原檔案）
        
    Returns:
        是否成功標準化
    """
    try:
        # 讀取原始檔案
        df = pd.read_csv(input_csv)
        
        # 確保所有標準欄位都存在
        for col in DESIRED_ORDER:
            if col not in df.columns:
                df[col] = None
        
        # 重新排序欄位
        df = df[DESIRED_ORDER]
        
        # 保存標準化後的檔案
        output_path = output_csv if output_csv else input_csv
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ 已標準化: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 標準化失敗 {input_csv}: {e}")
        return False

def generate_format_report(csv_files: List[str]) -> None:
    """
    生成CSV格式驗證報告
    
    Args:
        csv_files: CSV檔案路徑列表
    """
    print("\n" + "="*80)
    print("📋 JobSpy CSV格式驗證報告")
    print("="*80)
    
    compliant_files = []
    non_compliant_files = []
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            print(f"⚠️  檔案不存在: {csv_file}")
            continue
            
        result = validate_csv_format(csv_file)
        
        print(f"\n📄 檔案: {os.path.basename(csv_file)}")
        print(f"   路徑: {csv_file}")
        print(f"   資料筆數: {result.get('total_rows', 'N/A')}")
        print(f"   欄位數量: {result.get('total_columns', 'N/A')}")
        
        if 'error' in result:
            print(f"   ❌ 錯誤: {result['error']}")
            non_compliant_files.append(csv_file)
            continue
        
        if result['format_compliant']:
            print("   ✅ 格式完全符合標準")
            compliant_files.append(csv_file)
        else:
            print("   ⚠️  格式不完全符合標準")
            non_compliant_files.append(csv_file)
            
            if result['missing_standard_columns']:
                print(f"   缺失欄位: {', '.join(result['missing_standard_columns'])}")
            
            if result['extra_columns']:
                print(f"   額外欄位: {', '.join(result['extra_columns'])}")
            
            if not result['column_order_correct']:
                print("   欄位順序不正確")
        
        if result['sites_found']:
            print(f"   包含網站: {', '.join(result['sites_found'])}")
    
    # 總結報告
    print("\n" + "="*80)
    print("📊 驗證總結")
    print("="*80)
    print(f"✅ 符合標準的檔案: {len(compliant_files)}")
    print(f"⚠️  不符合標準的檔案: {len(non_compliant_files)}")
    print(f"📁 總檔案數: {len(csv_files)}")
    
    if non_compliant_files:
        print("\n🔧 建議標準化以下檔案:")
        for file in non_compliant_files:
            print(f"   - {os.path.basename(file)}")

def demonstrate_format_standardization():
    """
    展示格式標準化過程
    """
    print("\n" + "="*80)
    print("🔧 JobSpy CSV格式標準化展示")
    print("="*80)
    
    # 創建範例原始資料（模擬不同網站的格式）
    sample_data = {
        'indeed_raw.csv': {
            'SITE': ['indeed', 'indeed'],
            'TITLE': ['Software Engineer', 'Senior Software Engineer'],
            'COMPANY': ['AMERICAN SYSTEMS', 'TherapyNotes.com'],
            'CITY': ['Arlington', 'Philadelphia'],
            'STATE': ['VA', 'PA'],
            'JOB_TYPE': [None, 'fulltime'],
            'INTERVAL': ['yearly', 'yearly'],
            'MIN_AMOUNT': [150000, 110000],
            'MAX_AMOUNT': [200000, 135000],
            'JOB_URL': ['https://www.indeed.com/viewjob?jk=5e409e577046...', 
                       'https://www.indeed.com/viewjob?jk=da39574a40cb...'],
            'DESCRIPTION': ['THIS POSITION COMES WITH A 10K SIGNING BONUS!...', 
                           'About Us TherapyNotes is the national leader i...']
        },
        'linkedin_raw.csv': {
            'site': ['linkedin', 'linkedin'],
            'title': ['Software Engineer - Early Career', 'Full-Stack Software Engineer'],
            'company': ['Lockheed Martin', 'Rain'],
            'location': ['Sunnyvale, CA', 'New York, NY'],
            'job_type': ['fulltime', 'fulltime'],
            'interval': ['yearly', 'yearly'],
            'min_amount': [None, None],
            'max_amount': [None, None],
            'job_url': ['https://www.linkedin.com/jobs/view/3693012711',
                       'https://www.linkedin.com/jobs/view/3696158877'],
            'description': ['Description:By bringing together people that u...',
                           'Rain\'s mission is to create the fastest and ea...']
        }
    }
    
    # 創建範例檔案
    for filename, data in sample_data.items():
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"📝 已創建範例檔案: {filename}")
    
    print("\n🔍 原始格式分析:")
    for filename in sample_data.keys():
        result = validate_csv_format(filename)
        print(f"\n📄 {filename}:")
        print(f"   欄位: {result['columns']}")
        print(f"   符合標準: {'✅' if result['format_compliant'] else '❌'}")
        
        if not result['format_compliant']:
            print(f"   缺失欄位: {result['missing_standard_columns'][:5]}..." 
                  if len(result['missing_standard_columns']) > 5 
                  else result['missing_standard_columns'])
    
    print("\n🔧 執行標準化...")
    for filename in sample_data.keys():
        standardized_name = filename.replace('_raw.csv', '_standardized.csv')
        standardize_csv_format(filename, standardized_name)
    
    print("\n✅ 標準化後格式分析:")
    for filename in sample_data.keys():
        standardized_name = filename.replace('_raw.csv', '_standardized.csv')
        result = validate_csv_format(standardized_name)
        print(f"\n📄 {standardized_name}:")
        print(f"   符合標準: {'✅' if result['format_compliant'] else '❌'}")
        print(f"   總欄位數: {result['total_columns']}")
    
    # 清理範例檔案
    print("\n🧹 清理範例檔案...")
    for filename in sample_data.keys():
        for suffix in ['', '_standardized']:
            file_to_remove = filename.replace('.csv', f'{suffix}.csv')
            if os.path.exists(file_to_remove):
                os.remove(file_to_remove)
                print(f"   已刪除: {file_to_remove}")

def main():
    """
    主函數
    """
    print("🚀 JobSpy CSV格式驗證與標準化工具")
    
    # 尋找當前目錄下的CSV檔案
    current_dir = Path('.')
    csv_files = list(current_dir.glob('*.csv'))
    csv_file_paths = [str(f) for f in csv_files]
    
    if csv_file_paths:
        print(f"\n📁 找到 {len(csv_file_paths)} 個CSV檔案")
        generate_format_report(csv_file_paths)
    else:
        print("\n📁 當前目錄下沒有找到CSV檔案")
    
    # 展示格式標準化過程
    demonstrate_format_standardization()
    
    print("\n" + "="*80)
    print("📋 JobSpy標準CSV格式說明")
    print("="*80)
    print("JobSpy使用統一的CSV格式來確保不同網站爬蟲的輸出一致性:")
    print("\n🔹 核心欄位:")
    core_fields = DESIRED_ORDER[:15]
    for i, field in enumerate(core_fields, 1):
        print(f"   {i:2d}. {field}")
    
    print("\n🔹 擴展欄位:")
    extended_fields = DESIRED_ORDER[15:]
    for i, field in enumerate(extended_fields, 16):
        print(f"   {i:2d}. {field}")
    
    print("\n💡 重要特點:")
    print("   • 所有網站爬蟲輸出都會轉換為此統一格式")
    print("   • 缺失的欄位會填充為None/空值")
    print("   • 欄位順序固定，確保一致性")
    print("   • 支援多種薪資格式和貨幣")
    print("   • 包含網站特定欄位（如Naukri的技能評分）")

if __name__ == "__main__":
    main()