#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試案例執行引擎
自動執行測試案例，收集結果並進行分析

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, Counter
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from llm_config import LLMConfig


class ExecutionStatus(Enum):
    """執行狀態"""
    PENDING = "pending"  # 待執行
    RUNNING = "running"  # 執行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 執行失敗
    TIMEOUT = "timeout"  # 超時
    CANCELLED = "cancelled"  # 已取消


class ExecutionMode(Enum):
    """執行模式"""
    SEQUENTIAL = "sequential"  # 順序執行
    PARALLEL = "parallel"  # 並行執行
    BATCH = "batch"  # 批次執行
    STREAMING = "streaming"  # 流式執行


@dataclass
class TestExecution:
    """測試執行記錄"""
    test_case_id: str
    provider: LLMProvider
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionBatch:
    """執行批次"""
    batch_id: str
    test_cases: List[Dict[str, Any]]
    providers: List[LLMProvider]
    executions: List[TestExecution] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0


@dataclass
class ExecutionConfig:
    """執行配置"""
    mode: ExecutionMode = ExecutionMode.PARALLEL
    max_workers: int = 5
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 10
    rate_limit_delay: float = 0.1
    enable_caching: bool = True
    save_intermediate_results: bool = True
    progress_callback: Optional[Callable] = None


class ExecutionMonitor:
    """執行監控器"""
    
    def __init__(self):
        """初始化監控器"""
        self.start_time = None
        self.total_tests = 0
        self.completed_tests = 0
        self.failed_tests = 0
        self.current_batch = None
        self.progress_queue = queue.Queue()
        self.is_monitoring = False
        
    def start_monitoring(self, total_tests: int) -> None:
        """開始監控"""
        self.start_time = datetime.now()
        self.total_tests = total_tests
        self.completed_tests = 0
        self.failed_tests = 0
        self.is_monitoring = True
        
    def update_progress(self, completed: int, failed: int = 0) -> None:
        """更新進度"""
        self.completed_tests = completed
        self.failed_tests = failed
        
        if self.is_monitoring:
            progress = (completed + failed) / self.total_tests if self.total_tests > 0 else 0
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            eta = (elapsed / progress * (1 - progress)) if progress > 0 else 0
            
            self.progress_queue.put({
                "progress": progress,
                "completed": completed,
                "failed": failed,
                "total": self.total_tests,
                "elapsed": elapsed,
                "eta": eta
            })
    
    def stop_monitoring(self) -> None:
        """停止監控"""
        self.is_monitoring = False
    
    def get_progress(self) -> Dict[str, Any]:
        """獲取進度信息"""
        try:
            return self.progress_queue.get_nowait()
        except queue.Empty:
            return {}


