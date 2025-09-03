#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行搜尋功能調試腳本
專門檢查首頁智能職位搜尋區的問題
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


class SearchDebugger:
    """搜尋功能調試器"""
    
    def __init__(self):
        self.base_url = "https://www.104.com.tw"
        self.debug_results = []
    
    async def debug_search_functionality(self):
        """調試搜尋功能"""
        print("🔍 開始調試104人力銀行搜尋功能...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)  # 可視化模式便於觀察
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # 訪問首頁
                await page.goto(self.base_url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                print("📄 頁面載入完成，開始分析搜尋區域...")
                
                # 分析頁面結構
                await self._analyze_page_structure(page)
                
                # 測試搜尋輸入框
                await self._test_search_inputs(page)
                
                # 測試搜尋按鈕
                await self._test_search_buttons(page)
                
                # 測試完整搜尋流程
                await self._test_complete_search_flow(page)
                
                await browser.close()
                
        except Exception as e:
            print(f"❌ 調試過程出錯: {e}")
    
    async def _analyze_page_structure(self, page):
        """分析頁面結構"""
        print("\n🔍 分析頁面結構...")
        
        # 檢查頁面標題
        title = await page.title()
        print(f"📄 頁面標題: {title}")
        
        # 檢查是否有搜尋相關的元素
        search_elements = await page.query_selector_all('input, button, form')
        print(f"🔍 找到 {len(search_elements)} 個輸入/按鈕/表單元素")
        
        # 分析搜尋相關元素
        search_analysis = []
        for i, element in enumerate(search_elements[:10]):  # 只檢查前10個
            try:
                tag_name = await element.evaluate('el => el.tagName')
                element_type = await element.evaluate('el => el.type')
                placeholder = await element.evaluate('el => el.placeholder')
                name = await element.evaluate('el => el.name')
                id_attr = await element.evaluate('el => el.id')
                class_name = await element.evaluate('el => el.className')
                
                element_info = {
                    "index": i,
                    "tag": tag_name,
                    "type": element_type,
                    "placeholder": placeholder,
                    "name": name,
                    "id": id_attr,
                    "class": class_name
                }
                search_analysis.append(element_info)
                
                print(f"  {i}: {tag_name} - type:{element_type} - placeholder:{placeholder} - name:{name} - id:{id_attr}")
                
            except Exception as e:
                print(f"  {i}: 分析失敗 - {e}")
        
        self.debug_results.append({
            "type": "page_structure",
            "title": title,
            "total_elements": len(search_elements),
            "analysis": search_analysis
        })
    
    async def _test_search_inputs(self, page):
        """測試搜尋輸入框"""
        print("\n🔍 測試搜尋輸入框...")
        
        # 常見的搜尋輸入框選擇器
        input_selectors = [
            'input[name="keyword"]',
            'input[name="job"]',
            'input[name="q"]',
            'input[placeholder*="職務"]',
            'input[placeholder*="工作"]',
            'input[placeholder*="職位"]',
            'input[placeholder*="搜尋"]',
            'input[type="text"]',
            '#keyword',
            '#job',
            '#search',
            '.search-input',
            '.keyword-input',
            '.job-input'
        ]
        
        input_results = []
        for selector in input_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        placeholder = await element.evaluate('el => el.placeholder')
                        name = await element.evaluate('el => el.name')
                        
                        result = {
                            "selector": selector,
                            "found": True,
                            "visible": is_visible,
                            "enabled": is_enabled,
                            "placeholder": placeholder,
                            "name": name
                        }
                        input_results.append(result)
                        print(f"✅ 找到: {selector} - 可見:{is_visible} - 啟用:{is_enabled} - placeholder:{placeholder}")
                        
                        # 嘗試輸入測試
                        if is_visible and is_enabled:
                            try:
                                await element.fill("")
                                await element.type("Python工程師")
                                await asyncio.sleep(1)
                                value = await element.evaluate('el => el.value')
                                print(f"   ✅ 輸入測試成功，值: {value}")
                                result["input_test"] = "success"
                                result["input_value"] = value
                            except Exception as e:
                                print(f"   ❌ 輸入測試失敗: {e}")
                                result["input_test"] = "failed"
                                result["input_error"] = str(e)
                else:
                    print(f"❌ 未找到: {selector}")
                    
            except Exception as e:
                print(f"❌ 測試 {selector} 時出錯: {e}")
        
        self.debug_results.append({
            "type": "search_inputs",
            "results": input_results
        })
    
    async def _test_search_buttons(self, page):
        """測試搜尋按鈕"""
        print("\n🔍 測試搜尋按鈕...")
        
        button_selectors = [
            'button[type="submit"]',
            'button:has-text("搜尋")',
            'button:has-text("Search")',
            'button:has-text("找")',
            'input[type="submit"]',
            '.search-btn',
            '.search-button',
            '#search-btn',
            '#search-button',
            'button'
        ]
        
        button_results = []
        for selector in button_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        text = await element.evaluate('el => el.textContent')
                        button_type = await element.evaluate('el => el.type')
                        
                        result = {
                            "selector": selector,
                            "found": True,
                            "visible": is_visible,
                            "enabled": is_enabled,
                            "text": text.strip(),
                            "type": button_type
                        }
                        button_results.append(result)
                        print(f"✅ 找到按鈕: {selector} - 可見:{is_visible} - 啟用:{is_enabled} - 文字:{text.strip()}")
                        
            except Exception as e:
                print(f"❌ 測試按鈕 {selector} 時出錯: {e}")
        
        self.debug_results.append({
            "type": "search_buttons",
            "results": button_results
        })
    
    async def _test_complete_search_flow(self, page):
        """測試完整搜尋流程"""
        print("\n🔍 測試完整搜尋流程...")
        
        # 嘗試多種搜尋流程
        search_flows = [
            {
                "name": "標準搜尋流程",
                "input_selector": 'input[name="keyword"]',
                "button_selector": 'button[type="submit"]'
            },
            {
                "name": "通用輸入框流程",
                "input_selector": 'input[type="text"]',
                "button_selector": 'button'
            },
            {
                "name": "表單提交流程",
                "input_selector": 'input',
                "button_selector": 'button[type="submit"]'
            }
        ]
        
        flow_results = []
        for flow in search_flows:
            print(f"\n🔄 測試流程: {flow['name']}")
            try:
                # 尋找輸入框
                input_element = await page.query_selector(flow['input_selector'])
                if not input_element:
                    print(f"❌ 未找到輸入框: {flow['input_selector']}")
                    continue
                
                # 檢查輸入框是否可用
                is_visible = await input_element.is_visible()
                is_enabled = await input_element.is_enabled()
                
                if not (is_visible and is_enabled):
                    print(f"❌ 輸入框不可用: 可見:{is_visible}, 啟用:{is_enabled}")
                    continue
                
                # 輸入搜尋詞
                await input_element.fill("")
                await input_element.type("Python工程師")
                await asyncio.sleep(1)
                
                # 尋找並點擊搜尋按鈕
                button_element = await page.query_selector(flow['button_selector'])
                if not button_element:
                    print(f"❌ 未找到按鈕: {flow['button_selector']}")
                    continue
                
                # 檢查按鈕是否可用
                is_visible = await button_element.is_visible()
                is_enabled = await button_element.is_enabled()
                
                if not (is_visible and is_enabled):
                    print(f"❌ 按鈕不可用: 可見:{is_visible}, 啟用:{is_enabled}")
                    continue
                
                # 點擊搜尋
                print("🔄 點擊搜尋按鈕...")
                await button_element.click()
                
                # 等待頁面變化
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    current_url = page.url
                    print(f"✅ 搜尋成功，當前URL: {current_url}")
                    
                    flow_results.append({
                        "flow_name": flow['name'],
                        "success": True,
                        "final_url": current_url,
                        "input_selector": flow['input_selector'],
                        "button_selector": flow['button_selector']
                    })
                    
                except Exception as e:
                    print(f"❌ 等待頁面載入失敗: {e}")
                    flow_results.append({
                        "flow_name": flow['name'],
                        "success": False,
                        "error": str(e),
                        "input_selector": flow['input_selector'],
                        "button_selector": flow['button_selector']
                    })
                
                # 返回首頁進行下一次測試
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ 流程 {flow['name']} 測試失敗: {e}")
                flow_results.append({
                    "flow_name": flow['name'],
                    "success": False,
                    "error": str(e)
                })
        
        self.debug_results.append({
            "type": "search_flows",
            "results": flow_results
        })
    
    def generate_debug_report(self):
        """生成調試報告"""
        report = {
            "debug_summary": {
                "total_tests": len(self.debug_results),
                "timestamp": datetime.now().isoformat()
            },
            "debug_results": self.debug_results
        }
        
        # 保存報告
        report_path = Path("tests/results/104_search_debug_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"📊 104人力銀行搜尋功能調試報告")
        print(f"{'='*60}")
        print(f"調試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"詳細報告已保存至: {report_path}")
        
        return report


async def main():
    """主函數"""
    debugger = SearchDebugger()
    await debugger.debug_search_functionality()
    debugger.generate_debug_report()


if __name__ == "__main__":
    asyncio.run(main())
