#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化LLM測試執行器
用於批量運行不同的LLM測試案例，收集結果並生成對比報告

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging
from enum import Enum
import psutil
import signal
from contextlib import contextmanager

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMProvider
from llm_config import LLMConfig

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_test_runner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestType(Enum):
    """測試類型枚舉"""
    COMPREHENSIVE = "comprehensive"  # 全面測試
    BENCHMARK = "benchmark"  # 基準測試
    STRESS = "stress"  # 壓力測試
    PERFORMANCE = "performance"  # 性能測試
    COMPARISON = "comparison"  # 對比測試
    CUSTOM = "custom"  # 自定義測試


class TestStatus(Enum):
    """測試狀態枚舉"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 執行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失敗
    TIMEOUT = "timeout"  # 超時
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TestTask:
    """測試任務"""
    task_id: str
    test_type: TestType
    test_script: str
    providers: List[str]
    config: Dict[str, Any]
    priority: int = 1  # 1-5, 5最高
    timeout: int = 3600  # 超時時間（秒）
    retry_count: int = 0  # 重試次數
    max_retries: int = 2  # 最大重試次數
    dependencies: List[str] = field(default_factory=list)  # 依賴的任務ID
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result_file: Optional[str] = None
    error_message: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class TestSuite:
    """測試套件"""
    suite_id: str
    name: str
    description: str
    tasks: List[TestTask]
    parallel_limit: int = 3  # 並行執行限制
    total_timeout: int = 7200  # 總超時時間（秒）
    created_time: datetime = field(default_factory=datetime.now)
    status: TestStatus = TestStatus.PENDING


@dataclass
class TestResult:
    """測試結果"""
    task_id: str
    test_type: TestType
    provider: str
    success: bool
    execution_time: float
    result_data: Dict[str, Any]
    error_details: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self):
        self.monitoring = False
        self.data = []
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 1.0):
        """開始監控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.data = []
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("資源監控已啟動")
    
    def stop_monitoring(self) -> Dict[str, float]:
        """停止監控並返回統計數據"""
        if not self.monitoring:
            return {}
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        if not self.data:
            return {}
        
        # 計算統計數據
        cpu_values = [d['cpu'] for d in self.data]
        memory_values = [d['memory'] for d in self.data]
        
        stats = {
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'sample_count': len(self.data)
        }
        
        logger.info(f"資源監控已停止，收集了 {len(self.data)} 個樣本")
        return stats
    
    def _monitor_loop(self, interval: float):
        """監控循環"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                self.data.append({
                    'timestamp': time.time(),
                    'cpu': cpu_percent,
                    'memory': memory_mb
                })
                
                time.sleep(interval)
            except Exception as e:
                logger.warning(f"資源監控錯誤: {e}")
                break


class AutomatedLLMTestRunner:
    """自動化LLM測試執行器"""
    
    def __init__(self, output_dir: str = "test_results", max_workers: int = 3):
        """初始化測試執行器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 創建子目錄
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "results").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        
        self.max_workers = max_workers
        self.test_suites: Dict[str, TestSuite] = {}
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        self.completed_results: List[TestResult] = []
        
        # 資源監控
        self.resource_monitor = ResourceMonitor()
        
        # 執行器
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 可用的測試腳本
        self.available_scripts = {
            TestType.COMPREHENSIVE: "comprehensive_llm_test.py",
            TestType.BENCHMARK: "llm_benchmark_test_suite.py",
            TestType.STRESS: "llm_stress_test_tool.py",
            TestType.PERFORMANCE: "advanced_llm_performance_analyzer.py",
            TestType.COMPARISON: "enhanced_llm_model_comparison_test.py"
        }
        
        # 信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def create_test_suite(self, suite_id: str, name: str, description: str, 
                         parallel_limit: int = 3) -> TestSuite:
        """創建測試套件"""
        suite = TestSuite(
            suite_id=suite_id,
            name=name,
            description=description,
            tasks=[],
            parallel_limit=parallel_limit
        )
        
        self.test_suites[suite_id] = suite
        logger.info(f"創建測試套件: {name} (ID: {suite_id})")
        return suite
    
    def add_test_task(self, suite_id: str, task_id: str, test_type: TestType,
                     providers: List[str], config: Dict[str, Any] = None,
                     priority: int = 1, timeout: int = 3600,
                     dependencies: List[str] = None) -> TestTask:
        """添加測試任務"""
        if suite_id not in self.test_suites:
            raise ValueError(f"測試套件 {suite_id} 不存在")
        
        if test_type not in self.available_scripts:
            raise ValueError(f"不支援的測試類型: {test_type}")
        
        task = TestTask(
            task_id=task_id,
            test_type=test_type,
            test_script=self.available_scripts[test_type],
            providers=providers,
            config=config or {},
            priority=priority,
            timeout=timeout,
            dependencies=dependencies or []
        )
        
        self.test_suites[suite_id].tasks.append(task)
        logger.info(f"添加測試任務: {task_id} 到套件 {suite_id}")
        return task
    
    def create_comprehensive_test_suite(self, providers: List[str]) -> str:
        """創建全面測試套件"""
        suite_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        suite = self.create_test_suite(
            suite_id=suite_id,
            name="全面LLM測試套件",
            description="包含所有類型的LLM測試，用於全面評估模型性能",
            parallel_limit=2
        )
        
        # 基礎功能測試
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_comprehensive",
            test_type=TestType.COMPREHENSIVE,
            providers=providers,
            config={"test_mode": "full", "iterations": 3},
            priority=5,
            timeout=1800
        )
        
        # 基準測試
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_benchmark",
            test_type=TestType.BENCHMARK,
            providers=providers,
            config={"test_mode": "standard", "categories": "all"},
            priority=4,
            timeout=2400,
            dependencies=[f"{suite_id}_comprehensive"]
        )
        
        # 性能分析
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_performance",
            test_type=TestType.PERFORMANCE,
            providers=providers,
            config={"analysis_mode": "standard", "include_charts": True},
            priority=3,
            timeout=1800,
            dependencies=[f"{suite_id}_benchmark"]
        )
        
        # 壓力測試
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_stress",
            test_type=TestType.STRESS,
            providers=providers,
            config={"stress_type": "moderate", "duration": 300},
            priority=2,
            timeout=900
        )
        
        # 對比測試
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_comparison",
            test_type=TestType.COMPARISON,
            providers=providers,
            config={"comparison_mode": "detailed", "generate_report": True},
            priority=1,
            timeout=1200,
            dependencies=[f"{suite_id}_performance", f"{suite_id}_stress"]
        )
        
        logger.info(f"創建全面測試套件: {suite_id}，包含 {len(suite.tasks)} 個任務")
        return suite_id
    
    def create_quick_test_suite(self, providers: List[str]) -> str:
        """創建快速測試套件"""
        suite_id = f"quick_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        suite = self.create_test_suite(
            suite_id=suite_id,
            name="快速LLM測試套件",
            description="快速評估LLM模型基本性能",
            parallel_limit=3
        )
        
        # 基礎測試
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_basic",
            test_type=TestType.COMPREHENSIVE,
            providers=providers,
            config={"test_mode": "quick", "iterations": 1},
            priority=3,
            timeout=600
        )
        
        # 簡單對比
        self.add_test_task(
            suite_id=suite_id,
            task_id=f"{suite_id}_comparison",
            test_type=TestType.COMPARISON,
            providers=providers,
            config={"comparison_mode": "basic"},
            priority=2,
            timeout=600,
            dependencies=[f"{suite_id}_basic"]
        )
        
        logger.info(f"創建快速測試套件: {suite_id}，包含 {len(suite.tasks)} 個任務")
        return suite_id
    
    def create_stress_test_suite(self, providers: List[str]) -> str:
        """創建壓力測試套件"""
        suite_id = f"stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        suite = self.create_test_suite(
            suite_id=suite_id,
            name="LLM壓力測試套件",
            description="測試LLM模型在高負載下的表現",
            parallel_limit=1  # 壓力測試通常不並行
        )
        
        stress_types = ["concurrent", "sustained", "burst", "memory"]
        
        for i, stress_type in enumerate(stress_types):
            self.add_test_task(
                suite_id=suite_id,
                task_id=f"{suite_id}_{stress_type}",
                test_type=TestType.STRESS,
                providers=providers,
                config={
                    "stress_type": stress_type,
                    "duration": 600,
                    "intensity": "high"
                },
                priority=4 - i,
                timeout=1200
            )
        
        logger.info(f"創建壓力測試套件: {suite_id}，包含 {len(suite.tasks)} 個任務")
        return suite_id
    
    async def run_test_suite(self, suite_id: str) -> Dict[str, Any]:
        """運行測試套件"""
        if suite_id not in self.test_suites:
            raise ValueError(f"測試套件 {suite_id} 不存在")
        
        suite = self.test_suites[suite_id]
        suite.status = TestStatus.RUNNING
        
        logger.info(f"開始運行測試套件: {suite.name} (ID: {suite_id})")
        logger.info(f"包含 {len(suite.tasks)} 個任務，並行限制: {suite.parallel_limit}")
        
        # 啟動資源監控
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        
        try:
            # 按依賴關係和優先級排序任務
            sorted_tasks = self._sort_tasks_by_dependencies(suite.tasks)
            
            # 執行任務
            results = await self._execute_tasks_parallel(sorted_tasks, suite.parallel_limit)
            
            # 停止資源監控
            resource_stats = self.resource_monitor.stop_monitoring()
            
            execution_time = time.time() - start_time
            
            # 統計結果
            successful_tasks = sum(1 for r in results if r.success)
            failed_tasks = len(results) - successful_tasks
            
            suite.status = TestStatus.COMPLETED if failed_tasks == 0 else TestStatus.FAILED
            
            # 生成套件結果
            suite_result = {
                'suite_id': suite_id,
                'suite_name': suite.name,
                'status': suite.status.value,
                'execution_time': execution_time,
                'total_tasks': len(suite.tasks),
                'successful_tasks': successful_tasks,
                'failed_tasks': failed_tasks,
                'success_rate': successful_tasks / len(suite.tasks) if suite.tasks else 0,
                'resource_usage': resource_stats,
                'task_results': [asdict(r) for r in results],
                'timestamp': datetime.now().isoformat()
            }
            
            # 保存結果
            result_file = self._save_suite_result(suite_result)
            
            logger.info(f"測試套件 {suite_id} 執行完成")
            logger.info(f"成功: {successful_tasks}/{len(suite.tasks)}, 執行時間: {execution_time:.2f}秒")
            logger.info(f"結果已保存到: {result_file}")
            
            return suite_result
            
        except Exception as e:
            suite.status = TestStatus.FAILED
            self.resource_monitor.stop_monitoring()
            logger.error(f"測試套件 {suite_id} 執行失敗: {str(e)}")
            raise
    
    def _sort_tasks_by_dependencies(self, tasks: List[TestTask]) -> List[TestTask]:
        """按依賴關係和優先級排序任務"""
        # 創建任務映射
        task_map = {task.task_id: task for task in tasks}
        
        # 拓撲排序
        sorted_tasks = []
        visited = set()
        visiting = set()
        
        def visit(task_id: str):
            if task_id in visiting:
                raise ValueError(f"檢測到循環依賴: {task_id}")
            if task_id in visited:
                return
            
            visiting.add(task_id)
            
            task = task_map.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id in task_map:
                        visit(dep_id)
                
                sorted_tasks.append(task)
                visited.add(task_id)
            
            visiting.remove(task_id)
        
        # 訪問所有任務
        for task in tasks:
            if task.task_id not in visited:
                visit(task.task_id)
        
        # 按優先級排序（相同依賴層級內）
        return sorted(sorted_tasks, key=lambda t: (-t.priority, t.task_id))
    
    async def _execute_tasks_parallel(self, tasks: List[TestTask], 
                                    parallel_limit: int) -> List[TestResult]:
        """並行執行任務"""
        results = []
        semaphore = asyncio.Semaphore(parallel_limit)
        
        async def execute_single_task(task: TestTask) -> TestResult:
            async with semaphore:
                return await self._execute_task(task)
        
        # 創建任務協程
        task_coroutines = [execute_single_task(task) for task in tasks]
        
        # 等待所有任務完成
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # 處理異常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 創建失敗結果
                task = tasks[i]
                failed_result = TestResult(
                    task_id=task.task_id,
                    test_type=task.test_type,
                    provider="unknown",
                    success=False,
                    execution_time=0.0,
                    result_data={},
                    error_details=str(result)
                )
                processed_results.append(failed_result)
                logger.error(f"任務 {task.task_id} 執行異常: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_task(self, task: TestTask) -> TestResult:
        """執行單個測試任務"""
        logger.info(f"開始執行任務: {task.task_id} ({task.test_type.value})")
        
        task.status = TestStatus.RUNNING
        task.start_time = datetime.now()
        
        # 準備命令
        cmd = self._prepare_command(task)
        
        # 啟動任務資源監控
        task_monitor = ResourceMonitor()
        task_monitor.start_monitoring()
        
        try:
            # 執行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.running_tasks[task.task_id] = process
            
            # 等待完成或超時
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout
                )
                
                task.end_time = datetime.now()
                execution_time = (task.end_time - task.start_time).total_seconds()
                
                # 停止資源監控
                resource_usage = task_monitor.stop_monitoring()
                task.resource_usage = resource_usage
                
                # 檢查執行結果
                if process.returncode == 0:
                    task.status = TestStatus.COMPLETED
                    
                    # 查找結果文件
                    result_file = self._find_result_file(task)
                    task.result_file = result_file
                    
                    # 解析結果
                    result_data = self._parse_result_file(result_file) if result_file else {}
                    
                    result = TestResult(
                        task_id=task.task_id,
                        test_type=task.test_type,
                        provider="multiple" if len(task.providers) > 1 else task.providers[0],
                        success=True,
                        execution_time=execution_time,
                        result_data=result_data,
                        resource_usage=resource_usage
                    )
                    
                    logger.info(f"任務 {task.task_id} 執行成功，耗時 {execution_time:.2f}秒")
                    
                else:
                    task.status = TestStatus.FAILED
                    error_msg = stderr.decode('utf-8', errors='ignore')
                    task.error_message = error_msg
                    
                    result = TestResult(
                        task_id=task.task_id,
                        test_type=task.test_type,
                        provider="multiple" if len(task.providers) > 1 else task.providers[0],
                        success=False,
                        execution_time=execution_time,
                        result_data={},
                        error_details=error_msg,
                        resource_usage=resource_usage
                    )
                    
                    logger.error(f"任務 {task.task_id} 執行失敗: {error_msg}")
                
            except asyncio.TimeoutError:
                task.status = TestStatus.TIMEOUT
                task.end_time = datetime.now()
                
                # 終止進程
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except:
                    process.kill()
                
                resource_usage = task_monitor.stop_monitoring()
                task.resource_usage = resource_usage
                
                result = TestResult(
                    task_id=task.task_id,
                    test_type=task.test_type,
                    provider="multiple" if len(task.providers) > 1 else task.providers[0],
                    success=False,
                    execution_time=task.timeout,
                    result_data={},
                    error_details=f"任務超時 ({task.timeout}秒)",
                    resource_usage=resource_usage
                )
                
                logger.warning(f"任務 {task.task_id} 執行超時")
            
            finally:
                # 清理
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
            
            return result
            
        except Exception as e:
            task.status = TestStatus.FAILED
            task.end_time = datetime.now()
            task.error_message = str(e)
            
            resource_usage = task_monitor.stop_monitoring()
            task.resource_usage = resource_usage
            
            result = TestResult(
                task_id=task.task_id,
                test_type=task.test_type,
                provider="multiple" if len(task.providers) > 1 else task.providers[0],
                success=False,
                execution_time=0.0,
                result_data={},
                error_details=str(e),
                resource_usage=resource_usage
            )
            
            logger.error(f"任務 {task.task_id} 執行異常: {str(e)}")
            return result
    
    def _prepare_command(self, task: TestTask) -> List[str]:
        """準備執行命令"""
        cmd = ["python", task.test_script]
        
        # 添加提供商參數
        if task.providers:
            cmd.extend(["--providers"] + task.providers)
        
        # 添加配置參數
        for key, value in task.config.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])
        
        # 添加輸出目錄
        output_file = self.output_dir / "results" / f"{task.task_id}_result.json"
        cmd.extend(["--output", str(output_file)])
        
        return cmd
    
    def _find_result_file(self, task: TestTask) -> Optional[str]:
        """查找結果文件"""
        # 可能的結果文件位置
        possible_files = [
            self.output_dir / "results" / f"{task.task_id}_result.json",
            Path(f"{task.task_id}_result.json"),
            Path(f"test_results_{task.task_id}.json"),
            Path(f"{task.test_type.value}_results.json")
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                return str(file_path)
        
        # 搜尋最近創建的結果文件
        result_pattern = f"*{task.task_id}*.json"
        recent_files = list(Path(".").glob(result_pattern))
        
        if recent_files:
            # 返回最新的文件
            latest_file = max(recent_files, key=lambda f: f.stat().st_mtime)
            return str(latest_file)
        
        return None
    
    def _parse_result_file(self, file_path: str) -> Dict[str, Any]:
        """解析結果文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"解析結果文件失敗 {file_path}: {str(e)}")
            return {}
    
    def _save_suite_result(self, result: Dict[str, Any]) -> str:
        """保存套件結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / "results" / f"suite_result_{result['suite_id']}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        return str(filename)
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，正在清理...")
        
        # 終止所有運行中的任務
        for task_id, process in self.running_tasks.items():
            try:
                process.terminate()
                logger.info(f"已終止任務: {task_id}")
            except:
                pass
        
        # 停止資源監控
        self.resource_monitor.stop_monitoring()
        
        # 關閉執行器
        self.executor.shutdown(wait=False)
        
        logger.info("清理完成")
        sys.exit(0)
    
    def get_suite_status(self, suite_id: str) -> Dict[str, Any]:
        """獲取套件狀態"""
        if suite_id not in self.test_suites:
            return {"error": f"套件 {suite_id} 不存在"}
        
        suite = self.test_suites[suite_id]
        
        task_statuses = {}
        for task in suite.tasks:
            task_statuses[task.task_id] = {
                'status': task.status.value,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'error_message': task.error_message
            }
        
        return {
            'suite_id': suite_id,
            'name': suite.name,
            'status': suite.status.value,
            'total_tasks': len(suite.tasks),
            'task_statuses': task_statuses,
            'created_time': suite.created_time.isoformat()
        }
    
    def list_available_providers(self) -> List[str]:
        """列出可用的提供商"""
        return [provider.value for provider in LLMProvider]
    
    def cleanup(self):
        """清理資源"""
        logger.info("開始清理資源...")
        
        # 停止所有運行中的任務
        for task_id, process in self.running_tasks.items():
            try:
                process.terminate()
                logger.info(f"已終止任務: {task_id}")
            except:
                pass
        
        # 停止資源監控
        self.resource_monitor.stop_monitoring()
        
        # 關閉執行器
        self.executor.shutdown(wait=True)
        
        logger.info("資源清理完成")


def main():
    """主函數 - 自動化測試執行器入口點"""
    print("🤖 自動化LLM測試執行器")
    print("=" * 60)
    
    # 創建測試執行器
    runner = AutomatedLLMTestRunner()
    
    try:
        # 獲取可用提供商
        available_providers = runner.list_available_providers()
        print(f"\n📋 可用的LLM提供商: {', '.join(available_providers)}")
        
        # 選擇測試模式
        print("\n🎯 選擇測試模式:")
        print("1. 快速測試 (基礎功能驗證)")
        print("2. 全面測試 (完整性能評估)")
        print("3. 壓力測試 (高負載測試)")
        print("4. 自定義測試")
        
        choice = input("\n請選擇 (1-4): ").strip()
        
        # 選擇提供商
        print(f"\n📝 選擇要測試的提供商 (可多選，用逗號分隔):")
        print(f"可選: {', '.join(available_providers)}")
        provider_input = input("提供商: ").strip()
        
        if not provider_input:
            providers = available_providers[:2]  # 默認選擇前兩個
        else:
            providers = [p.strip() for p in provider_input.split(',') if p.strip() in available_providers]
        
        if not providers:
            print("❌ 沒有選擇有效的提供商")
            return
        
        print(f"\n✅ 已選擇提供商: {', '.join(providers)}")
        
        # 創建測試套件
        if choice == "1":
            suite_id = runner.create_quick_test_suite(providers)
        elif choice == "2":
            suite_id = runner.create_comprehensive_test_suite(providers)
        elif choice == "3":
            suite_id = runner.create_stress_test_suite(providers)
        else:
            print("❌ 自定義測試模式尚未實現")
            return
        
        # 運行測試套件
        print(f"\n🚀 開始執行測試套件: {suite_id}")
        
        async def run_tests():
            result = await runner.run_test_suite(suite_id)
            return result
        
        # 執行測試
        result = asyncio.run(run_tests())
        
        # 顯示結果摘要
        print("\n📊 測試結果摘要:")
        print(f"   套件: {result['suite_name']}")
        print(f"   狀態: {result['status']}")
        print(f"   總任務: {result['total_tasks']}")
        print(f"   成功: {result['successful_tasks']}")
        print(f"   失敗: {result['failed_tasks']}")
        print(f"   成功率: {result['success_rate']:.1%}")
        print(f"   執行時間: {result['execution_time']:.2f}秒")
        
        if result['resource_usage']:
            print(f"   平均CPU: {result['resource_usage'].get('avg_cpu_percent', 0):.1f}%")
            print(f"   平均記憶體: {result['resource_usage'].get('avg_memory_mb', 0):.1f}MB")
        
        print(f"\n💾 詳細結果已保存到: {runner.output_dir / 'results'}")
        
        # 生成報告
        print("\n📄 是否生成對比報告? (y/n): ", end="")
        if input().strip().lower() == 'y':
            print("正在生成報告...")
            # 這裡可以調用報告生成器
            subprocess.run(["python", "llm_comparison_report_generator.py"], check=False)
        
    except KeyboardInterrupt:
        print("\n❌ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試執行過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理資源
        runner.cleanup()


if __name__ == "__main__":
    main()