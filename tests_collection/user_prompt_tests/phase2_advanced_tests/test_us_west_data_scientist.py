#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美國西部 Data Scientist 職位搜尋測試
測試目標：搜尋舊金山和西雅圖的 Data Scientist 職位
測試類型：地點篩選 + 薪資分析
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加 jobseeker 模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jobseeker import scrape_jobs
from jobseeker.model import Site, Country

def convert_types(obj):
    """
    將 numpy/pandas 數據類型轉換為 Python 原生類型，以便 JSON 序列化
    """
    import numpy as np
    
    if pd.isna(obj):
        return None
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj

def test_us_west_data_scientist():
    """
    測試美國西部地區 Data Scientist 職位搜尋功能
    """
    print("=== 美國西部 Data Scientist 職位搜尋測試 ===")
    
    # 測試參數
    test_params = {
        'san_francisco': {
            'site_name': [Site.INDEED, Site.LINKEDIN, Site.ZIP_RECRUITER],
            'search_term': 'Data Scientist',
            'location': 'San Francisco, CA',
            'country': Country.USA,
            'results_wanted': 75,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        },
        'seattle': {
            'site_name': [Site.INDEED, Site.LINKEDIN, Site.ZIP_RECRUITER],
            'search_term': 'Data Scientist',
            'location': 'Seattle, WA',
            'country': Country.USA,
            'results_wanted': 75,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        }
    }
    
    all_jobs = []
    test_results = {}
    
    # 為每個城市執行搜尋
    for city, params in test_params.items():
        print(f"\n🔍 搜尋 {city.replace('_', ' ').title()} 的 Data Scientist 職位...")
        
        try:
            jobs = scrape_jobs(**params)
            
            if jobs is not None and not jobs.empty:
                print(f"✅ {city.replace('_', ' ').title()} 找到 {len(jobs)} 個職位")
                
                # 添加城市標記
                jobs['search_city'] = city.replace('_', ' ').title()
                all_jobs.append(jobs)
                
                # 收集測試結果
                test_results[city] = {
                    'job_count': len(jobs),
                    'sites': jobs['site'].value_counts().to_dict() if 'site' in jobs.columns else {},
                    'companies': jobs['company'].value_counts().head(5).to_dict() if 'company' in jobs.columns else {},
                    'avg_salary': jobs['salary_avg'].mean() if 'salary_avg' in jobs.columns else None
                }
                
                # 顯示基本統計
                print(f"   網站分布: {dict(jobs['site'].value_counts()) if 'site' in jobs.columns else 'N/A'}")
                if 'salary_avg' in jobs.columns and jobs['salary_avg'].notna().any():
                    avg_salary = jobs['salary_avg'].mean()
                    print(f"   平均薪資: ${avg_salary:,.0f}")
                    
            else:
                print(f"❌ {city.replace('_', ' ').title()} 未找到職位")
                test_results[city] = {'job_count': 0, 'error': 'No jobs found'}
                
        except Exception as e:
            print(f"❌ {city.replace('_', ' ').title()} 搜尋失敗: {str(e)}")
            test_results[city] = {'job_count': 0, 'error': str(e)}
    
    # 合併所有結果
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        total_jobs = len(combined_jobs)
        print(f"\n📊 總計找到 {total_jobs} 個 Data Scientist 職位")
        
        # 創建結果目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path(f"tests_collection/user_prompt_tests/phase2_advanced_tests/us_west_data_scientist_{timestamp}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詳細結果
        combined_jobs.to_csv(result_dir / "us_west_data_scientist_jobs.csv", index=False, encoding='utf-8')
        
        # 薪資分析
        salary_analysis = {}
        if 'salary_avg' in combined_jobs.columns:
            salary_data = combined_jobs['salary_avg'].dropna()
            if not salary_data.empty:
                salary_analysis = {
                    'overall_avg': convert_types(salary_data.mean()),
                    'median': convert_types(salary_data.median()),
                    'min': convert_types(salary_data.min()),
                    'max': convert_types(salary_data.max()),
                    'std': convert_types(salary_data.std())
                }
        
        # 生成分析報告
        analysis = {
            'test_info': {
                'test_name': 'US West Data Scientist Search',
                'test_date': datetime.now().isoformat(),
                'total_jobs': total_jobs,
                'cities_tested': list(test_params.keys())
            },
            'salary_analysis': salary_analysis,
            'city_results': {}
        }
        
        for city in test_params.keys():
            city_data = combined_jobs[combined_jobs['search_city'] == city.replace('_', ' ').title()]
            if not city_data.empty:
                city_salary_analysis = {}
                if 'salary_avg' in city_data.columns:
                    city_salary_data = city_data['salary_avg'].dropna()
                    if not city_salary_data.empty:
                        city_salary_analysis = {
                            'avg': convert_types(city_salary_data.mean()),
                            'median': convert_types(city_salary_data.median()),
                            'min': convert_types(city_salary_data.min()),
                            'max': convert_types(city_salary_data.max())
                        }
                
                analysis['city_results'][city] = {
                    'job_count': len(city_data),
                    'site_distribution': {k: convert_types(v) for k, v in city_data['site'].value_counts().to_dict().items()} if 'site' in city_data.columns else {},
                    'top_companies': {k: convert_types(v) for k, v in city_data['company'].value_counts().head(5).to_dict().items()} if 'company' in city_data.columns else {},
                    'salary_analysis': city_salary_analysis
                }
        
        # 保存分析結果
        with open(result_dir / "analysis_report.json", 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # 生成測試報告
        report_content = f"""# 美國西部 Data Scientist 職位搜尋測試報告

## 測試概要
- **測試日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **測試城市**: San Francisco, Seattle
- **搜尋職位**: Data Scientist
- **總職位數**: {total_jobs}

## 薪資分析
{f"- **整體平均薪資**: ${salary_analysis.get('overall_avg', 0):,.0f}" if salary_analysis.get('overall_avg') else "- 薪資資訊不足"}
{f"- **薪資中位數**: ${salary_analysis.get('median', 0):,.0f}" if salary_analysis.get('median') else ""}
{f"- **薪資範圍**: ${salary_analysis.get('min', 0):,.0f} - ${salary_analysis.get('max', 0):,.0f}" if salary_analysis.get('min') and salary_analysis.get('max') else ""}

## 城市分析

### San Francisco
- 職位數量: {test_results.get('san_francisco', {}).get('job_count', 0)}
- 網站分布: {test_results.get('san_francisco', {}).get('sites', {})}
{f"- 平均薪資: ${test_results.get('san_francisco', {}).get('avg_salary', 0):,.0f}" if test_results.get('san_francisco', {}).get('avg_salary') else ""}

### Seattle
- 職位數量: {test_results.get('seattle', {}).get('job_count', 0)}
- 網站分布: {test_results.get('seattle', {}).get('sites', {})}
{f"- 平均薪資: ${test_results.get('seattle', {}).get('avg_salary', 0):,.0f}" if test_results.get('seattle', {}).get('avg_salary') else ""}

## 測試結論
✅ 美國西部 Data Scientist 職位搜尋測試完成
📁 結果已保存至: {result_dir}
"""
        
        with open(result_dir / "test_report.md", 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📁 測試結果已保存至: {result_dir}")
        return True
        
    else:
        print("\n❌ 所有城市都未找到職位")
        return False

if __name__ == "__main__":
    success = test_us_west_data_scientist()
    if success:
        print("\n🎉 美國西部 Data Scientist 測試成功完成！")
    else:
        print("\n💥 美國西部 Data Scientist 測試失敗")
        sys.exit(1)