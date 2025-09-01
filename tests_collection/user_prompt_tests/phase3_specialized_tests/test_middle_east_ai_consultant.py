#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中東地區 AI Consultant 職位搜尋測試
測試目標：搜尋杜拜和阿布達比的 AI Consultant 職位
測試類型：專業諮詢職位 + 中東市場測試
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
    if pd.isna(obj):
        return None
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    else:
        return obj

def test_middle_east_ai_consultant():
    """
    測試中東地區 AI Consultant 職位搜尋功能
    """
    print("=== 中東地區 AI Consultant 職位搜尋測試 ===")
    
    # 測試參數
    test_params = {
        'dubai': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'AI Consultant',
            'location': 'Dubai, UAE',
            'country': Country.UNITEDARABEMIRATES,
            'results_wanted': 50,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        },
        'abu_dhabi': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'AI Consultant',
            'location': 'Abu Dhabi, UAE',
            'country': Country.UNITEDARABEMIRATES,
            'results_wanted': 50,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        }
    }
    
    all_jobs = []
    test_results = {}
    
    # 為每個城市執行搜尋
    for city, params in test_params.items():
        print(f"\n🔍 搜尋 {city.replace('_', ' ').title()} 的 AI Consultant 職位...")
        
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
                    print(f"   平均薪資: {avg_salary:,.0f} AED")
                    
                # 分析職位描述中的關鍵技能
                if 'description' in jobs.columns:
                    descriptions = ' '.join(jobs['description'].fillna('').astype(str))
                    ai_keywords = ['machine learning', 'deep learning', 'neural network', 'tensorflow', 'pytorch', 'python', 'data science', 'nlp', 'computer vision']
                    keyword_counts = {keyword: descriptions.lower().count(keyword) for keyword in ai_keywords}
                    top_skills = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f"   熱門技能: {dict(top_skills)}")
                    
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
        print(f"\n📊 總計找到 {total_jobs} 個 AI Consultant 職位")
        
        # 創建結果目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path(f"tests_collection/user_prompt_tests/phase3_specialized_tests/middle_east_ai_consultant_{timestamp}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詳細結果
        combined_jobs.to_csv(result_dir / "middle_east_ai_consultant_jobs.csv", index=False, encoding='utf-8')
        
        # 技能分析
        skill_analysis = {}
        if 'description' in combined_jobs.columns:
            all_descriptions = ' '.join(combined_jobs['description'].fillna('').astype(str))
            ai_keywords = {
                'machine_learning': ['machine learning', 'ml'],
                'deep_learning': ['deep learning', 'neural network'],
                'python': ['python'],
                'tensorflow': ['tensorflow'],
                'pytorch': ['pytorch'],
                'data_science': ['data science', 'data analytics'],
                'nlp': ['nlp', 'natural language processing'],
                'computer_vision': ['computer vision', 'cv'],
                'cloud': ['aws', 'azure', 'gcp', 'cloud'],
                'consulting': ['consulting', 'advisory', 'strategy']
            }
            
            for skill, keywords in ai_keywords.items():
                count = sum(all_descriptions.lower().count(keyword) for keyword in keywords)
                skill_analysis[skill] = count
        
        # 生成分析報告
        analysis = {
            'test_info': {
                'test_name': 'Middle East AI Consultant Search',
                'test_date': datetime.now().isoformat(),
                'total_jobs': total_jobs,
                'cities_tested': list(test_params.keys())
            },
            'skill_analysis': skill_analysis,
            'city_results': {}
        }
        
        for city in test_params.keys():
            city_data = combined_jobs[combined_jobs['search_city'] == city.replace('_', ' ').title()]
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
        top_skills = sorted(skill_analysis.items(), key=lambda x: x[1], reverse=True)[:5] if skill_analysis else []
        
        report_content = f"""# 中東地區 AI Consultant 職位搜尋測試報告

## 測試概要
- **測試日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **測試城市**: Dubai, Abu Dhabi
- **搜尋職位**: AI Consultant
- **總職位數**: {total_jobs}

## 技能需求分析
{chr(10).join([f"- **{skill.replace('_', ' ').title()}**: {count} 次提及" for skill, count in top_skills]) if top_skills else "- 技能分析資料不足"}

## 城市分析

### Dubai
- 職位數量: {test_results.get('dubai', {}).get('job_count', 0)}
- 網站分布: {test_results.get('dubai', {}).get('sites', {})}
{f"- 平均薪資: {test_results.get('dubai', {}).get('avg_salary', 0):,.0f} AED" if test_results.get('dubai', {}).get('avg_salary') else ""}

### Abu Dhabi
- 職位數量: {test_results.get('abu_dhabi', {}).get('job_count', 0)}
- 網站分布: {test_results.get('abu_dhabi', {}).get('sites', {})}
{f"- 平均薪資: {test_results.get('abu_dhabi', {}).get('avg_salary', 0):,.0f} AED" if test_results.get('abu_dhabi', {}).get('avg_salary') else ""}

## 市場洞察
- 中東地區對AI諮詢服務需求逐漸增長
- 政府數位化轉型推動AI人才需求
- 跨國企業在UAE設立AI中心

## 測試結論
✅ 中東地區 AI Consultant 職位搜尋測試完成
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
    success = test_middle_east_ai_consultant()
    if success:
        print("\n🎉 中東地區 AI Consultant 測試成功完成！")
    else:
        print("\n💥 中東地區 AI Consultant 測試失敗")
        sys.exit(1)