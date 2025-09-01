#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 效能測試

這個檔案包含了 JobSpy 的效能測試，用於測試系統在不同負載下的表現，
包括響應時間、吞吐量、記憶體使用等指標。

作者: JobSpy Team
日期: 2024
"""

import pytest
import pandas as pd
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import gc
import sys
from pathlib import Path

# JobSpy 模組導入
from jobspy import scrape_jobs
try:
    from jobspy import scrape_jobs_async, create_async_config
    from jobspy.async_scraping import AsyncConfig, AsyncMode, ConcurrencyLevel
except ImportError:
    scrape_jobs_async = None
    create_async_config = None
    AsyncConfig = None
    AsyncMode = None
    ConcurrencyLevel = None

try:
    from jobspy.cache_system import JobCache
except ImportError:
    JobCache = None

try:
    from jobspy.performance_monitoring import ScrapingMetrics
except ImportError:
    ScrapingMetrics = None


class PerformanceMonitor:
    """效能監控輔助類"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        self.cpu_percent = []
    
    def start(self):
        """開始監控"""
        gc.collect()  # 清理記憶體
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.cpu_percent = []
    
    def update(self):
        """更新監控數據"""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        cpu = psutil.cpu_percent()
        self.cpu_percent.append(cpu)
    
    def stop(self):
        """停止監控"""
        self.end_time = time.time()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    def get_stats(self):
        """獲取效能統計"""
        return {
            'duration': self.end_time - self.start_time if self.end_time else None,
            'memory_start': self.start_memory,
            'memory_end': self.end_memory,
            'memory_peak': self.peak_memory,
            'memory_delta': self.end_memory - self.start_memory if self.end_memory else None,
            'avg_cpu': sum(self.cpu_percent) / len(self.cpu_percent) if self.cpu_percent else 0
        }


