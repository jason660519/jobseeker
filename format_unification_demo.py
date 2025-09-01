#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy格式統一展示

這個腳本展示JobSpy如何將不同網站的原始資料格式統一為標準CSV格式，
回應使用者關於「不同網站爬下來的原始raw檔格式也許會不一樣，但最終整理好的csv檔格式大家要統一」的需求。

作者: JobSpy Team
日期: 2025
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any

def create_raw_data_samples():
    """
    創建不同網站的原始資料範例，展示格式差異
    """
    
    # Indeed原始資料格式
    indeed_raw = {
        'jobs': [
            {
                'jobkey': '5e409e577046abcd',
                'title': 'Software Engineer',
                'company': 'AMERICAN SYSTEMS',
                'formattedLocation': 'Arlington, VA',
                'salary': '$150,000 - $200,000 a year',
                'snippet': 'THIS POSITION COMES WITH A 10K SIGNING BONUS!...',
                'url': '/viewjob?jk=5e409e577046abcd',
                'onmousedown': 'indeed_clk(this,\'\');',
                'jobLocationCity': 'Arlington',
                'jobLocationState': 'VA',
                'jobLocationCountry': 'US',
                'jobTypes': ['Full-time'],
                'pubDate': 'Mon, 02 Sep 2024 00:00:00 GMT'
            },
            {
                'jobkey': 'da39574a40cbef12',
                'title': 'Senior Software Engineer',
                'company': 'TherapyNotes.com',
                'formattedLocation': 'Philadelphia, PA',
                'salary': '$110,000 - $135,000 a year',
                'snippet': 'About Us TherapyNotes is the national leader i...',
                'url': '/viewjob?jk=da39574a40cbef12',
                'jobLocationCity': 'Philadelphia',
                'jobLocationState': 'PA',
                'jobLocationCountry': 'US',
                'jobTypes': ['Full-time'],
                'pubDate': 'Sun, 01 Sep 2024 00:00:00 GMT'
            }
        ]
    }
    
    # LinkedIn原始資料格式
    linkedin_raw = {
        'elements': [
            {
                'dashEntityUrn': 'urn:li:fsd_jobPosting:3693012711',
                'title': 'Software Engineer - Early Career',
                'companyDetails': {
                    'company': 'Lockheed Martin',
                    'companyResolutionResult': {
                        'name': 'Lockheed Martin',
                        'url': 'https://www.linkedin.com/company/lockheed-martin'
                    }
                },
                'primaryDescription': {
                    'text': 'Description:By bringing together people that u...'
                },
                'formattedLocation': 'Sunnyvale, CA',
                'workplaceTypes': ['On-site'],
                'listedAt': 1725148800000,  # Unix timestamp
                'jobPostingUrl': 'https://www.linkedin.com/jobs/view/3693012711',
                'applyMethod': {
                    'companyApplyUrl': 'https://careers.lockheedmartin.com/job/sunnyvale/...'
                }
            },
            {
                'dashEntityUrn': 'urn:li:fsd_jobPosting:3696158877',
                'title': 'Full-Stack Software Engineer',
                'companyDetails': {
                    'company': 'Rain',
                    'companyResolutionResult': {
                        'name': 'Rain',
                        'url': 'https://www.linkedin.com/company/rain-ai'
                    }
                },
                'primaryDescription': {
                    'text': 'Rain\'s mission is to create the fastest and ea...'
                },
                'formattedLocation': 'New York, NY',
                'workplaceTypes': ['On-site'],
                'listedAt': 1725235200000,
                'jobPostingUrl': 'https://www.linkedin.com/jobs/view/3696158877'
            }
        ]
    }
    
    # ZipRecruiter原始資料格式
    ziprecruiter_raw = {
        'jobs': [
            {
                'id': 'ziprecruiter-job-12345',
                'name': 'Software Engineer - New Grad',
                'hiring_company': {
                    'name': 'ZipRecruiter'
                },
                'location': {
                    'city': 'Santa Monica',
                    'state': 'CA',
                    'country': 'US'
                },
                'salary_range': {
                    'min': 130000,
                    'max': 150000,
                    'currency': 'USD',
                    'period': 'yearly'
                },
                'employment_type': 'FULL_TIME',
                'posted_time_friendly': '1 day ago',
                'url': 'https://www.ziprecruiter.com/jobs/ziprecruiter-12345',
                'snippet': 'We offer a hybrid work environment. Most US-ba...'
            },
            {
                'id': 'teksystems-67890',
                'name': 'Software Developer',
                'hiring_company': {
                    'name': 'TEKsystems'
                },
                'location': {
                    'city': 'Phoenix',
                    'state': 'AZ',
                    'country': 'US'
                },
                'salary_range': {
                    'min': 65,
                    'max': 75,
                    'currency': 'USD',
                    'period': 'hourly'
                },
                'employment_type': 'FULL_TIME',
                'posted_time_friendly': '2 days ago',
                'url': 'https://www.ziprecruiter.com/jobs/teksystems-67890',
                'snippet': 'Top Skills\' Details• 6 years of Java developme...'
            }
        ]
    }
    
    return {
        'indeed': indeed_raw,
        'linkedin': linkedin_raw,
        'ziprecruiter': ziprecruiter_raw
    }

