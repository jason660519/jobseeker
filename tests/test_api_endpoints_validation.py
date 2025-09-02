#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 端點和數據驗證測試

本測試檔案專注於驗證 Web 應用的 API 端點功能、數據格式和響應正確性。
測試包括搜尋 API、數據格式驗證、錯誤處理等關鍵功能。

作者: AI Assistant
創建時間: 2025年1月
"""

import pytest
import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any


class TestAPIEndpointsValidation:
    """API 端點和數據驗證測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前的設置"""
        self.session = requests.Session()
        # 設置合理的超時時間
        self.session.timeout = 30
        
    def teardown_method(self):
        """測試後的清理"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def test_search_api_basic_functionality(self):
        """測試搜尋 API 的基本功能"""
        search_data = {
            'query': 'python developer',
            'location': 'taipei',
            'results_wanted': '25',
            'hours_old': '168'
        }
        
        response = self.session.post(
            f"{self.BASE_URL}/search",
            data=search_data
        )
        
        assert response.status_code == 200
        
        # 檢查響應內容 - API 返回 JSON 格式
        response_data = response.json()
        assert response_data.get('success', False), "API 應返回成功狀態"
        assert 'jobs' in response_data, "響應應包含職位列表"
        
        # 檢查是否有錯誤信息
        assert not response_data.get('error', False), "響應不應包含錯誤信息"
    
    def test_search_api_data_validation(self):
        """測試搜尋 API 的數據驗證"""
        # 測試各種有效的搜尋參數組合
        test_cases = [
            {
                'query': 'data scientist',
                'location': 'taiwan',
                'results_wanted': '10'
            },
            {
                'query': 'software engineer',
                'location': 'taipei',
                'results_wanted': '25'
            },
            {
                'query': 'project manager',
                'location': 'singapore',
                'results_wanted': '10'
            }
        ]
        
        for i, search_data in enumerate(test_cases):
            response = self.session.post(
                f"{self.BASE_URL}/search",
                data=search_data
            )
            
            assert response.status_code == 200, f"Test case {i+1} failed"
            
            # 添加請求間隔，避免過於頻繁的請求
            if i < len(test_cases) - 1:
                time.sleep(2)
    
    def test_invalid_search_parameters(self):
        """測試無效搜尋參數的處理"""
        invalid_cases = [
            # 空的搜尋詞
            {
                'query': '',
                'location': 'taipei'
            },
            # 過大的結果數量
            {
                'query': 'developer',
                'location': 'taipei',
                'results_wanted': '1000'
            },
            # 負數結果數量
            {
                'query': 'developer',
                'location': 'taipei',
                'results_wanted': '-5'
            },
            # 無效的時間範圍
            {
                'query': 'developer',
                'location': 'taipei',
                'hours_old': '-24'
            }
        ]
        
        for i, search_data in enumerate(invalid_cases):
            response = self.session.post(
                f"{self.BASE_URL}/search",
                data=search_data
            )
            
            # 應用應該能處理無效輸入，不應該返回 500 錯誤
            assert response.status_code != 500, f"Invalid case {i+1} caused server error"
            
            # 檢查是否有適當的錯誤處理
            content = response.text.lower()
            # 應該包含錯誤信息或重新顯示表單
            assert ("error" in content or "錯誤" in content or 
                   "form" in content or "搜尋" in content), f"Invalid case {i+1} not handled properly"
    
    def test_search_response_structure(self):
        """測試搜尋響應的結構和內容"""
        search_data = {
            'query': 'python',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        response = self.session.post(
            f"{self.BASE_URL}/search",
            data=search_data
        )
        
        assert response.status_code == 200
        content = response.text
        
        # 檢查響應格式 - API 返回 JSON 格式
        response_data = response.json()
        assert 'success' in response_data, "響應應包含成功狀態"
        assert 'jobs' in response_data, "響應應包含職位數據"
        assert 'total_jobs' in response_data, "響應應包含職位總數"
        
        # 檢查是否包含搜尋相關的內容
        if response_data.get('success'):
            # 檢查搜尋參數是否在響應中
            assert 'search_params' in response_data or 'query' in str(response_data), "響應應包含搜尋相關資訊"
            
            # 檢查職位數據結構
            jobs = response_data.get('jobs', [])
            if jobs:
                # 檢查職位數據是否包含必要字段
                first_job = jobs[0] if isinstance(jobs, list) else jobs
                assert isinstance(first_job, dict), "職位數據應為字典格式"
    
    def test_concurrent_api_requests(self):
        """測試併發 API 請求的處理"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(thread_id):
            """執行單個 API 請求"""
            try:
                search_data = {
                    'query': f'developer {thread_id}',
                    'location': 'taipei',
                    'results_wanted': '10'
                }
                
                response = requests.post(
                    f"{self.BASE_URL}/search",
                    data=search_data,
                    timeout=30
                )
                
                success = False
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        success = response_data.get('success', False)
                    except:
                        pass  # JSON 解析失敗
                
                results.put({
                    'thread_id': thread_id,
                    'status_code': response.status_code,
                    'success': success
                })
                
            except Exception as e:
                results.put({
                    'thread_id': thread_id,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                })
        
        # 創建 3 個併發請求
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join(timeout=60)  # 60秒超時
        
        # 收集結果
        all_results = []
        while not results.empty():
            all_results.append(results.get())
        
        # 驗證結果
        assert len(all_results) == 3, "Not all concurrent requests completed"
        
        successful_requests = sum(1 for result in all_results if result['success'])
        
        # 至少應該有一個請求成功（考慮到網路延遲和伺服器負載）
        assert successful_requests >= 1, f"Only {successful_requests}/3 concurrent requests succeeded"
    
    def test_search_performance_metrics(self):
        """測試搜尋性能指標"""
        search_data = {
            'query': 'software engineer',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        # 測量響應時間
        start_time = time.time()
        
        response = self.session.post(
            f"{self.BASE_URL}/search",
            data=search_data
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        
        # 響應時間應該在合理範圍內（120秒內，考慮到搜尋可能需要較長時間）
        assert response_time < 120, f"Response time too slow: {response_time:.2f} seconds"
        
        # 記錄性能指標
        print(f"\nPerformance metrics:")
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Response size: {len(response.content)} bytes")
    
    def test_error_handling_robustness(self):
        """測試錯誤處理的魯棒性"""
        # 測試各種可能導致錯誤的情況
        error_cases = [
            # 特殊字符
            {
                'query': '!@#$%^&*()',
                'location': 'taipei'
            },
            # 非常長的搜尋詞
            {
                'query': 'a' * 1000,
                'location': 'taipei'
            },
            # SQL 注入嘗試
            {
                'query': "'; DROP TABLE jobs; --",
                'location': 'taipei'
            },
            # XSS 嘗試
            {
                'query': '<script>alert("xss")</script>',
                'location': 'taipei'
            }
        ]
        
        for i, search_data in enumerate(error_cases):
            response = self.session.post(
                f"{self.BASE_URL}/search",
                data=search_data
            )
            
            # 應用不應該崩潰
            assert response.status_code != 500, f"Error case {i+1} caused server crash"
            
            # 響應應該是有效的 JSON
            try:
                response_data = response.json()
                # 錯誤情況下應該有適當的錯誤標記
                if response.status_code == 200:
                    assert not response_data.get('success', True) or response_data.get('error'), f"Error case {i+1} should indicate failure"
            except:
                # JSON 解析失敗也是可接受的錯誤響應
                pass
            
            # 不應該執行惡意腳本
            if "<script>" in search_data['query']:
                try:
                    response_data = response.json()
                    # 檢查 JSON 響應中是否包含未轉義的腳本
                    response_str = str(response_data)
                    assert "<script>" not in response_str, "XSS vulnerability detected in JSON response"
                except:
                    # 如果不是 JSON，檢查原始內容
                    content = response.text
                    assert "<script>" not in content, "XSS vulnerability detected"
    
    def test_session_handling(self):
        """測試會話處理"""
        # 測試會話是否正確維護
        response1 = self.session.get(self.BASE_URL)
        assert response1.status_code == 200
        
        # 檢查是否設置了會話 cookie
        cookies_before = len(self.session.cookies)
        
        # 執行搜尋
        search_data = {
            'query': 'test',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        response2 = self.session.post(
            f"{self.BASE_URL}/search",
            data=search_data
        )
        
        assert response2.status_code == 200
        
        # 再次訪問首頁，檢查會話是否保持
        response3 = self.session.get(self.BASE_URL)
        assert response3.status_code == 200
        
        # 會話應該保持一致
        cookies_after = len(self.session.cookies)
        assert cookies_after >= cookies_before, "Session not properly maintained"


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "-s"])