class TestBasicPerformance:
    """基本效能測試"""
    
    @pytest.mark.performance
    def test_single_request_performance(self):
        """測試單一請求效能"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        start_time = time.time()
        
        result = scrape_jobs(
            site_name="indeed",
            search_term="python",
            location="Sydney",
            results_wanted=5
        )
        
        end_time = time.time()
        monitor.stop()
        
        duration = end_time - start_time
        stats = monitor.get_stats()
        
        # 效能斷言
        assert duration < 30.0, f"單一請求耗時過長: {duration:.2f}秒"
        assert stats['memory_delta'] < 100, f"記憶體使用過多: {stats['memory_delta']:.2f}MB"
        
        print(f"單一請求效能 - 耗時: {duration:.2f}秒, 記憶體: {stats['memory_delta']:.2f}MB")
        
        if isinstance(result, pd.DataFrame):
            print(f"獲取職位數量: {len(result)}")
    
    @pytest.mark.performance
    def test_multiple_requests_performance(self):
        """測試多重請求效能"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        requests = [
            {"site_name": "indeed", "search_term": "python", "location": "Sydney"},
            {"site_name": "indeed", "search_term": "javascript", "location": "Melbourne"},
            {"site_name": "indeed", "search_term": "java", "location": "Brisbane"},
        ]
        
        start_time = time.time()
        results = []
        
        for req in requests:
            try:
                result = scrape_jobs(
                    site_name=req["site_name"],
                    search_term=req["search_term"],
                    location=req["location"],
                    results_wanted=3
                )
                results.append(result)
                monitor.update()
                time.sleep(0.5)  # 避免過於頻繁的請求
            except Exception as e:
                print(f"請求失敗: {e}")
                continue
        
        end_time = time.time()
        monitor.stop()
        
        duration = end_time - start_time
        stats = monitor.get_stats()
        
        # 效能斷言
        assert duration < 60.0, f"多重請求耗時過長: {duration:.2f}秒"
        assert stats['memory_delta'] < 200, f"記憶體使用過多: {stats['memory_delta']:.2f}MB"
        
        successful_requests = len([r for r in results if isinstance(r, pd.DataFrame)])
        print(f"多重請求效能 - 耗時: {duration:.2f}秒, 成功: {successful_requests}/{len(requests)}")
        print(f"記憶體使用: {stats['memory_delta']:.2f}MB, 峰值: {stats['peak_memory']:.2f}MB")
    
    @pytest.mark.performance
    def test_large_result_set_performance(self):
        """測試大結果集效能"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        start_time = time.time()
        
        result = scrape_jobs(
            site_name="indeed",
            search_term="software",
            location="Sydney",
            results_wanted=50  # 較大的結果集
        )
        
        end_time = time.time()
        monitor.stop()
        
        duration = end_time - start_time
        stats = monitor.get_stats()
        
        # 效能斷言
        assert duration < 120.0, f"大結果集請求耗時過長: {duration:.2f}秒"
        
        if isinstance(result, pd.DataFrame):
            result_count = len(result)
            throughput = result_count / duration if duration > 0 else 0
            
            print(f"大結果集效能 - 耗時: {duration:.2f}秒, 結果: {result_count}個")
            print(f"吞吐量: {throughput:.2f} 職位/秒")
            print(f"記憶體使用: {stats['memory_delta']:.2f}MB")


class TestConcurrentPerformance:
    """並發效能測試"""
    
    @pytest.mark.performance
    def test_thread_pool_performance(self):
        """測試執行緒池效能"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        def scrape_task(params):
            """爬取任務"""
            try:
                return scrape_jobs(
                    site_name=params["site"],
                    search_term=params["term"],
                    location=params["location"],
                    results_wanted=3
                )
            except Exception as e:
                return f"錯誤: {e}"
        
        # 準備任務
        tasks = [
            {"site": "indeed", "term": "python", "location": "Sydney"},
            {"site": "indeed", "term": "javascript", "location": "Melbourne"},
            {"site": "indeed", "term": "java", "location": "Brisbane"},
            {"site": "indeed", "term": "react", "location": "Perth"},
        ]
        
        start_time = time.time()
        
        # 使用執行緒池
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_task = {executor.submit(scrape_task, task): task for task in tasks}
            results = []
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                    monitor.update()
                except Exception as e:
                    print(f"任務失敗 {task}: {e}")
                    results.append(None)
        
        end_time = time.time()
        monitor.stop()
        
        duration = end_time - start_time
        stats = monitor.get_stats()
        
        successful_results = [r for r in results if isinstance(r, pd.DataFrame)]
        
        # 效能斷言
        assert duration < 45.0, f"並發請求耗時過長: {duration:.2f}秒"
        assert len(successful_results) > 0, "至少應該有一個成功的結果"
        
        print(f"執行緒池效能 - 耗時: {duration:.2f}秒, 成功: {len(successful_results)}/{len(tasks)}")
        print(f"平均 CPU 使用率: {stats['avg_cpu']:.1f}%")
        print(f"記憶體使用: {stats['memory_delta']:.2f}MB")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_async_concurrent_performance(self):
        """測試非同步並發效能"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        # 準備非同步任務
        tasks = [
            scrape_jobs_async(
                site_name=["indeed"],
                search_term="python",
                location="Sydney",
                results_wanted=3
            ),
            scrape_jobs_async(
                site_name=["indeed"],
                search_term="javascript",
                location="Melbourne",
                results_wanted=3
            ),
            scrape_jobs_async(
                site_name=["indeed"],
                search_term="java",
                location="Brisbane",
                results_wanted=3
            ),
        ]
        
        start_time = time.time()
        
        # 並發執行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        monitor.stop()
        
        duration = end_time - start_time
        stats = monitor.get_stats()
        
        successful_results = [r for r in results if isinstance(r, pd.DataFrame)]
        
        # 效能斷言
        assert duration < 30.0, f"非同步並發耗時過長: {duration:.2f}秒"
        
        print(f"非同步並發效能 - 耗時: {duration:.2f}秒, 成功: {len(successful_results)}/{len(tasks)}")
        print(f"記憶體使用: {stats['memory_delta']:.2f}MB")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_async_vs_sync_performance(self):
        """測試非同步 vs 同步效能比較"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        search_params = {
            "search_term": "python developer",
            "location": "Sydney",
            "results_wanted": 5
        }
        
        # 同步測試
        sync_monitor = PerformanceMonitor()
        sync_monitor.start()
        
        sync_start = time.time()
        sync_results = []
        
        for site in ["indeed", "linkedin"]:
            try:
                result = scrape_jobs(
                    site_name=site,
                    **search_params
                )
                sync_results.append(result)
                time.sleep(0.5)  # 模擬請求間隔
            except Exception as e:
                print(f"同步請求失敗 {site}: {e}")
        
        sync_duration = time.time() - sync_start
        sync_monitor.stop()
        sync_stats = sync_monitor.get_stats()
        
        # 非同步測試
        async_monitor = PerformanceMonitor()
        async_monitor.start()
        
        async_start = time.time()
        
        async_tasks = [
            scrape_jobs_async(
                site_name=["indeed"],
                **search_params
            ),
            scrape_jobs_async(
                site_name=["linkedin"],
                **search_params
            )
        ]
        
        async_results = await asyncio.gather(*async_tasks, return_exceptions=True)
        async_duration = time.time() - async_start
        async_monitor.stop()
        async_stats = async_monitor.get_stats()
        
        # 效能比較
        sync_successful = len([r for r in sync_results if isinstance(r, pd.DataFrame)])
        async_successful = len([r for r in async_results if isinstance(r, pd.DataFrame)])
        
        print(f"\n=== 效能比較 ===")
        print(f"同步模式 - 耗時: {sync_duration:.2f}秒, 成功: {sync_successful}")
        print(f"非同步模式 - 耗時: {async_duration:.2f}秒, 成功: {async_successful}")
        
        if async_duration > 0 and sync_duration > 0:
            speedup = sync_duration / async_duration
            print(f"速度提升: {speedup:.2f}x")
        
        print(f"同步記憶體使用: {sync_stats['memory_delta']:.2f}MB")
        print(f"非同步記憶體使用: {async_stats['memory_delta']:.2f}MB")


