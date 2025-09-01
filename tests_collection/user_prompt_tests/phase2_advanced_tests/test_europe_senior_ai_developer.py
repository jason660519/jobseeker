#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歐洲 Senior AI Developer 職位搜尋測試
測試目標：搜尋倫敦和柏林的 Senior AI Developer 職位
測試類型：地點篩選 + 職位等級篩選
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

def test_europe_senior_ai_developer():
    """
    測試歐洲地區 Senior AI Developer 職位搜尋功能
    """
    print("=== 歐洲 Senior AI Developer 職位搜尋測試 ===")
    
    # 測試參數
    test_params = {
        'london': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'Senior AI Developer',
            'location': 'London, UK',
            'country': Country.UK,
            'results_wanted': 50,
            'hours_old': 72,
            'job_type': 'fulltime'
        },
        'berlin': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'Senior AI Developer',
            'location': 'Berlin, Germany',
            'country': Country.GERMANY,
            'results_wanted': 50,
            'hours_old': 72,
            'job_type': 'fulltime'
        }
    }
    
    all_jobs = []
    test_results = {}
    
    # 為每個城市執行搜尋
    for city, params in test_params.items():
        print(f"\n🔍 搜尋 {city.title()} 的 Senior AI Developer 職位...")
        
        try:
            jobs = scrape_jobs(**params)
            
            if jobs is not None and not jobs.empty:
                print(f"✅ {city.title()} 找到 {len(jobs)} 個職位")
                
                # 添加城市標記
                jobs['search_city'] = city.title()
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
                    print(f"   平均薪資: {avg_salary:,.0f}")
                    
            else:
                print(f"❌ {city.title()} 未找到職位")
                test_results[city] = {'job_count': 0, 'error': 'No jobs found'}
                
        except Exception as e:
            print(f"❌ {city.title()} 搜尋失敗: {str(e)}")
            test_results[city] = {'job_count': 0, 'error': str(e)}
    
    # 合併所有結果
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        total_jobs = len(combined_jobs)
        print(f"\n📊 總計找到 {total_jobs} 個 Senior AI Developer 職位")
        
        # 創建結果目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path(f"tests_collection/user_prompt_tests/phase2_advanced_tests/europe_senior_ai_developer_{timestamp}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詳細結果
        combined_jobs.to_csv(result_dir / "europe_senior_ai_developer_jobs.csv", index=False, encoding='utf-8')
        
        # 生成分析報告
        analysis = {
            'test_info': {
                'test_name': 'Europe Senior AI Developer Search',
                'test_date': datetime.now().isoformat(),
                'total_jobs': total_jobs,
                'cities_tested': list(test_params.keys())
            },
            'city_results': {}
        }
        
        for city in test_params.keys():
            city_data = combined_jobs[combined_jobs['search_city'] == city.title()]
            if not city_data.empty:
                analysis['city_results'][city] = {
                    'job_count': len(city_data),
                    'site_distribution': {k: convert_types(v) for k, v in city_data['site'].value_counts().to_dict().items()} if 'site' in city_data.columns else {},
                    'top_companies': {k: convert_types(v) for k, v in city_data['company'].value_counts().head(5).to_dict().items()} if 'company' in city_data.columns else {},
                    'salary_info': {
                        'avg_salary': convert_types(city_data['salary_avg'].mean()) if 'salary_avg' in city_data.columns else None,
                        'min_salary': convert_types(city_data['salary_min'].min()) if 'salary_min' in city_data.columns else None,
                        'max_salary': convert_types(city_data['salary_max'].max()) if 'salary_max' in city_data.columns else None
                    }
                }
        
        # 保存分析結果
        with open(result_dir / "analysis_report.json", 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # 生成測試報告
        report_content = f"""# 歐洲 Senior AI Developer 職位搜尋測試報告

## 測試概要
- **測試日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **測試城市**: London, Berlin
- **搜尋職位**: Senior AI Developer
- **總職位數**: {total_jobs}

## 城市分析

### London
- 職位數量: {test_results.get('london', {}).get('job_count', 0)}
- 網站分布: {test_results.get('london', {}).get('sites', {})}

### Berlin  
- 職位數量: {test_results.get('berlin', {}).get('job_count', 0)}
- 網站分布: {test_results.get('berlin', {}).get('sites', {})}

## 測試結論
✅ 歐洲 Senior AI Developer 職位搜尋測試完成
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
    success = test_europe_senior_ai_developer()
    if success:
        print("\n🎉 歐洲 Senior AI Developer 測試成功完成！")
    else:
        print("\n💥 歐洲 Senior AI Developer 測試失敗")
        sys.exit(1)