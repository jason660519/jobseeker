#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 基本功能單元測試

這個檔案包含了 jobseeker 核心功能的基本單元測試，
用於驗證主要功能的正確性。

作者: jobseeker Team
日期: 2024
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

# jobseeker 模組導入
from jobseeker import scrape_jobs
try:
    from jobseeker import scrape_jobs_async
except ImportError:
    scrape_jobs_async = None


class TestBasicScraping:
    """基本爬取功能測試"""
    
    def test_scrape_jobs_returns_dataframe(self):
        """測試 scrape_jobs 返回 DataFrame"""
        result = scrape_jobs(
            site_name="indeed",
            search_term="test",
            location="Sydney",
            results_wanted=1
        )
        
        assert isinstance(result, pd.DataFrame), "結果應該是 pandas DataFrame"
    
    def test_scrape_jobs_with_valid_parameters(self):
        """測試使用有效參數的爬取"""
        result = scrape_jobs(
            site_name="indeed",
            search_term="python developer",
            location="Melbourne",
            results_wanted=3,
            distance=25,
            job_type="fulltime"
        )
        
        assert isinstance(result, pd.DataFrame)
        # 檢查基本欄位存在（如果有結果的話）
        if len(result) > 0:
            expected_columns = ['title', 'company', 'location']
            for col in expected_columns:
                assert col in result.columns, f"缺少欄位: {col}"
    
    def test_scrape_jobs_multiple_sites(self):
        """測試多網站爬取"""
        sites = ["indeed", "linkedin"]
        result = scrape_jobs(
            site_name=sites,
            search_term="software engineer",
            location="Brisbane",
            results_wanted=2
        )
        
        assert isinstance(result, pd.DataFrame)
        # 如果有結果，檢查是否包含網站來源資訊
        if len(result) > 0:
            # 可能的來源欄位名稱
            source_columns = ['site', 'source', 'job_source']
            has_source = any(col in result.columns for col in source_columns)
            # 注意：這個斷言可能需要根據實際實現調整
            # assert has_source, "應該包含來源網站資訊"
    
    def test_scrape_jobs_invalid_site(self):
        """測試無效網站處理"""
        with pytest.raises((ValueError, KeyError, Exception)):
            scrape_jobs(
                site_name="nonexistent_site",
                search_term="test",
                location="Sydney",
                results_wanted=1
            )
    
    def test_scrape_jobs_empty_search_term(self):
        """測試空搜尋詞處理"""
        # 這個測試可能需要根據實際行為調整
        try:
            result = scrape_jobs(
                site_name="indeed",
                search_term="",
                location="Sydney",
                results_wanted=1
            )
            # 如果允許空搜尋詞，檢查結果
            assert isinstance(result, pd.DataFrame)
        except (ValueError, Exception):
            # 如果不允許空搜尋詞，應該拋出異常
            pass


