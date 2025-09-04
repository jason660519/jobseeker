#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台異步搜尋調度器
支援地區導向的智能平台選擇和任務分配追蹤

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import aiofiles
import aioredis
from concurrent.futures import ThreadPoolExecutor

# 導入現有組件
from jobseeker.smart_router import SmartJobRouter
from jobseeker.intelligent_router import IntelligentRouter
from jobseeker.route_manager import RouteManager
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


class PlatformType(Enum):
    """平台類型枚舉"""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GOOGLE = "google"
    SEEK = "seek"
    TW104 = "tw104"
    TW1111 = "tw1111"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"


class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class RegionType(Enum):
    """地區類型枚舉"""
    US = "us"
    TAIWAN = "taiwan"
    AUSTRALIA = "australia"
    GLOBAL = "global"
    ASIA_PACIFIC = "asia_pacific"
    EUROPE = "europe"


@dataclass
class PlatformTask:
    """單個平台任務"""
    task_id: str
    platform: PlatformType
    query: str
    location: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    job_count: int = 0
    worker_id: Optional[str] = None


@dataclass
class MultiPlatformJob:
    """多平台搜尋任務"""
    job_id: str
    original_query: str
    location: str
    region: RegionType
    target_platforms: List[PlatformType]
    platform_tasks: Dict[str, PlatformTask] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 1
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化平台任務"""
        for platform in self.target_platforms:
            task_id = f"{self.job_id}_{platform.value}"
            self.platform_tasks[platform.value] = PlatformTask(
                task_id=task_id,
                platform=platform,
                query=self.original_query,
                location=self.location,
                status=TaskStatus.PENDING,
                created_at=self.created_at
            )


@dataclass
class PlatformCapability:
    """平台能力配置"""
    platform: PlatformType
    supported_regions: List[RegionType]
    max_concurrent_tasks: int
    reliability_score: float
    average_response_time: float
    cost_per_request: float
    strengths: List[str]
    limitations: List[str]


class RegionPlatformMapper:
    """地區平台映射器"""
    
    def __init__(self):
        """初始化地區平台映射配置"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        
        # 定義平台能力
        self.platform_capabilities = {
            PlatformType.LINKEDIN: PlatformCapability(
                platform=PlatformType.LINKEDIN,
                supported_regions=[RegionType.US, RegionType.GLOBAL, RegionType.EUROPE, RegionType.ASIA_PACIFIC],
                max_concurrent_tasks=5,
                reliability_score=0.9,
                average_response_time=3.5,
                cost_per_request=0.1,
                strengths=["專業職位", "高級職位", "網絡連接"],
                limitations=["需要登入", "反爬蟲嚴格"]
            ),
            PlatformType.INDEED: PlatformCapability(
                platform=PlatformType.INDEED,
                supported_regions=[RegionType.US, RegionType.GLOBAL, RegionType.EUROPE],
                max_concurrent_tasks=8,
                reliability_score=0.85,
                average_response_time=2.8,
                cost_per_request=0.05,
                strengths=["職位數量多", "覆蓋面廣", "更新頻繁"],
                limitations=["職位質量參差不齊"]
            ),
            PlatformType.GOOGLE: PlatformCapability(
                platform=PlatformType.GOOGLE,
                supported_regions=[RegionType.US, RegionType.GLOBAL, RegionType.EUROPE, RegionType.ASIA_PACIFIC],
                max_concurrent_tasks=10,
                reliability_score=0.8,
                average_response_time=2.0,
                cost_per_request=0.03,
                strengths=["搜尋範圍廣", "聚合多源", "速度快"],
                limitations=["結果重複", "詳細信息有限"]
            ),
            PlatformType.SEEK: PlatformCapability(
                platform=PlatformType.SEEK,
                supported_regions=[RegionType.AUSTRALIA, RegionType.ASIA_PACIFIC],
                max_concurrent_tasks=6,
                reliability_score=0.9,
                average_response_time=3.0,
                cost_per_request=0.08,
                strengths=["澳洲主導", "職位質量高", "薪資信息準確"],
                limitations=["地區限制"]
            ),
            PlatformType.TW104: PlatformCapability(
                platform=PlatformType.TW104,
                supported_regions=[RegionType.TAIWAN, RegionType.ASIA_PACIFIC],
                max_concurrent_tasks=4,
                reliability_score=0.85,
                average_response_time=4.0,
                cost_per_request=0.06,
                strengths=["台灣主導", "本地化好", "企業信息完整"],
                limitations=["僅限台灣"]
            ),
            PlatformType.TW1111: PlatformCapability(
                platform=PlatformType.TW1111,
                supported_regions=[RegionType.TAIWAN, RegionType.ASIA_PACIFIC],
                max_concurrent_tasks=4,
                reliability_score=0.8,
                average_response_time=4.5,
                cost_per_request=0.07,
                strengths=["台灣本土", "中小企業多", "薪資透明"],
                limitations=["僅限台灣", "職位更新較慢"]
            )
        }
        
        # 地區平台優先級映射
        self.region_platform_priority = {
            RegionType.US: [
                PlatformType.LINKEDIN,
                PlatformType.INDEED,
                PlatformType.GOOGLE
            ],
            RegionType.TAIWAN: [
                PlatformType.TW104,
                PlatformType.TW1111,
                PlatformType.LINKEDIN
            ],
            RegionType.AUSTRALIA: [
                PlatformType.SEEK,
                PlatformType.LINKEDIN,
                PlatformType.INDEED
            ],
            RegionType.GLOBAL: [
                PlatformType.LINKEDIN,
                PlatformType.INDEED,
                PlatformType.GOOGLE
            ]
        }
    
    def detect_region(self, query: str, location: str) -> RegionType:
        """檢測查詢的目標地區"""
        text = f"{query} {location}".lower()
        
        # 台灣關鍵詞
        taiwan_keywords = ["台灣", "taiwan", "taipei", "台北", "高雄", "kaohsiung", "taichung", "台中"]
        if any(keyword in text for keyword in taiwan_keywords):
            return RegionType.TAIWAN
        
        # 澳洲關鍵詞
        australia_keywords = ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide"]
        if any(keyword in text for keyword in australia_keywords):
            return RegionType.AUSTRALIA
        
        # 美國關鍵詞
        us_keywords = ["usa", "united states", "new york", "california", "texas", "florida", "seattle", "san francisco"]
        if any(keyword in text for keyword in us_keywords):
            return RegionType.US
        
        # 默認全球
        return RegionType.GLOBAL
    
    def get_platforms_for_region(self, region: RegionType, max_platforms: int = 3) -> List[PlatformType]:
        """獲取指定地區的推薦平台"""
        platforms = self.region_platform_priority.get(region, [])
        return platforms[:max_platforms]
    
    def get_platform_capability(self, platform: PlatformType) -> PlatformCapability:
        """獲取平台能力信息"""
        return self.platform_capabilities.get(platform)


