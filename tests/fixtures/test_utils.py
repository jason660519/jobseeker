#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 測試工具

這個檔案包含了 jobseeker 測試所需的工具函數、Mock 類別和測試輔助工具，
用於簡化測試編寫和提高測試效率。

作者: jobseeker Team
日期: 2024
"""

import asyncio
import time
import json
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import contextmanager, asynccontextmanager
import pandas as pd
from datetime import datetime, timedelta
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import aiohttp

# 導入測試資料
from .test_data import (
    SAMPLE_JOB_DATA, SAMPLE_JOBS_LIST, MOCK_JSON_RESPONSE,
    SITE_SPECIFIC_DATA, ERROR_TEST_SCENARIOS
)


# ==================== Mock 類別 ====================

class MockResponse:
    """Mock HTTP 響應類別"""
    
    def __init__(self, json_data: Dict = None, text_data: str = None, 
                 status_code: int = 200, headers: Dict = None):
        self.json_data = json_data or {}
        self.text_data = text_data or ""
        self.status_code = status_code
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300
    
    def json(self):
        """返回 JSON 資料"""
        return self.json_data
    
    @property
    def text(self):
        """返回文字資料"""
        return self.text_data
    
    def raise_for_status(self):
        """檢查狀態碼"""
        if not self.ok:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class MockHTTPResponse:
    """Mock HTTP 響應類別（與 MockResponse 類似但參數名稱不同）"""
    
    def __init__(self, json_data: Dict = None, text: str = None,
                 status_code: int = 200, headers: Dict = None):
        self.json_data = json_data or {}
        self.text = text or ""
        self.status_code = status_code
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300
    
    def json(self):
        """返回 JSON 資料"""
        return self.json_data
    
    def raise_for_status(self):
        """檢查狀態碼"""
        if not self.ok:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class MockAsyncResponse:
    """Mock 非同步 HTTP 響應類別"""
    
    def __init__(self, json_data: Dict = None, text_data: str = None,
                 status_code: int = 200, headers: Dict = None):
        self.json_data = json_data or {}
        self.text_data = text_data or ""
        self.status = status_code
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300
    
    async def json(self):
        """返回 JSON 資料"""
        return self.json_data
    
    async def text(self):
        """返回文字資料"""
        return self.text_data
    
    def raise_for_status(self):
        """檢查狀態碼"""
        if not self.ok:
            raise aiohttp.ClientResponseError(
                request_info=None,
                history=None,
                status=self.status
            )


class MockScraper:
    """Mock 爬蟲類別"""
    
    def __init__(self, site_name: str, response_data: List[Dict] = None,
                 delay: float = 0.1, should_fail: bool = False):
        self.site_name = site_name
        self.response_data = response_data or SAMPLE_JOBS_LIST[:3]
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0
    
    def scrape(self, search_term: str, location: str, results_wanted: int = 10,
               **kwargs) -> List[Dict]:
        """模擬同步爬取"""
        self.call_count += 1
        time.sleep(self.delay)
        
        if self.should_fail:
            raise Exception(f"Mock scraper failure for {self.site_name}")
        
        return self.response_data[:results_wanted]
    
    async def scrape_async(self, search_term: str, location: str, 
                          results_wanted: int = 10, **kwargs) -> List[Dict]:
        """模擬非同步爬取"""
        self.call_count += 1
        await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise Exception(f"Mock async scraper failure for {self.site_name}")
        
        return self.response_data[:results_wanted]


class MockCache:
    """Mock 快取類別"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        if key in self._cache:
            # 檢查是否過期
            if time.time() - self._timestamps[key] < self.ttl:
                self.hit_count += 1
                return self._cache[key]
            else:
                # 過期，刪除
                del self._cache[key]
                del self._timestamps[key]
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """設置快取值"""
        # 如果快取已滿，刪除最舊的項目
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._timestamps.keys(), 
                           key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """清空快取"""
        self._cache.clear()
        self._timestamps.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    @property
    def hit_rate(self) -> float:
        """快取命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


class MockMetrics:
    """Mock 效能指標類別"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_times": [],
            "memory_usage": [],
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.start_time = time.time()
    
    def record_request(self, success: bool, response_time: float, 
                      memory_usage: float = None):
        """記錄請求指標"""
        self.metrics["requests_total"] += 1
        if success:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        self.metrics["response_times"].append(response_time)
        
        if memory_usage:
            self.metrics["memory_usage"].append(memory_usage)
    
    def record_cache_hit(self):
        """記錄快取命中"""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """記錄快取未命中"""
        self.metrics["cache_misses"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        response_times = self.metrics["response_times"]
        return {
            "total_requests": self.metrics["requests_total"],
            "success_rate": (
                self.metrics["requests_successful"] / 
                max(self.metrics["requests_total"], 1)
            ),
            "avg_response_time": (
                sum(response_times) / len(response_times) 
                if response_times else 0
            ),
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / 
                max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1)
            ),
            "total_time": time.time() - self.start_time
        }


