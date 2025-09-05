#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM壓力測試工具
用於測試LLM模型在高負載、並發和極端條件下的表現

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
import threading
import statistics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from enum import Enum
import random
import psutil
import gc
from pathlib import Path
import queue
import multiprocessing as mp

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from jobseeker.llm_config import LLMConfigManager


class StressTestType(Enum):
    """壓力測試類型"""
    CONCURRENT_LOAD = "concurrent_load"  # 並發負載測試
    SUSTAINED_LOAD = "sustained_load"  # 持續負載測試
    BURST_LOAD = "burst_load"  # 突發負載測試
    MEMORY_STRESS = "memory_stress"  # 記憶體壓力測試
    RATE_LIMITING = "rate_limiting"  # 速率限制測試
    TIMEOUT_STRESS = "timeout_stress"  # 超時壓力測試
    ERROR_RECOVERY = "error_recovery"  # 錯誤恢復測試
    SCALABILITY = "scalability"  # 擴展性測試


class LoadPattern(Enum):
    """負載模式"""
    CONSTANT = "constant"  # 恆定負載
    RAMP_UP = "ramp_up"  # 逐漸增加
    RAMP_DOWN = "ramp_down"  # 逐漸減少
    SPIKE = "spike"  # 尖峰負載
    WAVE = "wave"  # 波浪式負載
    RANDOM = "random"  # 隨機負載


@dataclass
class StressTestConfig:
    """壓力測試配置"""
    test_type: StressTestType
    load_pattern: LoadPattern
    duration_seconds: int
    max_concurrent_requests: int
    requests_per_second: float
    ramp_up_time: int = 0
    ramp_down_time: int = 0
    burst_interval: int = 10
    burst_duration: int = 5
    timeout_seconds: float = 30.0
    memory_limit_mb: int = 1024
    error_threshold: float = 0.1
    retry_attempts: int = 3
    cool_down_time: int = 5
    enable_monitoring: bool = True
    save_detailed_logs: bool = True


@dataclass
class StressTestResult:
    """壓力測試結果"""
    test_id: str
    provider: str
    config: StressTestConfig
    start_time: str
    end_time: str
    total_duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    timeout_requests: int
    error_requests: int
    success_rate: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    throughput: float  # 每秒成功請求數
    peak_memory_usage: float  # MB
    avg_memory_usage: float  # MB
    cpu_usage_stats: Dict[str, float]
    error_distribution: Dict[str, int]
    response_time_distribution: List[float]
    latency_percentiles: Dict[str, float]
    stability_score: float
    performance_degradation: float
    resource_efficiency: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    active_threads: int
    open_files: int
    network_connections: int


