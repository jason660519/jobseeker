#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務追蹤服務
提供多平台任務的完整追蹤和狀態管理功能

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory cache")

from task_tracking_models import (
    TaskStatus, PlatformStatus, TaskPriority, TaskMetrics,
    PlatformTaskResult, TaskTrackingDatabase, get_task_database
)


class EventType(Enum):
    """事件類型枚舉"""
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    PLATFORM_STARTED = "platform_started"
    PLATFORM_COMPLETED = "platform_completed"
    PLATFORM_FAILED = "platform_failed"
    PLATFORM_RETRY = "platform_retry"
    STATUS_CHANGED = "status_changed"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    PERFORMANCE_UPDATE = "performance_update"


@dataclass
class TaskEvent:
    """任務事件"""
    job_id: str
    event_type: EventType
    platform: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    old_status: Optional[str] = None
    new_status: Optional[str] = None


@dataclass
class TaskProgress:
    """任務進度信息"""
    job_id: str
    total_platforms: int
    completed_platforms: int
    failed_platforms: int
    pending_platforms: int
    processing_platforms: int
    overall_progress: float = 0.0
    estimated_completion_time: Optional[datetime] = None
    platform_statuses: Dict[str, str] = field(default_factory=dict)
    platform_results: Dict[str, PlatformTaskResult] = field(default_factory=dict)