class NetworkDelaySimulator:
    """網路延遲模擬器"""
    
    def __init__(self, min_delay: float = 0.1, max_delay: float = 2.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
    
    def simulate_delay(self):
        """模擬網路延遲"""
        import random
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        return delay
    
    async def simulate_async_delay(self):
        """模擬非同步網路延遲"""
        import random
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        return delay


# ==================== 測試輔助函數 ====================

def create_temp_directory() -> str:
    """創建臨時目錄"""
    return tempfile.mkdtemp(prefix="jobseeker_test_")


def cleanup_temp_directory(temp_dir: str) -> None:
    """清理臨時目錄"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@contextmanager
def temporary_directory():
    """臨時目錄上下文管理器"""
    temp_dir = create_temp_directory()
    try:
        yield temp_dir
    finally:
        cleanup_temp_directory(temp_dir)


@contextmanager
def mock_environment_variables(**env_vars):
    """Mock 環境變數上下文管理器"""
    original_env = {}
    
    # 保存原始環境變數
    for key in env_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # 設置新的環境變數
    for key, value in env_vars.items():
        os.environ[key] = str(value)
    
    try:
        yield
    finally:
        # 恢復原始環境變數
        for key in env_vars:
            if key in original_env:
                os.environ[key] = original_env[key]
            else:
                os.environ.pop(key, None)


@asynccontextmanager
async def async_timer():
    """非同步計時器上下文管理器"""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        print(f"執行時間: {end_time - start_time:.2f} 秒")


def measure_memory_usage() -> float:
    """測量當前記憶體使用量 (MB)"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def measure_execution_time(func: Callable) -> Callable:
    """測量函數執行時間的裝飾器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} 執行時間: {execution_time:.2f} 秒")
        return result
    return wrapper


def measure_async_execution_time(func: Callable) -> Callable:
    """測量非同步函數執行時間的裝飾器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} 執行時間: {execution_time:.2f} 秒")
        return result
    return wrapper


def create_mock_requests_session(responses: List[MockResponse]) -> Mock:
    """創建 Mock requests session"""
    session = Mock()
    session.get.side_effect = responses
    return session


def create_mock_aiohttp_session(responses: List[MockAsyncResponse]) -> AsyncMock:
    """創建 Mock aiohttp session"""
    session = AsyncMock()
    session.get.return_value.__aenter__.side_effect = responses
    return session


def generate_test_jobs(count: int, site: str = "indeed") -> List[Dict]:
    """生成測試職位資料"""
    jobs = []
    for i in range(count):
        job = SAMPLE_JOB_DATA.copy()
        job["title"] = f"{job['title']} {i+1}"
        job["job_url"] = f"https://example.com/job/{i+1}"
        job["site"] = site
        jobs.append(job)
    return jobs


def create_mock_job_data(num_jobs: int = 3) -> List[Dict]:
    """創建 Mock 工作資料"""
    return SAMPLE_JOBS_LIST[:num_jobs]


def create_test_dataframe(jobs: List[Dict] = None) -> pd.DataFrame:
    """創建測試用的 DataFrame"""
    if jobs is None:
        jobs = SAMPLE_JOBS_LIST[:5]
    
    return pd.DataFrame(jobs)


def validate_dataframe_structure(df: pd.DataFrame, 
                               required_columns: List[str] = None) -> List[str]:
    """驗證 DataFrame 結構"""
    errors = []
    
    if required_columns is None:
        required_columns = ["title", "company", "location", "site"]
    
    # 檢查必要欄位
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        errors.append(f"缺少欄位: {missing_columns}")
    
    # 檢查資料類型
    for column in required_columns:
        if column in df.columns:
            if df[column].dtype == 'object':
                # 檢查是否有空值
                null_count = df[column].isnull().sum()
                if null_count > 0:
                    errors.append(f"欄位 {column} 有 {null_count} 個空值")
    
    return errors


def compare_job_data(job1: Dict, job2: Dict, 
                    ignore_fields: List[str] = None) -> bool:
    """比較兩個職位資料是否相同"""
    if ignore_fields is None:
        ignore_fields = ["date_posted", "job_url"]
    
    for key in job1:
        if key not in ignore_fields:
            if job1.get(key) != job2.get(key):
                return False
    
    return True


def simulate_network_delay(min_delay: float = 0.1, max_delay: float = 1.0):
    """模擬網路延遲"""
    import random
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


async def simulate_async_network_delay(min_delay: float = 0.1, 
                                     max_delay: float = 1.0):
    """模擬非同步網路延遲"""
    import random
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)


