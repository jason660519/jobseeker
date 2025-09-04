#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務追蹤數據模型
定義用於持久化存儲任務狀態和追蹤信息的數據模型

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

try:
    from sqlalchemy import (
        create_engine, Column, String, Integer, Float, DateTime, 
        Text, Boolean, JSON, ForeignKey, Index, UniqueConstraint
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, Session
    from sqlalchemy.dialects.postgresql import UUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("SQLAlchemy not available, using in-memory storage")


class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class PlatformStatus(Enum):
    """平台狀態枚舉"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """任務優先級枚舉"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class TaskMetrics:
    """任務執行指標"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_duration: float = 0.0
    queue_wait_time: float = 0.0
    retry_count: int = 0
    error_count: int = 0
    success_rate: float = 0.0
    throughput: float = 0.0  # 每秒處理的項目數
    memory_usage: float = 0.0  # MB
    cpu_usage: float = 0.0  # 百分比


@dataclass
class PlatformTaskResult:
    """平台任務結果"""
    platform: str
    status: TaskStatus
    job_count: int = 0
    success_count: int = 0
    error_count: int = 0
    execution_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    results_data: Optional[Dict[str, Any]] = None
    metrics: Optional[TaskMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class MultiPlatformJob(Base):
        """多平台任務主表"""
        __tablename__ = 'multi_platform_jobs'
        
        # 主鍵和基本信息
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String(100), nullable=True, index=True)
        query = Column(Text, nullable=False)
        location = Column(String(200), nullable=True)
        region = Column(String(50), nullable=True, index=True)
        
        # 任務狀態
        overall_status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
        priority = Column(Integer, default=TaskPriority.NORMAL.value, index=True)
        
        # 平台信息
        target_platforms = Column(JSON, nullable=False)  # List[str]
        completed_platforms = Column(JSON, default=list)  # List[str]
        failed_platforms = Column(JSON, default=list)  # List[str]
        
        # 執行統計
        total_jobs_found = Column(Integer, default=0)
        total_execution_time = Column(Float, default=0.0)
        success_rate = Column(Float, default=0.0)
        
        # 時間戳
        created_at = Column(DateTime, default=datetime.utcnow, index=True)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        started_at = Column(DateTime, nullable=True)
        completed_at = Column(DateTime, nullable=True)
        
        # 配置和元數據
        max_results = Column(Integer, default=25)
        timeout_seconds = Column(Integer, default=300)
        retry_attempts = Column(Integer, default=3)
        validation_level = Column(String(20), default="standard")
        metadata = Column(JSON, default=dict)
        
        # 關聯關係
        platform_tasks = relationship("PlatformTask", back_populates="job", cascade="all, delete-orphan")
        tracking_events = relationship("TaskTrackingEvent", back_populates="job", cascade="all, delete-orphan")
        
        # 索引
        __table_args__ = (
            Index('idx_job_status_created', 'overall_status', 'created_at'),
            Index('idx_job_user_region', 'user_id', 'region'),
            Index('idx_job_priority_status', 'priority', 'overall_status'),
        )
        
        def to_dict(self) -> Dict[str, Any]:
            """轉換為字典"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'query': self.query,
                'location': self.location,
                'region': self.region,
                'overall_status': self.overall_status,
                'priority': self.priority,
                'target_platforms': self.target_platforms,
                'completed_platforms': self.completed_platforms,
                'failed_platforms': self.failed_platforms,
                'total_jobs_found': self.total_jobs_found,
                'total_execution_time': self.total_execution_time,
                'success_rate': self.success_rate,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'max_results': self.max_results,
                'timeout_seconds': self.timeout_seconds,
                'retry_attempts': self.retry_attempts,
                'validation_level': self.validation_level,
                'metadata': self.metadata
            }
    
    class PlatformTask(Base):
        """平台任務表"""
        __tablename__ = 'platform_tasks'
        
        # 主鍵和關聯
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        job_id = Column(String(36), ForeignKey('multi_platform_jobs.id'), nullable=False, index=True)
        platform = Column(String(50), nullable=False, index=True)
        
        # 任務狀態
        status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
        retry_count = Column(Integer, default=0)
        
        # 執行結果
        job_count = Column(Integer, default=0)
        success_count = Column(Integer, default=0)
        error_count = Column(Integer, default=0)
        execution_time = Column(Float, default=0.0)
        
        # 錯誤信息
        error_messages = Column(JSON, default=list)  # List[str]
        last_error = Column(Text, nullable=True)
        
        # 結果數據
        results_data = Column(JSON, nullable=True)
        results_file_path = Column(String(500), nullable=True)
        
        # 時間戳
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        started_at = Column(DateTime, nullable=True)
        completed_at = Column(DateTime, nullable=True)
        
        # 性能指標
        queue_wait_time = Column(Float, default=0.0)
        memory_usage = Column(Float, default=0.0)
        cpu_usage = Column(Float, default=0.0)
        
        # 關聯關係
        job = relationship("MultiPlatformJob", back_populates="platform_tasks")
        
        # 索引
        __table_args__ = (
            Index('idx_platform_task_status', 'platform', 'status'),
            Index('idx_platform_task_job', 'job_id', 'platform'),
            UniqueConstraint('job_id', 'platform', name='uq_job_platform'),
        )
        
        def to_dict(self) -> Dict[str, Any]:
            """轉換為字典"""
            return {
                'id': self.id,
                'job_id': self.job_id,
                'platform': self.platform,
                'status': self.status,
                'retry_count': self.retry_count,
                'job_count': self.job_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'execution_time': self.execution_time,
                'error_messages': self.error_messages,
                'last_error': self.last_error,
                'results_data': self.results_data,
                'results_file_path': self.results_file_path,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'queue_wait_time': self.queue_wait_time,
                'memory_usage': self.memory_usage,
                'cpu_usage': self.cpu_usage
            }
    
    class TaskTrackingEvent(Base):
        """任務追蹤事件表"""
        __tablename__ = 'task_tracking_events'
        
        # 主鍵和關聯
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        job_id = Column(String(36), ForeignKey('multi_platform_jobs.id'), nullable=False, index=True)
        platform = Column(String(50), nullable=True, index=True)
        
        # 事件信息
        event_type = Column(String(50), nullable=False, index=True)
        event_data = Column(JSON, nullable=True)
        message = Column(Text, nullable=True)
        
        # 狀態變更
        old_status = Column(String(20), nullable=True)
        new_status = Column(String(20), nullable=True)
        
        # 時間戳
        created_at = Column(DateTime, default=datetime.utcnow, index=True)
        
        # 關聯關係
        job = relationship("MultiPlatformJob", back_populates="tracking_events")
        
        # 索引
        __table_args__ = (
            Index('idx_event_job_type', 'job_id', 'event_type'),
            Index('idx_event_platform_type', 'platform', 'event_type'),
            Index('idx_event_created', 'created_at'),
        )
        
        def to_dict(self) -> Dict[str, Any]:
            """轉換為字典"""
            return {
                'id': self.id,
                'job_id': self.job_id,
                'platform': self.platform,
                'event_type': self.event_type,
                'event_data': self.event_data,
                'message': self.message,
                'old_status': self.old_status,
                'new_status': self.new_status,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    class PlatformHealthStatus(Base):
        """平台健康狀態表"""
        __tablename__ = 'platform_health_status'
        
        # 主鍵
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        platform = Column(String(50), nullable=False, unique=True, index=True)
        
        # 健康狀態
        status = Column(String(20), nullable=False, default=PlatformStatus.IDLE.value)
        is_healthy = Column(Boolean, default=True, index=True)
        
        # 性能指標
        success_rate = Column(Float, default=1.0)
        average_response_time = Column(Float, default=0.0)
        current_load = Column(Integer, default=0)
        max_capacity = Column(Integer, default=10)
        
        # 統計信息
        total_requests = Column(Integer, default=0)
        successful_requests = Column(Integer, default=0)
        failed_requests = Column(Integer, default=0)
        
        # 時間戳
        last_success_time = Column(DateTime, nullable=True)
        last_failure_time = Column(DateTime, nullable=True)
        last_health_check = Column(DateTime, default=datetime.utcnow)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # 配置
        health_check_interval = Column(Integer, default=60)  # 秒
        failure_threshold = Column(Integer, default=5)
        recovery_time = Column(Integer, default=300)  # 秒
        
        def to_dict(self) -> Dict[str, Any]:
            """轉換為字典"""
            return {
                'id': self.id,
                'platform': self.platform,
                'status': self.status,
                'is_healthy': self.is_healthy,
                'success_rate': self.success_rate,
                'average_response_time': self.average_response_time,
                'current_load': self.current_load,
                'max_capacity': self.max_capacity,
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'health_check_interval': self.health_check_interval,
                'failure_threshold': self.failure_threshold,
                'recovery_time': self.recovery_time
            }

else:
    # 如果SQLAlchemy不可用，使用簡單的數據類
    @dataclass
    class MultiPlatformJob:
        """多平台任務（內存版本）"""
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        user_id: Optional[str] = None
        query: str = ""
        location: Optional[str] = None
        region: Optional[str] = None
        overall_status: str = TaskStatus.PENDING.value
        priority: int = TaskPriority.NORMAL.value
        target_platforms: List[str] = field(default_factory=list)
        completed_platforms: List[str] = field(default_factory=list)
        failed_platforms: List[str] = field(default_factory=list)
        total_jobs_found: int = 0
        total_execution_time: float = 0.0
        success_rate: float = 0.0
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        started_at: Optional[datetime] = None
        completed_at: Optional[datetime] = None
        max_results: int = 25
        timeout_seconds: int = 300
        retry_attempts: int = 3
        validation_level: str = "standard"
        metadata: Dict[str, Any] = field(default_factory=dict)
        
        def to_dict(self) -> Dict[str, Any]:
            """轉換為字典"""
            return asdict(self)


class TaskTrackingDatabase:
    """任務追蹤數據庫管理器"""
    
    def __init__(self, database_url: str = None):
        """初始化數據庫管理器"""
        self.database_url = database_url or "sqlite:///task_tracking.db"
        self.engine = None
        self.SessionLocal = None
        self.initialized = False
        
        if SQLALCHEMY_AVAILABLE:
            self._setup_database()
        else:
            # 使用內存存儲
            self.jobs: Dict[str, MultiPlatformJob] = {}
            self.platform_tasks: Dict[str, List[Dict]] = {}
            self.tracking_events: List[Dict] = []
            self.platform_health: Dict[str, Dict] = {}
    
    def _setup_database(self):
        """設置數據庫連接"""
        if not SQLALCHEMY_AVAILABLE:
            return
        
        try:
            self.engine = create_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 創建表
            Base.metadata.create_all(bind=self.engine)
            
            # 創建會話工廠
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.initialized = True
            
        except Exception as e:
            print(f"數據庫初始化失敗: {e}")
            # 回退到內存存儲
            self.jobs = {}
            self.platform_tasks = {}
            self.tracking_events = []
            self.platform_health = {}
    
    def get_session(self) -> Optional[Session]:
        """獲取數據庫會話"""
        if self.SessionLocal:
            return self.SessionLocal()
        return None
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """創建新任務"""
        if SQLALCHEMY_AVAILABLE and self.initialized:
            return self._create_job_db(job_data)
        else:
            return self._create_job_memory(job_data)
    
    def _create_job_db(self, job_data: Dict[str, Any]) -> str:
        """在數據庫中創建任務"""
        session = self.get_session()
        if not session:
            return self._create_job_memory(job_data)
        
        try:
            job = MultiPlatformJob(**job_data)
            session.add(job)
            session.commit()
            return job.id
        except Exception as e:
            session.rollback()
            print(f"創建任務失敗: {e}")
            return ""
        finally:
            session.close()
    
    def _create_job_memory(self, job_data: Dict[str, Any]) -> str:
        """在內存中創建任務"""
        job = MultiPlatformJob(**job_data)
        self.jobs[job.id] = job
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務信息"""
        if SQLALCHEMY_AVAILABLE and self.initialized:
            return self._get_job_db(job_id)
        else:
            return self._get_job_memory(job_id)
    
    def _get_job_db(self, job_id: str) -> Optional[Dict[str, Any]]:
        """從數據庫獲取任務"""
        session = self.get_session()
        if not session:
            return self._get_job_memory(job_id)
        
        try:
            job = session.query(MultiPlatformJob).filter_by(id=job_id).first()
            return job.to_dict() if job else None
        except Exception as e:
            print(f"獲取任務失敗: {e}")
            return None
        finally:
            session.close()
    
    def _get_job_memory(self, job_id: str) -> Optional[Dict[str, Any]]:
        """從內存獲取任務"""
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None
    
    def update_job_status(self, job_id: str, status: TaskStatus, **kwargs) -> bool:
        """更新任務狀態"""
        if SQLALCHEMY_AVAILABLE and self.initialized:
            return self._update_job_status_db(job_id, status, **kwargs)
        else:
            return self._update_job_status_memory(job_id, status, **kwargs)
    
    def _update_job_status_db(self, job_id: str, status: TaskStatus, **kwargs) -> bool:
        """在數據庫中更新任務狀態"""
        session = self.get_session()
        if not session:
            return self._update_job_status_memory(job_id, status, **kwargs)
        
        try:
            job = session.query(MultiPlatformJob).filter_by(id=job_id).first()
            if job:
                job.overall_status = status.value
                job.updated_at = datetime.utcnow()
                
                # 更新其他字段
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"更新任務狀態失敗: {e}")
            return False
        finally:
            session.close()
    
    def _update_job_status_memory(self, job_id: str, status: TaskStatus, **kwargs) -> bool:
        """在內存中更新任務狀態"""
        job = self.jobs.get(job_id)
        if job:
            job.overall_status = status.value
            job.updated_at = datetime.now()
            
            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            return True
        return False
    
    def add_tracking_event(self, job_id: str, event_type: str, **kwargs) -> bool:
        """添加追蹤事件"""
        event_data = {
            'job_id': job_id,
            'event_type': event_type,
            'created_at': datetime.now(),
            **kwargs
        }
        
        if SQLALCHEMY_AVAILABLE and self.initialized:
            return self._add_tracking_event_db(event_data)
        else:
            return self._add_tracking_event_memory(event_data)
    
    def _add_tracking_event_db(self, event_data: Dict[str, Any]) -> bool:
        """在數據庫中添加追蹤事件"""
        session = self.get_session()
        if not session:
            return self._add_tracking_event_memory(event_data)
        
        try:
            event = TaskTrackingEvent(**event_data)
            session.add(event)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"添加追蹤事件失敗: {e}")
            return False
        finally:
            session.close()
    
    def _add_tracking_event_memory(self, event_data: Dict[str, Any]) -> bool:
        """在內存中添加追蹤事件"""
        event_data['id'] = str(uuid.uuid4())
        self.tracking_events.append(event_data)
        return True
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """獲取任務統計信息"""
        if SQLALCHEMY_AVAILABLE and self.initialized:
            return self._get_job_statistics_db()
        else:
            return self._get_job_statistics_memory()
    
    def _get_job_statistics_db(self) -> Dict[str, Any]:
        """從數據庫獲取任務統計"""
        session = self.get_session()
        if not session:
            return self._get_job_statistics_memory()
        
        try:
            total_jobs = session.query(MultiPlatformJob).count()
            completed_jobs = session.query(MultiPlatformJob).filter_by(overall_status=TaskStatus.COMPLETED.value).count()
            failed_jobs = session.query(MultiPlatformJob).filter_by(overall_status=TaskStatus.FAILED.value).count()
            pending_jobs = session.query(MultiPlatformJob).filter_by(overall_status=TaskStatus.PENDING.value).count()
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'pending_jobs': pending_jobs,
                'success_rate': completed_jobs / total_jobs if total_jobs > 0 else 0
            }
        except Exception as e:
            print(f"獲取統計信息失敗: {e}")
            return {}
        finally:
            session.close()
    
    def _get_job_statistics_memory(self) -> Dict[str, Any]:
        """從內存獲取任務統計"""
        total_jobs = len(self.jobs)
        completed_jobs = sum(1 for job in self.jobs.values() if job.overall_status == TaskStatus.COMPLETED.value)
        failed_jobs = sum(1 for job in self.jobs.values() if job.overall_status == TaskStatus.FAILED.value)
        pending_jobs = sum(1 for job in self.jobs.values() if job.overall_status == TaskStatus.PENDING.value)
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'pending_jobs': pending_jobs,
            'success_rate': completed_jobs / total_jobs if total_jobs > 0 else 0
        }


# 全局數據庫實例
task_db = TaskTrackingDatabase()


def get_task_database() -> TaskTrackingDatabase:
    """獲取任務數據庫實例"""
    return task_db


if __name__ == "__main__":
    # 測試數據庫功能
    db = TaskTrackingDatabase()
    
    # 創建測試任務
    job_data = {
        'query': 'test job',
        'location': 'test location',
        'region': 'us',
        'target_platforms': ['linkedin', 'indeed']
    }
    
    job_id = db.create_job(job_data)
    print(f"創建任務: {job_id}")
    
    # 獲取任務
    job = db.get_job(job_id)
    print(f"任務信息: {job}")
    
    # 更新狀態
    db.update_job_status(job_id, TaskStatus.PROCESSING)
    
    # 添加事件
    db.add_tracking_event(job_id, 'job_started', platform='linkedin')
    
    # 獲取統計
    stats = db.get_job_statistics()
    print(f"統計信息: {stats}")