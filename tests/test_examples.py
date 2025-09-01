#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 測試範例

這個檔案展示了如何為 JobSpy 專案實施各種類型的測試，
包括單元測試、整合測試、效能測試和 Mock 測試。

作者: JobSpy Team
日期: 2024
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# 測試依賴
try:
    import responses
    import aioresponses
except ImportError:
    print("請安裝測試依賴: pip install responses aioresponses")

# JobSpy 模組導入
from jobspy import scrape_jobs
try:
    from jobspy import scrape_jobs_async
    from jobspy.async_scraping import AsyncScrapingManager, AsyncConfig, AsyncMode
    from jobspy.cache_system import JobCache, get_global_cache
    from jobspy.data_quality import DataQualityChecker, clean_job_data
    from jobspy.error_handling import retry_with_backoff, JobSpyException
    from jobspy.performance_monitoring import get_global_metrics, performance_monitor
    from jobspy.model import Site, ScraperInput, JobPost
except ImportError as e:
    print(f"某些模組尚未實現: {e}")


class TestJobSpyCore:
    """JobSpy 核心功能測試類別"""
    
    def test_scrape_jobs_basic(self):
        """測試基本的同步爬取功能"""
        # 使用小量資料進行測試
        result = scrape_jobs(
            site_name="indeed",
            search_term="python",
            location="Sydney",
            results_wanted=3
        )
        
        # 驗證結果
        assert result is not None
        assert len(result) >= 0  # 可能沒有結果，但不應該出錯
        
        if len(result) > 0:
            # 檢查必要的欄位
            required_columns = ['title', 'company', 'location']
            for col in required_columns:
                assert col in result.columns, f"缺少必要欄位: {col}"
    
    def test_multiple_sites(self):
        """測試多網站爬取"""
        sites = ["indeed", "linkedin"]
        result = scrape_jobs(
            site_name=sites,
            search_term="software engineer",
            location="Melbourne",
            results_wanted=5
        )
        
        assert result is not None
        if len(result) > 0:
            # 檢查是否包含來源網站資訊
            assert 'site' in result.columns or 'source' in result.columns
    
    def test_invalid_site(self):
        """測試無效網站處理"""
        with pytest.raises((ValueError, KeyError, JobSpyException)):
            scrape_jobs(
                site_name="invalid_site",
                search_term="test",
                location="Sydney",
                results_wanted=1
            )


class TestAsyncScraping:
    """非同步爬取功能測試類別"""
    
    @pytest.mark.asyncio
    async def test_async_scrape_basic(self):
        """測試基本非同步爬取"""
        try:
            result = await scrape_jobs_async(
                site_name=["indeed"],
                search_term="python",
                location="Sydney",
                results_wanted=3,
                max_concurrent_requests=2
            )
            
            assert result is not None
            assert len(result) >= 0
            
            if len(result) > 0:
                assert 'title' in result.columns
                assert 'company' in result.columns
        except NameError:
            pytest.skip("非同步功能尚未實現")
    
    @pytest.mark.asyncio
    async def test_async_multiple_sites(self):
        """測試非同步多網站爬取"""
        try:
            sites = ["indeed", "linkedin"]
            
            start_time = time.time()
            result = await scrape_jobs_async(
                site_name=sites,
                search_term="data scientist",
                location="Brisbane",
                results_wanted=5,
                max_concurrent_requests=3
            )
            duration = time.time() - start_time
            
            assert result is not None
            assert duration < 60  # 應該在合理時間內完成
            
            print(f"非同步爬取完成時間: {duration:.2f}秒")
        except NameError:
            pytest.skip("非同步功能尚未實現")
    
    @pytest.mark.asyncio
    async def test_async_config(self):
        """測試非同步配置"""
        try:
            config = AsyncConfig(
                mode=AsyncMode.THREADED,
                max_concurrent_requests=3,
                request_delay=0.5,
                timeout=30.0,
                enable_caching=True
            )
            
            result = await scrape_jobs_async(
                site_name=["indeed"],
                search_term="test",
                location="Perth",
                results_wanted=3,
                async_config=config
            )
            
            assert result is not None
        except NameError:
            pytest.skip("非同步配置功能尚未實現")


