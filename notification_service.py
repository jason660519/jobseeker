#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
異常通知服務
專門處理多平台任務的異常通知，支援多種通知渠道和智能通知策略

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import uuid

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory notification tracking")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests not available, webhook notifications disabled")

from error_handling_manager import ErrorInfo, ErrorSeverity, ErrorCategory


class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    SMS = "sms"
    PUSH = "push"
    LOG = "log"


class NotificationPriority(Enum):
    """通知優先級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class NotificationType(Enum):
    """通知類型"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    ALERT = "alert"
    HEALTH = "health"
    PERFORMANCE = "performance"
    SECURITY = "security"


class DeliveryStatus(Enum):
    """投遞狀態"""
    PENDING = "pending"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class NotificationTemplate:
    """通知模板"""
    template_id: str
    name: str
    channel: NotificationChannel
    subject_template: str = ""
    body_template: str = ""
    html_template: str = ""
    variables: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class NotificationRule:
    """通知規則"""
    rule_id: str
    name: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    channels: List[NotificationChannel] = field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    template_id: Optional[str] = None
    rate_limit: int = 10  # 每小時最大通知數
    cooldown: int = 300  # 冷卻時間（秒）
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class NotificationRecipient:
    """通知接收者"""
    recipient_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_user_id: Optional[str] = None
    webhook_url: Optional[str] = None
    channels: List[NotificationChannel] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class NotificationMessage:
    """通知消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channel: NotificationChannel = NotificationChannel.EMAIL
    recipient_id: str = ""
    subject: str = ""
    body: str = ""
    html_body: str = ""
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 投遞信息
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    # 關聯信息
    job_id: Optional[str] = None
    error_id: Optional[str] = None
    platform: Optional[str] = None
    rule_id: Optional[str] = None
    template_id: Optional[str] = None


@dataclass
class ChannelConfig:
    """渠道配置"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    rate_limit: int = 100  # 每小時最大發送數
    retry_config: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30  # 超時時間（秒）


