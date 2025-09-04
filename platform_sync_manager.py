#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台狀態同步管理器
負責多平台任務的狀態同步、錯誤處理和數據完整性檢查

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
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import aiofiles
import aioredis
from concurrent.futures import ThreadPoolExecutor

# 導入多平台調度器組件
from multi_platform_scheduler import (
    MultiPlatformJob, PlatformTask, TaskStatus, PlatformType, RegionType,
    TaskTracker
)
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


class SyncEventType(Enum):
    """同步事件類型"""
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_CANCELLED = "task_cancelled"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    SYNC_ERROR = "sync_error"


class RetryStrategy(Enum):
    """重試策略"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    NO_RETRY = "no_retry"


@dataclass
class SyncEvent:
    """同步事件"""
    event_id: str
    event_type: SyncEventType
    job_id: str
    platform: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "platform_sync_manager"
    processed: bool = False
    retry_count: int = 0


@dataclass
class RetryConfig:
    """重試配置"""
    strategy: RetryStrategy
    max_retries: int
    base_delay: float
    max_delay: float
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class PlatformHealthStatus:
    """平台健康狀態"""
    platform: PlatformType
    is_healthy: bool
    last_success_time: Optional[datetime]
    last_failure_time: Optional[datetime]
    consecutive_failures: int
    average_response_time: float
    success_rate: float
    current_load: int
    max_capacity: int
    error_messages: List[str] = field(default_factory=list)


class PlatformHealthMonitor:
    """平台健康監控器"""
    
    def __init__(self, health_check_interval: int = 30):
        """初始化健康監控器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.health_check_interval = health_check_interval
        self.platform_health: Dict[str, PlatformHealthStatus] = {}
        self.monitoring_task = None
        self.running = False
        
        # 初始化平台健康狀態
        for platform in PlatformType:
            self.platform_health[platform.value] = PlatformHealthStatus(
                platform=platform,
                is_healthy=True,
                last_success_time=None,
                last_failure_time=None,
                consecutive_failures=0,
                average_response_time=0.0,
                success_rate=1.0,
                current_load=0,
                max_capacity=10
            )
    
    async def start_monitoring(self):
        """開始健康監控"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("平台健康監控已啟動")
    
    async def stop_monitoring(self):
        """停止健康監控"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("平台健康監控已停止")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.running:
            try:
                await self._check_all_platforms_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"健康監控錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_platforms_health(self):
        """檢查所有平台健康狀態"""
        for platform_name, health_status in self.platform_health.items():
            try:
                # 執行健康檢查（這裡可以實現具體的健康檢查邏輯）
                is_healthy = await self._perform_health_check(platform_name)
                
                if is_healthy:
                    health_status.last_success_time = datetime.now()
                    health_status.consecutive_failures = 0
                    if not health_status.is_healthy:
                        self.logger.info(f"平台 {platform_name} 恢復健康")
                        health_status.is_healthy = True
                else:
                    health_status.last_failure_time = datetime.now()
                    health_status.consecutive_failures += 1
                    if health_status.consecutive_failures >= 3:
                        health_status.is_healthy = False
                        self.logger.warning(f"平台 {platform_name} 標記為不健康")
                
            except Exception as e:
                self.logger.error(f"檢查平台 {platform_name} 健康狀態失敗: {e}")
    
    async def _perform_health_check(self, platform_name: str) -> bool:
        """執行平台健康檢查"""
        # 這裡可以實現具體的健康檢查邏輯
        # 例如：發送測試請求、檢查響應時間等
        await asyncio.sleep(0.1)  # 模擬健康檢查
        return True  # 暫時返回健康
    
    def update_platform_metrics(self, platform: str, success: bool, 
                               response_time: float, error_message: str = None):
        """更新平台指標"""
        if platform not in self.platform_health:
            return
        
        health_status = self.platform_health[platform]
        
        # 更新響應時間
        if health_status.average_response_time == 0:
            health_status.average_response_time = response_time
        else:
            health_status.average_response_time = (
                health_status.average_response_time * 0.8 + response_time * 0.2
            )
        
        # 更新成功率（簡化計算）
        if success:
            health_status.success_rate = min(1.0, health_status.success_rate + 0.01)
            health_status.last_success_time = datetime.now()
            health_status.consecutive_failures = 0
        else:
            health_status.success_rate = max(0.0, health_status.success_rate - 0.05)
            health_status.last_failure_time = datetime.now()
            health_status.consecutive_failures += 1
            
            if error_message:
                health_status.error_messages.append(f"{datetime.now().isoformat()}: {error_message}")
                # 只保留最近10條錯誤消息
                health_status.error_messages = health_status.error_messages[-10:]
    
    def get_healthy_platforms(self) -> List[str]:
        """獲取健康的平台列表"""
        return [platform for platform, health in self.platform_health.items() 
                if health.is_healthy]
    
    def get_platform_health(self, platform: str) -> Optional[PlatformHealthStatus]:
        """獲取平台健康狀態"""
        return self.platform_health.get(platform)
    
    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有平台健康狀態"""
        result = {}
        for platform, health in self.platform_health.items():
            result[platform] = {
                "is_healthy": health.is_healthy,
                "last_success_time": health.last_success_time.isoformat() if health.last_success_time else None,
                "last_failure_time": health.last_failure_time.isoformat() if health.last_failure_time else None,
                "consecutive_failures": health.consecutive_failures,
                "average_response_time": health.average_response_time,
                "success_rate": health.success_rate,
                "current_load": health.current_load,
                "max_capacity": health.max_capacity,
                "recent_errors": health.error_messages[-3:]  # 只返回最近3條錯誤
            }
        return result


class RetryManager:
    """重試管理器"""
    
    def __init__(self):
        """初始化重試管理器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.retry_configs: Dict[str, RetryConfig] = {
            "default": RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=3,
                base_delay=1.0,
                max_delay=60.0
            ),
            "critical": RetryConfig(
                strategy=RetryStrategy.IMMEDIATE,
                max_retries=5,
                base_delay=0.5,
                max_delay=30.0
            ),
            "low_priority": RetryConfig(
                strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=2,
                base_delay=5.0,
                max_delay=120.0
            )
        }
        
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        self.retry_task = None
        self.running = False
    
    async def start(self):
        """啟動重試管理器"""
        if self.running:
            return
        
        self.running = True
        self.retry_task = asyncio.create_task(self._retry_loop())
        self.logger.info("重試管理器已啟動")
    
    async def stop(self):
        """停止重試管理器"""
        self.running = False
        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("重試管理器已停止")
    
    async def _retry_loop(self):
        """重試循環"""
        while self.running:
            try:
                # 獲取重試任務
                retry_item = await asyncio.wait_for(self.retry_queue.get(), timeout=1.0)
                await self._process_retry(retry_item)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"重試循環錯誤: {e}")
    
    async def _process_retry(self, retry_item: Dict[str, Any]):
        """處理重試項目"""
        job_id = retry_item['job_id']
        platform = retry_item['platform']
        retry_func = retry_item['retry_func']
        config_name = retry_item.get('config', 'default')
        current_retry = retry_item.get('current_retry', 0)
        
        config = self.retry_configs.get(config_name, self.retry_configs['default'])
        
        if current_retry >= config.max_retries:
            self.logger.error(f"任務 {job_id}_{platform} 重試次數已達上限")
            return
        
        # 計算延遲時間
        delay = self._calculate_delay(config, current_retry)
        
        self.logger.info(f"任務 {job_id}_{platform} 將在 {delay:.2f} 秒後重試 (第 {current_retry + 1} 次)")
        
        await asyncio.sleep(delay)
        
        try:
            # 執行重試
            await retry_func()
            self.logger.info(f"任務 {job_id}_{platform} 重試成功")
        except Exception as e:
            self.logger.error(f"任務 {job_id}_{platform} 重試失敗: {e}")
            
            # 如果還有重試次數，重新加入隊列
            if current_retry + 1 < config.max_retries:
                retry_item['current_retry'] = current_retry + 1
                await self.retry_queue.put(retry_item)
    
    def _calculate_delay(self, config: RetryConfig, retry_count: int) -> float:
        """計算重試延遲時間"""
        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** retry_count)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (retry_count + 1)
        elif config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        else:
            delay = config.base_delay
        
        # 限制最大延遲
        delay = min(delay, config.max_delay)
        
        # 添加抖動
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    async def schedule_retry(self, job_id: str, platform: str, retry_func: Callable,
                           config: str = "default"):
        """安排重試"""
        retry_item = {
            'job_id': job_id,
            'platform': platform,
            'retry_func': retry_func,
            'config': config,
            'current_retry': 0
        }
        
        await self.retry_queue.put(retry_item)
        self.logger.info(f"已安排任務 {job_id}_{platform} 重試")


