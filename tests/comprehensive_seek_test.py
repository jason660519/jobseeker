#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的Seek網站測試腳本
包含用戶行為模擬、數據抓取和功能驗證
"""

import asyncio
from playwright.async_api import async_playwright
import time
import random
import json
from datetime import datetime

class ComprehensiveSeekTest:
    """全面的Seek網站測試類"""
    
    def __init__(self):
        self.test_results = []
        self.scraped_data = []
        self.performance_metrics = {}
        
    async def test_homepage_interaction(self):
        """測試首頁互動功能"""
        print("\n=== 測試首頁互動功能 ===")
        
        async with async_playwright() as p:
            try:
                start_time = time.time()
                
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # 訪問首頁
                await page.goto('https://www.seek.com.au', wait_until='networkidle')
                load_time = time.time() - start_time
                
                # 記錄性能指標
                self.performance_metrics['homepage_load_time'] = load_time
                print(f"首頁加載時間: {load_time:.2f}秒")
                
                # 檢查頁面元素
                title = await page.title()
                print(f"頁面標題: {title}")
                
                # 模擬用戶瀏覽行為
                await self.simulate_browsing_behavior(page)
                
                # 檢查關鍵元素是否存在
                elements_to_check = [
                    ('搜索框', 'input[placeholder*="keyword"], input[data-automation*="search"]'),
                    ('位置輸入', 'input[placeholder*="location"], input[placeholder*="suburb"]'),
                    ('搜索按鈕', 'button[type="submit"], button[data-automation*="search"]')
                ]
                
                found_elements = 0
                for element_name, selector in elements_to_check:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            print(f"✓ 找到{element_name}")
                            found_elements += 1
                    except:
                        print(f"✗ 未找到{element_name}")
                
                if found_elements >= 2:
                    print("✓ 首頁互動功能測試通過")
                    self.test_results.append(("首頁互動功能測試", "通過", None))
                else:
                    print("✗ 首頁互動功能測試失敗")
                    self.test_results.append(("首頁互動功能測試", "失敗", "關鍵元素缺失"))
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 首頁互動功能測試失敗: {str(e)}")
                self.test_results.append(("首頁互動功能測試", "失敗", str(e)))
    
    async def test_job_search_and_scraping(self):
        """測試職位搜索和數據抓取"""
        print("\n=== 測試職位搜索和數據抓取 ===")
        
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
                
                # 訪問首頁
                await page.goto('https://www.seek.com.au', wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 執行搜索
                search_keyword = 'python developer'
                location = 'Sydney NSW'
                
                print(f"搜索關鍵字: '{search_keyword}' 位置: '{location}'")
                
                # 找到並填寫搜索框
                search_selectors = [
                    'input[placeholder*="keyword"]',
                    'input[data-automation*="search"]',
                    'input[placeholder*="job title"]'
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=5000)
                        if search_input:
                            break
                    except:
                        continue
                
                if search_input:
                    await search_input.fill(search_keyword)
                    await page.wait_for_timeout(1000)
                    
                    # 嘗試找到位置輸入框
                    location_selectors = [
                        'input[placeholder*="location"]',
                        'input[placeholder*="suburb"]',
                        'input[data-automation*="location"]'
                    ]
                    
                    for selector in location_selectors:
                        try:
                            location_input = await page.wait_for_selector(selector, timeout=3000)
                            if location_input:
                                await location_input.fill(location)
                                break
                        except:
                            continue
                    
                    # 提交搜索
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(5000)
                    
                    # 等待搜索結果加載
                    await page.wait_for_load_state('networkidle')
                    
                    # 抓取職位數據
                    jobs_data = await self.scrape_job_listings(page)
                    
                    if jobs_data:
                        print(f"✓ 成功抓取 {len(jobs_data)} 個職位")
                        self.scraped_data.extend(jobs_data)
                        self.test_results.append(("職位搜索和數據抓取測試", "通過", None))
                    else:
                        print("✗ 未能抓取到職位數據")
                        self.test_results.append(("職位搜索和數據抓取測試", "失敗", "無法抓取數據"))
                else:
                    print("✗ 未找到搜索框")
                    self.test_results.append(("職位搜索和數據抓取測試", "失敗", "未找到搜索框"))
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 職位搜索和數據抓取測試失敗: {str(e)}")
                self.test_results.append(("職位搜索和數據抓取測試", "失敗", str(e)))
    
    async def test_advanced_user_behaviors(self):
        """測試高級用戶行為"""
        print("\n=== 測試高級用戶行為 ===")
        
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
                
                # 高級用戶行為測試
                behaviors = [
                    ("多次滾動", self.simulate_multiple_scrolls),
                    ("鼠標懸停", self.simulate_mouse_hover),
                    ("頁面縮放", self.simulate_page_zoom),
                    ("返回操作", self.simulate_back_navigation),
                    ("新標籤頁", self.simulate_new_tab)
                ]
                
                successful_behaviors = 0
                
                for behavior_name, behavior_func in behaviors:
                    try:
                        print(f"執行行為: {behavior_name}")
                        await behavior_func(page)
                        successful_behaviors += 1
                        print(f"✓ {behavior_name} 執行成功")
                    except Exception as e:
                        print(f"✗ {behavior_name} 執行失敗: {str(e)}")
                
                if successful_behaviors >= 3:
                    print("✓ 高級用戶行為測試通過")
                    self.test_results.append(("高級用戶行為測試", "通過", None))
                else:
                    print("✗ 高級用戶行為測試失敗")
                    self.test_results.append(("高級用戶行為測試", "失敗", "多個行為執行失敗"))
                
                await browser.close()
                
            except Exception as e:
                print(f"✗ 高級用戶行為測試失敗: {str(e)}")
                self.test_results.append(("高級用戶行為測試", "失敗", str(e)))
    
    async def simulate_browsing_behavior(self, page):
        """模擬真實瀏覽行為"""
        # 隨機滾動
        for _ in range(3):
            scroll_y = random.randint(200, 600)
            await page.evaluate(f'window.scrollTo(0, {scroll_y})')
            await page.wait_for_timeout(random.randint(1000, 2000))
        
        # 返回頂部
        await page.evaluate('window.scrollTo(0, 0)')
        await page.wait_for_timeout(1000)
    
    async def simulate_multiple_scrolls(self, page):
        """模擬多次滾動"""
        for i in range(5):
            scroll_y = random.randint(100, 800)
            await page.evaluate(f'window.scrollTo(0, {scroll_y})')
            await page.wait_for_timeout(random.randint(500, 1500))
    
    async def simulate_mouse_hover(self, page):
        """模擬鼠標懸停"""
        for _ in range(3):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await page.wait_for_timeout(random.randint(500, 1000))
    
    async def simulate_page_zoom(self, page):
        """模擬頁面縮放"""
        # 放大
        await page.keyboard.down('Control')
        await page.keyboard.press('Equal')
        await page.keyboard.up('Control')
        await page.wait_for_timeout(1000)
        
        # 縮小
        await page.keyboard.down('Control')
        await page.keyboard.press('Minus')
        await page.keyboard.up('Control')
        await page.wait_for_timeout(1000)
    
    async def simulate_back_navigation(self, page):
        """模擬返回導航"""
        # 記錄當前URL
        current_url = page.url
        
        # 嘗試點擊一個鏈接（如果存在）
        try:
            link = await page.wait_for_selector('a[href]', timeout=3000)
            if link:
                await link.click()
                await page.wait_for_timeout(2000)
                
                # 返回
                await page.go_back()
                await page.wait_for_timeout(1000)
        except:
            # 如果沒有鏈接，只是模擬返回操作
            pass
    
    async def simulate_new_tab(self, page):
        """模擬新標籤頁操作"""
        # 使用Ctrl+T打開新標籤頁（在某些情況下可能不工作）
        await page.keyboard.down('Control')
        await page.keyboard.press('KeyT')
        await page.keyboard.up('Control')
        await page.wait_for_timeout(1000)
    
    async def scrape_job_listings(self, page):
        """抓取職位列表數據"""
        jobs = []
        
        try:
            # 等待職位列表加載
            await page.wait_for_timeout(3000)
            
            # 嘗試不同的職位選擇器
            job_selectors = [
                '[data-automation="normalJob"]',
                '[data-automation="jobListing"]',
                'article[data-automation]',
                '.job-item',
                '[data-testid="job-card"]'
            ]
            
            job_elements = None
            for selector in job_selectors:
                try:
                    job_elements = await page.query_selector_all(selector)
                    if job_elements:
                        print(f"使用選擇器找到職位: {selector}")
                        break
                except:
                    continue
            
            if job_elements:
                # 限制抓取數量以避免過長時間
                max_jobs = min(5, len(job_elements))
                
                for i, job_element in enumerate(job_elements[:max_jobs]):
                    try:
                        # 抓取職位標題
                        title_element = await job_element.query_selector('a[data-automation="jobTitle"], h3 a, .job-title a')
                        title = await title_element.inner_text() if title_element else "未知職位"
                        
                        # 抓取公司名稱
                        company_element = await job_element.query_selector('[data-automation="jobCompany"], .company-name, .job-company')
                        company = await company_element.inner_text() if company_element else "未知公司"
                        
                        # 抓取位置
                        location_element = await job_element.query_selector('[data-automation="jobLocation"], .job-location, .location')
                        location = await location_element.inner_text() if location_element else "未知位置"
                        
                        job_data = {
                            'title': title.strip(),
                            'company': company.strip(),
                            'location': location.strip(),
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        jobs.append(job_data)
                        print(f"抓取職位 {i+1}: {title} - {company}")
                        
                    except Exception as e:
                        print(f"抓取職位 {i+1} 時出錯: {str(e)}")
                        continue
            else:
                print("未找到職位元素")
                
        except Exception as e:
            print(f"抓取職位數據時出錯: {str(e)}")
        
        return jobs
    
    def save_results_to_file(self):
        """保存測試結果到文件"""
        try:
            results = {
                'test_results': self.test_results,
                'scraped_data': self.scraped_data,
                'performance_metrics': self.performance_metrics,
                'test_timestamp': datetime.now().isoformat()
            }
            
            filename = f"seek_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n測試結果已保存到: {filename}")
            
        except Exception as e:
            print(f"保存結果時出錯: {str(e)}")
    
    def print_comprehensive_results(self):
        """打印全面的測試結果"""
        print("\n" + "="*80)
        print("全面測試結果摘要")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[1] == "通過"])
        failed_tests = total_tests - passed_tests
        
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "成功率: 0%")
        
        print("\n詳細結果:")
        print("-"*80)
        for test_name, status, error in self.test_results:
            status_symbol = "✓" if status == "通過" else "✗"
            print(f"{status_symbol} {test_name}: {status}")
            if error:
                print(f"  錯誤: {error}")
        
        # 性能指標
        if self.performance_metrics:
            print("\n性能指標:")
            print("-"*80)
            for metric, value in self.performance_metrics.items():
                print(f"{metric}: {value}")
        
        # 抓取數據摘要
        if self.scraped_data:
            print("\n數據抓取摘要:")
            print("-"*80)
            print(f"抓取職位數量: {len(self.scraped_data)}")
            print("\n前3個職位:")
            for i, job in enumerate(self.scraped_data[:3]):
                print(f"{i+1}. {job['title']} - {job['company']} ({job['location']})")
    
    async def run_comprehensive_tests(self):
        """運行全面測試"""
        print("開始運行全面Seek網站測試...")
        print("注意: 此測試將打開瀏覽器窗口並模擬真實用戶行為")
        
        await self.test_homepage_interaction()
        await self.test_job_search_and_scraping()
        await self.test_advanced_user_behaviors()
        
        self.print_comprehensive_results()
        self.save_results_to_file()

async def main():
    """主函數"""
    tester = ComprehensiveSeekTest()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())