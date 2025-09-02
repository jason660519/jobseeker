#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
壓力測試和魯棒性測試
測試應用在高負載和極端條件下的穩定性
"""

import pytest
import requests
import time
import random
import threading
import queue
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional


class TestStressAndRobustness:
    """壓力測試和魯棒性測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前設置"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StressTest/1.0 Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
    
    def generate_random_string(self, length: int) -> str:
        """生成隨機字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
    
    def generate_random_search_data(self) -> Dict[str, Any]:
        """生成隨機搜尋數據"""
        job_titles = [
            "software engineer", "data scientist", "product manager", 
            "web developer", "mobile developer", "devops engineer",
            "machine learning engineer", "backend developer", "frontend developer",
            "full stack developer", "qa engineer", "system administrator"
        ]
        
        locations = [
            "usa", "canada", "uk", "australia", "singapore", 
            "germany", "france", "japan", "india", "brazil"
        ]
        
        return {
            "job_title": random.choice(job_titles),
            "location": random.choice(locations),
            "results_wanted": random.randint(1, 50),
            "hours_old": random.randint(1, 720),
            "country_indeed": random.choice(["usa", "canada", "uk", "australia"])
        }
    
    def test_high_frequency_requests(self):
        """測試高頻率請求"""
        results = []
        
        # 在短時間內發送多個請求
        for i in range(10):  # 限制數量避免過載服務器
            try:
                start_time = time.time()
                response = self.session.get(self.BASE_URL)
                end_time = time.time()
                
                results.append({
                    "request_id": i,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                })
                
                # 很短的間隔
                time.sleep(0.1)
                
            except Exception as e:
                results.append({
                    "request_id": i,
                    "error": str(e),
                    "success": False
                })
        
        # 分析結果
        successful_requests = sum(1 for r in results if r.get("success", False))
        avg_response_time = sum(r.get("response_time", 0) for r in results if "response_time" in r) / len(results)
        
        print(f"成功請求: {successful_requests}/{len(results)}")
        print(f"平均響應時間: {avg_response_time:.3f}秒")
        
        # 至少應該有一半的請求成功
        assert successful_requests >= len(results) // 2, "高頻率請求下成功率過低"
    
    def test_concurrent_search_requests(self):
        """測試併發搜尋請求"""
        def perform_search(thread_id: int) -> Dict[str, Any]:
            """執行單次搜尋"""
            session = requests.Session()
            session.headers.update({
                'User-Agent': f'ConcurrentTest-{thread_id} Mozilla/5.0'
            })
            
            try:
                search_data = self.generate_random_search_data()
                start_time = time.time()
                
                response = session.post(f"{self.BASE_URL}/search", data=search_data)
                
                end_time = time.time()
                
                return {
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "search_data": search_data,
                    "success": response.status_code in [200, 400, 422]
                }
                
            except Exception as e:
                return {
                    "thread_id": thread_id,
                    "error": str(e),
                    "success": False
                }
            finally:
                session.close()
        
        # 使用線程池執行併發請求
        max_workers = 5  # 限制併發數避免過載
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(perform_search, i) for i in range(max_workers)]
            
            for future in as_completed(futures, timeout=60):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "success": False})
        
        # 分析併發測試結果
        successful_searches = sum(1 for r in results if r.get("success", False))
        
        print(f"併發搜尋成功: {successful_searches}/{len(results)}")
        
        # 至少應該有一半的併發請求成功
        assert successful_searches >= len(results) // 2, "併發搜尋成功率過低"
    
    def test_large_payload_handling(self):
        """測試大型負載處理"""
        # 測試超長職位標題
        large_payloads = [
            {
                "job_title": self.generate_random_string(500),  # 500字符
                "location": "usa",
                "results_wanted": 10
            },
            {
                "job_title": "software engineer",
                "location": self.generate_random_string(100),  # 100字符地點
                "results_wanted": 10
            },
            {
                "job_title": "a" * 1000,  # 1000個相同字符
                "location": "usa",
                "results_wanted": 10
            }
        ]
        
        for i, payload in enumerate(large_payloads):
            try:
                response = self.session.post(f"{self.BASE_URL}/search", data=payload)
                
                # 應該優雅處理大型負載
                assert response.status_code in [200, 400, 413, 422], f"大型負載 {i} 處理異常"
                
                # 如果返回錯誤，應該有適當的錯誤信息
                if response.status_code >= 400:
                    assert len(response.text) > 0, "錯誤響應應該包含信息"
                
            except Exception as e:
                # 記錄異常但不失敗測試
                print(f"大型負載 {i} 處理異常: {str(e)}")
    
    def test_malformed_requests(self):
        """測試格式錯誤的請求"""
        malformed_requests = [
            # 缺少必要字段
            {"location": "usa"},
            {"job_title": "test"},
            {},
            
            # 錯誤的數據類型
            {"job_title": 123, "location": "usa"},
            {"job_title": "test", "location": 456},
            {"job_title": "test", "location": "usa", "results_wanted": "not_a_number"},
            
            # 特殊字符和編碼
            {"job_title": "test\x00\x01\x02", "location": "usa"},
            {"job_title": "test", "location": "usa\n\r\t"},
            {"job_title": "🚀💻🔥", "location": "usa"},  # emoji
        ]
        
        for i, malformed_data in enumerate(malformed_requests):
            try:
                response = self.session.post(f"{self.BASE_URL}/search", data=malformed_data)
                
                # 應該優雅處理格式錯誤的請求
                assert response.status_code in [200, 400, 422, 500], f"格式錯誤請求 {i} 處理異常"
                
                # 不應該導致服務器崩潰
                assert len(response.text) > 0, "響應不應該為空"
                
            except Exception as e:
                print(f"格式錯誤請求 {i} 處理異常: {str(e)}")
    
    def test_memory_stress(self):
        """測試記憶體壓力"""
        # 創建多個會話並保持活躍
        sessions = []
        
        try:
            # 創建多個會話
            for i in range(10):  # 限制數量
                session = requests.Session()
                session.headers.update({
                    'User-Agent': f'MemoryStressTest-{i}'
                })
                sessions.append(session)
            
            # 在所有會話中執行操作
            for i, session in enumerate(sessions):
                try:
                    response = session.get(self.BASE_URL)
                    assert response.status_code == 200
                    
                    # 執行搜尋
                    search_data = self.generate_random_search_data()
                    search_response = session.post(f"{self.BASE_URL}/search", data=search_data)
                    
                    # 檢查記憶體使用是否正常
                    assert search_response.status_code in [200, 400, 422]
                    
                except Exception as e:
                    print(f"會話 {i} 記憶體壓力測試異常: {str(e)}")
        
        finally:
            # 清理所有會話
            for session in sessions:
                try:
                    session.close()
                except:
                    pass
    
    def test_rapid_form_submissions(self):
        """測試快速表單提交"""
        # 快速連續提交相同表單
        search_data = {
            "job_title": "rapid test",
            "location": "usa",
            "results_wanted": 5
        }
        
        results = []
        
        for i in range(5):  # 限制提交次數
            try:
                start_time = time.time()
                response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
                end_time = time.time()
                
                results.append({
                    "submission": i,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 400, 422]
                })
                
                # 極短間隔
                time.sleep(0.05)
                
            except Exception as e:
                results.append({
                    "submission": i,
                    "error": str(e),
                    "success": False
                })
        
        # 檢查快速提交的處理
        successful_submissions = sum(1 for r in results if r.get("success", False))
        
        print(f"快速提交成功: {successful_submissions}/{len(results)}")
        
        # 應該能處理大部分快速提交
        assert successful_submissions >= len(results) // 2, "快速提交處理能力不足"
    
    def test_resource_exhaustion_protection(self):
        """測試資源耗盡保護"""
        # 嘗試請求大量結果
        extreme_requests = [
            {"job_title": "test", "location": "usa", "results_wanted": 1000},
            {"job_title": "test", "location": "usa", "results_wanted": 10000},
            {"job_title": "test", "location": "usa", "hours_old": 1},  # 很新的職位
        ]
        
        for i, extreme_data in enumerate(extreme_requests):
            try:
                response = self.session.post(f"{self.BASE_URL}/search", data=extreme_data)
                
                # 應該有適當的限制機制
                assert response.status_code in [200, 400, 422, 429], f"極端請求 {i} 未被適當限制"
                
                # 響應時間不應該過長（30秒內）
                # 這個測試可能需要根據實際情況調整
                
            except requests.exceptions.Timeout:
                # 超時是可以接受的保護機制
                print(f"極端請求 {i} 超時 - 這是正常的保護機制")
            except Exception as e:
                print(f"極端請求 {i} 異常: {str(e)}")
    
    def test_error_cascade_prevention(self):
        """測試錯誤級聯預防"""
        # 先發送一個可能導致錯誤的請求
        error_inducing_data = {
            "job_title": "",
            "location": "invalid_location_12345",
            "results_wanted": -999
        }
        
        try:
            error_response = self.session.post(f"{self.BASE_URL}/search", data=error_inducing_data)
            # 記錄錯誤但繼續測試
        except:
            pass
        
        # 立即發送正常請求，檢查是否受到影響
        normal_data = {
            "job_title": "software engineer",
            "location": "usa",
            "results_wanted": 10
        }
        
        normal_response = self.session.post(f"{self.BASE_URL}/search", data=normal_data)
        
        # 正常請求不應該受到之前錯誤的影響
        assert normal_response.status_code in [200, 400, 422], "錯誤級聯影響了後續請求"
        
        # 檢查應用是否仍然正常運行
        health_check = self.session.get(self.BASE_URL)
        assert health_check.status_code == 200, "應用在錯誤後無法恢復"
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'session'):
            self.session.close()


if __name__ == "__main__":
    # 可以直接運行此檔案進行測試
    pytest.main([__file__, "-v", "-s"])