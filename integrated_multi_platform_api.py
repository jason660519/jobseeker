#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合多平台智能路由API
提供統一的多平台異步搜尋接口，整合任務分配、狀態同步和數據完整性檢查

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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 導入自定義組件
from multi_platform_scheduler import (
    MultiPlatformScheduler, PlatformType, RegionType, TaskStatus,
    multi_platform_scheduler
)
from platform_sync_manager import (
    PlatformSyncManager, SyncEvent, SyncEventType,
    platform_sync_manager
)
from data_integrity_manager import (
    DataIntegrityManager, ValidationLevel,
    data_integrity_manager
)
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


# Pydantic模型定義
class SearchRequest(BaseModel):
    """搜尋請求模型"""
    query: str = Field(..., description="搜尋查詢")
    location: str = Field("", description="地點")
    region: Optional[str] = Field(None, description="地區 (us, taiwan, australia, global)")
    platforms: Optional[List[str]] = Field(None, description="指定平台列表")
    max_results: int = Field(25, description="每個平台最大結果數")
    priority: int = Field(1, description="任務優先級 (1-5)")
    validation_level: str = Field("standard", description="驗證級別 (basic, standard, strict, comprehensive)")
    user_id: Optional[str] = Field(None, description="用戶ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外元數據")


class JobStatusResponse(BaseModel):
    """任務狀態響應模型"""
    job_id: str
    status: str
    created_at: str
    query: str
    location: str
    region: str
    target_platforms: List[str]
    platform_status: Dict[str, Any]
    integrity_status: Optional[Dict[str, Any]] = None
    total_jobs: int = 0
    execution_time: float = 0.0


class SearchResponse(BaseModel):
    """搜尋響應模型"""
    job_id: str
    message: str
    estimated_completion_time: int
    target_platforms: List[str]
    region: str


class PlatformHealthResponse(BaseModel):
    """平台健康狀態響應模型"""
    platform: str
    is_healthy: bool
    success_rate: float
    average_response_time: float
    current_load: int
    max_capacity: int
    last_success_time: Optional[str]
    last_failure_time: Optional[str]


class SystemStatusResponse(BaseModel):
    """系統狀態響應模型"""
    scheduler_running: bool
    sync_manager_running: bool
    pending_jobs: int
    active_jobs: int
    completed_jobs: int
    platform_health: Dict[str, Any]
    integrity_summary: Dict[str, Any]