def create_error_scenario(error_type: str) -> Exception:
    """創建錯誤場景"""
    error_map = {
        "timeout": requests.exceptions.Timeout("Request timed out"),
        "connection": requests.exceptions.ConnectionError("Connection failed"),
        "http_404": requests.exceptions.HTTPError("404 Not Found"),
        "http_429": requests.exceptions.HTTPError("429 Too Many Requests"),
        "parsing": ValueError("Failed to parse response"),
        "generic": Exception("Generic error")
    }
    
    return error_map.get(error_type, error_map["generic"])


def run_concurrent_test(func: Callable, args_list: List[tuple], 
                       max_workers: int = 5) -> List[Any]:
    """執行並發測試"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, *args) for args in args_list]
        results = [future.result() for future in futures]
    return results


async def run_async_concurrent_test(func: Callable, args_list: List[tuple],
                                  max_concurrent: int = 5) -> List[Any]:
    """執行非同步並發測試"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_func(*args):
        async with semaphore:
            return await func(*args)
    
    tasks = [limited_func(*args) for args in args_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


def assert_performance_within_limits(execution_time: float, 
                                    memory_usage: float,
                                    max_time: float = 60.0,
                                    max_memory: float = 500.0):
    """斷言效能在限制範圍內"""
    assert execution_time <= max_time, (
        f"執行時間 {execution_time:.2f}s 超過限制 {max_time}s"
    )
    assert memory_usage <= max_memory, (
        f"記憶體使用 {memory_usage:.2f}MB 超過限制 {max_memory}MB"
    )


def create_stress_test_scenario(duration: int = 60, 
                              requests_per_second: int = 10) -> Dict[str, Any]:
    """創建壓力測試場景"""
    return {
        "duration": duration,
        "requests_per_second": requests_per_second,
        "total_requests": duration * requests_per_second,
        "request_interval": 1.0 / requests_per_second
    }


def monitor_system_resources() -> Dict[str, float]:
    """監控系統資源使用情況"""
    process = psutil.Process()
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "num_threads": process.num_threads(),
        "open_files": len(process.open_files())
    }


class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.samples = []
        self.monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self):
        """開始監控"""
        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def _monitor_loop(self):
        """監控循環"""
        while self.monitoring:
            sample = {
                "timestamp": time.time(),
                **monitor_system_resources()
            }
            self.samples.append(sample)
            time.sleep(self.sample_interval)
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取監控摘要"""
        if not self.samples:
            return {}
        
        cpu_values = [s["cpu_percent"] for s in self.samples]
        memory_values = [s["memory_mb"] for s in self.samples]
        
        return {
            "duration": self.samples[-1]["timestamp"] - self.samples[0]["timestamp"],
            "samples_count": len(self.samples),
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "max_memory_mb": max(memory_values),
            "peak_threads": max(s["num_threads"] for s in self.samples)
        }


# ==================== 測試裝飾器 ====================

def skip_if_no_network(func):
    """如果沒有網路連接則跳過測試"""
    import pytest
    
    def check_network():
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except:
            return False
    
    return pytest.mark.skipif(
        not check_network(),
        reason="需要網路連接"
    )(func)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """失敗時重試的裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


def timeout_test(timeout_seconds: float = 30.0):
    """測試超時裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"測試超時 ({timeout_seconds}s)")
            
            # 設置超時信號
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超時
                return result
            except TimeoutError:
                signal.alarm(0)
                raise
        return wrapper
    return decorator


# ==================== 導出所有工具 ====================

__all__ = [
    # Mock 類別
    "MockResponse",
    "MockHTTPResponse",
    "MockAsyncResponse",
    "MockScraper",
    "MockCache",
    "MockMetrics",
    "NetworkDelaySimulator",
    
    # 輔助函數
    "create_temp_directory",
    "cleanup_temp_directory",
    "temporary_directory",
    "mock_environment_variables",
    "async_timer",
    "measure_memory_usage",
    "measure_execution_time",
    "measure_async_execution_time",
    
    # Mock 創建函數
    "create_mock_requests_session",
    "create_mock_aiohttp_session",
    
    # 測試資料生成
    "create_mock_job_data",
    "generate_test_jobs",
    "create_test_dataframe",
    "validate_dataframe_structure",
    "compare_job_data",
    
    # 網路模擬
    "simulate_network_delay",
    "simulate_async_network_delay",
    "create_error_scenario",
    
    # 並發測試
    "run_concurrent_test",
    "run_async_concurrent_test",
    
    # 效能測試
    "assert_performance_within_limits",
    "create_stress_test_scenario",
    "monitor_system_resources",
    "PerformanceMonitor",
    
    # 測試裝飾器
    "skip_if_no_network",
    "retry_on_failure",
    "timeout_test"
]