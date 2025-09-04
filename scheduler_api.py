#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON調度器管理API
提供RESTful接口來管理和監控調度器

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 導入調度器組件
from llm_json_scheduler import (
    LLMJSONScheduler, TaskInfo, TaskPriority, TaskStatus, 
    ProcessingMode, ProcessingResult
)
from jobseeker.enhanced_logging import get_enhanced_logger, LogCategory


# Pydantic模型定義
class TaskCreateRequest(BaseModel):
    """創建任務請求"""
    file_path: str = Field(..., description="JSON檔案路徑")
    task_type: str = Field(..., description="任務類型")
    priority: str = Field(default="normal", description="任務優先級")
    user_id: Optional[str] = Field(None, description="用戶ID")
    user_tier: str = Field(default="free", description="用戶等級")
    metadata: Optional[Dict[str, Any]] = Field(None, description="任務元數據")


class TaskResponse(BaseModel):
    """任務響應"""
    task_id: str
    file_path: str
    task_type: str
    priority: str
    status: str
    created_at: datetime
    user_id: Optional[str] = None
    user_tier: str = "free"
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class SchedulerStatusResponse(BaseModel):
    """調度器狀態響應"""
    scheduler_stats: Dict[str, Any]
    queue_stats: Dict[str, Any]
    worker_stats: Dict[str, Any]
    processing_mode: str
    batch_config: Dict[str, Any]
    task_status_summary: Dict[str, int]


class ProcessingModeRequest(BaseModel):
    """處理模式更改請求"""
    mode: str = Field(..., description="處理模式: realtime, batch, hybrid")


class WorkerConfigRequest(BaseModel):
    """工作線程配置請求"""
    max_workers: int = Field(..., ge=1, le=50, description="最大工作線程數")


class BatchConfigRequest(BaseModel):
    """批量處理配置請求"""
    batch_size: int = Field(..., ge=1, le=100, description="批量大小")
    batch_timeout: int = Field(..., ge=30, le=3600, description="批量超時時間（秒）")


class HealthCheckResponse(BaseModel):
    """健康檢查響應"""
    status: str
    timestamp: datetime
    uptime: float
    version: str
    components: Dict[str, str]


class MetricsResponse(BaseModel):
    """指標響應"""
    timestamp: datetime
    scheduler_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]


# 全局調度器實例
scheduler_instance: Optional[LLMJSONScheduler] = None
app_start_time = time.time()


