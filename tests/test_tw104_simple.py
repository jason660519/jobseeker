#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行簡化測試腳本
"""

import asyncio
import time
import random
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


class SimpleTW104Test:
    """簡化的104測試類"""
    
    def __init__(self):
        self.base_url = "https://www.104.com.tw"
        self.test_results = []
    
    async def test_104_access(self):
        """測試104網站訪問"""
        print("🚀 開始測試104人力銀行網站訪問...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # 測試首頁訪問
                start_time = time.time()
                await page.goto(self.base_url, timeout=30000)
                load_time = time.time() - start_time
                
                # 檢查頁面標題
                title = await page.title()
                
                # 模擬搜尋
                search_success = await self._test_search(page)
                
                await browser.close()
                
                result = {
                    "test_name": "104網站訪問測試",
                    "success": True,
                    "load_time": load_time,
                    "page_title": title,
                    "search_success": search_success,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"✅ 測試成功!")
                print(f"⏱️  頁面載入時間: {load_time:.2f}秒")
                print(f"📄 頁面標題: {title}")
                print(f"🔍 搜尋功能: {'成功' if search_success else '失敗'}")
                
                return result
                
        except Exception as e:
            result = {
                "test_name": "104網站訪問測試",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ 測試失敗: {e}")
            return result
    
    async def _test_search(self, page):
        """測試搜尋功能 - 使用替代搜尋策略"""
        try:
            # 使用替代搜尋策略：直接訪問搜尋URL
            search_url = "https://www.104.com.tw/jobs/search/?keyword=工程師"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # 檢查是否成功跳轉到搜尋結果頁面
            current_url = page.url
            if 'search' in current_url and 'keyword' in current_url:
                # 檢查是否有搜尋結果
                job_elements = await page.query_selector_all('.job')
                if len(job_elements) > 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"搜尋測試錯誤: {e}")
            return False
    
    async def run_multiple_tests(self, count=3):
        """運行多次測試"""
        print(f"🎯 開始運行 {count} 次測試...")
        
        for i in range(count):
            print(f"\n--- 第 {i+1}/{count} 次測試 ---")
            result = await self.test_104_access()
            self.test_results.append(result)
            
            # 測試間隔
            if i < count - 1:
                delay = random.uniform(3, 8)
                print(f"⏳ 等待 {delay:.1f} 秒後繼續...")
                await asyncio.sleep(delay)
        
        return self.test_results
    
    def generate_report(self):
        """生成測試報告"""
        if not self.test_results:
            print("❌ 沒有測試結果可報告")
            return
        
        # 統計結果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        success_rate = successful_tests / total_tests * 100
        
        avg_load_time = sum(r.get("load_time", 0) for r in self.test_results) / total_tests
        search_success_count = sum(1 for r in self.test_results if r.get("search_success", False))
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_load_time": avg_load_time,
                "search_success_count": search_success_count
            },
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存報告
        report_path = Path("tests/results/tw104_simple_test_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 顯示報告
        print(f"\n{'='*50}")
        print(f"📊 104人力銀行測試報告")
        print(f"{'='*50}")
        print(f"總測試數: {total_tests}")
        print(f"成功測試數: {successful_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"平均載入時間: {avg_load_time:.2f}秒")
        print(f"搜尋功能成功: {search_success_count}/{total_tests}")
        print(f"詳細報告已保存至: {report_path}")
        
        return report


async def main():
    """主函數"""
    test_runner = SimpleTW104Test()
    
    # 運行3次測試
    await test_runner.run_multiple_tests(3)
    
    # 生成報告
    test_runner.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