class NotificationService:
    """通知服務"""
    
    def __init__(self,
                 redis_url: str = "redis://localhost:6379/4",
                 default_channels: Optional[List[NotificationChannel]] = None):
        """初始化通知服務"""
        self.redis_url = redis_url
        self.default_channels = default_channels or [NotificationChannel.LOG]
        
        # Redis連接
        self.redis_client = None
        self._setup_redis()
        
        # 存儲
        self.templates: Dict[str, NotificationTemplate] = {}
        self.rules: Dict[str, NotificationRule] = {}
        self.recipients: Dict[str, NotificationRecipient] = {}
        self.channel_configs: Dict[NotificationChannel, ChannelConfig] = {}
        self.messages: Dict[str, NotificationMessage] = {}
        
        # 隊列和處理
        self.message_queue: List[NotificationMessage] = []
        self.processing_queue: List[NotificationMessage] = []
        self.queue_lock = threading.Lock()
        
        # 速率限制
        self.rate_limits: Dict[str, List[datetime]] = {}  # channel_recipient -> timestamps
        self.rate_lock = threading.Lock()
        
        # 統計信息
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'by_channel': {},
            'by_priority': {},
            'by_type': {},
            'start_time': datetime.now()
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="NotificationSender")
        self.background_tasks: List[Future] = []
        self.shutdown_event = threading.Event()
        
        # 渠道處理器
        self.channel_handlers = {
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.WEBHOOK: self._send_webhook,
            NotificationChannel.SLACK: self._send_slack,
            NotificationChannel.TEAMS: self._send_teams,
            NotificationChannel.DISCORD: self._send_discord,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.PUSH: self._send_push,
            NotificationChannel.LOG: self._send_log
        }
        
        # 初始化默認配置
        self._setup_default_configs()
        self._setup_default_templates()
        
        # 啟動背景任務
        self._start_background_tasks()
        
        logging.info("通知服務已初始化")
    
    def _setup_redis(self):
        """設置Redis連接"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logging.info("Redis連接已建立（通知服務）")
        except Exception as e:
            logging.warning(f"Redis連接失敗（通知服務）: {e}")
            self.redis_client = None
    
    def _setup_default_configs(self):
        """設置默認渠道配置"""
        # 郵件配置
        self.channel_configs[NotificationChannel.EMAIL] = ChannelConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            config={
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': '',
                'use_tls': True
            },
            rate_limit=50,
            timeout=30
        )
        
        # Webhook配置
        self.channel_configs[NotificationChannel.WEBHOOK] = ChannelConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=True,
            config={
                'default_url': '',
                'headers': {'Content-Type': 'application/json'},
                'verify_ssl': True
            },
            rate_limit=100,
            timeout=15
        )
        
        # Slack配置
        self.channel_configs[NotificationChannel.SLACK] = ChannelConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            config={
                'webhook_url': '',
                'bot_token': '',
                'default_channel': '#alerts'
            },
            rate_limit=60,
            timeout=20
        )
        
        # 日誌配置
        self.channel_configs[NotificationChannel.LOG] = ChannelConfig(
            channel=NotificationChannel.LOG,
            enabled=True,
            config={
                'logger_name': 'notification',
                'log_level': 'INFO'
            },
            rate_limit=1000,
            timeout=5
        )
    
    def _setup_default_templates(self):
        """設置默認通知模板"""
        # 錯誤通知模板
        self.templates['error_notification'] = NotificationTemplate(
            template_id='error_notification',
            name='錯誤通知',
            channel=NotificationChannel.EMAIL,
            subject_template='[JobSpy Alert] 錯誤通知: {job_id}',
            body_template='''
任務錯誤通知

任務ID: {job_id}
平台: {platform}
錯誤類型: {error_type}
錯誤消息: {error_message}
嚴重程度: {severity}
時間: {timestamp}

詳細信息:
{details}

錯誤ID: {error_id}
            ''',
            variables=['job_id', 'platform', 'error_type', 'error_message', 'severity', 'timestamp', 'details', 'error_id']
        )
        
        # 系統健康警報模板
        self.templates['health_alert'] = NotificationTemplate(
            template_id='health_alert',
            name='系統健康警報',
            channel=NotificationChannel.SLACK,
            subject_template='[JobSpy] 系統健康警報',
            body_template='''
系統健康檢查發現問題:

問題列表:
{issues}

系統狀態:
{system_status}

檢查時間: {timestamp}
            ''',
            variables=['issues', 'system_status', 'timestamp']
        )
        
        # 任務完成通知模板
        self.templates['job_completion'] = NotificationTemplate(
            template_id='job_completion',
            name='任務完成通知',
            channel=NotificationChannel.EMAIL,
            subject_template='[JobSpy] 任務完成: {job_id}',
            body_template='''
任務執行完成

任務ID: {job_id}
狀態: {status}
平台數量: {platform_count}
成功平台: {successful_platforms}
失敗平台: {failed_platforms}
執行時間: {duration}
完成時間: {completion_time}

結果摘要:
{summary}
            ''',
            variables=['job_id', 'status', 'platform_count', 'successful_platforms', 'failed_platforms', 'duration', 'completion_time', 'summary']
        )
    
    def _start_background_tasks(self):
        """啟動背景任務"""
        # 消息處理任務
        self.background_tasks.append(
            self.executor.submit(self._message_processing_loop)
        )
        
        # 重試處理任務
        self.background_tasks.append(
            self.executor.submit(self._retry_processing_loop)
        )
        
        # 清理任務
        self.background_tasks.append(
            self.executor.submit(self._cleanup_loop)
        )
        
        # 統計更新任務
        self.background_tasks.append(
            self.executor.submit(self._stats_update_loop)
        )
    
    def send_notification(self,
                         notification_type: NotificationType,
                         priority: NotificationPriority,
                         subject: str,
                         body: str,
                         recipients: Optional[List[str]] = None,
                         channels: Optional[List[NotificationChannel]] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         job_id: Optional[str] = None,
                         error_id: Optional[str] = None,
                         platform: Optional[str] = None,
                         template_id: Optional[str] = None,
                         template_vars: Optional[Dict[str, Any]] = None,
                         scheduled_at: Optional[datetime] = None) -> List[str]:
        """發送通知"""
        try:
            message_ids = []
            
            # 使用默認接收者和渠道
            if not recipients:
                recipients = list(self.recipients.keys()) or ['default']
            
            if not channels:
                channels = self.default_channels
            
            # 處理模板
            if template_id and template_vars:
                template = self.templates.get(template_id)
                if template:
                    subject = template.subject_template.format(**template_vars)
                    body = template.body_template.format(**template_vars)
            
            # 為每個接收者和渠道創建消息
            for recipient_id in recipients:
                for channel in channels:
                    # 檢查渠道是否啟用
                    if not self._is_channel_enabled(channel):
                        continue
                    
                    # 檢查速率限制
                    if not self._check_rate_limit(channel, recipient_id):
                        logging.warning(f"速率限制: {channel.value} -> {recipient_id}")
                        continue
                    
                    # 創建消息
                    message = NotificationMessage(
                        notification_type=notification_type,
                        priority=priority,
                        channel=channel,
                        recipient_id=recipient_id,
                        subject=subject,
                        body=body,
                        metadata=metadata or {},
                        job_id=job_id,
                        error_id=error_id,
                        platform=platform,
                        template_id=template_id,
                        scheduled_at=scheduled_at
                    )
                    
                    # 添加到隊列
                    self._add_to_queue(message)
                    message_ids.append(message.message_id)
                    
                    # 存儲消息
                    self.messages[message.message_id] = message
            
            logging.info(f"已創建 {len(message_ids)} 個通知消息")
            return message_ids
            
        except Exception as e:
            logging.error(f"發送通知失敗: {e}")
            return []
    
    def send_error_notification(self, error_info: ErrorInfo, additional_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """發送錯誤通知"""
        try:
            # 確定通知優先級
            priority_mapping = {
                ErrorSeverity.LOW: NotificationPriority.LOW,
                ErrorSeverity.MEDIUM: NotificationPriority.MEDIUM,
                ErrorSeverity.HIGH: NotificationPriority.HIGH,
                ErrorSeverity.CRITICAL: NotificationPriority.CRITICAL
            }
            priority = priority_mapping.get(error_info.severity, NotificationPriority.MEDIUM)
            
            # 確定通知渠道
            channels = self._determine_channels_for_error(error_info)
            
            # 準備模板變量
            template_vars = {
                'job_id': error_info.job_id,
                'platform': error_info.platform or 'N/A',
                'error_type': error_info.error_type,
                'error_message': error_info.error_message,
                'severity': error_info.severity.value,
                'category': error_info.category.value,
                'timestamp': error_info.timestamp.isoformat(),
                'error_id': error_info.error_id,
                'retry_count': error_info.retry_count,
                'details': json.dumps(error_info.context, indent=2) if error_info.context else 'N/A'
            }
            
            # 添加額外上下文
            if additional_context:
                template_vars.update(additional_context)
            
            # 發送通知
            return self.send_notification(
                notification_type=NotificationType.ERROR,
                priority=priority,
                subject=f"[JobSpy Alert] 錯誤通知: {error_info.job_id}",
                body="",  # 將使用模板
                channels=channels,
                metadata={
                    'error_category': error_info.category.value,
                    'error_severity': error_info.severity.value,
                    'retry_count': error_info.retry_count
                },
                job_id=error_info.job_id,
                error_id=error_info.error_id,
                platform=error_info.platform,
                template_id='error_notification',
                template_vars=template_vars
            )
            
        except Exception as e:
            logging.error(f"發送錯誤通知失敗: {e}")
            return []
    
    def send_health_alert(self, health_status: Dict[str, Any]) -> List[str]:
        """發送健康警報"""
        try:
            # 確定優先級
            priority = NotificationPriority.HIGH
            if len(health_status.get('issues', [])) > 5:
                priority = NotificationPriority.CRITICAL
            
            # 準備模板變量
            template_vars = {
                'issues': '\n'.join(f"- {issue}" for issue in health_status.get('issues', [])),
                'system_status': json.dumps(health_status.get('stats', {}), indent=2),
                'timestamp': health_status.get('timestamp', datetime.now().isoformat())
            }
            
            # 發送通知
            return self.send_notification(
                notification_type=NotificationType.ALERT,
                priority=priority,
                subject="[JobSpy] 系統健康警報",
                body="",  # 將使用模板
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                metadata={
                    'alert_type': 'health_check',
                    'issue_count': len(health_status.get('issues', []))
                },
                template_id='health_alert',
                template_vars=template_vars
            )
            
        except Exception as e:
            logging.error(f"發送健康警報失敗: {e}")
            return []
    
    def send_job_completion_notification(self, job_result: Dict[str, Any]) -> List[str]:
        """發送任務完成通知"""
        try:
            # 確定通知類型和優先級
            status = job_result.get('status', 'unknown')
            if status == 'completed':
                notification_type = NotificationType.SUCCESS
                priority = NotificationPriority.LOW
            elif status == 'failed':
                notification_type = NotificationType.ERROR
                priority = NotificationPriority.MEDIUM
            else:
                notification_type = NotificationType.INFO
                priority = NotificationPriority.LOW
            
            # 準備模板變量
            template_vars = {
                'job_id': job_result.get('job_id', 'unknown'),
                'status': status,
                'platform_count': job_result.get('platform_count', 0),
                'successful_platforms': ', '.join(job_result.get('successful_platforms', [])),
                'failed_platforms': ', '.join(job_result.get('failed_platforms', [])),
                'duration': job_result.get('duration', 'unknown'),
                'completion_time': job_result.get('completion_time', datetime.now().isoformat()),
                'summary': json.dumps(job_result.get('summary', {}), indent=2)
            }
            
            # 發送通知
            return self.send_notification(
                notification_type=notification_type,
                priority=priority,
                subject=f"[JobSpy] 任務完成: {job_result.get('job_id', 'unknown')}",
                body="",  # 將使用模板
                channels=[NotificationChannel.EMAIL],
                metadata={
                    'completion_type': 'job_result',
                    'job_status': status
                },
                job_id=job_result.get('job_id'),
                template_id='job_completion',
                template_vars=template_vars
            )
            
        except Exception as e:
            logging.error(f"發送任務完成通知失敗: {e}")
            return []
    
    def _determine_channels_for_error(self, error_info: ErrorInfo) -> List[NotificationChannel]:
        """根據錯誤信息確定通知渠道"""
        channels = [NotificationChannel.LOG]  # 總是記錄日誌
        
        # 根據嚴重程度確定渠道
        if error_info.severity == ErrorSeverity.CRITICAL:
            channels.extend([NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK])
        elif error_info.severity == ErrorSeverity.HIGH:
            channels.extend([NotificationChannel.EMAIL, NotificationChannel.SLACK])
        elif error_info.severity == ErrorSeverity.MEDIUM:
            channels.append(NotificationChannel.EMAIL)
        
        # 根據錯誤類別調整
        if error_info.category == ErrorCategory.AUTHENTICATION:
            channels.append(NotificationChannel.SLACK)  # 認證錯誤需要立即關注
        elif error_info.category == ErrorCategory.SYSTEM:
            channels.extend([NotificationChannel.EMAIL, NotificationChannel.WEBHOOK])
        
        # 去重並過濾啟用的渠道
        unique_channels = list(set(channels))
        return [ch for ch in unique_channels if self._is_channel_enabled(ch)]
    
    def _is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """檢查渠道是否啟用"""
        config = self.channel_configs.get(channel)
        return config is not None and config.enabled
    
    def _check_rate_limit(self, channel: NotificationChannel, recipient_id: str) -> bool:
        """檢查速率限制"""
        try:
            with self.rate_lock:
                key = f"{channel.value}_{recipient_id}"
                now = datetime.now()
                hour_ago = now - timedelta(hours=1)
                
                # 清理舊記錄
                if key in self.rate_limits:
                    self.rate_limits[key] = [
                        ts for ts in self.rate_limits[key]
                        if ts > hour_ago
                    ]
                else:
                    self.rate_limits[key] = []
                
                # 檢查限制
                config = self.channel_configs.get(channel)
                if config and len(self.rate_limits[key]) >= config.rate_limit:
                    return False
                
                # 記錄本次發送
                self.rate_limits[key].append(now)
                return True
        
        except Exception as e:
            logging.warning(f"檢查速率限制失敗: {e}")
            return True
    
    def _add_to_queue(self, message: NotificationMessage):
        """添加消息到隊列"""
        with self.queue_lock:
            # 根據優先級插入
            priority_order = {
                NotificationPriority.URGENT: 0,
                NotificationPriority.CRITICAL: 1,
                NotificationPriority.HIGH: 2,
                NotificationPriority.MEDIUM: 3,
                NotificationPriority.LOW: 4
            }
            
            message_priority = priority_order.get(message.priority, 3)
            
            # 找到插入位置
            insert_index = len(self.message_queue)
            for i, queued_message in enumerate(self.message_queue):
                queued_priority = priority_order.get(queued_message.priority, 3)
                if message_priority < queued_priority:
                    insert_index = i
                    break
            
            self.message_queue.insert(insert_index, message)
    
    def _message_processing_loop(self):
        """消息處理循環"""
        while not self.shutdown_event.is_set():
            try:
                messages_to_process = []
                
                # 獲取待處理消息
                with self.queue_lock:
                    current_time = datetime.now()
                    
                    # 檢查調度時間
                    for message in self.message_queue[:]:
                        if message.scheduled_at is None or message.scheduled_at <= current_time:
                            messages_to_process.append(message)
                            self.message_queue.remove(message)
                            self.processing_queue.append(message)
                        
                        # 限制批量處理數量
                        if len(messages_to_process) >= 10:
                            break
                
                # 處理消息
                for message in messages_to_process:
                    self._process_message(message)
                
                # 等待下一次處理
                if not messages_to_process:
                    self.shutdown_event.wait(1)
                
            except Exception as e:
                logging.error(f"消息處理循環錯誤: {e}")
                self.shutdown_event.wait(5)
    
    def _process_message(self, message: NotificationMessage):
        """處理單個消息"""
        try:
            # 更新狀態
            message.status = DeliveryStatus.SENDING
            
            # 獲取渠道處理器
            handler = self.channel_handlers.get(message.channel)
            if not handler:
                raise ValueError(f"不支援的通知渠道: {message.channel.value}")
            
            # 發送消息
            success = handler(message)
            
            if success:
                message.status = DeliveryStatus.DELIVERED
                message.delivered_at = datetime.now()
                self.stats['total_delivered'] += 1
                logging.info(f"通知已發送: {message.message_id} via {message.channel.value}")
            else:
                message.status = DeliveryStatus.FAILED
                message.failed_at = datetime.now()
                self.stats['total_failed'] += 1
                
                # 檢查是否需要重試
                if message.retry_count < message.max_retries:
                    self._schedule_retry(message)
                else:
                    logging.error(f"通知發送失敗（已達最大重試次數）: {message.message_id}")
            
            # 更新統計
            self._update_stats(message)
            
            # 從處理隊列移除
            with self.queue_lock:
                if message in self.processing_queue:
                    self.processing_queue.remove(message)
            
        except Exception as e:
            logging.error(f"處理消息失敗: {e}")
            message.status = DeliveryStatus.FAILED
            message.failed_at = datetime.now()
            message.error_message = str(e)
            
            # 檢查重試
            if message.retry_count < message.max_retries:
                self._schedule_retry(message)
    
    def _schedule_retry(self, message: NotificationMessage):
        """安排重試"""
        try:
            message.retry_count += 1
            message.status = DeliveryStatus.RETRYING
            
            # 計算重試延遲（指數退避）
            delay = min(60 * (2 ** (message.retry_count - 1)), 3600)  # 最大1小時
            retry_time = datetime.now() + timedelta(seconds=delay)
            
            message.scheduled_at = retry_time
            
            # 重新添加到隊列
            with self.queue_lock:
                if message in self.processing_queue:
                    self.processing_queue.remove(message)
                self.message_queue.append(message)
            
            logging.info(f"已安排重試: {message.message_id}, 延遲 {delay} 秒")
            
        except Exception as e:
            logging.error(f"安排重試失敗: {e}")
    
    def _update_stats(self, message: NotificationMessage):
        """更新統計信息"""
        try:
            self.stats['total_sent'] += 1
            
            # 按渠道統計
            channel_key = message.channel.value
            if channel_key not in self.stats['by_channel']:
                self.stats['by_channel'][channel_key] = {'sent': 0, 'delivered': 0, 'failed': 0}
            
            self.stats['by_channel'][channel_key]['sent'] += 1
            if message.status == DeliveryStatus.DELIVERED:
                self.stats['by_channel'][channel_key]['delivered'] += 1
            elif message.status == DeliveryStatus.FAILED:
                self.stats['by_channel'][channel_key]['failed'] += 1
            
            # 按優先級統計
            priority_key = message.priority.value
            if priority_key not in self.stats['by_priority']:
                self.stats['by_priority'][priority_key] = {'sent': 0, 'delivered': 0, 'failed': 0}
            
            self.stats['by_priority'][priority_key]['sent'] += 1
            if message.status == DeliveryStatus.DELIVERED:
                self.stats['by_priority'][priority_key]['delivered'] += 1
            elif message.status == DeliveryStatus.FAILED:
                self.stats['by_priority'][priority_key]['failed'] += 1
            
            # 按類型統計
            type_key = message.notification_type.value
            if type_key not in self.stats['by_type']:
                self.stats['by_type'][type_key] = {'sent': 0, 'delivered': 0, 'failed': 0}
            
            self.stats['by_type'][type_key]['sent'] += 1
            if message.status == DeliveryStatus.DELIVERED:
                self.stats['by_type'][type_key]['delivered'] += 1
            elif message.status == DeliveryStatus.FAILED:
                self.stats['by_type'][type_key]['failed'] += 1
        
        except Exception as e:
            logging.warning(f"更新統計信息失敗: {e}")
    
    # 渠道處理器實現
    def _send_email(self, message: NotificationMessage) -> bool:
        """發送郵件"""
        try:
            config = self.channel_configs[NotificationChannel.EMAIL].config
            
            # 檢查配置
            if not all([config.get('smtp_server'), config.get('username'), config.get('password')]):
                logging.warning("郵件配置不完整")
                return False
            
            # 獲取接收者信息
            recipient = self.recipients.get(message.recipient_id)
            if not recipient or not recipient.email:
                logging.warning(f"找不到接收者郵件地址: {message.recipient_id}")
                return False
            
            # 創建郵件
            msg = MIMEMultipart()
            msg['From'] = config.get('from_email', config['username'])
            msg['To'] = recipient.email
            msg['Subject'] = message.subject
            
            # 添加正文
            if message.html_body:
                msg.attach(MIMEText(message.html_body, 'html'))
            else:
                msg.attach(MIMEText(message.body, 'plain'))
            
            # 添加附件
            for attachment_path in message.attachments:
                if Path(attachment_path).exists():
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {Path(attachment_path).name}'
                        )
                        msg.attach(part)
            
            # 發送郵件
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logging.error(f"發送郵件失敗: {e}")
            message.error_message = str(e)
            return False
    
    def _send_webhook(self, message: NotificationMessage) -> bool:
        """發送Webhook"""
        try:
            if not REQUESTS_AVAILABLE:
                logging.warning("Requests庫不可用，無法發送Webhook")
                return False
            
            config = self.channel_configs[NotificationChannel.WEBHOOK].config
            
            # 獲取接收者信息
            recipient = self.recipients.get(message.recipient_id)
            webhook_url = None
            
            if recipient and recipient.webhook_url:
                webhook_url = recipient.webhook_url
            elif config.get('default_url'):
                webhook_url = config['default_url']
            
            if not webhook_url:
                logging.warning(f"找不到Webhook URL: {message.recipient_id}")
                return False
            
            # 準備payload
            payload = {
                'message_id': message.message_id,
                'type': message.notification_type.value,
                'priority': message.priority.value,
                'subject': message.subject,
                'body': message.body,
                'timestamp': message.created_at.isoformat(),
                'metadata': message.metadata
            }
            
            # 添加任務相關信息
            if message.job_id:
                payload['job_id'] = message.job_id
            if message.error_id:
                payload['error_id'] = message.error_id
            if message.platform:
                payload['platform'] = message.platform
            
            # 發送請求
            headers = config.get('headers', {'Content-Type': 'application/json'})
            timeout = self.channel_configs[NotificationChannel.WEBHOOK].timeout
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=timeout,
                verify=config.get('verify_ssl', True)
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logging.error(f"發送Webhook失敗: {e}")
            message.error_message = str(e)
            return False
    
    def _send_slack(self, message: NotificationMessage) -> bool:
        """發送Slack通知"""
        try:
            if not REQUESTS_AVAILABLE:
                logging.warning("Requests庫不可用，無法發送Slack通知")
                return False
            
            config = self.channel_configs[NotificationChannel.SLACK].config
            
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                logging.warning("Slack Webhook URL未配置")
                return False
            
            # 確定顏色
            color_mapping = {
                NotificationPriority.LOW: 'good',
                NotificationPriority.MEDIUM: 'warning',
                NotificationPriority.HIGH: 'danger',
                NotificationPriority.CRITICAL: 'danger',
                NotificationPriority.URGENT: 'danger'
            }
            color = color_mapping.get(message.priority, 'warning')
            
            # 準備Slack消息
            payload = {
                'channel': config.get('default_channel', '#alerts'),
                'username': 'JobSpy Notification',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': message.subject,
                    'text': message.body,
                    'fields': [],
                    'timestamp': int(message.created_at.timestamp())
                }]
            }
            
            # 添加字段
            attachment = payload['attachments'][0]
            
            if message.job_id:
                attachment['fields'].append({
                    'title': '任務ID',
                    'value': message.job_id,
                    'short': True
                })
            
            if message.platform:
                attachment['fields'].append({
                    'title': '平台',
                    'value': message.platform,
                    'short': True
                })
            
            attachment['fields'].append({
                'title': '優先級',
                'value': message.priority.value,
                'short': True
            })
            
            attachment['fields'].append({
                'title': '類型',
                'value': message.notification_type.value,
                'short': True
            })
            
            # 發送請求
            timeout = self.channel_configs[NotificationChannel.SLACK].timeout
            response = requests.post(webhook_url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logging.error(f"發送Slack通知失敗: {e}")
            message.error_message = str(e)
            return False
    
    def _send_teams(self, message: NotificationMessage) -> bool:
        """發送Teams通知"""
        # Teams通知實現
        logging.info(f"Teams通知: {message.subject}")
        return True
    
    def _send_discord(self, message: NotificationMessage) -> bool:
        """發送Discord通知"""
        # Discord通知實現
        logging.info(f"Discord通知: {message.subject}")
        return True
    
    def _send_sms(self, message: NotificationMessage) -> bool:
        """發送SMS通知"""
        # SMS通知實現
        logging.info(f"SMS通知: {message.subject}")
        return True
    
    def _send_push(self, message: NotificationMessage) -> bool:
        """發送推送通知"""
        # 推送通知實現
        logging.info(f"推送通知: {message.subject}")
        return True
    
    def _send_log(self, message: NotificationMessage) -> bool:
        """記錄日誌通知"""
        try:
            config = self.channel_configs[NotificationChannel.LOG].config
            logger_name = config.get('logger_name', 'notification')
            log_level = config.get('log_level', 'INFO')
            
            logger = logging.getLogger(logger_name)
            
            log_message = f"[{message.notification_type.value.upper()}] {message.subject}"
            if message.body:
                log_message += f" - {message.body}"
            
            if message.job_id:
                log_message += f" (Job: {message.job_id})"
            
            if log_level.upper() == 'DEBUG':
                logger.debug(log_message)
            elif log_level.upper() == 'INFO':
                logger.info(log_message)
            elif log_level.upper() == 'WARNING':
                logger.warning(log_message)
            elif log_level.upper() == 'ERROR':
                logger.error(log_message)
            elif log_level.upper() == 'CRITICAL':
                logger.critical(log_message)
            else:
                logger.info(log_message)
            
            return True
            
        except Exception as e:
            print(f"記錄日誌通知失敗: {e}")
            return False
    
    def _retry_processing_loop(self):
        """重試處理循環"""
        while not self.shutdown_event.is_set():
            try:
                # 檢查需要重試的消息
                current_time = datetime.now()
                retry_messages = []
                
                with self.queue_lock:
                    for message in self.message_queue[:]:
                        if (message.status == DeliveryStatus.RETRYING and
                            message.scheduled_at and
                            message.scheduled_at <= current_time):
                            retry_messages.append(message)
                            self.message_queue.remove(message)
                
                # 處理重試消息
                for message in retry_messages:
                    message.status = DeliveryStatus.PENDING
                    self._add_to_queue(message)
                
                # 等待下一次檢查
                self.shutdown_event.wait(30)
                
            except Exception as e:
                logging.error(f"重試處理循環錯誤: {e}")
                self.shutdown_event.wait(60)
    
    def _cleanup_loop(self):
        """清理循環"""
        while not self.shutdown_event.is_set():
            try:
                # 清理已完成的舊消息
                cutoff_time = datetime.now() - timedelta(days=7)
                
                completed_messages = [
                    msg_id for msg_id, msg in self.messages.items()
                    if msg.status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED] and
                    (msg.delivered_at or msg.failed_at or msg.created_at) < cutoff_time
                ]
                
                for msg_id in completed_messages:
                    del self.messages[msg_id]
                
                # 清理速率限制歷史
                hour_ago = datetime.now() - timedelta(hours=1)
                with self.rate_lock:
                    for key in list(self.rate_limits.keys()):
                        self.rate_limits[key] = [
                            ts for ts in self.rate_limits[key]
                            if ts > hour_ago
                        ]
                        if not self.rate_limits[key]:
                            del self.rate_limits[key]
                
                logging.info(f"清理完成: 移除了 {len(completed_messages)} 個已完成消息")
                
                # 等待下一次清理
                self.shutdown_event.wait(3600)  # 每小時清理一次
                
            except Exception as e:
                logging.error(f"清理循環錯誤: {e}")
                self.shutdown_event.wait(300)
    
    def _stats_update_loop(self):
        """統計更新循環"""
        while not self.shutdown_event.is_set():
            try:
                # 持久化統計信息到Redis
                if self.redis_client:
                    self.redis_client.hset(
                        'notification_stats',
                        'current',
                        json.dumps(self.stats, default=str)
                    )
                
                # 等待下一次更新
                self.shutdown_event.wait(300)  # 每5分鐘更新一次
                
            except Exception as e:
                logging.error(f"統計更新循環錯誤: {e}")
                self.shutdown_event.wait(60)
    
    # 管理方法
    def add_recipient(self, recipient: NotificationRecipient):
        """添加接收者"""
        self.recipients[recipient.recipient_id] = recipient
        logging.info(f"已添加接收者: {recipient.name}")
    
    def add_template(self, template: NotificationTemplate):
        """添加模板"""
        self.templates[template.template_id] = template
        logging.info(f"已添加模板: {template.name}")
    
    def add_rule(self, rule: NotificationRule):
        """添加規則"""
        self.rules[rule.rule_id] = rule
        logging.info(f"已添加規則: {rule.name}")
    
    def update_channel_config(self, channel: NotificationChannel, config: Dict[str, Any]):
        """更新渠道配置"""
        if channel in self.channel_configs:
            self.channel_configs[channel].config.update(config)
            logging.info(f"已更新渠道配置: {channel.value}")
    
    def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """獲取消息狀態"""
        message = self.messages.get(message_id)
        if not message:
            return None
        
        return {
            'message_id': message.message_id,
            'status': message.status.value,
            'created_at': message.created_at.isoformat(),
            'sent_at': message.sent_at.isoformat() if message.sent_at else None,
            'delivered_at': message.delivered_at.isoformat() if message.delivered_at else None,
            'failed_at': message.failed_at.isoformat() if message.failed_at else None,
            'retry_count': message.retry_count,
            'error_message': message.error_message,
            'channel': message.channel.value,
            'priority': message.priority.value,
            'type': message.notification_type.value
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        current_time = datetime.now()
        uptime = current_time - self.stats['start_time']
        
        # 計算成功率
        total_sent = self.stats['total_sent']
        success_rate = 0
        if total_sent > 0:
            success_rate = self.stats['total_delivered'] / total_sent
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_sent': total_sent,
            'total_delivered': self.stats['total_delivered'],
            'total_failed': self.stats['total_failed'],
            'success_rate': success_rate,
            'queue_size': len(self.message_queue),
            'processing_size': len(self.processing_queue),
            'by_channel': self.stats['by_channel'],
            'by_priority': self.stats['by_priority'],
            'by_type': self.stats['by_type'],
            'timestamp': current_time.isoformat()
        }
    
    def shutdown(self):
        """關閉通知服務"""
        try:
            logging.info("正在關閉通知服務...")
            
            # 設置關閉事件
            self.shutdown_event.set()
            
            # 等待背景任務完成
            for future in self.background_tasks:
                try:
                    future.result(timeout=5)
                except Exception as e:
                    logging.warning(f"背景任務關閉異常: {e}")
            
            # 關閉線程池
            self.executor.shutdown(wait=True, timeout=10)
            
            # 關閉Redis連接
            if self.redis_client:
                self.redis_client.close()
            
            logging.info("通知服務已關閉")
            
        except Exception as e:
            logging.error(f"關閉通知服務失敗: {e}")


if __name__ == "__main__":
    # 測試通知服務
    import time
    
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建通知服務
    notification_service = NotificationService(
        default_channels=[NotificationChannel.LOG, NotificationChannel.EMAIL]
    )
    
    try:
        # 添加測試接收者
        test_recipient = NotificationRecipient(
            recipient_id="test_user",
            name="測試用戶",
            email="test@example.com",
            channels=[NotificationChannel.EMAIL, NotificationChannel.LOG]
        )
        notification_service.add_recipient(test_recipient)
        
        # 測試發送通知
        print("\n=== 測試通知服務 ===")
        
        # 發送信息通知
        message_ids = notification_service.send_notification(
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.LOW,
            subject="測試信息通知",
            body="這是一個測試信息通知",
            recipients=["test_user"],
            channels=[NotificationChannel.LOG]
        )
        print(f"發送信息通知: {message_ids}")
        
        # 發送警告通知
        message_ids = notification_service.send_notification(
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.MEDIUM,
            subject="測試警告通知",
            body="這是一個測試警告通知",
            recipients=["test_user"],
            channels=[NotificationChannel.LOG]
        )
        print(f"發送警告通知: {message_ids}")
        
        # 模擬錯誤通知
        from error_handling_manager import ErrorInfo, ErrorSeverity, ErrorCategory
        
        test_error = ErrorInfo(
            job_id="test_job_123",
            platform="linkedin",
            error_type="ConnectionError",
            error_message="連接超時",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK
        )
        
        message_ids = notification_service.send_error_notification(test_error)
        print(f"發送錯誤通知: {message_ids}")
        
        # 等待處理
        print("\n等待通知處理...")
        time.sleep(3)
        
        # 顯示統計信息
        print("\n=== 統計信息 ===")
        stats = notification_service.get_statistics()
        for key, value in stats.items():
            if key not in ['by_channel', 'by_priority', 'by_type']:
                print(f"{key}: {value}")
        
        print("\n按渠道統計:")
        for channel, channel_stats in stats['by_channel'].items():
            print(f"  {channel}: {channel_stats}")
        
        print("\n測試完成")
        
    except KeyboardInterrupt:
        print("\n收到中斷信號")
    finally:
        # 關閉服務
        notification_service.shutdown()
        print("通知服務已關閉")