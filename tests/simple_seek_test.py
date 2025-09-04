#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的Seek網站測試腳本
用於驗證基本的網頁訪問和用戶行為模擬功能
"""

import asyncio
from playwright.async_api import async_playwright
import time
import random

class SimpleSeekTest:
    """簡化的Seek網站測試類"""
    
    def __init__(self):
        self.test_results = []
        
    async def test_basic_access(self):
        """測試基本網站訪問"""
        print("\n=== 測試基本網站訪問 ===")
        
        async with async_playwright() as p:
            try:
                # 啟動瀏覽器
                browser = await p.chromium.launch(
                    headless=False,  # 顯示瀏覽器窗口
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # 創建新頁面
                page = await browser.new_page()
                
                # 設置用戶代理
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # 訪問Seek首頁
                print("正在訪問Seek首頁...")
                await page.goto('https://www.seek.com.au', wait_until='networkidle')
                
                # 等待頁面加載
                await page.wait_for_timeout(3000)
                
                # 獲取頁面標題
                title = await page.title()
                print(f"頁面標題: {title}")
                
                # 檢查是否成功訪問
                if 'SEEK' in title:
                    print("✓ 成功訪問Seek網站")
                    self.test_results.append(("基本訪問測試", "通過", None))
                else:
                    print("✗ 訪問失敗")
                    self.test_results.append(("基本訪問測試", "失敗", "頁面標題不正確"))
                
                # 模擬用戶行為 - 滾動頁面
                print("模擬用戶滾動行為...")
                await page.evaluate('window.scrollTo(0, 500)')
                await page.wait_for_timeout(1000)
                await page.evaluate('window.scrollTo(0, 0)')
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 基本訪問測試失敗: {str(e)}")
                self.test_results.append(("基本訪問測試", "失敗", str(e)))
    
    async def test_search_interaction(self):
        """測試搜索互動"""
        print("\n=== 測試搜索互動 ===")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # 訪問Seek首頁
                await page.goto('https://www.seek.com.au', wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 嘗試找到搜索框
                search_selectors = [
                    'input[data-automation="searchKeywordsField"]',
                    'input[placeholder*="job title"]',
                    'input[placeholder*="keyword"]',
                    '#SearchBar-Keywords',
                    'input[type="search"]'
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=5000)
                        if search_input:
                            print(f"找到搜索框: {selector}")
                            break
                    except:
                        continue
                
                if search_input:
                    # 模擬輸入搜索關鍵字
                    print("輸入搜索關鍵字: 'python developer'")
                    await search_input.fill('python developer')
                    await page.wait_for_timeout(1000)
                    
                    # 模擬按Enter鍵
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(5000)
                    
                    print("✓ 搜索互動測試完成")
                    self.test_results.append(("搜索互動測試", "通過", None))
                else:
                    print("✗ 未找到搜索框")
                    self.test_results.append(("搜索互動測試", "失敗", "未找到搜索框"))
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 搜索互動測試失敗: {str(e)}")
                self.test_results.append(("搜索互動測試", "失敗", str(e)))
    
    async def test_user_behavior_simulation(self):
        """測試用戶行為模擬"""
        print("\n=== 測試用戶行為模擬 ===")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # 訪問網站
                await page.goto('https://www.seek.com.au', wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # 模擬真實用戶行為
                behaviors = [
                    "隨機滾動",
                    "鼠標移動",
                    "頁面停留",
                    "返回頂部"
                ]
                
                for behavior in behaviors:
                    print(f"執行行為: {behavior}")
                    
                    if behavior == "隨機滾動":
                        # 隨機滾動
                        scroll_y = random.randint(200, 800)
                        await page.evaluate(f'window.scrollTo(0, {scroll_y})')
                        await page.wait_for_timeout(random.randint(1000, 2000))
                    
                    elif behavior == "鼠標移動":
                        # 模擬鼠標移動
                        await page.mouse.move(random.randint(100, 500), random.randint(100, 400))
                        await page.wait_for_timeout(500)
                    
                    elif behavior == "頁面停留":
                        # 模擬用戶閱讀時間
                        await page.wait_for_timeout(random.randint(2000, 4000))
                    
                    elif behavior == "返回頂部":
                        # 返回頂部
                        await page.evaluate('window.scrollTo(0, 0)')
                        await page.wait_for_timeout(1000)
                
                print("✓ 用戶行為模擬測試完成")
                self.test_results.append(("用戶行為模擬測試", "通過", None))
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 用戶行為模擬測試失敗: {str(e)}")
                self.test_results.append(("用戶行為模擬測試", "失敗", str(e)))
    
    def print_results(self):
        """打印測試結果"""
        print("\n" + "="*60)
        print("測試結果摘要")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[1] == "通過"])
        failed_tests = total_tests - passed_tests
        
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "成功率: 0%")
        
        print("\n詳細結果:")
        print("-"*60)
        for test_name, status, error in self.test_results:
            status_symbol = "✓" if status == "通過" else "✗"
            print(f"{status_symbol} {test_name}: {status}")
            if error:
                print(f"  錯誤: {error}")
    
    async def run_all_tests(self):
        """運行所有測試"""
        print("開始運行簡化Seek網站測試...")
        
        await self.test_basic_access()
        await self.test_search_interaction()
        await self.test_user_behavior_simulation()
        
        self.print_results()

async def main():
    """主函數"""
    tester = SimpleSeekTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())