class TaskTrackingService:
    """任務追蹤服務"""
    
    def __init__(self, 
                 database: Optional[TaskTrackingDatabase] = None,
                 redis_url: str = "redis://localhost:6379/0",
                 enable_real_time: bool = True):
        """初始化任務追蹤服務"""
        self.database = database or get_task_database()
        self.redis_url = redis_url
        self.enable_real_time = enable_real_time
        
        # Redis連接
        self.redis_client = None
        if REDIS_AVAILABLE and enable_real_time:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis連接失敗: {e}")
                self.redis_client = None
        
        # 內存緩存
        self.task_cache: Dict[str, Dict[str, Any]] = {}
        self.platform_cache: Dict[str, Dict[str, Any]] = {}
        self.event_listeners: List[Callable[[TaskEvent], None]] = []
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="TaskTracker")
        
        # 統計信息
        self.stats = {
            'total_jobs': 0,
            'active_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_events': 0,
            'start_time': datetime.now()
        }
        
        # 配置
        self.config = {
            'cache_ttl': 3600,  # 緩存過期時間（秒）
            'event_retention': 86400,  # 事件保留時間（秒）
            'health_check_interval': 60,  # 健康檢查間隔（秒）
            'batch_size': 100,  # 批處理大小
            'max_retry_attempts': 3,  # 最大重試次數
            'retry_delay': 5  # 重試延遲（秒）
        }
        
        # 啟動後台任務
        self._start_background_tasks()
        
        logging.info("任務追蹤服務已初始化")
    
    def _start_background_tasks(self):
        """啟動後台任務"""
        # 健康檢查任務
        self.executor.submit(self._health_check_loop)
        
        # 緩存清理任務
        self.executor.submit(self._cache_cleanup_loop)
        
        # 統計更新任務
        self.executor.submit(self._stats_update_loop)
    
    def create_job(self, 
                   query: str,
                   location: str,
                   target_platforms: List[str],
                   user_id: Optional[str] = None,
                   region: Optional[str] = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   **kwargs) -> str:
        """創建新的多平台任務"""
        try:
            # 準備任務數據
            job_data = {
                'user_id': user_id,
                'query': query,
                'location': location,
                'region': region,
                'target_platforms': target_platforms,
                'priority': priority.value,
                'overall_status': TaskStatus.PENDING.value,
                **kwargs
            }
            
            # 創建任務
            job_id = self.database.create_job(job_data)
            
            if job_id:
                # 更新緩存
                self._update_job_cache(job_id, job_data)
                
                # 發送事件
                event = TaskEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_CREATED,
                    message=f"任務已創建: {query}",
                    data={
                        'platforms': target_platforms,
                        'location': location,
                        'priority': priority.value
                    }
                )
                self._emit_event(event)
                
                # 更新統計
                self.stats['total_jobs'] += 1
                
                logging.info(f"任務已創建: {job_id}")
                return job_id
            
            raise Exception("任務創建失敗")
            
        except Exception as e:
            logging.error(f"創建任務失敗: {e}")
            raise
    
    def start_job(self, job_id: str) -> bool:
        """開始執行任務"""
        try:
            # 更新任務狀態
            success = self.database.update_job_status(
                job_id, 
                TaskStatus.PROCESSING,
                started_at=datetime.now()
            )
            
            if success:
                # 更新緩存
                self._update_job_cache(job_id, {
                    'overall_status': TaskStatus.PROCESSING.value,
                    'started_at': datetime.now()
                })
                
                # 發送事件
                event = TaskEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_STARTED,
                    message="任務開始執行",
                    old_status=TaskStatus.PENDING.value,
                    new_status=TaskStatus.PROCESSING.value
                )
                self._emit_event(event)
                
                # 更新統計
                self.stats['active_jobs'] += 1
                
                logging.info(f"任務開始執行: {job_id}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"啟動任務失敗: {e}")
            return False
    
    def complete_job(self, job_id: str, results: Dict[str, Any] = None) -> bool:
        """完成任務"""
        try:
            # 更新任務狀態
            update_data = {
                'completed_at': datetime.now()
            }
            
            if results:
                update_data.update(results)
            
            success = self.database.update_job_status(
                job_id,
                TaskStatus.COMPLETED,
                **update_data
            )
            
            if success:
                # 更新緩存
                self._update_job_cache(job_id, {
                    'overall_status': TaskStatus.COMPLETED.value,
                    'completed_at': datetime.now(),
                    **update_data
                })
                
                # 發送事件
                event = TaskEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_COMPLETED,
                    message="任務執行完成",
                    data=results or {},
                    old_status=TaskStatus.PROCESSING.value,
                    new_status=TaskStatus.COMPLETED.value
                )
                self._emit_event(event)
                
                # 更新統計
                self.stats['active_jobs'] -= 1
                self.stats['completed_jobs'] += 1
                
                logging.info(f"任務執行完成: {job_id}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"完成任務失敗: {e}")
            return False
    
    def fail_job(self, job_id: str, error_message: str, error_data: Dict[str, Any] = None) -> bool:
        """標記任務失敗"""
        try:
            # 更新任務狀態
            update_data = {
                'completed_at': datetime.now(),
                'last_error': error_message
            }
            
            if error_data:
                update_data['metadata'] = error_data
            
            success = self.database.update_job_status(
                job_id,
                TaskStatus.FAILED,
                **update_data
            )
            
            if success:
                # 更新緩存
                self._update_job_cache(job_id, {
                    'overall_status': TaskStatus.FAILED.value,
                    'completed_at': datetime.now(),
                    **update_data
                })
                
                # 發送事件
                event = TaskEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_FAILED,
                    message=f"任務執行失敗: {error_message}",
                    data=error_data or {},
                    old_status=TaskStatus.PROCESSING.value,
                    new_status=TaskStatus.FAILED.value
                )
                self._emit_event(event)
                
                # 更新統計
                self.stats['active_jobs'] -= 1
                self.stats['failed_jobs'] += 1
                
                logging.error(f"任務執行失敗: {job_id} - {error_message}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"標記任務失敗時出錯: {e}")
            return False
    
    def update_platform_status(self, 
                              job_id: str, 
                              platform: str, 
                              status: TaskStatus,
                              result: Optional[PlatformTaskResult] = None) -> bool:
        """更新平台任務狀態"""
        try:
            # 準備平台任務數據
            platform_data = {
                'job_id': job_id,
                'platform': platform,
                'status': status.value,
                'updated_at': datetime.now()
            }
            
            if result:
                platform_data.update({
                    'job_count': result.job_count,
                    'success_count': result.success_count,
                    'error_count': result.error_count,
                    'execution_time': result.execution_time,
                    'error_messages': result.error_messages,
                    'results_data': result.results_data
                })
                
                if status == TaskStatus.COMPLETED:
                    platform_data['completed_at'] = datetime.now()
                elif status == TaskStatus.PROCESSING:
                    platform_data['started_at'] = datetime.now()
            
            # 更新平台緩存
            cache_key = f"{job_id}:{platform}"
            self.platform_cache[cache_key] = platform_data
            
            # 發送平台事件
            if status == TaskStatus.PROCESSING:
                event_type = EventType.PLATFORM_STARTED
                message = f"平台 {platform} 開始處理"
            elif status == TaskStatus.COMPLETED:
                event_type = EventType.PLATFORM_COMPLETED
                message = f"平台 {platform} 處理完成"
            elif status == TaskStatus.FAILED:
                event_type = EventType.PLATFORM_FAILED
                message = f"平台 {platform} 處理失敗"
            else:
                event_type = EventType.STATUS_CHANGED
                message = f"平台 {platform} 狀態變更為 {status.value}"
            
            event = TaskEvent(
                job_id=job_id,
                event_type=event_type,
                platform=platform,
                message=message,
                data=platform_data
            )
            self._emit_event(event)
            
            # 檢查是否需要更新任務整體狀態
            self._check_job_completion(job_id)
            
            logging.info(f"平台狀態已更新: {job_id}:{platform} -> {status.value}")
            return True
            
        except Exception as e:
            logging.error(f"更新平台狀態失敗: {e}")
            return False
    
    def get_job_progress(self, job_id: str) -> Optional[TaskProgress]:
        """獲取任務進度"""
        try:
            # 從緩存或數據庫獲取任務信息
            job_data = self._get_job_from_cache_or_db(job_id)
            if not job_data:
                return None
            
            target_platforms = job_data.get('target_platforms', [])
            total_platforms = len(target_platforms)
            
            # 統計平台狀態
            platform_statuses = {}
            platform_results = {}
            completed_count = 0
            failed_count = 0
            processing_count = 0
            pending_count = 0
            
            for platform in target_platforms:
                cache_key = f"{job_id}:{platform}"
                platform_data = self.platform_cache.get(cache_key, {})
                
                status = platform_data.get('status', TaskStatus.PENDING.value)
                platform_statuses[platform] = status
                
                if status == TaskStatus.COMPLETED.value:
                    completed_count += 1
                elif status == TaskStatus.FAILED.value:
                    failed_count += 1
                elif status == TaskStatus.PROCESSING.value:
                    processing_count += 1
                else:
                    pending_count += 1
                
                # 構建平台結果
                if platform_data:
                    platform_results[platform] = PlatformTaskResult(
                        platform=platform,
                        status=TaskStatus(status),
                        job_count=platform_data.get('job_count', 0),
                        success_count=platform_data.get('success_count', 0),
                        error_count=platform_data.get('error_count', 0),
                        execution_time=platform_data.get('execution_time', 0.0),
                        error_messages=platform_data.get('error_messages', []),
                        results_data=platform_data.get('results_data')
                    )
            
            # 計算進度
            overall_progress = (completed_count + failed_count) / total_platforms if total_platforms > 0 else 0
            
            # 估算完成時間
            estimated_completion_time = None
            if processing_count > 0 and completed_count > 0:
                # 基於已完成任務的平均時間估算
                avg_time = self._calculate_average_execution_time(job_id)
                if avg_time > 0:
                    remaining_time = avg_time * (pending_count + processing_count)
                    estimated_completion_time = datetime.now() + timedelta(seconds=remaining_time)
            
            return TaskProgress(
                job_id=job_id,
                total_platforms=total_platforms,
                completed_platforms=completed_count,
                failed_platforms=failed_count,
                pending_platforms=pending_count,
                processing_platforms=processing_count,
                overall_progress=overall_progress,
                estimated_completion_time=estimated_completion_time,
                platform_statuses=platform_statuses,
                platform_results=platform_results
            )
            
        except Exception as e:
            logging.error(f"獲取任務進度失敗: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        try:
            job_data = self._get_job_from_cache_or_db(job_id)
            if not job_data:
                return None
            
            # 獲取進度信息
            progress = self.get_job_progress(job_id)
            
            return {
                'job_id': job_id,
                'status': job_data.get('overall_status'),
                'query': job_data.get('query'),
                'location': job_data.get('location'),
                'region': job_data.get('region'),
                'target_platforms': job_data.get('target_platforms', []),
                'created_at': job_data.get('created_at'),
                'started_at': job_data.get('started_at'),
                'completed_at': job_data.get('completed_at'),
                'total_jobs_found': job_data.get('total_jobs_found', 0),
                'total_execution_time': job_data.get('total_execution_time', 0.0),
                'success_rate': job_data.get('success_rate', 0.0),
                'progress': progress.__dict__ if progress else None
            }
            
        except Exception as e:
            logging.error(f"獲取任務狀態失敗: {e}")
            return None
    
    def cancel_job(self, job_id: str, reason: str = "用戶取消") -> bool:
        """取消任務"""
        try:
            success = self.database.update_job_status(
                job_id,
                TaskStatus.CANCELLED,
                completed_at=datetime.now(),
                last_error=reason
            )
            
            if success:
                # 更新緩存
                self._update_job_cache(job_id, {
                    'overall_status': TaskStatus.CANCELLED.value,
                    'completed_at': datetime.now()
                })
                
                # 發送事件
                event = TaskEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_CANCELLED,
                    message=f"任務已取消: {reason}",
                    data={'reason': reason}
                )
                self._emit_event(event)
                
                # 更新統計
                self.stats['active_jobs'] -= 1
                
                logging.info(f"任務已取消: {job_id} - {reason}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"取消任務失敗: {e}")
            return False
    
    def add_event_listener(self, listener: Callable[[TaskEvent], None]):
        """添加事件監聽器"""
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[TaskEvent], None]):
        """移除事件監聽器"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        # 從數據庫獲取最新統計
        db_stats = self.database.get_job_statistics()
        
        # 合併統計信息
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            **db_stats,
            'uptime_seconds': uptime.total_seconds(),
            'cache_size': len(self.task_cache),
            'platform_cache_size': len(self.platform_cache),
            'event_listeners': len(self.event_listeners),
            'redis_connected': self.redis_client is not None
        }
    
    def _emit_event(self, event: TaskEvent):
        """發送事件"""
        try:
            # 更新統計
            self.stats['total_events'] += 1
            
            # 存儲到數據庫
            self.database.add_tracking_event(
                job_id=event.job_id,
                event_type=event.event_type.value,
                platform=event.platform,
                message=event.message,
                event_data=event.data,
                old_status=event.old_status,
                new_status=event.new_status
            )
            
            # 發送到Redis（如果可用）
            if self.redis_client:
                try:
                    event_data = {
                        'job_id': event.job_id,
                        'event_type': event.event_type.value,
                        'platform': event.platform,
                        'message': event.message,
                        'data': event.data,
                        'timestamp': event.timestamp.isoformat(),
                        'old_status': event.old_status,
                        'new_status': event.new_status
                    }
                    
                    # 發布到頻道
                    self.redis_client.publish('task_events', json.dumps(event_data))
                    
                    # 存儲到列表（用於歷史查詢）
                    self.redis_client.lpush(f'job_events:{event.job_id}', json.dumps(event_data))
                    self.redis_client.expire(f'job_events:{event.job_id}', self.config['event_retention'])
                    
                except Exception as e:
                    logging.warning(f"Redis事件發送失敗: {e}")
            
            # 通知事件監聽器
            for listener in self.event_listeners:
                try:
                    listener(event)
                except Exception as e:
                    logging.warning(f"事件監聽器執行失敗: {e}")
            
        except Exception as e:
            logging.error(f"發送事件失敗: {e}")
    
    def _update_job_cache(self, job_id: str, data: Dict[str, Any]):
        """更新任務緩存"""
        if job_id not in self.task_cache:
            self.task_cache[job_id] = {}
        
        self.task_cache[job_id].update(data)
        self.task_cache[job_id]['cache_updated_at'] = datetime.now()
        
        # 同步到Redis
        if self.redis_client:
            try:
                self.redis_client.hset(
                    f'job_cache:{job_id}',
                    mapping={k: json.dumps(v, default=str) for k, v in data.items()}
                )
                self.redis_client.expire(f'job_cache:{job_id}', self.config['cache_ttl'])
            except Exception as e:
                logging.warning(f"Redis緩存更新失敗: {e}")
    
    def _get_job_from_cache_or_db(self, job_id: str) -> Optional[Dict[str, Any]]:
        """從緩存或數據庫獲取任務"""
        # 先檢查內存緩存
        if job_id in self.task_cache:
            cache_data = self.task_cache[job_id]
            cache_time = cache_data.get('cache_updated_at')
            if cache_time and (datetime.now() - cache_time).seconds < self.config['cache_ttl']:
                return cache_data
        
        # 檢查Redis緩存
        if self.redis_client:
            try:
                cached_data = self.redis_client.hgetall(f'job_cache:{job_id}')
                if cached_data:
                    # 反序列化數據
                    job_data = {}
                    for k, v in cached_data.items():
                        try:
                            job_data[k] = json.loads(v)
                        except:
                            job_data[k] = v
                    
                    # 更新內存緩存
                    self.task_cache[job_id] = job_data
                    return job_data
            except Exception as e:
                logging.warning(f"Redis緩存讀取失敗: {e}")
        
        # 從數據庫獲取
        job_data = self.database.get_job(job_id)
        if job_data:
            # 更新緩存
            self._update_job_cache(job_id, job_data)
            return job_data
        
        return None
    
    def _check_job_completion(self, job_id: str):
        """檢查任務是否完成"""
        try:
            progress = self.get_job_progress(job_id)
            if not progress:
                return
            
            # 檢查是否所有平台都完成了
            if progress.pending_platforms == 0 and progress.processing_platforms == 0:
                if progress.failed_platforms == 0:
                    # 所有平台都成功
                    self.complete_job(job_id, {
                        'total_jobs_found': sum(r.job_count for r in progress.platform_results.values()),
                        'success_rate': 1.0
                    })
                elif progress.completed_platforms == 0:
                    # 所有平台都失敗
                    self.fail_job(job_id, "所有平台都執行失敗")
                else:
                    # 部分成功
                    success_rate = progress.completed_platforms / progress.total_platforms
                    self.complete_job(job_id, {
                        'total_jobs_found': sum(r.job_count for r in progress.platform_results.values()),
                        'success_rate': success_rate
                    })
        
        except Exception as e:
            logging.error(f"檢查任務完成狀態失敗: {e}")
    
    def _calculate_average_execution_time(self, job_id: str) -> float:
        """計算平均執行時間"""
        try:
            total_time = 0.0
            completed_count = 0
            
            job_data = self._get_job_from_cache_or_db(job_id)
            if not job_data:
                return 0.0
            
            target_platforms = job_data.get('target_platforms', [])
            
            for platform in target_platforms:
                cache_key = f"{job_id}:{platform}"
                platform_data = self.platform_cache.get(cache_key, {})
                
                if platform_data.get('status') == TaskStatus.COMPLETED.value:
                    execution_time = platform_data.get('execution_time', 0.0)
                    if execution_time > 0:
                        total_time += execution_time
                        completed_count += 1
            
            return total_time / completed_count if completed_count > 0 else 0.0
            
        except Exception as e:
            logging.error(f"計算平均執行時間失敗: {e}")
            return 0.0
    
    def _health_check_loop(self):
        """健康檢查循環"""
        while True:
            try:
                time.sleep(self.config['health_check_interval'])
                
                # 檢查數據庫連接
                db_healthy = True
                try:
                    self.database.get_job_statistics()
                except Exception as e:
                    db_healthy = False
                    logging.warning(f"數據庫健康檢查失敗: {e}")
                
                # 檢查Redis連接
                redis_healthy = True
                if self.redis_client:
                    try:
                        self.redis_client.ping()
                    except Exception as e:
                        redis_healthy = False
                        logging.warning(f"Redis健康檢查失敗: {e}")
                
                # 發送健康檢查事件
                health_data = {
                    'database_healthy': db_healthy,
                    'redis_healthy': redis_healthy,
                    'cache_size': len(self.task_cache),
                    'active_jobs': self.stats['active_jobs']
                }
                
                # 這裡可以添加健康檢查邏輯
                
            except Exception as e:
                logging.error(f"健康檢查循環錯誤: {e}")
    
    def _cache_cleanup_loop(self):
        """緩存清理循環"""
        while True:
            try:
                time.sleep(3600)  # 每小時清理一次
                
                current_time = datetime.now()
                expired_keys = []
                
                # 清理過期的任務緩存
                for job_id, cache_data in self.task_cache.items():
                    cache_time = cache_data.get('cache_updated_at')
                    if cache_time and (current_time - cache_time).seconds > self.config['cache_ttl']:
                        expired_keys.append(job_id)
                
                for key in expired_keys:
                    del self.task_cache[key]
                
                # 清理平台緩存
                expired_platform_keys = []
                for cache_key, platform_data in self.platform_cache.items():
                    updated_at = platform_data.get('updated_at')
                    if updated_at and (current_time - updated_at).seconds > self.config['cache_ttl']:
                        expired_platform_keys.append(cache_key)
                
                for key in expired_platform_keys:
                    del self.platform_cache[key]
                
                logging.info(f"緩存清理完成: 清理了 {len(expired_keys)} 個任務緩存和 {len(expired_platform_keys)} 個平台緩存")
                
            except Exception as e:
                logging.error(f"緩存清理循環錯誤: {e}")
    
    def _stats_update_loop(self):
        """統計更新循環"""
        while True:
            try:
                time.sleep(300)  # 每5分鐘更新一次
                
                # 更新活躍任務數
                active_count = 0
                for job_id, cache_data in self.task_cache.items():
                    status = cache_data.get('overall_status')
                    if status in [TaskStatus.PROCESSING.value, TaskStatus.QUEUED.value]:
                        active_count += 1
                
                self.stats['active_jobs'] = active_count
                
            except Exception as e:
                logging.error(f"統計更新循環錯誤: {e}")
    
    def shutdown(self):
        """關閉服務"""
        try:
            logging.info("正在關閉任務追蹤服務...")
            
            # 關閉線程池
            self.executor.shutdown(wait=True)
            
            # 關閉Redis連接
            if self.redis_client:
                self.redis_client.close()
            
            logging.info("任務追蹤服務已關閉")
            
        except Exception as e:
            logging.error(f"關閉服務時出錯: {e}")


# 全局服務實例
task_tracking_service = TaskTrackingService()


def get_task_tracking_service() -> TaskTrackingService:
    """獲取任務追蹤服務實例"""
    return task_tracking_service


if __name__ == "__main__":
    # 測試任務追蹤服務
    import time
    
    service = TaskTrackingService()
    
    # 添加事件監聽器
    def event_listener(event: TaskEvent):
        print(f"事件: {event.event_type.value} - {event.message}")
    
    service.add_event_listener(event_listener)
    
    # 創建測試任務
    job_id = service.create_job(
        query="Python Developer",
        location="台北",
        target_platforms=["linkedin", "indeed", "1111"],
        region="tw"
    )
    
    print(f"創建任務: {job_id}")
    
    # 開始任務
    service.start_job(job_id)
    
    # 模擬平台執行
    time.sleep(1)
    service.update_platform_status(job_id, "linkedin", TaskStatus.PROCESSING)
    
    time.sleep(2)
    result = PlatformTaskResult(
        platform="linkedin",
        status=TaskStatus.COMPLETED,
        job_count=10,
        success_count=10,
        execution_time=2.5
    )
    service.update_platform_status(job_id, "linkedin", TaskStatus.COMPLETED, result)
    
    # 獲取進度
    progress = service.get_job_progress(job_id)
    print(f"任務進度: {progress}")
    
    # 獲取統計
    stats = service.get_statistics()
    print(f"服務統計: {stats}")
    
    # 關閉服務
    service.shutdown()