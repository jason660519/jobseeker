#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 測試配置檔案

這個檔案包含了所有測試的共用配置、fixtures 和設定。
它會被 pytest 自動載入，為所有測試提供共用的測試環境。

作者: jobseeker Team
日期: 2024
"""

import pytest
import asyncio
import tempfile
import shutil
import sys
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

# 設定專案根目錄
project_root = Path(__file__).parent.parent  # 回到 jobseeker 根目錄
tests_dir = Path(__file__).parent  # tests 資料夾
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))

# jobseeker 模組導入
try:
    from jobseeker.model import ScraperInput, Site, JobPost
    from jobseeker.cache_system import get_global_cache
    from jobseeker.performance_monitoring import get_global_metrics
    from jobseeker.async_scraping import AsyncConfig, AsyncMode
except ImportError:
    # 如果模組尚未實現，創建 Mock 物件
    ScraperInput = Mock
    Site = Mock
    JobPost = Mock
    get_global_cache = Mock
    get_global_metrics = Mock
    AsyncConfig = Mock
    AsyncMode = Mock


# ==================== 基本配置 ====================

@pytest.fixture(scope="session")
def event_loop():
    """為整個測試會話創建事件循環"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def clean_environment():
    """每個測試前清理環境"""
    # 測試前的清理
    try:
        # 清理快取
        cache = get_global_cache()
        if hasattr(cache, 'clear'):
            cache.clear()
    except (NameError, AttributeError):
        pass
    
    try:
        # 重置效能指標
        metrics = get_global_metrics()
        if hasattr(metrics, 'reset'):
            metrics.reset()
    except (NameError, AttributeError):
        pass
    
    yield
    
    # 測試後的清理
    try:
        cache = get_global_cache()
        if hasattr(cache, 'clear'):
            cache.clear()
    except (NameError, AttributeError):
        pass


# ==================== 測試資料 Fixtures ====================

@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """提供範例職位資料"""
    return {
        'title': 'Senior Python Developer',
        'company': 'TechCorp Australia',
        'location': 'Sydney, NSW',
        'salary': '$90,000 - $120,000',
        'description': 'We are looking for an experienced Python developer to join our team. Requirements include 5+ years of Python experience, Django/Flask knowledge, and strong problem-solving skills.',
        'date_posted': '2024-01-15',
        'job_url': 'https://example.com/jobs/123',
        'site': 'indeed'
    }


@pytest.fixture
def sample_job_list() -> list:
    """提供範例職位列表"""
    return [
        {
            'title': 'Python Developer',
            'company': 'StartupCorp',
            'location': 'Melbourne, VIC',
            'salary': '$70,000 - $90,000',
            'description': 'Junior Python developer position...',
            'date_posted': '2024-01-10',
            'site': 'indeed'
        },
        {
            'title': 'Senior Software Engineer',
            'company': 'BigTech',
            'location': 'Sydney, NSW',
            'salary': '$120,000 - $150,000',
            'description': 'Senior position requiring 8+ years experience...',
            'date_posted': '2024-01-12',
            'site': 'linkedin'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp',
            'location': 'Brisbane, QLD',
            'salary': '$100,000 - $130,000',
            'description': 'Looking for a data scientist with ML experience...',
            'date_posted': '2024-01-14',
            'site': 'glassdoor'
        }
    ]


@pytest.fixture
def sample_scraper_input():
    """提供範例爬蟲輸入"""
    try:
        return ScraperInput(
            search_term='python developer',
            location='Sydney',
            results_wanted=10,
            distance=25,
            job_type='fulltime',
            is_remote=False
        )
    except (TypeError, NameError):
        # 如果 ScraperInput 尚未實現，返回字典
        return {
            'search_term': 'python developer',
            'location': 'Sydney',
            'results_wanted': 10,
            'distance': 25,
            'job_type': 'fulltime',
            'is_remote': False
        }