class PlatformSyncManager:
    """平台狀態同步管理器"""
    
    def __init__(self, 
                 redis_url: str = None,
                 sync_interval: int = 5,
                 health_check_interval: int = 30):
        """初始化同步管理器"""
        self.logger = get_enhanced_logger(__name__, LogCategory.SYSTEM)
        self.redis_url = redis_url
        self.redis_client = None
        self.sync_interval = sync_interval
        
        # 初始化組件
        self.task_tracker = TaskTracker(redis_url)
        self.health_monitor = PlatformHealthMonitor(health_check_interval)
        self.retry_manager = RetryManager()
        
        # 事件處理
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: Dict[SyncEventType, List[Callable]] = {}
        self.sync_callbacks: List[Callable] = []
        
        # 同步狀態
        self.sync_task = None
        self.event_processor_task = None
        self.running = False
        
        # 註冊默認事件處理器
        self._register_default_handlers()
    
    async def initialize(self):
        """初始化同步管理器"""
        # 初始化Redis連接
        if self.redis_url:
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.logger.info("Redis連接成功")
            except Exception as e:
                self.logger.error(f"Redis連接失敗: {e}")
                self.redis_client = None
        
        # 初始化組件
        await self.task_tracker.initialize()
        await self.health_monitor.start_monitoring()
        await self.retry_manager.start()
        
        self.logger.info("平台同步管理器初始化完成")
    
    async def start(self):
        """啟動同步管理器"""
        if self.running:
            return
        
        self.running = True
        self.sync_task = asyncio.create_task(self._sync_loop())
        self.event_processor_task = asyncio.create_task(self._event_processor_loop())
        
        self.logger.info("平台同步管理器已啟動")
    
    async def stop(self):
        """停止同步管理器"""
        self.running = False
        
        # 停止任務
        for task in [self.sync_task, self.event_processor_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # 停止組件
        await self.health_monitor.stop_monitoring()
        await self.retry_manager.stop()
        
        self.logger.info("平台同步管理器已停止")
    
    def _register_default_handlers(self):
        """註冊默認事件處理器"""
        self.register_event_handler(SyncEventType.TASK_FAILED, self._handle_task_failed)
        self.register_event_handler(SyncEventType.TASK_COMPLETED, self._handle_task_completed)
        self.register_event_handler(SyncEventType.JOB_COMPLETED, self._handle_job_completed)
    
    def register_event_handler(self, event_type: SyncEventType, handler: Callable):
        """註冊事件處理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def register_sync_callback(self, callback: Callable):
        """註冊同步回調"""
        self.sync_callbacks.append(callback)
    
    async def emit_event(self, event: SyncEvent):
        """發送同步事件"""
        await self.event_queue.put(event)
        
        # 保存到Redis
        if self.redis_client:
            await self.redis_client.lpush(
                "sync_events",
                json.dumps(asdict(event), default=str)
            )
            # 只保留最近1000個事件
            await self.redis_client.ltrim("sync_events", 0, 999)
    
    async def _sync_loop(self):
        """同步循環"""
        while self.running:
            try:
                await self._perform_sync()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                self.logger.error(f"同步循環錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _event_processor_loop(self):
        """事件處理循環"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"事件處理錯誤: {e}")
    
    async def _perform_sync(self):
        """執行同步操作"""
        # 執行同步回調
        for callback in self.sync_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                self.logger.error(f"同步回調錯誤: {e}")
    
    async def _process_event(self, event: SyncEvent):
        """處理同步事件"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"事件處理器錯誤: {e}")
        
        event.processed = True
    
    async def _handle_task_failed(self, event: SyncEvent):
        """處理任務失敗事件"""
        job_id = event.job_id
        platform = event.platform
        error_message = event.data.get('error_message', '')
        
        # 更新平台健康指標
        self.health_monitor.update_platform_metrics(
            platform, False, 0, error_message
        )
        
        # 檢查是否需要重試
        retry_count = event.data.get('retry_count', 0)
        if retry_count < 3:  # 最多重試3次
            # 創建重試函數
            async def retry_func():
                # 這裡應該調用實際的重試邏輯
                self.logger.info(f"重試任務 {job_id}_{platform}")
            
            await self.retry_manager.schedule_retry(
                job_id, platform, retry_func, "default"
            )
    
    async def _handle_task_completed(self, event: SyncEvent):
        """處理任務完成事件"""
        platform = event.platform
        execution_time = event.data.get('execution_time', 0)
        
        # 更新平台健康指標
        self.health_monitor.update_platform_metrics(
            platform, True, execution_time
        )
    
    async def _handle_job_completed(self, event: SyncEvent):
        """處理任務完成事件"""
        job_id = event.job_id
        total_jobs = event.data.get('total_jobs', 0)
        successful_platforms = event.data.get('successful_platforms', [])
        failed_platforms = event.data.get('failed_platforms', [])
        
        self.logger.info(f"多平台任務完成: {job_id}, 總職位: {total_jobs}, 成功平台: {successful_platforms}, 失敗平台: {failed_platforms}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        return {
            'running': self.running,
            'event_queue_size': self.event_queue.qsize(),
            'platform_health': self.health_monitor.get_all_health_status(),
            'healthy_platforms': self.health_monitor.get_healthy_platforms(),
            'retry_queue_size': self.retry_manager.retry_queue.qsize()
        }


# 全局同步管理器實例
platform_sync_manager = PlatformSyncManager()


if __name__ == "__main__":
    async def main():
        """測試平台同步管理器"""
        sync_manager = PlatformSyncManager()
        await sync_manager.initialize()
        await sync_manager.start()
        
        try:
            # 模擬一些同步事件
            await sync_manager.emit_event(SyncEvent(
                event_id=str(uuid.uuid4()),
                event_type=SyncEventType.TASK_CREATED,
                job_id="test_job_1",
                platform="linkedin",
                data={"query": "python developer", "location": "San Francisco"}
            ))
            
            await sync_manager.emit_event(SyncEvent(
                event_id=str(uuid.uuid4()),
                event_type=SyncEventType.TASK_FAILED,
                job_id="test_job_1",
                platform="linkedin",
                data={"error_message": "連接超時", "retry_count": 0}
            ))
            
            # 等待一段時間讓事件處理
            await asyncio.sleep(5)
            
            # 檢查同步狀態
            status = sync_manager.get_sync_status()
            print(f"同步狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
        finally:
            await sync_manager.stop()
    
    asyncio.run(main())