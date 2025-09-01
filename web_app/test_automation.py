#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSeeker 網頁自動化測試腳本
使用 Playwright 模擬用戶操作，測試網頁功能完整性

Author: JobSeeker Team
Date: 2025-01-02
"""

import json
import os
import time
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import pandas as pd

class JobSeekerWebTester:
    """
    JobSeeker 網頁自動化測試類
    """
    
    def __init__(self, base_url="http://localhost:5000"):
        """
        初始化測試器
        
        Args:
            base_url: 網站基礎URL
        """
        self.base_url = base_url
        self.test_results = []
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
    async def load_test_cases(self, test_file="test_cases.json"):
        """
        載入測試案例
        
        Args:
            test_file: 測試案例檔案路徑
            
        Returns:
            list: 測試案例列表
        """
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_cases', [])
        except FileNotFoundError:
            print(f"測試案例檔案 {test_file} 不存在")
            return []
        except json.JSONDecodeError:
            print(f"測試案例檔案 {test_file} 格式錯誤")
            return []
    
    async def wait_for_element(self, page: Page, selector: str, timeout: int = 10000):
        """
        等待元素出現
        
        Args:
            page: Playwright頁面對象
            selector: CSS選擇器
            timeout: 超時時間（毫秒）
            
        Returns:
            bool: 元素是否出現
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"等待元素 {selector} 超時: {e}")
            return False
    
    async def fill_search_form(self, page: Page, test_case: dict):
        """
        填寫搜索表單
        
        Args:
            page: Playwright頁面對象
            test_case: 測試案例數據
            
        Returns:
            bool: 填寫是否成功
        """
        try:
            # 填寫搜索關鍵字
            await page.fill('#query', test_case['query'])
            
            # 填寫地點（如果有）
            if test_case.get('location'):
                await page.fill('#location', test_case['location'])
            
            # 選擇結果數量
            await page.select_option('#results_wanted', str(test_case['results_wanted']))
            
            # 選擇時間限制（如果有）
            if test_case.get('hours_old'):
                await page.select_option('#hours_old', str(test_case['hours_old']))
            
            return True
        except Exception as e:
            print(f"填寫表單失敗: {e}")
            return False
    
    async def submit_search(self, page: Page):
        """
        提交搜索表單
        
        Args:
            page: Playwright頁面對象
            
        Returns:
            bool: 提交是否成功
        """
        try:
            # 點擊搜索按鈕
            await page.click('#searchForm button[type="submit"]')
            
            # 等待載入動畫出現
            await self.wait_for_element(page, '#loadingSpinner', timeout=5000)
            
            # 等待搜索結果出現或錯誤訊息
            result_appeared = await self.wait_for_element(page, '#searchResults', timeout=120000)
            error_appeared = await self.wait_for_element(page, '.alert-danger', timeout=5000)
            
            return result_appeared or error_appeared
        except Exception as e:
            print(f"提交搜索失敗: {e}")
            return False
    
    async def check_search_results(self, page: Page):
        """
        檢查搜索結果
        
        Args:
            page: Playwright頁面對象
            
        Returns:
            dict: 搜索結果統計
        """
        try:
            # 檢查是否有錯誤訊息
            error_elements = await page.query_selector_all('.alert-danger')
            if error_elements:
                error_text = await error_elements[0].text_content()
                return {
                    'success': False,
                    'error': error_text,
                    'total_jobs': 0,
                    'has_download_buttons': False
                }
            
            # 檢查搜索結果是否顯示
            results_visible = await page.is_visible('#searchResults')
            if not results_visible:
                return {
                    'success': False,
                    'error': '搜索結果區域未顯示',
                    'total_jobs': 0,
                    'has_download_buttons': False
                }
            
            # 獲取職位總數
            total_jobs_element = await page.query_selector('#totalJobs')
            total_jobs = 0
            if total_jobs_element:
                total_jobs_text = await total_jobs_element.text_content()
                total_jobs = int(total_jobs_text.replace(',', '')) if total_jobs_text.isdigit() else 0
            
            # 檢查下載按鈕是否存在
            csv_button_visible = await page.is_visible('#downloadCsv')
            json_button_visible = await page.is_visible('#downloadJson')
            
            # 檢查職位卡片數量
            job_cards = await page.query_selector_all('.job-card')
            displayed_jobs = len(job_cards)
            
            return {
                'success': True,
                'total_jobs': total_jobs,
                'displayed_jobs': displayed_jobs,
                'has_download_buttons': csv_button_visible and json_button_visible,
                'csv_button_visible': csv_button_visible,
                'json_button_visible': json_button_visible
            }
        except Exception as e:
            print(f"檢查搜索結果失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_jobs': 0,
                'has_download_buttons': False
            }
    
    async def test_download_functionality(self, page: Page, test_case_id: str):
        """
        測試下載功能
        
        Args:
            page: Playwright頁面對象
            test_case_id: 測試案例ID
            
        Returns:
            dict: 下載測試結果
        """
        try:
            download_results = {
                'csv_download': False,
                'json_download': False,
                'csv_file_path': None,
                'json_file_path': None
            }
            
            # 測試CSV下載
            if await page.is_visible('#downloadCsv'):
                async with page.expect_download() as download_info:
                    await page.click('#downloadCsv')
                download = await download_info.value
                
                # 保存下載的檔案
                csv_filename = f"test_{test_case_id}_results.csv"
                csv_path = self.downloads_dir / csv_filename
                await download.save_as(csv_path)
                
                download_results['csv_download'] = True
                download_results['csv_file_path'] = str(csv_path)
                
                # 等待一下再進行下一個下載
                await page.wait_for_timeout(2000)
            
            # 測試JSON下載
            if await page.is_visible('#downloadJson'):
                async with page.expect_download() as download_info:
                    await page.click('#downloadJson')
                download = await download_info.value
                
                # 保存下載的檔案
                json_filename = f"test_{test_case_id}_results.json"
                json_path = self.downloads_dir / json_filename
                await download.save_as(json_path)
                
                download_results['json_download'] = True
                download_results['json_file_path'] = str(json_path)
            
            return download_results
        except Exception as e:
            print(f"測試下載功能失敗: {e}")
            return {
                'csv_download': False,
                'json_download': False,
                'error': str(e)
            }
    
    async def run_single_test(self, browser: Browser, test_case: dict):
        """
        執行單個測試案例
        
        Args:
            browser: Playwright瀏覽器對象
            test_case: 測試案例數據
            
        Returns:
            dict: 測試結果
        """
        print(f"\n開始測試: {test_case['name']}")
        
        # 創建新頁面
        page = await browser.new_page()
        
        test_result = {
            'test_id': test_case['id'],
            'test_name': test_case['name'],
            'start_time': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'search_params': {
                'query': test_case['query'],
                'location': test_case.get('location', ''),
                'results_wanted': test_case['results_wanted'],
                'hours_old': test_case.get('hours_old')
            }
        }
        
        try:
            # 訪問網站首頁
            await page.goto(self.base_url, wait_until='networkidle')
            
            # 檢查頁面是否正確載入
            title = await page.title()
            if 'jobseeker' not in title.lower():
                test_result['error'] = f"頁面標題不正確: {title}"
                return test_result
            
            # 填寫搜索表單
            form_filled = await self.fill_search_form(page, test_case)
            if not form_filled:
                test_result['error'] = "填寫搜索表單失敗"
                return test_result
            
            # 提交搜索
            search_submitted = await self.submit_search(page)
            if not search_submitted:
                test_result['error'] = "提交搜索失敗或超時"
                return test_result
            
            # 檢查搜索結果
            search_results = await self.check_search_results(page)
            test_result['search_results'] = search_results
            
            if not search_results['success']:
                test_result['error'] = search_results.get('error', '搜索失敗')
                return test_result
            
            # 如果有搜索結果，測試下載功能
            if search_results['total_jobs'] > 0:
                download_results = await self.test_download_functionality(page, test_case['id'])
                test_result['download_results'] = download_results
            
            test_result['success'] = True
            test_result['end_time'] = datetime.now().isoformat()
            
        except Exception as e:
            test_result['error'] = str(e)
            print(f"測試 {test_case['name']} 發生錯誤: {e}")
        
        finally:
            await page.close()
        
        return test_result
    
    async def run_all_tests(self):
        """
        執行所有測試案例
        
        Returns:
            list: 所有測試結果
        """
        print("開始執行 JobSeeker 網頁自動化測試...")
        
        # 載入測試案例
        test_cases = await self.load_test_cases()
        if not test_cases:
            print("沒有找到測試案例")
            return []
        
        print(f"載入了 {len(test_cases)} 個測試案例")
        
        async with async_playwright() as p:
            # 啟動瀏覽器
            browser = await p.chromium.launch(headless=False)  # 設為 False 可以看到瀏覽器操作
            
            try:
                # 執行每個測試案例
                for test_case in test_cases:
                    result = await self.run_single_test(browser, test_case)
                    self.test_results.append(result)
                    
                    # 在測試之間稍作停頓
                    await asyncio.sleep(2)
                
            finally:
                await browser.close()
        
        return self.test_results
    
    def generate_test_report(self, output_file="test_report.json"):
        """
        生成測試報告
        
        Args:
            output_file: 輸出檔案路徑
        """
        if not self.test_results:
            print("沒有測試結果可以生成報告")
            return
        
        # 統計測試結果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{(successful_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
                'test_date': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n測試報告已保存到: {output_file}")
        print(f"測試總數: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(successful_tests / total_tests * 100):.1f}%")

async def main():
    """
    主函數
    """
    tester = JobSeekerWebTester()
    
    # 執行所有測試
    results = await tester.run_all_tests()
    
    # 生成測試報告
    tester.generate_test_report("web_test_report.json")
    
    return results

if __name__ == "__main__":
    # 執行測試
    asyncio.run(main())