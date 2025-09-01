#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成亞洲AI工程師職位詳細列表
"""

import pandas as pd
from datetime import datetime

def generate_detailed_job_list():
    """生成詳細的職位列表"""
    
    try:
        # 讀取CSV文件
        df = pd.read_csv('asia_ai_engineer_jobs.csv')
        
        print('=' * 80)
        print('🤖 亞洲AI工程師職位詳細列表 (前50個)')
        print('=' * 80)
        print(f'總計職位數: {len(df)} 個')
        print(f'報告生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 80)
        print()
        
        # 顯示前50個職位
        for i, row in df.head(50).iterrows():
            print(f'{i+1:2d}. 【{row["title"]}】')
            print(f'    🏢 公司: {row["company"]}')
            print(f'    📍 地點: {row["city"]}, {row["country"]}')
            print(f'    📅 發布: {row["date_posted"]}')
            
            # 薪資資訊
            if (pd.notna(row.get('min_amount')) and 
                pd.notna(row.get('max_amount')) and 
                row.get('min_amount') != '' and 
                row.get('max_amount') != ''):
                min_sal = row.get('min_amount', 'N/A')
                max_sal = row.get('max_amount', 'N/A')
                currency = row.get('currency', '')
                print(f'    💰 薪資: {min_sal}-{max_sal} {currency}')
            
            # 工作類型
            if pd.notna(row.get('job_type')) and row.get('job_type') != '':
                print(f'    💼 類型: {row["job_type"]}')
            
            # 遠程工作
            if pd.notna(row.get('is_remote')):
                remote_status = '是' if row['is_remote'] else '否'
                print(f'    🏠 遠程: {remote_status}')
            
            print(f'    🌐 來源: {row["site"].upper()}')
            
            # 職位連結
            if pd.notna(row.get('job_url')) and row.get('job_url') != '':
                print(f'    🔗 連結: {row["job_url"]}')
            
            print()
        
        # 統計資訊
        print('=' * 80)
        print('📊 統計摘要')
        print('=' * 80)
        
        # 按國家統計
        print('\n🌏 按國家分布:')
        country_stats = df['country'].value_counts()
        for country, count in country_stats.items():
            percentage = (count / len(df)) * 100
            print(f'  {country}: {count} 個職位 ({percentage:.1f}%)')
        
        # 按網站統計
        print('\n🌐 按來源網站分布:')
        site_stats = df['site'].value_counts()
        for site, count in site_stats.items():
            percentage = (count / len(df)) * 100
            print(f'  {site.upper()}: {count} 個職位 ({percentage:.1f}%)')
        
        # 按職位類型統計
        print('\n💼 按工作類型分布:')
        if 'job_type' in df.columns:
            job_type_stats = df['job_type'].value_counts()
            for job_type, count in job_type_stats.items():
                if pd.notna(job_type) and job_type != '':
                    percentage = (count / len(df)) * 100
                    print(f'  {job_type}: {count} 個職位 ({percentage:.1f}%)')
        
        # 遠程工作統計
        print('\n🏠 遠程工作選項:')
        if 'is_remote' in df.columns:
            remote_stats = df['is_remote'].value_counts()
            for is_remote, count in remote_stats.items():
                if pd.notna(is_remote):
                    remote_label = '支援遠程' if is_remote else '需到辦公室'
                    percentage = (count / len(df)) * 100
                    print(f'  {remote_label}: {count} 個職位 ({percentage:.1f}%)')
        
        print('\n' + '=' * 80)
        print('✅ 詳細職位列表生成完成！')
        print('📄 完整數據請查看: asia_ai_engineer_jobs.csv')
        print('📋 搜尋摘要請查看: search_summary.csv')
        print('📖 詳細報告請查看: 亞洲AI工程師職位報告.md')
        print('=' * 80)
        
    except FileNotFoundError:
        print('❌ 錯誤: 找不到 asia_ai_engineer_jobs.csv 文件')
        print('請先執行搜尋腳本生成數據文件')
    except Exception as e:
        print(f'❌ 錯誤: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    generate_detailed_job_list()