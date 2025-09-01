#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 測試配置

這個檔案包含了 JobSpy 測試的配置設定，包括測試環境變數、
測試參數、Mock 配置和測試資料路徑等。

作者: JobSpy Team
日期: 2024
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


# ==================== 測試環境配置 ====================

class TestEnvironment(Enum):
    """測試環境類型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    NETWORK = "network"
    CI = "ci"
    LOCAL = "local"


@dataclass
class TestConfig:
    """測試配置類別"""
    
    # 基本配置
    environment: TestEnvironment = TestEnvironment.LOCAL
    debug_mode: bool = False
    verbose_logging: bool = False
    
    # 超時配置
    default_timeout: float = 30.0
    network_timeout: float = 60.0
    performance_timeout: float = 300.0
    
    # 重試配置
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 並發配置
    max_concurrent_requests: int = 5
    max_workers: int = 4
    
    # 快取配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_size: int = 100
    
    # 效能配置
    performance_baseline: bool = False
    memory_limit_mb: float = 500.0
    cpu_limit_percent: float = 80.0
    
    # 網路配置
    network_tests_enabled: bool = False
    rate_limit_delay: float = 1.0
    user_agent: str = "JobSpy-Test/1.0"
    
    # 資料配置
    test_data_dir: Optional[Path] = None
    temp_dir: Optional[Path] = None
    cleanup_temp_files: bool = True
    
    # Mock 配置
    mock_network_requests: bool = True
    mock_file_operations: bool = False
    mock_database_operations: bool = True
    
    # 報告配置
    generate_html_report: bool = False
    generate_junit_xml: bool = False
    generate_coverage_report: bool = False
    
    def __post_init__(self):
        """初始化後處理"""
        if self.test_data_dir is None:
            self.test_data_dir = Path(__file__).parent / "fixtures"
        
        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "jobspy_tests"
        
        # 確保目錄存在
        self.test_data_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
    
    @classmethod
    def from_environment(cls) -> 'TestConfig':
        """從環境變數創建配置"""
        env_type = os.getenv('JOBSPY_TEST_ENV', 'local')
        
        try:
            environment = TestEnvironment(env_type)
        except ValueError:
            environment = TestEnvironment.LOCAL
        
        return cls(
            environment=environment,
            debug_mode=os.getenv('JOBSPY_DEBUG', 'false').lower() == 'true',
            verbose_logging=os.getenv('JOBSPY_VERBOSE', 'false').lower() == 'true',
            default_timeout=float(os.getenv('JOBSPY_TIMEOUT', '30.0')),
            network_timeout=float(os.getenv('JOBSPY_NETWORK_TIMEOUT', '60.0')),
            max_retries=int(os.getenv('JOBSPY_MAX_RETRIES', '3')),
            max_concurrent_requests=int(os.getenv('JOBSPY_MAX_CONCURRENT', '5')),
            cache_enabled=os.getenv('JOBSPY_CACHE_ENABLED', 'true').lower() == 'true',
            network_tests_enabled=os.getenv('JOBSPY_NETWORK_TESTS', 'false').lower() == 'true',
            mock_network_requests=os.getenv('JOBSPY_MOCK_NETWORK', 'true').lower() == 'true',
            generate_html_report=os.getenv('JOBSPY_HTML_REPORT', 'false').lower() == 'true',
            generate_junit_xml=os.getenv('JOBSPY_JUNIT_XML', 'false').lower() == 'true',
            generate_coverage_report=os.getenv('JOBSPY_COVERAGE', 'false').lower() == 'true'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'environment': self.environment.value,
            'debug_mode': self.debug_mode,
            'verbose_logging': self.verbose_logging,
            'default_timeout': self.default_timeout,
            'network_timeout': self.network_timeout,
            'performance_timeout': self.performance_timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'max_concurrent_requests': self.max_concurrent_requests,
            'max_workers': self.max_workers,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'cache_size': self.cache_size,
            'performance_baseline': self.performance_baseline,
            'memory_limit_mb': self.memory_limit_mb,
            'cpu_limit_percent': self.cpu_limit_percent,
            'network_tests_enabled': self.network_tests_enabled,
            'rate_limit_delay': self.rate_limit_delay,
            'user_agent': self.user_agent,
            'test_data_dir': str(self.test_data_dir),
            'temp_dir': str(self.temp_dir),
            'cleanup_temp_files': self.cleanup_temp_files,
            'mock_network_requests': self.mock_network_requests,
            'mock_file_operations': self.mock_file_operations,
            'mock_database_operations': self.mock_database_operations,
            'generate_html_report': self.generate_html_report,
            'generate_junit_xml': self.generate_junit_xml,
            'generate_coverage_report': self.generate_coverage_report
        }


# ==================== 預定義配置 ====================

# 本地開發配置
LOCAL_CONFIG = TestConfig(
    environment=TestEnvironment.LOCAL,
    debug_mode=True,
    verbose_logging=True,
    default_timeout=30.0,
    max_retries=2,
    cache_enabled=True,
    mock_network_requests=True,
    generate_html_report=True
)

# CI/CD 配置
CI_CONFIG = TestConfig(
    environment=TestEnvironment.CI,
    debug_mode=False,
    verbose_logging=False,
    default_timeout=60.0,
    max_retries=3,
    cache_enabled=False,
    mock_network_requests=True,
    generate_junit_xml=True,
    generate_coverage_report=True
)

# 效能測試配置
PERFORMANCE_CONFIG = TestConfig(
    environment=TestEnvironment.PERFORMANCE,
    debug_mode=False,
    verbose_logging=False,
    performance_timeout=600.0,
    max_concurrent_requests=10,
    cache_enabled=True,
    performance_baseline=True,
    memory_limit_mb=1000.0,
    mock_network_requests=False
)

# 網路測試配置
NETWORK_CONFIG = TestConfig(
    environment=TestEnvironment.NETWORK,
    debug_mode=False,
    verbose_logging=True,
    network_timeout=120.0,
    max_retries=5,
    network_tests_enabled=True,
    mock_network_requests=False,
    rate_limit_delay=2.0
)

# 整合測試配置
INTEGRATION_CONFIG = TestConfig(
    environment=TestEnvironment.INTEGRATION,
    debug_mode=False,
    verbose_logging=True,
    default_timeout=90.0,
    max_concurrent_requests=3,
    cache_enabled=True,
    mock_network_requests=False
)


# ==================== 測試資料配置 ====================

TEST_SITES = [
    "indeed",
    "linkedin",
    "glassdoor",
    "seek",
    "ziprecruiter"
]

TEST_SEARCH_TERMS = [
    "python developer",
    "data scientist",
    "software engineer",
    "web developer",
    "machine learning engineer"
]

TEST_LOCATIONS = [
    "Sydney, NSW",
    "Melbourne, VIC",
    "Brisbane, QLD",
    "Perth, WA",
    "Adelaide, SA"
]

TEST_JOB_TYPES = [
    "fulltime",
    "parttime",
    "contract",
    "temporary",
    "internship"
]


# ==================== Mock 配置 ====================

MOCK_RESPONSE_DELAYS = {
    "fast": 0.1,
    "normal": 0.5,
    "slow": 2.0,
    "timeout": 10.0
}

MOCK_ERROR_RATES = {
    "none": 0.0,
    "low": 0.05,
    "medium": 0.15,
    "high": 0.30
}

MOCK_RESPONSE_SIZES = {
    "small": 5,
    "medium": 20,
    "large": 50,
    "xlarge": 100
}


# ==================== 效能基準 ====================

PERFORMANCE_BENCHMARKS = {
    "single_request": {
        "max_time": 10.0,
        "max_memory": 50.0
    },
    "small_batch": {
        "max_time": 30.0,
        "max_memory": 100.0,
        "requests": 10
    },
    "medium_batch": {
        "max_time": 60.0,
        "max_memory": 200.0,
        "requests": 25
    },
    "large_batch": {
        "max_time": 120.0,
        "max_memory": 400.0,
        "requests": 50
    },
    "stress_test": {
        "max_time": 300.0,
        "max_memory": 800.0,
        "requests": 100,
        "concurrent": 10
    }
}


# ==================== 測試標記配置 ====================

TEST_MARKERS = {
    "unit": "單元測試",
    "integration": "整合測試",
    "performance": "效能測試",
    "slow": "慢速測試（執行時間 > 10秒）",
    "fast": "快速測試（執行時間 < 5秒）",
    "requires_network": "需要網路連接的測試",
    "requires_auth": "需要認證的測試",
    "flaky": "可能不穩定的測試",
    "skip_ci": "在 CI 環境中跳過的測試",
    "smoke": "冒煙測試",
    "regression": "回歸測試",
    "security": "安全測試",
    "compatibility": "相容性測試"
}


# ==================== 測試環境檢查 ====================

def check_test_environment() -> Dict[str, bool]:
    """檢查測試環境是否準備就緒"""
    checks = {}
    
    # 檢查 Python 版本
    import sys
    checks['python_version'] = sys.version_info >= (3, 8)
    
    # 檢查必要套件
    required_packages = ['pytest', 'requests', 'pandas', 'beautifulsoup4']
    for package in required_packages:
        try:
            __import__(package)
            checks[f'package_{package}'] = True
        except ImportError:
            checks[f'package_{package}'] = False
    
    # 檢查網路連接
    try:
        import requests
        response = requests.get('https://www.google.com', timeout=5)
        checks['network_connection'] = response.status_code == 200
    except:
        checks['network_connection'] = False
    
    # 檢查磁碟空間
    import shutil
    free_space_gb = shutil.disk_usage('.').free / (1024**3)
    checks['disk_space'] = free_space_gb > 1.0  # 至少 1GB 可用空間
    
    # 檢查記憶體
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        checks['memory'] = available_memory_gb > 1.0  # 至少 1GB 可用記憶體
    except ImportError:
        checks['memory'] = True  # 如果沒有 psutil，假設記憶體足夠
    
    return checks


def get_test_config() -> TestConfig:
    """獲取當前測試配置"""
    # 優先從環境變數讀取
    config = TestConfig.from_environment()
    
    # 根據環境類型調整配置
    if config.environment == TestEnvironment.CI:
        return CI_CONFIG
    elif config.environment == TestEnvironment.PERFORMANCE:
        return PERFORMANCE_CONFIG
    elif config.environment == TestEnvironment.NETWORK:
        return NETWORK_CONFIG
    elif config.environment == TestEnvironment.INTEGRATION:
        return INTEGRATION_CONFIG
    else:
        return LOCAL_CONFIG


def setup_test_environment(config: TestConfig = None) -> None:
    """設置測試環境"""
    if config is None:
        config = get_test_config()
    
    # 設置環境變數
    os.environ['JOBSPY_TEST_MODE'] = 'true'
    os.environ['JOBSPY_LOG_LEVEL'] = 'DEBUG' if config.debug_mode else 'INFO'
    os.environ['JOBSPY_CACHE_ENABLED'] = str(config.cache_enabled).lower()
    os.environ['JOBSPY_MOCK_NETWORK'] = str(config.mock_network_requests).lower()
    
    # 創建必要目錄
    config.test_data_dir.mkdir(exist_ok=True)
    config.temp_dir.mkdir(exist_ok=True)
    
    # 設置日誌
    import logging
    log_level = logging.DEBUG if config.verbose_logging else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cleanup_test_environment(config: TestConfig = None) -> None:
    """清理測試環境"""
    if config is None:
        config = get_test_config()
    
    if config.cleanup_temp_files and config.temp_dir.exists():
        import shutil
        shutil.rmtree(config.temp_dir, ignore_errors=True)
    
    # 清理環境變數
    test_env_vars = [
        'JOBSPY_TEST_MODE',
        'JOBSPY_LOG_LEVEL',
        'JOBSPY_CACHE_ENABLED',
        'JOBSPY_MOCK_NETWORK'
    ]
    
    for var in test_env_vars:
        os.environ.pop(var, None)


# ==================== 全域配置實例 ====================

# 當前測試配置
CURRENT_CONFIG = get_test_config()

# 設置測試環境
setup_test_environment(CURRENT_CONFIG)


# ==================== 導出 ====================

__all__ = [
    'TestEnvironment',
    'TestConfig',
    'LOCAL_CONFIG',
    'CI_CONFIG',
    'PERFORMANCE_CONFIG',
    'NETWORK_CONFIG',
    'INTEGRATION_CONFIG',
    'TEST_SITES',
    'TEST_SEARCH_TERMS',
    'TEST_LOCATIONS',
    'TEST_JOB_TYPES',
    'MOCK_RESPONSE_DELAYS',
    'MOCK_ERROR_RATES',
    'MOCK_RESPONSE_SIZES',
    'PERFORMANCE_BENCHMARKS',
    'TEST_MARKERS',
    'check_test_environment',
    'get_test_config',
    'setup_test_environment',
    'cleanup_test_environment',
    'CURRENT_CONFIG'
]