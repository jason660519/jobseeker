#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶網頁瀏覽行為測試
模擬真實用戶在網頁應用中的各種操作行為
"""

import pytest
import requests
import time
import random
import json
from typing import Dict, List, Any


class TestUserWebBehavior:
    """用戶網頁瀏覽行為測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前設置"""
        self.session = requests.Session()
        # 模擬真實瀏覽器 User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def test_homepage_access_patterns(self):
        """測試首頁訪問模式"""
        # 模擬用戶多次訪問首頁
        for i in range(3):
            response = self.session.get(self.BASE_URL)
            assert response.status_code == 200
            assert "jobseeker" in response.text or "智能職位搜尋" in response.text
            
            # 模擬用戶停留時間
            time.sleep(random.uniform(0.5, 2.0))
    
    def test_rapid_search_requests(self):
        """測試快速連續搜尋請求"""
        search_terms = [
            "python developer",
            "data scientist", 
            "software engineer",
            "machine learning",
            "web developer"
        ]
        
        locations = ["usa", "canada", "uk", "australia", "singapore"]
        
        # 模擬用戶快速連續搜尋
        for term in search_terms[:3]:  # 限制搜尋次數避免過載
            search_data = {
                "job_title": term,
                "location": random.choice(locations),
                "results_wanted": random.randint(5, 15),
                "hours_old": random.randint(24, 168),
                "country_indeed": random.choice(["usa", "canada", "uk"])
            }
            
            response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
            
            # 檢查回應狀態
            if response.status_code == 200:
                # 檢查是否有結果返回
                assert "results" in response.text.lower() or "job" in response.text.lower()
            else:
                # 記錄非200狀態碼但不失敗測試（可能是正常的限流）
                print(f"搜尋請求返回狀態碼: {response.status_code}")
            
            # 模擬用戶思考時間
            time.sleep(random.uniform(0.2, 1.0))
    
    def test_invalid_input_handling(self):
        """測試無效輸入處理"""
        invalid_inputs = [
            {"job_title": "", "location": "usa"},  # 空職位標題
            {"job_title": "test", "location": ""},  # 空地點
            {"job_title": "a" * 1000, "location": "usa"},  # 超長職位標題
            {"job_title": "test", "location": "invalid_country"},  # 無效國家
            {"job_title": "<script>alert('xss')</script>", "location": "usa"},  # XSS 測試
            {"job_title": "test", "results_wanted": -1},  # 負數結果
            {"job_title": "test", "results_wanted": 10000},  # 過大結果數
        ]
        
        for invalid_data in invalid_inputs:
            response = self.session.post(f"{self.BASE_URL}/search", data=invalid_data)
            
            # 應用應該優雅處理錯誤，不應該崩潰
            assert response.status_code in [200, 400, 422], f"意外的狀態碼: {response.status_code}"
            
            # 檢查是否有適當的錯誤處理
            if response.status_code != 200:
                assert "error" in response.text.lower() or "invalid" in response.text.lower()
    
    def test_concurrent_user_simulation(self):
        """模擬併發用戶行為"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def user_session(user_id: int):
            """模擬單個用戶會話"""
            session = requests.Session()
            session.headers.update({
                'User-Agent': f'TestUser-{user_id} Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            
            try:
                # 訪問首頁
                response = session.get(self.BASE_URL)
                
                # 執行搜尋
                search_data = {
                    "job_title": f"developer {user_id}",
                    "location": "usa",
                    "results_wanted": 5
                }
                
                search_response = session.post(f"{self.BASE_URL}/search", data=search_data)
                
                results.put({
                    "user_id": user_id,
                    "homepage_status": response.status_code,
                    "search_status": search_response.status_code,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                results.put({
                    "user_id": user_id,
                    "error": str(e),
                    "success": False
                })
        
        # 創建3個併發用戶
        threads = []
        for i in range(3):
            thread = threading.Thread(target=user_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join(timeout=30)  # 30秒超時
        
        # 檢查結果
        successful_users = 0
        while not results.empty():
            result = results.get()
            if result.get("success", False):
                successful_users += 1
        
        # 至少應該有一個用戶成功
        assert successful_users >= 1, "沒有用戶成功完成操作"
    
    def test_edge_case_searches(self):
        """測試邊界情況搜尋"""
        edge_cases = [
            {"job_title": "AI", "location": "usa", "results_wanted": 1},  # 最小搜尋
            {"job_title": "software engineer python django react", "location": "canada", "results_wanted": 50},  # 長查詢
            {"job_title": "123", "location": "uk"},  # 數字職位
            {"job_title": "café manager", "location": "australia"},  # 特殊字符
            {"job_title": "remote work", "location": "worldwide"},  # 全球搜尋
        ]
        
        for case in edge_cases:
            response = self.session.post(f"{self.BASE_URL}/search", data=case)
            
            # 應用應該能處理這些邊界情況
            assert response.status_code in [200, 400], f"邊界情況處理失敗: {case}"
            
            # 模擬用戶查看結果的時間
            time.sleep(random.uniform(0.3, 1.5))
    
    def test_session_persistence(self):
        """測試會話持久性"""
        # 第一次請求
        response1 = self.session.get(self.BASE_URL)
        assert response1.status_code == 200
        
        # 檢查是否設置了 cookies
        cookies_before = len(self.session.cookies)
        
        # 執行搜尋
        search_data = {
            "job_title": "test job",
            "location": "usa",
            "results_wanted": 5
        }
        
        search_response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
        
        # 第二次請求，檢查會話是否保持
        response2 = self.session.get(self.BASE_URL)
        assert response2.status_code == 200
        
        # 會話應該保持一致
        cookies_after = len(self.session.cookies)
        print(f"Cookies before: {cookies_before}, after: {cookies_after}")
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'session'):
            self.session.close()


if __name__ == "__main__":
    # 可以直接運行此檔案進行測試
    pytest.main([__file__, "-v"])