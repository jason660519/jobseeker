#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek 爬蟲高級調試腳本
使用與實際爬蟲相同的配置來診斷問題
"""

import sys
import asyncio
import random
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
from jobseeker.seek.constant import USER_AGENTS, DEFAULT_HEADERS

async def debug_seek_with_stealth():
    """使用隱身配置調試 Seek 網站"""
    print("🔍 開始高級調試 Seek 網站...")
    
    async with async_playwright() as p:
        # 使用與 SeekScraper 相同的瀏覽器配置
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=' + random.choice(USER_AGENTS)
            ]
        )
        
        # 創建頁面並設置配置
        page = await browser.new_page(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 設置額外的請求頭
        await page.set_extra_http_headers(DEFAULT_HEADERS)
        
        # 隱藏 webdriver 特徵
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        try:
            # 設置較長的超時時間
            page.set_default_timeout(30000)
            
            print("📱 訪問 Seek 首頁...")
            await page.goto("https://www.seek.com.au", wait_until="domcontentloaded")
            
            # 等待頁面加載
            await page.wait_for_timeout(5000)
            
            # 檢查頁面標題
            title = await page.title()
            print(f"📄 頁面標題: {title}")
            
            # 如果遇到 Cloudflare 挑戰，等待更長時間
            if "Just a moment" in title or "Checking your browser" in title:
                print("⏳ 檢測到 Cloudflare 挑戰，等待通過...")
                
                # 等待最多 30 秒讓 Cloudflare 挑戰完成
                for i in range(30):
                    await page.wait_for_timeout(1000)
                    current_title = await page.title()
                    if "Just a moment" not in current_title and "Checking your browser" not in current_title:
                        print(f"✅ Cloudflare 挑戰已通過，新標題: {current_title}")
                        break
                    if i % 5 == 0:
                        print(f"⏳ 等待中... ({i+1}/30 秒)")
                
                # 再次檢查標題
                title = await page.title()
                print(f"📄 最終頁面標題: {title}")
            
            # 檢查當前 URL
            current_url = page.url
            print(f"🌐 當前 URL: {current_url}")
            
            # 如果成功通過 Cloudflare，嘗試搜索
            if "Just a moment" not in title:
                print("🔍 嘗試執行搜索...")
                
                # 查找搜索框
                search_selectors = [
                    'input[data-automation="searchKeywords"]',
                    'input[placeholder*="job title"]',
                    'input[placeholder*="keyword"]',
                    '#keywords'
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=5000)
                        if search_input:
                            print(f"✅ 找到搜索框: {selector}")
                            break
                    except:
                        continue
                
                if search_input:
                    # 輸入搜索詞
                    await search_input.fill("AI Engineer")
                    await page.wait_for_timeout(1000)
                    
                    # 查找並點擊搜索按鈕
                    search_button_selectors = [
                        'button[data-automation="searchButton"]',
                        'button[type="submit"]',
                        '.search-button'
                    ]
                    
                    for selector in search_button_selectors:
                        try:
                            search_button = await page.wait_for_selector(selector, timeout=3000)
                            if search_button:
                                print(f"✅ 找到搜索按鈕: {selector}")
                                await search_button.click()
                                break
                        except:
                            continue
                    
                    # 等待搜索結果頁面加載
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(5000)
                    
                    # 檢查搜索結果頁面
                    search_title = await page.title()
                    search_url = page.url
                    print(f"📄 搜索結果頁面標題: {search_title}")
                    print(f"🌐 搜索結果 URL: {search_url}")
                    
                    # 如果搜索結果頁面也遇到 Cloudflare
                    if "Just a moment" in search_title:
                        print("⏳ 搜索結果頁面也遇到 Cloudflare 挑戰...")
                        for i in range(20):
                            await page.wait_for_timeout(1000)
                            current_title = await page.title()
                            if "Just a moment" not in current_title:
                                print(f"✅ 搜索結果頁面 Cloudflare 挑戰已通過: {current_title}")
                                break
                    
                    # 保存搜索結果頁面
                    html = await page.content()
                    with open("seek_search_advanced.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("💾 搜索結果頁面 HTML 已保存")
                    
                    await page.screenshot(path="seek_search_advanced.png", full_page=True)
                    print("📸 搜索結果頁面截圖已保存")
                    
                    # 分析頁面結構
                    print("\n🔍 分析搜索結果頁面結構...")
                    
                    # 查找職位相關元素
                    job_selectors = [
                        'article[data-automation="normalJob"]',
                        'article[data-testid="job-card"]',
                        'div[data-automation="searchResults"]',
                        'article',
                        '[class*="job"]'
                    ]
                    
                    for selector in job_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                print(f"✅ 找到 {len(elements)} 個元素: {selector}")
                                
                                # 分析第一個元素
                                if elements:
                                    first_element = elements[0]
                                    try:
                                        text = await first_element.inner_text()
                                        print(f"📝 第一個元素內容: {text[:200]}...")
                                    except:
                                        pass
                        except:
                            pass
                    
                    # 查找 data-automation 屬性
                    automation_elements = await page.query_selector_all('[data-automation]')
                    if automation_elements:
                        print(f"\n🏷️ 找到 {len(automation_elements)} 個 data-automation 元素")
                        
                        automation_values = set()
                        for element in automation_elements[:10]:
                            try:
                                value = await element.get_attribute('data-automation')
                                if value:
                                    automation_values.add(value)
                            except:
                                pass
                        
                        print("📋 data-automation 值:")
                        for value in sorted(automation_values):
                            print(f"  - {value}")
                
                else:
                    print("❌ 未找到搜索框")
            
            else:
                print("❌ 無法通過 Cloudflare 挑戰")
                # 保存失敗頁面
                html = await page.content()
                with open("seek_cloudflare_blocked.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("💾 被阻擋頁面 HTML 已保存")
            
            print("\n✅ 高級調試完成！")
            
        except Exception as e:
            print(f"❌ 調試過程中出錯: {e}")
            try:
                await page.screenshot(path="seek_advanced_error.png")
                print("📸 錯誤截圖已保存")
            except:
                pass
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_seek_with_stealth())
