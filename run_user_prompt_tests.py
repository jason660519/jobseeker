#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶提示測試執行器

此腳本根據預定義的用戶提示自動執行JobSpy測試，
支援不同階段和單一測試的執行。

Author: JobSpy Team
Date: 2025-01-09
"""

import json
import os
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加jobseeker模組到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker import scrape_jobs
from jobseeker.model import Site


class UserPromptTestRunner:
    """
    用戶提示測試執行器類
    
    負責載入測試配置、執行測試案例、收集結果和生成報告。
    """
    
    def __init__(self, config_file: str = "test_user_prompts.json"):
        """
        初始化測試執行器
        
        Args:
            config_file: 測試配置檔案路徑
        """
        self.config_file = config_file
        self.test_config = self._load_test_config()
        self.results_dir = Path("tests_collection/user_prompt_tests")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_test_config(self) -> Dict[str, Any]:
        """
        載入測試配置檔案
        
        Returns:
            測試配置字典
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 找不到配置檔案: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 配置檔案格式錯誤: {e}")
            sys.exit(1)
    
    def _get_site_enum(self, site_name: str) -> Optional[Site]:
        """
        將網站名稱轉換為Site枚舉
        
        Args:
            site_name: 網站名稱字串
            
        Returns:
            對應的Site枚舉值
        """
        site_mapping = {
            'indeed': Site.INDEED,
            'linkedin': Site.LINKEDIN,
            'glassdoor': Site.GLASSDOOR,
            'seek': Site.SEEK,
            'naukri': Site.NAUKRI,
            'bayt': Site.BAYT,
            'ziprecruiter': Site.ZIP_RECRUITER
        }
        return site_mapping.get(site_name.lower())
    
    def _create_test_directory(self, test_id: str, phase: str) -> Path:
        """
        為測試創建專用目錄
        
        Args:
            test_id: 測試ID
            phase: 測試階段
            
        Returns:
            測試目錄路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = self.results_dir / f"{phase}" / f"{test_id}_{timestamp}"
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir
    
    def _execute_single_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行單一測試案例
        
        Args:
            test_config: 測試配置
            
        Returns:
            測試結果字典
        """
        test_id = test_config['id']
        prompt = test_config['prompt']
        params = test_config['parameters']
        
        print(f"\n🚀 執行測試: {test_id}")
        print(f"📝 提示: {prompt}")
        print(f"📍 地點: {', '.join(params['location'])}")
        
        # 確定測試階段
        phase = self._get_test_phase(test_id)
        test_dir = self._create_test_directory(test_id, phase)
        
        # 準備搜尋參數
        sites = [self._get_site_enum(site) for site in params.get('sites', ['indeed', 'linkedin'])]
        sites = [site for site in sites if site is not None]
        
        if not sites:
            return {
                'test_id': test_id,
                'status': 'failed',
                'error': '無有效的網站配置',
                'execution_time': 0,
                'job_count': 0
            }
        
        start_time = time.time()
        
        try:
            # 為每個地點執行搜尋
            all_jobs = []
            for location in params['location']:
                print(f"🔍 搜尋地點: {location}")
                
                # 執行JobSpy搜尋
                jobs_df = scrape_jobs(
                    site_name=sites,
                    search_term=params['job_title'],
                    location=location,
                    results_wanted=50,  # 每個地點最多50個職位
                    hours_old=168 if params.get('date_posted') == '7 days' else None,
                    country_indeed=params.get('country', 'Australia').title()
                )
                
                if jobs_df is not None and not jobs_df.empty:
                    all_jobs.append(jobs_df)
                    print(f"✅ 找到 {len(jobs_df)} 個職位")
                else:
                    print(f"⚠️  {location} 沒有找到職位")
            
            # 合併所有結果
            if all_jobs:
                import pandas as pd
                combined_df = pd.concat(all_jobs, ignore_index=True)
                
                # 移除重複職位
                combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
                
                # 儲存結果
                csv_file = test_dir / f"{test_id}_jobs.csv"
                combined_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                
                # 儲存原始資料
                raw_file = test_dir / f"{test_id}_raw_data.json"
                combined_df.to_json(raw_file, orient='records', indent=2, force_ascii=False)
                
                execution_time = time.time() - start_time
                job_count = len(combined_df)
                
                print(f"✅ 測試完成: 找到 {job_count} 個職位，耗時 {execution_time:.2f} 秒")
                
                # 生成測試報告
                self._generate_test_report(test_config, combined_df, test_dir, execution_time)
                
                return {
                    'test_id': test_id,
                    'status': 'success',
                    'job_count': job_count,
                    'execution_time': execution_time,
                    'csv_file': str(csv_file),
                    'raw_file': str(raw_file),
                    'sites_used': [site.value for site in sites],
                    'locations_searched': params['location']
                }
            else:
                return {
                    'test_id': test_id,
                    'status': 'failed',
                    'error': '所有地點都沒有找到職位',
                    'execution_time': time.time() - start_time,
                    'job_count': 0
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 測試失敗: {str(e)}")
            return {
                'test_id': test_id,
                'status': 'error',
                'error': str(e),
                'execution_time': execution_time,
                'job_count': 0
            }
    
    def _get_test_phase(self, test_id: str) -> str:
        """
        根據測試ID確定測試階段
        
        Args:
            test_id: 測試ID
            
        Returns:
            測試階段名稱
        """
        execution_plan = self.test_config.get('test_execution_plan', {})
        
        for phase_key, phase_info in execution_plan.items():
            if test_id in phase_info.get('tests', []):
                return phase_key
        
        return 'unknown_phase'
    
    def _generate_test_report(self, test_config: Dict[str, Any], 
                            jobs_df, test_dir: Path, execution_time: float):
        """
        生成測試報告
        
        Args:
            test_config: 測試配置
            jobs_df: 職位資料DataFrame
            test_dir: 測試目錄
            execution_time: 執行時間
        """
        test_id = test_config['id']
        expected = test_config.get('expected_results', {})
        
        # 分析結果
        total_jobs = len(jobs_df)
        unique_sites = jobs_df['site'].nunique() if 'site' in jobs_df.columns else 0
        unique_companies = jobs_df['company'].nunique() if 'company' in jobs_df.columns else 0
        
        # 檢查是否達到預期
        min_jobs_met = total_jobs >= expected.get('min_jobs', 0)
        
        report_content = f"""# {test_id.upper()} 測試報告

## 📋 測試概要

- **測試ID**: {test_id}
- **用戶提示**: "{test_config['prompt']}"
- **測試描述**: {test_config['description']}
- **執行時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 測試參數

- **職位標題**: {test_config['parameters']['job_title']}
- **搜尋地點**: {', '.join(test_config['parameters']['location'])}
- **目標網站**: {', '.join(test_config['parameters']['sites'])}
- **特殊條件**: {test_config['parameters'].get('date_posted', '無')}

## 📊 執行結果

### 基本統計
- **總職位數**: {total_jobs}
- **涵蓋網站數**: {unique_sites}
- **涵蓋公司數**: {unique_companies}
- **執行時間**: {execution_time:.2f} 秒

### 預期目標檢查
- **最低職位數要求**: {expected.get('min_jobs', 0)} (實際: {total_jobs}) {'✅' if min_jobs_met else '❌'}
- **網站覆蓋**: {', '.join(expected.get('sites_coverage', []))}

## 📈 詳細分析

### 網站分布
"""
        
        if 'site' in jobs_df.columns:
            site_counts = jobs_df['site'].value_counts()
            for site, count in site_counts.items():
                report_content += f"- **{site}**: {count} 個職位\n"
        
        report_content += "\n### 地點分布\n"
        if 'location' in jobs_df.columns:
            location_counts = jobs_df['location'].value_counts().head(10)
            for location, count in location_counts.items():
                report_content += f"- **{location}**: {count} 個職位\n"
        
        report_content += "\n### 公司分布 (前10名)\n"
        if 'company' in jobs_df.columns:
            company_counts = jobs_df['company'].value_counts().head(10)
            for company, count in company_counts.items():
                report_content += f"- **{company}**: {count} 個職位\n"
        
        # 薪資分析
        if 'min_amount' in jobs_df.columns and 'max_amount' in jobs_df.columns:
            salary_jobs = jobs_df.dropna(subset=['min_amount', 'max_amount'])
            if not salary_jobs.empty:
                avg_min = salary_jobs['min_amount'].mean()
                avg_max = salary_jobs['max_amount'].mean()
                report_content += f"\n### 薪資分析\n"
                report_content += f"- **有薪資資訊的職位**: {len(salary_jobs)} 個\n"
                report_content += f"- **平均最低薪資**: {avg_min:,.0f}\n"
                report_content += f"- **平均最高薪資**: {avg_max:,.0f}\n"
        
        report_content += f"\n## 🎯 測試結論\n\n"
        if min_jobs_met:
            report_content += "✅ **測試通過**: 達到預期的職位數量要求\n"
        else:
            report_content += "❌ **測試未通過**: 未達到預期的職位數量要求\n"
        
        report_content += f"\n---\n\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        # 儲存報告
        report_file = test_dir / f"{test_id}_test_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def run_phase_tests(self, phase: int) -> List[Dict[str, Any]]:
        """
        執行指定階段的所有測試
        
        Args:
            phase: 測試階段 (1, 2, 或 3)
            
        Returns:
            測試結果列表
        """
        phase_key = f"phase{phase}"
        execution_plan = self.test_config.get('test_execution_plan', {})
        
        if phase_key not in execution_plan:
            print(f"❌ 找不到階段 {phase} 的測試配置")
            return []
        
        phase_info = execution_plan[phase_key]
        test_ids = phase_info.get('tests', [])
        
        print(f"\n🎯 執行 {phase_info['name']} (階段 {phase})")
        print(f"📝 測試重點: {phase_info['focus']}")
        print(f"📋 包含測試: {', '.join(test_ids)}")
        
        results = []
        for test_id in test_ids:
            test_config = self._get_test_config_by_id(test_id)
            if test_config:
                result = self._execute_single_test(test_config)
                results.append(result)
            else:
                print(f"❌ 找不到測試 {test_id} 的配置")
        
        return results
    
    def run_single_test(self, test_id: str) -> Dict[str, Any]:
        """
        執行單一測試
        
        Args:
            test_id: 測試ID
            
        Returns:
            測試結果字典
        """
        test_config = self._get_test_config_by_id(test_id)
        if not test_config:
            print(f"❌ 找不到測試 {test_id} 的配置")
            return {'test_id': test_id, 'status': 'not_found'}
        
        return self._execute_single_test(test_config)
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """
        執行所有測試
        
        Returns:
            所有測試結果列表
        """
        print("\n🚀 開始執行所有用戶提示測試")
        
        all_results = []
        for phase in [1, 2, 3]:
            phase_results = self.run_phase_tests(phase)
            all_results.extend(phase_results)
        
        # 生成總體報告
        self._generate_summary_report(all_results)
        
        return all_results
    
    def _get_test_config_by_id(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        根據ID獲取測試配置
        
        Args:
            test_id: 測試ID
            
        Returns:
            測試配置字典或None
        """
        for test_config in self.test_config.get('test_prompts', []):
            if test_config['id'] == test_id:
                return test_config
        return None
    
    def _generate_summary_report(self, results: List[Dict[str, Any]]):
        """
        生成總體測試報告
        
        Args:
            results: 所有測試結果列表
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"user_prompt_tests_summary_{timestamp}.md"
        
        total_tests = len(results)
        successful_tests = len([r for r in results if r.get('status') == 'success'])
        total_jobs = sum(r.get('job_count', 0) for r in results)
        total_time = sum(r.get('execution_time', 0) for r in results)
        
        report_content = f"""# 用戶提示測試總體報告

## 📊 執行摘要

- **執行時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **總測試數**: {total_tests}
- **成功測試數**: {successful_tests}
- **成功率**: {(successful_tests/total_tests*100):.1f}%
- **總職位數**: {total_jobs}
- **總執行時間**: {total_time:.2f} 秒

## 📋 詳細結果

| 測試ID | 狀態 | 職位數 | 執行時間 | 備註 |
|--------|------|--------|----------|------|
"""
        
        for result in results:
            status_icon = "✅" if result.get('status') == 'success' else "❌"
            test_id = result.get('test_id', 'unknown')
            job_count = result.get('job_count', 0)
            exec_time = result.get('execution_time', 0)
            error = result.get('error', '')
            
            report_content += f"| {test_id} | {status_icon} | {job_count} | {exec_time:.2f}s | {error} |\n"
        
        report_content += f"\n---\n\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 總體報告已生成: {report_file}")


def main():
    """
    主函數 - 處理命令列參數並執行測試
    """
    parser = argparse.ArgumentParser(description='JobSpy 用戶提示測試執行器')
    parser.add_argument('--all', action='store_true', help='執行所有測試')
    parser.add_argument('--phase', type=int, choices=[1, 2, 3], help='執行指定階段的測試')
    parser.add_argument('--test', type=str, help='執行單一測試 (例如: user1)')
    parser.add_argument('--config', type=str, default='test_user_prompts.json', 
                       help='測試配置檔案路徑')
    
    args = parser.parse_args()
    
    # 檢查是否提供了執行選項
    if not any([args.all, args.phase, args.test]):
        parser.print_help()
        print("\n請指定要執行的測試類型。")
        return
    
    # 初始化測試執行器
    runner = UserPromptTestRunner(args.config)
    
    try:
        if args.all:
            results = runner.run_all_tests()
        elif args.phase:
            results = runner.run_phase_tests(args.phase)
        elif args.test:
            result = runner.run_single_test(args.test)
            results = [result] if result else []
        
        # 顯示執行摘要
        if results:
            successful = len([r for r in results if r.get('status') == 'success'])
            total_jobs = sum(r.get('job_count', 0) for r in results)
            print(f"\n🎯 測試完成摘要:")
            print(f"   📊 成功率: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            print(f"   💼 總職位數: {total_jobs}")
            print(f"   📁 結果目錄: tests_collection/user_prompt_tests/")
        
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試執行出錯: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()