class LLMTestExecutionEngine:
    """LLM測試執行引擎"""
    
    def __init__(self, config: ExecutionConfig = None):
        """初始化執行引擎"""
        self.config = config or ExecutionConfig()
        self.monitor = ExecutionMonitor()
        self.analyzers = {}
        self.execution_cache = {}
        self.results_storage = []
        self.is_cancelled = False
        
    def _get_analyzer(self, provider: LLMProvider) -> LLMIntentAnalyzer:
        """獲取分析器實例"""
        if provider not in self.analyzers:
            # 創建LLM配置
            llm_config = LLMConfig(
                provider=provider,
                api_key=os.getenv(f"{provider.value.upper()}_API_KEY", "test_key"),
                model_name=self._get_default_model(provider),
                temperature=0.1,
                max_tokens=1000
            )
            
            self.analyzers[provider] = LLMIntentAnalyzer(llm_config)
        
        return self.analyzers[provider]
    
    def _get_default_model(self, provider: LLMProvider) -> str:
        """獲取默認模型"""
        default_models = {
            LLMProvider.OPENAI: "gpt-3.5-turbo",
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.GOOGLE: "gemini-pro",
            LLMProvider.AZURE_OPENAI: "gpt-35-turbo",
            LLMProvider.HUGGINGFACE: "microsoft/DialoGPT-medium",
            LLMProvider.COHERE: "command",
            LLMProvider.OLLAMA: "llama2"
        }
        return default_models.get(provider, "gpt-3.5-turbo")
    
    def execute_test_cases(self, test_cases: List[Dict[str, Any]], 
                          providers: List[LLMProvider]) -> List[ExecutionBatch]:
        """執行測試案例"""
        print(f"🚀 開始執行 {len(test_cases)} 個測試案例，使用 {len(providers)} 個提供商...")
        
        total_executions = len(test_cases) * len(providers)
        self.monitor.start_monitoring(total_executions)
        
        batches = []
        
        try:
            if self.config.mode == ExecutionMode.SEQUENTIAL:
                batches = self._execute_sequential(test_cases, providers)
            elif self.config.mode == ExecutionMode.PARALLEL:
                batches = self._execute_parallel(test_cases, providers)
            elif self.config.mode == ExecutionMode.BATCH:
                batches = self._execute_batch(test_cases, providers)
            elif self.config.mode == ExecutionMode.STREAMING:
                batches = self._execute_streaming(test_cases, providers)
            
        except KeyboardInterrupt:
            print("\n❌ 執行被用戶中斷")
            self.is_cancelled = True
        except Exception as e:
            print(f"\n❌ 執行過程中發生錯誤: {str(e)}")
        finally:
            self.monitor.stop_monitoring()
        
        print(f"\n✅ 執行完成，共處理 {len(batches)} 個批次")
        return batches
    
    def _execute_sequential(self, test_cases: List[Dict[str, Any]], 
                          providers: List[LLMProvider]) -> List[ExecutionBatch]:
        """順序執行"""
        print("   📋 使用順序執行模式")
        
        batch = ExecutionBatch(
            batch_id=f"sequential_{int(time.time())}",
            test_cases=test_cases,
            providers=providers,
            start_time=datetime.now()
        )
        
        completed = 0
        failed = 0
        
        for test_case in test_cases:
            if self.is_cancelled:
                break
                
            for provider in providers:
                if self.is_cancelled:
                    break
                    
                execution = self._execute_single_test(test_case, provider)
                batch.executions.append(execution)
                
                if execution.status == ExecutionStatus.COMPLETED:
                    completed += 1
                    batch.success_count += 1
                else:
                    failed += 1
                    if execution.status == ExecutionStatus.FAILED:
                        batch.failure_count += 1
                    elif execution.status == ExecutionStatus.TIMEOUT:
                        batch.timeout_count += 1
                
                self.monitor.update_progress(completed, failed)
                
                # 速率限制
                if self.config.rate_limit_delay > 0:
                    time.sleep(self.config.rate_limit_delay)
        
        batch.end_time = datetime.now()
        batch.total_duration = (batch.end_time - batch.start_time).total_seconds()
        
        return [batch]
    
    def _execute_parallel(self, test_cases: List[Dict[str, Any]], 
                         providers: List[LLMProvider]) -> List[ExecutionBatch]:
        """並行執行"""
        print(f"   🔄 使用並行執行模式，最大工作線程: {self.config.max_workers}")
        
        batch = ExecutionBatch(
            batch_id=f"parallel_{int(time.time())}",
            test_cases=test_cases,
            providers=providers,
            start_time=datetime.now()
        )
        
        # 創建執行任務
        tasks = []
        for test_case in test_cases:
            for provider in providers:
                tasks.append((test_case, provider))
        
        completed = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任務
            future_to_task = {
                executor.submit(self._execute_single_test, test_case, provider): (test_case, provider)
                for test_case, provider in tasks
            }
            
            # 收集結果
            for future in as_completed(future_to_task):
                if self.is_cancelled:
                    break
                    
                try:
                    execution = future.result()
                    batch.executions.append(execution)
                    
                    if execution.status == ExecutionStatus.COMPLETED:
                        completed += 1
                        batch.success_count += 1
                    else:
                        failed += 1
                        if execution.status == ExecutionStatus.FAILED:
                            batch.failure_count += 1
                        elif execution.status == ExecutionStatus.TIMEOUT:
                            batch.timeout_count += 1
                    
                    self.monitor.update_progress(completed, failed)
                    
                except Exception as e:
                    print(f"   ⚠️ 任務執行異常: {str(e)}")
                    failed += 1
                    batch.failure_count += 1
                    self.monitor.update_progress(completed, failed)
        
        batch.end_time = datetime.now()
        batch.total_duration = (batch.end_time - batch.start_time).total_seconds()
        
        return [batch]
    
    def _execute_batch(self, test_cases: List[Dict[str, Any]], 
                      providers: List[LLMProvider]) -> List[ExecutionBatch]:
        """批次執行"""
        print(f"   📦 使用批次執行模式，批次大小: {self.config.batch_size}")
        
        batches = []
        
        # 分割測試案例
        for i in range(0, len(test_cases), self.config.batch_size):
            if self.is_cancelled:
                break
                
            batch_cases = test_cases[i:i + self.config.batch_size]
            
            batch = ExecutionBatch(
                batch_id=f"batch_{i//self.config.batch_size + 1}_{int(time.time())}",
                test_cases=batch_cases,
                providers=providers,
                start_time=datetime.now()
            )
            
            print(f"   🔄 執行批次 {len(batches) + 1}: {len(batch_cases)} 個案例")
            
            # 並行執行當前批次
            parallel_batches = self._execute_parallel(batch_cases, providers)
            if parallel_batches:
                batch.executions = parallel_batches[0].executions
                batch.success_count = parallel_batches[0].success_count
                batch.failure_count = parallel_batches[0].failure_count
                batch.timeout_count = parallel_batches[0].timeout_count
            
            batch.end_time = datetime.now()
            batch.total_duration = (batch.end_time - batch.start_time).total_seconds()
            
            batches.append(batch)
            
            # 批次間延遲
            if i + self.config.batch_size < len(test_cases):
                time.sleep(self.config.rate_limit_delay * 10)  # 批次間較長延遲
        
        return batches
    
    def _execute_streaming(self, test_cases: List[Dict[str, Any]], 
                          providers: List[LLMProvider]) -> List[ExecutionBatch]:
        """流式執行"""
        print("   🌊 使用流式執行模式")
        
        batch = ExecutionBatch(
            batch_id=f"streaming_{int(time.time())}",
            test_cases=test_cases,
            providers=providers,
            start_time=datetime.now()
        )
        
        completed = 0
        failed = 0
        
        # 創建執行隊列
        execution_queue = queue.Queue()
        
        # 填充隊列
        for test_case in test_cases:
            for provider in providers:
                execution_queue.put((test_case, provider))
        
        def worker():
            """工作線程"""
            nonlocal completed, failed
            
            while not execution_queue.empty() and not self.is_cancelled:
                try:
                    test_case, provider = execution_queue.get(timeout=1)
                    execution = self._execute_single_test(test_case, provider)
                    batch.executions.append(execution)
                    
                    if execution.status == ExecutionStatus.COMPLETED:
                        completed += 1
                        batch.success_count += 1
                    else:
                        failed += 1
                        if execution.status == ExecutionStatus.FAILED:
                            batch.failure_count += 1
                        elif execution.status == ExecutionStatus.TIMEOUT:
                            batch.timeout_count += 1
                    
                    self.monitor.update_progress(completed, failed)
                    execution_queue.task_done()
                    
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"   ⚠️ 工作線程異常: {str(e)}")
                    failed += 1
                    batch.failure_count += 1
                    self.monitor.update_progress(completed, failed)
        
        # 啟動工作線程
        threads = []
        for _ in range(min(self.config.max_workers, execution_queue.qsize())):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        batch.end_time = datetime.now()
        batch.total_duration = (batch.end_time - batch.start_time).total_seconds()
        
        return [batch]
    
    def _execute_single_test(self, test_case: Dict[str, Any], provider: LLMProvider) -> TestExecution:
        """執行單個測試"""
        execution = TestExecution(
            test_case_id=test_case.get("id", "unknown"),
            provider=provider,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        
        # 檢查緩存
        cache_key = f"{test_case.get('id')}_{provider.value}"
        if self.config.enable_caching and cache_key in self.execution_cache:
            cached_result = self.execution_cache[cache_key]
            execution.result = cached_result
            execution.status = ExecutionStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.duration = 0.001  # 緩存命中，幾乎無延遲
            execution.metadata["from_cache"] = True
            return execution
        
        execution.status = ExecutionStatus.RUNNING
        
        for attempt in range(self.config.retry_attempts):
            try:
                # 獲取分析器
                analyzer = self._get_analyzer(provider)
                
                # 執行分析
                query = test_case.get("query", "")
                
                start_time = time.time()
                
                # 設置超時
                result = self._analyze_with_timeout(analyzer, query, self.config.timeout_seconds)
                
                end_time = time.time()
                
                # 記錄結果
                execution.result = {
                    "intent": result.get("intent", "unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "entities": result.get("entities", {}),
                    "response_time": end_time - start_time,
                    "provider": provider.value,
                    "model": self._get_default_model(provider)
                }
                
                execution.status = ExecutionStatus.COMPLETED
                execution.duration = end_time - start_time
                
                # 緩存結果
                if self.config.enable_caching:
                    self.execution_cache[cache_key] = execution.result
                
                break
                
            except TimeoutError:
                execution.status = ExecutionStatus.TIMEOUT
                execution.error = "執行超時"
                execution.retry_count = attempt + 1
                
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))  # 指數退避
                
            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.error = str(e)
                execution.retry_count = attempt + 1
                
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        
        execution.end_time = datetime.now()
        if execution.duration is None:
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
        
        execution.metadata.update({
            "retry_count": execution.retry_count,
            "test_case_category": test_case.get("category", ""),
            "test_case_complexity": test_case.get("complexity", ""),
            "expected_intent": test_case.get("expected_intent", "")
        })
        
        return execution
    
    def _analyze_with_timeout(self, analyzer: LLMIntentAnalyzer, query: str, timeout: int) -> Dict[str, Any]:
        """帶超時的分析"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("分析超時")
        
        # 設置超時信號 (僅在Unix系統上可用)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        try:
            result = analyzer.analyze_intent(query)
            return {
                "intent": result.intent,
                "confidence": result.confidence,
                "entities": result.entities
            }
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # 取消超時
    
    def analyze_execution_results(self, batches: List[ExecutionBatch]) -> Dict[str, Any]:
        """分析執行結果"""
        print("📊 分析執行結果...")
        
        all_executions = []
        for batch in batches:
            all_executions.extend(batch.executions)
        
        if not all_executions:
            return {"error": "沒有執行結果可分析"}
        
        # 基本統計
        total_executions = len(all_executions)
        successful_executions = [e for e in all_executions if e.status == ExecutionStatus.COMPLETED]
        failed_executions = [e for e in all_executions if e.status == ExecutionStatus.FAILED]
        timeout_executions = [e for e in all_executions if e.status == ExecutionStatus.TIMEOUT]
        
        success_rate = len(successful_executions) / total_executions if total_executions > 0 else 0
        failure_rate = len(failed_executions) / total_executions if total_executions > 0 else 0
        timeout_rate = len(timeout_executions) / total_executions if total_executions > 0 else 0
        
        # 性能統計
        durations = [e.duration for e in successful_executions if e.duration is not None]
        avg_duration = statistics.mean(durations) if durations else 0
        median_duration = statistics.median(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # 提供商統計
        provider_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "timeout": 0, "avg_duration": 0})
        
        for execution in all_executions:
            provider = execution.provider.value
            provider_stats[provider]["total"] += 1
            
            if execution.status == ExecutionStatus.COMPLETED:
                provider_stats[provider]["success"] += 1
                if execution.duration:
                    provider_stats[provider]["avg_duration"] += execution.duration
            elif execution.status == ExecutionStatus.FAILED:
                provider_stats[provider]["failed"] += 1
            elif execution.status == ExecutionStatus.TIMEOUT:
                provider_stats[provider]["timeout"] += 1
        
        # 計算平均持續時間
        for provider, stats in provider_stats.items():
            if stats["success"] > 0:
                stats["avg_duration"] /= stats["success"]
            stats["success_rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0
        
        # 意圖準確性分析
        intent_accuracy = self._analyze_intent_accuracy(successful_executions)
        
        # 錯誤分析
        error_analysis = self._analyze_errors(failed_executions)
        
        # 性能趨勢
        performance_trends = self._analyze_performance_trends(successful_executions)
        
        analysis = {
            "execution_summary": {
                "total_executions": total_executions,
                "successful_executions": len(successful_executions),
                "failed_executions": len(failed_executions),
                "timeout_executions": len(timeout_executions),
                "success_rate": success_rate,
                "failure_rate": failure_rate,
                "timeout_rate": timeout_rate
            },
            "performance_metrics": {
                "average_duration": avg_duration,
                "median_duration": median_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "total_duration": sum(durations)
            },
            "provider_statistics": dict(provider_stats),
            "intent_accuracy": intent_accuracy,
            "error_analysis": error_analysis,
            "performance_trends": performance_trends,
            "batch_summary": {
                "total_batches": len(batches),
                "avg_batch_duration": statistics.mean([b.total_duration for b in batches if b.total_duration]) if batches else 0
            }
        }
        
        return analysis
    
    def _analyze_intent_accuracy(self, executions: List[TestExecution]) -> Dict[str, Any]:
        """分析意圖準確性"""
        correct_predictions = 0
        total_predictions = 0
        
        intent_confusion = defaultdict(lambda: defaultdict(int))
        
        for execution in executions:
            if not execution.result or not execution.metadata:
                continue
                
            predicted_intent = execution.result.get("intent", "unknown")
            expected_intent = execution.metadata.get("expected_intent", "unknown")
            
            if expected_intent != "unknown":
                total_predictions += 1
                intent_confusion[expected_intent][predicted_intent] += 1
                
                if predicted_intent == expected_intent:
                    correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        return {
            "overall_accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions,
            "confusion_matrix": dict(intent_confusion)
        }
    
    def _analyze_errors(self, failed_executions: List[TestExecution]) -> Dict[str, Any]:
        """分析錯誤"""
        error_types = Counter()
        error_by_provider = defaultdict(list)
        
        for execution in failed_executions:
            error_msg = execution.error or "未知錯誤"
            error_types[error_msg] += 1
            error_by_provider[execution.provider.value].append(error_msg)
        
        return {
            "error_types": dict(error_types),
            "error_by_provider": dict(error_by_provider),
            "total_errors": len(failed_executions)
        }
    
    def _analyze_performance_trends(self, executions: List[TestExecution]) -> Dict[str, Any]:
        """分析性能趨勢"""
        # 按時間排序
        sorted_executions = sorted(executions, key=lambda x: x.start_time or datetime.min)
        
        # 計算移動平均
        window_size = min(10, len(sorted_executions))
        moving_averages = []
        
        for i in range(len(sorted_executions) - window_size + 1):
            window = sorted_executions[i:i + window_size]
            avg_duration = statistics.mean([e.duration for e in window if e.duration])
            moving_averages.append(avg_duration)
        
        # 性能變化趨勢
        if len(moving_averages) >= 2:
            trend = "improving" if moving_averages[-1] < moving_averages[0] else "degrading"
        else:
            trend = "stable"
        
        return {
            "moving_averages": moving_averages,
            "trend": trend,
            "performance_variance": statistics.variance([e.duration for e in executions if e.duration]) if len(executions) > 1 else 0
        }
    
    def export_execution_results(self, batches: List[ExecutionBatch], 
                               analysis: Dict[str, Any], 
                               output_file: str = None) -> str:
        """導出執行結果"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"execution_results_{timestamp}.json"
        
        print(f"💾 導出執行結果到 {output_file}...")
        
        # 準備導出數據
        export_data = {
            "execution_info": {
                "execution_time": datetime.now().isoformat(),
                "config": {
                    "mode": self.config.mode.value,
                    "max_workers": self.config.max_workers,
                    "timeout_seconds": self.config.timeout_seconds,
                    "retry_attempts": self.config.retry_attempts,
                    "batch_size": self.config.batch_size
                }
            },
            "batches": [],
            "analysis": analysis
        }
        
        # 序列化批次數據
        for batch in batches:
            batch_data = {
                "batch_id": batch.batch_id,
                "start_time": batch.start_time.isoformat() if batch.start_time else None,
                "end_time": batch.end_time.isoformat() if batch.end_time else None,
                "total_duration": batch.total_duration,
                "success_count": batch.success_count,
                "failure_count": batch.failure_count,
                "timeout_count": batch.timeout_count,
                "executions": []
            }
            
            for execution in batch.executions:
                execution_data = {
                    "test_case_id": execution.test_case_id,
                    "provider": execution.provider.value,
                    "status": execution.status.value,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "duration": execution.duration,
                    "result": execution.result,
                    "error": execution.error,
                    "retry_count": execution.retry_count,
                    "metadata": execution.metadata
                }
                batch_data["executions"].append(execution_data)
            
            export_data["batches"].append(batch_data)
        
        # 寫入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 執行結果已導出")
        return output_file
    
    def print_execution_summary(self, analysis: Dict[str, Any]) -> None:
        """打印執行摘要"""
        print("\n" + "=" * 60)
        print("🚀 LLM測試執行結果摘要")
        print("=" * 60)
        
        # 執行摘要
        summary = analysis.get("execution_summary", {})
        print(f"\n📊 執行摘要:")
        print(f"   總執行次數: {summary.get('total_executions', 0)}")
        print(f"   成功執行: {summary.get('successful_executions', 0)}")
        print(f"   失敗執行: {summary.get('failed_executions', 0)}")
        print(f"   超時執行: {summary.get('timeout_executions', 0)}")
        print(f"   成功率: {summary.get('success_rate', 0):.1%}")
        
        # 性能指標
        performance = analysis.get("performance_metrics", {})
        print(f"\n⚡ 性能指標:")
        print(f"   平均響應時間: {performance.get('average_duration', 0):.3f} 秒")
        print(f"   中位數響應時間: {performance.get('median_duration', 0):.3f} 秒")
        print(f"   最快響應: {performance.get('min_duration', 0):.3f} 秒")
        print(f"   最慢響應: {performance.get('max_duration', 0):.3f} 秒")
        
        # 提供商統計
        provider_stats = analysis.get("provider_statistics", {})
        if provider_stats:
            print(f"\n🏢 提供商統計:")
            for provider, stats in provider_stats.items():
                print(f"   {provider}:")
                print(f"     成功率: {stats.get('success_rate', 0):.1%}")
                print(f"     平均響應時間: {stats.get('avg_duration', 0):.3f} 秒")
                print(f"     執行次數: {stats.get('total', 0)}")
        
        # 意圖準確性
        intent_accuracy = analysis.get("intent_accuracy", {})
        if intent_accuracy:
            print(f"\n🎯 意圖準確性:")
            print(f"   總體準確率: {intent_accuracy.get('overall_accuracy', 0):.1%}")
            print(f"   正確預測: {intent_accuracy.get('correct_predictions', 0)}")
            print(f"   總預測數: {intent_accuracy.get('total_predictions', 0)}")
        
        # 錯誤分析
        error_analysis = analysis.get("error_analysis", {})
        if error_analysis.get("total_errors", 0) > 0:
            print(f"\n❌ 錯誤分析:")
            print(f"   總錯誤數: {error_analysis.get('total_errors', 0)}")
            
            error_types = error_analysis.get("error_types", {})
            if error_types:
                print(f"   主要錯誤類型:")
                for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"     {error}: {count} 次")
        
        print("\n" + "=" * 60)


