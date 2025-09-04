#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即時狀態同步管理器
實現多平台任務的即時狀態同步和事件廣播功能

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("WebSockets not available, using polling mode")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory pub/sub")

from task_tracking_service import TaskTrackingService, TaskEvent, EventType
from task_tracking_models import TaskStatus, PlatformStatus


class SyncEventType(Enum):
    """同步事件類型"""
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    PLATFORM_HEALTH = "platform_health"
    SYSTEM_ALERT = "system_alert"
    CLIENT_CONNECT = "client_connect"
    CLIENT_DISCONNECT = "client_disconnect"
    HEARTBEAT = "heartbeat"
    BATCH_UPDATE = "batch_update"
    ERROR_NOTIFICATION = "error_notification"
    PERFORMANCE_METRICS = "performance_metrics"


class ClientType(Enum):
    """客戶端類型"""
    WEB_DASHBOARD = "web_dashboard"
    MOBILE_APP = "mobile_app"
    API_CLIENT = "api_client"
    CRAWLER_AGENT = "crawler_agent"
    MONITORING_SYSTEM = "monitoring_system"
    ADMIN_PANEL = "admin_panel"


@dataclass
class SyncEvent:
    """同步事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SyncEventType = SyncEventType.STATUS_UPDATE
    job_id: Optional[str] = None
    platform: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"
    target_clients: Optional[List[str]] = None  # None表示廣播給所有客戶端
    priority: int = 1  # 1=低, 2=中, 3=高, 4=緊急
    ttl: int = 300  # 事件生存時間（秒）


@dataclass
class ConnectedClient:
    """連接的客戶端"""
    client_id: str
    client_type: ClientType
    websocket: Optional[Any] = None
    subscriptions: Set[str] = field(default_factory=set)  # 訂閱的事件類型
    last_heartbeat: datetime = field(default_factory=datetime.now)
    connected_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


class RealTimeSyncManager:
    """即時狀態同步管理器"""
    
    def __init__(self,
                 task_service: Optional[TaskTrackingService] = None,
                 websocket_host: str = "localhost",
                 websocket_port: int = 8765,
                 redis_url: str = "redis://localhost:6379/1",
                 enable_websockets: bool = True,
                 enable_redis_pubsub: bool = True):
        """初始化即時同步管理器"""
        self.task_service = task_service
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        self.redis_url = redis_url
        self.enable_websockets = enable_websockets and WEBSOCKETS_AVAILABLE
        self.enable_redis_pubsub = enable_redis_pubsub and REDIS_AVAILABLE
        
        # 連接管理
        self.connected_clients: Dict[str, ConnectedClient] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> event_types
        self.event_channels: Dict[str, Set[str]] = {}  # event_type -> client_ids
        
        # WebSocket服務器
        self.websocket_server = None
        self.websocket_loop = None
        self.websocket_thread = None
        
        # Redis連接
        self.redis_client = None
        self.redis_pubsub = None
        self.redis_thread = None
        
        # 事件隊列
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.event_history: List[SyncEvent] = []
        self.max_history_size = 1000
        
        # 統計信息
        self.stats = {
            'total_events_sent': 0,
            'total_clients_connected': 0,
            'total_clients_disconnected': 0,
            'events_per_second': 0.0,
            'average_latency': 0.0,
            'start_time': datetime.now()
        }
        
        # 配置
        self.config = {
            'heartbeat_interval': 30,  # 心跳間隔（秒）
            'client_timeout': 120,  # 客戶端超時（秒）
            'max_clients': 1000,  # 最大客戶端數
            'event_batch_size': 50,  # 批量事件大小
            'event_batch_timeout': 1.0,  # 批量事件超時（秒）
            'compression_enabled': True,  # 啟用壓縮
            'rate_limit_per_client': 100  # 每客戶端每秒最大事件數
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="SyncManager")
        
        # 初始化組件
        self._setup_redis()
        self._setup_task_service_listener()
        
        logging.info("即時狀態同步管理器已初始化")
    
    def _setup_redis(self):
        """設置Redis連接"""
        if not self.enable_redis_pubsub:
            return
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            
            # 設置發布/訂閱
            self.redis_pubsub = self.redis_client.pubsub()
            
            # 訂閱頻道
            channels = [
                'task_events',
                'platform_status',
                'system_alerts',
                'performance_metrics'
            ]
            
            for channel in channels:
                self.redis_pubsub.subscribe(channel)
            
            # 啟動Redis監聽線程
            self.redis_thread = threading.Thread(
                target=self._redis_listener_loop,
                daemon=True,
                name="RedisListener"
            )
            self.redis_thread.start()
            
            logging.info("Redis發布/訂閱已設置")
            
        except Exception as e:
            logging.warning(f"Redis設置失敗: {e}")
            self.redis_client = None
            self.redis_pubsub = None
    
    def _setup_task_service_listener(self):
        """設置任務服務事件監聽器"""
        if self.task_service:
            self.task_service.add_event_listener(self._handle_task_event)
    
    async def start_websocket_server(self):
        """啟動WebSocket服務器"""
        if not self.enable_websockets:
            logging.info("WebSocket服務器已禁用")
            return
        
        try:
            # 創建WebSocket服務器
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                self.websocket_host,
                self.websocket_port,
                ping_interval=self.config['heartbeat_interval'],
                ping_timeout=self.config['client_timeout'],
                max_size=1024*1024,  # 1MB
                compression="deflate" if self.config['compression_enabled'] else None
            )
            
            logging.info(f"WebSocket服務器已啟動: ws://{self.websocket_host}:{self.websocket_port}")
            
            # 啟動事件處理循環
            await asyncio.gather(
                self._event_processing_loop(),
                self._heartbeat_loop(),
                self._cleanup_loop()
            )
            
        except Exception as e:
            logging.error(f"WebSocket服務器啟動失敗: {e}")
            raise
    
    def start_websocket_server_threaded(self):
        """在線程中啟動WebSocket服務器"""
        if not self.enable_websockets:
            return
        
        def run_server():
            self.websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.websocket_loop)
            
            try:
                self.websocket_loop.run_until_complete(self.start_websocket_server())
            except Exception as e:
                logging.error(f"WebSocket服務器線程錯誤: {e}")
            finally:
                self.websocket_loop.close()
        
        self.websocket_thread = threading.Thread(
            target=run_server,
            daemon=True,
            name="WebSocketServer"
        )
        self.websocket_thread.start()
        
        logging.info("WebSocket服務器線程已啟動")
    
    async def _handle_websocket_connection(self, websocket, path):
        """處理WebSocket連接"""
        client_id = str(uuid.uuid4())
        client = None
        
        try:
            # 等待客戶端認證消息
            auth_message = await asyncio.wait_for(
                websocket.recv(),
                timeout=10.0
            )
            
            auth_data = json.loads(auth_message)
            
            # 創建客戶端對象
            client = ConnectedClient(
                client_id=client_id,
                client_type=ClientType(auth_data.get('client_type', 'api_client')),
                websocket=websocket,
                user_id=auth_data.get('user_id'),
                metadata=auth_data.get('metadata', {})
            )
            
            # 註冊客戶端
            self.connected_clients[client_id] = client
            self.stats['total_clients_connected'] += 1
            
            # 發送連接確認
            await self._send_to_client(client_id, SyncEvent(
                event_type=SyncEventType.CLIENT_CONNECT,
                data={
                    'client_id': client_id,
                    'server_time': datetime.now().isoformat(),
                    'config': {
                        'heartbeat_interval': self.config['heartbeat_interval'],
                        'compression_enabled': self.config['compression_enabled']
                    }
                }
            ))
            
            logging.info(f"客戶端已連接: {client_id} ({client.client_type.value})")
            
            # 處理客戶端消息
            async for message in websocket:
                await self._handle_client_message(client_id, message)
        
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"客戶端連接已關閉: {client_id}")
        except asyncio.TimeoutError:
            logging.warning(f"客戶端認證超時: {client_id}")
        except Exception as e:
            logging.error(f"WebSocket連接錯誤: {e}")
        finally:
            # 清理客戶端
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                self.stats['total_clients_disconnected'] += 1
            
            # 清理訂閱
            if client_id in self.client_subscriptions:
                for event_type in self.client_subscriptions[client_id]:
                    if event_type in self.event_channels:
                        self.event_channels[event_type].discard(client_id)
                del self.client_subscriptions[client_id]
    
    async def _handle_client_message(self, client_id: str, message: str):
        """處理客戶端消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                # 訂閱事件類型
                event_types = data.get('event_types', [])
                await self._subscribe_client(client_id, event_types)
            
            elif message_type == 'unsubscribe':
                # 取消訂閱
                event_types = data.get('event_types', [])
                await self._unsubscribe_client(client_id, event_types)
            
            elif message_type == 'heartbeat':
                # 心跳響應
                client = self.connected_clients.get(client_id)
                if client:
                    client.last_heartbeat = datetime.now()
            
            elif message_type == 'get_status':
                # 獲取狀態
                job_id = data.get('job_id')
                if job_id and self.task_service:
                    status = self.task_service.get_job_status(job_id)
                    if status:
                        await self._send_to_client(client_id, SyncEvent(
                            event_type=SyncEventType.STATUS_UPDATE,
                            job_id=job_id,
                            data=status
                        ))
            
            elif message_type == 'get_history':
                # 獲取事件歷史
                job_id = data.get('job_id')
                limit = data.get('limit', 50)
                history = self._get_event_history(job_id, limit)
                
                await self._send_to_client(client_id, SyncEvent(
                    event_type=SyncEventType.BATCH_UPDATE,
                    data={'history': history}
                ))
            
        except Exception as e:
            logging.error(f"處理客戶端消息失敗: {e}")
    
    async def _subscribe_client(self, client_id: str, event_types: List[str]):
        """訂閱客戶端到事件類型"""
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        
        for event_type in event_types:
            # 添加到客戶端訂閱
            self.client_subscriptions[client_id].add(event_type)
            
            # 添加到事件頻道
            if event_type not in self.event_channels:
                self.event_channels[event_type] = set()
            self.event_channels[event_type].add(client_id)
        
        logging.info(f"客戶端 {client_id} 已訂閱事件: {event_types}")
    
    async def _unsubscribe_client(self, client_id: str, event_types: List[str]):
        """取消客戶端訂閱"""
        if client_id not in self.client_subscriptions:
            return
        
        for event_type in event_types:
            # 從客戶端訂閱中移除
            self.client_subscriptions[client_id].discard(event_type)
            
            # 從事件頻道中移除
            if event_type in self.event_channels:
                self.event_channels[event_type].discard(client_id)
        
        logging.info(f"客戶端 {client_id} 已取消訂閱事件: {event_types}")
    
    async def _send_to_client(self, client_id: str, event: SyncEvent):
        """發送事件到特定客戶端"""
        client = self.connected_clients.get(client_id)
        if not client or not client.is_active:
            return False
        
        try:
            message = {
                'event_id': event.event_id,
                'type': event.event_type.value,
                'job_id': event.job_id,
                'platform': event.platform,
                'data': event.data,
                'timestamp': event.timestamp.isoformat(),
                'source': event.source
            }
            
            if client.websocket:
                await client.websocket.send(json.dumps(message))
                return True
            
        except Exception as e:
            logging.warning(f"發送消息到客戶端失敗 {client_id}: {e}")
            # 標記客戶端為非活躍
            client.is_active = False
        
        return False
    
    async def _broadcast_event(self, event: SyncEvent):
        """廣播事件到所有相關客戶端"""
        event_type = event.event_type.value
        target_clients = set()
        
        # 確定目標客戶端
        if event.target_clients:
            # 指定的客戶端
            target_clients.update(event.target_clients)
        else:
            # 訂閱了此事件類型的所有客戶端
            target_clients.update(self.event_channels.get(event_type, set()))
            # 也發送給訂閱了所有事件的客戶端
            target_clients.update(self.event_channels.get('*', set()))
        
        # 發送到目標客戶端
        sent_count = 0
        for client_id in target_clients:
            if await self._send_to_client(client_id, event):
                sent_count += 1
        
        self.stats['total_events_sent'] += sent_count
        return sent_count
    
    async def _event_processing_loop(self):
        """事件處理循環"""
        batch_events = []
        last_batch_time = time.time()
        
        while True:
            try:
                # 等待事件或超時
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.config['event_batch_timeout']
                    )
                    batch_events.append(event)
                except asyncio.TimeoutError:
                    pass
                
                current_time = time.time()
                
                # 檢查是否需要處理批量事件
                should_process = (
                    len(batch_events) >= self.config['event_batch_size'] or
                    (batch_events and current_time - last_batch_time >= self.config['event_batch_timeout'])
                )
                
                if should_process and batch_events:
                    # 處理批量事件
                    await self._process_event_batch(batch_events)
                    batch_events.clear()
                    last_batch_time = current_time
                
            except Exception as e:
                logging.error(f"事件處理循環錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _process_event_batch(self, events: List[SyncEvent]):
        """處理批量事件"""
        try:
            # 按優先級排序
            events.sort(key=lambda e: e.priority, reverse=True)
            
            # 處理每個事件
            for event in events:
                # 檢查事件是否過期
                if (datetime.now() - event.timestamp).seconds > event.ttl:
                    continue
                
                # 廣播事件
                await self._broadcast_event(event)
                
                # 添加到歷史記錄
                self._add_to_history(event)
                
                # 發布到Redis（如果可用）
                if self.redis_client:
                    try:
                        channel = f"sync_events_{event.event_type.value}"
                        self.redis_client.publish(channel, json.dumps(asdict(event), default=str))
                    except Exception as e:
                        logging.warning(f"Redis發布失敗: {e}")
        
        except Exception as e:
            logging.error(f"處理批量事件失敗: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循環"""
        while True:
            try:
                await asyncio.sleep(self.config['heartbeat_interval'])
                
                current_time = datetime.now()
                disconnected_clients = []
                
                # 檢查客戶端心跳
                for client_id, client in self.connected_clients.items():
                    time_since_heartbeat = (current_time - client.last_heartbeat).seconds
                    
                    if time_since_heartbeat > self.config['client_timeout']:
                        disconnected_clients.append(client_id)
                    else:
                        # 發送心跳
                        await self._send_to_client(client_id, SyncEvent(
                            event_type=SyncEventType.HEARTBEAT,
                            data={'server_time': current_time.isoformat()}
                        ))
                
                # 清理超時的客戶端
                for client_id in disconnected_clients:
                    if client_id in self.connected_clients:
                        del self.connected_clients[client_id]
                        logging.info(f"客戶端超時斷開: {client_id}")
            
            except Exception as e:
                logging.error(f"心跳循環錯誤: {e}")
    
    async def _cleanup_loop(self):
        """清理循環"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分鐘清理一次
                
                # 清理事件歷史
                if len(self.event_history) > self.max_history_size:
                    # 保留最新的事件
                    self.event_history = self.event_history[-self.max_history_size//2:]
                
                # 清理非活躍客戶端
                inactive_clients = [
                    client_id for client_id, client in self.connected_clients.items()
                    if not client.is_active
                ]
                
                for client_id in inactive_clients:
                    del self.connected_clients[client_id]
                
                logging.info(f"清理完成: 移除了 {len(inactive_clients)} 個非活躍客戶端")
                
            except Exception as e:
                logging.error(f"清理循環錯誤: {e}")
    
    def _redis_listener_loop(self):
        """Redis監聽循環"""
        if not self.redis_pubsub:
            return
        
        try:
            for message in self.redis_pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # 解析Redis消息
                        data = json.loads(message['data'])
                        
                        # 轉換為同步事件
                        event = SyncEvent(
                            event_type=SyncEventType.STATUS_UPDATE,
                            job_id=data.get('job_id'),
                            platform=data.get('platform'),
                            data=data,
                            source='redis'
                        )
                        
                        # 添加到事件隊列
                        if self.websocket_loop:
                            asyncio.run_coroutine_threadsafe(
                                self.event_queue.put(event),
                                self.websocket_loop
                            )
                    
                    except Exception as e:
                        logging.warning(f"處理Redis消息失敗: {e}")
        
        except Exception as e:
            logging.error(f"Redis監聽循環錯誤: {e}")
    
    def _handle_task_event(self, task_event: TaskEvent):
        """處理任務服務事件"""
        try:
            # 轉換為同步事件
            sync_event = SyncEvent(
                event_type=SyncEventType.STATUS_UPDATE,
                job_id=task_event.job_id,
                platform=task_event.platform,
                data={
                    'event_type': task_event.event_type.value,
                    'message': task_event.message,
                    'old_status': task_event.old_status,
                    'new_status': task_event.new_status,
                    **task_event.data
                },
                source='task_service',
                priority=3 if task_event.event_type in [EventType.JOB_FAILED, EventType.ERROR_OCCURRED] else 2
            )
            
            # 添加到事件隊列
            if self.websocket_loop:
                asyncio.run_coroutine_threadsafe(
                    self.event_queue.put(sync_event),
                    self.websocket_loop
                )
        
        except Exception as e:
            logging.error(f"處理任務事件失敗: {e}")
    
    def _add_to_history(self, event: SyncEvent):
        """添加事件到歷史記錄"""
        self.event_history.append(event)
        
        # 限制歷史記錄大小
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
    
    def _get_event_history(self, job_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取事件歷史"""
        events = self.event_history
        
        # 按任務ID過濾
        if job_id:
            events = [e for e in events if e.job_id == job_id]
        
        # 按時間倒序排列並限制數量
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        # 轉換為字典
        return [asdict(event) for event in events]
    
    def send_custom_event(self, 
                         event_type: SyncEventType,
                         data: Dict[str, Any],
                         job_id: Optional[str] = None,
                         platform: Optional[str] = None,
                         target_clients: Optional[List[str]] = None,
                         priority: int = 2):
        """發送自定義事件"""
        try:
            event = SyncEvent(
                event_type=event_type,
                job_id=job_id,
                platform=platform,
                data=data,
                target_clients=target_clients,
                priority=priority,
                source='custom'
            )
            
            # 添加到事件隊列
            if self.websocket_loop:
                asyncio.run_coroutine_threadsafe(
                    self.event_queue.put(event),
                    self.websocket_loop
                )
            
            return True
        
        except Exception as e:
            logging.error(f"發送自定義事件失敗: {e}")
            return False
    
    def get_connected_clients(self) -> Dict[str, Dict[str, Any]]:
        """獲取連接的客戶端信息"""
        return {
            client_id: {
                'client_type': client.client_type.value,
                'user_id': client.user_id,
                'connected_at': client.connected_at.isoformat(),
                'last_heartbeat': client.last_heartbeat.isoformat(),
                'subscriptions': list(self.client_subscriptions.get(client_id, set())),
                'is_active': client.is_active,
                'metadata': client.metadata
            }
            for client_id, client in self.connected_clients.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'connected_clients': len(self.connected_clients),
            'active_subscriptions': sum(len(subs) for subs in self.client_subscriptions.values()),
            'event_history_size': len(self.event_history),
            'uptime_seconds': uptime.total_seconds(),
            'websocket_enabled': self.enable_websockets,
            'redis_enabled': self.enable_redis_pubsub,
            'redis_connected': self.redis_client is not None
        }
    
    def shutdown(self):
        """關閉同步管理器"""
        try:
            logging.info("正在關閉即時狀態同步管理器...")
            
            # 關閉WebSocket服務器
            if self.websocket_server:
                self.websocket_server.close()
            
            # 關閉WebSocket循環
            if self.websocket_loop and self.websocket_loop.is_running():
                self.websocket_loop.call_soon_threadsafe(self.websocket_loop.stop)
            
            # 關閉Redis連接
            if self.redis_pubsub:
                self.redis_pubsub.close()
            
            if self.redis_client:
                self.redis_client.close()
            
            # 關閉線程池
            self.executor.shutdown(wait=True)
            
            logging.info("即時狀態同步管理器已關閉")
            
        except Exception as e:
            logging.error(f"關閉同步管理器時出錯: {e}")


# 全局同步管理器實例
sync_manager = None


def get_sync_manager(task_service: Optional[TaskTrackingService] = None) -> RealTimeSyncManager:
    """獲取同步管理器實例"""
    global sync_manager
    if sync_manager is None:
        sync_manager = RealTimeSyncManager(task_service=task_service)
    return sync_manager


if __name__ == "__main__":
    # 測試即時同步管理器
    import time
    
    # 創建同步管理器
    manager = RealTimeSyncManager()
    
    # 啟動WebSocket服務器（在線程中）
    manager.start_websocket_server_threaded()
    
    # 等待服務器啟動
    time.sleep(2)
    
    # 發送測試事件
    manager.send_custom_event(
        event_type=SyncEventType.STATUS_UPDATE,
        data={'message': '測試事件', 'status': 'processing'},
        job_id='test-job-123',
        platform='linkedin'
    )
    
    # 獲取統計信息
    stats = manager.get_statistics()
    print(f"同步管理器統計: {stats}")
    
    # 保持運行
    try:
        while True:
            time.sleep(10)
            print(f"連接的客戶端: {len(manager.connected_clients)}")
    except KeyboardInterrupt:
        print("正在關閉...")
        manager.shutdown()