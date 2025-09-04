#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強型ETL配置管理
統一管理視覺爬蟲和傳統爬蟲的整合配置

Author: JobSpy Team
Date: 2025-01-05
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import os
from pathlib import Path


class ScrapingMode(Enum):
    """爬蟲模式枚舉"""
    VISUAL_ONLY = "visual_only"          # 僅視覺爬蟲
    TRADITIONAL_ONLY = "traditional_only"  # 僅傳統爬蟲
    HYBRID = "hybrid"                    # 混合模式
    ADAPTIVE = "adaptive"                # 自適應模式


class DataQualityLevel(Enum):
    """數據質量等級"""
    BASIC = "basic"        # 基本質量
    STANDARD = "standard"  # 標準質量
    HIGH = "high"          # 高質量
    PREMIUM = "premium"    # 頂級質量


class PerformanceMode(Enum):
    """性能模式"""
    SPEED = "speed"        # 速度優先
    BALANCED = "balanced"  # 平衡模式
    QUALITY = "quality"    # 質量優先
    STEALTH = "stealth"    # 隱蔽模式


@dataclass
class VisualScrapingConfig:
    """視覺爬蟲配置"""
    # 瀏覽器設置
    headless: bool = False
    window_size: tuple = (1920, 1080)
    user_agent: Optional[str] = None
    
    # 等待設置
    page_load_timeout: int = 30
    element_wait_timeout: int = 10
    scroll_pause_time: float = 2.0
    
    # 行為模擬
    enable_human_behavior: bool = True
    mouse_movement_delay: tuple = (0.5, 2.0)
    typing_delay: tuple = (0.1, 0.3)
    
    # 截圖設置
    enable_screenshots: bool = True
    screenshot_quality: int = 85
    
    # 反檢測設置
    enable_stealth: bool = True
    rotate_user_agents: bool = True
    enable_proxy_rotation: bool = False
    
    # OCR設置
    enable_ocr: bool = True
    ocr_confidence_threshold: float = 0.8
    ocr_languages: List[str] = field(default_factory=lambda: ['eng'])


@dataclass
class TraditionalScrapingConfig:
    """傳統爬蟲配置"""
    # 請求設置
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 併發設置
    max_concurrent_requests: int = 5
    request_delay: tuple = (1.0, 3.0)
    
    # 會話設置
    enable_session_reuse: bool = True
    session_pool_size: int = 10
    
    # 代理設置
    enable_proxy: bool = False
    proxy_rotation: bool = False
    
    # 緩存設置
    enable_cache: bool = True
    cache_ttl: int = 3600
    
    # 用戶代理設置
    rotate_user_agents: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ETLProcessingConfig:
    """ETL處理配置"""
    # 數據清洗
    enable_data_cleaning: bool = True
    remove_html_tags: bool = True
    normalize_whitespace: bool = True
    
    # 數據驗證
    enable_data_validation: bool = True
    required_fields: List[str] = field(default_factory=lambda: ['title', 'company'])
    
    # 去重設置
    enable_deduplication: bool = True
    dedup_fields: List[str] = field(default_factory=lambda: ['title', 'company', 'location'])
    similarity_threshold: float = 0.85
    
    # 數據豐富
    enable_data_enrichment: bool = True
    extract_salary_info: bool = True
    extract_job_type: bool = True
    extract_experience_level: bool = True
    
    # 質量控制
    min_title_length: int = 3
    max_title_length: int = 200
    min_description_length: int = 50
    
    # 輸出格式
    output_formats: List[str] = field(default_factory=lambda: ['json', 'csv'])
    include_metadata: bool = True
    include_timestamps: bool = True


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 內存管理
    max_memory_usage_mb: int = 2048
    enable_memory_monitoring: bool = True
    
    # 並發控制
    max_concurrent_jobs: int = 3
    max_concurrent_pages: int = 5
    
    # 超時設置
    job_timeout: int = 1800  # 30分鐘
    page_timeout: int = 300   # 5分鐘
    
    # 緩存設置
    enable_result_cache: bool = True
    cache_size_limit_mb: int = 512
    
    # 監控設置
    enable_performance_logging: bool = True
    log_level: str = "INFO"
    
    # 資源限制
    max_cpu_usage_percent: int = 80
    max_disk_usage_mb: int = 1024


@dataclass
class QualityAssuranceConfig:
    """質量保證配置"""
    # 交叉驗證
    enable_cross_validation: bool = True
    min_sources_for_validation: int = 2
    
    # 數據一致性檢查
    enable_consistency_check: bool = True
    consistency_threshold: float = 0.9
    
    # 完整性檢查
    enable_completeness_check: bool = True
    min_completeness_score: float = 0.8
    
    # 準確性檢查
    enable_accuracy_check: bool = True
    accuracy_sampling_rate: float = 0.1
    
    # 時效性檢查
    enable_freshness_check: bool = True
    max_data_age_hours: int = 24
    
    # 質量報告
    generate_quality_report: bool = True
    quality_report_format: str = "json"