# FastAPI應用初始化
app = FastAPI(
    title="LLM JSON調度器管理API",
    description="用於管理和監控LLM JSON檔案處理調度器的RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 日誌記錄器
logger = get_enhanced_logger("SchedulerAPI", LogCategory.API)


# 依賴注入
def get_scheduler() -> LLMJSONScheduler:
    """獲取調度器實例"""
    if scheduler_instance is None:
        raise HTTPException(status_code=503, detail="調度器未初始化")
    return scheduler_instance


# 啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global scheduler_instance
    
    logger.info("正在啟動調度器API...")
    
    try:
        # 讀取配置
        config_path = Path("scheduler_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # 創建調度器實例
        scheduler_instance = LLMJSONScheduler(
            watch_directory=config.get("directories", {}).get("watch_directory", "./data/llm_generated/raw"),
            output_directory=config.get("directories", {}).get("output_directory", "./data/llm_generated/processed"),
            max_workers=config.get("processing", {}).get("max_workers", 10),
            processing_mode=ProcessingMode(config.get("processing", {}).get("mode", "hybrid")),
            redis_url=config.get("queue", {}).get("redis_url")
        )
        
        # 啟動調度器
        await scheduler_instance.start()
        
        logger.info("調度器API已成功啟動")
        
    except Exception as e:
        logger.error(f"調度器API啟動失敗: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    global scheduler_instance
    
    logger.info("正在關閉調度器API...")
    
    if scheduler_instance:
        try:
            await scheduler_instance.stop()
            logger.info("調度器已成功關閉")
        except Exception as e:
            logger.error(f"調度器關閉失敗: {e}")
    
    logger.info("調度器API已關閉")


# API路由定義

@app.get("/", summary="API根路徑")
async def root():
    """API根路徑"""
    return {
        "message": "LLM JSON調度器管理API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse, summary="健康檢查")
async def health_check(scheduler: LLMJSONScheduler = Depends(get_scheduler)):
    """健康檢查端點"""
    
    uptime = time.time() - app_start_time
    
    # 檢查各組件狀態
    components = {
        "scheduler": "healthy",
        "file_watcher": "healthy",
        "task_queue": "healthy",
        "worker_pool": "healthy"
    }
    
    try:
        # 檢查調度器狀態
        status = scheduler.get_status()
        
        # 檢查佇列是否響應
        queue_stats = status.get("queue_stats", {})
        if queue_stats.get("current_size", 0) > 1000:
            components["task_queue"] = "warning"
        
        # 檢查工作線程
        worker_stats = status.get("worker_stats", {})
        if worker_stats.get("active_workers", 0) == worker_stats.get("max_workers", 0):
            components["worker_pool"] = "warning"
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        components["scheduler"] = "unhealthy"
    
    overall_status = "healthy"
    if "unhealthy" in components.values():
        overall_status = "unhealthy"
    elif "warning" in components.values():
        overall_status = "warning"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(),
        uptime=uptime,
        version="1.0.0",
        components=components
    )


@app.get("/status", response_model=SchedulerStatusResponse, summary="獲取調度器狀態")
async def get_scheduler_status(scheduler: LLMJSONScheduler = Depends(get_scheduler)):
    """獲取調度器詳細狀態"""
    
    try:
        status = scheduler.get_status()
        return SchedulerStatusResponse(**status)
    except Exception as e:
        logger.error(f"獲取調度器狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@app.get("/metrics", response_model=MetricsResponse, summary="獲取性能指標")
async def get_metrics(scheduler: LLMJSONScheduler = Depends(get_scheduler)):
    """獲取詳細的性能指標"""
    
    try:
        status = scheduler.get_status()
        
        # 系統指標
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
        }
        
        # 性能指標
        scheduler_stats = status.get("scheduler_stats", {})
        performance_metrics = {
            "throughput": scheduler_stats.get("successful_tasks", 0) / max((time.time() - app_start_time) / 3600, 0.01),  # 任務/小時
            "success_rate": scheduler_stats.get("successful_tasks", 0) / max(scheduler_stats.get("total_files_processed", 1), 1),
            "average_processing_time": scheduler_stats.get("average_processing_time", 0),
            "queue_utilization": status.get("queue_stats", {}).get("current_size", 0) / 1000  # 假設最大佇列大小為1000
        }
        
        return MetricsResponse(
            timestamp=datetime.now(),
            scheduler_metrics=scheduler_stats,
            system_metrics=system_metrics,
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標失敗: {str(e)}")


@app.post("/tasks", response_model=TaskResponse, summary="創建新任務")
async def create_task(
    task_request: TaskCreateRequest,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """手動創建新任務"""
    
    try:
        # 驗證檔案是否存在
        file_path = Path(task_request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"檔案不存在: {task_request.file_path}")
        
        # 驗證檔案格式
        if not file_path.suffix.lower() == '.json':
            raise HTTPException(status_code=400, detail="只支持JSON檔案")
        
        # 創建任務信息
        task_info = TaskInfo(
            task_id=f"manual_{task_request.task_type}_{int(time.time())}",
            file_path=task_request.file_path,
            task_type=task_request.task_type,
            priority=TaskPriority(task_request.priority),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            user_id=task_request.user_id,
            user_tier=task_request.user_tier,
            metadata=task_request.metadata or {}
        )
        
        # 添加任務到調度器
        await scheduler.add_task(task_info)
        
        logger.info(f"手動創建任務: {task_info.task_id}")
        
        return TaskResponse(
            task_id=task_info.task_id,
            file_path=task_info.file_path,
            task_type=task_info.task_type,
            priority=task_info.priority.value,
            status=task_info.status.value,
            created_at=task_info.created_at,
            user_id=task_info.user_id,
            user_tier=task_info.user_tier,
            retry_count=task_info.retry_count,
            metadata=task_info.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的參數: {str(e)}")
    except Exception as e:
        logger.error(f"創建任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建任務失敗: {str(e)}")


@app.get("/tasks/{task_id}", response_model=TaskResponse, summary="獲取任務狀態")
async def get_task_status(
    task_id: str,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """獲取特定任務的狀態"""
    
    try:
        task_info = await scheduler.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail=f"任務不存在: {task_id}")
        
        return TaskResponse(
            task_id=task_info.task_id,
            file_path=task_info.file_path,
            task_type=task_info.task_type,
            priority=task_info.priority.value,
            status=task_info.status.value,
            created_at=task_info.created_at,
            user_id=task_info.user_id,
            user_tier=task_info.user_tier,
            retry_count=task_info.retry_count,
            metadata=task_info.metadata
        )
        
    except Exception as e:
        logger.error(f"獲取任務狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務狀態失敗: {str(e)}")


@app.delete("/tasks/{task_id}", summary="取消任務")
async def cancel_task(
    task_id: str,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """取消特定任務"""
    
    try:
        success = await scheduler.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"任務不存在或無法取消: {task_id}")
        
        logger.info(f"任務已取消: {task_id}")
        
        return {"message": f"任務 {task_id} 已成功取消"}
        
    except Exception as e:
        logger.error(f"取消任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")


@app.get("/tasks", summary="獲取任務列表")
async def list_tasks(
    status: Optional[str] = Query(None, description="按狀態過濾"),
    task_type: Optional[str] = Query(None, description="按任務類型過濾"),
    user_id: Optional[str] = Query(None, description="按用戶ID過濾"),
    limit: int = Query(50, ge=1, le=500, description="返回數量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """獲取任務列表（支持過濾和分頁）"""
    
    try:
        # 獲取所有任務
        all_tasks = list(scheduler.task_status.values())
        
        # 應用過濾器
        filtered_tasks = all_tasks
        
        if status:
            try:
                status_enum = TaskStatus(status)
                filtered_tasks = [t for t in filtered_tasks if t.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的狀態: {status}")
        
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t.task_type == task_type]
        
        if user_id:
            filtered_tasks = [t for t in filtered_tasks if t.user_id == user_id]
        
        # 排序（最新的在前）
        filtered_tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        # 分頁
        total_count = len(filtered_tasks)
        paginated_tasks = filtered_tasks[offset:offset + limit]
        
        # 轉換為響應格式
        task_responses = [
            TaskResponse(
                task_id=task.task_id,
                file_path=task.file_path,
                task_type=task.task_type,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                user_id=task.user_id,
                user_tier=task.user_tier,
                retry_count=task.retry_count,
                metadata=task.metadata
            )
            for task in paginated_tasks
        ]
        
        return {
            "tasks": task_responses,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"獲取任務列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")


@app.put("/config/processing-mode", summary="更改處理模式")
async def update_processing_mode(
    mode_request: ProcessingModeRequest,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """更改調度器的處理模式"""
    
    try:
        new_mode = ProcessingMode(mode_request.mode)
        scheduler.processing_mode = new_mode
        
        logger.info(f"處理模式已更改為: {new_mode.value}")
        
        return {"message": f"處理模式已更改為: {new_mode.value}"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"無效的處理模式: {mode_request.mode}")
    except Exception as e:
        logger.error(f"更改處理模式失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更改處理模式失敗: {str(e)}")


@app.put("/config/workers", summary="更改工作線程配置")
async def update_worker_config(
    worker_request: WorkerConfigRequest,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """更改工作線程配置"""
    
    try:
        scheduler.worker_pool.max_workers = worker_request.max_workers
        scheduler.worker_pool.semaphore = asyncio.Semaphore(worker_request.max_workers)
        
        logger.info(f"最大工作線程數已更改為: {worker_request.max_workers}")
        
        return {"message": f"最大工作線程數已更改為: {worker_request.max_workers}"}
        
    except Exception as e:
        logger.error(f"更改工作線程配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更改工作線程配置失敗: {str(e)}")


@app.put("/config/batch", summary="更改批量處理配置")
async def update_batch_config(
    batch_request: BatchConfigRequest,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """更改批量處理配置"""
    
    try:
        scheduler.batch_config['batch_size'] = batch_request.batch_size
        scheduler.batch_config['batch_timeout'] = batch_request.batch_timeout
        
        logger.info(f"批量配置已更新: 大小={batch_request.batch_size}, 超時={batch_request.batch_timeout}秒")
        
        return {
            "message": "批量配置已更新",
            "batch_size": batch_request.batch_size,
            "batch_timeout": batch_request.batch_timeout
        }
        
    except Exception as e:
        logger.error(f"更改批量配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更改批量配置失敗: {str(e)}")


@app.post("/admin/restart", summary="重啟調度器")
async def restart_scheduler(
    background_tasks: BackgroundTasks,
    scheduler: LLMJSONScheduler = Depends(get_scheduler)
):
    """重啟調度器（管理員功能）"""
    
    try:
        logger.info("正在重啟調度器...")
        
        # 在背景任務中執行重啟
        background_tasks.add_task(_restart_scheduler_task, scheduler)
        
        return {"message": "調度器重啟已開始"}
        
    except Exception as e:
        logger.error(f"重啟調度器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"重啟調度器失敗: {str(e)}")


async def _restart_scheduler_task(scheduler: LLMJSONScheduler):
    """重啟調度器的背景任務"""
    
    try:
        # 停止調度器
        await scheduler.stop()
        
        # 等待一段時間
        await asyncio.sleep(2)
        
        # 重新啟動調度器
        await scheduler.start()
        
        logger.info("調度器重啟完成")
        
    except Exception as e:
        logger.error(f"調度器重啟失敗: {e}")


@app.get("/admin/logs", summary="獲取日誌")
async def get_logs(
    lines: int = Query(100, ge=1, le=1000, description="返回的日誌行數"),
    level: Optional[str] = Query(None, description="日誌級別過濾")
):
    """獲取調度器日誌（管理員功能）"""
    
    try:
        log_file = Path("./logs/scheduler.log")
        
        if not log_file.exists():
            return {"logs": [], "message": "日誌檔案不存在"}
        
        # 讀取日誌檔案的最後N行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # 獲取最後N行
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # 如果指定了日誌級別，進行過濾
        if level:
            level_upper = level.upper()
            recent_lines = [line for line in recent_lines if level_upper in line]
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(recent_lines),
            "requested_lines": lines,
            "level_filter": level
        }
        
    except Exception as e:
        logger.error(f"獲取日誌失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取日誌失敗: {str(e)}")


# 錯誤處理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用異常處理器"""
    logger.error(f"未處理的異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "內部服務器錯誤",
                "timestamp": datetime.now().isoformat()
            }
        }
    )


# 主程序入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM JSON調度器管理API")
    parser.add_argument("--host", default="0.0.0.0", help="API服務器主機")
    parser.add_argument("--port", type=int, default=8080, help="API服務器端口")
    parser.add_argument("--reload", action="store_true", help="啟用自動重載")
    parser.add_argument("--log-level", default="info", help="日誌級別")
    
    args = parser.parse_args()
    
    # 啟動API服務器
    uvicorn.run(
        "scheduler_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )