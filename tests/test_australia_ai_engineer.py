#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 澳洲 AI 工程師職位爬蟲測試

這個腳本專門用於測試所有9個網站在澳洲地區的AI工程師職位爬取功能。
每個網站至少爬取20筆資料，並保存原始資料和整理後的CSV檔案。

Author: jobseeker Team
Date: 2024
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, List, Any

# 設定路徑
project_root = Path(__file__).parent.parent
tests_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))

try:
    from jobseeker import scrape_jobs
    from jobseeker.model import Site, Country
except ImportError as e:
    print(f"❌ 導入錯誤：{e}")
    print("請確保 jobseeker 模組可以正常導入")
    sys.exit(1)

class AustraliaAIEngineerTester:
    """
    澳洲 AI 工程師職位測試類別
    """
    
    def __init__(self):
        """
        初始化測試器
        """
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = tests_dir / "results" / f"australia_ai_engineer_{self.timestamp}"
        self.raw_data_dir = self.output_dir / "raw_data"
        self.csv_data_dir = self.output_dir / "csv_data"
        self.summary_dir = self.output_dir / "summary"
        
        # 創建輸出目錄
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.csv_data_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        
        # 支援的網站列表
        self.sites = [
            Site.LINKEDIN,
            Site.INDEED,
            Site.ZIP_RECRUITER,  # 正確的枚舉名稱
            Site.GLASSDOOR,
            Site.GOOGLE,
            # Site.BAYT,      # 中東地區，可能不適用澳洲
            # Site.NAUKRI,    # 印度地區，可能不適用澳洲
            # Site.BDJOBS,    # 孟加拉地區，可能不適用澳洲
            Site.SEEK,       # 澳洲本地網站，應該有很好的結果
        ]
        
        # 搜尋參數
        self.search_params = {
            "search_term": "AI Engineer",
            "location": "Australia",
            "country_indeed": "australia",  # 使用字串而非枚舉
            "results_wanted": 25,  # 每個網站爬取25筆，確保至少20筆
            "job_type": "fulltime",
            "is_remote": False,
            "linkedin_fetch_description": True,
            "linkedin_company_ids": None,
            "offset": 0,
            "hours_old": 72,  # 3天內的職位
        }
        
        self.results = {}
        self.errors = {}
        
    def save_raw_data(self, site_name: str, data: Any) -> str:
        """
        保存原始爬蟲資料
        
        Args:
            site_name: 網站名稱
            data: 原始資料
            
        Returns:
            str: 保存的檔案路徑
        """
        raw_file = self.raw_data_dir / f"{site_name}_raw_data.json"
        
        # 將 DataFrame 轉換為可序列化的格式
        if isinstance(data, pd.DataFrame):
            raw_data = {
                "metadata": {
                    "site": site_name,
                    "timestamp": self.timestamp,
                    "total_records": len(data),
                    "columns": list(data.columns)
                },
                "data": data.to_dict(orient="records")
            }
        else:
            raw_data = {
                "metadata": {
                    "site": site_name,
                    "timestamp": self.timestamp,
                    "data_type": str(type(data))
                },
                "data": str(data)
            }
        
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
        
        return str(raw_file)
    
    def save_csv_data(self, site_name: str, df: pd.DataFrame) -> str:
        """
        保存整理後的CSV資料
        
        Args:
            site_name: 網站名稱
            df: DataFrame 資料
            
        Returns:
            str: 保存的檔案路徑
        """
        csv_file = self.csv_data_dir / f"{site_name}_jobs.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return str(csv_file)
    
    def scrape_single_site(self, site: Site) -> Dict[str, Any]:
        """
        爬取單個網站的資料
        
        Args:
            site: 網站枚舉
            
        Returns:
            Dict: 包含結果和錯誤資訊的字典
        """
        site_name = site.value
        print(f"\n🔍 開始爬取 {site_name} 的澳洲 AI 工程師職位...")
        
        try:
            # 根據不同網站調整參數
            params = self.search_params.copy()
            
            if site == Site.SEEK:
                # Seek 是澳洲本地網站，調整搜尋參數
                params["location"] = "Sydney, Australia"
            elif site == Site.LINKEDIN:
                # LinkedIn 可能需要更具體的位置
                params["location"] = "Sydney, NSW, Australia"
            elif site == Site.INDEED:
                # Indeed 使用國家參數
                params["location"] = "Sydney NSW"
            
            start_time = time.time()
            
            # 執行爬蟲 - 使用正確的 scrape_jobs 函數
            result = scrape_jobs(
                site_name=site.value,  # 使用字串值而非枚舉
                search_term=params["search_term"],
                location=params["location"],
                country_indeed=params["country_indeed"],
                results_wanted=params["results_wanted"],
                job_type=params["job_type"],
                is_remote=params["is_remote"],
                linkedin_fetch_description=params.get("linkedin_fetch_description", True),
                linkedin_company_ids=params.get("linkedin_company_ids"),
                offset=params.get("offset", 0),
                hours_old=params.get("hours_old", 72)
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if isinstance(result, pd.DataFrame) and not result.empty:
                # 保存原始資料
                raw_file = self.save_raw_data(site_name, result)
                
                # 保存CSV資料
                csv_file = self.save_csv_data(site_name, result)
                
                print(f"✅ {site_name} 爬取成功：{len(result)} 筆資料")
                print(f"   原始資料：{raw_file}")
                print(f"   CSV檔案：{csv_file}")
                print(f"   耗時：{duration:.2f} 秒")
                
                return {
                    "success": True,
                    "site": site_name,
                    "records_count": len(result),
                    "duration": duration,
                    "raw_file": raw_file,
                    "csv_file": csv_file,
                    "data": result
                }
            else:
                print(f"⚠️ {site_name} 沒有找到資料")
                return {
                    "success": False,
                    "site": site_name,
                    "error": "No data found",
                    "duration": duration
                }
                
        except Exception as e:
            print(f"❌ {site_name} 爬取失敗：{str(e)}")
            return {
                "success": False,
                "site": site_name,
                "error": str(e),
                "duration": 0
            }
    
    def run_all_sites(self) -> Dict[str, Any]:
        """
        執行所有網站的爬蟲
        
        Returns:
            Dict: 完整的測試結果
        """
        print("🚀 開始執行澳洲 AI 工程師職位爬蟲測試")
        print(f"📍 搜尋條件：{self.search_params['search_term']} in {self.search_params['location']}")
        print(f"📊 目標：每個網站至少 {self.search_params['results_wanted']} 筆資料")
        print(f"🌐 測試網站：{[site.value for site in self.sites]}")
        print("="*80)
        
        total_start_time = time.time()
        
        for site in self.sites:
            result = self.scrape_single_site(site)
            
            if result["success"]:
                self.results[site.value] = result
            else:
                self.errors[site.value] = result
            
            # 在網站之間稍作停頓，避免被封鎖
            time.sleep(2)
        
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        # 生成總結報告
        summary = self.generate_summary(total_duration)
        
        return summary
    
    def generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """
        生成測試總結報告
        
        Args:
            total_duration: 總執行時間
            
        Returns:
            Dict: 總結報告
        """
        print("\n" + "="*80)
        print("📊 測試總結報告")
        print("="*80)
        
        successful_sites = len(self.results)
        failed_sites = len(self.errors)
        total_sites = successful_sites + failed_sites
        total_records = sum(result["records_count"] for result in self.results.values())
        
        print(f"\n✅ 成功網站：{successful_sites}/{total_sites}")
        print(f"📈 總計資料：{total_records} 筆")
        print(f"⏱️ 總執行時間：{total_duration:.2f} 秒")
        
        # 成功的網站詳情
        if self.results:
            print("\n🎯 成功爬取的網站：")
            for site, result in self.results.items():
                print(f"  • {site}: {result['records_count']} 筆資料 ({result['duration']:.2f}秒)")
        
        # 失敗的網站詳情
        if self.errors:
            print("\n❌ 失敗的網站：")
            for site, error in self.errors.items():
                print(f"  • {site}: {error['error']}")
        
        # 檔案位置資訊
        print(f"\n📁 結果檔案位置：")
        print(f"  📂 主目錄：{self.output_dir}")
        print(f"  📄 原始資料：{self.raw_data_dir}")
        print(f"  📊 CSV檔案：{self.csv_data_dir}")
        print(f"  📋 總結報告：{self.summary_dir}")
        
        # 創建總結報告
        summary_data = {
            "test_info": {
                "timestamp": self.timestamp,
                "search_term": self.search_params["search_term"],
                "location": self.search_params["location"],
                "target_results_per_site": self.search_params["results_wanted"]
            },
            "results": {
                "successful_sites": successful_sites,
                "failed_sites": failed_sites,
                "total_sites": total_sites,
                "total_records": total_records,
                "total_duration": total_duration
            },
            "site_details": {
                "successful": self.results,
                "failed": self.errors
            },
            "file_locations": {
                "output_directory": str(self.output_dir),
                "raw_data_directory": str(self.raw_data_dir),
                "csv_data_directory": str(self.csv_data_dir),
                "summary_directory": str(self.summary_dir)
            }
        }
        
        # 保存總結報告
        summary_file = self.summary_dir / "test_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 創建合併的CSV檔案
        if self.results:
            self.create_combined_csv()
        
        print(f"\n📋 詳細報告已保存：{summary_file}")
        
        return summary_data
    
    def create_combined_csv(self) -> str:
        """
        創建合併所有網站資料的CSV檔案
        
        Returns:
            str: 合併檔案的路徑
        """
        combined_data = []
        
        for site, result in self.results.items():
            df = result["data"].copy()
            df["source_site"] = site
            df["scrape_timestamp"] = self.timestamp
            combined_data.append(df)
        
        if combined_data:
            combined_df = pd.concat(combined_data, ignore_index=True)
            combined_file = self.csv_data_dir / "combined_all_sites.csv"
            combined_df.to_csv(combined_file, index=False, encoding='utf-8-sig')
            
            print(f"📊 合併檔案已創建：{combined_file}")
            print(f"   總計 {len(combined_df)} 筆資料來自 {len(self.results)} 個網站")
            
            return str(combined_file)
        
        return ""

def main():
    """
    主要執行函數
    """
    print("🎯 jobseeker 澳洲 AI 工程師職位爬蟲測試")
    print("="*50)
    
    try:
        tester = AustraliaAIEngineerTester()
        summary = tester.run_all_sites()
        
        print("\n🎉 測試完成！")
        print(f"📁 所有結果已保存到：{tester.output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 測試執行失敗：{e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