class IntegratedMultiPlatformAPI:
    """整合多平台API"""
    
    def __init__(self, 
                 redis_url: str = None,
                 max_concurrent_jobs: int = 20,
                 enable_auto_retry: bool = True):
        """初始化API"""
        self.logger = get_enhanced_logger(__name__, LogCategory.API)
        self.redis_url = redis_url
        self.max_concurrent_jobs = max_concurrent_jobs
        self.enable_auto_retry = enable_auto_retry
        
        # 初始化組件
        self.scheduler = MultiPlatformScheduler(
            max_concurrent_jobs=max_concurrent_jobs,
            redis_url=redis_url
        )
        self.sync_manager = PlatformSyncManager(
            redis_url=redis_url
        )
        self.integrity_manager = DataIntegrityManager(
            redis_url=redis_url
        )
        
        # API狀態
        self.initialized = False
        self.running = False
        
        # 創建FastAPI應用
        self.app = FastAPI(
            title="多平台智能路由API",
            description="支援多個人力銀行平台的異步搜尋和智能路由",
            version="1.0.0"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 註冊路由
        self._register_routes()
        
        # 註冊事件處理器
        self._register_event_handlers()
    
    async def initialize(self):
        """初始化所有組件"""
        if self.initialized:
            return
        
        try:
            # 初始化各組件
            await self.scheduler.initialize()
            await self.sync_manager.initialize()
            await self.integrity_manager.initialize()
            
            self.initialized = True
            self.logger.info("多平台API初始化完成")
            
        except Exception as e:
            self.logger.error(f"API初始化失敗: {e}")
            raise
    
    async def start(self):
        """啟動API服務"""
        if not self.initialized:
            await self.initialize()
        
        if self.running:
            return
        
        try:
            # 啟動各組件
            await self.scheduler.start()
            await self.sync_manager.start()
            
            self.running = True
            self.logger.info("多平台API服務已啟動")
            
        except Exception as e:
            self.logger.error(f"API啟動失敗: {e}")
            raise
    
    async def stop(self):
        """停止API服務"""
        if not self.running:
            return
        
        try:
            # 停止各組件
            await self.scheduler.stop()
            await self.sync_manager.stop()
            
            self.running = False
            self.logger.info("多平台API服務已停止")
            
        except Exception as e:
            self.logger.error(f"API停止失敗: {e}")
    
    def _register_routes(self):
        """註冊API路由"""
        
        @self.app.post("/search", response_model=SearchResponse)
        async def submit_search(request: SearchRequest, background_tasks: BackgroundTasks):
            """提交多平台搜尋任務"""
            try:
                # 驗證請求
                if not request.query.strip():
                    raise HTTPException(status_code=400, detail="搜尋查詢不能為空")
                
                # 轉換地區
                region = None
                if request.region:
                    try:
                        region = RegionType(request.region.lower())
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"無效的地區: {request.region}")
                
                # 轉換平台
                target_platforms = None
                if request.platforms:
                    try:
                        target_platforms = [PlatformType(p.lower()) for p in request.platforms]
                    except ValueError as e:
                        raise HTTPException(status_code=400, detail=f"無效的平台: {e}")
                
                # 提交任務
                job_id = await self.scheduler.submit_search_job(
                    query=request.query,
                    location=request.location,
                    region=region,
                    target_platforms=target_platforms,
                    priority=request.priority,
                    user_id=request.user_id
                )
                
                # 添加後台任務進行完整性檢查
                background_tasks.add_task(
                    self._monitor_job_completion,
                    job_id,
                    ValidationLevel(request.validation_level)
                )
                
                # 獲取目標平台和地區信息
                job_status = self.scheduler.get_job_status(job_id)
                target_platforms_list = job_status['target_platforms'] if job_status else []
                region_str = job_status['region'] if job_status else 'unknown'
                
                # 估算完成時間（基於平台數量）
                estimated_time = len(target_platforms_list) * 10  # 每個平台約10秒
                
                return SearchResponse(
                    job_id=job_id,
                    message="搜尋任務已提交",
                    estimated_completion_time=estimated_time,
                    target_platforms=target_platforms_list,
                    region=region_str
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"提交搜尋任務失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
        async def get_job_status(job_id: str):
            """獲取任務狀態"""
            try:
                # 獲取基本狀態
                job_status = self.scheduler.get_job_status(job_id)
                if not job_status:
                    raise HTTPException(status_code=404, detail="任務不存在")
                
                # 獲取完整性狀態
                integrity_status = self.integrity_manager.get_integrity_status(job_id)
                
                # 計算總職位數和執行時間
                total_jobs = 0
                total_execution_time = 0.0
                
                for platform_status in job_status['platform_status'].values():
                    total_jobs += platform_status.get('job_count', 0)
                    total_execution_time += platform_status.get('execution_time', 0)
                
                return JobStatusResponse(
                    job_id=job_id,
                    status=job_status['overall_status'],
                    created_at=job_status['created_at'],
                    query=job_status['query'],
                    location=job_status['location'],
                    region=job_status['region'],
                    target_platforms=job_status['target_platforms'],
                    platform_status=job_status['platform_status'],
                    integrity_status=integrity_status,
                    total_jobs=total_jobs,
                    execution_time=total_execution_time
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"獲取任務狀態失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.get("/jobs/{job_id}/results")
        async def get_job_results(job_id: str):
            """獲取任務結果"""
            try:
                # 檢查任務狀態
                job_status = self.scheduler.get_job_status(job_id)
                if not job_status:
                    raise HTTPException(status_code=404, detail="任務不存在")
                
                if job_status['overall_status'] not in ['completed', 'failed']:
                    raise HTTPException(status_code=202, detail="任務尚未完成")
                
                # 這裡應該從存儲中獲取實際結果
                # 暫時返回狀態信息
                return {
                    "job_id": job_id,
                    "status": job_status['overall_status'],
                    "platform_results": job_status['platform_status'],
                    "integrity_check": self.integrity_manager.get_integrity_status(job_id)
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"獲取任務結果失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.get("/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """獲取系統狀態"""
            try:
                scheduler_status = self.scheduler.get_scheduler_status()
                sync_status = self.sync_manager.get_sync_status()
                integrity_summary = self.integrity_manager.get_global_integrity_summary()
                
                return SystemStatusResponse(
                    scheduler_running=scheduler_status['running'],
                    sync_manager_running=sync_status['running'],
                    pending_jobs=scheduler_status['pending_jobs'],
                    active_jobs=scheduler_status['active_jobs_summary']['total_active_jobs'],
                    completed_jobs=scheduler_status['active_jobs_summary']['total_completed_jobs'],
                    platform_health=sync_status['platform_health'],
                    integrity_summary=integrity_summary
                )
                
            except Exception as e:
                self.logger.error(f"獲取系統狀態失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.get("/platforms/health")
        async def get_platform_health():
            """獲取平台健康狀態"""
            try:
                sync_status = self.sync_manager.get_sync_status()
                platform_health = sync_status['platform_health']
                
                health_responses = []
                for platform, health_data in platform_health.items():
                    health_responses.append(PlatformHealthResponse(
                        platform=platform,
                        is_healthy=health_data['is_healthy'],
                        success_rate=health_data['success_rate'],
                        average_response_time=health_data['average_response_time'],
                        current_load=health_data['current_load'],
                        max_capacity=health_data['max_capacity'],
                        last_success_time=health_data['last_success_time'],
                        last_failure_time=health_data['last_failure_time']
                    ))
                
                return health_responses
                
            except Exception as e:
                self.logger.error(f"獲取平台健康狀態失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.post("/jobs/{job_id}/cancel")
        async def cancel_job(job_id: str):
            """取消任務"""
            try:
                # 檢查任務是否存在
                job_status = self.scheduler.get_job_status(job_id)
                if not job_status:
                    raise HTTPException(status_code=404, detail="任務不存在")
                
                if job_status['overall_status'] in ['completed', 'failed', 'cancelled']:
                    raise HTTPException(status_code=400, detail="任務已完成或已取消")
                
                # 發送取消事件
                await self.sync_manager.emit_event(SyncEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SyncEventType.TASK_CANCELLED,
                    job_id=job_id,
                    data={"cancelled_by": "user_request"}
                ))
                
                return {"message": "任務取消請求已提交"}
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"取消任務失敗: {e}")
                raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")
        
        @self.app.get("/health")
        async def health_check():
            """健康檢查"""
            return {
                "status": "healthy" if self.running else "stopped",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
    
    def _register_event_handlers(self):
        """註冊事件處理器"""
        
        async def handle_job_completion(event: SyncEvent):
            """處理任務完成事件"""
            if event.event_type == SyncEventType.JOB_COMPLETED:
                job_id = event.job_id
                
                # 執行完整性檢查
                job_status = self.scheduler.get_job_status(job_id)
                if job_status:
                    # 這裡需要從調度器獲取完整的任務對象
                    # 暫時跳過完整性檢查
                    pass
        
        # 註冊事件處理器
        self.sync_manager.register_event_handler(
            SyncEventType.JOB_COMPLETED,
            handle_job_completion
        )
    
    async def _monitor_job_completion(self, job_id: str, validation_level: ValidationLevel):
        """監控任務完成並執行完整性檢查"""
        max_wait_time = 300  # 最多等待5分鐘
        check_interval = 5   # 每5秒檢查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            job_status = self.scheduler.get_job_status(job_id)
            
            if not job_status:
                self.logger.warning(f"任務 {job_id} 不存在")
                break
            
            if job_status['overall_status'] in ['completed', 'failed']:
                # 任務完成，執行完整性檢查
                try:
                    # 這裡需要獲取完整的任務對象進行完整性檢查
                    # 暫時記錄日誌
                    self.logger.info(f"任務 {job_id} 完成，狀態: {job_status['overall_status']}")
                    
                    # 發送完成事件
                    await self.sync_manager.emit_event(SyncEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=SyncEventType.JOB_COMPLETED,
                        job_id=job_id,
                        data={
                            "status": job_status['overall_status'],
                            "platform_status": job_status['platform_status']
                        }
                    ))
                    
                except Exception as e:
                    self.logger.error(f"完整性檢查失敗: {job_id}, 錯誤: {e}")
                
                break
            
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
        
        if elapsed_time >= max_wait_time:
            self.logger.warning(f"任務 {job_id} 監控超時")


# 全局API實例
integrated_api = IntegratedMultiPlatformAPI()


# FastAPI應用實例
app = integrated_api.app


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    await integrated_api.start()


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    await integrated_api.stop()


if __name__ == "__main__":
    # 運行API服務器
    uvicorn.run(
        "integrated_multi_platform_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )