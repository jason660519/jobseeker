#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡和香港Machine Learning Engineer職位搜尋測試

測試用戶提示: "尋找新加坡和香港的Machine Learning Engineer職位，薪資範圍80k-150k USD"

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


def test_singapore_ml_engineer():
    """
    執行新加坡和香港Machine Learning Engineer職位搜尋測試
    
    測試參數:
    - 職位: Machine Learning Engineer
    - 地點: Singapore, Hong Kong
    - 網站: Indeed, LinkedIn, Glassdoor
    - 薪資範圍: 80k-150k USD
    
    Returns:
        dict: 測試結果
    """
    print("🚀 開始執行新加坡和香港Machine Learning Engineer職位搜尋測試")
    print("📝 用戶提示: 尋找新加坡和香港的Machine Learning Engineer職位，薪資範圍80k-150k USD")
    
    # 測試配置
    test_config = {
        'job_title': 'Machine Learning Engineer',
        'locations': [
            {'name': 'Singapore', 'country': 'Singapore'},
            {'name': 'Hong Kong', 'country': 'Hong Kong'}
        ],
        'sites': [Site.INDEED, Site.LINKEDIN, Site.GLASSDOOR],
        'results_wanted': 75,
        'salary_range': {'min': 80000, 'max': 150000, 'currency': 'USD'}
    }
    
    # 創建結果目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / f"singapore_ml_engineer_{timestamp}"
    results_dir.mkdir(exist_ok=True)
    
    all_jobs = []
    test_results = {
        'test_name': 'singapore_ml_engineer',
        'user_prompt': '尋找新加坡和香港的Machine Learning Engineer職位，薪資範圍80k-150k USD',
        'start_time': datetime.now(),
        'locations_tested': [],
        'total_jobs': 0,
        'jobs_by_location': {},
        'jobs_by_site': {},
        'salary_analysis': {},
        'status': 'running'
    }
    
    try:
        # 為每個地點執行搜尋
        for location_info in test_config['locations']:
            location = location_info['name']
            country = location_info['country']
            print(f"\n🔍 搜尋地點: {location}")
            print(f"🌏 國家設定: {country}")
            print(f"💰 目標薪資: {test_config['salary_range']['min']:,}-{test_config['salary_range']['max']:,} {test_config['salary_range']['currency']}")
            
            try:
                # 執行JobSpy搜尋
                jobs_df = scrape_jobs(
                    site_name=test_config['sites'],
                    search_term=test_config['job_title'],
                    location=location,
                    results_wanted=test_config['results_wanted'],
                    country_indeed=country
                )
                
                if jobs_df is not None and not jobs_df.empty:
                    all_jobs.append(jobs_df)
                    job_count = len(jobs_df)
                    test_results['jobs_by_location'][location] = job_count
                    test_results['locations_tested'].append(location)
                    print(f"✅ {location}: 找到 {job_count} 個職位")
                    
                    # 分析薪資資訊
                    salary_info = analyze_salary_data(jobs_df, test_config['salary_range'])
                    if salary_info['jobs_with_salary'] > 0:
                        print(f"💰 有薪資資訊: {salary_info['jobs_with_salary']} 個職位")
                        print(f"💰 符合薪資範圍: {salary_info['jobs_in_range']} 個職位")
                    
                    # 儲存單一地點結果
                    location_file = results_dir / f"{location.replace(' ', '_').lower()}_jobs.csv"
                    jobs_df.to_csv(location_file, index=False, encoding='utf-8-sig')
                    
                else:
                    print(f"⚠️  {location}: 沒有找到職位")
                    test_results['jobs_by_location'][location] = 0
                    
            except Exception as e:
                print(f"❌ {location} 搜尋失敗: {str(e)}")
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
            
            # 詳細薪資分析
            salary_analysis = analyze_salary_data(combined_df, test_config['salary_range'])
            test_results['salary_analysis'] = salary_analysis
            
            print(f"\n💰 薪資分析:")
            print(f"   有薪資資訊: {salary_analysis['jobs_with_salary']} 個職位")
            print(f"   符合範圍: {salary_analysis['jobs_in_range']} 個職位")
            if salary_analysis['avg_min_salary'] > 0:
                print(f"   平均最低薪資: {salary_analysis['avg_min_salary']:,.0f}")
                print(f"   平均最高薪資: {salary_analysis['avg_max_salary']:,.0f}")
            
            # 儲存合併結果
            combined_file = results_dir / "singapore_ml_engineer_combined.csv"
            combined_df.to_csv(combined_file, index=False, encoding='utf-8-sig')
            
            # 儲存原始JSON資料
            json_file = results_dir / "singapore_ml_engineer_raw_data.json"
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
                'remote_jobs': len(combined_df[combined_df['is_remote'] == True]) if 'is_remote' in combined_df.columns else 0,
                'senior_positions': count_senior_positions(combined_df)
            }
            test_results['statistics'] = stats
            
            print(f"\n📈 統計資訊:")
            print(f"   💼 總職位數: {final_count}")
            print(f"   🏢 公司數: {stats['unique_companies']}")
            print(f"   📍 地點數: {stats['unique_locations']}")
            print(f"   🏠 遠程工作: {stats['remote_jobs']}")
            print(f"   👔 高級職位: {stats['senior_positions']}")
            
            # 分析技能要求
            skill_analysis = analyze_ml_skills(combined_df)
            if skill_analysis:
                test_results['skill_analysis'] = skill_analysis
                print(f"\n🔧 技能分析:")
                for skill, count in skill_analysis.items():
                    print(f"   {skill}: {count} 個職位")
            
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


def analyze_salary_data(df: pd.DataFrame, target_range: dict) -> dict:
    """
    分析薪資資料
    
    Args:
        df: 職位資料DataFrame
        target_range: 目標薪資範圍
        
    Returns:
        dict: 薪資分析結果
    """
    analysis = {
        'jobs_with_salary': 0,
        'jobs_in_range': 0,
        'avg_min_salary': 0,
        'avg_max_salary': 0,
        'salary_currencies': {}
    }
    
    if 'min_amount' in df.columns and 'max_amount' in df.columns:
        # 有薪資資訊的職位
        salary_jobs = df.dropna(subset=['min_amount'])
        analysis['jobs_with_salary'] = len(salary_jobs)
        
        if len(salary_jobs) > 0:
            # 計算平均薪資
            analysis['avg_min_salary'] = salary_jobs['min_amount'].mean()
            analysis['avg_max_salary'] = salary_jobs['max_amount'].mean()
            
            # 統計貨幣類型
            if 'currency' in salary_jobs.columns:
                currency_counts = salary_jobs['currency'].value_counts()
                analysis['salary_currencies'] = currency_counts.to_dict()
            
            # 檢查符合薪資範圍的職位
            target_min = target_range['min']
            target_max = target_range['max']
            
            # 假設薪資在目標範圍內的條件：最低薪資 >= target_min 或 最高薪資 <= target_max
            in_range = salary_jobs[
                (salary_jobs['min_amount'] >= target_min) | 
                (salary_jobs['max_amount'] <= target_max)
            ]
            analysis['jobs_in_range'] = len(in_range)
    
    return analysis


def count_senior_positions(df: pd.DataFrame) -> int:
    """
    統計高級職位數量
    
    Args:
        df: 職位資料DataFrame
        
    Returns:
        int: 高級職位數量
    """
    if 'title' not in df.columns:
        return 0
    
    senior_keywords = ['Senior', 'Lead', 'Principal', 'Staff', 'Director', 'Manager', 'Head']
    senior_count = 0
    
    for keyword in senior_keywords:
        senior_count += df['title'].str.contains(keyword, case=False, na=False).sum()
    
    return senior_count


def analyze_ml_skills(df: pd.DataFrame) -> dict:
    """
    分析機器學習相關技能要求
    
    Args:
        df: 職位資料DataFrame
        
    Returns:
        dict: 技能分析結果
    """
    if 'description' not in df.columns:
        return {}
    
    ml_skills = {
        'Python': 0,
        'TensorFlow': 0,
        'PyTorch': 0,
        'Scikit-learn': 0,
        'Keras': 0,
        'AWS': 0,
        'Azure': 0,
        'GCP': 0,
        'Docker': 0,
        'Kubernetes': 0,
        'SQL': 0,
        'Spark': 0,
        'Hadoop': 0
    }
    
    # 合併所有描述文字
    all_descriptions = df['description'].dropna().str.lower()
    
    for skill in ml_skills.keys():
        skill_count = all_descriptions.str.contains(skill.lower(), na=False).sum()
        ml_skills[skill] = skill_count
    
    # 只返回有出現的技能
    return {skill: count for skill, count in ml_skills.items() if count > 0}


