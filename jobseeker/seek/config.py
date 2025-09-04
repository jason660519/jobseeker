# -*- coding: utf-8 -*-
"""
Seek爬蟲引擎配置模組
定義爬蟲引擎的各種配置參數、常量和設置選項

Author: JobSpy Team
Date: 2024
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class BrowserConfig:
    """
    瀏覽器配置類
    """
    headless: bool = True
    slow_mo: int = 100  # 毫秒
    timeout: int = 30000  # 毫秒
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # 瀏覽器啟動參數
    browser_args: List[str] = field(default_factory=lambda: [
        '--no-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--disable-default-apps',
        '--disable-extensions'
    ])


@dataclass
class OCRConfig:
    """
    OCR配置類
    """
    enabled: bool = True
    languages: List[str] = field(default_factory=lambda: ['en', 'ch_sim'])
    use_angle_cls: bool = True
    use_gpu: bool = False
    show_log: bool = False
    confidence_threshold: float = 0.7
    
    # OCR處理選項
    process_screenshots: bool = True
    save_ocr_results: bool = True
    ocr_output_format: str = 'json'  # 'json', 'txt', 'both'


@dataclass
class ScrapingConfig:
    """
    爬蟲配置類
    """
    mode: str = "hybrid"  # "traditional", "enhanced", "hybrid"
    max_pages: int = 5
    results_wanted: int = 100
    max_workers: int = 3
    rate_limit_delay: float = 2.0  # 秒
    
    # 重試配置
    max_retries: int = 3
    retry_delay: float = 5.0  # 秒
    
    # 超時配置
    page_load_timeout: int = 30  # 秒
    element_wait_timeout: int = 10  # 秒
    
    # 數據抓取選項
    enable_screenshots: bool = True
    enable_full_page_screenshots: bool = True
    screenshot_quality: int = 90  # 1-100
    
    # 分頁處理
    auto_pagination: bool = True
    pagination_delay: float = 2.0  # 秒
    max_pagination_attempts: int = 10


@dataclass
class ETLConfig:
    """
    ETL處理配置類
    """
    enable_data_validation: bool = True
    enable_deduplication: bool = True
    enable_data_enrichment: bool = True
    
    # 數據質量控制
    min_title_length: int = 2
    min_company_length: int = 2
    min_description_length: int = 10
    
    # 薪資處理
    salary_validation: bool = True
    min_hourly_wage: float = 15.0  # 澳洲最低工資參考
    min_annual_salary: float = 30000.0
    max_annual_salary: float = 500000.0
    
    # 去重策略
    dedup_by_url: bool = True
    dedup_by_title_company: bool = True
    dedup_similarity_threshold: float = 0.85
    
    # 輸出格式
    output_formats: List[str] = field(default_factory=lambda: ['json'])
    include_metadata: bool = True
    include_quality_stats: bool = True


@dataclass
class StorageConfig:
    """
    存儲配置類
    """
    base_path: str = "./seek_data"
    
    # 目錄結構
    subdirs: Dict[str, str] = field(default_factory=lambda: {
        'raw_data': 'raw_data',
        'processed_data': 'processed_data',
        'screenshots': 'screenshots',
        'ocr_results': 'ocr_results',
        'logs': 'logs',
        'exports': 'exports',
        'cache': 'cache'
    })
    
    # 文件命名
    use_timestamp_in_filename: bool = True
    timestamp_format: str = '%Y%m%d_%H%M%S'
    
    # 數據保留策略
    max_file_age_days: int = 30
    auto_cleanup: bool = False
    max_storage_size_mb: int = 1000
    
    # 壓縮選項
    compress_old_files: bool = False
    compression_format: str = 'zip'  # 'zip', 'gzip', '7z'


@dataclass
class LoggingConfig:
    """
    日誌配置類
    """
    level: str = 'INFO'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 日誌輸出
    console_output: bool = True
    file_output: bool = True
    
    # 日誌文件配置
    log_file_max_size_mb: int = 10
    log_file_backup_count: int = 5
    log_rotation: bool = True
    
    # 特定模組日誌級別
    module_levels: Dict[str, str] = field(default_factory=lambda: {
        'playwright': 'WARNING',
        'urllib3': 'WARNING',
        'requests': 'WARNING'
    })


@dataclass
class PerformanceConfig:
    """
    性能配置類
    """
    # 並發控制
    max_concurrent_requests: int = 3
    request_pool_size: int = 10
    
    # 內存管理
    max_memory_usage_mb: int = 512
    garbage_collection_interval: int = 100  # 處理多少個職位後進行垃圾回收
    
    # 緩存配置
    enable_caching: bool = True
    cache_size_limit: int = 1000  # 緩存項目數量限制
    cache_ttl_seconds: int = 3600  # 緩存生存時間
    
    # 性能監控
    enable_performance_monitoring: bool = True
    performance_log_interval: int = 50  # 每處理多少個職位記錄一次性能
    
    # 資源限制
    max_screenshot_size_mb: int = 5
    max_html_size_mb: int = 2
    max_ocr_processing_time_seconds: int = 30


class SeekCrawlerConfig:
    """
    Seek爬蟲主配置類
    整合所有配置選項
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路徑（可選）
        """
        # 初始化各個配置組件
        self.browser = BrowserConfig()
        self.ocr = OCRConfig()
        self.scraping = ScrapingConfig()
        self.etl = ETLConfig()
        self.storage = StorageConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
        
        # 從環境變量加載配置
        self._load_from_env()
        
        # 從配置文件加載（如果提供）
        if config_file:
            self._load_from_file(config_file)
        
        # 驗證配置
        self._validate_config()
    
    def _load_from_env(self):
        """
        從環境變量加載配置
        """
        # 瀏覽器配置
        self.browser.headless = os.getenv('SEEK_HEADLESS', 'true').lower() == 'true'
        self.browser.timeout = int(os.getenv('SEEK_BROWSER_TIMEOUT', '30000'))
        
        # OCR配置
        self.ocr.enabled = os.getenv('SEEK_OCR_ENABLED', 'true').lower() == 'true'
        
        # 爬蟲配置
        self.scraping.mode = os.getenv('SEEK_SCRAPING_MODE', 'hybrid')
        self.scraping.max_pages = int(os.getenv('SEEK_MAX_PAGES', '5'))
        self.scraping.results_wanted = int(os.getenv('SEEK_RESULTS_WANTED', '100'))
        
        # 存儲配置
        self.storage.base_path = os.getenv('SEEK_STORAGE_PATH', './seek_data')
        
        # 日誌配置
        self.logging.level = os.getenv('SEEK_LOG_LEVEL', 'INFO')
    
    def _load_from_file(self, config_file: str):
        """
        從配置文件加載配置
        
        Args:
            config_file: 配置文件路徑
        """
        try:
            import json
            
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置（簡化版本，實際應該遞歸更新）
                if 'browser' in config_data:
                    for key, value in config_data['browser'].items():
                        if hasattr(self.browser, key):
                            setattr(self.browser, key, value)
                
                # 類似地更新其他配置...
                
        except Exception as e:
            print(f"配置文件加載失敗: {e}")
    
    def _validate_config(self):
        """
        驗證配置的有效性
        """
        # 驗證爬蟲模式
        valid_modes = ['traditional', 'enhanced', 'hybrid']
        if self.scraping.mode not in valid_modes:
            raise ValueError(f"無效的爬蟲模式: {self.scraping.mode}. 有效選項: {valid_modes}")
        
        # 驗證數值範圍
        if self.scraping.max_pages < 1:
            raise ValueError("max_pages 必須大於 0")
        
        if self.scraping.results_wanted < 1:
            raise ValueError("results_wanted 必須大於 0")
        
        if self.performance.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests 必須大於 0")
        
        # 創建存儲目錄
        self._ensure_storage_dirs()
    
    def _ensure_storage_dirs(self):
        """
        確保存儲目錄存在
        """
        base_path = Path(self.storage.base_path)
        base_path.mkdir(exist_ok=True)
        
        for subdir in self.storage.subdirs.values():
            (base_path / subdir).mkdir(exist_ok=True)
    
    def get_storage_path(self, subdir: str) -> Path:
        """
        獲取特定子目錄的完整路徑
        
        Args:
            subdir: 子目錄名稱
            
        Returns:
            Path: 完整路徑
        """
        if subdir not in self.storage.subdirs:
            raise ValueError(f"未知的子目錄: {subdir}")
        
        return Path(self.storage.base_path) / self.storage.subdirs[subdir]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        將配置轉換為字典格式
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        from dataclasses import asdict
        
        return {
            'browser': asdict(self.browser),
            'ocr': asdict(self.ocr),
            'scraping': asdict(self.scraping),
            'etl': asdict(self.etl),
            'storage': asdict(self.storage),
            'logging': asdict(self.logging),
            'performance': asdict(self.performance)
        }
    
    def save_to_file(self, config_file: str):
        """
        將配置保存到文件
        
        Args:
            config_file: 配置文件路徑
        """
        import json
        
        try:
            config_data = self.to_dict()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到: {config_file}")
            
        except Exception as e:
            print(f"配置保存失敗: {e}")


# 預定義配置模板
class ConfigTemplates:
    """
    預定義的配置模板
    """
    
    @staticmethod
    def development() -> SeekCrawlerConfig:
        """
        開發環境配置
        
        Returns:
            SeekCrawlerConfig: 開發配置
        """
        config = SeekCrawlerConfig()
        
        # 開發環境設置
        config.browser.headless = False  # 顯示瀏覽器便於調試
        config.browser.slow_mo = 500  # 慢速操作便於觀察
        config.scraping.max_pages = 2  # 限制頁數
        config.scraping.results_wanted = 20  # 限制結果數量
        config.logging.level = 'DEBUG'  # 詳細日誌
        config.performance.enable_performance_monitoring = True
        
        return config
    
    @staticmethod
    def production() -> SeekCrawlerConfig:
        """
        生產環境配置
        
        Returns:
            SeekCrawlerConfig: 生產配置
        """
        config = SeekCrawlerConfig()
        
        # 生產環境設置
        config.browser.headless = True  # 無頭模式
        config.browser.slow_mo = 100  # 正常速度
        config.scraping.max_pages = 10  # 更多頁數
        config.scraping.results_wanted = 500  # 更多結果
        config.logging.level = 'INFO'  # 標準日誌
        config.performance.max_concurrent_requests = 5  # 更高並發
        config.storage.auto_cleanup = True  # 自動清理
        
        return config
    
    @staticmethod
    def testing() -> SeekCrawlerConfig:
        """
        測試環境配置
        
        Returns:
            SeekCrawlerConfig: 測試配置
        """
        config = SeekCrawlerConfig()
        
        # 測試環境設置
        config.browser.headless = True
        config.browser.timeout = 10000  # 較短超時
        config.scraping.max_pages = 1  # 最少頁數
        config.scraping.results_wanted = 5  # 最少結果
        config.ocr.enabled = False  # 禁用OCR加快測試
        config.scraping.enable_screenshots = False  # 禁用截圖
        config.logging.level = 'WARNING'  # 最少日誌
        
        return config


# 全局配置實例
default_config = SeekCrawlerConfig()


# 使用示例
if __name__ == "__main__":
    # 創建開發環境配置
    dev_config = ConfigTemplates.development()
    print("開發環境配置:")
    print(f"無頭模式: {dev_config.browser.headless}")
    print(f"最大頁數: {dev_config.scraping.max_pages}")
    print(f"日誌級別: {dev_config.logging.level}")
    
    # 保存配置到文件
    dev_config.save_to_file("seek_dev_config.json")
    
    # 創建生產環境配置
    prod_config = ConfigTemplates.production()
    print("\n生產環境配置:")
    print(f"無頭模式: {prod_config.browser.headless}")
    print(f"最大頁數: {prod_config.scraping.max_pages}")
    print(f"並發請求數: {prod_config.performance.max_concurrent_requests}")
    
    # 獲取存儲路徑示例
    screenshots_path = dev_config.get_storage_path('screenshots')
    print(f"\n截圖存儲路徑: {screenshots_path}")