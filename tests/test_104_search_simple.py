#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行搜尋功能簡化調試
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


async def debug_104_search():
    """調試104搜尋功能"""
    print("🔍 開始調試104搜尋功能...")
    
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
            
            # 檢查頁面標題
            title = await page.title()
            print(f"📄 頁面標題: {title}")
            
            # 檢查搜尋相關元素
            print("🔍 檢查搜尋元素...")
            
            # 檢查所有輸入框
            inputs = await page.query_selector_all('input')
            print(f"找到 {len(inputs)} 個輸入框")
            
            search_inputs = []
            for i, input_elem in enumerate(inputs[:5]):  # 只檢查前5個
                try:
                    input_type = await input_elem.evaluate('el => el.type')
                    placeholder = await input_elem.evaluate('el => el.placeholder')
                    name = await input_elem.evaluate('el => el.name')
                    id_attr = await input_elem.evaluate('el => el.id')
                    is_visible = await input_elem.is_visible()
                    
                    print(f"  輸入框 {i+1}: type={input_type}, placeholder={placeholder}, name={name}, id={id_attr}, visible={is_visible}")
                    
                    if is_visible and input_type in ['text', 'search']:
                        search_inputs.append({
                            "index": i,
                            "type": input_type,
                            "placeholder": placeholder,
                            "name": name,
                            "id": id_attr
                        })
                except Exception as e:
                    print(f"  輸入框 {i+1}: 檢查失敗 - {e}")
            
            # 檢查所有按鈕
            buttons = await page.query_selector_all('button')
            print(f"找到 {len(buttons)} 個按鈕")
            
            search_buttons = []
            for i, button_elem in enumerate(buttons[:5]):  # 只檢查前5個
                try:
                    button_text = await button_elem.evaluate('el => el.textContent')
                    button_type = await button_elem.evaluate('el => el.type')
                    is_visible = await button_elem.is_visible()
                    
                    print(f"  按鈕 {i+1}: text={button_text.strip()}, type={button_type}, visible={is_visible}")
                    
                    if is_visible and ('搜尋' in button_text or 'search' in button_text.lower() or button_type == 'submit'):
                        search_buttons.append({
                            "index": i,
                            "text": button_text.strip(),
                            "type": button_type
                        })
                except Exception as e:
                    print(f"  按鈕 {i+1}: 檢查失敗 - {e}")
            
            # 嘗試搜尋測試
            print("\n🔄 嘗試搜尋測試...")
            search_success = False
            
            if search_inputs and search_buttons:
                try:
                    # 使用第一個可見的搜尋輸入框
                    input_elem = inputs[search_inputs[0]["index"]]
                    await input_elem.fill("Python工程師")
                    await asyncio.sleep(1)
                    
                    # 使用第一個搜尋按鈕
                    button_elem = buttons[search_buttons[0]["index"]]
                    await button_elem.click()
                    
                    # 等待頁面變化
                    await page.wait_for_load_state('networkidle', timeout=15000)
                    current_url = page.url
                    
                    if 'search' in current_url or 'job' in current_url:
                        print(f"✅ 搜尋成功! 跳轉到: {current_url}")
                        search_success = True
                    else:
                        print(f"❌ 搜尋可能失敗，當前URL: {current_url}")
                        
                except Exception as e:
                    print(f"❌ 搜尋測試失敗: {e}")
            else:
                print("❌ 未找到可用的搜尋輸入框或按鈕")
            
            await browser.close()
            
            # 生成報告
            report = {
                "timestamp": datetime.now().isoformat(),
                "page_title": title,
                "total_inputs": len(inputs),
                "total_buttons": len(buttons),
                "search_inputs": search_inputs,
                "search_buttons": search_buttons,
                "search_test_success": search_success
            }
            
            # 保存報告
            report_path = Path("tests/results/104_search_simple_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 調試報告已保存至: {report_path}")
            
            return report
            
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(debug_104_search())
