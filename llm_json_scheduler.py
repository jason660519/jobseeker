#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON檔案調度器實現
負責監控、調度和處理LLM生成的JSON檔案

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import aioredis
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import uuid

# 導入現有組件
from jobseeker.smart_router import SmartJobRouter
from jobseeker.intelligent_router import IntelligentRouter
from jobseeker.data_manager import DataManager
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


class TaskPriority(Enum):
    """任務優先級"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ProcessingMode(Enum):
    """處理模式"""
    REALTIME = "realtime"  # 即時處理
    BATCH = "batch"       # 批量處理
    HYBRID = "hybrid"     # 混合模式


@dataclass
class TaskInfo:
    """任務信息"""
    task_id: str
    file_path: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    user_id: Optional[str] = None
    user_tier: str = "free"
    estimated_time: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """處理結果"""
    task_id: str
    success: bool
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    worker_node: Optional[str] = None
    output_files: List[str] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []


class LLMFileWatcher(FileSystemEventHandler):
    """
    LLM檔案監控器
    監控指定目錄中新生成的JSON檔案
    """

    def __init__(self, scheduler: 'LLMJSONScheduler'):
        self.scheduler = scheduler
        self.logger = get_enhanced_logger(self.__class__.__name__, LogCategory.MONITORING)

    def on_created(self, event):
        """檔案創建事件處理"""
        if not event.is_directory and event.src_path.endswith('.json'):
            asyncio.create_task(self._handle_new_file(event.src_path))

    async def _handle_new_file(self, file_path: str):
        """處理新檔案"""
        try:
            self.logger.info(f"檢測到新的JSON檔案: {file_path}")
            
            # 等待檔案寫入完成
            await asyncio.sleep(0.5)
            
            # 提取檔案元數據
            task_info = await self._extract_task_info(file_path)
            
            # 添加到調度器
            await self.scheduler.add_task(task_info)
            
        except Exception as e:
            self.logger.error(f"處理新檔案失敗 {file_path}: {e}")

    async def _extract_task_info(self, file_path: str) -> TaskInfo:
        """從檔案路徑和內容提取任務信息"""
        
        # 從檔案名提取信息
        file_name = Path(file_path).stem
        parts = file_name.split('_')
        
        task_type = parts[1] if len(parts) > 1 else 'unknown'
        provider = parts[2] if len(parts) > 2 else 'unknown'
        session_id = parts[3] if len(parts) > 3 else str(uuid.uuid4())[:8]
        
        # 讀取檔案內容獲取更多信息
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
                metadata = data.get('metadata', {})
                user_id = metadata.get('user_id')
                user_tier = metadata.get('user_tier', 'free')
                
        except Exception as e:
            self.logger.warning(f"無法讀取檔案內容 {file_path}: {e}")
            user_id = None
            user_tier = 'free'
        
        # 確定任務優先級
        priority = self._determine_priority(task_type, user_tier)
        
        return TaskInfo(
            task_id=f"{task_type}_{session_id}_{int(time.time())}",
            file_path=file_path,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            user_id=user_id,
            user_tier=user_tier,
            metadata={
                'provider': provider,
                'session_id': session_id,
                'file_size': Path(file_path).stat().st_size
            }
        )

    def _determine_priority(self, task_type: str, user_tier: str) -> TaskPriority:
        """確定任務優先級"""
        
        # 付費用戶的意圖分析任務 - 高優先級
        if user_tier == 'premium' and task_type == 'intent_analysis':
            return TaskPriority.HIGH
        
        # 即時查詢相關任務 - 普通優先級
        if task_type in ['job_extraction', 'data_enrichment']:
            return TaskPriority.NORMAL
        
        # 批量處理任務 - 低優先級
        return TaskPriority.LOW


class TaskQueue:
    """
    任務佇列管理器
    支持優先級佇列和負載均衡
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self.redis = None
        self.local_queues = {
            TaskPriority.HIGH: asyncio.PriorityQueue(),
            TaskPriority.NORMAL: asyncio.PriorityQueue(),
            TaskPriority.LOW: asyncio.PriorityQueue()
        }
        self.queue_stats = {
            'total_added': 0,
            'total_processed': 0,
            'current_size': 0
        }
        self.logger = get_enhanced_logger(self.__class__.__name__, LogCategory.QUEUE)

    async def initialize(self):
        """初始化佇列"""
        if self.redis_url:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
                self.logger.info("Redis佇列已連接")
            except Exception as e:
                self.logger.warning(f"Redis連接失敗，使用本地佇列: {e}")

    async def add_task(self, task_info: TaskInfo):
        """添加任務到佇列"""
        
        priority_score = self._calculate_priority_score(task_info)
        
        if self.redis:
            # 使用Redis佇列
            await self._add_to_redis_queue(task_info, priority_score)
        else:
            # 使用本地佇列
            await self.local_queues[task_info.priority].put(
                (priority_score, task_info)
            )
        
        self.queue_stats['total_added'] += 1
        self.queue_stats['current_size'] += 1
        
        self.logger.info(
            f"任務已添加到佇列: {task_info.task_id}, 優先級: {task_info.priority.value}"
        )

    async def get_next_task(self) -> Optional[TaskInfo]:
        """獲取下一個任務"""
        
        if self.redis:
            return await self._get_from_redis_queue()
        else:
            return await self._get_from_local_queue()

    async def _get_from_local_queue(self) -> Optional[TaskInfo]:
        """從本地佇列獲取任務"""
        
        # 按優先級順序檢查佇列
        for priority in [TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self.local_queues[priority]
            
            if not queue.empty():
                try:
                    _, task_info = await asyncio.wait_for(queue.get(), timeout=0.1)
                    self.queue_stats['current_size'] -= 1
                    return task_info
                except asyncio.TimeoutError:
                    continue
        
        return None

    def _calculate_priority_score(self, task_info: TaskInfo) -> float:
        """計算優先級分數（越小優先級越高）"""
        
        base_score = {
            TaskPriority.HIGH: 1.0,
            TaskPriority.NORMAL: 2.0,
            TaskPriority.LOW: 3.0
        }[task_info.priority]
        
        # 考慮等待時間
        wait_time = (datetime.now() - task_info.created_at).total_seconds()
        time_factor = wait_time / 3600  # 每小時降低0.1分
        
        # 考慮用戶等級
        user_factor = 0.5 if task_info.user_tier == 'premium' else 0.0
        
        return base_score - time_factor - user_factor

    async def _add_to_redis_queue(self, task_info: TaskInfo, priority_score: float):
        """添加任務到Redis佇列"""
        
        queue_key = f"llm_tasks:{task_info.priority.value}"
        task_data = json.dumps(asdict(task_info), default=str)
        
        await self.redis.zadd(queue_key, {task_data: priority_score})

    async def _get_from_redis_queue(self) -> Optional[TaskInfo]:
        """從Redis佇列獲取任務"""
        
        # 按優先級順序檢查佇列
        for priority in [TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue_key = f"llm_tasks:{priority.value}"
            
            # 獲取最高優先級的任務
            result = await self.redis.zpopmin(queue_key, count=1)
            
            if result:
                task_data, _ = result[0]
                task_dict = json.loads(task_data)
                
                # 重建TaskInfo對象
                task_dict['priority'] = TaskPriority(task_dict['priority'])
                task_dict['status'] = TaskStatus(task_dict['status'])
                task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
                
                return TaskInfo(**task_dict)
        
        return None

    def get_queue_stats(self) -> Dict[str, Any]:
        """獲取佇列統計信息"""
        
        local_sizes = {
            priority.value: queue.qsize() 
            for priority, queue in self.local_queues.items()
        }
        
        return {
            **self.queue_stats,
            'local_queue_sizes': local_sizes
        }


class WorkerPool:
    """
    工作線程池
    管理並發處理任務的工作線程
    """

    def __init__(self, max_workers: int = 10, scheduler: 'LLMJSONScheduler' = None):
        self.max_workers = max_workers
        self.scheduler = scheduler
        self.active_workers = set()
        self.worker_stats = {}
        self.semaphore = asyncio.Semaphore(max_workers)
        self.logger = get_enhanced_logger(self.__class__.__name__, LogCategory.WORKER)

    async def process_task(self, task_info: TaskInfo) -> ProcessingResult:
        """處理單個任務"""
        
        worker_id = f"worker_{len(self.active_workers)}_{int(time.time())}"
        
        async with self.semaphore:
            self.active_workers.add(worker_id)
            start_time = time.time()
            
            try:
                self.logger.info(f"工作線程 {worker_id} 開始處理任務 {task_info.task_id}")
                
                # 更新任務狀態
                task_info.status = TaskStatus.PROCESSING
                await self.scheduler.update_task_status(task_info)
                
                # 根據任務類型選擇處理方法
                result = await self._process_by_type(task_info, worker_id)
                
                processing_time = time.time() - start_time
                
                # 記錄工作線程統計
                self._update_worker_stats(worker_id, processing_time, True)
                
                self.logger.info(
                    f"任務 {task_info.task_id} 處理完成，耗時 {processing_time:.2f}秒"
                )
                
                return ProcessingResult(
                    task_id=task_info.task_id,
                    success=True,
                    result_data=result,
                    processing_time=processing_time,
                    worker_node=worker_id
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                self._update_worker_stats(worker_id, processing_time, False)
                
                self.logger.error(f"任務 {task_info.task_id} 處理失敗: {e}")
                
                return ProcessingResult(
                    task_id=task_info.task_id,
                    success=False,
                    error_message=str(e),
                    processing_time=processing_time,
                    worker_node=worker_id
                )
                
            finally:
                self.active_workers.discard(worker_id)

    async def _process_by_type(self, task_info: TaskInfo, worker_id: str) -> Dict[str, Any]:
        """根據任務類型處理"""
        
        # 讀取JSON檔案
        async with aiofiles.open(task_info.file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            json_data = json.loads(content)
        
        task_type = task_info.task_type
        
        if task_type == 'intent_analysis':
            return await self._process_intent_analysis(json_data, task_info)
        
        elif task_type == 'job_extraction':
            return await self._process_job_extraction(json_data, task_info)
        
        elif task_type == 'data_enrichment':
            return await self._process_data_enrichment(json_data, task_info)
        
        elif task_type == 'quality_validation':
            return await self._process_quality_validation(json_data, task_info)
        
        else:
            raise ValueError(f"未知的任務類型: {task_type}")

    async def _process_intent_analysis(self, json_data: Dict, task_info: TaskInfo) -> Dict[str, Any]:
        """處理意圖分析任務"""
        
        intent_data = json_data.get('content', {}).get('intent', {})
        
        if not intent_data.get('is_job_related', False):
            return {
                'status': 'rejected',
                'reason': 'Query is not job-related',
                'confidence': intent_data.get('confidence', 0.0)
            }
        
        # 提取搜索參數
        search_params = {
            'query': intent_data.get('job_title', ''),
            'location': intent_data.get('location', ''),
            'skills': intent_data.get('skills', []),
            'experience_level': intent_data.get('experience_level', '')
        }
        
        # 使用智能路由器進行搜索
        smart_router = SmartJobRouter()
        search_result = smart_router.search_jobs(
            query=search_params['query'],
            location=search_params['location'],
            max_results=25
        )
        
        return {
            'status': 'completed',
            'search_params': search_params,
            'search_result': {
                'total_jobs': search_result.total_jobs,
                'successful_platforms': search_result.successful_platforms,
                'execution_time': search_result.total_execution_time,
                'jobs': [asdict(job) for job in search_result.jobs[:10]]  # 只返回前10個
            }
        }

    async def _process_job_extraction(self, json_data: Dict, task_info: TaskInfo) -> Dict[str, Any]:
        """處理職位提取任務"""
        
        extraction_data = json_data.get('content', {})
        
        # 這裡可以調用具體的職位提取邏輯
        # 例如：從網頁內容中提取結構化職位信息
        
        return {
            'status': 'completed',
            'extracted_jobs': extraction_data.get('jobs', []),
            'extraction_metadata': {
                'source_url': extraction_data.get('source_url'),
                'extraction_time': datetime.now().isoformat(),
                'quality_score': 0.85
            }
        }

    async def _process_data_enrichment(self, json_data: Dict, task_info: TaskInfo) -> Dict[str, Any]:
        """處理數據豐富任務"""
        
        enrichment_data = json_data.get('content', {})
        
        # 數據豐富邏輯：添加薪資信息、公司信息等
        enriched_jobs = []
        
        for job in enrichment_data.get('jobs', []):
            enriched_job = job.copy()
            
            # 添加估算薪資（示例）
            if not job.get('salary'):
                enriched_job['estimated_salary'] = self._estimate_salary(job)
            
            # 添加公司信息（示例）
            if job.get('company'):
                enriched_job['company_info'] = await self._get_company_info(job['company'])
            
            enriched_jobs.append(enriched_job)
        
        return {
            'status': 'completed',
            'enriched_jobs': enriched_jobs,
            'enrichment_stats': {
                'total_jobs': len(enriched_jobs),
                'salary_enriched': len([j for j in enriched_jobs if 'estimated_salary' in j]),
                'company_enriched': len([j for j in enriched_jobs if 'company_info' in j])
            }
        }

    async def _process_quality_validation(self, json_data: Dict, task_info: TaskInfo) -> Dict[str, Any]:
        """處理品質驗證任務"""
        
        validation_data = json_data.get('content', {})
        
        # 品質驗證邏輯
        validation_results = []
        
        for job in validation_data.get('jobs', []):
            validation_result = {
                'job_id': job.get('id'),
                'is_valid': True,
                'quality_score': 0.0,
                'issues': []
            }
            
            # 檢查必要欄位
            required_fields = ['title', 'company', 'location']
            for field in required_fields:
                if not job.get(field):
                    validation_result['issues'].append(f"Missing {field}")
                    validation_result['is_valid'] = False
            
            # 計算品質分數
            validation_result['quality_score'] = self._calculate_quality_score(job)
            
            validation_results.append(validation_result)
        
        return {
            'status': 'completed',
            'validation_results': validation_results,
            'summary': {
                'total_jobs': len(validation_results),
                'valid_jobs': len([r for r in validation_results if r['is_valid']]),
                'average_quality': sum(r['quality_score'] for r in validation_results) / len(validation_results) if validation_results else 0
            }
        }

    def _estimate_salary(self, job: Dict) -> str:
        """估算薪資（示例實現）"""
        # 這裡可以實現基於職位標題、地點等的薪資估算邏輯
        return "$60,000 - $80,000 per year (estimated)"

    async def _get_company_info(self, company_name: str) -> Dict:
        """獲取公司信息（示例實現）"""
        # 這裡可以調用外部API獲取公司信息
        return {
            'name': company_name,
            'industry': 'Technology',
            'size': '100-500 employees',
            'rating': 4.2
        }

    def _calculate_quality_score(self, job: Dict) -> float:
        """計算品質分數"""
        score = 0.0
        
        # 檢查各個欄位的完整性
        if job.get('title'): score += 0.2
        if job.get('company'): score += 0.2
        if job.get('location'): score += 0.15
        if job.get('description'): score += 0.2
        if job.get('salary'): score += 0.15
        if job.get('job_url'): score += 0.1
        
        return min(score, 1.0)

    def _update_worker_stats(self, worker_id: str, processing_time: float, success: bool):
        """更新工作線程統計"""
        
        if worker_id not in self.worker_stats:
            self.worker_stats[worker_id] = {
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'total_time': 0.0,
                'average_time': 0.0
            }
        
        stats = self.worker_stats[worker_id]
        stats['total_tasks'] += 1
        stats['total_time'] += processing_time
        
        if success:
            stats['successful_tasks'] += 1
        else:
            stats['failed_tasks'] += 1
        
        stats['average_time'] = stats['total_time'] / stats['total_tasks']

    def get_worker_stats(self) -> Dict[str, Any]:
        """獲取工作線程統計"""
        
        return {
            'active_workers': len(self.active_workers),
            'max_workers': self.max_workers,
            'worker_details': self.worker_stats
        }


class LLMJSONScheduler:
    """
    LLM JSON檔案調度器主類
    統一管理檔案監控、任務調度和處理
    """

    def __init__(self, 
                 watch_directory: str = "./data/llm_generated/raw",
                 output_directory: str = "./data/llm_generated/processed",
                 max_workers: int = 10,
                 processing_mode: ProcessingMode = ProcessingMode.HYBRID,
                 redis_url: str = None):
        
        self.watch_directory = Path(watch_directory)
        self.output_directory = Path(output_directory)
        self.processing_mode = processing_mode
        
        # 確保目錄存在
        self.watch_directory.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # 初始化組件
        self.file_watcher = LLMFileWatcher(self)
        self.task_queue = TaskQueue(redis_url)
        self.worker_pool = WorkerPool(max_workers, self)
        
        # 監控組件
        self.observer = Observer()
        
        # 統計信息
        self.scheduler_stats = {
            'start_time': datetime.now(),
            'total_files_processed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_processing_time': 0.0
        }
        
        # 任務狀態追蹤
        self.task_status = {}
        
        self.logger = get_enhanced_logger(self.__class__.__name__, LogCategory.SCHEDULER)
        
        # 批量處理配置
        self.batch_config = {
            'batch_size': 20,
            'batch_timeout': 300,  # 5分鐘
            'current_batch': [],
            'last_batch_time': time.time()
        }

    async def start(self):
        """啟動調度器"""
        
        self.logger.info("正在啟動LLM JSON調度器...")
        
        # 初始化組件
        await self.task_queue.initialize()
        
        # 啟動檔案監控
        self.observer.schedule(
            self.file_watcher, 
            str(self.watch_directory), 
            recursive=True
        )
        self.observer.start()
        
        # 啟動任務處理循環
        asyncio.create_task(self._task_processing_loop())
        
        # 如果是批量模式，啟動批量處理循環
        if self.processing_mode in [ProcessingMode.BATCH, ProcessingMode.HYBRID]:
            asyncio.create_task(self._batch_processing_loop())
        
        self.logger.info(f"調度器已啟動，監控目錄: {self.watch_directory}")
        self.logger.info(f"處理模式: {self.processing_mode.value}")

    async def stop(self):
        """停止調度器"""
        
        self.logger.info("正在停止調度器...")
        
        # 停止檔案監控
        self.observer.stop()
        self.observer.join()
        
        # 處理剩餘任務
        await self._process_remaining_tasks()
        
        self.logger.info("調度器已停止")

    async def add_task(self, task_info: TaskInfo):
        """添加任務"""
        
        # 記錄任務狀態
        self.task_status[task_info.task_id] = task_info
        
        # 根據處理模式決定如何處理
        if self.processing_mode == ProcessingMode.REALTIME:
            # 即時處理
            await self._process_task_immediately(task_info)
        
        elif self.processing_mode == ProcessingMode.BATCH:
            # 添加到批量處理
            await self._add_to_batch(task_info)
        
        else:  # HYBRID
            # 混合模式：根據優先級決定
            if task_info.priority == TaskPriority.HIGH:
                await self._process_task_immediately(task_info)
            else:
                await self._add_to_batch(task_info)

    async def _task_processing_loop(self):
        """任務處理主循環"""
        
        while True:
            try:
                # 獲取下一個任務
                task_info = await self.task_queue.get_next_task()
                
                if task_info:
                    # 處理任務
                    asyncio.create_task(self._process_task(task_info))
                else:
                    # 沒有任務時短暫休眠
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"任務處理循環錯誤: {e}")
                await asyncio.sleep(5)

    async def _batch_processing_loop(self):
        """批量處理循環"""
        
        while True:
            try:
                current_time = time.time()
                batch = self.batch_config['current_batch']
                
                # 檢查是否需要處理批量
                should_process = (
                    len(batch) >= self.batch_config['batch_size'] or
                    (batch and current_time - self.batch_config['last_batch_time'] > self.batch_config['batch_timeout'])
                )
                
                if should_process:
                    await self._process_current_batch()
                
                await asyncio.sleep(10)  # 每10秒檢查一次
                
            except Exception as e:
                self.logger.error(f"批量處理循環錯誤: {e}")
                await asyncio.sleep(30)

    async def _process_task_immediately(self, task_info: TaskInfo):
        """立即處理任務"""
        
        self.logger.info(f"立即處理任務: {task_info.task_id}")
        await self._process_task(task_info)

    async def _add_to_batch(self, task_info: TaskInfo):
        """添加到批量處理"""
        
        self.batch_config['current_batch'].append(task_info)
        self.logger.info(f"任務已添加到批量處理: {task_info.task_id}")

    async def _process_current_batch(self):
        """處理當前批量"""
        
        batch = self.batch_config['current_batch']
        if not batch:
            return
        
        self.logger.info(f"開始處理批量任務，共 {len(batch)} 個任務")
        
        # 並發處理批量任務
        tasks = [self._process_task(task_info) for task_info in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 清空批量
        self.batch_config['current_batch'] = []
        self.batch_config['last_batch_time'] = time.time()
        
        self.logger.info("批量任務處理完成")

    async def _process_task(self, task_info: TaskInfo):
        """處理單個任務"""
        
        try:
            # 使用工作線程池處理任務
            result = await self.worker_pool.process_task(task_info)
            
            # 保存處理結果
            await self._save_processing_result(result)
            
            # 更新統計
            self._update_scheduler_stats(result)
            
            # 更新任務狀態
            if result.success:
                task_info.status = TaskStatus.COMPLETED
            else:
                task_info.status = TaskStatus.FAILED
                
                # 檢查是否需要重試
                if task_info.retry_count < task_info.max_retries:
                    task_info.retry_count += 1
                    task_info.status = TaskStatus.RETRYING
                    
                    # 延遲重試
                    await asyncio.sleep(2 ** task_info.retry_count)  # 指數退避
                    await self.task_queue.add_task(task_info)
            
            await self.update_task_status(task_info)
            
        except Exception as e:
            self.logger.error(f"任務處理失敗 {task_info.task_id}: {e}")
            
            task_info.status = TaskStatus.FAILED
            await self.update_task_status(task_info)

    async def _save_processing_result(self, result: ProcessingResult):
        """保存處理結果"""
        
        if not result.success:
            return
        
        # 生成輸出檔案路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_directory / f"{result.task_id}_{timestamp}_result.json"
        
        # 保存結果
        result_data = {
            'task_id': result.task_id,
            'processing_time': result.processing_time,
            'worker_node': result.worker_node,
            'timestamp': datetime.now().isoformat(),
            'result': result.result_data
        }
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(result_data, indent=2, ensure_ascii=False))
        
        result.output_files.append(str(output_file))
        
        self.logger.info(f"處理結果已保存: {output_file}")

    async def update_task_status(self, task_info: TaskInfo):
        """更新任務狀態"""
        
        self.task_status[task_info.task_id] = task_info
        
        # 這裡可以添加狀態持久化邏輯
        # 例如：保存到數據庫或Redis

    def _update_scheduler_stats(self, result: ProcessingResult):
        """更新調度器統計"""
        
        self.scheduler_stats['total_files_processed'] += 1
        
        if result.success:
            self.scheduler_stats['successful_tasks'] += 1
        else:
            self.scheduler_stats['failed_tasks'] += 1
        
        # 更新平均處理時間
        total_tasks = self.scheduler_stats['total_files_processed']
        current_avg = self.scheduler_stats['average_processing_time']
        new_avg = (current_avg * (total_tasks - 1) + result.processing_time) / total_tasks
        self.scheduler_stats['average_processing_time'] = new_avg

    async def _process_remaining_tasks(self):
        """處理剩餘任務"""
        
        self.logger.info("處理剩餘任務...")
        
        # 處理批量中的剩餘任務
        if self.batch_config['current_batch']:
            await self._process_current_batch()
        
        # 處理佇列中的剩餘任務
        remaining_count = 0
        while True:
            task_info = await self.task_queue.get_next_task()
            if not task_info:
                break
            
            await self._process_task(task_info)
            remaining_count += 1
        
        self.logger.info(f"已處理 {remaining_count} 個剩餘任務")

    def get_status(self) -> Dict[str, Any]:
        """獲取調度器狀態"""
        
        return {
            'scheduler_stats': self.scheduler_stats,
            'queue_stats': self.task_queue.get_queue_stats(),
            'worker_stats': self.worker_pool.get_worker_stats(),
            'processing_mode': self.processing_mode.value,
            'batch_config': {
                'current_batch_size': len(self.batch_config['current_batch']),
                'batch_size_limit': self.batch_config['batch_size'],
                'batch_timeout': self.batch_config['batch_timeout']
            },
            'task_status_summary': {
                status.value: len([t for t in self.task_status.values() if t.status == status])
                for status in TaskStatus
            }
        }

    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """獲取特定任務狀態"""
        
        return self.task_status.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        
        if task_id in self.task_status:
            task_info = self.task_status[task_id]
            
            if task_info.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                task_info.status = TaskStatus.FAILED
                await self.update_task_status(task_info)
                
                self.logger.info(f"任務已取消: {task_id}")
                return True
        
        return False


# 使用示例
if __name__ == "__main__":
    async def main():
        # 創建調度器
        scheduler = LLMJSONScheduler(
            watch_directory="./data/llm_generated/raw",
            output_directory="./data/llm_generated/processed",
            max_workers=5,
            processing_mode=ProcessingMode.HYBRID
        )
        
        try:
            # 啟動調度器
            await scheduler.start()
            
            # 運行一段時間
            print("調度器正在運行，按 Ctrl+C 停止...")
            while True:
                await asyncio.sleep(10)
                
                # 打印狀態
                status = scheduler.get_status()
                print(f"\n調度器狀態:")
                print(f"  已處理任務: {status['scheduler_stats']['total_files_processed']}")
                print(f"  成功任務: {status['scheduler_stats']['successful_tasks']}")
                print(f"  失敗任務: {status['scheduler_stats']['failed_tasks']}")
                print(f"  平均處理時間: {status['scheduler_stats']['average_processing_time']:.2f}秒")
                print(f"  活躍工作線程: {status['worker_stats']['active_workers']}")
                
        except KeyboardInterrupt:
            print("\n正在停止調度器...")
            await scheduler.stop()
            print("調度器已停止")
    
    # 運行主程序
    asyncio.run(main())