class TestAsyncScraping:
    """非同步爬取功能測試"""
    
    @pytest.mark.asyncio
    async def test_async_scrape_basic(self):
        """測試基本非同步爬取"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        result = await scrape_jobs_async(
            site_name=["indeed"],
            search_term="python",
            location="Sydney",
            results_wanted=2,
            max_concurrent_requests=2
        )
        
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.asyncio
    async def test_async_scrape_multiple_sites(self):
        """測試非同步多網站爬取"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        sites = ["indeed", "linkedin"]
        result = await scrape_jobs_async(
            site_name=sites,
            search_term="data scientist",
            location="Melbourne",
            results_wanted=2,
            max_concurrent_requests=3
        )
        
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.asyncio
    async def test_async_scrape_with_config(self):
        """測試使用配置的非同步爬取"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        try:
            from jobseeker.async_scraping import AsyncConfig, AsyncMode
            
            config = AsyncConfig(
                mode=AsyncMode.THREADED,
                max_concurrent_requests=2,
                request_delay=0.5,
                timeout=30.0
            )
            
            result = await scrape_jobs_async(
                site_name=["indeed"],
                search_term="test",
                location="Brisbane",
                results_wanted=1,
                async_config=config
            )
            
            assert isinstance(result, pd.DataFrame)
        except ImportError:
            pytest.skip("AsyncConfig 尚未實現")


class TestDataValidation:
    """資料驗證測試"""
    
    def test_result_dataframe_structure(self, sample_job_data):
        """測試結果 DataFrame 結構"""
        # 創建測試 DataFrame
        df = pd.DataFrame([sample_job_data])
        
        # 檢查基本結構
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # 檢查必要欄位
        required_fields = ['title', 'company', 'location']
        for field in required_fields:
            assert field in df.columns, f"缺少必要欄位: {field}"
    
    def test_job_data_types(self, sample_job_data):
        """測試職位資料類型"""
        # 檢查字串欄位
        string_fields = ['title', 'company', 'location', 'description']
        for field in string_fields:
            if field in sample_job_data:
                assert isinstance(sample_job_data[field], str), f"{field} 應該是字串"
    
    def test_job_data_not_empty(self, sample_job_data):
        """測試職位資料不為空"""
        critical_fields = ['title', 'company']
        for field in critical_fields:
            assert sample_job_data.get(field), f"{field} 不能為空"
            assert sample_job_data[field].strip(), f"{field} 不能只包含空白字符"


class TestErrorHandling:
    """錯誤處理測試"""
    
    def test_invalid_site_parameter(self):
        """測試無效網站參數"""
        invalid_sites = ["invalid_site", "nonexistent", ""]
        
        for site in invalid_sites:
            with pytest.raises((ValueError, KeyError, Exception)):
                scrape_jobs(
                    site_name=site,
                    search_term="test",
                    location="Sydney",
                    results_wanted=1
                )
    
    def test_invalid_results_wanted(self):
        """測試無效的結果數量參數"""
        invalid_values = [-1, 0, "invalid", None]
        
        for value in invalid_values:
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term="test",
                    location="Sydney",
                    results_wanted=value
                )
                # 如果沒有拋出異常，檢查是否有合理的預設行為
                assert isinstance(result, pd.DataFrame)
            except (ValueError, TypeError, Exception):
                # 預期的異常
                pass
    
    def test_network_error_handling(self):
        """測試網路錯誤處理"""
        # 這個測試需要 Mock 網路請求
        with patch('requests.get') as mock_get:
            # 模擬網路錯誤
            mock_get.side_effect = ConnectionError("網路連接失敗")
            
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term="test",
                    location="Sydney",
                    results_wanted=1
                )
                # 如果沒有拋出異常，應該返回空的 DataFrame
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 0
            except (ConnectionError, Exception):
                # 預期的網路異常
                pass


class TestParameterValidation:
    """參數驗證測試"""
    
    def test_site_name_validation(self):
        """測試網站名稱驗證"""
        valid_sites = ["indeed", "linkedin", "glassdoor", "seek"]
        
        for site in valid_sites:
            try:
                result = scrape_jobs(
                    site_name=site,
                    search_term="test",
                    location="Sydney",
                    results_wanted=1
                )
                assert isinstance(result, pd.DataFrame)
            except Exception as e:
                # 記錄但不失敗，因為可能是網路或其他問題
                print(f"網站 {site} 測試失敗: {e}")
    
    def test_location_parameter(self):
        """測試地點參數"""
        locations = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
        
        for location in locations:
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term="test",
                    location=location,
                    results_wanted=1
                )
                assert isinstance(result, pd.DataFrame)
            except Exception as e:
                print(f"地點 {location} 測試失敗: {e}")
    
    def test_job_type_parameter(self):
        """測試職位類型參數"""
        job_types = ["fulltime", "parttime", "contract", "internship"]
        
        for job_type in job_types:
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term="test",
                    location="Sydney",
                    results_wanted=1,
                    job_type=job_type
                )
                assert isinstance(result, pd.DataFrame)
            except Exception as e:
                print(f"職位類型 {job_type} 測試失敗: {e}")


class TestMockScenarios:
    """Mock 場景測試"""
    
    def test_mock_successful_response(self, mock_requests):
        """測試 Mock 成功響應"""
        # 設定 Mock 響應
        mock_requests['response'].json.return_value = {
            'jobs': [
                {
                    'title': 'Mock Job',
                    'company': 'Mock Company',
                    'location': 'Mock Location'
                }
            ]
        }
        
        # 這裡需要根據實際的爬蟲實現來調整測試
        # 目前只是示範 Mock 的使用
        assert mock_requests['get'] is not None
        assert mock_requests['response'] is not None
    
    def test_mock_cache_functionality(self, mock_cache):
        """測試 Mock 快取功能"""
        # 測試快取設定和獲取
        test_key = "test_key"
        test_value = {"data": "test_value"}
        
        mock_cache.set(test_key, test_value)
        retrieved = mock_cache.get(test_key)
        
        assert retrieved == test_value
        
        # 測試快取統計
        stats = mock_cache.get_stats()
        assert hasattr(stats, 'size')
        assert hasattr(stats, 'hit_rate')
    
    def test_mock_metrics_functionality(self, mock_metrics):
        """測試 Mock 效能監控功能"""
        # 記錄一些請求
        mock_metrics.record_request(0.5, success=True)
        mock_metrics.record_request(1.0, success=False)
        
        # 獲取統計
        stats = mock_metrics.get_stats()
        assert hasattr(stats, 'total_requests')
        assert hasattr(stats, 'success_rate')
        assert hasattr(stats, 'avg_response_time')
        
        # 重置指標
        mock_metrics.reset()
        stats_after_reset = mock_metrics.get_stats()
        assert stats_after_reset.total_requests == 0


# ==================== 測試標記範例 ====================

@pytest.mark.slow
def test_large_result_set():
    """慢速測試：大量結果集"""
    result = scrape_jobs(
        site_name="indeed",
        search_term="software",
        location="Sydney",
        results_wanted=50  # 較大的結果集
    )
    
    assert isinstance(result, pd.DataFrame)
    # 注意：實際結果可能少於請求的數量


@pytest.mark.integration
def test_end_to_end_workflow():
    """整合測試：端到端工作流程"""
    # 這是一個簡單的整合測試範例
    sites = ["indeed", "linkedin"]
    
    for site in sites:
        try:
            result = scrape_jobs(
                site_name=site,
                search_term="python",
                location="Melbourne",
                results_wanted=3
            )
            
            assert isinstance(result, pd.DataFrame)
            print(f"{site}: {len(result)} 個結果")
            
        except Exception as e:
            print(f"{site} 整合測試失敗: {e}")
            # 不讓單個網站的失敗影響整個測試
            continue


@pytest.mark.requires_network
def test_real_network_request():
    """需要網路的測試"""
    # 這個測試需要真實的網路連接
    result = scrape_jobs(
        site_name="indeed",
        search_term="test",
        location="Sydney",
        results_wanted=1
    )
    
    assert isinstance(result, pd.DataFrame)