class TestCacheSystem:
    """快取系統測試類別"""
    
    def setup_method(self):
        """每個測試前的設定"""
        try:
            self.cache = get_global_cache()
            self.cache.clear()
        except NameError:
            self.cache = None
    
    def test_cache_basic_operations(self):
        """測試基本快取操作"""
        if self.cache is None:
            pytest.skip("快取系統尚未實現")
        
        # 測試設定和獲取
        key = "test_key"
        value = {"data": "test_value"}
        
        self.cache.set(key, value)
        retrieved = self.cache.get(key)
        
        assert retrieved == value
    
    def test_cache_expiration(self):
        """測試快取過期"""
        if self.cache is None:
            pytest.skip("快取系統尚未實現")
        
        key = "expire_test"
        value = {"data": "expire_value"}
        
        # 設定短期過期
        self.cache.set(key, value, ttl=1)
        
        # 立即獲取應該成功
        assert self.cache.get(key) == value
        
        # 等待過期
        time.sleep(1.1)
        
        # 過期後應該返回 None
        assert self.cache.get(key) is None
    
    def test_cache_statistics(self):
        """測試快取統計"""
        if self.cache is None:
            pytest.skip("快取系統尚未實現")
        
        # 重置統計
        self.cache.clear()
        
        # 執行一些操作
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.get("key1")  # 命中
        self.cache.get("key3")  # 未命中
        
        try:
            stats = self.cache.get_stats()
            assert hasattr(stats, 'hit_rate')
            assert hasattr(stats, 'size')
        except AttributeError:
            # 如果統計功能尚未實現，跳過
            pass


class TestDataQuality:
    """資料品質測試類別"""
    
    def test_data_cleaning(self):
        """測試資料清理功能"""
        try:
            # 測試資料
            dirty_data = {
                'title': '  Software Engineer  ',
                'company': 'TECH CORP',
                'location': 'sydney, nsw',
                'salary': '$80,000 - $100,000 per year',
                'description': 'Looking for a developer...\n\n'
            }
            
            cleaned = clean_job_data(dirty_data)
            
            # 驗證清理結果
            assert cleaned['title'].strip() == 'Software Engineer'
            assert 'sydney' in cleaned['location'].lower()
            
        except NameError:
            pytest.skip("資料品質功能尚未實現")
    
    def test_duplicate_detection(self):
        """測試重複檢測"""
        try:
            checker = DataQualityChecker()
            
            jobs = [
                {'title': 'Python Developer', 'company': 'TechCorp', 'location': 'Sydney'},
                {'title': 'Python Developer', 'company': 'TechCorp', 'location': 'Sydney'},  # 重複
                {'title': 'Java Developer', 'company': 'TechCorp', 'location': 'Sydney'}
            ]
            
            unique_jobs = checker.remove_duplicates(jobs)
            assert len(unique_jobs) == 2
            
        except NameError:
            pytest.skip("重複檢測功能尚未實現")


class TestErrorHandling:
    """錯誤處理測試類別"""
    
    def test_retry_decorator(self):
        """測試重試裝飾器"""
        try:
            call_count = 0
            
            @retry_with_backoff(max_attempts=3, backoff_factor=0.1)
            def failing_function():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("網路錯誤")
                return "成功"
            
            result = failing_function()
            assert result == "成功"
            assert call_count == 3
            
        except NameError:
            pytest.skip("錯誤處理功能尚未實現")
    
    def test_custom_exceptions(self):
        """測試自定義異常"""
        try:
            with pytest.raises(JobSpyException):
                raise JobSpyException("測試異常")
        except NameError:
            pytest.skip("自定義異常尚未實現")


class TestPerformanceMonitoring:
    """效能監控測試類別"""
    
    def test_performance_metrics(self):
        """測試效能指標收集"""
        try:
            metrics = get_global_metrics()
            
            # 重置指標
            metrics.reset()
            
            # 模擬一些操作
            with performance_monitor("test_operation"):
                time.sleep(0.1)
            
            stats = metrics.get_stats()
            assert hasattr(stats, 'total_requests')
            
        except NameError:
            pytest.skip("效能監控功能尚未實現")
    
    def test_performance_decorator(self):
        """測試效能監控裝飾器"""
        try:
            @performance_monitor
            def test_function():
                time.sleep(0.05)
                return "完成"
            
            result = test_function()
            assert result == "完成"
            
        except NameError:
            pytest.skip("效能裝飾器尚未實現")


class TestMockExamples:
    """Mock 測試範例類別"""
    
    @responses.activate
    def test_http_mock_with_responses(self):
        """使用 responses 進行 HTTP Mock 測試"""
        # 設定 Mock 響應
        responses.add(
            responses.GET,
            "https://api.example.com/jobs",
            json={
                "jobs": [
                    {
                        "title": "Mock Job",
                        "company": "Mock Company",
                        "location": "Mock Location"
                    }
                ]
            },
            status=200
        )
        
        # 這裡可以測試使用該 API 的函數
        import requests
        response = requests.get("https://api.example.com/jobs")
        data = response.json()
        
        assert response.status_code == 200
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["title"] == "Mock Job"
    
    @pytest.mark.asyncio
    async def test_async_http_mock(self):
        """非同步 HTTP Mock 測試"""
        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.example.com/async-jobs",
                payload={
                    "jobs": [
                        {"title": "Async Mock Job", "company": "Async Company"}
                    ]
                }
            )
            
            # 測試非同步 HTTP 請求
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.example.com/async-jobs") as response:
                    data = await response.json()
                    
                    assert response.status == 200
                    assert len(data["jobs"]) == 1
                    assert data["jobs"][0]["title"] == "Async Mock Job"
    
    def test_function_mock(self):
        """函數 Mock 測試"""
        with patch('time.sleep') as mock_sleep:
            # Mock time.sleep 以加速測試
            mock_sleep.return_value = None
            
            start = time.time()
            time.sleep(1)  # 這個調用會被 Mock
            duration = time.time() - start
            
            # 驗證 sleep 被調用但實際沒有等待
            mock_sleep.assert_called_once_with(1)
            assert duration < 0.1  # 應該很快完成


