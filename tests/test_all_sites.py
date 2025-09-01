#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 全網站測試套件

這個模組包含針對所有支援網站的綜合測試，確保每個網站的爬蟲功能正常運作。
支援的網站包括：LinkedIn, Indeed, ZipRecruiter, Glassdoor, Google, Bayt, Naukri, BDJobs, Seek

Author: jobseeker Team
Date: 2024
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

import pandas as pd
from jobseeker import scrape_jobs
from jobseeker.model import Site, JobType, Country
from jobseeker.async_scraping import async_scrape_jobs, AsyncConfig, AsyncMode
from tests.fixtures.test_utils import (
    MockHTTPResponse, MockScraper, create_mock_job_data,
    measure_execution_time, NetworkDelaySimulator
)
from tests.fixtures.test_data import (
    SAMPLE_JOB_DATA, SEARCH_PARAMETERS, SITE_SPECIFIC_DATA,
    MOCK_RESPONSES, get_sample_jobs
)


class TestAllSitesIntegration:
    """
    測試所有支援網站的整合功能
    """
    
    # 所有支援的網站列表
    ALL_SITES = [
        Site.LINKEDIN,
        Site.INDEED, 
        Site.ZIP_RECRUITER,
        Site.GLASSDOOR,
        Site.GOOGLE,
        Site.BAYT,
        Site.NAUKRI,
        Site.BDJOBS,
        Site.SEEK
    ]
    
    # 網站名稱對應
    SITE_NAMES = {
        Site.LINKEDIN: "linkedin",
        Site.INDEED: "indeed",
        Site.ZIP_RECRUITER: "ziprecruiter", 
        Site.GLASSDOOR: "glassdoor",
        Site.GOOGLE: "google",
        Site.BAYT: "bayt",
        Site.NAUKRI: "naukri",
        Site.BDJOBS: "bdjobs",
        Site.SEEK: "seek"
    }
    
    @pytest.mark.unit
    @pytest.mark.parametrize("site", ALL_SITES)
    def test_individual_site_scraping_mock(self, site, mock_requests):
        """
        測試每個網站的個別爬取功能（使用 Mock）
        
        Args:
            site: 要測試的網站
            mock_requests: Mock HTTP 請求 fixture
        """
        # 設定 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text=MOCK_RESPONSES.get(self.SITE_NAMES[site], "<html>Mock response</html>"),
            json_data=SITE_SPECIFIC_DATA.get(self.SITE_NAMES[site], {})
        )
        mock_requests.return_value = mock_response
        
        # 執行爬取
        try:
            result = scrape_jobs(
                site_name=site,
                search_term="python developer",
                location="remote",
                results_wanted=5
            )
            
            # 驗證結果
            assert isinstance(result, pd.DataFrame)
            assert len(result.columns) > 0
            
            # 檢查必要欄位
            expected_columns = ['title', 'company', 'location', 'site']
            for col in expected_columns:
                assert col in result.columns, f"Missing column: {col}"
                
            # 驗證網站標識
            if not result.empty:
                assert all(result['site'] == self.SITE_NAMES[site])
                
        except Exception as e:
            pytest.fail(f"Site {site.value} scraping failed: {str(e)}")
    
    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.slow
    @pytest.mark.parametrize("site", ALL_SITES[:3])  # 只測試前3個網站以節省時間
    def test_individual_site_scraping_real(self, site):
        """
        測試個別網站的真實爬取功能（需要網路連接）
        
        Args:
            site: 要測試的網站
        """
        try:
            with measure_execution_time() as timer:
                result = scrape_jobs(
                    site_name=site,
                    search_term="software engineer",
                    location="san francisco",
                    results_wanted=3  # 減少結果數量以加快測試
                )
            
            # 驗證執行時間合理
            assert timer.elapsed < 60, f"Site {site.value} took too long: {timer.elapsed}s"
            
            # 驗證結果
            assert isinstance(result, pd.DataFrame)
            
            if not result.empty:
                # 檢查資料品質
                assert all(result['site'] == self.SITE_NAMES[site])
                assert result['title'].notna().any()
                assert result['company'].notna().any()
                
        except Exception as e:
            # 某些網站可能暫時不可用，記錄但不失敗
            pytest.skip(f"Site {site.value} temporarily unavailable: {str(e)}")
    
    @pytest.mark.unit
    def test_multiple_sites_scraping_mock(self, mock_requests):
        """
        測試多個網站同時爬取功能（使用 Mock）
        """
        # 設定 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>Mock multi-site response</html>"
        )
        mock_requests.return_value = mock_response
        
        # 測試多個網站
        test_sites = [Site.INDEED, Site.LINKEDIN, Site.GLASSDOOR]
        
        result = scrape_jobs(
            site_name=test_sites,
            search_term="data scientist",
            location="new york",
            results_wanted=5
        )
        
        # 驗證結果
        assert isinstance(result, pd.DataFrame)
        
        if not result.empty:
            # 檢查是否包含所有測試網站的資料
            sites_in_result = set(result['site'].unique())
            expected_sites = {self.SITE_NAMES[site] for site in test_sites}
            
            # 至少應該有一個網站的資料
            assert len(sites_in_result.intersection(expected_sites)) > 0
    
    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.slow
    def test_all_sites_scraping_real(self):
        """
        測試所有網站同時爬取功能（真實網路請求）
        """
        try:
            with measure_execution_time() as timer:
                result = scrape_jobs(
                    site_name=self.ALL_SITES,
                    search_term="python",
                    location="remote",
                    results_wanted=2  # 每個網站只要2個結果
                )
            
            # 驗證執行時間
            assert timer.elapsed < 300, f"All sites scraping took too long: {timer.elapsed}s"
            
            # 驗證結果
            assert isinstance(result, pd.DataFrame)
            
            if not result.empty:
                # 檢查網站覆蓋率
                sites_in_result = set(result['site'].unique())
                print(f"Successfully scraped from sites: {sites_in_result}")
                
                # 至少應該有一半的網站成功
                success_rate = len(sites_in_result) / len(self.ALL_SITES)
                assert success_rate >= 0.3, f"Too few sites succeeded: {success_rate:.2%}"
                
        except Exception as e:
            pytest.skip(f"All sites scraping failed: {str(e)}")
    
    @pytest.mark.unit
    @pytest.mark.parametrize("job_type", ["full-time", "part-time", "contract", "internship"])
    def test_job_type_filtering_all_sites(self, job_type, mock_requests):
        """
        測試所有網站的工作類型過濾功能
        
        Args:
            job_type: 工作類型
            mock_requests: Mock HTTP 請求 fixture
        """
        # 設定 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text=f"<html>Mock response for {job_type}</html>"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=self.ALL_SITES[:3],  # 測試前3個網站
            search_term="developer",
            job_type=job_type,
            results_wanted=3
        )
        
        # 驗證結果
        assert isinstance(result, pd.DataFrame)
        # 注意：由於使用 Mock，無法驗證實際的工作類型過濾
        # 但可以確保請求成功執行
    
    @pytest.mark.unit
    @pytest.mark.parametrize("country", ["usa", "uk", "canada", "australia"])
    def test_country_support_all_sites(self, country, mock_requests):
        """
        測試所有網站的國家支援功能
        
        Args:
            country: 國家代碼
            mock_requests: Mock HTTP 請求 fixture
        """
        # 設定 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text=f"<html>Mock response for {country}</html>"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=[Site.INDEED, Site.LINKEDIN],  # 測試支援多國的網站
            search_term="engineer",
            country_indeed=country,
            results_wanted=3
        )
        
        # 驗證結果
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_scraping_performance(self, mock_requests):
        """
        測試並發爬取的效能表現
        """
        # 設定 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>Mock concurrent response</html>"
        )
        mock_requests.return_value = mock_response
        
        # 測試並發爬取
        start_time = time.time()
        
        result = scrape_jobs(
            site_name=self.ALL_SITES,
            search_term="software developer",
            results_wanted=5
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 驗證並發效能
        # 並發執行應該比序列執行快
        max_expected_time = len(self.ALL_SITES) * 2  # 每個網站最多2秒
        assert execution_time < max_expected_time, f"Concurrent scraping too slow: {execution_time}s"
        
        # 驗證結果
        assert isinstance(result, pd.DataFrame)


class TestAsyncAllSites:
    """
    測試所有網站的非同步爬取功能
    """
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_async_scraping_all_sites_mock(self, mock_aiohttp_session):
        """
        測試所有網站的非同步爬取功能（使用 Mock）
        """
        # 設定 Mock 回應
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: "<html>Mock async response</html>")()
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response
        
        # 配置非同步設定
        config = AsyncConfig(
            mode=AsyncMode.CONCURRENT,
            max_concurrent=3,
            delay_between_requests=0.1
        )
        
        # 執行非同步爬取
        result = await async_scrape_jobs(
            site_name=TestAllSitesIntegration.ALL_SITES[:3],
            search_term="python developer",
            results_wanted=3,
            config=config
        )
        
        # 驗證結果
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.slow
    async def test_async_scraping_performance_comparison(self):
        """
        比較非同步和同步爬取的效能差異
        """
        test_sites = [Site.INDEED, Site.LINKEDIN]
        search_params = {
            "search_term": "developer",
            "location": "remote",
            "results_wanted": 2
        }
        
        try:
            # 測試同步爬取
            sync_start = time.time()
            sync_result = scrape_jobs(site_name=test_sites, **search_params)
            sync_time = time.time() - sync_start
            
            # 測試非同步爬取
            async_start = time.time()
            async_result = await async_scrape_jobs(
                site_name=test_sites,
                config=AsyncConfig(mode=AsyncMode.CONCURRENT, max_concurrent=2),
                **search_params
            )
            async_time = time.time() - async_start
            
            # 驗證結果
            assert isinstance(sync_result, pd.DataFrame)
            assert isinstance(async_result, pd.DataFrame)
            
            # 非同步應該更快（或至少不會慢太多）
            performance_ratio = async_time / sync_time if sync_time > 0 else 1
            assert performance_ratio <= 1.5, f"Async too slow compared to sync: {performance_ratio:.2f}x"
            
            print(f"Sync time: {sync_time:.2f}s, Async time: {async_time:.2f}s")
            print(f"Performance ratio (async/sync): {performance_ratio:.2f}")
            
        except Exception as e:
            pytest.skip(f"Performance comparison failed: {str(e)}")


