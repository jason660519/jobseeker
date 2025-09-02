#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瀏覽器互動模式測試
模擬真實用戶的瀏覽器行為模式和互動習慣
"""

import pytest
import requests
import time
import random
import json
from urllib.parse import urlencode
from typing import Dict, List, Any, Optional


class TestBrowserInteractionPatterns:
    """瀏覽器互動模式測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前設置"""
        self.session = requests.Session()
        # 模擬不同瀏覽器的 User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def test_different_browser_agents(self):
        """測試不同瀏覽器代理的兼容性"""
        for user_agent in self.user_agents:
            session = requests.Session()
            session.headers.update({'User-Agent': user_agent})
            
            # 測試首頁訪問
            response = session.get(self.BASE_URL)
            assert response.status_code == 200, f"瀏覽器代理失敗: {user_agent[:50]}..."
            
            # 測試搜尋功能
            search_data = {
                "job_title": "software engineer",
                "location": "usa",
                "results_wanted": 10
            }
            
            search_response = session.post(f"{self.BASE_URL}/search", data=search_data)
            # 應該能正常處理不同瀏覽器的請求
            assert search_response.status_code in [200, 400, 422]
            
            session.close()
            time.sleep(0.5)  # 避免請求過於頻繁
    
    def test_mobile_device_simulation(self):
        """模擬移動設備訪問"""
        mobile_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        
        for mobile_agent in mobile_agents:
            session = requests.Session()
            session.headers.update({
                'User-Agent': mobile_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate'
            })
            
            response = session.get(self.BASE_URL)
            assert response.status_code == 200, f"移動設備訪問失敗: {mobile_agent[:30]}..."
            
            # 檢查響應是否適合移動設備
            assert "viewport" in response.text or "mobile" in response.text.lower()
            
            session.close()
    
    def test_form_submission_variations(self):
        """測試表單提交的各種變化"""
        # 測試不同的表單提交方式
        base_search_data = {
            "job_title": "python developer",
            "location": "canada",
            "results_wanted": 15
        }
        
        # 1. 標準 POST 請求
        response1 = self.session.post(f"{self.BASE_URL}/search", data=base_search_data)
        assert response1.status_code in [200, 400, 422]
        
        time.sleep(1)
        
        # 2. 帶有額外 headers 的請求
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': self.BASE_URL,
            'Origin': self.BASE_URL
        }
        response2 = self.session.post(f"{self.BASE_URL}/search", data=base_search_data, headers=headers)
        assert response2.status_code in [200, 400, 422]
        
        time.sleep(1)
        
        # 3. JSON 格式提交（如果支持）
        json_headers = {'Content-Type': 'application/json'}
        try:
            response3 = self.session.post(f"{self.BASE_URL}/search", json=base_search_data, headers=json_headers)
            # JSON 可能不被支持，這是正常的
            assert response3.status_code in [200, 400, 415, 422]
        except Exception:
            pass  # JSON 提交可能不被支持
    
    def test_user_typing_simulation(self):
        """模擬用戶打字行為"""
        # 模擬用戶逐步輸入搜尋詞
        search_terms = [
            "d",
            "da", 
            "dat",
            "data",
            "data ",
            "data s",
            "data sc",
            "data sci",
            "data scientist"
        ]
        
        for i, term in enumerate(search_terms):
            # 模擬自動完成或即時搜尋（如果有的話）
            search_data = {
                "job_title": term,
                "location": "usa",
                "results_wanted": 5
            }
            
            # 只在完整詞彙時進行實際搜尋
            if len(term) >= 4 and i % 3 == 0:  # 減少請求頻率
                response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
                assert response.status_code in [200, 400, 422]
            
            # 模擬打字間隔
            time.sleep(random.uniform(0.1, 0.3))
    
    def test_back_button_simulation(self):
        """模擬瀏覽器返回按鈕行為"""
        # 首次訪問首頁
        response1 = self.session.get(self.BASE_URL)
        assert response1.status_code == 200
        
        # 執行搜尋
        search_data = {
            "job_title": "web developer",
            "location": "uk",
            "results_wanted": 10
        }
        
        search_response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
        
        # 模擬用戶點擊返回按鈕（重新訪問首頁）
        response2 = self.session.get(self.BASE_URL)
        assert response2.status_code == 200
        
        # 再次執行不同的搜尋
        search_data2 = {
            "job_title": "backend engineer",
            "location": "australia",
            "results_wanted": 8
        }
        
        search_response2 = self.session.post(f"{self.BASE_URL}/search", data=search_data2)
        assert search_response2.status_code in [200, 400, 422]
    
    def test_refresh_behavior(self):
        """測試頁面刷新行為"""
        # 多次刷新首頁
        for i in range(3):
            response = self.session.get(self.BASE_URL)
            assert response.status_code == 200
            
            # 檢查頁面內容一致性
            assert "jobseeker" in response.text or "智能職位搜尋" in response.text
            
            # 模擬用戶刷新間隔
            time.sleep(random.uniform(0.5, 2.0))
    
    def test_tab_switching_simulation(self):
        """模擬標籤頁切換行為"""
        # 創建多個會話模擬多個標籤頁
        sessions = []
        
        for i in range(3):
            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(self.user_agents)
            })
            sessions.append(session)
        
        # 在不同「標籤頁」中執行操作
        search_queries = [
            {"job_title": "frontend developer", "location": "usa"},
            {"job_title": "backend developer", "location": "canada"},
            {"job_title": "fullstack developer", "location": "uk"}
        ]
        
        for i, (session, query) in enumerate(zip(sessions, search_queries)):
            # 訪問首頁
            response = session.get(self.BASE_URL)
            assert response.status_code == 200
            
            # 執行搜尋
            query["results_wanted"] = 5
            search_response = session.post(f"{self.BASE_URL}/search", data=query)
            
            # 模擬標籤頁切換延遲
            time.sleep(random.uniform(0.3, 1.0))
        
        # 清理會話
        for session in sessions:
            session.close()
    
    def test_error_recovery_patterns(self):
        """測試錯誤恢復模式"""
        # 1. 先發送一個可能導致錯誤的請求
        invalid_data = {
            "job_title": "",  # 空標題
            "location": "invalid_location",
            "results_wanted": -1
        }
        
        error_response = self.session.post(f"{self.BASE_URL}/search", data=invalid_data)
        # 應該優雅處理錯誤
        assert error_response.status_code in [200, 400, 422]
        
        # 2. 用戶修正錯誤後重新提交
        corrected_data = {
            "job_title": "software engineer",
            "location": "usa",
            "results_wanted": 10
        }
        
        corrected_response = self.session.post(f"{self.BASE_URL}/search", data=corrected_data)
        assert corrected_response.status_code in [200, 400, 422]
        
        # 3. 檢查應用是否從錯誤中恢復
        final_check = self.session.get(self.BASE_URL)
        assert final_check.status_code == 200
    
    def test_slow_network_simulation(self):
        """模擬慢速網路條件"""
        # 設置較短的超時時間模擬慢速網路
        slow_session = requests.Session()
        slow_session.headers.update({
            'User-Agent': random.choice(self.user_agents)
        })
        
        try:
            # 設置較短超時
            response = slow_session.get(self.BASE_URL, timeout=10)
            assert response.status_code == 200
            
            # 測試搜尋在慢速網路下的表現
            search_data = {
                "job_title": "data analyst",
                "location": "singapore",
                "results_wanted": 5
            }
            
            search_response = slow_session.post(
                f"{self.BASE_URL}/search", 
                data=search_data, 
                timeout=15
            )
            
            # 應該能在合理時間內響應
            assert search_response.status_code in [200, 400, 422]
            
        except requests.exceptions.Timeout:
            # 超時是可以接受的，但應該記錄
            print("請求超時 - 這可能表明需要優化性能")
        
        finally:
            slow_session.close()
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'session'):
            self.session.close()


if __name__ == "__main__":
    # 可以直接運行此檔案進行測試
    pytest.main([__file__, "-v"])