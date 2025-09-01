"""統一錯誤處理模組

此模組提供統一的錯誤處理機制，包括重試裝飾器和自定義異常類別。
"""

from __future__ import annotations

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Type, Optional
from enum import Enum

import requests
from jobspy.util import create_logger


class ErrorType(Enum):
    """錯誤類型枚舉"""
    NETWORK_ERROR = "network_error"
    RATE_LIMIT = "rate_limit"
    PARSING_ERROR = "parsing_error"
    AUTHENTICATION_ERROR = "authentication_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ScrapingError(Exception):
    """爬蟲基礎異常類別"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 site: str = None, original_exception: Exception = None):
        """
        初始化爬蟲異常
        
        Args:
            message: 錯誤訊息
            error_type: 錯誤類型
            site: 發生錯誤的網站
            original_exception: 原始異常
        """
        super().__init__(message)
        self.error_type = error_type
        self.site = site
        self.original_exception = original_exception
        self.timestamp = time.time()


class NetworkError(ScrapingError):
    """網路錯誤異常"""
    
    def __init__(self, message: str, site: str = None, status_code: int = None, 
                 original_exception: Exception = None):
        super().__init__(message, ErrorType.NETWORK_ERROR, site, original_exception)
        self.status_code = status_code


class RateLimitError(ScrapingError):
    """速率限制錯誤異常"""
    
    def __init__(self, message: str, site: str = None, retry_after: int = None,
                 original_exception: Exception = None):
        super().__init__(message, ErrorType.RATE_LIMIT, site, original_exception)
        self.retry_after = retry_after


class ParsingError(ScrapingError):
    """解析錯誤異常"""
    
    def __init__(self, message: str, site: str = None, element: str = None,
                 original_exception: Exception = None):
        super().__init__(message, ErrorType.PARSING_ERROR, site, original_exception)
        self.element = element


class AuthenticationError(ScrapingError):
    """認證錯誤異常"""
    
    def __init__(self, message: str, site: str = None, 
                 original_exception: Exception = None):
        super().__init__(message, ErrorType.AUTHENTICATION_ERROR, site, original_exception)


class TimeoutError(ScrapingError):
    """超時錯誤異常"""
    
    def __init__(self, message: str, site: str = None, timeout_duration: float = None,
                 original_exception: Exception = None):
        super().__init__(message, ErrorType.TIMEOUT_ERROR, site, original_exception)
        self.timeout_duration = timeout_duration


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger_name: str = None
):
    """
    重試裝飾器，支援指數退避和抖動
    
    Args:
        max_retries: 最大重試次數
        backoff_factor: 退避因子
        max_delay: 最大延遲時間（秒）
        jitter: 是否添加隨機抖動
        exceptions: 需要重試的異常類型
        logger_name: 日誌記錄器名稱
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = create_logger(logger_name or func.__name__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"函數 {func.__name__} 在 {max_retries} 次重試後仍然失敗: {str(e)}")
                        raise
                    
                    # 計算延遲時間
                    delay = min(backoff_factor ** attempt, max_delay)
                    
                    # 添加隨機抖動
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函數 {func.__name__} 第 {attempt + 1} 次嘗試失敗: {str(e)}. "
                        f"將在 {delay:.2f} 秒後重試..."
                    )
                    
                    time.sleep(delay)
                except Exception as e:
                    # 對於不在重試列表中的異常，直接拋出
                    logger.error(f"函數 {func.__name__} 發生不可重試的錯誤: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger_name: str = None
):
    """
    非同步重試裝飾器，支援指數退避和抖動
    
    Args:
        max_retries: 最大重試次數
        backoff_factor: 退避因子
        max_delay: 最大延遲時間（秒）
        jitter: 是否添加隨機抖動
        exceptions: 需要重試的異常類型
        logger_name: 日誌記錄器名稱
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            logger = create_logger(logger_name or func.__name__)
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"非同步函數 {func.__name__} 在 {max_retries} 次重試後仍然失敗: {str(e)}")
                        raise
                    
                    # 計算延遲時間
                    delay = min(backoff_factor ** attempt, max_delay)
                    
                    # 添加隨機抖動
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"非同步函數 {func.__name__} 第 {attempt + 1} 次嘗試失敗: {str(e)}. "
                        f"將在 {delay:.2f} 秒後重試..."
                    )
                    
                    await asyncio.sleep(delay)
                except Exception as e:
                    # 對於不在重試列表中的異常，直接拋出
                    logger.error(f"非同步函數 {func.__name__} 發生不可重試的錯誤: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator


class ErrorHandler:
    """
    統一錯誤處理器
    """
    
    def __init__(self, logger_name: str = "ErrorHandler"):
        """
        初始化錯誤處理器
        
        Args:
            logger_name: 日誌記錄器名稱
        """
        self.logger = create_logger(logger_name)
        self.error_counts = {}
    
    def handle_error(self, error: Exception, context: dict = None) -> ScrapingError:
        """
        處理錯誤並轉換為統一的異常類型
        
        Args:
            error: 原始異常
            context: 錯誤上下文資訊
            
        Returns:
            統一的爬蟲異常
        """
        context = context or {}
        site = context.get('site', 'unknown')
        
        # 記錄錯誤統計
        error_key = f"{site}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # 根據異常類型轉換為統一異常
        if isinstance(error, (ConnectionError, requests.exceptions.ConnectionError)):
            return NetworkError(
                f"網路連接錯誤: {str(error)}",
                site=site,
                original_exception=error
            )
        elif isinstance(error, (TimeoutError, requests.exceptions.Timeout)):
            return TimeoutError(
                f"請求超時: {str(error)}",
                site=site,
                original_exception=error
            )
        elif "429" in str(error) or "rate limit" in str(error).lower():
            return RateLimitError(
                f"速率限制: {str(error)}",
                site=site,
                original_exception=error
            )
        elif "401" in str(error) or "403" in str(error) or "unauthorized" in str(error).lower():
            return AuthenticationError(
                f"認證錯誤: {str(error)}",
                site=site,
                original_exception=error
            )
        else:
            return ScrapingError(
                f"未知錯誤: {str(error)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                site=site,
                original_exception=error
            )
    
    def get_error_statistics(self) -> dict:
        """
        獲取錯誤統計資訊
        
        Returns:
            錯誤統計字典
        """
        return self.error_counts.copy()
    
    def reset_statistics(self):
        """
        重置錯誤統計
        """
        self.error_counts.clear()


# 全域錯誤處理器實例
global_error_handler = ErrorHandler("JobSpy.GlobalErrorHandler")


# 常用的重試裝飾器預設配置
network_retry = retry_with_backoff(
    max_retries=3,
    backoff_factor=2.0,
    exceptions=(NetworkError, ConnectionError, requests.exceptions.ConnectionError)
)

rate_limit_retry = retry_with_backoff(
    max_retries=5,
    backoff_factor=3.0,
    max_delay=300.0,
    exceptions=(RateLimitError,)
)

general_retry = retry_with_backoff(
    max_retries=2,
    backoff_factor=1.5,
    exceptions=(ScrapingError,)
)


# 非同步版本
async_network_retry = async_retry_with_backoff(
    max_retries=3,
    backoff_factor=2.0,
    exceptions=(NetworkError, ConnectionError)
)

async_rate_limit_retry = async_retry_with_backoff(
    max_retries=5,
    backoff_factor=3.0,
    max_delay=300.0,
    exceptions=(RateLimitError,)
)

async_general_retry = async_retry_with_backoff(
    max_retries=2,
    backoff_factor=1.5,
    exceptions=(ScrapingError,)
)