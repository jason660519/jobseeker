#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台智能路由配置管理
管理地區平台映射、路由規則和系統配置

Author: JobSpy Team
Date: 2025-01-27
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum


class ConfigLevel(Enum):
    """配置級別"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PlatformConfig:
    """平台配置"""
    name: str
    enabled: bool = True
    max_concurrent_requests: int = 5
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 2
    rate_limit_per_minute: int = 60
    priority: int = 1  # 1-5, 1為最高優先級
    health_check_interval: int = 60
    max_failure_threshold: int = 5
    recovery_time_minutes: int = 10
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy_settings: Optional[Dict[str, Any]] = None
    authentication: Optional[Dict[str, Any]] = None


@dataclass
class RegionConfig:
    """地區配置"""
    name: str
    display_name: str
    primary_platforms: List[str]
    fallback_platforms: List[str] = field(default_factory=list)
    timezone: str = "UTC"
    language: str = "en"
    currency: str = "USD"
    location_keywords: List[str] = field(default_factory=list)
    custom_search_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """調度器配置"""
    max_concurrent_jobs: int = 20
    max_queue_size: int = 1000
    job_timeout_minutes: int = 30
    cleanup_interval_minutes: int = 60
    retry_failed_jobs: bool = True
    max_retry_attempts: int = 3
    retry_delay_minutes: int = 5
    enable_job_persistence: bool = True
    enable_metrics: bool = True
    metrics_retention_days: int = 7


@dataclass
class SyncConfig:
    """同步配置"""
    sync_interval_seconds: int = 10
    event_retention_hours: int = 24
    max_event_batch_size: int = 100
    enable_real_time_sync: bool = True
    enable_event_persistence: bool = True
    health_check_interval_seconds: int = 30
    platform_timeout_seconds: int = 60
    max_sync_retries: int = 3


@dataclass
class IntegrityConfig:
    """完整性檢查配置"""
    default_validation_level: str = "standard"
    enable_auto_validation: bool = True
    validation_timeout_seconds: int = 120
    min_success_rate_threshold: float = 0.8
    max_error_rate_threshold: float = 0.2
    data_consistency_threshold: float = 0.9
    enable_quality_scoring: bool = True
    quality_score_weights: Dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.3,
        "accuracy": 0.3,
        "consistency": 0.2,
        "freshness": 0.2
    })


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    max_connections: int = 50
    connection_pool_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    log_level: str = "info"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    request_timeout: int = 300
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    enable_docs: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


class MultiPlatformConfig:
    """多平台配置管理器"""
    
    def __init__(self, config_level: ConfigLevel = ConfigLevel.DEVELOPMENT):
        """初始化配置管理器"""
        self.config_level = config_level
        self.logger = logging.getLogger(__name__)
        
        # 配置文件路徑
        self.config_dir = Path(__file__).parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # 初始化配置
        self._initialize_default_configs()
        
        # 加載配置文件
        self._load_configs()
    
    def _initialize_default_configs(self):
        """初始化默認配置"""
        
        # 平台配置
        self.platforms = {
            "linkedin": PlatformConfig(
                name="linkedin",
                enabled=True,
                max_concurrent_requests=3,
                timeout_seconds=45,
                retry_attempts=3,
                rate_limit_per_minute=30,
                priority=1
            ),
            "indeed": PlatformConfig(
                name="indeed",
                enabled=True,
                max_concurrent_requests=5,
                timeout_seconds=30,
                retry_attempts=2,
                rate_limit_per_minute=60,
                priority=2
            ),
            "google": PlatformConfig(
                name="google",
                enabled=True,
                max_concurrent_requests=4,
                timeout_seconds=35,
                retry_attempts=3,
                rate_limit_per_minute=45,
                priority=2
            ),
            "seek": PlatformConfig(
                name="seek",
                enabled=True,
                max_concurrent_requests=3,
                timeout_seconds=40,
                retry_attempts=3,
                rate_limit_per_minute=40,
                priority=1
            ),
            "job_bank_1111": PlatformConfig(
                name="job_bank_1111",
                enabled=True,
                max_concurrent_requests=4,
                timeout_seconds=30,
                retry_attempts=2,
                rate_limit_per_minute=50,
                priority=1
            ),
            "job_bank_104": PlatformConfig(
                name="job_bank_104",
                enabled=True,
                max_concurrent_requests=4,
                timeout_seconds=30,
                retry_attempts=2,
                rate_limit_per_minute=50,
                priority=1
            )
        }
        
        # 地區配置
        self.regions = {
            "us": RegionConfig(
                name="us",
                display_name="美國",
                primary_platforms=["linkedin", "indeed", "google"],
                fallback_platforms=["glassdoor"],
                timezone="America/New_York",
                language="en",
                currency="USD",
                location_keywords=["united states", "usa", "america", "new york", "california", "texas"]
            ),
            "taiwan": RegionConfig(
                name="taiwan",
                display_name="台灣",
                primary_platforms=["job_bank_1111", "job_bank_104"],
                fallback_platforms=["linkedin"],
                timezone="Asia/Taipei",
                language="zh-TW",
                currency="TWD",
                location_keywords=["taiwan", "taipei", "taichung", "kaohsiung", "台灣", "台北", "台中", "高雄"]
            ),
            "australia": RegionConfig(
                name="australia",
                display_name="澳洲",
                primary_platforms=["seek", "linkedin"],
                fallback_platforms=["indeed"],
                timezone="Australia/Sydney",
                language="en",
                currency="AUD",
                location_keywords=["australia", "sydney", "melbourne", "brisbane", "perth"]
            ),
            "global": RegionConfig(
                name="global",
                display_name="全球",
                primary_platforms=["linkedin", "indeed", "google"],
                fallback_platforms=[],
                timezone="UTC",
                language="en",
                currency="USD",
                location_keywords=["remote", "worldwide", "global"]
            )
        }
        
        # 調度器配置
        self.scheduler = SchedulerConfig(
            max_concurrent_jobs=20 if self.config_level == ConfigLevel.PRODUCTION else 10,
            max_queue_size=1000 if self.config_level == ConfigLevel.PRODUCTION else 100,
            job_timeout_minutes=30,
            cleanup_interval_minutes=60,
            retry_failed_jobs=True,
            max_retry_attempts=3,
            enable_job_persistence=True,
            enable_metrics=True
        )
        
        # 同步配置
        self.sync = SyncConfig(
            sync_interval_seconds=10 if self.config_level == ConfigLevel.PRODUCTION else 5,
            event_retention_hours=24,
            max_event_batch_size=100,
            enable_real_time_sync=True,
            enable_event_persistence=True,
            health_check_interval_seconds=30
        )
        
        # 完整性配置
        self.integrity = IntegrityConfig(
            default_validation_level="standard",
            enable_auto_validation=True,
            validation_timeout_seconds=120,
            min_success_rate_threshold=0.8,
            max_error_rate_threshold=0.2,
            data_consistency_threshold=0.9,
            enable_quality_scoring=True
        )
        
        # Redis配置
        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            max_connections=50 if self.config_level == ConfigLevel.PRODUCTION else 20
        )
        
        # API配置
        self.api = APIConfig(
            host="0.0.0.0",
            port=int(os.getenv("API_PORT", "8000")),
            debug=self.config_level in [ConfigLevel.DEVELOPMENT, ConfigLevel.TESTING],
            reload=self.config_level == ConfigLevel.DEVELOPMENT,
            workers=4 if self.config_level == ConfigLevel.PRODUCTION else 1,
            log_level="info" if self.config_level == ConfigLevel.PRODUCTION else "debug"
        )
    
    def _load_configs(self):
        """從配置文件加載配置"""
        config_file = self.config_dir / f"{self.config_level.value}.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置
                self._update_configs_from_dict(config_data)
                self.logger.info(f"已加載配置文件: {config_file}")
                
            except Exception as e:
                self.logger.error(f"加載配置文件失敗: {e}")
        else:
            # 創建默認配置文件
            self.save_configs()
    
    def _update_configs_from_dict(self, config_data: Dict[str, Any]):
        """從字典更新配置"""
        
        # 更新平台配置
        if "platforms" in config_data:
            for platform_name, platform_data in config_data["platforms"].items():
                if platform_name in self.platforms:
                    # 更新現有平台配置
                    for key, value in platform_data.items():
                        if hasattr(self.platforms[platform_name], key):
                            setattr(self.platforms[platform_name], key, value)
                else:
                    # 創建新平台配置
                    self.platforms[platform_name] = PlatformConfig(**platform_data)
        
        # 更新地區配置
        if "regions" in config_data:
            for region_name, region_data in config_data["regions"].items():
                if region_name in self.regions:
                    # 更新現有地區配置
                    for key, value in region_data.items():
                        if hasattr(self.regions[region_name], key):
                            setattr(self.regions[region_name], key, value)
                else:
                    # 創建新地區配置
                    self.regions[region_name] = RegionConfig(**region_data)
        
        # 更新其他配置
        config_mappings = {
            "scheduler": self.scheduler,
            "sync": self.sync,
            "integrity": self.integrity,
            "redis": self.redis,
            "api": self.api
        }
        
        for config_key, config_obj in config_mappings.items():
            if config_key in config_data:
                for key, value in config_data[config_key].items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def save_configs(self):
        """保存配置到文件"""
        config_file = self.config_dir / f"{self.config_level.value}.json"
        
        try:
            config_data = {
                "platforms": {name: asdict(config) for name, config in self.platforms.items()},
                "regions": {name: asdict(config) for name, config in self.regions.items()},
                "scheduler": asdict(self.scheduler),
                "sync": asdict(self.sync),
                "integrity": asdict(self.integrity),
                "redis": asdict(self.redis),
                "api": asdict(self.api)
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存到: {config_file}")
            
        except Exception as e:
            self.logger.error(f"保存配置文件失敗: {e}")
    
    def get_platform_config(self, platform_name: str) -> Optional[PlatformConfig]:
        """獲取平台配置"""
        return self.platforms.get(platform_name)
    
    def get_region_config(self, region_name: str) -> Optional[RegionConfig]:
        """獲取地區配置"""
        return self.regions.get(region_name)
    
    def get_enabled_platforms(self) -> List[str]:
        """獲取啟用的平台列表"""
        return [name for name, config in self.platforms.items() if config.enabled]
    
    def get_platforms_for_region(self, region_name: str) -> List[str]:
        """獲取地區的平台列表"""
        region_config = self.get_region_config(region_name)
        if not region_config:
            return []
        
        # 返回主要平台和後備平台
        all_platforms = region_config.primary_platforms + region_config.fallback_platforms
        
        # 只返回啟用的平台
        enabled_platforms = self.get_enabled_platforms()
        return [p for p in all_platforms if p in enabled_platforms]
    
    def detect_region_from_location(self, location: str) -> Optional[str]:
        """從位置檢測地區"""
        location_lower = location.lower()
        
        for region_name, region_config in self.regions.items():
            for keyword in region_config.location_keywords:
                if keyword.lower() in location_lower:
                    return region_name
        
        return None
    
    def get_redis_url(self) -> str:
        """獲取Redis連接URL"""
        if self.redis.password:
            return f"redis://:{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"
        else:
            return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    def validate_config(self) -> List[str]:
        """驗證配置"""
        errors = []
        
        # 檢查平台配置
        for platform_name, platform_config in self.platforms.items():
            if platform_config.max_concurrent_requests <= 0:
                errors.append(f"平台 {platform_name} 的最大併發請求數必須大於0")
            
            if platform_config.timeout_seconds <= 0:
                errors.append(f"平台 {platform_name} 的超時時間必須大於0")
        
        # 檢查地區配置
        for region_name, region_config in self.regions.items():
            if not region_config.primary_platforms:
                errors.append(f"地區 {region_name} 必須至少有一個主要平台")
            
            # 檢查平台是否存在
            for platform in region_config.primary_platforms + region_config.fallback_platforms:
                if platform not in self.platforms:
                    errors.append(f"地區 {region_name} 引用了不存在的平台: {platform}")
        
        # 檢查調度器配置
        if self.scheduler.max_concurrent_jobs <= 0:
            errors.append("調度器最大併發任務數必須大於0")
        
        if self.scheduler.max_queue_size <= 0:
            errors.append("調度器最大隊列大小必須大於0")
        
        return errors
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MultiPlatformConfig(level={self.config_level.value}, platforms={len(self.platforms)}, regions={len(self.regions)})"


# 全局配置實例
_config_level = ConfigLevel(os.getenv("CONFIG_LEVEL", "development"))
config = MultiPlatformConfig(_config_level)


# 便捷函數
def get_config() -> MultiPlatformConfig:
    """獲取全局配置實例"""
    return config


def get_platform_config(platform_name: str) -> Optional[PlatformConfig]:
    """獲取平台配置"""
    return config.get_platform_config(platform_name)


def get_region_config(region_name: str) -> Optional[RegionConfig]:
    """獲取地區配置"""
    return config.get_region_config(region_name)


def get_platforms_for_region(region_name: str) -> List[str]:
    """獲取地區的平台列表"""
    return config.get_platforms_for_region(region_name)


def detect_region_from_location(location: str) -> Optional[str]:
    """從位置檢測地區"""
    return config.detect_region_from_location(location)


if __name__ == "__main__":
    # 測試配置
    print(f"配置級別: {config.config_level.value}")
    print(f"啟用的平台: {config.get_enabled_platforms()}")
    print(f"美國地區平台: {config.get_platforms_for_region('us')}")
    print(f"台灣地區平台: {config.get_platforms_for_region('taiwan')}")
    
    # 驗證配置
    errors = config.validate_config()
    if errors:
        print("配置錯誤:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置驗證通過")
    
    # 保存配置
    config.save_configs()