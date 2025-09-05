#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 自動切換管理器
實現多 LLM 提供商之間的自動切換，包含錯誤偵測機制和無縫切換功能

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import random

from .llm_config import LLMProvider, LLMConfig
from .llm_client import create_llm_client, LLMResponse


class ErrorType(Enum):
    """錯誤類型枚舉"""
    QUOTA_EXCEEDED = "quota_exceeded"  # 配額超出
    RATE_LIMIT = "rate_limit"  # 速率限制
    AUTHENTICATION = "authentication"  # 認證錯誤
    NETWORK_ERROR = "network_error"  # 網路錯誤
    TIMEOUT = "timeout"  # 超時
    INVALID_REQUEST = "invalid_request"  # 無效請求
    SERVER_ERROR = "server_error"  # 伺服器錯誤
    UNKNOWN = "unknown"  # 未知錯誤


@dataclass
class ProviderStatus:
    """提供商狀態"""
    provider: LLMProvider
    is_available: bool = True
    last_error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    error_count: int = 0
    last_success_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        # 如果連續失敗超過 3 次，認為不健康
        if self.consecutive_failures >= 3:
            return False
        
        # 如果成功率低於 50%，認為不健康
        if self.success_rate < 0.5 and self.total_requests >= 5:
            return False
        
        return self.is_available


@dataclass
class SwitchEvent:
    """切換事件記錄"""
    timestamp: datetime
    from_provider: LLMProvider
    to_provider: LLMProvider
    reason: str
    error_type: Optional[ErrorType] = None