@pytest.fixture
def sample_async_config():
    """提供範例非同步配置"""
    try:
        return AsyncConfig(
            mode=AsyncMode.THREADED,
            max_concurrent_requests=3,
            request_delay=0.5,
            timeout=30.0,
            enable_caching=True,
            enable_quality_check=True,
            retry_attempts=3
        )
    except (TypeError, NameError):
        # 如果 AsyncConfig 尚未實現，返回字典
        return {
            'mode': 'threaded',
            'max_concurrent_requests': 3,
            'request_delay': 0.5,
            'timeout': 30.0,
            'enable_caching': True,
            'enable_quality_check': True,
            'retry_attempts': 3
        }


# ==================== 臨時檔案和目錄 ====================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """提供臨時目錄"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_cache_dir(temp_dir) -> Path:
    """提供臨時快取目錄"""
    cache_dir = temp_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


@pytest.fixture
def temp_log_dir(temp_dir) -> Path:
    """提供臨時日誌目錄"""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_requests():
    """Mock requests 模組"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # 設定預設響應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'jobs': []}
        mock_response.text = '<html><body>Mock HTML</body></html>'
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }


@pytest.fixture
def mock_playwright():
    """Mock Playwright 瀏覽器"""
    mock_browser = Mock()
    mock_page = Mock()
    mock_context = Mock()
    
    # 設定 Mock 行為
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = None
    mock_page.content.return_value = '<html><body>Mock Page Content</body></html>'
    mock_page.query_selector_all.return_value = []
    
    with patch('playwright.sync_api.sync_playwright') as mock_playwright_context:
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright_context.return_value.__enter__.return_value = mock_playwright_instance
        
        yield {
            'playwright': mock_playwright_instance,
            'browser': mock_browser,
            'context': mock_context,
            'page': mock_page
        }


@pytest.fixture
def mock_cache():
    """Mock 快取系統"""
    cache_data = {}
    
    def mock_get(key):
        return cache_data.get(key)
    
    def mock_set(key, value, ttl=None):
        cache_data[key] = value
    
    def mock_clear():
        cache_data.clear()
    
    def mock_get_stats():
        return Mock(
            size=len(cache_data),
            hit_rate=0.8,
            memory_usage_mb=10.5
        )
    
    mock_cache_obj = Mock()
    mock_cache_obj.get.side_effect = mock_get
    mock_cache_obj.set.side_effect = mock_set
    mock_cache_obj.clear.side_effect = mock_clear
    mock_cache_obj.get_stats.side_effect = mock_get_stats
    
    with patch('jobseeker.cache_system.get_global_cache', return_value=mock_cache_obj):
        yield mock_cache_obj


@pytest.fixture
def mock_metrics():
    """Mock 效能監控系統"""
    metrics_data = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'total_time': 0.0
    }
    
    def mock_record_request(duration, success=True):
        metrics_data['total_requests'] += 1
        metrics_data['total_time'] += duration
        if success:
            metrics_data['successful_requests'] += 1
        else:
            metrics_data['failed_requests'] += 1
    
    def mock_get_stats():
        total = metrics_data['total_requests']
        return Mock(
            total_requests=total,
            success_rate=metrics_data['successful_requests'] / max(total, 1),
            avg_response_time=metrics_data['total_time'] / max(total, 1),
            cache_hit_rate=0.75
        )
    
    def mock_reset():
        metrics_data.update({
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_time': 0.0
        })
    
    mock_metrics_obj = Mock()
    mock_metrics_obj.record_request.side_effect = mock_record_request
    mock_metrics_obj.get_stats.side_effect = mock_get_stats
    mock_metrics_obj.reset.side_effect = mock_reset
    
    with patch('jobseeker.performance_monitoring.get_global_metrics', return_value=mock_metrics_obj):
        yield mock_metrics_obj


# ==================== 測試標記和跳過條件 ====================

def pytest_configure(config):
    """pytest 配置鉤子"""
    # 註冊自定義標記
    config.addinivalue_line(
        "markers", "requires_network: 標記需要網路連接的測試"
    )
    config.addinivalue_line(
        "markers", "slow: 標記慢速測試"
    )
    config.addinivalue_line(
        "markers", "integration: 標記整合測試"
    )


def pytest_collection_modifyitems(config, items):
    """修改測試項目收集"""
    # 為需要網路的測試添加跳過標記
    skip_network = pytest.mark.skip(reason="需要網路連接")
    
    for item in items:
        if "requires_network" in item.keywords:
            # 可以根據環境變數決定是否跳過網路測試
            import os
            if os.getenv("SKIP_NETWORK_TESTS", "false").lower() == "true":
                item.add_marker(skip_network)


# ==================== 測試報告鉤子 ====================

@pytest.fixture(autouse=True)
def test_timing(request):
    """自動記錄測試執行時間"""
    import time
    start_time = time.time()
    
    yield
    
    duration = time.time() - start_time
    if duration > 5.0:  # 超過 5 秒的測試
        print(f"\n⚠️  慢速測試: {request.node.name} 耗時 {duration:.2f}秒")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """自定義測試報告"""
    outcome = yield
    rep = outcome.get_result()
    
    # 為失敗的測試添加額外資訊
    if rep.when == "call" and rep.failed:
        # 可以在這裡添加失敗時的額外資訊收集
        pass


# ==================== 輔助函數 ====================

def create_mock_job_response(num_jobs: int = 3) -> Dict[str, Any]:
    """創建 Mock 職位響應資料"""
    jobs = []
    for i in range(num_jobs):
        jobs.append({
            'title': f'Test Job {i+1}',
            'company': f'Test Company {i+1}',
            'location': f'Test Location {i+1}',
            'salary': f'${50000 + i*10000} - ${70000 + i*10000}',
            'description': f'Test job description {i+1}',
            'date_posted': '2024-01-15',
            'job_url': f'https://example.com/job/{i+1}'
        })
    
    return {
        'jobs': jobs,
        'total_found': num_jobs,
        'page': 1,
        'total_pages': 1
    }


def assert_valid_job_data(job_data: Dict[str, Any]):
    """驗證職位資料的有效性"""
    required_fields = ['title', 'company', 'location']
    
    for field in required_fields:
        assert field in job_data, f"缺少必要欄位: {field}"
        assert job_data[field], f"欄位 {field} 不能為空"
    
    # 檢查可選欄位
    if 'salary' in job_data and job_data['salary']:
        assert isinstance(job_data['salary'], str), "薪資應該是字串格式"
    
    if 'date_posted' in job_data and job_data['date_posted']:
        assert isinstance(job_data['date_posted'], str), "發布日期應該是字串格式"


def assert_valid_dataframe(df):
    """驗證 DataFrame 的有效性"""
    import pandas as pd
    
    assert isinstance(df, pd.DataFrame), "結果應該是 pandas DataFrame"
    assert len(df) >= 0, "DataFrame 長度應該 >= 0"
    
    if len(df) > 0:
        required_columns = ['title', 'company', 'location']
        for col in required_columns:
            assert col in df.columns, f"DataFrame 缺少必要欄位: {col}"


# ==================== 測試環境檢查 ====================

@pytest.fixture(scope="session", autouse=True)
def check_test_environment():
    """檢查測試環境"""
    import sys
    import platform
    
    print(f"\n=== 測試環境資訊 ===")
    print(f"Python 版本: {sys.version}")
    print(f"平台: {platform.platform()}")
    print(f"架構: {platform.architecture()}")
    
    # 檢查必要的套件
    required_packages = ['pytest', 'pandas']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        pytest.fail(f"缺少必要套件: {', '.join(missing_packages)}")
    
    yield
    
    print(f"\n=== 測試完成 ===")
