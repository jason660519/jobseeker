#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行搜尋功能修復版本
解決彈出視窗阻擋問題
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


async def test_104_search_fixed():
    """修復版本的104搜尋測試"""
    print("🔧 開始測試修復版本的104搜尋功能...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # 訪問首頁
            print("📄 訪問首頁...")
            await page.goto("https://www.104.com.tw", timeout=60000)
            await page.wait_for_load_state('domcontentloaded')
            
            # 等待頁面完全載入
            await asyncio.sleep(3)
            
            # 檢查並關閉彈出視窗
            print("🔍 檢查彈出視窗...")
            popup_selectors = [
                '.popupBackdrop',
                '.popup',
                '[data-v-9baf5aae]',
                '.modal',
                '.overlay',
                'div[class*="popup"]',
                'div[class*="modal"]'
            ]
            
            popup_closed = False
            for selector in popup_selectors:
                try:
                    popup = await page.query_selector(selector)
                    if popup and await popup.is_visible():
                        print(f"🚫 發現彈出視窗: {selector}")
                        
                        # 嘗試點擊關閉按鈕
                        close_selectors = [
                            'button[aria-label="關閉"]',
                            'button[aria-label="Close"]',
                            '.close',
                            '.close-btn',
                            'button:has-text("×")',
                            'button:has-text("關閉")',
                            'button:has-text("Close")',
                            '[data-dismiss="modal"]'
                        ]
                        
                        for close_selector in close_selectors:
                            try:
                                close_btn = await page.query_selector(close_selector)
                                if close_btn and await close_btn.is_visible():
                                    await close_btn.click()
                                    print(f"✅ 成功關閉彈出視窗: {close_selector}")
                                    popup_closed = True
                                    break
                            except:
                                continue
                        
                        # 如果沒有找到關閉按鈕，嘗試按ESC鍵
                        if not popup_closed:
                            try:
                                await page.keyboard.press('Escape')
                                print("✅ 使用ESC鍵關閉彈出視窗")
                                popup_closed = True
                            except:
                                pass
                        
                        # 如果還是沒關閉，嘗試點擊背景
                        if not popup_closed:
                            try:
                                await popup.click()
                                print("✅ 點擊背景關閉彈出視窗")
                                popup_closed = True
                            except:
                                pass
                        
                        break
                except:
                    continue
            
            if not popup_closed:
                print("ℹ️  未發現彈出視窗或已自動關閉")
            
            # 等待一下確保彈出視窗完全關閉
            await asyncio.sleep(2)
            
            # 現在嘗試搜尋
            print("🔍 開始搜尋測試...")
            
            # 找到搜尋輸入框
            search_input = await page.query_selector('input[type="text"]')
            if not search_input:
                print("❌ 未找到搜尋輸入框")
                return False
            
            # 輸入搜尋詞
            await search_input.fill("Python工程師")
            await asyncio.sleep(1)
            print("✅ 已輸入搜尋詞: Python工程師")
            
            # 找到搜尋按鈕
            search_button = await page.query_selector('button:has-text("搜尋")')
            if not search_button:
                print("❌ 未找到搜尋按鈕")
                return False
            
            # 嘗試多種方式點擊搜尋按鈕
            click_success = False
            
            # 方法1: 直接點擊
            try:
                await search_button.click(timeout=5000)
                click_success = True
                print("✅ 方法1: 直接點擊成功")
            except Exception as e:
                print(f"❌ 方法1失敗: {e}")
            
            # 方法2: 使用JavaScript點擊
            if not click_success:
                try:
                    await search_button.evaluate('button => button.click()')
                    click_success = True
                    print("✅ 方法2: JavaScript點擊成功")
                except Exception as e:
                    print(f"❌ 方法2失敗: {e}")
            
            # 方法3: 使用Enter鍵
            if not click_success:
                try:
                    await search_input.press('Enter')
                    click_success = True
                    print("✅ 方法3: Enter鍵成功")
                except Exception as e:
                    print(f"❌ 方法3失敗: {e}")
            
            if not click_success:
                print("❌ 所有點擊方法都失敗")
                return False
            
            # 等待搜尋結果
            print("⏳ 等待搜尋結果...")
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
                current_url = page.url
                
                if 'search' in current_url or 'job' in current_url or '104.com.tw/jobs' in current_url:
                    print(f"✅ 搜尋成功! 跳轉到: {current_url}")
                    
                    # 檢查是否有搜尋結果
                    job_elements = await page.query_selector_all('.job-list-item, .job-item, .job-card, [data-testid="job-item"]')
                    print(f"📊 找到 {len(job_elements)} 個職位結果")
                    
                    return True
                else:
                    print(f"❌ 搜尋可能失敗，當前URL: {current_url}")
                    return False
                    
            except Exception as e:
                print(f"❌ 等待搜尋結果失敗: {e}")
                return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        try:
            await browser.close()
        except:
            pass


async def run_multiple_tests():
    """運行多次測試"""
    print("🎯 開始運行多次修復測試...")
    
    results = []
    for i in range(3):
        print(f"\n--- 第 {i+1}/3 次測試 ---")
        success = await test_104_search_fixed()
        results.append({
            "test_number": i + 1,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        if i < 2:  # 不是最後一次測試
            print("⏳ 等待5秒後繼續...")
            await asyncio.sleep(5)
    
    # 統計結果
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = successful_tests / len(results) * 100
    
    print(f"\n{'='*50}")
    print(f"📊 修復測試結果")
    print(f"{'='*50}")
    print(f"總測試數: {len(results)}")
    print(f"成功測試數: {successful_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    # 保存結果
    report = {
        "test_summary": {
            "total_tests": len(results),
            "successful_tests": successful_tests,
            "success_rate": success_rate
        },
        "test_results": results,
        "generated_at": datetime.now().isoformat()
    }
    
    report_path = Path("tests/results/104_search_fixed_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 詳細報告已保存至: {report_path}")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_multiple_tests())