class LLMAutoSwitcher:
    """LLM 自動切換管理器"""
    
    def __init__(self, 
                 config_manager,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 health_check_interval: int = 300,  # 5分鐘
                 enable_fallback: bool = True):
        """
        初始化自動切換管理器
        
        Args:
            config_manager: LLM配置管理器
            max_retries: 最大重試次數
            retry_delay: 重試延遲（秒）
            health_check_interval: 健康檢查間隔（秒）
            enable_fallback: 是否啟用回退機制
        """
        self.config_manager = config_manager
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.health_check_interval = health_check_interval
        self.enable_fallback = enable_fallback
        
        # 日誌記錄器
        self.logger = logging.getLogger(__name__)
        
        # 初始化提供商狀態
        self.provider_status: Dict[LLMProvider, ProviderStatus] = {}
        self._init_provider_status()
        
        # 切換事件記錄
        self.switch_events: List[SwitchEvent] = []
        
        # 當前提供商
        self.current_provider = self.config_manager.current_provider
        
        # 最後健康檢查時間
        self.last_health_check = datetime.now()
        
        self.logger.info(f"LLM自動切換管理器初始化完成，當前提供商: {self.current_provider.value}")
    
    def _init_provider_status(self):
        """初始化提供商狀態"""
        for provider in LLMProvider:
            config = self.config_manager.get_config(provider)
            if config and config.is_valid():
                self.provider_status[provider] = ProviderStatus(
                    provider=provider,
                    is_available=True,
                    last_success_time=datetime.now()
                )
                self.logger.info(f"提供商 {provider.value} 已初始化")
            else:
                self.logger.warning(f"提供商 {provider.value} 配置無效，跳過初始化")
    
    def _classify_error(self, error_message: str) -> ErrorType:
        """分類錯誤類型"""
        error_lower = error_message.lower()
        
        # 配額相關錯誤
        if any(keyword in error_lower for keyword in [
            'quota', 'insufficient_quota', 'billing', 'credits', 'usage limit'
        ]):
            return ErrorType.QUOTA_EXCEEDED
        
        # 速率限制錯誤
        if any(keyword in error_lower for keyword in [
            'rate limit', 'too many requests', 'throttle', 'rate_limit_exceeded'
        ]):
            return ErrorType.RATE_LIMIT
        
        # 認證錯誤
        if any(keyword in error_lower for keyword in [
            'authentication', 'unauthorized', 'invalid api key', 'api_key'
        ]):
            return ErrorType.AUTHENTICATION
        
        # 網路錯誤
        if any(keyword in error_lower for keyword in [
            'connection', 'network', 'timeout', 'dns', 'unreachable'
        ]):
            return ErrorType.NETWORK_ERROR
        
        # 超時錯誤
        if any(keyword in error_lower for keyword in [
            'timeout', 'timed out', 'deadline exceeded'
        ]):
            return ErrorType.TIMEOUT
        
        # 無效請求
        if any(keyword in error_lower for keyword in [
            'invalid request', 'bad request', 'validation error'
        ]):
            return ErrorType.INVALID_REQUEST
        
        # 伺服器錯誤
        if any(keyword in error_lower for keyword in [
            'server error', 'internal error', '500', '502', '503', '504'
        ]):
            return ErrorType.SERVER_ERROR
        
        return ErrorType.UNKNOWN
    
    def _should_switch_provider(self, error_type: ErrorType, provider: LLMProvider) -> bool:
        """判斷是否應該切換提供商"""
        status = self.provider_status.get(provider)
        if not status:
            return True
        
        # 配額超出或認證錯誤，立即切換
        if error_type in [ErrorType.QUOTA_EXCEEDED, ErrorType.AUTHENTICATION]:
            return True
        
        # 連續失敗超過閾值，切換
        if status.consecutive_failures >= 2:
            return True
        
        # 速率限制，暫時切換
        if error_type == ErrorType.RATE_LIMIT:
            return True
        
        return False
    
    def _get_next_provider(self, exclude_providers: List[LLMProvider] = None) -> Optional[LLMProvider]:
        """獲取下一個可用的提供商"""
        if exclude_providers is None:
            exclude_providers = []
        
        # 獲取所有健康的提供商
        healthy_providers = [
            provider for provider, status in self.provider_status.items()
            if status.is_healthy and provider not in exclude_providers
        ]
        
        if not healthy_providers:
            self.logger.warning("沒有健康的提供商可用")
            return None
        
        # 按成功率和響應時間排序
        healthy_providers.sort(
            key=lambda p: (
                self.provider_status[p].success_rate,
                -self.provider_status[p].average_response_time
            ),
            reverse=True
        )
        
        return healthy_providers[0]
    
    def _update_provider_status(self, provider: LLMProvider, success: bool, 
                              response_time: float = 0.0, error_message: str = None):
        """更新提供商狀態"""
        if provider not in self.provider_status:
            self.provider_status[provider] = ProviderStatus(provider=provider)
        
        status = self.provider_status[provider]
        status.total_requests += 1
        
        if success:
            status.successful_requests += 1
            status.last_success_time = datetime.now()
            status.consecutive_failures = 0
            status.is_available = True
            
            # 更新平均響應時間
            if status.average_response_time == 0:
                status.average_response_time = response_time
            else:
                status.average_response_time = (
                    status.average_response_time * 0.8 + response_time * 0.2
                )
        else:
            status.error_count += 1
            status.consecutive_failures += 1
            status.last_error_time = datetime.now()
            status.last_error = error_message
            
            if error_message:
                status.error_type = self._classify_error(error_message)
                
                # 某些錯誤類型標記為不可用
                if status.error_type in [ErrorType.QUOTA_EXCEEDED, ErrorType.AUTHENTICATION]:
                    status.is_available = False
    
    def _record_switch_event(self, from_provider: LLMProvider, to_provider: LLMProvider, 
                           reason: str, error_type: ErrorType = None):
        """記錄切換事件"""
        event = SwitchEvent(
            timestamp=datetime.now(),
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            error_type=error_type
        )
        self.switch_events.append(event)
        
        # 保留最近100個事件
        if len(self.switch_events) > 100:
            self.switch_events = self.switch_events[-100:]
        
        self.logger.info(f"LLM提供商切換: {from_provider.value} -> {to_provider.value}, 原因: {reason}")
    
    def call_with_auto_switch(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """帶自動切換的LLM調用"""
        start_time = time.time()
        attempted_providers = []
        last_error = None
        
        # 執行健康檢查
        self._perform_health_check_if_needed()
        
        for attempt in range(self.max_retries + 1):
            try:
                # 獲取當前提供商
                current_provider = self.current_provider
                
                # 如果當前提供商已嘗試過且失敗，選擇下一個
                if current_provider in attempted_providers:
                    next_provider = self._get_next_provider(exclude_providers=attempted_providers)
                    if next_provider:
                        old_provider = self.current_provider
                        self.current_provider = next_provider
                        self._record_switch_event(
                            from_provider=old_provider,
                            to_provider=next_provider,
                            reason=f"重試第{attempt}次，切換到備用提供商"
                        )
                        current_provider = next_provider
                    else:
                        self.logger.error("沒有可用的提供商進行重試")
                        break
                
                attempted_providers.append(current_provider)
                
                # 獲取配置並創建客戶端
                config = self.config_manager.get_config(current_provider)
                if not config or not config.is_valid():
                    self.logger.warning(f"提供商 {current_provider.value} 配置無效")
                    continue
                
                client = create_llm_client(config)
                if not client:
                    self.logger.warning(f"無法創建 {current_provider.value} 客戶端")
                    continue
                
                # 調用LLM
                self.logger.info(f"使用提供商 {current_provider.value} 進行LLM調用")
                response = client.call(messages, **kwargs)
                
                if response.success:
                    # 更新成功狀態
                    self._update_provider_status(
                        current_provider, 
                        success=True, 
                        response_time=response.response_time
                    )
                    
                    total_time = time.time() - start_time
                    self.logger.info(
                        f"LLM調用成功，提供商: {current_provider.value}, "
                        f"響應時間: {response.response_time:.2f}s, "
                        f"總時間: {total_time:.2f}s"
                    )
                    
                    return response
                else:
                    # 處理失敗情況
                    error_type = self._classify_error(response.error_message or "")
                    self._update_provider_status(
                        current_provider, 
                        success=False, 
                        error_message=response.error_message
                    )
                    
                    last_error = response.error_message
                    
                    # 判斷是否需要切換提供商
                    if self._should_switch_provider(error_type, current_provider):
                        next_provider = self._get_next_provider(exclude_providers=attempted_providers)
                        if next_provider:
                            old_provider = self.current_provider
                            self.current_provider = next_provider
                            self._record_switch_event(
                                from_provider=old_provider,
                                to_provider=next_provider,
                                reason=f"錯誤自動切換: {response.error_message}",
                                error_type=error_type
                            )
                            
                            # 如果是速率限制，等待一段時間
                            if error_type == ErrorType.RATE_LIMIT:
                                time.sleep(self.retry_delay * 2)
                        else:
                            self.logger.error("沒有可用的備用提供商")
                    
                    # 等待重試
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * (attempt + 1))
            
            except Exception as e:
                self.logger.error(f"LLM調用異常: {e}")
                last_error = str(e)
                
                # 更新失敗狀態
                if self.current_provider in self.provider_status:
                    self._update_provider_status(
                        self.current_provider, 
                        success=False, 
                        error_message=str(e)
                    )
                
                # 等待重試
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        # 所有重試都失敗了
        total_time = time.time() - start_time
        self.logger.error(
            f"LLM調用完全失敗，嘗試了 {len(attempted_providers)} 個提供商，"
            f"總時間: {total_time:.2f}s，最後錯誤: {last_error}"
        )
        
        return LLMResponse(
            content="",
            usage={},
            model="unknown",
            provider=self.current_provider,
            response_time=total_time,
            success=False,
            error_message=f"所有LLM提供商都失敗了。最後錯誤: {last_error}"
        )
    
    def _perform_health_check_if_needed(self):
        """如果需要，執行健康檢查"""
        now = datetime.now()
        if (now - self.last_health_check).seconds >= self.health_check_interval:
            self._perform_health_check()
            self.last_health_check = now
    
    def _perform_health_check(self):
        """執行健康檢查"""
        self.logger.info("執行LLM提供商健康檢查")
        
        test_messages = [
            {"role": "user", "content": "Hello, this is a health check. Please respond with 'OK'."}
        ]
        
        for provider in list(self.provider_status.keys()):
            try:
                config = self.config_manager.get_config(provider)
                if not config or not config.is_valid():
                    continue
                
                client = create_llm_client(config)
                if not client:
                    continue
                
                # 簡單的健康檢查調用
                response = client.call(test_messages, max_tokens=10, temperature=0)
                
                if response.success:
                    self._update_provider_status(provider, success=True, response_time=response.response_time)
                    self.logger.debug(f"提供商 {provider.value} 健康檢查通過")
                else:
                    self._update_provider_status(provider, success=False, error_message=response.error_message)
                    self.logger.warning(f"提供商 {provider.value} 健康檢查失敗: {response.error_message}")
            
            except Exception as e:
                self._update_provider_status(provider, success=False, error_message=str(e))
                self.logger.warning(f"提供商 {provider.value} 健康檢查異常: {e}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """獲取狀態報告"""
        return {
            "current_provider": self.current_provider.value,
            "provider_status": {
                provider.value: {
                    "is_available": status.is_available,
                    "is_healthy": status.is_healthy,
                    "success_rate": status.success_rate,
                    "total_requests": status.total_requests,
                    "consecutive_failures": status.consecutive_failures,
                    "average_response_time": status.average_response_time,
                    "last_error": status.last_error,
                    "last_success_time": status.last_success_time.isoformat() if status.last_success_time else None,
                    "last_error_time": status.last_error_time.isoformat() if status.last_error_time else None
                }
                for provider, status in self.provider_status.items()
            },
            "recent_switches": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "from_provider": event.from_provider.value,
                    "to_provider": event.to_provider.value,
                    "reason": event.reason,
                    "error_type": event.error_type.value if event.error_type else None
                }
                for event in self.switch_events[-10:]  # 最近10個切換事件
            ]
        }
    
    def get_available_providers(self) -> List[str]:
        """
        獲取可用的LLM提供商列表
        
        Returns:
            可用提供商名稱列表
        """
        available = []
        for provider, status in self.provider_status.items():
            if status.is_healthy:
                available.append(provider.value)
        return available
    
    def manual_switch(self, provider_name: str) -> bool:
        """
        手動切換到指定的LLM提供商
        
        Args:
            provider_name: 提供商名稱
            
        Returns:
            切換是否成功
        """
        try:
            # 查找對應的提供商枚舉
            target_provider = None
            for provider in self.provider_status.keys():
                if provider.value == provider_name:
                    target_provider = provider
                    break
            
            if not target_provider:
                self.logger.error(f"未找到提供商: {provider_name}")
                return False
            
            # 檢查提供商是否可用
            if not self.provider_status[target_provider].is_healthy:
                self.logger.warning(f"提供商 {provider_name} 當前不健康，嘗試強制切換")
            
            # 執行切換
            self.force_switch_provider(target_provider, "手動切換")
            self.logger.info(f"手動切換到提供商: {provider_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"手動切換失敗: {e}")
            return False
    
    def force_switch_provider(self, target_provider: LLMProvider, reason: str = "手動切換"):
        """強制切換提供商"""
        if target_provider not in self.provider_status:
            raise ValueError(f"提供商 {target_provider.value} 不可用")
        
        old_provider = self.current_provider
        self.current_provider = target_provider
        
        self._record_switch_event(
            from_provider=old_provider,
            to_provider=target_provider,
            reason=reason
        )
        
        self.logger.info(f"手動切換LLM提供商: {old_provider.value} -> {target_provider.value}")
    
    def reset_provider_status(self, provider: LLMProvider):
        """重置提供商狀態"""
        if provider in self.provider_status:
            self.provider_status[provider] = ProviderStatus(
                provider=provider,
                is_available=True,
                last_success_time=datetime.now()
            )
            self.logger.info(f"已重置提供商 {provider.value} 的狀態")