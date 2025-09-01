#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亞洲AI工程師職位搜尋測試 (台北、東京)

測試用戶提示: "搜尋台北和東京近7日創建的AI Engineer職位"

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


def test_asia_ai_engineer():
    """
    執行亞洲AI工程師職位搜尋測試 (台北、東京)
    
    測試參數:
    - 職位: AI Engineer
    - 地點: Taipei, Tokyo
    - 網站: Indeed, LinkedIn
    - 時間限制: 近7日
    
    Returns:
        dict: 測試結果
    """
    print("🚀 開始執行亞洲AI工程師職位搜尋測試")
    print("📝 用戶提示: 搜尋台北和東京近7日創建的AI Engineer職位")
    
    # 測試配置
    test_config = {
        'job_title': 'AI Engineer',
        'locations': [
            {'name': 'Taipei, Taiwan', 'country': 'Taiwan'},
            {'name': 'Tokyo, Japan', 'country': 'Japan'}
        ],
        'sites': [Site.INDEED, Site.LINKEDIN],
        'results_wanted': 50,
        'hours_old': 168  # 7天 = 168小時
    }
    
    # 創建結果目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / f"asia_ai_engineer_{timestamp}"
    results_dir.mkdir(exist_ok=True)
    
    all_jobs = []
    test_results = {
        'test_name': 'asia_ai_engineer',
        'user_prompt': '搜尋台北和東京近7日創建的AI Engineer職位',
        'start_time': datetime.now(),
        'locations_tested': [],
        'total_jobs': 0,
        'jobs_by_location': {},
        'jobs_by_site': {},
        'recent_jobs_count': 0,
        'status': 'running'
    }
    
    try:
        # 為每個地點執行搜尋
        for location_info in test_config['locations']:
            location = location_info['name']
            country = location_info['country']
            print(f"\n🔍 搜尋地點: {location}")
            print(f"🌏 國家設定: {country}")
            print(f"📅 時間限制: 近7日")
            
            try:
                # 執行JobSpy搜尋
                jobs_df = scrape_jobs(
                    site_name=test_config['sites'],
                    search_term=test_config['job_title'],
                    location=location,
                    results_wanted=test_config['results_wanted'],
                    hours_old=test_config['hours_old'],
                    country_indeed=country
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
                    
                    # 分析日期資訊
                    if 'date_posted' in jobs_df.columns:
                        recent_count = len(jobs_df.dropna(subset=['date_posted']))
                        print(f"📅 有發布日期資訊的職位: {recent_count}")
                    
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
            
            # 分析日期資訊
            if 'date_posted' in combined_df.columns:
                date_info = combined_df['date_posted'].dropna()
                test_results['recent_jobs_count'] = len(date_info)
                print(f"\n📅 日期分析:")
                print(f"   有發布日期的職位: {len(date_info)}")
                if len(date_info) > 0:
                    print(f"   最新職位: {date_info.max()}")
                    print(f"   最舊職位: {date_info.min()}")
            
            # 儲存合併結果
            combined_file = results_dir / "asia_ai_engineer_combined.csv"
            combined_df.to_csv(combined_file, index=False, encoding='utf-8-sig')
            
            # 儲存原始JSON資料
            json_file = results_dir / "asia_ai_engineer_raw_data.json"
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
                'has_salary_info': len(combined_df.dropna(subset=['min_amount'])) if 'min_amount' in combined_df.columns else 0,
                'remote_jobs': len(combined_df[combined_df['is_remote'] == True]) if 'is_remote' in combined_df.columns else 0
            }
            test_results['statistics'] = stats
            
            print(f"\n📈 統計資訊:")
            print(f"   💼 總職位數: {final_count}")
            print(f"   🏢 公司數: {stats['unique_companies']}")
            print(f"   📍 地點數: {stats['unique_locations']}")
            print(f"   💰 有薪資資訊: {stats['has_salary_info']}")
            print(f"   🏠 遠程工作: {stats['remote_jobs']}")
            
            # 分析職位標題關鍵字
            if 'title' in combined_df.columns:
                ai_keywords = ['AI', 'Machine Learning', 'Deep Learning', 'Neural', 'Artificial Intelligence']
                keyword_counts = {}
                for keyword in ai_keywords:
                    count = combined_df['title'].str.contains(keyword, case=False, na=False).sum()
                    if count > 0:
                        keyword_counts[keyword] = count
                
                if keyword_counts:
                    test_results['keyword_analysis'] = keyword_counts
                    print(f"\n🔍 關鍵字分析:")
                    for keyword, count in keyword_counts.items():
                        print(f"   {keyword}: {count} 個職位")
            
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
    report_content = f"""# 亞洲AI工程師職位搜尋測試報告

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
- **有日期資訊的職位**: {test_results.get('recent_jobs_count', 0)}

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
        report_content += f"- **遠程工作**: {stats['remote_jobs']}\n"
    
    if test_results.get('keyword_analysis'):
        report_content += "\n### 關鍵字分析\n"
        for keyword, count in test_results['keyword_analysis'].items():
            report_content += f"- **{keyword}**: {count} 個職位\n"
    
    # 測試結論
    report_content += "\n## 🎯 測試結論\n\n"
    if test_results['status'] == 'success':
        if test_results['total_jobs'] >= 5:
            report_content += "✅ **測試通過**: 成功找到亞洲地區的AI工程師職位\n"
        else:
            report_content += "⚠️ **部分成功**: 找到職位但數量較少，可能受到地區和時間限制影響\n"
        
        if test_results.get('recent_jobs_count', 0) > 0:
            report_content += "✅ **日期篩選有效**: 找到有發布日期資訊的職位\n"
        else:
            report_content += "⚠️ **日期資訊缺失**: 大部分職位缺少發布日期資訊\n"
            
    elif test_results['status'] == 'no_results':
        report_content += "❌ **測試失敗**: 沒有找到任何職位，可能原因:\n"
        report_content += "   - 亞洲地區AI工程師職位較少\n"
        report_content += "   - 7日時間限制過於嚴格\n"
        report_content += "   - 網站對亞洲地區支援有限\n"
    else:
        report_content += f"❌ **測試錯誤**: {test_results.get('error', '未知錯誤')}\n"
    
    report_content += "\n### 建議\n"
    report_content += "- 如果職位數量較少，可以考慮擴大搜尋範圍到其他亞洲城市\n"
    report_content += "- 可以嘗試移除時間限制以獲得更多結果\n"
    report_content += "- 考慮使用當地的求職網站進行補充搜尋\n"
    
    report_content += f"\n---\n\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    
    # 儲存報告
    report_file = results_dir / "test_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 測試報告已生成: {report_file}")


if __name__ == "__main__":
    # 執行測試
    results = test_asia_ai_engineer()
    
    # 生成報告
    if 'csv_file' in results:
        results_dir = Path(results['csv_file']).parent
        generate_test_report(results, results_dir)
    
    # 顯示最終狀態
    if results['status'] == 'success':
        print(f"\n🎉 測試成功完成! 找到 {results['total_jobs']} 個AI工程師職位")
        if results.get('recent_jobs_count', 0) > 0:
            print(f"📅 其中 {results['recent_jobs_count']} 個職位有發布日期資訊")
    else:
        print(f"\n⚠️ 測試狀態: {results['status']}")