class SystemMonitor:
    """系統監控器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.metrics: List[SystemMetrics] = []
        self.monitoring = False
        self.monitor_thread = None
        self.process = psutil.Process()
    
    def start_monitoring(self) -> None:
        """開始監控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.metrics.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """停止監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self) -> None:
        """監控循環"""
        while self.monitoring:
            try:
                # 收集系統指標
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                
                # 線程和文件描述符
                try:
                    num_threads = self.process.num_threads()
                    num_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
                except (psutil.AccessDenied, AttributeError):
                    num_threads = 0
                    num_fds = 0
                
                # 網路連接
                try:
                    connections = len(self.process.connections())
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    connections = 0
                
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_used_mb=memory_info.rss / 1024 / 1024,
                    active_threads=num_threads,
                    open_files=num_fds,
                    network_connections=connections
                )
                
                self.metrics.append(metrics)
                
                # 限制記錄數量，避免記憶體溢出
                if len(self.metrics) > 10000:
                    self.metrics = self.metrics[-5000:]
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"監控錯誤: {e}")
                time.sleep(self.interval)
    
    def get_peak_memory(self) -> float:
        """獲取峰值記憶體使用量"""
        if not self.metrics:
            return 0.0
        return max(m.memory_used_mb for m in self.metrics)
    
    def get_avg_memory(self) -> float:
        """獲取平均記憶體使用量"""
        if not self.metrics:
            return 0.0
        return statistics.mean(m.memory_used_mb for m in self.metrics)
    
    def get_cpu_stats(self) -> Dict[str, float]:
        """獲取CPU統計"""
        if not self.metrics:
            return {"avg": 0.0, "max": 0.0, "min": 0.0}
        
        cpu_values = [m.cpu_percent for m in self.metrics]
        return {
            "avg": statistics.mean(cpu_values),
            "max": max(cpu_values),
            "min": min(cpu_values)
        }


class LLMStressTestTool:
    """LLM壓力測試工具"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化壓力測試工具"""
        self.config_manager = LLMConfigManager()
        self.system_monitor = SystemMonitor()
        self.test_queries = self._generate_test_queries()
        self.results: List[StressTestResult] = []
        self.active_requests = 0
        self.request_lock = threading.Lock()
        
        # 設置隨機種子
        random.seed(42)
        np.random.seed(42)
    
    def _generate_test_queries(self) -> List[str]:
        """生成測試查詢"""
        return [
            # 簡單查詢
            "找工作",
            "我想找軟體工程師的工作",
            "Looking for data scientist position",
            "今天天氣如何？",
            "我想轉職",
            
            # 中等複雜度查詢
            "我想在台北找年薪80萬以上的Python開發工程師職位",
            "尋找有彈性工時的前端工程師工作，要求會React和Vue",
            "I want to find a remote machine learning engineer job with 5+ years experience",
            "什麼是人工智慧？",
            "我想學習新技能來提升職場競爭力",
            
            # 複雜查詢
            "我是一個有10年經驗的全端工程師，精通多種程式語言，現在想找技術主管職位，薪資期望150K以上，地點台北或新竹",
            "Looking for senior software architect position in fintech company, remote work preferred, salary 200K+, equity options",
            "我想了解資料科學領域的職涯發展路徑和所需技能",
            "如何在不同的科技公司之間做選擇？",
            "我想創業，需要什麼準備？",
            
            # 邊界案例
            "",
            "？！。",
            "123456",
            "工作" * 50,
            "a" * 1000,
            
            # 多語言查詢
            "データサイエンティストの仕事を探しています",
            "데이터 사이언티스트 일자리를 찾고 있습니다",
            "Je cherche un emploi d'ingénieur logiciel",
            "Ich suche eine Stelle als Softwareentwickler",
            "我想找软件工程师的工作",  # 簡體中文
        ]
    
    def run_stress_test(self, provider: LLMProvider, config: StressTestConfig) -> StressTestResult:
        """運行壓力測試"""
        test_id = f"stress_{provider.value}_{config.test_type.value}_{int(time.time())}"
        
        print(f"🚀 開始壓力測試: {test_id}")
        print(f"   提供商: {provider.value}")
        print(f"   測試類型: {config.test_type.value}")
        print(f"   負載模式: {config.load_pattern.value}")
        print(f"   持續時間: {config.duration_seconds}秒")
        print(f"   最大並發: {config.max_concurrent_requests}")
        print(f"   每秒請求: {config.requests_per_second}")
        
        # 開始系統監控
        if config.enable_monitoring:
            self.system_monitor.start_monitoring()
        
        start_time = time.time()
        start_time_str = datetime.now().isoformat()
        
        # 執行測試
        try:
            if config.test_type == StressTestType.CONCURRENT_LOAD:
                test_results = self._run_concurrent_load_test(provider, config)
            elif config.test_type == StressTestType.SUSTAINED_LOAD:
                test_results = self._run_sustained_load_test(provider, config)
            elif config.test_type == StressTestType.BURST_LOAD:
                test_results = self._run_burst_load_test(provider, config)
            elif config.test_type == StressTestType.MEMORY_STRESS:
                test_results = self._run_memory_stress_test(provider, config)
            elif config.test_type == StressTestType.RATE_LIMITING:
                test_results = self._run_rate_limiting_test(provider, config)
            elif config.test_type == StressTestType.TIMEOUT_STRESS:
                test_results = self._run_timeout_stress_test(provider, config)
            elif config.test_type == StressTestType.ERROR_RECOVERY:
                test_results = self._run_error_recovery_test(provider, config)
            elif config.test_type == StressTestType.SCALABILITY:
                test_results = self._run_scalability_test(provider, config)
            else:
                raise ValueError(f"不支援的測試類型: {config.test_type}")
        
        except Exception as e:
            print(f"❌ 測試執行失敗: {str(e)}")
            test_results = {
                "requests": [],
                "errors": [str(e)],
                "timeouts": [],
                "response_times": []
            }
        
        finally:
            # 停止系統監控
            if config.enable_monitoring:
                self.system_monitor.stop_monitoring()
        
        end_time = time.time()
        end_time_str = datetime.now().isoformat()
        total_duration = end_time - start_time
        
        # 分析結果
        result = self._analyze_stress_test_results(
            test_id, provider, config, start_time_str, end_time_str, 
            total_duration, test_results
        )
        
        self.results.append(result)
        
        print(f"✅ 壓力測試完成: {test_id}")
        print(f"   總請求數: {result.total_requests}")
        print(f"   成功率: {result.success_rate:.1%}")
        print(f"   平均響應時間: {result.avg_response_time:.2f}秒")
        print(f"   吞吐量: {result.throughput:.1f} 請求/秒")
        
        return result
    
    def _run_concurrent_load_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行並發負載測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        
        # 計算總請求數
        total_requests = int(config.duration_seconds * config.requests_per_second)
        
        # 使用線程池執行並發請求
        with ThreadPoolExecutor(max_workers=config.max_concurrent_requests) as executor:
            futures = []
            
            for i in range(total_requests):
                # 選擇測試查詢
                query = random.choice(self.test_queries)
                
                # 提交任務
                future = executor.submit(self._execute_single_request, analyzer, query, config.timeout_seconds)
                futures.append((future, time.time(), query))
                
                # 控制請求速率
                if i < total_requests - 1:
                    time.sleep(1.0 / config.requests_per_second)
            
            # 收集結果
            for future, submit_time, query in futures:
                try:
                    result = future.result(timeout=config.timeout_seconds + 5)
                    requests_data.append({
                        "query": query,
                        "submit_time": submit_time,
                        "result": result
                    })
                    
                    if result["success"]:
                        response_times.append(result["response_time"])
                    else:
                        errors.append(result["error"])
                        
                except Exception as e:
                    timeouts.append(str(e))
                    errors.append(str(e))
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times
        }
    
    def _run_sustained_load_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行持續負載測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        
        start_time = time.time()
        request_count = 0
        
        # 持續發送請求直到時間結束
        while time.time() - start_time < config.duration_seconds:
            query = random.choice(self.test_queries)
            
            try:
                result = self._execute_single_request(analyzer, query, config.timeout_seconds)
                
                requests_data.append({
                    "query": query,
                    "submit_time": time.time(),
                    "result": result
                })
                
                if result["success"]:
                    response_times.append(result["response_time"])
                else:
                    errors.append(result["error"])
                
                request_count += 1
                
                # 控制請求速率
                time.sleep(1.0 / config.requests_per_second)
                
            except Exception as e:
                errors.append(str(e))
                timeouts.append(str(e))
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times
        }
    
    def _run_burst_load_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行突發負載測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        
        start_time = time.time()
        
        while time.time() - start_time < config.duration_seconds:
            # 突發期間
            burst_start = time.time()
            burst_requests = []
            
            # 在突發期間發送大量並發請求
            with ThreadPoolExecutor(max_workers=config.max_concurrent_requests) as executor:
                futures = []
                
                # 在突發持續時間內發送請求
                while time.time() - burst_start < config.burst_duration:
                    query = random.choice(self.test_queries)
                    future = executor.submit(self._execute_single_request, analyzer, query, config.timeout_seconds)
                    futures.append((future, time.time(), query))
                    
                    time.sleep(0.1)  # 短暫間隔
                
                # 收集突發期間的結果
                for future, submit_time, query in futures:
                    try:
                        result = future.result(timeout=config.timeout_seconds + 5)
                        requests_data.append({
                            "query": query,
                            "submit_time": submit_time,
                            "result": result
                        })
                        
                        if result["success"]:
                            response_times.append(result["response_time"])
                        else:
                            errors.append(result["error"])
                            
                    except Exception as e:
                        timeouts.append(str(e))
                        errors.append(str(e))
            
            # 冷卻期間
            time.sleep(config.burst_interval - config.burst_duration)
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times
        }
    
    def _run_memory_stress_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行記憶體壓力測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        
        # 創建大量分析器實例來增加記憶體壓力
        analyzers = [LLMIntentAnalyzer(provider=provider) for _ in range(10)]
        
        # 創建大量測試數據
        large_queries = []
        for base_query in self.test_queries:
            # 創建更長的查詢來增加記憶體使用
            large_query = base_query + " " + "額外內容 " * 100
            large_queries.extend([large_query] * 10)
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < config.duration_seconds:
            # 隨機選擇分析器和查詢
            analyzer_instance = random.choice(analyzers)
            query = random.choice(large_queries)
            
            try:
                result = self._execute_single_request(analyzer_instance, query, config.timeout_seconds)
                
                requests_data.append({
                    "query": query[:100] + "...",  # 截斷顯示
                    "submit_time": time.time(),
                    "result": result
                })
                
                if result["success"]:
                    response_times.append(result["response_time"])
                else:
                    errors.append(result["error"])
                
                request_count += 1
                
                # 檢查記憶體使用量
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > config.memory_limit_mb:
                    print(f"⚠️ 記憶體使用量超過限制: {current_memory:.1f}MB > {config.memory_limit_mb}MB")
                    # 強制垃圾回收
                    gc.collect()
                
                time.sleep(1.0 / config.requests_per_second)
                
            except Exception as e:
                errors.append(str(e))
                timeouts.append(str(e))
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times
        }
    
    def _run_rate_limiting_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行速率限制測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        rate_limit_errors = []
        
        # 逐漸增加請求速率直到觸發限制
        current_rps = 1.0
        max_rps = config.requests_per_second
        rps_increment = 0.5
        
        start_time = time.time()
        
        while time.time() - start_time < config.duration_seconds and current_rps <= max_rps:
            print(f"   測試速率: {current_rps:.1f} 請求/秒")
            
            # 在當前速率下測試10秒
            rate_test_start = time.time()
            rate_test_duration = min(10, config.duration_seconds - (time.time() - start_time))
            
            while time.time() - rate_test_start < rate_test_duration:
                query = random.choice(self.test_queries)
                
                try:
                    result = self._execute_single_request(analyzer, query, config.timeout_seconds)
                    
                    requests_data.append({
                        "query": query,
                        "submit_time": time.time(),
                        "result": result,
                        "rps": current_rps
                    })
                    
                    if result["success"]:
                        response_times.append(result["response_time"])
                    else:
                        error_msg = result["error"]
                        errors.append(error_msg)
                        
                        # 檢查是否為速率限制錯誤
                        if any(keyword in error_msg.lower() for keyword in 
                               ["rate limit", "too many requests", "quota", "throttle"]):
                            rate_limit_errors.append({
                                "rps": current_rps,
                                "error": error_msg,
                                "time": time.time()
                            })
                    
                    time.sleep(1.0 / current_rps)
                    
                except Exception as e:
                    errors.append(str(e))
                    timeouts.append(str(e))
            
            # 增加請求速率
            current_rps += rps_increment
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times,
            "rate_limit_errors": rate_limit_errors
        }
    
    def _run_timeout_stress_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行超時壓力測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        
        # 使用不同的超時設置
        timeout_values = [1.0, 2.0, 5.0, 10.0, 15.0, 30.0]
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < config.duration_seconds:
            query = random.choice(self.test_queries)
            timeout = random.choice(timeout_values)
            
            try:
                result = self._execute_single_request(analyzer, query, timeout)
                
                requests_data.append({
                    "query": query,
                    "submit_time": time.time(),
                    "result": result,
                    "timeout_setting": timeout
                })
                
                if result["success"]:
                    response_times.append(result["response_time"])
                else:
                    errors.append(result["error"])
                
                request_count += 1
                time.sleep(1.0 / config.requests_per_second)
                
            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                
                if "timeout" in error_msg.lower():
                    timeouts.append({
                        "query": query,
                        "timeout_setting": timeout,
                        "error": error_msg,
                        "time": time.time()
                    })
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times
        }
    
    def _run_error_recovery_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行錯誤恢復測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        recovery_attempts = []
        
        # 故意引入錯誤的查詢
        error_queries = [
            None,  # 空查詢
            "",  # 空字符串
            "a" * 10000,  # 超長查詢
            "\x00\x01\x02",  # 特殊字符
            {"invalid": "object"},  # 錯誤類型
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < config.duration_seconds:
            # 隨機決定是否使用錯誤查詢
            if random.random() < 0.3:  # 30%機率使用錯誤查詢
                query = random.choice(error_queries)
            else:
                query = random.choice(self.test_queries)
            
            # 嘗試執行請求，包含重試機制
            for attempt in range(config.retry_attempts + 1):
                try:
                    if isinstance(query, str) or query is None:
                        result = self._execute_single_request(analyzer, query, config.timeout_seconds)
                    else:
                        # 故意觸發錯誤
                        raise ValueError(f"無效的查詢類型: {type(query)}")
                    
                    requests_data.append({
                        "query": str(query)[:100] if query else "None",
                        "submit_time": time.time(),
                        "result": result,
                        "attempt": attempt + 1
                    })
                    
                    if result["success"]:
                        response_times.append(result["response_time"])
                    else:
                        errors.append(result["error"])
                    
                    break  # 成功執行，跳出重試循環
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    if attempt < config.retry_attempts:
                        # 記錄重試嘗試
                        recovery_attempts.append({
                            "query": str(query)[:100] if query else "None",
                            "attempt": attempt + 1,
                            "error": error_msg,
                            "time": time.time()
                        })
                        
                        # 等待後重試
                        time.sleep(0.5 * (attempt + 1))  # 指數退避
                    else:
                        # 最終失敗
                        errors.append(error_msg)
                        timeouts.append(error_msg)
            
            time.sleep(1.0 / config.requests_per_second)
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times,
            "recovery_attempts": recovery_attempts
        }
    
    def _run_scalability_test(self, provider: LLMProvider, config: StressTestConfig) -> Dict[str, Any]:
        """運行擴展性測試"""
        analyzer = LLMIntentAnalyzer(provider=provider)
        
        requests_data = []
        errors = []
        timeouts = []
        response_times = []
        scalability_metrics = []
        
        # 逐漸增加並發數
        concurrent_levels = [1, 2, 4, 8, 16, 32, min(64, config.max_concurrent_requests)]
        test_duration_per_level = config.duration_seconds // len(concurrent_levels)
        
        for concurrent_level in concurrent_levels:
            if concurrent_level > config.max_concurrent_requests:
                break
            
            print(f"   測試並發級別: {concurrent_level}")
            
            level_start_time = time.time()
            level_requests = []
            level_errors = []
            level_response_times = []
            
            # 在當前並發級別下測試
            with ThreadPoolExecutor(max_workers=concurrent_level) as executor:
                futures = []
                
                while time.time() - level_start_time < test_duration_per_level:
                    # 提交並發請求
                    for _ in range(concurrent_level):
                        query = random.choice(self.test_queries)
                        future = executor.submit(self._execute_single_request, analyzer, query, config.timeout_seconds)
                        futures.append((future, time.time(), query))
                    
                    time.sleep(1.0)  # 每秒一批
                
                # 收集當前級別的結果
                for future, submit_time, query in futures:
                    try:
                        result = future.result(timeout=config.timeout_seconds + 5)
                        
                        level_requests.append({
                            "query": query,
                            "submit_time": submit_time,
                            "result": result,
                            "concurrent_level": concurrent_level
                        })
                        
                        if result["success"]:
                            level_response_times.append(result["response_time"])
                        else:
                            level_errors.append(result["error"])
                            
                    except Exception as e:
                        level_errors.append(str(e))
                        timeouts.append(str(e))
            
            # 計算當前級別的指標
            level_duration = time.time() - level_start_time
            level_throughput = len(level_response_times) / level_duration if level_duration > 0 else 0
            level_avg_response_time = statistics.mean(level_response_times) if level_response_times else 0
            level_error_rate = len(level_errors) / len(level_requests) if level_requests else 0
            
            scalability_metrics.append({
                "concurrent_level": concurrent_level,
                "throughput": level_throughput,
                "avg_response_time": level_avg_response_time,
                "error_rate": level_error_rate,
                "total_requests": len(level_requests),
                "successful_requests": len(level_response_times)
            })
            
            # 累積到總結果
            requests_data.extend(level_requests)
            errors.extend(level_errors)
            response_times.extend(level_response_times)
        
        return {
            "requests": requests_data,
            "errors": errors,
            "timeouts": timeouts,
            "response_times": response_times,
            "scalability_metrics": scalability_metrics
        }
    
    def _execute_single_request(self, analyzer: LLMIntentAnalyzer, query: str, timeout: float) -> Dict[str, Any]:
        """執行單個請求"""
        start_time = time.time()
        
        try:
            with self.request_lock:
                self.active_requests += 1
            
            # 處理特殊情況
            if query is None:
                raise ValueError("查詢不能為None")
            
            if not isinstance(query, str):
                raise TypeError(f"查詢必須是字符串，得到: {type(query)}")
            
            # 執行分析
            result = analyzer.analyze_intent(query)
            response_time = time.time() - start_time
            
            # 檢查超時
            if response_time > timeout:
                raise TimeoutError(f"請求超時: {response_time:.2f}s > {timeout}s")
            
            return {
                "success": True,
                "response_time": response_time,
                "result": {
                    "is_job_related": result.is_job_related,
                    "intent_type": result.intent_type.value if hasattr(result.intent_type, 'value') else str(result.intent_type),
                    "confidence": result.confidence
                },
                "error": None
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time": response_time,
                "result": None,
                "error": str(e)
            }
        
        finally:
            with self.request_lock:
                self.active_requests -= 1
    
    def _analyze_stress_test_results(self, test_id: str, provider: LLMProvider, 
                                   config: StressTestConfig, start_time: str, 
                                   end_time: str, total_duration: float, 
                                   test_results: Dict[str, Any]) -> StressTestResult:
        """分析壓力測試結果"""
        requests = test_results.get("requests", [])
        errors = test_results.get("errors", [])
        timeouts = test_results.get("timeouts", [])
        response_times = test_results.get("response_times", [])
        
        # 基本統計
        total_requests = len(requests)
        successful_requests = len([r for r in requests if r["result"]["success"]])
        failed_requests = total_requests - successful_requests
        timeout_requests = len(timeouts)
        error_requests = len(errors)
        
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        # 響應時間統計
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0.0
            p95_response_time = p99_response_time = 0.0
        
        # 吞吐量
        throughput = successful_requests / total_duration if total_duration > 0 else 0.0
        
        # 系統資源統計
        peak_memory = self.system_monitor.get_peak_memory()
        avg_memory = self.system_monitor.get_avg_memory()
        cpu_stats = self.system_monitor.get_cpu_stats()
        
        # 錯誤分佈
        error_distribution = {}
        for error in errors:
            error_type = self._classify_error(error)
            error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
        
        # 延遲百分位數
        latency_percentiles = {}
        if response_times:
            for p in [50, 75, 90, 95, 99, 99.9]:
                latency_percentiles[f"p{p}"] = np.percentile(response_times, p)
        
        # 穩定性分數（基於響應時間變異性）
        if len(response_times) > 1:
            cv = statistics.stdev(response_times) / avg_response_time if avg_response_time > 0 else 0
            stability_score = max(0.0, 1.0 - cv)  # 變異係數越小，穩定性越高
        else:
            stability_score = 1.0 if response_times else 0.0
        
        # 性能退化（比較前後期間的響應時間）
        performance_degradation = 0.0
        if len(response_times) > 10:
            early_times = response_times[:len(response_times)//3]
            late_times = response_times[-len(response_times)//3:]
            
            if early_times and late_times:
                early_avg = statistics.mean(early_times)
                late_avg = statistics.mean(late_times)
                performance_degradation = (late_avg - early_avg) / early_avg if early_avg > 0 else 0.0
        
        # 資源效率（成功請求數 / 平均記憶體使用量）
        resource_efficiency = successful_requests / avg_memory if avg_memory > 0 else 0.0
        
        return StressTestResult(
            test_id=test_id,
            provider=provider.value,
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            timeout_requests=timeout_requests,
            error_requests=error_requests,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            throughput=throughput,
            peak_memory_usage=peak_memory,
            avg_memory_usage=avg_memory,
            cpu_usage_stats=cpu_stats,
            error_distribution=error_distribution,
            response_time_distribution=response_times,
            latency_percentiles=latency_percentiles,
            stability_score=stability_score,
            performance_degradation=performance_degradation,
            resource_efficiency=resource_efficiency,
            metadata={
                "test_type": config.test_type.value,
                "load_pattern": config.load_pattern.value,
                "max_concurrent": config.max_concurrent_requests,
                "target_rps": config.requests_per_second,
                "additional_data": test_results
            }
        )
    
    def _classify_error(self, error_msg: str) -> str:
        """分類錯誤類型"""
        error_msg_lower = error_msg.lower()
        
        if "timeout" in error_msg_lower:
            return "timeout"
        elif "rate limit" in error_msg_lower or "too many requests" in error_msg_lower:
            return "rate_limit"
        elif "connection" in error_msg_lower:
            return "connection"
        elif "authentication" in error_msg_lower or "unauthorized" in error_msg_lower:
            return "auth"
        elif "quota" in error_msg_lower or "limit" in error_msg_lower:
            return "quota"
        elif "server error" in error_msg_lower or "500" in error_msg_lower:
            return "server_error"
        elif "bad request" in error_msg_lower or "400" in error_msg_lower:
            return "client_error"
        else:
            return "other"
    
    def save_stress_test_results(self, filename_prefix: str = "stress_test") -> str:
        """保存壓力測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_results_{timestamp}.json"
        
        # 準備保存的數據
        save_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "test_types": list(set(r.config.test_type.value for r in self.results)),
                "providers": list(set(r.provider for r in self.results))
            },
            "results": [asdict(result) for result in self.results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 壓力測試結果已保存: {filename}")
        return filename
    
    def print_stress_test_summary(self) -> None:
        """打印壓力測試摘要"""
        if not self.results:
            print("❌ 沒有壓力測試結果可顯示")
            return
        
        print("\n📊 LLM壓力測試摘要")
        print("=" * 60)
        
        for result in self.results:
            print(f"\n🧪 測試: {result.test_id}")
            print(f"   提供商: {result.provider}")
            print(f"   測試類型: {result.config.test_type.value}")
            print(f"   持續時間: {result.total_duration:.1f}秒")
            print(f"   總請求數: {result.total_requests}")
            print(f"   成功率: {result.success_rate:.1%}")
            print(f"   平均響應時間: {result.avg_response_time:.2f}秒")
            print(f"   P95響應時間: {result.p95_response_time:.2f}秒")
            print(f"   吞吐量: {result.throughput:.1f} 請求/秒")
            print(f"   峰值記憶體: {result.peak_memory_usage:.1f}MB")
            print(f"   穩定性分數: {result.stability_score:.2f}")
            
            if result.error_distribution:
                print(f"   錯誤分佈: {result.error_distribution}")


def main():
    """主函數 - 壓力測試工具入口點"""
    print("🚀 LLM壓力測試工具")
    print("=" * 60)
    
    # 創建壓力測試工具
    stress_tester = LLMStressTestTool()
    
    # 選擇測試類型
    print("\n請選擇壓力測試類型:")
    test_types = list(StressTestType)
    for i, test_type in enumerate(test_types, 1):
        print(f"{i}. {test_type.value}")
    
    try:
        choice = input("\n請輸入選擇 (1-8): ").strip()
        test_type_index = int(choice) - 1
        
        if 0 <= test_type_index < len(test_types):
            selected_test_type = test_types[test_type_index]
        else:
            print("❌ 無效選擇，使用並發負載測試")
            selected_test_type = StressTestType.CONCURRENT_LOAD
        
        # 選擇提供商
        config_manager = LLMConfigManager()
        available_providers = config_manager.get_available_providers()
        
        if not available_providers:
            print("❌ 沒有可用的LLM提供商")
            return
        
        print("\n可用的LLM提供商:")
        for i, provider in enumerate(available_providers, 1):
            print(f"{i}. {provider.value}")
        
        provider_choice = input("\n請選擇提供商 (1-{}): ".format(len(available_providers))).strip()
        provider_index = int(provider_choice) - 1
        
        if 0 <= provider_index < len(available_providers):
            selected_provider = available_providers[provider_index]
        else:
            print("❌ 無效選擇，使用第一個可用提供商")
            selected_provider = available_providers[0]
        
        # 創建測試配置
        config = StressTestConfig(
            test_type=selected_test_type,
            load_pattern=LoadPattern.CONSTANT,
            duration_seconds=60,  # 1分鐘測試
            max_concurrent_requests=10,
            requests_per_second=2.0,
            timeout_seconds=30.0
        )
        
        # 運行壓力測試
        result = stress_tester.run_stress_test(selected_provider, config)
        
        # 顯示摘要
        stress_tester.print_stress_test_summary()
        
        # 保存結果
        stress_tester.save_stress_test_results()
        
        print("\n✅ 壓力測試完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()