#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版TW104爬蟲測試
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobseeker.tw104.enhanced_tw104 import EnhancedTW104Scraper


class EnhancedTW104Tester:
    """增強版TW104爬蟲測試器"""
    
    def __init__(self):
        self.scraper = EnhancedTW104Scraper(headless=True)
        self.test_results = []
    
    async def test_basic_search(self):
        """測試基本搜尋功能"""
        print("🔍 測試基本搜尋功能...")
        
        try:
            jobs = await self.scraper.search_jobs(
                keyword="Python工程師",
                max_pages=2
            )
            
            result = {
                "test_name": "基本搜尋功能",
                "success": len(jobs) > 0,
                "job_count": len(jobs),
                "timestamp": datetime.now().isoformat()
            }
            
            if jobs:
                print(f"✅ 基本搜尋成功，找到 {len(jobs)} 個職位")
                # 顯示前3個職位資訊
                for i, job in enumerate(jobs[:3]):
                    print(f"  {i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
            else:
                print("❌ 基本搜尋失敗，沒有找到職位")
            
            return result
            
        except Exception as e:
            print(f"❌ 基本搜尋測試失敗: {e}")
            return {
                "test_name": "基本搜尋功能",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_search_with_location(self):
        """測試帶地區的搜尋"""
        print("🔍 測試帶地區的搜尋...")
        
        try:
            jobs = await self.scraper.search_jobs(
                keyword="軟體工程師",
                location="6001001000",  # 台北市
                max_pages=2
            )
            
            result = {
                "test_name": "帶地區搜尋",
                "success": len(jobs) > 0,
                "job_count": len(jobs),
                "timestamp": datetime.now().isoformat()
            }
            
            if jobs:
                print(f"✅ 帶地區搜尋成功，找到 {len(jobs)} 個職位")
                # 檢查地區資訊
                locations = [job.get('location', '') for job in jobs if job.get('location')]
                unique_locations = set(locations)
                print(f"  地區分佈: {list(unique_locations)[:5]}")
            else:
                print("❌ 帶地區搜尋失敗，沒有找到職位")
            
            return result
            
        except Exception as e:
            print(f"❌ 帶地區搜尋測試失敗: {e}")
            return {
                "test_name": "帶地區搜尋",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_search_with_category(self):
        """測試帶職務類別的搜尋"""
        print("🔍 測試帶職務類別的搜尋...")
        
        try:
            jobs = await self.scraper.search_jobs(
                keyword="前端工程師",
                job_category="2007000000",  # 軟體工程師
                max_pages=2
            )
            
            result = {
                "test_name": "帶職務類別搜尋",
                "success": len(jobs) > 0,
                "job_count": len(jobs),
                "timestamp": datetime.now().isoformat()
            }
            
            if jobs:
                print(f"✅ 帶職務類別搜尋成功，找到 {len(jobs)} 個職位")
                # 檢查職位標題
                titles = [job.get('title', '') for job in jobs if job.get('title')]
                print(f"  職位標題範例: {titles[:3]}")
            else:
                print("❌ 帶職務類別搜尋失敗，沒有找到職位")
            
            return result
            
        except Exception as e:
            print(f"❌ 帶職務類別搜尋測試失敗: {e}")
            return {
                "test_name": "帶職務類別搜尋",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_multiple_keywords(self):
        """測試多個關鍵字搜尋"""
        print("🔍 測試多個關鍵字搜尋...")
        
        keywords = ["資料分析師", "產品經理", "UI設計師"]
        results = []
        
        for keyword in keywords:
            try:
                print(f"  搜尋關鍵字: {keyword}")
                jobs = await self.scraper.search_jobs(
                    keyword=keyword,
                    max_pages=1
                )
                
                result = {
                    "keyword": keyword,
                    "success": len(jobs) > 0,
                    "job_count": len(jobs)
                }
                results.append(result)
                
                if jobs:
                    print(f"    ✅ 找到 {len(jobs)} 個職位")
                else:
                    print(f"    ❌ 沒有找到職位")
                
                # 搜尋間隔
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"    ❌ 搜尋失敗: {e}")
                results.append({
                    "keyword": keyword,
                    "success": False,
                    "error": str(e)
                })
        
        # 統計結果
        successful_searches = sum(1 for r in results if r.get("success", False))
        total_jobs = sum(r.get("job_count", 0) for r in results)
        
        return {
            "test_name": "多個關鍵字搜尋",
            "success": successful_searches > 0,
            "successful_searches": successful_searches,
            "total_keywords": len(keywords),
            "total_jobs": total_jobs,
            "keyword_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_job_details(self):
        """測試職位詳細資訊獲取"""
        print("🔍 測試職位詳細資訊獲取...")
        
        try:
            # 先搜尋一些職位
            jobs = await self.scraper.search_jobs(
                keyword="Python工程師",
                max_pages=1
            )
            
            if not jobs:
                return {
                    "test_name": "職位詳細資訊獲取",
                    "success": False,
                    "error": "沒有找到職位進行詳細資訊測試",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 獲取第一個職位的詳細資訊
            first_job = jobs[0]
            job_url = first_job.get('job_url', '')
            
            if not job_url:
                return {
                    "test_name": "職位詳細資訊獲取",
                    "success": False,
                    "error": "職位沒有URL",
                    "timestamp": datetime.now().isoformat()
                }
            
            print(f"  獲取職位詳細資訊: {first_job.get('title', 'N/A')}")
            details = await self.scraper.get_job_details(job_url)
            
            result = {
                "test_name": "職位詳細資訊獲取",
                "success": bool(details),
                "job_title": first_job.get('title', ''),
                "job_url": job_url,
                "details_keys": list(details.keys()) if details else [],
                "timestamp": datetime.now().isoformat()
            }
            
            if details:
                print(f"✅ 成功獲取職位詳細資訊，包含 {len(details)} 個欄位")
                print(f"  詳細資訊欄位: {list(details.keys())}")
            else:
                print("❌ 獲取職位詳細資訊失敗")
            
            return result
            
        except Exception as e:
            print(f"❌ 職位詳細資訊測試失敗: {e}")
            return {
                "test_name": "職位詳細資訊獲取",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_statistics(self):
        """測試統計功能"""
        print("🔍 測試統計功能...")
        
        try:
            # 先搜尋一些職位
            jobs = await self.scraper.search_jobs(
                keyword="工程師",
                max_pages=2
            )
            
            if not jobs:
                return {
                    "test_name": "統計功能",
                    "success": False,
                    "error": "沒有找到職位進行統計測試",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 獲取統計資訊
            stats = self.scraper.get_statistics()
            
            result = {
                "test_name": "統計功能",
                "success": bool(stats),
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
            
            if stats:
                print(f"✅ 統計功能正常")
                print(f"  總職位數: {stats.get('total_jobs', 0)}")
                print(f"  公司數: {stats.get('unique_companies', 0)}")
                print(f"  地區數: {stats.get('unique_locations', 0)}")
                print(f"  有薪資資訊的職位: {stats.get('jobs_with_salary', 0)}")
            else:
                print("❌ 統計功能失敗")
            
            return result
            
        except Exception as e:
            print(f"❌ 統計功能測試失敗: {e}")
            return {
                "test_name": "統計功能",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 開始增強版TW104爬蟲測試...")
        
        tests = [
            self.test_basic_search,
            self.test_search_with_location,
            self.test_search_with_category,
            self.test_multiple_keywords,
            self.test_job_details,
            self.test_statistics
        ]
        
        for test_func in tests:
            try:
                result = await test_func()
                self.test_results.append(result)
                print()  # 空行分隔
            except Exception as e:
                print(f"❌ 測試 {test_func.__name__} 執行失敗: {e}")
                self.test_results.append({
                    "test_name": test_func.__name__,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # 生成測試報告
        self.generate_report()
    
    def generate_report(self):
        """生成測試報告"""
        if not self.test_results:
            print("❌ 沒有測試結果可報告")
            return
        
        # 統計結果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        success_rate = successful_tests / total_tests * 100
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "test_type": "enhanced_tw104_scraper"
            },
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存報告
        report_path = Path("tests/results/enhanced_tw104_test_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 顯示報告
        print(f"{'='*60}")
        print(f"📊 增強版TW104爬蟲測試報告")
        print(f"{'='*60}")
        print(f"總測試數: {total_tests}")
        print(f"成功測試數: {successful_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"詳細報告已保存至: {report_path}")
        
        # 顯示失敗的測試
        failed_tests = [r for r in self.test_results if not r.get("success", False)]
        if failed_tests:
            print(f"\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"  - {test.get('test_name', 'Unknown')}: {test.get('error', 'Unknown error')}")
        
        return report


async def main():
    """主函數"""
    tester = EnhancedTW104Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