def load_test_cases_from_file(file_path: str) -> List[Dict[str, Any]]:
    """從文件載入測試案例"""
    print(f"📂 載入測試案例從 {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "test_cases" in data:
            test_cases = data["test_cases"]
        elif isinstance(data, list):
            test_cases = data
        else:
            raise ValueError("無效的文件格式")
        
        print(f"   ✅ 成功載入 {len(test_cases)} 個測試案例")
        return test_cases
        
    except Exception as e:
        print(f"   ❌ 載入失敗: {str(e)}")
        return []


def main():
    """主函數 - 測試執行引擎入口點"""
    print("🚀 LLM測試執行引擎")
    print("=" * 60)
    
    try:
        # 獲取輸入文件
        input_file = input("請輸入測試案例文件路徑 (或按Enter使用默認): ").strip()
        if not input_file:
            input_file = "generated_test_cases.json"
        
        # 載入測試案例
        test_cases = load_test_cases_from_file(input_file)
        
        if not test_cases:
            print("❌ 沒有找到有效的測試案例")
            return
        
        # 選擇提供商
        print("\n🏢 選擇LLM提供商:")
        available_providers = list(LLMProvider)
        for i, provider in enumerate(available_providers, 1):
            print(f"{i}. {provider.value}")
        
        provider_input = input("請選擇提供商 (用逗號分隔編號，或按Enter選擇所有): ").strip()
        
        if provider_input:
            try:
                indices = [int(x.strip()) - 1 for x in provider_input.split(",")]
                providers = [available_providers[i] for i in indices if 0 <= i < len(available_providers)]
            except:
                print("無效的選擇，使用所有提供商")
                providers = available_providers
        else:
            providers = available_providers
        
        # 配置執行參數
        print("\n⚙️ 執行配置:")
        print("1. 快速模式 (並行，5線程)")
        print("2. 標準模式 (並行，10線程)")
        print("3. 批次模式 (批次大小: 20)")
        print("4. 順序模式 (單線程)")
        print("5. 自定義")
        
        config_choice = input("請選擇執行模式 (1-5): ").strip()
        
        if config_choice == "1":
            config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=5, timeout_seconds=15)
        elif config_choice == "2":
            config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=10, timeout_seconds=30)
        elif config_choice == "3":
            config = ExecutionConfig(mode=ExecutionMode.BATCH, batch_size=20, max_workers=5)
        elif config_choice == "4":
            config = ExecutionConfig(mode=ExecutionMode.SEQUENTIAL, timeout_seconds=30)
        elif config_choice == "5":
            # 自定義配置
            mode_input = input("執行模式 (sequential/parallel/batch/streaming): ").strip().lower()
            mode = ExecutionMode.PARALLEL
            if mode_input in ["sequential", "parallel", "batch", "streaming"]:
                mode = ExecutionMode(mode_input)
            
            max_workers = int(input("最大工作線程數 (默認5): ").strip() or "5")
            timeout = int(input("超時時間(秒) (默認30): ").strip() or "30")
            
            config = ExecutionConfig(mode=mode, max_workers=max_workers, timeout_seconds=timeout)
        else:
            config = ExecutionConfig()
        
        # 創建執行引擎
        engine = LLMTestExecutionEngine(config)
        
        # 執行測試
        print(f"\n🚀 開始執行測試，模式: {config.mode.value}")
        print(f"   測試案例: {len(test_cases)}")
        print(f"   提供商: {[p.value for p in providers]}")
        print(f"   總執行次數: {len(test_cases) * len(providers)}")
        
        batches = engine.execute_test_cases(test_cases, providers)
        
        # 分析結果
        analysis = engine.analyze_execution_results(batches)
        
        # 顯示摘要
        engine.print_execution_summary(analysis)
        
        # 導出結果
        export_result = input("\n是否導出執行結果？ (y/n): ").strip().lower()
        if export_result == 'y':
            output_file = engine.export_execution_results(batches, analysis)
            print(f"   📄 結果文件: {output_file}")
        
        print("\n🎉 測試執行完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 執行過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()