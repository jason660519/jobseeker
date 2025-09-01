"""jobseeker.jobboard.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of Scrapers' exceptions.
包含統一的錯誤處理機制和網站特定的異常類別。
"""

# 導入統一錯誤處理機制
from jobseeker.error_handling import (
    ScrapingError, NetworkError, RateLimitError, ParsingError, 
    AuthenticationError, TimeoutError, ErrorType
)


# 網站特定異常類別（繼承自統一異常基類）
class LinkedInException(ScrapingError):
    """LinkedIn 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with LinkedIn", 
            error_type=error_type, 
            site="linkedin", 
            original_exception=original_exception
        )


class IndeedException(ScrapingError):
    """Indeed 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Indeed", 
            error_type=error_type, 
            site="indeed", 
            original_exception=original_exception
        )


class ZipRecruiterException(ScrapingError):
    """ZipRecruiter 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with ZipRecruiter", 
            error_type=error_type, 
            site="ziprecruiter", 
            original_exception=original_exception
        )


class GlassdoorException(ScrapingError):
    """Glassdoor 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Glassdoor", 
            error_type=error_type, 
            site="glassdoor", 
            original_exception=original_exception
        )


class GoogleJobsException(ScrapingError):
    """Google Jobs 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Google Jobs", 
            error_type=error_type, 
            site="google", 
            original_exception=original_exception
        )


class BaytException(ScrapingError):
    """Bayt 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Bayt", 
            error_type=error_type, 
            site="bayt", 
            original_exception=original_exception
        )


class NaukriException(ScrapingError):
    """Naukri 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Naukri", 
            error_type=error_type, 
            site="naukri", 
            original_exception=original_exception
        )


class BDJobsException(ScrapingError):
    """BDJobs 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with BDJobs", 
            error_type=error_type, 
            site="bdjobs", 
            original_exception=original_exception
        )


class SeekException(ScrapingError):
    """Seek 特定異常"""
    def __init__(self, message=None, error_type=ErrorType.UNKNOWN_ERROR, original_exception=None):
        super().__init__(
            message or "An error occurred with Seek", 
            error_type=error_type, 
            site="seek", 
            original_exception=original_exception
        )


# 向後相容性：保持舊的異常類別可用
__all__ = [
    # 統一異常類別
    'ScrapingError', 'NetworkError', 'RateLimitError', 'ParsingError', 
    'AuthenticationError', 'TimeoutError', 'ErrorType',
    # 網站特定異常
    'LinkedInException', 'IndeedException', 'ZipRecruiterException', 
    'GlassdoorException', 'GoogleJobsException', 'BaytException', 
    'NaukriException', 'BDJobsException', 'SeekException'
]