class TestCachePerformance:
    """快取效能測試"""
    
    @pytest.mark.performance
    def test_cache_hit_performance(self, temp_dir):
        """測試快取命中效能"""
        if JobCache is None:
            pytest.skip("快取系統尚未實現")
        
        cache_dir = temp_dir / "perf_cache"
        cache = JobCache(cache_dir=str(cache_dir))
        
        search_params = {
            "site_name": "indeed",
            "search_term": "test",
            "location": "Sydney",
            "results_wanted": 5
        }
        
        # 第一次請求（快取未命中）
        miss_start = time.time()
        result1 = scrape_jobs(**search_params)
        miss_duration = time.time() - miss_start
        
        # 模擬快取存儲
        cache_key = cache._generate_cache_key(search_params)
        if isinstance(result1, pd.DataFrame) and len(result1) > 0:
            cache.set(cache_key, result1.to_dict('records'))
        
        # 第二次請求（快取命中）
        hit_start = time.time()
        cached_result = cache.get(cache_key)
        hit_duration = time.time() - hit_start
        
        if cached_result:
            # 效能斷言
            assert hit_duration < miss_duration, "快取命中應該更快"
            
            speedup = miss_duration / hit_duration if hit_duration > 0 else float('inf')
            print(f"快取效能 - 未命中: {miss_duration:.3f}秒, 命中: {hit_duration:.3f}秒")
            print(f"快取速度提升: {speedup:.2f}x")
        
        # 測試快取統計效能
        stats_start = time.time()
        stats = cache.get_stats()
        stats_duration = time.time() - stats_start
        
        assert stats_duration < 0.1, "快取統計獲取應該很快"
        print(f"快取統計耗時: {stats_duration:.3f}秒")
    
    @pytest.mark.performance
    def test_cache_memory_usage(self, temp_dir):
        """測試快取記憶體使用"""
        if JobCache is None:
            pytest.skip("快取系統尚未實現")
        
        cache_dir = temp_dir / "memory_cache"
        cache = JobCache(cache_dir=str(cache_dir), max_size=100)
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        # 添加大量快取項目
        for i in range(50):
            key = f"test_key_{i}"
            value = {
                "jobs": [
                    {
                        "title": f"Job {j}",
                        "company": f"Company {j}",
                        "location": "Test Location",
                        "description": "Test description " * 10  # 較大的描述
                    }
                    for j in range(10)
                ]
            }
            cache.set(key, value)
            
            if i % 10 == 0:
                monitor.update()
        
        monitor.stop()
        stats = monitor.get_stats()
        
        # 檢查記憶體使用
        cache_stats = cache.get_stats()
        
        print(f"快取記憶體測試 - 項目數: {cache_stats.size}")
        print(f"記憶體增長: {stats['memory_delta']:.2f}MB")
        print(f"峰值記憶體: {stats['peak_memory']:.2f}MB")
        
        # 記憶體使用應該合理
        assert stats['memory_delta'] < 500, "快取記憶體使用過多"


