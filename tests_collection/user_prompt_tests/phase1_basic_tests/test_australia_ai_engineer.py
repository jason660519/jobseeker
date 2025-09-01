#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳洲AI工程師職位搜尋測試

測試用戶提示: "搜尋澳洲Sydney和Melbourne的AI Engineer工作"

Author: JobSpy Team
Date: 2025-01-09
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加jobseeker模組到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jobseeker import scrape_jobs
from jobseeker.model import Site


def test_australia_ai_engineer():
    """
    執行澳洲AI工程師職位搜尋測試
    
    測試參數:
    - 職位: AI Engineer
    - 地點: Sydney, Melbourne
    - 網站: Indeed, LinkedIn
    - 國家: Australia
    
    Returns:
        dict: 測試結果
    """
    print("🚀 開始執行澳洲AI工程師職位搜尋測試")
    print("📝 用戶提示: 搜尋澳洲Sydney和Melbourne的AI Engineer工作")
    
    # 測試配置
    test_config = {
        'job_title': 'AI Engineer',
        'locations': ['Sydney, Australia', 'Melbourne, Australia'],
        'sites': [Site.INDEED, Site.LINKEDIN],
        'results_wanted': 50,
        'country': 'Australia'
    }
    
    # 創建結果目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / f"australia_ai_engineer_{timestamp}"
    results_dir.mkdir(exist_ok=True)
    
    all_jobs = []
    test_results = {
        'test_name': 'australia_ai_engineer',
        'user_prompt': '搜尋澳洲Sydney和Melbourne的AI Engineer工作',
        'start_time': datetime.now(),
        'locations_tested': [],
        'total_jobs': 0,
        'jobs_by_location': {},
        'jobs_by_site': {},
        'status': 'running'
    }
    
    try:
        # 為每個地點執行搜尋
        for location in test_config['locations']:
            print(f"\n🔍 搜尋地點: {location}")
            
            # 執行JobSpy搜尋
            jobs_df = scrape_jobs(
                site_name=test_config['sites'],
                search_term=test_config['job_title'],
                location=location,
                results_wanted=test_config['results_wanted'],
                country_indeed=test_config['country']
            )
            
            if jobs_df is not None and not jobs_df.empty:
                all_jobs.append(jobs_df)
                job_count = len(jobs_df)
                test_results['jobs_by_location'][location] = job_count
                test_results['locations_tested'].append(location)
                print(f"✅ {location}: 找到 {job_count} 個職位")
                
                # 儲存單一地點結果
                location_file = results_dir / f"{location.replace(', ', '_').replace(' ', '_').lower()}_jobs.csv"
                jobs_df.to_csv(location_file, index=False, encoding='utf-8-sig')
                
            else:
                print(f"⚠️  {location}: 沒有找到職位")
                test_results['jobs_by_location'][location] = 0
        
        # 合併所有結果
        if all_jobs:
            combined_df = pd.concat(all_jobs, ignore_index=True)
            
            # 移除重複職位 (基於job_url)
            original_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
            final_count = len(combined_df)
            
            print(f"\n📊 合併結果: {original_count} → {final_count} (移除 {original_count - final_count} 個重複職位)")
            
            # 統計網站分布
            if 'site' in combined_df.columns:
                site_counts = combined_df['site'].value_counts()
                test_results['jobs_by_site'] = site_counts.to_dict()
                print("\n🌐 網站分布:")
                for site, count in site_counts.items():
                    print(f"   {site}: {count} 個職位")
            
            # 儲存合併結果
            combined_file = results_dir / "australia_ai_engineer_combined.csv"
            combined_df.to_csv(combined_file, index=False, encoding='utf-8-sig')
            
            # 儲存原始JSON資料
            json_file = results_dir / "australia_ai_engineer_raw_data.json"
            combined_df.to_json(json_file, orient='records', indent=2, force_ascii=False)
            
            # 更新測試結果
            test_results['total_jobs'] = final_count
            test_results['status'] = 'success'
            test_results['csv_file'] = str(combined_file)
            test_results['json_file'] = str(json_file)
            
            # 生成基本統計
            stats = {
                'unique_companies': combined_df['company'].nunique() if 'company' in combined_df.columns else 0,
                'unique_locations': combined_df['location'].nunique() if 'location' in combined_df.columns else 0,
                'has_salary_info': len(combined_df.dropna(subset=['min_amount'])) if 'min_amount' in combined_df.columns else 0
            }
            test_results['statistics'] = stats
            
            print(f"\n📈 統計資訊:")
            print(f"   💼 總職位數: {final_count}")
            print(f"   🏢 公司數: {stats['unique_companies']}")
            print(f"   📍 地點數: {stats['unique_locations']}")
            print(f"   💰 有薪資資訊: {stats['has_salary_info']}")
            
        else:
            test_results['status'] = 'no_results'
            test_results['total_jobs'] = 0
            print("❌ 所有地點都沒有找到職位")
    
    except Exception as e:
        test_results['status'] = 'error'
        test_results['error'] = str(e)
        print(f"❌ 測試執行出錯: {str(e)}")
    
    finally:
        test_results['end_time'] = datetime.now()
        test_results['execution_time'] = (test_results['end_time'] - test_results['start_time']).total_seconds()
        
        # 儲存測試結果
        import json
        results_file = results_dir / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            # 轉換datetime為字串以便JSON序列化
            results_copy = test_results.copy()
            results_copy['start_time'] = test_results['start_time'].isoformat()
            results_copy['end_time'] = test_results['end_time'].isoformat()
            
            # 轉換numpy/pandas數據類型為Python原生類型
            def convert_types(obj):
                if hasattr(obj, 'item'):
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(v) for v in obj]
                return obj
            
            results_copy = convert_types(results_copy)
            json.dump(results_copy, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 測試結果已儲存至: {results_dir}")
        print(f"⏱️  執行時間: {test_results['execution_time']:.2f} 秒")
    
    return test_results


def generate_test_report(test_results: dict, results_dir: Path):
    """
    生成測試報告
    
    Args:
        test_results: 測試結果字典
        results_dir: 結果目錄路徑
    """
    report_content = f"""# 澳洲AI工程師職位搜尋測試報告

## 📋 測試概要

- **測試名稱**: {test_results['test_name']}
- **用戶提示**: "{test_results['user_prompt']}"
- **執行時間**: {test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
- **測試狀態**: {test_results['status']}
- **執行時長**: {test_results['execution_time']:.2f} 秒

## 🎯 測試結果

### 總體統計
- **總職位數**: {test_results['total_jobs']}
- **測試地點數**: {len(test_results['locations_tested'])}

### 地點分布
"""
    
    for location, count in test_results.get('jobs_by_location', {}).items():
        report_content += f"- **{location}**: {count} 個職位\n"
    
    if test_results.get('jobs_by_site'):
        report_content += "\n### 網站分布\n"
        for site, count in test_results['jobs_by_site'].items():
            report_content += f"- **{site}**: {count} 個職位\n"
    
    if test_results.get('statistics'):
        stats = test_results['statistics']
        report_content += f"\n### 詳細統計\n"
        report_content += f"- **公司數量**: {stats['unique_companies']}\n"
        report_content += f"- **地點數量**: {stats['unique_locations']}\n"
        report_content += f"- **有薪資資訊**: {stats['has_salary_info']}\n"
    
    # 測試結論
    report_content += "\n## 🎯 測試結論\n\n"
    if test_results['status'] == 'success':
        if test_results['total_jobs'] >= 10:
            report_content += "✅ **測試通過**: 成功找到足夠數量的AI工程師職位\n"
        else:
            report_content += "⚠️ **部分成功**: 找到職位但數量較少\n"
    elif test_results['status'] == 'no_results':
        report_content += "❌ **測試失敗**: 沒有找到任何職位\n"
    else:
        report_content += f"❌ **測試錯誤**: {test_results.get('error', '未知錯誤')}\n"
    
    report_content += f"\n---\n\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    
    # 儲存報告
    report_file = results_dir / "test_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 測試報告已生成: {report_file}")


if __name__ == "__main__":
    # 執行測試
    results = test_australia_ai_engineer()
    
    # 生成報告
    if 'csv_file' in results:
        results_dir = Path(results['csv_file']).parent
        generate_test_report(results, results_dir)
    
    # 顯示最終狀態
    if results['status'] == 'success':
        print(f"\n🎉 測試成功完成! 找到 {results['total_jobs']} 個AI工程師職位")
    else:
        print(f"\n⚠️ 測試狀態: {results['status']}")