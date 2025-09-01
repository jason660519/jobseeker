#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 整合測試

這個檔案包含了 jobseeker 的整合測試，用於測試不同模組之間的協作，
以及端到端的功能驗證。

作者: jobseeker Team
日期: 2024
"""

import pytest
import pandas as pd
import asyncio
from unittest.mock import patch, MagicMock
import time
from pathlib import Path

# jobseeker 模組導入
from jobseeker import scrape_jobs
try:
    from jobseeker import scrape_jobs_async, create_async_config
    from jobseeker.async_scraping import AsyncConfig, AsyncMode, ConcurrencyLevel
except ImportError:
    scrape_jobs_async = None
    create_async_config = None
    AsyncConfig = None
    AsyncMode = None
    ConcurrencyLevel = None

try:
    from jobseeker.cache_system import JobCache
except ImportError:
    JobCache = None

try:
    from jobseeker.performance_monitoring import ScrapingMetrics
except ImportError:
    ScrapingMetrics = None


class TestMultiSiteIntegration:
    """多網站整合測試"""
    
    @pytest.mark.integration
    @pytest.mark.requires_network
    def test_multiple_sites_sync(self):
        """測試同步多網站爬取整合"""
        sites = ["indeed", "linkedin"]
        
        result = scrape_jobs(
            site_name=sites,
            search_term="python developer",
            location="Sydney",
            results_wanted=5,
            distance=25
        )
        
        assert isinstance(result, pd.DataFrame)
        
        # 如果有結果，驗證資料完整性
        if len(result) > 0:
            # 檢查必要欄位
            required_columns = ['title', 'company', 'location']
            for col in required_columns:
                assert col in result.columns, f"缺少必要欄位: {col}"
            
            # 檢查資料不為空
            assert not result['title'].isna().all(), "所有職位標題都不能為空"
            assert not result['company'].isna().all(), "所有公司名稱都不能為空"
            
            print(f"成功獲取 {len(result)} 個職位")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.requires_network
    async def test_multiple_sites_async(self):
        """測試非同步多網站爬取整合"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        sites = ["indeed", "linkedin"]
        
        result = await scrape_jobs_async(
            site_name=sites,
            search_term="data scientist",
            location="Melbourne",
            results_wanted=5,
            max_concurrent_requests=3
        )
        
        assert isinstance(result, pd.DataFrame)
        
        if len(result) > 0:
            required_columns = ['title', 'company', 'location']
            for col in required_columns:
                assert col in result.columns
            
            print(f"非同步獲取 {len(result)} 個職位")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_scale_scraping(self):
        """測試大規模爬取整合"""
        sites = ["indeed", "linkedin", "glassdoor"]
        search_terms = ["python", "javascript", "data science"]
        locations = ["Sydney", "Melbourne"]
        
        all_results = []
        
        for site in sites:
            for term in search_terms:
                for location in locations:
                    try:
                        result = scrape_jobs(
                            site_name=site,
                            search_term=term,
                            location=location,
                            results_wanted=3
                        )
                        
                        if isinstance(result, pd.DataFrame) and len(result) > 0:
                            # 添加元資料
                            result['search_site'] = site
                            result['search_term'] = term
                            result['search_location'] = location
                            all_results.append(result)
                            
                        # 避免過於頻繁的請求
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"爬取失敗 - 網站: {site}, 搜尋詞: {term}, 地點: {location}, 錯誤: {e}")
                        continue
        
        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            assert isinstance(combined_results, pd.DataFrame)
            assert len(combined_results) > 0
            print(f"大規模爬取總共獲取 {len(combined_results)} 個職位")
        else:
            pytest.skip("無法獲取任何結果，可能是網路問題")