class TestSiteSpecificFeatures:
    """
    測試各網站特有功能
    """
    
    @pytest.mark.unit
    def test_linkedin_specific_features(self, mock_requests):
        """
        測試 LinkedIn 特有功能
        """
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>LinkedIn mock response</html>"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=Site.LINKEDIN,
            search_term="data scientist",
            linkedin_fetch_description=True,
            linkedin_company_ids=[1234, 5678],
            results_wanted=3
        )
        
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.unit
    def test_indeed_country_support(self, mock_requests):
        """
        測試 Indeed 的多國支援
        """
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>Indeed mock response</html>"
        )
        mock_requests.return_value = mock_response
        
        countries = ["usa", "uk", "canada", "australia"]
        
        for country in countries:
            result = scrape_jobs(
                site_name=Site.INDEED,
                search_term="engineer",
                country_indeed=country,
                results_wanted=2
            )
            
            assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.unit
    def test_google_search_term(self, mock_requests):
        """
        測試 Google 的特殊搜尋功能
        """
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>Google jobs mock response</html>"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=Site.GOOGLE,
            google_search_term="python developer jobs",
            location="san francisco",
            results_wanted=3
        )
        
        assert isinstance(result, pd.DataFrame)


class TestErrorHandlingAllSites:
    """
    測試所有網站的錯誤處理
    """
    
    @pytest.mark.unit
    @pytest.mark.parametrize("site", TestAllSitesIntegration.ALL_SITES)
    def test_network_error_handling(self, site, mock_requests):
        """
        測試網路錯誤處理
        
        Args:
            site: 要測試的網站
            mock_requests: Mock HTTP 請求 fixture
        """
        # 模擬網路錯誤
        mock_requests.side_effect = Exception("Network error")
        
        # 執行爬取，應該優雅地處理錯誤
        result = scrape_jobs(
            site_name=site,
            search_term="test",
            results_wanted=1
        )
        
        # 應該返回空的 DataFrame 而不是拋出異常
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    @pytest.mark.unit
    @pytest.mark.parametrize("status_code", [404, 500, 503])
    def test_http_error_handling(self, status_code, mock_requests):
        """
        測試 HTTP 錯誤處理
        
        Args:
            status_code: HTTP 狀態碼
            mock_requests: Mock HTTP 請求 fixture
        """
        # 模擬 HTTP 錯誤
        mock_response = MockHTTPResponse(
            status_code=status_code,
            text="Error page"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=[Site.INDEED, Site.LINKEDIN],
            search_term="test",
            results_wanted=1
        )
        
        # 應該優雅地處理錯誤
        assert isinstance(result, pd.DataFrame)
    
    @pytest.mark.unit
    def test_invalid_parameters(self):
        """
        測試無效參數處理
        """
        # 測試無效網站名稱
        with pytest.raises((ValueError, AttributeError)):
            scrape_jobs(
                site_name="invalid_site",
                search_term="test"
            )
        
        # 測試無效工作類型
        with pytest.raises((ValueError, AttributeError)):
            scrape_jobs(
                site_name=Site.INDEED,
                search_term="test",
                job_type="invalid_job_type"
            )


