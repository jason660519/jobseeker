#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行替代搜尋策略測試
直接訪問搜尋URL，避免首頁彈出視窗問題
"""

import asyncio
import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


class AlternativeSearchStrategy:
    """替代搜尋策略"""
    
    def __init__(self):
        self.base_url = "https://www.104.com.tw"
        self.search_base_url = "https://www.104.com.tw/jobs/search/"
        self.test_results = []
    
    async def test_direct_search_url(self, keyword="Python工程師"):
        """測試直接訪問搜尋URL"""
        print(f"🔍 測試直接搜尋URL: {keyword}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # 構建搜尋URL
                search_url = f"{self.search_base_url}?keyword={urllib.parse.quote(keyword)}"
                print(f"📄 訪問搜尋URL: {search_url}")
                
                # 直接訪問搜尋頁面
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state('networkidle')
                
                # 檢查頁面標題
                title = await page.title()
                print(f"📄 頁面標題: {title}")
                
                # 檢查搜尋結果
                job_elements = await self._find_job_elements(page)
                print(f"📊 找到 {len(job_elements)} 個職位結果")
                
                # 檢查搜尋關鍵字是否正確顯示
                search_keyword_displayed = await self._check_search_keyword(page, keyword)
                print(f"🔍 搜尋關鍵字顯示: {'✅' if search_keyword_displayed else '❌'}")
                
                # 檢查是否有分頁
                pagination_info = await self._check_pagination(page)
                print(f"📄 分頁資訊: {pagination_info}")
                
                await browser.close()
                
                result = {
                    "keyword": keyword,
                    "search_url": search_url,
                    "page_title": title,
                    "job_count": len(job_elements),
                    "keyword_displayed": search_keyword_displayed,
                    "pagination": pagination_info,
                    "success": len(job_elements) > 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"✅ 搜尋測試完成: {'成功' if result['success'] else '失敗'}")
                return result
                
        except Exception as e:
            print(f"❌ 搜尋測試失敗: {e}")
            return {
                "keyword": keyword,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _find_job_elements(self, page):
        """尋找職位元素"""
        job_selectors = [
            '.job-list-item',
            '.job-item', 
            '.job-card',
            '[data-testid="job-item"]',
            '.job-list .job-item',
            '.job-list-item-container',
            '.job-info',
            '.job-title',
            'article[data-job-id]',
            '.job-list > div'
        ]
        
        for selector in job_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ 使用選擇器找到職位: {selector}")
                    return elements
            except:
                continue
        
        print("❌ 未找到職位元素")
        return []
    
    async def _check_search_keyword(self, page, keyword):
        """檢查搜尋關鍵字是否正確顯示"""
        try:
            # 檢查搜尋框中的值
            search_input = await page.query_selector('input[type="text"]')
            if search_input:
                input_value = await search_input.evaluate('el => el.value')
                if keyword in input_value:
                    return True
            
            # 檢查頁面中的搜尋關鍵字顯示
            keyword_elements = await page.query_selector_all(f'text="{keyword}"')
            if keyword_elements:
                return True
            
            # 檢查URL參數
            current_url = page.url
            if keyword in current_url:
                return True
                
            return False
        except:
            return False
    
    async def _check_pagination(self, page):
        """檢查分頁資訊"""
        try:
            # 尋找分頁元素
            pagination_selectors = [
                '.pagination',
                '.page-nav',
                '.pager',
                '[class*="page"]',
                '.job-list-pagination'
            ]
            
            for selector in pagination_selectors:
                pagination = await page.query_selector(selector)
                if pagination and await pagination.is_visible():
                    # 檢查總頁數
                    page_links = await pagination.query_selector_all('a, button')
                    total_pages = len(page_links)
                    
                    # 檢查當前頁
                    current_page = await page.evaluate("""
                        () => {
                            const current = document.querySelector('.pagination .active, .current, .selected');
                            return current ? parseInt(current.textContent) || 1 : 1;
                        }
                    """)
                    
                    return {
                        "found": True,
                        "total_pages": total_pages,
                        "current_page": current_page,
                        "selector": selector
                    }
            
            return {"found": False}
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    async def test_multiple_keywords(self, keywords=None):
        """測試多個關鍵字"""
        if keywords is None:
            keywords = [
                "Python工程師",
                "軟體工程師", 
                "前端工程師",
                "後端工程師",
                "資料分析師",
                "產品經理",
                "UI設計師",
                "行銷專員"
            ]
        
        print(f"🎯 開始測試 {len(keywords)} 個關鍵字...")
        
        results = []
        for i, keyword in enumerate(keywords):
            print(f"\n--- 測試 {i+1}/{len(keywords)}: {keyword} ---")
            result = await self.test_direct_search_url(keyword)
            results.append(result)
            
            # 測試間隔
            if i < len(keywords) - 1:
                delay = 2
                print(f"⏳ 等待 {delay} 秒後繼續...")
                await asyncio.sleep(delay)
        
        return results
    
    async def test_search_with_filters(self):
        """測試帶篩選條件的搜尋"""
        print("🔍 測試帶篩選條件的搜尋...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # 構建帶篩選條件的搜尋URL
                search_params = {
                    'keyword': 'Python工程師',
                    'area': '6001001000',  # 台北市
                    'jobcat': '2007000000',  # 軟體工程師
                    'order': '1',  # 相關性排序
                    'asc': '0'  # 降序
                }
                
                query_string = '&'.join([f"{k}={v}" for k, v in search_params.items()])
                search_url = f"{self.search_base_url}?{query_string}"
                
                print(f"📄 訪問帶篩選條件的搜尋URL: {search_url}")
                
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state('networkidle')
                
                # 檢查篩選條件是否生效
                job_elements = await self._find_job_elements(page)
                print(f"📊 找到 {len(job_elements)} 個職位結果")
                
                # 檢查地區篩選
                area_filter_active = await self._check_filter_active(page, 'area')
                print(f"🏢 地區篩選: {'✅' if area_filter_active else '❌'}")
                
                # 檢查職務類別篩選
                jobcat_filter_active = await self._check_filter_active(page, 'jobcat')
                print(f"💼 職務類別篩選: {'✅' if jobcat_filter_active else '❌'}")
                
                await browser.close()
                
                result = {
                    "search_url": search_url,
                    "job_count": len(job_elements),
                    "area_filter_active": area_filter_active,
                    "jobcat_filter_active": jobcat_filter_active,
                    "success": len(job_elements) > 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"✅ 篩選搜尋測試完成: {'成功' if result['success'] else '失敗'}")
                return result
                
        except Exception as e:
            print(f"❌ 篩選搜尋測試失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_filter_active(self, page, filter_type):
        """檢查篩選條件是否生效"""
        try:
            # 檢查篩選按鈕是否為活躍狀態
            active_selectors = [
                f'[data-filter="{filter_type}"].active',
                f'[data-filter="{filter_type}"].selected',
                f'[data-filter="{filter_type}"].current',
                f'.filter-{filter_type}.active',
                f'.filter-{filter_type}.selected'
            ]
            
            for selector in active_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    return True
            
            return False
        except:
            return False
    
    def generate_report(self, results):
        """生成測試報告"""
        if not results:
            print("❌ 沒有測試結果可報告")
            return
        
        # 統計結果
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get("success", False))
        success_rate = successful_tests / total_tests * 100
        
        # 計算平均職位數量
        job_counts = [r.get("job_count", 0) for r in results if r.get("job_count", 0) > 0]
        avg_job_count = sum(job_counts) / len(job_counts) if job_counts else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_job_count": avg_job_count,
                "test_type": "alternative_search_strategy"
            },
            "test_results": results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存報告
        report_path = Path("tests/results/104_alternative_search_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 顯示報告
        print(f"\n{'='*60}")
        print(f"📊 104人力銀行替代搜尋策略測試報告")
        print(f"{'='*60}")
        print(f"總測試數: {total_tests}")
        print(f"成功測試數: {successful_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"平均職位數量: {avg_job_count:.1f}")
        print(f"詳細報告已保存至: {report_path}")
        
        return report


async def main():
    """主函數"""
    strategy = AlternativeSearchStrategy()
    
    print("🚀 開始104人力銀行替代搜尋策略測試...")
    
    # 測試1: 單一關鍵字搜尋
    print("\n" + "="*50)
    print("測試1: 單一關鍵字搜尋")
    print("="*50)
    single_result = await strategy.test_direct_search_url("Python工程師")
    
    # 測試2: 多個關鍵字搜尋
    print("\n" + "="*50)
    print("測試2: 多個關鍵字搜尋")
    print("="*50)
    multiple_results = await strategy.test_multiple_keywords([
        "Python工程師",
        "軟體工程師",
        "前端工程師"
    ])
    
    # 測試3: 帶篩選條件的搜尋
    print("\n" + "="*50)
    print("測試3: 帶篩選條件的搜尋")
    print("="*50)
    filter_result = await strategy.test_search_with_filters()
    
    # 合併所有結果
    all_results = [single_result] + multiple_results + [filter_result]
    
    # 生成報告
    strategy.generate_report(all_results)


if __name__ == "__main__":
    asyncio.run(main())
