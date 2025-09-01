#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大 AI Research Scientist 職位搜尋測試
測試目標：搜尋多倫多和溫哥華的 AI Research Scientist 職位
測試類型：研究職位 + 加拿大AI生態系統測試
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

def test_canada_ai_research_scientist():
    """
    測試加拿大地區 AI Research Scientist 職位搜尋功能
    """
    print("=== 加拿大 AI Research Scientist 職位搜尋測試 ===")
    
    # 測試參數
    test_params = {
        'toronto': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'AI Research Scientist',
            'location': 'Toronto, ON',
            'country': Country.CANADA,
            'results_wanted': 50,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        },
        'vancouver': {
            'site_name': [Site.INDEED, Site.LINKEDIN],
            'search_term': 'AI Research Scientist',
            'location': 'Vancouver, BC',
            'country': Country.CANADA,
            'results_wanted': 50,
            'hours_old': 168,  # 一週內
            'job_type': 'fulltime'
        }
    }
    
    all_jobs = []
    test_results = {}
    
    # 為每個城市執行搜尋
    for city, params in test_params.items():
        print(f"\n🔍 搜尋 {city.title()} 的 AI Research Scientist 職位...")
        
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
                    print(f"   平均薪資: CAD ${avg_salary:,.0f}")
                    
                # 分析研究領域
                if 'description' in jobs.columns:
                    descriptions = ' '.join(jobs['description'].fillna('').astype(str))
                    research_areas = ['computer vision', 'natural language processing', 'reinforcement learning', 'robotics', 'healthcare ai']
                    area_counts = {area: descriptions.lower().count(area) for area in research_areas}
                    top_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"   熱門研究領域: {dict(top_areas)}")
                    
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
        print(f"\n📊 總計找到 {total_jobs} 個 AI Research Scientist 職位")
        
        # 創建結果目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path(f"tests_collection/user_prompt_tests/phase3_specialized_tests/canada_ai_research_scientist_{timestamp}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詳細結果
        combined_jobs.to_csv(result_dir / "canada_ai_research_scientist_jobs.csv", index=False, encoding='utf-8')
        
        # 研究領域分析
        research_analysis = {}
        if 'description' in combined_jobs.columns:
            all_descriptions = ' '.join(combined_jobs['description'].fillna('').astype(str))
            research_keywords = {
                'computer_vision': ['computer vision', 'cv', 'image recognition', 'object detection'],
                'nlp': ['nlp', 'natural language processing', 'text mining', 'language model'],
                'machine_learning': ['machine learning', 'ml', 'supervised learning', 'unsupervised learning'],
                'deep_learning': ['deep learning', 'neural network', 'cnn', 'rnn', 'transformer'],
                'reinforcement_learning': ['reinforcement learning', 'rl', 'q-learning'],
                'robotics': ['robotics', 'autonomous', 'robot'],
                'healthcare_ai': ['healthcare', 'medical ai', 'biomedical', 'clinical'],
                'autonomous_vehicles': ['autonomous vehicle', 'self-driving', 'automotive'],
                'quantum_computing': ['quantum', 'quantum computing'],
                'ethics_ai': ['ai ethics', 'fairness', 'bias', 'responsible ai']
            }
            
            for area, keywords in research_keywords.items():
                count = sum(all_descriptions.lower().count(keyword) for keyword in keywords)
                research_analysis[area] = count
        
        # 機構類型分析
        institution_analysis = {}
        if 'company' in combined_jobs.columns:
            companies = combined_jobs['company'].value_counts()
            # 分類機構類型
            tech_companies = ['Google', 'Microsoft', 'Amazon', 'Facebook', 'Apple', 'Nvidia', 'OpenAI']
            universities = ['University of Toronto', 'UBC', 'McGill', 'Waterloo', 'Alberta']
            research_labs = ['Vector Institute', 'Mila', 'CIFAR', 'Element AI']
            canadian_companies = ['Shopify', 'BlackBerry', 'Cohere', 'Layer 6']
            
            institution_analysis = {
                'tech_companies': sum(companies.get(company, 0) for company in tech_companies),
                'universities': sum(companies.get(company, 0) for company in universities),
                'research_labs': sum(companies.get(company, 0) for company in research_labs),
                'canadian_companies': sum(companies.get(company, 0) for company in canadian_companies),
                'others': len(combined_jobs) - sum(companies.get(company, 0) for company in tech_companies + universities + research_labs + canadian_companies)
            }
        
        # 生成分析報告
        analysis = {
            'test_info': {
                'test_name': 'Canada AI Research Scientist Search',
                'test_date': datetime.now().isoformat(),
                'total_jobs': total_jobs,
                'cities_tested': list(test_params.keys())
            },
            'research_analysis': research_analysis,
            'institution_analysis': institution_analysis,
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
        top_research_areas = sorted(research_analysis.items(), key=lambda x: x[1], reverse=True)[:5] if research_analysis else []
        
        report_content = f"""# 加拿大 AI Research Scientist 職位搜尋測試報告

## 測試概要
- **測試日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **測試城市**: Toronto, Vancouver
- **搜尋職位**: AI Research Scientist
- **總職位數**: {total_jobs}

## 研究領域分析
{chr(10).join([f"- **{area.replace('_', ' ').title()}**: {count} 次提及" for area, count in top_research_areas]) if top_research_areas else "- 研究領域分析資料不足"}

## 機構類型分布
{f"- **跨國科技公司**: {institution_analysis.get('tech_companies', 0)} 個職位" if institution_analysis else ""}
{f"- **大學院校**: {institution_analysis.get('universities', 0)} 個職位" if institution_analysis else ""}
{f"- **研究機構**: {institution_analysis.get('research_labs', 0)} 個職位" if institution_analysis else ""}
{f"- **加拿大本土公司**: {institution_analysis.get('canadian_companies', 0)} 個職位" if institution_analysis else ""}
{f"- **其他機構**: {institution_analysis.get('others', 0)} 個職位" if institution_analysis else ""}

## 城市分析

### Toronto
- 職位數量: {test_results.get('toronto', {}).get('job_count', 0)}
- 網站分布: {test_results.get('toronto', {}).get('sites', {})}
{f"- 平均薪資: CAD ${test_results.get('toronto', {}).get('avg_salary', 0):,.0f}" if test_results.get('toronto', {}).get('avg_salary') else ""}

### Vancouver
- 職位數量: {test_results.get('vancouver', {}).get('job_count', 0)}
- 網站分布: {test_results.get('vancouver', {}).get('sites', {})}
{f"- 平均薪資: CAD ${test_results.get('vancouver', {}).get('avg_salary', 0):,.0f}" if test_results.get('vancouver', {}).get('avg_salary') else ""}

## 加拿大AI生態系統洞察
- Toronto: Vector Institute、多倫多大學等頂尖AI研究機構聚集地
- Vancouver: UBC、加拿大AI研究的重要據點
- 政府支持：加拿大AI戰略投資超過$125M
- 人才優勢：世界級AI研究人員如Geoffrey Hinton、Yoshua Bengio
- 移民政策：Global Talent Stream吸引國際AI人才

## 測試結論
✅ 加拿大 AI Research Scientist 職位搜尋測試完成
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
    success = test_canada_ai_research_scientist()
    if success:
        print("\n🎉 加拿大 AI Research Scientist 測試成功完成！")
    else:
        print("\n💥 加拿大 AI Research Scientist 測試失敗")
        sys.exit(1)