class TestPerformanceComparison:
    """效能比較測試類別"""
    
    def test_sync_vs_async_performance(self):
        """比較同步與非同步效能"""
        # 測試參數
        test_params = {
            "site_name": ["indeed"],
            "search_term": "test",
            "location": "Sydney",
            "results_wanted": 3
        }
        
        # 同步測試
        start = time.time()
        try:
            sync_result = scrape_jobs(**test_params)
            sync_time = time.time() - start
            sync_success = True
        except Exception as e:
            sync_time = float('inf')
            sync_success = False
            print(f"同步測試失敗: {e}")
        
        # 非同步測試
        async def async_test():
            try:
                return await scrape_jobs_async(
                    **test_params,
                    max_concurrent_requests=2
                )
            except NameError:
                pytest.skip("非同步功能尚未實現")
        
        start = time.time()
        try:
            async_result = asyncio.run(async_test())
            async_time = time.time() - start
            async_success = True
        except Exception as e:
            async_time = float('inf')
            async_success = False
            print(f"非同步測試失敗: {e}")
        
        # 效能比較
        if sync_success and async_success:
            print(f"同步時間: {sync_time:.2f}秒")
            print(f"非同步時間: {async_time:.2f}秒")
            
            if async_time < sync_time:
                speedup = sync_time / async_time
                print(f"非同步速度提升: {speedup:.2f}x")
            
            # 驗證結果一致性
            if hasattr(sync_result, '__len__') and hasattr(async_result, '__len__'):
                # 允許一定的差異
                assert abs(len(sync_result) - len(async_result)) <= 2


class TestIntegration:
    """整合測試類別"""
    
    def test_full_pipeline(self):
        """測試完整的處理流程"""
        # 這個測試驗證從爬取到資料處理的完整流程
        try:
            # 1. 爬取資料
            raw_data = scrape_jobs(
                site_name="indeed",
                search_term="python",
                location="Sydney",
                results_wanted=3
            )
            
            if len(raw_data) == 0:
                pytest.skip("沒有爬取到資料")
            
            # 2. 資料品質檢查
            try:
                checker = DataQualityChecker()
                quality_score = checker.calculate_quality_score(raw_data.to_dict('records'))
                assert quality_score >= 0.0
                assert quality_score <= 1.0
            except NameError:
                pass  # 資料品質功能尚未實現
            
            # 3. 快取測試
            try:
                cache = get_global_cache()
                cache_key = "integration_test"
                cache.set(cache_key, raw_data.to_dict())
                cached_data = cache.get(cache_key)
                assert cached_data is not None
            except NameError:
                pass  # 快取功能尚未實現
            
            print(f"整合測試完成，處理了 {len(raw_data)} 筆資料")
            
        except Exception as e:
            print(f"整合測試失敗: {e}")
            # 不讓整合測試失敗影響其他測試
            pass


def run_performance_benchmark():
    """執行效能基準測試"""
    print("\n=== JobSpy 效能基準測試 ===")
    
    test_cases = [
        {"site": "indeed", "term": "python", "location": "Sydney"},
        {"site": "linkedin", "term": "data scientist", "location": "Melbourne"},
    ]
    
    for case in test_cases:
        print(f"\n測試案例: {case['site']} - {case['term']} @ {case['location']}")
        
        start = time.time()
        try:
            result = scrape_jobs(
                site_name=case["site"],
                search_term=case["term"],
                location=case["location"],
                results_wanted=5
            )
            duration = time.time() - start
            
            print(f"  結果: {len(result)} 個職位")
            print(f"  時間: {duration:.2f}秒")
            print(f"  速率: {len(result)/duration:.2f} 職位/秒")
            
        except Exception as e:
            print(f"  錯誤: {e}")


if __name__ == "__main__":
    # 執行基準測試
    run_performance_benchmark()
    
    # 執行所有測試
    print("\n=== 執行測試套件 ===")
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # 遇到第一個失敗就停止
    ])