#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試頁面結構
"""

import asyncio
from playwright.async_api import async_playwright


async def debug_page_structure():
    """調試頁面結構"""
    print("🔍 調試頁面結構...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # 訪問搜尋頁面
            search_url = "https://www.104.com.tw/jobs/search/?keyword=Python工程師"
            print(f"📄 訪問: {search_url}")
            
            await page.goto(search_url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # 檢查頁面標題
            title = await page.title()
            print(f"📄 頁面標題: {title}")
            
            # 檢查是否有職位列表
            print("\n🔍 檢查職位列表:")
            
            # 檢查各種可能的選擇器
            selectors = [
                '.job-list',
                '.job-list > div',
                '.job-item',
                '.job-card',
                '.job-list-item',
                '[data-job-id]',
                '.job-info',
                '.job-title',
                'article',
                '.job',
                '.list-item',
                '.search-result',
                '.result-item'
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: {len(elements)} 個元素")
                    
                    if elements and len(elements) > 0:
                        # 檢查第一個元素的內容
                        first_element = elements[0]
                        text_content = await first_element.evaluate('el => el.textContent')
                        print(f"    第一個元素內容: {text_content[:200]}...")
                        
                        # 檢查是否有職位相關的內容
                        if any(keyword in text_content for keyword in ['工程師', 'Python', '軟體', '開發']):
                            print(f"    ✅ 找到職位相關內容!")
                            
                            # 檢查這個元素是否有鏈接
                            links = await first_element.query_selector_all('a')
                            print(f"    包含 {len(links)} 個鏈接")
                            
                            for i, link in enumerate(links[:3]):
                                href = await link.evaluate('el => el.href')
                                text = await link.evaluate('el => el.textContent')
                                print(f"      鏈接 {i+1}: {href} - {text[:50]}...")
                            
                            break
                        
                except Exception as e:
                    print(f"  {selector}: 錯誤 - {e}")
            
            # 檢查頁面是否包含職位資訊
            print("\n🔍 檢查頁面內容:")
            page_content = await page.content()
            
            if 'Python' in page_content:
                print("  ✅ 頁面包含 'Python'")
            if '工程師' in page_content:
                print("  ✅ 頁面包含 '工程師'")
            if '職位' in page_content:
                print("  ✅ 頁面包含 '職位'")
            if '工作' in page_content:
                print("  ✅ 頁面包含 '工作'")
            
            # 檢查是否有錯誤訊息
            print("\n🔍 檢查錯誤訊息:")
            error_selectors = [
                '.error',
                '.no-result',
                '.empty',
                '.not-found',
                '[class*="error"]',
                '[class*="empty"]',
                '[class*="no-result"]',
                '.no-data',
                '.no-jobs'
            ]
            
            for selector in error_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            text = await element.evaluate('el => el.textContent')
                            if text.strip():
                                print(f"  {selector}: {text.strip()}")
                except:
                    pass
            
            # 檢查頁面是否正常載入
            print("\n🔍 檢查頁面載入狀態:")
            current_url = page.url
            print(f"  當前URL: {current_url}")
            
            # 檢查是否有重定向
            if 'search' not in current_url:
                print("  ⚠️  可能發生了重定向")
            
            # 檢查頁面是否包含搜尋結果
            if '搜尋結果' in page_content or 'search results' in page_content.lower():
                print("  ✅ 頁面包含搜尋結果")
            else:
                print("  ❌ 頁面不包含搜尋結果")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ 調試失敗: {e}")


if __name__ == "__main__":
    asyncio.run(debug_page_structure())
