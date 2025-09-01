#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印度 Deep Learning Engineer 職位搜尋測試
測試目標：搜尋班加羅爾和海德拉巴的 Deep Learning Engineer 職位
測試類型：專業技術職位 + 印度科技中心測試
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

def test_india_deep_learning_engineer():
    """
    測試印度地區 Deep Learning Engineer 職位搜尋功能
    """
    print("=== 印度 Deep Learning Engineer 職位搜尋測試 ===")
    
    # 測試參數
    test_params = {
        'bangalore': {
            'site_name': [Site.INDEED, Site.LINKEDIN, Site.NAUKRI],
            'search_term': 'Deep Learning Engineer',
            'location': 'Bangalore, India',
            'country': Country.INDIA,
            'results_wanted': 75,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        },
        'hyderabad': {
            'site_name': [Site.INDEED, Site.LINKEDIN, Site.NAUKRI],
            'search_term': 'Deep Learning Engineer',
            'location': 'Hyderabad, India',
            'country': Country.INDIA,
            'results_wanted': 75,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        }
    }
    
    all_jobs = []
    test_results = {}
    
    # 為每個城市執行搜尋
    for city, params in test_params.items():
        print(f"\n🔍 搜尋 {city.title()} 的 Deep Learning Engineer 職位...")
        
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
                    print(f"   平均薪資: ₹{avg_salary:,.0f}")
                    
                # 分析公司類型
                if 'company' in jobs.columns:
                    companies = jobs['company'].value_counts().head(10)
                    print(f"   主要雇主: {list(companies.index[:3])}")
                    
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
        print(f"\n📊 總計找到 {total_jobs} 個 Deep Learning Engineer 職位")
        
        # 創建結果目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path(f"tests_collection/user_prompt_tests/phase3_specialized_tests/india_deep_learning_engineer_{timestamp}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詳細結果
        combined_jobs.to_csv(result_dir / "india_deep_learning_engineer_jobs.csv", index=False, encoding='utf-8')
        
        # 深度學習技能分析
        skill_analysis = {}
        if 'description' in combined_jobs.columns:
            all_descriptions = ' '.join(combined_jobs['description'].fillna('').astype(str))
            dl_keywords = {
                'tensorflow': ['tensorflow', 'tf'],
                'pytorch': ['pytorch', 'torch'],
                'keras': ['keras'],
                'python': ['python'],
                'cnn': ['cnn', 'convolutional neural network'],
                'rnn': ['rnn', 'recurrent neural network', 'lstm', 'gru'],
                'transformer': ['transformer', 'bert', 'gpt'],
                'computer_vision': ['computer vision', 'cv', 'image processing'],
                'nlp': ['nlp', 'natural language processing'],
                'gpu': ['gpu', 'cuda', 'nvidia'],
                'docker': ['docker', 'kubernetes'],
                'cloud': ['aws', 'azure', 'gcp', 'cloud']
            }
            
            for skill, keywords in dl_keywords.items():
                count = sum(all_descriptions.lower().count(keyword) for keyword in keywords)
                skill_analysis[skill] = count
        
        # 公司類型分析
        company_analysis = {}
        if 'company' in combined_jobs.columns:
            companies = combined_jobs['company'].value_counts()
            # 分類公司類型（基於常見的印度科技公司）
            tech_giants = ['Google', 'Microsoft', 'Amazon', 'Facebook', 'Apple', 'IBM']
            indian_it = ['TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra', 'Cognizant']
            startups = ['Flipkart', 'Ola', 'Paytm', 'Zomato', 'Swiggy', 'BYJU\'S']
            
            company_analysis = {
                'tech_giants': sum(companies.get(company, 0) for company in tech_giants),
                'indian_it_services': sum(companies.get(company, 0) for company in indian_it),
                'startups': sum(companies.get(company, 0) for company in startups),
                'others': len(combined_jobs) - sum(companies.get(company, 0) for company in tech_giants + indian_it + startups)
            }
        
        # 生成分析報告
        analysis = {
            'test_info': {
                'test_name': 'India Deep Learning Engineer Search',
                'test_date': datetime.now().isoformat(),
                'total_jobs': convert_types(total_jobs),
                'cities_tested': list(test_params.keys())
            },
            'skill_analysis': {k: convert_types(v) for k, v in skill_analysis.items()},
            'company_analysis': {k: convert_types(v) for k, v in company_analysis.items()},
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
        top_skills = sorted(skill_analysis.items(), key=lambda x: x[1], reverse=True)[:5] if skill_analysis else []
        
        report_content = f"""# 印度 Deep Learning Engineer 職位搜尋測試報告

## 測試概要
- **測試日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **測試城市**: Bangalore, Hyderabad
- **搜尋職位**: Deep Learning Engineer
- **總職位數**: {total_jobs}

## 深度學習技能需求分析
{chr(10).join([f"- **{skill.replace('_', ' ').title()}**: {count} 次提及" for skill, count in top_skills]) if top_skills else "- 技能分析資料不足"}

## 公司類型分布
{f"- **跨國科技巨頭**: {company_analysis.get('tech_giants', 0)} 個職位" if company_analysis else ""}
{f"- **印度IT服務公司**: {company_analysis.get('indian_it_services', 0)} 個職位" if company_analysis else ""}
{f"- **新創公司**: {company_analysis.get('startups', 0)} 個職位" if company_analysis else ""}
{f"- **其他公司**: {company_analysis.get('others', 0)} 個職位" if company_analysis else ""}

## 城市分析

### Bangalore
- 職位數量: {test_results.get('bangalore', {}).get('job_count', 0)}
- 網站分布: {test_results.get('bangalore', {}).get('sites', {})}
{f"- 平均薪資: ₹{test_results.get('bangalore', {}).get('avg_salary', 0):,.0f}" if test_results.get('bangalore', {}).get('avg_salary') else ""}

### Hyderabad
- 職位數量: {test_results.get('hyderabad', {}).get('job_count', 0)}
- 網站分布: {test_results.get('hyderabad', {}).get('sites', {})}
{f"- 平均薪資: ₹{test_results.get('hyderabad', {}).get('avg_salary', 0):,.0f}" if test_results.get('hyderabad', {}).get('avg_salary') else ""}

## 市場洞察
- 印度是全球深度學習人才的重要供應地
- Bangalore 作為"印度矽谷"擁有最多AI職位
- Hyderabad 正快速發展為AI研發中心
- 薪資水平相對較低但人才素質高

## 測試結論
✅ 印度 Deep Learning Engineer 職位搜尋測試完成
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
    success = test_india_deep_learning_engineer()
    if success:
        print("\n🎉 印度 Deep Learning Engineer 測試成功完成！")
    else:
        print("\n💥 印度 Deep Learning Engineer 測試失敗")
        sys.exit(1)