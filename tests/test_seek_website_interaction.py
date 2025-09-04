#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek網站實際互動測試
使用Playwright模擬真實用戶在Seek.com.au網站上的瀏覽行為
"""

import pytest
import asyncio
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class TestSeekWebsiteInteraction:
    """Seek網站實際互動測試類"""
    
    def __init__(self):
        self.base_url = "https://www.seek.com.au"
        self.browser = None
        self.context = None
        self.page = None
        
        # 真實的搜索關鍵詞
        self.job_keywords = [
            "software engineer",
            "data scientist",
            "product manager",
            "marketing coordinator",
            "business analyst",
            "frontend developer",
            "python developer",
            "project manager",
            "ui designer",
            "sales representative"
        ]
        
        # 澳洲真實地點
        self.locations = [
            "Sydney NSW",
            "Melbourne VIC",
            "Brisbane QLD",
            "Perth WA",
            "Adelaide SA",
            "Canberra ACT",
            "Gold Coast QLD",
            "Newcastle NSW"
        ]
    
    async def setup_browser(self, headless: bool = True):
        """設置瀏覽器環境"""
        playwright = await async_playwright().start()
        
        # 啟動瀏覽器（模擬真實用戶環境）
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # 創建瀏覽器上下文（模擬真實用戶）
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )
        
        # 創建頁面
        self.page = await self.context.new_page()
        
        # 設置額外的反檢測措施
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
    
    async def test_homepage_access(self):
        """測試首頁訪問"""
        print("\n=== 測試Seek首頁訪問 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 訪問Seek首頁
            print(f"正在訪問: {self.base_url}")
            response = await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 檢查頁面是否成功加載
            assert response.status == 200, f"頁面加載失敗，狀態碼: {response.status}"
            
            # 檢查頁面標題
            title = await self.page.title()
            print(f"頁面標題: {title}")
            assert "seek" in title.lower(), "頁面標題不包含'seek'"
            
            # 檢查關鍵元素是否存在
            search_elements = [
                '[data-automation="jobTitle"]',  # 職位搜索框
                '[data-automation="location"]',   # 地點搜索框
                '[data-automation="searchSubmit"]' # 搜索按鈕
            ]
            
            for selector in search_elements:
                element = await self.page.wait_for_selector(selector, timeout=10000)
                assert element is not None, f"找不到搜索元素: {selector}"
                print(f"✓ 找到搜索元素: {selector}")
            
            print("✓ 首頁訪問測試通過")
            
        except Exception as e:
            print(f"✗ 首頁訪問測試失敗: {str(e)}")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_job_search_interaction(self):
        """測試職位搜索互動"""
        print("\n=== 測試職位搜索互動 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 訪問首頁
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 隨機選擇搜索條件
            job_keyword = random.choice(self.job_keywords)
            location = random.choice(self.locations)
            
            print(f"搜索條件: '{job_keyword}' in '{location}'")
            
            # 模擬用戶輸入職位關鍵詞
            job_input = await self.page.wait_for_selector('[data-automation="jobTitle"]')
            await job_input.clear()
            await job_input.type(job_keyword, delay=random.randint(50, 150))
            
            # 模擬短暫停頓（用戶思考時間）
            await self.page.wait_for_timeout(random.randint(500, 1500))
            
            # 模擬用戶輸入地點
            location_input = await self.page.wait_for_selector('[data-automation="location"]')
            await location_input.clear()
            await location_input.type(location, delay=random.randint(50, 150))
            
            # 等待地點建議出現並選擇
            await self.page.wait_for_timeout(1000)
            
            # 點擊搜索按鈕
            search_button = await self.page.wait_for_selector('[data-automation="searchSubmit"]')
            await search_button.click()
            
            # 等待搜索結果頁面加載
            await self.page.wait_for_load_state('networkidle')
            
            # 檢查是否到達搜索結果頁面
            current_url = self.page.url
            assert "/jobs" in current_url, f"未到達搜索結果頁面: {current_url}"
            
            # 檢查搜索結果
            job_cards = await self.page.query_selector_all('[data-automation="normalJob"]')
            print(f"找到 {len(job_cards)} 個職位結果")
            
            if len(job_cards) > 0:
                # 檢查第一個職位卡片的內容
                first_job = job_cards[0]
                
                # 獲取職位標題
                title_element = await first_job.query_selector('[data-automation="jobTitle"]')
                if title_element:
                    title = await title_element.inner_text()
                    print(f"第一個職位: {title}")
                
                # 獲取公司名稱
                company_element = await first_job.query_selector('[data-automation="jobCompany"]')
                if company_element:
                    company = await company_element.inner_text()
                    print(f"公司: {company}")
                
                print("✓ 職位搜索互動測試通過")
            else:
                print("⚠ 沒有找到職位結果，但搜索功能正常")
            
        except Exception as e:
            print(f"✗ 職位搜索互動測試失敗: {str(e)}")
            # 截圖用於調試
            await self.page.screenshot(path=f"search_error_{int(time.time())}.png")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_job_detail_page_interaction(self):
        """測試職位詳情頁面互動"""
        print("\n=== 測試職位詳情頁面互動 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 先進行搜索
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 執行搜索
            job_input = await self.page.wait_for_selector('[data-automation="jobTitle"]')
            await job_input.type("software engineer")
            
            location_input = await self.page.wait_for_selector('[data-automation="location"]')
            await location_input.type("Sydney")
            
            search_button = await self.page.wait_for_selector('[data-automation="searchSubmit"]')
            await search_button.click()
            
            await self.page.wait_for_load_state('networkidle')
            
            # 找到第一個職位並點擊
            job_links = await self.page.query_selector_all('[data-automation="jobTitle"] a')
            
            if len(job_links) > 0:
                # 模擬用戶點擊第一個職位
                first_job_link = job_links[0]
                
                # 獲取職位URL
                job_url = await first_job_link.get_attribute('href')
                print(f"點擊職位URL: {job_url}")
                
                # 點擊職位鏈接
                await first_job_link.click()
                await self.page.wait_for_load_state('networkidle')
                
                # 檢查職位詳情頁面元素
                detail_elements = [
                    '[data-automation="job-detail-title"]',
                    '[data-automation="advertiser-name"]',
                    '[data-automation="job-detail-location"]'
                ]
                
                for selector in detail_elements:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=5000)
                        if element:
                            text = await element.inner_text()
                            print(f"✓ 找到元素 {selector}: {text[:50]}...")
                    except:
                        print(f"⚠ 未找到元素: {selector}")
                
                # 模擬用戶滾動頁面
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                await self.page.wait_for_timeout(1000)
                
                # 檢查是否有申請按鈕
                apply_buttons = await self.page.query_selector_all('[data-automation="job-apply"]')
                if apply_buttons:
                    print(f"✓ 找到 {len(apply_buttons)} 個申請按鈕")
                
                print("✓ 職位詳情頁面互動測試通過")
            else:
                print("⚠ 沒有找到可點擊的職位鏈接")
            
        except Exception as e:
            print(f"✗ 職位詳情頁面互動測試失敗: {str(e)}")
            await self.page.screenshot(path=f"detail_error_{int(time.time())}.png")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_filter_interaction(self):
        """測試過濾器互動"""
        print("\n=== 測試過濾器互動 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 進行基本搜索
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            job_input = await self.page.wait_for_selector('[data-automation="jobTitle"]')
            await job_input.type("developer")
            
            search_button = await self.page.wait_for_selector('[data-automation="searchSubmit"]')
            await search_button.click()
            
            await self.page.wait_for_load_state('networkidle')
            
            # 嘗試使用過濾器
            filter_selectors = [
                '[data-automation="workTypeFilter"]',  # 工作類型過濾器
                '[data-automation="salaryFilter"]',    # 薪資過濾器
                '[data-automation="datePostedFilter"]' # 發布日期過濾器
            ]
            
            for selector in filter_selectors:
                try:
                    filter_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if filter_element:
                        print(f"✓ 找到過濾器: {selector}")
                        
                        # 模擬點擊過濾器
                        await filter_element.click()
                        await self.page.wait_for_timeout(500)
                        
                        # 檢查是否有過濾選項出現
                        options = await self.page.query_selector_all(f"{selector} option, {selector} + * [role='option']")
                        if options:
                            print(f"  - 找到 {len(options)} 個過濾選項")
                        
                except Exception as filter_error:
                    print(f"⚠ 過濾器 {selector} 互動失敗: {str(filter_error)[:50]}...")
            
            print("✓ 過濾器互動測試完成")
            
        except Exception as e:
            print(f"✗ 過濾器互動測試失敗: {str(e)}")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_pagination_interaction(self):
        """測試分頁互動"""
        print("\n=== 測試分頁互動 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 進行搜索以獲得多頁結果
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            job_input = await self.page.wait_for_selector('[data-automation="jobTitle"]')
            await job_input.type("manager")  # 使用常見關鍵詞獲得更多結果
            
            search_button = await self.page.wait_for_selector('[data-automation="searchSubmit"]')
            await search_button.click()
            
            await self.page.wait_for_load_state('networkidle')
            
            # 檢查是否有分頁
            pagination_selectors = [
                '[data-automation="page-next"]',
                '.pagination',
                '[aria-label="Next page"]',
                'a[href*="page="]'
            ]
            
            pagination_found = False
            for selector in pagination_selectors:
                try:
                    pagination_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if pagination_element:
                        print(f"✓ 找到分頁元素: {selector}")
                        pagination_found = True
                        
                        # 模擬點擊下一頁
                        await pagination_element.click()
                        await self.page.wait_for_load_state('networkidle')
                        
                        # 檢查URL是否改變
                        current_url = self.page.url
                        if "page=" in current_url or "start=" in current_url:
                            print(f"✓ 成功導航到下一頁: {current_url}")
                        
                        break
                        
                except Exception as page_error:
                    print(f"⚠ 分頁元素 {selector} 互動失敗: {str(page_error)[:50]}...")
            
            if not pagination_found:
                print("⚠ 未找到分頁元素，可能結果不足一頁")
            
            print("✓ 分頁互動測試完成")
            
        except Exception as e:
            print(f"✗ 分頁互動測試失敗: {str(e)}")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_mobile_responsive_behavior(self):
        """測試移動端響應式行為"""
        print("\n=== 測試移動端響應式行為 ===")
        
        try:
            # 設置移動端瀏覽器環境
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(headless=True)
            
            # 模擬iPhone設備
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                viewport={'width': 375, 'height': 667},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True
            )
            
            self.page = await self.context.new_page()
            
            # 訪問移動版網站
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 檢查移動端特定元素
            mobile_elements = [
                '[data-automation="jobTitle"]',
                '[data-automation="location"]',
                '[data-automation="searchSubmit"]'
            ]
            
            for selector in mobile_elements:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # 檢查元素是否可見
                        is_visible = await element.is_visible()
                        print(f"✓ 移動端元素 {selector}: {'可見' if is_visible else '不可見'}")
                        
                except Exception as mobile_error:
                    print(f"⚠ 移動端元素 {selector} 檢查失敗: {str(mobile_error)[:50]}...")
            
            # 測試觸摸互動
            try:
                job_input = await self.page.wait_for_selector('[data-automation="jobTitle"]')
                await job_input.tap()  # 使用tap而不是click
                await job_input.type("developer")
                print("✓ 移動端觸摸輸入測試通過")
                
            except Exception as touch_error:
                print(f"⚠ 移動端觸摸測試失敗: {str(touch_error)[:50]}...")
            
            print("✓ 移動端響應式行為測試完成")
            
        except Exception as e:
            print(f"✗ 移動端響應式行為測試失敗: {str(e)}")
            raise
        finally:
            await self.cleanup_browser()
    
    async def test_performance_metrics(self):
        """測試性能指標"""
        print("\n=== 測試性能指標 ===")
        
        try:
            await self.setup_browser(headless=True)
            
            # 記錄開始時間
            start_time = time.time()
            
            # 訪問首頁並測量加載時間
            response = await self.page.goto(self.base_url, wait_until='networkidle')
            
            load_time = time.time() - start_time
            print(f"頁面加載時間: {load_time:.2f} 秒")
            
            # 獲取性能指標
            performance_metrics = await self.page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                        firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
                    };
                }
            """)
            
            print(f"DOM內容加載: {performance_metrics['domContentLoaded']:.2f} ms")
            print(f"頁面完全加載: {performance_metrics['loadComplete']:.2f} ms")
            print(f"首次繪製: {performance_metrics['firstPaint']:.2f} ms")
            print(f"首次內容繪製: {performance_metrics['firstContentfulPaint']:.2f} ms")
            
            # 性能基準檢查
            assert load_time < 10, f"頁面加載時間過長: {load_time:.2f} 秒"
            assert performance_metrics['firstContentfulPaint'] < 3000, f"首次內容繪製時間過長: {performance_metrics['firstContentfulPaint']:.2f} ms"
            
            print("✓ 性能指標測試通過")
            
        except Exception as e:
            print(f"✗ 性能指標測試失敗: {str(e)}")
            raise
        finally:
            await self.cleanup_browser()
    
    async def cleanup_browser(self):
        """清理瀏覽器資源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"清理瀏覽器時發生錯誤: {str(e)}")


# 測試運行器
class TestSeekWebsiteRunner:
    """Seek網站測試運行器"""
    
    def __init__(self):
        self.test_instance = TestSeekWebsiteInteraction()
    
    async def run_all_tests(self):
        """運行所有測試"""
        tests = [
            ("首頁訪問測試", self.test_instance.test_homepage_access),
            ("職位搜索互動測試", self.test_instance.test_job_search_interaction),
            ("職位詳情頁面測試", self.test_instance.test_job_detail_page_interaction),
            ("過濾器互動測試", self.test_instance.test_filter_interaction),
            ("分頁互動測試", self.test_instance.test_pagination_interaction),
            ("移動端響應式測試", self.test_instance.test_mobile_responsive_behavior),
            ("性能指標測試", self.test_instance.test_performance_metrics)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*50}")
                print(f"開始執行: {test_name}")
                print(f"{'='*50}")
                
                await test_func()
                results.append((test_name, "通過", None))
                print(f"✓ {test_name} 完成")
                
            except Exception as e:
                results.append((test_name, "失敗", str(e)))
                print(f"✗ {test_name} 失敗: {str(e)}")
            
            # 測試間隔
            await asyncio.sleep(2)
        
        # 輸出測試摘要
        print(f"\n{'='*50}")
        print("測試摘要")
        print(f"{'='*50}")
        
        passed = 0
        failed = 0
        
        for test_name, status, error in results:
            if status == "通過":
                print(f"✓ {test_name}: {status}")
                passed += 1
            else:
                print(f"✗ {test_name}: {status}")
                if error:
                    print(f"  錯誤: {error[:100]}...")
                failed += 1
        
        print(f"\n總計: {passed + failed} 個測試")
        print(f"通過: {passed} 個")
        print(f"失敗: {failed} 個")
        print(f"成功率: {passed/(passed+failed)*100:.1f}%")
        
        return results


if __name__ == "__main__":
    async def main():
        """主函數"""
        print("開始Seek網站實際互動測試...")
        
        runner = TestSeekWebsiteRunner()
        results = await runner.run_all_tests()
        
        print("\n測試完成！")
    
    # 運行測試
    asyncio.run(main())