class TaskTracker:
    """任務追蹤器"""
    
    def __init__(self, redis_url: str = None):
        """初始化任務追蹤器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.redis_url = redis_url
        self.redis_client = None
        self.active_jobs: Dict[str, MultiPlatformJob] = {}
        self.completed_jobs: Dict[str, MultiPlatformJob] = {}
        self.platform_workers: Dict[str, Set[str]] = {}
        
        # 初始化平台工作器集合
        for platform in PlatformType:
            self.platform_workers[platform.value] = set()
    
    async def initialize(self):
        """初始化Redis連接"""
        if self.redis_url:
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.logger.info("Redis連接成功")
            except Exception as e:
                self.logger.error(f"Redis連接失敗: {e}")
                self.redis_client = None
    
    async def register_job(self, job: MultiPlatformJob):
        """註冊新的多平台任務"""
        self.active_jobs[job.job_id] = job
        
        # 保存到Redis
        if self.redis_client:
            await self.redis_client.hset(
                "active_jobs",
                job.job_id,
                json.dumps(asdict(job), default=str)
            )
        
        self.logger.info(f"註冊多平台任務: {job.job_id}, 目標平台: {[p.value for p in job.target_platforms]}")
    
    async def update_platform_task_status(self, job_id: str, platform: str, status: TaskStatus, 
                                         result_data: Optional[Dict] = None, 
                                         error_message: Optional[str] = None,
                                         execution_time: float = 0.0,
                                         job_count: int = 0):
        """更新平台任務狀態"""
        if job_id not in self.active_jobs:
            self.logger.warning(f"任務 {job_id} 不存在")
            return
        
        job = self.active_jobs[job_id]
        if platform not in job.platform_tasks:
            self.logger.warning(f"平台任務 {platform} 不存在於任務 {job_id}")
            return
        
        platform_task = job.platform_tasks[platform]
        platform_task.status = status
        platform_task.execution_time = execution_time
        platform_task.job_count = job_count
        
        if status == TaskStatus.PROCESSING:
            platform_task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            platform_task.completed_at = datetime.now()
            platform_task.result_data = result_data
            platform_task.error_message = error_message
        
        # 檢查整體任務狀態
        await self._update_job_status(job)
        
        # 保存到Redis
        if self.redis_client:
            await self.redis_client.hset(
                "active_jobs",
                job_id,
                json.dumps(asdict(job), default=str)
            )
        
        self.logger.info(f"更新平台任務狀態: {job_id}_{platform} -> {status.value}")
    
    async def _update_job_status(self, job: MultiPlatformJob):
        """更新整體任務狀態"""
        platform_statuses = [task.status for task in job.platform_tasks.values()]
        
        # 如果所有平台任務都完成或失敗
        if all(status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
               for status in platform_statuses):
            
            # 如果至少有一個成功
            if any(status == TaskStatus.COMPLETED for status in platform_statuses):
                job.status = TaskStatus.COMPLETED
            else:
                job.status = TaskStatus.FAILED
            
            # 移動到已完成任務
            self.completed_jobs[job.job_id] = job
            del self.active_jobs[job.job_id]
            
            # 從Redis移除
            if self.redis_client:
                await self.redis_client.hdel("active_jobs", job.job_id)
                await self.redis_client.hset(
                    "completed_jobs",
                    job.job_id,
                    json.dumps(asdict(job), default=str)
                )
        
        elif any(status == TaskStatus.PROCESSING for status in platform_statuses):
            job.status = TaskStatus.PROCESSING
        elif any(status == TaskStatus.ASSIGNED for status in platform_statuses):
            job.status = TaskStatus.ASSIGNED
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)
        if not job:
            return None
        
        platform_status = {}
        for platform, task in job.platform_tasks.items():
            platform_status[platform] = {
                "status": task.status.value,
                "job_count": task.job_count,
                "execution_time": task.execution_time,
                "error_message": task.error_message
            }
        
        return {
            "job_id": job.job_id,
            "overall_status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "query": job.original_query,
            "location": job.location,
            "region": job.region.value,
            "target_platforms": [p.value for p in job.target_platforms],
            "platform_status": platform_status
        }
    
    def get_active_jobs_summary(self) -> Dict[str, Any]:
        """獲取活躍任務摘要"""
        total_jobs = len(self.active_jobs)
        platform_counts = {}
        
        for job in self.active_jobs.values():
            for platform_task in job.platform_tasks.values():
                platform = platform_task.platform.value
                status = platform_task.status.value
                
                if platform not in platform_counts:
                    platform_counts[platform] = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
                
                platform_counts[platform][status] = platform_counts[platform].get(status, 0) + 1
        
        return {
            "total_active_jobs": total_jobs,
            "platform_task_counts": platform_counts,
            "total_completed_jobs": len(self.completed_jobs)
        }


class MultiPlatformScheduler:
    """多平台異步搜尋調度器"""
    
    def __init__(self, 
                 max_concurrent_jobs: int = 10,
                 max_workers_per_platform: int = 3,
                 redis_url: str = None):
        """初始化多平台調度器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_workers_per_platform = max_workers_per_platform
        
        # 初始化組件
        self.region_mapper = RegionPlatformMapper()
        self.task_tracker = TaskTracker(redis_url)
        self.smart_router = SmartJobRouter()
        self.route_manager = RouteManager()
        
        # 工作器管理
        self.platform_workers: Dict[str, Set[str]] = {}
        self.worker_semaphores: Dict[str, asyncio.Semaphore] = {}
        
        # 初始化平台工作器
        for platform in PlatformType:
            self.platform_workers[platform.value] = set()
            capability = self.region_mapper.get_platform_capability(platform)
            max_workers = capability.max_concurrent_tasks if capability else self.max_workers_per_platform
            self.worker_semaphores[platform.value] = asyncio.Semaphore(max_workers)
        
        # 任務隊列
        self.pending_jobs: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.scheduler_task = None
    
    async def initialize(self):
        """初始化調度器"""
        await self.task_tracker.initialize()
        self.logger.info("多平台調度器初始化完成")
    
    async def start(self):
        """啟動調度器"""
        if self.running:
            self.logger.warning("調度器已在運行")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("多平台調度器已啟動")
    
    async def stop(self):
        """停止調度器"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("多平台調度器已停止")
    
    async def submit_search_job(self, query: str, location: str = "", 
                               region: Optional[RegionType] = None,
                               target_platforms: Optional[List[PlatformType]] = None,
                               priority: int = 1,
                               user_id: Optional[str] = None) -> str:
        """提交多平台搜尋任務"""
        
        # 自動檢測地區
        if not region:
            region = self.region_mapper.detect_region(query, location)
        
        # 自動選擇平台
        if not target_platforms:
            target_platforms = self.region_mapper.get_platforms_for_region(region)
        
        # 創建多平台任務
        job_id = str(uuid.uuid4())
        job = MultiPlatformJob(
            job_id=job_id,
            original_query=query,
            location=location,
            region=region,
            target_platforms=target_platforms,
            priority=priority,
            user_id=user_id
        )
        
        # 註冊任務
        await self.task_tracker.register_job(job)
        
        # 加入待處理隊列
        await self.pending_jobs.put(job)
        
        self.logger.info(f"提交多平台搜尋任務: {job_id}, 查詢: {query}, 地區: {region.value}, 平台: {[p.value for p in target_platforms]}")
        
        return job_id
    
    async def _scheduler_loop(self):
        """調度器主循環"""
        while self.running:
            try:
                # 獲取待處理任務
                job = await asyncio.wait_for(self.pending_jobs.get(), timeout=1.0)
                
                # 為每個平台創建異步任務
                platform_tasks = []
                for platform in job.target_platforms:
                    task = asyncio.create_task(
                        self._execute_platform_search(job, platform)
                    )
                    platform_tasks.append(task)
                
                # 不等待完成，讓任務異步執行
                self.logger.info(f"為任務 {job.job_id} 啟動 {len(platform_tasks)} 個平台搜尋")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"調度器循環錯誤: {e}")
    
    async def _execute_platform_search(self, job: MultiPlatformJob, platform: PlatformType):
        """執行單個平台搜尋"""
        platform_name = platform.value
        worker_id = f"{platform_name}_{uuid.uuid4().hex[:8]}"
        
        # 獲取平台信號量
        semaphore = self.worker_semaphores[platform_name]
        
        async with semaphore:
            try:
                # 更新狀態為處理中
                await self.task_tracker.update_platform_task_status(
                    job.job_id, platform_name, TaskStatus.PROCESSING
                )
                
                start_time = time.time()
                
                # 執行搜尋
                result = await self._perform_platform_search(platform, job.original_query, job.location)
                
                execution_time = time.time() - start_time
                
                # 更新成功狀態
                await self.task_tracker.update_platform_task_status(
                    job.job_id, platform_name, TaskStatus.COMPLETED,
                    result_data=result,
                    execution_time=execution_time,
                    job_count=len(result.get('jobs', []))
                )
                
                self.logger.info(f"平台搜尋完成: {job.job_id}_{platform_name}, 找到 {len(result.get('jobs', []))} 個職位")
                
            except Exception as e:
                # 更新失敗狀態
                await self.task_tracker.update_platform_task_status(
                    job.job_id, platform_name, TaskStatus.FAILED,
                    error_message=str(e)
                )
                
                self.logger.error(f"平台搜尋失敗: {job.job_id}_{platform_name}, 錯誤: {e}")
    
    async def _perform_platform_search(self, platform: PlatformType, query: str, location: str) -> Dict[str, Any]:
        """執行實際的平台搜尋"""
        
        # 根據平台類型選擇搜尋方法
        if platform in [PlatformType.LINKEDIN, PlatformType.INDEED, PlatformType.GOOGLE]:
            # 使用智能路由器
            result = self.smart_router.search_jobs(
                query=query,
                location=location,
                max_results=25,
                platforms=[platform.value]
            )
            
            return {
                'jobs': [asdict(job) for job in result.jobs],
                'total_jobs': result.total_jobs,
                'execution_time': result.total_execution_time,
                'successful_platforms': result.successful_platforms,
                'failed_platforms': result.failed_platforms
            }
        
        elif platform in [PlatformType.SEEK]:
            # 使用路由管理器
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.route_manager.execute_search(
                    user_query=query,
                    location=location,
                    forced_site="seek"
                )
            )
            
            return {
                'jobs': result.combined_jobs_data or [],
                'total_jobs': result.total_jobs,
                'execution_time': result.total_execution_time,
                'successful_agents': [agent.value for agent in result.successful_agents],
                'failed_agents': [agent.value for agent in result.failed_agents]
            }
        
        elif platform in [PlatformType.TW104, PlatformType.TW1111]:
            # 台灣平台搜尋（需要實現具體邏輯）
            await asyncio.sleep(2)  # 模擬搜尋時間
            return {
                'jobs': [],
                'total_jobs': 0,
                'execution_time': 2.0,
                'message': f'{platform.value} 搜尋功能待實現'
            }
        
        else:
            raise ValueError(f"不支援的平台: {platform.value}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        return self.task_tracker.get_job_status(job_id)
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """獲取調度器狀態"""
        active_summary = self.task_tracker.get_active_jobs_summary()
        
        platform_worker_status = {}
        for platform, semaphore in self.worker_semaphores.items():
            capability = self.region_mapper.get_platform_capability(PlatformType(platform))
            max_workers = capability.max_concurrent_tasks if capability else self.max_workers_per_platform
            available_workers = semaphore._value
            
            platform_worker_status[platform] = {
                'max_workers': max_workers,
                'available_workers': available_workers,
                'active_workers': max_workers - available_workers
            }
        
        return {
            'running': self.running,
            'pending_jobs': self.pending_jobs.qsize(),
            'active_jobs_summary': active_summary,
            'platform_worker_status': platform_worker_status
        }


# 全局調度器實例
multi_platform_scheduler = MultiPlatformScheduler()


if __name__ == "__main__":
    async def main():
        """測試多平台調度器"""
        scheduler = MultiPlatformScheduler()
        await scheduler.initialize()
        await scheduler.start()
        
        try:
            # 測試美國地區搜尋
            job_id1 = await scheduler.submit_search_job(
                query="python developer",
                location="San Francisco",
                priority=1
            )
            print(f"提交美國搜尋任務: {job_id1}")
            
            # 測試台灣地區搜尋
            job_id2 = await scheduler.submit_search_job(
                query="軟體工程師",
                location="台北",
                priority=1
            )
            print(f"提交台灣搜尋任務: {job_id2}")
            
            # 等待一段時間讓任務執行
            await asyncio.sleep(10)
            
            # 檢查任務狀態
            status1 = scheduler.get_job_status(job_id1)
            status2 = scheduler.get_job_status(job_id2)
            
            print(f"任務1狀態: {status1}")
            print(f"任務2狀態: {status2}")
            
            # 檢查調度器狀態
            scheduler_status = scheduler.get_scheduler_status()
            print(f"調度器狀態: {scheduler_status}")
            
        finally:
            await scheduler.stop()
    
    asyncio.run(main())