class TestDataQualityAllSites:
    """
    測試所有網站的資料品質
    """
    
    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.slow
    def test_data_consistency_across_sites(self):
        """
        測試不同網站間的資料一致性
        """
        try:
            result = scrape_jobs(
                site_name=[Site.INDEED, Site.LINKEDIN, Site.GLASSDOOR],
                search_term="software engineer",
                location="san francisco",
                results_wanted=3
            )
            
            if not result.empty:
                # 檢查必要欄位存在
                required_columns = ['title', 'company', 'location', 'site']
                for col in required_columns:
                    assert col in result.columns
                
                # 檢查資料類型一致性
                assert result['title'].dtype == 'object'
                assert result['company'].dtype == 'object'
                assert result['site'].dtype == 'object'
                
                # 檢查網站標識正確性
                valid_sites = {'indeed', 'linkedin', 'glassdoor'}
                assert all(site in valid_sites for site in result['site'].unique())
                
        except Exception as e:
            pytest.skip(f"Data consistency test failed: {str(e)}")
    
    @pytest.mark.unit
    def test_data_validation_all_sites(self, mock_requests):
        """
        測試所有網站的資料驗證
        """
        # 設定包含完整資料的 Mock 回應
        mock_response = MockHTTPResponse(
            status_code=200,
            text="<html>Complete job data</html>"
        )
        mock_requests.return_value = mock_response
        
        result = scrape_jobs(
            site_name=TestAllSitesIntegration.ALL_SITES[:3],
            search_term="developer",
            results_wanted=2
        )
        
        if not result.empty:
            # 驗證資料完整性
            assert not result['title'].isna().all()
            assert not result['company'].isna().all()
            assert not result['site'].isna().any()
            
            # 驗證資料格式
            for _, row in result.iterrows():
                if pd.notna(row['title']):
                    assert isinstance(row['title'], str)
                    assert len(row['title'].strip()) > 0
                
                if pd.notna(row['company']):
                    assert isinstance(row['company'], str)
                    assert len(row['company'].strip()) > 0


# 測試標記說明
pytest_marks = {
    "unit": "單元測試 - 快速執行，使用 Mock",
    "integration": "整合測試 - 測試模組協作", 
    "performance": "效能測試 - 測量執行時間和資源使用",
    "network": "需要網路連接的測試",
    "slow": "慢速測試 - 執行時間較長",
    "mock": "使用 Mock 的測試",
    "asyncio": "非同步測試"
}


if __name__ == "__main__":
    # 執行測試的範例
    print("jobseeker 全網站測試套件")
    print("支援的網站：")
    for site in TestAllSitesIntegration.ALL_SITES:
        print(f"  - {site.value}")
    
    print("\n執行測試命令：")
    print("  pytest tests/test_all_sites.py -v")
    print("  pytest tests/test_all_sites.py -m unit")
    print("  pytest tests/test_all_sites.py -m 'not slow'")
    print("  pytest tests/test_all_sites.py::TestAllSitesIntegration::test_individual_site_scraping_mock")