def generate_test_report(test_results: dict, results_dir: Path):
    """
    生成測試報告
    
    Args:
        test_results: 測試結果字典
        results_dir: 結果目錄路徑
    """
    report_content = f"""# 新加坡和香港Machine Learning Engineer職位搜尋測試報告

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
    
    # 薪資分析
    if test_results.get('salary_analysis'):
        salary = test_results['salary_analysis']
        report_content += f"\n### 💰 薪資分析\n"
        report_content += f"- **有薪資資訊的職位**: {salary['jobs_with_salary']}\n"
        report_content += f"- **符合薪資範圍的職位**: {salary['jobs_in_range']}\n"
        if salary['avg_min_salary'] > 0:
            report_content += f"- **平均最低薪資**: {salary['avg_min_salary']:,.0f}\n"
            report_content += f"- **平均最高薪資**: {salary['avg_max_salary']:,.0f}\n"
        
        if salary.get('salary_currencies'):
            report_content += "\n#### 薪資貨幣分布\n"
            for currency, count in salary['salary_currencies'].items():
                report_content += f"- **{currency}**: {count} 個職位\n"
    
    if test_results.get('statistics'):
        stats = test_results['statistics']
        report_content += f"\n### 📊 詳細統計\n"
        report_content += f"- **公司數量**: {stats['unique_companies']}\n"
        report_content += f"- **地點數量**: {stats['unique_locations']}\n"
        report_content += f"- **遠程工作**: {stats['remote_jobs']}\n"
        report_content += f"- **高級職位**: {stats['senior_positions']}\n"
    
    if test_results.get('skill_analysis'):
        report_content += "\n### 🔧 技能要求分析\n"
        for skill, count in test_results['skill_analysis'].items():
            report_content += f"- **{skill}**: {count} 個職位\n"
    
    # 測試結論
    report_content += "\n## 🎯 測試結論\n\n"
    if test_results['status'] == 'success':
        if test_results['total_jobs'] >= 10:
            report_content += "✅ **測試通過**: 成功找到足夠數量的Machine Learning Engineer職位\n"
        else:
            report_content += "⚠️ **部分成功**: 找到職位但數量較少\n"
        
        salary_analysis = test_results.get('salary_analysis', {})
        if salary_analysis.get('jobs_with_salary', 0) > 0:
            report_content += "✅ **薪資資訊**: 部分職位包含薪資資訊\n"
            if salary_analysis.get('jobs_in_range', 0) > 0:
                report_content += "✅ **薪資範圍**: 找到符合目標薪資範圍的職位\n"
            else:
                report_content += "⚠️ **薪資範圍**: 沒有職位完全符合目標薪資範圍\n"
        else:
            report_content += "⚠️ **薪資資訊**: 大部分職位缺少薪資資訊\n"
            
    elif test_results['status'] == 'no_results':
        report_content += "❌ **測試失敗**: 沒有找到任何職位\n"
    else:
        report_content += f"❌ **測試錯誤**: {test_results.get('error', '未知錯誤')}\n"
    
    report_content += "\n### 建議\n"
    report_content += "- 新加坡和香港是亞洲ML工程師職位的重要市場\n"
    report_content += "- 薪資資訊可能因為隱私政策而較少公開\n"
    report_content += "- 可以考慮擴大搜尋到其他相關職位如Data Scientist\n"
    
    report_content += f"\n---\n\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    
    # 儲存報告
    report_file = results_dir / "test_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 測試報告已生成: {report_file}")


if __name__ == "__main__":
    # 執行測試
    results = test_singapore_ml_engineer()
    
    # 生成報告
    if 'csv_file' in results:
        results_dir = Path(results['csv_file']).parent
        generate_test_report(results, results_dir)
    
    # 顯示最終狀態
    if results['status'] == 'success':
        print(f"\n🎉 測試成功完成! 找到 {results['total_jobs']} 個Machine Learning Engineer職位")
        salary_info = results.get('salary_analysis', {})
        if salary_info.get('jobs_with_salary', 0) > 0:
            print(f"💰 其中 {salary_info['jobs_with_salary']} 個職位有薪資資訊")
    else:
        print(f"\n⚠️ 測試狀態: {results['status']}")