class TestScalabilityPerformance:
    """可擴展性效能測試"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_increasing_load_performance(self):
        """測試遞增負載效能"""
        load_levels = [1, 3, 5, 8]
        results = {}
        
        for load in load_levels:
            monitor = PerformanceMonitor()
            monitor.start()
            
            start_time = time.time()
            
            # 執行指定數量的請求
            successful_requests = 0
            for i in range(load):
                try:
                    result = scrape_jobs(
                        site_name="indeed",
                        search_term=f"test{i}",
                        location="Sydney",
                        results_wanted=2
                    )
                    if isinstance(result, pd.DataFrame):
                        successful_requests += 1
                    
                    time.sleep(0.5)  # 避免過於頻繁的請求
                    monitor.update()
                    
                except Exception as e:
                    print(f"負載 {load} 中的請求 {i} 失敗: {e}")
            
            duration = time.time() - start_time
            monitor.stop()
            stats = monitor.get_stats()
            
            results[load] = {
                'duration': duration,
                'successful_requests': successful_requests,
                'throughput': successful_requests / duration if duration > 0 else 0,
                'memory_delta': stats['memory_delta'],
                'avg_cpu': stats['avg_cpu']
            }
            
            print(f"負載 {load} - 耗時: {duration:.2f}秒, 成功: {successful_requests}/{load}")
            print(f"  吞吐量: {results[load]['throughput']:.2f} 請求/秒")
            print(f"  記憶體: {stats['memory_delta']:.2f}MB, CPU: {stats['avg_cpu']:.1f}%")
        
        # 分析可擴展性
        print("\n=== 可擴展性分析 ===")
        for load in load_levels:
            r = results[load]
            print(f"負載 {load}: 吞吐量 {r['throughput']:.2f}, 記憶體 {r['memory_delta']:.1f}MB")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_async_scalability_performance(self):
        """測試非同步可擴展性效能"""
        if scrape_jobs_async is None:
            pytest.skip("非同步功能尚未實現")
        
        concurrency_levels = [2, 4, 6, 8]
        results = {}
        
        for concurrency in concurrency_levels:
            monitor = PerformanceMonitor()
            monitor.start()
            
            # 創建非同步任務
            tasks = []
            for i in range(concurrency):
                task = scrape_jobs_async(
                    site_name=["indeed"],
                    search_term=f"test{i}",
                    location="Sydney",
                    results_wanted=2,
                    max_concurrent_requests=concurrency
                )
                tasks.append(task)
            
            start_time = time.time()
            
            # 並發執行
            async_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            monitor.stop()
            stats = monitor.get_stats()
            
            successful_results = len([r for r in async_results if isinstance(r, pd.DataFrame)])
            
            results[concurrency] = {
                'duration': duration,
                'successful_requests': successful_results,
                'throughput': successful_results / duration if duration > 0 else 0,
                'memory_delta': stats['memory_delta']
            }
            
            print(f"並發 {concurrency} - 耗時: {duration:.2f}秒, 成功: {successful_results}/{concurrency}")
            print(f"  吞吐量: {results[concurrency]['throughput']:.2f} 請求/秒")
            print(f"  記憶體: {stats['memory_delta']:.2f}MB")
        
        # 分析非同步可擴展性
        print("\n=== 非同步可擴展性分析 ===")
        for concurrency in concurrency_levels:
            r = results[concurrency]
            print(f"並發 {concurrency}: 吞吐量 {r['throughput']:.2f}, 記憶體 {r['memory_delta']:.1f}MB")


class TestMemoryPerformance:
    """記憶體效能測試"""
    
    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """測試記憶體洩漏檢測"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 執行多次爬取操作
        for i in range(10):
            try:
                result = scrape_jobs(
                    site_name="indeed",
                    search_term=f"test{i}",
                    location="Sydney",
                    results_wanted=2
                )
                
                # 強制垃圾回收
                del result
                gc.collect()
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"記憶體測試中的請求 {i} 失敗: {e}")
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        print(f"記憶體洩漏測試 - 初始: {initial_memory:.2f}MB, 最終: {final_memory:.2f}MB")
        print(f"記憶體增長: {memory_growth:.2f}MB")
        
        # 記憶體增長應該在合理範圍內
        assert memory_growth < 100, f"可能存在記憶體洩漏: {memory_growth:.2f}MB"
    
    @pytest.mark.performance
    def test_large_dataset_memory_usage(self):
        """測試大資料集記憶體使用"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        # 請求大量資料
        try:
            result = scrape_jobs(
                site_name="indeed",
                search_term="software",
                location="Sydney",
                results_wanted=100  # 大資料集
            )
            
            monitor.stop()
            stats = monitor.get_stats()
            
            if isinstance(result, pd.DataFrame):
                # 計算每個職位的平均記憶體使用
                if len(result) > 0:
                    memory_per_job = stats['memory_delta'] / len(result)
                    print(f"大資料集記憶體測試 - 職位數: {len(result)}")
                    print(f"總記憶體使用: {stats['memory_delta']:.2f}MB")
                    print(f"每個職位記憶體: {memory_per_job:.3f}MB")
                    
                    # 每個職位的記憶體使用應該合理
                    assert memory_per_job < 1.0, "每個職位記憶體使用過多"
            
        except Exception as e:
            print(f"大資料集測試失敗: {e}")
            monitor.stop()


# ==================== 效能基準測試 ====================

@pytest.mark.performance
@pytest.mark.benchmark
def test_performance_baseline():
    """效能基準測試"""
    print("\n=== JobSpy 效能基準測試 ===")
    
    # 系統資訊
    print(f"Python 版本: {sys.version}")
    print(f"CPU 核心數: {psutil.cpu_count()}")
    print(f"總記憶體: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
    
    # 基準測試參數
    test_cases = [
        {"name": "小型請求", "results_wanted": 5, "expected_time": 15},
        {"name": "中型請求", "results_wanted": 20, "expected_time": 30},
        {"name": "大型請求", "results_wanted": 50, "expected_time": 60},
    ]
    
    baseline_results = {}
    
    for test_case in test_cases:
        monitor = PerformanceMonitor()
        monitor.start()
        
        start_time = time.time()
        
        try:
            result = scrape_jobs(
                site_name="indeed",
                search_term="python",
                location="Sydney",
                results_wanted=test_case["results_wanted"]
            )
            
            duration = time.time() - start_time
            monitor.stop()
            stats = monitor.get_stats()
            
            baseline_results[test_case["name"]] = {
                'duration': duration,
                'expected_time': test_case["expected_time"],
                'result_count': len(result) if isinstance(result, pd.DataFrame) else 0,
                'memory_usage': stats['memory_delta'],
                'passed': duration <= test_case["expected_time"]
            }
            
            status = "✓" if duration <= test_case["expected_time"] else "✗"
            print(f"{status} {test_case['name']}: {duration:.2f}s (預期 ≤ {test_case['expected_time']}s)")
            print(f"  結果數量: {baseline_results[test_case['name']]['result_count']}")
            print(f"  記憶體使用: {stats['memory_delta']:.2f}MB")
            
        except Exception as e:
            print(f"✗ {test_case['name']}: 測試失敗 - {e}")
            baseline_results[test_case["name"]] = {
                'duration': None,
                'passed': False,
                'error': str(e)
            }
    
    # 總結
    passed_tests = sum(1 for r in baseline_results.values() if r.get('passed', False))
    total_tests = len(test_cases)
    
    print(f"\n基準測試結果: {passed_tests}/{total_tests} 通過")
    
    return baseline_results


@pytest.mark.performance
@pytest.mark.stress
def test_stress_test():
    """壓力測試"""
    print("\n=== JobSpy 壓力測試 ===")
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    # 壓力測試參數
    stress_duration = 60  # 秒
    request_interval = 2  # 秒
    
    start_time = time.time()
    request_count = 0
    successful_requests = 0
    errors = []
    
    while time.time() - start_time < stress_duration:
        try:
            result = scrape_jobs(
                site_name="indeed",
                search_term=f"test{request_count}",
                location="Sydney",
                results_wanted=3
            )
            
            if isinstance(result, pd.DataFrame):
                successful_requests += 1
            
            request_count += 1
            monitor.update()
            
            time.sleep(request_interval)
            
        except Exception as e:
            errors.append(str(e))
            request_count += 1
            time.sleep(request_interval)
    
    monitor.stop()
    stats = monitor.get_stats()
    
    # 壓力測試結果
    success_rate = (successful_requests / request_count * 100) if request_count > 0 else 0
    
    print(f"壓力測試結果:")
    print(f"  測試時長: {stats['duration']:.1f}秒")
    print(f"  總請求數: {request_count}")
    print(f"  成功請求: {successful_requests}")
    print(f"  成功率: {success_rate:.1f}%")
    print(f"  錯誤數: {len(errors)}")
    print(f"  平均 CPU: {stats['avg_cpu']:.1f}%")
    print(f"  記憶體使用: {stats['memory_delta']:.2f}MB")
    
    # 壓力測試斷言
    assert success_rate >= 70, f"成功率過低: {success_rate:.1f}%"
    assert stats['memory_delta'] < 300, f"記憶體使用過多: {stats['memory_delta']:.2f}MB"
    
    if errors:
        print(f"\n錯誤樣本 (前5個):")
        for error in errors[:5]:
            print(f"  - {error}")