#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亞洲各國首都 AI 工程師職位搜尋腳本
搜尋亞洲主要城市的 AI 工程師職位，並生成報告
"""

from jobseeker import scrape_jobs
import pandas as pd
import time
from datetime import datetime

def search_asia_ai_jobs():
    """搜尋亞洲各國首都的 AI 工程師職位"""
    
    # 亞洲主要國家首都列表
    cities = [
        ('Tokyo', 'Japan'),
        ('Seoul', 'South Korea'),
        ('Beijing', 'China'),
        ('Singapore', 'Singapore'),
        ('Bangkok', 'Thailand'),
        ('Jakarta', 'Indonesia'),
        ('Manila', 'Philippines'),
        ('New Delhi', 'India'),
        ('Kuala Lumpur', 'Malaysia'),
        ('Hanoi', 'Vietnam'),
        ('Dhaka', 'Bangladesh'),
        ('Colombo', 'Sri Lanka'),
        ('Kathmandu', 'Nepal'),
        ('Yangon', 'Myanmar'),
        ('Phnom Penh', 'Cambodia'),
        ('Vientiane', 'Laos'),
        ('Bandar Seri Begawan', 'Brunei'),
        ('Dili', 'East Timor')
    ]
    
    all_jobs = []
    search_summary = []
    
    print('=' * 60)
    print('開始搜尋亞洲各國首都的 AI 工程師職位...')
    print('=' * 60)
    
    for i, (city, country) in enumerate(cities, 1):
        print(f'\n[{i}/{len(cities)}] 正在搜尋 {city}, {country}...')
        
        try:
            # 搜尋 AI engineer 職位
            result = scrape_jobs(
                site_name=['indeed', 'linkedin'],
                search_term='AI engineer',
                location=city,
                results_wanted=5,
                job_type='fulltime'
            )
            
            job_count = len(result)
            
            if job_count > 0:
                # 添加城市和國家資訊
                result['city'] = city
                result['country'] = country
                result['search_date'] = datetime.now().strftime('%Y-%m-%d')
                all_jobs.append(result)
                print(f'  ✅ 找到 {job_count} 個職位')
            else:
                print(f'  ❌ 未找到職位')
            
            # 記錄搜尋摘要
            search_summary.append({
                'city': city,
                'country': country,
                'job_count': job_count,
                'status': 'success'
            })
            
            # 避免過於頻繁的請求
            time.sleep(2)
            
        except Exception as e:
            print(f'  ❌ 搜尋 {city} 時發生錯誤: {e}')
            search_summary.append({
                'city': city,
                'country': country,
                'job_count': 0,
                'status': f'error: {str(e)}'
            })
            continue
    
    # 處理搜尋結果
    if all_jobs:
        # 合併所有結果
        combined_df = pd.concat(all_jobs, ignore_index=True)
        total_jobs = len(combined_df)
        
        print('\n' + '=' * 60)
        print(f'搜尋完成！總共找到 {total_jobs} 個 AI 工程師職位')
        print('=' * 60)
        
        # 顯示前 20 個職位
        print('\n📋 前 20 個職位預覽:')
        print('-' * 80)
        display_columns = ['title', 'company', 'city', 'country', 'location']
        if all(col in combined_df.columns for col in display_columns):
            print(combined_df[display_columns].head(20).to_string(index=False))
        else:
            print(combined_df.head(20).to_string(index=False))
        
        # 按國家統計
        print('\n📊 按國家統計:')
        print('-' * 30)
        country_stats = combined_df['country'].value_counts()
        for country, count in country_stats.items():
            print(f'{country}: {count} 個職位')
        
        # 保存結果
        output_file = 'asia_ai_engineer_jobs.csv'
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f'\n💾 完整結果已保存到: {output_file}')
        
        # 保存搜尋摘要
        summary_df = pd.DataFrame(search_summary)
        summary_file = 'search_summary.csv'
        summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
        print(f'📋 搜尋摘要已保存到: {summary_file}')
        
        return combined_df, summary_df
    
    else:
        print('\n❌ 未找到任何職位')
        # 仍然保存搜尋摘要
        summary_df = pd.DataFrame(search_summary)
        summary_file = 'search_summary.csv'
        summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
        print(f'📋 搜尋摘要已保存到: {summary_file}')
        
        return None, summary_df

if __name__ == '__main__':
    try:
        jobs_df, summary_df = search_asia_ai_jobs()
        
        if jobs_df is not None:
            print(f'\n🎉 搜尋成功完成！找到 {len(jobs_df)} 個 AI 工程師職位')
        else:
            print('\n⚠️ 搜尋完成，但未找到符合條件的職位')
            
    except Exception as e:
        print(f'\n💥 程序執行時發生錯誤: {e}')
        import traceback
        traceback.print_exc()