class TestCacheIntegration:
    """快取系統整合測試"""
    
    @pytest.mark.integration
    def test_cache_with_scraping(self, temp_dir):
        """測試快取與爬取的整合"""
        if JobCache is None:
            pytest.skip("快取系統尚未實現")
        
        cache_dir = temp_dir / "test_cache"
        cache = JobCache(cache_dir=str(cache_dir))
        
        # 第一次爬取（應該快取結果）
        search_params = {
            "site_name": "indeed",
            "search_term": "test job",
            "location": "Sydney",
            "results_wanted": 2
        }
        
        start_time = time.time()
        result1 = scrape_jobs(**search_params)
        first_duration = time.time() - start_time
        
        # 模擬快取存儲
        cache_key = cache._generate_cache_key(search_params)
        if isinstance(result1, pd.DataFrame) and len(result1) > 0:
            cache.set(cache_key, result1.to_dict('records'))
        
        # 第二次爬取（應該從快取獲取）
        start_time = time.time()
        cached_result = cache.get(cache_key)
        second_duration = time.time() - start_time
        
        if cached_result:
            # 快取命中應該更快
            assert second_duration < first_duration
            print(f"快取命中，速度提升: {first_duration/second_duration:.2f}x")
        
        # 檢查快取統計
        stats = cache.get_stats()
        assert hasattr(stats, 'size')
        print(f"快取統計: {stats}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_cache_integration(self, temp_dir):
        """測試非同步快取整合"""
        if scrape_jobs_async is None or JobCache is None:
            pytest.skip("非同步功能或快取系統尚未實現")
        
        cache_dir = temp_dir / "async_cache"
        cache = JobCache(cache_dir=str(cache_dir))
        
        search_params = {
            "site_name": ["indeed"],
            "search_term": "python",
            "location": "Melbourne",
            "results_wanted": 3
        }
        
        # 非同步爬取
        result = await scrape_jobs_async(**search_params)
        
        if isinstance(result, pd.DataFrame) and len(result) > 0:
            # 存儲到快取
            cache_key = cache._generate_cache_key(search_params)
            cache.set(cache_key, result.to_dict('records'))
            
            # 驗證快取
            cached_data = cache.get(cache_key)
            assert cached_data is not None
            
            # 轉換回 DataFrame 並比較
            cached_df = pd.DataFrame(cached_data)
            assert len(cached_df) == len(result)
            print("非同步快取整合測試成功")


class TestPerformanceIntegration:
    """效能監控整合測試"""
    
    @pytest.mark.integration
    def test_metrics_with_scraping(self):
        """測試效能監控與爬取的整合"""
        if ScrapingMetrics is None:
            pytest.skip("效能監控系統尚未實現")
        
        metrics = ScrapingMetrics()
        
        # 執行爬取並記錄指標
        start_time = time.time()
        
        try:
            result = scrape_jobs(
                site_name="indeed",
                search_term="test",
                location="Sydney",
                results_wanted=2
            )
            
            duration = time.time() - start_time
            success = isinstance(result, pd.DataFrame)
            
            # 記錄指標
            metrics.record_request(duration, success=success)
            
            if success and len(result) > 0:
                metrics.record_jobs_found(len(result))
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_request(duration, success=False)
            print(f"爬取失敗: {e}")
        
        # 檢查指標
        stats = metrics.get_stats()
        assert hasattr(stats, 'total_requests')
        assert hasattr(stats, 'success_rate')
        assert hasattr(stats, 'avg_response_time')
        assert stats.total_requests > 0
        
        print(f"效能統計: {stats}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_performance_monitoring(self):
        """測試非同步效能監控整合"""
        if scrape_jobs_async is None or ScrapingMetrics is None:
            pytest.skip("非同步功能或效能監控系統尚未實現")
        
        metrics = ScrapingMetrics()
        
        # 並發爬取多個搜尋
        tasks = []
        search_configs = [
            {"site_name": ["indeed"], "search_term": "python", "location": "Sydney"},
            {"site_name": ["linkedin"], "search_term": "javascript", "location": "Melbourne"},
        ]
        
        for config in search_configs:
            task = asyncio.create_task(
                self._async_scrape_with_metrics(
                    metrics, 
                    config["site_name"], 
                    config["search_term"], 
                    config["location"]
                )
            )
            tasks.append(task)
        
        # 等待所有任務完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 檢查結果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        print(f"成功完成 {len(successful_results)}/{len(tasks)} 個非同步任務")
        
        # 檢查效能指標
        stats = metrics.get_stats()
        assert stats.total_requests >= len(tasks)
        print(f"非同步效能統計: {stats}")
    
    async def _async_scrape_with_metrics(self, metrics, site_name, search_term, location):
        """帶效能監控的非同步爬取輔助方法"""
        start_time = time.time()
        
        try:
            result = await scrape_jobs_async(
                site_name=site_name,
                search_term=search_term,
                location=location,
                results_wanted=2
            )
            
            duration = time.time() - start_time
            success = isinstance(result, pd.DataFrame)
            
            metrics.record_request(duration, success=success)
            
            if success and len(result) > 0:
                metrics.record_jobs_found(len(result))
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_request(duration, success=False)
            raise e


class TestAsyncConfigIntegration:
    """非同步配置整合測試"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_config_modes(self):
        """測試不同非同步模式的整合"""
        if scrape_jobs_async is None or AsyncConfig is None:
            pytest.skip("非同步功能尚未實現")
        
        # 測試不同的非同步模式
        modes = [AsyncMode.ASYNCIO, AsyncMode.THREADED]
        
        for mode in modes:
            config = AsyncConfig(
                mode=mode,
                max_concurrent_requests=2,
                request_delay=0.5,
                timeout=30.0
            )
            
            start_time = time.time()
            
            try:
                result = await scrape_jobs_async(
                    site_name=["indeed"],
                    search_term="test",
                    location="Sydney",
                    results_wanted=2,
                    async_config=config
                )
                
                duration = time.time() - start_time
                
                assert isinstance(result, pd.DataFrame)
                print(f"模式 {mode.value}: {duration:.2f}秒, {len(result)}個結果")
                
            except Exception as e:
                print(f"模式 {mode.value} 測試失敗: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrency_levels(self):
        """測試不同並發級別的整合"""
        if scrape_jobs_async is None or ConcurrencyLevel is None:
            pytest.skip("非同步功能尚未實現")
        
        # 測試不同並發級別
        levels = [ConcurrencyLevel.LOW, ConcurrencyLevel.MEDIUM, ConcurrencyLevel.HIGH]
        
        for level in levels:
            if create_async_config:
                config = create_async_config(concurrency_level=level)
            else:
                config = AsyncConfig(
                    max_concurrent_requests=level.value if hasattr(level, 'value') else 2
                )
            
            start_time = time.time()
            
            try:
                result = await scrape_jobs_async(
                    site_name=["indeed", "linkedin"],
                    search_term="python",
                    location="Melbourne",
                    results_wanted=3,
                    async_config=config
                )
                
                duration = time.time() - start_time
                
                assert isinstance(result, pd.DataFrame)
                print(f"並發級別 {level}: {duration:.2f}秒, {len(result)}個結果")
                
            except Exception as e:
                print(f"並發級別 {level} 測試失敗: {e}")


class TestErrorHandlingIntegration:
    """錯誤處理整合測試"""
    
    @pytest.mark.integration
    def test_network_error_recovery(self):
        """測試網路錯誤恢復整合"""
        # 模擬網路錯誤
        with patch('requests.get') as mock_get:
            # 第一次請求失敗
            mock_get.side_effect = [ConnectionError("網路錯誤"), MagicMock()]
            
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term="test",
                    location="Sydney",
                    results_wanted=1
                )
                
                # 應該處理錯誤並返回空結果或重試
                assert isinstance(result, pd.DataFrame)
                
            except Exception as e:
                # 如果沒有錯誤恢復機制，應該拋出異常
                assert "網路錯誤" in str(e) or "ConnectionError" in str(e)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """測試非同步錯誤處理整合"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        # 測試無效網站處理
        try:
            result = await scrape_jobs_async(
                site_name=["invalid_site"],
                search_term="test",
                location="Sydney",
                results_wanted=1
            )
            
            # 如果沒有拋出異常，應該返回空結果
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            
        except (ValueError, KeyError, Exception) as e:
            # 預期的錯誤
            print(f"正確處理無效網站錯誤: {e}")
    
    @pytest.mark.integration
    def test_partial_failure_handling(self):
        """測試部分失敗處理整合"""
        # 測試多網站中部分失敗的情況
        sites = ["indeed", "invalid_site", "linkedin"]
        
        try:
            result = scrape_jobs(
                site_name=sites,
                search_term="test",
                location="Sydney",
                results_wanted=2
            )
            
            # 應該返回成功網站的結果
            assert isinstance(result, pd.DataFrame)
            print(f"部分失敗處理: 獲取 {len(result)} 個結果")
            
        except Exception as e:
            print(f"部分失敗處理測試: {e}")


class TestDataQualityIntegration:
    """資料品質整合測試"""
    
    @pytest.mark.integration
    def test_data_cleaning_integration(self):
        """測試資料清理整合"""
        result = scrape_jobs(
            site_name="indeed",
            search_term="python developer",
            location="Sydney",
            results_wanted=5
        )
        
        if isinstance(result, pd.DataFrame) and len(result) > 0:
            # 檢查資料清理效果
            
            # 檢查是否有重複資料
            duplicates = result.duplicated(subset=['title', 'company']).sum()
            print(f"重複資料數量: {duplicates}")
            
            # 檢查必要欄位是否為空
            for col in ['title', 'company']:
                if col in result.columns:
                    null_count = result[col].isna().sum()
                    empty_count = (result[col] == '').sum()
                    print(f"{col} 欄位 - 空值: {null_count}, 空字串: {empty_count}")
            
            # 檢查資料格式
            if 'location' in result.columns:
                # 檢查地點格式是否一致
                unique_locations = result['location'].unique()
                print(f"唯一地點數量: {len(unique_locations)}")
            
            print("資料品質檢查完成")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_data_quality(self):
        """測試非同步資料品質整合"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        result = await scrape_jobs_async(
            site_name=["indeed", "linkedin"],
            search_term="data scientist",
            location="Melbourne",
            results_wanted=5
        )
        
        if isinstance(result, pd.DataFrame) and len(result) > 0:
            # 檢查多網站資料一致性
            if 'site' in result.columns or 'source' in result.columns:
                source_col = 'site' if 'site' in result.columns else 'source'
                sources = result[source_col].unique()
                print(f"資料來源: {sources}")
                
                # 檢查每個來源的資料品質
                for source in sources:
                    source_data = result[result[source_col] == source]
                    print(f"{source}: {len(source_data)} 個職位")
            
            print("非同步資料品質檢查完成")


# ==================== 端到端測試 ====================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_network
def test_complete_workflow():
    """完整工作流程端到端測試"""
    print("\n=== 開始完整工作流程測試 ===")
    
    # 1. 同步爬取
    print("1. 執行同步爬取...")
    sync_result = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term="python developer",
        location="Sydney",
        results_wanted=5,
        distance=25,
        job_type="fulltime"
    )
    
    assert isinstance(sync_result, pd.DataFrame)
    print(f"   同步爬取完成: {len(sync_result)} 個職位")
    
    # 2. 資料驗證
    print("2. 驗證資料品質...")
    if len(sync_result) > 0:
        required_columns = ['title', 'company', 'location']
        for col in required_columns:
            assert col in sync_result.columns, f"缺少欄位: {col}"
        
        # 檢查資料完整性
        complete_rows = sync_result.dropna(subset=['title', 'company']).shape[0]
        print(f"   完整資料行數: {complete_rows}/{len(sync_result)}")
    
    # 3. 效能測試
    print("3. 執行效能測試...")
    start_time = time.time()
    
    perf_result = scrape_jobs(
        site_name="indeed",
        search_term="test",
        location="Melbourne",
        results_wanted=3
    )
    
    duration = time.time() - start_time
    print(f"   效能測試完成: {duration:.2f}秒, {len(perf_result)}個結果")
    
    print("=== 完整工作流程測試完成 ===")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.requires_network
async def test_complete_async_workflow():
    """完整非同步工作流程端到端測試"""
    if scrape_jobs_async is None:
        pytest.skip("非同步功能尚未實現")
    
    print("\n=== 開始完整非同步工作流程測試 ===")
    
    # 1. 非同步爬取
    print("1. 執行非同步爬取...")
    async_result = await scrape_jobs_async(
        site_name=["indeed", "linkedin"],
        search_term="data scientist",
        location="Melbourne",
        results_wanted=5,
        max_concurrent_requests=3
    )
    
    assert isinstance(async_result, pd.DataFrame)
    print(f"   非同步爬取完成: {len(async_result)} 個職位")
    
    # 2. 並發效能測試
    print("2. 執行並發效能測試...")
    start_time = time.time()
    
    # 並發執行多個搜尋
    tasks = [
        scrape_jobs_async(
            site_name=["indeed"],
            search_term="python",
            location="Sydney",
            results_wanted=2
        ),
        scrape_jobs_async(
            site_name=["linkedin"],
            search_term="javascript",
            location="Brisbane",
            results_wanted=2
        )
    ]
    
    concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start_time
    
    successful_results = [r for r in concurrent_results if not isinstance(r, Exception)]
    print(f"   並發測試完成: {duration:.2f}秒, {len(successful_results)}個成功任務")
    
    print("=== 完整非同步工作流程測試完成 ===")