@dataclass
class EnhancedETLConfig:
    """增強型ETL主配置"""
    # 基本設置
    project_name: str = "JobSpy Enhanced ETL"
    version: str = "1.0.0"
    
    # 模式設置
    scraping_mode: ScrapingMode = ScrapingMode.HYBRID
    data_quality_level: DataQualityLevel = DataQualityLevel.STANDARD
    performance_mode: PerformanceMode = PerformanceMode.BALANCED
    
    # 路徑設置
    base_output_path: str = "./output"
    logs_path: str = "./logs"
    cache_path: str = "./cache"
    temp_path: str = "./temp"
    
    # 子配置
    visual_config: VisualScrapingConfig = field(default_factory=VisualScrapingConfig)
    traditional_config: TraditionalScrapingConfig = field(default_factory=TraditionalScrapingConfig)
    etl_config: ETLProcessingConfig = field(default_factory=ETLProcessingConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    qa_config: QualityAssuranceConfig = field(default_factory=QualityAssuranceConfig)
    
    # 策略設置
    fallback_strategy: ScrapingMode = ScrapingMode.TRADITIONAL_ONLY
    auto_fallback_enabled: bool = True
    fallback_threshold_seconds: int = 300
    
    # 調試設置
    debug_mode: bool = False
    verbose_logging: bool = False
    save_raw_data: bool = False
    
    def __post_init__(self):
        """初始化後處理"""
        # 創建必要的目錄
        self._create_directories()
        
        # 根據性能模式調整配置
        self._adjust_config_by_performance_mode()
        
        # 根據質量等級調整配置
        self._adjust_config_by_quality_level()
    
    def _create_directories(self):
        """創建必要的目錄"""
        directories = [
            self.base_output_path,
            self.logs_path,
            self.cache_path,
            self.temp_path
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _adjust_config_by_performance_mode(self):
        """根據性能模式調整配置"""
        if self.performance_mode == PerformanceMode.SPEED:
            # 速度優先：減少等待時間，增加併發
            self.visual_config.page_load_timeout = 15
            self.visual_config.element_wait_timeout = 5
            self.traditional_config.max_concurrent_requests = 10
            self.performance_config.max_concurrent_jobs = 5
            
        elif self.performance_mode == PerformanceMode.QUALITY:
            # 質量優先：增加等待時間，減少併發
            self.visual_config.page_load_timeout = 45
            self.visual_config.element_wait_timeout = 15
            self.traditional_config.max_concurrent_requests = 2
            self.performance_config.max_concurrent_jobs = 1
            
        elif self.performance_mode == PerformanceMode.STEALTH:
            # 隱蔽模式：啟用所有反檢測功能
            self.visual_config.enable_stealth = True
            self.visual_config.enable_human_behavior = True
            self.visual_config.mouse_movement_delay = (1.0, 3.0)
            self.traditional_config.request_delay = (2.0, 5.0)
            self.traditional_config.max_concurrent_requests = 1
    
    def _adjust_config_by_quality_level(self):
        """根據質量等級調整配置"""
        if self.data_quality_level == DataQualityLevel.BASIC:
            # 基本質量：關閉一些高級功能
            self.qa_config.enable_cross_validation = False
            self.etl_config.enable_data_enrichment = False
            
        elif self.data_quality_level == DataQualityLevel.HIGH:
            # 高質量：啟用所有質量檢查
            self.qa_config.enable_cross_validation = True
            self.qa_config.enable_consistency_check = True
            self.qa_config.enable_completeness_check = True
            self.etl_config.enable_data_enrichment = True
            
        elif self.data_quality_level == DataQualityLevel.PREMIUM:
            # 頂級質量：最嚴格的質量控制
            self.qa_config.min_completeness_score = 0.95
            self.qa_config.consistency_threshold = 0.95
            self.etl_config.similarity_threshold = 0.95
    
    def get_config_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            'project_name': self.project_name,
            'version': self.version,
            'scraping_mode': self.scraping_mode.value,
            'data_quality_level': self.data_quality_level.value,
            'performance_mode': self.performance_mode.value,
            'visual_scraping_enabled': self.scraping_mode in [ScrapingMode.VISUAL_ONLY, ScrapingMode.HYBRID, ScrapingMode.ADAPTIVE],
            'traditional_scraping_enabled': self.scraping_mode in [ScrapingMode.TRADITIONAL_ONLY, ScrapingMode.HYBRID, ScrapingMode.ADAPTIVE],
            'quality_assurance_enabled': self.qa_config.enable_cross_validation,
            'debug_mode': self.debug_mode
        }
    
    def export_config(self, file_path: str):
        """導出配置到文件"""
        import json
        from dataclasses import asdict
        
        config_dict = asdict(self)
        
        # 處理枚舉類型
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        config_dict = convert_enums(config_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_config(cls, file_path: str) -> 'EnhancedETLConfig':
        """從文件加載配置"""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 處理枚舉類型
        if 'scraping_mode' in config_dict:
            config_dict['scraping_mode'] = ScrapingMode(config_dict['scraping_mode'])
        if 'data_quality_level' in config_dict:
            config_dict['data_quality_level'] = DataQualityLevel(config_dict['data_quality_level'])
        if 'performance_mode' in config_dict:
            config_dict['performance_mode'] = PerformanceMode(config_dict['performance_mode'])
        if 'fallback_strategy' in config_dict:
            config_dict['fallback_strategy'] = ScrapingMode(config_dict['fallback_strategy'])
        
        return cls(**config_dict)


# 預設配置模板
class ConfigTemplates:
    """配置模板類"""
    
    @staticmethod
    def get_speed_optimized_config() -> EnhancedETLConfig:
        """獲取速度優化配置"""
        config = EnhancedETLConfig(
            scraping_mode=ScrapingMode.TRADITIONAL_ONLY,
            data_quality_level=DataQualityLevel.BASIC,
            performance_mode=PerformanceMode.SPEED
        )
        return config
    
    @staticmethod
    def get_quality_optimized_config() -> EnhancedETLConfig:
        """獲取質量優化配置"""
        config = EnhancedETLConfig(
            scraping_mode=ScrapingMode.HYBRID,
            data_quality_level=DataQualityLevel.HIGH,
            performance_mode=PerformanceMode.QUALITY
        )
        return config
    
    @staticmethod
    def get_stealth_config() -> EnhancedETLConfig:
        """獲取隱蔽模式配置"""
        config = EnhancedETLConfig(
            scraping_mode=ScrapingMode.VISUAL_ONLY,
            data_quality_level=DataQualityLevel.STANDARD,
            performance_mode=PerformanceMode.STEALTH
        )
        return config
    
    @staticmethod
    def get_balanced_config() -> EnhancedETLConfig:
        """獲取平衡模式配置"""
        config = EnhancedETLConfig(
            scraping_mode=ScrapingMode.HYBRID,
            data_quality_level=DataQualityLevel.STANDARD,
            performance_mode=PerformanceMode.BALANCED
        )
        return config


# 環境變量配置
def load_config_from_env() -> EnhancedETLConfig:
    """從環境變量加載配置"""
    config = EnhancedETLConfig()
    
    # 基本設置
    if os.getenv('JOBSPY_PROJECT_NAME'):
        config.project_name = os.getenv('JOBSPY_PROJECT_NAME')
    
    if os.getenv('JOBSPY_SCRAPING_MODE'):
        config.scraping_mode = ScrapingMode(os.getenv('JOBSPY_SCRAPING_MODE'))
    
    if os.getenv('JOBSPY_QUALITY_LEVEL'):
        config.data_quality_level = DataQualityLevel(os.getenv('JOBSPY_QUALITY_LEVEL'))
    
    if os.getenv('JOBSPY_PERFORMANCE_MODE'):
        config.performance_mode = PerformanceMode(os.getenv('JOBSPY_PERFORMANCE_MODE'))
    
    # 路徑設置
    if os.getenv('JOBSPY_OUTPUT_PATH'):
        config.base_output_path = os.getenv('JOBSPY_OUTPUT_PATH')
    
    if os.getenv('JOBSPY_LOGS_PATH'):
        config.logs_path = os.getenv('JOBSPY_LOGS_PATH')
    
    # 調試設置
    if os.getenv('JOBSPY_DEBUG_MODE'):
        config.debug_mode = os.getenv('JOBSPY_DEBUG_MODE').lower() == 'true'
    
    if os.getenv('JOBSPY_VERBOSE_LOGGING'):
        config.verbose_logging = os.getenv('JOBSPY_VERBOSE_LOGGING').lower() == 'true'
    
    return config


if __name__ == "__main__":
    # 測試配置
    print("增強型ETL配置測試")
    print("=" * 50)
    
    # 創建默認配置
    config = EnhancedETLConfig()
    print("默認配置摘要:")
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    
    # 測試不同模板
    templates = {
        "速度優化": ConfigTemplates.get_speed_optimized_config(),
        "質量優化": ConfigTemplates.get_quality_optimized_config(),
        "隱蔽模式": ConfigTemplates.get_stealth_config(),
        "平衡模式": ConfigTemplates.get_balanced_config()
    }
    
    for name, template_config in templates.items():
        print(f"\n{name}配置:")
        template_summary = template_config.get_config_summary()
        for key, value in template_summary.items():
            print(f"  {key}: {value}")
    
    print("\n配置測試完成!")