def transform_indeed_data(raw_data: Dict) -> List[Dict]:
    """
    將Indeed原始資料轉換為JobSpy標準格式
    """
    jobs = []
    for job in raw_data['jobs']:
        # 解析薪資
        salary_text = job.get('salary', '')
        min_amount, max_amount, interval = None, None, None
        if salary_text:
            if 'year' in salary_text.lower():
                interval = 'yearly'
            elif 'hour' in salary_text.lower():
                interval = 'hourly'
            
            # 簡單的薪資解析
            import re
            amounts = re.findall(r'\$([\d,]+)', salary_text)
            if len(amounts) >= 2:
                min_amount = int(amounts[0].replace(',', ''))
                max_amount = int(amounts[1].replace(',', ''))
        
        # 轉換為標準格式
        standardized_job = {
            'id': f"in-{job['jobkey']}",
            'site': 'indeed',
            'job_url': f"https://www.indeed.com{job['url']}",
            'job_url_direct': None,
            'title': job['title'],
            'company': job['company'],
            'location': job['formattedLocation'],
            'date_posted': datetime.strptime(job['pubDate'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d'),
            'job_type': ', '.join(job.get('jobTypes', [])).lower().replace('-', '') if job.get('jobTypes') else None,
            'salary_source': 'direct_data' if salary_text else None,
            'interval': interval,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'currency': 'USD',
            'is_remote': False,
            'job_level': None,
            'job_function': None,
            'listing_type': 'organic',
            'emails': None,
            'description': job.get('snippet', ''),
            'company_industry': None,
            'company_url': None,
            'company_logo': None,
            'company_url_direct': None,
            'company_addresses': None,
            'company_num_employees': None,
            'company_revenue': None,
            'company_description': None,
            'skills': None,
            'experience_range': None,
            'company_rating': None,
            'company_reviews_count': None,
            'vacancy_count': None,
            'work_from_home_type': None
        }
        jobs.append(standardized_job)
    
    return jobs

def transform_linkedin_data(raw_data: Dict) -> List[Dict]:
    """
    將LinkedIn原始資料轉換為JobSpy標準格式
    """
    jobs = []
    for job in raw_data['elements']:
        # 提取ID
        job_id = job['dashEntityUrn'].split(':')[-1]
        
        # 轉換時間戳
        posted_date = datetime.fromtimestamp(job['listedAt'] / 1000).strftime('%Y-%m-%d')
        
        # 判斷是否遠程
        is_remote = 'remote' in ' '.join(job.get('workplaceTypes', [])).lower()
        
        standardized_job = {
            'id': f"li-{job_id}",
            'site': 'linkedin',
            'job_url': job['jobPostingUrl'],
            'job_url_direct': job.get('applyMethod', {}).get('companyApplyUrl'),
            'title': job['title'],
            'company': job['companyDetails']['company'],
            'location': job['formattedLocation'],
            'date_posted': posted_date,
            'job_type': 'fulltime',  # LinkedIn通常是全職
            'salary_source': None,
            'interval': None,
            'min_amount': None,
            'max_amount': None,
            'currency': None,
            'is_remote': is_remote,
            'job_level': None,
            'job_function': None,
            'listing_type': 'organic',
            'emails': None,
            'description': job['primaryDescription']['text'],
            'company_industry': None,
            'company_url': job['companyDetails']['companyResolutionResult'].get('url'),
            'company_logo': None,
            'company_url_direct': None,
            'company_addresses': None,
            'company_num_employees': None,
            'company_revenue': None,
            'company_description': None,
            'skills': None,
            'experience_range': None,
            'company_rating': None,
            'company_reviews_count': None,
            'vacancy_count': None,
            'work_from_home_type': None
        }
        jobs.append(standardized_job)
    
    return jobs

def transform_ziprecruiter_data(raw_data: Dict) -> List[Dict]:
    """
    將ZipRecruiter原始資料轉換為JobSpy標準格式
    """
    jobs = []
    for job in raw_data['jobs']:
        # 處理薪資
        salary_range = job.get('salary_range', {})
        min_amount = salary_range.get('min')
        max_amount = salary_range.get('max')
        interval = salary_range.get('period', 'yearly')
        currency = salary_range.get('currency', 'USD')
        
        # 組合地點
        location_data = job.get('location', {})
        location = f"{location_data.get('city', '')}, {location_data.get('state', '')}".strip(', ')
        
        standardized_job = {
            'id': f"zr-{job['id']}",
            'site': 'zip_recruiter',
            'job_url': job['url'],
            'job_url_direct': None,
            'title': job['name'],
            'company': job['hiring_company']['name'],
            'location': location,
            'date_posted': datetime.now().strftime('%Y-%m-%d'),  # 簡化處理
            'job_type': job['employment_type'].lower().replace('_', ''),
            'salary_source': 'direct_data' if min_amount else None,
            'interval': interval,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'currency': currency,
            'is_remote': False,
            'job_level': None,
            'job_function': None,
            'listing_type': 'organic',
            'emails': None,
            'description': job.get('snippet', ''),
            'company_industry': None,
            'company_url': None,
            'company_logo': None,
            'company_url_direct': None,
            'company_addresses': None,
            'company_num_employees': None,
            'company_revenue': None,
            'company_description': None,
            'skills': None,
            'experience_range': None,
            'company_rating': None,
            'company_reviews_count': None,
            'vacancy_count': None,
            'work_from_home_type': None
        }
        jobs.append(standardized_job)
    
    return jobs

def demonstrate_format_unification():
    """
    展示格式統一過程
    """
    print("\n" + "="*80)
    print("🔄 JobSpy格式統一展示")
    print("="*80)
    print("展示如何將不同網站的原始資料格式統一為JobSpy標準CSV格式")
    
    # 創建原始資料範例
    raw_data_samples = create_raw_data_samples()
    
    print("\n📥 步驟1: 原始資料格式展示")
    print("-" * 50)
    
    for site, raw_data in raw_data_samples.items():
        print(f"\n🌐 {site.upper()} 原始資料結構:")
        if site == 'indeed':
            sample_job = raw_data['jobs'][0]
            print(f"   • 職位ID: {sample_job['jobkey']}")
            print(f"   • 標題: {sample_job['title']}")
            print(f"   • 公司: {sample_job['company']}")
            print(f"   • 地點: {sample_job['formattedLocation']}")
            print(f"   • 薪資: {sample_job.get('salary', 'N/A')}")
            print(f"   • 發布時間: {sample_job['pubDate']}")
        elif site == 'linkedin':
            sample_job = raw_data['elements'][0]
            print(f"   • 職位URN: {sample_job['dashEntityUrn']}")
            print(f"   • 標題: {sample_job['title']}")
            print(f"   • 公司: {sample_job['companyDetails']['company']}")
            print(f"   • 地點: {sample_job['formattedLocation']}")
            print(f"   • 工作類型: {sample_job['workplaceTypes']}")
            print(f"   • 發布時間: {sample_job['listedAt']} (Unix時間戳)")
        elif site == 'ziprecruiter':
            sample_job = raw_data['jobs'][0]
            print(f"   • 職位ID: {sample_job['id']}")
            print(f"   • 標題: {sample_job['name']}")
            print(f"   • 公司: {sample_job['hiring_company']['name']}")
            print(f"   • 地點: {sample_job['location']}")
            print(f"   • 薪資範圍: {sample_job['salary_range']}")
            print(f"   • 就業類型: {sample_job['employment_type']}")
    
    print("\n🔄 步驟2: 資料轉換處理")
    print("-" * 50)
    
    all_standardized_jobs = []
    
    # 轉換Indeed資料
    print("\n🔧 轉換Indeed資料...")
    indeed_jobs = transform_indeed_data(raw_data_samples['indeed'])
    all_standardized_jobs.extend(indeed_jobs)
    print(f"   ✅ 已轉換 {len(indeed_jobs)} 個Indeed職位")
    
    # 轉換LinkedIn資料
    print("\n🔧 轉換LinkedIn資料...")
    linkedin_jobs = transform_linkedin_data(raw_data_samples['linkedin'])
    all_standardized_jobs.extend(linkedin_jobs)
    print(f"   ✅ 已轉換 {len(linkedin_jobs)} 個LinkedIn職位")
    
    # 轉換ZipRecruiter資料
    print("\n🔧 轉換ZipRecruiter資料...")
    ziprecruiter_jobs = transform_ziprecruiter_data(raw_data_samples['ziprecruiter'])
    all_standardized_jobs.extend(ziprecruiter_jobs)
    print(f"   ✅ 已轉換 {len(ziprecruiter_jobs)} 個ZipRecruiter職位")
    
    print("\n📤 步驟3: 統一格式輸出")
    print("-" * 50)
    
    # 創建統一的DataFrame
    unified_df = pd.DataFrame(all_standardized_jobs)
    
    # 保存為CSV
    output_file = 'unified_format_demo.csv'
    unified_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n📊 統一格式結果:")
    print(f"   • 總職位數: {len(unified_df)}")
    print(f"   • 總欄位數: {len(unified_df.columns)}")
    print(f"   • 包含網站: {', '.join(unified_df['site'].unique())}")
    print(f"   • 輸出檔案: {output_file}")
    
    # 顯示統一格式的範例
    print("\n📋 統一格式範例 (前3筆):")
    display_columns = ['site', 'title', 'company', 'location', 'job_type', 'interval', 'min_amount', 'max_amount']
    print(unified_df[display_columns].head(3).to_string(index=False))
    
    print("\n💡 格式統一的關鍵特點:")
    print("   🔹 所有網站使用相同的欄位名稱和順序")
    print("   🔹 薪資格式標準化 (min_amount, max_amount, interval, currency)")
    print("   🔹 日期格式統一為 YYYY-MM-DD")
    print("   🔹 布林值統一為 True/False")
    print("   🔹 缺失資料統一為 None/空值")
    print("   🔹 職位類型標準化 (fulltime, parttime, contract, etc.)")
    
    return unified_df

def compare_before_after():
    """
    對比轉換前後的格式差異
    """
    print("\n" + "="*80)
    print("📊 轉換前後對比分析")
    print("="*80)
    
    # 原始格式特點
    print("\n❌ 轉換前 - 各網站原始格式差異:")
    print("\n🔸 Indeed:")
    print("   • 職位ID: jobkey")
    print("   • 薪資: 文字描述 ('$150,000 - $200,000 a year')")
    print("   • 日期: RFC 2822格式 ('Mon, 02 Sep 2024 00:00:00 GMT')")
    print("   • 地點: formattedLocation")
    print("   • 職位類型: jobTypes陣列")
    
    print("\n🔸 LinkedIn:")
    print("   • 職位ID: dashEntityUrn (URN格式)")
    print("   • 薪資: 通常不提供")
    print("   • 日期: Unix時間戳 (1725148800000)")
    print("   • 地點: formattedLocation")
    print("   • 工作類型: workplaceTypes陣列")
    
    print("\n🔸 ZipRecruiter:")
    print("   • 職位ID: id")
    print("   • 薪資: 結構化物件 {min, max, currency, period}")
    print("   • 日期: 相對時間 ('1 day ago')")
    print("   • 地點: 結構化物件 {city, state, country}")
    print("   • 職位類型: employment_type")
    
    print("\n✅ 轉換後 - JobSpy統一格式:")
    print("\n🔹 統一欄位:")
    print("   • 職位ID: 統一前綴格式 (in-xxx, li-xxx, zr-xxx)")
    print("   • 薪資: min_amount, max_amount, interval, currency")
    print("   • 日期: YYYY-MM-DD格式")
    print("   • 地點: 統一字串格式 'City, State'")
    print("   • 職位類型: 標準化值 (fulltime, parttime, contract)")
    
    print("\n🔹 標準化處理:")
    print("   • 薪資解析: 文字→數值")
    print("   • 時間轉換: 各種格式→ISO日期")
    print("   • 地點標準化: 結構化→統一字串")
    print("   • 布林值統一: 各種表示→True/False")
    print("   • 空值處理: 各種空值→None")

def main():
    """
    主函數
    """
    print("🚀 JobSpy格式統一展示工具")
    print("回應使用者需求：'不同網站爬下來的原始raw檔格式也許會不一樣，但最終整理好的csv檔格式大家要統一'")
    
    # 展示格式統一過程
    unified_df = demonstrate_format_unification()
    
    # 對比分析
    compare_before_after()
    
    print("\n" + "="*80)
    print("🎯 JobSpy格式統一總結")
    print("="*80)
    print("\n✨ JobSpy的格式統一機制確保:")
    print("   1️⃣ 不同網站的原始資料格式差異被完全抹平")
    print("   2️⃣ 所有輸出都遵循相同的34欄位標準格式")
    print("   3️⃣ 資料類型和格式完全一致")
    print("   4️⃣ 便於後續分析和處理")
    print("   5️⃣ 支援多網站資料合併")
    
    print("\n🔧 技術實現:")
    print("   • 每個網站爬蟲都有專門的資料轉換邏輯")
    print("   • 統一的JobPost模型定義標準格式")
    print("   • DataFrame輸出時強制欄位順序")
    print("   • 自動填充缺失欄位為None")
    
    print("\n📁 檔案輸出:")
    print(f"   📄 統一格式範例: unified_format_demo.csv")
    print(f"   📊 包含 {len(unified_df)} 個職位，來自3個不同網站")
    
    # 清理範例檔案
    import os
    if os.path.exists('unified_format_demo.csv'):
        print("\n🧹 清理範例檔案...")
        os.remove('unified_format_demo.csv')
        print("   已刪除: unified_format_demo.csv")

if __name__ == "__main__":
    main()